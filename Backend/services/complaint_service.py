import os
import random
from datetime import datetime, timedelta

from core.constants import (
    ACCEPT_DEADLINE_HOURS,
    CATEGORY_PRIORITY_MAP,
    INACTIVE_STATUSES,
    PRESET_PROGRESS_NOTES,
    PRIORITIES,
    SLA_ACTIVE_STATUSES,
    SLA_HOURS,
    STATUS_ASSIGNED,
    STATUS_BLOCKED,
    STATUS_IN_PROGRESS,
    STATUS_PENDING_WARDEN,
    STATUS_SUBMITTED,
    STATUS_WAITING_STUDENT,
    get_sla_hours,
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
        sla_hours = get_sla_hours(final_priority, category=category)
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
        candidate_coords = self._get_mapped_coordinators(location_id, department_id)

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

    def _get_mapped_coordinators(self, location_id, department_id):
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
        return candidate_coords

    def assign_work(self, complaint_id, coordinator_id, reason=None, actor_id=None):
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
        if not self.auth_service.is_coordinator_assigned(coordinator_id, complaint.location_id, complaint.department_id):
            raise ValueError(f"Coordinator {target_user.name} is not mapped to this location and department.")

        old_status = complaint.status
        old_assigned = complaint.assigned_to
        is_reassign = bool(old_assigned and old_assigned != coordinator_id)

        complaint.assigned_to = coordinator_id
        complaint.assigned_at = now_string()
        if complaint.status in (Complaint.SUBMITTED, Complaint.ASSIGNED):
            complaint.status = Complaint.ASSIGNED

        hist_msg = f"Assigned to coordinator {target_user.name} ({coordinator_id})."
        if is_reassign:
            hist_msg = f"Reassigned to coordinator {target_user.name} ({coordinator_id}) by {actor_id or 'admin'}."
            if reason:
                hist_msg += f" Reason: {reason}"
        complaint.add_history(hist_msg)

        try:
            self.save_complaint(complaint)
            self.notification_service.assigned(complaint_id, coordinator_id)
            if is_reassign and old_assigned:
                self.notification_service.notify(
                    old_assigned,
                    f"Complaint {complaint_id} has been reassigned to {target_user.name}." + (f" Reason: {reason}" if reason else ""),
                    complaint_id=complaint_id,
                    title="Complaint Reassigned",
                )
        except Exception as err:
            complaint.status = old_status
            complaint.assigned_to = old_assigned
            self.save_complaint(complaint)
            raise err
        return complaint

    def mark_resolved(self, complaint_id, user_id=None, notes=""):
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

        uid = getattr(user_id, "user_id", str(user_id)) if user_id else (complaint.assigned_to or "system")

        # Resolution photo & notes validation
        attachments = self.attachment_service.list_attachments(complaint_id)
        has_after_repair = any(a.get("category", "").lower() in ("after repair", "after_repair") for a in attachments)

        p = normalize_priority(complaint.priority)
        is_high_or_crit = p in ("High", "Critical")

        if is_high_or_crit:
            if not has_after_repair:
                raise ValueError("High and Critical priority complaints require a photo attachment of the completed work before resolving.")
        else:
            if not has_after_repair and not (notes or "").strip():
                raise ValueError("Resolution Notes are mandatory when no 'After Repair' image is provided.")

        # High/Critical always requires warden in-person check; Normal/Low has ~10% spot check
        if is_high_or_crit:
            requires_warden = True
            is_spot = False
        else:
            spot_rate_env = os.getenv("SPOT_CHECK_RATE")
            if spot_rate_env is not None:
                spot_rate = float(spot_rate_env)
            elif os.getenv("PYTEST_CURRENT_TEST"):
                spot_rate = 0.0
            else:
                spot_rate = 0.10
            is_spot = (getattr(self, "_spot_check_fn", None) or (lambda: random.random() < spot_rate))()
            requires_warden = is_spot

        now_ts = now_string()
        complaint.fixed_at = now_ts
        complaint.fixed_by = uid
        complaint.resolved_at = now_ts
        complaint.resolution_notes = (notes or "").strip()

        loc = self.auth_service.get_location(complaint.location_id)
        warden_id = getattr(loc, "in_charge_id", None)

        if requires_warden:
            complaint.requires_warden_check = True
            complaint.is_spot_check = is_spot
            complaint.status = Complaint.PENDING_WARDEN_VERIFICATION
            hist_msg = f"Marked fixed by {uid}."
            if is_spot:
                hist_msg += " Randomly selected for warden spot check."
            else:
                hist_msg += " Awaiting in-person warden verification."
            complaint.add_history(hist_msg)
            self.save_complaint(complaint)

            if warden_id:
                coord_u = self.auth_service.get_user(uid)
                c_name = coord_u.name if coord_u else uid
                alert_text = (
                    f"Spot check: Complaint {complaint_id} randomly selected for in-person verification."
                    if is_spot
                    else f"Complaint {complaint_id} marked fixed by {c_name}. Please verify in person."
                )
                self.notification_service.notify(
                    warden_id,
                    alert_text,
                    complaint_id=complaint_id,
                    title="Warden Verification Required",
                )
        else:
            complaint.requires_warden_check = False
            complaint.is_spot_check = False
            complaint.status = Complaint.WAITING_VERIFICATION
            complaint.student_stage_at = now_ts
            # 48 hours for student confirmation
            complaint.verification_due_at = (now() + timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")
            complaint.add_history(f"Complaint marked resolved by {uid}; waiting for student confirmation.")
            self.save_complaint(complaint)

            self.notification_service.notify(
                complaint.created_by,
                f"Your complaint {complaint_id} has been marked resolved. Please confirm within 48 hours.",
                complaint_id=complaint_id,
                title="Complaint Resolved",
            )

        try:
            from utils.websocket_manager import manager
            manager.push_sync("coordinator", {
                "event": "complaint_resolved",
                "complaint_id": complaint_id,
                "status": complaint.status,
                "requires_warden_check": complaint.requires_warden_check,
            })
            manager.push_sync(complaint.created_by, {
                "event": "complaint_resolved",
                "complaint_id": complaint_id,
                "status": complaint.status,
            })
        except Exception:
            pass

        return complaint

    def warden_verify(self, complaint_id, warden_user, verdict, notes=""):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")

        warden_id = getattr(warden_user, "user_id", str(warden_user))
        warden_role = getattr(warden_user, "role", "").lower()
        warden_name = getattr(warden_user, "name", warden_id)

        # Self-verification guard
        if warden_id == complaint.assigned_to or warden_id == complaint.created_by:
            raise PermissionError("You cannot verify a complaint you worked on or filed.")

        # Permission check
        if warden_role != "administrator":
            loc = self.auth_service.get_location(complaint.location_id)
            loc_in_charge = getattr(loc, "in_charge_id", None)
            user_loc = getattr(warden_user, "location_id", None)
            if warden_id != loc_in_charge and user_loc != complaint.location_id:
                raise PermissionError("Only the warden of this location or an administrator can verify.")

        if complaint.status not in (Complaint.PENDING_WARDEN_VERIFICATION, "Pending Warden Verification"):
            raise ValueError("Complaint is not pending warden verification.")

        v_norm = (verdict or "").strip()
        now_ts = now_string()
        if v_norm.lower() in ("verified", "fixed"):
            complaint.warden_verified_at = now_ts
            complaint.warden_verified_by = warden_id
            complaint.warden_verdict = "Verified"
            complaint.warden_notes = (notes or "").strip()
            complaint.status = Complaint.WAITING_VERIFICATION
            complaint.student_stage_at = now_ts
            complaint.verification_due_at = (now() + timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S")
            complaint.add_history(f"Verified in person by Warden {warden_name}: {notes or 'No notes'}")
            self.save_complaint(complaint)

            self.notification_service.notify(
                complaint.created_by,
                f"Warden {warden_name} has verified the fix on complaint {complaint_id}. Please confirm to close.",
                complaint_id=complaint_id,
                title="Warden Verified Fix",
            )
        elif v_norm.lower() in ("not fixed", "not_fixed", "rejected"):
            complaint.warden_verified_at = now_ts
            complaint.warden_verified_by = warden_id
            complaint.warden_verdict = "Not Fixed"
            complaint.warden_notes = (notes or "").strip()
            complaint.status = Complaint.IN_PROGRESS
            complaint.add_history(f"Warden {warden_name} inspected in person and found issue NOT fixed: {notes or 'No notes'}")
            self.save_complaint(complaint)

            if complaint.assigned_to:
                self.notification_service.notify(
                    complaint.assigned_to,
                    f"RE-WORK REQUIRED: Warden {warden_name} inspected complaint {complaint_id} and reported it not fixed: {notes or 'No notes'}",
                    complaint_id=complaint_id,
                    title="Re-work Required",
                )
        else:
            raise ValueError("Verdict must be 'Verified' or 'Not Fixed'.")

        try:
            from utils.websocket_manager import manager
            event_payload = {
                "event": "warden_verification_completed",
                "complaint_id": complaint_id,
                "status": complaint.status,
                "verdict": complaint.warden_verdict,
            }
            manager.push_sync("coordinator", event_payload)
            manager.push_sync(complaint.created_by, event_payload)
        except Exception:
            pass

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
        if complaint.status not in (
            Complaint.WAITING_VERIFICATION,
            "Waiting for Verification",
            "Waiting For Verification",
            "Resolved",
        ):
            raise ValueError("Complaint is not waiting for verification.")

        uid = getattr(user, "user_id", str(user))
        u_role = getattr(user, "role", "").lower()
        u_name = getattr(user, "name", uid)

        if u_role != "administrator":
            allowed_creators = {complaint.created_by}
            if getattr(user, "email", None):
                allowed_creators.add(user.email)
            if uid not in allowed_creators:
                raise PermissionError("Only the student who filed the complaint or an administrator can close it.")

        now_ts = now_string()
        complaint.status = Complaint.CLOSED
        complaint.closed_at = now_ts
        complaint.closed_by = uid
        complaint.verification_reports.append({"by": uid, "result": "Fixed", "at": now_ts})
        complaint.add_history(f"Verified and closed by {u_name}.")
        self.save_complaint(complaint)

        # Notify coordinator and warden
        if complaint.assigned_to:
            self.notification_service.notify(
                complaint.assigned_to,
                f"Complaint {complaint_id} confirmed fixed and closed by student.",
                complaint_id=complaint_id,
                title="Complaint Closed",
            )
        loc = self.auth_service.get_location(complaint.location_id)
        warden_id = getattr(loc, "in_charge_id", None)
        if warden_id and warden_id != uid:
            self.notification_service.notify(
                warden_id,
                f"Complaint {complaint_id} verified and closed by student.",
                complaint_id=complaint_id,
                title="Complaint Closed",
            )

        try:
            from utils.websocket_manager import manager
            manager.push_sync("coordinator", {
                "event": "complaint_closed",
                "complaint_id": complaint_id,
                "status": "Closed",
            })
        except Exception:
            pass

        return complaint

    def report_not_fixed(self, complaint_id, user, reason):
        return self.reopen_complaint(complaint_id, user, reason)

    def reopen_complaint(self, complaint_id, user, reason):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")

        uid = getattr(user, "user_id", str(user))
        u_role = getattr(user, "role", "").lower()
        u_name = getattr(user, "name", uid)

        if u_role != "administrator":
            allowed_creators = {complaint.created_by}
            if getattr(user, "email", None):
                allowed_creators.add(user.email)
            if uid not in allowed_creators:
                raise PermissionError("Only the student who filed the complaint can reopen it.")

        valid_status = False
        if complaint.status in (
            Complaint.WAITING_VERIFICATION,
            "Waiting for Verification",
            "Waiting For Verification",
            "Resolved",
        ):
            valid_status = True
        elif complaint.status in (Complaint.CLOSED, Complaint.AUTO_CLOSED):
            closed_dt = parse_date(complaint.closed_at)
            if closed_dt and (now() - closed_dt).total_seconds() <= 48 * 3600:
                valid_status = True
            elif not closed_dt:
                valid_status = True

        if not valid_status:
            raise ValueError("Complaint can only be reopened when waiting for verification or within 48 hours of closing.")

        complaint.reopen_count = int(getattr(complaint, "reopen_count", 0)) + 1
        complaint.verification_due_at = None
        complaint.student_stage_at = None
        complaint.auto_close_reminded = False

        loc = self.auth_service.get_location(complaint.location_id)
        warden_id = getattr(loc, "in_charge_id", None)

        if complaint.reopen_count < 3:
            complaint.status = Complaint.IN_PROGRESS
            complaint.add_history(f"Reopened by student {u_name} (reopen #{complaint.reopen_count}): {reason}")
            self.save_complaint(complaint)

            if complaint.assigned_to:
                self.notification_service.notify(
                    complaint.assigned_to,
                    f"Complaint {complaint_id} reopened by student (reopen #{complaint.reopen_count}): {reason}",
                    complaint_id=complaint_id,
                    title="Complaint Reopened",
                )
            if warden_id:
                self.notification_service.notify(
                    warden_id,
                    f"Complaint {complaint_id} in your location was reopened by student (reopen #{complaint.reopen_count}): {reason}",
                    complaint_id=complaint_id,
                    title="Complaint Reopened",
                )
            event_name = "complaint_reopened"
        else:
            complaint.status = "Admin Review"
            complaint.admin_review_reason = f"Exceeded maximum reopens (3). Disputed between student and coordinator: {reason}"
            complaint.add_history("Complaint escalated to Admin Review after 3 reopens.")
            self.save_complaint(complaint)

            for admin_u in self.auth_service.list_users(role="administrator"):
                if admin_u.active and not getattr(admin_u, "is_deleted", False):
                    self.notification_service.notify(
                        admin_u.user_id,
                        f"DISPUTED TICKET: Complaint {complaint_id} has been reopened 3 times. Requires administrator intervention.",
                        complaint_id=complaint_id,
                        title="Disputed Ticket (Admin Review)",
                    )
            self.notification_service.notify(
                complaint.created_by,
                "Your complaint has reached the maximum reopens and is now under Administrator review.",
                complaint_id=complaint_id,
                title="Under Admin Review",
            )
            if complaint.assigned_to:
                self.notification_service.notify(
                    complaint.assigned_to,
                    f"Complaint {complaint_id} reached 3 reopens and escalated to Admin Review.",
                    complaint_id=complaint_id,
                    title="Escalated to Admin Review",
                )
            if warden_id:
                self.notification_service.notify(
                    warden_id,
                    f"Complaint {complaint_id} escalated to Admin Review.",
                    complaint_id=complaint_id,
                    title="Escalated to Admin Review",
                )
            event_name = "complaint_admin_review"

        try:
            from utils.websocket_manager import manager
            manager.push_sync("coordinator", {
                "event": event_name,
                "complaint_id": complaint_id,
                "status": complaint.status,
                "reopen_count": complaint.reopen_count,
            })
            manager.push_sync(complaint.created_by, {
                "event": event_name,
                "complaint_id": complaint_id,
                "status": complaint.status,
            })
        except Exception:
            pass

        return complaint

    def admin_decision(self, complaint_id, admin_user, decision, notes="", reassign_to=None):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")

        admin_id = getattr(admin_user, "user_id", str(admin_user))
        admin_name = getattr(admin_user, "name", admin_id)

        if complaint.status != "Admin Review":
            raise ValueError("Complaint is not in Admin Review status.")

        d_norm = (decision or "").strip()
        loc = self.auth_service.get_location(complaint.location_id)
        warden_id = getattr(loc, "in_charge_id", None)
        now_ts = now_string()

        if d_norm.lower() == "close":
            complaint.status = Complaint.CLOSED
            complaint.closed_at = now_ts
            complaint.closed_by = admin_id
            complaint.admin_decision = f"Closed: {notes}"
            complaint.admin_decided_by = admin_id
            complaint.admin_decided_at = now_ts
            complaint.add_history(f"Admin Review decision by {admin_name}: Closed. Notes: {notes}")
            self.save_complaint(complaint)

            self.notification_service.notify(
                complaint.created_by,
                f"Your complaint {complaint_id} was reviewed and closed by Administrator: {notes}",
                complaint_id=complaint_id,
                title="Admin Decision: Closed",
            )
            if complaint.assigned_to:
                self.notification_service.notify(
                    complaint.assigned_to,
                    f"Complaint {complaint_id} closed by Administrator: {notes}",
                    complaint_id=complaint_id,
                    title="Admin Decision: Closed",
                )
            if warden_id:
                self.notification_service.notify(
                    warden_id,
                    f"Complaint {complaint_id} closed by Administrator: {notes}",
                    complaint_id=complaint_id,
                    title="Admin Decision: Closed",
                )
        elif d_norm.lower() == "reopen":
            complaint.status = Complaint.IN_PROGRESS
            if reassign_to:
                new_coord = self.auth_service.get_user(reassign_to)
                if not new_coord or (new_coord.role or "").lower() != "coordinator":
                    raise ValueError("Reassign target must be a valid coordinator.")
                complaint.assigned_to = reassign_to
                complaint.assigned_at = now_ts

            complaint.admin_decision = f"Reopened: {notes}"
            complaint.admin_decided_by = admin_id
            complaint.admin_decided_at = now_ts
            complaint.add_history(f"Admin Review decision by {admin_name}: Reopened. Assigned to: {complaint.assigned_to}. Notes: {notes}")
            self.save_complaint(complaint)

            self.notification_service.notify(
                complaint.created_by,
                f"Your complaint {complaint_id} has been reopened following Administrator review.",
                complaint_id=complaint_id,
                title="Admin Decision: Reopened",
            )
            if complaint.assigned_to:
                self.notification_service.notify(
                    complaint.assigned_to,
                    f"Complaint {complaint_id} reopened and assigned to you by Administrator: {notes}",
                    complaint_id=complaint_id,
                    title="Admin Decision: Reopened",
                )
            if warden_id:
                self.notification_service.notify(
                    warden_id,
                    f"Complaint {complaint_id} reopened by Administrator.",
                    complaint_id=complaint_id,
                    title="Admin Decision: Reopened",
                )
        else:
            raise ValueError("Decision must be 'Close' or 'Reopen'.")

        try:
            from utils.websocket_manager import manager
            manager.push_sync("coordinator", {
                "event": "complaint_admin_decision",
                "complaint_id": complaint_id,
                "status": complaint.status,
                "admin_decision": complaint.admin_decision,
            })
        except Exception:
            pass

        return complaint

    def get_coordinator_stats(self):
        coordinators = self.auth_service.list_users(role="coordinator")
        all_complaints = self.list_all(include_archived=True)
        current_time = now()
        thirty_days_ago = current_time - timedelta(days=30)

        stats = []
        for c in coordinators:
            cid = c.user_id
            c_complaints = [comp for comp in all_complaints if comp.assigned_to == cid]

            assigned_count = sum(1 for comp in c_complaints if comp.status == Complaint.ASSIGNED)
            in_prog_count = sum(1 for comp in c_complaints if comp.status == Complaint.IN_PROGRESS)

            resolved_30d = 0
            res_hours_list = []
            reopen_count_total = 0

            for comp in c_complaints:
                if comp.reopen_count and comp.reopen_count > 0:
                    reopen_count_total += 1

                res_ts = parse_date(getattr(comp, "fixed_at", None) or comp.resolved_at)
                if res_ts and res_ts >= thirty_days_ago:
                    resolved_30d += 1

                created_ts = parse_date(comp.created_at)
                if created_ts and res_ts and res_ts >= created_ts:
                    res_hours = (res_ts - created_ts).total_seconds() / 3600.0
                    res_hours_list.append(res_hours)

            avg_res_hrs = round(sum(res_hours_list) / len(res_hours_list), 1) if res_hours_list else 0.0
            reopen_rate = round(reopen_count_total / len(c_complaints), 2) if c_complaints else 0.0

            overdue_count = 0
            for comp in c_complaints:
                if comp.status in (Complaint.ASSIGNED, Complaint.IN_PROGRESS, STATUS_BLOCKED):
                    sla_deadline_dt = parse_date(getattr(comp, "sla_deadline", None))
                    if sla_deadline_dt and current_time > sla_deadline_dt:
                        overdue_count += 1

            stats.append({
                "coordinator_id": cid,
                "name": c.name,
                "email": c.email,
                "assigned_count": assigned_count,
                "in_progress_count": in_prog_count,
                "resolved_last_30_days": resolved_30d,
                "avg_resolution_hours": avg_res_hrs,
                "reopen_rate": reopen_rate,
                "overdue_count": overdue_count,
            })
        return stats


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

                # 50% and 90% SLA Reminders to coordinator
                created_dt = parse_date(complaint.created_at) or current_time
                total_seconds = (sla_deadline_dt - created_dt).total_seconds()
                if total_seconds > 0 and current_time < sla_deadline_dt:
                    ratio = (current_time - created_dt).total_seconds() / total_seconds
                    if ratio >= 0.50 and int(getattr(complaint, "sla_reminders_sent", 0) or 0) < 1:
                        complaint.sla_reminders_sent = 1
                        complaint.add_history("50% of SLA time elapsed. Reminder sent.")
                        if complaint.assigned_to:
                            self.notification_service.notify(
                                complaint.assigned_to,
                                f"SLA 50% Reminder: Complaint {complaint.complaint_id} ({complaint.priority}) is halfway through its SLA window.",
                                complaint_id=complaint.complaint_id,
                                title="SLA 50% Reminder",
                            )
                        changed = True
                    if ratio >= 0.90 and int(getattr(complaint, "sla_reminders_sent", 0) or 0) < 2:
                        complaint.sla_reminders_sent = 2
                        complaint.add_history("90% of SLA time elapsed. Urgency reminder sent.")
                        if complaint.assigned_to:
                            self.notification_service.notify(
                                complaint.assigned_to,
                                f"SLA 90% Warning: Complaint {complaint.complaint_id} ({complaint.priority}) is approaching its deadline ({complaint.sla_deadline}).",
                                complaint_id=complaint.complaint_id,
                                title="SLA 90% Urgency Warning",
                            )
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
                            loc = _get_loc(complaint.location_id)
                            warden_id = getattr(loc, "in_charge_id", None)
                            if warden_id:
                                self.notification_service.notify(
                                    warden_id,
                                    f"Complaint {complaint.complaint_id} went unclaimed after {accept_hours}h; auto-assigned to coordinator {least_loaded}.",
                                    complaint_id=complaint.complaint_id,
                                    title="Unclaimed Complaint Auto-Assigned",
                                )
                            changed = True

            # Blocked status monitoring: if blocked >72h or past blocked_until without update
            if complaint.status == STATUS_BLOCKED:
                blocked_dt = parse_date(getattr(complaint, "blocked_at", None) or complaint.updated_at)
                until_dt = parse_date(getattr(complaint, "blocked_until", None))
                is_past_72h = bool(blocked_dt and current_time > blocked_dt + timedelta(hours=72))
                is_past_until = bool(until_dt and current_time > until_dt)
                if (is_past_72h or is_past_until) and not getattr(complaint, "blocked_alerted", False):
                    complaint.blocked_alerted = True
                    loc = _get_loc(complaint.location_id)
                    warden_id = getattr(loc, "in_charge_id", None)
                    app_mgr_id = getattr(loc, "app_manager_id", None) or self.get_active_app_manager()
                    reason = getattr(complaint, "blocked_reason", "None specified")
                    alert_text = f"BLOCKED DELAY: Complaint {complaint.complaint_id} has been blocked for >72h or past expected date. Reason: {reason}"
                    if warden_id:
                        self.notification_service.notify(
                            warden_id, alert_text, complaint_id=complaint.complaint_id, title="Blocked Delay Alert"
                        )
                    if app_mgr_id:
                        self.notification_service.notify(
                            app_mgr_id, alert_text, complaint_id=complaint.complaint_id, title="Blocked Delay Alert"
                        )
                    complaint.add_history("Blocked duration exceeded threshold. Alerted Warden and App Manager.")
                    changed = True

            # 3. Complaints pending warden verification (>24h reminder to warden, >48h to App Manager)
            if complaint.status in (Complaint.PENDING_WARDEN_VERIFICATION, "Pending Warden Verification"):
                fixed_dt = parse_date(getattr(complaint, "fixed_at", None) or complaint.resolved_at or complaint.updated_at)
                loc = _get_loc(complaint.location_id)
                warden_id = getattr(loc, "in_charge_id", None)
                app_mgr_id = getattr(loc, "app_manager_id", None) or self.get_active_app_manager()

                if not warden_id and not getattr(complaint, "no_warden_alerted", False):
                    complaint.no_warden_alerted = True
                    loc_name = loc.name if loc else complaint.location_id
                    self.notification_service.notify(
                        app_mgr_id,
                        f"SETUP GAP: Location {loc_name} has no warden assigned. Complaint {complaint.complaint_id} is pending verification. Please assign a warden.",
                        complaint_id=complaint.complaint_id,
                        title="Setup Gap: No Warden Assigned",
                    )
                    complaint.add_history(f"Setup gap: Location {loc_name} has no warden. Alerted App Manager.")
                    changed = True

                if fixed_dt:
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

            # 4. Auto-close background check for Waiting for Verification tickets
            if complaint.status in (Complaint.WAITING_VERIFICATION, "Waiting for Verification", "Waiting For Verification"):
                due_dt = parse_date(complaint.verification_due_at)
                if due_dt:
                    # 24h reminder before auto-close
                    if current_time > (due_dt - timedelta(hours=24)) and not getattr(complaint, "auto_close_reminded", False):
                        complaint.auto_close_reminded = True
                        self.notification_service.notify(
                            complaint.created_by,
                            f"Reminder: Complaint {complaint.complaint_id} will auto-close in 24 hours. Please confirm if fixed.",
                            complaint_id=complaint.complaint_id,
                            title="Auto-Close Reminder",
                        )
                        changed = True

                    # Expired -> Auto close
                    if current_time > due_dt:
                        complaint.status = Complaint.AUTO_CLOSED
                        complaint.auto_closed = True
                        complaint.closed_at = current_time.strftime("%Y-%m-%d %H:%M:%S")
                        complaint.closed_by = "system"
                        complaint.add_history("Auto-closed after 48 hours without student response.")
                        self.notification_service.notify(
                            complaint.created_by,
                            f"Complaint {complaint.complaint_id} was automatically closed after 48h of inactivity. You may reopen within 48h if not fixed.",
                            complaint_id=complaint.complaint_id,
                            title="Complaint Auto-Closed",
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

        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")

        if (coord_user.role or "").lower() == "coordinator":
            if not self.auth_service.is_coordinator_assigned(
                coordinator_id, complaint.location_id, complaint.department_id
            ):
                raise PermissionError("You are not mapped to handle complaints for this location and department.")

        now_str = now_string()
        with self.repository._connect() as conn:
            # Case 1: unassigned ticket in queue
            cursor = conn.execute(
                """
                UPDATE complaints
                SET assigned_to = ?, status = 'In Progress', assigned_at = ?, started_at = ?, updated_at = ?
                WHERE complaint_id = ? AND (assigned_to IS NULL OR assigned_to = '')
                """,
                (coordinator_id, now_str, now_str, now_str, complaint_id),
            )
            if cursor.rowcount == 0:
                # Case 2: ticket was already assigned directly to this coordinator (status Assigned)
                cursor = conn.execute(
                    """
                    UPDATE complaints
                    SET status = 'In Progress', started_at = CASE WHEN started_at IS NULL THEN ? ELSE started_at END, updated_at = ?
                    WHERE complaint_id = ? AND assigned_to = ? AND status IN ('Assigned', 'Submitted')
                    """,
                    (now_str, now_str, complaint_id, coordinator_id),
                )
                if cursor.rowcount == 0:
                    row = conn.execute("SELECT status, assigned_to FROM complaints WHERE complaint_id = ?", (complaint_id,)).fetchone()
                    if not row:
                        raise ValueError("Complaint not found.")
                    current_assignee = row["assigned_to"]
                    if current_assignee == coordinator_id and row["status"] == "In Progress":
                        pass
                    else:
                        other_user = self.auth_service.get_user(current_assignee) if current_assignee else None
                        name = other_user.name if other_user else (current_assignee or "another coordinator")
                        raise ComplaintConflictError(f"Complaint has already been accepted by {name}.")

        complaint = self.get_complaint(complaint_id)
        if complaint:
            complaint.add_history(f"Accepted by coordinator {coord_user.name} ({coordinator_id}). Status is In Progress.")
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

    def record_progress(self, complaint_id, coordinator_id, note=None, photo_url=None, note_code=None):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")
        if complaint.assigned_to != coordinator_id:
            raise ValueError("You can only update complaints assigned to you.")

        final_note = (note or "").strip()
        if note_code:
            code_upper = note_code.strip().upper()
            if code_upper in PRESET_PROGRESS_NOTES:
                complaint.last_progress_code = code_upper
                if not final_note:
                    final_note = PRESET_PROGRESS_NOTES[code_upper]
            else:
                complaint.last_progress_code = note_code

        if not final_note:
            raise ValueError("Progress note or preset note code is required.")

        msg = f"Progress update: {final_note}"
        if note_code:
            msg += f" [{note_code}]"
        if photo_url:
            msg += " (photo attached)"
        complaint.add_history(msg)
        self.save_complaint(complaint)

        self.notification_service.notify(
            complaint.created_by,
            f"Update on your complaint {complaint.complaint_id}: {final_note}",
            complaint_id=complaint.complaint_id,
            title="Complaint Progress Update",
        )
        return complaint

    def correct_location(self, complaint_id, correct_location_id, user, note=None):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")
        new_loc = self.auth_service.get_location(correct_location_id)
        if not new_loc:
            raise ValueError("Target location not found.")
        if not getattr(new_loc, "active", True):
            raise ValueError("Target location is inactive.")

        old_loc_id = complaint.location_id
        old_loc = self.auth_service.get_location(old_loc_id)
        old_loc_name = old_loc.name if old_loc else old_loc_id
        new_loc_name = new_loc.name or correct_location_id

        complaint.location_id = correct_location_id
        complaint.wrong_location_corrected_at = now_string()
        complaint.wrong_location_corrections = int(getattr(complaint, "wrong_location_corrections", 0) or 0) + 1

        u_name = getattr(user, "name", str(getattr(user, "user_id", user)))
        hist_msg = f"Location corrected from {old_loc_name} to {new_loc_name} by {u_name}."
        if note and note.strip():
            hist_msg += f" Note: {note.strip()}"
        complaint.add_history(hist_msg)

        # Re-route according to new location & department
        candidate_coords = self._get_mapped_coordinators(correct_location_id, complaint.department_id)
        if len(candidate_coords) == 1:
            coord_id = candidate_coords[0]
            complaint.assigned_to = coord_id
            complaint.status = Complaint.ASSIGNED
            complaint.assigned_at = now_string()
            complaint.auto_assigned = True
            complaint.team_location_id = None
            complaint.team_department_id = None
            complaint.add_history(f"Auto-assigned to coordinator {coord_id} for new location.")
            self.notification_service.notify(
                coord_id,
                f"Complaint {complaint.complaint_id} relocated to {new_loc_name} assigned to you.",
                complaint_id=complaint.complaint_id,
                title="Complaint Relocated & Assigned",
            )
        elif len(candidate_coords) >= 2:
            complaint.assigned_to = None
            complaint.status = Complaint.SUBMITTED
            complaint.team_location_id = correct_location_id
            complaint.team_department_id = complaint.department_id
            complaint.add_history("Multiple coordinators available for new location. Placed in accept queue.")
            for cid in candidate_coords:
                self.notification_service.notify(
                    cid,
                    f"Work available in {new_loc_name}: {complaint.title or complaint.category} ({complaint.priority}).",
                    complaint_id=complaint.complaint_id,
                    title="Work Available in Queue",
                )
        else:
            complaint.assigned_to = None
            complaint.status = Complaint.SUBMITTED
            complaint.team_location_id = None
            complaint.team_department_id = None
            complaint.add_history("No coordinator assigned for new location/department. Placed in queue.")
            dept_obj = self.auth_service.get_department(complaint.department_id)
            dept_label = dept_obj.name if dept_obj else complaint.department_id
            alert_msg = f"Complaint {complaint.complaint_id} moved to {new_loc_name}/{dept_label} has no coordinator assigned."
            warden_id = getattr(new_loc, "in_charge_id", None)
            if warden_id:
                self.notification_service.notify(
                    warden_id, alert_msg, complaint_id=complaint.complaint_id, title="Coverage Gap Alert"
                )
            app_mgr_id = getattr(new_loc, "app_manager_id", None)
            if app_mgr_id:
                self.notification_service.notify(
                    app_mgr_id, alert_msg, complaint_id=complaint.complaint_id, title="Coverage Gap Alert"
                )
            for admin_u in self.auth_service.list_users(role="administrator"):
                if admin_u.active and not getattr(admin_u, "is_deleted", False):
                    self.notification_service.notify(
                        admin_u.user_id, alert_msg, complaint_id=complaint.complaint_id, title="Coverage Gap Alert"
                    )

        # Notify new location warden
        new_warden_id = getattr(new_loc, "in_charge_id", None)
        if new_warden_id:
            self.notification_service.notify(
                new_warden_id,
                f"Complaint {complaint.complaint_id} was relocated to your location ({new_loc_name}).",
                complaint_id=complaint.complaint_id,
                title="Complaint Relocated to Your Location",
            )

        # Notify student submitter
        self.notification_service.notify(
            complaint.created_by,
            f"The location for your complaint {complaint.complaint_id} was updated to {new_loc_name}.",
            complaint_id=complaint.complaint_id,
            title="Complaint Location Updated",
        )

        self._enrich_sla(complaint)
        self.save_complaint(complaint)
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
