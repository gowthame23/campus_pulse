import pytest
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
    assert res.status_code == 200, f"Login failed: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="module")
def admin_headers():
    return _login("gowthamejjurothu@gmail.com", "Admin@123")

@pytest.fixture(scope="module")
def coord_headers():
    return _login("employee.a1@campuspulse.edu", "Employee@123")

@pytest.fixture(scope="module")
def student_headers():
    return _login("gowtham.e23@iiits.in", "Student@123")

def test_unassigned_complaint_direct_soft_delete(student_headers):
    # 1. Student creates unassigned complaint
    res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_1",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical",
        "title": "Unassigned ticket for delete test",
        "description": "Flickering bulb in corridor",
        "visibility_type": "Private",
    }, headers=student_headers)
    assert res.status_code == 201, res.text
    complaint_id = res.json()["complaint_id"]

    # 2. Student directly soft-deletes unassigned complaint
    del_res = client.delete(f"/complaints/{complaint_id}", headers=student_headers)
    assert del_res.status_code == 200, del_res.text
    assert del_res.json().get("status") in ("deleted", "soft_deleted")

    # 3. Verify it does not appear in active listings
    list_res = client.get("/complaints", headers=student_headers)
    assert list_res.status_code == 200
    active_ids = [c["complaint_id"] for c in list_res.json()]
    assert complaint_id not in active_ids

def test_assigned_complaint_cannot_be_directly_deleted(student_headers, admin_headers):
    # 1. Student creates complaint
    res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_1",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical",
        "title": "Assigned ticket delete blocked test",
        "description": "Geyser element burned",
        "visibility_type": "Private",
    }, headers=student_headers)
    assert res.status_code == 201
    complaint_id = res.json()["complaint_id"]

    # 2. Admin assigns complaint to coordinator
    assign_res = client.post(f"/complaints/{complaint_id}/assign", json={
        "assigned_to": "USR_EMP_A1",
        "reason": "Assigning for repair"
    }, headers=admin_headers)
    assert assign_res.status_code == 200

    # 3. Student attempts direct delete -> MUST return 400
    del_res = client.delete(f"/complaints/{complaint_id}", headers=student_headers)
    assert del_res.status_code == 400
    assert "cancellation" in del_res.json()["detail"].lower()

def test_assigned_complaint_cancellation_workflow(student_headers, admin_headers):
    # 1. Create and assign complaint
    res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_1",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical",
        "title": "Cancellation lifecycle test",
        "description": "Water cooler sparking",
        "visibility_type": "Private",
    }, headers=student_headers)
    assert res.status_code == 201
    complaint_id = res.json()["complaint_id"]

    assign_res = client.post(f"/complaints/{complaint_id}/assign", json={
        "assigned_to": "USR_EMP_A1",
        "reason": "Urgent electrical dispatch"
    }, headers=admin_headers)
    assert assign_res.status_code == 200

    # 2. Student requests cancellation
    cancel_req_res = client.post(f"/complaints/{complaint_id}/request-cancellation", json={
        "reason": "The maintenance staff fixed it while doing routine rounds."
    }, headers=student_headers)
    assert cancel_req_res.status_code == 200, cancel_req_res.text
    cancel_data = cancel_req_res.json()
    assert cancel_data["status"] == "Cancellation Requested"
    assert cancel_data["cancellation_requested"] is True
    assert "maintenance staff fixed it" in cancel_data["cancellation_reason"]

    # 3. Admin / In-scope Coordinator reviews and approves
    approve_res = client.post(f"/complaints/{complaint_id}/approve-cancellation", json={
        "note": "Verified with hostel resident. Ticket cancelled."
    }, headers=admin_headers)
    assert approve_res.status_code == 200, approve_res.text
    appr_data = approve_res.json()
    assert appr_data["status"] == "Cancelled"

def test_cancellation_rejection_restores_status(student_headers, admin_headers):
    # 1. Create and assign complaint
    res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_1",
        "department_id": "DEPT_HOSTEL_ELECTRICAL",
        "category": "electrical",
        "title": "Cancellation rejection test",
        "description": "AC compressor humming",
        "visibility_type": "Private",
    }, headers=student_headers)
    assert res.status_code == 201
    complaint_id = res.json()["complaint_id"]

    client.post(f"/complaints/{complaint_id}/assign", json={
        "assigned_to": "USR_EMP_A1",
        "reason": "HVAC dispatch"
    }, headers=admin_headers)

    # 2. Request cancellation
    client.post(f"/complaints/{complaint_id}/request-cancellation", json={
        "reason": "Mistaken ticket submission"
    }, headers=student_headers)

    # 3. Reject cancellation
    reject_res = client.post(f"/complaints/{complaint_id}/reject-cancellation", json={
        "reason": "Technician is already on premises with replacement motor."
    }, headers=admin_headers)
    assert reject_res.status_code == 200, reject_res.text
    rej_data = reject_res.json()
    # Restored to Assigned
    assert rej_data["status"] in ("Assigned", "Going On")
    assert rej_data["cancellation_requested"] is False
