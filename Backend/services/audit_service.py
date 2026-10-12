import csv
import io
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from utils.helper import csv_safe, generate_id, now_string


class AuditService:
    SENSITIVE_KEYS = {
        "password",
        "password_hash",
        "token",
        "access_token",
        "refresh_token",
        "reset_token",
        "otp",
        "secret",
        "confirm_password",
    }

    # The platform Super Admin's own activity is not part of any institution's audit trail.
    _NOT_SUPER_ADMIN = (
        "COALESCE(performed_by, '') NOT IN (SELECT user_id FROM users WHERE role = 'super_admin') "
        "AND COALESCE(entity_id, '') NOT IN (SELECT user_id FROM users WHERE role = 'super_admin')"
    )

    def __init__(self, db_path="storage/campus_pulse.db"):
        self.db_path = Path(db_path)
        self._ensure_table()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    audit_id TEXT PRIMARY KEY,
                    module TEXT NOT NULL DEFAULT 'Complaint',
                    entity_type TEXT NOT NULL DEFAULT 'Complaint',
                    entity_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    performed_by TEXT,
                    performed_role TEXT DEFAULT 'System',
                    target_user TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    description TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    request_method TEXT,
                    request_url TEXT,
                    request_id TEXT,
                    status TEXT NOT NULL DEFAULT 'SUCCESS',
                    failure_reason TEXT,
                    created_at TEXT NOT NULL,
                    log_id TEXT,
                    user_id TEXT,
                    target_id TEXT,
                    details TEXT
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(performed_by)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at)"
            )
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS prevent_audit_update
                BEFORE UPDATE ON audit_logs
                BEGIN
                    SELECT RAISE(ABORT, 'Audit records are append-only');
                END
            """)
            conn.execute("""
                CREATE TRIGGER IF NOT EXISTS prevent_audit_delete
                BEFORE DELETE ON audit_logs
                BEGIN
                    SELECT RAISE(ABORT, 'Audit records are append-only');
                END
            """)

    def _sanitize(self, data):
        """Recursively removes sensitive parameters (passwords, tokens, OTPs) from audit data snapshots."""
        if isinstance(data, dict):
            clean = {}
            for k, v in data.items():
                if k.lower() in self.SENSITIVE_KEYS:
                    clean[k] = "******"
                else:
                    clean[k] = self._sanitize(v)
            return clean
        elif isinstance(data, list):
            return [self._sanitize(i) for i in data]
        return data

    def log_event(
        self,
        module="Complaint",
        entity_type="Complaint",
        entity_id="",
        action="UPDATE",
        performed_by=None,
        performed_role="System",
        target_user=None,
        old_value=None,
        new_value=None,
        description="",
        ip_address=None,
        user_agent=None,
        request_method=None,
        request_url=None,
        request_id=None,
        status="SUCCESS",
        failure_reason=None,
    ):
        """Central immutable audit logger automatically invoked across modules."""
        aid = generate_id("AUD")
        created_at = now_string()

        sanitized_old = (
            json.dumps(self._sanitize(old_value)) if old_value is not None else None
        )
        sanitized_new = (
            json.dumps(self._sanitize(new_value)) if new_value is not None else None
        )

        desc = description or f"{action} performed on {entity_type} {entity_id}"

        try:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO audit_logs
                    (audit_id, module, entity_type, entity_id, action, performed_by, performed_role, target_user, old_value, new_value, description, ip_address, user_agent, request_method, request_url, request_id, status, failure_reason, created_at, log_id, user_id, target_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        aid,
                        module,
                        entity_type,
                        str(entity_id),
                        action,
                        performed_by,
                        performed_role,
                        target_user,
                        sanitized_old,
                        sanitized_new,
                        desc,
                        ip_address,
                        user_agent,
                        request_method,
                        request_url,
                        request_id,
                        status,
                        failure_reason,
                        created_at,
                        aid,
                        performed_by or "system",
                        str(entity_id),
                    ),
                )
        except Exception as e:
            # Audit logging failure must not prevent business logic execution
            print(f"[Audit Log Error] Failed to insert audit log: {e}")

        return aid

    # Overloaded backward-compatible log method
    def log(self, user_id, action, target_id, old_value=None, new_value=None):
        return self.log_event(
            module="System",
            entity_type="Entity",
            entity_id=target_id,
            action=action,
            performed_by=user_id,
            old_value=old_value,
            new_value=new_value,
            description=f"{action} on {target_id}",
        )

    # ==========================================
    # AUDIT QUERIES
    # ==========================================
    def list_logs(
        self,
        user=None,
        q=None,
        module=None,
        action=None,
        entity_type=None,
        performed_by=None,
        role=None,
        status=None,
        date_from=None,
        date_to=None,
        ip_address=None,
    ):
        query = f"SELECT * FROM audit_logs WHERE {self._NOT_SUPER_ADMIN}"
        params = []

        if user:
            u_role = (user.role or "").lower()
            if u_role == "student" or u_role == "coordinator":
                # Students and Coordinators have NO access to audit logs per spec
                return []
            elif u_role == "location_in_charge":
                # Wardens view only audit logs related to assigned location
                loc_id = getattr(user, "location_id", "") or ""
                query += " AND (description LIKE ? OR entity_id = ? OR target_id = ?)"
                params.extend([f"%{loc_id}%", loc_id, loc_id])
            if u_role != "administrator":
                # Safety report audit entries are administrator only per Section 3.4 & 5.5
                query += " AND LOWER(COALESCE(module, '')) NOT LIKE '%safety%' AND LOWER(COALESCE(entity_type, '')) NOT LIKE '%safety%'"

        if q:
            term = f"%{q.strip()}%"
            query += " AND (audit_id LIKE ? OR log_id LIKE ? OR entity_id LIKE ? OR target_id LIKE ? OR performed_by LIKE ? OR user_id LIKE ? OR description LIKE ? OR ip_address LIKE ? OR request_id LIKE ?)"
            params.extend([term, term, term, term, term, term, term, term, term])

        if module:
            query += " AND LOWER(module) = LOWER(?)"
            params.append(module)
        if action:
            query += " AND LOWER(action) = LOWER(?)"
            params.append(action)
        if entity_type:
            query += " AND LOWER(entity_type) = LOWER(?)"
            params.append(entity_type)
        if performed_by:
            query += (
                " AND (LOWER(performed_by) = LOWER(?) OR LOWER(user_id) = LOWER(?))"
            )
            params.extend([performed_by, performed_by])
        if role:
            query += " AND LOWER(performed_role) = LOWER(?)"
            params.append(role)
        if status:
            query += " AND LOWER(status) = LOWER(?)"
            params.append(status)
        if date_from:
            query += " AND created_at >= ?"
            params.append(date_from)
        if date_to:
            query += " AND created_at <= ?"
            params.append(date_to)
        if ip_address:
            query += " AND ip_address = ?"
            params.append(ip_address)

        query += " ORDER BY created_at DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def get_log(self, audit_id, user=None):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM audit_logs WHERE audit_id = ? OR log_id = ?",
                (audit_id, audit_id),
            ).fetchone()
            d = self._row_to_dict(row) if row else None
            if d and user:
                u_role = (user.role or "").lower()
                if u_role != "administrator":
                    mod = (d.get("module") or "").lower()
                    etype = (d.get("entity_type") or "").lower()
                    if "safety" in mod or "safety" in etype:
                        return None
            return d

    def get_entity_timeline(self, entity_type, entity_id, user=None):
        if user:
            u_role = (user.role or "").lower()
            if u_role != "administrator" and "safety" in (entity_type or "").lower():
                return []
        query = "SELECT * FROM audit_logs WHERE (LOWER(entity_type) = LOWER(?) OR LOWER(module) = LOWER(?)) AND (entity_id = ? OR target_id = ?) ORDER BY created_at ASC"
        with self._connect() as conn:
            rows = conn.execute(
                query, (entity_type, entity_type, entity_id, entity_id)
            ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def get_dashboard_metrics(self):
        now_str = datetime.now().strftime("%Y-%m-%d")
        today_start = f"{now_str} 00:00:00"

        with self._connect() as conn:
            not_sa = self._NOT_SUPER_ADMIN
            total_logs = conn.execute(
                f"SELECT COUNT(*) FROM audit_logs WHERE {not_sa}"
            ).fetchone()[0]
            failed_actions = conn.execute(
                f"SELECT COUNT(*) FROM audit_logs WHERE status = 'FAILED' AND {not_sa}"
            ).fetchone()[0]
            login_failures = conn.execute(
                f"SELECT COUNT(*) FROM audit_logs WHERE action IN ('LOGIN_FAILED', 'Failed Login') AND {not_sa}"
            ).fetchone()[0]
            today_activity = conn.execute(
                f"SELECT COUNT(*) FROM audit_logs WHERE created_at >= ? AND {not_sa}",
                (today_start,),
            ).fetchone()[0]

            most_active_mod_row = conn.execute(
                f"SELECT module, COUNT(*) as cnt FROM audit_logs WHERE {not_sa} GROUP BY module ORDER BY cnt DESC LIMIT 1"
            ).fetchone()
            most_active = (
                most_active_mod_row["module"] if most_active_mod_row else "Complaint"
            )

            return {
                "total_logs": total_logs,
                "failed_actions": failed_actions,
                "login_failures": login_failures,
                "today_activity": today_activity,
                "most_active_module": most_active,
            }

    def export_logs(self, fmt="csv", filters=None, user=None):
        logs = self.list_logs(user=user, **(filters or {}))
        output = io.StringIO()

        if fmt == "json":
            return json.dumps(logs, indent=2).encode("utf-8")

        writer = csv.writer(output)
        writer.writerow(
            [
                "Audit ID",
                "Timestamp",
                "Module",
                "Entity Type",
                "Entity ID",
                "Action",
                "Performed By",
                "Role",
                "Status",
                "IP Address",
                "Description",
            ]
        )

        for l in logs:
            writer.writerow(
                [
                    l["audit_id"],
                    l["created_at"],
                    l["module"],
                    l["entity_type"],
                    csv_safe(l["entity_id"]),
                    l["action"],
                    l["performed_by"],
                    l["performed_role"],
                    l["status"],
                    l["ip_address"],
                    csv_safe(l["description"]),
                ]
            )

        output.seek(0)
        return output.getvalue().encode("utf-8")

    def archive_logs(self, retention_days=180, performer_id="system"):
        cutoff_date = (datetime.now() - timedelta(days=retention_days)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        with self._connect() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE created_at < ?", (cutoff_date,)
            ).fetchone()[0]
            # Soft flag or move to compressed archive
            return {"archived_count": count, "cutoff_date": cutoff_date}

    def _row_to_dict(self, row):
        if not row:
            return None
        d = dict(row)

        old_val = d.get("old_value")
        new_val = d.get("new_value")

        if old_val and isinstance(old_val, str):
            try:
                old_val = json.loads(old_val)
            except Exception:
                pass

        if new_val and isinstance(new_val, str):
            try:
                new_val = json.loads(new_val)
            except Exception:
                pass

        return {
            "audit_id": d.get("audit_id") or d.get("log_id"),
            "log_id": d.get("audit_id") or d.get("log_id"),
            "module": d.get("module") or "Complaint",
            "entity_type": d.get("entity_type") or "Complaint",
            "entity_id": d.get("entity_id") or d.get("target_id", ""),
            "action": d.get("action", "UPDATE"),
            "performed_by": d.get("performed_by") or d.get("user_id", "system"),
            "user_id": d.get("performed_by") or d.get("user_id", "system"),
            "performed_role": d.get("performed_role") or "System",
            "target_user": d.get("target_user"),
            "old_value": old_val,
            "new_value": new_val,
            "description": d.get("description")
            or f"{d.get('action')} on {d.get('target_id')}",
            "ip_address": d.get("ip_address") or "127.0.0.1",
            "user_agent": d.get("user_agent"),
            "request_method": d.get("request_method"),
            "request_url": d.get("request_url"),
            "request_id": d.get("request_id"),
            "status": d.get("status") or "SUCCESS",
            "failure_reason": d.get("failure_reason"),
            "created_at": d.get("created_at"),
        }
