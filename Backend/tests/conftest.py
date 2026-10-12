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
            shutil.copy2(BASE_DB_PATH, TEST_DB_PATH)
        os.environ["DATABASE_PATH"] = TEST_DB_PATH
        from api.dependencies import _service_cache
        _service_cache.clear()
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
