"""
Comprehensive Automated Test Suite for Multi-Department Coordinators & Employee Responsibilities
Covers all 16 scenarios specified in Campus Pulse Section 8.
"""

import pytest
import sqlite3
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from api.main import app

import os

def get_db_connection():
    db_path = "storage/campus_pulse.db"
    if not os.path.exists(db_path):
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage", "campus_pulse.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

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
def emp_a1_hdr():
    return login("employee.a1@campuspulse.edu", "Employee@123")


@pytest.fixture(scope="module")
def emp_a2_hdr():
    return login("employee.a2@campuspulse.edu", "Employee@123")


@pytest.fixture(scope="module")
def emp_b1_hdr():
    return login("employee.b1@campuspulse.edu", "Employee@123")


@pytest.fixture(scope="module")
def emp_b2_hdr():
    return login("employee.b2@campuspulse.edu", "Employee@123")


@pytest.fixture(scope="module")
def student_hdr():
    return login("gowtham.e23@iiits.in", "Student@123")


@pytest.fixture(scope="module")
def warden_hdr():
    return login("naveen@campus.edu", "Warden@123")



# =========================================================================
# Scenario 1: One employee can coordinate two departments
# =========================================================================
def test_scenario_1_employee_can_coordinate_two_departments(admin_hdr):
    # Assign USR_EMP_A1 as Coord 1 in Electrical and Coord 1 in Plumbing
    res1 = client.put(
        "/departments/DEPT_HOSTEL_ELECTRICAL/coordinators",
        json={"coordinator_1_id": "USR_EMP_A1", "coordinator_2_id": "USR_EMP_A2"},
        headers=admin_hdr,
    )
    assert res1.status_code == 200
    assert res1.json()["coordinator_id"] == "USR_EMP_A1"

    res2 = client.put(
        "/departments/DEPT_HOSTEL_PLUMBING/coordinators",
        json={"coordinator_1_id": "USR_EMP_A1", "coordinator_2_id": "USR_EMP_B1"},
        headers=admin_hdr,
    )
    assert res2.status_code == 200
    assert res2.json()["coordinator_id"] == "USR_EMP_A1"


# =========================================================================
# Scenario 2: One employee can coordinate three or more departments
# =========================================================================
def test_scenario_2_employee_can_coordinate_three_or_more_departments(admin_hdr):
    # Assign USR_EMP_A1 to a third department (DEPT_CAMPUS_FIRE)
    res = client.put(
        "/departments/DEPT_CAMPUS_FIRE/coordinators",
        json={"coordinator_1_id": "USR_EMP_A1", "coordinator_2_id": "USR_EMP_A2"},
        headers=admin_hdr,
    )
    assert res.status_code == 200
    assert res.json()["coordinator_id"] == "USR_EMP_A1"

    # Verify eligible coordinators endpoint lists USR_EMP_A1 with multiple assignments
    res_elig = client.get("/departments/DEPT_HOSTEL_HOUSEKEEPING/eligible-coordinators", headers=admin_hdr)
    assert res_elig.status_code == 200
    emp_a1 = next((e for e in res_elig.json() if e["user_id"] == "USR_EMP_A1"), None)
    assert emp_a1 is not None
    assert emp_a1["is_eligible"] is True
    assert emp_a1.get("assigned_departments_count", 0) >= 2 or len(emp_a1.get("other_positions", [])) >= 2 or len(emp_a1.get("current_assignments", [])) >= 2


    # Clean up third assignment
    client.put(
        "/departments/DEPT_CAMPUS_FIRE/coordinators",
        json={"coordinator_1_id": None, "coordinator_2_id": None},
        headers=admin_hdr,
    )


# =========================================================================
# Scenario 3: One employee can be Coordinator 1 in Dept A and Coordinator 2 in Dept B
# =========================================================================
def test_scenario_3_coord1_in_dept_a_and_coord2_in_dept_b(admin_hdr):
    # USR_EMP_A2: Coordinator 2 in Electrical, Coordinator 1 in Housekeeping
    res1 = client.put(
        "/departments/DEPT_HOSTEL_ELECTRICAL/coordinators",
        json={"coordinator_1_id": "USR_EMP_A1", "coordinator_2_id": "USR_EMP_A2"},
        headers=admin_hdr,
    )
    assert res1.status_code == 200
    assert res1.json()["coordinator_2_id"] == "USR_EMP_A2"

    res2 = client.put(
        "/departments/DEPT_HOSTEL_HOUSEKEEPING/coordinators",
        json={"coordinator_1_id": "USR_EMP_A2", "coordinator_2_id": "USR_EMP_B2"},
        headers=admin_hdr,
    )
    assert res2.status_code == 200
    assert res2.json()["coordinator_id"] == "USR_EMP_A2"
    assert res2.json()["coordinator_2_id"] == "USR_EMP_B2"


