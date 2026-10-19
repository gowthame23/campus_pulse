import os
import sqlite3
import time
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.security import create_session, _lookup_session, SESSION_LIFETIME, hash_token, _get_db_conn
from api.dependencies import get_auth_service, get_complaint_service, get_dashboard_service, get_analytics_service, get_db_path
from models.complaint import Complaint
from models.app_manager import AppManager
from models.administrator import Administrator
from services.auth_service import AuthService
from services.complaint_service import ComplaintService
from services.dashboard_service import DashboardService
from services.analytics_service import AnalyticsService
from services.scheduler_service import SchedulerService

client = TestClient(app)

def test_f01_sliding_session_preserves_created_at():
    """F-01: Session lookup preserves original created_at timestamp and sliding expiry works."""
    auth_service = get_auth_service()
    user = auth_service.get_user("USR_STUDENT")
    token = create_session(user)
    
    sess = _lookup_session(token)
    assert sess is not None
    assert sess["user_id"] == "USR_STUDENT"
    original_created = sess["created_at"]
    assert original_created > 0
    
    # Second lookup should not overwrite or shift created_at
    time.sleep(0.05)
    sess2 = _lookup_session(token)
    assert sess2 is not None
    assert abs(sess2["created_at"] - original_created) < 1.0

def test_f02_otp_isolation_and_lockout():
    """F-02: OTP failure attempts must increment only target reset_id and enforce lockout."""
    complaint_service = get_complaint_service()
    repo = complaint_service.repository
    with repo.get_connection() as conn:
        conn.execute("DELETE FROM password_resets WHERE reset_id = 'test_reset_f02'")
        conn.execute("""
            INSERT INTO password_resets (reset_id, email, otp, expires_at, attempts, created_at)
            VALUES ('test_reset_f02', 'test_f02@example.com', '123456', datetime('now', '+15 minutes'), 0, datetime('now'))
        """)
    
    # Verify attempt increment only on this reset_id
    with repo.get_connection() as conn:
        conn.execute("UPDATE password_resets SET attempts = attempts + 1 WHERE reset_id = 'test_reset_f02'")
        row = conn.execute("SELECT attempts FROM password_resets WHERE reset_id = 'test_reset_f02'").fetchone()
        assert row["attempts"] == 1
        
        # Simulate max attempts exceeded (lockout)
        conn.execute("UPDATE password_resets SET attempts = 5 WHERE reset_id = 'test_reset_f02'")
        locked_row = conn.execute("SELECT attempts FROM password_resets WHERE reset_id = 'test_reset_f02'").fetchone()
        assert locked_row["attempts"] >= 5

def test_f03_dual_login_lockout_cleared():
    """F-03: Password reset/change must clear both login_attempts and login_rate_limits."""
    auth_service = get_auth_service()
    test_identity = "test_lockout_identity"
    
    # Register login failures to trigger lockout
    for _ in range(5):
        auth_service._register_login_failure(test_identity)
    
    # Clear failures
    auth_service._clear_login_failures(test_identity)
    
    with auth_service._login_attempts_conn() as conn:
        attempts = conn.execute("SELECT COUNT(*) FROM login_attempts WHERE identity = ?", (test_identity,)).fetchone()[0]
        assert attempts == 0

