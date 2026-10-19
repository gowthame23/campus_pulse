import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def login(username, password):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, f"Login failed for {username}: {res.text}"
    token = res.cookies.get("session_token")
    return {"Cookie": f"session_token={token}"} if token else {}


def test_eligible_coordinators_endpoint():
    admin_hdr = login("gowthamejjurothu@gmail.com", "Admin@123")
    res = client.get("/teams/eligible-coordinators", headers=admin_hdr)
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 6

    # Verify employees remain eligible across teams/departments
    a1 = next((u for u in data if u["user_id"] == "USR_EMP_A1"), None)
    assert a1 is not None
    assert a1["is_eligible"] is True
    assert a1["current_position"] == "Coordinator 1"

    a2 = next((u for u in data if u["user_id"] == "USR_EMP_A2"), None)
    assert a2 is not None
    assert a2["is_eligible"] is True
    assert a2["current_position"] == "Coordinator 2"

    a3 = next((u for u in data if u["user_id"] == "USR_EMP_A3"), None)
    assert a3 is not None
    assert a3["is_eligible"] is True


def test_intra_team_coordinator_rule_rejection_and_multi_department_allowed():
    admin_hdr = login("gowthamejjurothu@gmail.com", "Admin@123")

    # 1. Attempt to assign same person as Coordinator 1 and Backup Coordinator on same team -> REJECTED
    res = client.post(
        "/teams",
        json={
            "name": "Same Person Team",
            "department_id": "DEPT_HOSTEL_PLUMBING",
            "coordinator_id": "USR_EMP_A3",
            "backup_coordinator_id": "USR_EMP_A3",
            "location_ids": ["LOC_ACADEMIC_1"],
        },
        headers=admin_hdr,
    )
    assert res.status_code == 400
    assert "cannot be both Coordinator 1 and Coordinator 2" in res.json()["detail"]

    # 2. Assigning an employee to coordinate multiple teams/departments -> ALLOWED
    res = client.post(
        "/teams",
        json={
            "name": "Multi Coord Team",
            "department_id": "DEPT_HOSTEL_PLUMBING",
            "coordinator_id": "USR_EMP_A1",
            "location_ids": ["LOC_ACADEMIC_1"],
        },
        headers=admin_hdr,
    )
    assert res.status_code == 201
    created_team = res.json()
    # Clean up created team
    client.delete(f"/teams/{created_team['team_id']}", headers=admin_hdr)


def test_work_memberships_crud_and_scoping():
    mgr1_hdr = login("ejjurothugowtham@gmail.com", "Manager@123")

    # App Manager in scope: LOC_ACADEMIC_1 is in Manager 1's facilities
    res = client.post(
        "/teams/work-memberships",
        json={
            "user_id": "USR_EMP_A3",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "location_id": "LOC_ACADEMIC_1",
        },
        headers=mgr1_hdr,
    )
    assert res.status_code == 201
    membership = res.json()
    assert membership["user_id"] == "USR_EMP_A3"
    assert membership["location_id"] == "LOC_ACADEMIC_1"
    membership_id = membership["membership_id"]

    # App Manager out of scope: LOC_HOSTEL_2 is in Group 2 facilities
    res_bad = client.post(
        "/teams/work-memberships",
        json={
            "user_id": "USR_EMP_A3",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "location_id": "LOC_HOSTEL_2",
        },
        headers=mgr1_hdr,
    )
    assert res_bad.status_code == 403

    # Delete membership
    res_del = client.delete(f"/teams/work-memberships/{membership_id}", headers=mgr1_hdr)
    assert res_del.status_code == 200


def test_employees_overview_endpoint():
    admin_hdr = login("gowthamejjurothu@gmail.com", "Admin@123")
    res = client.get("/teams/employees-overview", headers=admin_hdr)
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 6
    for emp in data:
        assert "memberships" in emp
        assert "coordinator_role" in emp
        assert "open_jobs" in emp


def test_complaint_job_visibility_and_actions():
    # 1. Student files a complaint
    student_hdr = login("gowtham.e23@iiits.in", "Student@123")
    res = client.post(
        "/complaints",
        json={
            "title": "Flickering Light in Room 101",
            "description": "The ceiling tube light is constantly flickering and making a buzzing noise.",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "location_id": "LOC_HOSTEL_1",
            "category": "Lighting",
            "priority": "Medium",
        },
        headers=student_hdr,
    )
    assert res.status_code == 201, f"Create complaint failed: {res.text}"
    comp = res.json()
    complaint_id = comp["complaint_id"]

    # 2. Coordinator (USR_EMP_A1) assigns to Employee A3
    coord_hdr = login("employee.a1@campuspulse.edu", "Employee@123")
    res_assign = client.post(
        f"/complaints/{complaint_id}/assign",
        json={"assignee_id": "USR_EMP_A3"},
        headers=coord_hdr,
    )
    assert res_assign.status_code == 200

    # 3. Employee A3 logs in and queries their assigned jobs
    emp3_hdr = login("employee.a3@campuspulse.edu", "Employee@123")
    res_jobs = client.get("/complaints?include_archived=false", headers=emp3_hdr)
    assert res_jobs.status_code == 200
    my_jobs = [c for c in res_jobs.json() if c["assigned_to"] == "USR_EMP_A3"]
    assert any(c["complaint_id"] == complaint_id for c in my_jobs)

    # 4. Employee starts job
    res_start = client.patch(
        f"/complaints/{complaint_id}/status",
        json={"status": "In Progress"},
        headers=emp3_hdr,
    )
    assert res_start.status_code == 200
    assert res_start.json()["status"] == "In Progress"

    # 5. Employee marks job resolved
    res_resolve = client.post(
        f"/complaints/{complaint_id}/resolve",
        json={
            "notes": "Replaced the fluorescent tube and starter with new LED fixture.",
            "skip_photo": True,
            "photo_skip_reason": "No camera available during maintenance",
        },
        headers=emp3_hdr,
    )
    assert res_resolve.status_code == 200
    assert res_resolve.json()["status"] in ("Resolved", "Waiting for Verification")
