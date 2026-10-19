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


def _cleanup_isolated_db():
    for ext in ["", "-wal", "-shm", "-journal"]:
        target = TEST_DB_PATH + ext
        if os.path.exists(target):
            try:
                os.remove(target)
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
                conn.commit()
    except Exception:
        pass
    yield


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
