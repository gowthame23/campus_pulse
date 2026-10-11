import sqlite3
from pathlib import Path

from services.audit_service import AuditService
from utils.helper import generate_id, now_string


class ChatService:
    def __init__(
        self, db_path="storage/campus_pulse.db", audit_service: AuditService = None
    ):
        self.db_path = Path(db_path)
        # attach provided audit service or create one
        self.audit_service = audit_service or AuditService(db_path=db_path)
        self._ensure_table()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_table(self):
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    sender_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_read INTEGER DEFAULT 0
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_conv ON chat_messages(conversation_id)"
            )
            # conversations linked to domain entities (lost_found items)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_conversations (
                    conversation_id TEXT PRIMARY KEY,
                    item_id TEXT,
                    participant_a TEXT,
                    participant_b TEXT,
                    read_only INTEGER DEFAULT 0,
                    created_at TEXT
                )
            """)
            for column in ("participant_a", "participant_b"):
                try:
                    conn.execute(f"ALTER TABLE chat_conversations ADD COLUMN {column} TEXT")
                except sqlite3.OperationalError:
                    pass
            try:
                conn.execute("ALTER TABLE chat_messages ADD COLUMN is_read INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_conv_item ON chat_conversations(item_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_chat_conv_created ON chat_conversations(created_at)"
            )

    def _normalize_conv(self, a, b):
        # deterministic conversation id for 1:1 chats
        parts = sorted([a or "", b or ""])
        return f"chat:{parts[0]}:{parts[1]}"

    def get_participants(self, conversation_id):
        link = self.get_link_for_conversation(conversation_id)
        if link and (link.get("participant_a") or link.get("participant_b")):
            return [p for p in (link.get("participant_a"), link.get("participant_b")) if p]
        parts = (conversation_id or "").split(":")
        if len(parts) == 3 and parts[0] == "chat":
            return [parts[1], parts[2]]
        return []

    def is_participant(self, conversation_id, user_id):
        return user_id in self.get_participants(conversation_id)

    def start_conversation(self, user_a, user_b):
        return self._normalize_conv(user_a, user_b)

    def start_personal_conversation(self, user_a, user_b):
        conv_id = self._normalize_conv(user_a, user_b)
        now = now_string()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO chat_conversations (conversation_id, item_id, participant_a, participant_b, read_only, created_at)
                VALUES (?, NULL, ?, ?, 0, ?)
                ON CONFLICT(conversation_id) DO NOTHING
                """,
                (conv_id, min(user_a, user_b), max(user_a, user_b), now),
            )
        return conv_id

    def mark_as_read(self, conversation_id, reader_id):
        with self._connect() as conn:
            conn.execute(
                "UPDATE chat_messages SET is_read = 1 WHERE conversation_id = ? AND sender_id != ? AND is_read = 0",
                (conversation_id, reader_id),
            )

    def get_unread_count(self, conversation_id, user_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM chat_messages WHERE conversation_id = ? AND sender_id != ? AND is_read = 0",
                (conversation_id, user_id),
            ).fetchone()
            return row["cnt"] if row else 0

    def get_total_unread_count(self, user_id):
        pattern1 = f"%:{user_id}:%"
        pattern2 = f"%:{user_id}"
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM chat_messages WHERE (conversation_id LIKE ? OR conversation_id LIKE ?) AND sender_id != ? AND is_read = 0",
                (pattern1, pattern2, user_id),
            ).fetchone()
            return row["cnt"] if row else 0

    def save_message(self, conversation_id, sender_id, content):
        mid = generate_id("MSG")
        now = now_string()
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO chat_messages (message_id, conversation_id, sender_id, content, created_at, is_read) VALUES (?, ?, ?, ?, ?, 0)",
                (mid, conversation_id, sender_id, content, now),
            )
        msg = {
            "message_id": mid,
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "content": content,
            "created_at": now,
            "is_read": False,
        }

        # Audit message send
        try:
            if self.audit_service:
                self.audit_service.log_event(
                    module="Chat",
                    entity_type="Message",
                    entity_id=mid,
                    action="SEND",
                    performed_by=sender_id,
                    new_value=msg,
                    description=f"Message sent in {conversation_id} by {sender_id}",
                )
        except Exception:
            pass

        return msg

    def list_messages(self, conversation_id, limit=100, since=None):
        with self._connect() as conn:
            if since:
                rows = conn.execute(
                    "SELECT * FROM chat_messages WHERE conversation_id = ? AND created_at > ? ORDER BY created_at ASC LIMIT ?",
                    (conversation_id, since, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM chat_messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ?",
                    (conversation_id, limit),
                ).fetchall()
            return [self._row_to_dict(r) for r in rows]

    def list_conversations(self, user_id, limit=100):
        # Return a list of conversations involving user_id with last message preview and unread counts
        pattern1 = f"%:{user_id}:%"
        pattern2 = f"%:{user_id}"
        with self._connect() as conn:
            # 1. Fetch conversations from chat_conversations
            c_rows = conn.execute(
                """
                SELECT conversation_id, item_id, participant_a, participant_b, read_only, created_at
                FROM chat_conversations
                WHERE participant_a = ? OR participant_b = ? OR conversation_id LIKE ? OR conversation_id LIKE ?
                """,
                (user_id, user_id, pattern1, pattern2),
            ).fetchall()
            conv_map = {}
            for r in c_rows:
                cid = r["conversation_id"]
                conv_map[cid] = {
                    "conversation_id": cid,
                    "item_id": r["item_id"],
                    "participant_a": r["participant_a"],
                    "participant_b": r["participant_b"],
                    "read_only": bool(r["read_only"]),
                    "created_at": r["created_at"],
                    "last_message": "",
                    "last_sender": None,
                    "last_at": r["created_at"] or "",
                    "unread_count": 0,
                }

            # 2. Also check conversations that exist in chat_messages
            m_rows = conn.execute(
                """
                SELECT conversation_id, MAX(created_at) as last_at
                FROM chat_messages
                WHERE conversation_id LIKE ? OR conversation_id LIKE ?
                GROUP BY conversation_id
                """,
                (pattern1, pattern2),
            ).fetchall()

            for r in m_rows:
                cid = r["conversation_id"]
                if cid not in conv_map:
                    parts = cid.split(":")
                    pa = parts[1] if len(parts) == 3 else None
                    pb = parts[2] if len(parts) == 3 else None
                    conv_map[cid] = {
                        "conversation_id": cid,
                        "item_id": None,
                        "participant_a": pa,
                        "participant_b": pb,
                        "read_only": False,
                        "created_at": r["last_at"],
                        "last_message": "",
                        "last_sender": None,
                        "last_at": r["last_at"] or "",
                        "unread_count": 0,
                    }

            # 3. For each conversation, populate last message and unread count
            for cid, cinfo in conv_map.items():
                msg_row = conn.execute(
                    "SELECT content, sender_id, created_at FROM chat_messages WHERE conversation_id = ? ORDER BY created_at DESC LIMIT 1",
                    (cid,),
                ).fetchone()
                if msg_row:
                    cinfo["last_message"] = msg_row["content"]
                    cinfo["last_sender"] = msg_row["sender_id"]
                    cinfo["last_at"] = msg_row["created_at"]

                unread_row = conn.execute(
                    "SELECT COUNT(*) as unread FROM chat_messages WHERE conversation_id = ? AND sender_id != ? AND is_read = 0",
                    (cid, user_id),
                ).fetchone()
                cinfo["unread_count"] = unread_row["unread"] if unread_row else 0

            # Sort by last_at descending
            results = sorted(conv_map.values(), key=lambda x: x.get("last_at") or "", reverse=True)
            return results[:limit]

    # Conversation <-> item linkage
    def create_conversation_link(self, conversation_id, item_id, participant_a=None, participant_b=None):
        now = now_string()
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO chat_conversations (conversation_id, item_id, participant_a, participant_b, read_only, created_at) VALUES (?, ?, ?, ?, 0, ?)",
                (conversation_id, item_id, participant_a, participant_b, now),
            )
        # Audit the creation of the conversation ↔ item link
        try:
            if self.audit_service:
                self.audit_service.log_event(
                    module="Chat",
                    entity_type="Conversation",
                    entity_id=conversation_id,
                    action="CREATE",
                    performed_by=None,
                    new_value={"conversation_id": conversation_id, "item_id": item_id},
                    description=f"Linked conversation {conversation_id} to item {item_id}",
                )
        except Exception:
            pass

    def get_conversation_for_item(self, item_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM chat_conversations WHERE item_id = ?", (item_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_link_for_conversation(self, conversation_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM chat_conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
            return dict(row) if row else None

    def is_read_only(self, conversation_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT read_only FROM chat_conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
            return bool(row["read_only"]) if row else False

    def set_read_only(self, conversation_id, value=True):
        v = 1 if value else 0
        # Capture old value for audit
        old = None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT read_only FROM chat_conversations WHERE conversation_id = ?",
                (conversation_id,),
            ).fetchone()
            old = dict(row)["read_only"] if row else None
            conn.execute(
                "UPDATE chat_conversations SET read_only = ? WHERE conversation_id = ?",
                (v, conversation_id),
            )

        try:
            if self.audit_service:
                self.audit_service.log_event(
                    module="Chat",
                    entity_type="Conversation",
                    entity_id=conversation_id,
                    action="SET_READ_ONLY",
                    performed_by=None,
                    old_value={"read_only": bool(old)},
                    new_value={"read_only": bool(v)},
                    description=f"Set read_only={bool(v)} for {conversation_id}",
                )
        except Exception:
            pass

    def _row_to_dict(self, row):
        return {
            "message_id": row["message_id"],
            "conversation_id": row["conversation_id"],
            "sender_id": row["sender_id"],
            "content": row["content"],
            "created_at": row["created_at"],
            "is_read": bool(row["is_read"]),
        }
