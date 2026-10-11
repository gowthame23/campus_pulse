"""Campus Pulse — Idempotent Database Migrations

Automatically checks existing SQLite schema at startup, adds required columns,
creates operational tables, normalizes priorities, and ensures data consistency
without dropping or altering existing columns.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from core.constants import (
    INACTIVE_STATUSES,
    PRIORITIES,
    SLA_HOURS,
    STATUS_SUBMITTED,
    normalize_priority,
)
from utils.logger import get_logger

logger = get_logger(__name__)


def run_migrations(db_path: str = "storage/campus_pulse.db"):
    """Run all idempotent migrations on the specified database path."""
    db_file = Path(db_path)
    if not db_file.exists():
        # Will be created on first connection
        db_file.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    try:
        # Enable WAL mode for high concurrency
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA foreign_keys = OFF;")  # Disable during DDL modifications

        _migrate_complaints_table(conn)
        _migrate_users_table(conn)
        _migrate_attachments_table(conn)
        _migrate_coordinator_assignments_table(conn)
        _migrate_locations_table(conn)
        _migrate_operational_tables(conn)
        _migrate_push_subscriptions_table(conn)
        _migrate_lost_found_items_table(conn)
        _normalize_priorities_and_deadlines(conn)
        _reroute_warden_assigned_open_complaints(conn)

        conn.commit()
        logger.info("Database migrations completed successfully.")
    except Exception as err:
        conn.rollback()
        logger.error(f"Migration error: {err}")
        raise err
    finally:
        conn.close()


def _get_existing_columns(conn: sqlite3.Connection, table_name: str) -> set:
    """Return a set of column names currently present in table_name."""
    cursor = conn.execute(f"PRAGMA table_info({table_name});")
    return {row["name"] for row in cursor.fetchall()}


def _migrate_complaints_table(conn: sqlite3.Connection):
    """Ensure complaints table exists and possesses all lifecycle tracking columns."""
    # Ensure table exists first if fresh DB
    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id TEXT PRIMARY KEY,
            created_by TEXT NOT NULL,
            creator_role TEXT NOT NULL,
            location_id TEXT NOT NULL,
            department_id TEXT NOT NULL,
            complaint_type TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            assigned_to TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            resolved_at TEXT,
            verification_due_at TEXT,
            reopen_count INTEGER NOT NULL DEFAULT 0,
            auto_closed INTEGER NOT NULL DEFAULT 0,
            escalated INTEGER NOT NULL DEFAULT 0,
            admin_notified INTEGER NOT NULL DEFAULT 0,
            resolution_notes TEXT NOT NULL DEFAULT '',
            verification_reports TEXT NOT NULL DEFAULT '[]',
            history TEXT NOT NULL DEFAULT '[]',
            archived INTEGER NOT NULL DEFAULT 0,
            priority TEXT NOT NULL DEFAULT 'Medium',
            category TEXT,
            visibility_type TEXT NOT NULL DEFAULT 'Private',
            attachment_url TEXT,
            title TEXT NOT NULL DEFAULT ''
        );
    """)

    existing_cols = _get_existing_columns(conn, "complaints")

    # Mapping of column_name -> SQL type definition
    new_columns = {
        "sla_deadline": "TEXT",
        "assigned_at": "TEXT",
        "started_at": "TEXT",
        "auto_assigned": "INTEGER DEFAULT 0",
        "blocked_reason": "TEXT",
        "blocked_until": "TEXT",
        "blocked_at": "TEXT",
        "sla_reminders_sent": "INTEGER DEFAULT 0",
        "escalation_level": "INTEGER DEFAULT 0",
        "warden_escalation_level": "INTEGER DEFAULT 0",
        "team_location_id": "TEXT",
        "team_department_id": "TEXT",
        "is_urgent": "INTEGER DEFAULT 0",
        "urgent_reason": "TEXT",
        "fixed_at": "TEXT",
        "fixed_by": "TEXT",
        "warden_verified_at": "TEXT",
        "warden_verified_by": "TEXT",
        "warden_verdict": "TEXT",
        "warden_notes": "TEXT",
        "student_stage_at": "TEXT",
        "closed_at": "TEXT",
        "closed_by": "TEXT",
        "requires_warden_check": "INTEGER DEFAULT 0",
        "is_spot_check": "INTEGER DEFAULT 0",
        "auto_close_reminded": "INTEGER DEFAULT 0",
        "admin_review_reason": "TEXT",
        "admin_decision": "TEXT",
        "admin_decided_by": "TEXT",
        "admin_decided_at": "TEXT",
        "deletion_requested": "INTEGER DEFAULT 0",
        "deletion_requested_by": "TEXT",
        "deletion_requested_name": "TEXT",
        "deletion_requested_role": "TEXT",
        "deletion_reason": "TEXT",
        "deletion_requested_at": "TEXT",
        "wrong_location_corrected_at": "TEXT",
        "wrong_location_corrections": "INTEGER DEFAULT 0",
        "last_progress_code": "TEXT",
        "photo_skipped": "INTEGER DEFAULT 0",
        "photo_skip_reason": "TEXT",
        "reopen_notes": "TEXT",
        "resolution_proof_url": "TEXT",
        "affected_upgraded": "INTEGER DEFAULT 0",
    }

    for col_name, col_type in new_columns.items():
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE complaints ADD COLUMN {col_name} {col_type};")
            logger.info(f"Added column {col_name} to complaints table.")


