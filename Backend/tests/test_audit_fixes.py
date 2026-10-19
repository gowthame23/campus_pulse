import sqlite3
import pytest
from services.auth_service import AuthService
from api.dependencies import get_db_path


def test_rel_001_custom_department_issues_persist_across_startup():
    """REL-001: Ensure custom department issues are not wiped when startup / seed runs."""
    db_path = get_db_path()
    auth_service = AuthService(db_path=db_path)
    auth_service.ensure_seed_data()

    # Insert a custom department issue
    custom_issue_id = "ISS_CUSTOM_TEST_001"
    with sqlite3.connect(db_path) as conn:
        conn.execute("DELETE FROM department_issues WHERE issue_id = ?", (custom_issue_id,))
        conn.execute("""
            INSERT INTO department_issues (issue_id, department_id, issue_name, description, active, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
        """, (custom_issue_id, "DEP_ELEC", "Custom Solar Inverter Malfunction", "Custom issue description", "2026-10-12 10:00:00"))
        conn.commit()

    # Re-run startup / seed initialization
    auth_service_restarted = AuthService(db_path=db_path)
    auth_service_restarted.ensure_seed_data()

    # Verify custom issue still exists
    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT issue_id, issue_name FROM department_issues WHERE issue_id = ?",
            (custom_issue_id,)
        ).fetchone()

    assert row is not None, "Custom department issue was wiped during seed initialization / startup!"
    assert row[0] == custom_issue_id


def test_sec_007_personal_email_cannot_login_and_placeholder_works():
    """SEC-007: Unregistered personal emails cannot log in as admin or any role; placeholder works."""
    from fastapi.testclient import TestClient
    from api.main import app
    from middleware.rate_limiter import auth_limiter

    client = TestClient(app)
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()

    # Unregistered personal emails must NOT be able to log in
    res_admin_personal = client.post("/auth/login", json={"username": "unregistered_external_user@gmail.com", "password": "Admin@123"})
    assert res_admin_personal.status_code == 401, f"Expected 401 for unregistered email but got {res_admin_personal.status_code}"

    res_student_personal = client.post("/auth/login", json={"username": "unregistered_student@gmail.com", "password": "Student@123"})
    assert res_student_personal.status_code == 401, f"Expected 401 for unregistered email but got {res_student_personal.status_code}"

    # Standard canonical admin must work
    res_placeholder = client.post("/auth/login", json={"username": "gowthamejjurothu@gmail.com", "password": "Admin@123"})
    assert res_placeholder.status_code == 200, f"Expected 200 for canonical admin but got {res_placeholder.status_code}"
    assert res_placeholder.json()["role"] == "administrator"


def test_sec_006_safety_report_idor_prevention():
    """SEC-006: Close safety report IDOR. Non-admins must provide case_code and match reporter identity."""
    from fastapi.testclient import TestClient
    from api.main import app
    from middleware.rate_limiter import auth_limiter

    client = TestClient(app)
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()

    # Login Student A
    res_a = client.post("/auth/login", json={"username": "gowtham.e23@iiits.in", "password": "Student@123"})
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Login Student B
    res_b = client.post("/auth/login", json={"username": "student2@campus.edu", "password": "Student@123"})
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Login Warden
    res_w = client.post("/auth/login", json={"username": "naveen@campus.edu", "password": "Warden@123"})
    token_w = res_w.json()["access_token"]
    headers_w = {"Authorization": f"Bearer {token_w}"}

    # Login Admin
    res_adm = client.post("/auth/login", json={"username": "gowthamejjurothu@gmail.com", "password": "Admin@123"})
    token_adm = res_adm.json()["access_token"]
    headers_adm = {"Authorization": f"Bearer {token_adm}"}

    # Enable safety reports if disabled
    with sqlite3.connect(get_db_path()) as conn:
        conn.execute("UPDATE system_settings SET setting_value = 'true' WHERE setting_key = 'safety_reports_enabled'")
        conn.commit()

    with client:
        # Student A creates a safety report
        create_res = client.post(
            "/safety-reports",
            json={"category": "Harassment", "description": "Confidential report by Student A"},
            headers=headers_a,
        )
        assert create_res.status_code == 201
        data = create_res.json()
        report_id = data["report_id"]
        case_code = data["case_code"]

        # Student B cannot view it with report_id alone (must be 403 or 404)
        idor_res_report_id = client.get(f"/safety-reports/{report_id}", headers=headers_b)
        assert idor_res_report_id.status_code in (403, 404), f"Expected 403 or 404 for Student B with report_id alone, got {idor_res_report_id.status_code}"

        # Student B cannot view it even if guessing or passing case_code (must be 403)
        idor_res_case_code = client.get(f"/safety-reports/{case_code}", headers=headers_b)
        assert idor_res_case_code.status_code == 403, f"Expected 403 for Student B accessing Student A's case_code, got {idor_res_case_code.status_code}"

        # Student A with correct case_code CAN view and post messages
        view_res_a = client.get(f"/safety-reports/{case_code}", headers=headers_a)
        assert view_res_a.status_code == 200
        assert view_res_a.json()["report_id"] == report_id

        msg_res_a = client.post(
            f"/safety-reports/{case_code}/messages",
            json={"body": "Follow-up message from reporter"},
            headers=headers_a,
        )
        assert msg_res_a.status_code == 200

        # Warden cannot view it (403)
        warden_res = client.get(f"/safety-reports/{case_code}", headers=headers_w)
        assert warden_res.status_code == 403

        # Admin CAN view it
        admin_res = client.get(f"/safety-reports/{case_code}", headers=headers_adm)
        assert admin_res.status_code == 200


