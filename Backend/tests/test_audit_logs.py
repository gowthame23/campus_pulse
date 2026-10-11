import os
from pathlib import Path

import pytest

from services.audit_service import AuditService
from services.chat_service import ChatService


def test_chat_audit_logs():
    # Use isolated test DB path from environment or local storage
    db_path = os.environ.get("DATABASE_PATH", "storage/pytest_audit.db")

    audit = AuditService(db_path=db_path)
    chat = ChatService(db_path=db_path, audit_service=audit)

    # Create a conversation link and send a message
    conv = chat.start_conversation("USR_A", "USR_B")
    chat.create_conversation_link(conv, "ITEM_TEST_1")

    msg = chat.save_message(conv, "USR_A", "Hello test")

    # Query audit logs for conversation creation and message send
    logs = audit.list_logs()
    actions = {l["action"] for l in logs}
    assert "CREATE" in actions
    assert "SEND" in actions

    # Ensure message audit contains expected fields
    send_logs = [l for l in logs if l["action"] == "SEND"]
    assert any("Message sent" in (l["description"] or "") for l in send_logs)