# =========================================================================
# Scenario 4: One employee cannot be both Coordinator 1 and Coordinator 2 in the same department
# =========================================================================
def test_scenario_4_cannot_be_both_c1_and_c2_in_same_department(admin_hdr):
    res = client.put(
        "/departments/DEPT_HOSTEL_ELECTRICAL/coordinators",
        json={"coordinator_1_id": "USR_EMP_A1", "coordinator_2_id": "USR_EMP_A1"},
        headers=admin_hdr,
    )
    assert res.status_code == 400
    assert "cannot be the same employee" in res.json()["detail"]


# =========================================================================
# Scenario 5: Four coordinators assigned across six employees without extra users
# =========================================================================
def test_scenario_5_four_coordinators_across_six_employees_no_extra_users(admin_hdr):
    with get_db_connection() as conn:
        users = conn.execute("SELECT user_id, role FROM users WHERE is_deleted = 0 OR is_deleted IS NULL").fetchall()
        assert len(users) == 14, f"Expected 14 user accounts, found {len(users)}"
        employees = [u for u in users if u["role"] == "employee"]
        assert len(employees) == 6, f"Expected 6 employees, found {len(employees)}"
        coord_users = [u for u in users if u["role"] == "coordinator"]
        assert len(coord_users) == 0, "No duplicate coordinator-only accounts should exist"

    # Set up canonical 4 coordinator responsibilities:
    # A1: Electrical C1, Plumbing C1
    # A2: Electrical C2, Housekeeping C1
    # B1: Plumbing C2
    # B2: Network & IT C1, Maintenance C2
    client.put("/departments/DEPT_HOSTEL_ELECTRICAL/coordinators", json={"coordinator_1_id": "USR_EMP_A1", "coordinator_2_id": "USR_EMP_A2"}, headers=admin_hdr)
    client.put("/departments/DEPT_HOSTEL_PLUMBING/coordinators", json={"coordinator_1_id": "USR_EMP_A1", "coordinator_2_id": "USR_EMP_B1"}, headers=admin_hdr)
    client.put("/departments/DEPT_HOSTEL_HOUSEKEEPING/coordinators", json={"coordinator_1_id": "USR_EMP_A2", "coordinator_2_id": "USR_EMP_B2"}, headers=admin_hdr)
    client.put("/departments/DEPT_HOSTEL_NETWORK/coordinators", json={"coordinator_1_id": "USR_EMP_B2", "coordinator_2_id": "USR_EMP_B1"}, headers=admin_hdr)
    client.put("/departments/DEPT_MESS_MAINTENANCE/coordinators", json={"coordinator_1_id": "USR_EMP_B1", "coordinator_2_id": "USR_EMP_B2"}, headers=admin_hdr)

    # Verify user count remains 14
    with get_db_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM users WHERE is_deleted = 0 OR is_deleted IS NULL").fetchone()[0]
        assert count == 14


# =========================================================================
# Scenario 6: A coordinator can also receive and complete eligible employee work
# =========================================================================
def test_scenario_6_coordinator_receives_and_completes_employee_work(student_hdr, admin_hdr, emp_a1_hdr):
    # 1. Student creates a complaint
    c_res = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "Lighting & Electrical",
            "complaint_type": "Tube light flickering",
            "title": "Study Lamp broken",
            "description": "Room 101 desk lamp socket broken",
            "priority": "Medium",
        },
        headers=student_hdr,
    )
    assert c_res.status_code == 201
    cid = c_res.json()["complaint_id"]

    # 2. Coordinator (USR_EMP_A1) is eligible to be assigned as regular worker
    asgn_res = client.post(
        f"/complaints/{cid}/assign",
        json={"assigned_to": "USR_EMP_A1", "reason": "Self-assigned to fix fixture"},
        headers=admin_hdr,
    )
    assert asgn_res.status_code == 200
    assert asgn_res.json()["assigned_to"] == "USR_EMP_A1"

    # 3. Employee A1 starts and resolves work
    st_res = client.post(f"/complaints/{cid}/start-work", headers=emp_a1_hdr)
    assert st_res.status_code == 200

    res_res = client.post(
        f"/complaints/{cid}/resolve",
        json={"notes": "Replaced desk socket", "skip_photo": True, "photo_skip_reason": "Tool repair complete"},
        headers=emp_a1_hdr,
    )
    assert res_res.status_code == 200
    assert res_res.json()["status"] in ("Resolved", "Waiting for Verification")


