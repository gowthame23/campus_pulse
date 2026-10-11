from datetime import datetime, timedelta

from core.constants import (
    ACCEPT_DEADLINE_HOURS,
    CATEGORY_PRIORITY_MAP,
    INACTIVE_STATUSES,
    PRIORITIES,
    SLA_ACTIVE_STATUSES,
    SLA_HOURS,
    STATUS_ASSIGNED,
    STATUS_BLOCKED,
    STATUS_IN_PROGRESS,
    STATUS_PENDING_WARDEN,
    STATUS_SUBMITTED,
    STATUS_WAITING_STUDENT,
    normalize_priority,
    normalize_role,
)
from models.complaint import Complaint
from models.location_in_charge import LocationInCharge
from models.student import Student
from storage.sqlite_repository import SQLiteRepository
from utils.helper import now, now_string, parse_date


class ComplaintConflictError(Exception):
    """Raised when an atomic operation conflicts with existing complaint state."""
    pass


class ComplaintService:
    def __init__(
        self, auth_service, notification_service, db_path="storage/campus_pulse.db"
    ):
        self.auth_service = auth_service
        self.notification_service = notification_service
        self.repository = SQLiteRepository(db_path, {"complaints": []})
        from services.config_service import ConfigService

        self.config_service = ConfigService(db_path)
        from services.attachment_service import AttachmentService

        self.attachment_service = AttachmentService(db_path)

    def _load_complaints(self):
        return [
            Complaint.from_dict(item)
            for item in self.repository.load().get("complaints", [])
        ]

    def _save_complaints(self, complaints):
        self.repository.save(
            {"complaints": [complaint.to_dict() for complaint in complaints]}
        )

    def get_affected_students_counts(self):
        try:
            with self._db_conn() as conn:
                rows = conn.execute("SELECT complaint_id, COUNT(*) as count FROM affected_students GROUP BY complaint_id").fetchall()
                return {r["complaint_id"]: r["count"] for r in rows}
        except Exception:
            return {}

    def _enrich_sla(self, complaint, dept_cache=None):
        if dept_cache is not None:
            if complaint.department_id not in dept_cache:
                dept_cache[complaint.department_id] = self.auth_service.get_department(
                    complaint.department_id
                )
            dept = dept_cache[complaint.department_id]
        else:
            dept = self.auth_service.get_department(complaint.department_id)
        if not dept:
            complaint.due_date = None
            complaint.sla_status = "🟢 On Time"
            return

        created_dt = parse_date(complaint.created_at)
        if not created_dt:
            complaint.due_date = None
            complaint.sla_status = "🟢 On Time"
            return

        due_dt = created_dt + timedelta(days=dept.sla_days)
        complaint.due_date = due_dt.strftime("%Y-%m-%d %H:%M:%S")

        current_time = now()
        if (
            complaint.status in (Complaint.CLOSED, Complaint.AUTO_CLOSED)
            or complaint.resolved_at
        ):
            end_dt = parse_date(complaint.resolved_at or complaint.updated_at)
            if end_dt and end_dt <= due_dt:
                complaint.sla_status = "🟢 On Time"
            else:
                complaint.sla_status = "🔴 Overdue"
        else:
            if current_time > due_dt:
                complaint.sla_status = "🔴 Overdue"
            elif current_time.date() == due_dt.date():
                complaint.sla_status = "🟡 Due Today"
            else:
                complaint.sla_status = "🟢 On Time"

    def list_all(self, include_archived=False):
        complaints = self._load_complaints()
        self.apply_automatic_rules(complaints)
        complaints = self._load_complaints()
        dept_cache = {}
        for c in complaints:
            self._enrich_sla(c, dept_cache)
        if not include_archived:
            return [c for c in complaints if not c.archived]
        return complaints

    def get_complaint(self, complaint_id, include_archived=False):
        for complaint in self.list_all(include_archived=include_archived):
            if complaint.complaint_id == complaint_id:
                return complaint
        return None

    def save_complaint(self, complaint):
        complaints = self._load_complaints()
        if complaint.status in (Complaint.CLOSED, Complaint.AUTO_CLOSED):
            try:
                self.clear_affected_records(complaint.complaint_id)
            except Exception:
                pass
        for index, item in enumerate(complaints):
            if item.complaint_id == complaint.complaint_id:
                complaints[index] = complaint
                self._save_complaints(complaints)
                return
        complaints.append(complaint)
        self._save_complaints(complaints)

    def create_complaint(
        self,
        user,
        location_id,
        department_id,
        complaint_type,
        description,
        title=None,
        attachment_url=None,
        category=None,
        visibility_type="Private",
        issue_id=None,
        visibility=None,
        priority=None,
        is_urgent=False,
        urgent_reason=None,
    ):
        # 1. Role Verification - Only Students and Location In-Charges can create complaints
        if (getattr(user, "role", "") or "").lower() not in ("student", "location_in_charge"):
            raise PermissionError("Only students and location in-charges can create complaints.")

        # 2. Input Validation
        if not description or not description.strip():
            raise ValueError("Description is required.")
        if not location_id or not location_id.strip():
            raise ValueError("Location is required.")
        if not department_id or not department_id.strip():
            raise ValueError("Department is required.")

        title = title or f"Issue reported by {user.name}"
        category = category or complaint_type or "General"
        complaint_type = complaint_type or category
        if visibility:
            visibility_type = visibility.capitalize()

        # 3. Active Structure Validation
        location = self.auth_service.get_location(location_id)
        if not location:
            raise ValueError("Location does not exist.")
        if hasattr(location, "active") and not location.active:
            raise ValueError("Selected location is inactive.")

        # Student hostel restriction: a student's assigned hostel restricts hostel complaints,
        # not other permitted campus facilities (Academic Block, Mess, SAC, Sports Complex, etc.).
        if (getattr(user, "role", "") or "").lower() == "student":
            loc_type = (getattr(location, "location_type", "") or getattr(location, "name", "")).lower()
            if "hostel" in loc_type:
                student_loc_id = getattr(user, "location_id", None)
                student_hostel = getattr(user, "hostel", None)
                profile = (
                    self.auth_service.get_student_profile(user.user_id)
                    if hasattr(self.auth_service, "get_student_profile")
                    else None
                )
                if profile:
                    student_loc_id = student_loc_id or profile.get("location_id")
                    student_hostel = student_hostel or profile.get("hostel")

                allowed_ids = set()
                allowed_names = set()
                if student_loc_id:
                    allowed_ids.add(str(student_loc_id).lower())
                    st_loc = self.auth_service.get_location(student_loc_id)
                    if st_loc:
                        allowed_ids.add(st_loc.location_id.lower())
                        allowed_names.add(st_loc.name.lower())
                if student_hostel:
                    allowed_names.add(str(student_hostel).lower())
                    st_loc_by_name = self.auth_service.get_location(student_hostel)
                    if st_loc_by_name:
                        allowed_ids.add(st_loc_by_name.location_id.lower())
                        allowed_names.add(st_loc_by_name.name.lower())
                    for l in self.auth_service.list_locations():
                        if l.name.lower() == str(student_hostel).lower() or l.location_id.lower() == str(student_hostel).lower():
                            allowed_ids.add(l.location_id.lower())
                            allowed_names.add(l.name.lower())

                target_id = location.location_id.lower()
                target_name = location.name.lower()
                is_match = target_id in allowed_ids or target_name in allowed_names

                if not is_match:
                    raise PermissionError(
                        "Students can only submit complaints for their assigned hostel."
                    )

        department = self.auth_service.get_department(department_id)
        if not department and (department_id == "DEPT_OTHER" or department_id.lower() == "other"):
            from models.department import Department
            department = Department("Other", 1, department_id="DEPT_OTHER")
        elif not department:
            raise ValueError("Department does not exist.")
        if hasattr(department, "active") and not department.active:
            raise ValueError("Selected department is inactive.")

        # 4. Issue & Priority Validation
        final_priority = None
        if priority:
            final_priority = normalize_priority(priority)
        elif issue_id:
            try:
                import sqlite3
                conn = sqlite3.connect(self.repository.path)
                conn.row_factory = sqlite3.Row
                issue_row = conn.execute("SELECT * FROM department_issues WHERE issue_id = ?", (issue_id,)).fetchone()
                conn.close()
                if issue_row:
                    iss_dict = dict(issue_row)
                    if iss_dict.get("department_id") != department_id:
                        raise ValueError("Selected issue does not belong to the chosen department.")
                    if iss_dict.get("active") == 0:
                        raise ValueError("Selected issue is inactive.")
                    final_priority = normalize_priority(iss_dict.get("default_priority"))
            except Exception as e:
                if isinstance(e, ValueError):
                    raise e

        if not final_priority:
            cat_key = (category or "").strip().lower()
            ct_key = (complaint_type or "").strip().lower()
            if cat_key in CATEGORY_PRIORITY_MAP:
                final_priority = CATEGORY_PRIORITY_MAP[cat_key]
            elif ct_key in CATEGORY_PRIORITY_MAP:
                final_priority = CATEGORY_PRIORITY_MAP[ct_key]
            else:
                final_priority = "Medium"

        if is_urgent:
            if final_priority in ("Low", "Medium"):
                final_priority = "High"

        final_priority = normalize_priority(final_priority)

        # 5. Prevent duplicate rapid submissions from same student
        current_time = now()
        for c in self.list_all():
            if (
                c.created_by == user.user_id
                and c.location_id == location_id
                and c.department_id == department_id
                and c.description.strip().lower() == description.strip().lower()
            ):
                created_time = parse_date(c.created_at)
                if (
                    created_time
                    and (current_time - created_time).total_seconds() < 300
                ):
                    raise ValueError(
                        "Duplicate complaint detected. You have already submitted this issue recently."
                    )

        # 6. Compute initial SLA deadline
        sla_hours = SLA_HOURS.get(final_priority, 48)
        sla_deadline = (current_time + timedelta(hours=sla_hours)).isoformat()

        # 7. Create Complaint instance
        complaint = Complaint(
            user.user_id,
            user.role,
            location_id,
            department_id,
            complaint_type,
            description,
            attachment_url=attachment_url,
            priority=final_priority,
            category=category,
            visibility_type=visibility_type,
            title=title,
        )
        complaint.sla_deadline = sla_deadline
        complaint.is_urgent = bool(is_urgent)
        complaint.urgent_reason = urgent_reason if is_urgent else None

        # 8. Auto-routing: Check active coordinators for (location, department)
        assignments = (
            self.auth_service.list_coordinator_assignments(
                location_id=location_id, department_id=department_id
            )
            or []
        )
        all_loc_assignments = (
            self.auth_service.list_coordinator_assignments(
                location_id="ALL", department_id=department_id
            )
            or []
        )

        candidate_coords = []
        seen_coords = set()
        for a in assignments + all_loc_assignments:
            cid = a.get("coordinator_id")
            if cid and cid not in seen_coords:
                seen_coords.add(cid)
                u = self.auth_service.get_user(cid)
                if (
                    u
                    and getattr(u, "active", False)
                    and not getattr(u, "is_deleted", False)
                    and getattr(u, "status", "Active") == "Active"
                ):
                    candidate_coords.append(cid)

        if len(candidate_coords) == 1:
            coord_id = candidate_coords[0]
            complaint.assigned_to = coord_id
            complaint.status = Complaint.ASSIGNED
            complaint.assigned_at = complaint.created_at
            complaint.auto_assigned = True
            complaint.add_history(f"Auto-assigned to coordinator {coord_id}.")
            self.notification_service.notify(
                coord_id,
                f"Complaint {complaint.complaint_id} ({complaint.priority}) assigned to you.",
                complaint_id=complaint.complaint_id,
                title="New Assigned Complaint",
            )
        elif len(candidate_coords) >= 2:
            complaint.assigned_to = None
            complaint.status = Complaint.SUBMITTED
            complaint.team_location_id = location_id
            complaint.team_department_id = department_id
            complaint.add_history("Multiple coordinators available. Placed in coordinator accept queue.")
            for cid in candidate_coords:
                self.notification_service.notify(
                    cid,
                    f"New work available in your queue: {complaint.title or complaint.category} ({complaint.priority}).",
                    complaint_id=complaint.complaint_id,
                    title="Work Available in Queue",
                )
        else:
            complaint.assigned_to = None
            complaint.status = Complaint.SUBMITTED
            complaint.add_history("No coordinator assigned for this location/department. Placed in queue.")
            loc_obj = self.auth_service.get_location(location_id)
            dept_obj = self.auth_service.get_department(department_id)
            loc_label = loc_obj.name if loc_obj else location_id
            dept_label = dept_obj.name if dept_obj else department_id
            alert_msg = f"Complaint {complaint.complaint_id} filed in {loc_label}/{dept_label} has no coordinator assigned. Please assign coverage."

            warden_id = getattr(loc_obj, "in_charge_id", None)
            if warden_id:
                self.notification_service.notify(
                    warden_id, alert_msg, complaint_id=complaint.complaint_id, title="Coverage Gap Alert"
                )
            app_mgr_id = getattr(loc_obj, "app_manager_id", None)
            if app_mgr_id:
                self.notification_service.notify(
                    app_mgr_id, alert_msg, complaint_id=complaint.complaint_id, title="Coverage Gap Alert"
                )
            for admin_u in self.auth_service.list_users(role="administrator"):
                if admin_u.active and not getattr(admin_u, "is_deleted", False):
                    self.notification_service.notify(
                        admin_u.user_id, alert_msg, complaint_id=complaint.complaint_id, title="Coverage Gap Alert"
                    )

        # 9. In ALL cases: ALWAYS notify the warden of the complaint's location
        loc_obj = self.auth_service.get_location(location_id)
        warden_id = getattr(loc_obj, "in_charge_id", None)
        if warden_id:
            self.notification_service.notify(
                warden_id,
                f"New complaint filed in your location: {complaint.title or complaint.category} ({complaint.priority})",
                complaint_id=complaint.complaint_id,
                title="New Complaint in Your Location",
            )

        # 10. Notify submitter
        self.notification_service.notify(
            user.user_id,
            f"Your complaint {complaint.complaint_id} has been submitted successfully.",
            complaint_id=complaint.complaint_id,
            title="Complaint Submitted",
        )

        self._enrich_sla(complaint)
        self.save_complaint(complaint)
        return complaint

    def complaints_for_student(self, student_id):
        return [
            item
            for item in self.list_all(include_archived=True)
            if item.created_by == student_id
        ]

    def complaints_for_department(self, department_id):
        return [
            item
            for item in self.list_all(include_archived=True)
            if item.department_id == department_id
        ]

    def complaints_for_location(self, location_id):
        return [
            item
            for item in self.list_all(include_archived=True)
            if item.location_id == location_id
        ]

    def unassigned_complaints(self):
        return [
            item
            for item in self.list_all(include_archived=True)
            if not item.assigned_to
        ]

    def assign_work(self, complaint_id, coordinator_id):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")
        target_user = self.auth_service.get_user(coordinator_id)
        if not target_user:
            raise ValueError("Assigned user does not exist.")
        if (target_user.role or "").lower() != "coordinator":
            raise ValueError("Complaints can only be assigned to coordinators.")
        if not target_user.active or getattr(target_user, "is_deleted", False) or getattr(target_user, "status", "Active") != "Active":
            raise ValueError("Coordinator is inactive.")
        old_status = complaint.status
        old_assigned = complaint.assigned_to
        complaint.assign(coordinator_id)
        complaint.assigned_at = complaint.assigned_at or now_string()
        try:
            self.save_complaint(complaint)
            self.notification_service.assigned(complaint_id, coordinator_id)
        except Exception as err:
            complaint.status = old_status
            complaint.assigned_to = old_assigned
            self.save_complaint(complaint)
            raise err
        return complaint

    def mark_resolved(self, complaint_id, notes=""):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")

        # Allow resolving from In Progress (or Assigned with implicit transition)
        if complaint.status == Complaint.ASSIGNED:
            complaint.status = Complaint.IN_PROGRESS
            complaint.started_at = complaint.started_at or now_string()
            complaint.add_history("Work implicitly started upon resolution.")
        elif complaint.status != Complaint.IN_PROGRESS:
            raise ValueError("Complaint must be In Progress or Assigned before it can be resolved.")

        # 10. Resolution Validation
        attachments = self.attachment_service.list_attachments(complaint_id)
        has_after_repair = any(a["category"] == "After Repair" for a in attachments)

        if not has_after_repair and not (notes or "").strip():
            raise ValueError(
                "Resolution Notes are mandatory when no 'After Repair' image is provided."
            )

        old_status = complaint.status
        old_resolved_at = complaint.resolved_at
        old_notes = complaint.resolution_notes
        complaint.mark_resolved(notes)

        # Override auto-close days based on dynamic settings
        from utils.helper import add_days_string

        try:
            auto_close_days = int(self.config_service.get_setting("auto_close_days", 5))
        except Exception:
            auto_close_days = 5
        complaint.verification_due_at = add_days_string(auto_close_days)

        try:
            self.save_complaint(complaint)
            self.notification_service.resolved(
                complaint_id, receiver_id=complaint.created_by or "Verifier"
            )
        except Exception as err:
            complaint.status = old_status
            complaint.resolved_at = old_resolved_at
            complaint.resolution_notes = old_notes
            self.save_complaint(complaint)
            raise err
        return complaint

    def can_verify(self, complaint, user):
        if user.user_id == complaint.assigned_to:
            return False
        if complaint.creator_role == Student.ROLE:
            if user.user_id == complaint.created_by:
                return True
            if (
                user.role == LocationInCharge.ROLE
                and user.location_id == complaint.location_id
            ):
                return True
        if complaint.creator_role == LocationInCharge.ROLE:
            return user.user_id == complaint.created_by
        return False

    def verify_fixed(self, complaint_id, user):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")
        if complaint.status != Complaint.WAITING_VERIFICATION:
            raise ValueError("Complaint is not waiting for verification.")
        if not self.can_verify(complaint, user):
            raise ValueError("This user cannot verify the complaint.")
        complaint.verification_reports.append({"by": user.user_id, "result": "Fixed"})
        complaint.close(user.user_id)
        self.save_complaint(complaint)

        # Notify assigned staff member if present
        if complaint.assigned_to:
            self.notification_service.publish(
                receiver_id=complaint.assigned_to,
                title="Complaint Verified and Closed",
                message=f"Complaint {complaint_id} has been verified and closed.",
                module="Complaint",
                notification_type="closure",
                reference_type="Complaint",
                reference_id=complaint_id,
                priority="Medium",
            )
        # Notify verifier
        self.notification_service.publish(
            receiver_id=user.user_id,
            title="Complaint Closed",
            message=f"Complaint {complaint_id} has been verified and closed successfully.",
            module="Complaint",
            notification_type="closure",
            reference_type="Complaint",
            reference_id=complaint_id,
            priority="Medium",
        )
        return complaint

    def report_not_fixed(self, complaint_id, user, reason):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")
        if complaint.status != Complaint.WAITING_VERIFICATION:
            raise ValueError("Complaint is not waiting for verification.")
        if not self.can_verify(complaint, user):
            raise ValueError("This user cannot report on this complaint.")

        try:
            max_reopen = int(self.config_service.get_setting("max_reopen_count", 3))
        except Exception:
            max_reopen = 3

        if complaint.reopen_count >= max_reopen:
            raise ValueError(
                f"Cannot reopen complaint. Reopen limit of {max_reopen} has been reached."
            )

        old_status = complaint.status
        old_reopen_count = complaint.reopen_count
        complaint.reopen(user.user_id, reason)

        try:
            if complaint.reopen_count >= 2 and not complaint.admin_notified:
                complaint.admin_notified = True
                self.notification_service.repeated_reopen(complaint_id)
            self.save_complaint(complaint)
            self.notification_service.reopened(
                complaint_id, receiver_id=complaint.assigned_to or "Coordinator"
            )
        except Exception as err:
            complaint.status = old_status
            complaint.reopen_count = old_reopen_count
            self.save_complaint(complaint)
            raise err
        return complaint

    def find_least_loaded_coordinator(self, location_id, department_id):
        assignments = (
            self.auth_service.list_coordinator_assignments(
                location_id=location_id, department_id=department_id
            )
            or []
        )
        all_loc_assignments = (
            self.auth_service.list_coordinator_assignments(
                location_id="ALL", department_id=department_id
            )
            or []
        )
        candidate_ids = []
        seen = set()
        for a in assignments + all_loc_assignments:
            cid = a.get("coordinator_id")
            if cid and cid not in seen:
                seen.add(cid)
                u = self.auth_service.get_user(cid)
                if (
                    u
                    and getattr(u, "active", False)
                    and not getattr(u, "is_deleted", False)
                    and getattr(u, "status", "Active") == "Active"
                ):
                    candidate_ids.append(cid)

        if not candidate_ids:
            return None
        if len(candidate_ids) == 1:
            return candidate_ids[0]

        counts = {cid: 0 for cid in candidate_ids}
        for c in self.list_all():
            if c.assigned_to in counts and c.status in SLA_ACTIVE_STATUSES:
                counts[c.assigned_to] += 1

        return min(counts.keys(), key=lambda k: counts[k])

    def apply_automatic_rules(self, complaints=None):
        complaints = complaints or self._load_complaints()
        changed = False
        current_time = now()
        loc_cache = {}

        def _get_loc(loc_id):
            if loc_id not in loc_cache:
                loc_cache[loc_id] = self.auth_service.get_location(loc_id)
            return loc_cache[loc_id]

        for complaint in complaints:
            # 1. 48h Auto-Close & 24h Reminder for Waiting for Verification
            if complaint.status in (Complaint.WAITING_VERIFICATION, "Waiting for Verification"):
                due_at = parse_date(complaint.verification_due_at)
                # Check 24h reminder
                if not getattr(complaint, "auto_close_reminded", False):
                    stage_start = parse_date(getattr(complaint, "student_stage_at", None) or complaint.resolved_at or complaint.updated_at)
                    if stage_start and current_time > stage_start + timedelta(hours=24):
                        complaint.auto_close_reminded = True
                        complaint.add_history("24-hour auto-close reminder sent to student.")
                        self.notification_service.notify(
                            complaint.created_by,
                            f"Reminder: Complaint {complaint.complaint_id} was resolved. It will auto-close in 24 hours if no action is taken.",
                            complaint_id=complaint.complaint_id,
                            title="Resolution Auto-Close Reminder",
                        )
                        changed = True

                # Check 48h deadline for auto-close
                if due_at and current_time > due_at:
                    complaint.auto_close()
                    complaint.add_history("Auto-closed after 48h student inactivity.")
                    changed = True

            # 2. SLA Countdown & Escalation Ladder for active tickets
            if complaint.status in SLA_ACTIVE_STATUSES or (complaint.status not in INACTIVE_STATUSES and complaint.status not in (Complaint.WAITING_VERIFICATION, "Waiting for Verification")):
                sla_deadline_dt = parse_date(complaint.sla_deadline)
                if not sla_deadline_dt:
                    created_dt = parse_date(complaint.created_at) or current_time
                    p = normalize_priority(complaint.priority)
                    sla_hours = SLA_HOURS.get(p, 48)
                    sla_deadline_dt = created_dt + timedelta(hours=sla_hours)
                    complaint.sla_deadline = sla_deadline_dt.isoformat()
                    changed = True

                if current_time > sla_deadline_dt:
                    loc = _get_loc(complaint.location_id)
                    warden_id = getattr(loc, "in_charge_id", None)
                    app_mgr_id = getattr(loc, "app_manager_id", None)

                    # Level 1: Overdue -> Coordinator + Warden
                    if int(getattr(complaint, "escalation_level", 0)) < 1:
                        complaint.escalation_level = 1
                        complaint.escalated = True
                        complaint.add_history("SLA deadline exceeded. Escalated to Coordinator and Warden.")
                        if complaint.assigned_to:
                            self.notification_service.notify(
                                complaint.assigned_to,
                                f"Complaint {complaint.complaint_id} ({complaint.priority}) is OVERDUE. Deadline was {complaint.sla_deadline}.",
                                complaint_id=complaint.complaint_id,
                                title="SLA Overdue Alert",
                            )
                        if warden_id:
                            self.notification_service.notify(
                                warden_id,
                                f"Complaint {complaint.complaint_id} ({complaint.priority}) in your location is OVERDUE.",
                                complaint_id=complaint.complaint_id,
                                title="SLA Overdue Alert",
                            )
                        changed = True

                    # Level 2: Overdue + 24h -> App Manager
                    if current_time > sla_deadline_dt + timedelta(hours=24):
                        if int(getattr(complaint, "escalation_level", 0)) < 2:
                            complaint.escalation_level = 2
                            complaint.add_history("SLA deadline exceeded by 24h. Escalated to App Manager.")
                            if app_mgr_id:
                                self.notification_service.notify(
                                    app_mgr_id,
                                    f"Complaint {complaint.complaint_id} ({complaint.priority}) is 24h past SLA. Escalated to App Manager.",
                                    complaint_id=complaint.complaint_id,
                                    title="SLA 24h Escalation",
                                )
                            changed = True

                    # Level 3: Overdue + 48h -> Administrator
                    if current_time > sla_deadline_dt + timedelta(hours=48):
                        if int(getattr(complaint, "escalation_level", 0)) < 3:
                            complaint.escalation_level = 3
                            complaint.admin_notified = True
                            complaint.add_history("SLA deadline exceeded by 48h. Escalated to Administrator.")
                            for admin_u in self.auth_service.list_users(role="administrator"):
                                if admin_u.active and not getattr(admin_u, "is_deleted", False):
                                    self.notification_service.notify(
                                        admin_u.user_id,
                                        f"CRITICAL: Complaint {complaint.complaint_id} ({complaint.priority}) is 48h past SLA. Escalated to Administrator.",
                                        complaint_id=complaint.complaint_id,
                                        title="SLA Critical Escalation",
                                    )
                            changed = True

                # Accept queue deadline check for unassigned Submitted tickets
                if complaint.status == Complaint.SUBMITTED and not complaint.assigned_to:
                    created_dt = parse_date(complaint.created_at) or current_time
                    p = normalize_priority(complaint.priority)
                    accept_hours = ACCEPT_DEADLINE_HOURS.get(p, 4)
                    if current_time > created_dt + timedelta(hours=accept_hours):
                        least_loaded = self.find_least_loaded_coordinator(complaint.location_id, complaint.department_id)
                        if least_loaded:
                            complaint.assigned_to = least_loaded
                            complaint.status = Complaint.ASSIGNED
                            complaint.assigned_at = current_time.isoformat()
                            complaint.auto_assigned = True
                            complaint.add_history(
                                f"Accept deadline expired ({accept_hours}h). Auto-assigned to least-loaded coordinator {least_loaded}."
                            )
                            self.notification_service.notify(
                                least_loaded,
                                f"Complaint {complaint.complaint_id} ({complaint.priority}) auto-assigned to you after queue timeout.",
                                complaint_id=complaint.complaint_id,
                                title="Complaint Auto-Assigned",
                            )
                            changed = True

            # 3. Complaints pending warden verification (>24h reminder to warden, >48h to App Manager)
            if complaint.status in (Complaint.PENDING_WARDEN_VERIFICATION, "Pending Warden Verification"):
                fixed_dt = parse_date(getattr(complaint, "fixed_at", None) or complaint.resolved_at or complaint.updated_at)
                if fixed_dt:
                    loc = _get_loc(complaint.location_id)
                    warden_id = getattr(loc, "in_charge_id", None)
                    app_mgr_id = getattr(loc, "app_manager_id", None)

                    if current_time > fixed_dt + timedelta(hours=24):
                        if int(getattr(complaint, "warden_escalation_level", 0)) < 1:
                            complaint.warden_escalation_level = 1
                            complaint.add_history("Pending warden verification >24h. Reminder sent to Warden.")
                            if warden_id:
                                self.notification_service.notify(
                                    warden_id,
                                    f"Complaint {complaint.complaint_id} has been waiting for your verification for >24 hours. Please inspect.",
                                    complaint_id=complaint.complaint_id,
                                    title="Pending Verification Reminder",
                                )
                            changed = True

                    if current_time > fixed_dt + timedelta(hours=48):
                        if int(getattr(complaint, "warden_escalation_level", 0)) < 2:
                            complaint.warden_escalation_level = 2
                            complaint.add_history("Pending warden verification >48h. Escalated to App Manager.")
                            if app_mgr_id:
                                self.notification_service.notify(
                                    app_mgr_id,
                                    f"Complaint {complaint.complaint_id} has been waiting for warden verification for >48 hours in {loc.name if loc else complaint.location_id}.",
                                    complaint_id=complaint.complaint_id,
                                    title="Warden Verification Overdue",
                                )
                            changed = True

        if changed:
            self._save_complaints(complaints)

    def analytics(self):
        complaints = self.list_all()
        status_counts = {}
        dept_counts = {}
        loc_counts = {}
        resolution_times = []

        auto_closed_count = 0
        escalated_count = 0
        reopened_count = 0
        unassigned_count = 0

        for complaint in complaints:
            status_counts[complaint.status] = status_counts.get(complaint.status, 0) + 1
            dept_counts[complaint.department_id] = (
                dept_counts.get(complaint.department_id, 0) + 1
            )
            loc_counts[complaint.location_id] = (
                loc_counts.get(complaint.location_id, 0) + 1
            )

            if complaint.auto_closed:
                auto_closed_count += 1
            if complaint.escalated:
                escalated_count += 1
            if complaint.reopen_count > 0:
                reopened_count += 1
            if not complaint.assigned_to:
                unassigned_count += 1

            if (
                complaint.status in (Complaint.CLOSED, Complaint.AUTO_CLOSED)
                or complaint.resolved_at
            ):
                try:
                    t_start = parse_date(complaint.created_at)
                    t_end = parse_date(complaint.resolved_at or complaint.updated_at)
                    if t_start and t_end:
                        diff = (t_end - t_start).total_seconds() / 3600.0
                        resolution_times.append(diff)
                except Exception:
                    pass

        avg_res_time = (
            sum(resolution_times) / len(resolution_times) if resolution_times else 0.0
        )

        return {
            "total": len(complaints),
            "by_status": status_counts,
            "auto_closed": auto_closed_count,
            "escalated": escalated_count,
            "reopened": reopened_count,
            "unassigned": unassigned_count,
            "average_resolution_time": round(avg_res_time, 2),
            "by_department": dept_counts,
            "by_location": loc_counts,
        }

    def delete_complaint(self, complaint_id):
        # 1. Clean up notifications referencing this complaint
        self.notification_service.delete_complaint_notifications(complaint_id)
        # 2. Clear affected student records
        self.clear_affected_records(complaint_id)
        # 3. SQLite transaction to delete complaint
        with self.repository._connect() as connection:
            connection.execute("BEGIN TRANSACTION")
            try:
                connection.execute(
                    "DELETE FROM complaints WHERE complaint_id = ?", (complaint_id,)
                )
                connection.execute("COMMIT")
            except Exception as e:
                connection.execute("ROLLBACK")
                raise e

    def _db_conn(self):
        import sqlite3

        conn = sqlite3.connect(self.repository.path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_affected_count(self, complaint_id):
        with self._db_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as count FROM affected_students WHERE complaint_id = ?",
                (complaint_id,),
            ).fetchone()
            return row["count"] if row else 0

    def is_student_affected(self, complaint_id, student_id):
        with self._db_conn() as conn:
            row = conn.execute(
                "SELECT 1 FROM affected_students WHERE complaint_id = ? AND student_id = ?",
                (complaint_id, student_id),
            ).fetchone()
            return row is not None

    def get_duplicate_complaints(self, location_id, department_id, issue_id=None):
        active_complaints = [
            c for c in self.list_all(include_archived=False)
            if c.location_id == location_id
            and c.department_id == department_id
            and c.status not in (Complaint.CLOSED, Complaint.AUTO_CLOSED)
        ]
        if issue_id:
            active_complaints = [c for c in active_complaints if getattr(c, "issue_id", None) == issue_id or c.category == issue_id]

        result = []
        for c in active_complaints:
            d = c.to_dict()
            d["affected_count"] = self.get_affected_count(c.complaint_id)
            result.append(d)
        return result

    def add_affected_student(self, complaint_id, student_id, room_note=None):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")
        if complaint.status in (Complaint.CLOSED, Complaint.AUTO_CLOSED):
            raise ValueError("Complaint is closed.")

        if self.is_student_affected(complaint_id, student_id):
            raise ValueError(
                "You have already marked yourself as affected by this issue."
            )

        with self._db_conn() as conn:
            conn.execute(
                "INSERT INTO affected_students (complaint_id, student_id) VALUES (?, ?)",
                (complaint_id, student_id),
            )

        note_str = f" ({room_note})" if room_note else ""
        complaint.add_history(f"Student {student_id} marked themselves as affected{note_str}.")
        self.save_complaint(complaint)
        return complaint

    def clear_affected_records(self, complaint_id):
        with self._db_conn() as conn:
            conn.execute(
                "DELETE FROM affected_students WHERE complaint_id = ?", (complaint_id,)
            )

    def get_active_app_manager(self):
        """Returns the user_id of the first active App Manager, or a fallback."""
        with self._db_conn() as conn:
            row = conn.execute(
                "SELECT user_id FROM users WHERE role = 'app_manager' AND active = 1 LIMIT 1"
            ).fetchone()
            return row["user_id"] if row else "USR_APP_MANAGER"

    def take_complaint(self, complaint_id, user_id):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")
        if complaint.status != Complaint.SUBMITTED:
            raise ValueError("Only Submitted complaints can be taken.")
        if complaint.assigned_to:
            raise ValueError("Complaint is already assigned to a staff member.")
        complaint.status = Complaint.ASSIGNED
        complaint.assigned_to = user_id
        complaint.add_history(f"Complaint taken by staff {user_id}.")
        self.save_complaint(complaint)
        return complaint

    def accept_complaint(self, complaint_id, coordinator_id):
        coord_user = self.auth_service.get_user(coordinator_id)
        if not coord_user or (coord_user.role or "").lower() not in ("coordinator", "administrator"):
            raise ValueError("Only coordinators or administrators can accept complaints.")
        if not coord_user.active or getattr(coord_user, "is_deleted", False) or getattr(coord_user, "status", "Active") != "Active":
            raise ValueError("Coordinator is inactive.")

        now_str = now_string()
        with self.repository._connect() as conn:
            cursor = conn.execute(
                """
                UPDATE complaints
                SET assigned_to = ?, status = 'Assigned', assigned_at = ?, updated_at = ?
                WHERE complaint_id = ? AND (assigned_to IS NULL OR status = 'Submitted')
                """,
                (coordinator_id, now_str, now_str, complaint_id),
            )
            if cursor.rowcount == 0:
                row = conn.execute("SELECT status, assigned_to FROM complaints WHERE complaint_id = ?", (complaint_id,)).fetchone()
                if not row:
                    raise ValueError("Complaint not found.")
                raise ComplaintConflictError("Complaint has already been accepted by another coordinator or is not available.")

        complaint = self.get_complaint(complaint_id)
        if complaint:
            complaint.add_history(f"Accepted by coordinator {coord_user.name} ({coordinator_id}).")
            self.save_complaint(complaint)
        return complaint

    def start_work(self, complaint_id, coordinator_id):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")
        if complaint.status not in (Complaint.ASSIGNED, Complaint.REOPENED, Complaint.SUBMITTED):
            raise ValueError("Complaint must be Assigned, Submitted, or Reopened before starting work.")
        if complaint.assigned_to and complaint.assigned_to != coordinator_id:
            raise ValueError("You can only work on complaints assigned to you.")

        complaint.status = Complaint.IN_PROGRESS
        complaint.assigned_to = coordinator_id
        complaint.started_at = complaint.started_at or now_string()
        complaint.add_history(f"Work started by Coordinator {coordinator_id}.")
        self.save_complaint(complaint)
        return complaint

    def record_progress(self, complaint_id, coordinator_id, note, photo_url=None):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")
        if complaint.assigned_to != coordinator_id:
            raise ValueError("You can only update complaints assigned to you.")
        if not note or not note.strip():
            raise ValueError("Progress note is required.")

        msg = f"Progress update: {note.strip()}"
        if photo_url:
            msg += " (photo attached)"
        complaint.add_history(msg)
        self.save_complaint(complaint)

        self.notification_service.notify(
            complaint.created_by,
            f"Update on your complaint {complaint.complaint_id}: {note.strip()}",
            complaint_id=complaint.complaint_id,
            title="Complaint Progress Update",
        )
        return complaint

    def block_complaint(self, complaint_id, coordinator_id, reason, expected_date=None):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")
        if complaint.assigned_to != coordinator_id:
            raise ValueError("You can only block complaints assigned to you.")
        if not reason or not reason.strip():
            raise ValueError("Block reason is required.")

        complaint.status = STATUS_BLOCKED
        complaint.blocked_reason = reason.strip()
        complaint.blocked_until = expected_date
        complaint.blocked_at = now_string()
        complaint.add_history(f"Work paused: {reason.strip()} (Expected: {expected_date or 'TBD'})")
        self.save_complaint(complaint)

        loc = self.auth_service.get_location(complaint.location_id)
        warden_id = getattr(loc, "in_charge_id", None)
        if warden_id:
            self.notification_service.notify(
                warden_id,
                f"Complaint {complaint.complaint_id} blocked: {reason.strip()}",
                complaint_id=complaint.complaint_id,
                title="Complaint Work Paused",
            )
        self.notification_service.notify(
            complaint.created_by,
            f"Work on your complaint {complaint.complaint_id} is temporarily paused: {reason.strip()}",
            complaint_id=complaint.complaint_id,
            title="Complaint Work Paused",
        )
        return complaint

    def unblock_complaint(self, complaint_id, coordinator_id):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")
        if complaint.assigned_to != coordinator_id:
            raise ValueError("You can only resume complaints assigned to you.")
        if complaint.status != STATUS_BLOCKED:
            raise ValueError("Complaint is not currently blocked.")

        complaint.status = STATUS_IN_PROGRESS
        complaint.blocked_reason = None
        complaint.blocked_until = None
        complaint.add_history("Work resumed by coordinator.")
        self.save_complaint(complaint)

        self.notification_service.notify(
            complaint.created_by,
            f"Work on your complaint {complaint.complaint_id} has resumed.",
            complaint_id=complaint.complaint_id,
            title="Complaint Resumed",
        )
        return complaint

    def change_priority(self, complaint_id, user, new_priority, reason=None):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")
        old_priority = complaint.priority
        norm_priority = normalize_priority(new_priority)
        if norm_priority == old_priority:
            return complaint

        complaint.priority = norm_priority
        created_dt = parse_date(complaint.created_at) or now()
        hours = SLA_HOURS.get(norm_priority, 48)
        complaint.sla_deadline = (created_dt + timedelta(hours=hours)).isoformat()

        msg = f"Priority changed from {old_priority} to {norm_priority} by {user.name}."
        if reason:
            msg += f" Reason: {reason.strip()}"
        complaint.add_history(msg)
        self.save_complaint(complaint)

        p_order = {"Critical": 4, "High": 3, "Medium": 2, "Low": 1}
        if p_order.get(norm_priority, 0) < p_order.get(old_priority, 0):
            loc = self.auth_service.get_location(complaint.location_id)
            warden_id = getattr(loc, "in_charge_id", None)
            app_mgr_id = getattr(loc, "app_manager_id", None)
            alert_msg = f"Complaint {complaint.complaint_id} downgraded from {old_priority} to {norm_priority}. Reason: {reason or 'None'}"
            if warden_id:
                self.notification_service.notify(
                    warden_id, alert_msg, complaint_id=complaint.complaint_id, title="Priority Downgrade Alert"
                )
            if app_mgr_id:
                self.notification_service.notify(
                    app_mgr_id, alert_msg, complaint_id=complaint.complaint_id, title="Priority Downgrade Alert"
                )
        return complaint

    def escalate_complaint(self, complaint_id, user, reason):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")
        if not reason or not reason.strip():
            raise ValueError("Escalation reason is mandatory.")
        if complaint.status in (Complaint.CLOSED, Complaint.AUTO_CLOSED):
            raise ValueError("Closed complaints cannot be escalated.")

        u_role = (user.role or "").lower()
        if u_role == "coordinator":
            location = self.auth_service.get_location(complaint.location_id)
            if location and location.in_charge_id:
                target_id = location.in_charge_id
                target_role = "Warden"
            else:
                target_id = self.get_active_app_manager()
                target_role = "App Manager"

            complaint.assigned_to = target_id
            complaint.escalated = True
            complaint.add_history(
                f"Escalated to {target_role} by Coordinator {user.user_id}. Reason: {reason}"
            )
            self.notification_service.notify(
                target_id,
                f"Escalated complaint: {complaint_id}. Reason: {reason}",
                complaint_id=complaint_id,
                title="Complaint Escalated",
            )

        elif u_role == "location_in_charge":
            app_manager_id = self.get_active_app_manager()
            complaint.assigned_to = app_manager_id
            complaint.escalated = True
            complaint.add_history(
                f"Escalated to App Manager by Warden {user.user_id}. Reason: {reason}"
            )
            self.notification_service.notify(
                app_manager_id,
                f"Escalated complaint: {complaint_id}. Reason: {reason}",
                complaint_id=complaint_id,
                title="Complaint Escalated",
            )

        elif u_role == "app_manager":
            with self._db_conn() as conn:
                row = conn.execute(
                    "SELECT user_id FROM users WHERE role = 'administrator' AND active = 1 LIMIT 1"
                ).fetchone()
                admin_id = row["user_id"] if row else "USR_ADMIN"

            complaint.assigned_to = admin_id
            complaint.escalated = True
            complaint.add_history(
                f"Escalated to Administrator by App Manager {user.user_id}. Reason: {reason}"
            )
            self.notification_service.notify(
                admin_id,
                f"Escalated complaint: {complaint_id}. Reason: {reason}",
                complaint_id=complaint_id,
                title="Complaint Escalated",
            )
        else:
            raise PermissionError("Your role is not authorized to escalate complaints.")

        self.save_complaint(complaint)
        return complaint
