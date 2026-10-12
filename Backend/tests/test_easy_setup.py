import os
import sys
import io
import uuid
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from middleware.rate_limiter import auth_limiter
from api.dependencies import (
    get_auth_service,
    get_team_service,
    get_setup_import_service,
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


def _reset_limiter():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()


def _unpack(payload):
    if isinstance(payload, dict) and "data" in payload and len(payload) == 1:
        return payload["data"]
    return payload


def _login(username, password="Temp@Pass123"):
    _reset_limiter()
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, f"Login failed for {username}: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _login_with_active_password(username, initial_password="Temp@Pass123", final_password="Perm@Pass123"):
    _reset_limiter()
    res = client.post("/auth/login", json={"username": username, "password": initial_password})
    assert res.status_code == 200, f"Login failed for {username}: {res.text}"
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    chg = client.post(
        "/auth/change-password",
        json={
            "old_password": initial_password,
            "new_password": final_password,
            "confirm_password": final_password,
        },
        headers=headers,
    )
    if chg.status_code == 200:
        return _login(username, final_password)
    return headers


def _get_admin_headers():
    _reset_limiter()
    try:
        return _login("admin@example.com", "Admin@123")
    except Exception:
        return _login("admin@example.com", "Admin@123")


@pytest.fixture(scope="module")
def admin_headers():
    return _get_admin_headers()


@pytest.fixture(scope="module")
def services():
    return {
        "auth": get_auth_service(),
        "team": get_team_service(),
        "setup": get_setup_import_service(),
    }


def _create_user(admin_headers, role, email_prefix, phone="9876543210"):
    uid = uuid.uuid4().hex[:8]
    email = f"{email_prefix}_{uid}@example.com"
    payload = {
        "name": f"User {uid}",
        "email": email,
        "role": role,
        "phone": phone,
        "password": "Temp@Pass123",
        "confirm_password": "Temp@Pass123",
    }
    res = client.post("/users", json=payload, headers=admin_headers)
    assert res.status_code == 201, f"Create user failed: {res.text}"
    data = res.json()
    # Handle response wrapper if present
    user_obj = data.get("data") if isinstance(data, dict) and "data" in data else data
    return user_obj


def test_template_downloads(admin_headers):
    for imp_type in ["locations", "staff", "teams", "emergency_contacts"]:
        for fmt in ["csv", "xlsx"]:
            res = client.get(f"/setup/import/template?type={imp_type}&format={fmt}", headers=admin_headers)
            assert res.status_code == 200, f"Failed template download for {imp_type} in {fmt}: {res.text}"
            assert len(res.content) > 0


def test_locations_import_preview_and_execute(admin_headers):
    uid = uuid.uuid4().hex[:6]
    warden = _create_user(admin_headers, ROLE_LOCATION_IN_CHARGE, f"warden_loc_{uid}", phone="9112233445")
    parent_name = f"Alpha Tower {uid}"
    child_name = f"Alpha Floor {uid}"

    csv_content = (
        "name,parent,type,warden_email_or_phone\n"
        f"{parent_name},,Hostel,{warden['email']}\n"
        f"{child_name},{parent_name},Hostel,\n"
        "Broken Location,,Hostel,nonexistent_warden@college.edu\n"
    )

    # Preview
    preview_res = client.post(
        "/setup/import/preview",
        data={"type": "locations"},
        files={"file": ("locations.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        headers=admin_headers,
    )
    assert preview_res.status_code == 200, preview_res.text
    pdata = _unpack(preview_res.json())
    assert pdata["total_rows"] == 3
    assert pdata["valid_count"] == 2
    assert pdata["invalid_count"] == 1
    assert pdata["rows"][2]["errors"], "Expected error on broken warden"

    # Execute
    exec_res = client.post(
        "/setup/import/execute",
        data={"type": "locations"},
        files={"file": ("locations.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        headers=admin_headers,
    )
    assert exec_res.status_code == 200, exec_res.text
    edata = _unpack(exec_res.json())
    assert edata["imported_count"] == 2
    assert edata["skipped_count"] == 1


def test_staff_import_worker_without_email_and_phone_normalization(admin_headers, services):
    auth = services["auth"]
    import random
    uid = uuid.uuid4().hex[:6]
    worker_phone = f"98{random.randint(10000000, 99999999)}"
    warden_phone = f"99{random.randint(10000000, 99999999)}"
    warden_email = f"suresh_{uid}@testpulse.local"

    # Worker without email: phone +91 XXXXX XXXXX -> normalized to 10 digits
    # Coordinator with phone: +91-XXXXX-XXXXX
    csv_content = (
        "name,role,email,phone,teams\n"
        f"Ramu Electrician,Employee,,+91 {worker_phone[:5]} {worker_phone[5:]},\n"
        f"Suresh InCharge,Warden,{warden_email},+91 {warden_phone[:5]} {warden_phone[5:]},\n"
        "Missing Phone Coord,Coordinator,coord_nophone@testpulse.local,,\n"
    )

    # Preview
    preview_res = client.post(
        "/setup/import/preview",
        data={"type": "staff"},
        files={"file": ("staff.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        headers=admin_headers,
    )
    assert preview_res.status_code == 200, preview_res.text
    pdata = _unpack(preview_res.json())
    assert pdata["total_rows"] == 3
    assert pdata["valid_count"] == 2
    assert pdata["invalid_count"] == 1
    assert "Phone number is required" in str(pdata["rows"][2]["errors"])

    # Execute
    exec_res = client.post(
        "/setup/import/execute",
        data={"type": "staff"},
        files={"file": ("staff.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        headers=admin_headers,
    )
    assert exec_res.status_code == 200, exec_res.text
    edata = _unpack(exec_res.json())
    assert edata["success_count"] == 2, f"Import failed report: {edata.get('report')}"
    assert edata["imported_count"] == 2

    # Verify worker was created without email and can login with phone
    worker_user = auth.get_user_by_phone(worker_phone)
    assert worker_user is not None
    worker_phone_val = getattr(worker_user, "phone_number", None) or (worker_user.get("phone") if isinstance(worker_user, dict) else "")
    assert auth.normalize_phone(worker_phone_val) == worker_phone
    worker_uid = getattr(worker_user, "user_id", None) or (worker_user.get("user_id") if isinstance(worker_user, dict) else "")

    # Check that temp password slip generation works
    slip_res = client.post(f"/setup/workers/{worker_uid}/reset-password", headers=admin_headers)
    assert slip_res.status_code == 200, slip_res.text
    slip_data = _unpack(slip_res.json())
    temp_pwd = slip_data.get("temp_password") or slip_data.get("temporary_password")
    assert temp_pwd.startswith("CP-")
    assert slip_data["phone"] == worker_phone

    # Worker can log in using normalized 10-digit phone number and new temp password
    login_res = client.post("/auth/login", json={"username": worker_phone, "password": temp_pwd})
    assert login_res.status_code == 200, f"Phone login failed: {login_res.text}"
    login_data = login_res.json()
    assert (login_data["user"].get("phone") or login_data["user"].get("phone_number")) == worker_phone
    assert login_data.get("first_login") is True or login_data["user"].get("first_login") is True or login_data["user"].get("is_temp_password") is True

    # Also login with "+91 XXXXX XXXXX" format
    login_prefix_res = client.post("/auth/login", json={"username": f"+91 {worker_phone[:5]} {worker_phone[5:]}", "password": temp_pwd})
    assert login_prefix_res.status_code == 200


def test_teams_import_with_overlap_collision(admin_headers, services):
    auth = services["auth"]
    coord = _create_user(admin_headers, ROLE_COORDINATOR, "coord_t_imp", phone="9123456789")

    # Create a place and department
    loc = auth.create_location("Science Block Alpha", "Academic Block")
    dept = auth.create_department("Electronics Dept")

    csv_content = (
        "team_name,department,places,coordinator,backup,members\n"
        f"Electronics Team 1,{dept.name},Science Block Alpha,{coord['email']},,\n"
        f"Conflicting Team,{dept.name},Science Block Alpha,{coord['email']},,\n"
    )

    preview_res = client.post(
        "/setup/import/preview",
        data={"type": "teams"},
        files={"file": ("teams.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        headers=admin_headers,
    )
    assert preview_res.status_code == 200, preview_res.text
    pdata = _unpack(preview_res.json())
    assert pdata["total_rows"] == 2
    assert pdata["valid_count"] == 1
    assert pdata["invalid_count"] == 1
    assert "Conflict" in str(pdata["rows"][1]["errors"]) or "already assigned" in str(pdata["rows"][1]["errors"])


def test_emergency_contacts_import(admin_headers, services):
    auth = services["auth"]
    dept = auth.create_department("Medical Center Dept")

    csv_content = (
        "department,location,name,phone,order,day_only,night_only\n"
        f"{dept.name},,Dr. Ramesh,+91 98765 00001,1,0,0\n"
        f"{dept.name},,Night Nurse,+91 98765 00002,2,0,1\n"
    )

    exec_res = client.post(
        "/setup/import/execute",
        data={"type": "emergency_contacts"},
        files={"file": ("emergency_contacts.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        headers=admin_headers,
    )
    assert exec_res.status_code == 200, exec_res.text
    edata = _unpack(exec_res.json())
    assert edata["imported_count"] == 2


def test_checklist_and_coordinator_worker_password_reset(admin_headers, services):
    auth = services["auth"]
    team_svc = services["team"]

    coord1 = _create_user(admin_headers, ROLE_COORDINATOR, "coord_chk1", phone="9800011111")
    coord2 = _create_user(admin_headers, ROLE_COORDINATOR, "coord_chk2", phone="9800022222")
    worker = _create_user(admin_headers, ROLE_EMPLOYEE, "worker_chk", phone="9800033333")

    # Create team with coord1 and worker
    loc = auth.create_location("Omega Wing", "Hostel")
    dept = auth.create_department("Civil Works")
    team = team_svc.create_team(
        name="Omega Civil Team",
        department_id=dept.department_id,
        coordinator_id=coord1["user_id"],
        location_ids=[loc.location_id],
        member_ids=[worker["user_id"]],
    )

    coord1_headers = _login_with_active_password(coord1["email"])
    coord2_headers = _login_with_active_password(coord2["email"])

    # Checklist endpoint
    chk_res = client.get("/setup/checklist", headers=admin_headers)
    assert chk_res.status_code == 200
    chk_data = _unpack(chk_res.json())
    assert "students" in chk_data
    assert "locations" in chk_data
    assert "teams_no_backup" in chk_data
    assert "is_complete" in chk_data

    # Coord1 resets password for worker in his team
    reset_res = client.post(f"/teams/{team['team_id']}/members/{worker['user_id']}/reset-password", headers=coord1_headers)
    assert reset_res.status_code == 200, reset_res.text
    slip = _unpack(reset_res.json())
    slip_pwd = slip.get("temp_password") or slip.get("temporary_password")
    assert slip_pwd.startswith("CP-")
    assert slip["name"] == worker["name"]

    # Coord2 attempts to reset password for worker in Coord1's team -> 403 Forbidden
    unauth_res = client.post(f"/teams/{team['team_id']}/members/{worker['user_id']}/reset-password", headers=coord2_headers)
    assert unauth_res.status_code == 403