# =========================================================================
# Scenario 7: An employee on leave cannot receive prohibited assignments
# =========================================================================
def test_scenario_7_employee_on_leave_cannot_receive_prohibited_assignments(admin_hdr, student_hdr):
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

    # Put USR_EMP_A3 on leave
    l_res = client.post(
        "/leaves",
        json={
            "user_id": "USR_EMP_A3",
            "from_date": today,
            "to_date": tomorrow,
            "reason": "Medical leave",
        },
        headers=admin_hdr,
    )
    assert l_res.status_code in (200, 201)

    # Create complaint
    c_res = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "Lighting & Electrical",
            "complaint_type": "Switch replacement",
            "title": "Switch sparking",
            "description": "Switch sparking in hallway",
            "priority": "High",
        },
        headers=student_hdr,
    )
    assert c_res.status_code == 201
    cid = c_res.json()["complaint_id"]

    # Attempt to assign USR_EMP_A3 -> Should be rejected
    asgn_res = client.post(
        f"/complaints/{cid}/assign",
        json={"assigned_to": "USR_EMP_A3", "reason": "Assigned on leave"},
        headers=admin_hdr,
    )
    assert asgn_res.status_code in (400, 409)
    assert "leave" in asgn_res.json()["detail"].lower()

    # Clean up leave
    client.delete(f"/leaves/{l_res.json()['leave_id']}", headers=admin_hdr)


# =========================================================================
# Scenario 8: Backup coordinator takes over when Coordinator 1 is unavailable
# =========================================================================
def test_scenario_8_backup_coordinator_takeover_when_c1_unavailable(admin_hdr):
    from api.dependencies import get_auth_service, get_team_service
    auth_svc = get_auth_service()
    team_svc = get_team_service()

    # Ensure DEPT_HOSTEL_ELECTRICAL has C1=USR_EMP_A1, C2=USR_EMP_A2
    client.put(
        "/departments/DEPT_HOSTEL_ELECTRICAL/coordinators",
        json={"coordinator_1_id": "USR_EMP_A1", "coordinator_2_id": "USR_EMP_A2"},
        headers=admin_hdr,
    )

    # Put C1 (USR_EMP_A1) on leave
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    l_res = client.post(
        "/leaves",
        json={"user_id": "USR_EMP_A1", "from_date": today, "to_date": tomorrow, "reason": "Emergency leave"},
        headers=admin_hdr,
    )
    assert l_res.status_code in (200, 201)
    leave_id = l_res.json()["leave_id"]

    try:
        # Active coordinator for Electrical should now be C2 (USR_EMP_A2)
        active_coord = auth_svc.get_active_coordinator_for_department("DEPT_HOSTEL_ELECTRICAL")
        assert active_coord is not None
        assert active_coord.user_id == "USR_EMP_A2"
    finally:
        # Clean up leave
        client.delete(f"/leaves/{leave_id}", headers=admin_hdr)

    # Active coordinator returns to C1
    active_coord_restored = auth_svc.get_active_coordinator_for_department("DEPT_HOSTEL_ELECTRICAL")
    assert active_coord_restored.user_id == "USR_EMP_A1"


# =========================================================================
# Scenario 9: Leave in one department does not disable other department responsibilities
# =========================================================================
def test_scenario_9_leave_in_one_dept_does_not_disable_other_dept_responsibilities(admin_hdr):
    from api.dependencies import get_auth_service, get_team_service
    auth_svc = get_auth_service()
    team_svc = get_team_service()

    # USR_EMP_A1 coordinates Electrical (C1) and Plumbing (C1)
    client.put("/departments/DEPT_HOSTEL_ELECTRICAL/coordinators", json={"coordinator_1_id": "USR_EMP_A1", "coordinator_2_id": "USR_EMP_A2"}, headers=admin_hdr)
    client.put("/departments/DEPT_HOSTEL_PLUMBING/coordinators", json={"coordinator_1_id": "USR_EMP_A1", "coordinator_2_id": "USR_EMP_B1"}, headers=admin_hdr)

    # Put USR_EMP_A1 on leave specifically in Electrical
    today = datetime.now().strftime("%Y-%m-%d")
    tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    l_res = client.post(
        "/leaves",
        json={
            "user_id": "USR_EMP_A1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "from_date": today,
            "to_date": tomorrow,
            "reason": "Training in electrical systems",
        },
        headers=admin_hdr,
    )
    assert l_res.status_code in (200, 201)
    leave_id = l_res.json()["leave_id"]

    try:
        # USR_EMP_A1 is on leave for Electrical
        assert team_svc.is_user_on_leave("USR_EMP_A1", department_id="DEPT_HOSTEL_ELECTRICAL") is True
        # USR_EMP_A1 is NOT on leave for Plumbing
        assert team_svc.is_user_on_leave("USR_EMP_A1", department_id="DEPT_HOSTEL_PLUMBING") is False

        # In Electrical, active coordinator falls back to C2 (USR_EMP_A2)
        active_elec = auth_svc.get_active_coordinator_for_department("DEPT_HOSTEL_ELECTRICAL")
        assert active_elec.user_id == "USR_EMP_A2"

        # In Plumbing, active coordinator remains C1 (USR_EMP_A1)
        active_plumb = auth_svc.get_active_coordinator_for_department("DEPT_HOSTEL_PLUMBING")
        assert active_plumb.user_id == "USR_EMP_A1"
    finally:
        # Clean up leave
        client.delete(f"/leaves/{leave_id}", headers=admin_hdr)


