import os
import sys
import uuid
import pytest

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
def coord_headers():
    return _login("coordinator@example.com", "Coordinator@123")


@pytest.fixture(scope="module")
def warden_headers():
    try:
        return _login("naveen@campus.edu", "warden@123")
    except Exception:
        return _login("warden@example.com", "warden@123")


def _create_test_student(admin_headers):
    uid = uuid.uuid4().hex[:8]
    email = f"student_{uid}@phase2.edu"
    res = client.post("/users", json={
        "name": f"Student {uid}",
        "email": email,
        "role": "student",
        "password": "Temp@Pass123",
        "confirm_password": "Temp@Pass123",
        "location_id": "LOC_HOSTEL_A",
    }, headers=admin_headers)
    assert res.status_code == 201

    headers = _login(email, "Temp@Pass123")
    res2 = client.post("/auth/change-password", json={
        "old_password": "Temp@Pass123",
        "new_password": "Stud@Pass456",
        "confirm_password": "Stud@Pass456",
    }, headers=headers)
    assert res2.status_code == 200
    return _login(email, "Stud@Pass456")


def _upload_after_repair(cid, headers):
    res = client.post(
        f"/complaints/{cid}/attachments",
        data={"category": "After Repair"},
        files={"files": ("fixed.jpg", b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00repairphoto", "image/jpeg")},
        headers=headers,
    )
    assert res.status_code == 200, f"Attachment upload failed: {res.text}"
    return res


def test_resolve_high_critical_requires_photo(admin_headers, coord_headers):
    student_headers = _create_test_student(admin_headers)

    # 1. Create a complaint where student included a photo
    res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical hazard",
        "title": "Exposed high voltage wire",
        "description": f"Dangerous live wire hanging in corridor {uuid.uuid4().hex[:6]}",
        "visibility_type": "Private",
        "priority": "Medium",
        "attachment_url": "/static/uploads/hazard.jpg",
    }, headers=student_headers)
    assert res.status_code == 201
    cid = res.json()["complaint_id"]

    # Start work
    client.post(f"/complaints/{cid}/start-work", headers=coord_headers)

    # 2. Attempt resolve without After Repair photo or skip -> MUST FAIL WITH 400
    fail_res = client.put(f"/complaints/{cid}/resolve", json={"notes": "Wire taped."}, headers=coord_headers)
    assert fail_res.status_code == 400
    assert "after photo" in fail_res.json()["detail"].lower() or "skip_photo" in fail_res.json()["detail"].lower()

    # 3. Upload 'After Repair' attachment
    _upload_after_repair(cid, coord_headers)

    # 4. Resolve now succeeds
    ok_res = client.put(f"/complaints/{cid}/resolve", json={"notes": "Replaced wiring and insulated conduit."}, headers=coord_headers)
    assert ok_res.status_code == 200
    data = ok_res.json()
    assert data["fixed_at"] is not None
    assert data["fixed_by"] is not None


def test_warden_verify_self_verification_guard(admin_headers, coord_headers, warden_headers):
    student_headers = _create_test_student(admin_headers)

    # Student files a High priority complaint
    res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical hazard",
        "title": "Self verification guard test",
        "description": f"Testing self-verification guard {uuid.uuid4().hex[:6]}",
        "visibility_type": "Private",
        "priority": "High",
    }, headers=student_headers)
    assert res.status_code == 201
    cid = res.json()["complaint_id"]

    # Coordinator takes/starts work, uploads after repair photo, and marks resolved
    client.post(f"/complaints/{cid}/start-work", headers=coord_headers)
    _upload_after_repair(cid, coord_headers)
    res_ok = client.put(f"/complaints/{cid}/resolve", json={"notes": "Repaired by coordinator"}, headers=coord_headers)
    assert res_ok.status_code == 200
    assert res_ok.json()["status"] == "Pending Warden Verification"

    # Assignee (coordinator) attempts to verify -> MUST BE REJECTED WITH 403
    coord_v = client.post(f"/complaints/{cid}/warden-verify", json={"verdict": "Verified", "notes": "Coordinator approved"}, headers=coord_headers)
    assert coord_v.status_code == 403

    # Student verify is rejected while Pending Warden Verification
    stud_v = client.post(f"/complaints/{cid}/verify", headers=student_headers)
    assert stud_v.status_code == 400

    # Warden of LOC_HOSTEL_A verifies -> succeeds -> Waiting for Verification
    w_res = client.post(f"/complaints/{cid}/warden-verify", json={"verdict": "Verified", "notes": "Approved by warden"}, headers=warden_headers)
    assert w_res.status_code == 200
    assert w_res.json()["status"] == "Waiting for Verification"


def test_warden_verify_flow_verified_and_not_fixed(admin_headers, coord_headers, warden_headers):
    student_headers = _create_test_student(admin_headers)

    res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical hazard",
        "title": "Two-tier verification lifecycle",
        "description": f"Testing warden verification flows {uuid.uuid4().hex[:6]}",
        "visibility_type": "Private",
        "priority": "High",
    }, headers=student_headers)
    cid = res.json()["complaint_id"]

    client.post(f"/complaints/{cid}/start-work", headers=coord_headers)
    _upload_after_repair(cid, coord_headers)
    client.put(f"/complaints/{cid}/resolve", json={"notes": "Work done"}, headers=coord_headers)

    # 1. Warden inspects: Not Fixed -> returns to In Progress
    nf_res = client.post(f"/complaints/{cid}/warden-verify", json={
        "verdict": "Not Fixed",
        "notes": "Cover plate is missing, wires still exposed."
    }, headers=warden_headers)
    assert nf_res.status_code == 200
    assert nf_res.json()["status"] == "In Progress"

    # 2. Coordinator fixes again and marks resolved
    client.put(f"/complaints/{cid}/resolve", json={"notes": "Installed secure cover plate."}, headers=coord_headers)

    # 3. Warden inspects: Verified -> advances to Waiting for Verification
    v_res = client.post(f"/complaints/{cid}/warden-verify", json={
        "verdict": "Verified",
        "notes": "Inspected in person; installation complete and secure."
    }, headers=warden_headers)
    assert v_res.status_code == 200
    assert v_res.json()["status"] == "Waiting for Verification"
    assert v_res.json()["student_stage_at"] is not None
    assert v_res.json()["verification_due_at"] is not None


