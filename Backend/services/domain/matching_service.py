import sqlite3
from typing import List, Dict, Any

class MatchingService:
    def __init__(self, db_path="storage/campus_pulse.db"):
        self.db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def find_lost_found_matches(self, item_id: str) -> List[Dict[str, Any]]:
        """Automated matching algorithm between Lost and Found reports."""
        with self._connect() as conn:
            target = conn.execute("SELECT * FROM lost_found_items WHERE item_id = ?", (item_id,)).fetchone()
            if not target:
                return []

            target_dict = dict(target)
            target_type = (target_dict.get("report_type") or "").upper()
            target_cat = (target_dict.get("category") or "").lower()

            opposite_type = "FOUND" if target_type == "LOST" else "LOST"
            opposite_rows = conn.execute(
                "SELECT * FROM lost_found_items WHERE UPPER(report_type) = ? AND status != 'Returned'",
                (opposite_type,),
            ).fetchall()

            matches = []
            target_words = set((target_dict.get("title") or "").lower().split())
            for row in opposite_rows:
                r_dict = dict(row)
                r_cat = (r_dict.get("category") or "").lower()
                r_words = set((r_dict.get("title") or "").lower().split())

                score = 0
                if target_cat and target_cat == r_cat:
                    score += 50
                overlap = len(target_words.intersection(r_words))
                score += overlap * 25

                if score > 0:
                    r_dict["match_score"] = min(100, score)
                    matches.append(r_dict)

            matches.sort(key=lambda x: x["match_score"], reverse=True)
            return matches
