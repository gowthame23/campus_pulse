# Campus Pulse — Issues, Gaps, and Technical Risks Register

**Document ID:** `CP-DOC-005`  
**Classification:** Evidence-Based Source Code Investigation  
**Status:** Complete  
**Date:** October 2026  

---

## 1. Overview and Methodology

This document details all confirmed technical issues, architectural limitations, security risks, documentation contradictions, and dead code identified during the comprehensive source code audit of the **Campus Pulse** repository (`CampusPulse_co`).

Each issue is assigned a unique tracking identifier, categorized, evaluated for severity, and mapped directly to source code references with reproduction mechanisms and remediation paths.

---

## 2. Issues Summary Matrix

| Issue ID | Severity | Category | Title | Affected File(s) |
| :--- | :--- | :--- | :--- | :--- |
| **ISSUE-001** | High | Concurrency / DB | SQLite Single-Writer Lock Bottleneck | `Backend/database/session.py`, `Backend/storage/campus_pulse.db` |
| **ISSUE-002** | High | Architecture / Concurrency | In-Process Thread Scheduler Multi-Worker Duplication | `Backend/services/scheduler_service.py`, `Backend/main.py` |
| **ISSUE-003** | Medium | Scalability / Realtime | In-Memory WebSocket Manager Lacks Cross-Worker Bus | `Backend/api/routes/websockets.py`, `Backend/services/websocket_service.py` |
| **ISSUE-004** | Medium | Performance | Synchronous SMTP Dispatch Blocking HTTP Request Threads | `Backend/services/email_service.py`, `Backend/api/routes/auth.py` |
| **ISSUE-005** | Medium | Schema Governance | 160+ Enterprise Placeholder Tables (Schema Drift) | `Backend/storage/campus_pulse.db`, `Backend/models/` |
| **ISSUE-006** | Low | Storage / Deployment | Local Disk File Attachment Storage in Stateless Deployments | `Backend/api/routes/attachments.py`, `Backend/storage/uploads/` |
| **ISSUE-007** | High | Doc Contradiction | Documented SMS OTP Flow Non-Existent in Source Code | `Backend/api/routes/auth.py`, Legacy Documentation |
| **ISSUE-008** | Medium | Doc Contradiction | Documented AI Predictive Dispatch Is Scaffolded Only | `Backend/storage/campus_pulse.db` (`ai_predictions`) |
| **ISSUE-009** | Medium | Doc Contradiction | Super Admin Operational Complaint Viewing Blocked | `Backend/api/routes/complaints.py` (`_visible_complaints`) |
| **ISSUE-010** | Low | Workflow Edge Case | Reopen Count Limit Reached Lacks Escalation Alert | `Backend/api/routes/complaints.py`, `Backend/models/complaint.py` |

---

## 3. Detailed Issue Specifications

