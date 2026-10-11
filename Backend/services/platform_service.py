import sqlite3
from pathlib import Path
from utils.helper import generate_id, now_string
from utils.logger import get_logger

logger = get_logger(__name__)


class PlatformService:
    PLATFORM_VERSION = "1.0.0"
    DEPLOYMENT_ID = "DEP-CP-PROD-01"

    def __init__(self, db_path="storage/campus_pulse.db"):
        self.db_path = Path(db_path)
        self.ensure_seed_institutions()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def ensure_seed_institutions(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM institutions")
            row = cursor.fetchone()
            if row["count"] == 0:
                now = now_string()
                cursor.execute(
                    """
                    INSERT INTO institutions (
                        institution_id, name, code, status, admin_name, admin_email,
                        contact_info, application_version, deployment_id, created_at, last_health_check
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "INST_ABC",
                        "ABC Institute of Technology",
                        "ABC",
                        "Active",
                        "Administrator",
                        "gowthamejjurothu@gmail.com",
                        "+91-9876543210",
                        self.PLATFORM_VERSION,
                        self.DEPLOYMENT_ID,
                        now,
                        now,
                    ),
                )
                conn.commit()
                logger.info("Seeded default institution metadata: INST_ABC")

    def get_platform_dashboard(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM institutions")
            inst_rows = cursor.fetchall()

            total_institutions = len(inst_rows)
            active_institutions = sum(1 for r in inst_rows if r["status"] == "Active")
            inactive_institutions = total_institutions - active_institutions

            healthy_deployments = active_institutions
            unhealthy_deployments = inactive_institutions

            cursor.execute(
                "SELECT COUNT(*) as open_count FROM support_tickets WHERE status IN ('Open', 'Investigating')"
            )
            ticket_row = cursor.fetchone()
            open_support_tickets = ticket_row["open_count"] if ticket_row else 0

        return {
            "total_registered_institutions": total_institutions,
            "active_institutions": active_institutions,
            "inactive_institutions": inactive_institutions,
            "healthy_deployments": healthy_deployments,
            "unhealthy_deployments": unhealthy_deployments,
            "open_support_issues": open_support_tickets,
            "platform_version": self.PLATFORM_VERSION,
        }

    def get_institutions(self):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM institutions ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_institution(self, institution_id: str):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM institutions WHERE institution_id = ?", (institution_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def _delete_institution(self, institution_id: str):
        with self._connect() as conn:
            conn.execute("DELETE FROM institutions WHERE institution_id = ?", (institution_id,))
            conn.commit()

    def onboard_institution(self, data: dict, auth_service=None):
        name = data.get("name")
        code = data.get("code")
        admin_name = data.get("admin_name")
        admin_email = data.get("admin_email")
        contact_info = data.get("contact_info", "")

        if not name or not code or not admin_name or not admin_email:
            raise ValueError("Institution name, code, admin_name, and admin_email are required.")

        institution_id = f"INST_{code.upper()}"
        deployment_id = f"DEP-{code.upper()}-PROD"
        now = now_string()

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT institution_id FROM institutions WHERE code = ?", (code.upper(),))
            if cursor.fetchone():
                raise ValueError(f"Institution with code '{code}' already exists.")

            cursor.execute(
                """
                INSERT INTO institutions (
                    institution_id, name, code, status, admin_name, admin_email,
                    contact_info, application_version, deployment_id, created_at, last_health_check
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    institution_id,
                    name,
                    code.upper(),
                    "Active",
                    admin_name,
                    admin_email,
                    contact_info,
                    self.PLATFORM_VERSION,
                    deployment_id,
                    now,
                    now,
                ),
            )
            conn.commit()

        # Provision Initial Institution Admin user if auth_service provided
        if auth_service:
            from models.user import User
            from utils.passwords import hash_password, validate_password_complexity

            existing = auth_service.get_user_by_email(admin_email)
            if existing:
                self._delete_institution(institution_id)
                raise ValueError(f"User with email '{admin_email}' already exists.")

            raw_password = data.get("admin_password") or data.get("password")
            if not raw_password:
                self._delete_institution(institution_id)
                raise ValueError("Admin password is required.")

            if not validate_password_complexity(raw_password):
                self._delete_institution(institution_id)
                raise ValueError(
                    "Password complexity requirements not met (min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special character)."
                )

            admin_user_id = f"USR_ADMIN_{code.upper()}"
            try:
                admin_user = User(
                    user_id=admin_user_id,
                    name=admin_name,
                    email=admin_email,
                    password=hash_password(raw_password),
                    role="administrator",
                    first_login=True,
                    status="Active",
                    active=True,
                    created_by="superadmin",
                )
                auth_service.save_user(admin_user)
            except Exception as e:
                self._delete_institution(institution_id)
                raise ValueError(f"Failed to create institution administrator: {str(e)}")

        return self.get_institution(institution_id)

    def get_support_tickets(self, institution_id: str = None):
        with self._connect() as conn:
            cursor = conn.cursor()
            if institution_id:
                cursor.execute(
                    "SELECT * FROM support_tickets WHERE institution_id = ? ORDER BY created_at DESC",
                    (institution_id,),
                )
            else:
                cursor.execute("SELECT * FROM support_tickets ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_support_ticket(self, issue_id: str):
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM support_tickets WHERE issue_id = ?", (issue_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_support_ticket(self, institution_id: str, data: dict):
        module = data.get("module", "General")
        title = data.get("title")
        description = data.get("description")
        error_reference = data.get("error_reference")
        priority = data.get("priority", "Medium")

        if not title or not description:
            raise ValueError("Support issue title and description are required.")

        issue_id = generate_id("SUP")
        now = now_string()

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO support_tickets (
                    issue_id, institution_id, module, title, description,
                    error_reference, priority, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    issue_id,
                    institution_id,
                    module,
                    title,
                    description,
                    error_reference,
                    priority,
                    "Open",
                    now,
                    now,
                ),
            )
            conn.commit()

        return self.get_support_ticket(issue_id)

    def update_support_ticket(self, issue_id: str, status: str = None, resolution_notes: str = None):
        ticket = self.get_support_ticket(issue_id)
        if not ticket:
            raise ValueError(f"Support ticket '{issue_id}' not found.")

        now = now_string()
        new_status = status or ticket["status"]
        resolved_at = now if new_status in ("Resolved", "Closed") else ticket.get("resolved_at")
        notes = resolution_notes if resolution_notes is not None else ticket.get("resolution_notes")

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE support_tickets
                SET status = ?, resolution_notes = ?, resolved_at = ?, updated_at = ?
                WHERE issue_id = ?
                """,
                (new_status, notes, resolved_at, now, issue_id),
            )
            conn.commit()

        return self.get_support_ticket(issue_id)

    def get_system_health(self):
        db_connected = False
        try:
            with self._connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                db_connected = True
        except Exception:
            db_connected = False

        return {
            "application_status": "Healthy" if db_connected else "Degraded",
            "api_availability": True,
            "database_connectivity": db_connected,
            "application_version": self.PLATFORM_VERSION,
            "deployment_id": self.DEPLOYMENT_ID,
            "last_health_check": now_string(),
        }

    def get_version_info(self):
        return {
            "application_version": self.PLATFORM_VERSION,
            "deployment_id": self.DEPLOYMENT_ID,
            "environment": "Production",
            "release_date": "2026-07-18",
            "status": "Healthy",
        }
