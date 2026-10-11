#!/usr/bin/env python3
"""
Campus Pulse — Drop Unused Legacy Tables Script
Safely removes speculative, unused legacy enterprise tables from an existing database.

SAFETY RULES:
1. Requires explicit `--confirm` flag to execute.
2. Creates an automatic timestamped database backup BEFORE executing any drop.
3. Will never drop active application tables (users, complaints, locations, etc.).
"""
import argparse
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Add Backend root to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from scripts.legacy_scaffold_schema import LEGACY_TABLE_NAMES

# Tables that must NEVER be dropped under any circumstance
PROTECTED_TABLES = {
    "users",
    "student_profiles",
    "staff_profiles",
    "user_activities",
    "activation_tokens",
    "academic_programs",
    "departments",
    "complaint_categories",
    "coordinator_assignments",
    "locations",
    "location_types",
    "campuses",
    "buildings",
    "hostels",
    "blocks",
    "floors",
    "rooms",
    "complaints",
    "affected_students",
    "comments",
    "attachments",
    "audit_logs",
    "notifications",
    "chat_messages",
    "push_subscriptions",
    "login_rate_limits",
    "announcements",
    "announcement_targets",
    "announcement_attachments",
    "announcement_reads",
    "announcement_acknowledgements",
    "lost_found_items",
    "lost_found_images",
    "ownership_claims",
    "feedback",
    "reports",
    "report_templates",
    "scheduled_reports",
    "report_downloads",
    "documents",
    "document_versions",
    "search_index",
    "search_history",
    "saved_searches",
    "system_settings",
    "setting_audit_logs",
    "master_references",
    "institutions",
    "support_tickets",
    "backups",
    "backup_schedules",
    "backup_files",
    "restore_history",
    "highlights",
}


def drop_unused_tables(db_path: str, confirmed: bool) -> None:
    db_file = Path(db_path)
    if not db_file.exists():
        print(f"Error: Database file does not exist at {db_path}")
        sys.exit(1)

    with sqlite3.connect(db_path) as conn:
        existing_tables = set(
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        )

    # Tables to drop: intersection of existing tables and legacy list, excluding protected
    to_drop = [
        tbl
        for tbl in LEGACY_TABLE_NAMES
        if tbl in existing_tables and tbl not in PROTECTED_TABLES
    ]

    print("=" * 70)
    print("CAMPUS PULSE — UNUSED TABLE PURGE UTILITY")
    print("=" * 70)
    print(f"Target Database: {db_path}")
    print(f"Existing Tables in DB: {len(existing_tables)}")
    print(f"Identified Unused Legacy Tables: {len(to_drop)}")

    if not to_drop:
        print("No unused legacy tables found in this database. Nothing to drop.")
        return

    print("\nTables to be dropped:")
    for idx, tbl in enumerate(sorted(to_drop), 1):
        print(f"  {idx:2d}. {tbl}")

    if not confirmed:
        print("\n" + "!" * 70)
        print("SAFETY ABORT: `--confirm` flag was not provided.")
        print("To drop these tables, re-run with: python scripts/drop_unused_tables.py --confirm")
        print("!" * 70)
        sys.exit(1)

    # Step 1: Create automatic backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_file.parent / f"{db_file.stem}_pre_drop_{timestamp}{db_file.suffix}"
    print(f"\n[1/2] Creating pre-drop database backup: {backup_path}")
    shutil.copy2(db_file, backup_path)
    print("      Backup created successfully.")

    # Step 2: Drop tables
    print(f"\n[2/2] Dropping {len(to_drop)} unused tables...")
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = OFF;")
        for tbl in to_drop:
            conn.execute(f"DROP TABLE IF EXISTS {tbl};")
        conn.commit()
        # Vacuum database to reclaim space
        conn.execute("VACUUM;")
        conn.commit()

    print(f"Successfully dropped {len(to_drop)} unused tables and vacuumed {db_path}.")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Drop unused legacy tables from database.")
    parser.add_argument(
        "--db",
        default="storage/campus_pulse.db",
        help="Path to target database file (default: storage/campus_pulse.db)",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Explicitly confirm dropping unused tables.",
    )
    args = parser.parse_args()
    drop_unused_tables(args.db, args.confirm)