def test_sec_005_certificate_endpoint_security():
    """SEC-005: /recognitions/certificate must require authentication, validate month format, and escape HTML."""
    from fastapi.testclient import TestClient
    from api.main import app
    from middleware.rate_limiter import auth_limiter

    client = TestClient(app)
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()

    # 1. Unauthenticated request must return 401
    res_unauth = client.get("/recognitions/certificate?coordinator_id=USR_COORDINATOR&month=2026-08")
    assert res_unauth.status_code == 401, f"Expected 401 for unauthenticated request, got {res_unauth.status_code}"

    # Authenticate as admin
    login_adm = client.post("/auth/login", json={"username": "gowthamejjurothu@gmail.com", "password": "Admin@123"})
    token_adm = login_adm.json()["access_token"]
    headers_adm = {"Authorization": f"Bearer {token_adm}"}

    # 2. Malicious or invalid month parameter must return 400
    res_xss = client.get(
        "/recognitions/certificate?coordinator_id=USR_COORDINATOR&month=<script>alert(1)</script>",
        headers=headers_adm,
    )
    assert res_xss.status_code == 400, f"Expected 400 for XSS month input, got {res_xss.status_code}"

    # 3. Authenticated request with valid month returns 200 HTML with all inputs escaped
    res_valid = client.get(
        "/recognitions/certificate?coordinator_id=USR_EMP_A1&month=2026-08",
        headers=headers_adm,
    )
    assert res_valid.status_code == 200
    assert "Fixer of the Month" in res_valid.text
    assert "2026-08" in res_valid.text
    assert "<script>" not in res_valid.text


def test_sec_008_spreadsheet_formula_injection_sanitization():
    """SEC-008: Spreadsheet exports must neutralize formula injection characters (=, +, -, @, \\t, \\r)."""
    import csv
    import io
    from fastapi.testclient import TestClient
    from api.main import app
    from middleware.rate_limiter import auth_limiter

    client = TestClient(app)
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()

    # Update student name with dangerous formula injection payload
    payload_name = "=cmd|' /C calc'!A0"
    with sqlite3.connect(get_db_path()) as conn:
        conn.execute("UPDATE users SET name = ? WHERE user_id = 'USR_STUDENT'", (payload_name,))
        conn.commit()

    # Login as admin
    login_adm = client.post("/auth/login", json={"username": "gowthamejjurothu@gmail.com", "password": "Admin@123"})
    token_adm = login_adm.json()["access_token"]
    headers_adm = {"Authorization": f"Bearer {token_adm}"}

    # Export users CSV
    res_csv = client.get("/users/export?format=csv", headers=headers_adm)
    assert res_csv.status_code == 200

    csv_reader = csv.DictReader(io.StringIO(res_csv.text))
    student_rows = [row for row in csv_reader if row.get("User ID") == "USR_STUDENT"]
    assert len(student_rows) == 1
    name_cell = student_rows[0].get("Name")
    assert name_cell.startswith("'="), f"Expected formula injection to be neutralized with leading quote, got: {name_cell}"


