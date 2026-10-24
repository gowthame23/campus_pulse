import os
import sys
import uuid
import pytest
from datetime import datetime, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from middleware.rate_limiter import auth_limiter
from core.constants import PRESET_PROGRESS_NOTES, STATUS_IN_PROGRESS, STATUS_BLOCKED

client = TestClient(app)


def _reset_limiter():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()


def _login(username, password):
    _reset_limiter()
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, f"Login failed for {username}: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def admin_headers():
    return _login("admin@example.com", "Admin@123")


@pytest.fixture(scope="module")
def app_mgr_headers():
    try:
        return _login("ejjurothugowtham@gmail.com", "Manager@123")
    except Exception:
        return _login("manager@example.com", "Manager@123")


@pytest.fixture(scope="module")
def coord_headers():
    try:
        return _login("gowthamejjurothu15@gmail.com", "Coord@123")
    except Exception:
        return _login("coordinator@example.com", "Coordinator@123")


@pytest.fixture(scope="module")
def warden_headers():
    return _login("warden@example.com", "warden@123")


def _create_user(admin_headers, role, email_prefix, location_id=None, department_id=None):
    uid = uuid.uuid4().hex[:8]
    email = f"{email_prefix}_{uid}@example.com"
    payload = {
        "name": f"User {uid}",
        "email": email,
        "role": role,
        "password": "Temp@Pass123",
        "confirm_password": "Temp@Pass123",
    }
    if role != "student":
        payload["employee_id"] = f"EMP{uid.upper()[:6]}"
    if location_id:
        payload["location_id"] = location_id
    if department_id:
        payload["department_id"] = department_id
    res = client.post("/users", json=payload, headers=admin_headers)
    assert res.status_code == 201, res.text

    headers = _login(email, "Temp@Pass123")
    res2 = client.post("/auth/change-password", json={
        "old_password": "Temp@Pass123",
        "new_password": "Perm@Pass456",
        "confirm_password": "Perm@Pass456",
    }, headers=headers)
    assert res2.status_code == 200, res2.text
    return _login(email, "Perm@Pass456"), res.json()


def test_accept_complaint_transitions_to_in_progress(admin_headers, coord_headers):
    # Create student to file complaint
    student_headers, student_data = _create_user(admin_headers, "student", "std_acc", location_id="LOC_HOSTEL_1")

    # File complaint in LOC_HOSTEL_1, DEPT_HOSTEL_ELECTRICAL (where USR_COORDINATOR is mapped)
    c_res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_1",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical",
        "title": "Accept test fan issue",
        "description": "Fan speed regulator broken and noisy",
        "visibility_type": "Private",
    }, headers=student_headers)
    assert c_res.status_code == 201, c_res.text
    c_data = c_res.json()
    complaint_id = c_data["complaint_id"]

    # Coordinator accepts the complaint: old accept endpoint returns 410 Gone (Part A3)
    acc_res = client.post(f"/complaints/{complaint_id}/accept", headers=coord_headers)
    assert acc_res.status_code == 410

    # Coordinator assigns the complaint
    assign_res = client.post(f"/complaints/{complaint_id}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=coord_headers)
    assert assign_res.status_code == 200, assign_res.text
    acc_data = assign_res.json()
    assert acc_data["status"] == STATUS_IN_PROGRESS
    assert acc_data["assigned_to"] == "USR_COORD_1"  # legacy "USR_COORDINATOR" alias resolves to the real account id


def test_accept_unmapped_coordinator_forbidden(admin_headers):
    student_headers, _ = _create_user(admin_headers, "student", "std_unmap", location_id="LOC_HOSTEL_1")
    # Create coordinator mapped only to Academic Block, not Hostel
    coord2_headers, coord2_data = _create_user(admin_headers, "coordinator", "coord_unmap", location_id="LOC_ACADEMIC_2", department_id="DEPT_ACADEMIC_PLUMBING")

    # File complaint in LOC_HOSTEL_1, DEPT_HOSTEL_ELECTRICAL
    c_res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_1",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical",
        "title": "Unmapped test",
        "description": "Electrical switch issue in hostel",
        "visibility_type": "Private",
    }, headers=student_headers)
    assert c_res.status_code == 201
    cid = c_res.json()["complaint_id"]

    # Coord2 attempts to accept -> 403 Forbidden
    acc_res = client.post(f"/complaints/{cid}/accept", headers=coord2_headers)
    assert acc_res.status_code == 403


