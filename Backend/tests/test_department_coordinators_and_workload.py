import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def login(username, password):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, f"Login failed for {username}: {res.text}"
    token = res.cookies.get("session_token")
    return {"Cookie": f"session_token={token}"} if token else {}


def test_department_coordinators_retrieval_and_eligibility():
    admin_hdr = login("gowthamejjurothu@gmail.com", "Admin@123")

    # Fetch eligible coordinators for DEPT_HOSTEL_ELECTRICAL
    res = client.get("/departments/DEPT_HOSTEL_ELECTRICAL/eligible-coordinators", headers=admin_hdr)
    assert res.status_code == 200
    candidates = res.json()
    assert len(candidates) >= 6

    # USR_EMP_A1 is currently Coordinator 1 for DEPT_HOSTEL_ELECTRICAL -> eligible
    emp_a1 = next((c for c in candidates if c["user_id"] == "USR_EMP_A1"), None)
    assert emp_a1 is not None
    assert emp_a1["is_eligible"] is True
    assert emp_a1["current_position"] == "Coordinator 1"

    # USR_EMP_B1 is Coordinator 1 for Plumbing -> ALSO eligible for Electrical (multi-coordination allowed)
    emp_b1 = next((c for c in candidates if c["user_id"] == "USR_EMP_B1"), None)
    assert emp_b1 is not None
    assert emp_b1["is_eligible"] is True

    # USR_EMP_B2 is Coordinator 2 for Plumbing -> ALSO eligible for Electrical
    emp_b2 = next((c for c in candidates if c["user_id"] == "USR_EMP_B2"), None)
    assert emp_b2 is not None
    assert emp_b2["is_eligible"] is True

    # USR_EMP_A3 holds no coordinator position -> ELIGIBLE
    emp_a3 = next((c for c in candidates if c["user_id"] == "USR_EMP_A3"), None)
    assert emp_a3 is not None
    assert emp_a3["is_eligible"] is True
    assert emp_a3["current_position"] is None


def test_department_coordinator_rules_and_multi_department_support():
    admin_hdr = login("gowthamejjurothu@gmail.com", "Admin@123")

    # 1. Reject same person as both Coordinator 1 and Coordinator 2 in same department
    res = client.put(
        "/departments/DEPT_HOSTEL_ELECTRICAL/coordinators",
        json={"coordinator_1_id": "USR_EMP_A3", "coordinator_2_id": "USR_EMP_A3"},
        headers=admin_hdr,
    )
    assert res.status_code == 400
    assert "cannot be the same employee" in res.json()["detail"]

    # 2. Allow an employee (USR_EMP_A1) to coordinate multiple departments simultaneously
    res = client.put(
        "/departments/DEPT_HOSTEL_PLUMBING/coordinators",
        json={"coordinator_1_id": "USR_EMP_A1", "coordinator_2_id": "USR_EMP_B2"},
        headers=admin_hdr,
    )
    assert res.status_code == 200
    updated_dept = res.json()
    assert updated_dept["coordinator_id"] == "USR_EMP_A1"

    # Restore Plumbing coordinator 1 to USR_EMP_B1
    res_restore = client.put(
        "/departments/DEPT_HOSTEL_PLUMBING/coordinators",
        json={"coordinator_1_id": "USR_EMP_B1", "coordinator_2_id": "USR_EMP_B2"},
        headers=admin_hdr,
    )
    assert res_restore.status_code == 200


def test_department_coordinator_routing_when_available():
    student_hdr = login("gowtham.e23@iiits.in", "Student@123")

    # Create a complaint in Hostel 1 for Electrical
    res = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "Lighting & Electrical",
            "complaint_type": "Tube light flickering in common study room",
            "title": "Study Room Light Broken",
            "description": "Tube light flickering heavily in study hall, please replace.",
            "priority": "Medium",
        },
        headers=student_hdr,
    )
    assert res.status_code == 201
    complaint_data = res.json()
    complaint_id = complaint_data["complaint_id"]
    assert complaint_data["status"] == "Submitted"
    assert complaint_data["assign_escalation_level"] == 0

    # Coordinator 1 (USR_EMP_A1) should have received a notification
    a1_hdr = login("employee.a1@campuspulse.edu", "Employee@123")
    notif_res = client.get("/notifications", headers=a1_hdr)
    assert notif_res.status_code == 200
    notifs = notif_res.json()
    assert any(n.get("complaint_id") == complaint_id for n in notifs)