def test_sec_009_warden_leave_permissions_scoped_to_location():
    """SEC-009: Warden can set leave ONLY for members who cover warden's assigned locations."""
    import sqlite3
    import pytest
    from models.location_in_charge import LocationInCharge
    from services.team_service import TeamService

    db_path = get_db_path()
    with sqlite3.connect(db_path) as conn:
        conn.execute("INSERT OR IGNORE INTO locations (location_id, name, location_type, in_charge_id, active) VALUES ('LOC_TEST_H1', 'Test Hostel 1', 'hostel', 'USR_WARDEN_TEST_1', 1)")
        conn.execute("INSERT OR IGNORE INTO locations (location_id, name, location_type, in_charge_id, active) VALUES ('LOC_TEST_H2', 'Test Hostel 2', 'hostel', 'USR_WARDEN_TEST_2', 1)")
        conn.execute("INSERT OR IGNORE INTO users (user_id, name, email, password, role, location_id, status, active) VALUES ('USR_WARDEN_TEST_1', 'Warden H1', 'wardenh1@example.com', 'pwd', 'location_in_charge', 'LOC_TEST_H1', 'Active', 1)")
        conn.execute("INSERT OR IGNORE INTO users (user_id, name, email, password, role, location_id, status, active) VALUES ('USR_COORD_TEST_1', 'Coord H1', 'coordh1@example.com', 'pwd', 'coordinator', 'LOC_TEST_H1', 'Active', 1)")
        conn.execute("INSERT OR IGNORE INTO users (user_id, name, email, password, role, location_id, status, active) VALUES ('USR_COORD_TEST_2', 'Coord H2', 'coordh2@example.com', 'pwd', 'coordinator', 'LOC_TEST_H2', 'Active', 1)")

        conn.execute("INSERT OR IGNORE INTO teams (team_id, name, department_id, coordinator_id, active, created_at) VALUES ('TEAM_TEST_H1', 'Team H1', 'DEP_ELEC', 'USR_COORD_TEST_1', 1, '2026-10-12')")
        conn.execute("INSERT OR IGNORE INTO team_locations (team_id, location_id) VALUES ('TEAM_TEST_H1', 'LOC_TEST_H1')")

        conn.execute("INSERT OR IGNORE INTO teams (team_id, name, department_id, coordinator_id, active, created_at) VALUES ('TEAM_TEST_H2', 'Team H2', 'DEP_PLUMB', 'USR_COORD_TEST_2', 1, '2026-10-12')")
        conn.execute("INSERT OR IGNORE INTO team_locations (team_id, location_id) VALUES ('TEAM_TEST_H2', 'LOC_TEST_H2')")
        conn.commit()

    team_service = TeamService(db_path=db_path)
    warden_user = LocationInCharge(
        user_id="USR_WARDEN_TEST_1",
        name="Warden H1",
        email="wardenh1@example.com",
        password="pwd",
        location_id="LOC_TEST_H1",
    )
    warden_user.assigned_locations = ["LOC_TEST_H1"]

    # 1. Warden of H1 tries to set leave for Coordinator covering only H2 -> must raise PermissionError
    with pytest.raises(PermissionError) as exc_info:
        team_service.set_leave(
            user_id="USR_COORD_TEST_2",
            from_date="2026-11-01",
            to_date="2026-11-05",
            reason="Vacation",
            set_by="USR_WARDEN_TEST_1",
            caller_user=warden_user,
        )
    assert "location" in str(exc_info.value).lower()

    # 2. Warden of H1 sets leave for Coordinator covering H1 -> succeeds
    res_success = team_service.set_leave(
        user_id="USR_COORD_TEST_1",
        from_date="2026-11-01",
        to_date="2026-11-05",
        reason="Vacation",
        set_by="USR_WARDEN_TEST_1",
        caller_user=warden_user,
    )
    assert res_success["user_id"] == "USR_COORD_TEST_1"






