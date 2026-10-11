import hashlib
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
        db_path="storage/campus_pulse.db",
    ):
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
            with sqlite3.connect(self.db_path) as dst_conn:
                src_conn.backup(dst_conn)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO restore_history (restore_id, backup_id, restored_by, restore_type, started_at, completed_at, status, remarks)
                VALUES (?, ?, ?, ?, ?, ?, 'Completed', 'System database restored successfully.')
                """,
                (rid, backup_id, restored_by, bkp["backup_type"], now, now),
            )

        if self.notification_service:
            self.notification_service.publish(
                receiver_id=restored_by,
                title="Database Restoration Completed",
                message=f"Database restored from backup '{bkp['backup_name']}'.",
                module="Backup & Restore",
                notification_type="restore_completed",
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
                description=f"Restored system database from backup '{bkp['backup_name']}'",
            )

        return {
            "restore_id": rid,
            "status": "Completed",
            "backup_name": bkp["backup_name"],
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