def _migrate_users_table(conn: sqlite3.Connection):
    """Ensure users table has photo_skip_streak, force_next_warden_check, and language columns."""
    existing_cols = _get_existing_columns(conn, "users")
    user_cols = {
        "photo_skip_streak": "INTEGER DEFAULT 0",
        "force_next_warden_check": "INTEGER DEFAULT 0",
        "language": "TEXT DEFAULT 'en'",
    }
    for col_name, col_type in user_cols.items():
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};")
            logger.info(f"Added column {col_name} to users table.")


def _migrate_attachments_table(conn: sqlite3.Connection):
    """Ensure attachments table has source, sha256, exif_taken_at, kind, flags columns."""
    existing_cols = _get_existing_columns(conn, "attachments")
    att_cols = {
        "source": "TEXT DEFAULT 'gallery'",
        "sha256": "TEXT",
        "exif_taken_at": "TEXT",
        "kind": "TEXT DEFAULT 'attachment'",
        "flags": "TEXT",
    }
    for col_name, col_type in att_cols.items():
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE attachments ADD COLUMN {col_name} {col_type};")
            logger.info(f"Added column {col_name} to attachments table.")


def _migrate_coordinator_assignments_table(conn: sqlite3.Connection):
    """Ensure coordinator_assignments table exists with unique constraint."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS coordinator_assignments (
            assignment_id TEXT PRIMARY KEY,
            coordinator_id TEXT NOT NULL,
            location_id TEXT NOT NULL,
            department_id TEXT NOT NULL,
            assigned_at TEXT,
            is_active INTEGER NOT NULL DEFAULT 1
        );
    """)

    # De-duplicate any existing identical (coordinator_id, location_id, department_id) rows before index
    conn.execute("""
        DELETE FROM coordinator_assignments
        WHERE rowid NOT IN (
            SELECT MIN(rowid)
            FROM coordinator_assignments
            GROUP BY coordinator_id, location_id, department_id
        );
    """)

    # Create unique index to enforce one row per (coordinator, location, department)
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_coord_loc_dept
        ON coordinator_assignments(coordinator_id, location_id, department_id);
    """)


def _migrate_locations_table(conn: sqlite3.Connection):
    """Ensure locations table uses in_charge_id and copies from warden_id if present."""
    existing_cols = _get_existing_columns(conn, "locations")
    if "in_charge_id" not in existing_cols:
        conn.execute("ALTER TABLE locations ADD COLUMN in_charge_id TEXT;")

    # If legacy warden_id column exists, copy any missing in_charge_id values
    if "warden_id" in existing_cols:
        conn.execute("""
            UPDATE locations
            SET in_charge_id = warden_id
            WHERE (in_charge_id IS NULL OR in_charge_id = '') AND warden_id IS NOT NULL;
        """)


def _migrate_operational_tables(conn: sqlite3.Connection):
    """Create distributed scheduler lock, login attempts, ws tickets, and push subscriptions."""
    # 1. Distributed scheduler lock for multi-worker safety
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scheduler_lock (
            name TEXT PRIMARY KEY,
            owner TEXT,
            expires_at REAL
        );
    """)

    # 2. SQLite-backed rate limiter for login brute force protection across workers
    conn.execute("""
        CREATE TABLE IF NOT EXISTS login_rate_limits (
            ip TEXT NOT NULL,
            email TEXT NOT NULL,
            attempted_at REAL NOT NULL
        );
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_login_rate_limits_lookup
        ON login_rate_limits(email, ip, attempted_at);
    """)

    # 3. Short-lived single-use WebSocket tickets
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ws_tickets (
            ticket_hash TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            created_at REAL NOT NULL,
            expires_at REAL NOT NULL
        );
    """)

    # 4. Web push subscriptions
    conn.execute("""
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            user_id TEXT NOT NULL,
            endpoint TEXT PRIMARY KEY,
            p256dh TEXT NOT NULL,
            auth TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)