def test_department_coordinator_routing_when_coord1_on_leave():
    # Put Coordinator 1 (USR_EMP_A1) on leave
    a1_hdr = login("employee.a1@campuspulse.edu", "Employee@123")
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

    leave_res = client.post(
        "/leaves",
        json={
            "from_date": today,
            "to_date": tomorrow,
            "reason": "Family function emergency",
        },
        headers=a1_hdr,
    )
    assert leave_res.status_code == 201

    # Submit complaint as student
    student_hdr = login("gowtham.e23@iiits.in", "Student@123")
    res = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "Lighting & Electrical",
            "complaint_type": "Switch board spark",
            "title": "Corridor Switch Board Sparking",
            "description": "Corridor switch sparks whenever touched, safety hazard.",
            "priority": "High",
        },
        headers=student_hdr,
    )
    assert res.status_code == 201
    complaint_data = res.json()
    complaint_id = complaint_data["complaint_id"]

    # Since Coordinator 1 is on leave, Coordinator 2 (USR_EMP_A2) should receive notification
    a2_hdr = login("employee.a2@campuspulse.edu", "Employee@123")
    notif_res = client.get("/notifications", headers=a2_hdr)
    assert notif_res.status_code == 200
    notifs = notif_res.json()
    assert any(n.get("complaint_id") == complaint_id for n in notifs)

    # Cancel leave to keep clean state
    leave_id = leave_res.json().get("leave_id")
    if leave_id:
        cancel_res = client.delete(f"/leaves/{leave_id}", headers=a1_hdr)
        assert cancel_res.status_code == 200


def test_eligible_assignees_and_cross_department_workload():
    student_hdr = login("gowtham.e23@iiits.in", "Student@123")
    res = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "Lighting & Electrical",
            "complaint_type": "Ceiling fan speed regulator",
            "title": "Room Fan Regulator Burned",
            "description": f"Fan speed regulator burned out and smell coming from regulator {int(datetime.now().timestamp())}.",
            "priority": "Medium",
        },
        headers=student_hdr,
    )
    assert res.status_code == 201
    complaint_id = res.json()["complaint_id"]

    # Coordinator 1 queries eligible assignees
    a1_hdr = login("employee.a1@campuspulse.edu", "Employee@123")
    assignees_res = client.get(f"/complaints/{complaint_id}/eligible-assignees", headers=a1_hdr)
    assert assignees_res.status_code == 200
    assignees = assignees_res.json()
    assert len(assignees) >= 3

    # Verify only Electrical technicians for Hostel 1 are returned
    user_ids = [a["user_id"] for a in assignees]
    assert "USR_EMP_A1" in user_ids
    assert "USR_EMP_A2" in user_ids
    assert "USR_EMP_A3" in user_ids
    # Plumbers (USR_EMP_B1, USR_EMP_B2, USR_EMP_B3 at Hostel 2) must NOT be in eligible assignees
    assert "USR_EMP_B1" not in user_ids

    # Verify privacy rules: NO student reporter details, descriptions, or attachments
    for a in assignees:
        assert "workload_state" in a
        assert a["workload_state"] in ("available", "assigned", "on_leave")
        assert "active_jobs_count" in a
        assert "active_jobs" in a
        for job in a["active_jobs"]:
            assert "complaint_id" in job
            assert "title" in job
            assert "department_name" in job
            assert "location_name" in job
            assert "status" in job
            assert "priority" in job
            # Critical privacy constraints
            assert "created_by" not in job
            assert "student_name" not in job
            assert "description" not in job
            assert "attachment_url" not in job

    # Assign work to USR_EMP_A3
    assign_res = client.post(
        f"/complaints/{complaint_id}/assign",
        json={"assigned_to": "USR_EMP_A3", "reason": "Electrician A3 available for Hostel 1 repairs"},
        headers=a1_hdr,
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["assigned_to"] == "USR_EMP_A3"
    assert assign_res.json()["status"] == "Assigned"

    # Query eligible assignees again -> USR_EMP_A3 now has workload_state == 'assigned' and active_jobs_count == 1
    assignees_res2 = client.get(f"/complaints/{complaint_id}/eligible-assignees", headers=a1_hdr)
    assert assignees_res2.status_code == 200
    a3_data = next((a for a in assignees_res2.json() if a["user_id"] == "USR_EMP_A3"), None)
    assert a3_data is not None
    assert a3_data["active_jobs_count"] >= 1
    assert a3_data["workload_state"] == "assigned"
