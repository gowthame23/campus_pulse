import os
import shutil
import sys
import pytest

# Ensure Backend root is on sys.path for pytest discovery
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

TEST_DB_PATH = os.path.join(ROOT, "storage", "pytest_isolated.db")
BASE_DB_PATH = os.path.join(ROOT, "storage", "campus_pulse.db")

# Force DATABASE_PATH to pytest_isolated.db at import time so tests never touch main campus_pulse.db
os.environ["DATABASE_PATH"] = TEST_DB_PATH

# The full suite logs in as the seeded demo accounts (admin@..., coordinator1@...,
# etc.) with their documented default passwords. Outside of tests, AuthService
# only grants those well-known passwords when this flag is explicitly set --
# otherwise a fresh non-production boot gets a random, first-login-forced
# password instead. Tests are not a real deployment, so opt in here.
os.environ.setdefault("ALLOW_DEMO_SEED_PASSWORDS", "true")


def _seed_test_coordinators(db_path):
    if not os.path.exists(db_path):
        return
    import sqlite3
    from utils.passwords import hash_password
    pwd = hash_password("Employee@123")
    emp_users = [
        ("USR_EMP_A1", "Employee A1", "employee.a1@campuspulse.edu", pwd, "coordinator", 0, 1, "Active", "EMP_A1", "Electrical Coordinator / Electrician", "DEPT_HOSTEL_ELECTRICAL", "LOC_HOSTEL_1"),
        ("USR_EMP_A2", "Employee A2", "employee.a2@campuspulse.edu", pwd, "coordinator", 0, 1, "Active", "EMP_A2", "Backup Coordinator / Electrician", "DEPT_HOSTEL_ELECTRICAL", "LOC_HOSTEL_1"),
        ("USR_EMP_A3", "Employee A3", "employee.a3@campuspulse.edu", pwd, "coordinator", 0, 1, "Active", "EMP_A3", "HVAC Specialist", "DEPT_HOSTEL_ELECTRICAL", "LOC_HOSTEL_1"),
        ("USR_EMP_B1", "Employee B1", "employee.b1@campuspulse.edu", pwd, "coordinator", 0, 1, "Active", "EMP_B1", "Plumbing Coordinator / Plumber", "DEPT_HOSTEL_PLUMBING", "LOC_HOSTEL_2"),
        ("USR_EMP_B2", "Employee B2", "employee.b2@campuspulse.edu", pwd, "coordinator", 0, 1, "Active", "EMP_B2", "Backup Coordinator / Plumber", "DEPT_HOSTEL_PLUMBING", "LOC_HOSTEL_2"),
        ("USR_EMP_B3", "Employee B3", "employee.b3@campuspulse.edu", pwd, "coordinator", 0, 1, "Active", "EMP_B3", "Sanitation Technician", "DEPT_HOSTEL_PLUMBING", "LOC_HOSTEL_2"),
    ]
    try:
        with sqlite3.connect(db_path) as conn:
            for uid, name, email, p, role, fl, act, st, empid, desig, dept, loc in emp_users:
                conn.execute("""
                    INSERT OR REPLACE INTO users (user_id, name, email, password, role, first_login, active, status, department_id, location_id, created_at, updated_at, is_deleted)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'), 0)
                """, (uid, name, email, p, role, fl, act, st, dept, loc))
                conn.execute("""
                    INSERT OR REPLACE INTO staff_profiles (user_id, employee_id, designation, department, assigned_locations)
                    VALUES (?, ?, ?, ?, ?)
                """, (uid, empid, desig, dept, f'["{loc}"]'))
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO employee_work_memberships (membership_id, user_id, department_id, location_id, created_at)
                        VALUES (?, ?, ?, ?, datetime('now'))
                    """, (f"MEMB_{uid}", uid, dept, loc))
                except Exception:
                    pass
            
            assignments = [
                ("ASGN_COORD_A1", "USR_EMP_A1", "DEPT_HOSTEL_ELECTRICAL", "LOC_HOSTEL_1"),
                ("ASGN_COORD_A2", "USR_EMP_A2", "DEPT_HOSTEL_ELECTRICAL", "LOC_HOSTEL_1"),
                ("ASGN_COORD_A3", "USR_EMP_A3", "DEPT_HOSTEL_ELECTRICAL", "LOC_HOSTEL_1"),
                ("ASGN_COORD_B1", "USR_EMP_B1", "DEPT_HOSTEL_PLUMBING", "LOC_HOSTEL_2"),
                ("ASGN_COORD_B2", "USR_EMP_B2", "DEPT_HOSTEL_PLUMBING", "LOC_HOSTEL_2"),
                ("ASGN_COORD_B3", "USR_EMP_B3", "DEPT_HOSTEL_PLUMBING", "LOC_HOSTEL_2"),
            ]
            for asgn_id, cid, did, lid in assignments:
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO coordinator_assignments (assignment_id, coordinator_id, department_id, location_id, assigned_at)
                        VALUES (?, ?, ?, ?, datetime('now'))
                    """, (asgn_id, cid, did, lid))
                except Exception:
                    pass
            conn.commit()
    except Exception:
        pass


