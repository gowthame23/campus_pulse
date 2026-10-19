"""Campus Pulse — Unified Database Connection & Adapter Layer

Provides transparent, production-ready PostgreSQL connection pooling via psycopg v3,
automatic query dialect translation (qmark '?' to format '%s', PRAGMA handling,
and ON CONFLICT conversion), with seamless, zero-regression SQLite fallback.
"""

import os
import re
import sqlite3
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

BACKEND_DIR = Path(__file__).resolve().parent.parent

try:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg_pool import ConnectionPool
except ImportError:
    psycopg = None
    dict_row = None
    ConnectionPool = None


def get_db_path() -> str:
    """Returns configured SQLite database path for fallback/development."""
    raw = os.environ.get("DATABASE_PATH", "storage/campus_pulse.db")
    p = Path(raw)
    if not p.is_absolute():
        p = (BACKEND_DIR / p).resolve()
    return str(p)


def is_postgres_configured() -> bool:
    """Check if PostgreSQL environment is enabled and configured."""
    engine = os.environ.get("DB_ENGINE", "").lower()
    if engine == "sqlite":
        return False
    if engine in ("postgres", "postgresql"):
        return True
    db_url = os.environ.get("DATABASE_URL", "").lower()
    if db_url.startswith("postgres://") or db_url.startswith("postgresql://"):
        return True
    if os.environ.get("POSTGRES_DB") and (os.environ.get("POSTGRES_HOST") or os.environ.get("PGHOST")):
        return True
    return False


def get_pg_conninfo() -> str:
    """Constructs a standard PostgreSQL connection URI from environment variables."""
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = "postgresql://" + db_url[len("postgres://"):]
        return db_url

    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "postgres")
    host = os.environ.get("POSTGRES_HOST", os.environ.get("PGHOST", "localhost"))
    port = os.environ.get("POSTGRES_PORT", os.environ.get("PGPORT", "5432"))
    dbname = os.environ.get("POSTGRES_DB", "campuspulse")
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


# Global connection pool lock & instance
_pg_pool: Optional[Any] = None
_pool_lock = threading.Lock()


def get_pg_pool() -> Any:
    """Lazy initialize and return the global PostgreSQL ConnectionPool."""
    global _pg_pool
    if not psycopg or not ConnectionPool:
        raise RuntimeError("psycopg and psycopg-pool packages are required for PostgreSQL mode.")

    if _pg_pool is None:
        with _pool_lock:
            if _pg_pool is None:
                conninfo = get_pg_conninfo()
                min_size = int(os.environ.get("DB_POOL_MIN", "2"))
                max_size = int(os.environ.get("DB_POOL_MAX", "20"))
                _pg_pool = ConnectionPool(
                    conninfo=conninfo,
                    min_size=min_size,
                    max_size=max_size,
                    open=True,
                    kwargs={"row_factory": dict_row}
                )
    return _pg_pool


def close_pg_pool():
    """Cleanly close the global PostgreSQL ConnectionPool on application shutdown."""
    global _pg_pool
    with _pool_lock:
        if _pg_pool is not None:
            _pg_pool.close()
            _pg_pool = None


def translate_sqlite_to_pg(sql: str) -> str:
    """Translate SQLite-specific SQL syntax into PostgreSQL equivalents."""
    s = sql.strip()
    # 1. Strip or safe no-op for PRAGMA statements
    if re.match(r"^PRAGMA\s+", s, re.I):
        return "SELECT 1"

    # 2. INSERT OR IGNORE -> ON CONFLICT DO NOTHING
    if re.search(r"\bINSERT\s+OR\s+IGNORE\s+INTO\b", s, re.I):
        s = re.sub(r"\bINSERT\s+OR\s+IGNORE\s+INTO\b", "INSERT INTO", s, flags=re.I)
        if "ON CONFLICT" not in s.upper():
            s = s.rstrip(";") + " ON CONFLICT DO NOTHING"

    # 3. INSERT OR REPLACE -> INSERT INTO ...
    if re.search(r"\bINSERT\s+OR\s+REPLACE\s+INTO\b", s, re.I):
        s = re.sub(r"\bINSERT\s+OR\s+REPLACE\s+INTO\b", "INSERT INTO", s, flags=re.I)

    # 4. datetime('now') and date('now')
    s = re.sub(r"\bdatetime\s*\(\s*['\"]now['\"]\s*\)", "CURRENT_TIMESTAMP", s, flags=re.I)
    s = re.sub(r"\bdate\s*\(\s*['\"]now['\"]\s*\)", "CURRENT_DATE", s, flags=re.I)

    # 5. strftime date formatting
    s = re.sub(r"\bstrftime\s*\(\s*'%Y-%m'\s*,\s*([^)]+)\)", r"to_char(\1::timestamp, 'YYYY-MM')", s, flags=re.I)
    s = re.sub(r"\bstrftime\s*\(\s*'%Y-%m-%d'\s*,\s*([^)]+)\)", r"to_char(\1::timestamp, 'YYYY-MM-DD')", s, flags=re.I)

    # 6. sqlite_master table references
    s = re.sub(r"\bsqlite_master\b", "information_schema.tables", s, flags=re.I)

    # 7. Convert SQLite '?' parameters to PostgreSQL '%s' while escaping literal '%'
    parts = s.split("?")
    if len(parts) > 1:
        escaped_parts = [p.replace("%", "%%") for p in parts]
        s = "%s".join(escaped_parts)
    return s


