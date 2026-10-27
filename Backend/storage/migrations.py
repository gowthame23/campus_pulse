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
from utils.db import is_postgres_configured, get_db_connection
from utils.logger import get_logger

logger = get_logger(__name__)


def run_postgres_migrations():
    """Run all idempotent migrations on PostgreSQL."""
    conn = get_db_connection()
    try:
        # Create schema_migrations tracking table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

        # Check if 001_baseline_schema is applied
        row = conn.execute("SELECT version FROM schema_migrations WHERE version = '001_baseline_schema';").fetchone()
        if not row:
            schema_file = Path(__file__).resolve().parent / "postgres_schema.sql"
            if schema_file.exists():
                sql_content = schema_file.read_text(encoding="utf-8")
                raw_conn = getattr(conn, "_conn", conn)
                with raw_conn.cursor() as cur:
                    cur.execute(sql_content)
                conn.execute("INSERT INTO schema_migrations (version) VALUES ('001_baseline_schema') ON CONFLICT DO NOTHING;")
                conn.commit()
                logger.info("Applied 001_baseline_schema (215 tables) to PostgreSQL.")

        _normalize_priorities_and_deadlines(conn)
        _reroute_warden_assigned_open_complaints(conn)
        _migrate_translation_tables(conn)
        conn.commit()
        logger.info("PostgreSQL database migrations completed successfully.")
    except Exception as err:
        conn.rollback()
        logger.error(f"PostgreSQL migration error: {err}")
        raise err
    finally:
        conn.close()


def run_migrations(db_path: str = "storage/campus_pulse.db"):
    """Run all idempotent migrations on the specified database path or PostgreSQL."""
    if is_postgres_configured():
        return run_postgres_migrations()

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
        _migrate_phase5_tables(conn)
        _migrate_teams_and_leaves(conn)
        _migrate_emergency_tables(conn)
        _migrate_sla_configs_table(conn)
        _migrate_translation_tables(conn)
        _migrate_location_departments_table(conn)
        _normalize_priorities_and_deadlines(conn)
        _reroute_warden_assigned_open_complaints(conn)
        _migrate_multi_department_coordinators(conn)

        conn.commit()
        logger.info("Database migrations completed successfully.")
    except Exception as err:
        conn.rollback()
        logger.error(f"Migration error: {err}")
        raise err
    finally:
        conn.close()


def _get_existing_columns(conn, table_name: str) -> set:
    """Return a set of column names currently present in table_name."""
    try:
        if is_postgres_configured():
            cursor = conn.execute(
                "SELECT column_name FROM information_schema.columns WHERE table_name = %s;",
                (table_name.lower(),)
            )
            rows = cursor.fetchall()
            return {r["column_name"] if isinstance(r, dict) or hasattr(r, "__getitem__") else r[0] for r in rows}
    except Exception:
        pass
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
        "exact_spot": "TEXT",
        "is_emergency": "INTEGER DEFAULT 0",
        "emergency_category": "TEXT",
        "reached": "INTEGER",
        "reached_at": "TEXT",
        "acknowledged_by": "TEXT",
        "acknowledged_at": "TEXT",
        "emergency_outcome": "TEXT",
        "emergency_realert_sent": "INTEGER DEFAULT 0",
        "is_deleted": "INTEGER DEFAULT 0",
        "deleted_at": "TEXT",
        "deleted_by": "TEXT",
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
        "safety_blocked_until": "TEXT",
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

    if "public_complaint_access" not in existing_cols:
        conn.execute("ALTER TABLE locations ADD COLUMN public_complaint_access TEXT DEFAULT 'everyone';")
        conn.execute("""
            UPDATE locations
            SET public_complaint_access = 'location_only'
            WHERE location_type = 'Hostel' OR name LIKE '%Hostel%';
        """)
        logger.info("Added public_complaint_access column to locations table.")

    if "complaint_submission_policy" not in existing_cols:
        conn.execute("ALTER TABLE locations ADD COLUMN complaint_submission_policy TEXT DEFAULT 'everyone';")
        conn.execute("""
            UPDATE locations
            SET complaint_submission_policy = CASE
                WHEN public_complaint_access IS NOT NULL THEN public_complaint_access
                WHEN location_type = 'Hostel' OR name LIKE '%Hostel%' THEN 'location_only'
                ELSE 'everyone'
            END;
        """)
        logger.info("Added complaint_submission_policy column to locations table.")


