import sqlite3
from typing import List, Dict, Any, Optional
from models.complaint import Complaint

class PublicComplaintService:
    def __init__(self, complaint_service, auth_service, notification_service, db_path="storage/campus_pulse.db"):
        self.complaint_service = complaint_service
        self.auth_service = auth_service
        self.notification_service = notification_service
        self.db_path = db_path

    def _db_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def list_public_locations(self) -> List[Dict[str, Any]]:
        with self._db_conn() as conn:
            rows = conn.execute("""
                SELECT DISTINCT l.location_id, l.name
                FROM locations l
                JOIN complaints c ON (l.location_id = c.location_id OR l.name = c.location_id)
                WHERE (c.visibility_type = 'Public' OR c.visibility_type = 'Community')
                  AND l.active = 1
                ORDER BY l.name ASC
            """).fetchall()
            return [dict(r) for r in rows]

    def list_public_departments(self, location_id: str) -> List[Dict[str, Any]]:
        with self._db_conn() as conn:
            rows = conn.execute("""
                SELECT DISTINCT d.department_id, d.name
                FROM departments d
                JOIN complaints c ON (d.department_id = c.department_id OR d.name = c.department_id)
                WHERE (c.visibility_type = 'Public' OR c.visibility_type = 'Community')
                  AND (c.location_id = ? OR c.location_id = (SELECT name FROM locations WHERE location_id = ?))
                  AND d.active = 1
                ORDER BY d.name ASC
            """, (location_id, location_id)).fetchall()
            return [dict(r) for r in rows]

    def list_public_issues(self, location_id: str, department_id: str) -> List[Dict[str, Any]]:
        with self._db_conn() as conn:
            rows = conn.execute("""
                SELECT DISTINCT category as issue_name
                FROM complaints
                WHERE (visibility_type = 'Public' OR visibility_type = 'Community')
                  AND (location_id = ? OR location_id = (SELECT name FROM locations WHERE location_id = ?))
                  AND (department_id = ? OR department_id = (SELECT name FROM departments WHERE department_id = ?))
                ORDER BY category ASC
            """, (location_id, location_id, department_id, department_id)).fetchall()
            return [dict(r) for r in rows]

    def list_public_complaints(
        self,
        location_id: Optional[str] = None,
        department_id: Optional[str] = None,
        issue_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        all_complaints = self.complaint_service.list_all(include_archived=False)

        # Filter public complaints only
        public_list = []
        for c in all_complaints:
            is_pub = c.visibility_type in ("Public", "Community") or getattr(c, "visibility", "") == "PUBLIC"
            if not is_pub:
                continue

            loc = self.auth_service.get_location(c.location_id)
            c_loc_id = loc.location_id if loc else c.location_id

            dept = self.auth_service.get_department(c.department_id)
            c_dept_id = dept.department_id if dept else c.department_id

            if location_id and c_loc_id != location_id:
                continue
            if department_id and c_dept_id != department_id:
                continue
            if issue_id and getattr(c, "issue_id", None) != issue_id and c.category != issue_id:
                continue
            if status and c.status.lower() != status.lower():
                continue
            if search:
                s = search.lower()
                num = (c.complaint_number or c.complaint_id or "").lower()
                title = (c.title or "").lower()
                desc = (c.description or "").lower()
                if s not in num and s not in title and s not in desc:
                    continue

            d = c.to_dict()
            d["affected_count"] = self.complaint_service.get_affected_count(c.complaint_id)

            # Enrich latest official update and expected completion
            updates = [h for h in c.history if "update" in h.get("message", "").lower() or "progress" in h.get("message", "").lower()]
            d["latest_update"] = updates[-1]["message"] if updates else (c.history[-1]["message"] if c.history else "Submitted")
            d["expected_completion"] = c.due_date or "Pending SLA"

            public_list.append(d)

        # Default sorting: Affected Students highest first, then newest complaint
        public_list.sort(key=lambda x: (x["affected_count"], x["created_at"]), reverse=True)
        return public_list

    def get_public_complaint(self, complaint_id: str, user_id: str) -> Dict[str, Any]:
        complaint = self.complaint_service.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")

        is_pub = complaint.visibility_type in ("Public", "Community") or getattr(complaint, "visibility", "") == "PUBLIC"
        if not is_pub:
            raise PermissionError("Access denied. Private complaint requested.")

        d = complaint.to_dict()
        d["affected_count"] = self.complaint_service.get_affected_count(complaint_id)
        d["has_joined"] = self.complaint_service.is_student_affected(complaint_id, user_id)

        # Summary Card payload
        loc = self.auth_service.get_location(complaint.location_id)
        dept = self.auth_service.get_department(complaint.department_id)
        updates = [h for h in complaint.history if "update" in h.get("message", "").lower() or "progress" in h.get("message", "").lower()]

        d["summary_card"] = {
            "complaint_number": getattr(complaint, "complaint_number", None) or complaint.complaint_id,
            "title": complaint.title or f"Public Issue ({complaint.category})",
            "location_name": loc.name if loc else complaint.location_id,
            "department_name": dept.name if dept else complaint.department_id,
            "issue_name": complaint.category or complaint.complaint_type,
            "status": complaint.status,
            "priority": complaint.priority or "Medium",
            "affected_count": d["affected_count"],
            "latest_update": updates[-1]["message"] if updates else (complaint.history[-1]["message"] if complaint.history else "Submitted"),
            "expected_completion": complaint.due_date or "Pending SLA"
        }
        return d

    def join_public_complaint(self, complaint_id: str, student_id: str, room_note: Optional[str] = None) -> Dict[str, Any]:
        complaint = self.complaint_service.get_complaint(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found.")

        is_pub = complaint.visibility_type in ("Public", "Community") or getattr(complaint, "visibility", "") == "PUBLIC"
        if not is_pub:
            raise PermissionError("Access denied. Private complaint requested.")

        if complaint.status in (Complaint.CLOSED, Complaint.AUTO_CLOSED):
            raise ValueError("Cannot join a closed complaint.")

        if self.complaint_service.is_student_affected(complaint_id, student_id):
            raise ValueError("You have already joined this complaint.")

        self.complaint_service.add_affected_student(complaint_id, student_id, room_note=room_note)

        new_count = self.complaint_service.get_affected_count(complaint_id)
        return {
            "message": "Successfully joined public complaint.",
            "complaint_id": complaint_id,
            "affected_count": new_count
        }
