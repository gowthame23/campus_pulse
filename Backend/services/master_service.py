import sqlite3
from pathlib import Path
from utils.helper import now_string

class MasterReferenceService:
    DEFAULT_REFERENCES = [
        # Priorities
        ("REF_PR_HIGH", "PRIORITY", "HIGH", "High Priority", 1),
        ("REF_PR_MED", "PRIORITY", "MEDIUM", "Medium Priority", 2),
        ("REF_PR_LOW", "PRIORITY", "LOW", "Low Priority", 3),
        ("REF_PR_URG", "PRIORITY", "URGENT", "Urgent Priority", 0),
        # Visibility
        ("REF_VIS_PUB", "VISIBILITY", "PUBLIC", "Public", 1),
        ("REF_VIS_PRI", "VISIBILITY", "PRIVATE", "Private", 2),
        # Complaint Statuses
        ("REF_ST_PEND", "COMPLAINT_STATUS", "PENDING", "Pending", 1),
        ("REF_ST_ASSG", "COMPLAINT_STATUS", "ASSIGNED", "Assigned", 2),
        ("REF_ST_INPR", "COMPLAINT_STATUS", "IN_PROGRESS", "In Progress", 3),
        ("REF_ST_WAIT", "COMPLAINT_STATUS", "WAITING_VERIFICATION", "Waiting for Verification", 4),
        ("REF_ST_RESO", "COMPLAINT_STATUS", "RESOLVED", "Resolved", 5),
        ("REF_ST_REOP", "COMPLAINT_STATUS", "REOPENED", "Reopened", 6),
        ("REF_ST_CLOS", "COMPLAINT_STATUS", "CLOSED", "Closed", 7),
        ("REF_ST_CANC", "COMPLAINT_STATUS", "CANCELLED", "Cancelled", 8),
    ]

    def __init__(self, db_path="storage/campus_pulse.db"):
        self.db_path = Path(db_path)
        self._ensure_seeds()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_seeds(self):
        now = now_string()
        with self._connect() as conn:
            cnt = conn.execute("SELECT COUNT(*) FROM master_references").fetchone()[0]
            if cnt == 0:
                for ref_id, cat, code, label, order in self.DEFAULT_REFERENCES:
                    conn.execute(
                        "INSERT INTO master_references (ref_id, category, code, display_label, sort_order, active, created_at) VALUES (?, ?, ?, ?, ?, 1, ?)",
                        (ref_id, cat, code, label, order, now),
                    )

    def list_references(self, category=None):
        query = "SELECT * FROM master_references WHERE active = 1"
        params = []
        if category:
            query += " AND LOWER(category) = LOWER(?)"
            params.append(category)
        query += " ORDER BY category ASC, sort_order ASC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
