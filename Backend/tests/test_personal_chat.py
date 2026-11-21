import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.security import create_session
from api.dependencies import get_auth_service, get_chat_service


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_service():
    auth = get_auth_service()
    auth.ensure_seed_data()
    return auth


@pytest.fixture
def chat_service():
    return get_chat_service()


def auth_header(user_id: str, auth_service) -> dict:
    user = auth_service.get_user(user_id)
    token = create_session(user)
    return {"Authorization": f"Bearer {token}"}


def test_personal_chat_contacts_list(client, auth_service):
    """Staff can list authorized chat contacts, student access is rejected with 403."""
    # App Manager 1 gets contacts
    resp = client.get("/chat/users", headers=auth_header("USR_MANAGER", auth_service))
    assert resp.status_code == 200
    contacts = resp.json()
    assert isinstance(contacts, list)
    contact_ids = [c["user_id"] for c in contacts]
    assert "USR_MANAGER_2" in contact_ids
    assert "USR_WARDEN" in contact_ids
    assert "USR_EMP_A1" in contact_ids
    assert "USR_ADMIN" in contact_ids
    # Current user is excluded
    assert "USR_MANAGER" not in contact_ids
    # Students are excluded from staff contacts
    assert "USR_STUDENT" not in contact_ids
    assert "USR_STUDENT_2" not in contact_ids

    # Student attempts to get contacts -> 403 Forbidden
    resp_student = client.get("/chat/users", headers=auth_header("USR_STUDENT", auth_service))
    assert resp_student.status_code == 403
    assert "not permitted" in resp_student.json()["detail"].lower()


def test_personal_chat_role_combinations(client, auth_service):
    """Verify chat starts between all supported role combinations."""
    combinations = [
        ("USR_MANAGER", "USR_MANAGER_2"),         # App Manager 1 <-> App Manager 2
        ("USR_WARDEN", "USR_EMP_A1"),             # Warden 1 <-> Coordinator 1 (Employee A1)
        ("USR_ADMIN", "USR_MANAGER"),             # Administrator <-> App Manager 1
        ("USR_EMP_A1", "USR_EMP_A2"),             # Coordinator 1 <-> Coordinator 2 (Employee A1 <-> A2)
    ]

    for sender_id, recipient_id in combinations:
        resp = client.post(
            "/chat/personal/start",
            json={"recipient_id": recipient_id},
            headers=auth_header(sender_id, auth_service),
        )
        assert resp.status_code == 200, f"Failed for {sender_id} -> {recipient_id}: {resp.text}"
        data = resp.json()
        assert "conversation_id" in data
        assert data["other_user_id"] == recipient_id
        assert data["other_user"]["user_id"] == recipient_id


def test_personal_chat_messaging_persistence_and_unread(client, auth_service, chat_service):
    """Verify persistent message delivery, offline recipient unread counter, and reading."""
    # 1. Start conversation between Warden 1 and Coordinator 1 (Employee A1)
    start_resp = client.post(
        "/chat/start",
        json={"recipient_id": "USR_EMP_A1"},
        headers=auth_header("USR_WARDEN", auth_service),
    )
    assert start_resp.status_code == 200
    conv_id = start_resp.json()["conversation_id"]

    # 2. Warden 1 sends a message
    msg_content = "Hello Coordinator, please check electrical room in Hostel 1."
    send_resp = client.post(
        "/chat/message",
        json={"conversation_id": conv_id, "content": msg_content},
        headers=auth_header("USR_WARDEN", auth_service),
    )
    assert send_resp.status_code == 200
    msg = send_resp.json()
    assert msg["content"] == msg_content
    assert msg["sender_id"] == "USR_WARDEN"

    # 3. Check Coordinator's conversation list and unread count (recipient offline until checked)
    unread_resp = client.get(
        "/chat/unread-count",
        headers=auth_header("USR_EMP_A1", auth_service),
    )
    assert unread_resp.status_code == 200
    assert unread_resp.json()["unread_count"] >= 1

    convs_resp = client.get(
        "/chat/conversations",
        headers=auth_header("USR_EMP_A1", auth_service),
    )
    assert convs_resp.status_code == 200
    conv_list = convs_resp.json()
    matching = [c for c in conv_list if c["conversation_id"] == conv_id]
    assert len(matching) == 1
    assert matching[0]["last_message"] == msg_content
    assert matching[0]["other_user_id"] == "USR_WARDEN"
    assert matching[0]["unread_count"] >= 1

    # 4. Coordinator opens conversation -> messages loaded and marked read
    history_resp = client.get(
        f"/chat/{conv_id}",
        headers=auth_header("USR_EMP_A1", auth_service),
    )
    assert history_resp.status_code == 200
    msgs = history_resp.json()
    assert any(m["content"] == msg_content for m in msgs)

    # 5. After reading, Coordinator's unread count for this conversation is 0
    unread_after = client.get(
        "/chat/unread-count",
        headers=auth_header("USR_EMP_A1", auth_service),
    )
    assert unread_after.status_code == 200
    assert chat_service.get_unread_count(conv_id, "USR_EMP_A1") == 0


def test_student_forbidden_from_personal_chat(client, auth_service):
    """Students cannot start, post, or view personal chat conversations."""
    # Start attempt
    resp_start = client.post(
        "/chat/start",
        json={"recipient_id": "USR_MANAGER"},
        headers=auth_header("USR_STUDENT", auth_service),
    )
    assert resp_start.status_code == 403

    # Post message attempt to existing personal conversation
    personal_conv = "chat:USR_ADMIN:USR_MANAGER"
    resp_post = client.post(
        "/chat/message",
        json={"conversation_id": personal_conv, "content": "Trying to bypass"},
        headers=auth_header("USR_STUDENT", auth_service),
    )
    assert resp_post.status_code == 403

    # Read conversation attempt
    resp_read = client.get(
        f"/chat/{personal_conv}",
        headers=auth_header("USR_STUDENT", auth_service),
    )
    assert resp_read.status_code == 403

    # Student conversation list should not include personal chats
    resp_list = client.get(
        "/chat/conversations",
        headers=auth_header("USR_STUDENT", auth_service),
    )
    assert resp_list.status_code == 200
    for conv in resp_list.json():
        assert conv.get("item_id") is not None, "Student must only see item-linked chats"


def test_unauthorized_staff_cannot_access_other_conversation(client, auth_service):
    """Staff C cannot access conversation between Staff A and Staff B."""
    # Create conversation between Manager 1 and Coordinator 1
    conv_id = "chat:USR_COORDINATOR:USR_MANAGER"

    # Warden 2 attempts to read -> 403
    resp = client.get(
        f"/chat/{conv_id}",
        headers=auth_header("USR_WARDEN_2", auth_service),
    )
    assert resp.status_code == 403
    assert "not a participant" in resp.json()["detail"].lower()

    # Warden 2 attempts to send message -> 403
    resp_post = client.post(
        "/chat/message",
        json={"conversation_id": conv_id, "content": "Spying message"},
        headers=auth_header("USR_WARDEN_2", auth_service),
    )
    assert resp_post.status_code == 403


def test_cannot_chat_with_oneself(client, auth_service):
    """Staff cannot start a conversation with themselves."""
    resp = client.post(
        "/chat/personal/start",
        json={"recipient_id": "USR_ADMIN"},
        headers=auth_header("USR_ADMIN", auth_service),
    )
    assert resp.status_code == 400
    assert "yourself" in resp.json()["detail"].lower()
