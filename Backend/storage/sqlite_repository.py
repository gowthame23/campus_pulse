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
                CREATE TABLE IF NOT EXISTS resources (
                    resource_id TEXT PRIMARY KEY,
                    resource_name TEXT NOT NULL,
                    resource_code TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL DEFAULT 'Sports Facility',
                    building_id TEXT,
                    block_id TEXT,
                    floor_id TEXT,
                    room_id TEXT,
                    description TEXT,
                    capacity INTEGER NOT NULL DEFAULT 10,
                    booking_required INTEGER NOT NULL DEFAULT 1,
                    approval_required INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'Available',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0,
                    deleted_at TEXT,
                    deleted_by TEXT
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS resource_schedules (
                    schedule_id TEXT PRIMARY KEY,
                    resource_id TEXT NOT NULL,
                    day_of_week TEXT NOT NULL,
                    opening_time TEXT NOT NULL DEFAULT '06:00',
                    closing_time TEXT NOT NULL DEFAULT '22:00',
                    is_closed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS resource_bookings (
                    booking_id TEXT PRIMARY KEY,
                    resource_id TEXT NOT NULL,
                    booked_by TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    booking_date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    participants INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    approval_by TEXT,
                    approval_time TEXT,
                    rejection_reason TEXT,
                    cancel_reason TEXT,
                    recurrence_type TEXT DEFAULT 'None',
                    recurrence_end_date TEXT,
                    parent_booking_id TEXT,
                    checked_in INTEGER NOT NULL DEFAULT 0,
                    check_in_time TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
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
                CREATE TABLE IF NOT EXISTS visitors (
                    visitor_id TEXT PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    phone_number TEXT NOT NULL UNIQUE,
                    email TEXT,
                    gender TEXT,
                    date_of_birth TEXT,
                    government_id_type TEXT NOT NULL DEFAULT 'Aadhaar',
                    government_id_number TEXT NOT NULL,
                    address TEXT,
                    photo_url TEXT,
                    is_blacklisted INTEGER NOT NULL DEFAULT 0,
                    blacklist_reason TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS visitor_requests (
                    request_id TEXT PRIMARY KEY,
                    visitor_id TEXT NOT NULL,
                    host_user_id TEXT NOT NULL,
                    host_role TEXT NOT NULL DEFAULT 'Student',
                    purpose TEXT NOT NULL,
                    visit_type TEXT NOT NULL DEFAULT 'Personal',
                    visit_date TEXT NOT NULL,
                    expected_check_in TEXT NOT NULL,
                    expected_check_out TEXT NOT NULL,
                    number_of_visitors INTEGER NOT NULL DEFAULT 1,
                    approval_required INTEGER NOT NULL DEFAULT 1,
                    approved_by TEXT,
                    approval_time TEXT,
                    rejection_reason TEXT,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (visitor_id) REFERENCES visitors(visitor_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS visitor_locations (
                    location_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    campus_id TEXT,
                    building_id TEXT,
                    block_id TEXT,
                    floor_id TEXT,
                    room_id TEXT,
                    allowed_area TEXT NOT NULL DEFAULT 'Main Campus',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (request_id) REFERENCES visitor_requests(request_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS visitor_documents (
                    document_id TEXT PRIMARY KEY,
                    visitor_id TEXT NOT NULL,
                    document_type TEXT NOT NULL DEFAULT 'Government ID',
                    document_url TEXT NOT NULL,
                    verified INTEGER NOT NULL DEFAULT 0,
                    verified_by TEXT,
                    uploaded_at TEXT NOT NULL,
                    FOREIGN KEY (visitor_id) REFERENCES visitors(visitor_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS visitor_gate_pass (
                    pass_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL UNIQUE,
                    qr_code TEXT NOT NULL,
                    otp TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    used INTEGER NOT NULL DEFAULT 0,
                    printed INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (request_id) REFERENCES visitor_requests(request_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS visitor_checkins (
                    checkin_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    security_guard_id TEXT NOT NULL,
                    check_in_time TEXT NOT NULL,
                    check_out_time TEXT,
                    gate_name TEXT NOT NULL DEFAULT 'Main Gate',
                    visitor_photo TEXT,
                    remarks TEXT,
                    FOREIGN KEY (request_id) REFERENCES visitor_requests(request_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS visitor_blacklist (
                    blacklist_id TEXT PRIMARY KEY,
                    visitor_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    added_by TEXT NOT NULL,
                    added_at TEXT NOT NULL,
                    expires_at TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (visitor_id) REFERENCES visitors(visitor_id)
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS work_orders (
                    work_order_id TEXT PRIMARY KEY,
                    complaint_id TEXT NOT NULL,
                    work_order_number TEXT NOT NULL UNIQUE,
                    department_id TEXT,
                    assigned_technician_id TEXT,
                    assigned_team TEXT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    priority TEXT NOT NULL DEFAULT 'Medium',
                    status TEXT NOT NULL DEFAULT 'Draft',
                    estimated_start_time TEXT,
                    estimated_completion_time TEXT,
                    actual_start_time TEXT,
                    actual_completion_time TEXT,
                    sla_deadline TEXT,
                    verification_required INTEGER NOT NULL DEFAULT 1,
                    verified_by TEXT,
                    verified_at TEXT,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS work_order_assignments (
                    assignment_id TEXT PRIMARY KEY,
                    work_order_id TEXT NOT NULL,
                    technician_id TEXT NOT NULL,
                    assigned_by TEXT NOT NULL,
                    assigned_at TEXT NOT NULL,
                    accepted_at TEXT,
                    rejected_at TEXT,
                    rejection_reason TEXT,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (work_order_id) REFERENCES work_orders(work_order_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS work_order_notes (
                    note_id TEXT PRIMARY KEY,
                    work_order_id TEXT NOT NULL,
                    author_id TEXT NOT NULL,
                    visibility TEXT NOT NULL DEFAULT 'Public',
                    note TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (work_order_id) REFERENCES work_orders(work_order_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS work_order_images (
                    image_id TEXT PRIMARY KEY,
                    work_order_id TEXT NOT NULL,
                    uploaded_by TEXT NOT NULL,
                    image_type TEXT NOT NULL DEFAULT 'Evidence',
                    image_url TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    FOREIGN KEY (work_order_id) REFERENCES work_orders(work_order_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS work_order_parts (
                    part_usage_id TEXT PRIMARY KEY,
                    work_order_id TEXT NOT NULL,
                    part_name TEXT NOT NULL,
                    part_code TEXT,
                    quantity INTEGER NOT NULL DEFAULT 1,
                    unit_cost REAL NOT NULL DEFAULT 0.0,
                    supplier TEXT,
                    remarks TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (work_order_id) REFERENCES work_orders(work_order_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS work_order_time_logs (
                    time_log_id TEXT PRIMARY KEY,
                    work_order_id TEXT NOT NULL,
                    technician_id TEXT NOT NULL,
                    clock_in TEXT NOT NULL,
                    clock_out TEXT,
                    hours_worked REAL DEFAULT 0.0,
                    remarks TEXT,
                    FOREIGN KEY (work_order_id) REFERENCES work_orders(work_order_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS work_order_costs (
                    cost_id TEXT PRIMARY KEY,
                    work_order_id TEXT NOT NULL UNIQUE,
                    labor_cost REAL NOT NULL DEFAULT 0.0,
                    material_cost REAL NOT NULL DEFAULT 0.0,
                    transport_cost REAL NOT NULL DEFAULT 0.0,
                    miscellaneous_cost REAL NOT NULL DEFAULT 0.0,
                    total_cost REAL NOT NULL DEFAULT 0.0,
                    approved_by TEXT,
                    FOREIGN KEY (work_order_id) REFERENCES work_orders(work_order_id)
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS asset_categories (
                    category_id TEXT PRIMARY KEY,
                    category_name TEXT NOT NULL UNIQUE,
                    parent_category TEXT,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS asset_suppliers (
                    supplier_id TEXT PRIMARY KEY,
                    supplier_name TEXT NOT NULL,
                    contact_person TEXT,
                    phone TEXT,
                    email TEXT,
                    address TEXT,
                    gst_number TEXT,
                    website TEXT,
                    remarks TEXT
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS assets (
                    asset_id TEXT PRIMARY KEY,
                    asset_code TEXT NOT NULL UNIQUE,
                    asset_name TEXT NOT NULL,
                    category_id TEXT NOT NULL,
                    serial_number TEXT,
                    barcode TEXT,
                    qr_code TEXT,
                    brand TEXT,
                    model TEXT,
                    manufacturer TEXT,
                    purchase_date TEXT,
                    purchase_cost REAL DEFAULT 0.0,
                    supplier_id TEXT,
                    warranty_start TEXT,
                    warranty_end TEXT,
                    current_condition TEXT NOT NULL DEFAULT 'Good',
                    status TEXT NOT NULL DEFAULT 'Available',
                    assigned_location_id TEXT,
                    assigned_user_id TEXT,
                    department_id TEXT,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY (category_id) REFERENCES asset_categories(category_id),
                    FOREIGN KEY (supplier_id) REFERENCES asset_suppliers(supplier_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS asset_assignments (
                    assignment_id TEXT PRIMARY KEY,
                    asset_id TEXT NOT NULL,
                    assigned_to_user TEXT NOT NULL,
                    assigned_by TEXT NOT NULL,
                    assigned_date TEXT NOT NULL,
                    returned_date TEXT,
                    remarks TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS asset_transfers (
                    transfer_id TEXT PRIMARY KEY,
                    asset_id TEXT NOT NULL,
                    from_location TEXT NOT NULL,
                    to_location TEXT NOT NULL,
                    requested_by TEXT NOT NULL,
                    approved_by TEXT,
                    transfer_date TEXT NOT NULL,
                    reason TEXT,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS asset_maintenance (
                    maintenance_id TEXT PRIMARY KEY,
                    asset_id TEXT NOT NULL,
                    work_order_id TEXT,
                    complaint_id TEXT,
                    maintenance_date TEXT NOT NULL,
                    maintenance_type TEXT NOT NULL DEFAULT 'Corrective',
                    performed_by TEXT NOT NULL,
                    remarks TEXT,
                    cost REAL DEFAULT 0.0,
                    next_service_date TEXT,
                    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS asset_disposals (
                    disposal_id TEXT PRIMARY KEY,
                    asset_id TEXT NOT NULL UNIQUE,
                    disposal_reason TEXT NOT NULL,
                    approved_by TEXT NOT NULL,
                    disposal_date TEXT NOT NULL,
                    disposal_method TEXT,
                    remarks TEXT,
                    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
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
                CREATE TABLE IF NOT EXISTS scheduled_jobs (
                    job_id TEXT PRIMARY KEY,
                    job_name TEXT NOT NULL,
                    job_type TEXT NOT NULL DEFAULT 'Custom',
                    description TEXT,
                    cron_expression TEXT,
                    frequency TEXT NOT NULL DEFAULT 'Daily',
                    enabled INTEGER NOT NULL DEFAULT 1,
                    next_run TEXT,
                    last_run TEXT,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS job_queue (
                    queue_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    payload_json TEXT,
                    priority INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    scheduled_time TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    worker_id TEXT,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES scheduled_jobs(job_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS job_history (
                    history_id TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL,
                    queue_id TEXT,
                    execution_time TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,
                    worker_id TEXT,
                    logs TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (job_id) REFERENCES scheduled_jobs(job_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS workers (
                    worker_id TEXT PRIMARY KEY,
                    worker_name TEXT NOT NULL,
                    host TEXT NOT NULL DEFAULT 'localhost',
                    status TEXT NOT NULL DEFAULT 'Online',
                    started_at TEXT NOT NULL,
                    last_heartbeat TEXT NOT NULL,
                    active_jobs INTEGER NOT NULL DEFAULT 0,
                    version TEXT DEFAULT '1.0.0'
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS job_retry_policy (
                    policy_id TEXT PRIMARY KEY,
                    job_type TEXT NOT NULL UNIQUE,
                    max_retries INTEGER NOT NULL DEFAULT 3,
                    retry_interval INTEGER NOT NULL DEFAULT 60,
                    backoff_strategy TEXT NOT NULL DEFAULT 'Fixed',
                    active INTEGER NOT NULL DEFAULT 1
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
                CREATE TABLE IF NOT EXISTS dashboard_layouts (
                    layout_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    layout_name TEXT NOT NULL DEFAULT 'Default Dashboard',
                    is_default INTEGER NOT NULL DEFAULT 1,
                    theme TEXT NOT NULL DEFAULT 'Dark',
                    sidebar_collapsed INTEGER NOT NULL DEFAULT 0,
                    landing_page TEXT NOT NULL DEFAULT '/student',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS dashboard_widgets (
                    widget_id TEXT PRIMARY KEY,
                    layout_id TEXT NOT NULL,
                    widget_type TEXT NOT NULL,
                    position_x INTEGER NOT NULL DEFAULT 0,
                    position_y INTEGER NOT NULL DEFAULT 0,
                    width INTEGER NOT NULL DEFAULT 1,
                    height INTEGER NOT NULL DEFAULT 1,
                    visible INTEGER NOT NULL DEFAULT 1,
                    refresh_interval INTEGER NOT NULL DEFAULT 300,
                    settings_json TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (layout_id) REFERENCES dashboard_layouts(layout_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS favorite_modules (
                    favorite_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    module_name TEXT NOT NULL,
                    display_order INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, module_name)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS dashboard_preferences (
                    preference_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL UNIQUE,
                    language TEXT NOT NULL DEFAULT 'English',
                    timezone TEXT NOT NULL DEFAULT 'UTC+05:30',
                    date_format TEXT NOT NULL DEFAULT 'YYYY-MM-DD',
                    time_format TEXT NOT NULL DEFAULT '24h',
                    color_theme TEXT NOT NULL DEFAULT 'Indigo Slate',
                    compact_mode INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS quick_actions (
                    action_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    action_name TEXT NOT NULL,
                    route TEXT NOT NULL,
                    icon TEXT NOT NULL DEFAULT 'Plus',
                    display_order INTEGER NOT NULL DEFAULT 1,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
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

            connection.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    api_key_id TEXT PRIMARY KEY,
                    key_name TEXT NOT NULL,
                    api_key_hash TEXT NOT NULL,
                    raw_key_preview TEXT,
                    owner_id TEXT NOT NULL,
                    permissions_json TEXT,
                    expires_at TEXT,
                    last_used_at TEXT,
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS oauth_clients (
                    client_id TEXT PRIMARY KEY,
                    client_name TEXT NOT NULL,
                    client_secret_hash TEXT NOT NULL,
                    redirect_uri TEXT NOT NULL,
                    grant_type TEXT NOT NULL DEFAULT 'authorization_code',
                    owner_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS webhook_endpoints (
                    webhook_id TEXT PRIMARY KEY,
                    endpoint_name TEXT NOT NULL,
                    target_url TEXT NOT NULL,
                    secret_key TEXT NOT NULL,
                    event_types TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    last_delivery TEXT,
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS api_usage_logs (
                    usage_id TEXT PRIMARY KEY,
                    api_key_id TEXT,
                    endpoint TEXT NOT NULL,
                    http_method TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    response_time_ms INTEGER NOT NULL DEFAULT 0,
                    client_ip TEXT,
                    requested_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS integration_registry (
                    integration_id TEXT PRIMARY KEY,
                    integration_name TEXT NOT NULL UNIQUE,
                    provider TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'ERP',
                    status TEXT NOT NULL DEFAULT 'Active',
                    configuration_json TEXT,
                    health_status TEXT NOT NULL DEFAULT 'Healthy',
                    last_sync TEXT,
                    created_at TEXT NOT NULL
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    device_name TEXT NOT NULL DEFAULT 'Web Browser',
                    device_type TEXT NOT NULL DEFAULT 'Desktop',
                    browser TEXT NOT NULL DEFAULT 'Chrome',
                    operating_system TEXT NOT NULL DEFAULT 'Windows',
                    ip_address TEXT NOT NULL DEFAULT '127.0.0.1',
                    country TEXT DEFAULT 'India',
                    city TEXT DEFAULT 'Campus City',
                    login_time TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    refresh_token_hash TEXT,
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS password_resets (
                    reset_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    email TEXT NOT NULL,
                    otp TEXT NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    expires_at REAL NOT NULL,
                    used INTEGER DEFAULT 0,
                    created_at REAL NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS trusted_devices (
                    device_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    device_name TEXT NOT NULL,
                    device_fingerprint TEXT NOT NULL,
                    browser TEXT NOT NULL,
                    operating_system TEXT NOT NULL,
                    trusted_since TEXT NOT NULL,
                    last_used TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(user_id, device_fingerprint)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS login_history (
                    login_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    email TEXT NOT NULL,
                    ip_address TEXT NOT NULL DEFAULT '127.0.0.1',
                    country TEXT DEFAULT 'India',
                    city TEXT DEFAULT 'Campus City',
                    device TEXT NOT NULL DEFAULT 'Desktop',
                    browser TEXT NOT NULL DEFAULT 'Chrome',
                    operating_system TEXT NOT NULL DEFAULT 'Windows',
                    login_status TEXT NOT NULL DEFAULT 'Success',
                    failure_reason TEXT,
                    login_time TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS security_alerts (
                    alert_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'Medium',
                    description TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Unresolved',
                    created_at TEXT NOT NULL,
                    resolved_at TEXT
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS password_policy (
                    policy_id TEXT PRIMARY KEY,
                    minimum_length INTEGER NOT NULL DEFAULT 8,
                    require_uppercase INTEGER NOT NULL DEFAULT 1,
                    require_lowercase INTEGER NOT NULL DEFAULT 1,
                    require_numbers INTEGER NOT NULL DEFAULT 1,
                    require_special_characters INTEGER NOT NULL DEFAULT 1,
                    password_expiry_days INTEGER NOT NULL DEFAULT 90,
                    password_history_count INTEGER NOT NULL DEFAULT 5,
                    maximum_failed_attempts INTEGER NOT NULL DEFAULT 5,
                    lockout_duration_minutes INTEGER NOT NULL DEFAULT 15,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS mfa_settings (
                    mfa_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL UNIQUE,
                    enabled INTEGER NOT NULL DEFAULT 0,
                    method TEXT NOT NULL DEFAULT 'TOTP',
                    secret_key TEXT,
                    backup_codes TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS ip_access_rules (
                    rule_id TEXT PRIMARY KEY,
                    rule_type TEXT NOT NULL DEFAULT 'Block',
                    ip_address TEXT NOT NULL UNIQUE,
                    description TEXT,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS system_services (
                    service_id TEXT PRIMARY KEY,
                    service_name TEXT NOT NULL UNIQUE,
                    service_type TEXT NOT NULL DEFAULT 'Application',
                    status TEXT NOT NULL DEFAULT 'Healthy',
                    host TEXT DEFAULT '127.0.0.1',
                    port INTEGER DEFAULT 8000,
                    version TEXT DEFAULT 'v2.4.0',
                    last_health_check TEXT NOT NULL,
                    response_time_ms INTEGER NOT NULL DEFAULT 15,
                    uptime_percentage REAL NOT NULL DEFAULT 99.9,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS health_metrics (
                    metric_id TEXT PRIMARY KEY,
                    service_id TEXT NOT NULL,
                    cpu_usage_percent REAL NOT NULL DEFAULT 15.0,
                    memory_usage_percent REAL NOT NULL DEFAULT 35.0,
                    disk_usage_percent REAL NOT NULL DEFAULT 22.0,
                    network_latency_ms INTEGER NOT NULL DEFAULT 12,
                    active_connections INTEGER NOT NULL DEFAULT 45,
                    requests_per_minute INTEGER NOT NULL DEFAULT 180,
                    error_rate REAL NOT NULL DEFAULT 0.01,
                    recorded_at TEXT NOT NULL,
                    FOREIGN KEY (service_id) REFERENCES system_services(service_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS incident_logs (
                    incident_id TEXT PRIMARY KEY,
                    service_id TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'Medium',
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Open',
                    started_at TEXT NOT NULL,
                    resolved_at TEXT,
                    acknowledged_by TEXT,
                    FOREIGN KEY (service_id) REFERENCES system_services(service_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS monitoring_rules (
                    rule_id TEXT PRIMARY KEY,
                    rule_name TEXT NOT NULL,
                    service_type TEXT NOT NULL DEFAULT 'Application',
                    metric TEXT NOT NULL,
                    warning_threshold REAL NOT NULL DEFAULT 80.0,
                    critical_threshold REAL NOT NULL DEFAULT 95.0,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS uptime_history (
                    uptime_id TEXT PRIMARY KEY,
                    service_id TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Healthy',
                    checked_at TEXT NOT NULL,
                    response_time_ms INTEGER NOT NULL DEFAULT 15,
                    FOREIGN KEY (service_id) REFERENCES system_services(service_id)
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS system_configuration (
                    config_id TEXT PRIMARY KEY,
                    config_key TEXT NOT NULL UNIQUE,
                    config_category TEXT NOT NULL DEFAULT 'General',
                    config_value TEXT NOT NULL,
                    value_type TEXT NOT NULL DEFAULT 'string',
                    description TEXT,
                    is_system INTEGER NOT NULL DEFAULT 0,
                    is_encrypted INTEGER NOT NULL DEFAULT 0,
                    editable INTEGER NOT NULL DEFAULT 1,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS feature_flags (
                    flag_id TEXT PRIMARY KEY,
                    flag_key TEXT NOT NULL UNIQUE,
                    feature_name TEXT NOT NULL,
                    description TEXT,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    rollout_percentage INTEGER NOT NULL DEFAULT 100,
                    target_roles TEXT DEFAULT 'all',
                    environment TEXT NOT NULL DEFAULT 'Production',
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS configuration_history (
                    history_id TEXT PRIMARY KEY,
                    config_id TEXT NOT NULL,
                    config_key TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT NOT NULL,
                    changed_by TEXT NOT NULL,
                    change_reason TEXT,
                    changed_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS maintenance_windows (
                    maintenance_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    description TEXT,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    maintenance_type TEXT NOT NULL DEFAULT 'Scheduled',
                    status TEXT NOT NULL DEFAULT 'Upcoming',
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS media_files (
                    media_id TEXT PRIMARY KEY,
                    original_file_name TEXT NOT NULL,
                    stored_file_name TEXT NOT NULL,
                    storage_provider TEXT NOT NULL DEFAULT 'Local',
                    storage_path TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    file_extension TEXT NOT NULL,
                    file_size INTEGER NOT NULL DEFAULT 0,
                    checksum_sha256 TEXT,
                    uploaded_by TEXT NOT NULL,
                    related_module TEXT DEFAULT 'General',
                    related_entity_id TEXT,
                    visibility TEXT NOT NULL DEFAULT 'Public',
                    status TEXT NOT NULL DEFAULT 'Available',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_deleted INTEGER NOT NULL DEFAULT 0
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS media_versions (
                    version_id TEXT PRIMARY KEY,
                    media_id TEXT NOT NULL,
                    version_number INTEGER NOT NULL DEFAULT 1,
                    storage_path TEXT NOT NULL,
                    checksum TEXT,
                    uploaded_by TEXT NOT NULL,
                    uploaded_at TEXT NOT NULL,
                    change_notes TEXT,
                    FOREIGN KEY (media_id) REFERENCES media_files(media_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS storage_providers (
                    provider_id TEXT PRIMARY KEY,
                    provider_name TEXT NOT NULL UNIQUE,
                    provider_type TEXT NOT NULL DEFAULT 'Local',
                    configuration_json TEXT,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    is_default INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS storage_quotas (
                    quota_id TEXT PRIMARY KEY,
                    role TEXT NOT NULL UNIQUE,
                    maximum_storage_mb INTEGER NOT NULL DEFAULT 500,
                    maximum_file_size_mb INTEGER NOT NULL DEFAULT 25,
                    maximum_files INTEGER NOT NULL DEFAULT 100,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS virus_scan_logs (
                    scan_id TEXT PRIMARY KEY,
                    media_id TEXT NOT NULL,
                    scan_engine TEXT NOT NULL DEFAULT 'ClamAV Core',
                    scan_status TEXT NOT NULL DEFAULT 'Clean',
                    threat_name TEXT,
                    scanned_at TEXT NOT NULL,
                    FOREIGN KEY (media_id) REFERENCES media_files(media_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS shared_media_links (
                    link_id TEXT PRIMARY KEY,
                    media_id TEXT NOT NULL,
                    token TEXT NOT NULL UNIQUE,
                    expires_at TEXT NOT NULL,
                    download_limit INTEGER NOT NULL DEFAULT 5,
                    downloads_used INTEGER NOT NULL DEFAULT 0,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (media_id) REFERENCES media_files(media_id)
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS mobile_devices (
                    device_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    device_name TEXT NOT NULL,
                    device_type TEXT NOT NULL DEFAULT 'Android',
                    manufacturer TEXT DEFAULT 'Google',
                    model TEXT DEFAULT 'Pixel 8',
                    operating_system TEXT NOT NULL DEFAULT 'Android',
                    os_version TEXT DEFAULT '14.0',
                    app_version TEXT DEFAULT 'v2.4.0',
                    device_identifier TEXT NOT NULL UNIQUE,
                    push_token TEXT,
                    status TEXT NOT NULL DEFAULT 'Active',
                    last_seen TEXT NOT NULL,
                    registered_at TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS mobile_sessions (
                    mobile_session_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    access_token_hash TEXT,
                    refresh_token_hash TEXT,
                    login_time TEXT NOT NULL,
                    last_activity TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Active',
                    FOREIGN KEY (device_id) REFERENCES mobile_devices(device_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS push_notifications (
                    notification_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    notification_type TEXT DEFAULT 'info',
                    status TEXT NOT NULL DEFAULT 'Sent',
                    sent_at TEXT NOT NULL,
                    delivered_at TEXT,
                    opened_at TEXT,
                    FOREIGN KEY (device_id) REFERENCES mobile_devices(device_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS offline_sync_queue (
                    sync_id TEXT PRIMARY KEY,
                    device_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT,
                    operation TEXT NOT NULL DEFAULT 'Create',
                    payload_json TEXT NOT NULL,
                    sync_status TEXT NOT NULL DEFAULT 'Synced',
                    created_at TEXT NOT NULL,
                    synced_at TEXT,
                    FOREIGN KEY (device_id) REFERENCES mobile_devices(device_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS supported_app_versions (
                    version_id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL DEFAULT 'Android',
                    minimum_version TEXT NOT NULL DEFAULT '1.0.0',
                    latest_version TEXT NOT NULL DEFAULT '2.4.0',
                    force_update INTEGER NOT NULL DEFAULT 0,
                    release_notes TEXT,
                    released_at TEXT NOT NULL
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS ai_models (
                    model_id TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    model_type TEXT NOT NULL DEFAULT 'Classification',
                    provider TEXT NOT NULL DEFAULT 'CampusPulse-NLP-v2',
                    version TEXT NOT NULL DEFAULT 'v2.4',
                    status TEXT NOT NULL DEFAULT 'Active',
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS ai_requests (
                    request_id TEXT PRIMARY KEY,
                    model_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    input_hash TEXT,
                    input_length INTEGER NOT NULL DEFAULT 0,
                    processing_time_ms INTEGER NOT NULL DEFAULT 25,
                    status TEXT NOT NULL DEFAULT 'Completed',
                    confidence_score REAL NOT NULL DEFAULT 0.95,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (model_id) REFERENCES ai_models(model_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS ai_predictions (
                    prediction_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    entity_type TEXT DEFAULT 'Complaint',
                    entity_id TEXT,
                    prediction TEXT NOT NULL,
                    confidence REAL NOT NULL DEFAULT 0.92,
                    accepted INTEGER NOT NULL DEFAULT 1,
                    corrected_by TEXT,
                    corrected_value TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (request_id) REFERENCES ai_requests(request_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS ai_prompts (
                    prompt_id TEXT PRIMARY KEY,
                    prompt_name TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    prompt_template TEXT NOT NULL,
                    version TEXT NOT NULL DEFAULT 'v1.0',
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS ai_feedback (
                    feedback_id TEXT PRIMARY KEY,
                    prediction_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    feedback_type TEXT NOT NULL DEFAULT 'Accepted',
                    rating INTEGER NOT NULL DEFAULT 5,
                    comments TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (prediction_id) REFERENCES ai_predictions(prediction_id)
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS workflow_definitions (
                    workflow_id TEXT PRIMARY KEY,
                    workflow_name TEXT NOT NULL,
                    description TEXT,
                    module_name TEXT NOT NULL DEFAULT 'Complaints',
                    version TEXT NOT NULL DEFAULT 'v1.0',
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS workflow_steps (
                    step_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    step_order INTEGER NOT NULL DEFAULT 1,
                    step_name TEXT NOT NULL,
                    step_type TEXT NOT NULL DEFAULT 'Approval',
                    assigned_role TEXT DEFAULT 'coordinator',
                    condition_expression TEXT,
                    timeout_hours INTEGER DEFAULT 24,
                    next_step_on_success TEXT,
                    next_step_on_failure TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (workflow_id) REFERENCES workflow_definitions(workflow_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS workflow_instances (
                    instance_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    entity_type TEXT NOT NULL DEFAULT 'Complaint',
                    entity_id TEXT,
                    current_step TEXT DEFAULT 'Step 1: Department Approval',
                    status TEXT NOT NULL DEFAULT 'Running',
                    started_by TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    FOREIGN KEY (workflow_id) REFERENCES workflow_definitions(workflow_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS workflow_tasks (
                    task_id TEXT PRIMARY KEY,
                    instance_id TEXT NOT NULL,
                    step_id TEXT NOT NULL,
                    assigned_user TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Pending',
                    action_taken TEXT,
                    comments TEXT,
                    assigned_at TEXT NOT NULL,
                    completed_at TEXT,
                    FOREIGN KEY (instance_id) REFERENCES workflow_instances(instance_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS workflow_history (
                    history_id TEXT PRIMARY KEY,
                    instance_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    performed_by TEXT NOT NULL,
                    action TEXT NOT NULL,
                    remarks TEXT,
                    performed_at TEXT NOT NULL,
                    FOREIGN KEY (instance_id) REFERENCES workflow_instances(instance_id)
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS business_rules (
                    rule_id TEXT PRIMARY KEY,
                    rule_name TEXT NOT NULL,
                    rule_category TEXT NOT NULL DEFAULT 'Complaint Rules',
                    description TEXT,
                    version TEXT NOT NULL DEFAULT 'v1.0',
                    priority INTEGER NOT NULL DEFAULT 1,
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS rule_conditions (
                    condition_id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    field_name TEXT NOT NULL,
                    operator TEXT NOT NULL DEFAULT 'Equals',
                    comparison_value TEXT NOT NULL,
                    logical_group TEXT DEFAULT 'AND',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (rule_id) REFERENCES business_rules(rule_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS rule_actions (
                    action_id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    action_type TEXT NOT NULL DEFAULT 'AssignPriority',
                    action_parameters TEXT,
                    execution_order INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (rule_id) REFERENCES business_rules(rule_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS decision_tables (
                    decision_table_id TEXT PRIMARY KEY,
                    table_name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    version TEXT NOT NULL DEFAULT 'v1.0',
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS rule_execution_logs (
                    execution_id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    entity_type TEXT DEFAULT 'Complaint',
                    entity_id TEXT,
                    result TEXT NOT NULL,
                    execution_time_ms INTEGER DEFAULT 12,
                    executed_at TEXT NOT NULL,
                    FOREIGN KEY (rule_id) REFERENCES business_rules(rule_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS rule_simulations (
                    simulation_id TEXT PRIMARY KEY,
                    rule_id TEXT NOT NULL,
                    input_payload TEXT NOT NULL,
                    predicted_result TEXT NOT NULL,
                    executed_by TEXT NOT NULL,
                    executed_at TEXT NOT NULL,
                    FOREIGN KEY (rule_id) REFERENCES business_rules(rule_id)
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS event_types (
                    event_type_id TEXT PRIMARY KEY,
                    event_name TEXT NOT NULL UNIQUE,
                    event_version TEXT NOT NULL DEFAULT 'v1.0',
                    description TEXT,
                    category TEXT NOT NULL DEFAULT 'Business',
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS event_log (
                    event_id TEXT PRIMARY KEY,
                    event_type_id TEXT NOT NULL,
                    entity_type TEXT DEFAULT 'Complaint',
                    entity_id TEXT,
                    payload_json TEXT NOT NULL,
                    published_by TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Completed',
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    correlation_id TEXT NOT NULL,
                    FOREIGN KEY (event_type_id) REFERENCES event_types(event_type_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS event_subscriptions (
                    subscription_id TEXT PRIMARY KEY,
                    event_type_id TEXT NOT NULL,
                    subscriber_name TEXT NOT NULL,
                    handler_name TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    retry_policy TEXT NOT NULL DEFAULT 'Linear-3x',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (event_type_id) REFERENCES event_types(event_type_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS dead_letter_queue (
                    dlq_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    failure_reason TEXT NOT NULL,
                    failed_at TEXT NOT NULL,
                    resolved INTEGER NOT NULL DEFAULT 0,
                    resolved_at TEXT,
                    resolved_by TEXT,
                    FOREIGN KEY (event_id) REFERENCES event_log(event_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS event_replay_history (
                    replay_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    replayed_by TEXT NOT NULL,
                    replayed_at TEXT NOT NULL,
                    result TEXT NOT NULL,
                    FOREIGN KEY (event_id) REFERENCES event_log(event_id)
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS integration_connectors (
                    connector_id TEXT PRIMARY KEY,
                    connector_name TEXT NOT NULL UNIQUE,
                    connector_type TEXT NOT NULL DEFAULT 'REST',
                    provider TEXT NOT NULL DEFAULT 'Google Workspace',
                    base_url TEXT,
                    authentication_type TEXT DEFAULT 'OAuth2',
                    status TEXT NOT NULL DEFAULT 'Active',
                    configuration_json TEXT,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS integration_jobs (
                    job_id TEXT PRIMARY KEY,
                    connector_id TEXT NOT NULL,
                    job_name TEXT NOT NULL,
                    trigger_type TEXT NOT NULL DEFAULT 'Scheduled',
                    schedule_expression TEXT DEFAULT '0 */6 * * *',
                    status TEXT NOT NULL DEFAULT 'Completed',
                    last_run TEXT,
                    next_run TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (connector_id) REFERENCES integration_connectors(connector_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS integration_mappings (
                    mapping_id TEXT PRIMARY KEY,
                    connector_id TEXT NOT NULL,
                    source_field TEXT NOT NULL,
                    target_field TEXT NOT NULL,
                    transformation_rule TEXT DEFAULT 'Uppercase',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (connector_id) REFERENCES integration_connectors(connector_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS integration_logs (
                    log_id TEXT PRIMARY KEY,
                    connector_id TEXT NOT NULL,
                    job_id TEXT,
                    request_summary TEXT NOT NULL,
                    response_summary TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'Success',
                    duration_ms INTEGER DEFAULT 240,
                    executed_at TEXT NOT NULL,
                    FOREIGN KEY (connector_id) REFERENCES integration_connectors(connector_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS integration_errors (
                    error_id TEXT PRIMARY KEY,
                    connector_id TEXT NOT NULL,
                    job_id TEXT,
                    error_code TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    retry_count INTEGER DEFAULT 0,
                    resolved INTEGER NOT NULL DEFAULT 0,
                    occurred_at TEXT NOT NULL,
                    FOREIGN KEY (connector_id) REFERENCES integration_connectors(connector_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS synchronization_history (
                    sync_id TEXT PRIMARY KEY,
                    connector_id TEXT NOT NULL,
                    entity_type TEXT DEFAULT 'Users',
                    records_processed INTEGER DEFAULT 500,
                    records_success INTEGER DEFAULT 498,
                    records_failed INTEGER DEFAULT 2,
                    started_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    FOREIGN KEY (connector_id) REFERENCES integration_connectors(connector_id)
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS data_classifications (
                    classification_id TEXT PRIMARY KEY,
                    classification_name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    sensitivity_level TEXT NOT NULL DEFAULT 'Confidential',
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS retention_policies (
                    policy_id TEXT PRIMARY KEY,
                    module_name TEXT NOT NULL DEFAULT 'Complaints',
                    entity_type TEXT NOT NULL DEFAULT 'Complaint',
                    retention_period_days INTEGER DEFAULT 365,
                    archive_after_days INTEGER DEFAULT 180,
                    delete_after_days INTEGER DEFAULT 365,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS consent_records (
                    consent_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    consent_type TEXT NOT NULL DEFAULT 'Marketing',
                    granted INTEGER NOT NULL DEFAULT 1,
                    granted_at TEXT NOT NULL,
                    withdrawn_at TEXT,
                    version TEXT DEFAULT 'v1.0'
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS privacy_requests (
                    request_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    request_type TEXT NOT NULL DEFAULT 'DataExport',
                    status TEXT NOT NULL DEFAULT 'Pending',
                    submitted_at TEXT NOT NULL,
                    processed_at TEXT,
                    processed_by TEXT,
                    remarks TEXT
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS legal_holds (
                    hold_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL DEFAULT 'Complaint',
                    entity_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    active INTEGER NOT NULL DEFAULT 1
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS masking_rules (
                    rule_id TEXT PRIMARY KEY,
                    field_name TEXT NOT NULL,
                    masking_type TEXT NOT NULL DEFAULT 'Partial',
                    roles_allowed TEXT DEFAULT 'administrator,app_manager',
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS governance_reports (
                    report_id TEXT PRIMARY KEY,
                    report_type TEXT NOT NULL DEFAULT 'GDPR Audit Report',
                    generated_by TEXT NOT NULL,
                    generated_at TEXT NOT NULL,
                    storage_location TEXT
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS activity_events (
                    activity_id TEXT PRIMARY KEY,
                    activity_type TEXT NOT NULL DEFAULT 'View',
                    module_name TEXT NOT NULL DEFAULT 'Complaints',
                    entity_type TEXT DEFAULT 'Complaint',
                    entity_id TEXT,
                    user_id TEXT NOT NULL,
                    session_id TEXT,
                    description TEXT NOT NULL,
                    ip_address TEXT DEFAULT '127.0.0.1',
                    device_type TEXT DEFAULT 'Web Browser',
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS module_usage_statistics (
                    usage_id TEXT PRIMARY KEY,
                    module_name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    active_users INTEGER DEFAULT 120,
                    requests_count INTEGER DEFAULT 1450,
                    average_response_time_ms INTEGER DEFAULT 24,
                    errors_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS user_activity_summary (
                    summary_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    login_count INTEGER DEFAULT 12,
                    actions_performed INTEGER DEFAULT 45,
                    average_session_duration TEXT DEFAULT '24 mins',
                    last_active TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS activity_timelines (
                    timeline_id TEXT PRIMARY KEY,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    activity_id TEXT NOT NULL,
                    sequence_number INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (activity_id) REFERENCES activity_events(activity_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS dashboard_widgets (
                    widget_id TEXT PRIMARY KEY,
                    widget_name TEXT NOT NULL,
                    widget_type TEXT NOT NULL DEFAULT 'KPICard',
                    configuration_json TEXT,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS operational_kpis (
                    kpi_id TEXT PRIMARY KEY,
                    kpi_name TEXT NOT NULL UNIQUE,
                    current_value REAL NOT NULL,
                    target_value REAL NOT NULL,
                    unit TEXT DEFAULT '%',
                    last_updated TEXT NOT NULL
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS configuration_keys (
                    config_id TEXT PRIMARY KEY,
                    config_key TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    description TEXT,
                    data_type TEXT NOT NULL DEFAULT 'String',
                    scope TEXT NOT NULL DEFAULT 'Global',
                    default_value TEXT NOT NULL,
                    validation_rule TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS configuration_values (
                    value_id TEXT PRIMARY KEY,
                    config_id TEXT NOT NULL,
                    scope_type TEXT NOT NULL DEFAULT 'Global',
                    scope_id TEXT NOT NULL DEFAULT 'global',
                    config_value TEXT NOT NULL,
                    effective_from TEXT,
                    effective_until TEXT,
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (config_id) REFERENCES configuration_keys(config_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS configuration_templates (
                    template_id TEXT PRIMARY KEY,
                    template_name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    configuration_json TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS configuration_history (
                    history_id TEXT PRIMARY KEY,
                    config_id TEXT NOT NULL,
                    old_value TEXT,
                    new_value TEXT NOT NULL,
                    changed_by TEXT NOT NULL,
                    changed_at TEXT NOT NULL,
                    reason TEXT,
                    FOREIGN KEY (config_id) REFERENCES configuration_keys(config_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS configuration_dependencies (
                    dependency_id TEXT PRIMARY KEY,
                    parent_config TEXT NOT NULL,
                    child_config TEXT NOT NULL,
                    dependency_type TEXT DEFAULT 'Requires',
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS runtime_cache (
                    cache_id TEXT PRIMARY KEY,
                    config_key TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    cached_value TEXT NOT NULL,
                    last_refreshed TEXT NOT NULL,
                    expires_at TEXT
                )
                """)

            connection.execute("""
                CREATE TABLE IF NOT EXISTS recovery_plans (
                    plan_id TEXT PRIMARY KEY,
                    plan_name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    system_scope TEXT DEFAULT 'Full Platform',
                    recovery_type TEXT NOT NULL DEFAULT 'Database',
                    rto_minutes INTEGER DEFAULT 60,
                    rpo_minutes INTEGER DEFAULT 15,
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS restore_points (
                    restore_point_id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    backup_reference TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    storage_location TEXT NOT NULL,
                    verified INTEGER DEFAULT 0,
                    checksum TEXT NOT NULL,
                    FOREIGN KEY (plan_id) REFERENCES recovery_plans(plan_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS recovery_drills (
                    drill_id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    scheduled_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    status TEXT NOT NULL DEFAULT 'Scheduled',
                    executed_by TEXT NOT NULL,
                    report_location TEXT,
                    FOREIGN KEY (plan_id) REFERENCES recovery_plans(plan_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS failover_targets (
                    target_id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    environment TEXT NOT NULL DEFAULT 'Secondary DC',
                    endpoint TEXT NOT NULL,
                    priority INTEGER DEFAULT 1,
                    health_status TEXT DEFAULT 'Healthy',
                    last_checked TEXT NOT NULL,
                    FOREIGN KEY (plan_id) REFERENCES recovery_plans(plan_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS recovery_history (
                    history_id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    performed_by TEXT NOT NULL,
                    result TEXT DEFAULT 'Success',
                    started_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    remarks TEXT,
                    FOREIGN KEY (plan_id) REFERENCES recovery_plans(plan_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS continuity_procedures (
                    procedure_id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    step_order INTEGER DEFAULT 1,
                    title TEXT NOT NULL,
                    instructions TEXT NOT NULL,
                    mandatory INTEGER DEFAULT 1,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (plan_id) REFERENCES recovery_plans(plan_id)
                )
                """)

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_rp_stat ON recovery_plans(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_rst_ver ON restore_points(verified)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_rd_stat ON recovery_drills(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ft_hlth ON failover_targets(health_status)"
            )

            connection.execute("""
                CREATE TABLE IF NOT EXISTS release_versions (
                    release_id TEXT PRIMARY KEY,
                    version_number TEXT NOT NULL UNIQUE,
                    release_name TEXT NOT NULL,
                    description TEXT,
                    release_type TEXT NOT NULL DEFAULT 'Minor',
                    status TEXT NOT NULL DEFAULT 'Draft',
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    released_at TEXT
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS deployment_pipelines (
                    pipeline_id TEXT PRIMARY KEY,
                    pipeline_name TEXT NOT NULL UNIQUE,
                    environment TEXT NOT NULL DEFAULT 'Production',
                    deployment_strategy TEXT NOT NULL DEFAULT 'Rolling',
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS deployment_history (
                    deployment_id TEXT PRIMARY KEY,
                    release_id TEXT NOT NULL,
                    pipeline_id TEXT NOT NULL,
                    environment TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    status TEXT NOT NULL DEFAULT 'Success',
                    executed_by TEXT NOT NULL,
                    duration_seconds INTEGER DEFAULT 120,
                    FOREIGN KEY (release_id) REFERENCES release_versions(release_id),
                    FOREIGN KEY (pipeline_id) REFERENCES deployment_pipelines(pipeline_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS environments (
                    environment_id TEXT PRIMARY KEY,
                    environment_name TEXT NOT NULL UNIQUE,
                    environment_type TEXT NOT NULL DEFAULT 'Production',
                    endpoint TEXT NOT NULL,
                    health_status TEXT DEFAULT 'Healthy',
                    current_version TEXT DEFAULT 'v2.4.0'
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS maintenance_windows (
                    window_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    scheduled_start TEXT NOT NULL,
                    scheduled_end TEXT NOT NULL,
                    affected_modules TEXT DEFAULT 'All System Modules',
                    status TEXT NOT NULL DEFAULT 'Scheduled',
                    created_by TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS rollback_plans (
                    rollback_id TEXT PRIMARY KEY,
                    release_id TEXT NOT NULL,
                    rollback_version TEXT NOT NULL,
                    rollback_strategy TEXT DEFAULT 'Immediate Rollback',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (release_id) REFERENCES release_versions(release_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS release_notes (
                    note_id TEXT PRIMARY KEY,
                    release_id TEXT NOT NULL,
                    category TEXT DEFAULT 'Feature',
                    description TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (release_id) REFERENCES release_versions(release_id)
                )
                """)

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_rv_ver ON release_versions(version_number)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_rv_stat ON release_versions(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_dh_env ON deployment_history(environment)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_mw_stat ON maintenance_windows(status)"
            )

            connection.execute("""
                CREATE TABLE IF NOT EXISTS plugins (
                    plugin_id TEXT PRIMARY KEY,
                    plugin_name TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL DEFAULT 'Academic',
                    version TEXT NOT NULL DEFAULT 'v1.0.0',
                    provider TEXT DEFAULT 'CampusPulse Core Team',
                    status TEXT NOT NULL DEFAULT 'Installed',
                    installed_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS plugin_versions (
                    version_id TEXT PRIMARY KEY,
                    plugin_id TEXT NOT NULL,
                    version TEXT NOT NULL,
                    minimum_platform_version TEXT DEFAULT 'v2.0.0',
                    maximum_platform_version TEXT DEFAULT 'v3.0.0',
                    release_notes TEXT,
                    published_at TEXT NOT NULL,
                    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS plugin_dependencies (
                    dependency_id TEXT PRIMARY KEY,
                    plugin_id TEXT NOT NULL,
                    depends_on_plugin TEXT NOT NULL,
                    minimum_version TEXT DEFAULT 'v1.0.0',
                    required INTEGER DEFAULT 1,
                    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS plugin_permissions (
                    permission_id TEXT PRIMARY KEY,
                    plugin_id TEXT NOT NULL,
                    permission_name TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    access_level TEXT DEFAULT 'ReadWrite',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS installed_extensions (
                    extension_id TEXT PRIMARY KEY,
                    plugin_id TEXT NOT NULL,
                    installation_scope TEXT DEFAULT 'Global',
                    enabled INTEGER DEFAULT 1,
                    installed_by TEXT NOT NULL,
                    installed_at TEXT NOT NULL,
                    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS marketplace_packages (
                    package_id TEXT PRIMARY KEY,
                    plugin_name TEXT NOT NULL UNIQUE,
                    provider TEXT NOT NULL,
                    latest_version TEXT NOT NULL,
                    download_reference TEXT NOT NULL,
                    verified INTEGER DEFAULT 1,
                    published_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS plugin_usage_statistics (
                    usage_id TEXT PRIMARY KEY,
                    plugin_id TEXT NOT NULL,
                    active_users INTEGER DEFAULT 140,
                    requests INTEGER DEFAULT 2100,
                    errors INTEGER DEFAULT 0,
                    average_response_time_ms INTEGER DEFAULT 14,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id)
                )
                """)

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_plg_cat ON plugins(category)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_plg_stat ON plugins(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_mp_name ON marketplace_packages(plugin_name)"
            )
            # Legacy enterprise tables are retained for safe migration, but are not used by Campus Pulse.
            connection.execute("""
                CREATE TABLE IF NOT EXISTS deprecated_schema_objects (
                    object_name TEXT PRIMARY KEY,
                    replacement TEXT NOT NULL,
                    deprecated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            for object_name, replacement in (
                ("marketplace_packages", "No replacement; marketplace removed"),
                ("deployment_pipelines", "External CI/CD"),
                ("deployment_history", "External CI/CD"),
                ("failover_targets", "Backup & Recovery"),
                ("recovery_drills", "Backup & Recovery"),
                ("integration_connectors", "Notifications or optional ERP API"),
                ("integration_jobs", "Notifications or optional ERP API"),
                ("integration_mappings", "Notifications or optional ERP API"),
                ("integration_logs", "System Monitoring"),
                ("integration_errors", "System Monitoring"),
            ):
                connection.execute(
                    "INSERT OR IGNORE INTO deprecated_schema_objects (object_name, replacement) VALUES (?, ?)",
                    (object_name, replacement),
                )

            connection.execute("""
                CREATE TABLE IF NOT EXISTS organizations (
                    organization_id TEXT PRIMARY KEY,
                    organization_name TEXT NOT NULL UNIQUE,
                    organization_type TEXT NOT NULL DEFAULT 'University',
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS organization_units (
                    unit_id TEXT PRIMARY KEY,
                    organization_id TEXT NOT NULL,
                    parent_unit_id TEXT,
                    unit_name TEXT NOT NULL,
                    unit_code TEXT NOT NULL UNIQUE,
                    head_user_id TEXT,
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (organization_id) REFERENCES organizations(organization_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS campuses (
                    campus_id TEXT PRIMARY KEY,
                    campus_name TEXT NOT NULL UNIQUE,
                    address TEXT,
                    timezone TEXT DEFAULT 'Asia/Kolkata',
                    contact_email TEXT DEFAULT 'admin@campuspulse.edu',
                    status TEXT NOT NULL DEFAULT 'Active',
                    created_at TEXT NOT NULL
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS buildings (
                    building_id TEXT PRIMARY KEY,
                    campus_id TEXT NOT NULL,
                    building_name TEXT NOT NULL,
                    building_code TEXT NOT NULL UNIQUE,
                    floors INTEGER DEFAULT 4,
                    status TEXT NOT NULL DEFAULT 'Active',
                    FOREIGN KEY (campus_id) REFERENCES campuses(campus_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS rooms (
                    room_id TEXT PRIMARY KEY,
                    building_id TEXT,
                    floor_id TEXT,
                    room_number TEXT NOT NULL,
                    room_type TEXT NOT NULL DEFAULT 'Classroom',
                    capacity INTEGER DEFAULT 40,
                    occupied INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'Active',
                    FOREIGN KEY (building_id) REFERENCES buildings(building_id)
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS user_affiliations (
                    affiliation_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    organization_unit TEXT NOT NULL,
                    role TEXT NOT NULL,
                    effective_from TEXT NOT NULL,
                    effective_until TEXT,
                    active INTEGER DEFAULT 1
                )
                """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS academic_calendar (
                    calendar_id TEXT PRIMARY KEY,
                    campus_id TEXT NOT NULL,
                    event_name TEXT NOT NULL,
                    event_type TEXT NOT NULL DEFAULT 'Event',
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (campus_id) REFERENCES campuses(campus_id)
                )
                """)

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_org_type ON organizations(organization_type)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ou_code ON organization_units(unit_code)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_bld_code ON buildings(building_code)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_aff_usr ON user_affiliations(user_id)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ck_key ON configuration_keys(config_key)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_cv_stat ON configuration_values(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_cv_scope ON configuration_values(scope_type, scope_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_rc_key ON runtime_cache(config_key)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_act_mod ON activity_events(module_name)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_act_user ON activity_events(user_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_act_type ON activity_events(activity_type)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_mus_mod ON module_usage_statistics(module_name)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_dc_sens ON data_classifications(sensitivity_level)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_rp_mod ON retention_policies(module_name)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_pr_stat ON privacy_requests(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_lh_act ON legal_holds(active)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ic_prov ON integration_connectors(provider)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ic_stat ON integration_connectors(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ij_stat ON integration_jobs(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ierr_res ON integration_errors(resolved)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_evt_cat ON event_types(category)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_evl_stat ON event_log(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_evl_corr ON event_log(correlation_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_dlq_res ON dead_letter_queue(resolved)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_br_cat ON business_rules(rule_category)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_br_stat ON business_rules(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_br_prio ON business_rules(priority)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_brex_rule ON rule_execution_logs(rule_id)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_wf_mod ON workflow_definitions(module_name)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_wf_stat ON workflow_definitions(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_wfi_stat ON workflow_instances(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_wft_user ON workflow_tasks(assigned_user)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_aim_type ON ai_models(model_type)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_aim_status ON ai_models(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_air_task ON ai_requests(task_type)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_aip_entity ON ai_predictions(entity_id)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_mob_user ON mobile_devices(user_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_mob_status ON mobile_devices(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_push_dev ON push_notifications(device_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_sync_status ON offline_sync_queue(sync_status)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_med_mod ON media_files(related_module)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_med_stat ON media_files(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_med_user ON media_files(uploaded_by)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_scan_stat ON virus_scan_logs(scan_status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_link_tok ON shared_media_links(token)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_cfg_cat ON system_configuration(config_category)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ff_key ON feature_flags(flag_key)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ff_env ON feature_flags(environment)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_maint_stat ON maintenance_windows(status)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_srv_type ON system_services(service_type)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_srv_status ON system_services(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_met_srv ON health_metrics(service_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_inc_status ON incident_logs(status)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_sess_user ON user_sessions(user_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_sess_status ON user_sessions(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_log_status ON login_history(login_status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_sec_alert ON security_alerts(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_mfa_user ON mfa_settings(user_id)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_api_status ON api_keys(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_api_owner ON api_keys(owner_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_wh_enabled ON webhook_endpoints(enabled)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_usg_req ON api_usage_logs(requested_at)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_int_cat ON integration_registry(category)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_bkp_type ON backups(backup_type)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_bkp_status ON backups(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_rst_bkp ON restore_history(backup_id)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_dash_user ON dashboard_layouts(user_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_dash_wdg ON dashboard_widgets(layout_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_dash_fav ON favorite_modules(user_id)"
            )

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

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_job_type ON scheduled_jobs(job_type)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_job_enabled ON scheduled_jobs(enabled)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_q_status ON job_queue(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_q_priority ON job_queue(priority)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_hist_job ON job_history(job_id)"
            )

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

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ast_code ON assets(asset_code)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ast_cat ON assets(category_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ast_status ON assets(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ast_cond ON assets(current_condition)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_ast_dept ON assets(department_id)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_wo_num ON work_orders(work_order_number)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_wo_cmpl ON work_orders(complaint_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_wo_tech ON work_orders(assigned_technician_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_wo_status ON work_orders(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_wo_priority ON work_orders(priority)"
            )

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_vis_phone ON visitors(phone_number)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_vis_gov_id ON visitors(government_id_number)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_req_host ON visitor_requests(host_user_id)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_req_status ON visitor_requests(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_req_date ON visitor_requests(visit_date)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_pass_otp ON visitor_gate_pass(otp)"
            )

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

            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_resources_cat ON resources(category)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_resources_status ON resources(status)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_bookings_res_date ON resource_bookings(resource_id, booking_date)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_bookings_user ON resource_bookings(booked_by)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_bookings_status ON resource_bookings(status)"
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
