# Campus Pulse - Changelog

All notable changes and release milestones for Campus Pulse are documented in this file.

---

## [1.0.0] - 2026-07-18

### 🚀 Initial Production Release (v1.0.0)

#### Added
- **Dynamic SLA Monitoring & Escalation Engine:**
  - Dynamic status indicators: 🟢 **On Time**, 🟡 **Due Today**, 🔴 **Overdue**.
  - Multi-stage escalations notifying Coordinator $\rightarrow$ App Manager $\rightarrow$ Administrator.
- **Audit Log Trail & State Diffs:**
  - Dedicated `/admin/audit` page with search and JSON before/after state diff viewer modal.
- **Database Backup & Recovery:**
  - Full system database JSON snapshot export (`GET /settings/backup`) and restore (`POST /settings/restore`) controls on `DataCleanupPage.jsx`.
- **Data Duplicate Consolidator Tool (`/admin/cleanup`):**
  - Safe duplicate consolidation wizard migrating mapped complaints and users before purging stale records.
- **Enhanced Notifications System:**
  - Mark All as Read, Delete single notification, and Unread filter tabs.
- **Complaint Attachments:**
  - Support photo and document attachment URLs on complaint filing and details pages.
- **Dashboard Summary Stat Cards:**
  - SLA status counters (Pending, Resolved, Overdue) across Student, Coordinator, Manager, and Admin dashboards.
- **Automated Lifecycle Integration Test Suite:**
  - In-memory `TestClient` verification script (`test_lifecycles.py`) verifying user protection rules, coordinator transfers, archiving, and SLA calculations.
- **Full Project Documentation Suite:**
  - `README.md`, `INSTALL.md`, `API_DOCUMENTATION.md`, `DATABASE_SCHEMA.md`, `ARCHITECTURE.md`, `BUG_TRACKER.md`, `CHANGELOG.md`.

#### Fixed
- Fixed authorization 403 issue on department creation by aligning role checks in `security.py`.
- Fixed self-deactivation and self-deletion vulnerabilities on Administrator/Manager accounts.
- Added safeguard preventing deletion of the last active Administrator.