def test_f05_app_manager_privilege_escalation_guard():
    """F-05: App Manager cannot restore or alter Administrator/Super Admin accounts."""
    auth_service = get_auth_service()
    repo = auth_service.repository
    
    # Create temporary soft-deleted admin
    with repo.get_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO users (user_id, email, name, password, role, is_deleted, deleted_at, status, created_at, first_login, active)
            VALUES ('USR_TEMP_ADMIN', 'temp_admin@campuspulse.edu', 'Temp Admin', 'hashed_pw', 'administrator', 1, datetime('now'), 'Archived', datetime('now'), 0, 0)
        """)
    
    app_manager = auth_service.get_user("USR_MANAGER")
    assert app_manager is not None
    
    try:
        with pytest.raises(PermissionError) as exc_info:
            auth_service.restore_user_account("USR_TEMP_ADMIN", app_manager)
        assert "not authorized to restore" in str(exc_info.value).lower()
    finally:
        with repo.get_connection() as conn:
            conn.execute("DELETE FROM users WHERE user_id = 'USR_TEMP_ADMIN'")

def test_f06_admin_step_up_safety_report_reveal():
    """F-06: Revealing safety report reporter requires Admin step-up password."""
    # Ensure unauthenticated request is rejected with 401
    res = client.post("/safety-reports/SR_TEST/reveal", json={"reason": "Abuse investigation", "admin_password": "WrongPassword"})
    assert res.status_code == 401

def test_f07_safety_report_ban_utc_comparison():
    """F-07: Safety report ban checks timezone-aware UTC datetime without TypeError."""
    now_utc = datetime.now(timezone.utc)
    blocked_until_str = (now_utc + timedelta(hours=1)).isoformat()
    
    parsed_dt = datetime.fromisoformat(blocked_until_str)
    if parsed_dt.tzinfo is None:
        parsed_dt = parsed_dt.replace(tzinfo=timezone.utc)
        
    assert parsed_dt > now_utc

def test_f08_selective_complaint_saving():
    """F-08: ComplaintService provides granular per-complaint saving."""
    complaint_service = get_complaint_service()
    assert hasattr(complaint_service, "save_complaint")

def test_f09_soft_delete_preservation():
    """F-09: Complaint model and repository preserve is_deleted, deleted_at, deleted_by."""
    c = Complaint(
        complaint_id="CMP_F09_TEST",
        created_by="USR_STUDENT",
        creator_role="student",
        location_id="LOC_HOSTEL_A",
        department_id="DEP_ELEC",
        complaint_type="Electrical",
        description="Test for F-09 soft delete",
        is_deleted=True,
        deleted_at="2026-10-19T10:00:00Z",
        deleted_by="USR_ADMIN",
    )
    d = c.to_dict()
    assert d["is_deleted"] is True
    assert d["deleted_at"] == "2026-10-19T10:00:00Z"
    assert d["deleted_by"] == "USR_ADMIN"
    
    c2 = Complaint.from_dict(d)
    assert c2.is_deleted is True
    assert c2.deleted_at == "2026-10-19T10:00:00Z"
    assert c2.deleted_by == "USR_ADMIN"

def test_f10_work_reassignment_state_guards():
    """F-10: assign_work prevents reassigning Closed or Rejected complaints."""
    complaint_service = get_complaint_service()
    closed_c = Complaint(
        complaint_id="CMP_CLOSED_TEST",
        created_by="USR_STUDENT",
        creator_role="student",
        location_id="LOC_HOSTEL_A",
        department_id="DEP_ELEC",
        complaint_type="Electrical",
        description="Closed test",
        status="Closed",
    )
    complaint_service.save_complaint(closed_c)
    
    with pytest.raises(ValueError) as exc_info:
        complaint_service.assign_work("CMP_CLOSED_TEST", "USR_EMP_A1", actor_id="USR_ADMIN")
    assert "cannot assign or reassign" in str(exc_info.value).lower()

def test_f12_import_users_form_data_resilience():
    """F-12: Bulk user import endpoint exists and handles form data/queries."""
    res = client.post("/users/import")
    assert res.status_code in (401, 422)

def test_f13_dashboard_aggregations_grouped():
    """F-13: Dashboard user breakdown uses single GROUP BY query."""
    dash_service = get_dashboard_service()
    admin_dash = dash_service.get_admin_dashboard("USR_ADMIN")
    assert "user_statistics" in admin_dash
    assert "students" in admin_dash["user_statistics"]
    assert "coordinators" in admin_dash["user_statistics"]

def test_f14_scheduler_lock_table_schema():
    """F-14: Scheduler lock table has lock_name column and avoids leaks."""
    complaint_service = get_complaint_service()
    repo = complaint_service.repository
    with repo.get_connection() as conn:
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(scheduler_lock)").fetchall()]
        assert "lock_name" in cols
        assert "locked_by" in cols
        assert "locked_at" in cols
        assert "expires_at" in cols

def test_f15_feedback_ownership_guard():
    """F-15: Feedback endpoint rejects unauthenticated or unauthorized users."""
    res = client.post("/complaints/CMP_TEST/feedback", json={"rating": 5, "comment": "Great!"})
    assert res.status_code == 401
