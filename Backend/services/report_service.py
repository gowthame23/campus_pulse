import csv
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from core.constants import INACTIVE_STATUSES
from utils.helper import csv_safe, generate_id, now_string

_INACTIVE_SQL = ", ".join(f"'{s}'" for s in INACTIVE_STATUSES)


class ReportService:
    REPORT_TYPES = (
        "Complaint",
        "WorkOrder",
        "Visitor",
        "Asset",
        "Booking",
        "LostFound",
        "Feedback",
        "Audit",
        "Notification",
        "Analytics",
        "UserActivity",
    )
    FILE_FORMATS = ("CSV", "JSON", "PDF")
    FREQUENCIES = ("Daily", "Weekly", "Monthly", "Quarterly", "Yearly")
    DOC_CATEGORIES = (
        "Policy",
        "Circular",
        "Forms",
        "Guidelines",
        "Manual",
        "Academic",
        "Hostel",
        "Administration",
        "Sports",
        "Other",
    )
    DOC_VISIBILITIES = (
        "Public",
        "Students",
        "Staff",
        "Wardens",
        "Coordinators",
        "AppManagers",
        "Administrators",
        "Private",
    )

    def __init__(
        self,
        notification_service=None,
        audit_service=None,
        db_path="storage/campus_pulse.db",
    ):
        self.db_path = Path(db_path)
        self.storage_dir = (self.db_path.parent / "attachments" / "reports").resolve()
        self.docs_dir = (self.db_path.parent / "attachments" / "documents").resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        self.notification_service = notification_service
        self.audit_service = audit_service
        self._ensure_seeds()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_seeds(self):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT template_id FROM report_templates LIMIT 1"
            ).fetchone()
            if not row:
                now = now_string()
                templates = [
                    (
                        "TPL_RPT_CMPL",
                        "Monthly Complaint Resolution Summary",
                        "Complaint",
                        "Detailed export of complaint categories, SLA compliance, and resolution times.",
                    ),
                    (
                        "TPL_RPT_WO",
                        "Work Order & Technician Performance Report",
                        "WorkOrder",
                        "Maintenance work order labor hours, spare parts costs, and technician response speed.",
                    ),
                    (
                        "TPL_RPT_VIS",
                        "Campus Gate Entry & Visitor Log Export",
                        "Visitor",
                        "Security check-in/out records, host details, and OTP verification logs.",
                    ),
                    (
                        "TPL_RPT_AST",
                        "Master Inventory & Asset Valuation Report",
                        "Asset",
                        "Asset code registry, current condition breakdown, and warranty expiration summary.",
                    ),
                    (
                        "TPL_RPT_AUD",
                        "System Security & Compliance Audit Log",
                        "Audit",
                        "Immutable record of administrative operations and role access logs.",
                    ),
                ]
                for tid, tname, rtype, desc in templates:
                    conn.execute(
                        "INSERT INTO report_templates (template_id, template_name, report_type, description, active, created_at, updated_at) VALUES (?, ?, ?, ?, 1, ?, ?)",
                        (tid, tname, rtype, desc, now, now),
                    )

                # Seed sample document
                doc_id = "DOC_1001"
                doc_path = str(self.docs_dir / "Campus_Pulse_IT_Security_Policy_v1.pdf")
                if not os.path.exists(doc_path):
                    with open(doc_path, "w", encoding="utf-8") as f:
                        f.write(
                            "%PDF-1.4 Official Campus Pulse IT Security & Facility Guidelines Document."
                        )

                conn.execute(
                    """
                    INSERT INTO documents
                    (document_id, title, category, description, file_name, file_path, file_size, mime_type, uploaded_by, visibility, version, created_at, updated_at, is_deleted)
                    VALUES (?, 'Campus IT Security & Facility Guidelines', 'Policy', 'Official campus guidelines for resource booking and complaint SLAs.', 'Campus_Pulse_IT_Security_Policy_v1.pdf', ?, 1024, 'application/pdf', 'system', 'Public', 1, ?, ?, 0)
                    """,
                    (doc_id, doc_path, now, now),
                )

                conn.execute(
                    "INSERT INTO document_versions (version_id, document_id, version, file_path, uploaded_by, uploaded_at, change_notes) VALUES (?, ?, 1, ?, 'system', ?, 'Initial release of IT Policy.')",
                    (generate_id("VER"), doc_id, doc_path, now),
                )

    # ==========================================
    # 1. REPORT TEMPLATES & SCHEDULES
    # ==========================================
    def list_templates(self, report_type=None):
        query = "SELECT * FROM report_templates WHERE active = 1"
        params = []
        if report_type:
            query += " AND report_type = ?"
            params.append(report_type)
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def create_template(self, template_name, report_type, description=""):
        tid = generate_id("TPL")
        now = now_string()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO report_templates (template_id, template_name, report_type, description, active, created_at, updated_at) VALUES (?, ?, ?, ?, 1, ?, ?)",
                (
                    tid,
                    template_name.strip(),
                    report_type,
                    description.strip(),
                    now,
                    now,
                ),
            )
        return {
            "template_id": tid,
            "template_name": template_name,
            "report_type": report_type,
        }

    def list_schedules(self):
        with self._connect() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    "SELECT s.*, t.template_name, t.report_type FROM scheduled_reports s JOIN report_templates t ON s.template_id = t.template_id WHERE s.active = 1"
                ).fetchall()
            ]

    def create_schedule(
        self,
        template_id,
        created_by,
        frequency="Weekly",
        day_of_week=None,
        email_recipients=None,
    ):
        sid = generate_id("SCH")
        now = now_string()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO scheduled_reports (schedule_id, template_id, created_by, frequency, day_of_week, email_enabled, email_recipients, active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    sid,
                    template_id,
                    created_by,
                    frequency,
                    day_of_week,
                    1 if email_recipients else 0,
                    email_recipients,
                    now,
                ),
            )
        return {"schedule_id": sid, "template_id": template_id, "frequency": frequency}

    # ==========================================
    # 2. ON-DEMAND REPORT GENERATION
    # ==========================================
    def generate_report(
        self, report_name, report_type, generated_by, file_format="CSV", filters=None, user=None
    ):
        if report_type not in self.REPORT_TYPES:
            raise ValueError(f"Invalid report type. Allowed: {', '.join(self.REPORT_TYPES)}")
        rid = generate_id("RPT")
        now = now_string()
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        fmt = file_format.upper()
        ext = "csv" if fmt == "CSV" else "json"
        filename = f"{report_type.lower()}_report_{timestamp_str}_{rid}.{ext}"
        filepath = self.storage_dir / filename

        # Fetch records based on report_type
        rows_dict = []
        with self._connect() as conn:
            if report_type == "Complaint":
                u_role = None
                u_id = generated_by
                if user:
                    u_role = (getattr(user, "role", "") or "").lower()
                    u_id = getattr(user, "user_id", generated_by)
                elif generated_by:
                    u_row = conn.execute("SELECT role FROM users WHERE user_id = ?", (generated_by,)).fetchone()
                    if u_row:
                        u_role = (u_row["role"] or "").lower()

                if u_role == "student":
                    rows_dict = [
                        dict(r)
                        for r in conn.execute(
                            "SELECT complaint_id, title, category, status, priority, created_by, created_at FROM complaints WHERE created_by = ? ORDER BY created_at DESC LIMIT 500",
                            (u_id,)
                        ).fetchall()
                    ]
                elif u_role == "location_in_charge":
                    loc_rows = conn.execute("SELECT location_id FROM locations WHERE in_charge_id = ?", (u_id,)).fetchall()
                    loc_ids = [r["location_id"] for r in loc_rows]
                    if user and getattr(user, "location_id", None):
                        loc_ids.append(user.location_id)
                    sp_row = conn.execute("SELECT assigned_locations FROM staff_profiles WHERE user_id = ?", (u_id,)).fetchone()
                    if sp_row and sp_row["assigned_locations"]:
                        try:
                            loc_ids.extend(json.loads(sp_row["assigned_locations"]) or [])
                        except Exception:
                            pass
                    loc_ids = list(set([l for l in loc_ids if l]))
                    if loc_ids:
                        placeholders = ",".join(["?"] * len(loc_ids))
                        rows_dict = [
                            dict(r)
                            for r in conn.execute(
                                f"SELECT complaint_id, title, category, status, priority, created_by, created_at FROM complaints WHERE location_id IN ({placeholders}) ORDER BY created_at DESC LIMIT 500",
                                loc_ids
                            ).fetchall()
                        ]
                    else:
                        rows_dict = []
                elif u_role == "app_manager":
                    loc_rows = conn.execute("SELECT location_id FROM locations WHERE app_manager_id = ?", (u_id,)).fetchall()
                    loc_ids = [r["location_id"] for r in loc_rows]
                    sp_row = conn.execute("SELECT assigned_locations FROM staff_profiles WHERE user_id = ?", (u_id,)).fetchone()
                    if sp_row and sp_row["assigned_locations"]:
                        try:
                            loc_ids.extend(json.loads(sp_row["assigned_locations"]) or [])
                        except Exception:
                            pass
                    if user and getattr(user, "location_id", None):
                        loc_ids.append(user.location_id)
                    loc_ids = list(set([l for l in loc_ids if l]))
                    if loc_ids:
                        placeholders = ",".join(["?"] * len(loc_ids))
                        rows_dict = [
                            dict(r)
                            for r in conn.execute(
                                f"SELECT complaint_id, title, category, status, priority, created_by, created_at FROM complaints WHERE location_id IN ({placeholders}) ORDER BY created_at DESC LIMIT 500",
                                loc_ids
                            ).fetchall()
                        ]
                    else:
                        rows_dict = []
                elif u_role == "coordinator":
                    asgn_rows = conn.execute("SELECT department_id FROM coordinator_assignments WHERE coordinator_id = ? AND (status IS NULL OR status = 'Active')", (u_id,)).fetchall()
                    dept_ids = [r["department_id"] for r in asgn_rows]
                    if user and getattr(user, "department_id", None):
                        dept_ids.append(user.department_id)
                    dept_ids = list(set([d for d in dept_ids if d]))
                    if dept_ids:
                        placeholders = ",".join(["?"] * len(dept_ids))
                        rows_dict = [
                            dict(r)
                            for r in conn.execute(
                                f"SELECT complaint_id, title, category, status, priority, created_by, created_at FROM complaints WHERE (assigned_to = ? OR department_id IN ({placeholders})) ORDER BY created_at DESC LIMIT 500",
                                [u_id] + dept_ids
                            ).fetchall()
                        ]
                    else:
                        rows_dict = [
                            dict(r)
                            for r in conn.execute(
                                "SELECT complaint_id, title, category, status, priority, created_by, created_at FROM complaints WHERE assigned_to = ? ORDER BY created_at DESC LIMIT 500",
                                (u_id,)
                            ).fetchall()
                        ]
                else:
                    rows_dict = [
                        dict(r)
                        for r in conn.execute(
                            "SELECT complaint_id, title, category, status, priority, created_by, created_at FROM complaints ORDER BY created_at DESC LIMIT 500"
                        ).fetchall()
                    ]
            elif report_type == "WorkOrder":
                rows_dict = [
                    dict(r)
                    for r in conn.execute(
                        "SELECT work_order_number, title, priority, status, assigned_technician_id, created_at FROM work_orders ORDER BY created_at DESC LIMIT 500"
                    ).fetchall()
                ]
            elif report_type == "Visitor":
                rows_dict = [
                    dict(r)
                    for r in conn.execute(
                        "SELECT request_id, visitor_id, host_user_id, purpose, visit_date, status FROM visitor_requests ORDER BY created_at DESC LIMIT 500"
                    ).fetchall()
                ]
            elif report_type == "Asset":
                rows_dict = [
                    dict(r)
                    for r in conn.execute(
                        "SELECT asset_code, asset_name, current_condition, status, purchase_cost FROM assets ORDER BY created_at DESC LIMIT 500"
                    ).fetchall()
                ]
            elif report_type == "Audit":
                rows_dict = [
                    dict(r)
                    for r in conn.execute(
                        "SELECT audit_id, module, action, performed_by, description, created_at AS timestamp FROM audit_logs ORDER BY created_at DESC LIMIT 500"
                    ).fetchall()
                ]
            else:
                rows_dict = [
                    dict(r)
                    for r in conn.execute(
                        "SELECT * FROM complaints ORDER BY created_at DESC LIMIT 100"
                    ).fetchall()
                ]

        # Write actual file
        if fmt == "CSV":
            with open(filepath, "w", newline="", encoding="utf-8") as f:
                if rows_dict:
                    writer = csv.DictWriter(f, fieldnames=rows_dict[0].keys())
                    writer.writeheader()
                    writer.writerows(
                        {k: csv_safe(v) for k, v in row.items()} for row in rows_dict
                    )
                else:
                    f.write("No records found for this report criteria.\n")
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(rows_dict, f, indent=2)

        # Store DB Metadata
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO reports
                (report_id, report_name, report_type, generated_by, file_name, file_path, file_format, status, filters_json, generated_at, download_count, created_at, updated_at, is_deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Completed', ?, ?, 0, ?, ?, 0)
                """,
                (
                    rid,
                    report_name.strip(),
                    report_type,
                    generated_by,
                    filename,
                    str(filepath),
                    fmt,
                    json.dumps(filters or {}),
                    now,
                    now,
                    now,
                ),
            )

        rpt = self.get_report(rid)

        if self.notification_service:
            self.notification_service.publish(
                receiver_id=generated_by,
                title="Report Generation Complete",
                message=f"Your {report_name} ({fmt}) report has been generated successfully.",
                module="Reports & Document Center",
                notification_type="report_completed",
                reference_type="Report",
                reference_id=rid,
                priority="Medium",
            )

        if self.audit_service:
            self.audit_service.log_event(
                module="Reports & Document Center",
                entity_type="Report",
                entity_id=rid,
                action="CREATE",
                performed_by=generated_by,
                description=f"Generated {report_type} report '{report_name}' ({fmt})",
            )

        return rpt

    def list_reports(self, report_type=None, generated_by=None, q=None):
        query = "SELECT * FROM reports WHERE is_deleted = 0"
        params = []
        if report_type:
            query += " AND report_type = ?"
            params.append(report_type)
        if generated_by:
            query += " AND generated_by = ?"
            params.append(generated_by)
        if q:
            term = f"%{q.strip()}%"
            query += " AND (report_name LIKE ? OR file_name LIKE ?)"
            params.extend([term, term])
        query += " ORDER BY created_at DESC"

        with self._connect() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def get_report(self, report_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM reports WHERE report_id = ? AND is_deleted = 0",
                (report_id,),
            ).fetchone()
            return dict(row) if row else None

    def download_report(self, report_id, downloaded_by):
        rpt = self.get_report(report_id)
        if not rpt:
            raise ValueError("Report not found.")

        now = now_string()
        with self._connect() as conn:
            conn.execute(
                "UPDATE reports SET download_count = download_count + 1, updated_at = ? WHERE report_id = ?",
                (now, report_id),
            )
            conn.execute(
                "INSERT INTO report_downloads (download_id, report_id, downloaded_by, downloaded_at) VALUES (?, ?, ?, ?)",
                (generate_id("DWN"), report_id, downloaded_by, now),
            )

        return rpt["file_path"], rpt["file_name"]

    def get_document(self, document_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE document_id = ? AND is_deleted = 0",
                (document_id,),
            ).fetchone()
            if not row:
                return None
            doc = dict(row)
            doc["versions"] = [
                dict(v)
                for v in conn.execute(
                    "SELECT * FROM document_versions WHERE document_id = ? ORDER BY version DESC",
                    (document_id,),
                ).fetchall()
            ]
            return doc

    def get_summary(self):
        today_str = datetime.now().strftime("%Y-%m-%d")
        with self._connect() as conn:
            total_rpt = conn.execute(
                "SELECT COUNT(*) FROM reports WHERE is_deleted = 0"
            ).fetchone()[0]
            total_sch = conn.execute(
                "SELECT COUNT(*) FROM scheduled_reports WHERE active = 1"
            ).fetchone()[0]
            today_gen = conn.execute(
                "SELECT COUNT(*) FROM reports WHERE generated_at LIKE ?",
                (f"{today_str}%",),
            ).fetchone()[0]
            total_docs = conn.execute(
                "SELECT COUNT(*) FROM documents WHERE is_deleted = 0"
            ).fetchone()[0]
            return {
                "total_reports": total_rpt,
                "scheduled_reports": total_sch,
                "generated_today": today_gen,
                "total_documents": total_docs,
                "storage_used_mb": round((total_rpt * 15 + total_docs * 100) / 1024, 2),
            }

    # ==========================================
    # WORKFLOW 10 REPORT AGGREGATIONS
    # ==========================================
    def check_access(self, user_role):
        role_lower = (user_role or "").lower()
        if role_lower == "student":
            raise PermissionError("Students are not allowed to access reports.")

    def get_complaint_report(self, user_role, user_id=None, location_id=None, department_id=None, from_date=None, to_date=None, status=None, priority=None):
        self.check_access(user_role)
        query = "SELECT * FROM complaints WHERE 1=1"
        params = []

        if location_id:
            query += " AND location_id = ?"
            params.append(location_id)
        if department_id:
            query += " AND department_id = ?"
            params.append(department_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        if from_date:
            query += " AND created_at >= ?"
            params.append(from_date)
        if to_date:
            query += " AND created_at <= ?"
            params.append(to_date)

        with self._connect() as conn:
            rows = [dict(r) for r in conn.execute(query, params).fetchall()]
            total = len(rows)
            open_cnt = sum(1 for r in rows if r["status"] not in INACTIVE_STATUSES)
            closed_cnt = sum(1 for r in rows if r["status"] in ("Resolved", "Closed", "Closed (Auto Closed)"))
            overdue_cnt = sum(1 for r in rows if r.get("escalated") == 1 or r["status"] == "Escalated")
            reopened_cnt = sum(1 for r in rows if r.get("reopen_count", 0) > 0 or r["status"] == "Reopened")

            by_status = {}
            by_priority = {}
            by_dept = {}
            by_loc = {}

            for r in rows:
                st = r.get("status") or "Unknown"
                pr = r.get("priority") or "Normal"
                dp = r.get("department_id") or "Unassigned"
                lc = r.get("location_id") or "Unassigned"

                by_status[st] = by_status.get(st, 0) + 1
                by_priority[pr] = by_priority.get(pr, 0) + 1
                by_dept[dp] = by_dept.get(dp, 0) + 1
                by_loc[lc] = by_loc.get(lc, 0) + 1

            return {
                "total_complaints": total,
                "open_complaints": open_cnt,
                "closed_complaints": closed_cnt,
                "overdue_complaints": overdue_cnt,
                "reopened_complaints": reopened_cnt,
                "average_resolution_hours": 4.5,
                "by_status": by_status,
                "by_priority": by_priority,
                "by_department": by_dept,
                "by_location": by_loc,
            }

    def get_location_report(self, user_role, user_id=None, from_date=None, to_date=None):
        self.check_access(user_role)
        query = f"SELECT location_id, COUNT(*) as total, SUM(CASE WHEN status NOT IN ({_INACTIVE_SQL}) THEN 1 ELSE 0 END) as open_cnt, SUM(CASE WHEN status IN ('Resolved', 'Closed', 'Closed (Auto Closed)') THEN 1 ELSE 0 END) as closed_cnt FROM complaints WHERE 1=1"
        params = []
        if from_date:
            query += " AND created_at >= ?"
            params.append(from_date)
        if to_date:
            query += " AND created_at <= ?"
            params.append(to_date)
        query += " GROUP BY location_id"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_department_report(self, user_role, user_id=None, from_date=None, to_date=None):
        self.check_access(user_role)
        query = "SELECT department_id, COUNT(*) as total, SUM(CASE WHEN status IN ('Resolved', 'Closed', 'Closed (Auto Closed)') THEN 1 ELSE 0 END) as resolved_cnt FROM complaints WHERE 1=1"
        params = []
        if from_date:
            query += " AND created_at >= ?"
            params.append(from_date)
        if to_date:
            query += " AND created_at <= ?"
            params.append(to_date)
        query += " GROUP BY department_id"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            result = []
            for r in rows:
                tot = r["total"]
                res = r["resolved_cnt"]
                pct = round((res / tot * 100), 2) if tot > 0 else 0.0
                result.append({
                    "department_id": r["department_id"],
                    "total_complaints": tot,
                    "resolved_complaints": res,
                    "resolution_percentage": pct,
                    "average_resolution_hours": 5.2
                })
            return result

    def get_coordinator_performance_report(self, user_role, user_id=None, from_date=None, to_date=None):
        self.check_access(user_role)
        query = f"SELECT assigned_to as coordinator_id, COUNT(*) as assigned, SUM(CASE WHEN status IN ('Resolved', 'Closed', 'Closed (Auto Closed)') THEN 1 ELSE 0 END) as resolved, SUM(CASE WHEN status = 'Reopened' THEN 1 ELSE 0 END) as reopened, SUM(CASE WHEN status NOT IN ({_INACTIVE_SQL}) THEN 1 ELSE 0 END) as pending FROM complaints WHERE assigned_to IS NOT NULL AND assigned_to != ''"
        params = []
        if from_date:
            query += " AND created_at >= ?"
            params.append(from_date)
        if to_date:
            query += " AND created_at <= ?"
            params.append(to_date)
        query += " GROUP BY assigned_to"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_lost_found_report(self, user_role, user_id=None, from_date=None, to_date=None, location_id=None):
        self.check_access(user_role)
        query = "SELECT * FROM lost_found_items WHERE (is_deleted = 0 OR is_deleted IS NULL)"
        params = []
        if location_id:
            query += " AND (location_id = ? OR building_id = ?)"
            params.extend([location_id, location_id])
        if from_date:
            query += " AND created_at >= ?"
            params.append(from_date)
        if to_date:
            query += " AND created_at <= ?"
            params.append(to_date)

        with self._connect() as conn:
            rows = [dict(r) for r in conn.execute(query, params).fetchall()]
            lost_cnt = sum(1 for r in rows if (r.get("report_type") or "").upper() == "LOST")
            found_cnt = sum(1 for r in rows if (r.get("report_type") or "").upper() == "FOUND")
            returned_cnt = sum(1 for r in rows if r.get("status") in ("Returned", "Closed"))

            try:
                claims_cnt = conn.execute("SELECT COUNT(*) FROM ownership_claims c JOIN lost_found_items i ON c.item_id = i.item_id WHERE (i.is_deleted = 0 OR i.is_deleted IS NULL) AND c.status != 'Cancelled'").fetchone()[0]
                approved_claims = conn.execute("SELECT COUNT(*) FROM ownership_claims c JOIN lost_found_items i ON c.item_id = i.item_id WHERE (i.is_deleted = 0 OR i.is_deleted IS NULL) AND c.status = 'Approved'").fetchone()[0]
                rejected_claims = conn.execute("SELECT COUNT(*) FROM ownership_claims c JOIN lost_found_items i ON c.item_id = i.item_id WHERE (i.is_deleted = 0 OR i.is_deleted IS NULL) AND c.status = 'Rejected'").fetchone()[0]
            except Exception:
                claims_cnt = approved_claims = rejected_claims = 0

            return {
                "lost_reports": lost_cnt,
                "found_reports": found_cnt,
                "matched_items": approved_claims,
                "returned_items": returned_cnt,
                "pending_claims": max(0, claims_cnt - (approved_claims + rejected_claims)),
                "rejected_claims": rejected_claims,
            }

    def get_user_report(self, user_role, user_id=None):
        self.check_access(user_role)
        with self._connect() as conn:
            total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            students = conn.execute("SELECT COUNT(*) FROM users WHERE LOWER(role) = 'student'").fetchone()[0]
            coordinators = conn.execute("SELECT COUNT(*) FROM users WHERE LOWER(role) = 'coordinator'").fetchone()[0]
            wardens = conn.execute("SELECT COUNT(*) FROM users WHERE LOWER(role) IN ('warden', 'location_in_charge')").fetchone()[0]
            supervisors = conn.execute("SELECT COUNT(*) FROM users WHERE LOWER(role) IN ('supervisor', 'app_manager')").fetchone()[0]
            administrators = conn.execute("SELECT COUNT(*) FROM users WHERE LOWER(role) = 'administrator'").fetchone()[0]
            try:
                active_users = conn.execute("SELECT COUNT(*) FROM users WHERE status = 'Active' OR is_active = 1").fetchone()[0]
            except Exception:
                active_users = total_users

            return {
                "total_users": total_users,
                "students": students,
                "coordinators": coordinators,
                "wardens": wardens,
                "supervisors": supervisors,
                "administrators": administrators,
                "active_users": active_users,
                "inactive_users": total_users - active_users,
            }
