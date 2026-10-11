import json
import sqlite3
from pathlib import Path


from storage.migrations import run_migrations


class SQLiteRepository:
    def __init__(self, db_path, default_data):
        self.path = Path(db_path)
        self.default_data = default_data
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()
        run_migrations(str(self.path))
        if self._is_empty():
            self.save(default_data)

    def _connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize_schema(self):
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    first_login INTEGER NOT NULL,
                    active INTEGER NOT NULL,
                    department_id TEXT,
                    location_id TEXT,
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS departments (
                    department_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    sla_days INTEGER NOT NULL,
                    complaint_types TEXT NOT NULL,
                    coordinator_id TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    archived INTEGER NOT NULL DEFAULT 0,
                    location_id TEXT
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS location_types (
                    type_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS locations (
                    location_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    location_type TEXT,
                    in_charge_id TEXT,
                    coordinator_id TEXT,
                    app_manager_id TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    archived INTEGER NOT NULL DEFAULT 0
                )
                """)
            try:
                connection.execute("ALTER TABLE locations ADD COLUMN location_type TEXT")
            except Exception:
                pass
            try:
                connection.execute("ALTER TABLE locations ADD COLUMN coordinator_id TEXT")
            except Exception:
                pass
            try:
                connection.execute("ALTER TABLE locations ADD COLUMN app_manager_id TEXT")
            except Exception:
                pass
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_locations_app_mgr ON locations(app_manager_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_locations_in_charge ON locations(in_charge_id)"
            )
            connection.execute("""
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
                    reopen_count INTEGER NOT NULL,
                    auto_closed INTEGER NOT NULL,
                    escalated INTEGER NOT NULL,
                    admin_notified INTEGER NOT NULL,
                    resolution_notes TEXT NOT NULL,
                    verification_reports TEXT NOT NULL,
                    history TEXT NOT NULL,
                    archived INTEGER NOT NULL DEFAULT 0
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    audit_id TEXT PRIMARY KEY,
                    module TEXT NOT NULL DEFAULT 'Complaint',
                    entity_type TEXT NOT NULL DEFAULT 'Complaint',
                    entity_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    performed_by TEXT,
                    performed_role TEXT DEFAULT 'System',
                    target_user TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    description TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    request_method TEXT,
                    request_url TEXT,
                    request_id TEXT,
                    status TEXT NOT NULL DEFAULT 'SUCCESS',
                    failure_reason TEXT,
                    created_at TEXT NOT NULL,
                    log_id TEXT,
                    user_id TEXT,
                    target_id TEXT,
                    details TEXT
                )
                """)
            # Column migrations for existing audit_logs table
            for col_def in [
                ("module", "TEXT DEFAULT 'Complaint'"),
                ("entity_type", "TEXT DEFAULT 'Complaint'"),
                ("entity_id", "TEXT"),
                ("performed_by", "TEXT"),
                ("performed_role", "TEXT DEFAULT 'System'"),
                ("target_user", "TEXT"),
                ("old_value", "TEXT"),
                ("new_value", "TEXT"),
                ("description", "TEXT"),
                ("ip_address", "TEXT"),
                ("user_agent", "TEXT"),
                ("request_method", "TEXT"),
                ("request_url", "TEXT"),
                ("request_id", "TEXT"),
                ("status", "TEXT DEFAULT 'SUCCESS'"),
                ("failure_reason", "TEXT"),
            ]:
                try:
                    connection.execute(
                        f"ALTER TABLE audit_logs ADD COLUMN {col_def[0]} {col_def[1]}"
                    )
                except sqlite3.OperationalError:
                    pass
            connection.execute("""
                CREATE TABLE IF NOT EXISTS comments (
                    comment_id TEXT PRIMARY KEY,
                    complaint_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_internal INTEGER NOT NULL DEFAULT 0
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS highlights (
                    highlight_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    target_location TEXT,
                    priority TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expiry_date TEXT
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS system_settings (
                    setting_id TEXT PRIMARY KEY,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT NOT NULL,
                    setting_type TEXT NOT NULL DEFAULT 'String',
                    category TEXT NOT NULL DEFAULT 'General',
                    description TEXT,
                    is_editable INTEGER NOT NULL DEFAULT 1,
                    requires_restart INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    updated_by TEXT NOT NULL DEFAULT 'system'
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS setting_audit_logs (
                    audit_id TEXT PRIMARY KEY,
                    setting_key TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT,
                    changed_by TEXT NOT NULL,
                    changed_at TEXT NOT NULL,
                    ip_address TEXT,
                    reason TEXT
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS master_references (
                    ref_id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    code TEXT NOT NULL,
                    display_label TEXT NOT NULL,
                    sort_order INTEGER DEFAULT 0,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS institutions (
                    institution_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    code TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL DEFAULT 'Active',
                    admin_name TEXT NOT NULL,
                    admin_email TEXT NOT NULL,
                    contact_info TEXT,
                    application_version TEXT NOT NULL DEFAULT '1.0.0',
                    deployment_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_health_check TEXT
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS support_tickets (
                    issue_id TEXT PRIMARY KEY,
                    institution_id TEXT NOT NULL,
                    module TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    error_reference TEXT,
                    priority TEXT NOT NULL DEFAULT 'Medium',
                    status TEXT NOT NULL DEFAULT 'Open',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    resolved_at TEXT,
                    resolution_notes TEXT
                )
                """)
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_master_ref_cat ON master_references(category)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_setting_key ON system_settings(setting_key)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_setting_cat ON system_settings(category)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_setting_audit_key ON setting_audit_logs(setting_key)"
            )

            # Column migrations for existing databases
            for col_def in [
                ("setting_key", "TEXT UNIQUE"),
                ("setting_value", "TEXT"),
                ("setting_type", "TEXT DEFAULT 'String'"),
                ("category", "TEXT DEFAULT 'General'"),
                ("description", "TEXT"),
                ("is_editable", "INTEGER DEFAULT 1"),
                ("requires_restart", "INTEGER DEFAULT 0"),
                ("created_at", "TEXT"),
                ("updated_at", "TEXT"),
                ("updated_by", "TEXT DEFAULT 'system'"),
            ]:
                try:
                    connection.execute(
                        f"ALTER TABLE system_settings ADD COLUMN {col_def[0]} {col_def[1]}"
                    )
                except sqlite3.OperationalError:
                    pass

            connection.execute("""
                CREATE TABLE IF NOT EXISTS attachments (
                    attachment_id TEXT PRIMARY KEY,
                    complaint_id TEXT NOT NULL,
                    uploaded_by TEXT NOT NULL,
                    uploader_role TEXT NOT NULL,
                    category TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    stored_filename TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    uploaded_at TEXT NOT NULL
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS lost_found_items (
                    item_id TEXT PRIMARY KEY,
                    report_type TEXT NOT NULL,
                    reported_by TEXT NOT NULL,
                    assigned_to TEXT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'Other',
                    brand TEXT,
                    color TEXT,
                    serial_number TEXT,
                    unique_identifiers TEXT,
                    estimated_value REAL DEFAULT 0.0,
                    date_lost_found TEXT NOT NULL,
                    time_lost_found TEXT,
                    campus_id TEXT,
                    building_id TEXT,
                    block_id TEXT,
                    floor_id TEXT,
                    room_id TEXT,
                    exact_location TEXT,
                    current_storage_location TEXT,
                    status TEXT NOT NULL DEFAULT 'Reported',
                    visibility TEXT NOT NULL DEFAULT 'Public',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0,
                    deleted_at TEXT,
                    deleted_by TEXT
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS lost_found_images (
                    image_id TEXT PRIMARY KEY,
                    item_id TEXT NOT NULL,
                    uploaded_by TEXT NOT NULL,
                    image_type TEXT NOT NULL DEFAULT 'Overview',
                    image_url TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    FOREIGN KEY (item_id) REFERENCES lost_found_items(item_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS ownership_claims (
                    claim_id TEXT PRIMARY KEY,
                    item_id TEXT NOT NULL,
                    claimed_by TEXT NOT NULL,
                    claim_reason TEXT NOT NULL,
                    proof_description TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    reviewed_by TEXT,
                    reviewed_at TEXT,
                    decision_notes TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (item_id) REFERENCES lost_found_items(item_id)
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS announcements (
                    announcement_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT,
                    content TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'General',
                    priority TEXT NOT NULL DEFAULT 'Normal',
                    created_by TEXT NOT NULL,
                    published_by TEXT,
                    status TEXT NOT NULL DEFAULT 'Draft',
                    visibility TEXT NOT NULL DEFAULT 'Public',
                    requires_acknowledgement INTEGER NOT NULL DEFAULT 0,
                    publish_at TEXT,
                    expire_at TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0,
                    deleted_at TEXT,
                    deleted_by TEXT
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS announcement_targets (
                    target_id TEXT PRIMARY KEY,
                    announcement_id TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_value TEXT NOT NULL,
                    FOREIGN KEY (announcement_id) REFERENCES announcements(announcement_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS announcement_attachments (
                    attachment_id TEXT PRIMARY KEY,
                    announcement_id TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    file_type TEXT NOT NULL,
                    uploaded_by TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    FOREIGN KEY (announcement_id) REFERENCES announcements(announcement_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS announcement_reads (
                    read_id TEXT PRIMARY KEY,
                    announcement_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    read_at TEXT NOT NULL,
                    device TEXT,
                    ip_address TEXT,
                    UNIQUE (announcement_id, user_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS announcement_acknowledgements (
                    ack_id TEXT PRIMARY KEY,
                    announcement_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    acknowledged_at TEXT NOT NULL,
                    remarks TEXT,
                    UNIQUE (announcement_id, user_id)
                )
                """)


            connection.execute("""
                CREATE TABLE IF NOT EXISTS feedback_templates (
                    template_id TEXT PRIMARY KEY,
                    feedback_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS feedback_questions (
                    question_id TEXT PRIMARY KEY,
                    template_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    question_type TEXT NOT NULL DEFAULT 'Rating',
                    required INTEGER NOT NULL DEFAULT 1,
                    display_order INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (template_id) REFERENCES feedback_templates(template_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    feedback_id TEXT PRIMARY KEY,
                    feedback_type TEXT NOT NULL DEFAULT 'Complaint',
                    reference_id TEXT NOT NULL,
                    submitted_by TEXT NOT NULL,
                    assigned_to TEXT,
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    title TEXT,
                    comments TEXT,
                    anonymous INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'Pending Review',
                    submitted_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS feedback_answers (
                    answer_id TEXT PRIMARY KEY,
                    feedback_id TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    answer_value TEXT NOT NULL,
                    FOREIGN KEY (feedback_id) REFERENCES feedback(feedback_id),
                    FOREIGN KEY (question_id) REFERENCES feedback_questions(question_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS feedback_responses (
                    response_id TEXT PRIMARY KEY,
                    feedback_id TEXT NOT NULL,
                    responded_by TEXT NOT NULL,
                    response TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (feedback_id) REFERENCES feedback(feedback_id)
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS report_templates (
                    template_id TEXT PRIMARY KEY,
                    template_name TEXT NOT NULL,
                    report_type TEXT NOT NULL,
                    description TEXT,
                    default_filters TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    report_id TEXT PRIMARY KEY,
                    report_name TEXT NOT NULL,
                    report_type TEXT NOT NULL DEFAULT 'Complaint',
                    generated_by TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_format TEXT NOT NULL DEFAULT 'CSV',
                    status TEXT NOT NULL DEFAULT 'Completed',
                    filters_json TEXT,
                    generated_at TEXT NOT NULL,
                    expires_at TEXT,
                    download_count INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS scheduled_reports (
                    schedule_id TEXT PRIMARY KEY,
                    template_id TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    frequency TEXT NOT NULL DEFAULT 'Weekly',
                    day_of_week TEXT,
                    day_of_month INTEGER,
                    time TEXT DEFAULT '09:00',
                    email_enabled INTEGER NOT NULL DEFAULT 0,
                    email_recipients TEXT,
                    next_run TEXT,
                    last_run TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (template_id) REFERENCES report_templates(template_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS report_downloads (
                    download_id TEXT PRIMARY KEY,
                    report_id TEXT NOT NULL,
                    downloaded_by TEXT NOT NULL,
                    downloaded_at TEXT NOT NULL,
                    ip_address TEXT,
                    device TEXT,
                    FOREIGN KEY (report_id) REFERENCES reports(report_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'Circular',
                    description TEXT,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL DEFAULT 0,
                    mime_type TEXT NOT NULL DEFAULT 'application/pdf',
                    uploaded_by TEXT NOT NULL,
                    visibility TEXT NOT NULL DEFAULT 'Public',
                    version INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS document_versions (
                    version_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    uploaded_by TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    change_notes TEXT,
                    FOREIGN KEY (document_id) REFERENCES documents(document_id)
                )
                """)


            connection.execute("""
                CREATE TABLE IF NOT EXISTS search_index (
                    index_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    keywords TEXT,
                    location_id TEXT,
                    department_id TEXT,
                    owner_id TEXT,
                    visibility TEXT NOT NULL DEFAULT 'Public',
                    last_indexed TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(entity_type, entity_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    history_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    search_query TEXT NOT NULL,
                    filters_json TEXT,
                    result_count INTEGER NOT NULL DEFAULT 0,
                    searched_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS saved_searches (
                    saved_search_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    search_name TEXT NOT NULL,
                    query TEXT NOT NULL,
                    filters_json TEXT,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, search_name)
                )
                """)


            connection.execute("""
                CREATE TABLE IF NOT EXISTS backups (
                    backup_id TEXT PRIMARY KEY,
                    backup_name TEXT NOT NULL UNIQUE,
                    backup_type TEXT NOT NULL DEFAULT 'Full',
                    status TEXT NOT NULL DEFAULT 'Completed',
                    storage_location TEXT NOT NULL DEFAULT 'Local',
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_size INTEGER NOT NULL DEFAULT 0,
                    checksum TEXT,
                    encrypted INTEGER NOT NULL DEFAULT 0,
                    compression_enabled INTEGER NOT NULL DEFAULT 1,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    expires_at TEXT,
                    remarks TEXT,
                    is_deleted INTEGER NOT NULL DEFAULT 0
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS backup_schedules (
                    schedule_id TEXT PRIMARY KEY,
                    backup_type TEXT NOT NULL DEFAULT 'Full',
                    frequency TEXT NOT NULL DEFAULT 'Daily',
                    cron_expression TEXT,
                    retention_days INTEGER NOT NULL DEFAULT 30,
                    compression_enabled INTEGER NOT NULL DEFAULT 1,
                    encryption_enabled INTEGER NOT NULL DEFAULT 0,
                    storage_provider TEXT NOT NULL DEFAULT 'Local',
                    enabled INTEGER NOT NULL DEFAULT 1,
                    next_run TEXT,
                    last_run TEXT,
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS backup_files (
                    backup_file_id TEXT PRIMARY KEY,
                    backup_id TEXT NOT NULL,
                    file_type TEXT NOT NULL DEFAULT 'Database',
                    file_path TEXT NOT NULL,
                    original_path TEXT NOT NULL,
                    size INTEGER NOT NULL DEFAULT 0,
                    checksum TEXT,
                    FOREIGN KEY (backup_id) REFERENCES backups(backup_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS restore_history (
                    restore_id TEXT PRIMARY KEY,
                    backup_id TEXT NOT NULL,
                    restored_by TEXT NOT NULL,
                    restore_type TEXT NOT NULL DEFAULT 'Full',
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    status TEXT NOT NULL DEFAULT 'Completed',
                    remarks TEXT,
                    FOREIGN KEY (backup_id) REFERENCES backups(backup_id)
                )
                """)

            # Backups Indexes
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_bkp_type ON backups(backup_type)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_bkp_status ON backups(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_rst_bkp ON restore_history(backup_id)"
            )

            # Search Index Indexes
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_src_type ON search_index(entity_type)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_src_entity ON search_index(entity_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_src_title ON search_index(title)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_src_vis ON search_index(visibility)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_src_hist_user ON search_history(user_id)"
            )

            # Reports Indexes
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_rpt_type ON reports(report_type)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_rpt_status ON reports(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_rpt_gen ON reports(generated_by)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_doc_cat ON documents(category)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_doc_vis ON documents(visibility)"
            )

            # Feedback Indexes
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_fb_type ON feedback(feedback_type)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_fb_ref ON feedback(reference_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_fb_rating ON feedback(rating)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_fb_status ON feedback(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_fb_sub ON feedback(submitted_by)"
            )

            # Announcements Indexes
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ann_status ON announcements(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ann_priority ON announcements(priority)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ann_cat ON announcements(category)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ann_targets ON announcement_targets(announcement_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ann_reads ON announcement_reads(announcement_id, user_id)"
            )

            # Lost and Found Indexes
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_lf_type ON lost_found_items(report_type)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_lf_status ON lost_found_items(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_lf_cat ON lost_found_items(category)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_lf_serial ON lost_found_items(serial_number)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_lf_claims_item ON ownership_claims(item_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_lf_claims_user ON ownership_claims(claimed_by)"
            )

            # Add database indexes for fast query execution
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_dept ON users(department_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_users_loc ON users(location_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_complaints_created_by ON complaints(created_by)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_complaints_dept ON complaints(department_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_complaints_loc ON complaints(location_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_complaints_assigned ON complaints(assigned_to)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_comments_complaint ON comments(complaint_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_highlights_location ON highlights(target_location)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_attachments_complaint ON attachments(complaint_id)"
            )

            connection.execute("""
                CREATE TABLE IF NOT EXISTS academic_programs (
                    program_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    duration_years INTEGER NOT NULL DEFAULT 4,
                    description TEXT,
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS activation_tokens (
                    token_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    token TEXT NOT NULL UNIQUE,
                    expires_at TEXT NOT NULL,
                    used INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """)
            prog_count = connection.execute("SELECT COUNT(*) FROM academic_programs").fetchone()[0]
            if prog_count == 0:
                now_str = "2024-01-01T00:00:00"
                default_programs = [
                    ("PROG_BTECH", "B.Tech", 4, "Bachelor of Technology (4 Years Undergraduate Program)", now_str),
                    ("PROG_DEGREE", "Degree", 3, "Undergraduate Degree Program (3 Years)", now_str),
                    ("PROG_MTECH", "M.Tech", 2, "Master of Technology (2 Years Postgraduate Program)", now_str),
                    ("PROG_MBA", "MBA", 2, "Master of Business Administration (2 Years Postgraduate Program)", now_str),
                ]
                connection.executemany(
                    "INSERT OR IGNORE INTO academic_programs (program_id, name, duration_years, description, created_at) VALUES (?, ?, ?, ?, ?)",
                    default_programs
                )

            connection.execute("""
                CREATE TABLE IF NOT EXISTS student_profiles (
                    user_id TEXT PRIMARY KEY,
                    roll_number TEXT NOT NULL UNIQUE,
                    department TEXT,
                    program TEXT,
                    year TEXT,
                    section TEXT,
                    hostel TEXT,
                    block TEXT,
                    room_number TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS staff_profiles (
                    user_id TEXT PRIMARY KEY,
                    employee_id TEXT NOT NULL UNIQUE,
                    designation TEXT,
                    department TEXT,
                    assigned_locations TEXT,
                    assigned_categories TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS user_activities (
                    activity_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    performed_by TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    remarks TEXT
                )
                """)
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_student_roll ON student_profiles(roll_number)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_staff_emp ON staff_profiles(employee_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_user_activities ON user_activities(user_id)"
            )

            connection.execute("""
                CREATE TABLE IF NOT EXISTS campuses (
                    campus_id TEXT PRIMARY KEY,
                    campus_name TEXT NOT NULL,
                    campus_code TEXT NOT NULL UNIQUE,
                    description TEXT,
                    address TEXT,
                    city TEXT,
                    state TEXT,
                    country TEXT,
                    postal_code TEXT,
                    contact_email TEXT,
                    contact_phone TEXT,
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0,
                    deleted_at TEXT,
                    deleted_by TEXT
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS buildings (
                    building_id TEXT PRIMARY KEY,
                    campus_id TEXT NOT NULL,
                    building_name TEXT NOT NULL,
                    building_code TEXT NOT NULL,
                    building_type TEXT NOT NULL DEFAULT 'Hostel',
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0,
                    deleted_at TEXT,
                    deleted_by TEXT,
                    FOREIGN KEY (campus_id) REFERENCES campuses(campus_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS hostels (
                    hostel_id TEXT PRIMARY KEY,
                    building_id TEXT NOT NULL UNIQUE,
                    hostel_name TEXT NOT NULL,
                    gender TEXT NOT NULL DEFAULT 'Co-ed',
                    capacity INTEGER NOT NULL DEFAULT 100,
                    occupied_rooms INTEGER NOT NULL DEFAULT 0,
                    warden_id TEXT,
                    status TEXT NOT NULL DEFAULT 'Active',
                    FOREIGN KEY (building_id) REFERENCES buildings(building_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS blocks (
                    block_id TEXT PRIMARY KEY,
                    building_id TEXT NOT NULL,
                    block_name TEXT NOT NULL,
                    block_code TEXT NOT NULL,
                    number_of_floors INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (building_id) REFERENCES buildings(building_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS floors (
                    floor_id TEXT PRIMARY KEY,
                    block_id TEXT NOT NULL,
                    floor_number INTEGER NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL DEFAULT 'Active',
                    FOREIGN KEY (block_id) REFERENCES blocks(block_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    room_id TEXT PRIMARY KEY,
                    floor_id TEXT NOT NULL,
                    room_number TEXT NOT NULL,
                    room_type TEXT NOT NULL DEFAULT 'Hostel Room',
                    capacity INTEGER NOT NULL DEFAULT 2,
                    occupied INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'Active',
                    FOREIGN KEY (floor_id) REFERENCES floors(floor_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS complaint_categories (
                    category_id TEXT PRIMARY KEY,
                    department_id TEXT NOT NULL,
                    category_name TEXT NOT NULL,
                    category_description TEXT,
                    default_priority TEXT NOT NULL DEFAULT 'Medium',
                    default_sla_days INTEGER NOT NULL DEFAULT 3,
                    allow_community INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'Active',
                    FOREIGN KEY (department_id) REFERENCES departments(department_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS coordinator_assignments (
                    assignment_id TEXT PRIMARY KEY,
                    coordinator_id TEXT NOT NULL,
                    department_id TEXT NOT NULL,
                    location_id TEXT NOT NULL,
                    assigned_at TEXT NOT NULL,
                    assigned_by TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Active'
                )
                """)

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_buildings_campus ON buildings(campus_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_blocks_building ON blocks(building_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_floors_block ON floors(block_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_rooms_floor ON rooms(floor_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_cat_dept ON complaint_categories(department_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_coord_assign ON coordinator_assignments(department_id, location_id)"
            )

            connection.execute("""
                CREATE TABLE IF NOT EXISTS affected_students (
                    complaint_id TEXT NOT NULL,
                    student_id TEXT NOT NULL,
                    PRIMARY KEY (complaint_id, student_id),
                    FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id),
                    FOREIGN KEY (student_id) REFERENCES users(user_id)
                )
                """)

            # Compatibility columns for the original directory schema.
            for table_name, col_def in [
                ("campuses", "campus_code TEXT"),
                ("campuses", "description TEXT"),
                ("campuses", "city TEXT"),
                ("campuses", "state TEXT"),
                ("campuses", "country TEXT"),
                ("campuses", "postal_code TEXT"),
                ("campuses", "contact_phone TEXT"),
                ("campuses", "updated_at TEXT"),
                ("campuses", "created_by TEXT DEFAULT 'system'"),
                ("campuses", "is_deleted INTEGER NOT NULL DEFAULT 0"),
                ("campuses", "deleted_at TEXT"),
                ("campuses", "deleted_by TEXT"),
                ("buildings", "building_type TEXT NOT NULL DEFAULT 'Hostel'"),
                ("buildings", "description TEXT"),
                ("buildings", "created_at TEXT"),
                ("buildings", "updated_at TEXT"),
                ("buildings", "created_by TEXT DEFAULT 'system'"),
                ("buildings", "is_deleted INTEGER NOT NULL DEFAULT 0"),
                ("buildings", "deleted_at TEXT"),
                ("buildings", "deleted_by TEXT"),
            ]:
                try:
                    connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_def}")
                except sqlite3.OperationalError:
                    pass
            # Column migrations for departments table
            for col_def in [
                ("department_code", "TEXT"),
                ("description", "TEXT"),
                ("head_of_department", "TEXT"),
                ("contact_email", "TEXT"),
                ("status", "TEXT DEFAULT 'Active'"),
            ]:
                try:
                    connection.execute(
                        f"ALTER TABLE departments ADD COLUMN {col_def[0]} {col_def[1]}"
                    )
                except sqlite3.OperationalError:
                    pass

            # Automated Migrations for existing databases
            for col_def in [
                ("phone_number", "TEXT"),
                ("status", "TEXT DEFAULT 'Active'"),
                ("profile_photo", "TEXT"),
                ("updated_at", "TEXT"),
                ("last_login", "TEXT"),
                ("last_logout", "TEXT"),
                ("created_by", "TEXT DEFAULT 'system'"),
                ("is_deleted", "INTEGER DEFAULT 0"),
                ("deleted_at", "TEXT"),
                ("deleted_by", "TEXT"),
                ("deactivated_by_user_id", "TEXT"),
                ("deactivated_by_role", "TEXT"),
                ("deactivated_at", "TEXT"),
            ]:
                try:
                    connection.execute(
                        f"ALTER TABLE users ADD COLUMN {col_def[0]} {col_def[1]}"
                    )
                except sqlite3.OperationalError:
                    pass

            try:
                connection.execute(
                    "ALTER TABLE departments ADD COLUMN active INTEGER NOT NULL DEFAULT 1"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE departments ADD COLUMN archived INTEGER NOT NULL DEFAULT 0"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE departments ADD COLUMN location_id TEXT"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE locations ADD COLUMN active INTEGER NOT NULL DEFAULT 1"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE locations ADD COLUMN archived INTEGER NOT NULL DEFAULT 0"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE complaints ADD COLUMN archived INTEGER NOT NULL DEFAULT 0"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE complaints ADD COLUMN priority TEXT NOT NULL DEFAULT 'Medium'"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute("ALTER TABLE complaints ADD COLUMN category TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE complaints ADD COLUMN visibility_type TEXT NOT NULL DEFAULT 'Private'"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE complaints ADD COLUMN attachment_url TEXT"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute("ALTER TABLE complaints ADD COLUMN title TEXT")
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE complaints ADD COLUMN is_deleted INTEGER NOT NULL DEFAULT 0"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE dashboard_widgets ADD COLUMN widget_name TEXT"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE dashboard_widgets ADD COLUMN configuration_json TEXT"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE dashboard_widgets ADD COLUMN created_by TEXT"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE configuration_history ADD COLUMN reason TEXT"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE configuration_history ADD COLUMN change_reason TEXT"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE maintenance_windows ADD COLUMN window_id TEXT"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE maintenance_windows ADD COLUMN scheduled_start TEXT"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE maintenance_windows ADD COLUMN scheduled_end TEXT"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE maintenance_windows ADD COLUMN affected_modules TEXT DEFAULT 'All System Modules'"
                )
            except sqlite3.OperationalError:
                pass
            try:
                connection.execute(
                    "ALTER TABLE comments ADD COLUMN is_internal INTEGER NOT NULL DEFAULT 0"
                )
            except sqlite3.OperationalError:
                pass

    def _is_empty(self):
        table_names = []
        if "users" in self.default_data:
            table_names.extend(["users", "departments", "locations"])
        if "complaints" in self.default_data:
            table_names.append("complaints")
        with self._connect() as connection:
            for table_name in table_names:
                count = connection.execute(
                    f"SELECT COUNT(*) AS count FROM {table_name}"
                ).fetchone()["count"]
                if count:
                    return False
        return True

    def load(self):
        data = {}
        with self._connect() as connection:
            if "users" in self.default_data:
                data["users"] = [
                    self._row_to_user(row)
                    for row in connection.execute(
                        "SELECT * FROM users ORDER BY created_at"
                    )
                ]
                data["departments"] = [
                    self._row_to_department(row)
                    for row in connection.execute(
                        "SELECT * FROM departments ORDER BY name"
                    )
                ]
                data["locations"] = [
                    self._row_to_location(row)
                    for row in connection.execute(
                        "SELECT * FROM locations ORDER BY name"
                    )
                ]
            data["location_types"] = []
            try:
                rows = connection.execute("SELECT * FROM location_types").fetchall()
                for r in rows:
                    data["location_types"].append({
                        "type_id": r["type_id"],
                        "name": r["name"],
                        "description": r["description"] if "description" in r.keys() else None,
                    })
            except Exception:
                pass
            if "complaints" in self.default_data:
                data["complaints"] = [
                    self._row_to_complaint(row)
                    for row in connection.execute(
                        "SELECT * FROM complaints ORDER BY created_at"
                    )
                ]

            # Export comments and highlights
            data["comments"] = []
            try:
                rows = connection.execute("SELECT * FROM comments").fetchall()
                for r in rows:
                    data["comments"].append(
                        {
                            "comment_id": r["comment_id"],
                            "complaint_id": r["complaint_id"],
                            "user_id": r["user_id"],
                            "message": r["message"],
                            "created_at": r["created_at"],
                            "is_internal": (
                                bool(r["is_internal"])
                                if "is_internal" in r.keys()
                                else False
                            ),
                        }
                    )
            except Exception:
                pass

            data["highlights"] = []
            try:
                rows = connection.execute("SELECT * FROM highlights").fetchall()
                for r in rows:
                    data["highlights"].append(
                        {
                            "highlight_id": r["highlight_id"],
                            "title": r["title"],
                            "description": r["description"],
                            "target_location": r["target_location"],
                            "priority": r["priority"],
                            "created_by": r["created_by"],
                            "created_at": r["created_at"],
                            "expiry_date": r["expiry_date"],
                        }
                    )
            except Exception:
                pass

            data["system_settings"] = []
            try:
                rows = connection.execute("SELECT * FROM system_settings").fetchall()
                for r in rows:
                    data["system_settings"].append(
                        {"key": r["setting_key"], "value": r["setting_value"]}
                    )
            except Exception:
                pass

            data["attachments"] = []
            try:
                rows = connection.execute("SELECT * FROM attachments").fetchall()
                for r in rows:
                    data["attachments"].append(
                        {
                            "attachment_id": r["attachment_id"],
                            "complaint_id": r["complaint_id"],
                            "uploaded_by": r["uploaded_by"],
                            "uploader_role": r["uploader_role"],
                            "category": r["category"],
                            "original_filename": r["original_filename"],
                            "stored_filename": r["stored_filename"],
                            "file_path": r["file_path"],
                            "file_size": r["file_size"],
                            "uploaded_at": r["uploaded_at"],
                        }
                    )
            except Exception:
                pass

            data["affected_students"] = []
            try:
                rows = connection.execute("SELECT * FROM affected_students").fetchall()
                for r in rows:
                    data["affected_students"].append(
                        {
                            "complaint_id": r["complaint_id"],
                            "student_id": r["student_id"],
                        }
                    )
            except Exception:
                pass
        return data

    def save(self, data):
        with self._connect() as connection:
            connection.execute("PRAGMA foreign_keys = OFF")
            if "users" in data:
                connection.execute("DELETE FROM users")
                connection.executemany(
                    """
                    INSERT INTO users (
                        user_id, name, email, password, role, first_login, active,
                        department_id, location_id, created_at, phone_number, status,
                        profile_photo, updated_at, last_login, last_logout, created_by,
                        is_deleted, deleted_at, deleted_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [self._user_to_values(item) for item in data.get("users", [])],
                )
            if "departments" in data:
                connection.execute("DELETE FROM departments")
                connection.executemany(
                    """
                    INSERT INTO departments (
                        department_id, name, sla_days, complaint_types, coordinator_id, active, archived, location_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        self._department_to_values(item)
                        for item in data.get("departments", [])
                    ],
                )
            if "locations" in data:
                connection.execute("DELETE FROM locations")
                connection.executemany(
                    """
                    INSERT INTO locations (location_id, name, in_charge_id, coordinator_id, active, archived, location_type, app_manager_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        self._location_to_values(item)
                        for item in data.get("locations", [])
                    ],
                )
            if "complaints" in data:
                connection.execute("DELETE FROM complaints")
                connection.executemany(
                    """
                    INSERT INTO complaints (
                        complaint_id, created_by, creator_role, location_id, department_id,
                        complaint_type, description, status, assigned_to, created_at, updated_at,
                        resolved_at, verification_due_at, reopen_count, auto_closed, escalated,
                        admin_notified, resolution_notes, verification_reports, history, archived,
                        priority, category, visibility_type, attachment_url, title,
                        sla_deadline, assigned_at, started_at, auto_assigned, blocked_reason,
                        blocked_until, blocked_at, sla_reminders_sent, escalation_level,
                        warden_escalation_level, team_location_id, team_department_id,
                        is_urgent, urgent_reason, fixed_at, fixed_by, warden_verified_at,
                        warden_verified_by, warden_verdict, warden_notes, student_stage_at,
                        closed_at, closed_by, requires_warden_check, is_spot_check,
                        auto_close_reminded, admin_review_reason, admin_decision,
                        admin_decided_by, admin_decided_at, deletion_requested,
                        deletion_requested_by, deletion_requested_name, deletion_requested_role,
                        deletion_reason, deletion_requested_at
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    [
                        self._complaint_to_values(item)
                        for item in data.get("complaints", [])
                    ],
                )
            if "comments" in data:
                connection.execute("DELETE FROM comments")
                connection.executemany(
                    """
                    INSERT INTO comments (comment_id, complaint_id, user_id, message, created_at, is_internal)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            c["comment_id"],
                            c["complaint_id"],
                            c["user_id"],
                            c["message"],
                            c["created_at"],
                            int(c.get("is_internal", False)),
                        )
                        for c in data.get("comments", [])
                    ],
                )
            if "highlights" in data:
                connection.execute("DELETE FROM highlights")
                connection.executemany(
                    """
                    INSERT INTO highlights (highlight_id, title, description, target_location, priority, created_by, created_at, expiry_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            h["highlight_id"],
                            h["title"],
                            h["description"],
                            h["target_location"],
                            h["priority"],
                            h["created_by"],
                            h["created_at"],
                            h["expiry_date"],
                        )
                        for h in data.get("highlights", [])
                    ],
                )
            if "system_settings" in data:
                connection.execute("DELETE FROM system_settings")
                connection.executemany(
                    """
                    INSERT INTO system_settings (setting_id, setting_key, setting_value, created_at, updated_at)
                    VALUES ('SET_' || ?, ?, ?, datetime('now'), datetime('now'))
                    """,
                    [
                        (s["key"], s["key"], s["value"])
                        for s in data.get("system_settings", [])
                    ],
                )
            if "attachments" in data:
                connection.execute("DELETE FROM attachments")
                connection.executemany(
                    """
                    INSERT INTO attachments (attachment_id, complaint_id, uploaded_by, uploader_role, category, original_filename, stored_filename, file_path, file_size, uploaded_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            a["attachment_id"],
                            a["complaint_id"],
                            a["uploaded_by"],
                            a["uploader_role"],
                            a["category"],
                            a["original_filename"],
                            a["stored_filename"],
                            a["file_path"],
                            a["file_size"],
                            a["uploaded_at"],
                        )
                        for a in data.get("attachments", [])
                    ],
                )
            if "affected_students" in data:
                connection.execute("DELETE FROM affected_students")
                connection.executemany(
                    """
                    INSERT INTO affected_students (complaint_id, student_id)
                    VALUES (?, ?)
                    """,
                    [
                        (a["complaint_id"], a["student_id"])
                        for a in data.get("affected_students", [])
                    ],
                )

    def _user_to_values(self, item):
        return (
            item["user_id"],
            item["name"],
            item["email"],
            item["password"],
            item["role"],
            int(item.get("first_login", False)),
            int(item.get("active", True)),
            item.get("department_id"),
            item.get("location_id"),
            item["created_at"],
            item.get("phone_number"),
            item.get("status", "Active"),
            item.get("profile_photo"),
            item.get("updated_at"),
            item.get("last_login"),
            item.get("last_logout"),
            item.get("created_by", "system"),
            int(item.get("is_deleted", False)),
            item.get("deleted_at"),
            item.get("deleted_by"),
        )

    def _department_to_values(self, item):
        return (
            item["department_id"],
            item["name"],
            int(item.get("sla_days", 3)),
            json.dumps(item.get("complaint_types", [])),
            item.get("coordinator_id"),
            int(item.get("active", True)),
            int(item.get("archived", False)),
            item.get("location_id"),
        )

    def _location_to_values(self, item):
        return (
            item["location_id"],
            item["name"],
            item.get("in_charge_id"),
            item.get("coordinator_id"),
            int(item.get("active", True)),
            int(item.get("archived", False)),
            item.get("location_type"),
            item.get("app_manager_id"),
        )

    def _complaint_to_values(self, item):
        return (
            item["complaint_id"],
            item["created_by"],
            item["creator_role"],
            item["location_id"],
            item["department_id"],
            item["complaint_type"],
            item["description"],
            item["status"],
            item.get("assigned_to"),
            item["created_at"],
            item["updated_at"],
            item.get("resolved_at"),
            item.get("verification_due_at"),
            int(item.get("reopen_count", 0)),
            int(item.get("auto_closed", False)),
            int(item.get("escalated", False)),
            int(item.get("admin_notified", False)),
            (
                item.get("resolution_notes")
                if item.get("resolution_notes") is not None
                else ""
            ),
            json.dumps(item.get("verification_reports", [])),
            json.dumps(item.get("history", [])),
            int(item.get("archived", False)),
            item.get("priority", "Medium"),
            item.get("category", item.get("complaint_type", "General")),
            item.get("visibility_type", "Private"),
            item.get("attachment_url"),
            item.get("title", ""),
            item.get("sla_deadline"),
            item.get("assigned_at"),
            item.get("started_at"),
            int(bool(item.get("auto_assigned", False))),
            item.get("blocked_reason"),
            item.get("blocked_until"),
            item.get("blocked_at"),
            int(item.get("sla_reminders_sent", 0)),
            int(item.get("escalation_level", 0)),
            int(item.get("warden_escalation_level", 0)),
            item.get("team_location_id"),
            item.get("team_department_id"),
            int(bool(item.get("is_urgent", False))),
            item.get("urgent_reason"),
            item.get("fixed_at"),
            item.get("fixed_by"),
            item.get("warden_verified_at"),
            item.get("warden_verified_by"),
            item.get("warden_verdict"),
            item.get("warden_notes"),
            item.get("student_stage_at"),
            item.get("closed_at"),
            item.get("closed_by"),
            int(bool(item.get("requires_warden_check", False))),
            int(bool(item.get("is_spot_check", False))),
            int(bool(item.get("auto_close_reminded", False))),
            item.get("admin_review_reason"),
            item.get("admin_decision"),
            item.get("admin_decided_by"),
            item.get("admin_decided_at"),
            int(bool(item.get("deletion_requested", False))),
            item.get("deletion_requested_by"),
            item.get("deletion_requested_name"),
            item.get("deletion_requested_role"),
            item.get("deletion_reason"),
            item.get("deletion_requested_at"),
        )

    def _row_to_user(self, row):
        return {
            "user_id": row["user_id"],
            "name": row["name"],
            "email": row["email"],
            "password": row["password"],
            "role": row["role"],
            "first_login": bool(row["first_login"]),
            "active": bool(row["active"]),
            "department_id": row["department_id"],
            "location_id": row["location_id"],
            "created_at": row["created_at"],
            "phone_number": row["phone_number"] if "phone_number" in row.keys() else None,
            "status": row["status"] if "status" in row.keys() else "Active",
            "profile_photo": row["profile_photo"] if "profile_photo" in row.keys() else None,
            "updated_at": row["updated_at"] if "updated_at" in row.keys() else None,
            "last_login": row["last_login"] if "last_login" in row.keys() else None,
            "last_logout": row["last_logout"] if "last_logout" in row.keys() else None,
            "created_by": row["created_by"] if "created_by" in row.keys() else "system",
            "is_deleted": bool(row["is_deleted"]) if "is_deleted" in row.keys() else False,
            "deleted_at": row["deleted_at"] if "deleted_at" in row.keys() else None,
            "deleted_by": row["deleted_by"] if "deleted_by" in row.keys() else None,
        }

    def _row_to_department(self, row):
        return {
            "department_id": row["department_id"],
            "name": row["name"],
            "sla_days": row["sla_days"],
            "complaint_types": json.loads(row["complaint_types"]),
            "coordinator_id": row["coordinator_id"],
            "active": bool(row["active"]) if "active" in row.keys() else True,
            "archived": bool(row["archived"]) if "archived" in row.keys() else False,
            "location_id": row["location_id"] if "location_id" in row.keys() else None,
        }

    def _row_to_location(self, row):
        return {
            "location_id": row["location_id"],
            "name": row["name"],
            "location_type": row["location_type"] if "location_type" in row.keys() else None,
            "in_charge_id": row["in_charge_id"],
            "coordinator_id": row["coordinator_id"] if "coordinator_id" in row.keys() else None,
            "app_manager_id": row["app_manager_id"] if "app_manager_id" in row.keys() else None,
            "active": bool(row["active"]) if "active" in row.keys() else True,
            "archived": bool(row["archived"]) if "archived" in row.keys() else False,
        }

    def _row_to_complaint(self, row):
        return {
            "complaint_id": row["complaint_id"],
            "created_by": row["created_by"],
            "creator_role": row["creator_role"],
            "location_id": row["location_id"],
            "department_id": row["department_id"],
            "complaint_type": row["complaint_type"],
            "description": row["description"],
            "status": row["status"],
            "assigned_to": row["assigned_to"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "resolved_at": row["resolved_at"],
            "verification_due_at": row["verification_due_at"],
            "reopen_count": row["reopen_count"],
            "auto_closed": bool(row["auto_closed"]),
            "escalated": bool(row["escalated"]),
            "admin_notified": bool(row["admin_notified"]),
            "resolution_notes": row["resolution_notes"],
            "verification_reports": json.loads(row["verification_reports"]),
            "history": json.loads(row["history"]),
            "archived": bool(row["archived"]) if "archived" in row.keys() else False,
            "priority": row["priority"] if "priority" in row.keys() else "Medium",
            "category": (
                row["category"]
                if ("category" in row.keys() and row["category"] is not None)
                else (
                    row["complaint_type"]
                    if "complaint_type" in row.keys()
                    else "General"
                )
            ),
            "visibility_type": (
                row["visibility_type"] if "visibility_type" in row.keys() else "Private"
            ),
            "attachment_url": (
                row["attachment_url"] if "attachment_url" in row.keys() else None
            ),
            "title": (
                row["title"]
                if ("title" in row.keys() and row["title"] is not None)
                else ""
            ),
            "sla_deadline": row["sla_deadline"] if "sla_deadline" in row.keys() else None,
            "assigned_at": row["assigned_at"] if "assigned_at" in row.keys() else None,
            "started_at": row["started_at"] if "started_at" in row.keys() else None,
            "auto_assigned": bool(row["auto_assigned"]) if "auto_assigned" in row.keys() and row["auto_assigned"] is not None else False,
            "blocked_reason": row["blocked_reason"] if "blocked_reason" in row.keys() else None,
            "blocked_until": row["blocked_until"] if "blocked_until" in row.keys() else None,
            "blocked_at": row["blocked_at"] if "blocked_at" in row.keys() else None,
            "sla_reminders_sent": row["sla_reminders_sent"] if "sla_reminders_sent" in row.keys() and row["sla_reminders_sent"] is not None else 0,
            "escalation_level": row["escalation_level"] if "escalation_level" in row.keys() and row["escalation_level"] is not None else 0,
            "warden_escalation_level": row["warden_escalation_level"] if "warden_escalation_level" in row.keys() and row["warden_escalation_level"] is not None else 0,
            "team_location_id": row["team_location_id"] if "team_location_id" in row.keys() else None,
            "team_department_id": row["team_department_id"] if "team_department_id" in row.keys() else None,
            "is_urgent": bool(row["is_urgent"]) if "is_urgent" in row.keys() and row["is_urgent"] is not None else False,
            "urgent_reason": row["urgent_reason"] if "urgent_reason" in row.keys() else None,
            "fixed_at": row["fixed_at"] if "fixed_at" in row.keys() else None,
            "fixed_by": row["fixed_by"] if "fixed_by" in row.keys() else None,
            "warden_verified_at": row["warden_verified_at"] if "warden_verified_at" in row.keys() else None,
            "warden_verified_by": row["warden_verified_by"] if "warden_verified_by" in row.keys() else None,
            "warden_verdict": row["warden_verdict"] if "warden_verdict" in row.keys() else None,
            "warden_notes": row["warden_notes"] if "warden_notes" in row.keys() else None,
            "student_stage_at": row["student_stage_at"] if "student_stage_at" in row.keys() else None,
            "closed_at": row["closed_at"] if "closed_at" in row.keys() else None,
            "closed_by": row["closed_by"] if "closed_by" in row.keys() else None,
            "requires_warden_check": bool(row["requires_warden_check"]) if "requires_warden_check" in row.keys() and row["requires_warden_check"] is not None else False,
            "is_spot_check": bool(row["is_spot_check"]) if "is_spot_check" in row.keys() and row["is_spot_check"] is not None else False,
            "auto_close_reminded": bool(row["auto_close_reminded"]) if "auto_close_reminded" in row.keys() and row["auto_close_reminded"] is not None else False,
            "admin_review_reason": row["admin_review_reason"] if "admin_review_reason" in row.keys() else None,
            "admin_decision": row["admin_decision"] if "admin_decision" in row.keys() else None,
            "admin_decided_by": row["admin_decided_by"] if "admin_decided_by" in row.keys() else None,
            "admin_decided_at": row["admin_decided_at"] if "admin_decided_at" in row.keys() else None,
            "deletion_requested": bool(row["deletion_requested"]) if "deletion_requested" in row.keys() and row["deletion_requested"] is not None else False,
            "deletion_requested_by": row["deletion_requested_by"] if "deletion_requested_by" in row.keys() else None,
            "deletion_requested_name": row["deletion_requested_name"] if "deletion_requested_name" in row.keys() else None,
            "deletion_requested_role": row["deletion_requested_role"] if "deletion_requested_role" in row.keys() else None,
            "deletion_reason": row["deletion_reason"] if "deletion_reason" in row.keys() else None,
            "deletion_requested_at": row["deletion_requested_at"] if "deletion_requested_at" in row.keys() else None,
        }
