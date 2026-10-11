import json
import sqlite3
from pathlib import Path

from utils.helper import generate_id, now_string


class ConfigService:
    CATEGORIES = (
        "General",
        "Complaint",
        "Security",
        "Notification",
        "File Upload",
        "Authentication",
        "Analytics",
        "Maintenance",
    )
    SETTING_TYPES = ("String", "Integer", "Boolean", "Float", "JSON")

    DEFAULTS = [
        # General Settings
        (
            "app_name",
            "Campus Pulse",
            "String",
            "General",
            "Application Name displayed across system headers",
            1,
            0,
        ),
        (
            "app_logo_url",
            "/logo.png",
            "String",
            "General",
            "Application Logo URL",
            1,
            0,
        ),
        (
            "support_email",
            "support@campuspulse.edu",
            "String",
            "General",
            "Official support email for system help",
            1,
            0,
        ),
        (
            "support_phone",
            "+1 (800) 555-0199",
            "String",
            "General",
            "Support contact phone number",
            1,
            0,
        ),
        (
            "default_timezone",
            "UTC",
            "String",
            "General",
            "Default system timezone for display",
            1,
            0,
        ),
        (
            "default_language",
            "en",
            "String",
            "General",
            "Default system language",
            1,
            0,
        ),
        (
            "default_date_format",
            "YYYY-MM-DD",
            "String",
            "General",
            "System date format pattern",
            1,
            0,
        ),
        (
            "default_time_format",
            "12H",
            "String",
            "General",
            "System time format (12H or 24H)",
            1,
            0,
        ),
        # Complaint Settings
        (
            "default_sla_days",
            "4",
            "Integer",
            "Complaint",
            "Default SLA resolution window in days",
            1,
            0,
        ),
        (
            "max_reopen_count",
            "3",
            "Integer",
            "Complaint",
            "Maximum times a student can reopen a complaint",
            1,
            0,
        ),
        (
            "auto_close_days",
            "5",
            "Integer",
            "Complaint",
            "Auto-close complaints after verification wait",
            1,
            0,
        ),
        (
            "allow_community_complaints",
            "true",
            "Boolean",
            "Complaint",
            "Allow community visible complaints",
            1,
            0,
        ),
        (
            "allow_anonymous_complaints",
            "false",
            "Boolean",
            "Complaint",
            "Allow anonymous complaint submissions",
            1,
            0,
        ),
        (
            "max_description_length",
            "2000",
            "Integer",
            "Complaint",
            "Maximum characters allowed in description",
            1,
            0,
        ),
        (
            "min_description_length",
            "10",
            "Integer",
            "Complaint",
            "Minimum characters required in description",
            1,
            0,
        ),
        # Security Settings
        (
            "password_min_length",
            "8",
            "Integer",
            "Security",
            "Minimum password length required",
            1,
            0,
        ),
        (
            "password_require_uppercase",
            "true",
            "Boolean",
            "Security",
            "Require uppercase letter in password",
            1,
            0,
        ),
        (
            "password_require_lowercase",
            "true",
            "Boolean",
            "Security",
            "Require lowercase letter in password",
            1,
            0,
        ),
        (
            "password_require_number",
            "true",
            "Boolean",
            "Security",
            "Require number in password",
            1,
            0,
        ),
        (
            "password_require_special",
            "true",
            "Boolean",
            "Security",
            "Require special character in password",
            1,
            0,
        ),
        (
            "max_failed_login_attempts",
            "5",
            "Integer",
            "Security",
            "Lockout trigger attempt count",
            1,
            0,
        ),
        (
            "account_lock_duration_minutes",
            "30",
            "Integer",
            "Security",
            "Account lockout period in minutes",
            1,
            0,
        ),
        (
            "session_timeout_minutes",
            "60",
            "Integer",
            "Security",
            "Inactivity session expiration in minutes",
            1,
            0,
        ),
        # Notification Settings
        (
            "enable_email_notifications",
            "true",
            "Boolean",
            "Notification",
            "Enable email notification dispatch",
            1,
            1,
        ),
        (
            "enable_push_notifications",
            "false",
            "Boolean",
            "Notification",
            "Enable push notifications for mobile app",
            1,
            0,
        ),
        (
            "enable_in_app_notifications",
            "true",
            "Boolean",
            "Notification",
            "Enable in-app web panel notifications",
            1,
            0,
        ),
        (
            "critical_notification_sound",
            "alert.mp3",
            "String",
            "Notification",
            "Sound alert file for critical events",
            1,
            0,
        ),
        (
            "notification_retention_days",
            "90",
            "Integer",
            "Notification",
            "Retention period for notification logs",
            1,
            0,
        ),
        (
            "offline_queue_limit",
            "100",
            "Integer",
            "Notification",
            "Maximum offline notifications queued per user",
            1,
            0,
        ),
        # File Upload Settings
        (
            "max_attachment_size_mb",
            "5",
            "Integer",
            "File Upload",
            "Maximum attachment upload size in megabytes",
            1,
            0,
        ),
        (
            "max_attachments_per_upload",
            "5",
            "Integer",
            "File Upload",
            "Maximum files permitted in a single upload batch",
            1,
            0,
        ),
        (
            "max_attachments_per_complaint",
            "20",
            "Integer",
            "File Upload",
            "Maximum cumulative attachments per complaint",
            1,
            0,
        ),
        (
            "allowed_file_types",
            "jpg,jpeg,png,pdf",
            "String",
            "File Upload",
            "Comma separated allowed file extensions",
            1,
            0,
        ),
        (
            "image_compression_enabled",
            "true",
            "Boolean",
            "File Upload",
            "Compress image uploads automatically",
            1,
            0,
        ),
        (
            "virus_scan_enabled",
            "false",
            "Boolean",
            "File Upload",
            "Scan file uploads for malicious content",
            1,
            0,
        ),
        # Authentication Settings
        (
            "access_token_expiry_minutes",
            "15",
            "Integer",
            "Authentication",
            "JWT access token lifetime in minutes",
            1,
            0,
        ),
        (
            "refresh_token_expiry_days",
            "7",
            "Integer",
            "Authentication",
            "JWT refresh token lifetime in days",
            1,
            0,
        ),
        (
            "remember_me_duration_days",
            "30",
            "Integer",
            "Authentication",
            "Remember me duration in days",
            1,
            0,
        ),
        (
            "force_first_login_password_change",
            "true",
            "Boolean",
            "Authentication",
            "Require password change upon first login",
            1,
            0,
        ),
        (
            "max_active_sessions_per_user",
            "3",
            "Integer",
            "Authentication",
            "Maximum active sessions per user account",
            1,
            0,
        ),
        # Analytics Settings
        (
            "dashboard_refresh_interval_seconds",
            "30",
            "Integer",
            "Analytics",
            "Dashboard auto-refresh polling interval",
            1,
            0,
        ),
        (
            "report_cache_duration_minutes",
            "10",
            "Integer",
            "Analytics",
            "Executive report query cache expiration",
            1,
            0,
        ),
        (
            "default_analytics_date_range_days",
            "30",
            "Integer",
            "Analytics",
            "Default date range filter in days",
            1,
            0,
        ),
        (
            "enable_live_dashboard_updates",
            "true",
            "Boolean",
            "Analytics",
            "Live WebSocket dashboard metrics updates",
            1,
            0,
        ),
        # Maintenance Settings
        (
            "maintenance_mode",
            "false",
            "Boolean",
            "Maintenance",
            "System maintenance mode flag",
            1,
            0,
        ),
        (
            "maintenance_message",
            "System is undergoing scheduled maintenance. Please try again later.",
            "String",
            "Maintenance",
            "Message displayed during maintenance mode",
            1,
            0,
        ),
        (
            "allow_admin_login_during_maintenance",
            "true",
            "Boolean",
            "Maintenance",
            "Permit Administrator logins when maintenance is active",
            1,
            0,
        ),
        (
            "scheduled_maintenance_start",
            "",
            "String",
            "Maintenance",
            "Scheduled maintenance start ISO timestamp",
            1,
            0,
        ),
        (
            "scheduled_maintenance_end",
            "",
            "String",
            "Maintenance",
            "Scheduled maintenance end ISO timestamp",
            1,
            0,
        ),
    ]

    def __init__(self, db_path="storage/campus_pulse.db"):
        self.db_path = Path(db_path)
        self._ensure_seeds()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_seeds(self):
        now = now_string()
        with self._connect() as conn:
            for key, val, stype, cat, desc, edit, restart in self.DEFAULTS:
                row = conn.execute(
                    "SELECT setting_key FROM system_settings WHERE setting_key = ?",
                    (key,),
                ).fetchone()
                if not row:
                    sid = generate_id("CFG")
                    conn.execute(
                        """
                        INSERT INTO system_settings (setting_id, setting_key, setting_value, setting_type, category, description, is_editable, requires_restart, created_at, updated_at, updated_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'system')
                        """,
                        (sid, key, val, stype, cat, desc, edit, restart, now, now),
                    )

    # ==========================================
    # VALIDATION
    # ==========================================
    def validate_value(self, val_str, setting_type):
        if setting_type == "Integer":
            try:
                int(val_str)
            except (ValueError, TypeError):
                raise ValueError(f"Value '{val_str}' must be a valid integer.")
        elif setting_type == "Float":
            try:
                float(val_str)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Value '{val_str}' must be a valid floating-point number."
                )
        elif setting_type == "Boolean":
            if str(val_str).lower() not in ("true", "false", "1", "0"):
                raise ValueError(
                    f"Value '{val_str}' must be a boolean ('true' or 'false')."
                )
        elif setting_type == "JSON":
            try:
                json.loads(val_str)
            except Exception:
                raise ValueError(f"Value '{val_str}' must be a valid JSON string.")

    # ==========================================
    # GETTERS
    # ==========================================
    def get_setting(self, key, default=None):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT setting_value FROM system_settings WHERE LOWER(setting_key) = LOWER(?)",
                (key,),
            ).fetchone()
            if row:
                return (
                    row["setting_value"]
                    if (
                        "setting_value" in row.keys()
                        and row["setting_value"] is not None
                    )
                    else row.get("value", default)
                )
            return default

    def get_setting_dict(self, key):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM system_settings WHERE LOWER(setting_key) = LOWER(?)", (key,)
            ).fetchone()
            if not row:
                return None
            return dict(row)

    def list_settings_by_category(self, category=None):
        query = "SELECT * FROM system_settings WHERE 1=1"
        params = []
        if category:
            query += " AND LOWER(category) = LOWER(?)"
            params.append(category)
        query += " ORDER BY category ASC, setting_key ASC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def get_all_grouped(self):
        settings = self.list_settings_by_category()
        grouped = {}
        for s in settings:
            cat = s["category"] or "General"
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append(s)
        return grouped

    # ==========================================
    # UPDATES & TRANSACTIONS
    # ==========================================
    def update_setting(
        self, key, new_val, performer_id="system", ip_address=None, reason=""
    ):
        target = self.get_setting_dict(key)
        if not target:
            raise ValueError(f"Setting key '{key}' does not exist.")

        if not target["is_editable"]:
            raise ValueError(
                f"Setting '{key}' is a system-managed setting and cannot be edited."
            )

        val_str = str(new_val)
        self.validate_value(val_str, target["setting_type"])

        old_val = (
            target["setting_value"]
            if "setting_value" in target
            else target.get("value", "")
        )
        now = now_string()

        with self._connect() as conn:
            # Update setting
            conn.execute(
                "UPDATE system_settings SET setting_value = ?, updated_at = ?, updated_by = ? WHERE setting_key = ?",
                (val_str, now, performer_id, key),
            )

            # Insert immutable audit log record
            aid = generate_id("AUD")
            conn.execute(
                """
                INSERT INTO setting_audit_logs (audit_id, setting_key, old_value, new_value, changed_by, changed_at, ip_address, reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (aid, key, old_val, val_str, performer_id, now, ip_address, reason),
            )

        return self.get_setting_dict(key)

    def bulk_update(
        self, settings_list, performer_id="system", ip_address=None, reason=""
    ):
        """Transactional bulk update of multiple settings."""
        # 1. Validate all settings first before applying
        validated_items = []
        for item in settings_list:
            key = item.get("setting_key") or item.get("key")
            val = item.get("setting_value") or item.get("value")
            if not key:
                raise ValueError("Each bulk update item must specify setting_key.")

            target = self.get_setting_dict(key)
            if not target:
                raise ValueError(f"Setting '{key}' not found.")
            if not target["is_editable"]:
                raise ValueError(f"Setting '{key}' is not editable.")

            val_str = str(val)
            self.validate_value(val_str, target["setting_type"])
            old_val = (
                target["setting_value"]
                if "setting_value" in target
                else target.get("value", "")
            )
            validated_items.append((key, old_val, val_str))

        # 2. Execute transactional update
        now = now_string()
        with self._connect() as conn:
            for key, old_val, val_str in validated_items:
                conn.execute(
                    "UPDATE system_settings SET setting_value = ?, updated_at = ?, updated_by = ? WHERE setting_key = ?",
                    (val_str, now, performer_id, key),
                )
                aid = generate_id("AUD")
                conn.execute(
                    """
                    INSERT INTO setting_audit_logs (audit_id, setting_key, old_value, new_value, changed_by, changed_at, ip_address, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        aid,
                        key,
                        old_val,
                        val_str,
                        performer_id,
                        now,
                        ip_address,
                        reason or "Bulk Settings Update",
                    ),
                )

        return self.get_all_grouped()

    def reset_category(self, category, performer_id="system"):
        cat_defaults = [d for d in self.DEFAULTS if d[3].lower() == category.lower()]
        if not cat_defaults:
            raise ValueError(f"Category '{category}' has no reset defaults.")

        bulk_payload = [
            {"setting_key": d[0], "setting_value": d[1]} for d in cat_defaults
        ]
        return self.bulk_update(
            bulk_payload, performer_id=performer_id, reason=f"Reset Category {category}"
        )

    def reset_all(self, performer_id="system"):
        bulk_payload = [
            {"setting_key": d[0], "setting_value": d[1]} for d in self.DEFAULTS
        ]
        return self.bulk_update(
            bulk_payload, performer_id=performer_id, reason="Reset All System Settings"
        )