def test_student_confirm_and_close(admin_headers, coord_headers, warden_headers):
    student_headers = _create_test_student(admin_headers)

    res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical hazard",
        "title": "Student close test",
        "description": f"Testing student close {uuid.uuid4().hex[:6]}",
        "visibility_type": "Private",
        "priority": "High",
    }, headers=student_headers)
    cid = res.json()["complaint_id"]

    client.post(f"/complaints/{cid}/start-work", headers=coord_headers)
    _upload_after_repair(cid, coord_headers)
    client.put(f"/complaints/{cid}/resolve", json={"notes": "Fixed"}, headers=coord_headers)
    client.post(f"/complaints/{cid}/warden-verify", json={"verdict": "Verified", "notes": "Approved"}, headers=warden_headers)

    # Student confirms fixed -> Closed
    close_res = client.post(f"/complaints/{cid}/close", headers=student_headers)
    assert close_res.status_code == 200
    assert close_res.json()["status"] == "Closed"
    assert close_res.json()["closed_at"] is not None


def test_reopen_escalation_to_admin_review_on_third_reopen(admin_headers, coord_headers, warden_headers):
    student_headers = _create_test_student(admin_headers)

    res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical hazard",
        "title": "Dispute limit escalation test",
        "description": f"Testing 3-reopen limit escalation to Admin Review {uuid.uuid4().hex[:6]}",
        "visibility_type": "Private",
        "priority": "High",
    }, headers=student_headers)
    cid = res.json()["complaint_id"]

    def _resolve_and_verify():
        client.post(f"/complaints/{cid}/start-work", headers=coord_headers)
        _upload_after_repair(cid, coord_headers)
        r_ok = client.put(f"/complaints/{cid}/resolve", json={"notes": "Resolved attempt"}, headers=coord_headers)
        assert r_ok.status_code == 200
        w_ok = client.post(f"/complaints/{cid}/warden-verify", json={"verdict": "Verified", "notes": "Checked"}, headers=warden_headers)
        assert w_ok.status_code == 200

    # First cycle
    _resolve_and_verify()
    r1 = client.post(f"/complaints/{cid}/reopen", json={"reason": "Still sparking at night"}, headers=student_headers)
    assert r1.status_code == 200
    assert r1.json()["status"] == "Reopened"
    assert r1.json()["reopen_count"] == 1

    # Second cycle
    _resolve_and_verify()
    r2 = client.post(f"/complaints/{cid}/reopen", json={"reason": "Sparked again after heavy rain"}, headers=student_headers)
    assert r2.status_code == 200
    assert r2.json()["status"] == "Reopened"
    assert r2.json()["reopen_count"] == 2

    # Third cycle -> Exceeds max reopens -> ESCALATES TO ADMIN REVIEW
    _resolve_and_verify()
    r3 = client.post(f"/complaints/{cid}/reopen", json={"reason": "Persistent fire hazard, still not fixed!"}, headers=student_headers)
    assert r3.status_code == 200
    data3 = r3.json()
    assert data3["status"] == "Admin Review"
    assert data3["reopen_count"] == 3
    assert "Exceeded maximum reopens" in (data3["admin_review_reason"] or "")


def test_admin_decision_on_disputed_ticket(admin_headers, coord_headers, warden_headers):
    student_headers = _create_test_student(admin_headers)

    res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical hazard",
        "title": "Admin review decision workflow",
        "description": f"Testing admin resolution decision {uuid.uuid4().hex[:6]}",
        "visibility_type": "Private",
        "priority": "High",
    }, headers=student_headers)
    cid = res.json()["complaint_id"]

    for _ in range(3):
        client.post(f"/complaints/{cid}/start-work", headers=coord_headers)
        _upload_after_repair(cid, coord_headers)
        client.put(f"/complaints/{cid}/resolve", json={"notes": "Resolved"}, headers=coord_headers)
        client.post(f"/complaints/{cid}/warden-verify", json={"verdict": "Verified", "notes": "Approved"}, headers=warden_headers)
        client.post(f"/complaints/{cid}/reopen", json={"reason": "Not satisfactory"}, headers=student_headers)

    # Complaint is now in Admin Review
    get_res = client.get(f"/complaints/{cid}", headers=admin_headers)
    assert get_res.json()["status"] == "Admin Review"

    # Administrator decides to Close ticket
    dec_res = client.post(f"/complaints/{cid}/admin-decision", json={
        "decision": "Close",
        "notes": "Independent engineering inspection conducted. Device meets safety standards."
    }, headers=admin_headers)
    assert dec_res.status_code == 200
    assert dec_res.json()["status"] == "Closed"
    assert "Independent engineering inspection" in dec_res.json()["admin_decision"]


def test_coordinator_stats_endpoint(admin_headers):
    res = client.get("/coordinators/stats", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    for key in ("coordinator_id", "name", "email", "assigned_count", "in_progress_count", "resolved_last_30_days", "avg_resolution_hours", "reopen_rate", "overdue_count"):
        assert key in first
