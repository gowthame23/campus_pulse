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
    """SEC-007: Personal emails cannot log in as admin or any role; placeholder works."""
    from fastapi.testclient import TestClient
    from api.main import app
    from middleware.rate_limiter import auth_limiter

    client = TestClient(app)
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()

    # Personal emails must NOT be able to log in
    res_admin_personal = client.post("/auth/login", json={"username": "gowthamejjurothu@gmail.com", "password": "Admin@123"})
    assert res_admin_personal.status_code == 401, f"Expected 401 for personal email but got {res_admin_personal.status_code}"

    res_student_personal = client.post("/auth/login", json={"username": "gowtham.e23@iiits.in", "password": "Student@123"})
    assert res_student_personal.status_code == 401, f"Expected 401 for personal email but got {res_student_personal.status_code}"

    # Standard placeholder must work
    res_placeholder = client.post("/auth/login", json={"username": "admin@example.com", "password": "Admin@123"})
    assert res_placeholder.status_code == 200, f"Expected 200 for placeholder admin@example.com but got {res_placeholder.status_code}"
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
    res_a = client.post("/auth/login", json={"username": "student@example.com", "password": "Student@123"})
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # Login Student B
    res_b = client.post("/auth/login", json={"username": "student2@campus.edu", "password": "Student@123"})
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Login Warden
    res_w = client.post("/auth/login", json={"username": "warden@example.com", "password": "warden@123"})
    token_w = res_w.json()["access_token"]
    headers_w = {"Authorization": f"Bearer {token_w}"}

    # Login Admin
    res_adm = client.post("/auth/login", json={"username": "admin@example.com", "password": "Admin@123"})
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



