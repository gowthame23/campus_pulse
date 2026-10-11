# Campus Pulse — REST API Reference, Routing Registry & Security Directory

> **Document Type:** Complete REST API Specification & Endpoint Directory  
> **Repository:** Campus Pulse (`CampusPulse_co`)  
> **Total Registered Routes:** 277 Endpoints across 24 Routers  
> **Base URL:** `http://127.0.0.1:8000` (Direct) or `/api` (Reverse Proxy)  

---

## 1. API Architecture & Standards

- **Protocol:** HTTP/1.1 with TLS (Production); WebSockets on `/ws/{user_id}`
- **Authentication:** `Authorization: Bearer <token>` header containing opaque 32-byte session token
- **Response Format:** `application/json` (REST endpoints); `multipart/form-data` (file uploads)
- **Error Standard:** Standard RFC 7807 JSON error body:
  ```json
  {
    "detail": "Error message description or validation array"
  }
  ```
- **Global Middleware:** Rate limiter, CORS header injector, security headers (`nosniff`, `DENY`, conditional `HSTS`), request timing logger.

---

## 2. API Endpoints Catalog by Module

---

### Module 1: Authentication & Account Management (`/auth`)
*Source Router:* [`Backend/api/routers/auth.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/auth.py)  
*Covered Tests:* [`Backend/tests/test_workflow1_auth.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/tests/test_workflow1_auth.py), [`Backend/tests/smoke_test.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/tests/smoke_test.py)

| Method | Path | Purpose | Required Roles | Auth | Request Body / Params | Database Effects | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| `POST` | `/auth/login` | Authenticates user & issues session token | Public | No | `LoginRequest(username, password)` | Inserts `login_attempts`, inserts `user_sessions` | 200, 401, 403, 429 |
| `POST` | `/auth/logout` | Revokes active session token | Any | Yes | Bearer Token | Deletes token from `user_sessions` | 200, 401 |
| `GET` | `/auth/me` | Fetches authenticated caller profile | Any | Yes | None | Reads `users` & profile table | 200, 401 |
| `POST` | `/auth/change-password` | Updates password & revokes other sessions | Any | Yes | `PasswordChangeRequest(old_password, new_password)` | Updates `users.password_hash`, revokes `user_sessions` | 200, 400, 401 |
| `POST` | `/auth/forgot-password` | Sends password reset email link | Public | No | `ForgotPasswordRequest(email)` | Inserts `password_resets`, sends email | 200, 404 |
| `POST` | `/auth/reset-password` | Resets password via email token | Public | No | `ResetPasswordRequest(token, new_password)` | Updates `users.password_hash`, deletes reset token | 200, 400 |
| `POST` | `/auth/activate` | Activates account via activation token | Public | No | `ActivateAccountRequest(token, password)` | Updates `users.status='Active'`, deletes token | 200, 400 |

---

### Module 2: User & Roster Management (`/users`)
*Source Router:* [`Backend/api/routers/users.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/users.py)  
*Covered Tests:* [`Backend/tests/test_workflow2_user_management.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/tests/test_workflow2_user_management.py)

| Method | Path | Purpose | Required Roles | Auth | Request Body / Params | Database Effects | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| `GET` | `/users` | Lists users with role/status filters | Admin, App Manager | Yes | `?role=&status=&q=&limit=&skip=` | Reads `users` | 200, 401, 403 |
| `POST` | `/users` | Creates single user account | Admin, App Manager | Yes | `UserCreateRequest(...)` | Inserts `users`, `activation_tokens` | 201, 400, 403 |
| `GET` | `/users/{user_id}` | Retrieves full user profile | Admin, Manager, Self | Yes | Path: `user_id` | Reads `users`, `student_profiles` | 200, 404 |
| `PUT` | `/users/{user_id}` | Updates user information | Admin, Manager | Yes | `UserUpdateRequest(...)` | Updates `users`, logs to `audit_logs` | 200, 400, 403 |
| `PUT` | `/users/{user_id}/deactivate`| Deactivates user & revokes sessions | Admin, Manager | Yes | Path: `user_id` | Updates `users.status='Inactive'`, clears `user_sessions` | 200, 403, 404 |
| `PUT` | `/users/{user_id}/activate` | Reactivates inactive account | Admin, Manager | Yes | Path: `user_id` | Updates `users.status='Active'`, `users.active=1` | 200, 403, 404 |
| `DELETE`| `/users/{user_id}` | Soft-deletes user | Admin | Yes | Path: `user_id` | Sets `is_deleted=1` (or cascades if safe) | 200, 403, 404 |
| `POST` | `/users/import` | Bulk imports students from CSV/XLSX | Admin, Manager | Yes | `UploadFile` (multipart) | Batch inserts `users`, `student_profiles` | 200, 400, 403 |

---

### Module 3: Facility & Location Management (`/locations`)
*Source Router:* [`Backend/api/routers/locations.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/locations.py)  
*Covered Tests:* [`Backend/tests/test_role_location_assignment.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/tests/test_role_location_assignment.py)

| Method | Path | Purpose | Required Roles | Auth | Request Body / Params | Database Effects | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| `GET` | `/locations` | Lists campus locations & buildings | Any | Yes | `?type=&status=` | Reads `locations` | 200, 401 |
| `POST` | `/locations` | Creates new campus location | Admin, Manager | Yes | `LocationCreateRequest(...)` | Inserts `locations`, logs `audit_logs` | 201, 400, 403 |
| `GET` | `/locations/{id}` | Gets location details & wardens | Any | Yes | Path: `id` | Reads `locations` | 200, 404 |
| `PUT` | `/locations/{id}` | Updates location assignments | Admin, Manager | Yes | `LocationUpdateRequest(...)` | Updates `locations.app_manager_id`, `warden_id` | 200, 400, 403 |
| `DELETE`| `/locations/{id}` | Deactivates or removes location | Admin | Yes | Path: `id` | Updates `locations.status='Inactive'` | 200, 400, 403 |

---

### Module 4: Department Management (`/departments`)
*Source Router:* [`Backend/api/routers/departments.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/departments.py)

