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
    get_emergency_service,
    get_config_service,
)
from core.constants import (
    ROLE_ADMINISTRATOR,
    ROLE_APP_MANAGER,
    ROLE_COORDINATOR,
    ROLE_EMPLOYEE,
    ROLE_LOCATION_IN_CHARGE,
    ROLE_STUDENT,
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
        "emergency": get_emergency_service(),
        "config": get_config_service(),
    }


def _create_user(auth, role, prefix, phone="9876543210"):
    uid = uuid.uuid4().hex[:6]
    email = f"{prefix}_{uid}@testpulse.local"
    u = auth.create_user(
        name=f"User {prefix}_{uid}",
        email=email,
        password="Temp@Pass123",
        role=role,
    )
    u.phone_number = phone
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


def test_emergency_categories_and_call_list_ordering(services):
    """Test emergency call list sorting:
    - Fire/Smoke: 112 first, Security, Warden, Dept contacts
    - Electrical: Dept contacts first, Coordinator, Warden, Security, 112 last
    - Duplicates removed, 112 always present
    """
    auth = services["auth"]
    emg = services["emergency"]
    team_svc = services["team"]

    # 1. Setup staff & student
    coord, coord_headers = _create_user(auth, ROLE_COORDINATOR, "emg_coord", phone="9988771122")
    warden, warden_headers = _create_user(auth, ROLE_LOCATION_IN_CHARGE, "emg_warden", phone="9988773344")
    student, student_headers = _create_user(auth, ROLE_STUDENT, "emg_stu")

    loc = _create_loc(auth, "EMG_LOC", in_charge_id=warden.user_id)
    student.location_id = loc.location_id
    auth.save_user(student)

    elec_dept = _create_dept(auth, "Electrical")
    team = team_svc.create_team(
        name=f"Electrical Team {loc.location_id}",
        department_id=elec_dept.department_id,
        coordinator_id=coord.user_id,
        location_ids=[loc.location_id],
        member_ids=[],
    )

    # Add emergency contact for Electrical
    emg.create_contact(
        name="Senior Electrician",
        phone="9988775566",
        department_id=elec_dept.department_id,
        location_id=loc.location_id,
        sort_order=1,
    )

    # Create/Ensure categories
    elec_cat = emg.create_category("Electrical", department_id=elec_dept.department_id, sort_order=1)
    fire_cat = emg.create_category("Fire / Smoke", department_id=None, sort_order=2)

    # 2. Test Electrical Call List (non-fire/medical)
    res_elec = client.get(
        f"/emergency/call-list?category={elec_cat['category_id']}&location_id={loc.location_id}",
        headers=student_headers,
    )
    assert res_elec.status_code == 200
    elec_list = res_elec.json()
    assert len(elec_list) >= 3

    # Electrical: 112 must be the LAST item
    assert elec_list[-1]["phone"] == "112"
    # Department contact (Senior Electrician) should be first
    assert any("Senior Electrician" in item["name"] for item in elec_list[:2])
    # Coordinator and Warden must be present
    assert any("9988771122" in item["phone"] for item in elec_list)
    assert any("9988773344" in item["phone"] for item in elec_list)

    # 3. Test Fire / Smoke Call List
    res_fire = client.get(
        f"/emergency/call-list?category={fire_cat['category_id']}&location_id={loc.location_id}",
        headers=student_headers,
    )
    assert res_fire.status_code == 200
    fire_list = res_fire.json()
    assert len(fire_list) >= 2
    # Fire/Medical: 112 must be the FIRST item
    assert fire_list[0]["phone"] == "112"
    # Warden must be in the list
    assert any("9988773344" in item["phone"] for item in fire_list)


def test_coordinator_on_leave_shows_backup(services):
    """When coordinator is on leave, call list displays backup coordinator."""
    auth = services["auth"]
    emg = services["emergency"]
    team_svc = services["team"]

    coord, _ = _create_user(auth, ROLE_COORDINATOR, "c_leave", phone="9111111111")
    backup, _ = _create_user(auth, ROLE_EMPLOYEE, "b_work", phone="9222222222")
    student, student_headers = _create_user(auth, ROLE_STUDENT, "stu_bk")

    loc = _create_loc(auth, "LOC_BK")
    student.location_id = loc.location_id
    auth.save_user(student)

    dept = _create_dept(auth, "Plumbing")
    team = team_svc.create_team(
        name=f"Plumbing Team {loc.location_id}",
        department_id=dept.department_id,
        coordinator_id=coord.user_id,
        backup_coordinator_id=backup.user_id,
        location_ids=[loc.location_id],
        member_ids=[backup.user_id],
    )
    cat = emg.create_category("Plumbing / Water", department_id=dept.department_id)

    # Coordinator takes leave today
    today_str = date.today().isoformat()
    team_svc.set_leave(coord.user_id, today_str, today_str, "Flu", set_by=coord.user_id)

    # Fetch call list -> should show backup's phone
    res = client.get(
        f"/emergency/call-list?category={cat['category_id']}&location_id={loc.location_id}",
        headers=student_headers,
    )
    assert res.status_code == 200
    call_list = res.json()
    phones = [item["phone"] for item in call_list]
    assert "9222222222" in phones
    assert "9111111111" not in phones