### ISSUE-001: SQLite Single-Writer Lock Bottleneck
- **Category:** Concurrency / Database Architecture
- **Severity:** High
- **Affected Files:**
  - [`Backend/database/session.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/database/session.py)
  - [`Backend/storage/campus_pulse.db`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/storage/campus_pulse.db)
- **Description & Evidence:**
  The production backend uses SQLite 3 configured with `PRAGMA journal_mode=WAL` and `PRAGMA busy_timeout=5000`. While Write-Ahead Logging allows multiple concurrent readers alongside one active writer, write transactions are strictly serialized at the operating system file lock level. Under burst conditions (e.g., hundreds of students filing complaints following a campus-wide outage), concurrent `POST /complaints`, attachment uploads, and background SLA status updates can hold the write lock longer than 5,000ms, triggering `sqlite3.OperationalError: database is locked`.
- **Reproduction:**
  1. Launch 50 concurrent asynchronous threads submitting complaints via `POST /api/complaints`.
  2. Background scheduler simultaneously executes batch updates on `complaints` for SLA escalation.
  3. Tail requests log `sqlite3.OperationalError` with HTTP 500 status.
- **Impact:** Request timeouts and transaction failures during high-traffic campus incidents.
- **Remediation:** For enterprise deployment beyond pilot scale, migrate the SQLAlchemy engine connection string to PostgreSQL (`postgresql+psycopg2://...`).

---

### ISSUE-002: In-Process Thread Scheduler Multi-Worker Duplication
- **Category:** Background Jobs / Architecture
- **Severity:** High
- **Affected Files:**
  - [`Backend/services/scheduler_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/scheduler_service.py)
  - [`Backend/main.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/main.py)
- **Description & Evidence:**
  In `Backend/main.py`, the SLA checker and auto-close background runner is started in an in-process daemon thread (`scheduler_service.start_scheduler()`) on FastAPI lifespan startup. If Uvicorn or Gunicorn is launched with multiple worker processes (e.g. `uvicorn main:app --workers 4`), each worker process spawns an independent scheduler thread. Every 300 seconds, 4 distinct threads query the same SQLite database for overdue complaints and trigger duplicate notification dispatches and audit log records.
- **Reproduction:**
  1. Start Uvicorn with `--workers 2`.
  2. Seed an overdue complaint past its 48-hour SLA deadline.
  3. Observe notifications table receiving duplicate escalation alerts simultaneously.
- **Impact:** Duplicate emails, notifications, and unnecessary database write lock contention.
- **Remediation:** Move periodic background tasks to a dedicated worker process (Celery or APScheduler running as a standalone single-instance service) or introduce distributed database lock leasing.

---

### ISSUE-003: In-Memory WebSocket Manager Lacks Cross-Worker Bus
- **Category:** Real-Time Messaging / Scalability
- **Severity:** Medium
- **Affected Files:**
  - [`Backend/api/routes/websockets.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routes/websockets.py)
  - [`Backend/services/websocket_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/websocket_service.py)
- **Description & Evidence:**
  The `ConnectionManager` class maintains WebSocket connections inside a Python in-memory dictionary `self.active_connections: Dict[int, List[WebSocket]]`. When a backend route (e.g. complaint status change) invokes `manager.send_personal_message(user_id, data)`, it can only broadcast to connections managed by the current Python process. In a multi-worker or multi-container environment, if Student 1 is connected to Worker A and an update is processed on Worker B, Student 1 will not receive the real-time notification push.
- **Reproduction:**
  1. Connect a WebSocket client to Worker A.
  2. Issue a REST API status update that hits Worker B.
  3. The WebSocket client on Worker A receives no frame until page refresh.
- **Impact:** Inconsistent real-time UI updates in production multi-process clusters.
- **Remediation:** Introduce a Redis pub/sub backplane or ASGI channel layer (`broadcaster` library) to synchronize broadcast events across all worker processes.

---

### ISSUE-004: Synchronous SMTP Dispatch Blocking HTTP Request Threads
- **Category:** Performance / Availability
- **Severity:** Medium
- **Affected Files:**
  - [`Backend/services/email_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/email_service.py)
  - [`Backend/api/routes/auth.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routes/auth.py)
- **Description & Evidence:**
  `email_service.send_email()` establishes a synchronous `smtplib.SMTP` connection, executes TLS negotiation, and transmits messages directly within the HTTP request execution flow (or fast background task). If the external SMTP server has network latency, throttles requests, or times out, the user's HTTP request hangs for 10–30 seconds.
- **Reproduction:**
  1. Configure SMTP host to an unresponsive IP.
  2. Submit `POST /api/auth/register` or `POST /api/auth/request-password-reset`.
  3. The request blocks until socket timeout occurs before returning a response.
- **Impact:** Thread pool exhaustion, degraded UI responsiveness, and potential 504 Gateway Timeouts.
- **Remediation:** Offload email compilation and dispatch to an asynchronous background task queue (Celery, ARQ, or FastAPI `BackgroundTasks` with strict socket timeouts).

---

### ISSUE-005: 160+ Enterprise Placeholder Tables (Schema Drift)
- **Category:** Database Schema Governance
- **Severity:** Medium
- **Affected Files:**
  - [`Backend/storage/campus_pulse.db`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/storage/campus_pulse.db)
  - [`Backend/models/`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/models/)
- **Description & Evidence:**
  The SQLite catalog contains 196 tables. Detailed code analysis confirms that only ~35 tables are actively referenced by SQLAlchemy models, query builders, or API routes. The remaining ~160 tables (e.g. `visitor_logs`, `gate_passes`, `vendor_contracts`, `asset_inventories`, `ai_predictions`) are dormant artifacts from an expanded schema script. They possess foreign key constraints and indexes that consume schema catalog memory and mislead new developers.
- **Reproduction:**
  Run `SELECT tbl_name FROM sqlite_master WHERE type='table'` and cross-reference against `Backend/models/`.
- **Impact:** High cognitive overhead for maintenance developers, risk of accidental dependencies on dead tables, and inflated migration complexity.
- **Remediation:** Archive unused schema definitions into a separate enterprise roadmap migration file or drop unused placeholder tables from operational databases.

---

### ISSUE-006: Local Disk File Attachment Storage in Stateless Deployments
- **Category:** Deployment / Cloud Scalability
- **Severity:** Low
- **Affected Files:**
  - [`Backend/api/routes/attachments.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routes/attachments.py)
  - `Backend/storage/uploads/`
- **Description & Evidence:**
  Complaint attachment uploads are written directly to local disk directory `Backend/storage/uploads/{uuid}.{ext}`. In modern containerized deployments (Docker, Kubernetes, AWS ECS, Google Cloud Run) where container instances are ephemeral and autoscaled, attachments written on one instance cannot be read by another instance and are lost upon container recreation.
- **Reproduction:**
  Deploy two container replicas without shared persistent volumes; uploaded images on container A return HTTP 404 when requested through container B.
- **Impact:** Missing images and attachments in distributed or ephemeral cloud environments.
- **Remediation:** Implement an S3-compatible object storage provider abstraction (AWS S3, Cloudflare R2, MinIO) for attachment storage.

---

### ISSUE-007: Documented SMS OTP Flow Non-Existent in Source Code
- **Category:** Documentation Contradiction
- **Severity:** High
- **Affected Files:**
  - [`Backend/api/routes/auth.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routes/auth.py)
  - Legacy documentation / design specs
- **Description & Evidence:**
  Several historical design summaries claim Campus Pulse uses "6-digit SMS OTP verification" for user activation and two-factor authentication. Inspection of the codebase reveals **no SMS provider integration** (no Twilio, AWS SNS, MSG91, or Fast2SMS libraries). Authentication and password reset rely strictly on 32-byte cryptographic URL tokens stored in `activation_tokens` and dispatched via email (`/activate?token=...`).
- **Impact:** Misleads security auditors and prospective institutional evaluators regarding the system's external communications infrastructure.
- **Remediation:** Update documentation to reflect reality (email token-based activation only) or specify SMS OTP as an unbuilt roadmap item.

---

### ISSUE-008: Documented AI Predictive Dispatch Is Scaffolded Only
- **Category:** Documentation Contradiction / Feature Completeness
- **Severity:** Medium
- **Affected Files:**
  - [`Backend/storage/campus_pulse.db`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/storage/campus_pulse.db) (`ai_predictions` table)
  - `Backend/api/routes/analytics.py`
- **Description & Evidence:**
  Marketing documents and legacy README files state that Campus Pulse incorporates an "AI-driven complaint categorization and predictive maintenance engine". While the database contains a table named `ai_predictions`, there are no machine learning libraries (`torch`, `scikit-learn`, `transformers`) imported in the backend requirements, nor is there any active inference pipeline during complaint creation. Categorization is driven strictly by user selection, keyword heuristics, and explicit department mapping.
- **Impact:** False perception of feature readiness.
- **Remediation:** Reclassify AI features in documentation as "Future Architecture Scaffold" rather than implemented capabilities.

---

### ISSUE-009: Super Admin Operational Complaint Viewing Blocked
- **Category:** Documentation Contradiction / Permission Design
- **Severity:** Medium
- **Affected Files:**
  - [`Backend/api/routes/complaints.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routes/complaints.py) (`_visible_complaints`)
- **Description & Evidence:**
  General administrator documentation typically assumes `super_admin` has god-mode privileges across all data entities. In `complaints.py`, the helper function `_visible_complaints(current_user, db)` contains an explicit security boundary:
  ```python
  if current_user.role == "super_admin":
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="Super Admins cannot access operational complaints."
      )
  ```
  Super administrators are strictly limited to system-level configuration, tenant settings, and audit logs. Only `administrator`, `app_manager`, `location_in_charge`, `coordinator`, and `student` roles can query complaints.
- **Impact:** Administrators logging in under the `super_admin` credential expecting to view complaint queues will encounter HTTP 403 Forbidden errors if unaware of this architectural segregation.
- **Remediation:** Clearly document this role segregation in administrative runbooks.

---

### ISSUE-010: Reopen Count Limit Reached Lacks Escalation Alert
- **Category:** Workflow Edge Case / Business Logic
- **Severity:** Low
- **Affected Files:**
  - [`Backend/api/routes/complaints.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routes/complaints.py)
  - [`Backend/models/complaint.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/models/complaint.py)
- **Description & Evidence:**
  When a student attempts to reopen a complaint, `complaint.reopened_count` is evaluated against a maximum threshold of 3. If `reopened_count >= 3`, the API returns HTTP 400 Bad Request with `"Maximum reopen limit reached"`. However, the system does not automatically flag the complaint as a "Disputed / Stalled" ticket nor does it trigger an automated alert to the App Manager or Administrator indicating that a student remains unsatisfied after 3 resolution attempts.
- **Impact:** Dissatisfied students reach a dead end without automated managerial oversight.
- **Remediation:** Introduce an automatic escalation workflow when `reopened_count >= 3` that notifies the App Manager and flags the complaint for administrative arbitration.

---

## 4. Accepted Limitations (By Design)

1. **SQLite as Single Storage Engine:**
   - Single-file database suitable for small-to-medium campus deployments (< 5,000 active concurrent users).
   - Low operational overhead, zero external database service configuration required for local pilot installations.
2. **Stateful Database Session Management:**
   - Stateful sessions stored in `user_sessions` enable instant single-session revocation, security auditing, and concurrent login limiting, accepting the minor trade-off of one database read per authenticated request.
3. **No Direct Student Announcement Creation:**
   - By policy and security enforcement, students cannot create campus-wide notices. Only authorized staff and administrators can publish official announcements.
4. **48-Hour Auto-Close Window:**
   - Auto-closing complaints 48 hours after reaching `Resolved` if the student takes no action is an intentional mechanism to prevent infinite queue backlogs.
