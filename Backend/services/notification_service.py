import sqlite3
from pathlib import Path

from utils.helper import generate_id, now_string, now
from utils.logger import get_logger
from utils.websocket_manager import manager

logger = get_logger(__name__)


class NotificationService:
    MODULES = (
        "Complaint",
        "User",
        "System",
        "Resource Booking",
        "Lost & Found",
        "Visitor Management",
        "Event",
    )
    PRIORITIES = ("Low", "Medium", "High", "Critical")

    def __init__(self, db_path="storage/campus_pulse.db"):
        self.db_path = Path(db_path)
        self._ensure_table()

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_table(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    notification_id TEXT PRIMARY KEY,
                    receiver_id TEXT NOT NULL,
                    sender_id TEXT,
                    module TEXT NOT NULL DEFAULT 'Complaint',
                    notification_type TEXT DEFAULT 'info',
                    title TEXT DEFAULT '',
                    message TEXT NOT NULL,
                    reference_type TEXT,
                    reference_id TEXT,
                    priority TEXT DEFAULT 'Medium',
                    is_read INTEGER DEFAULT 0,
                    read_at TEXT,
                    delivery_status TEXT DEFAULT 'Pending',
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    is_deleted INTEGER DEFAULT 0,
                    deleted_at TEXT,
                    deleted_by TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notification_preferences (
                    preference_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL UNIQUE,
                    in_app_enabled INTEGER DEFAULT 1,
                    email_enabled INTEGER DEFAULT 0,
                    push_enabled INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notification_user_dismissals (
                    user_id TEXT NOT NULL,
                    notification_id TEXT NOT NULL,
                    dismissed_at TEXT NOT NULL,
                    PRIMARY KEY (user_id, notification_id)
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_notif_dismiss_user ON notification_user_dismissals(user_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_notif_receiver ON notifications(receiver_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_notif_read ON notifications(is_read)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_notif_priority ON notifications(priority)"
            )

            # Column migrations for existing databases
            for col_def in [
                ("sender_id", "TEXT"),
                ("module", "TEXT DEFAULT 'Complaint'"),
                ("reference_type", "TEXT"),
                ("reference_id", "TEXT"),
                ("priority", "TEXT DEFAULT 'Medium'"),
                ("delivery_status", "TEXT DEFAULT 'Pending'"),
                ("expires_at", "TEXT"),
                ("payload", "TEXT"),
            ]:
                try:
                    conn.execute(
                        f"ALTER TABLE notifications ADD COLUMN {col_def[0]} {col_def[1]}"
                    )
                except sqlite3.OperationalError:
                    pass

    # ==========================================
    # PREFERENCES
    # ==========================================
    def get_preferences(self, user_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM notification_preferences WHERE user_id = ?", (user_id,)
            ).fetchone()
            if row:
                return {
                    "preference_id": row["preference_id"],
                    "user_id": row["user_id"],
                    "in_app_enabled": bool(row["in_app_enabled"]),
                    "email_enabled": bool(row["email_enabled"]),
                    "push_enabled": bool(row["push_enabled"]),
                }
            # Default preferences per spec: In-App Enabled (1), Email Disabled (0), Push Disabled (0)
            return {
                "preference_id": f"PREF_{user_id}",
                "user_id": user_id,
                "in_app_enabled": True,
                "email_enabled": False,
                "push_enabled": False,
            }

    def update_preferences(
        self, user_id, in_app_enabled=True, email_enabled=False, push_enabled=False
    ):
        now = now_string()
        pid = generate_id("PRF")
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO notification_preferences (preference_id, user_id, in_app_enabled, email_enabled, push_enabled, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(user_id) DO UPDATE SET
                       in_app_enabled=excluded.in_app_enabled,
                       email_enabled=excluded.email_enabled,
                       push_enabled=excluded.push_enabled,
                       updated_at=excluded.updated_at""",
                (
                    pid,
                    user_id,
                    int(in_app_enabled),
                    int(email_enabled),
                    int(push_enabled),
                    now,
                    now,
                ),
            )
        return self.get_preferences(user_id)

    # ==========================================
    # CENTRAL PUBLISH METHOD
    # ==========================================
    def publish(
        self,
        receiver_id,
        title,
        message,
        module="Complaint",
        notification_type="info",
        reference_type="Complaint",
        reference_id=None,
        priority="Medium",
        sender_id=None,
        expires_at=None,
    ):
        """Central publisher method used by all modules."""
        prefs = self.get_preferences(receiver_id)
        if not prefs["in_app_enabled"]:
            logger.info(
                f"[Notification Skipped] In-App notifications disabled for {receiver_id}"
            )
            return None

        nid = generate_id("NTF")
        created_at = now().strftime("%Y-%m-%d %H:%M:%S.%f")

        # Determine initial delivery status
        is_online = manager.is_online(receiver_id)
        delivery_status = "Delivered" if is_online else "Pending"

        import json
        payload_dict = {
            "type": notification_type or "info",
            "module": module,
            "reference_type": reference_type,
            "reference_id": reference_id,
            "message": message,
            "title": title or module,
            "priority": priority,
        }
        payload_json = json.dumps(payload_dict)

        # Deduplication check: do not flood duplicate unread alerts/reminders for the same reference item
        if reference_id and notification_type in ("alert", "info"):
            with self._connect() as conn:
                existing = conn.execute(
                    """SELECT notification_id FROM notifications 
                       WHERE receiver_id = ? AND reference_id = ? AND title = ? AND is_read = 0 AND is_deleted = 0
                       ORDER BY created_at DESC LIMIT 1""",
                    (receiver_id, reference_id, title),
                ).fetchone()
                if existing:
                    logger.info(
                        f"[Notification Deduplicated] Notification for {receiver_id} ref {reference_id} title '{title}' already pending unread."
                    )
                    return existing["notification_id"]

        with self._connect() as conn:
            conn.execute(
                """INSERT INTO notifications
                   (notification_id, receiver_id, sender_id, module, notification_type, title, message, reference_type, reference_id, priority, is_read, delivery_status, created_at, expires_at, payload, is_deleted)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, 0)""",
                (
                    nid,
                    receiver_id,
                    sender_id,
                    module,
                    notification_type,
                    title,
                    message,
                    reference_type,
                    reference_id,
                    priority,
                    delivery_status,
                    created_at,
                    expires_at,
                    payload_json,
                ),
            )

        notification_payload = {
            "notification_id": nid,
            "receiver_id": receiver_id,
            "recipient": receiver_id,
            "sender_id": sender_id,
            "module": module,
            "notification_type": notification_type,
            "title": title or module,
            "message": message,
            "reference_type": reference_type,
            "reference_id": reference_id,
            "complaint_id": reference_id if reference_type == "Complaint" else None,
            "priority": priority,
            "is_read": False,
            "read": False,
            "delivery_status": delivery_status,
            "created_at": created_at,
            "expires_at": expires_at,
            "payload": payload_dict,
        }

        # Real-time WebSocket delivery
        manager.push_sync(
            receiver_id, {"event": "new_notification", "data": notification_payload}
        )

        # Email dispatch if enabled and high/critical priority
        if prefs["email_enabled"] and priority in ("High", "Critical"):
            try:
                from utils.email import send_notification_email

                with self._connect() as conn:
                    recipient = conn.execute(
                        "SELECT email FROM users WHERE user_id = ?", (receiver_id,)
                    ).fetchone()
                if recipient and recipient["email"]:
                    send_notification_email(recipient["email"], title, message)
            except Exception:
                logger.exception(
                    "Notification email delivery failed",
                    extra={"receiver_id": receiver_id, "notification_id": nid},
                )

        # Web Push notification dispatch
        try:
            from services.push_service import send_web_push_for_notification
            send_web_push_for_notification(receiver_id, notification_payload)
        except Exception:
            logger.exception(
                "Web push notification dispatch failed",
                extra={"receiver_id": receiver_id, "notification_id": nid},
            )

        return notification_payload

    create_notification = publish

    # Backward compatible helper methods
    def notify(
        self,
        user_or_role,
        message,
        complaint_id=None,
        title="",
        notification_type="info",
        created_by="system",
    ):
        return self.publish(
            receiver_id=user_or_role,
            title=title or "System Alert",
            message=message,
            module="Complaint",
            notification_type=notification_type,
            reference_type="Complaint",
            reference_id=complaint_id,
            priority="Medium",
            sender_id=created_by,
        )

    # ==========================================
    # QUERIES & ACTIONS
    # ==========================================
    def list_for_user(
        self,
        user_id,
        user_role,
        module=None,
        priority=None,
        read_status=None,
        date_from=None,
        date_to=None,
    ):
        user_role_lower = (user_role or "").lower()

        query = (
            "SELECT * FROM notifications WHERE (is_deleted = 0 OR is_deleted IS NULL) "
            "AND notification_id NOT IN (SELECT notification_id FROM notification_user_dismissals WHERE LOWER(user_id) = LOWER(?)) "
            "AND NOT ("
            "  (module = 'Lost & Found' OR reference_type IN ('LostItem', 'FoundItem', 'ItemMatch', 'Claim', 'LostFoundReport')) "
            "  AND ("
            "    reference_id IN (SELECT item_id FROM lost_found_items WHERE is_deleted = 1) "
            "    OR reference_id IN (SELECT c.claim_id FROM ownership_claims c JOIN lost_found_items i ON c.item_id = i.item_id WHERE i.is_deleted = 1) "
            "    OR reference_id IN (SELECT claim_id FROM ownership_claims WHERE status = 'Cancelled') "
            "  )"
            ")"
        )
        params = [user_id or ""]

        if user_role_lower not in ("administrator", "app_manager"):
            query += """ AND (LOWER(receiver_id) = LOWER(?)
                        OR LOWER(receiver_id) = LOWER(?)
                        OR LOWER(receiver_id) = 'all'
                        OR (LOWER(receiver_id) = 'verifier' AND LOWER(?) IN ('student', 'location_in_charge')))"""
            params.extend([user_id, user_role, user_role])

        if module:
            query += " AND module = ?"
            params.append(module)
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        if read_status is not None:
            query += " AND is_read = ?"
            params.append(1 if read_status else 0)
        if date_from:
            query += " AND created_at >= ?"
            params.append(date_from)
        if date_to:
            query += " AND created_at <= ?"
            params.append(date_to)

        # Critical priority pinned at top, then newest created_at
        query += """ ORDER BY
                        CASE WHEN priority = 'Critical' THEN 0 WHEN priority = 'High' THEN 1 WHEN priority = 'Medium' THEN 2 ELSE 3 END,
                        created_at DESC"""

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def count_unread(self, user_id, user_role):
        notifications = self.list_for_user(user_id, user_role, read_status=False)
        return len(notifications)

    def get_notification(self, notification_id, user_id=None, user_role=None, mark_as_read=True):
        with self._connect() as conn:
            ownership = ""
            params = [notification_id]
            if user_id:
                params.append(user_id)
                ownership = " AND notification_id NOT IN (SELECT notification_id FROM notification_user_dismissals WHERE LOWER(user_id) = LOWER(?))"
            
            ownership += " AND (LOWER(receiver_id) = LOWER(?) OR LOWER(receiver_id) = 'all' OR (LOWER(receiver_id) = 'verifier' AND LOWER(?) IN ('student', 'location_in_charge')))"
            params.extend([user_id, user_role])
            row = conn.execute(
                "SELECT * FROM notifications WHERE notification_id = ? AND (is_deleted = 0 OR is_deleted IS NULL)" + ownership,
                params,
            ).fetchone()
            if not row:
                return None
            if mark_as_read and not row["is_read"]:
                self.mark_read(notification_id, user_id=user_id, user_role=user_role)
            return self._row_to_dict(
                conn.execute(
                    "SELECT * FROM notifications WHERE notification_id = ?" + ownership,
                    params,
                ).fetchone()
            )

    def mark_read(self, notification_id, user_id=None, user_role=None):
        now = now_string()
        with self._connect() as conn:
            ownership = ""
            params = [now, notification_id]
            ownership = " AND (LOWER(receiver_id) = LOWER(?) OR LOWER(receiver_id) = 'all' OR (LOWER(receiver_id) = 'verifier' AND LOWER(?) IN ('student', 'location_in_charge')))"
            params.extend([user_id, user_role])
            cursor = conn.execute(
                "UPDATE notifications SET is_read = 1, read_at = ? WHERE notification_id = ? AND (is_deleted = 0 OR is_deleted IS NULL)" + ownership,
                params,
            )
            return cursor.rowcount > 0

    def mark_all_read(self, user_role, user_id):
        unread_notifs = self.list_for_user(user_id, user_role, read_status=False)
        ids = [n["notification_id"] for n in unread_notifs]
        if not ids:
            return 0
        now = now_string()
        with self._connect() as conn:
            placeholders = ",".join(["?"] * len(ids))
            conn.execute(
                f"UPDATE notifications SET is_read = 1, read_at = ? WHERE notification_id IN ({placeholders})",
                [now] + ids,
            )
        return len(ids)

    def delete_notification(self, notification_id, user_id=None, user_role=None):
        now = now_string()
        user_role_lower = (user_role or "").lower()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM notifications WHERE notification_id = ? AND (is_deleted = 0 OR is_deleted IS NULL)", (notification_id,)).fetchone()
            if not row:
                return False

            receiver_id_lower = (row["receiver_id"] or "").lower()
            is_personal = user_id and receiver_id_lower == user_id.lower()

            if user_id and not is_personal and user_role_lower not in ("administrator", "app_manager"):
                # Broadcast/shared notification: record user dismissal instead of global deletion
                conn.execute(
                    "INSERT OR IGNORE INTO notification_user_dismissals (user_id, notification_id, dismissed_at) VALUES (?, ?, ?)",
                    (user_id, notification_id, now)
                )
                return True

            params = [now, notification_id]
            if user_role_lower in ("administrator", "app_manager"):
                ownership = ""
            else:
                ownership = """ AND (LOWER(receiver_id) = LOWER(?)
                                    OR LOWER(receiver_id) = LOWER(?)
                                    OR (LOWER(receiver_id) = 'verifier' AND LOWER(?) IN ('student', 'location_in_charge')))"""
                params.extend([user_id, user_role, user_role])
            cursor = conn.execute(
                "UPDATE notifications SET is_deleted = 1, deleted_at = ? WHERE notification_id = ? AND (is_deleted = 0 OR is_deleted IS NULL)" + ownership,
                params,
            )
            return cursor.rowcount > 0

    def clear_notifications(self, user_id=None, user_role=None):
        if user_id:
            user_notifs = self.list_for_user(user_id, user_role)
            if not user_notifs:
                return 0
            now = now_string()
            personal_ids = []
            shared_ids = []
            for n in user_notifs:
                rec_id = (n.get("receiver_id") or "").lower()
                if rec_id == user_id.lower():
                    personal_ids.append(n["notification_id"])
                else:
                    shared_ids.append(n["notification_id"])

            total_cleared = 0
            with self._connect() as conn:
                if personal_ids:
                    placeholders = ",".join("?" for _ in personal_ids)
                    cursor = conn.execute(
                        f"UPDATE notifications SET is_deleted = 1, deleted_at = ? WHERE notification_id IN ({placeholders}) AND (is_deleted = 0 OR is_deleted IS NULL)",
                        [now] + personal_ids,
                    )
                    total_cleared += cursor.rowcount
                if shared_ids:
                    for s_id in shared_ids:
                        conn.execute(
                            "INSERT OR IGNORE INTO notification_user_dismissals (user_id, notification_id, dismissed_at) VALUES (?, ?, ?)",
                            (user_id, s_id, now)
                        )
                    total_cleared += len(shared_ids)
            return total_cleared

        now = now_string()
        with self._connect() as conn:
            conn.execute(
                "UPDATE notifications SET is_deleted = 1, deleted_at = ? WHERE (is_deleted = 0 OR is_deleted IS NULL)",
                (now,),
            )
            return 1

    def deliver_pending_websocket(self, user_id):
        """Delivers pending notifications when user connects to WebSocket."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM notifications WHERE LOWER(receiver_id) = LOWER(?) AND delivery_status = 'Pending' AND (is_deleted = 0 OR is_deleted IS NULL)",
                (user_id,),
            ).fetchall()
            if rows:
                conn.execute(
                    "UPDATE notifications SET delivery_status = 'Delivered' WHERE LOWER(receiver_id) = LOWER(?) AND delivery_status = 'Pending'",
                    (user_id,),
                )
                return [self._row_to_dict(r) for r in rows]
        return []

    def _row_to_dict(self, row):
        if not row:
            return None
        r_dict = dict(row)
        ref_id = r_dict.get("reference_id") or r_dict.get("complaint_id")

        payload_val = None
        if r_dict.get("payload"):
            try:
                import json
                payload_val = json.loads(r_dict["payload"])
            except Exception:
                payload_val = None

        if not payload_val:
            payload_val = {
                "type": r_dict.get("notification_type") or "info",
                "module": r_dict.get("module") or "Complaint",
                "reference_type": r_dict.get("reference_type") or "Complaint",
                "reference_id": ref_id,
                "message": r_dict.get("message", ""),
                "title": r_dict.get("title") or "Notification",
                "priority": r_dict.get("priority") or "Medium",
            }

        return {
            "notification_id": r_dict["notification_id"],
            "receiver_id": r_dict["receiver_id"],
            "recipient": r_dict["receiver_id"],
            "sender_id": r_dict.get("sender_id"),
            "module": r_dict.get("module") or "Complaint",
            "notification_type": r_dict.get("notification_type") or "info",
            "title": r_dict.get("title") or "Notification",
            "message": r_dict.get("message", ""),
            "reference_type": r_dict.get("reference_type") or "Complaint",
            "reference_id": ref_id,
            "complaint_id": ref_id,
            "priority": r_dict.get("priority") or "Medium",
            "is_read": bool(r_dict.get("is_read", 0)),
            "read": bool(r_dict.get("is_read", 0)),
            "read_at": r_dict.get("read_at"),
            "delivery_status": r_dict.get("delivery_status") or "Delivered",
            "created_at": r_dict.get("created_at"),
            "expires_at": r_dict.get("expires_at"),
            "payload": payload_val,
        }

    # Backward compatibility helpers
    def assigned(self, complaint_id, receiver_id="Coordinator"):
        self.publish(
            receiver_id=receiver_id,
            title="Complaint Assigned",
            message=f"New complaint assigned: {complaint_id}",
            module="Complaint",
            notification_type="assignment",
            reference_type="Complaint",
            reference_id=complaint_id,
            priority="Medium",
        )

    def resolved(self, complaint_id, receiver_id="Verifier"):
        self.publish(
            receiver_id=receiver_id,
            title="Verification Required",
            message=f"Complaint resolved and waiting for verification: {complaint_id}",
            module="Complaint",
            notification_type="resolution",
            reference_type="Complaint",
            reference_id=complaint_id,
            priority="High",
        )

    def reopened(self, complaint_id, receiver_id="Coordinator"):
        self.publish(
            receiver_id=receiver_id,
            title="Complaint Reopened",
            message=f"Complaint reopened: {complaint_id}",
            module="Complaint",
            notification_type="reopen",
            reference_type="Complaint",
            reference_id=complaint_id,
            priority="High",
        )

    def sla_exceeded(self, complaint_id):
        self.publish(
            receiver_id="App Manager",
            title="SLA Exceeded Alert",
            message=f"SLA exceeded for complaint: {complaint_id}",
            module="Complaint",
            notification_type="sla",
            reference_type="Complaint",
            reference_id=complaint_id,
            priority="High",
        )

    def repeated_reopen(self, complaint_id):
        self.publish(
            receiver_id="Administrator",
            title="Repeated Reopen Emergency",
            message=f"Repeated reopen detected for complaint: {complaint_id}",
            module="Complaint",
            notification_type="alert",
            reference_type="Complaint",
            reference_id=complaint_id,
            priority="Critical",
        )