class RowProxy(dict):
    """Row wrapper emulating sqlite3.Row supporting both key ('id') and index (0) access."""
    def __init__(self, d: Dict[str, Any], keys_order: Optional[List[str]] = None):
        super().__init__(d)
        self._keys = keys_order or list(d.keys())

    def __getitem__(self, item: Union[str, int]) -> Any:
        if isinstance(item, int):
            return super().__getitem__(self._keys[item])
        return super().__getitem__(item)

    def get(self, key: Union[str, int], default: Any = None) -> Any:
        if isinstance(key, int):
            try:
                return super().__getitem__(self._keys[key])
            except (IndexError, KeyError):
                return default
        return super().get(key, default)

    def keys(self) -> List[str]:
        return self._keys


class PostgresCursorWrapper:
    """Wraps psycopg Cursor to provide sqlite3.Row-like output and query translation."""
    def __init__(self, cursor: Any):
        self._cur = cursor

    def execute(self, query: str, params: Any = None) -> "PostgresCursorWrapper":
        pg_query = translate_sqlite_to_pg(query)
        if params is not None:
            if isinstance(params, (list, tuple)):
                self._cur.execute(pg_query, params)
            elif isinstance(params, dict):
                self._cur.execute(pg_query, params)
            else:
                self._cur.execute(pg_query, (params,))
        else:
            self._cur.execute(pg_query)
        return self

    def executemany(self, query: str, params_seq: Any) -> "PostgresCursorWrapper":
        pg_query = translate_sqlite_to_pg(query)
        self._cur.executemany(pg_query, params_seq)
        return self

    def fetchone(self) -> Optional[RowProxy]:
        r = self._cur.fetchone()
        if r is None:
            return None
        keys = [desc[0] for desc in self._cur.description] if self._cur.description else list(r.keys())
        return RowProxy(r, keys)

    def fetchall(self) -> List[RowProxy]:
        rows = self._cur.fetchall()
        if not rows:
            return []
        keys = [desc[0] for desc in self._cur.description] if self._cur.description else list(rows[0].keys())
        return [RowProxy(r, keys) for r in rows]

    def fetchmany(self, size: Optional[int] = None) -> List[RowProxy]:
        rows = self._cur.fetchmany(size)
        if not rows:
            return []
        keys = [desc[0] for desc in self._cur.description] if self._cur.description else list(rows[0].keys())
        return [RowProxy(r, keys) for r in rows]

    @property
    def description(self) -> Any:
        return self._cur.description

    @property
    def rowcount(self) -> int:
        return self._cur.rowcount

    @property
    def lastrowid(self) -> Optional[int]:
        return getattr(self._cur, "lastrowid", None)

    def close(self):
        self._cur.close()

    def __enter__(self) -> "PostgresCursorWrapper":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class PostgresConnectionWrapper:
    """Wraps psycopg Connection checked out from pool with sqlite3-compatible interface."""
    def __init__(self, raw_conn: Any, pool: Optional[Any] = None):
        self._conn = raw_conn
        self._pool = pool
        self._in_context = False

    def cursor(self) -> PostgresCursorWrapper:
        return PostgresCursorWrapper(self._conn.cursor())

    def execute(self, query: str, params: Any = None) -> PostgresCursorWrapper:
        cur = self.cursor()
        cur.execute(query, params)
        return cur

    def executemany(self, query: str, params_seq: Any) -> PostgresCursorWrapper:
        cur = self.cursor()
        cur.executemany(query, params_seq)
        return cur

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        if self._pool is not None:
            try:
                self._pool.putconn(self._conn)
            except Exception:
                self._conn.close()
        else:
            self._conn.close()

    @property
    def row_factory(self) -> Any:
        return dict_row

    @row_factory.setter
    def row_factory(self, val: Any):
        pass  # psycopg dict_row is automatically used

    def __enter__(self) -> "PostgresConnectionWrapper":
        self._in_context = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._in_context = False
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        # Auto-release if opened via with get_db_connection()
        self.close()


def get_db_connection(db_path: Optional[str] = None) -> Any:
    """
    Main database connection factory for Campus Pulse.
    Returns a pooled PostgreSQL connection proxy if PostgreSQL is configured;
    otherwise returns a configured SQLite Connection with foreign keys enabled.
    """
    if is_postgres_configured():
        pool = get_pg_pool()
        raw_conn = pool.getconn()
        return PostgresConnectionWrapper(raw_conn, pool)

    # SQLite connection fallback
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def check_db_connectivity() -> Dict[str, Any]:
    """Health check verifying live database connectivity."""
    engine = "postgresql" if is_postgres_configured() else "sqlite"
    try:
        conn = get_db_connection()
        try:
            cur = conn.execute("SELECT 1 as alive")
            row = cur.fetchone()
            is_alive = bool(row and (row["alive"] == 1 or row[0] == 1))
            return {
                "status": "healthy" if is_alive else "unhealthy",
                "engine": engine,
                "connected": is_alive,
            }
        finally:
            conn.close()
    except Exception as e:
        return {
            "status": "error",
            "engine": engine,
            "connected": False,
            "error": str(e),
        }
