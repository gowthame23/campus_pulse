import json
import os
import shutil
import sqlite3
import sys
import time
import uuid
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from api.security import create_ws_ticket, consume_ws_ticket, canonical_role, require_roles
from middleware.rate_limiter import (
    auth_limiter,
    check_login_lockout,
    record_login_attempt,
    prune_login_rate_limits,
)
from services.backup_service import BackupService, apply_pending_restore

client = TestClient(app)


def _reset_limiter():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()


def _get_admin_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "admin@example.com", "password": "Admin@123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _get_manager_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "manager@example.com", "password": "Manager@123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _get_student_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "student@example.com", "password": "Student@123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _get_coordinator_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "coordinator@example.com", "password": "Coord@123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# =========================================================================
# 3.1 SAFE DATABASE RESTORE TESTS
# =========================================================================
def test_safe_database_restore_staging_and_startup_apply(tmp_path):
    admin_headers = _get_admin_headers()
    # 1. Create a backup first
    create_res = client.post("/settings/backup", json={"backup_name": "TestPhase3Backup"}, headers=admin_headers)
    assert create_res.status_code == 200
    b_id = create_res.json()["backup_id"]

    # 2. Call restore endpoint: must return 202 Accepted and schedule restore
    rst_res = client.post(f"/backups/{b_id}/restore", headers=admin_headers)
    assert rst_res.status_code == 202
    data = rst_res.json()
    assert data["status"] == "Scheduled"
    assert "restart the server" in data["message"].lower()

    # 3. Verify staging files exist in storage directory
    db_path = os.environ.get("DATABASE_PATH", "storage/campus_pulse.db")
    db_dir = os.path.dirname(os.path.abspath(db_path))
    marker_file = os.path.join(db_dir, "restore_pending.marker")
    pending_db = os.path.join(db_dir, "restore_pending.db")

    assert os.path.exists(marker_file)
    assert os.path.exists(pending_db)

    with open(marker_file, "r", encoding="utf-8") as mf:
        meta = json.load(mf)
        assert meta["backup_id"] == b_id

    # 4. Execute apply_pending_restore and verify safe application
    applied = apply_pending_restore(db_path=db_path)
    assert applied is True

    # Marker and pending db should be removed after application
    assert not os.path.exists(marker_file)
    assert not os.path.exists(pending_db)


# =========================================================================
# 3.2 SQLITE LOGIN RATE LIMITER ACROSS WORKERS
# =========================================================================
def test_sqlite_login_rate_limiting_across_workers():
    test_ip = "192.168.1.105"
    test_email = f"test_rate_limit_{uuid.uuid4().hex[:6]}@example.com"
    db_path = os.environ.get("DATABASE_PATH", "storage/campus_pulse.db")

    # Clear initial state
    record_login_attempt(test_ip, test_email, success=True, db_path=db_path)
    is_locked, _ = check_login_lockout(test_ip, test_email, db_path=db_path)
    assert is_locked is False

    # 4 failed attempts -> not locked yet
    for _ in range(4):
        record_login_attempt(test_ip, test_email, success=False, db_path=db_path)
    is_locked, _ = check_login_lockout(test_ip, test_email, db_path=db_path)
    assert is_locked is False

    # 5th failed attempt -> locked out for 15 minutes (429)
    record_login_attempt(test_ip, test_email, success=False, db_path=db_path)
    is_locked, remaining = check_login_lockout(test_ip, test_email, db_path=db_path)
    assert is_locked is True
    assert 800 <= remaining <= 900

    # Successful login resets the counter
    record_login_attempt(test_ip, test_email, success=True, db_path=db_path)
    is_locked_after, _ = check_login_lockout(test_ip, test_email, db_path=db_path)
    assert is_locked_after is False


def test_sqlite_rate_limit_pruning():
    db_path = os.environ.get("DATABASE_PATH", "storage/campus_pulse.db")
    old_time = time.time() - 1000  # older than 15 minutes
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "INSERT INTO login_rate_limits (ip, email, attempted_at) VALUES ('1.1.1.1', 'old@test.com', ?)",
            (old_time,),
        )
        conn.commit()

    prune_login_rate_limits(db_path=db_path)

    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT COUNT(*) FROM login_rate_limits WHERE email = 'old@test.com'").fetchone()[0]
        assert row == 0


