import sqlite3
from pathlib import Path

from utils.helper import generate_id, now_string


class CommentService:
    def __init__(self, db_path="storage/campus_pulse.db"):
        self.db_path = Path(db_path)

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def get_comments(self, complaint_id):
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM comments WHERE complaint_id = ? ORDER BY created_at ASC",
                (complaint_id,),
            ).fetchall()
            return [
                {
                    "comment_id": r["comment_id"],
                    "complaint_id": r["complaint_id"],
                    "user_id": r["user_id"],
                    "message": r["message"],
                    "created_at": r["created_at"],
                    "is_internal": (
                        bool(r["is_internal"]) if "is_internal" in r.keys() else False
                    ),
                }
                for r in rows
            ]

    def add_comment(self, complaint_id, user_id, message, is_internal=False):
        comment_id = generate_id("CMT")
        created_at = now_string()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO comments (comment_id, complaint_id, user_id, message, created_at, is_internal)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    comment_id,
                    complaint_id,
                    user_id,
                    message,
                    created_at,
                    int(is_internal),
                ),
            )
        return {
            "comment_id": comment_id,
            "complaint_id": complaint_id,
            "user_id": user_id,
            "message": message,
            "created_at": created_at,
            "is_internal": is_internal,
        }
