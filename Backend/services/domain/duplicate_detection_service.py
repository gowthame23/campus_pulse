import sqlite3
from typing import List, Dict, Any, Optional

class DuplicateDetectionService:
    def __init__(self, db_path="storage/campus_pulse.db"):
        self.db_path = db_path

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def find_potential_duplicates(
        self,
        title: str,
        location_id: str,
        department_id: str,
        issue_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Finds potential duplicate complaints matching title keywords, location, or issue."""
        if not title:
            return []

        keywords = [k.lower() for k in title.strip().split() if len(k) > 3]
        if not keywords:
            return []

        query = "SELECT * FROM complaints WHERE location_id = ? AND department_id = ? AND status NOT IN ('Closed', 'Cancelled')"
        params = [location_id, department_id]

        with self._connect() as conn:
            rows = [dict(r) for r in conn.execute(query, params).fetchall()]

        matches = []
        for r in rows:
            c_title = (r.get("title") or "").lower()
            score = sum(1 for kw in keywords if kw in c_title)
            if score > 0:
                r["similarity_score"] = score
                matches.append(r)

        matches.sort(key=lambda x: x["similarity_score"], reverse=True)
        return matches[:limit]
