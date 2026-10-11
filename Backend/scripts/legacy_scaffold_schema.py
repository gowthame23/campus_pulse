"""
Campus Pulse — Legacy Scaffold Schema Module
Contains DDL statements for speculative enterprise tables that were defined during
early prototyping but are not part of the active Campus Pulse core product runtime.

These tables are preserved here so they are NOT auto-created in fresh database
initializations. Existing databases retain them for backward compatibility.
An administrator can optionally apply them using `apply_legacy_scaffold(db_path)`.
"""
import os
import sqlite3
from pathlib import Path


LEGACY_SCAFFOLD_DDL = """
-- Resource Management
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
);

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
);

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
);

-- Visitor Management
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
);

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
);

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
);

CREATE TABLE IF NOT EXISTS visitor_documents (
    document_id TEXT PRIMARY KEY,
    visitor_id TEXT NOT NULL,
    document_type TEXT NOT NULL DEFAULT 'Government ID',
    document_url TEXT NOT NULL,
    verified INTEGER NOT NULL DEFAULT 0,
    verified_by TEXT,
    uploaded_at TEXT NOT NULL,
    FOREIGN KEY (visitor_id) REFERENCES visitors(visitor_id)
);

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
);

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
);

CREATE TABLE IF NOT EXISTS visitor_blacklist (
    blacklist_id TEXT PRIMARY KEY,
    visitor_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    added_by TEXT NOT NULL,
    added_at TEXT NOT NULL,
    expires_at TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (visitor_id) REFERENCES visitors(visitor_id)
);

-- Work Orders & Maintenance
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
);

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
);

CREATE TABLE IF NOT EXISTS work_order_notes (
    note_id TEXT PRIMARY KEY,
    work_order_id TEXT NOT NULL,
    author_id TEXT NOT NULL,
    visibility TEXT NOT NULL DEFAULT 'Public',
    note TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (work_order_id) REFERENCES work_orders(work_order_id)
);

CREATE TABLE IF NOT EXISTS work_order_images (
    image_id TEXT PRIMARY KEY,
    work_order_id TEXT NOT NULL,
    uploaded_by TEXT NOT NULL,
    image_type TEXT NOT NULL DEFAULT 'Evidence',
    image_url TEXT NOT NULL,
    uploaded_at TEXT NOT NULL,
    FOREIGN KEY (work_order_id) REFERENCES work_orders(work_order_id)
);

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
);

CREATE TABLE IF NOT EXISTS work_order_time_logs (
    time_log_id TEXT PRIMARY KEY,
    work_order_id TEXT NOT NULL,
    technician_id TEXT NOT NULL,
    clock_in TEXT NOT NULL,
    clock_out TEXT,
    hours_worked REAL DEFAULT 0.0,
    remarks TEXT,
    FOREIGN KEY (work_order_id) REFERENCES work_orders(work_order_id)
);

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
);

-- Asset Management
CREATE TABLE IF NOT EXISTS asset_categories (
    category_id TEXT PRIMARY KEY,
    category_name TEXT NOT NULL UNIQUE,
    parent_category TEXT,
    description TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

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
);

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
);

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
);

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
);

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
);

CREATE TABLE IF NOT EXISTS asset_disposals (
    disposal_id TEXT PRIMARY KEY,
    asset_id TEXT NOT NULL UNIQUE,
    disposal_reason TEXT NOT NULL,
    approved_by TEXT NOT NULL,
    disposal_date TEXT NOT NULL,
    disposal_method TEXT,
    remarks TEXT,
    FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
);

-- Scheduled Job Engine
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
);

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
);

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
);

CREATE TABLE IF NOT EXISTS workers (
    worker_id TEXT PRIMARY KEY,
    worker_name TEXT NOT NULL,
    host TEXT NOT NULL DEFAULT 'localhost',
    status TEXT NOT NULL DEFAULT 'Online',
    started_at TEXT NOT NULL,
    last_heartbeat TEXT NOT NULL,
    active_jobs INTEGER NOT NULL DEFAULT 0,
    version TEXT DEFAULT '1.0.0'
);

CREATE TABLE IF NOT EXISTS job_retry_policy (
    policy_id TEXT PRIMARY KEY,
    job_type TEXT NOT NULL UNIQUE,
    max_retries INTEGER NOT NULL DEFAULT 3,
    retry_interval INTEGER NOT NULL DEFAULT 60,
    backoff_strategy TEXT NOT NULL DEFAULT 'Fixed',
    active INTEGER NOT NULL DEFAULT 1
);

-- Dashboard Customization
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
);

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
);

CREATE TABLE IF NOT EXISTS favorite_modules (
    favorite_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    module_name TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    UNIQUE(user_id, module_name)
);

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
);

CREATE TABLE IF NOT EXISTS quick_actions (
    action_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    action_name TEXT NOT NULL,
    route TEXT NOT NULL,
    icon TEXT NOT NULL DEFAULT 'Plus',
    display_order INTEGER NOT NULL DEFAULT 1,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

-- API Management
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
);

CREATE TABLE IF NOT EXISTS oauth_clients (
    client_id TEXT PRIMARY KEY,
    client_name TEXT NOT NULL,
    client_secret_hash TEXT NOT NULL,
    redirect_uri TEXT NOT NULL,
    grant_type TEXT NOT NULL DEFAULT 'authorization_code',
    owner_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active',
    created_at TEXT NOT NULL
);

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
);

CREATE TABLE IF NOT EXISTS api_usage_logs (
    usage_id TEXT PRIMARY KEY,
    api_key_id TEXT,
    endpoint TEXT NOT NULL,
    http_method TEXT NOT NULL,
    status_code INTEGER NOT NULL,
    response_time_ms INTEGER NOT NULL DEFAULT 0,
    client_ip TEXT,
    requested_at TEXT NOT NULL
);

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
);

-- Advanced Session & Device Tracking
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
);

CREATE TABLE IF NOT EXISTS password_resets (
    reset_id TEXT PRIMARY KEY,
    user_id TEXT,
    email TEXT NOT NULL,
    otp TEXT NOT NULL,
    attempts INTEGER DEFAULT 0,
    expires_at REAL NOT NULL,
    used INTEGER DEFAULT 0,
    created_at REAL NOT NULL
);

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
);

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
);

CREATE TABLE IF NOT EXISTS security_alerts (
    alert_id TEXT PRIMARY KEY,
    user_id TEXT,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'Medium',
    description TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Unresolved',
    created_at TEXT NOT NULL,
    resolved_at TEXT
);

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
);

CREATE TABLE IF NOT EXISTS mfa_settings (
    mfa_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL UNIQUE,
    enabled INTEGER NOT NULL DEFAULT 0,
    method TEXT NOT NULL DEFAULT 'TOTP',
    secret_key TEXT,
    backup_codes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ip_access_rules (
    rule_id TEXT PRIMARY KEY,
    rule_type TEXT NOT NULL DEFAULT 'Block',
    ip_address TEXT NOT NULL UNIQUE,
    description TEXT,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

-- Platform Monitoring
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
);

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
);

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
);

CREATE TABLE IF NOT EXISTS monitoring_rules (
    rule_id TEXT PRIMARY KEY,
    rule_name TEXT NOT NULL,
    service_type TEXT NOT NULL DEFAULT 'Application',
    metric TEXT NOT NULL,
    warning_threshold REAL NOT NULL DEFAULT 80.0,
    critical_threshold REAL NOT NULL DEFAULT 95.0,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS uptime_history (
    uptime_id TEXT PRIMARY KEY,
    service_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Healthy',
    checked_at TEXT NOT NULL,
    response_time_ms INTEGER NOT NULL DEFAULT 15,
    FOREIGN KEY (service_id) REFERENCES system_services(service_id)
);

-- Advanced Configuration
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
);

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
);

CREATE TABLE IF NOT EXISTS configuration_history (
    history_id TEXT PRIMARY KEY,
    config_id TEXT NOT NULL,
    config_key TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT NOT NULL,
    changed_by TEXT NOT NULL,
    change_reason TEXT,
    changed_at TEXT NOT NULL
);

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
);

-- Advanced Media Storage
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
);

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
);

CREATE TABLE IF NOT EXISTS storage_providers (
    provider_id TEXT PRIMARY KEY,
    provider_name TEXT NOT NULL UNIQUE,
    provider_type TEXT NOT NULL DEFAULT 'Local',
    configuration_json TEXT,
    enabled INTEGER NOT NULL DEFAULT 1,
    is_default INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS storage_quotas (
    quota_id TEXT PRIMARY KEY,
    role TEXT NOT NULL UNIQUE,
    maximum_storage_mb INTEGER NOT NULL DEFAULT 500,
    maximum_file_size_mb INTEGER NOT NULL DEFAULT 25,
    maximum_files INTEGER NOT NULL DEFAULT 100,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS virus_scan_logs (
    scan_id TEXT PRIMARY KEY,
    media_id TEXT NOT NULL,
    scan_engine TEXT NOT NULL DEFAULT 'ClamAV Core',
    scan_status TEXT NOT NULL DEFAULT 'Clean',
    threat_name TEXT,
    scanned_at TEXT NOT NULL,
    FOREIGN KEY (media_id) REFERENCES media_files(media_id)
);

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
);

-- Mobile App Support
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
);

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
);

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
);

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
);

CREATE TABLE IF NOT EXISTS supported_app_versions (
    version_id TEXT PRIMARY KEY,
    platform TEXT NOT NULL DEFAULT 'Android',
    minimum_version TEXT NOT NULL DEFAULT '1.0.0',
    latest_version TEXT NOT NULL DEFAULT '2.4.0',
    force_update INTEGER NOT NULL DEFAULT 0,
    release_notes TEXT,
    released_at TEXT NOT NULL
);

-- Speculative AI Engine
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
);

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
);

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
);

CREATE TABLE IF NOT EXISTS ai_prompts (
    prompt_id TEXT PRIMARY KEY,
    prompt_name TEXT NOT NULL,
    task_type TEXT NOT NULL,
    prompt_template TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT 'v1.0',
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ai_feedback (
    feedback_id TEXT PRIMARY KEY,
    prediction_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    feedback_type TEXT NOT NULL DEFAULT 'Accepted',
    rating INTEGER NOT NULL DEFAULT 5,
    comments TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (prediction_id) REFERENCES ai_predictions(prediction_id)
);

-- Speculative BPMN Workflows
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
);

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
);

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
);

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
);

CREATE TABLE IF NOT EXISTS workflow_history (
    history_id TEXT PRIMARY KEY,
    instance_id TEXT NOT NULL,
    step_name TEXT NOT NULL,
    performed_by TEXT NOT NULL,
    action TEXT NOT NULL,
    remarks TEXT,
    performed_at TEXT NOT NULL,
    FOREIGN KEY (instance_id) REFERENCES workflow_instances(instance_id)
);

-- Speculative Business Rules Engine
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
);

CREATE TABLE IF NOT EXISTS rule_conditions (
    condition_id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    field_name TEXT NOT NULL,
    operator TEXT NOT NULL DEFAULT 'Equals',
    comparison_value TEXT NOT NULL,
    logical_group TEXT DEFAULT 'AND',
    created_at TEXT NOT NULL,
    FOREIGN KEY (rule_id) REFERENCES business_rules(rule_id)
);

CREATE TABLE IF NOT EXISTS rule_actions (
    action_id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    action_type TEXT NOT NULL DEFAULT 'AssignPriority',
    action_parameters TEXT,
    execution_order INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (rule_id) REFERENCES business_rules(rule_id)
);

CREATE TABLE IF NOT EXISTS decision_tables (
    decision_table_id TEXT PRIMARY KEY,
    table_name TEXT NOT NULL UNIQUE,
    description TEXT,
    version TEXT NOT NULL DEFAULT 'v1.0',
    status TEXT NOT NULL DEFAULT 'Active',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rule_execution_logs (
    execution_id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    entity_type TEXT DEFAULT 'Complaint',
    entity_id TEXT,
    result TEXT NOT NULL,
    execution_time_ms INTEGER DEFAULT 12,
    executed_at TEXT NOT NULL,
    FOREIGN KEY (rule_id) REFERENCES business_rules(rule_id)
);

CREATE TABLE IF NOT EXISTS rule_simulations (
    simulation_id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    input_payload TEXT NOT NULL,
    predicted_result TEXT NOT NULL,
    executed_by TEXT NOT NULL,
    executed_at TEXT NOT NULL,
    FOREIGN KEY (rule_id) REFERENCES business_rules(rule_id)
);

-- Event Driven Architecture
CREATE TABLE IF NOT EXISTS event_types (
    event_type_id TEXT PRIMARY KEY,
    event_name TEXT NOT NULL UNIQUE,
    event_version TEXT NOT NULL DEFAULT 'v1.0',
    description TEXT,
    category TEXT NOT NULL DEFAULT 'Business',
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

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
);

CREATE TABLE IF NOT EXISTS event_subscriptions (
    subscription_id TEXT PRIMARY KEY,
    event_type_id TEXT NOT NULL,
    subscriber_name TEXT NOT NULL,
    handler_name TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    retry_policy TEXT NOT NULL DEFAULT 'Linear-3x',
    created_at TEXT NOT NULL,
    FOREIGN KEY (event_type_id) REFERENCES event_types(event_type_id)
);

CREATE TABLE IF NOT EXISTS dead_letter_queue (
    dlq_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    failure_reason TEXT NOT NULL,
    failed_at TEXT NOT NULL,
    resolved INTEGER NOT NULL DEFAULT 0,
    resolved_at TEXT,
    resolved_by TEXT,
    FOREIGN KEY (event_id) REFERENCES event_log(event_id)
);

CREATE TABLE IF NOT EXISTS event_replay_history (
    replay_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    replayed_by TEXT NOT NULL,
    replayed_at TEXT NOT NULL,
    result TEXT NOT NULL,
    FOREIGN KEY (event_id) REFERENCES event_log(event_id)
);

-- Integration Connectors
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
);

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
);

CREATE TABLE IF NOT EXISTS integration_mappings (
    mapping_id TEXT PRIMARY KEY,
    connector_id TEXT NOT NULL,
    source_field TEXT NOT NULL,
    target_field TEXT NOT NULL,
    transformation_rule TEXT DEFAULT 'Uppercase',
    created_at TEXT NOT NULL,
    FOREIGN KEY (connector_id) REFERENCES integration_connectors(connector_id)
);

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
);

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
);

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
);

-- Data Governance & Compliance
CREATE TABLE IF NOT EXISTS data_classifications (
    classification_id TEXT PRIMARY KEY,
    classification_name TEXT NOT NULL UNIQUE,
    description TEXT,
    sensitivity_level TEXT NOT NULL DEFAULT 'Confidential',
    created_at TEXT NOT NULL
);

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
);

CREATE TABLE IF NOT EXISTS consent_records (
    consent_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    consent_type TEXT NOT NULL DEFAULT 'Marketing',
    granted INTEGER NOT NULL DEFAULT 1,
    granted_at TEXT NOT NULL,
    withdrawn_at TEXT,
    version TEXT DEFAULT 'v1.0'
);

CREATE TABLE IF NOT EXISTS privacy_requests (
    request_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    request_type TEXT NOT NULL DEFAULT 'DataExport',
    status TEXT NOT NULL DEFAULT 'Pending',
    submitted_at TEXT NOT NULL,
    processed_at TEXT,
    processed_by TEXT,
    remarks TEXT
);

CREATE TABLE IF NOT EXISTS legal_holds (
    hold_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL DEFAULT 'Complaint',
    entity_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS masking_rules (
    rule_id TEXT PRIMARY KEY,
    field_name TEXT NOT NULL,
    masking_type TEXT NOT NULL DEFAULT 'Partial',
    roles_allowed TEXT DEFAULT 'administrator,app_manager',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS governance_reports (
    report_id TEXT PRIMARY KEY,
    report_type TEXT NOT NULL DEFAULT 'GDPR Audit Report',
    generated_by TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    storage_location TEXT
);

-- Activity Analytics
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
);

CREATE TABLE IF NOT EXISTS module_usage_statistics (
    usage_id TEXT PRIMARY KEY,
    module_name TEXT NOT NULL,
    date TEXT NOT NULL,
    active_users INTEGER DEFAULT 120,
    requests_count INTEGER DEFAULT 1450,
    average_response_time_ms INTEGER DEFAULT 24,
    errors_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_activity_summary (
    summary_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    login_count INTEGER DEFAULT 12,
    actions_performed INTEGER DEFAULT 45,
    average_session_duration TEXT DEFAULT '24 mins',
    last_active TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activity_timelines (
    timeline_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    activity_id TEXT NOT NULL,
    sequence_number INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (activity_id) REFERENCES activity_events(activity_id)
);

CREATE TABLE IF NOT EXISTS operational_kpis (
    kpi_id TEXT PRIMARY KEY,
    kpi_name TEXT NOT NULL UNIQUE,
    current_value REAL NOT NULL,
    target_value REAL NOT NULL,
    unit TEXT DEFAULT '%',
    last_updated TEXT NOT NULL
);

-- Advanced Scoped Configuration
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
);

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
);

CREATE TABLE IF NOT EXISTS configuration_templates (
    template_id TEXT PRIMARY KEY,
    template_name TEXT NOT NULL UNIQUE,
    description TEXT,
    configuration_json TEXT NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS configuration_dependencies (
    dependency_id TEXT PRIMARY KEY,
    parent_config TEXT NOT NULL,
    child_config TEXT NOT NULL,
    dependency_type TEXT DEFAULT 'Requires',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runtime_cache (
    cache_id TEXT PRIMARY KEY,
    config_key TEXT NOT NULL,
    scope TEXT NOT NULL,
    cached_value TEXT NOT NULL,
    last_refreshed TEXT NOT NULL,
    expires_at TEXT
);

-- Disaster Recovery Plans
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
);

CREATE TABLE IF NOT EXISTS restore_points (
    restore_point_id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    backup_reference TEXT NOT NULL,
    created_at TEXT NOT NULL,
    storage_location TEXT NOT NULL,
    verified INTEGER DEFAULT 0,
    checksum TEXT NOT NULL,
    FOREIGN KEY (plan_id) REFERENCES recovery_plans(plan_id)
);

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
);

CREATE TABLE IF NOT EXISTS failover_targets (
    target_id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    environment TEXT NOT NULL DEFAULT 'Secondary DC',
    endpoint TEXT NOT NULL,
    priority INTEGER DEFAULT 1,
    health_status TEXT DEFAULT 'Healthy',
    last_checked TEXT NOT NULL,
    FOREIGN KEY (plan_id) REFERENCES recovery_plans(plan_id)
);

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
);

CREATE TABLE IF NOT EXISTS continuity_procedures (
    procedure_id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL,
    step_order INTEGER DEFAULT 1,
    title TEXT NOT NULL,
    instructions TEXT NOT NULL,
    mandatory INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    FOREIGN KEY (plan_id) REFERENCES recovery_plans(plan_id)
);

-- Deployment & Release Pipelines
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
);

CREATE TABLE IF NOT EXISTS deployment_pipelines (
    pipeline_id TEXT PRIMARY KEY,
    pipeline_name TEXT NOT NULL UNIQUE,
    environment TEXT NOT NULL DEFAULT 'Production',
    deployment_strategy TEXT NOT NULL DEFAULT 'Rolling',
    status TEXT NOT NULL DEFAULT 'Active',
    created_at TEXT NOT NULL
);

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
);

CREATE TABLE IF NOT EXISTS environments (
    environment_id TEXT PRIMARY KEY,
    environment_name TEXT NOT NULL UNIQUE,
    environment_type TEXT NOT NULL DEFAULT 'Production',
    endpoint TEXT NOT NULL,
    health_status TEXT DEFAULT 'Healthy',
    current_version TEXT DEFAULT 'v2.4.0'
);

CREATE TABLE IF NOT EXISTS rollback_plans (
    rollback_id TEXT PRIMARY KEY,
    release_id TEXT NOT NULL,
    rollback_version TEXT NOT NULL,
    rollback_strategy TEXT DEFAULT 'Immediate Rollback',
    created_at TEXT NOT NULL,
    FOREIGN KEY (release_id) REFERENCES release_versions(release_id)
);

CREATE TABLE IF NOT EXISTS release_notes (
    note_id TEXT PRIMARY KEY,
    release_id TEXT NOT NULL,
    category TEXT DEFAULT 'Feature',
    description TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (release_id) REFERENCES release_versions(release_id)
);

-- Plugins & Extension Marketplace
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
);

CREATE TABLE IF NOT EXISTS plugin_versions (
    version_id TEXT PRIMARY KEY,
    plugin_id TEXT NOT NULL,
    version TEXT NOT NULL,
    minimum_platform_version TEXT DEFAULT 'v2.0.0',
    maximum_platform_version TEXT DEFAULT 'v3.0.0',
    release_notes TEXT,
    published_at TEXT NOT NULL,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id)
);

CREATE TABLE IF NOT EXISTS plugin_dependencies (
    dependency_id TEXT PRIMARY KEY,
    plugin_id TEXT NOT NULL,
    depends_on_plugin TEXT NOT NULL,
    minimum_version TEXT DEFAULT 'v1.0.0',
    required INTEGER DEFAULT 1,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id)
);

CREATE TABLE IF NOT EXISTS plugin_permissions (
    permission_id TEXT PRIMARY KEY,
    plugin_id TEXT NOT NULL,
    permission_name TEXT NOT NULL,
    resource TEXT NOT NULL,
    access_level TEXT DEFAULT 'ReadWrite',
    created_at TEXT NOT NULL,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id)
);

CREATE TABLE IF NOT EXISTS installed_extensions (
    extension_id TEXT PRIMARY KEY,
    plugin_id TEXT NOT NULL,
    installation_scope TEXT DEFAULT 'Global',
    enabled INTEGER DEFAULT 1,
    installed_by TEXT NOT NULL,
    installed_at TEXT NOT NULL,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id)
);

CREATE TABLE IF NOT EXISTS marketplace_packages (
    package_id TEXT PRIMARY KEY,
    plugin_name TEXT NOT NULL UNIQUE,
    provider TEXT NOT NULL,
    latest_version TEXT NOT NULL,
    download_reference TEXT NOT NULL,
    verified INTEGER DEFAULT 1,
    published_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plugin_usage_statistics (
    usage_id TEXT PRIMARY KEY,
    plugin_id TEXT NOT NULL,
    active_users INTEGER DEFAULT 140,
    requests INTEGER DEFAULT 2100,
    errors INTEGER DEFAULT 0,
    average_response_time_ms INTEGER DEFAULT 14,
    created_at TEXT NOT NULL,
    FOREIGN KEY (plugin_id) REFERENCES plugins(plugin_id)
);

CREATE TABLE IF NOT EXISTS deprecated_schema_objects (
    object_name TEXT PRIMARY KEY,
    replacement TEXT NOT NULL,
    deprecated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Speculative Multi-Organization Scaffolding
CREATE TABLE IF NOT EXISTS organizations (
    organization_id TEXT PRIMARY KEY,
    organization_name TEXT NOT NULL UNIQUE,
    organization_type TEXT NOT NULL DEFAULT 'University',
    status TEXT NOT NULL DEFAULT 'Active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

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
);

CREATE TABLE IF NOT EXISTS user_affiliations (
    affiliation_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    organization_unit TEXT NOT NULL,
    role TEXT NOT NULL,
    effective_from TEXT NOT NULL,
    effective_until TEXT,
    active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS academic_calendar (
    calendar_id TEXT PRIMARY KEY,
    campus_id TEXT NOT NULL,
    event_name TEXT NOT NULL,
    event_type TEXT NOT NULL DEFAULT 'Event',
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

# List of unused tables defined in the legacy scaffold
LEGACY_TABLE_NAMES = [
    "resources",
    "resource_schedules",
    "resource_bookings",
    "visitors",
    "visitor_requests",
    "visitor_locations",
    "visitor_documents",
    "visitor_gate_pass",
    "visitor_checkins",
    "visitor_blacklist",
    "work_orders",
    "work_order_assignments",
    "work_order_notes",
    "work_order_images",
    "work_order_parts",
    "work_order_time_logs",
    "work_order_costs",
    "asset_categories",
    "asset_suppliers",
    "assets",
    "asset_assignments",
    "asset_transfers",
    "asset_maintenance",
    "asset_disposals",
    "scheduled_jobs",
    "job_queue",
    "job_history",
    "workers",
    "job_retry_policy",
    "dashboard_layouts",
    "dashboard_widgets",
    "favorite_modules",
    "dashboard_preferences",
    "quick_actions",
    "api_keys",
    "oauth_clients",
    "webhook_endpoints",
    "api_usage_logs",
    "integration_registry",
    "user_sessions",
    "password_resets",
    "trusted_devices",
    "login_history",
    "security_alerts",
    "password_policy",
    "mfa_settings",
    "ip_access_rules",
    "system_services",
    "health_metrics",
    "incident_logs",
    "monitoring_rules",
    "uptime_history",
    "system_configuration",
    "feature_flags",
    "configuration_history",
    "maintenance_windows",
    "media_files",
    "media_versions",
    "storage_providers",
    "storage_quotas",
    "virus_scan_logs",
    "shared_media_links",
    "mobile_devices",
    "mobile_sessions",
    "push_notifications",
    "offline_sync_queue",
    "supported_app_versions",
    "ai_models",
    "ai_requests",
    "ai_predictions",
    "ai_prompts",
    "ai_feedback",
    "workflow_definitions",
    "workflow_steps",
    "workflow_instances",
    "workflow_tasks",
    "workflow_history",
    "business_rules",
    "rule_conditions",
    "rule_actions",
    "decision_tables",
    "rule_execution_logs",
    "rule_simulations",
    "event_types",
    "event_log",
    "event_subscriptions",
    "dead_letter_queue",
    "event_replay_history",
    "integration_connectors",
    "integration_jobs",
    "integration_mappings",
    "integration_logs",
    "integration_errors",
    "synchronization_history",
    "data_classifications",
    "retention_policies",
    "consent_records",
    "privacy_requests",
    "legal_holds",
    "masking_rules",
    "governance_reports",
    "activity_events",
    "module_usage_statistics",
    "user_activity_summary",
    "activity_timelines",
    "operational_kpis",
    "configuration_keys",
    "configuration_values",
    "configuration_templates",
    "configuration_dependencies",
    "runtime_cache",
    "recovery_plans",
    "restore_points",
    "recovery_drills",
    "failover_targets",
    "recovery_history",
    "continuity_procedures",
    "release_versions",
    "deployment_pipelines",
    "deployment_history",
    "environments",
    "rollback_plans",
    "release_notes",
    "plugins",
    "plugin_versions",
    "plugin_dependencies",
    "plugin_permissions",
    "installed_extensions",
    "marketplace_packages",
    "plugin_usage_statistics",
    "deprecated_schema_objects",
    "organizations",
    "organization_units",
    "user_affiliations",
    "academic_calendar",
]


def apply_legacy_scaffold(db_path: str) -> None:
    """Optionally apply the speculative legacy schema to a database."""
    with sqlite3.connect(db_path) as conn:
        conn.executescript(LEGACY_SCAFFOLD_DDL)
        conn.commit()
    print(f"Applied legacy scaffold DDL to {db_path}.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Apply legacy scaffold schema DDL to target DB.")
    parser.add_argument("--db", default="storage/campus_pulse.db", help="Path to database file")
    args = parser.parse_args()
    apply_legacy_scaffold(args.db)
