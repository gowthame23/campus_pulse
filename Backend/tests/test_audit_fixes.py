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


