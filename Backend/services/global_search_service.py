import json
import sqlite3
from pathlib import Path

from utils.helper import generate_id, now_string


class GlobalSearchService:
    ENTITY_TYPES = (
        "Complaint",
        "WorkOrder",
        "Visitor",
        "Asset",
        "Booking",
        "LostFound",
        "Feedback",
        "Announcement",
        "Document",
        "Report",
        "User",
        "Location",
        "Audit",
    )
    VISIBILITIES = ("Public", "Department", "Hostel", "Private", "AdminOnly")

    def __init__(
        self,
        notification_service=None,
        audit_service=None,
        db_path="storage/campus_pulse.db",
    ):
        self.db_path = Path(db_path)
        self.notification_service = notification_service
        self.audit_service = audit_service
        self.reindex_all()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ==========================================
    # 1. AUTOMATIC INDEX REBUILDER
    # ==========================================
    def reindex_all(self, performer_id="system"):
        now = now_string()
        with self._connect() as conn:
            # Reindex Complaints
            cmpls = conn.execute(
                "SELECT complaint_id, title, description, category, created_by, status, location_id, department_id, visibility_type FROM complaints WHERE (is_deleted = 0 OR is_deleted IS NULL)"
            ).fetchall()
            for c in cmpls:
                t_title = c["title"] or "Complaint"
                t_cat = c["category"] or "General"
                t_desc = c["description"] or ""
                conn.execute(
                    """
                    INSERT INTO search_index
                    (index_id, entity_type, entity_id, title, description, keywords, location_id, department_id, owner_id, visibility, last_indexed, created_at, updated_at)
                    VALUES (?, 'Complaint', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                        title=excluded.title, description=excluded.description, keywords=excluded.keywords,
                        location_id=excluded.location_id, department_id=excluded.department_id,
                        owner_id=excluded.owner_id, visibility=excluded.visibility,
                        last_indexed=excluded.last_indexed, updated_at=excluded.updated_at
                    """,
                    (
                        generate_id("IDX"),
                        c["complaint_id"],
                        t_title,
                        t_desc,
                        f"{c['complaint_id']} {t_cat} {c['status']}",
                        c["location_id"],
                        c["department_id"],
                        c["created_by"],
                        c["visibility_type"] or "Private",
                        now,
                        now,
                        now,
                    ),
                )

            # Reindex Work Orders (Legacy optional scaffold)
            try:
                wos = conn.execute(
                    "SELECT work_order_id, work_order_number, title, description, priority, status FROM work_orders WHERE is_deleted = 0"
                ).fetchall()
                for w in wos:
                    conn.execute(
                        """
                        INSERT INTO search_index
                        (index_id, entity_type, entity_id, title, description, keywords, visibility, last_indexed, created_at, updated_at)
                        VALUES (?, 'WorkOrder', ?, ?, ?, ?, 'Public', ?, ?, ?)
                        ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                            title=excluded.title, description=excluded.description, keywords=excluded.keywords, last_indexed=excluded.last_indexed
                        """,
                        (
                            generate_id("IDX"),
                            w["work_order_id"],
                            f"{w['work_order_number']} - {w['title']}",
                            w["description"],
                            f"{w['work_order_number']} {w['priority']} {w['status']}",
                            now,
                            now,
                            now,
                        ),
                    )
            except sqlite3.OperationalError:
                pass

            # Reindex Assets (Legacy optional scaffold)
            try:
                asts = conn.execute(
                    "SELECT asset_id, asset_code, asset_name, brand, model, serial_number, current_condition FROM assets WHERE is_deleted = 0"
                ).fetchall()
                for a in asts:
                    conn.execute(
                        """
                        INSERT INTO search_index
                        (index_id, entity_type, entity_id, title, description, keywords, visibility, last_indexed, created_at, updated_at)
                        VALUES (?, 'Asset', ?, ?, ?, ?, 'Public', ?, ?, ?)
                        ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                            title=excluded.title, description=excluded.description, keywords=excluded.keywords, last_indexed=excluded.last_indexed
                        """,
                        (
                            generate_id("IDX"),
                            a["asset_id"],
                            f"{a['asset_code']} - {a['asset_name']}",
                            f"Brand: {a['brand']} Model: {a['model']}",
                            f"{a['asset_code']} {a['serial_number']} {a['current_condition']}",
                            now,
                            now,
                            now,
                        ),
                    )
            except sqlite3.OperationalError:
                pass

            # Reindex Announcements
            anns = conn.execute(
                "SELECT announcement_id, title, summary, category, priority FROM announcements WHERE status = 'Published' AND is_deleted = 0"
            ).fetchall()
            for a in anns:
                conn.execute(
                    """
                    INSERT INTO search_index
                    (index_id, entity_type, entity_id, title, description, keywords, visibility, last_indexed, created_at, updated_at)
                    VALUES (?, 'Announcement', ?, ?, ?, ?, 'Public', ?, ?, ?)
                    ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                        title=excluded.title, description=excluded.description, keywords=excluded.keywords, last_indexed=excluded.last_indexed
                    """,
                    (
                        generate_id("IDX"),
                        a["announcement_id"],
                        a["title"],
                        a["summary"],
                        f"{a['category']} {a['priority']}",
                        now,
                        now,
                        now,
                    ),
                )

            # Reindex Visitors (Legacy optional scaffold)
            try:
                viss = conn.execute(
                    "SELECT r.request_id, v.full_name, v.phone_number, r.purpose, r.visit_date FROM visitor_requests r JOIN visitors v ON r.visitor_id = v.visitor_id"
                ).fetchall()
                for v in viss:
                    conn.execute(
                        """
                        INSERT INTO search_index
                        (index_id, entity_type, entity_id, title, description, keywords, visibility, last_indexed, created_at, updated_at)
                        VALUES (?, 'Visitor', ?, ?, ?, ?, 'Public', ?, ?, ?)
                        ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                            title=excluded.title, description=excluded.description, keywords=excluded.keywords, last_indexed=excluded.last_indexed
                        """,
                        (
                            generate_id("IDX"),
                            v["request_id"],
                            f"Visitor: {v['full_name']}",
                            v["purpose"],
                            f"{v['phone_number']} {v['visit_date']}",
                            now,
                            now,
                            now,
                        ),
                    )
            except sqlite3.OperationalError:
                pass

            # Reindex Audit Logs (Admin Only)
            auds = conn.execute(
                "SELECT audit_id, module, action, performed_by, description FROM audit_logs LIMIT 200"
            ).fetchall()
            for au in auds:
                conn.execute(
                    """
                    INSERT INTO search_index
                    (index_id, entity_type, entity_id, title, description, keywords, visibility, last_indexed, created_at, updated_at)
                    VALUES (?, 'Audit', ?, ?, ?, ?, 'AdminOnly', ?, ?, ?)
                    ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                        title=excluded.title, description=excluded.description, keywords=excluded.keywords, last_indexed=excluded.last_indexed
                    """,
                    (
                        generate_id("IDX"),
                        au["audit_id"],
                        f"Audit: {au['module']} {au['action']}",
                        au["description"],
                        f"{au['performed_by']} {au['module']}",
                        now,
                        now,
                        now,
                    ),
                )

        if self.audit_service and performer_id != "system":
            self.audit_service.log_event(
                module="Global Search",
                entity_type="SearchIndex",
                entity_id="GLOBAL_INDEX",
                action="REINDEX",
                performed_by=performer_id,
                description="Rebuilt global search engine index across all platform entities",
            )

        return {"message": "Search index rebuilt successfully."}

    # ==========================================
    # 2. SEARCH & SUGGESTIONS ENGINE
    # ==========================================
    def _build_visibility_clause(self, conn, user_role, user_id, user_department_id, user_location_id):
        if (user_role or "").lower() == "administrator":
            return "", []

        loc_ids = [user_location_id] if user_location_id else []
        dept_ids = [user_department_id] if user_department_id else []

        if user_id:
            u_r = (user_role or "").lower()
            if u_r == "app_manager":
                rows = conn.execute("SELECT location_id FROM locations WHERE app_manager_id = ?", (user_id,)).fetchall()
                loc_ids.extend([r["location_id"] for r in rows])
                sp_row = conn.execute("SELECT assigned_locations FROM staff_profiles WHERE user_id = ?", (user_id,)).fetchone()
                if sp_row and sp_row["assigned_locations"]:
                    try:
                        loc_ids.extend(json.loads(sp_row["assigned_locations"]) or [])
                    except Exception:
                        pass
            elif u_r == "location_in_charge":
                rows = conn.execute("SELECT location_id FROM locations WHERE in_charge_id = ?", (user_id,)).fetchall()
                loc_ids.extend([r["location_id"] for r in rows])
                sp_row = conn.execute("SELECT assigned_locations FROM staff_profiles WHERE user_id = ?", (user_id,)).fetchone()
                if sp_row and sp_row["assigned_locations"]:
                    try:
                        loc_ids.extend(json.loads(sp_row["assigned_locations"]) or [])
                    except Exception:
                        pass
            elif u_r == "coordinator":
                asgns = conn.execute("SELECT department_id FROM coordinator_assignments WHERE coordinator_id = ? AND (status IS NULL OR status = 'Active')", (user_id,)).fetchall()
                dept_ids.extend([a["department_id"] for a in asgns])

        loc_ids = list(set([l for l in loc_ids if l]))
        dept_ids = list(set([d for d in dept_ids if d]))

        params = []
        clause = " AND visibility != 'AdminOnly'"

        vis_branches = ["visibility = 'Public'"]
        if user_id:
            vis_branches.append("owner_id = ?")
            params.append(user_id)

        if dept_ids:
            dept_ph = ",".join(["?"] * len(dept_ids))
            vis_branches.append(f"(visibility = 'Department' AND department_id IN ({dept_ph}))")
            params.extend(dept_ids)
        elif user_department_id:
            vis_branches.append("(visibility = 'Department' AND department_id = ?)")
            params.append(user_department_id)

        if loc_ids:
            loc_ph = ",".join(["?"] * len(loc_ids))
            vis_branches.append(f"(visibility = 'Hostel' AND location_id IN ({loc_ph}))")
            params.extend(loc_ids)
        elif user_location_id:
            vis_branches.append("(visibility = 'Hostel' AND location_id = ?)")
            params.append(user_location_id)

        clause += f" AND ({' OR '.join(vis_branches)})"
        return clause, params

    def search(
        self, query, entity_type=None, user_role="student", user_id=None,
        user_department_id=None, user_location_id=None, limit=50
    ):
        if not query or not query.strip():
            return []

        clean_q = query.strip()
        term = f"%{clean_q}%"
        sql = "SELECT * FROM search_index WHERE (title LIKE ? OR description LIKE ? OR keywords LIKE ? OR entity_id LIKE ?)"
        params = [term, term, term, term]

        with self._connect() as conn:
            vis_clause, vis_params = self._build_visibility_clause(
                conn, user_role, user_id, user_department_id, user_location_id
            )
            sql += vis_clause
            params.extend(vis_params)

            if entity_type:
                sql += " AND entity_type = ?"
                params.append(entity_type)

            sql += " ORDER BY CASE WHEN title LIKE ? THEN 1 WHEN keywords LIKE ? THEN 2 ELSE 3 END, created_at DESC LIMIT ?"
            params.extend([f"{clean_q}%", f"{clean_q}%", limit])

            results = [dict(r) for r in conn.execute(sql, params).fetchall()]

            # Log search history
            if user_id:
                conn.execute(
                    "INSERT INTO search_history (history_id, user_id, search_query, result_count, searched_at) VALUES (?, ?, ?, ?, ?)",
                    (generate_id("HIS"), user_id, clean_q, len(results), now_string()),
                )

        return results

    def get_suggestions(self, query, user_role="student", user_id=None, user_department_id=None, user_location_id=None, limit=10):
        if not query or not query.strip():
            return []

        clean_q = query.strip()
        term = f"%{clean_q}%"
        sql = "SELECT entity_type, entity_id, title FROM search_index WHERE (title LIKE ? OR keywords LIKE ? OR entity_id LIKE ?)"
        params = [term, term, term]

        with self._connect() as conn:
            vis_clause, vis_params = self._build_visibility_clause(
                conn, user_role, user_id, user_department_id, user_location_id
            )
            sql += vis_clause
            params.extend(vis_params)
            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    # ==========================================
    # 3. SEARCH HISTORY & SAVED SEARCHES
    # ==========================================
    def get_history(self, user_id):
        with self._connect() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM search_history WHERE user_id = ? ORDER BY searched_at DESC LIMIT 30",
                    (user_id,),
                ).fetchall()
            ]

    def clear_history(self, user_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM search_history WHERE user_id = ?", (user_id,))
        return {"message": "Search history cleared."}

    def save_search(self, user_id, search_name, query, filters=None):
        sid = generate_id("SVD")
        now = now_string()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO saved_searches (saved_search_id, user_id, search_name, query, filters_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, search_name) DO UPDATE SET query=excluded.query, filters_json=excluded.filters_json
                """,
                (
                    sid,
                    user_id,
                    search_name.strip(),
                    query.strip(),
                    json.dumps(filters or {}),
                    now,
                ),
            )
        return {"saved_search_id": sid, "search_name": search_name, "query": query}

    def get_saved_searches(self, user_id):
        with self._connect() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM saved_searches WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,),
                ).fetchall()
            ]

    def delete_saved_search(self, saved_search_id, user_id):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM saved_searches WHERE saved_search_id = ? AND user_id = ?",
                (saved_search_id, user_id),
            )
        return {"message": "Saved search deleted."}
