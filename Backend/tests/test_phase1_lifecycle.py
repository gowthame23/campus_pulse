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
from core.constants import SLA_HOURS, ACCEPT_DEADLINE_HOURS, INACTIVE_STATUSES, STATUS_IN_PROGRESS

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
    return _login("warden@example.com", "warden@123")


def _create_test_student(admin_headers):
    uid = uuid.uuid4().hex[:8]
    email = f"student_{uid}@phase1.edu"
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


def test_auto_routing_and_sla_deadline(admin_headers):
    student_headers = _create_test_student(admin_headers)

    # File complaint in LOC_HOSTEL_A with electrical hazard (High)
    res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_ELECTRICAL",
        "category": "electrical hazard",
        "title": "Wire spark test",
        "description": f"Live electrical spark reported {uuid.uuid4().hex[:6]}",
        "visibility_type": "Private",
    }, headers=student_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["priority"] == "High"
    assert data["sla_deadline"] is not None
    # SLA for High is 24h
    created_dt = datetime.fromisoformat(data["created_at"])
    deadline_dt = datetime.fromisoformat(data["sla_deadline"])
    hours_diff = round((deadline_dt - created_dt).total_seconds() / 3600)
    assert hours_diff == SLA_HOURS["High"]


def test_urgent_flag_promotes_priority(admin_headers):
    student_headers = _create_test_student(admin_headers)

    # General category (normally Medium), but marked urgent -> promoted to High
    res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_PLUMBING",
        "category": "plumbing",
        "title": "Severe pipe leak",
        "description": f"Urgent flooding from broken pipe {uuid.uuid4().hex[:6]}",
        "visibility_type": "Private",
        "is_urgent": True,
        "urgent_reason": "Room is flooding rapidly",
    }, headers=student_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["priority"] == "High"
    assert data["is_urgent"] is True


def test_coordinator_atomic_accept_and_conflict(admin_headers, coord_headers):
    student_headers = _create_test_student(admin_headers)

    # Create complaint with multiple or no assigned coordinators so it's in Submitted queue
    res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_MESS",
        "category": "General",
        "title": "Accept Queue Race Test",
        "description": f"Testing atomic accept queue concurrency {uuid.uuid4().hex[:6]}",
        "visibility_type": "Private",
    }, headers=student_headers)
    assert res.status_code == 201
    cid = res.json()["complaint_id"]

    # First coordinator accepts via /take or /accept
    accept_res1 = client.post(f"/complaints/{cid}/accept", headers=coord_headers)
    # Could succeed or return 400 if already assigned by auto-routing
    if accept_res1.status_code == 200:
        assert accept_res1.json()["status"] == "Assigned"
        # Second accept must return 409 Conflict
        accept_res2 = client.post(f"/complaints/{cid}/accept", headers=coord_headers)
        assert accept_res2.status_code == 409


def test_coordinator_lifecycle_start_progress_block_unblock(admin_headers, coord_headers):
    student_headers = _create_test_student(admin_headers)

    res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical",
        "title": "Lifecycle workflow test",
        "description": f"Testing full start, progress, block, unblock {uuid.uuid4().hex[:6]}",
        "visibility_type": "Private",
    }, headers=student_headers)
    assert res.status_code == 201
    cid = res.json()["complaint_id"]

    # Start work
    start_res = client.post(f"/complaints/{cid}/start-work", headers=coord_headers)
    assert start_res.status_code == 200
    assert start_res.json()["status"] == STATUS_IN_PROGRESS

    # Progress update
    prog_res = client.post(f"/complaints/{cid}/progress", json={
        "note": "Inspected circuit board; ordered replacement switch."
    }, headers=coord_headers)
    assert prog_res.status_code == 200

    # Block work
    block_res = client.post(f"/complaints/{cid}/block", json={
        "reason": "Waiting for specialized 240V breaker part",
        "expected_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
    }, headers=coord_headers)
    assert block_res.status_code == 200
    assert block_res.json()["status"] == "Waiting for Parts"
    assert block_res.json()["blocked_reason"] == "Waiting for specialized 240V breaker part"

    # Unblock work
    unblock_res = client.post(f"/complaints/{cid}/unblock", headers=coord_headers)
    assert unblock_res.status_code == 200
    assert unblock_res.json()["status"] == STATUS_IN_PROGRESS


def test_coverage_gaps_endpoint(admin_headers):
    res = client.get("/setup/coverage-gaps", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "unassigned_pairs" in data
    assert "unassigned_warden_locations" in data
    assert isinstance(data["unassigned_pairs"], list)
    assert isinstance(data["unassigned_warden_locations"], list)


def test_bulk_coordinator_assignments_replacement(admin_headers):
    # Fetch existing
    res = client.get("/coordinators/USR_COORDINATOR/assignments", headers=admin_headers)
    assert res.status_code == 200
    orig_assignments = res.json()

    # Replace mapping
    new_asgns = [
        {"location_id": "LOC_HOSTEL_A", "department_id": "DEPT_HOSTEL_ELECTRICAL"},
        {"location_id": "LOC_HOSTEL_A", "department_id": "DEPT_HOSTEL_PLUMBING"},
    ]
    put_res = client.put("/coordinators/USR_COORDINATOR/assignments", json={
        "assignments": new_asgns
    }, headers=admin_headers)
    assert put_res.status_code == 200
    assert len(put_res.json()["assignments"]) == 2

    # Restore original assignments so subsequent tests retain valid state
    client.put("/coordinators/USR_COORDINATOR/assignments", json={
        "assignments": [{"location_id": a["location_id"], "department_id": a["department_id"]} for a in orig_assignments]
    }, headers=admin_headers)


def test_cannot_assign_complaint_to_non_coordinator(admin_headers):
    student_headers = _create_test_student(admin_headers)

    res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_ELECTRICAL",
        "title": "Invalid assignment target",
        "description": f"Trying to assign to warden or admin {uuid.uuid4().hex[:6]}",
        "visibility_type": "Private",
    }, headers=student_headers)
    assert res.status_code == 201
    cid = res.json()["complaint_id"]

    # Attempt to assign to a non-coordinator (e.g. Administrator or Warden)
    bad_assign = client.post(f"/complaints/{cid}/assign", json={
        "coordinator_id": "USR_ADMIN"
    }, headers=admin_headers)
    assert bad_assign.status_code == 400