def test_accept_conflict_409_when_already_accepted(admin_headers):
    # Map a new coordinator to LOC_HOSTEL_1 & DEPT_HOSTEL_ELECTRICAL to create a pooled queue
    coord_b_headers, coord_b_data = _create_user(admin_headers, "coordinator", "coord_b")
    # Map coord_b
    map_res = client.post("/departments/coordinators/assignments", json={
        "coordinator_id": coord_b_data["user_id"],
        "location_id": "LOC_HOSTEL_1",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "confirm_replacement": True,
    }, headers=admin_headers)
    assert map_res.status_code in (200, 201), map_res.text

    student_headers, _ = _create_user(admin_headers, "student", "std_pool", location_id="LOC_HOSTEL_1")
    # File complaint: now >= 2 coordinators mapped -> status Submitted, unassigned
    c_res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_1",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical",
        "title": "Pooled work queue test",
        "description": "Electrical light flickering in corridor",
        "visibility_type": "Private",
    }, headers=student_headers)
    assert c_res.status_code == 201
    cid = c_res.json()["complaint_id"]

    # First assigner assigns (e.g. admin or coordinator)
    res1 = client.post(f"/complaints/{cid}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=admin_headers)
    assert res1.status_code == 200
    assert res1.json()["status"] == STATUS_IN_PROGRESS

    # Second assigner tries to assign -> 409 Conflict
    seed_coord_headers = _login("coordinator@example.com", "Coordinator@123")
    res2 = client.post(f"/complaints/{cid}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=seed_coord_headers)
    assert res2.status_code == 409
    assert "already assigned" in res2.json()["detail"].lower()

    # Restore USR_COORDINATOR mapping for subsequent tests in module
    client.post("/departments/coordinators/assignments", json={
        "coordinator_id": "USR_COORDINATOR",
        "location_id": "LOC_HOSTEL_1",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "confirm_replacement": True,
    }, headers=admin_headers)


def test_single_tap_progress_notes(admin_headers, coord_headers):
    student_headers, _ = _create_user(admin_headers, "student", "std_prog", location_id="LOC_HOSTEL_1")

    c_res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_1",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical",
        "title": "Progress note test",
        "description": "Exhaust fan not working",
        "visibility_type": "Private",
    }, headers=student_headers)
    cid = c_res.json()["complaint_id"]

    # Coordinator assigns
    client.post(f"/complaints/{cid}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=coord_headers)

    # Post one-tap progress note with note_code
    prog_res = client.post(f"/complaints/{cid}/progress", json={
        "note_code": "PART_ORDERED"
    }, headers=coord_headers)
    assert prog_res.status_code == 200, prog_res.text
    p_data = prog_res.json()
    assert p_data["last_progress_code"] == "PART_ORDERED"
    assert any("PART_ORDERED" in h["message"] or PRESET_PROGRESS_NOTES["PART_ORDERED"] in h["message"] for h in p_data["history"])


def test_wrong_location_workflow(admin_headers, coord_headers):
    student_headers, _ = _create_user(admin_headers, "student", "std_wloc", location_id="LOC_HOSTEL_1")

    c_res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_1",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical",
        "title": "Wrong location test",
        "description": "Switch problem, but actually in Mess 1",
        "visibility_type": "Private",
    }, headers=student_headers)
    cid = c_res.json()["complaint_id"]

    # Coordinator assigns
    client.post(f"/complaints/{cid}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=coord_headers)

    # Report wrong location to LOC_MESS_1
    wl_res = client.post(f"/complaints/{cid}/wrong-location", json={
        "correct_location_id": "LOC_MESS_1",
        "note": "Student mistakenly chose Hostel 1 instead of Mess 1",
    }, headers=coord_headers)
    assert wl_res.status_code == 200, wl_res.text
    wl_data = wl_res.json()
    assert wl_data["location_id"] == "LOC_MESS_1"
    assert wl_data["wrong_location_corrections"] >= 1
    assert wl_data["wrong_location_corrected_at"] is not None


def test_reassign_requires_mandatory_reason(admin_headers, app_mgr_headers, coord_headers):
    student_headers, _ = _create_user(admin_headers, "student", "std_reassign", location_id="LOC_HOSTEL_1")

    c_res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_1",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical",
        "title": "Reassign reason test",
        "description": "Short circuit inspection",
        "visibility_type": "Private",
    }, headers=student_headers)
    cid = c_res.json()["complaint_id"]

    # Coordinator assigns
    client.post(f"/complaints/{cid}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=coord_headers)

    # Create another coordinator mapped to LOC_HOSTEL_1 & DEPT_HOSTEL_ELECTRICAL
    coord_c_headers, coord_c_data = _create_user(admin_headers, "coordinator", "coord_c")
    map_c_res = client.post("/departments/coordinators/assignments", json={
        "coordinator_id": coord_c_data["user_id"],
        "location_id": "LOC_HOSTEL_1",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "confirm_replacement": True,
    }, headers=admin_headers)
    assert map_c_res.status_code in (200, 201), map_c_res.text

    # Reassign WITHOUT reason -> 400 Bad Request
    re_no_reason = client.post(f"/complaints/{cid}/reassign", json={
        "assigned_to": coord_c_data["user_id"],
        "reason": "",
    }, headers=app_mgr_headers)
    assert re_no_reason.status_code == 400
    assert "mandatory reason" in re_no_reason.json()["detail"].lower()

    # Reassign WITH reason -> 200 OK
    re_with_reason = client.post(f"/complaints/{cid}/reassign", json={
        "assigned_to": coord_c_data["user_id"],
        "reason": "Primary coordinator called for emergency campus electrical maintenance",
    }, headers=app_mgr_headers)
    assert re_with_reason.status_code == 200, re_with_reason.text
    assert re_with_reason.json()["assigned_to"] == coord_c_data["user_id"]


def test_block_and_unblock_complaint(admin_headers, coord_headers):
    student_headers, _ = _create_user(admin_headers, "student", "std_blk", location_id="LOC_HOSTEL_1")

    c_res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_1",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical",
        "title": "Block unblock test",
        "description": "AC compressor unit noisy",
        "visibility_type": "Private",
    }, headers=student_headers)
    cid = c_res.json()["complaint_id"]
    client.post(f"/complaints/{cid}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=coord_headers)

    # Block
    blk_res = client.post(f"/complaints/{cid}/block", json={
        "reason": "Waiting for OEM spare motor part delivery",
        "expected_date": "2026-10-20",
    }, headers=coord_headers)
    assert blk_res.status_code == 200, blk_res.text
    assert blk_res.json()["status"] == STATUS_BLOCKED
    assert blk_res.json()["blocked_reason"] == "Waiting for OEM spare motor part delivery"

    # Unblock
    unblk_res = client.post(f"/complaints/{cid}/unblock", headers=coord_headers)
    assert unblk_res.status_code == 200, unblk_res.text
    assert unblk_res.json()["status"] == STATUS_IN_PROGRESS


def test_warden_cannot_be_assigned(admin_headers, app_mgr_headers, warden_headers):
    student_headers, _ = _create_user(admin_headers, "student", "std_w_assign", location_id="LOC_HOSTEL_1")

    c_res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_1",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical",
        "title": "Warden assignment prohibition test",
        "description": "Testing that wardens cannot be assigned complaints",
        "visibility_type": "Private",
    }, headers=student_headers)
    cid = c_res.json()["complaint_id"]

    # Try assigning to USR_WARDEN
    w_assign = client.post(f"/complaints/{cid}/assign", json={
        "coordinator_id": "USR_WARDEN",
        "reason": "Attempting invalid assignment to warden",
    }, headers=app_mgr_headers)
    assert w_assign.status_code == 400
    assert "target assignee must be a coordinator" in w_assign.json()["detail"].lower()

