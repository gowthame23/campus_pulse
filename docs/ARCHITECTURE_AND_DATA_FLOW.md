# Campus Pulse — Complete Application Architecture & End-to-End Data Flow

> **Document Type:** Core Architectural Specification & Functional Flow Analysis  
> **Status:** Verified against Source Code  
> **Repository:** Campus Pulse (`CampusPulse_co`)  

---

## 1. System Overview & The 20 Architectural Layers

The Campus Pulse architecture is organized into twenty distinct layers spanning the browser client, network perimeter, application server, business logic, asynchronous services, and storage persistence.

```mermaid
graph TD
    subgraph Client ["Client Tier (Browser)"]
        L1[Layer 1: Browser DOM & React 19 UI]
        L2[Layer 2: React Router v7 Routing]
        L3[Layer 3: UI Components & Layout Shells]
        L4[Layer 4: State Management & AuthContext]
        L5[Layer 5: Axios API Client & Interceptors]
    end

    subgraph Perimeter ["Network & Gateway Tier"]
        L6[Layer 6: ASGI Application & Lifespan]
        L7[Layer 7: Middleware Pipeline (CORS, RateLimiter, SecurityHeaders)]
        L8[Layer 8: Security & RBAC Dependencies]
    end

    subgraph Core ["Application Core Tier"]
        L9[Layer 9: API Routers (24 Modules)]
        L10[Layer 10: Pydantic Validation & DTO Schemas]
        L11[Layer 11: Business Logic & Service Singletons]
        L12[Layer 12: Data Access & SQL Parameterization]
        L13[Layer 13: Relational Entities & Models]
    end

    subgraph Services ["Background & Shared Services"]
        L14[Layer 14: Local File Attachment Store]
        L15[Layer 15: In-App Notification Engine]
        L16[Layer 16: Background Scheduler & SLA Escalation]
        L17[Layer 17: WebSocket Connection Pool]
        L18[Layer 18: SMTP Email Transport (smtplib)]
        L19[Layer 19: Logging, Auditing & Exception Handlers]
        L20[Layer 20: Test Suites & Deployment Harnesses]
    end

    L1 --> L2 --> L3 --> L4 --> L5
    L5 -- "HTTP / REST & WebSockets" --> L6
    L6 --> L7 --> L8 --> L9 --> L10 --> L11
    L11 --> L12 --> L13
    L11 --> L14
    L11 --> L15
    L11 --> L18
    L11 --> L19
    L6 --> L16
    L6 --> L17
```

---

### Detailed Analysis of the 20 Verified Layers

#### Layer 1: Browser DOM & User Interface
- **Responsibility:** Renders interactive HTML/CSS elements to the student or staff user.
- **Entry Point:** [`Frontend/index.html`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/index.html) mounting `Frontend/src/main.jsx`.
- **Implementation:** React 19 root (`createRoot(document.getElementById('root'))`).
- **Dependencies:** React DOM, Tailwind CSS utility classes.

#### Layer 2: Frontend Routing
- **Responsibility:** Maps browser URLs to view components; performs client-side route protection.
- **Entry Point:** [`Frontend/src/routes/AppRoutes.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/routes/AppRoutes.jsx).
- **Implementation:** React Router DOM v7 (`<BrowserRouter>`, `<Routes>`, `<Route>`).
- **Route Guarding:** [`Frontend/src/routes/ProtectedRoute.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/routes/ProtectedRoute.jsx) checks `isAuthenticated` and user role permissions, redirecting unauthorized users to `/login` or `/403`.

#### Layer 3: UI Components and Layouts
- **Responsibility:** Reusable UI controls and persistent page shells.
- **Components:** Button, Card, Input, Modal, Table, Toast, PageHeader, StatCard, Badge, EmptyState.
- **Layouts:** [`Frontend/src/layouts/Sidebar.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/layouts/Sidebar.jsx) renders dynamic, role-scoped navigation menus; [`Frontend/src/layouts/Navbar.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/layouts/Navbar.jsx) renders unread notifications indicator and user avatar menu.

