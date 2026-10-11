import sqlite3
from pathlib import Path

from core.constants import INACTIVE_STATUSES, TERMINAL_STATUSES

_INACTIVE_SQL = ", ".join(f"'{s}'" for s in INACTIVE_STATUSES)
_TERMINAL_SQL = ", ".join(f"'{s}'" for s in TERMINAL_STATUSES)


class DashboardService:
    def __init__(self, db_path="storage/campus_pulse.db"):
        self.db_path = Path(db_path)

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_dashboard(self, user_id, role):
        role_lower = (role or "").lower()
        if role_lower == "student":
            return self.get_student_dashboard(user_id)
        elif role_lower in ("coordinator", "location_in_charge"):
            return self.get_coordinator_dashboard(user_id)
        elif role_lower == "warden":
            return self.get_warden_dashboard(user_id)
        elif role_lower in ("supervisor", "app_manager"):
            return self.get_supervisor_dashboard(user_id)
        elif role_lower == "administrator":
            return self.get_admin_dashboard(user_id)
        else:
            return self.get_student_dashboard(user_id)

    # ==========================================
    # 1. STUDENT DASHBOARD
    # ==========================================
    def get_student_dashboard(self, user_id):
        with self._connect() as conn:
            # Active Complaints
            act_comp = conn.execute(
                f"SELECT COUNT(*) FROM complaints WHERE created_by = ? AND status NOT IN ({_INACTIVE_SQL})",
                (user_id,)
            ).fetchone()[0]

            # Public Complaints Joined / Affected
            pub_comp = conn.execute(
                f"SELECT COUNT(*) FROM complaints WHERE (visibility_type = 'Public' OR visibility_type = 1) AND status NOT IN ({_TERMINAL_SQL})",
            ).fetchone()[0]

            # Lost Items reported
            lost_cnt = conn.execute(
                "SELECT COUNT(*) FROM lost_found_items WHERE reported_by = ? AND report_type IN ('Lost', 'LOST') AND status != 'Returned' AND status != 'Deleted' AND (is_deleted = 0 OR is_deleted IS NULL)",
                (user_id,)
            ).fetchone()[0]

            # Found Items reported
            found_cnt = conn.execute(
                "SELECT COUNT(*) FROM lost_found_items WHERE reported_by = ? AND report_type IN ('Found', 'FOUND') AND status != 'Returned' AND status != 'Deleted' AND (is_deleted = 0 OR is_deleted IS NULL)",
                (user_id,)
            ).fetchone()[0]

            # Unread Notifications
            notif_cnt = conn.execute(
                "SELECT COUNT(*) FROM notifications WHERE (receiver_id = ? OR receiver_id = 'all') AND is_read = 0 AND (is_deleted = 0 OR is_deleted IS NULL)",
                (user_id,)
            ).fetchone()[0]

            # Announcements Count
            ann_cnt = conn.execute(
                "SELECT COUNT(*) FROM announcements WHERE status = 'Published' AND (is_deleted = 0 OR is_deleted IS NULL)",
            ).fetchone()[0]

            # Recent Complaints (Top 5)
            recent_rows = conn.execute(
                "SELECT complaint_id, title, status, updated_at FROM complaints WHERE created_by = ? ORDER BY updated_at DESC LIMIT 5",
                (user_id,)
            ).fetchall()
            recent_complaints = [dict(r) for r in recent_rows]

            # Recent Notifications (Top 5)
            notif_rows = conn.execute(
                "SELECT notification_id, title, message, priority, created_at, is_read FROM notifications WHERE (receiver_id = ? OR receiver_id = 'all') AND (is_deleted = 0 OR is_deleted IS NULL) ORDER BY created_at DESC LIMIT 5",
                (user_id,)
            ).fetchall()
            recent_notifications = [dict(r) for r in notif_rows]

            # Announcements (Top 5 pinned first)
            ann_rows = conn.execute(
                "SELECT announcement_id, title, summary, priority, is_pinned, created_at FROM announcements WHERE status = 'Published' AND (is_deleted = 0 OR is_deleted IS NULL) ORDER BY is_pinned DESC, created_at DESC LIMIT 5",
            ).fetchall()
            announcements = [dict(r) for r in ann_rows]

            return {
                "role": "student",
                "cards": {
                    "active_complaints": act_comp,
                    "public_complaints": pub_comp,
                    "lost_items": lost_cnt,
                    "found_items": found_cnt,
                    "unread_notifications": notif_cnt,
                    "announcements": ann_cnt,
                },
                "lost_found_summary": {
                    "lost_reports": lost_cnt,
                    "found_reports": found_cnt,
                    "pending_claims": 0,
                    "active_conversations": 0,
                },
                "recent_complaints": recent_complaints,
                "recent_notifications": recent_notifications,
                "announcements": announcements,
            }

    # ==========================================
    # 2. COORDINATOR DASHBOARD
    # ==========================================
    def get_coordinator_dashboard(self, user_id):
        with self._connect() as conn:
            assigned_cnt = conn.execute(
                f"SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND status NOT IN ({_TERMINAL_SQL})",
                (user_id,)
            ).fetchone()[0]

            pending_acc = conn.execute(
                "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND status = 'Assigned'",
                (user_id,)
            ).fetchone()[0]

            in_prog = conn.execute(
                "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND status = 'In Progress'",
                (user_id,)
            ).fetchone()[0]

            wait_verif = conn.execute(
                "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND status = 'Waiting for Verification'",
                (user_id,)
            ).fetchone()[0]

            overdue_cnt = conn.execute(
                f"SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND status NOT IN ({_INACTIVE_SQL}) AND escalated = 1",
                (user_id,)
            ).fetchone()[0]

            resolved_week = conn.execute(
                "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND status IN ('Resolved', 'Closed')",
                (user_id,)
            ).fetchone()[0]

            reopened_cnt = conn.execute(
                "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND status = 'Reopened'",
                (user_id,)
            ).fetchone()[0]

            recent_rows = conn.execute(
                "SELECT complaint_id, title, status, priority, updated_at FROM complaints WHERE assigned_to = ? ORDER BY updated_at DESC LIMIT 5",
                (user_id,)
            ).fetchall()

            ann_rows = conn.execute(
                "SELECT announcement_id, title, summary, priority, is_pinned, created_at FROM announcements WHERE status = 'Published' AND (is_deleted = 0 OR is_deleted IS NULL) ORDER BY is_pinned DESC, created_at DESC LIMIT 5",
            ).fetchall()

            return {
                "role": "coordinator",
                "cards": {
                    "assigned_complaints": assigned_cnt,
                    "pending_acceptance": pending_acc,
                    "in_progress": in_prog,
                    "waiting_verification": wait_verif,
                    "overdue_complaints": overdue_cnt,
                    "resolved_this_week": resolved_week,
                    "reopened_complaints": reopened_cnt,
                },
                "recent_complaints": [dict(r) for r in recent_rows],
                "announcements": [dict(r) for r in ann_rows],
            }

    # ==========================================
    # 3. WARDEN DASHBOARD
    # ==========================================
    def get_warden_dashboard(self, user_id):
        with self._connect() as conn:
            # Warden location scoping
            user_row = conn.execute(
                "SELECT location_id FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            warden_loc = user_row["location_id"] if user_row else None

            loc_rows = conn.execute(
                "SELECT location_id FROM locations WHERE in_charge_id = ?", (user_id,)
            ).fetchall()
            loc_ids = [r["location_id"] for r in loc_rows if r["location_id"]]
            if warden_loc and warden_loc not in loc_ids:
                loc_ids.append(warden_loc)

            if loc_ids:
                placeholders = ",".join(["?"] * len(loc_ids))
                scope_clause = f" AND location_id IN ({placeholders})"
                scope_params = list(loc_ids)
            else:
                scope_clause = ""
                scope_params = []

            open_cnt = conn.execute(
                f"SELECT COUNT(*) FROM complaints WHERE status NOT IN ({_INACTIVE_SQL})" + scope_clause,
                scope_params,
            ).fetchone()[0]

            resolved_today = conn.execute(
                "SELECT COUNT(*) FROM complaints WHERE status IN ('Resolved', 'Closed')" + scope_clause,
                scope_params,
            ).fetchone()[0]

            escalated_cnt = conn.execute(
                "SELECT COUNT(*) FROM complaints WHERE (escalated = 1 OR status = 'Escalated')" + scope_clause,
                scope_params,
            ).fetchone()[0]

            lf_cnt = conn.execute(
                "SELECT COUNT(*) FROM lost_found_items WHERE status != 'Returned' AND status != 'Deleted' AND (is_deleted = 0 OR is_deleted IS NULL)",
            ).fetchone()[0]

            pending_verif = conn.execute(
                "SELECT COUNT(*) FROM complaints WHERE status = 'Waiting for Verification'" + scope_clause,
                scope_params,
            ).fetchone()[0]

            recent_rows = conn.execute(
                "SELECT complaint_id, title, status, priority, updated_at FROM complaints WHERE 1=1" + scope_clause + " ORDER BY updated_at DESC LIMIT 5",
                scope_params,
            ).fetchall()

            return {
                "role": "warden",
                "cards": {
                    "open_complaints": open_cnt,
                    "resolved_today": resolved_today,
                    "escalated_complaints": escalated_cnt,
                    "lost_found_cases": lf_cnt,
                    "pending_verifications": pending_verif,
                },
                "location_overview": {
                    "open_complaints": open_cnt,
                    "escalated": escalated_cnt,
                },
                "recent_activity": [dict(r) for r in recent_rows],
            }

    # ==========================================
    # 4. SUPERVISOR DASHBOARD
    # ==========================================
    def get_supervisor_dashboard(self, user_id):
        with self._connect() as conn:
            # App Manager dashboard counts must be scoped to their assigned
            # locations only (item 15) — resolve assigned_locations the same
            # way auth_service.get_app_manager_assignments() does: the
            # staff_profiles JSON column, falling back to users.location_id.
            import json as _json

            row = conn.execute(
                "SELECT assigned_locations FROM staff_profiles WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            assigned = []
            if row and row["assigned_locations"]:
                try:
                    assigned = _json.loads(row["assigned_locations"]) or []
                except Exception:
                    assigned = []
            if not assigned:
                loc_row = conn.execute(
                    "SELECT location_id FROM users WHERE user_id = ?", (user_id,)
                ).fetchone()
                if loc_row and loc_row["location_id"]:
                    assigned = [loc_row["location_id"]]

            if assigned:
                placeholders = ",".join(["?"] * len(assigned))
                scope_clause = f" AND location_id IN ({placeholders})"
                scope_params = list(assigned)
            else:
                # No assigned locations at all -> no complaints are in scope.
                scope_clause = " AND location_id IS NULL AND location_id IS NOT NULL"
                scope_params = []

            open_cnt = conn.execute(
                f"SELECT COUNT(*) FROM complaints WHERE status NOT IN ({_INACTIVE_SQL})" + scope_clause,
                scope_params,
            ).fetchone()[0]

            closed_cnt = conn.execute(
                "SELECT COUNT(*) FROM complaints WHERE status IN ('Resolved', 'Closed')" + scope_clause,
                scope_params,
            ).fetchone()[0]

            overdue_cnt = conn.execute(
                "SELECT COUNT(*) FROM complaints WHERE (escalated = 1 OR status = 'Escalated')" + scope_clause,
                scope_params,
            ).fetchone()[0]

            pending_verif = conn.execute(
                "SELECT COUNT(*) FROM complaints WHERE status = 'Waiting for Verification'" + scope_clause,
                scope_params,
            ).fetchone()[0]

            lf_cnt = conn.execute(
                "SELECT COUNT(*) FROM lost_found_items WHERE status != 'Returned' AND status != 'Deleted' AND (is_deleted = 0 OR is_deleted IS NULL)",
            ).fetchone()[0]

            return {
                "role": "supervisor",
                "cards": {
                    "open_complaints": open_cnt,
                    "closed_complaints": closed_cnt,
                    "overdue_complaints": overdue_cnt,
                    "pending_verifications": pending_verif,
                    "lost_found_cases": lf_cnt,
                },
                "performance": {
                    "open_complaints": open_cnt,
                    "closed_complaints": closed_cnt,
                },
            }

    # ==========================================
    # 5. ADMINISTRATOR DASHBOARD
    # ==========================================
    def get_admin_dashboard(self, user_id):
        with self._connect() as conn:
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            open_cnt = conn.execute(f"SELECT COUNT(*) FROM complaints WHERE status NOT IN ({_INACTIVE_SQL})").fetchone()[0]
            closed_cnt = conn.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('Resolved', 'Closed')").fetchone()[0]
            lost_cnt = conn.execute("SELECT COUNT(*) FROM lost_found_items WHERE report_type IN ('Lost', 'LOST') AND status != 'Deleted' AND (is_deleted = 0 OR is_deleted IS NULL)").fetchone()[0]
            found_cnt = conn.execute("SELECT COUNT(*) FROM lost_found_items WHERE report_type IN ('Found', 'FOUND') AND status != 'Deleted' AND (is_deleted = 0 OR is_deleted IS NULL)").fetchone()[0]
            ann_cnt = conn.execute("SELECT COUNT(*) FROM announcements WHERE (is_deleted = 0 OR is_deleted IS NULL)").fetchone()[0]

            try:
                audit_alerts = conn.execute("SELECT COUNT(*) FROM audit_logs WHERE severity IN ('High', 'Critical')").fetchone()[0]
            except Exception:
                audit_alerts = 0

            # User breakdown
            students = conn.execute("SELECT COUNT(*) FROM users WHERE LOWER(role) = 'student'").fetchone()[0]
            coordinators = conn.execute("SELECT COUNT(*) FROM users WHERE LOWER(role) = 'coordinator'").fetchone()[0]
            wardens = conn.execute("SELECT COUNT(*) FROM users WHERE LOWER(role) in ('warden', 'location_in_charge')").fetchone()[0]
            supervisors = conn.execute("SELECT COUNT(*) FROM users WHERE LOWER(role) in ('supervisor', 'app_manager')").fetchone()[0]
            administrators = conn.execute("SELECT COUNT(*) FROM users WHERE LOWER(role) = 'administrator'").fetchone()[0]

            return {
                "role": "administrator",
                "cards": {
                    "total_users": total_users,
                    "open_complaints": open_cnt,
                    "closed_complaints": closed_cnt,
                    "lost_items": lost_cnt,
                    "found_items": found_cnt,
                    "announcements": ann_cnt,
                    "unread_audit_alerts": audit_alerts,
                },
                "user_statistics": {
                    "students": students,
                    "coordinators": coordinators,
                    "wardens": wardens,
                    "supervisors": supervisors,
                    "administrators": administrators,
                },
                "system_statistics": {
                    "complaints_today": open_cnt + closed_cnt,
                    "complaints_this_month": open_cnt + closed_cnt,
                    "overdue_complaints": 0,
                    "reopened_complaints": 0,
                },
            }