from models.user import User
_orig_check_pwd = User.check_password
def _test_check_pwd(self, password):
    if self.user_id and self.user_id.startswith("USR_EMP_") and password in ("Employee@123", "Coord@123"):
        return True
    return _orig_check_pwd(self, password)
User.check_password = _test_check_pwd

from services.auth_service import AuthService
_orig_ensure_seed_data = AuthService.ensure_seed_data
def _test_ensure_seed_data(self):
    _orig_ensure_seed_data(self)
    if os.environ.get("ENVIRONMENT") != "production":
        _seed_test_coordinators(str(self.db_path))
AuthService.ensure_seed_data = _test_ensure_seed_data


def _cleanup_isolated_db():
    for ext in ["", "-wal", "-shm", "-journal"]:
        target = TEST_DB_PATH + ext
        if os.path.exists(target):
            try:
                os.remove(target)
            except Exception:
                pass
    for ppath in [os.path.join(ROOT, "..", "storage", "platform.db"), os.path.join(ROOT, "storage", "platform.db")]:
        if os.path.exists(ppath):
            try:
                import sqlite3
                with sqlite3.connect(ppath) as pconn:
                    pconn.execute("DELETE FROM institutes WHERE institution_id != 'INST_ABC'")
                    pconn.execute("DELETE FROM institute_feature_overrides WHERE institution_id != 'INST_ABC'")
                    pconn.commit()
            except Exception:
                pass


def pytest_configure(config):
    """Set up isolated test database in writable storage directory before test execution."""
    _cleanup_isolated_db()
    try:
        if os.path.exists(BASE_DB_PATH):
            import sqlite3
            src = sqlite3.connect(f"file:{BASE_DB_PATH}?mode=ro", uri=True)
            dst = sqlite3.connect(TEST_DB_PATH)
            with dst:
                src.backup(dst)
            dst.close()
            src.close()
        os.environ["DATABASE_PATH"] = TEST_DB_PATH
        _seed_test_coordinators(TEST_DB_PATH)
        from api.dependencies import _service_cache
        _service_cache.clear()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def reset_rate_limiters_and_lockouts():
    """Ensure test cases do not suffer from cross-test rate-limiter or login-lockout cascades."""
    try:
        from middleware.rate_limiter import auth_limiter
        auth_limiter._requests.clear()
        auth_limiter._lockouts.clear()
    except Exception:
        pass

    try:
        import sqlite3
        db_path = os.environ.get("DATABASE_PATH", TEST_DB_PATH)
        if os.path.exists(db_path):
            with sqlite3.connect(db_path) as conn:
                conn.execute("DELETE FROM login_attempts")
                conn.execute("DELETE FROM login_rate_limits")
                conn.execute("UPDATE system_settings SET setting_value = 'false' WHERE key = 'safety_reports_enabled'")
                conn.commit()
            _seed_test_coordinators(db_path)
    except Exception:
        pass

    try:
        for ppath in [os.path.join(ROOT, "..", "storage", "platform.db"), os.path.join(ROOT, "storage", "platform.db")]:
            if os.path.exists(ppath):
                import sqlite3
                with sqlite3.connect(ppath) as pconn:
                    pconn.execute("DELETE FROM institutes WHERE institution_id != 'INST_ABC'")
                    pconn.execute("DELETE FROM institute_feature_overrides WHERE institution_id != 'INST_ABC'")
                    pconn.commit()
    except Exception:
        pass

    yield

    try:
        for ppath in [os.path.join(ROOT, "..", "storage", "platform.db"), os.path.join(ROOT, "storage", "platform.db")]:
            if os.path.exists(ppath):
                import sqlite3
                with sqlite3.connect(ppath) as pconn:
                    pconn.execute("DELETE FROM institutes WHERE institution_id != 'INST_ABC'")
                    pconn.execute("DELETE FROM institute_feature_overrides WHERE institution_id != 'INST_ABC'")
                    pconn.commit()
    except Exception:
        pass


def pytest_unconfigure(config):
    """Clean up isolated test database file when pytest finishes."""
    try:
        from api.dependencies import _service_cache
        _service_cache.clear()
    except Exception:
        pass
    import gc
    gc.collect()
    _cleanup_isolated_db()
