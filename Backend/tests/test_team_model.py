import os
import sys
import uuid
import pytest
from datetime import datetime, date, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import (
    get_auth_service,
    get_team_service,
    get_complaint_service,
    get_notification_service,
)
from core.constants import (
    ROLE_ADMINISTRATOR,
    ROLE_APP_MANAGER,
    ROLE_COORDINATOR,
    ROLE_EMPLOYEE,
    ROLE_LOCATION_IN_CHARGE,
    ROLE_STUDENT,
    STATUS_SUBMITTED,
    STATUS_ASSIGNED,
    STATUS_IN_PROGRESS,
    STATUS_WAITING_VERIFICATION,
)

client = TestClient(app)


def _login(email, password="Temp@Pass123"):
    res = client.post("/auth/login", json={"username": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def services():
    return {
        "auth": get_auth_service(),
        "team": get_team_service(),
        "complaint": get_complaint_service(),
        "notification": get_notification_service(),
    }


def _create_user(auth, role, prefix):
    uid = uuid.uuid4().hex[:6]
    email = f"{prefix}_{uid}@testpulse.local"
    u = auth.create_user(
        name=f"User {prefix}_{uid}",
        email=email,
        password="Temp@Pass123",
        role=role,
    )
    u.must_change_password = False
    u.first_login = False
    auth.save_user(u)
    headers = _login(email)
    return u, headers


def _create_loc(auth, prefix, in_charge_id=None):
    uid = uuid.uuid4().hex[:6]
    loc = auth.create_location(f"Location {prefix} {uid}")
    if in_charge_id:
        loc.in_charge_id = in_charge_id
        auth.save_location(loc)
    return loc


def _create_dept(auth, prefix):
    uid = uuid.uuid4().hex[:6]
    return auth.create_department(f"Dept {prefix} {uid}", sla_days=2)


def test_l1_complaint_filed_with_team_mapped(services):
    """L1: Complaint filed with team mapped: status Submitted, assigned_to empty, awaiting_assign_since set, acting coordinator notified."""
    auth = services["auth"]
    team_svc = services["team"]

    # 1. Setup users
    coord, coord_headers = _create_user(auth, ROLE_COORDINATOR, "l1_coord")
    emp, _ = _create_user(auth, ROLE_EMPLOYEE, "l1_emp")
    student, std_headers = _create_user(auth, ROLE_STUDENT, "l1_stu")

    # 2. Setup team
    loc = _create_loc(auth, "L1")
    dept = _create_dept(auth, "L1")

    team = team_svc.create_team(
        name=f"Team L1 {loc.location_id}",
        department_id=dept.department_id,
        coordinator_id=coord.user_id,
        location_ids=[loc.location_id],
        member_ids=[coord.user_id, emp.user_id],
    )

    # 3. File complaint
    c_res = client.post("/complaints", json={
        "location_id": loc.location_id,
        "department_id": dept.department_id,
        "category": "electrical",
        "title": "L1 Test Complaint",
        "description": "Flickering lamp in study hall",
        "visibility_type": "Private",
        "priority": "Medium",
    }, headers=std_headers)
    assert c_res.status_code == 201, c_res.text
    c_data = c_res.json()
    cid = c_data["complaint_id"]

    # Assert status Submitted, assigned_to empty, awaiting_assign_since set
    assert c_data["status"] == STATUS_SUBMITTED
    assert not c_data.get("assigned_to")
    assert c_data.get("awaiting_assign_since") is not None
    assert c_data.get("team_id") == team["team_id"]

    # Assert acting coordinator notified
    with team_svc._connect() as conn:
        notif = conn.execute(
            "SELECT * FROM notifications WHERE receiver_id = ? AND reference_id = ?",
            (coord.user_id, cid),
        ).fetchone()
        assert notif is not None
        assert "Awaiting Assignment" in dict(notif)["title"] or "New Complaint" in dict(notif)["title"]


def test_l2_complaint_filed_with_no_team_mapped(services):
    """L2: Complaint filed with no team mapped: status Submitted, assigned_to empty, alerts warden, App Manager, Admin."""
    auth = services["auth"]
    team_svc = services["team"]

    # 1. Setup location and department with NO team
    warden, _ = _create_user(auth, ROLE_LOCATION_IN_CHARGE, "l2_warden")
    loc = _create_loc(auth, "L2", in_charge_id=warden.user_id)
    dept = _create_dept(auth, "L2")

    student, std_headers = _create_user(auth, ROLE_STUDENT, "l2_stu")

    # 2. File complaint
    c_res = client.post("/complaints", json={
        "location_id": loc.location_id,
        "department_id": dept.department_id,
        "category": "carpentry",
        "title": "L2 No Team Complaint",
        "description": "Broken window hinge",
        "visibility_type": "Private",
        "priority": "High",
    }, headers=std_headers)
    assert c_res.status_code == 201
    c_data = c_res.json()
    cid = c_data["complaint_id"]

    assert c_data["status"] == STATUS_SUBMITTED
    assert not c_data.get("assigned_to")

    # Assert notifications to warden, app manager, and admin
    with team_svc._connect() as conn:
        notif_warden = conn.execute(
            "SELECT * FROM notifications WHERE receiver_id = ? AND reference_id = ?",
            (warden.user_id, cid),
        ).fetchone()
        assert notif_warden is not None
        assert "Unrouted Complaint" in dict(notif_warden)["title"] or "Unassigned Complaint" in dict(notif_warden)["title"] or "Coverage Gap" in dict(notif_warden)["title"]

        notif_admin = conn.execute(
            "SELECT * FROM notifications WHERE receiver_id = 'USR_ADMIN' AND reference_id = ?",
            (cid,),
        ).fetchone()
        assert notif_admin is not None


def test_l3_coordinator_assigns_to_employee(services):
    """L3: Coordinator assigns to employee: status Assigned, awaiting_assign_since cleared, worker notified, student notified."""
    auth = services["auth"]
    team_svc = services["team"]

    coord, coord_headers = _create_user(auth, ROLE_COORDINATOR, "l3_coord")
    emp, emp_headers = _create_user(auth, ROLE_EMPLOYEE, "l3_emp")
    student, std_headers = _create_user(auth, ROLE_STUDENT, "l3_stu")

    loc = _create_loc(auth, "L3")
    dept = _create_dept(auth, "L3")

    team = team_svc.create_team(
        name=f"Team L3 {loc.location_id}",
        department_id=dept.department_id,
        coordinator_id=coord.user_id,
        location_ids=[loc.location_id],
        member_ids=[coord.user_id, emp.user_id],
    )

    c_res = client.post("/complaints", json={
        "location_id": loc.location_id,
        "department_id": dept.department_id,
        "category": "electrical",
        "title": "L3 Assign Test",
        "description": "Corridor light switch broken",
        "visibility_type": "Private",
    }, headers=std_headers)
    cid = c_res.json()["complaint_id"]

    # Assign to employee
    assign_res = client.post(f"/complaints/{cid}/assign", json={
        "assigned_to": emp.user_id
    }, headers=coord_headers)
    assert assign_res.status_code == 200, assign_res.text
    a_data = assign_res.json()

    assert a_data["status"] == STATUS_ASSIGNED
    assert a_data["assigned_to"] == emp.user_id
    assert a_data.get("awaiting_assign_since") is None

    # Verify notifications to worker and student
    with team_svc._connect() as conn:
        notif_emp = conn.execute(
            "SELECT * FROM notifications WHERE receiver_id = ? AND reference_id = ?",
            (emp.user_id, cid),
        ).fetchone()
        assert notif_emp is not None
        assert "New Job" in dict(notif_emp)["title"]

        notif_stu = conn.execute(
            "SELECT * FROM notifications WHERE receiver_id = ? AND reference_id = ? ORDER BY created_at DESC",
            (student.user_id, cid),
        ).fetchone()
        assert notif_stu is not None
        assert "Complaint Assigned" in dict(notif_stu)["title"]


def test_l4_race_two_coordinators_assign(services):
    """L4: Race: two coordinators try to assign the same complaint at the same time: one gets 200, one gets 409 Conflict with 'Already assigned by <name>'."""
    auth = services["auth"]
    team_svc = services["team"]

    coord, coord_headers = _create_user(auth, ROLE_COORDINATOR, "l4_coord")
    emp, _ = _create_user(auth, ROLE_EMPLOYEE, "l4_emp")
    student, std_headers = _create_user(auth, ROLE_STUDENT, "l4_stu")
    admin_headers = _login("admin@example.com", "Admin@123")

    loc = _create_loc(auth, "L4")
    dept = _create_dept(auth, "L4")

    team = team_svc.create_team(
        name=f"Team L4 {loc.location_id}",
        department_id=dept.department_id,
        coordinator_id=coord.user_id,
        location_ids=[loc.location_id],
        member_ids=[coord.user_id, emp.user_id],
    )

    c_res = client.post("/complaints", json={
        "location_id": loc.location_id,
        "department_id": dept.department_id,
        "category": "electrical",
        "title": "L4 Race Test",
        "description": "Testing atomic assign conflict",
        "visibility_type": "Private",
    }, headers=std_headers)
    cid = c_res.json()["complaint_id"]

    # First coordinator assigns
    res1 = client.post(f"/complaints/{cid}/assign", json={
        "assigned_to": emp.user_id
    }, headers=coord_headers)
    assert res1.status_code == 200

    # Second caller tries initial assign without reason -> 409 Conflict
    res2 = client.post(f"/complaints/{cid}/assign", json={
        "assigned_to": coord.user_id
    }, headers=admin_headers)
    assert res2.status_code == 409
    assert "already assigned" in res2.json()["detail"].lower()


def test_l5_assign_to_member_on_leave(services):
    """L5: Assign to member on leave: returns 400 with 'User is on leave until <date>'."""
    auth = services["auth"]
    team_svc = services["team"]

    coord, coord_headers = _create_user(auth, ROLE_COORDINATOR, "l5_coord")
    emp, _ = _create_user(auth, ROLE_EMPLOYEE, "l5_emp")
    student, std_headers = _create_user(auth, ROLE_STUDENT, "l5_stu")

    loc = _create_loc(auth, "L5")
    dept = _create_dept(auth, "L5")

    team = team_svc.create_team(
        name=f"Team L5 {loc.location_id}",
        department_id=dept.department_id,
        coordinator_id=coord.user_id,
        location_ids=[loc.location_id],
        member_ids=[coord.user_id, emp.user_id],
    )

    # Set employee on leave today until next week
    today = date.today().isoformat()
    until_date = (date.today() + timedelta(days=7)).isoformat()
    team_svc.set_leave(emp.user_id, today, until_date, "Medical Leave", set_by=coord.user_id)

    c_res = client.post("/complaints", json={
        "location_id": loc.location_id,
        "department_id": dept.department_id,
        "category": "electrical",
        "title": "L5 Leave Test",
        "description": "Cannot assign to worker on leave",
        "visibility_type": "Private",
    }, headers=std_headers)
    cid = c_res.json()["complaint_id"]

    # Assign attempt must fail with 400
    assign_res = client.post(f"/complaints/{cid}/assign", json={
        "assigned_to": emp.user_id
    }, headers=coord_headers)
    assert assign_res.status_code == 400
    assert "user is on leave until" in assign_res.json()["detail"].lower()
    assert until_date in assign_res.json()["detail"]


def test_l6_reassign_requires_reason(services):
    """L6: Reassign requires reason: reassign without reason returns 400; with reason succeeds, previous assignee notified, new assignee notified, history logged."""
    auth = services["auth"]
    team_svc = services["team"]

    coord, coord_headers = _create_user(auth, ROLE_COORDINATOR, "l6_coord")
    emp1, _ = _create_user(auth, ROLE_EMPLOYEE, "l6_emp1")
    emp2, _ = _create_user(auth, ROLE_EMPLOYEE, "l6_emp2")
    student, std_headers = _create_user(auth, ROLE_STUDENT, "l6_stu")

    loc = _create_loc(auth, "L6")
    dept = _create_dept(auth, "L6")

    team = team_svc.create_team(
        name=f"Team L6 {loc.location_id}",
        department_id=dept.department_id,
        coordinator_id=coord.user_id,
        location_ids=[loc.location_id],
        member_ids=[coord.user_id, emp1.user_id, emp2.user_id],
    )

    c_res = client.post("/complaints", json={
        "location_id": loc.location_id,
        "department_id": dept.department_id,
        "category": "electrical",
        "title": "L6 Reassign Test",
        "description": "Reassigning complaint",
        "visibility_type": "Private",
    }, headers=std_headers)
    cid = c_res.json()["complaint_id"]

    # Assign to emp1 first
    res1 = client.post(f"/complaints/{cid}/assign", json={
        "assigned_to": emp1.user_id
    }, headers=coord_headers)
    assert res1.status_code == 200

    # Reassign to emp2 WITHOUT reason -> 400 Bad Request
    re_fail = client.post(f"/complaints/{cid}/assign", json={
        "assigned_to": emp2.user_id,
        "reason": "",
    }, headers=coord_headers)
    assert re_fail.status_code == 400
    assert "mandatory reason" in re_fail.json()["detail"].lower()

    # Reassign to emp2 WITH reason -> 200 OK
    re_ok = client.post(f"/complaints/{cid}/assign", json={
        "assigned_to": emp2.user_id,
        "reason": "Emp1 called for urgent campus substation inspection",
    }, headers=coord_headers)
    assert re_ok.status_code == 200
    data = re_ok.json()
    assert data["assigned_to"] == emp2.user_id

    # Verify history contains reason
    assert any("Emp1 called for urgent" in h["message"] for h in data["history"])

    # Verify notifications to previous assignee and new assignee
    with team_svc._connect() as conn:
        notif_old = conn.execute(
            "SELECT * FROM notifications WHERE receiver_id = ? AND reference_id = ? AND title LIKE '%Reassigned%'",
            (emp1.user_id, cid),
        ).fetchone()
        assert notif_old is not None

        notif_new = conn.execute(
            "SELECT * FROM notifications WHERE receiver_id = ? AND reference_id = ? AND title LIKE '%New Job%'",
            (emp2.user_id, cid),
        ).fetchone()
        assert notif_new is not None


def test_l7_employee_on_leave_flags(services):
    """L7: Employee marks himself on leave: open complaints get assignee_on_leave_flag = 1; cancelling leave clears it."""
    auth = services["auth"]
    team_svc = services["team"]

    coord, coord_headers = _create_user(auth, ROLE_COORDINATOR, "l7_coord")
    emp, emp_headers = _create_user(auth, ROLE_EMPLOYEE, "l7_emp")
    student, std_headers = _create_user(auth, ROLE_STUDENT, "l7_stu")

    loc = _create_loc(auth, "L7")
    dept = _create_dept(auth, "L7")

    team = team_svc.create_team(
        name=f"Team L7 {loc.location_id}",
        department_id=dept.department_id,
        coordinator_id=coord.user_id,
        location_ids=[loc.location_id],
        member_ids=[coord.user_id, emp.user_id],
    )

    c_res = client.post("/complaints", json={
        "location_id": loc.location_id,
        "department_id": dept.department_id,
        "category": "electrical",
        "title": "L7 Leave Flag Test",
        "description": "Testing leave flags",
        "visibility_type": "Private",
    }, headers=std_headers)
    cid = c_res.json()["complaint_id"]

    client.post(f"/complaints/{cid}/assign", json={"assigned_to": emp.user_id}, headers=coord_headers)

    # Employee marks himself on leave via API
    today = date.today().isoformat()
    until_date = (date.today() + timedelta(days=5)).isoformat()
    leave_res = client.post("/leaves", json={
        "from_date": today,
        "to_date": until_date,
        "reason": "Family emergency",
    }, headers=emp_headers)
    assert leave_res.status_code in (200, 201), leave_res.text
    leave_id = leave_res.json()["leave_id"]

    # Verify open complaint now has assignee_on_leave_flag = 1
    with team_svc._connect() as conn:
        row = conn.execute("SELECT assignee_on_leave_flag FROM complaints WHERE complaint_id = ?", (cid,)).fetchone()
        assert row is not None
        assert row[0] == 1

    # Employee cancels leave
    del_res = client.delete(f"/leaves/{leave_id}", headers=emp_headers)
    assert del_res.status_code == 200

    # Verify assignee_on_leave_flag cleared to 0
    with team_svc._connect() as conn:
        row2 = conn.execute("SELECT assignee_on_leave_flag FROM complaints WHERE complaint_id = ?", (cid,)).fetchone()
        assert row2[0] == 0


def test_l8_coordinator_on_leave_backup(services):
    """L8: Coordinator marks himself on leave: backup becomes acting coordinator; open unassigned complaints show for backup; if backup is also on leave, complaint escalates to Level 2."""
    auth = services["auth"]
    team_svc = services["team"]

    coord, coord_headers = _create_user(auth, ROLE_COORDINATOR, "l8_coord")
    backup, backup_headers = _create_user(auth, ROLE_EMPLOYEE, "l8_backup")
    emp, _ = _create_user(auth, ROLE_EMPLOYEE, "l8_emp")
    student, std_headers = _create_user(auth, ROLE_STUDENT, "l8_stu")

    warden, _ = _create_user(auth, ROLE_LOCATION_IN_CHARGE, "l8_warden")
    loc = _create_loc(auth, "L8", in_charge_id=warden.user_id)
    dept = _create_dept(auth, "L8")

    team = team_svc.create_team(
        name=f"Team L8 {loc.location_id}",
        department_id=dept.department_id,
        coordinator_id=coord.user_id,
        backup_coordinator_id=backup.user_id,
        location_ids=[loc.location_id],
        member_ids=[coord.user_id, backup.user_id, emp.user_id],
    )

    # 1. Primary coordinator on leave -> backup is acting coordinator
    today = date.today().isoformat()
    team_svc.set_leave(coord.user_id, today, today, "Doctor appointment")

    acting = team_svc.get_acting_coordinator(team)
    assert acting is not None
    assert acting.user_id == backup.user_id

    # 2. File complaint: acting coordinator is backup, backup is notified
    c_res = client.post("/complaints", json={
        "location_id": loc.location_id,
        "department_id": dept.department_id,
        "category": "electrical",
        "title": "L8 Acting Coordinator Complaint",
        "description": "Backup acting test",
        "visibility_type": "Private",
    }, headers=std_headers)
    cid = c_res.json()["complaint_id"]

    with team_svc._connect() as conn:
        notif_backup = conn.execute(
            "SELECT * FROM notifications WHERE receiver_id = ? AND reference_id = ?",
            (backup.user_id, cid),
        ).fetchone()
        assert notif_backup is not None

    # Backup coordinator can assign
    assign_res = client.post(f"/complaints/{cid}/assign", json={
        "assigned_to": emp.user_id
    }, headers=backup_headers)
    assert assign_res.status_code == 200

    # 3. If backup is ALSO on leave: acting coordinator is None -> escalates to Level 2
    team_svc.set_leave(backup.user_id, today, today, "Vacation")
    acting_none = team_svc.get_acting_coordinator(team)
    assert acting_none is None

    # File another complaint while both on leave
    c2_res = client.post("/complaints", json={
        "location_id": loc.location_id,
        "department_id": dept.department_id,
        "category": "electrical",
        "title": "L8 Both on Leave Complaint",
        "description": "Both leaders on leave",
        "visibility_type": "Private",
    }, headers=std_headers)
    c2_id = c2_res.json()["complaint_id"]

    # Verify escalated to Level 2
    with team_svc._connect() as conn:
        c_row = conn.execute("SELECT assign_escalation_level FROM complaints WHERE complaint_id = ?", (c2_id,)).fetchone()
        assert c_row[0] == 2

        # Warden notified of Level 2 escalation
        notif_w = conn.execute(
            "SELECT * FROM notifications WHERE receiver_id = ? AND reference_id = ?",
            (warden.user_id, c2_id),
        ).fetchone()
        assert notif_w is not None


def test_l9_assign_deadline_escalation(services):
    """L9: Assign deadline passes:
    - Level 1: backup coordinator can now assign (and is notified)
    - Level 2: warden and App Manager can assign (and are notified)
    - Complaint is NEVER auto-assigned.
    """
    auth = services["auth"]
    team_svc = services["team"]
    complaint_svc = services["complaint"]

    coord, coord_headers = _create_user(auth, ROLE_COORDINATOR, "l9_coord")
    backup, backup_headers = _create_user(auth, ROLE_EMPLOYEE, "l9_backup")
    emp, _ = _create_user(auth, ROLE_EMPLOYEE, "l9_emp")
    student, std_headers = _create_user(auth, ROLE_STUDENT, "l9_stu")
    warden, warden_headers = _create_user(auth, ROLE_LOCATION_IN_CHARGE, "l9_warden")

    loc = _create_loc(auth, "L9", in_charge_id=warden.user_id)
    dept = _create_dept(auth, "L9")

    team = team_svc.create_team(
        name=f"Team L9 {loc.location_id}",
        department_id=dept.department_id,
        coordinator_id=coord.user_id,
        backup_coordinator_id=backup.user_id,
        location_ids=[loc.location_id],
        member_ids=[coord.user_id, backup.user_id, emp.user_id],
    )

    c_res = client.post("/complaints", json={
        "location_id": loc.location_id,
        "department_id": dept.department_id,
        "category": "electrical",
        "title": "L9 Escalation Test",
        "description": "Testing assign deadline escalation levels",
        "visibility_type": "Private",
        "priority": "Critical",
    }, headers=std_headers)
    cid = c_res.json()["complaint_id"]

    # 1. Fast forward awaiting_assign_since past 1x deadline (35 mins ago for Critical)
    past_time_l1 = (datetime.now() - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S")
    with team_svc._connect() as conn:
        conn.execute("UPDATE complaints SET awaiting_assign_since = ? WHERE complaint_id = ?", (past_time_l1, cid))

    complaint_svc.apply_automatic_rules()

    comp_l1 = complaint_svc.get_complaint(cid)
    assert comp_l1.assign_escalation_level == 1
    assert not comp_l1.assigned_to  # NEVER auto-assigned!

    # Backup coordinator can now assign at Level 1
    with team_svc._connect() as conn:
        notif_b = conn.execute(
            "SELECT * FROM notifications WHERE receiver_id = ? AND reference_id = ? AND title LIKE '%Escalat%'",
            (backup.user_id, cid),
        ).fetchone()
        assert notif_b is not None

    # 2. Fast forward past 2x deadline (70 mins ago)
    past_time_l2 = (datetime.now() - timedelta(minutes=75)).strftime("%Y-%m-%d %H:%M:%S")
    with team_svc._connect() as conn:
        conn.execute("UPDATE complaints SET awaiting_assign_since = ? WHERE complaint_id = ?", (past_time_l2, cid))

    complaint_svc.apply_automatic_rules()

    comp_l2 = complaint_svc.get_complaint(cid)
    assert comp_l2.assign_escalation_level == 2
    assert not comp_l2.assigned_to  # NEVER auto-assigned!

    # Level 2: Warden and App Manager can assign
    with team_svc._connect() as conn:
        notif_w = conn.execute(
            "SELECT * FROM notifications WHERE receiver_id = ? AND reference_id = ? AND title LIKE '%Escalat%'",
            (warden.user_id, cid),
        ).fetchone()
        assert notif_w is not None

    # Warden assigns complaint to employee
    w_assign = client.post(f"/complaints/{cid}/assign", json={
        "assigned_to": emp.user_id,
        "reason": "Assigned by warden following escalation level 2",
    }, headers=warden_headers)
    assert w_assign.status_code == 200
    assert w_assign.json()["assigned_to"] == emp.user_id


def test_l10_worker_returns_complaint(services):
    """L10: Worker returns complaint: returns to Submitted, assigned_to cleared, assign clock restarts at 0, coordinator notified."""
    auth = services["auth"]
    team_svc = services["team"]

    coord, coord_headers = _create_user(auth, ROLE_COORDINATOR, "l10_coord")
    emp, emp_headers = _create_user(auth, ROLE_EMPLOYEE, "l10_emp")
    student, std_headers = _create_user(auth, ROLE_STUDENT, "l10_stu")

    loc = _create_loc(auth, "L10")
    dept = _create_dept(auth, "L10")

    team = team_svc.create_team(
        name=f"Team L10 {loc.location_id}",
        department_id=dept.department_id,
        coordinator_id=coord.user_id,
        location_ids=[loc.location_id],
        member_ids=[coord.user_id, emp.user_id],
    )

    c_res = client.post("/complaints", json={
        "location_id": loc.location_id,
        "department_id": dept.department_id,
        "category": "electrical",
        "title": "L10 Return Test",
        "description": "Worker cannot perform without special permit",
        "visibility_type": "Private",
    }, headers=std_headers)
    cid = c_res.json()["complaint_id"]

    # Coordinator assigns to employee
    client.post(f"/complaints/{cid}/assign", json={"assigned_to": emp.user_id}, headers=coord_headers)

    # Worker returns complaint
    return_res = client.post(f"/complaints/{cid}/return", json={
        "reason": "Requires high voltage certified technician",
    }, headers=emp_headers)
    assert return_res.status_code == 200, return_res.text
    ret_data = return_res.json()

    assert ret_data["status"] == STATUS_SUBMITTED
    assert not ret_data.get("assigned_to")
    assert ret_data.get("awaiting_assign_since") is not None
    assert ret_data.get("returned_reason") == "Requires high voltage certified technician"

    # Coordinator notified
    with team_svc._connect() as conn:
        notif_coord = conn.execute(
            "SELECT * FROM notifications WHERE receiver_id = ? AND reference_id = ? AND title LIKE '%Returned%'",
            (coord.user_id, cid),
        ).fetchone()
        assert notif_coord is not None


def test_l11_verification_guard(services):
    """L11: Verification guard: worker who did the work cannot verify; coordinator who marked resolved on behalf cannot verify."""
    auth = services["auth"]
    team_svc = services["team"]
    complaint_svc = services["complaint"]

    coord, coord_headers = _create_user(auth, ROLE_COORDINATOR, "l11_coord")
    emp, emp_headers = _create_user(auth, ROLE_EMPLOYEE, "l11_emp")
    student, std_headers = _create_user(auth, ROLE_STUDENT, "l11_stu")
    warden, _ = _create_user(auth, ROLE_LOCATION_IN_CHARGE, "l11_warden")

    loc = _create_loc(auth, "L11", in_charge_id=warden.user_id)
    dept = _create_dept(auth, "L11")

    team = team_svc.create_team(
        name=f"Team L11 {loc.location_id}",
        department_id=dept.department_id,
        coordinator_id=coord.user_id,
        location_ids=[loc.location_id],
        member_ids=[coord.user_id, emp.user_id],
    )

    c_res = client.post("/complaints", json={
        "location_id": loc.location_id,
        "department_id": dept.department_id,
        "category": "electrical",
        "title": "L11 Verification Guard Test",
        "description": "Ensuring no self-verification",
        "visibility_type": "Private",
    }, headers=std_headers)
    cid = c_res.json()["complaint_id"]

    # Assign to employee
    client.post(f"/complaints/{cid}/assign", json={"assigned_to": emp.user_id}, headers=coord_headers)

    # 1. Employee marks resolved
    client.put(f"/complaints/{cid}/resolve", json={"skip_photo": True, "notes": "Fixed by emp"}, headers=emp_headers)

    # Worker attempts verification -> Forbidden (403)
    worker_verify = client.post(f"/complaints/{cid}/verify", headers=emp_headers)
    assert worker_verify.status_code == 403

    # 2. Coordinator marks resolved on behalf of employee on a new complaint
    c2_res = client.post("/complaints", json={
        "location_id": loc.location_id,
        "department_id": dept.department_id,
        "category": "electrical",
        "title": "L11 On Behalf Resolution",
        "description": "Coordinator marking on behalf of worker",
        "visibility_type": "Private",
    }, headers=std_headers)
    c2_id = c2_res.json()["complaint_id"]

    client.post(f"/complaints/{c2_id}/assign", json={"assigned_to": emp.user_id}, headers=coord_headers)

    # Coordinator marks resolved on behalf
    client.put(f"/complaints/{c2_id}/resolve", json={
        "skip_photo": True,
        "notes": "Coordinator confirming employee completed work",
    }, headers=coord_headers)

    # Check marked_by is coordinator and fixed_by is employee
    comp2 = complaint_svc.get_complaint(c2_id)
    assert comp2.fixed_by == emp.user_id
    assert comp2.marked_by == coord.user_id

    # Coordinator cannot verify this complaint -> Forbidden (403)
    coord_verify = client.post(f"/complaints/{c2_id}/verify", headers=coord_headers)
    assert coord_verify.status_code == 403