def _migrate_sla_configs_table(conn: sqlite3.Connection):
    """Ensure department_sla_configs and sla_config_audit_logs tables exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS department_sla_configs (
            config_id TEXT PRIMARY KEY,
            department_id TEXT NOT NULL UNIQUE,
            normal_start_time TEXT DEFAULT '10:00',
            normal_end_time TEXT DEFAULT '16:00',
            normal_duration_hours INTEGER DEFAULT 72,
            medium_start_time TEXT DEFAULT '10:00',
            medium_end_time TEXT DEFAULT '16:00',
            medium_duration_hours INTEGER DEFAULT 48,
            high_start_time TEXT DEFAULT '10:00',
            high_end_time TEXT DEFAULT '18:00',
            high_duration_hours INTEGER DEFAULT 24,
            critical_start_time TEXT DEFAULT '00:00',
            critical_end_time TEXT DEFAULT '23:59',
            critical_duration_hours INTEGER DEFAULT 4,
            app_manager_escalation_hours INTEGER DEFAULT 24,
            admin_escalation_hours INTEGER DEFAULT 48,
            updated_at TEXT NOT NULL,
            updated_by TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sla_config_audit_logs (
            audit_id TEXT PRIMARY KEY,
            department_id TEXT NOT NULL,
            changed_by TEXT NOT NULL,
            changed_at TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            remarks TEXT,
            changes_json TEXT
        );
    """)
    audit_cols = _get_existing_columns(conn, "sla_config_audit_logs")
    if "changes_json" not in audit_cols:
        conn.execute("ALTER TABLE sla_config_audit_logs ADD COLUMN changes_json TEXT;")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sla_config_dept ON department_sla_configs(department_id);")
    logger.info("Department SLA configs and audit tables verified.")


