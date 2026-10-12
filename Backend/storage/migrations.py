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
        _migrate_phase5_tables(conn)
        _migrate_teams_and_leaves(conn)
        _migrate_emergency_tables(conn)
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
        "exact_spot": "TEXT",
        "is_emergency": "INTEGER DEFAULT 0",
        "emergency_category": "TEXT",
        "reached": "INTEGER",
        "reached_at": "TEXT",
        "acknowledged_by": "TEXT",
        "acknowledged_at": "TEXT",
        "emergency_outcome": "TEXT",
        "emergency_realert_sent": "INTEGER DEFAULT 0",
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
    loc_cols = [c["name"] for c in conn.execute("PRAGMA table_info(locations)").fetchall()]
    if "parent_id" not in loc_cols:
        conn.execute("ALTER TABLE locations ADD COLUMN parent_id TEXT NULL;")
        logger.info("Added parent_id column to locations table.")