| Method | Path | Purpose | Required Roles | Auth | Request Body / Params | Database Effects | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| `GET` | `/departments` | Lists all service departments | Any | Yes | `?status=` | Reads `departments` | 200, 401 |
| `POST` | `/departments` | Creates service department | Admin, Manager | Yes | `DepartmentCreateRequest(...)` | Inserts `departments` | 201, 400, 403 |
| `GET` | `/departments/{id}` | Gets department details | Any | Yes | Path: `id` | Reads `departments` | 200, 404 |
| `PUT` | `/departments/{id}` | Updates department config | Admin, Manager | Yes | `DepartmentUpdateRequest(...)` | Updates `departments` | 200, 400, 403 |
| `DELETE`| `/departments/{id}` | Deactivates department | Admin | Yes | Path: `id` | Sets `departments.status='Inactive'` | 200, 400, 403 |

---

### Module 5: Complaint Operations (`/complaints`)
*Source Router:* [`Backend/api/routers/complaints.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/complaints.py)  
*Covered Tests:* [`Backend/tests/test_workflow4_complaint_management.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/tests/test_workflow4_complaint_management.py)

| Method | Path | Purpose | Required Roles | Auth | Request Body / Params | Database Effects | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| `GET` | `/complaints` | Lists complaints scoped to caller role | Any | Yes | `?status=&priority=&location_id=&q=` | Reads `complaints` (filtered by `_visible_complaints`) | 200, 401, 403 |
| `POST` | `/complaints` | Lodges new student complaint | Student, Warden | Yes | `ComplaintCreateRequest(...)` | Inserts `complaints`, `notifications` | 201, 400, 403 |
| `GET` | `/complaints/{id}` | Gets full complaint detail & comments | Author, Staff | Yes | Path: `id` | Verified by `_ensure_visible()` | 200, 403, 404 |
| `PUT` | `/complaints/{id}/status` | Updates complaint status | Staff, Admin | Yes | `StatusUpdateRequest(status)` | Updates `complaints.status` | 200, 400, 403 |
| `PUT` | `/complaints/{id}/assign` | Reassigns complaint to coordinator | Admin, Manager, Warden| Yes | `AssignRequest(assigned_to)` | Updates `complaints.assigned_to` | 200, 400, 403 |
| `PUT` | `/complaints/{id}/resolve`| Marks complaint resolved with proof | Coordinator, Staff | Yes | `ResolveRequest(notes, proof_url)` | Updates status to `'Waiting for Verification'` | 200, 400, 403 |
| `PUT` | `/complaints/{id}/verify` | Approves resolution & closes issue | Complainant Student | Yes | `VerifyRequest(rating, comments)` | Updates status to `'Closed'` | 200, 400, 403 |
| `POST` | `/complaints/{id}/reopen` | Reopens unsatisfactory resolution | Complainant Student | Yes | `ReopenRequest(reason)` | Updates status to `'Reopened'`, increments count | 200, 400, 403 |
| `POST` | `/complaints/{id}/comments`| Appends discussion comment | Author, Staff | Yes | `CommentCreateRequest(content)` | Inserts `comments` | 201, 400, 403 |
| `POST` | `/complaints/{id}/upvote` | Upvotes public complaint | Student | Yes | Path: `id` | Inserts `affected_students` | 200, 400 |

---

### Module 6: Campus Announcements & Notices (`/announcements`)
*Source Router:* [`Backend/api/routers/announcements.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/announcements.py)  
*Covered Tests:* [`Backend/tests/test_workflow8_announcements.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/tests/test_workflow8_announcements.py)