def _migrate_operational_tables(conn: sqlite3.Connection):
    """Create distributed scheduler lock, login attempts, ws tickets, and push subscriptions."""
    # 1. Distributed scheduler lock for multi-worker safety
    existing_cols = _get_existing_columns(conn, "scheduler_lock")
    if "lock_name" not in existing_cols:
        conn.execute("DROP TABLE IF EXISTS scheduler_lock;")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduler_lock (
                lock_name TEXT PRIMARY KEY,
                locked_by TEXT,
                locked_at TEXT,
                expires_at TEXT
            );
        """)
    else:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scheduler_lock (
                lock_name TEXT PRIMARY KEY,
                locked_by TEXT,
                locked_at TEXT,
                expires_at TEXT
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


def _migrate_phase5_tables(conn: sqlite3.Connection):
    """Ensure feedback, recognitions, badges, and safety reports tables exist."""
    # 1. Feedback table (rating + optional thank you note)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaint_feedback (
            feedback_id TEXT PRIMARY KEY,
            complaint_id TEXT NOT NULL,
            student_id TEXT NOT NULL,
            rating INTEGER NOT NULL,
            thank_you_note TEXT DEFAULT '',
            created_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_feedback_complaint_student
        ON complaint_feedback(complaint_id, student_id);
    """)

    # 2. Fixer of the Month recognitions
    conn.execute("""
        CREATE TABLE IF NOT EXISTS recognitions (
            recognition_id TEXT PRIMARY KEY,
            month TEXT NOT NULL,
            coordinator_id TEXT NOT NULL,
            scope TEXT NOT NULL DEFAULT 'campus',
            score REAL NOT NULL,
            is_winner INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_recognitions_month
        ON recognitions(month, coordinator_id);
    """)

    # 3. Coordinator badges
    conn.execute("""
        CREATE TABLE IF NOT EXISTS coordinator_badges (
            badge_id TEXT PRIMARY KEY,
            coordinator_id TEXT NOT NULL,
            badge_name TEXT NOT NULL,
            badge_description TEXT NOT NULL,
            awarded_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_coordinator_badges_coord
        ON coordinator_badges(coordinator_id);
    """)

    # 4. Safety reports (Admin feature switch, private case codes)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS safety_reports (
            report_id TEXT PRIMARY KEY,
            case_code TEXT NOT NULL UNIQUE,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'submitted',
            outcome TEXT,
            outcome_notes TEXT,
            created_at TEXT NOT NULL,
            closed_at TEXT
        );
    """)

    # 5. Safety report messages (two-way anonymous chat)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS safety_report_messages (
            message_id TEXT PRIMARY KEY,
            report_id TEXT NOT NULL,
            sender_type TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_safety_msgs_report
        ON safety_report_messages(report_id, created_at);
    """)

    # 6. Safety report identity (sealed table, never returned by normal endpoints)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS safety_report_identity (
            report_id TEXT PRIMARY KEY,
            reporter_user_id TEXT NOT NULL,
            revealed INTEGER NOT NULL DEFAULT 0,
            revealed_at TEXT,
            revealed_by TEXT,
            reveal_reason TEXT
        );
    """)

    # 7. Default system settings for safety and health map
    default_settings = [
        ("setting_safety_reports_enabled", "safety_reports_enabled", "false", "boolean", "safety", "Enable safety reports module", 1),
        ("setting_safety_emergency_numbers", "safety_emergency_numbers", "112", "string", "safety", "Campus emergency contact numbers", 1),
        ("setting_show_health_map_to_students", "show_health_map_to_students", "false", "boolean", "features", "Expose campus health map to students", 1),
        ("setting_health_map_pattern_threshold", "health_map_pattern_threshold", "5", "integer", "features", "Threshold for recurring problem pattern alerts", 1),
    ]
    for s_id, s_key, s_val, s_type, s_cat, s_desc, is_edit in default_settings:
        conn.execute("""
            INSERT OR IGNORE INTO system_settings (setting_id, setting_key, setting_value, setting_type, category, description, is_editable, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'));
        """, (s_id, s_key, s_val, s_type, s_cat, s_desc, is_edit))
    logger.info("Phase 5 tables migration verified.")


def _migrate_teams_and_leaves(conn: sqlite3.Connection):
    """Ensure teams, team_locations, team_members, user_leaves tables and complaints columns exist.
    Migrate existing coordinator_assignments into teams if teams table is empty.
    """
    conn.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            team_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department_id TEXT NOT NULL,
            coordinator_id TEXT NOT NULL,
            backup_coordinator_id TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS team_locations (
            team_id TEXT NOT NULL,
            location_id TEXT NOT NULL,
            PRIMARY KEY (team_id, location_id),
            FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE CASCADE
        );
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS team_members (
            team_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            PRIMARY KEY (team_id, user_id),
            FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE CASCADE
        );
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_leaves (
            leave_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            from_date TEXT NOT NULL,
            to_date TEXT NOT NULL,
            reason TEXT,
            set_by TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)

    conn.execute("CREATE INDEX IF NOT EXISTS idx_team_dept ON teams(department_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_team_coord ON teams(coordinator_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_team_loc_loc ON team_locations(location_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_team_mem_user ON team_members(user_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_user_leaves_user ON user_leaves(user_id, from_date, to_date);")

    # Multi-Department Coordinator Support: Allow an employee to coordinate multiple departments/teams
    conn.execute("DROP INDEX IF EXISTS uq_team_coord1;")
    conn.execute("DROP INDEX IF EXISTS uq_team_coord2;")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_team_coord1 ON teams(coordinator_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_team_coord2 ON teams(backup_coordinator_id);")

    # Employee Department-Location Work Memberships
    conn.execute("""
        CREATE TABLE IF NOT EXISTS employee_work_memberships (
            membership_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            department_id TEXT NOT NULL,
            location_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            created_by TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE CASCADE,
            FOREIGN KEY (location_id) REFERENCES locations(location_id) ON DELETE CASCADE,
            UNIQUE (user_id, department_id, location_id)
        );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ewm_user ON employee_work_memberships(user_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ewm_dept_loc ON employee_work_memberships(department_id, location_id);")

    # Migrate initial work memberships from active teams, members, and locations
    conn.execute("""
        INSERT OR IGNORE INTO employee_work_memberships (membership_id, user_id, department_id, location_id, created_at, created_by)
        SELECT 
            'EWM_' || lower(hex(randomblob(6))),
            tm.user_id,
            t.department_id,
            tl.location_id,
            datetime('now'),
            'migration'
        FROM team_members tm
        JOIN teams t ON tm.team_id = t.team_id
        JOIN team_locations tl ON t.team_id = tl.team_id
        JOIN users u ON tm.user_id = u.user_id
        WHERE t.active = 1;
    """)

    # Complaints new columns for team model
    existing_cols = _get_existing_columns(conn, "complaints")
    team_model_cols = {
        "awaiting_assign_since": "TEXT",
        "assigned_by": "TEXT",
        "assign_escalation_level": "INTEGER DEFAULT 0",
        "marked_by": "TEXT",
        "team_id": "TEXT",
        "returned_reason": "TEXT",
        "assignee_on_leave_flag": "INTEGER DEFAULT 0",
        "assignee_removed_flag": "INTEGER DEFAULT 0",
        "cancellation_requested": "INTEGER DEFAULT 0",
        "cancellation_requested_by": "TEXT",
        "cancellation_reason": "TEXT",
        "cancellation_requested_at": "TEXT",
        "cancellation_decided_by": "TEXT",
        "cancellation_decided_at": "TEXT",
        "cancellation_decision_note": "TEXT",
        "previous_status": "TEXT",
    }
    for col, ctype in team_model_cols.items():
        if col not in existing_cols:
            conn.execute(f"ALTER TABLE complaints ADD COLUMN {col} {ctype};")
            logger.info(f"Added column {col} to complaints table.")

    # Migrate coordinator_assignments to teams if teams is empty
    count = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
    if count == 0:
        logger.info("Migrating existing coordinator_assignments to teams table...")
        asgn_rows = conn.execute(
            "SELECT coordinator_id, department_id, location_id FROM coordinator_assignments"
        ).fetchall()

        from collections import defaultdict
        pair_coords = defaultdict(list)
        for cid, did, lid in asgn_rows:
            if cid and did and lid:
                if cid not in pair_coords[(did, lid)]:
                    pair_coords[(did, lid)].append(cid)

        dept_rows = conn.execute("SELECT department_id, name FROM departments").fetchall()
        dept_names = {r[0]: r[1] for r in dept_rows}
        loc_rows = conn.execute("SELECT location_id, name FROM locations").fetchall()
        loc_names = {r[0]: r[1] for r in loc_rows}

        team_idx = 1
        for (did, lid), coords in pair_coords.items():
            ranked_coords = []
            for cid in coords:
                cnt = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE department_id = ? AND location_id = ? AND assigned_to = ?",
                    (did, lid, cid),
                ).fetchone()[0]
                ranked_coords.append((cnt, cid))

            # Highest complaint count first, then alphabetical by ID
            ranked_coords.sort(key=lambda x: (-x[0], x[1]))
            primary_coord = ranked_coords[0][1]
            backup_coord = ranked_coords[1][1] if len(ranked_coords) > 1 else None

            d_name = dept_names.get(did, did)
            l_name = loc_names.get(lid, lid)
            team_id = f"TEAM_{team_idx:04d}"
            team_name = f"{l_name} - {d_name}"
            team_idx += 1

            conn.execute(
                """
                INSERT OR IGNORE INTO teams (team_id, name, department_id, coordinator_id, backup_coordinator_id, active, created_at)
                VALUES (?, ?, ?, ?, ?, 1, datetime('now'))
                """,
                (team_id, team_name, did, primary_coord, backup_coord),
            )
            conn.execute(
                """
                INSERT OR IGNORE INTO team_locations (team_id, location_id)
                VALUES (?, ?)
                """,
                (team_id, lid),
            )
            for _, cid in ranked_coords:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO team_members (team_id, user_id)
                    VALUES (?, ?)
                    """,
                    (team_id, cid),
                )

        conn.execute("""
            UPDATE complaints
            SET awaiting_assign_since = created_at
            WHERE awaiting_assign_since IS NULL AND status = 'Submitted'
        """)
        conn.execute("""
            UPDATE complaints
            SET team_id = (
                SELECT t.team_id
                FROM teams t
                JOIN team_locations tl ON t.team_id = tl.team_id
                WHERE t.department_id = complaints.department_id
                  AND tl.location_id = complaints.location_id
                  AND t.active = 1
                LIMIT 1
            )
            WHERE team_id IS NULL
        """)
        logger.info("Migrated coordinator_assignments into teams successfully.")
    logger.info("Team model and user leaves migrations verified.")


def _migrate_emergency_tables(conn: sqlite3.Connection):
    """Ensure emergency_categories, emergency_contacts, and emergency_strikes tables exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS emergency_categories (
            category_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department_id TEXT,
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );
    """)

    # Seed default emergency categories if empty
    cnt = conn.execute("SELECT COUNT(*) FROM emergency_categories").fetchone()[0]
    if cnt == 0:
        depts = conn.execute("SELECT department_id, name FROM departments").fetchall()
        dept_by_name = {row["name"].lower(): row["department_id"] for row in depts}

        elec_id = next((did for name, did in dept_by_name.items() if "elec" in name), None)
        plumb_id = next((did for name, did in dept_by_name.items() if "plumb" in name or "water" in name), None)
        lift_id = next((did for name, did in dept_by_name.items() if "lift" in name or "maint" in name or "gen" in name), None)
        other_id = next((did for name, did in dept_by_name.items() if "gen" in name or "other" in name), None)

        default_cats = [
            ("EM_CAT_01", "Electrical", elec_id, 1, 1),
            ("EM_CAT_02", "Plumbing / Water", plumb_id, 1, 2),
            ("EM_CAT_03", "Lift", lift_id, 1, 3),
            ("EM_CAT_04", "Fire / Smoke", None, 1, 4),
            ("EM_CAT_05", "Medical", None, 1, 5),
            ("EM_CAT_06", "Other", other_id, 1, 6),
        ]
        now = datetime.now().isoformat()
        for cid, cname, did, act, sort_ord in default_cats:
            conn.execute(
                """
                INSERT OR IGNORE INTO emergency_categories (category_id, name, department_id, is_active, sort_order, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (cid, cname, did, act, sort_ord, now),
            )

    conn.execute("""
        CREATE TABLE IF NOT EXISTS emergency_contacts (
            contact_id TEXT PRIMARY KEY,
            department_id TEXT,
            location_id TEXT,
            user_id TEXT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            sort_order INTEGER DEFAULT 0,
            active INTEGER DEFAULT 1,
            night_only INTEGER DEFAULT 0,
            day_only INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_emergency_contacts_dept ON emergency_contacts(department_id, active);")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS emergency_strikes (
            strike_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            complaint_id TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_emergency_strikes_user ON emergency_strikes(user_id, created_at);")

    logger.info("Emergency tables and schema migration verified.")

    # Location hierarchy: parent_id column
    loc_cols = _get_existing_columns(conn, "locations")
    if "parent_id" not in loc_cols:
        conn.execute("ALTER TABLE locations ADD COLUMN parent_id TEXT NULL;")
        logger.info("Added parent_id column to locations table.")


def _migrate_translation_tables(conn):
    """Ensure complaint_translations table exists with compound caching index."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS complaint_translations (
            translation_id TEXT PRIMARY KEY,
            complaint_id TEXT NOT NULL,
            source_hash TEXT NOT NULL,
            source_language TEXT NOT NULL,
            target_language TEXT NOT NULL,
            translated_text TEXT NOT NULL,
            provider TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id) ON DELETE CASCADE
        );
    """)
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_translations_cache 
        ON complaint_translations (complaint_id, source_hash, target_language);
    """)
    logger.info("Complaint translations schema migration verified.")


