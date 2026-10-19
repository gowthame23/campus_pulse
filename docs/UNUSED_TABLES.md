# Campus Pulse — Unused Legacy & Speculative Schema Tables

## 1. Executive Summary

During initial design and architectural prototyping, a large collection of speculative enterprise tables (~135 tables) was authored into SQLite schema initialization. These tables covered hypothetical future features—such as industrial work order tracking, visitor gate passes, IoT campus facilities booking, BPMN workflow diagram engines, ERP integration connectors, and multi-tenant organization trees.

In the actual **Campus Pulse** core product runtime, complaint tracking, student verification, SLA escalation, lost & found, announcements, audit logging, and role-based access control operate entirely within a focused set of ~39 core tables. The speculative enterprise tables remained unpopulated, without frontend screens or operational backend routes.

---

## 2. Active Schema vs. Legacy Scaffold

### 2.1 Active Core Tables (Used in Production Runtime)

The following tables constitute the true Campus Pulse relational data model:

| Category | Active Tables | Purpose |
| :--- | :--- | :--- |
| **Authentication & Users** | `users`, `user_sessions`, `student_profiles`, `staff_profiles`, `user_activities`, `activation_tokens`, `academic_programs`, `push_subscriptions`, `login_rate_limits`, `login_attempts` | User identity, session token SHA-256 hashes, multi-role profile details, Web Push subscriptions, and brute-force protection. |
| **Organizational Hierarchy** | `departments`, `complaint_categories`, `coordinator_assignments`, `locations`, `location_types`, `campuses`, `buildings`, `hostels`, `blocks`, `floors`, `rooms` | Campus routing tree, physical location mapping, department SLA definitions, and coordinator team assignments. |
| **Complaint Lifecycle** | `complaints`, `affected_students`, `comments`, `attachments` | Full ticket lifecycle from submission, routing, accept queue, work progress, warden verification, student closure, and dispute review. |
| **Safety Reports** | `safety_reports`, `safety_report_identity` | Anonymous safety reports with isolated student identity storage accessible only via Admin step-up password verification. |
| **Audit & Governance** | `audit_logs`, `system_settings`, `setting_audit_logs`, `master_references`, `institutions`, `support_tickets`, `scheduler_lock` | Append-only audit trails, configurable SLAs/settings, scheduler multi-worker lease locks, institution metadata, and platform support. |
| **Communications & Alerts** | `notifications`, `chat_messages`, `highlights`, `announcements`, `announcement_targets`, `announcement_attachments`, `announcement_reads`, `announcement_acknowledgements` | In-app alerts, real-time WebSocket chat, bulletin board announcements, and read receipts. |
| **Community Features** | `lost_found_items`, `lost_found_images`, `ownership_claims` | Campus lost and found registry, claims management, and item verification. |
| **Reports, Search & Backups**| `feedback`, `reports`, `report_templates`, `scheduled_reports`, `report_downloads`, `documents`, `document_versions`, `search_index`, `search_history`, `saved_searches`, `backups`, `backup_schedules`, `backup_files`, `restore_history` | Historical reporting, full-text index cache, feedback forms, and database backup management. |

---

## 3. Inventory of Unused Legacy Scaffold Tables (135 Tables)

The following 135 tables are speculative scaffolding and are **not** part of the active Campus Pulse product:

### 3.1 Facility & Visitor Management (10 Tables)
- `resources`, `resource_schedules`, `resource_bookings`: Sports facility/hall booking prototype.
- `visitors`, `visitor_requests`, `visitor_locations`, `visitor_documents`, `visitor_gate_pass`, `visitor_checkins`, `visitor_blacklist`: Campus security gate visitor pass prototype.

### 3.2 Maintenance & Assets (14 Tables)
- `work_orders`, `work_order_assignments`, `work_order_notes`, `work_order_images`, `work_order_parts`, `work_order_time_logs`, `work_order_costs`: Technician labor and parts tracking.
- `asset_categories`, `asset_suppliers`, `assets`, `asset_assignments`, `asset_transfers`, `asset_maintenance`, `asset_disposals`: University physical asset inventory and depreciation.

### 3.3 Engine & Queue Management (5 Tables)
- `scheduled_jobs`, `job_queue`, `job_history`, `workers`, `job_retry_policy`: Distributed worker job execution framework.

### 3.4 Customization & Portals (5 Tables)
- `dashboard_layouts`, `dashboard_widgets`, `favorite_modules`, `dashboard_preferences`, `quick_actions`: Grid-drag widget dashboard layouts.