# =========================================================================
# Scenario 10: Department coordinators retain campus-wide responsibility
# =========================================================================
def test_scenario_10_department_coordinators_retain_campus_wide_responsibility(student_hdr, emp_a1_hdr):
    # USR_EMP_A1 coordinates Electrical campus-wide
    # Create complaints in two distinct locations: LOC_HOSTEL_1 and LOC_ACADEMIC_1
    c1 = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "Lighting & Electrical",
            "complaint_type": "Campus-wide test 1",
            "title": "Hostel 1 Light",
            "description": "Corridor light off",
            "priority": "Low",
        },
        headers=student_hdr,
    ).json()

    c2 = client.post(
        "/complaints",
        json={
            "location_id": "LOC_ACADEMIC_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "Lighting & Electrical",
            "complaint_type": "Campus-wide test 2",
            "title": "Academic Lab Light",
            "description": "Lab ceiling light off",
            "priority": "Low",
        },
        headers=student_hdr,
    ).json()

    # Coordinator A1 lists complaints: both complaints must be visible
    emp_list = client.get("/complaints", headers=emp_a1_hdr)
    assert emp_list.status_code == 200
    visible_ids = {c["complaint_id"] for c in emp_list.json()}
    assert c1["complaint_id"] in visible_ids, "Coordinator should see Hostel 1 Electrical complaints"
    assert c2["complaint_id"] in visible_ids, "Coordinator should see Academic Block 1 Electrical complaints"


# =========================================================================
# Scenario 11: Valid cross-department complaint reroute
# =========================================================================
def test_scenario_11_cross_department_complaint_reroute(student_hdr, admin_hdr, emp_a1_hdr):
    # Create complaint in Electrical
    c_res = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "Lighting & Electrical",
            "complaint_type": "Water leak on wiring",
            "title": "Water leaking on conduit",
            "description": "Pipe leaking above breaker box",
            "priority": "High",
        },
        headers=student_hdr,
    )
    assert c_res.status_code == 201
    cid = c_res.json()["complaint_id"]

    # Coordinator A1 reroutes from Electrical to Plumbing
    reroute_res = client.post(
        f"/complaints/{cid}/reroute",
        json={"destination_department_id": "DEPT_HOSTEL_PLUMBING", "reason": "Origin is a plumbing pipe leak"},
        headers=emp_a1_hdr,
    )
    assert reroute_res.status_code == 200
    updated = reroute_res.json()
    assert updated["department_id"] == "DEPT_HOSTEL_PLUMBING"
    assert updated["department_name"] == "Plumbing"

    # Verify history logs source, destination, actor, and reason
    hist = updated.get("history", [])
    assert any("rerouted from Electrical to Plumbing" in (h.get("message", "") if isinstance(h, dict) else str(h)) for h in hist)
    assert any("Origin is a plumbing pipe leak" in (h.get("message", "") if isinstance(h, dict) else str(h)) for h in hist)


# =========================================================================
# Scenario 12: Unauthorized users cannot modify coordinator assignments
# =========================================================================
def test_scenario_12_unauthorized_users_cannot_modify_coordinators(student_hdr, warden_hdr):
    # Student cannot modify coordinators
    res1 = client.put(
        "/departments/DEPT_HOSTEL_ELECTRICAL/coordinators",
        json={"coordinator_1_id": "USR_STUDENT", "coordinator_2_id": "USR_STUDENT"},
        headers=student_hdr,
    )
    assert res1.status_code == 403

    # Warden cannot modify coordinators
    res2 = client.put(
        "/departments/DEPT_HOSTEL_ELECTRICAL/coordinators",
        json={"coordinator_1_id": "USR_WARDEN", "coordinator_2_id": "USR_WARDEN"},
        headers=warden_hdr,
    )
    assert res2.status_code == 403


