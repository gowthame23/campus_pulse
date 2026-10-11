import argparse
import hashlib
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

# Ensure Backend directory is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def calculate_checksum(filepath: Path) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def restore_db_cli(backup_id: str, db_path: str = None):
    if not db_path:
        db_path = os.getenv("DATABASE_PATH", str(BACKEND_DIR / "storage" / "campus_pulse.db"))

    target_db = Path(db_path).resolve()
    storage_dir = target_db.parent
    backups_dir = storage_dir / "backups"

    if not backups_dir.exists():
        print(f"Error: Backups directory not found at {backups_dir}")
        sys.exit(1)

    # Locate backup metadata in database if target_db exists
    bkp_file = None
    stored_checksum = None
    backup_name = backup_id

    if target_db.exists():
        try:
            with sqlite3.connect(target_db) as conn:
                conn.row_factory = sqlite3.Row
                row = conn.execute(
                    "SELECT * FROM backups WHERE backup_id = ? OR file_name = ? OR backup_name = ?",
                    (backup_id, backup_id, backup_id),
                ).fetchone()
                if row:
                    bkp_file = Path(row["file_path"])
                    if not bkp_file.is_absolute():
                        bkp_file = storage_dir / bkp_file
                    stored_checksum = row["checksum"]
                    backup_name = row["backup_name"]
        except Exception as e:
            print(f"Note: Could not query backups table from {target_db.name}: {e}")

    # Fallback to direct file search in backups_dir
    if not bkp_file or not bkp_file.exists():
        candidates = list(backups_dir.glob(f"*{backup_id}*.db")) + list(backups_dir.glob(f"{backup_id}"))
        if candidates:
            bkp_file = candidates[0]
        else:
            print(f"Error: Could not locate backup file for ID/name '{backup_id}' in {backups_dir}")
            sys.exit(1)

    print(f"Verifying backup archive: {bkp_file}...")
    if stored_checksum:
        calc_sum = calculate_checksum(bkp_file)
        if calc_sum != stored_checksum:
            print(f"Error: Checksum mismatch for {bkp_file.name}! Stored: {stored_checksum}, Calculated: {calc_sum}")
            sys.exit(1)

    # Integrity check
    with sqlite3.connect(bkp_file) as src_conn:
        integrity = src_conn.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            print(f"Error: SQLite integrity check failed for {bkp_file.name}: {integrity}")
            sys.exit(1)

    print("Integrity check passed.")

    # Create pre-restore snapshot of live DB
    now_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pre_restore_path = backups_dir / f"pre_restore_{now_ts}.db"
    if target_db.exists():
        print(f"Creating pre-restore safety snapshot at {pre_restore_path}...")
        shutil.copy2(target_db, pre_restore_path)

    # Remove -wal and -shm files if present
    for ext in ("-wal", "-shm"):
        extra = Path(str(target_db) + ext)
        if extra.exists():
            try:
                os.remove(extra)
            except Exception as e:
                print(f"Warning removing {extra.name}: {e}")

    # Copy backup over target DB
    print(f"Restoring {bkp_file.name} to {target_db}...")
    shutil.copy2(bkp_file, target_db)

    # Remove any staged pending restore files/markers
    marker_file = storage_dir / "restore_pending.marker"
    pending_db = storage_dir / "restore_pending.db"
    for p in (marker_file, pending_db):
        if p.exists():
            try:
                os.remove(p)
            except Exception:
                pass

    # Record restoration in restore_history
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with sqlite3.connect(target_db) as conn:
            conn.execute(
                """
                INSERT INTO restore_history (restore_id, backup_id, restored_by, restore_type, started_at, completed_at, status, remarks)
                VALUES (?, ?, 'cli_admin', 'Full', ?, ?, 'Completed', 'CLI restore executed while server was stopped.')
                """,
                (f"RST_CLI_{now_ts}", backup_id, now_str, now_str),
            )
            conn.commit()
    except Exception as e:
        print(f"Note: Could not update restore_history: {e}")

    print(f"Database successfully restored from '{backup_name}'.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Campus Pulse offline database restore CLI")
    parser.add_argument("backup_id", help="Backup ID, file name, or backup name to restore")
    parser.add_argument("--db-path", default=None, help="Path to campus_pulse.db (defaults to storage/campus_pulse.db)")
    args = parser.parse_args()

    restore_db_cli(args.backup_id, db_path=args.db_path)
