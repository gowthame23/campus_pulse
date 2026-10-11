import pytest
import sys
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import db_path, notification_service
from middleware.rate_limiter import auth_limiter

client = TestClient(app)

def _reset_limiter():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()

def _get_student_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "gowtham.e23@iiits.in", "password": "Student@123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_workflow_7_publish_and_structured_payload():
    # Publish notification to student
    notif = notification_service.publish(
        receiver_id="USR_STUDENT",
        title="Test Notification Title",
        message="Test notification message content.",
        module="Complaint",
        notification_type="complaint_updated",
        reference_type="Complaint",
        reference_id="CP-2026-TEST",
        priority="High"
    )
    assert notif is not None
    assert "payload" in notif
    assert notif["payload"]["type"] == "complaint_updated"
    assert notif["payload"]["reference_id"] == "CP-2026-TEST"

def test_workflow_7_notification_endpoints():
    std_headers = _get_student_headers()

    # 1. Publish fresh notification
    ref_id = f"REF-{uuid.uuid4().hex[:6]}"
    notif = notification_service.publish(
        receiver_id="USR_STUDENT",
        title="Complaint Resolved Notification",
        message="Your complaint has been resolved.",
        module="Complaint",
        notification_type="complaint_resolved",
        reference_type="Complaint",
        reference_id=ref_id,
        priority="Medium"
    )
    nid = notif["notification_id"]

    # 2. Get unread count
    cnt_res = client.get("/notifications/unread-count", headers=std_headers)
    assert cnt_res.status_code == 200
    assert cnt_res.json()["unread_count"] >= 1

    # 3. List notifications
    list_res = client.get("/notifications", headers=std_headers)
    assert list_res.status_code == 200
    data = list_res.json()
    assert any(n["notification_id"] == nid for n in data)

    # Verify structured payload present in list item
    target_notif = next(n for n in data if n["notification_id"] == nid)
    assert "payload" in target_notif
    assert target_notif["payload"]["type"] == "complaint_resolved"

    # 4. Mark single notification as read
    read_res = client.patch(f"/notifications/{nid}/read", headers=std_headers)
    assert read_res.status_code == 200

    # 5. Mark all as read
    all_read = client.post("/notifications/mark-all-read", headers=std_headers)
    assert all_read.status_code == 200

    # 6. Delete single notification
    del_res = client.delete(f"/notifications/{nid}", headers=std_headers)
    assert del_res.status_code == 200