def _migrate_location_departments_table(conn):
    """Ensure location_departments table exists, consolidate duplicate location-specific
    departments into central campus-wide departments, and populate location-department
    mappings.
    """
    import uuid
    from datetime import datetime

    # 1. Create table and indexes
    conn.execute("""
        CREATE TABLE IF NOT EXISTS location_departments (
            id TEXT PRIMARY KEY,
            location_id TEXT NOT NULL,
            department_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            created_by TEXT DEFAULT 'system',
            is_active INTEGER NOT NULL DEFAULT 1,
            FOREIGN KEY (location_id) REFERENCES locations(location_id) ON DELETE CASCADE,
            FOREIGN KEY (department_id) REFERENCES departments(department_id) ON DELETE CASCADE,
            UNIQUE(location_id, department_id)
        );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_loc_dept_loc ON location_departments(location_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_loc_dept_dept ON location_departments(department_id);")

    # 2. Consolidation of duplicate location-scoped departments into central canonical entities
    consolidation_map = {
        'DEPT_ACADEMIC_ELECTRICAL': 'DEPT_HOSTEL_ELECTRICAL',
        'DEPT_SAC_ELECTRICAL': 'DEPT_HOSTEL_ELECTRICAL',
        'DEPT_SPORTS_LIGHTING': 'DEPT_HOSTEL_ELECTRICAL',
        
        'DEPT_ACADEMIC_PLUMBING': 'DEPT_HOSTEL_PLUMBING',
        'DEPT_MESS_PLUMBING': 'DEPT_HOSTEL_PLUMBING',
        'DEPT_SAC_PLUMBING': 'DEPT_HOSTEL_PLUMBING',
        'DEPT_SPORTS_PLUMBING': 'DEPT_HOSTEL_PLUMBING',
        
        'DEPT_ACADEMIC_HOUSEKEEPING': 'DEPT_HOSTEL_HOUSEKEEPING',
        'DEPT_SAC_HOUSEKEEPING': 'DEPT_HOSTEL_HOUSEKEEPING',
        'DEPT_SPORTS_HOUSEKEEPING': 'DEPT_HOSTEL_HOUSEKEEPING',
        'DEPT_MESS_HYGIENE': 'DEPT_HOSTEL_HOUSEKEEPING',
        
        'DEPT_ACADEMIC_FURNITURE': 'DEPT_HOSTEL_FURNITURE',
        'DEPT_MESS_FURNITURE': 'DEPT_HOSTEL_FURNITURE',
        
        'DEPT_ACADEMIC_NETWORK': 'DEPT_HOSTEL_NETWORK',
        
        'DEPT_HOSTEL_OTHER': 'DEPT_OTHER_GENERAL',
        'DEPT_ACADEMIC_OTHER': 'DEPT_OTHER_GENERAL',
        'DEPT_MESS_OTHER': 'DEPT_OTHER_GENERAL',
        'DEPT_SAC_OTHER': 'DEPT_OTHER_GENERAL',
        'DEPT_SPORTS_OTHER': 'DEPT_OTHER_GENERAL',
    }

    # Re-parent child references if table exists
    tables_to_reparent = [
        ("department_issues", "department_id"),
        ("complaints", "department_id"),
        ("users", "department_id"),
        ("employee_work_memberships", "department_id"),
        ("coordinator_assignments", "department_id"),
    ]
    for tbl, col in tables_to_reparent:
        try:
            for old_id, canonical_id in consolidation_map.items():
                conn.execute(f"UPDATE {tbl} SET {col} = ? WHERE {col} = ?", (canonical_id, old_id))
        except Exception:
            pass

    # Clean legacy duplicate department rows from departments
    try:
        # Update canonical departments to clean central names and detach location_id
        conn.execute("UPDATE departments SET name = 'Electrical', location_id = NULL WHERE department_id = 'DEPT_HOSTEL_ELECTRICAL'")
        conn.execute("UPDATE departments SET name = 'Plumbing', location_id = NULL WHERE department_id = 'DEPT_HOSTEL_PLUMBING'")
        conn.execute("UPDATE departments SET name = 'Housekeeping', location_id = NULL WHERE department_id = 'DEPT_HOSTEL_HOUSEKEEPING'")
        conn.execute("UPDATE departments SET name = 'Furniture & Fixtures', location_id = NULL WHERE department_id = 'DEPT_HOSTEL_FURNITURE'")
        conn.execute("UPDATE departments SET name = 'Network & IT', location_id = NULL WHERE department_id = 'DEPT_HOSTEL_NETWORK'")
        conn.execute("UPDATE departments SET name = 'Other / Not Sure', location_id = NULL WHERE department_id = 'DEPT_OTHER_GENERAL'")
        conn.execute("UPDATE departments SET location_id = NULL WHERE department_id IN ('DEPT_MESS_FOOD', 'DEPT_MESS_MAINTENANCE', 'DEPT_ACADEMIC_LIBRARY', 'DEPT_SPORTS_GROUNDS', 'DEPT_SPORTS_EQUIPMENT', 'DEPT_SAC_EQUIPMENT', 'DEPT_SAC_AV')")

        for old_id in consolidation_map.keys():
            conn.execute("DELETE FROM departments WHERE department_id = ?", (old_id,))
    except Exception as e:
        logger.warning(f"Note during department consolidation: {e}")

    # Clean orphan ownership claims
    try:
        conn.execute("DELETE FROM ownership_claims WHERE item_id NOT IN (SELECT item_id FROM lost_found_items)")
    except Exception:
        pass

    # 3. Clean up deleted departments and ensure all 10 core departments exist
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        import json
        conn.execute("DELETE FROM departments WHERE department_id IN ('DEPT_ACADEMIC_LIBRARY', 'DEPT_SPORTS_GROUNDS', 'DEPT_SPORTS_EQUIPMENT', 'DEPT_SAC_EQUIPMENT', 'DEPT_SAC_AV')")
        conn.execute("DELETE FROM location_departments WHERE department_id IN ('DEPT_ACADEMIC_LIBRARY', 'DEPT_SPORTS_GROUNDS', 'DEPT_SPORTS_EQUIPMENT', 'DEPT_SAC_EQUIPMENT', 'DEPT_SAC_AV')")
        conn.execute("DELETE FROM department_issues WHERE department_id IN ('DEPT_ACADEMIC_LIBRARY', 'DEPT_SPORTS_GROUNDS', 'DEPT_SPORTS_EQUIPMENT', 'DEPT_SAC_EQUIPMENT', 'DEPT_SAC_AV')")
        conn.execute("DELETE FROM coordinator_assignments WHERE department_id IN ('DEPT_ACADEMIC_LIBRARY', 'DEPT_SPORTS_GROUNDS', 'DEPT_SPORTS_EQUIPMENT', 'DEPT_SAC_EQUIPMENT', 'DEPT_SAC_AV')")

        core_departments = [
            (
                'DEPT_HOSTEL_ELECTRICAL', 'Electrical', 2,
                json.dumps(['Power Failure', 'Fan Not Working', 'Light Not Working', 'Switch Problem', 'Socket Problem', 'Projector Not Working / No Display', 'Audio / Speaker / Mic Issue', 'AC / Air Conditioning Issue', 'Other / Not Sure']),
                'Campus power supply, wiring, lighting, fans, switches, sockets, and AC systems.'
            ),
            (
                'DEPT_HOSTEL_PLUMBING', 'Plumbing', 3,
                json.dumps(['Water Leakage', 'Tap Not Working / Tap Leakage', 'No Water Supply', 'Low Water Pressure', 'Toilet Flush Not Working', 'Toilet Blockage', 'Wash Basin / Sink Blockage', 'Drainage Blockage', 'Shower Not Working', 'Water Cooler / Dispenser Issue', 'Other / Not Sure']),
                'Water supply lines, taps, bathroom fixtures, drainage, sewer pipelines, and water dispensers.'
            ),
            (
                'DEPT_HOSTEL_HOUSEKEEPING', 'Housekeeping', 1,
                json.dumps(['Room Cleaning Required', 'Washroom / Bathroom Cleaning', 'Dustbin / Waste Removal', 'Corridor / Common Area Cleaning', 'Classroom / Lab Cleaning Required', 'Other / Not Sure']),
                'Room cleanliness, common corridor sanitation, washroom hygiene, dustbins, and campus waste management.'
            ),
            (
                'DEPT_HOSTEL_FURNITURE', 'Furniture & Fixtures', 5,
                json.dumps(['Cot / Bed Frame Issue', 'Study Table / Chair Damaged', 'Cupboard / Wardrobe Lock/Door Issue', 'Door / Window Latch Problem', 'Desk / Bench Damaged', 'Carpenter Repair Work', 'Missing Furniture / Item', 'Other / Not Sure']),
                'Carpentry repairs, cot/bed frames, study tables, chairs, cupboards, wardrobe locks, doors, and window latches.'
            ),
            (
                'DEPT_HOSTEL_NETWORK', 'Network & IT', 3,
                json.dumps(['Wi-Fi Not Working', 'Wi-Fi Connected but No Internet', 'Slow Internet', 'Frequent Wi-Fi Disconnection', 'Weak Wi-Fi Signal', 'Ethernet / LAN Port Not Working', 'Other / Not Sure']),
                'Campus Wi-Fi connectivity, LAN ports, authentication routers, access points, and IT network infrastructure.'
            ),
            (
                'DEPT_MESS_FOOD', 'Food Quality & Catering', 1,
                json.dumps(['Food Quality / Taste Issue', 'Undercooked / Raw Food', 'Foreign Object in Food', 'Food / Utensil Shortage', 'Counter / Service Delay', 'Other / Not Sure']),
                'Dining hall food preparation, taste, raw ingredients, catering hygiene, utensils, and food counters.'
            ),
            (
                'DEPT_MESS_MAINTENANCE', 'Maintenance & Equipment', 3,
                json.dumps(['Water Cooler / Dispenser Issue', 'Food Warmer / Bain-Marie Not Working', 'Exhaust Fan / Ventilation Issue', 'Lighting / Electrical Issue', 'Fly Catcher Machine Not Working', 'Other / Not Sure']),
                'Mess appliances, bain-maries, food warmers, industrial water coolers, fly catchers, and exhaust fans.'
            ),
            (
                'DEPT_CAMPUS_FIRE', 'Fire & Safety', 1,
                json.dumps(['Fire Outbreak', 'Smoke Detected', 'Gas Leakage Hazard', 'Fire Extinguisher Inspection', 'Emergency Exit Blocked', 'Other / Not Sure']),
                'Campus fire protection, smoke detection, fire extinguishers, emergency evacuation, and safety hazard control.'
            ),
            (
                'DEPT_CAMPUS_MEDICAL', 'Health & Medical', 1,
                json.dumps(['Medical Emergency', 'First Aid Assistance', 'Ambulance Request', 'Clinic Consultation', 'Health & Hygiene Concern', 'Other / Not Sure']),
                'Campus Health Center, medical clinic, first aid, ambulance, and student healthcare services.'
            ),
            (
                'DEPT_OTHER_GENERAL', 'Other / Not Sure', 2,
                json.dumps(['Issue Not Listed / General Complaint', 'Urgent Safety or Security Issue', 'Infrastructure / Outdoor Maintenance', 'General Campus Cleanliness']),
                'General campus infrastructure, unlisted requests, and administrative assistance.'
            ),
        ]

        for dept_id, name, sla, types_json, desc in core_departments:
            conn.execute('''
                INSERT INTO departments (department_id, name, sla_days, complaint_types, coordinator_id, coordinator_2_id, active, archived, description, status)
                VALUES (?, ?, ?, ?, 'USR_COORD_1', 'USR_COORD_2', 1, 0, ?, 'Active')
                ON CONFLICT(department_id) DO UPDATE SET
                    name = excluded.name,
                    sla_days = excluded.sla_days,
                    complaint_types = excluded.complaint_types,
                    coordinator_id = 'USR_COORD_1',
                    coordinator_2_id = 'USR_COORD_2',
                    active = 1,
                    archived = 0,
                    description = excluded.description,
                    status = 'Active'
            ''', (dept_id, name, sla, types_json, desc))

        # Update emergency category mappings
        conn.execute("UPDATE emergency_categories SET department_id = 'DEPT_CAMPUS_MEDICAL' WHERE category_id = 'EM_CAT_05' AND (department_id IS NULL OR department_id = '')")
        conn.execute("UPDATE emergency_categories SET department_id = 'DEPT_CAMPUS_FIRE' WHERE category_id = 'EM_CAT_04' AND (department_id IS NULL OR department_id = '')")
        conn.execute("UPDATE emergency_categories SET department_id = 'DEPT_HOSTEL_PLUMBING' WHERE category_id = 'EM_CAT_02'")
    except Exception as e:
        logger.warning(f"Note during core departments migration: {e}")

    common_hostel_depts = ['DEPT_HOSTEL_ELECTRICAL', 'DEPT_HOSTEL_PLUMBING', 'DEPT_HOSTEL_HOUSEKEEPING', 'DEPT_HOSTEL_FURNITURE', 'DEPT_HOSTEL_NETWORK', 'DEPT_CAMPUS_MEDICAL', 'DEPT_CAMPUS_FIRE', 'DEPT_OTHER_GENERAL']
    academic_depts = ['DEPT_HOSTEL_ELECTRICAL', 'DEPT_HOSTEL_PLUMBING', 'DEPT_HOSTEL_HOUSEKEEPING', 'DEPT_HOSTEL_FURNITURE', 'DEPT_HOSTEL_NETWORK', 'DEPT_CAMPUS_MEDICAL', 'DEPT_CAMPUS_FIRE', 'DEPT_OTHER_GENERAL']
    mess_depts = ['DEPT_MESS_FOOD', 'DEPT_MESS_MAINTENANCE', 'DEPT_HOSTEL_HOUSEKEEPING', 'DEPT_HOSTEL_PLUMBING', 'DEPT_HOSTEL_ELECTRICAL', 'DEPT_CAMPUS_MEDICAL', 'DEPT_CAMPUS_FIRE', 'DEPT_OTHER_GENERAL']
    sac_depts = ['DEPT_HOSTEL_ELECTRICAL', 'DEPT_HOSTEL_PLUMBING', 'DEPT_HOSTEL_HOUSEKEEPING', 'DEPT_HOSTEL_FURNITURE', 'DEPT_CAMPUS_MEDICAL', 'DEPT_CAMPUS_FIRE', 'DEPT_OTHER_GENERAL']
    sports_depts = ['DEPT_HOSTEL_ELECTRICAL', 'DEPT_HOSTEL_PLUMBING', 'DEPT_HOSTEL_HOUSEKEEPING', 'DEPT_CAMPUS_MEDICAL', 'DEPT_CAMPUS_FIRE', 'DEPT_OTHER_GENERAL']
    other_depts = ['DEPT_OTHER_GENERAL', 'DEPT_HOSTEL_ELECTRICAL', 'DEPT_HOSTEL_PLUMBING', 'DEPT_HOSTEL_HOUSEKEEPING', 'DEPT_HOSTEL_FURNITURE', 'DEPT_HOSTEL_NETWORK', 'DEPT_CAMPUS_MEDICAL', 'DEPT_CAMPUS_FIRE']

    loc_mappings = {
        'LOC_HOSTEL_1': common_hostel_depts,
        'LOC_HOSTEL_2': common_hostel_depts,
        'LOC_ACADEMIC_1': academic_depts,
        'LOC_ACADEMIC_2': academic_depts,
        'LOC_MESS_1': mess_depts,
        'LOC_MESS_2': mess_depts,
        'LOC_SAC_1': sac_depts,
        'LOC_SAC_2': sac_depts,
        'LOC_SPORTS_1': sports_depts,
        'LOC_SPORTS_2': sports_depts,
        'LOC_OTHER': other_depts,
    }

    # Fetch valid department IDs to ensure zero foreign key violations
    valid_depts = {row[0] for row in conn.execute("SELECT department_id FROM departments").fetchall()}

    for loc_id, dept_ids in loc_mappings.items():
        for dept_id in dept_ids:
            if dept_id not in valid_depts:
                continue
            try:
                conn.execute('''
                    INSERT OR IGNORE INTO location_departments (id, location_id, department_id, created_at, created_by, is_active)
                    VALUES (?, ?, ?, ?, 'migration', 1)
                ''', (f'LD_{uuid.uuid4().hex[:12]}', loc_id, dept_id, now_str))
            except Exception:
                pass

    logger.info("location_departments schema migration and baseline associations verified.")
    _migrate_multi_department_coordinators(conn)


def _migrate_multi_department_coordinators(conn: sqlite3.Connection):
    """Enable multi-department coordinators:
    1. Drop obsolete global unique indexes on teams(coordinator_id) and teams(backup_coordinator_id).
    2. Add department_id column to user_leaves table if missing.
    3. Ensure index support for department-scoped leaves.
    """
    conn.execute("DROP INDEX IF EXISTS uq_team_coord1;")
    conn.execute("DROP INDEX IF EXISTS uq_team_coord2;")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_team_coord1 ON teams(coordinator_id);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_team_coord2 ON teams(backup_coordinator_id);")

    # Add department_id to user_leaves if missing
    cursor = conn.execute("PRAGMA table_info(user_leaves)")
    columns = [col[1] for col in cursor.fetchall()]
    if "department_id" not in columns:
        conn.execute("ALTER TABLE user_leaves ADD COLUMN department_id TEXT")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_user_leaves_dept ON user_leaves(user_id, department_id)")
    logger.info("Multi-department coordinator migrations verified.")



