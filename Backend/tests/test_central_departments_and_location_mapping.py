import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def login(username, password):
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, f"Login failed for {username}: {res.text}"
    token = res.cookies.get("session_token")
    return {"Cookie": f"session_token={token}"} if token else {}


@pytest.fixture(scope="module")
def admin_hdr():
    return login("gowthamejjurothu@gmail.com", "Admin@123")


@pytest.fixture(scope="module")
def app_mgr_hdr():
    # Manager for Hostel 1 (USR_MANAGER)
    return login("ejjurothugowtham@gmail.com", "Manager@123")


@pytest.fixture(scope="module")
def student_hdr():
    # Student in Hostel 1 (USR_STUDENT)
    return login("gowtham.e23@iiits.in", "Student@123")


def test_scenario_1_to_4_central_department_creation_and_multi_location_mapping(admin_hdr):
    """
    Scenarios 1-4:
    1. Create a campus-wide Electrical department.
    2. Associate Electrical with Hostel 1.
    3. Associate the same Electrical department with Hostel 2.
    4. Verify that only one Electrical department record exists.
    """
    from api.dependencies import get_auth_service
    auth_svc = get_auth_service()
    dept_name = "Central Robotics & Automation"
    with auth_svc._connect() as conn:
        conn.execute("DELETE FROM location_departments WHERE department_id IN (SELECT department_id FROM departments WHERE lower(name) = lower(?))", (dept_name,))
        conn.execute("DELETE FROM departments WHERE lower(name) = lower(?)", (dept_name,))
        conn.commit()
    res = client.post(
        "/departments",
        json={
            "name": dept_name,
            "description": "Campus-wide automated systems, robotics labs, and microcontrollers",
            "sla_days": 2,
            "complaint_types": ["Sensor Fault", "Controller Defect", "Firmware Bug"],
            "location_ids": ["LOC_HOSTEL_1"],  # Associate with Hostel 1 initially
        },
        headers=admin_hdr,
    )
    assert res.status_code == 201, f"Failed to create central department: {res.text}"
    new_dept = res.json()
    dept_id = new_dept["department_id"]
    assert new_dept["name"] == dept_name
    assert new_dept["description"] == "Campus-wide automated systems, robotics labs, and microcontrollers"
    assert "LOC_HOSTEL_1" in new_dept.get("location_ids", [])

    # 2 & 3. Associate with both Hostel 1 and Hostel 2
    res = client.put(
        f"/departments/{dept_id}/locations",
        json={"location_ids": ["LOC_HOSTEL_1", "LOC_HOSTEL_2"]},
        headers=admin_hdr,
    )
    assert res.status_code == 200, f"Failed to update locations: {res.text}"
    updated_locs = res.json()
    assert "LOC_HOSTEL_1" in updated_locs["location_ids"]
    assert "LOC_HOSTEL_2" in updated_locs["location_ids"]

    # 4. Verify only ONE department record exists with this name campus-wide
    res = client.get("/departments", headers=admin_hdr)
    assert res.status_code == 200
    all_depts = res.json()
    matching = [d for d in all_depts if d["name"].lower() == dept_name.lower()]
    assert len(matching) == 1, f"Expected exactly 1 department record, found {len(matching)}"
    assert set(matching[0]["location_ids"]) == {"LOC_HOSTEL_1", "LOC_HOSTEL_2"}


def test_scenario_5_to_7_dissociation_and_complaint_filtering(admin_hdr, student_hdr):
    """
    Scenarios 5-7:
    5. Remove department from Hostel 1 without removing it from Hostel 2.
    6. Verify that Hostel 1 no longer offers it during complaint submission.
    7. Verify that Hostel 2 still offers it.
    """
    # Use existing canonical DEPT_HOSTEL_ELECTRICAL
    dept_id = "DEPT_HOSTEL_ELECTRICAL"

    # Ensure it's currently mapped to both LOC_HOSTEL_1 and LOC_HOSTEL_2
    client.put(
        f"/departments/{dept_id}/locations",
        json={"location_ids": ["LOC_HOSTEL_1", "LOC_HOSTEL_2"]},
        headers=admin_hdr,
    )

    # Verify Hostel 1 offers it
    res = client.get("/departments?location_id=LOC_HOSTEL_1", headers=student_hdr)
    assert res.status_code == 200
    h1_depts = [d["department_id"] for d in res.json()]
    assert dept_id in h1_depts

    # 5. Remove from Hostel 1, keeping only Hostel 2
    res = client.put(
        f"/departments/{dept_id}/locations",
        json={"location_ids": ["LOC_HOSTEL_2"]},
        headers=admin_hdr,
    )
    assert res.status_code == 200

    # 6. Verify Hostel 1 no longer offers it
    res = client.get("/departments?location_id=LOC_HOSTEL_1", headers=student_hdr)
    assert res.status_code == 200
    h1_depts_after = [d["department_id"] for d in res.json()]
    assert dept_id not in h1_depts_after, "Department should no longer be offered at Hostel 1"

    # 7. Verify Hostel 2 still offers it
    res = client.get("/departments?location_id=LOC_HOSTEL_2", headers=student_hdr)
    assert res.status_code == 200
    h2_depts = [d["department_id"] for d in res.json()]
    assert dept_id in h2_depts, "Department must still be offered at Hostel 2"

    # Restore Electrical mapping for subsequent tests
    client.put(
        f"/departments/{dept_id}/locations",
        json={"location_ids": ["LOC_HOSTEL_1", "LOC_HOSTEL_2", "LOC_ACADEMIC_1", "LOC_ACADEMIC_2", "LOC_SAC_1", "LOC_SAC_2", "LOC_SPORTS_1", "LOC_SPORTS_2", "LOC_OTHER"]},
        headers=admin_hdr,
    )


