import hashlib
import json
import sqlite3
from io import BytesIO
from pathlib import Path

from utils.helper import generate_id, now_string, parse_date


class AttachmentService:
    def __init__(self, db_path="storage/campus_pulse.db"):
        self.db_path = Path(db_path)
        self.storage_dir = (self.db_path.parent / "attachments").resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_columns()

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_columns(self):
        with self._connect() as conn:
            try:
                conn.execute(
                    "ALTER TABLE attachments ADD COLUMN is_deleted INTEGER DEFAULT 0"
                )
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE attachments ADD COLUMN deleted_at TEXT")
            except Exception:
                pass
            try:
                conn.execute("ALTER TABLE attachments ADD COLUMN deleted_by TEXT")
            except Exception:
                pass

    def _format_row(self, row):
        if not row:
            return None
        d = dict(row)
        if isinstance(d.get("flags"), str):
            try:
                d["flags"] = json.loads(d["flags"])
            except Exception:
                d["flags"] = [d["flags"]] if d["flags"] else []
        elif d.get("flags") is None:
            d["flags"] = []
        return d

    def list_attachments(self, complaint_id):
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM attachments WHERE complaint_id = ? AND (is_deleted = 0 OR is_deleted IS NULL) ORDER BY uploaded_at ASC",
                (complaint_id,),
            ).fetchall()
            return [self._format_row(r) for r in rows]

    def get_attachment(self, attachment_id):
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM attachments WHERE attachment_id = ? AND (is_deleted = 0 OR is_deleted IS NULL)",
                (attachment_id,),
            ).fetchone()
            return self._format_row(row)

    def detect_flags(
        self,
        content_bytes=b"",
        exif_taken_at=None,
        job_started_at=None,
        complaint_id=None,
        sha256_hash=None,
        matching_other_complaint=None,
    ):
        flags = []
        file_sha256 = sha256_hash or (hashlib.sha256(content_bytes).hexdigest() if content_bytes else None)
        if matching_other_complaint:
            flags.append("REUSED")
        elif file_sha256 and complaint_id:
            with self._connect() as conn:
                dup_row = conn.execute(
                    "SELECT complaint_id FROM attachments WHERE sha256 = ? AND complaint_id != ? AND (is_deleted = 0 OR is_deleted IS NULL) LIMIT 1",
                    (file_sha256, complaint_id),
                ).fetchone()
                if dup_row:
                    flags.append("REUSED")

        if exif_taken_at and job_started_at:
            dt_str = str(exif_taken_at).strip()
            if " " in dt_str:
                d_part, t_part = dt_str.split(" ", 1)
                clean_dt = f"{d_part.replace(':', '-') } {t_part}"
            else:
                clean_dt = dt_str.replace(":", "-")
            exif_dt = parse_date(clean_dt)
            job_dt = parse_date(job_started_at)
            if exif_dt and job_dt and exif_dt < job_dt:
                flags.append("OLDER_THAN_JOB")
        return flags

    def create_attachment(
        self,
        complaint_id,
        uploaded_by,
        uploader_role,
        category,
        filename,
        file_bytes,
        source="gallery",
        kind=None,
        job_started_at=None,
    ):
        ext = filename.split(".")[-1].lower() if "." in filename else ""
        if ext not in ("jpg", "jpeg", "png", "pdf"):
            raise ValueError("Only JPG, JPEG, PNG, and PDF files are allowed.")

        file_size = len(file_bytes)
        if file_size > 5 * 1024 * 1024:
            raise ValueError("File exceeds maximum allowed size of 5 MB.")

        # File magic byte signature validation (defense-in-depth)
        if ext in ("jpg", "jpeg") and not file_bytes.startswith(b"\xff\xd8\xff"):
            raise ValueError("Invalid file content signature for JPEG image.")
        elif ext == "png" and not file_bytes.startswith(b"\x89PNG"):
            raise ValueError("Invalid file content signature for PNG image.")
        elif ext == "pdf" and not file_bytes.startswith(b"%PDF"):
            raise ValueError("Invalid file content signature for PDF document.")

        # Script execution payload inspection
        content_preview = file_bytes[:2048].lower()
        if any(tag in content_preview for tag in (b"<script", b"<?php", b"<%")):
            raise ValueError("File content contains prohibited executable script elements.")

        existing = self.list_attachments(complaint_id)
        if len(existing) >= 20:
            raise ValueError("Maximum complaint limit of 20 images reached.")

        # SHA-256 computation
        file_sha256 = hashlib.sha256(file_bytes).hexdigest()
        flags = self.detect_flags(content_bytes=file_bytes, complaint_id=complaint_id)

        # EXIF analysis for JPEG
        exif_taken_at = None
        if ext in ("jpg", "jpeg"):
            try:
                from PIL import Image
                img = Image.open(BytesIO(file_bytes))
                exif = img.getexif()
                if exif:
                    dt_val = exif.get(36867) or exif.get(306)
                    if dt_val:
                        exif_taken_at = str(dt_val)
                        clean_dt = str(dt_val).replace(":", "-", 2)
                        exif_dt = parse_date(clean_dt)
                        job_dt = parse_date(job_started_at) if job_started_at else None
                        if exif_dt and job_dt and exif_dt < job_dt:
                            flags.append("OLDER_THAN_JOB")
            except Exception:
                pass

        # Determine kind if not provided
        if not kind:
            cat_l = (category or "").lower()
            if any(k in cat_l for k in ("before", "initial", "student")):
                kind = "before"
            elif any(k in cat_l for k in ("after", "repair", "fix")):
                kind = "after"
            else:
                kind = "progress"

        attachment_id = generate_id("ATT")
        uploaded_at = now_string()

        category_clean = category.lower().replace(" ", "_")
        stored_filename = (
            f"complaint_{complaint_id}_{category_clean}_{attachment_id}.{ext}"
        )

        storage_dir = self.storage_dir
        file_path = storage_dir / stored_filename

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        file_path_str = f"/static/attachments/{stored_filename}"
        flags_str = json.dumps(flags)

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO attachments (
                    attachment_id, complaint_id, uploaded_by, uploader_role, category,
                    original_filename, stored_filename, file_path, file_size, uploaded_at,
                    is_deleted, source, sha256, exif_taken_at, kind, flags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?)
                """,
                (
                    attachment_id,
                    complaint_id,
                    uploaded_by,
                    uploader_role,
                    category,
                    filename,
                    stored_filename,
                    file_path_str,
                    file_size,
                    uploaded_at,
                    source or "gallery",
                    file_sha256,
                    exif_taken_at,
                    kind,
                    flags_str,
                ),
            )

        return {
            "attachment_id": attachment_id,
            "complaint_id": complaint_id,
            "uploaded_by": uploaded_by,
            "uploader_role": uploader_role,
            "category": category,
            "original_filename": filename,
            "stored_filename": stored_filename,
            "file_path": file_path_str,
            "file_size": file_size,
            "uploaded_at": uploaded_at,
            "source": source or "gallery",
            "sha256": file_sha256,
            "exif_taken_at": exif_taken_at,
            "kind": kind,
            "flags": flags,
        }

    def delete_attachment(self, attachment_id, user, complaint_status):
        attachment = self.get_attachment(attachment_id)
        if not attachment:
            raise ValueError("Attachment not found.")

        u_role = (user.role or "").lower()

        if u_role == "student":
            if attachment["uploaded_by"] != user.user_id:
                raise PermissionError(
                    "Students can only delete their own uploaded images."
                )
            if (complaint_status or "").lower() != "submitted":
                raise ValueError(
                    "Students can only delete images while the complaint is in Submitted status."
                )
        elif u_role not in ("administrator", "app_manager"):
            raise PermissionError(
                "Only students can delete their own uploaded images in Submitted status."
            )

        # Soft Delete metadata in DB (keep file on disk for audit trail)
        with self._connect() as connection:
            connection.execute(
                "UPDATE attachments SET is_deleted = 1, deleted_at = ?, deleted_by = ? WHERE attachment_id = ?",
                (now_string(), user.user_id, attachment_id),
            )

        return attachment
