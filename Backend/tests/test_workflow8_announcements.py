import pytest
import sys
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from middleware.rate_limiter import auth_limiter

client = TestClient(app)

def _reset_limiter():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()

def _get_admin_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "admin@example.com", "password": "Admin@123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def _get_student_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "student@example.com", "password": "Student@123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def _get_coordinator_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "coordinator@example.com", "password": "Coordinator@123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def _get_manager_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "manager@example.com", "password": "Manager@123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def _get_warden_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "warden@example.com", "password": "warden@123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_workflow_8_admin_creates_announcement_success():
    admin_headers = _get_admin_headers()
    uid = uuid.uuid4().hex[:6]
    payload = {
        "title": f"Emergency Water Maintenance {uid}",
        "description": "Water supply will be unavailable from 10 AM to 2 PM tomorrow in Hostel A.",
        "priority": "HIGH",
        "target": "LOC_HOSTEL_A",
        "is_pinned": True,
        "attachment_url": "https://example.com/notice.pdf"
    }
    res = client.post("/announcements", json=payload, headers=admin_headers)
    assert res.status_code == 201
    data = res.json()
    assert "announcement_id" in data
    assert data["priority"] == "High"
    assert data["status"] == "Published"

def test_workflow_8_non_admin_cannot_create_announcement():
    std_headers = _get_student_headers()
    coord_headers = _get_coordinator_headers()

    payload = {
        "title": "Student Announcement Attempt",
        "description": "This should be blocked."
    }

    # Student -> 403 Forbidden
    res_std = client.post("/announcements", json=payload, headers=std_headers)
    assert res_std.status_code == 403

    # Coordinator -> 403 Forbidden
    res_coord = client.post("/announcements", json=payload, headers=coord_headers)
    assert res_coord.status_code == 403

def test_workflow_8_validation_missing_description():
    admin_headers = _get_admin_headers()
    res = client.post("/announcements", json={
        "title": "Title with no description",
        "description": " "
    }, headers=admin_headers)
    assert res.status_code == 400

def test_workflow_8_feed_pinning_read_tracking_and_archive():
    admin_headers = _get_admin_headers()
    std_headers = _get_student_headers()
    uid = uuid.uuid4().hex[:6]

    # 1. Admin creates pinned announcement
    create_res = client.post("/announcements", json={
        "title": f"Pinned Registration Notice {uid}",
        "description": "Semester registration deadline extended.",
        "priority": "HIGH",
        "is_pinned": True
    }, headers=admin_headers)
    assert create_res.status_code == 201
    aid = create_res.json()["announcement_id"]

    # 2. Student views announcement feed
    feed_res = client.get("/announcements", headers=std_headers)
    assert feed_res.status_code == 200
    feed = feed_res.json()
    assert any(a["announcement_id"] == aid for a in feed)

    target_ann = next(a for a in feed if a["announcement_id"] == aid)
    assert target_ann["is_read"] is False

    # 3. Student marks announcement read
    read_res = client.post(f"/announcements/{aid}/read", headers=std_headers)
    assert read_res.status_code == 200

    # 4. Detail view shows is_read = True
    detail_res = client.get(f"/announcements/{aid}", headers=std_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["is_read"] is True

    # 5. Admin archives announcement
    arch_res = client.post(f"/announcements/{aid}/archive", headers=admin_headers)
    assert arch_res.status_code == 200
    assert arch_res.json()["status"] == "Archived"

def test_workflow_8_staff_roles_can_create_announcements():
    mgr_headers = _get_manager_headers()
    warden_headers = _get_warden_headers()

    # 1. App Manager creates announcement -> 201 Created
    uid_mgr = uuid.uuid4().hex[:6]
    res_mgr = client.post("/announcements", json={
        "title": f"Hostel Inspection Notice {uid_mgr}",
        "description": "Routine quarterly inspection scheduled for all blocks.",
        "priority": "NORMAL",
        "category": "Hostel"
    }, headers=mgr_headers)
    assert res_mgr.status_code == 201
    assert res_mgr.json()["created_by"] in ("USR_MANAGER", "USR_MANAGER_EX")

    # 2. Warden creates announcement -> 201 Created
    uid_wrd = uuid.uuid4().hex[:6]
    res_wrd = client.post("/announcements", json={
        "title": f"Block Night Roll Call {uid_wrd}",
        "description": "Mandatory roll call at 10 PM tonight.",
        "priority": "HIGH",
        "category": "Hostel"
    }, headers=warden_headers)
    assert res_wrd.status_code == 201
    assert res_wrd.json()["created_by"] in ("USR_WARDEN", "USR_WARDEN_EX")

def test_workflow_8_get_admin_contact_endpoint():
    std_headers = _get_student_headers()
    coord_headers = _get_coordinator_headers()

    # 1. Student queries admin contact
    res_std = client.get("/announcements/admin-contact", headers=std_headers)
    assert res_std.status_code == 200
    data_std = res_std.json()
    assert data_std["available"] is True
    assert "@" in data_std["email"]
    assert data_std["name"] is not None
    assert "contact" in data_std["message"].lower()

    # 2. Coordinator queries admin contact
    res_coord = client.get("/announcements/admin-contact", headers=coord_headers)
    assert res_coord.status_code == 200
    assert res_coord.json()["available"] is True
    assert "@" in res_coord.json()["email"]

    # 3. Unauthenticated request without session or token is rejected with 401
    anon_client = TestClient(app)
    res_unauth = anon_client.get("/announcements/admin-contact")
    assert res_unauth.status_code == 401