def test_scenario_8_reject_unassociated_department_complaint(student_hdr, admin_hdr):
    """
    Scenario 8:
    Reject a complaint submitted with a department not associated with its location.
    Backend must return HTTP 400 Bad Request with an informative error message.
    """
    # DEPT_SAC_AV is for SAC, not associated with LOC_HOSTEL_1
    # Ensure DEPT_SAC_AV is actively mapped to LOC_SAC_1 only
    client.put(
        "/departments/DEPT_SAC_AV/locations",
        json={"location_ids": ["LOC_SAC_1"]},
        headers=admin_hdr,
    )

    # Attempt to submit complaint to LOC_HOSTEL_1 with DEPT_SAC_AV
    res = client.post(
        "/complaints",
        json={
            "title": "Stage lights in student dorm room",
            "description": "Attempting invalid submission with unassociated department.",
            "category": "Stage Lighting",
            "priority": "Low",
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_SAC_AV",
            "visibility": "General",
        },
        headers=student_hdr,
    )
    assert res.status_code == 400, f"Expected 400 Bad Request, got {res.status_code}: {res.text}"
    detail = res.json().get("detail", "")
    assert "not available or associated with the selected location" in detail.lower()


def test_scenario_9_and_10_coordinators_manage_complaints_across_locations(admin_hdr):
    """
    Scenarios 9 & 10:
    9. Assign Coordinator 1 and Coordinator 2 to Electrical.
    10. Verify that both coordinators manage Electrical complaints across authorized locations.
    """
    # DEPT_HOSTEL_ELECTRICAL coordinators: USR_EMP_A1 (Coord 1), USR_EMP_A2 (Coord 2)
    res = client.put(
        "/departments/DEPT_HOSTEL_ELECTRICAL/coordinators",
        json={
            "coordinator_1_id": "USR_EMP_A1",
            "coordinator_2_id": "USR_EMP_A2",
        },
        headers=admin_hdr,
    )
    assert res.status_code == 200

    # Verify department info contains both coordinator 1 and 2
    res = client.get("/departments/DEPT_HOSTEL_ELECTRICAL", headers=admin_hdr)
    assert res.status_code == 200
    dept_info = res.json()
    assert dept_info["coordinator_id"] == "USR_EMP_A1"
    assert dept_info["coordinator_2_id"] == "USR_EMP_A2"
    assert dept_info["coordinator_1"]["user_id"] == "USR_EMP_A1"
    assert dept_info["coordinator_2"]["user_id"] == "USR_EMP_A2"