def _normalize_priorities_and_deadlines(conn: sqlite3.Connection):
    """Normalise 'Normal' to 'Medium' and compute SLA deadlines for open complaints."""
    # Normalise priorities across complaints, announcements, notifications
    conn.execute("UPDATE complaints SET priority = 'Medium' WHERE priority IN ('Normal', 'normal', '', NULL);")
    conn.execute("UPDATE complaints SET priority = 'High' WHERE priority IN ('Urgent', 'urgent');")

    try:
        conn.execute("UPDATE announcements SET priority = 'Medium' WHERE priority IN ('Normal', 'normal', '', NULL);")
    except Exception:
        pass

    try:
        conn.execute("UPDATE notifications SET priority = 'Medium' WHERE priority IN ('Normal', 'normal', '', NULL);")
    except Exception:
        pass

    # Compute sla_deadline for open complaints that lack one
    placeholders = ",".join("?" for _ in INACTIVE_STATUSES)
    query = f"""
        SELECT complaint_id, created_at, priority
        FROM complaints
        WHERE (sla_deadline IS NULL OR sla_deadline = '')
          AND status NOT IN ({placeholders});
    """
    rows = conn.execute(query, list(INACTIVE_STATUSES)).fetchall()
    for row in rows:
        cid = row["complaint_id"]
        p = normalize_priority(row["priority"])
        hours = SLA_HOURS.get(p, 48)
        created_str = row["created_at"]
        try:
            created_dt = datetime.strptime(created_str[:19], "%Y-%m-%d %H:%M:%S")
        except Exception:
            created_dt = datetime.now()
        deadline_dt = created_dt + timedelta(hours=hours)
        deadline_str = deadline_dt.strftime("%Y-%m-%d %H:%M:%S")

        conn.execute(
            "UPDATE complaints SET priority = ?, sla_deadline = ? WHERE complaint_id = ?;",
            (p, deadline_str, cid),
        )


def _reroute_warden_assigned_open_complaints(conn: sqlite3.Connection):
    """Re-route any open complaints currently assigned to a warden."""
    # Identify wardens
    warden_rows = conn.execute("SELECT user_id FROM users WHERE role IN ('location_in_charge', 'warden');").fetchall()
    warden_ids = [r["user_id"] for r in warden_rows]
    if not warden_ids:
        return

    placeholders_w = ",".join("?" for _ in warden_ids)
    placeholders_inact = ",".join("?" for _ in INACTIVE_STATUSES)

    query = f"""
        SELECT complaint_id, location_id, department_id
        FROM complaints
        WHERE assigned_to IN ({placeholders_w})
          AND status NOT IN ({placeholders_inact});
    """
    params = warden_ids + list(INACTIVE_STATUSES)
    assigned_to_wardens = conn.execute(query, params).fetchall()

    for row in assigned_to_wardens:
        cid = row["complaint_id"]
        loc_id = row["location_id"]
        dept_id = row["department_id"]

        # Check coordinators for this pair
        coord_rows = conn.execute("""
            SELECT coordinator_id FROM coordinator_assignments
            WHERE location_id = ? AND department_id = ? AND is_active = 1;
        """, (loc_id, dept_id)).fetchall()

        if len(coord_rows) == 1:
            new_coord = coord_rows[0]["coordinator_id"]
            conn.execute("""
                UPDATE complaints
                SET assigned_to = ?, status = 'Assigned', updated_at = datetime('now')
                WHERE complaint_id = ?;
            """, (new_coord, cid))
        else:
            # Two or more -> unassigned team queue; 0 -> unassigned
            conn.execute("""
                UPDATE complaints
                SET assigned_to = NULL, status = ?, team_location_id = ?, team_department_id = ?, updated_at = datetime('now')
                WHERE complaint_id = ?;
            """, (STATUS_SUBMITTED, loc_id, dept_id, cid))
        logger.info(f"Re-routed warden-assigned complaint {cid} away from warden.")


def _migrate_push_subscriptions_table(conn: sqlite3.Connection):
    """Ensure push_subscriptions table exists."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS push_subscriptions (
            user_id TEXT NOT NULL,
            endpoint TEXT PRIMARY KEY,
            p256dh TEXT NOT NULL,
            auth TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_push_sub_user ON push_subscriptions(user_id);
    """)
    logger.info("push_subscriptions table migration verified.")


def _migrate_lost_found_items_table(conn: sqlite3.Connection):
    """Ensure lost_found_items table has is_hidden, moderation_reason, moderated_by, moderated_at columns."""
    existing_cols = _get_existing_columns(conn, "lost_found_items")
    lf_cols = {
        "is_hidden": "INTEGER DEFAULT 0",
        "moderation_reason": "TEXT",
        "moderated_by": "TEXT",
        "moderated_at": "TEXT",
    }
    for col_name, col_type in lf_cols.items():
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE lost_found_items ADD COLUMN {col_name} {col_type};")
            logger.info(f"Added column {col_name} to lost_found_items table.")
