import os
import sys
import uuid
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from api.main import app
from api.dependencies import get_db_path, _service_cache
from services.auth_service import AuthService
from models.user import User
from utils.passwords import hash_password, verify_password, is_password_hash
from middleware.rate_limiter import auth_limiter

client = TestClient(app, raise_server_exceptions=False)


def _cleanup_test_user(user_id: str):
    db_path = get_db_path()
    svc = AuthService(db_path=db_path)
    with svc._connect() as conn:
        conn.execute("DELETE FROM user_sessions WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM student_profiles WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()


def _clear_rate_limits():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()
    _service_cache.clear()


def test_password_change_complete_persistence_lifecycle():
    """
    Covers exact requirements:
    1. Create a test student with password Student@123.
    2. Verify that the old password works.
    3. Change the password to Student@1234.
    4. Verify that the change succeeds.
    5. Reload the user from the database in a fresh database session.
    6. Verify that Student@1234 authenticates successfully.
    7. Verify that Student@123 is rejected.
    8. Verify that the password change persists after the application service/database session is recreated.
    9. Verify that existing sessions are invalidated.
    """
    _clear_rate_limits()
    uid = uuid.uuid4().hex[:8]
    user_id = f"USR_REG_{uid}"
    email = f"test_reg_student_{uid}@campuspulse.edu"

    db_path = get_db_path()
    svc = AuthService(db_path=db_path)

    # 1. Create a test student with password Student@123 (never use real student credentials)
    test_student = User(
        user_id=user_id,
        name=f"Regression Student {uid}",
        email=email,
        password=hash_password("Student@123"),
        role="student",
        first_login=False,
        status="Active",
        roll_number=f"ROLL_{uid}",
    )
    svc.save_user(test_student)

    try:
        # 2. Verify that the old password works and obtain session token
        login_res = client.post("/auth/login", json={"username": email, "password": "Student@123"})
        assert login_res.status_code == 200, f"Old password login failed: {login_res.text}"
        old_token = login_res.json()["access_token"]
        headers_old_session = {"Authorization": f"Bearer {old_token}"}

        # Verify old session works
        me_res = client.get("/auth/me", headers=headers_old_session)
        assert me_res.status_code == 200
        assert me_res.json()["user_id"] == user_id

        # 3. Change the password to Student@1234
        change_res = client.post(
            "/auth/change-password",
            json={
                "current_password": "Student@123",
                "new_password": "Student@1234",
                "confirm_password": "Student@1234",
            },
            headers=headers_old_session,
        )
        # 4. Verify that the change succeeds
        assert change_res.status_code == 200, f"Password change failed: {change_res.text}"

        # 5. Reload the user from the database in a fresh database session
        _service_cache.clear()
        fresh_svc = AuthService(db_path=db_path)
        reloaded_user = fresh_svc.get_user(user_id)
        assert reloaded_user is not None
        assert is_password_hash(reloaded_user.password)
        assert verify_password("Student@1234", reloaded_user.password)
        assert not verify_password("Student@123", reloaded_user.password)

        # 6. Verify that Student@1234 authenticates successfully
        _clear_rate_limits()
        new_login = client.post("/auth/login", json={"username": email, "password": "Student@1234"})
        assert new_login.status_code == 200, f"New password login failed: {new_login.text}"
        new_token = new_login.json()["access_token"]
        headers_new_session = {"Authorization": f"Bearer {new_token}"}

        new_me = client.get("/auth/me", headers=headers_new_session)
        assert new_me.status_code == 200
        assert new_me.json()["user_id"] == user_id

        # 7. Verify that Student@123 is rejected
        _clear_rate_limits()
        old_login_fail = client.post("/auth/login", json={"username": email, "password": "Student@123"})
        assert old_login_fail.status_code == 401

        # 8. Verify that the password change persists after application service/database session is recreated
        _service_cache.clear()
        recreated_svc = AuthService(db_path=db_path)
        recreated_auth = recreated_svc.authenticate(email, "Student@1234")
        assert recreated_auth.user_id == user_id

        with pytest.raises(ValueError, match="Invalid credentials"):
            recreated_svc.authenticate(email, "Student@123")

        # 9. Verify that existing sessions were invalidated
        old_session_check = client.get("/auth/me", headers=headers_old_session)
        assert old_session_check.status_code == 401, "Old session token must be revoked after password change"

    finally:
        _cleanup_test_user(user_id)


def test_failed_password_change_does_not_corrupt_existing_password():
    """
    Covers requirement 10:
    Verify that a failed password change does not corrupt the existing password.
    """
    _clear_rate_limits()
    uid = uuid.uuid4().hex[:8]
    user_id = f"USR_REG_FAIL_{uid}"
    email = f"test_fail_{uid}@campuspulse.edu"

    db_path = get_db_path()
    svc = AuthService(db_path=db_path)

    test_student = User(
        user_id=user_id,
        name=f"Fail Test Student {uid}",
        email=email,
        password=hash_password("Student@123"),
        role="student",
        first_login=False,
        status="Active",
        roll_number=f"ROLL_F_{uid}",
    )
    svc.save_user(test_student)

    try:
        # Authenticate with initial password
        login_res = client.post("/auth/login", json={"username": email, "password": "Student@123"})
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Attempt 1: Wrong current password
        res_wrong_curr = client.post(
            "/auth/change-password",
            json={
                "current_password": "WrongPassword999!",
                "new_password": "Student@1234",
                "confirm_password": "Student@1234",
            },
            headers=headers,
        )
        assert res_wrong_curr.status_code == 400

        # Attempt 2: Password complexity violation (too short, no special char)
        res_simple = client.post(
            "/auth/change-password",
            json={
                "current_password": "Student@123",
                "new_password": "simple",
                "confirm_password": "simple",
            },
            headers=headers,
        )
        assert res_simple.status_code in (400, 422)

        # Attempt 3: Confirmation mismatch
        res_mismatch = client.post(
            "/auth/change-password",
            json={
                "current_password": "Student@123",
                "new_password": "Student@1234",
                "confirm_password": "Different@1234",
            },
            headers=headers,
        )
        assert res_mismatch.status_code == 400

        # Verify that original password STILL works and was NOT corrupted
        _clear_rate_limits()
        login_check = client.post("/auth/login", json={"username": email, "password": "Student@123"})
        assert login_check.status_code == 200, "Original password must remain intact after failed attempts"

    finally:
        _cleanup_test_user(user_id)


def test_another_student_password_remains_unchanged():
    """
    Covers requirement 11:
    Verify that another student's password remains unchanged.
    """
    _clear_rate_limits()
    uid_a = uuid.uuid4().hex[:8]
    uid_b = uuid.uuid4().hex[:8]
    user_id_a = f"USR_REG_A_{uid_a}"
    user_id_b = f"USR_REG_B_{uid_b}"
    email_a = f"student_a_{uid_a}@campuspulse.edu"
    email_b = f"student_b_{uid_b}@campuspulse.edu"

    db_path = get_db_path()
    svc = AuthService(db_path=db_path)

    student_a = User(
        user_id=user_id_a,
        name=f"Student A {uid_a}",
        email=email_a,
        password=hash_password("Student@123"),
        role="student",
        first_login=False,
        status="Active",
        roll_number=f"ROLL_A_{uid_a}",
    )
    student_b = User(
        user_id=user_id_b,
        name=f"Student B {uid_b}",
        email=email_b,
        password=hash_password("Student@123"),
        role="student",
        first_login=False,
        status="Active",
        roll_number=f"ROLL_B_{uid_b}",
    )
    svc.save_user(student_a)
    svc.save_user(student_b)

    try:
        # Student A logs in and changes password to Student@1234
        login_a = client.post("/auth/login", json={"username": email_a, "password": "Student@123"})
        assert login_a.status_code == 200
        token_a = login_a.json()["access_token"]

        change_a = client.post(
            "/auth/change-password",
            json={
                "current_password": "Student@123",
                "new_password": "Student@1234",
                "confirm_password": "Student@1234",
            },
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert change_a.status_code == 200

        # Verify Student B's password is completely untouched and Student@123 continues to authenticate
        _clear_rate_limits()
        login_b = client.post("/auth/login", json={"username": email_b, "password": "Student@123"})
        assert login_b.status_code == 200, "Student B must authenticate with original password Student@123"

        # Verify Student B CANNOT log in with Student A's new password
        _clear_rate_limits()
        login_b_wrong = client.post("/auth/login", json={"username": email_b, "password": "Student@1234"})
        assert login_b_wrong.status_code == 401

    finally:
        _cleanup_test_user(user_id_a)
        _cleanup_test_user(user_id_b)


def test_database_failure_does_not_produce_false_success():
    """
    Covers requirement 12:
    Verify that a database failure does not produce a false success response.
    """
    _clear_rate_limits()
    uid = uuid.uuid4().hex[:8]
    user_id = f"USR_REG_ERR_{uid}"
    email = f"test_err_{uid}@campuspulse.edu"

    db_path = get_db_path()
    svc = AuthService(db_path=db_path)

    test_student = User(
        user_id=user_id,
        name=f"Error Test Student {uid}",
        email=email,
        password=hash_password("Student@123"),
        role="student",
        first_login=False,
        status="Active",
        roll_number=f"ROLL_ERR_{uid}",
    )
    svc.save_user(test_student)

    try:
        login_res = client.post("/auth/login", json={"username": email, "password": "Student@123"})
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Mock save_user to simulate a database failure
        with patch.object(AuthService, "save_user", side_effect=Exception("Simulated SQLite write error")):
            change_res = client.post(
                "/auth/change-password",
                json={
                    "current_password": "Student@123",
                    "new_password": "Student@1234",
                    "confirm_password": "Student@1234",
                },
                headers=headers,
            )
            # Must NOT produce 200 OK
            assert change_res.status_code in (400, 500)

        # Confirm old password still works
        _clear_rate_limits()
        login_check = client.post("/auth/login", json={"username": email, "password": "Student@123"})
        assert login_check.status_code == 200

    finally:
        _cleanup_test_user(user_id)


def test_password_reset_persistence_and_hashing():
    """
    Covers password-reset flow persistence, hashing, session invalidation, and verification.
    """
    _clear_rate_limits()
    uid = uuid.uuid4().hex[:8]
    user_id = f"USR_REG_RST_{uid}"
    email = f"test_reset_{uid}@campuspulse.edu"

    db_path = get_db_path()
    svc = AuthService(db_path=db_path)

    test_student = User(
        user_id=user_id,
        name=f"Reset Student {uid}",
        email=email,
        password=hash_password("Student@123"),
        role="student",
        first_login=False,
        status="Active",
        roll_number=f"ROLL_RST_{uid}",
    )
    svc.save_user(test_student)

    try:
        # Verify initial login works
        login_res = client.post("/auth/login", json={"username": email, "password": "Student@123"})
        assert login_res.status_code == 200
        old_token = login_res.json()["access_token"]

        # Reset password via auth_service.reset_password
        updated_user = svc.reset_password(email, "Student@Reset123")
        assert updated_user is not None
        assert is_password_hash(updated_user.password)

        # Invalidate sessions
        from api.security import invalidate_user_sessions
        invalidate_user_sessions(user_id)

        # Verify old session token revoked
        me_check = client.get("/auth/me", headers={"Authorization": f"Bearer {old_token}"})
        assert me_check.status_code == 401

        # Verify fresh DB instance authenticates new password
        _clear_rate_limits()
        fresh_svc = AuthService(db_path=db_path)
        auth_user = fresh_svc.authenticate(email, "Student@Reset123")
        assert auth_user.user_id == user_id

        # Verify old password rejected
        _clear_rate_limits()
        old_login = client.post("/auth/login", json={"username": email, "password": "Student@123"})
        assert old_login.status_code == 401

        # Verify new password logs in via API
        _clear_rate_limits()
        new_login = client.post("/auth/login", json={"username": email, "password": "Student@Reset123"})
        assert new_login.status_code == 200

    finally:
        _cleanup_test_user(user_id)
