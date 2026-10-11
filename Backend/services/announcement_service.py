import sqlite3
from pathlib import Path

from utils.helper import generate_id, now_string


class AnnouncementService:
    CATEGORIES = (
        "Academic",
        "Examination",
        "Placement",
        "Hostel",
        "Sports",
        "Library",
        "Events",
        "Club Activities",
        "Maintenance",
        "Emergency",
        "Administration",
        "Mess",
        "General",
        "Other",
    )
    PRIORITIES = ("Low", "Normal", "High", "Critical")
    STATUSES = ("Draft", "Scheduled", "Published", "Expired", "Archived", "Cancelled")
    TARGET_TYPES = (
        "Campus",
        "Building",
        "Hostel",
        "Department",
        "Role",
        "User",
        "Batch",
        "Program",
        "Year",
        "Section",
    )

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
            for col_def in [
                ("is_pinned", "INTEGER DEFAULT 0"),
                ("attachment_url", "TEXT"),
                ("target_type", "TEXT DEFAULT 'ALL'"),
                ("target_id", "TEXT"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE announcements ADD COLUMN {col_def[0]} {col_def[1]}")
                except Exception:
                    pass
            row = conn.execute(
                "SELECT announcement_id FROM announcements LIMIT 1"
            ).fetchone()
            if not row:
                now = now_string()
                aid1 = "ANN_CRIT_01"
                conn.execute(
                    """
                    INSERT INTO announcements
                    (announcement_id, title, summary, content, category, priority, created_by, published_by, status, visibility, requires_acknowledgement, created_at, updated_at, is_deleted)
                    VALUES (?, ?, ?, ?, 'Emergency', 'Critical', 'system', 'system', 'Published', 'Public', 1, ?, ?, 0)
                    """,
                    (
                        aid1,
                        "URGENT: Campus Maintenance Notice & Electrical Outage",
                        "Scheduled electrical maintenance for Block A & B on Saturday.",
                        "Dear Students & Staff, Please note that scheduled electrical maintenance will take place across Hostel Block A and Academic Block B on Saturday from 09:00 AM to 02:00 PM.",
                        now,
                        now,
                    ),
                )
                conn.execute(
                    "INSERT INTO announcement_targets (target_id, announcement_id, target_type, target_value) VALUES (?, ?, 'Campus', 'All')",
                    (generate_id("TGT"), aid1),
                )

                aid2 = "ANN_ACAD_02"
                conn.execute(
                    """
                    INSERT INTO announcements
                    (announcement_id, title, summary, content, category, priority, created_by, published_by, status, visibility, requires_acknowledgement, created_at, updated_at, is_deleted)
                    VALUES (?, ?, ?, ?, 'Examination', 'High', 'system', 'system', 'Published', 'Public', 0, ?, ?, 0)
                    """,
                    (
                        aid2,
                        "Mid-Semester Examination Schedule Published",
                        "Check your portal for the updated timetable.",
                        "The official mid-semester examination timetable for all undergraduate and postgraduate programs has been released. Please check your student portal dashboard.",
                        now,
                        now,
                    ),
                )
                conn.execute(
                    "INSERT INTO announcement_targets (target_id, announcement_id, target_type, target_value) VALUES (?, ?, 'Role', 'Student')",
                    (generate_id("TGT"), aid2),
                )

    # ==========================================
    # 1. ANNOUNCEMENT CRUD
    # ==========================================
    def list_announcements(
        self,
        user=None,
        category=None,
        priority=None,
        status=None,
        q=None,
        include_deleted=False,
    ):
        self.process_scheduled_and_expired()

        query = "SELECT a.* FROM announcements a WHERE 1=1"
        params = []

        if not include_deleted:
            query += " AND (a.is_deleted = 0 OR a.is_deleted IS NULL)"

        # Role & Targeting Scoping
        if user:
            role = (user.role or "").lower()
            if role == "student":
                query += """ AND a.status = 'Published' AND (
                    a.visibility = 'Public' OR
                    a.announcement_id IN (
                        SELECT announcement_id FROM announcement_targets
                        WHERE target_value IN ('All', 'Student', ?, ?, ?)
                    )
                )"""
                dept = getattr(user, "department_id", "") or ""
                loc = getattr(user, "location_id", "") or ""
                params.extend([user.user_id, dept, loc])

        if category:
            query += " AND LOWER(a.category) = LOWER(?)"
            params.append(category)
        if priority:
            query += " AND LOWER(a.priority) = LOWER(?)"
            params.append(priority)
        if status:
            query += " AND a.status = ?"
            params.append(status)

        if q:
            term = f"%{q.strip()}%"
            query += " AND (a.title LIKE ? OR a.summary LIKE ? OR a.content LIKE ?)"
            params.extend([term, term, term])

        # Critical & High priority pinned at top
        query += " ORDER BY CASE a.priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Normal' THEN 3 ELSE 4 END ASC, a.created_at DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            announcements = []
            for r in rows:
                ann = self._row_to_dict(r)
                if user:
                    ann["is_read"] = self.is_read_by_user(
                        ann["announcement_id"], user.user_id
                    )
                    ann["is_acknowledged"] = self.is_acknowledged_by_user(
                        ann["announcement_id"], user.user_id
                    )
                announcements.append(ann)
            return announcements

    def get_announcement(self, announcement_id, user=None):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM announcements WHERE announcement_id = ? AND (is_deleted = 0 OR is_deleted IS NULL)",
                (announcement_id,),
            ).fetchone()
            if not row:
                return None
            ann = self._row_to_dict(row)
            ann["targets"] = self.get_targets(announcement_id)
            ann["attachments"] = self.get_attachments(announcement_id)
            if user:
                ann["is_read"] = self.is_read_by_user(announcement_id, user.user_id)
                ann["is_acknowledged"] = self.is_acknowledged_by_user(
                    announcement_id, user.user_id
                )
            return ann

    def create_announcement(
        self,
        title,
        content=None,
        summary="",
        category="General",
        priority="Normal",
        targets=None,
        requires_acknowledgement=False,
        publish_at=None,
        expire_at=None,
        created_by="system",
        user_role="Administrator",
        description=None,
        target=None,
        target_type=None,
        target_id=None,
        is_pinned=False,
        expires_at=None,
        attachment_url=None,
    ):
        # 1. Creator Role Guard - Only staff with administrative or location authority can create announcements
        role_lower = (user_role or "").lower()
        if role_lower not in ("administrator", "app_manager", "location_in_charge", "warden"):
            raise PermissionError("Only staff with administrative or location authority can create announcements.")

        content = description or content or summary
        if not title or len(title.strip()) > 200:
            raise ValueError("Title is required and must be under 200 characters.")
        if not content or not content.strip():
            raise ValueError("Announcement Description is required.")

        # Normalize priority (HIGH -> High, MEDIUM -> Medium, LOW -> Low)
        pr_upper = (priority or "").upper()
        if pr_upper == "HIGH":
            priority = "High"
        elif pr_upper == "MEDIUM":
            priority = "Medium"
        elif pr_upper == "LOW":
            priority = "Low"
        elif priority not in self.PRIORITIES:
            priority = "Normal"

        expire_at = expires_at or expire_at

        # Target normalizing
        target_type = target_type or "Campus"
        target_val = target or target_id or "All"
        if not targets:
            targets = [{"target_type": target_type, "target_value": target_val}]

        aid = generate_id("ANN")
        now = now_string()
        initial_status = "Scheduled" if publish_at and publish_at > now else "Published"

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO announcements
                (announcement_id, title, summary, content, category, priority, created_by, published_by, status, visibility, requires_acknowledgement, publish_at, expire_at, created_at, updated_at, is_pinned, attachment_url, target_type, target_id, is_deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Public', ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    aid,
                    title.strip(),
                    summary.strip(),
                    content.strip(),
                    category,
                    priority,
                    created_by,
                    created_by if initial_status == "Published" else None,
                    initial_status,
                    int(requires_acknowledgement),
                    publish_at,
                    expire_at,
                    now,
                    now,
                    int(is_pinned),
                    attachment_url,
                    target_type,
                    target_val,
                ),
            )

        if targets:
            self.set_targets(aid, targets)

        ann = self.get_announcement(aid)

        # Notify if Published immediately
        if initial_status == "Published" and self.notification_service:
            notif_priority = (
                "Critical"
                if priority == "Critical"
                else "High" if priority == "High" else "Medium"
            )
            self.notification_service.publish(
                receiver_id="All",
                title=f"[{priority.upper()}] {title}",
                message=summary or content[:100],
                module="Announcements",
                notification_type="announcement",
                reference_type="Announcement",
                reference_id=aid,
                priority=notif_priority,
            )

        if self.audit_service:
            self.audit_service.log_event(
                module="Announcements",
                entity_type="Announcement",
                entity_id=aid,
                action="CREATE",
                performed_by=created_by,
                performed_role=user_role,
                new_value=ann,
                description=f"Created {priority} announcement '{title}' ({initial_status})",
            )

        return ann

    def update_announcement(self, announcement_id, updates, performer_id="system"):
        ann = self.get_announcement(announcement_id)
        if not ann:
            raise ValueError("Announcement not found.")

        allowed = (
            "title",
            "summary",
            "content",
            "category",
            "priority",
            "status",
            "requires_acknowledgement",
            "publish_at",
            "expire_at",
        )
        set_clauses = []
        params = []
        for k in allowed:
            if k in updates:
                set_clauses.append(f"{k} = ?")
                params.append(updates[k])

        if set_clauses:
            now = now_string()
            set_clauses.append("updated_at = ?")
            params.append(now)
            params.append(announcement_id)
            with self._connect() as conn:
                conn.execute(
                    f"UPDATE announcements SET {', '.join(set_clauses)} WHERE announcement_id = ?",
                    params,
                )

        updated = self.get_announcement(announcement_id)
        if self.audit_service:
            self.audit_service.log_event(
                module="Announcements",
                entity_type="Announcement",
                entity_id=announcement_id,
                action="UPDATE",
                performed_by=performer_id,
                old_value=ann,
                new_value=updated,
                description=f"Updated announcement '{ann['title']}'",
            )

        return updated

    def delete_announcement(self, announcement_id, performer_id="system"):
        ann = self.get_announcement(announcement_id)
        if not ann:
            raise ValueError("Announcement not found.")

        now = now_string()
        with self._connect() as conn:
            conn.execute(
                "UPDATE announcements SET is_deleted = 1, deleted_at = ?, deleted_by = ?, status = 'Cancelled' WHERE announcement_id = ?",
                (now, performer_id, announcement_id),
            )

        if self.audit_service:
            self.audit_service.log_event(
                module="Announcements",
                entity_type="Announcement",
                entity_id=announcement_id,
                action="SOFT_DELETE",
                performed_by=performer_id,
                description=f"Soft deleted announcement '{ann['title']}'",
            )
        return {"message": "Announcement soft deleted successfully."}

    # ==========================================
    # 2. TARGETING ENGINE
    # ==========================================
    def set_targets(self, announcement_id, targets_list):
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM announcement_targets WHERE announcement_id = ?",
                (announcement_id,),
            )
            for t in targets_list:
                ttype = t.get("target_type", "Campus")
                tval = t.get("target_value", "All")
                conn.execute(
                    "INSERT INTO announcement_targets (target_id, announcement_id, target_type, target_value) VALUES (?, ?, ?, ?)",
                    (generate_id("TGT"), announcement_id, ttype, tval),
                )

    def get_targets(self, announcement_id):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM announcement_targets WHERE announcement_id = ?",
                (announcement_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ==========================================
    # 3. ATTACHMENTS
    # ==========================================
    def add_attachment(
        self, announcement_id, file_name, file_path, file_size, file_type, uploaded_by
    ):
        att_id = generate_id("ATT")
        now = now_string()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO announcement_attachments
                (attachment_id, announcement_id, file_name, file_path, file_size, file_type, uploaded_by, uploaded_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    att_id,
                    announcement_id,
                    file_name,
                    file_path,
                    file_size,
                    file_type,
                    uploaded_by,
                    now,
                ),
            )
        return {
            "attachment_id": att_id,
            "announcement_id": announcement_id,
            "file_name": file_name,
            "file_path": file_path,
        }

    def get_attachments(self, announcement_id):
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM announcement_attachments WHERE announcement_id = ?",
                (announcement_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ==========================================
    # 4. READ TRACKING & ACKNOWLEDGEMENTS
    # ==========================================
    def mark_read(self, announcement_id, user_id, device=None, ip_address=None):
        rid = generate_id("RD")
        now = now_string()
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO announcement_reads (read_id, announcement_id, user_id, read_at, device, ip_address) VALUES (?, ?, ?, ?, ?, ?)",
                    (rid, announcement_id, user_id, now, device, ip_address),
                )
        except Exception:
            pass
        return {"status": "read", "read_at": now}

    def is_read_by_user(self, announcement_id, user_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT read_id FROM announcement_reads WHERE announcement_id = ? AND user_id = ?",
                (announcement_id, user_id),
            ).fetchone()
            return bool(row)

    def acknowledge(self, announcement_id, user_id, remarks=""):
        ack_id = generate_id("ACK")
        now = now_string()
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO announcement_acknowledgements (ack_id, announcement_id, user_id, acknowledged_at, remarks) VALUES (?, ?, ?, ?, ?)",
                (ack_id, announcement_id, user_id, now, remarks),
            )

        if self.audit_service:
            self.audit_service.log_event(
                module="Announcements",
                entity_type="Announcement",
                entity_id=announcement_id,
                action="UPDATE",
                performed_by=user_id,
                description=f"User {user_id} acknowledged mandatory announcement {announcement_id}",
            )

        return {"status": "acknowledged", "acknowledged_at": now}

    def is_acknowledged_by_user(self, announcement_id, user_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT ack_id FROM announcement_acknowledgements WHERE announcement_id = ? AND user_id = ?",
                (announcement_id, user_id),
            ).fetchone()
            return bool(row)

    def get_readership_metrics(self, announcement_id):
        with self._connect() as conn:
            reads_count = conn.execute(
                "SELECT COUNT(*) FROM announcement_reads WHERE announcement_id = ?",
                (announcement_id,),
            ).fetchone()[0]
            acks_count = conn.execute(
                "SELECT COUNT(*) FROM announcement_acknowledgements WHERE announcement_id = ?",
                (announcement_id,),
            ).fetchone()[0]
            return {"reads_count": reads_count, "acknowledgements_count": acks_count}

    # ==========================================
    # 5. SCHEDULER TRANSITIONS
    # ==========================================
    def process_scheduled_and_expired(self):
        now = now_string()
        with self._connect() as conn:
            # Scheduled -> Published
            conn.execute(
                "UPDATE announcements SET status = 'Published', published_by = 'scheduler', updated_at = ? WHERE status = 'Scheduled' AND publish_at <= ?",
                (now, now),
            )
            # Published -> Expired
            conn.execute(
                "UPDATE announcements SET status = 'Expired', updated_at = ? WHERE status = 'Published' AND expire_at IS NOT NULL AND expire_at <= ?",
                (now, now),
            )

    def _row_to_dict(self, row):
        if not row:
            return None
        return dict(row)