### 3.5 API Gateway & Integrations (10 Tables)
- `api_keys`, `oauth_clients`, `webhook_endpoints`, `api_usage_logs`, `integration_registry`: Developer third-party API gateway.
- `integration_connectors`, `integration_jobs`, `integration_mappings`, `integration_logs`, `integration_errors`: University ERP ETL connectors.

### 3.6 Advanced Device & Security Tracking (10 Tables)
- `password_resets`, `trusted_devices`, `login_history`, `security_alerts`, `password_policy`, `mfa_settings`, `ip_access_rules`: Speculative hardware token and IP firewall tables.

### 3.7 Platform Health & Media (11 Tables)
- `system_services`, `health_metrics`, `incident_logs`, `monitoring_rules`, `uptime_history`: Infrastructure monitoring agent logs.
- `media_files`, `media_versions`, `storage_providers`, `storage_quotas`, `virus_scan_logs`, `shared_media_links`: Dedicated media object store tables.

### 3.8 Mobile App Support (5 Tables)
- `mobile_devices`, `mobile_sessions`, `push_notifications`, `offline_sync_queue`, `supported_app_versions`: Legacy mobile binary synchronization (superseded by modern PWA Web Push).

### 3.9 Speculative AI & NLP (5 Tables)
- `ai_models`, `ai_requests`, `ai_predictions`, `ai_prompts`, `ai_feedback`: Machine learning model serving scaffold (Campus Pulse uses deterministic keyword classification).

### 3.10 BPMN Workflow & Rules Engines (11 Tables)
- `workflow_definitions`, `workflow_steps`, `workflow_instances`, `workflow_tasks`, `workflow_history`: Flowchart state machine engine.
- `business_rules`, `rule_conditions`, `rule_actions`, `decision_tables`, `rule_execution_logs`, `rule_simulations`: Drools-like rule evaluation engine.

### 3.11 Event-Driven Architecture (5 Tables)
- `event_types`, `event_log`, `event_subscriptions`, `dead_letter_queue`, `event_replay_history`: Event bus / Kafka-style replay queue.

### 3.12 Compliance & Governance (7 Tables)
- `data_classifications`, `retention_policies`, `consent_records`, `privacy_requests`, `legal_holds`, `masking_rules`, `governance_reports`: GDPR data governance and masking policies.

### 3.13 Activity Logs & Scoped Configuration (10 Tables)
- `activity_events`, `module_usage_statistics`, `user_activity_summary`, `activity_timelines`, `operational_kpis`: User mouse click tracking.
- `configuration_keys`, `configuration_values`, `configuration_templates`, `configuration_dependencies`, `runtime_cache`: Hierarchical configuration inheritance.

### 3.14 Disaster Recovery & Pipelines (12 Tables)
- `recovery_plans`, `restore_points`, `recovery_drills`, `failover_targets`, `recovery_history`, `continuity_procedures`: Multi-datacenter failover plans.
- `release_versions`, `deployment_pipelines`, `deployment_history`, `environments`, `rollback_plans`, `release_notes`: Blue/green deployment pipelines.

### 3.15 Plugins & Multi-Organization (14 Tables)
- `plugins`, `plugin_versions`, `plugin_dependencies`, `plugin_permissions`, `installed_extensions`, `marketplace_packages`, `plugin_usage_statistics`: Extension store.
- `deprecated_schema_objects`: Migration compatibility registry.
- `organizations`, `organization_units`, `user_affiliations`, `academic_calendar`: Multi-university consortium nesting.

---

## 4. Architectural Handling & Migration

1. **Clean Initialization**: `SQLiteRepository._initialize_schema()` initializes **only** the active ~39 production tables. Fresh databases never instantiate the 135 unused tables.
2. **Archived DDL**: All unused DDL statements are maintained in [`Backend/scripts/legacy_scaffold_schema.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/scripts/legacy_scaffold_schema.py) for architectural reference or optional testing.
3. **Safe Cleanup Script**: Existing databases can be cleanly purged of all 135 unused tables using the provided cleanup script:
   ```bash
   python Backend/scripts/drop_unused_tables.py --confirm
   ```
   The script:
   - Aborts safely without `--confirm`.
   - Creates an automatic, timestamped backup copy (`campus_pulse_pre_drop_YYYYMMDD_HHMMSS.db`) before performing drops.
   - Preserves all 39 active core tables.
   - Runs `VACUUM` to reclaim disk space.