def test_emergency_complaint_creation_and_reached_workflow(services):
    """Choosing category auto-creates Critical complaint, alerts staff, and handles reached Yes/No."""
    auth = services["auth"]
    emg = services["emergency"]
    team_svc = services["team"]

    coord, coord_headers = _create_user(auth, ROLE_COORDINATOR, "emg_wf_c")
    warden, warden_headers = _create_user(auth, ROLE_LOCATION_IN_CHARGE, "emg_wf_w")
    student, student_headers = _create_user(auth, ROLE_STUDENT, "emg_wf_s")

    loc = _create_loc(auth, "LOC_WF", in_charge_id=warden.user_id)
    student.location_id = loc.location_id
    auth.save_user(student)

    dept = _create_dept(auth, "Lift Dept")
    team = team_svc.create_team(
        name=f"Lift Team {loc.location_id}",
        department_id=dept.department_id,
        coordinator_id=coord.user_id,
        location_ids=[loc.location_id],
    )
    cat = emg.create_category("Lift", department_id=dept.department_id)

    # Student triggers emergency
    res = client.post(
        "/emergency/create",
        json={"category": cat["category_id"], "location_id": loc.location_id},
        headers=student_headers,
    )
    assert res.status_code == 201
    comp = res.json()
    assert comp["is_emergency"] is True
    assert comp["priority"] == "Critical"
    assert comp["emergency_category"] == "Lift"
    assert comp["status"] == "Submitted"
    complaint_id = comp["complaint_id"]

    # Student returns and selects "No answer"
    res_no = client.post(
        f"/emergency/complaints/{complaint_id}/reached",
        json={"reached": False},
        headers=student_headers,
    )
    assert res_no.status_code == 200
    assert res_no.json()["reached"] is False

    # Staff clicks "I'm on it"
    res_ack = client.post(
        f"/emergency/complaints/{complaint_id}/acknowledge",
        headers=coord_headers,
    )
    assert res_ack.status_code == 200
    assert res_ack.json()["acknowledged_by"] == coord.user_id

    # Warden views pinned emergencies
    res_pin = client.get("/emergency/pinned", headers=warden_headers)
    assert res_pin.status_code == 200
    pinned = res_pin.json()
    assert any(c["complaint_id"] == complaint_id for c in pinned)


def test_misuse_strike_policy_and_lockout(services):
    """3 Misuse strikes in 90 days pauses emergency button for 30 days.
    Genuine mistake does NOT count as strike.
    """
    auth = services["auth"]
    emg = services["emergency"]
    mgr, mgr_headers = _create_user(auth, ROLE_APP_MANAGER, "emg_mgr")
    warden, warden_headers = _create_user(auth, ROLE_LOCATION_IN_CHARGE, "emg_w_strk")
    student, student_headers = _create_user(auth, ROLE_STUDENT, "emg_bad_stu")

    loc = _create_loc(auth, "LOC_STRK", in_charge_id=warden.user_id)
    student.location_id = loc.location_id
    auth.save_user(student)

    cat = emg.create_category("General Misuse Test")

    # 1. First emergency -> Marked as "Genuine mistake" -> 0 strikes
    c1 = emg.create_emergency(student, cat["category_id"], loc.location_id)
    res_mistake = client.post(
        f"/emergency/complaints/{c1['complaint_id']}/outcome",
        json={"outcome": "mistake"},
        headers=warden_headers,
    )
    assert res_mistake.status_code == 200
    st_stat = emg.get_student_status(student.user_id)
    assert st_stat["strikes_count"] == 0

    # 2. Strike 1 (Misuse) -> Strike recorded, priority reset
    c2 = emg.create_emergency(student, cat["category_id"], loc.location_id)
    res_m1 = client.post(
        f"/emergency/complaints/{c2['complaint_id']}/outcome",
        json={"outcome": "misuse"},
        headers=warden_headers,
    )
    assert res_m1.status_code == 200
    st_stat = emg.get_student_status(student.user_id)
    assert st_stat["strikes_count"] == 1
    assert st_stat["is_locked"] is False

    # 3. Strike 2 (Misuse)
    c3 = emg.create_emergency(student, cat["category_id"], loc.location_id)
    client.post(
        f"/emergency/complaints/{c3['complaint_id']}/outcome",
        json={"outcome": "misuse"},
        headers=warden_headers,
    )
    st_stat = emg.get_student_status(student.user_id)
    assert st_stat["strikes_count"] == 2
    assert st_stat["is_locked"] is False

    # 4. Strike 3 (Misuse) -> Lockout triggered!
    c4 = emg.create_emergency(student, cat["category_id"], loc.location_id)
    client.post(
        f"/emergency/complaints/{c4['complaint_id']}/outcome",
        json={"outcome": "misuse"},
        headers=warden_headers,
    )
    st_stat = emg.get_student_status(student.user_id)
    assert st_stat["strikes_count"] == 3
    assert st_stat["is_locked"] is True
    assert st_stat["locked_until"] is not None

    # Subsequent emergency attempt must be blocked (403 Forbidden)
    res_blocked = client.post(
        "/emergency/create",
        json={"category": cat["category_id"], "location_id": loc.location_id},
        headers=student_headers,
    )
    assert res_blocked.status_code == 403
    assert "paused" in res_blocked.json()["detail"].lower()


def test_emergency_stats_endpoint(services):
    """Test emergency stats per location and per team."""
    auth = services["auth"]
    mgr, mgr_headers = _create_user(auth, ROLE_APP_MANAGER, "stat_mgr")

    res = client.get("/emergency/stats", headers=mgr_headers)
    assert res.status_code == 200
    data = res.json()
    assert "by_location" in data
    assert "by_team" in data