| Method | Path | Purpose | Required Roles | Auth | Request Body / Params | Database Effects | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| `GET` | `/announcements` | Fetches active campus circulars | Any | Yes | `?category=&priority=&q=` | Reads `announcements` | 200, 401 |
| `POST` | `/announcements` | Composes & broadcasts notice | **Admin, Manager, Warden** | Yes | `AnnouncementCreateRequest(...)` | Inserts `announcements`, `announcement_targets` | **201, 400, 403** |
| `GET` | `/announcements/admin-contact` | Dynamically gets admin contact email | Any | Yes | None | Reads active `administrator` in `users` | 200, 401 |
| `GET` | `/announcements/{id}`| Retrieves circular detail & metrics | Any | Yes | Path: `id` | Reads `announcements` | 200, 404 |
| `PUT` | `/announcements/{id}`| Updates announcement text | Creator, Admin | Yes | `AnnouncementUpdateRequest(...)` | Updates `announcements` | 200, 400, 403 |
| `DELETE`| `/announcements/{id}`| Deletes notice | Admin, Manager | Yes | Path: `id` | Deletes or archives notice | 200, 403, 404 |
| `POST` | `/announcements/{id}/read`| Records user read receipt | Any | Yes | Path: `id` | Inserts `announcement_reads` | 200, 404 |
| `PUT` | `/announcements/{id}/acknowledge`| Submits mandatory student acknowledgement | Student | Yes | `AcknowledgeRequest(remarks)` | Inserts `announcement_acknowledgements` | 200, 400 |

---

### Module 7: Notifications & WebSockets (`/notifications`, `/ws`)
*Source Router:* [`Backend/api/routers/notifications.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/notifications.py)

| Method | Path | Purpose | Required Roles | Auth | Request Body / Params | Database Effects | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| `GET` | `/notifications` | Lists paginated notifications for caller | Any | Yes | `?limit=&offset=` | Reads `notifications` | 200, 401 |
| `PUT` | `/notifications/{id}/read`| Marks notification as read | Caller | Yes | Path: `id` | Updates `notifications.is_read = 1` | 200, 404 |
| `PUT` | `/notifications/read-all` | Marks all notifications as read | Caller | Yes | None | Updates all user rows in `notifications` | 200, 401 |
| `DELETE`| `/notifications/{id}` | Dismisses notification | Caller | Yes | Path: `id` | Deletes from `notifications` | 200, 404 |
| `WS` | `/ws/{user_id}` | WebSocket stream for live alerts | Caller | Token Query | WS Connection | Registers socket in `WebSocketManager` | 101, 403 |

---

### Module 8: Governance & System Maintenance (`/audit`, `/backups`, `/settings`)

| Method | Path | Purpose | Required Roles | Auth | Request Body / Params | Database Effects | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| `GET` | `/audit` | Lists immutable audit log entries | Admin, Manager | Yes | `?action=&entity_type=&limit=` | Reads `audit_logs` | 200, 403 |
| `GET` | `/backups` | Lists database backups on disk | Admin, Manager | Yes | None | Reads `backups` table & filesystem | 200, 403 |
| `POST` | `/backups` | Triggers immediate SQLite online backup | Admin, Manager | Yes | None | Creates backup copy on disk | 201, 500 |
| `POST` | `/backups/{id}/restore`| Restores database snapshot | Admin | Yes | Path: `id` | Replaces active `campus_pulse.db` | 200, 403, 500 |
| `GET` | `/settings` | Retrieves system configuration keys | Admin | Yes | None | Reads `system_settings` | 200, 403 |
| `PUT` | `/settings` | Updates institutional configurations | Admin | Yes | `SettingsUpdateRequest(...)` | Updates `system_settings` | 200, 403 |

---

### Module 9: Multi-Tenant Platform Operations (`/platform`, `/superadmin`)
*Source Router:* [`Backend/api/routers/platform.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/platform.py)

| Method | Path | Purpose | Required Roles | Auth | Request Body / Params | Database Effects | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- | :--- |
| `GET` | `/superadmin/institutions` | Lists all campus tenant institutions | Super Admin | Yes | None | Reads `institutions` table | 200, 403 |
| `POST` | `/superadmin/institutions` | Registers new university institution | Super Admin | Yes | `InstitutionCreateRequest(...)` | Inserts `institutions` | 201, 400, 403 |
| `GET` | `/superadmin/health` | Comprehensive cluster health status | Super Admin | Yes | None | Checks disk, database WAL, schedulers | 200, 403 |
| `GET` | `/superadmin/support` | Global cross-institution support tickets | Super Admin | Yes | None | Reads platform support queue | 200, 403 |
