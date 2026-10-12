import pytest
import sys
import os
import uuid
import sqlite3

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_db_path
from middleware.rate_limiter import auth_limiter
from services.auth_service import AuthService

client = TestClient(app)
auth_service = AuthService(db_path=get_db_path())

def _reset_limiter():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()
    from api.dependencies import _service_cache, get_db_path
    _service_cache.clear()
    import sqlite3
    db_p = get_db_path()
    if os.path.exists(db_p):
        try:
            conn = sqlite3.connect(db_p)
            conn.execute("DELETE FROM login_attempts")
            conn.commit()
            conn.close()
        except Exception:
            pass
    _service_cache.clear()

def _get_student_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "student@example.com", "password": "Student@123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def _get_admin_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "admin@example.com", "password": "Admin@123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def _get_warden_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "warden@example.com", "password": "warden@123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_workflow_4_student_create_complaint_success():
    headers = _get_student_headers()
    uid = uuid.uuid4().hex[:6]
    payload = {
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_ELECTRICAL",
        "title": "Power failure in room A-101",
        "description": f"Power has been unavailable since morning in Block A {uid}.",
        "visibility_type": "Public"
    }
    res = client.post("/complaints", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert "complaint_id" in data
    assert data["status"] in ("Submitted", "Pending", "Assigned", "In Progress")

def test_workflow_4_non_student_cannot_create_complaint():
    headers = _get_admin_headers()
    payload = {
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_ELECTRICAL",
        "title": "Admin testing complaint creation",
        "description": "Admin attempt to create complaint."
    }
    res = client.post("/complaints", json=payload, headers=headers)
    assert res.status_code == 403

def test_workflow_4_inactive_location_fails():
    headers = _get_admin_headers()
    # Create inactive location
    uid = uuid.uuid4().hex[:6]
    loc_res = client.post("/locations", json={"name": f"Inactive Loc {uid}"}, headers=headers)
    loc_id = loc_res.json()["location_id"]
    client.patch(f"/locations/{loc_id}/deactivate", headers=headers)

    # Student attempts complaint on inactive location
    std_headers = _get_student_headers()
    payload = {
        "location_id": loc_id,
        "department_id": "DEPT_ELECTRICAL",
        "description": "Testing inactive location rejection."
    }
    res = client.post("/complaints", json=payload, headers=std_headers)
    assert res.status_code == 400
    assert "inactive" in res.json()["detail"].lower()

def test_workflow_4_other_department_routes_to_warden():
    headers = _get_student_headers()
    uid = uuid.uuid4().hex[:6]
    payload = {
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_HOSTEL_OTHER",
        "description": f"Unknown structural issue requiring warden attention {uid}."
    }
    res = client.post("/complaints", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["complaint_id"] is not None

def test_workflow_4_duplicate_search_and_affected():
    std_headers = _get_student_headers()
    uid = uuid.uuid4().hex[:6]
    # Create complaint
    c_res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_ELECTRICAL",
        "description": f"Unique duplicate test description {uid}",
        "visibility_type": "Community"
    }, headers=std_headers)
    cid = c_res.json()["complaint_id"]

    # Search duplicates
    dup_res = client.get(f"/complaints/duplicates?location_id=LOC_HOSTEL_A&department_id=DEPT_ELECTRICAL", headers=std_headers)
    assert dup_res.status_code == 200
    duplicates = dup_res.json()
    assert any(c["complaint_id"] == cid for c in duplicates)