#### Layer 4: Frontend State and Context
- **Responsibility:** Centralized user authentication state and session lifecycle.
- **Implementation:** [`Frontend/src/context/AuthContext.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/context/AuthContext.jsx).
- **Behavior:** Persists session token in `localStorage`, verifies token on boot via `/auth/me`, and provides `login()`, `logout()`, `user`, and `isAuthenticated` across the component tree.

#### Layer 5: API Client and Request Configuration
- **Responsibility:** Centralized HTTP transport with request and response interceptors.
- **Implementation:** [`Frontend/src/api/axios.js`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/api/axios.js).
- **Behavior:** Base URL set to `/api` or `http://127.0.0.1:8000`. Injects `Authorization: Bearer <token>` automatically on every outbound request. Listens for 401 Unauthorized responses to trigger automatic session cleanup.

#### Layer 6: Backend Application Initialization
- **Responsibility:** ASGI application bootstrapping, lifespan event management, and router registration.
- **Implementation:** [`Backend/api/main.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/main.py).
- **Lifespan Hook:** Starts the `BackgroundScheduler` and initializes the WebSocket event loop upon startup; halts the scheduler gracefully upon shutdown.

#### Layer 7: Middleware Pipeline
- **Responsibility:** Security controls executed on every inbound HTTP request:
  1. `CORSMiddleware`: Whitelists permitted origins (`http://127.0.0.1:5173`, `http://localhost:5173`), handles preflight `OPTIONS` requests.
  2. `security_headers_middleware`: Injects `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1`, and conditional HSTS.
  3. `rate_limit_middleware`: Enforces IP-based sliding window rate limits on sensitive endpoints (`/auth/login`, `/auth/forgot-password`).
  4. `log_request_middleware`: Captures user ID, role, HTTP method, route, status code, and millisecond execution latency.

#### Layer 8: Authentication and Authorization Dependencies
- **Responsibility:** Extracts session credentials, validates tokens, and enforces RBAC guards before endpoint execution.
- **Implementation:** [`Backend/api/security.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/security.py).
- **Core Functions:** `get_current_user`, `require_roles(*roles)`, `require_super_admin()`.

#### Layer 9: API Routers and Endpoints
- **Responsibility:** Exposes RESTful resources grouped by domain.
- **Registered Routers (24):** `auth`, `users`, `departments`, `locations`, `issues`, `complaints`, `public_complaints`, `dashboard`, `notifications`, `settings`, `attachments`, `analytics`, `audit`, `lost_found`, `announcements`, `feedback`, `reports`, `search`, `backups`, `chat`, `supervisor`, `master`, `programs`, `platform`.

#### Layer 10: Request Validation and Response Schemas
- **Responsibility:** Serialization, schema validation, and constraint checking.
- **Implementation:** Pydantic `BaseModel` classes across all routers (e.g., `ComplaintCreateRequest`, `AnnouncementCreateRequest`). Rejects malformed requests with `422 Unprocessable Entity` or `400 Bad Request`.

#### Layer 11: Service Layer and Business Rules
- **Responsibility:** Encapsulates domain logic, workflow state machines, and business policies.
- **Implementation:** 26 service modules in `Backend/services/` (e.g., [`ComplaintService`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/complaint_service.py), [`AuthService`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/auth_service.py)). Manages multi-table operations and routing algorithms.

#### Layer 12: Data Access and Repository Layer
- **Responsibility:** Manages SQLite database connection lifecycles, runs parameterized queries, and controls transaction boundaries.
- **Implementation:** Helper methods `_connect()` in services using Python `sqlite3` context managers with `conn.row_factory = sqlite3.Row`.

#### Layer 13: Database Models and Entities
- **Responsibility:** Data structures representing domain models.
- **Implementation:** Class definitions in `Backend/models/` (`User`, `Student`, `Coordinator`, `Complaint`, `Location`, `Department`, `AppManager`, `LocationInCharge`, `Administrator`).

#### Layer 14: File and Attachment Storage
- **Responsibility:** Validates, stores, and serves user-uploaded evidence images and document attachments.
- **Implementation:** [`Backend/services/attachment_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/attachment_service.py) writes files to `Backend/storage/attachments/` with sanitised filenames and UUID prefixes; serves files via streaming endpoints.

#### Layer 15: Notification Engine
- **Responsibility:** Dispatches in-app alerts to users based on role, location assignment, and complaint ownership.
- **Implementation:** [`Backend/services/notification_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/notification_service.py) writes notification records to the `notifications` table and triggers WebSocket broadcast.

#### Layer 16: Background Jobs and Schedulers
- **Responsibility:** Executes periodic cron tasks without blocking HTTP workers.
- **Implementation:** [`Backend/services/scheduler_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/scheduler_service.py).
- **Concurrency & Lease Locking (Remediation F-14):** Utilizes `scheduler_lock` with dedicated `lock_name` and TTL lease management to prevent multi-worker concurrency collisions; all database connections are strictly guarded with `finally: conn.close()` to eliminate SQLite resource leaks.
- **Tasks:** Runs every 300 seconds (5 minutes):
  1. *Auto-Close & SLA Escalation:* Auto-closes resolved complaints after the verification window; escalates overdue complaints.
  2. *Cleanup Expired Records:* Purges expired sessions and verification tokens.
  3. *Automatic Work Routing & Reassignment:* Re-evaluates unassigned tickets and applies business rules with selective `save_complaint` updates (Remediation F-08).

#### Layer 17: WebSocket Connections
- **Responsibility:** Bi-directional real-time communication for instant notifications and chat messages.
- **Implementation:** [`Backend/utils/websocket_manager.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/utils/websocket_manager.py). Manages active client socket connections indexed by `user_id`.
- **Heartbeat & Auth Security (Remediations F-04 & F-11):**
  - Unauthenticated connections or users with `first_login=True` are rejected at the handshake.
  - Periodic ping/pong heartbeat control frames are explicitly filtered out on the frontend (`AuthContext.jsx`) so they do not trigger spurious notification unread-count refetches.

#### Layer 18: External Email Services (SMTP)
- **Responsibility:** Transmits transactional activation codes and password reset links.
- **Implementation:** [`Backend/utils/email.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/utils/email.py) using Python's standard `smtplib.SMTP` with STARTTLS over port 587.

#### Layer 19: Logging, Audit Trail and Error Monitoring
- **Responsibility:** Centralized structured logging and immutable audit logging.
- **Implementation:** [`Backend/utils/logger.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/utils/logger.py) and [`Backend/services/audit_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/audit_service.py). Logs to stdout and file `Backend/logs/app.log`; records sensitive administrative actions to `audit_logs` table.

#### Layer 20: Tests and Deployment Infrastructure
- **Responsibility:** Verification, packaging, and hosting automation.
- **Implementation:** 31 Pytest suites in `Backend/tests/`, Vitest in `Frontend/src/__tests__/`, `Backend/Dockerfile`, and `docker-compose.yml`.

---

## 2. End-to-End Functional Traces (16 Key Workflows)

Below are detailed step-by-step traces for the primary workflows verified in the Campus Pulse codebase.

---

### Trace 1: Student Login Workflow
1. **User Action:** Student enters email `student@example.com` and password `Student@123` on [`Frontend/src/pages/auth/LoginPage.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/pages/auth/LoginPage.jsx).
2. **Frontend Dispatch:** `LoginPage.jsx` submits form to `authService.login({ username, password })`.
3. **HTTP Transport:** `POST /auth/login` received by [`Backend/api/routers/auth.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/auth.py).
4. **Middleware:** `rate_limit_middleware` records attempt in `login_attempts` table.
5. **Auth Evaluation:** `AuthService.authenticate()` fetches user record from `users` table; runs `verify_password(password, stored_hash, stored_salt)`.
6. **Session Creation:** `create_session(user_id)` generates random 32-byte token, computes SHA-256 hash, and inserts row into `user_sessions`.
7. **API Response:** Returns `200 OK` with JSON `{ access_token: "<token>", user: { ... } }`.
8. **Client Persistence:** `AuthContext.jsx` saves token to `localStorage`, updates React state `user`, and navigates to `/student`.

---

### Trace 2: Account Activation Workflow
1. **User Action:** User navigates to `/activate`, enters activation token (sent via email) and new password.
2. **Frontend Dispatch:** [`Frontend/src/pages/auth/ActivateAccountPage.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/pages/auth/ActivateAccountPage.jsx) calls `authService.activateAccount({ token, password })`.
3. **HTTP Transport:** `POST /auth/activate` received by `Backend/api/routers/auth.py`.
4. **Token Verification:** `AuthService.activate_account()` queries `activation_tokens` table for matching unexpired token.
5. **Password Update:** Generates new salt, hashes password with PBKDF2 (100,000 iterations), updates `users.password_hash`, `users.salt`, and sets `users.status = 'Active'`.
6. **Token Consumption:** Deletes or marks token used in `activation_tokens`.
7. **Response & Redirect:** Returns `200 OK`; user is redirected to `/login` with success banner.

---

### Trace 3: Password Change Workflow
1. **User Action:** Authenticated user navigates to `/change-password`, enters old password and new password.
2. **Frontend Dispatch:** [`Frontend/src/pages/auth/ChangePasswordPage.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/pages/auth/ChangePasswordPage.jsx) calls `authService.changePassword({ old_password, new_password })`.
3. **HTTP Transport:** `POST /auth/change-password` with `Bearer <token>` header.
4. **Security Dependency:** `get_current_user` validates caller identity.
5. **Verification & Mutation:** `AuthService.change_password()` verifies old password; updates `password_hash` and `salt`.
6. **Session Revocation:** Calls `revoke_user_sessions(user_id)` to invalidate all active sessions across other devices.
7. **Response:** Returns `200 OK`; client is prompted to log in again with new credentials.

---

### Trace 4: Password Reset Workflow
1. **User Action:** User enters email on `/forgot-password`.
2. **Frontend Dispatch:** `ForgotPasswordPage.jsx` calls `authService.forgotPassword({ email })`.
3. **Backend Logic:** `POST /auth/forgot-password` generates reset token, stores it in `password_resets`, and dispatches reset URL via `email.py`.
4. **Completion:** User clicks email link, submits new password to `POST /auth/reset-password`, which verifies token expiry and updates password.

---

### Trace 5: Student Account Import (CSV / Excel)
1. **User Action:** Administrator uploads student roster spreadsheet on `/admin/users`.
2. **Frontend Dispatch:** `UserManagementPage.jsx` posts `multipart/form-data` to `userService.importStudents(formData)`.
3. **Backend Processing:** `POST /users/import` receives file. `excel_importer.py` parses rows, validates email formatting, and verifies academic programs.
4. **Database Insertion:** Batch inserts records into `users` (role='student') and `student_profiles` inside a single SQLite transaction.
5. **Activation Trigger:** Generates activation tokens and queues welcome emails.

---

### Trace 6: Complaint Submission Workflow
1. **User Action:** Student selects location (Hostel 1), department (Plumbing), priority (High), enters title and description, and optionally attaches photo on `/complaints/new`.
2. **Frontend Dispatch:** `CreateComplaintPage.jsx` sends payload to `complaintService.create()`.
3. **Backend Handler:** `POST /complaints` validated against `ComplaintCreateRequest`.
4. **Routing Engine:** `ComplaintService.create_complaint()` queries `coordinator_assignments` to locate responsible Coordinator for (Hostel 1, Plumbing).
5. **Persistence:** Inserts record into `complaints` table with status `'Assigned'` (or `'Submitted'` if unassigned).
6. **Side Effects:** Generates notification for assigned Coordinator and confirms receipt to Student.

---

### Trace 7: Complaint Routing & Assignment Workflow
1. **Trigger:** Complaint created or location/department updated.
2. **Evaluation:** `ComplaintService._resolve_assignment(location_id, department_id)`:
   - Queries `coordinator_assignments` matching both `location_id` and `department_id`.
   - If found, sets `assigned_to = coordinator_id` and `status = 'Assigned'`.
   - If no specific Coordinator exists, checks for Location In-Charge (Warden) assigned to that location.
   - If neither exists, routes to App Manager or leaves unassigned with alert to Administrator.
3. **Audit Log:** Records routing decision in `activity_events` / `audit_logs`.

---

### Trace 8: Complaint Resolution & Student Verification
1. **Staff Action:** Coordinator resolves issue, attaches completion proof, sets status to `'Resolved'`, and enters resolution remarks.
2. **State Transition:** Status becomes `'Waiting for Verification'` with a 48-hour SLA verification timer.
3. **Student Notification:** Student receives alert with "Verify Resolution" or "Reopen" buttons.
4. **Verification Action:** Student approves resolution on `/complaints/:id`; status transitions to `'Closed'`.

---

### Trace 9: Complaint Reopening Workflow
1. **User Action:** Student rejects resolution within 48-hour window on `/complaints/:id`, providing rejection reason.
2. **Backend Handler:** `POST /complaints/:id/reopen` checks that caller is complaint author and status is `'Waiting for Verification'`.
3. **State Transition:** Status transitions to `'Reopened'`; increments `reopen_count`.
4. **Escalation Notification:** Alerts Coordinator and Location In-Charge (Warden) that the complaint was not satisfactorily addressed.

---

### Trace 10: In-App Notification Generation & Delivery
1. **Triggering Event:** Status change, new announcement, or complaint comment.
2. **Creation:** `NotificationService.create_notification(user_id, title, message, reference_type, reference_id)`.
3. **Storage:** Inserts row into `notifications` table (`is_read = FALSE`).
4. **Real-time Push:** If user is connected to WebSocket, `ws_manager.send_personal_message()` pushes JSON payload to client instantly.
5. **UI Rendering:** Bell icon in Navbar increments badge count; Toast appears if user is active.

---

### Trace 11: Lost & Found Item Reporting & Image Upload
1. **User Action:** User reports lost item (e.g., calculator) with image attachment on `/lost-found`.
2. **Image Upload:** File is uploaded via `POST /lost-found/upload` to `Backend/storage/attachments/`.
3. **Item Creation:** `POST /lost-found` persists item title, location, category, date, contact info, and image URL in `lost_found_items`.
4. **Feed Display:** Public Lost & Found feed updates dynamically; filters allow querying by category and date.

---

### Trace 12: File Upload and Streaming Retrieval
1. **Upload:** Client sends binary payload to `POST /attachments`.
2. **Validation:** `attachment_service.py` checks file size (max 10MB) and MIME type (PNG, JPEG, PDF).
3. **Sanitization:** Strips directory traversal characters, generates UUID-prefixed filename, and writes to disk.
4. **Retrieval:** `GET /attachments/:attachment_id` streams file content with `Content-Disposition: inline` and verified MIME headers.

---

### Trace 13: User Deactivation and Safe Restoration
1. **Admin Action:** Administrator deactivates user on `/admin/users`.
2. **Backend Logic:** `PUT /users/:id/deactivate` sets `users.status = 'Inactive'`, `users.active = FALSE`.
3. **Security Invalidation:** Revokes all active session tokens in `user_sessions`. Deactivated user is immediately blocked from API calls.
4. **Preservation:** Preserves all historical complaints, comments, and audit trails intact (no destructive deletion).
5. **Restoration:** `PUT /users/:id/activate` safely restores access.

---

### Trace 14: Global Search and Scoped Export
1. **User Action:** Staff types query into `/search` and clicks "Export CSV".
2. **Search Logic:** `GlobalSearchService.search()` performs parameterized SQL text search across complaints, announcements, users, and locations, filtered strictly by caller's role scope.
3. **Export Generation:** `ReportService.export_complaints_csv()` streams CSV format with UTF-8 encoding.

---

### Trace 15: Audit Log Recording
1. **Administrative Event:** User created, location updated, or role reassigned.
2. **Recording:** `AuditService.log_action(action, entity_type, entity_id, actor_id, details)`.
3. **Immutability:** Writes row into `audit_logs` table with timestamp and client IP. No update or delete endpoints exist for audit logs.

---

### Trace 16: Database Backup and Restoration
1. **Admin Action:** Administrator clicks "Create Backup" on `/backups`.
2. **Backend Logic:** `BackupService.create_backup()` creates a point-in-time copy of `campus_pulse.db` in `Backend/storage/backups/` using SQLite Online Backup API.
3. **Metadata Storage:** Records backup size, checksum, and creation timestamp in `backups` table.
4. **Restoration:** `BackupService.restore_backup(backup_id)` verifies file integrity and replaces active database safely.
