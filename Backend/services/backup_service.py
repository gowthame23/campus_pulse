import hashlib
import json
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from utils.helper import generate_id, now_string


class BackupService:
    BACKUP_TYPES = (
        "Full",
        "Incremental",
        "Differential",
        "Configuration",
        "FilesOnly",
        "DatabaseOnly",
    )
    STATUSES = (
        "Pending",
        "Running",
        "Completed",
        "Failed",
        "Restoring",
        "Restored",
        "Expired",
        "Deleted",
    )
    STORAGE_PROVIDERS = (
        "Local",
        "NAS",
        "Amazon S3",
        "Azure Blob",
        "Google Cloud Storage",
    )

    def __init__(
        self,
        notification_service=None,
        audit_service=None,
        db_path=None,
    ):
        if db_path is None:
            db_path = os.getenv("DATABASE_PATH", "storage/campus_pulse.db")
        self.db_path = Path(db_path)
        self.backup_dir = (self.db_path.parent / "backups").resolve()
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.notification_service = notification_service
        self.audit_service = audit_service
        self._ensure_seeds()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_seeds(self):
        with self._connect() as conn:
            row = conn.execute("SELECT backup_id FROM backups LIMIT 1").fetchone()
            if not row:
                now = now_string()
                # Create initial database snapshot file
                b_id = "BKP_SEED_01"
                b_name = "CampusPulse_Full_System_Backup_v1"
                b_path = self.backup_dir / f"{b_name}.db"

                if not os.path.exists(b_path):
                    shutil.copy2(self.db_path, b_path)

                checksum = self._calculate_checksum(b_path)
                size = os.path.getsize(b_path)
                expires = (datetime.now() + timedelta(days=30)).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                conn.execute(
                    """
                    INSERT INTO backups
                    (backup_id, backup_name, backup_type, status, storage_location, file_name, file_path, file_size, checksum, encrypted, compression_enabled, created_by, created_at, completed_at, expires_at, is_deleted)
                    VALUES (?, ?, 'Full', 'Completed', 'Local', ?, ?, ?, ?, 0, 1, 'system', ?, ?, ?, 0)
                    """,
                    (
                        b_id,
                        b_name,
                        f"{b_name}.db",
                        str(b_path),
                        size,
                        checksum,
                        now,
                        now,
                        expires,
                    ),
                )

                conn.execute(
                    "INSERT INTO backup_schedules (schedule_id, backup_type, frequency, retention_days, storage_provider, enabled, created_at) VALUES ('SCH_BKP_01', 'Full', 'Daily', 30, 'Local', 1, ?)",
                    (now,),
                )

    def _calculate_checksum(self, filepath):
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _backup_path(self, stored_path):
        path = Path(stored_path).resolve()
        backup_root = self.backup_dir.resolve()
        if backup_root not in path.parents:
            raise ValueError("Backup file is outside the backup storage directory.")
        return path

    # ==========================================
    # 1. MANUAL BACKUP CREATION
    # ==========================================
    def create_backup(
        self, backup_name, backup_type="Full", created_by="system", remarks=""
    ):
        if backup_type not in self.BACKUP_TYPES:
            raise ValueError(f"Invalid backup type. Allowed: {', '.join(self.BACKUP_TYPES)}")
        bid = generate_id("BKP")
        now = now_string()
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{backup_type.lower()}_backup_{timestamp_str}_{bid}.db"
        filepath = self.backup_dir / filename

        if not os.path.exists(self.db_path):
            with sqlite3.connect(self.db_path) as conn:
                pass
        with sqlite3.connect(self.db_path) as src_conn, sqlite3.connect(filepath) as dst_conn:
            src_conn.backup(dst_conn)

        checksum = self._calculate_checksum(filepath)
        size = os.path.getsize(filepath)
        expires = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO backups
                (backup_id, backup_name, backup_type, status, storage_location, file_name, file_path, file_size, checksum, encrypted, compression_enabled, created_by, created_at, completed_at, expires_at, remarks, is_deleted)
                VALUES (?, ?, ?, 'Completed', 'Local', ?, ?, ?, ?, 0, 1, ?, ?, ?, ?, ?, 0)
                """,
                (
                    bid,
                    backup_name.strip(),
                    backup_type,
                    filename,
                    str(filepath),
                    size,
                    checksum,
                    created_by,
                    now,
                    now,
                    expires,
                    remarks,
                ),
            )

        bkp = self.get_backup(bid)

        if self.notification_service:
            self.notification_service.publish(
                receiver_id=created_by,
                title="System Backup Completed",
                message=f"Backup '{backup_name}' ({size // 1024} KB) created successfully.",
                module="Backup & Restore",
                notification_type="backup_completed",
                reference_type="Backup",
                reference_id=bid,
                priority="Medium",
            )

        if self.audit_service:
            self.audit_service.log_event(
                module="Backup & Restore",
                entity_type="Backup",
                entity_id=bid,
                action="CREATE",
                performed_by=created_by,
                description=f"Created {backup_type} backup '{backup_name}'",
            )

        return bkp

    def list_backups(self, backup_type=None, status_filter=None):
        query = "SELECT * FROM backups WHERE is_deleted = 0"
        params = []
        if backup_type:
            query += " AND backup_type = ?"
            params.append(backup_type)
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)
        query += " ORDER BY created_at DESC"
        with self._connect() as conn:
            return [dict(r) for r in conn.execute(query, params).fetchall()]

    def get_backup(self, backup_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM backups WHERE backup_id = ? AND is_deleted = 0",
                (backup_id,),
            ).fetchone()
            return dict(row) if row else None

    def get_backup_file_path(self, backup_id):
        bkp = self.get_backup(backup_id)
        if not bkp:
            raise ValueError("Backup archive not found.")
        filepath = self._backup_path(bkp["file_path"])
        if not filepath.exists():
            raise ValueError("Backup file missing on disk.")
        return bkp, filepath

    # ==========================================
    # 2. VERIFICATION & RESTORE ENGINE
    # ==========================================
    def verify_backup(self, backup_id):
        bkp = self.get_backup(backup_id)
        if not bkp:
            raise ValueError("Backup archive not found.")

        filepath = self._backup_path(bkp["file_path"])
        if not filepath.exists():
            return {"valid": False, "message": "Backup file missing on disk."}

        current_checksum = self._calculate_checksum(filepath)
        valid = current_checksum == bkp["checksum"]

        if self.audit_service:
            self.audit_service.log_event(
                module="Backup & Restore",
                entity_type="Backup",
                entity_id=backup_id,
                action="VERIFY",
                performed_by="system",
                description=f"Verified SHA-256 checksum for backup '{bkp['backup_name']}' (Result: {valid})",
            )

        return {
            "valid": valid,
            "backup_name": bkp["backup_name"],
            "stored_checksum": bkp["checksum"],
            "calculated_checksum": current_checksum,
        }

    def restore_backup(self, backup_id, restored_by):
        bkp = self.get_backup(backup_id)
        if not bkp:
            raise ValueError("Backup archive not found.")

        verification = self.verify_backup(backup_id)
        if not verification["valid"]:
            raise ValueError("Backup verification failed. Checksum mismatch.")

        rid = generate_id("RST")
        now = now_string()

        source_path = self._backup_path(bkp["file_path"])
        with sqlite3.connect(source_path) as src_conn:
            integrity = src_conn.execute("PRAGMA integrity_check").fetchone()[0]
            if integrity != "ok":
                raise ValueError("Backup database failed integrity check.")

        # Stage to pending restore file and marker rather than overwriting live DB
        pending_db = self.db_path.parent / "restore_pending.db"
        marker_file = self.db_path.parent / "restore_pending.marker"

        shutil.copy2(source_path, pending_db)
        marker_payload = {
            "restore_id": rid,
            "backup_id": backup_id,
            "backup_name": bkp["backup_name"],
            "restored_by": restored_by,
            "scheduled_at": now,
        }
        with open(marker_file, "w", encoding="utf-8") as mf:
            json.dump(marker_payload, mf, indent=2)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO restore_history (restore_id, backup_id, restored_by, restore_type, started_at, completed_at, status, remarks)
                VALUES (?, ?, ?, ?, ?, NULL, 'Scheduled', 'Restore scheduled. Restart the server to apply.')
                """,
                (rid, backup_id, restored_by, bkp["backup_type"], now),
            )

        if self.notification_service:
            self.notification_service.publish(
                receiver_id=restored_by,
                title="Database Restoration Scheduled",
                message=f"Restore scheduled from backup '{bkp['backup_name']}'. Restart the server to apply.",
                module="Backup & Restore",
                notification_type="restore_scheduled",
                reference_type="Restore",
                reference_id=rid,
                priority="High",
            )

        if self.audit_service:
            self.audit_service.log_event(
                module="Backup & Restore",
                entity_type="Backup",
                entity_id=backup_id,
                action="RESTORE",
                performed_by=restored_by,
                description=f"Scheduled restore from backup '{bkp['backup_name']}'",
            )

        return {
            "restore_id": rid,
            "status": "Scheduled",
            "backup_name": bkp["backup_name"],
            "message": "Restore scheduled. Restart the server to apply.",
        }

    def list_restore_history(self):
        with self._connect() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    "SELECT r.*, b.backup_name, b.backup_type FROM restore_history r JOIN backups b ON r.backup_id = b.backup_id ORDER BY r.started_at DESC"
                ).fetchall()
            ]

    # ==========================================
    # 3. SCHEDULES & ANALYTICS
    # ==========================================
    def list_schedules(self):
        with self._connect() as conn:
            return [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM backup_schedules WHERE enabled = 1"
                ).fetchall()
            ]

    def get_summary(self):
        with self._connect() as conn:
            total_bkp = conn.execute(
                "SELECT COUNT(*) FROM backups WHERE is_deleted = 0"
            ).fetchone()[0]
            success_bkp = conn.execute(
                "SELECT COUNT(*) FROM backups WHERE status = 'Completed' AND is_deleted = 0"
            ).fetchone()[0]
            failed_bkp = conn.execute(
                "SELECT COUNT(*) FROM backups WHERE status = 'Failed' AND is_deleted = 0"
            ).fetchone()[0]
            storage_bytes = (
                conn.execute(
                    "SELECT SUM(file_size) FROM backups WHERE is_deleted = 0"
                ).fetchone()[0]
                or 0
            )
            return {
                "total_backups": total_bkp,
                "successful_backups": success_bkp,
                "failed_backups": failed_bkp,
                "storage_used_mb": round(storage_bytes / (1024 * 1024), 2),
            }