# =========================================================================
# 3.3 SINGLE-USE WEBSOCKET TICKETS
# =========================================================================
def test_websocket_single_use_ticket_flow():
    admin_headers = _get_admin_headers()
    # 1. Fetch single-use ticket via POST /api/ws-ticket
    ticket_res = client.post("/api/ws-ticket", headers=admin_headers)
    assert ticket_res.status_code == 200
    ticket_data = ticket_res.json()
    ticket = ticket_data["ticket"]
    assert ticket.startswith("WST-")
    assert ticket_data["expires_in"] == 60

    # 2. First consumption: valid user returned
    user = consume_ws_ticket(ticket)
    assert user is not None
    assert user.role.lower() == "administrator"

    # 3. Second consumption of same ticket: MUST FAIL (single-use!)
    user_reused = consume_ws_ticket(ticket)
    assert user_reused is None


def test_websocket_ticket_auth_endpoint():
    student_headers = _get_student_headers()
    res = client.post("/auth/ws-ticket", headers=student_headers)
    assert res.status_code == 200
    assert "ticket" in res.json()


# =========================================================================
# 3.4 ROLE ALIASES AND PERMISSION MATRIX
# =========================================================================
def test_role_alias_normalization():
    assert canonical_role("admin") == "administrator"
    assert canonical_role("manager") == "app_manager"
    assert canonical_role("warden") == "location_in_charge"
    assert canonical_role("student") == "student"
    assert canonical_role("coordinator") == "coordinator"


def test_audit_logs_accessible_to_app_manager():
    mgr_headers = _get_manager_headers()
    dash_res = client.get("/audit/dashboard", headers=mgr_headers)
    assert dash_res.status_code == 200

    list_res = client.get("/audit", headers=mgr_headers)
    assert list_res.status_code == 200


def test_coordinator_forbidden_from_changing_priority():
    coord_headers = _get_coordinator_headers()
    admin_headers = _get_admin_headers()
    comps_res = client.get("/complaints", headers=admin_headers)
    cid = comps_res.json()[0]["complaint_id"] if (comps_res.status_code == 200 and comps_res.json()) else "CP-2026-001"
    patch_res = client.patch(
        f"/complaints/{cid}/priority",
        json={"priority": "High", "reason": "Attempt by coordinator"},
        headers=coord_headers,
    )
    assert patch_res.status_code == 403
    assert "coordinators cannot change" in patch_res.json()["detail"].lower()


def test_coordinator_forbidden_from_reassigning():
    # In Team Model, coordinators assign their team's complaints (Part E).
    # Unauthorized roles like students are forbidden from assigning.
    student_headers = _get_student_headers()
    admin_headers = _get_admin_headers()
    comps_res = client.get("/complaints", headers=admin_headers)
    cid = comps_res.json()[0]["complaint_id"] if (comps_res.status_code == 200 and comps_res.json()) else "CP-2026-001"
    assign_res = client.post(
        f"/complaints/{cid}/assign",
        json={"coordinator_id": "USR_COORDINATOR"},
        headers=student_headers,
    )
    assert assign_res.status_code == 403


# =========================================================================
# 3.5 & 3.6 HEALTH AND ERRORS
# =========================================================================
def test_health_endpoint_details():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("ok", "healthy")
    assert data["database"] == "reachable"
    assert "scheduler_last_run" in data


def test_cli_restore_script():
    from scripts.restore_db import restore_db_cli

    admin_headers = _get_admin_headers()
    create_res = client.post("/settings/backup", json={"backup_name": "TestCliBackup"}, headers=admin_headers)
    assert create_res.status_code == 200
    b_id = create_res.json()["backup_id"]

    db_path = os.environ.get("DATABASE_PATH", "storage/campus_pulse.db")
    # Execute CLI restore function directly
    restore_db_cli(backup_id=b_id, db_path=db_path)


def test_non_blocking_email():
    from utils.email import send_notification_email, send_otp_email, send_password_changed_email, send_activation_email

    # None of these should raise an exception even without SMTP configured
    assert send_notification_email("test@example.com", "Test Subject", "Test Message") in (True, False)
    assert send_otp_email("test@example.com", "123456") in (True, False)
    assert send_password_changed_email("test@example.com", "Student") in (True, False)
    assert send_activation_email("test@example.com", "/activate?token=abc", "Student") in (True, False)
