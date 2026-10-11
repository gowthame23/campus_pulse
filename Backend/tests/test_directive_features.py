import io
import uuid
from fastapi.testclient import TestClient
from api.main import app
from middleware.rate_limiter import auth_limiter

client = TestClient(app)

def _reset_limiter():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()

def _get_admin_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "gowthamejjurothu@gmail.com", "password": "Admin@123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def _get_student_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "gowtham.e23@iiits.in", "password": "Student@123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_program_management():
    headers = _get_admin_headers()
    # 1. List programs (should contain default seeded programs: B.Tech, Degree, M.Tech, MBA)
    res = client.get("/programs", headers=headers)
    assert res.status_code == 200
    programs = res.json()
    names = [p["name"] for p in programs]
    assert "B.Tech" in names
    assert "Degree" in names

    # 2. Create custom program
    uid = uuid.uuid4().hex[:5]
    new_prog = {
        "name": f"B.Sc Data Science {uid}",
        "duration_years": 3,
        "description": "3-Year Degree in Data Science"
    }
    create_res = client.post("/programs", json=new_prog, headers=headers)
    assert create_res.status_code == 201
    prog_data = create_res.json()
    assert prog_data["name"] == new_prog["name"]
    assert prog_data["duration_years"] == 3

    # 3. Clean up
    del_res = client.delete(f"/programs/{prog_data['program_id']}", headers=headers)
    assert del_res.status_code == 200


def test_student_lifecycle_statuses():
    headers = _get_admin_headers()
    uid = uuid.uuid4().hex[:6]
    email = f"grad_{uid}@campuspulse.edu"

    # Create student
    res = client.post("/users", json={
        "name": "Graduating Student",
        "email": email,
        "role": "student",
        "roll_number": f"ROLL_GRAD_{uid}",
        "department_id": "DEPT_ELECTRICAL"
    }, headers=headers)
    assert res.status_code == 201
    user_id = res.json()["user_id"]
    temp_pw = res.json()["temporary_password"]

    # Mark as Graduated
    grad_res = client.patch(f"/users/{user_id}/status", json={"status": "Graduated"}, headers=headers)
    assert grad_res.status_code == 200
    assert grad_res.json()["status"] == "Graduated"
    assert grad_res.json()["active"] is False

    # Login should be blocked for non-active graduated status
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": email, "password": temp_pw})
    assert login_res.status_code == 403


def test_student_movement_bulk_import():
    headers = _get_admin_headers()
    uid = uuid.uuid4().hex[:6]
    email = f"move_{uid}@campuspulse.edu"
    roll = f"ROLL_MOVE_{uid}"

    # Year 1: Import student into LOC_HOSTEL_A
    csv_y1 = (
        "name,email,role,roll_number,location_id,year,program\n"
        f"Moving Student, {email}, student, {roll}, LOC_HOSTEL_A, Year 1, B.Tech\n"
    )
    res1 = client.post("/users/import", files={"file": ("y1.csv", io.BytesIO(csv_y1.encode("utf-8")), "text/csv")}, headers=headers)
    assert res1.status_code == 200
    rep1 = res1.json()
    assert rep1["success_count"] == 1
    assert "activation_token" in rep1["report"][0]

    # Year 2: Student moves to LOC_ACADEMIC / another location with update_existing enabled
    csv_y2 = (
        "name,email,role,roll_number,location_id,year,program\n"
        f"Moving Student, {email}, student, {roll}, LOC_ACADEMIC, Year 2, B.Tech\n"
    )
    res2 = client.post(
        "/users/import",
        data={"update_existing": "true", "program": "B.Tech", "year": "Year 2"},
        files={"file": ("y2.csv", io.BytesIO(csv_y2.encode("utf-8")), "text/csv")},
        headers=headers
    )
    assert res2.status_code == 200
    rep2 = res2.json()
    assert rep2["success_count"] == 1
    assert "Updated existing student" in (rep2["report"][0]["reason"] or "")


def test_account_activation_flow():
    headers = _get_admin_headers()
    uid = uuid.uuid4().hex[:6]
    email = f"activate_{uid}@campuspulse.edu"

    # Create user via import to get activation token
    csv_content = f"name,email,role,roll_number\nActivation User,{email},student,ROLL_ACT_{uid}\n"
    res = client.post("/users/import", files={"file": ("act.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}, headers=headers)
    token = res.json()["report"][0]["activation_token"]
    assert bool(token)

    # 1. Verify token
    verify_res = client.get(f"/auth/activate/verify?token={token}")
    assert verify_res.status_code == 200
    assert verify_res.json()["valid"] is True
    assert verify_res.json()["email"] == email

    # 2. Complete activation with new password
    new_pw = "NewSecurePassword@123"
    complete_res = client.post("/auth/activate/complete", json={
        "activation_token": token,
        "password": new_pw,
        "confirm_password": new_pw,
    })
    assert complete_res.status_code == 200

    # 3. Log in with newly activated password
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": email, "password": new_pw})
    assert login_res.status_code == 200
    assert bool(login_res.json()["access_token"])
    assert login_res.json()["first_login"] is False


def test_bulk_import_triggers_activation_email(monkeypatch):
    headers = _get_admin_headers()
    uid = uuid.uuid4().hex[:6]
    email = f"auto_mail_{uid}@campuspulse.edu"
    student_name = f"Mail Student {uid}"

    dispatched = []

    def mock_send_activation_email(to_email, activation_link, user_name="Student"):
        dispatched.append({
            "to_email": to_email,
            "activation_link": activation_link,
            "user_name": user_name
        })
        return True

    monkeypatch.setattr("utils.email.send_activation_email", mock_send_activation_email)

    csv_content = f"name,email,role,roll_number\n{student_name},{email},student,ROLL_MAIL_{uid}\n"
    res = client.post("/users/import", files={"file": ("mail.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}, headers=headers)
    assert res.status_code == 200
    report = res.json()["report"][0]
    assert report["status"] == "Success"
    token = report["activation_token"]

    # Verify email dispatch was triggered with the exact parameters
    assert len(dispatched) == 1
    assert dispatched[0]["to_email"] == email
    assert dispatched[0]["activation_link"] == f"/activate?token={token}"
    assert dispatched[0]["user_name"] == student_name


def test_bulk_import_email_failure_resilience(monkeypatch):
    headers = _get_admin_headers()
    uid = uuid.uuid4().hex[:6]
    email = f"resilient_{uid}@campuspulse.edu"
    student_name = f"Resilient Student {uid}"

    def mock_failing_email(to_email, activation_link, user_name="Student"):
        raise RuntimeError("Simulated network/SMTP timeout")

    monkeypatch.setattr("utils.email.send_activation_email", mock_failing_email)

    csv_content = f"name,email,role,roll_number\n{student_name},{email},student,ROLL_RES_{uid}\n"
    res = client.post("/users/import", files={"file": ("res.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}, headers=headers)
    assert res.status_code == 200
    report = res.json()["report"][0]
    # Import must still succeed even if email dispatch threw an error
    assert report["status"] == "Success"
    assert bool(report["activation_token"])
    assert report["activation_link"].startswith("/activate?token=")


def test_send_activation_email_formatting_and_safety(monkeypatch):
    from utils.email import send_activation_email
    # When unconfigured, safely returns False and does not crash
    monkeypatch.setenv("SMTP_USERNAME", "")
    monkeypatch.setenv("SMTP_PASSWORD", "")
    result = send_activation_email("test@example.com", "/activate?token=test12345", "Test User")
    assert result is False