def apply_pending_restore(db_path=None):
    """
    Checks for pending restore marker and pending db file on startup.
    If found, backs up current DB to pre_restore_<timestamp>.db, removes WAL/SHM,
    and moves pending db into place before any connections are opened.
    """
    if db_path is None:
        db_path = os.getenv("DATABASE_PATH", "storage/campus_pulse.db")

    target_path = Path(db_path).resolve()
    db_dir = target_path.parent
    marker_file = db_dir / "restore_pending.marker"
    pending_db = db_dir / "restore_pending.db"

    if not marker_file.exists() or not pending_db.exists():
        return False

    try:
        with open(marker_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except Exception:
        metadata = {}

    backups_dir = db_dir / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pre_restore_path = backups_dir / f"pre_restore_{ts}.db"

    # Backup current DB
    if target_path.exists():
        try:
            shutil.copy2(target_path, pre_restore_path)
        except Exception as e:
            print(f"[Safe Restore] Warning: failed to create pre-restore snapshot: {e}")

    # Remove -wal and -shm files if present
    for ext in ("-wal", "-shm"):
        extra_file = Path(str(target_path) + ext)
        if extra_file.exists():
            try:
                os.remove(extra_file)
            except Exception:
                pass

    # Move staged pending DB over active DB
    shutil.move(str(pending_db), str(target_path))

    # Remove marker file
    try:
        os.remove(marker_file)
    except Exception:
        pass

    # Mark restore as Completed in the newly restored database
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    restore_id = metadata.get("restore_id")
    try:
        with sqlite3.connect(target_path) as conn:
            if restore_id:
                conn.execute(
                    "UPDATE restore_history SET status = 'Completed', completed_at = ?, remarks = 'System database restored successfully.' WHERE restore_id = ?",
                    (now, restore_id),
                )
            else:
                conn.execute(
                    "UPDATE restore_history SET status = 'Completed', completed_at = ?, remarks = 'System database restored successfully.' WHERE status = 'Scheduled'",
                    (now,),
                )
            conn.commit()
    except Exception:
        pass

    print(f"[Safe Restore] Successfully restored database from staged backup (Pre-restore saved to {pre_restore_path.name})")
    return True
