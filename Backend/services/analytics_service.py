import csv
import io
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from utils.helper import csv_safe, now_string


class AnalyticsService:
    def __init__(self, db_path="storage/campus_pulse.db"):
        self.db_path = Path(db_path)

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _parse_date(self, date_str):
        if not date_str:
            return None
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(date_str.split(".")[0], fmt)
            except ValueError:
                pass
        return None

    def _get_app_manager_locations(self, user_id):
        """Resolves an App Manager's assigned locations checking:
        locations.app_manager_id, staff_profiles JSON, and users.location_id."""
        assigned = set()
        with self._connect() as conn:
            # 1. Check locations table app_manager_id
            rows = conn.execute("SELECT location_id FROM locations WHERE app_manager_id = ?", (user_id,)).fetchall()
            for r in rows:
                assigned.add(r["location_id"])

            # 2. Check staff_profiles JSON
            row = conn.execute(
                "SELECT assigned_locations FROM staff_profiles WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if row and row["assigned_locations"]:
                try:
                    for l in json.loads(row["assigned_locations"]) or []:
                        assigned.add(l)
                except Exception:
                    pass

            # 3. Check users.location_id
            loc_row = conn.execute(
                "SELECT location_id FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            if loc_row and loc_row["location_id"]:
                assigned.add(loc_row["location_id"])

        return list(assigned)

    def _get_warden_locations(self, user_id):
        """Resolves a Warden / Location In-Charge's assigned locations checking:
        locations.in_charge_id, staff_profiles JSON, and users.location_id."""
        assigned = set()
        with self._connect() as conn:
            # 1. Check locations table in_charge_id
            rows = conn.execute("SELECT location_id FROM locations WHERE in_charge_id = ?", (user_id,)).fetchall()
            for r in rows:
                assigned.add(r["location_id"])

            # 2. Check staff_profiles JSON
            row = conn.execute(
                "SELECT assigned_locations FROM staff_profiles WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if row and row["assigned_locations"]:
                try:
                    for l in json.loads(row["assigned_locations"]) or []:
                        assigned.add(l)
                except Exception:
                    pass

            # 3. Check users.location_id
            loc_row = conn.execute(
                "SELECT location_id FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            if loc_row and loc_row["location_id"]:
                assigned.add(loc_row["location_id"])

        return list(assigned)

    def _build_complaint_where(self, filters, user=None):
        where = ["(archived = 0 OR archived IS NULL)"]
        params = []

        if user:
            role = (user.role or "").lower()
            if role == "student":
                where.append(
                    "(created_by = ? OR (visibility_type = 'Community' AND location_id = ?))"
                )
                params.extend([user.user_id, getattr(user, "location_id", "") or ""])
            elif role == "coordinator":
                where.append("(assigned_to = ? OR department_id = ?)")
                params.extend([user.user_id, getattr(user, "department_id", "") or ""])
            elif role == "location_in_charge":
                assigned = self._get_warden_locations(user.user_id)
                if assigned:
                    placeholders = ",".join(["?"] * len(assigned))
                    where.append(f"location_id IN ({placeholders})")
                    params.extend(assigned)
                else:
                    where.append("1 = 0")
            elif role == "app_manager":
                assigned = self._get_app_manager_locations(user.user_id)
                if assigned:
                    placeholders = ",".join(["?"] * len(assigned))
                    where.append(f"location_id IN ({placeholders})")
                    params.extend(assigned)
                else:
                    where.append("1 = 0")

        if filters.get("date_from"):
            where.append("created_at >= ?")
            params.append(filters["date_from"])
        if filters.get("date_to"):
            where.append("created_at <= ?")
            params.append(filters["date_to"])
        if filters.get("department_id"):
            where.append("department_id = ?")
            params.append(filters["department_id"])
        if filters.get("location_id") or filters.get("building_id"):
            loc = filters.get("location_id") or filters.get("building_id")
            where.append("location_id = ?")
            params.append(loc)
        if filters.get("category_id"):
            where.append("(category = ? OR complaint_type = ?)")
            params.extend([filters["category_id"], filters["category_id"]])
        if filters.get("coordinator_id"):
            where.append("assigned_to = ?")
            params.append(filters["coordinator_id"])
        if filters.get("priority"):
            where.append("priority = ?")
            params.append(filters["priority"])
        if filters.get("status"):
            where.append("status = ?")
            params.append(filters["status"])
        if filters.get("complaint_type"):
            where.append("complaint_type = ?")
            params.append(filters["complaint_type"])

        return " AND ".join(where), params

    # ==========================================
    # 1. ROLE-SPECIFIC DASHBOARD SUMMARY
    # ==========================================
    def get_dashboard_summary(self, user):
        role = (user.role or "").lower()
        now_str = datetime.now().strftime("%Y-%m-%d")
        today_start = f"{now_str} 00:00:00"

        with self._connect() as conn:
            if role == "student":
                my_complaints = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE created_by = ?",
                    (user.user_id,),
                ).fetchone()[0]
                pending = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE created_by = ? AND status IN ('Pending', 'Submitted', 'Assigned', 'In Progress')",
                    (user.user_id,),
                ).fetchone()[0]
                resolved = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE created_by = ? AND status IN ('Closed', 'Closed (Auto Closed)')",
                    (user.user_id,),
                ).fetchone()[0]
                waiting_verification = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE created_by = ? AND status = 'Waiting for Verification'",
                    (user.user_id,),
                ).fetchone()[0]
                loc_id = getattr(user, "location_id", "") or ""
                community_issues = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE visibility_type = 'Community' AND location_id = ?",
                    (loc_id,),
                ).fetchone()[0]
                unread_notifs = conn.execute(
                    "SELECT COUNT(*) FROM notifications WHERE (LOWER(receiver_id) = LOWER(?) OR LOWER(receiver_id) = 'student') AND is_read = 0 AND (is_deleted = 0 OR is_deleted IS NULL)",
                    (user.user_id,),
                ).fetchone()[0]

                return {
                    "role": "student",
                    "metrics": {
                        "my_complaints": my_complaints,
                        "pending": pending,
                        "resolved": resolved,
                        "waiting_verification": waiting_verification,
                        "community_issues": community_issues,
                        "unread_notifications": unread_notifs,
                    },
                }

            elif role == "coordinator":
                assigned = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE assigned_to = ?",
                    (user.user_id,),
                ).fetchone()[0]
                pending = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND status IN ('Assigned', 'Pending', 'Submitted')",
                    (user.user_id,),
                ).fetchone()[0]
                in_progress = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND status = 'In Progress'",
                    (user.user_id,),
                ).fetchone()[0]
                waiting_verification = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND status = 'Waiting for Verification'",
                    (user.user_id,),
                ).fetchone()[0]
                resolved_today = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND resolved_at >= ?",
                    (user.user_id, today_start),
                ).fetchone()[0]
                reopened = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND reopen_count > 0",
                    (user.user_id,),
                ).fetchone()[0]
                escalated = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND escalated = 1",
                    (user.user_id,),
                ).fetchone()[0]

                # Calculate avg resolution time in hours
                rows = conn.execute(
                    "SELECT created_at, resolved_at FROM complaints WHERE assigned_to = ? AND resolved_at IS NOT NULL",
                    (user.user_id,),
                ).fetchall()
                durations = []
                for r in rows:
                    c_date = self._parse_date(r["created_at"])
                    r_date = self._parse_date(r["resolved_at"])
                    if c_date and r_date and r_date >= c_date:
                        durations.append((r_date - c_date).total_seconds() / 3600.0)
                avg_res_hours = (
                    round(sum(durations) / len(durations), 1) if durations else 0.0
                )

                return {
                    "role": "coordinator",
                    "metrics": {
                        "assigned_complaints": assigned,
                        "pending": pending,
                        "in_progress": in_progress,
                        "waiting_verification": waiting_verification,
                        "resolved_today": resolved_today,
                        "reopened": reopened,
                        "escalated": escalated,
                        "overdue_sla": conn.execute(
                            "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND status NOT IN ('Closed', 'Closed (Auto Closed)') AND verification_due_at < ?",
                            (user.user_id, now_str),
                        ).fetchone()[0],
                        "avg_resolution_hours": avg_res_hours,
                    },
                }

            elif role == "location_in_charge":
                assigned = self._get_warden_locations(user.user_id)
                if assigned:
                    placeholders = ",".join(["?"] * len(assigned))
                    loc_clause = f" AND location_id IN ({placeholders})"
                    loc_params = assigned
                else:
                    loc_clause = " AND 1 = 0"
                    loc_params = []

                hostel_complaints = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE 1=1" + loc_clause, loc_params
                ).fetchone()[0]
                pending = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE status IN ('Pending', 'Submitted', 'Assigned', 'In Progress')" + loc_clause,
                    loc_params,
                ).fetchone()[0]
                critical = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE priority = 'Critical'" + loc_clause,
                    loc_params,
                ).fetchone()[0]
                escalated = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE escalated = 1" + loc_clause,
                    loc_params,
                ).fetchone()[0]
                reopened = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE reopen_count > 0" + loc_clause,
                    loc_params,
                ).fetchone()[0]
                sla_breaches = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE verification_due_at < ?" + loc_clause,
                    [now_str] + loc_params,
                ).fetchone()[0]

                return {
                    "role": "location_in_charge",
                    "metrics": {
                        "hostel_complaints": hostel_complaints,
                        "pending": pending,
                        "critical": critical,
                        "escalated": escalated,
                        "reopened": reopened,
                        "sla_breaches": sla_breaches,
                    },
                }

            elif role == "app_manager":
                assigned = self._get_app_manager_locations(user.user_id)
                if assigned:
                    placeholders = ",".join(["?"] * len(assigned))
                    loc_clause = f" AND location_id IN ({placeholders})"
                else:
                    loc_clause = " AND 1 = 0"

                total_complaints = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE 1=1" + loc_clause, assigned
                ).fetchone()[0]
                active_complaints = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE status NOT IN ('Closed', 'Closed (Auto Closed)')" + loc_clause,
                    assigned,
                ).fetchone()[0]
                closed_today = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE status IN ('Closed', 'Closed (Auto Closed)') AND updated_at >= ?" + loc_clause,
                    [today_start] + assigned,
                ).fetchone()[0]
                critical = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE priority = 'Critical' AND status NOT IN ('Closed', 'Closed (Auto Closed)')" + loc_clause,
                    assigned,
                ).fetchone()[0]
                sla_breaches = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE status NOT IN ('Closed', 'Closed (Auto Closed)') AND verification_due_at < ?" + loc_clause,
                    [now_str] + assigned,
                ).fetchone()[0]
                total_users = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE (is_deleted = 0 OR is_deleted IS NULL)"
                ).fetchone()[0]
                students_count = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE role = 'student' AND (is_deleted = 0 OR is_deleted IS NULL)"
                ).fetchone()[0]
                staff_count = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE role != 'student' AND (is_deleted = 0 OR is_deleted IS NULL)"
                ).fetchone()[0]

                return {
                    "role": role,
                    "metrics": {
                        "total_complaints": total_complaints,
                        "active_complaints": active_complaints,
                        "closed_today": closed_today,
                        "critical_complaints": critical,
                        "sla_breaches": sla_breaches,
                        "total_users": total_users,
                        "students_count": students_count,
                        "staff_count": staff_count,
                        "departments_count": conn.execute(
                            "SELECT COUNT(*) FROM departments"
                        ).fetchone()[0],
                        "locations_count": conn.execute(
                            "SELECT COUNT(*) FROM locations"
                        ).fetchone()[0],
                    },
                }

            else:  # Administrator — global, unscoped
                total_complaints = conn.execute(
                    "SELECT COUNT(*) FROM complaints"
                ).fetchone()[0]
                active_complaints = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE status NOT IN ('Closed', 'Closed (Auto Closed)')"
                ).fetchone()[0]
                closed_today = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE status IN ('Closed', 'Closed (Auto Closed)') AND updated_at >= ?",
                    (today_start,),
                ).fetchone()[0]
                critical = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE priority = 'Critical' AND status NOT IN ('Closed', 'Closed (Auto Closed)')"
                ).fetchone()[0]
                sla_breaches = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE status NOT IN ('Closed', 'Closed (Auto Closed)') AND verification_due_at < ?",
                    (now_str,),
                ).fetchone()[0]
                total_users = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE (is_deleted = 0 OR is_deleted IS NULL)"
                ).fetchone()[0]
                students_count = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE role = 'student' AND (is_deleted = 0 OR is_deleted IS NULL)"
                ).fetchone()[0]
                staff_count = conn.execute(
                    "SELECT COUNT(*) FROM users WHERE role != 'student' AND (is_deleted = 0 OR is_deleted IS NULL)"
                ).fetchone()[0]

                return {
                    "role": role,
                    "metrics": {
                        "total_complaints": total_complaints,
                        "active_complaints": active_complaints,
                        "closed_today": closed_today,
                        "critical_complaints": critical,
                        "sla_breaches": sla_breaches,
                        "total_users": total_users,
                        "students_count": students_count,
                        "staff_count": staff_count,
                        "departments_count": conn.execute(
                            "SELECT COUNT(*) FROM departments"
                        ).fetchone()[0],
                        "coordinators_count": conn.execute(
                            "SELECT COUNT(*) FROM users WHERE role = 'coordinator'"
                        ).fetchone()[0],
                        "system_health": "100% Operational",
                    },
                }

    # ==========================================
    # 2. COMPLAINT ANALYTICS
    # ==========================================
    def get_complaint_analytics(self, filters, user=None):
        where_clause, params = self._build_complaint_where(filters, user)

        with self._connect() as conn:
            # Group by Status
            rows = conn.execute(
                f"SELECT status, COUNT(*) as cnt FROM complaints WHERE {where_clause} GROUP BY status",
                params,
            ).fetchall()
            by_status = {r["status"]: r["cnt"] for r in rows}

            # Group by Priority
            rows = conn.execute(
                f"SELECT priority, COUNT(*) as cnt FROM complaints WHERE {where_clause} GROUP BY priority",
                params,
            ).fetchall()
            by_priority = {r["priority"]: r["cnt"] for r in rows}

            # Group by Department
            rows = conn.execute(
                f"SELECT department_id, COUNT(*) as cnt FROM complaints WHERE {where_clause} GROUP BY department_id",
                params,
            ).fetchall()
            by_department = {r["department_id"]: r["cnt"] for r in rows}

            # Group by Location / Hostel
            rows = conn.execute(
                f"SELECT location_id, COUNT(*) as cnt FROM complaints WHERE {where_clause} GROUP BY location_id",
                params,
            ).fetchall()
            by_location = {r["location_id"]: r["cnt"] for r in rows}

            # Group by Category
            rows = conn.execute(
                f"SELECT category, COUNT(*) as cnt FROM complaints WHERE {where_clause} AND category IS NOT NULL GROUP BY category",
                params,
            ).fetchall()
            by_category = {r["category"]: r["cnt"] for r in rows}

            # Resolution Metrics
            rows = conn.execute(
                f"SELECT created_at, resolved_at FROM complaints WHERE {where_clause} AND resolved_at IS NOT NULL",
                params,
            ).fetchall()
            durations = []
            for r in rows:
                c_d = self._parse_date(r["created_at"])
                r_d = self._parse_date(r["resolved_at"])
                if c_d and r_d and r_d >= c_d:
                    durations.append((r_d - c_d).total_seconds() / 3600.0)
            avg_res_hours = (
                round(sum(durations) / len(durations), 1) if durations else 0.0
            )

            # Reopen Analysis
            reopened_count = conn.execute(
                f"SELECT COUNT(*) FROM complaints WHERE {where_clause} AND reopen_count > 0",
                params,
            ).fetchone()[0]
            max_reopen_rows = conn.execute(
                f"SELECT MAX(reopen_count) FROM complaints WHERE {where_clause}", params
            ).fetchone()[0]

            # Community Complaint Analytics
            community_total = conn.execute(
                f"SELECT COUNT(*) FROM complaints WHERE {where_clause} AND visibility_type = 'Community'",
                params,
            ).fetchone()[0]

            return {
                "total_complaints": sum(by_status.values()),
                "by_status": by_status,
                "by_priority": by_priority,
                "by_department": by_department,
                "by_location": by_location,
                "by_category": by_category,
                "average_resolution_hours": avg_res_hours,
                "reopened_count": reopened_count,
                "max_reopens": max_reopen_rows or 0,
                "community_total": community_total,
            }

    # ==========================================
    # 3. SLA ANALYTICS
    # ==========================================
    def get_sla_analytics(self, filters, user=None):
        where_clause, params = self._build_complaint_where(filters, user)
        today = datetime.now().strftime("%Y-%m-%d")

        with self._connect() as conn:
            on_time = conn.execute(
                f"SELECT COUNT(*) FROM complaints WHERE {where_clause} AND (verification_due_at >= ? OR status IN ('Closed', 'Closed (Auto Closed)'))",
                params + [today],
            ).fetchone()[0]
            due_today = conn.execute(
                f"SELECT COUNT(*) FROM complaints WHERE {where_clause} AND verification_due_at LIKE ? AND status NOT IN ('Closed', 'Closed (Auto Closed)')",
                params + [f"{today}%"],
            ).fetchone()[0]
            overdue = conn.execute(
                f"SELECT COUNT(*) FROM complaints WHERE {where_clause} AND verification_due_at < ? AND status NOT IN ('Closed', 'Closed (Auto Closed)')",
                params + [today],
            ).fetchone()[0]

            total = on_time + overdue
            sla_achievement_pct = (
                round((on_time / total) * 100, 1) if total > 0 else 100.0
            )

            # Department-wise SLA breaches
            dept_breaches = {}
            rows = conn.execute(
                f"SELECT department_id, COUNT(*) as cnt FROM complaints WHERE {where_clause} AND verification_due_at < ? AND status NOT IN ('Closed', 'Closed (Auto Closed)') GROUP BY department_id",
                params + [today],
            ).fetchall()
            for r in rows:
                dept_breaches[r["department_id"]] = r["cnt"]

            return {
                "on_time": on_time,
                "due_today": due_today,
                "overdue": overdue,
                "total_breaches": overdue,
                "sla_achievement_pct": sla_achievement_pct,
                "department_breaches": dept_breaches,
            }

    # ==========================================
    # 4. DEPARTMENT PERFORMANCE ANALYTICS
    # ==========================================
    def get_department_analytics(self, filters, user=None):
        with self._connect() as conn:
            depts = conn.execute("SELECT * FROM departments").fetchall()
            result = []
            today = datetime.now().strftime("%Y-%m-%d")

            for d in depts:
                did = d["department_id"]
                assigned = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE department_id = ?", (did,)
                ).fetchone()[0]
                completed = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE department_id = ? AND status IN ('Closed', 'Closed (Auto Closed)', 'Resolved')",
                    (did,),
                ).fetchone()[0]
                pending = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE department_id = ? AND status IN ('Pending', 'Submitted', 'Assigned', 'In Progress')",
                    (did,),
                ).fetchone()[0]
                breaches = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE department_id = ? AND verification_due_at < ? AND status NOT IN ('Closed', 'Closed (Auto Closed)')",
                    (did, today),
                ).fetchone()[0]
                reopened = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE department_id = ? AND reopen_count > 0",
                    (did,),
                ).fetchone()[0]

                rows = conn.execute(
                    "SELECT created_at, resolved_at FROM complaints WHERE department_id = ? AND resolved_at IS NOT NULL",
                    (did,),
                ).fetchall()
                durations = []
                for r in rows:
                    c_d = self._parse_date(r["created_at"])
                    r_d = self._parse_date(r["resolved_at"])
                    if c_d and r_d and r_d >= c_d:
                        durations.append((r_d - c_d).total_seconds() / 3600.0)
                avg_res_hours = (
                    round(sum(durations) / len(durations), 1) if durations else 0.0
                )

                result.append(
                    {
                        "department_id": did,
                        "department_name": d["name"],
                        "assigned_complaints": assigned,
                        "completed_complaints": completed,
                        "pending_complaints": pending,
                        "sla_breaches": breaches,
                        "reopened_complaints": reopened,
                        "average_resolution_hours": avg_res_hours,
                        "sla_compliance_pct": (
                            round(((assigned - breaches) / assigned * 100), 1)
                            if assigned > 0
                            else 100.0
                        ),
                    }
                )

            return result

    # ==========================================
    # 5. COORDINATOR PERFORMANCE ANALYTICS
    # ==========================================
    def get_coordinator_analytics(self, filters, user=None):
        with self._connect() as conn:
            coords = conn.execute(
                "SELECT * FROM users WHERE role = 'coordinator' AND (is_deleted = 0 OR is_deleted IS NULL)"
            ).fetchall()
            result = []
            today = datetime.now().strftime("%Y-%m-%d")

            for c in coords:
                cid = c["user_id"]
                assigned = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE assigned_to = ?", (cid,)
                ).fetchone()[0]
                resolved = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND status IN ('Closed', 'Closed (Auto Closed)', 'Resolved')",
                    (cid,),
                ).fetchone()[0]
                pending = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND status IN ('Pending', 'Submitted', 'Assigned', 'In Progress')",
                    (cid,),
                ).fetchone()[0]
                reopened = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND reopen_count > 0",
                    (cid,),
                ).fetchone()[0]
                escalated = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND escalated = 1",
                    (cid,),
                ).fetchone()[0]
                breaches = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND verification_due_at < ? AND status NOT IN ('Closed', 'Closed (Auto Closed)')",
                    (cid, today),
                ).fetchone()[0]

                rows = conn.execute(
                    "SELECT created_at, resolved_at FROM complaints WHERE assigned_to = ? AND resolved_at IS NOT NULL",
                    (cid,),
                ).fetchall()
                durations = []
                for r in rows:
                    c_d = self._parse_date(r["created_at"])
                    r_d = self._parse_date(r["resolved_at"])
                    if c_d and r_d and r_d >= c_d:
                        durations.append((r_d - c_d).total_seconds() / 3600.0)
                avg_res = (
                    round(sum(durations) / len(durations), 1) if durations else 0.0
                )

                ranking = (
                    "Best Performer"
                    if (resolved >= 5 and breaches == 0 and avg_res < 48.0)
                    else (
                        "Needs Improvement"
                        if (breaches > 2 or avg_res > 72.0)
                        else "Satisfactory"
                    )
                )

                result.append(
                    {
                        "coordinator_id": cid,
                        "coordinator_name": c["name"],
                        "assigned": assigned,
                        "resolved": resolved,
                        "pending": pending,
                        "reopened": reopened,
                        "escalations": escalated,
                        "sla_breaches": breaches,
                        "average_resolution_hours": avg_res,
                        "ranking": ranking,
                    }
                )

            return result

    # ==========================================
    # 6. HOSTEL ANALYTICS
    # ==========================================
    def get_hostel_analytics(self, filters, user=None):
        with self._connect() as conn:
            hostels = conn.execute("SELECT * FROM hostels").fetchall()
            result = []

            for h in hostels:
                hid = h["building_id"]
                hname = h["hostel_name"]
                total = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE location_id = ?", (hid,)
                ).fetchone()[0]
                critical = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE location_id = ? AND priority = 'Critical'",
                    (hid,),
                ).fetchone()[0]
                resolved = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE location_id = ? AND status IN ('Closed', 'Closed (Auto Closed)', 'Resolved')",
                    (hid,),
                ).fetchone()[0]
                pending = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE location_id = ? AND status IN ('Pending', 'Submitted', 'Assigned', 'In Progress')",
                    (hid,),
                ).fetchone()[0]

                top_cat_row = conn.execute(
                    "SELECT category, COUNT(*) as cnt FROM complaints WHERE location_id = ? AND category IS NOT NULL GROUP BY category ORDER BY cnt DESC LIMIT 1",
                    (hid,),
                ).fetchone()
                top_cat = top_cat_row["category"] if top_cat_row else "General"

                result.append(
                    {
                        "hostel_id": h["hostel_id"],
                        "building_id": hid,
                        "hostel_name": hname,
                        "total_complaints": total,
                        "critical_complaints": critical,
                        "resolved": resolved,
                        "pending": pending,
                        "most_common_category": top_cat,
                        "capacity": h["capacity"],
                        "occupied_rooms": h["occupied_rooms"],
                    }
                )

            return result

    # ==========================================
    # 7. USER ANALYTICS
    # ==========================================
    def get_user_analytics(self, filters, user=None):
        with self._connect() as conn:
            total_students = conn.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'student' AND (is_deleted = 0 OR is_deleted IS NULL)"
            ).fetchone()[0]
            active_students = conn.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'student' AND status = 'Active' AND (is_deleted = 0 OR is_deleted IS NULL)"
            ).fetchone()[0]
            inactive_students = conn.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'student' AND status != 'Active' AND (is_deleted = 0 OR is_deleted IS NULL)"
            ).fetchone()[0]

            coordinators = conn.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'coordinator' AND (is_deleted = 0 OR is_deleted IS NULL)"
            ).fetchone()[0]
            wardens = conn.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'location_in_charge' AND (is_deleted = 0 OR is_deleted IS NULL)"
            ).fetchone()[0]
            app_managers = conn.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'app_manager' AND (is_deleted = 0 OR is_deleted IS NULL)"
            ).fetchone()[0]
            administrators = conn.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'administrator' AND (is_deleted = 0 OR is_deleted IS NULL)"
            ).fetchone()[0]

            today = datetime.now().strftime("%Y-%m-%d")
            daily_logins = conn.execute(
                "SELECT COUNT(*) FROM user_activities WHERE action = 'User Login' AND timestamp >= ?",
                (f"{today} 00:00:00",),
            ).fetchone()[0]
            failed_logins = conn.execute(
                "SELECT COUNT(*) FROM user_activities WHERE action = 'Failed Login Attempt'",
                (),
            ).fetchone()[0]

            return {
                "students": {
                    "total": total_students,
                    "active": active_students,
                    "inactive": inactive_students,
                },
                "staff": {
                    "coordinators": coordinators,
                    "wardens": wardens,
                    "app_managers": app_managers,
                    "administrators": administrators,
                },
                "activity": {
                    "daily_logins": daily_logins,
                    "failed_login_attempts": failed_logins,
                },
            }

    # ==========================================
    # 8. NOTIFICATION ANALYTICS
    # ==========================================
    def get_notification_analytics(self, filters, user=None):
        with self._connect() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM notifications WHERE (is_deleted = 0 OR is_deleted IS NULL)"
            ).fetchone()[0]
            delivered = conn.execute(
                "SELECT COUNT(*) FROM notifications WHERE delivery_status = 'Delivered' AND (is_deleted = 0 OR is_deleted IS NULL)"
            ).fetchone()[0]
            pending = conn.execute(
                "SELECT COUNT(*) FROM notifications WHERE delivery_status = 'Pending' AND (is_deleted = 0 OR is_deleted IS NULL)"
            ).fetchone()[0]
            read_cnt = conn.execute(
                "SELECT COUNT(*) FROM notifications WHERE is_read = 1 AND (is_deleted = 0 OR is_deleted IS NULL)"
            ).fetchone()[0]
            unread_cnt = conn.execute(
                "SELECT COUNT(*) FROM notifications WHERE is_read = 0 AND (is_deleted = 0 OR is_deleted IS NULL)"
            ).fetchone()[0]

            by_module = {}
            for r in conn.execute(
                "SELECT module, COUNT(*) as cnt FROM notifications WHERE (is_deleted = 0 OR is_deleted IS NULL) GROUP BY module"
            ).fetchall():
                by_module[r["module"] or "Complaint"] = r["cnt"]

            by_priority = {}
            for r in conn.execute(
                "SELECT priority, COUNT(*) as cnt FROM notifications WHERE (is_deleted = 0 OR is_deleted IS NULL) GROUP BY priority"
            ).fetchall():
                by_priority[r["priority"] or "Medium"] = r["cnt"]

            return {
                "total_generated": total,
                "delivered": delivered,
                "pending": pending,
                "read": read_cnt,
                "unread": unread_cnt,
                "by_module": by_module,
                "by_priority": by_priority,
            }

    # ==========================================
    # 9. EXPORT REPORT ENGINE (CSV / PDF)
    # ==========================================
    def export_report(self, report_type, fmt="csv", filters=None, user=None):
        filters = filters or {}
        output = io.StringIO()
        raw_writer = csv.writer(output)

        class SafeWriter:
            def writerow(self, row):
                raw_writer.writerow([csv_safe(cell) for cell in row])

        writer = SafeWriter()

        if report_type == "complaints":
            analytics = self.get_complaint_analytics(filters, user)
            writer.writerow(["Complaint Metric", "Value"])
            writer.writerow(["Total Complaints", analytics["total_complaints"]])
            writer.writerow(
                ["Average Resolution (Hours)", analytics["average_resolution_hours"]]
            )
            writer.writerow(["Reopened Complaints", analytics["reopened_count"]])
            writer.writerow(["Community Complaints", analytics["community_total"]])
            writer.writerow([])
            writer.writerow(["Status", "Count"])
            for s, c in analytics["by_status"].items():
                writer.writerow([s, c])

        elif report_type == "department":
            depts = self.get_department_analytics(filters, user)
            writer.writerow(
                [
                    "Department Name",
                    "Assigned",
                    "Completed",
                    "Pending",
                    "SLA Breaches",
                    "Reopened",
                    "Avg Res Hours",
                    "SLA Compliance %",
                ]
            )
            for d in depts:
                writer.writerow(
                    [
                        d["department_name"],
                        d["assigned_complaints"],
                        d["completed_complaints"],
                        d["pending_complaints"],
                        d["sla_breaches"],
                        d["reopened_complaints"],
                        d["average_resolution_hours"],
                        d["sla_compliance_pct"],
                    ]
                )

        elif report_type == "coordinator":
            coords = self.get_coordinator_analytics(filters, user)
            writer.writerow(
                [
                    "Coordinator Name",
                    "Assigned",
                    "Resolved",
                    "Pending",
                    "Reopened",
                    "Escalations",
                    "SLA Breaches",
                    "Avg Res Hours",
                    "Ranking",
                ]
            )
            for c in coords:
                writer.writerow(
                    [
                        c["coordinator_name"],
                        c["assigned"],
                        c["resolved"],
                        c["pending"],
                        c["reopened"],
                        c["escalations"],
                        c["sla_breaches"],
                        c["average_resolution_hours"],
                        c["ranking"],
                    ]
                )

        elif report_type == "hostel":
            hostels = self.get_hostel_analytics(filters, user)
            writer.writerow(
                [
                    "Hostel Name",
                    "Total Complaints",
                    "Critical",
                    "Resolved",
                    "Pending",
                    "Most Common Category",
                    "Capacity",
                    "Occupied Rooms",
                ]
            )
            for h in hostels:
                writer.writerow(
                    [
                        h["hostel_name"],
                        h["total_complaints"],
                        h["critical_complaints"],
                        h["resolved"],
                        h["pending"],
                        h["most_common_category"],
                        h["capacity"],
                        h["occupied_rooms"],
                    ]
                )

        elif report_type == "sla":
            sla = self.get_sla_analytics(filters, user)
            writer.writerow(["SLA Metric", "Value"])
            writer.writerow(["On Time", sla["on_time"]])
            writer.writerow(["Due Today", sla["due_today"]])
            writer.writerow(["Overdue Breaches", sla["overdue"]])
            writer.writerow(["SLA Achievement %", sla["sla_achievement_pct"]])

        else:
            writer.writerow(["Report", "Generated At"])
            writer.writerow([report_type, now_string()])

        output.seek(0)
        return output.getvalue().encode("utf-8")
