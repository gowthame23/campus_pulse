from datetime import timedelta

from models.complaint import Complaint
from models.location_in_charge import LocationInCharge
from models.student import Student
from storage.sqlite_repository import SQLiteRepository
from utils.helper import now, parse_date


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
        priority = "Medium"
        if issue_id:
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            issue_row = conn.execute("SELECT * FROM department_issues WHERE issue_id = ?", (issue_id,)).fetchone()
            conn.close()
            if issue_row:
                iss_dict = dict(issue_row)
                if iss_dict.get("department_id") != department_id:
                    raise ValueError("Selected issue does not belong to the chosen department.")
                if iss_dict.get("active") == 0:
                    raise ValueError("Selected issue is inactive.")
                priority = iss_dict.get("default_priority") or "Medium"

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

        # 6. Create Complaint instance
        complaint = Complaint(
            user.user_id,
            user.role,
            location_id,
            department_id,
            complaint_type,
            description,
            attachment_url=attachment_url,
            priority=priority,
            category=category,
            visibility_type=visibility_type,
            title=title,
        )

        complaint.status = Complaint.SUBMITTED
        complaint.assigned_to = None
        complaint.add_history("Complaint submitted.")

        self.notification_service.notify(
            user.user_id,
            f"Your complaint {complaint.complaint_id} has been submitted successfully.",
            complaint_id=complaint.complaint_id,
            title="Complaint Submitted",
        )

        # Section 11: Notify only students associated with the complaint's location
        if str(complaint.visibility_type).capitalize() in ("Public", "Community"):
            loc = self.auth_service.get_location(location_id)
            loc_name = loc.name if loc else location_id
            loc_id_clean = loc.location_id if loc else location_id

            all_students = self.auth_service.list_users(role="student")
            for st in all_students:
                if st.user_id == user.user_id:
                    continue
                is_associated = (
                    st.location_id == loc_id_clean
                    or (getattr(st, "hostel", None) and str(st.hostel).strip().lower() == loc_name.strip().lower())
                    or (getattr(st, "block", None) and str(st.block).strip().lower() == loc_name.strip().lower())
                )
                if is_associated:
                    self.notification_service.notify(
                        st.user_id,
                        f"Notice: A public complaint '{complaint.title or complaint.category}' was reported in your location ({loc_name}).",
                        complaint_id=complaint.complaint_id,
                        title="Public Complaint in Your Area",
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
        old_status = complaint.status
        old_assigned = complaint.assigned_to
        complaint.assign(coordinator_id)
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

        # Only allow resolving from In Progress status
        if complaint.status != Complaint.IN_PROGRESS:
            raise ValueError("Complaint must be In Progress before it can be resolved.")

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

    def apply_automatic_rules(self, complaints=None):
        complaints = complaints or self._load_complaints()
        changed = False
        current_time = now()
        dept_cache = {}
        for complaint in complaints:
            if complaint.status == Complaint.WAITING_VERIFICATION:
                due_at = parse_date(complaint.verification_due_at)
                if due_at and current_time > due_at:
                    complaint.auto_close()
                    changed = True
            if complaint.status not in (
                Complaint.CLOSED,
                Complaint.AUTO_CLOSED,
                Complaint.RESOLVED,
                Complaint.WAITING_VERIFICATION,
            ):
                if complaint.department_id not in dept_cache:
                    dept_cache[complaint.department_id] = self.auth_service.get_department(
                        complaint.department_id
                    )
                department = dept_cache[complaint.department_id]
                created_at = parse_date(complaint.created_at)
                if department and created_at:
                    due_date = created_at + timedelta(days=department.sla_days)
                    days_overdue = (current_time - due_date).days
                    if days_overdue >= 0:
                        has_notified_coord = any(
                            "SLA exceeded; notified coordinator" in h["message"]
                            for h in complaint.history
                        )
                        if not has_notified_coord:
                            complaint.add_history("SLA exceeded; notified coordinator.")
                            coordinator_id = department.coordinator_id or "Coordinator"
                            self.notification_service.notify(
                                coordinator_id,
                                f"Overdue alert: Complaint {complaint.complaint_id} is past due.",
                                complaint_id=complaint.complaint_id,
                                title="SLA Overdue Alert",
                            )
                            changed = True
                    if days_overdue >= 2:
                        if not complaint.escalated:
                            complaint.escalated = True
                            complaint.add_history(
                                "SLA exceeded by 2+ days; escalated to App Manager."
                            )
                            self.notification_service.sla_exceeded(
                                complaint.complaint_id
                            )
                            changed = True
                    if days_overdue >= 4:
                        if not complaint.admin_notified:
                            complaint.admin_notified = True
                            complaint.add_history(
                                "SLA exceeded by 4+ days; escalated to Administrator."
                            )
                            self.notification_service.notify(
                                "Administrator",
                                f"CRITICAL: prolonged delay for complaint {complaint.complaint_id}. Escalated to Admin.",
                                complaint_id=complaint.complaint_id,
                                title="SLA Critical Escalation",
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
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")
        if complaint.status not in (
            Complaint.PENDING,
            Complaint.SUBMITTED,
            Complaint.REOPENED,
        ):
            raise ValueError(
                "Only Pending, Submitted, or Reopened complaints can be accepted."
            )
        complaint.status = Complaint.IN_PROGRESS
        if not complaint.assigned_to:
            complaint.assigned_to = coordinator_id
        complaint.add_history(f"Accepted and work started by staff {coordinator_id}.")
        self.save_complaint(complaint)
        return complaint

    def start_work(self, complaint_id, coordinator_id):
        complaint = self.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")
        if complaint.status not in (Complaint.ASSIGNED, Complaint.REOPENED):
            raise ValueError(
                "Complaint must be Accepted (Assigned) or Reopened before starting work."
            )
        if complaint.assigned_to != coordinator_id:
            raise ValueError("You can only work on complaints assigned to you.")

        complaint.status = Complaint.IN_PROGRESS
        complaint.add_history("Work started by Coordinator.")
        self.save_complaint(complaint)
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