def test_scenario_11_coordinator_2_takeover_when_coordinator_1_on_leave():
    """
    Scenario 11:
    Test that Coordinator 2 takes over if Coordinator 1 is absent.
    """
    # Coordinator 1: USR_EMP_A1, Coordinator 2: USR_EMP_A2
    # Verify using auth_service.get_active_coordinator_for_department
    from api.dependencies import get_auth_service
    auth_service = get_auth_service()

    # Normal state: Coordinator 1 is active
    active_coord = auth_service.get_active_coordinator_for_department("DEPT_HOSTEL_ELECTRICAL")
    assert active_coord is not None
    assert active_coord.user_id == "USR_EMP_A1"

    # Simulate USR_EMP_A1 on leave by inserting into user_leaves
    import uuid
    from datetime import datetime, timedelta
    start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    now_iso = datetime.now().isoformat()

    with auth_service._connect() as conn:
        conn.execute(
            """
            INSERT INTO user_leaves (leave_id, user_id, from_date, to_date, reason, set_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (f"LV_{uuid.uuid4().hex[:10]}", "USR_EMP_A1", start_date, end_date, "Medical Leave", "USR_ADMIN", now_iso),
        )
        conn.commit()

    try:
        # With Coord 1 on leave, Coordinator 2 should take over
        active_coord_during_leave = auth_service.get_active_coordinator_for_department("DEPT_HOSTEL_ELECTRICAL")
        assert active_coord_during_leave is not None
        assert active_coord_during_leave.user_id == "USR_EMP_A2", "Coordinator 2 must take over when Coordinator 1 is on leave"
    finally:
        # Clean up temporary leave record
        with auth_service._connect() as conn:
            conn.execute("DELETE FROM user_leaves WHERE user_id = ?", ("USR_EMP_A1",))
            conn.commit()


def test_scenario_12_coordinator_assignment_validation_rules(admin_hdr):
    """
    Scenario 12:
    Verify that invalid coordinator assignments are strictly rejected:
    1. The same employee cannot be assigned as both Coordinator 1 and Coordinator 2 in the same department.
    2. A non-employee (e.g. Student) cannot be assigned as a coordinator.
    """
    # 1. Attempt to assign same employee as both C1 and C2 in DEPT_HOSTEL_PLUMBING
    res = client.put(
        "/departments/DEPT_HOSTEL_PLUMBING/coordinators",
        json={
            "coordinator_1_id": "USR_EMP_A1",
            "coordinator_2_id": "USR_EMP_A1",
        },
        headers=admin_hdr,
    )
    assert res.status_code == 400
    assert "cannot be the same employee" in res.json().get("detail", "")

    # 2. Attempt to assign a non-employee (Student) as Coordinator 1
    res = client.put(
        "/departments/DEPT_HOSTEL_PLUMBING/coordinators",
        json={
            "coordinator_1_id": "USR_STUDENT",
            "coordinator_2_id": "USR_EMP_B2",
        },
        headers=admin_hdr,
    )
    assert res.status_code == 400
    assert "must be an active employee" in res.json().get("detail", "")


def test_scenario_13_employee_eligible_for_multiple_departments_and_locations(admin_hdr):
    """
    Scenario 13:
    Verify an employee eligible for multiple departments and locations can be queried and assigned appropriately.
    """
    # Check eligible employees for Electrical
    res = client.get("/departments/DEPT_HOSTEL_ELECTRICAL/eligible-employees", headers=admin_hdr)
    assert res.status_code == 200
    staff = res.json()
    assert len(staff) >= 3

    # USR_EMP_A3 is eligible for Electrical
    emp_a3 = next((s for s in staff if s["user_id"] == "USR_EMP_A3"), None)
    assert emp_a3 is not None
    assert "LOC_HOSTEL_1" in emp_a3["authorized_locations"]
    assert "active_workload" in emp_a3
    assert emp_a3["is_on_leave"] is False


def test_scenario_14_app_manager_scoped_authorization(app_mgr_hdr, admin_hdr):
    """
    Scenario 14:
    Verify that App Managers cannot edit mappings for locations outside their assigned scope.
    USR_MANAGER is assigned to LOC_HOSTEL_1, not LOC_HOSTEL_2.
    """
    # 1. App Manager attempting to assign departments to LOC_HOSTEL_2 (outside scope) -> 403 Forbidden
    res = client.put(
        "/locations/LOC_HOSTEL_2/departments",
        json={"department_ids": ["DEPT_HOSTEL_ELECTRICAL"]},
        headers=app_mgr_hdr,
    )
    assert res.status_code == 403, f"Expected 403 Forbidden, got {res.status_code}: {res.text}"
    assert "authorized scope" in res.json().get("detail", "").lower()

    # 2. App Manager modifying departments for LOC_HOSTEL_1 (within scope) -> 200 OK
    res = client.put(
        "/locations/LOC_HOSTEL_1/departments",
        json={"department_ids": ["DEPT_HOSTEL_ELECTRICAL", "DEPT_HOSTEL_PLUMBING", "DEPT_HOSTEL_HOUSEKEEPING"]},
        headers=app_mgr_hdr,
    )
    assert res.status_code == 200
    assigned_depts = res.json().get("department_ids", [])
    assert "DEPT_HOSTEL_ELECTRICAL" in assigned_depts


def test_scenario_15_department_name_duplicates_rejected(admin_hdr):
    """
    Scenario 15:
    Verify that department name duplicates (including case and whitespace differences) are rejected.
    """
    # Existing department: "Electrical"
    # Attempt exact match
    res = client.post(
        "/departments",
        json={"name": "Electrical", "sla_days": 3, "complaint_types": ["Test"]},
        headers=admin_hdr,
    )
    assert res.status_code in [400, 409], f"Expected 400/409, got {res.status_code}"

    # Attempt case variation: "electrical"
    res = client.post(
        "/departments",
        json={"name": "electrical", "sla_days": 3, "complaint_types": ["Test"]},
        headers=admin_hdr,
    )
    assert res.status_code in [400, 409]
    assert "already exists" in res.json().get("detail", "").lower()

    # Attempt whitespace variation: "   ELECTRICAL   "
    res = client.post(
        "/departments",
        json={"name": "   ELECTRICAL   ", "sla_days": 3, "complaint_types": ["Test"]},
        headers=admin_hdr,
    )
    assert res.status_code in [400, 409]
    assert "already exists" in res.json().get("detail", "").lower()