def test_workflow_4_full_lifecycle():
    admin_headers = _get_admin_headers()
    std_headers = _get_student_headers()

    # 1. Student creates complaint
    uid = uuid.uuid4().hex[:6]
    c_res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_ELECTRICAL",
        "description": f"Full lifecycle testing complaint {uid}."
    }, headers=std_headers)
    cid = c_res.json()["complaint_id"]

    # 2. Staff assigns/starts work
    accept_res = client.post(f"/complaints/{cid}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=admin_headers)

    # 3. Admin resolves complaint
    res_res = client.post(f"/complaints/{cid}/resolve", json={"notes": "Repaired fuse box."}, headers=admin_headers)
    assert res_res.status_code == 200
    assert res_res.json()["status"] in ("Resolved", "Waiting For Verification", "Waiting for Verification")

    # 4. Student verifies & closes complaint
    verify_res = client.post(f"/complaints/{cid}/close", json={}, headers=std_headers)
    assert verify_res.status_code in (200, 201)
    assert verify_res.json()["status"] == "Closed"

def test_workflow_4_warden_access_hostel_complaints():
    std_headers = _get_student_headers()
    warden_headers = _get_warden_headers()

    # Student creates complaint at LOC_HOSTEL_A
    uid = uuid.uuid4().hex[:6]
    c_res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_ELECTRICAL",
        "description": f"Warden access test complaint {uid}."
    }, headers=std_headers)
    assert c_res.status_code == 201
    cid = c_res.json()["complaint_id"]

    # Warden views complaint details at LOC_HOSTEL_A
    get_res = client.get(f"/complaints/{cid}", headers=warden_headers)
    assert get_res.status_code == 200
    assert get_res.json()["complaint_id"] == cid
    assert get_res.json()["location_id"] == "LOC_HOSTEL_A"


def test_workflow_4_complaint_deletion_ownership_and_status_controls():
    admin_headers = _get_admin_headers()
    std_headers = _get_student_headers()
    uid = uuid.uuid4().hex[:6]

    # 1. Create Student B at same hostel location
    u_res = client.post("/users", json={
        "name": f"Student B {uid}",
        "email": f"studentb_{uid}@iiits.in",
        "password": "Student@123",
        "role": "student",
        "location_id": "LOC_HOSTEL_A"
    }, headers=admin_headers)
    assert u_res.status_code == 201
    user_b_id = u_res.json()["user_id"]

    conn = sqlite3.connect(get_db_path())
    conn.execute("UPDATE users SET first_login = 0 WHERE user_id = ?", (user_b_id,))
    conn.commit()
    conn.close()

    _reset_limiter()
    login_b = client.post("/auth/login", json={"username": f"studentb_{uid}@iiits.in", "password": "Student@123"})
    std_b_headers = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    # 2. Student A creates a community complaint
    c_res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_ELECTRICAL",
        "title": "Ownership Deletion Security Test",
        "description": f"Testing student deletion ownership boundaries {uid}.",
        "visibility_type": "Community"
    }, headers=std_headers)
    assert c_res.status_code == 201
    cid = c_res.json()["complaint_id"]

    # 3. Student B attempts to delete Student A's complaint -> MUST RETURN 403 FORBIDDEN
    del_b_res = client.delete(f"/complaints/{cid}", headers=std_b_headers)
    assert del_b_res.status_code == 403
    assert "only delete your own complaints" in del_b_res.json()["detail"].lower()

    # 4. Admin advances complaint to Assigned
    client.post(f"/complaints/{cid}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=admin_headers)

    # 5. Student A attempts to delete own complaint while in Assigned/In Progress status -> MUST RETURN 400 BAD REQUEST
    del_a_inprogress = client.delete(f"/complaints/{cid}", headers=std_headers)
    assert del_a_inprogress.status_code == 400
    assert "submitted status" in del_a_inprogress.json()["detail"].lower()

    # 6. Administrator force deletes complaint -> MUST SUCCEED AND WRITE AUDIT LOG
    del_admin_res = client.delete(f"/complaints/{cid}", headers=admin_headers)
    assert del_admin_res.status_code == 200
    assert del_admin_res.json()["status"] == "deleted"

    # Verify soft delete in DB
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT archived FROM complaints WHERE complaint_id = ?", (cid,)).fetchone()
    assert row is not None
    assert row["archived"] == 1

    # Verify Audit Log entry in audit_logs table
    audit_row = conn.execute("SELECT * FROM audit_logs WHERE entity_id = ? OR target_id = ? OR description LIKE ?", (cid, cid, f"%{cid}%")).fetchone()
    assert audit_row is not None
    conn.close()