# =========================================================================
# Scenario 13: Duplicate or conflicting coordinator assignments are rejected
# =========================================================================
def test_scenario_13_conflicting_coordinator_assignments_rejected(admin_hdr):
    # 1. Non-existent user
    res1 = client.put(
        "/departments/DEPT_HOSTEL_ELECTRICAL/coordinators",
        json={"coordinator_1_id": "NON_EXISTENT_USER", "coordinator_2_id": None},
        headers=admin_hdr,
    )
    assert res1.status_code == 400

    # 2. Assigning non-employee (e.g. Student) as coordinator
    res2 = client.put(
        "/departments/DEPT_HOSTEL_ELECTRICAL/coordinators",
        json={"coordinator_1_id": "USR_STUDENT", "coordinator_2_id": None},
        headers=admin_hdr,
    )
    assert res2.status_code == 400

    # 3. Same employee as both C1 and C2 in same department
    res3 = client.put(
        "/departments/DEPT_HOSTEL_ELECTRICAL/coordinators",
        json={"coordinator_1_id": "USR_EMP_A1", "coordinator_2_id": "USR_EMP_A1"},
        headers=admin_hdr,
    )
    assert res3.status_code == 400


# =========================================================================
# Scenario 14: Complaint history, relationships, and notifications continue to work
# =========================================================================
def test_scenario_14_complaint_history_relationships_notifications_preserved(student_hdr, emp_a1_hdr, emp_b1_hdr):
    c_res = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "Lighting & Electrical",
            "complaint_type": "Audit check",
            "title": "History test ticket",
            "description": "Testing audit and notifications",
            "priority": "Medium",
        },
        headers=student_hdr,
    )
    assert c_res.status_code == 201
    complaint = c_res.json()
    cid = complaint["complaint_id"]
    assert len(complaint.get("history", [])) >= 1

    # Reroute complaint to Plumbing where USR_EMP_B1 is coordinator
    reroute_res = client.post(
        f"/complaints/{cid}/reroute",
        json={"destination_department_id": "DEPT_HOSTEL_PLUMBING", "reason": "Reroute notification audit test"},
        headers=emp_a1_hdr,
    )
    assert reroute_res.status_code == 200

    # Coordinator B1 receives notification for rerouted complaint
    notifs = client.get("/notifications", headers=emp_b1_hdr).json()
    assert any(n.get("reference_id") == cid or cid in str(n) for n in notifs)


# =========================================================================
# Scenario 15: No duplicate employee accounts or coordinator-only users
# =========================================================================
def test_scenario_15_no_duplicate_employee_or_coordinator_accounts():
    with get_db_connection() as conn:
        users = conn.execute("SELECT user_id, role, email FROM users WHERE is_deleted = 0 OR is_deleted IS NULL").fetchall()
        assert len(users) == 14, f"Found {len(users)} users, expected exactly 14"

        roles = [u["role"] for u in users]
        assert roles.count("super_admin") == 1
        assert roles.count("administrator") == 1
        assert roles.count("app_manager") == 2
        assert roles.count("employee") == 6
        assert roles.count("student") == 2
        assert roles.count("location_in_charge") == 2
        assert "coordinator" not in roles, "No coordinator-only user accounts allowed"


# =========================================================================
# Scenario 16: Existing RBAC and location restrictions remain enforced
# =========================================================================
def test_scenario_16_rbac_and_location_restrictions_enforced(student_hdr, warden_hdr):
    # Student cannot view private complaints of other students
    student2_hdr = login("student2@campus.edu", "Student@123")
    c_res = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "Lighting & Electrical",
            "complaint_type": "Confidential item",
            "title": "Student 1 Private Ticket",
            "description": "Room 101 personal issue",
            "priority": "Low",
            "visibility_type": "Private",
        },
        headers=student_hdr,
    )
    assert c_res.status_code == 201
    cid = c_res.json()["complaint_id"]

    # Student 2 cannot access it
    s2_view = client.get(f"/complaints/{cid}", headers=student2_hdr)
    assert s2_view.status_code == 403

    # Warden 1 (Hostel 1 in charge) can view complaints in Hostel 1
    w1_view = client.get(f"/complaints/{cid}", headers=warden_hdr)
    assert w1_view.status_code == 200

    # Warden 2 (Hostel 2 in charge) cannot access complaints in Hostel 1
    warden2_hdr = login("warden2@campus.edu", "Warden@123")
    w2_view = client.get(f"/complaints/{cid}", headers=warden2_hdr)
    assert w2_view.status_code == 403
