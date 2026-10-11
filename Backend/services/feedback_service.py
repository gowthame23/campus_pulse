import sqlite3
from pathlib import Path

from utils.helper import generate_id, now_string


class FeedbackService:
    FEEDBACK_TYPES = ("Complaint", "WorkOrder", "Booking", "LostFound", "Visitor")
    QUESTION_TYPES = ("Rating", "Text", "Yes/No", "Multiple Choice", "Checkbox")
    STATUSES = ("Pending Review", "Reviewed", "Responded", "Archived")

    def __init__(
        self,
        notification_service=None,
        audit_service=None,
        db_path="storage/campus_pulse.db",
    ):
        self.db_path = Path(db_path)
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
                "SELECT template_id FROM feedback_templates LIMIT 1"
            ).fetchone()
            if not row:
                now = now_string()
                templates = [
                    (
                        "TPL_CMPL",
                        "Complaint",
                        "Complaint Resolution Satisfaction Survey",
                    ),
                    ("TPL_WO", "WorkOrder", "Technician Repair Quality Survey"),
                    ("TPL_BOOK", "Booking", "Resource & Facility Booking Experience"),
                    ("TPL_LF", "LostFound", "Lost & Found Return Satisfaction"),
                    (
                        "TPL_VIS",
                        "Visitor",
                        "Campus Visitor Security & Gate Pass Survey",
                    ),
                ]
                for tid, ftype, title in templates:
                    conn.execute(
                        "INSERT INTO feedback_templates (template_id, feedback_type, title, active, created_at) VALUES (?, ?, ?, 1, ?)",
                        (tid, ftype, title, now),
                    )

                questions = [
                    (
                        "TPL_CMPL",
                        "Q_CMPL_1",
                        "How satisfied are you with the overall resolution speed?",
                        "Rating",
                        1,
                        1,
                    ),
                    (
                        "TPL_CMPL",
                        "Q_CMPL_2",
                        "Was the reported issue resolved completely without recurrence?",
                        "Yes/No",
                        1,
                        2,
                    ),
                    (
                        "TPL_CMPL",
                        "Q_CMPL_3",
                        "How would you rate the communication and behavior of campus staff?",
                        "Rating",
                        1,
                        3,
                    ),
                    (
                        "TPL_WO",
                        "Q_WO_1",
                        "How satisfied are you with the quality of repair work performed?",
                        "Rating",
                        1,
                        1,
                    ),
                    (
                        "TPL_WO",
                        "Q_WO_2",
                        "Did the technician arrive promptly and clean up after work?",
                        "Yes/No",
                        1,
                        2,
                    ),
                ]
                for tid, qid, qtext, qtype, req, order in questions:
                    conn.execute(
                        "INSERT INTO feedback_questions (question_id, template_id, question, question_type, required, display_order) VALUES (?, ?, ?, ?, ?, ?)",
                        (qid, tid, qtext, qtype, req, order),
                    )

                # Seed sample feedback
                fid = "FB_1001"
                conn.execute(
                    """
                    INSERT INTO feedback
                    (feedback_id, feedback_type, reference_id, submitted_by, assigned_to, rating, title, comments, anonymous, status, submitted_at, updated_at, is_deleted)
                    VALUES (?, 'Complaint', 'CP-1001', 'STU_001', 'COORD_ELEC', 5, 'Prompt Electrical Repair', 'Technician fixed fan regulator within 2 hours. Excellent service!', 0, 'Responded', ?, ?, 0)
                    """,
                    (fid, now, now),
                )

                conn.execute(
                    "INSERT INTO feedback_responses (response_id, feedback_id, responded_by, response, created_at) VALUES (?, ?, 'COORD_ELEC', 'Thank you for your feedback! Glad we could resolve it quickly.', ?)",
                    (generate_id("RES"), fid, now),
                )

    # ==========================================
    # 1. TEMPLATES & QUESTIONS API
    # ==========================================
    def list_templates(self, feedback_type=None):
        query = "SELECT * FROM feedback_templates WHERE active = 1"
        params = []
        if feedback_type:
            query += " AND feedback_type = ?"
            params.append(feedback_type)
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def create_template(self, feedback_type, title):
        tid = generate_id("TPL")
        now = now_string()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO feedback_templates (template_id, feedback_type, title, active, created_at) VALUES (?, ?, ?, 1, ?)",
                (tid, feedback_type, title.strip(), now),
            )
        return {"template_id": tid, "feedback_type": feedback_type, "title": title}

    def add_question(
        self, template_id, question, question_type="Rating", required=1, display_order=0
    ):
        qid = generate_id("QST")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO feedback_questions (question_id, template_id, question, question_type, required, display_order) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    qid,
                    template_id,
                    question.strip(),
                    question_type,
                    1 if required else 0,
                    display_order,
                ),
            )
        return {
            "question_id": qid,
            "question": question,
            "question_type": question_type,
        }

    def get_template_questions(self, template_id_or_type):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT template_id FROM feedback_templates WHERE template_id = ? OR feedback_type = ? LIMIT 1",
                (template_id_or_type, template_id_or_type),
            ).fetchone()
            if not row:
                return []
            tid = row["template_id"]
            return [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM feedback_questions WHERE template_id = ? ORDER BY display_order ASC",
                    (tid,),
                ).fetchall()
            ]

    # ==========================================
    # 2. FEEDBACK SUBMISSIONS
    # ==========================================
    def submit_feedback(
        self,
        feedback_type,
        reference_id,
        submitted_by,
        rating,
        title="",
        comments="",
        anonymous=False,
        answers=None,
    ):
        if rating < 1 or rating > 5:
            raise ValueError("Rating must be an integer between 1 and 5.")
        if not reference_id or not reference_id.strip():
            raise ValueError("Reference ID is required.")

        # Check existing active feedback
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT feedback_id FROM feedback WHERE feedback_type = ? AND reference_id = ? AND submitted_by = ? AND is_deleted = 0",
                (feedback_type, reference_id, submitted_by),
            ).fetchone()
            if existing:
                raise ValueError(
                    f"You have already submitted feedback for this {feedback_type}."
                )

        eligible = {
            (p["feedback_type"], p["reference_id"])
            for p in self.list_pending_services(submitted_by)
        }
        if (feedback_type, reference_id.strip()) not in eligible:
            raise ValueError("Feedback can only be submitted for your own closed complaints.")

        with self._connect() as conn:
            assigned_to = conn.execute(
                "SELECT assigned_to FROM complaints WHERE complaint_id = ?",
                (reference_id.strip(),),
            ).fetchone()["assigned_to"]

        fid = generate_id("FB")
        now = now_string()
        status = "Pending Review"

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO feedback
                (feedback_id, feedback_type, reference_id, submitted_by, assigned_to, rating, title, comments, anonymous, status, submitted_at, updated_at, is_deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    fid,
                    feedback_type,
                    reference_id.strip(),
                    submitted_by,
                    assigned_to,
                    int(rating),
                    title.strip(),
                    comments.strip(),
                    1 if anonymous else 0,
                    status,
                    now,
                    now,
                ),
            )

            if answers and isinstance(answers, list):
                for ans in answers:
                    qid = ans.get("question_id")
                    aval = str(ans.get("answer_value", ""))
                    if qid and aval:
                        conn.execute(
                            "INSERT INTO feedback_answers (answer_id, feedback_id, question_id, answer_value) VALUES (?, ?, ?, ?)",
                            (generate_id("ANS"), fid, qid, aval),
                        )

        fb = self.get_feedback(fid)

        # Low Rating Alert (1 or 2 stars)
        if int(rating) <= 2 and self.notification_service:
            self.notification_service.publish(
                receiver_id="Coordinator",
                title=f"⚠️ LOW RATING ALERT ({rating} Stars)",
                message=f"Low rating received on {feedback_type} #{reference_id}: '{comments or 'No comments'}'",
                module="Feedback & Satisfaction",
                notification_type="low_rating_alert",
                reference_type="Feedback",
                reference_id=fid,
                priority="High",
            )

        if self.audit_service:
            self.audit_service.log_event(
                module="Feedback & Satisfaction",
                entity_type="Feedback",
                entity_id=fid,
                action="CREATE",
                performed_by=submitted_by,
                description=f"Submitted {rating}-star feedback for {feedback_type} #{reference_id}",
            )

        return fb

    def get_feedback(self, feedback_id, user=None):
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT f.*, c.location_id as ref_location_id, c.department_id as ref_department_id
                FROM feedback f
                LEFT JOIN complaints c ON f.reference_id = c.complaint_id
                WHERE f.feedback_id = ? AND f.is_deleted = 0
                """,
                (feedback_id,),
            ).fetchone()
            if not row:
                return None
            fb = dict(row)

            if user:
                role = (getattr(user, "role", "") or "").lower()
                if role == "student" and fb.get("submitted_by") != user.user_id:
                    return None
                elif role == "coordinator":
                    u_loc = getattr(user, "location_id", "") or ""
                    u_dept = getattr(user, "department_id", "") or ""
                    is_owner_or_assigned = (
                        fb.get("submitted_by") == user.user_id
                        or fb.get("assigned_to") == user.user_id
                    )
                    in_scope = (
                        fb.get("ref_location_id") == u_loc
                        and fb.get("ref_department_id") == u_dept
                    )
                    if not (is_owner_or_assigned or in_scope):
                        return None
                elif role in ("location_in_charge", "warden", "app_manager"):
                    u_loc = getattr(user, "location_id", "") or ""
                    is_owner_or_assigned = (
                        fb.get("submitted_by") == user.user_id
                        or fb.get("assigned_to") == user.user_id
                    )
                    in_scope = fb.get("ref_location_id") == u_loc
                    if not (is_owner_or_assigned or in_scope):
                        return None

            fb["answers"] = [
                dict(a)
                for a in conn.execute(
                    "SELECT a.*, q.question FROM feedback_answers a JOIN feedback_questions q ON a.question_id = q.question_id WHERE a.feedback_id = ?",
                    (feedback_id,),
                ).fetchall()
            ]
            fb["responses"] = [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM feedback_responses WHERE feedback_id = ? ORDER BY created_at ASC",
                    (feedback_id,),
                ).fetchall()
            ]
            return fb

    def list_feedback(
        self,
        feedback_type=None,
        assigned_to=None,
        rating=None,
        status=None,
        submitted_by=None,
        q=None,
        user=None,
    ):
        query = """
        SELECT f.*
        FROM feedback f
        LEFT JOIN complaints c ON f.reference_id = c.complaint_id
        WHERE f.is_deleted = 0
        """
        params = []

        if feedback_type:
            query += " AND f.feedback_type = ?"
            params.append(feedback_type)
        if assigned_to:
            query += " AND f.assigned_to = ?"
            params.append(assigned_to)
        if rating:
            query += " AND f.rating = ?"
            params.append(int(rating))
        if status:
            query += " AND f.status = ?"
            params.append(status)
        if submitted_by:
            query += " AND f.submitted_by = ?"
            params.append(submitted_by)

        if user:
            role = (getattr(user, "role", "") or "").lower()
            if role == "student":
                query += " AND f.submitted_by = ?"
                params.append(user.user_id)
            elif role == "coordinator":
                u_loc = getattr(user, "location_id", "") or ""
                u_dept = getattr(user, "department_id", "") or ""
                query += " AND (f.assigned_to = ? OR f.submitted_by = ? OR (c.location_id = ? AND c.department_id = ?))"
                params.extend([user.user_id, user.user_id, u_loc, u_dept])
            elif role in ("location_in_charge", "warden", "app_manager"):
                u_loc = getattr(user, "location_id", "") or ""
                query += " AND (f.assigned_to = ? OR f.submitted_by = ? OR c.location_id = ?)"
                params.extend([user.user_id, user.user_id, u_loc])

        if q:
            term = f"%{q.strip()}%"
            query += " AND (f.title LIKE ? OR f.comments LIKE ? OR f.reference_id LIKE ?)"
            params.extend([term, term, term])

        query += " ORDER BY f.submitted_at DESC"

        with self._connect() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def add_staff_response(self, feedback_id, responded_by, response_text):
        if not response_text or not response_text.strip():
            raise ValueError("Response text cannot be empty.")

        fb = self.get_feedback(feedback_id)
        if not fb:
            raise ValueError("Feedback not found.")

        rid = generate_id("RES")
        now = now_string()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO feedback_responses (response_id, feedback_id, responded_by, response, created_at) VALUES (?, ?, ?, ?, ?)",
                (rid, feedback_id, responded_by, response_text.strip(), now),
            )
            conn.execute(
                "UPDATE feedback SET status = 'Responded', updated_at = ? WHERE feedback_id = ?",
                (now, feedback_id),
            )

        if self.notification_service and fb["submitted_by"]:
            self.notification_service.publish(
                receiver_id=fb["submitted_by"],
                title="Response Added to Your Feedback",
                message=f"Campus Staff responded: '{response_text.strip()[:60]}...'",
                module="Feedback & Satisfaction",
                notification_type="feedback_response",
                reference_type="Feedback",
                reference_id=feedback_id,
                priority="Medium",
            )

        return self.get_feedback(feedback_id)

    # ==========================================
    # 3. ANALYTICS & PENDING SERVICES
    # ==========================================
    def get_analytics(self):
        with self._connect() as conn:
            total = conn.execute(
                "SELECT COUNT(*) FROM feedback WHERE is_deleted = 0"
            ).fetchone()[0]
            if total == 0:
                return {
                    "average_rating": 0.0,
                    "total_feedback": 0,
                    "response_rate": 0.0,
                    "low_ratings_count": 0,
                    "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                }

            avg_rating = (
                conn.execute(
                    "SELECT AVG(rating) FROM feedback WHERE is_deleted = 0"
                ).fetchone()[0]
                or 0.0
            )
            responded = conn.execute(
                "SELECT COUNT(*) FROM feedback WHERE status = 'Responded' AND is_deleted = 0"
            ).fetchone()[0]
            low_count = conn.execute(
                "SELECT COUNT(*) FROM feedback WHERE rating <= 2 AND is_deleted = 0"
            ).fetchone()[0]

            dist = {}
            for r in range(1, 6):
                dist[r] = conn.execute(
                    "SELECT COUNT(*) FROM feedback WHERE rating = ? AND is_deleted = 0",
                    (r,),
                ).fetchone()[0]

            return {
                "average_rating": round(float(avg_rating), 2),
                "total_feedback": total,
                "response_rate": round((responded / total) * 100, 1),
                "low_ratings_count": low_count,
                "rating_distribution": dist,
            }

    def list_pending_services(self, user_id):
        """Discovers closed complaints / completed bookings for user that have no feedback yet."""
        with self._connect() as conn:
            # 1. Closed Complaints without feedback
            closed_cmpl = conn.execute(
                """
                SELECT c.complaint_id as reference_id, 'Complaint' as feedback_type, c.title, c.updated_at as completed_at
                FROM complaints c
                LEFT JOIN feedback f ON c.complaint_id = f.reference_id AND f.feedback_type = 'Complaint' AND f.submitted_by = ?
                WHERE c.created_by = ? AND LOWER(c.status) = 'closed' AND f.feedback_id IS NULL
                """,
                (user_id, user_id),
            ).fetchall()

            return [dict(r) for r in closed_cmpl]
