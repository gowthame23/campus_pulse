import os
import sqlite3


from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def get_db_path() -> str:
    """Returns the configured database path, respecting DATABASE_PATH environment variable."""
    raw = os.environ.get("DATABASE_PATH", "storage/campus_pulse.db")
    p = Path(raw)
    if not p.is_absolute():
        p = (BACKEND_DIR / p).resolve()
    return str(p)


def get_db_connection(db_path: str = None) -> sqlite3.Connection:
    """Returns a SQLite connection with Foreign Key enforcement enabled and Row factory configured."""
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn
