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

