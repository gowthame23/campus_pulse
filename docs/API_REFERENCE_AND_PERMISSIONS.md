# Campus Pulse — Consolidated REST API Reference & Permissions Inventory

> **Document Type:** Complete REST API Specification & Endpoint Directory  
> **Status:** Verified against FastAPI Route Registry (277 Endpoints)  
> **Repository:** Campus Pulse (`CampusPulse_co`)  

---

## 1. API Architecture & Standards

- **Base URL:** `http://127.0.0.1:8000` (Direct) or `/api` (Reverse Proxy)
- **Protocol:** HTTP/1.1 with TLS / HTTPS support; WebSockets on `/ws`
- **Data Interchange:** `application/json` (REST endpoints); `multipart/form-data` (file uploads)
- **Authentication Scheme:** `Authorization: Bearer <session_token>` header
- **Error Standard:** RFC 7807 compatible JSON payload:
  ```json
  {
    "detail": "Error description string or validation error array"
  }
  ```

---

## 2. API Endpoints Catalog by Module

---

### Module 1: Authentication & Account Management (`/auth`)
*Router file:* [`Backend/api/routers/auth.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/auth.py)

| Method | Endpoint | Description | Roles | Auth Required | Request Body / Params | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| `POST` | `/auth/login` | User login & token issuance | Public | No | `LoginRequest(username, password)` | 200, 401, 403, 429 |
| `POST` | `/auth/logout` | Terminates active session | Any | Yes | None (Bearer Token) | 200, 401 |
| `GET` | `/auth/me` | Fetches active caller profile | Any | Yes | None | 200, 401 |
| `POST` | `/auth/change-password` | Updates password & revokes other sessions | Any | Yes | `PasswordChangeRequest(old_password, new_password)` | 200, 400, 401 |
| `POST` | `/auth/forgot-password` | Requests password reset email link | Public | No | `ForgotPasswordRequest(email)` | 200, 404 |
| `POST` | `/auth/reset-password` | Resets password via token | Public | No | `ResetPasswordRequest(token, new_password)` | 200, 400 |
| `POST` | `/auth/activate` | Activates account & sets initial password | Public | No | `ActivateAccountRequest(token, password)` | 200, 400 |

---

### Module 2: User & Roster Management (`/users`)
*Router file:* [`Backend/api/routers/users.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/users.py)

| Method | Endpoint | Description | Roles | Auth Required | Request Body / Params | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| `GET` | `/users` | Lists users with role/status filters | Admin, App Manager | Yes | `?role=&status=&q=&limit=&skip=` | 200, 401, 403 |
| `POST` | `/users` | Creates a single user account | Admin, App Manager | Yes | `UserCreateRequest(...)` | 201, 400, 403 |
| `GET` | `/users/{user_id}` | Retrieves full user profile | Admin, Manager, Self | Yes | Path: `user_id` | 200, 404 |
| `PUT` | `/users/{user_id}` | Updates user information | Admin, Manager | Yes | `UserUpdateRequest(...)` | 200, 400, 403 |
| `PUT` | `/users/{user_id}/deactivate`| Deactivates account & revokes sessions | Admin, Manager | Yes | Path: `user_id` | 200, 403, 404 |
| `PUT` | `/users/{user_id}/activate` | Reactivates inactive account | Admin, Manager | Yes | Path: `user_id` | 200, 403, 404 |
| `DELETE`| `/users/{user_id}` | Soft-deletes user (if no audit ties) | Admin | Yes | Path: `user_id` | 200, 403, 404 |
| `POST` | `/users/import` | Batch imports students from CSV/XLSX | Admin, Manager | Yes | `UploadFile` (multipart) | 200, 400, 403 |

---

### Module 3: Facility & Location Management (`/locations`)
*Router file:* [`Backend/api/routers/locations.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/locations.py)

| Method | Endpoint | Description | Roles | Auth Required | Request Body / Params | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| `GET` | `/locations` | Lists campus locations & buildings | Any | Yes | `?type=&status=` | 200, 401 |
| `POST` | `/locations` | Creates new campus location | Admin, Manager | Yes | `LocationCreateRequest(...)` | 201, 400, 403 |
| `GET` | `/locations/{location_id}` | Gets location details & wardens | Any | Yes | Path: `location_id` | 200, 404 |
| `PUT` | `/locations/{location_id}` | Updates location assignments | Admin, Manager | Yes | `LocationUpdateRequest(...)` | 200, 400, 403 |
| `DELETE`| `/locations/{location_id}` | Deactivates or removes location | Admin | Yes | Path: `location_id` | 200, 400, 403 |

---

### Module 4: Department Management (`/departments`)
*Router file:* [`Backend/api/routers/departments.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/departments.py)

| Method | Endpoint | Description | Roles | Auth Required | Request Body / Params | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| `GET` | `/departments` | Lists all service departments | Any | Yes | `?status=` | 200, 401 |
| `POST` | `/departments` | Creates service department | Admin, Manager | Yes | `DepartmentCreateRequest(...)` | 201, 400, 403 |
| `GET` | `/departments/{dept_id}` | Gets department details | Any | Yes | Path: `dept_id` | 200, 404 |
| `PUT` | `/departments/{dept_id}` | Updates department configuration | Admin, Manager | Yes | `DepartmentUpdateRequest(...)` | 200, 400, 403 |
| `DELETE`| `/departments/{dept_id}` | Deactivates department | Admin | Yes | Path: `dept_id` | 200, 400, 403 |

---

### Module 5: Complaint Operations (`/complaints`)
*Router file:* [`Backend/api/routers/complaints.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/complaints.py)

| Method | Endpoint | Description | Roles | Auth Required | Request Body / Params | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| `GET` | `/complaints` | Lists complaints scoped to caller role | Any | Yes | `?status=&priority=&location_id=&q=` | 200, 401 |
| `POST` | `/complaints` | Lodges new student complaint | Student, Warden | Yes | `ComplaintCreateRequest(...)` | 201, 400, 403 |
| `GET` | `/complaints/{id}` | Gets full complaint detail & comments | Author, Staff | Yes | Path: `id` | 200, 403, 404 |
| `PUT` | `/complaints/{id}/status` | Updates complaint status | Staff, Admin | Yes | `StatusUpdateRequest(status)` | 200, 400, 403 |
| `PUT` | `/complaints/{id}/assign` | Reassigns complaint to coordinator | Admin, Manager, Warden| Yes | `AssignRequest(assigned_to)` | 200, 400, 403 |
| `PUT` | `/complaints/{id}/resolve`| Marks complaint resolved with proof | Coordinator, Staff | Yes | `ResolveRequest(notes, proof_url)` | 200, 400, 403 |
| `PUT` | `/complaints/{id}/verify` | Approves resolution & closes issue | Complainant Student | Yes | `VerifyRequest(rating, comments)` | 200, 400, 403 |
| `POST` | `/complaints/{id}/reopen` | Reopens unsatisfactory resolution | Complainant Student | Yes | `ReopenRequest(reason)` | 200, 400, 403 |
| `POST` | `/complaints/{id}/comments`| Appends discussion comment | Author, Staff | Yes | `CommentCreateRequest(content)` | 201, 400, 403 |
| `POST` | `/complaints/{id}/upvote` | Upvotes public complaint | Student | Yes | Path: `id` | 200, 400 |

---

### Module 6: Campus Announcements & Notices (`/announcements`)
*Router file:* [`Backend/api/routers/announcements.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/announcements.py)

| Method | Endpoint | Description | Roles | Auth Required | Request Body / Params | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| `GET` | `/announcements` | Fetches active campus circulars | Any | Yes | `?category=&priority=&q=` | 200, 401 |
| `POST` | `/announcements` | Composes & broadcasts notice | **Admin, Manager, Warden** | Yes | `AnnouncementCreateRequest(...)` | **201, 400, 403** |
| `GET` | `/announcements/admin-contact` | Dynamically gets admin contact email | Any | Yes | None | 200, 401 |
| `GET` | `/announcements/{id}`| Retrieves circular detail & metrics | Any | Yes | Path: `id` | 200, 404 |
| `PUT` | `/announcements/{id}`| Updates announcement text | Creator, Admin | Yes | `AnnouncementUpdateRequest(...)` | 200, 400, 403 |
| `DELETE`| `/announcements/{id}`| Deletes notice | Admin, Manager | Yes | Path: `id` | 200, 403, 404 |
| `POST` | `/announcements/{id}/read`| Records user read receipt | Any | Yes | Path: `id` | 200, 404 |
| `PUT` | `/announcements/{id}/acknowledge`| Submits mandatory student acknowledgement | Student | Yes | `AcknowledgeRequest(remarks)` | 200, 400 |
| `POST` | `/announcements/{id}/archive` | Archives expired circular | Admin, Manager | Yes | Path: `id` | 200, 403 |

---

### Module 7: Lost & Found Service (`/lost-found`)
*Router file:* [`Backend/api/routers/lost_found.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/lost_found.py)

| Method | Endpoint | Description | Roles | Auth Required | Request Body / Params | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| `GET` | `/lost-found` | Lists lost & found items | Any | Yes | `?category=&type=&status=&q=` | 200, 401 |
| `POST` | `/lost-found` | Registers lost or found item | Any | Yes | `LostFoundCreateRequest(...)` | 201, 400 |
| `POST` | `/lost-found/upload` | Uploads photographic evidence | Any | Yes | `UploadFile` (multipart) | 200, 400 |
| `GET` | `/lost-found/{id}` | Gets item detail & claim info | Any | Yes | Path: `id` | 200, 404 |
| `PUT` | `/lost-found/{id}` | Updates item or marks claimed | Author, Admin | Yes | `LostFoundUpdateRequest(...)` | 200, 403, 404 |
| `DELETE`| `/lost-found/{id}` | Deletes record & attached photos | Author, Admin | Yes | Path: `id` | 200, 403, 404 |

---

### Module 8: Notifications & WebSockets (`/notifications`, `/ws`)
*Router file:* [`Backend/api/routers/notifications.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/notifications.py)

| Method | Endpoint | Description | Roles | Auth Required | Request Body / Params | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| `GET` | `/notifications` | Lists paginated notifications for caller | Any | Yes | `?limit=&offset=` | 200, 401 |
| `PUT` | `/notifications/{id}/read`| Marks notification as read | Caller | Yes | Path: `id` | 200, 404 |
| `PUT` | `/notifications/read-all` | Marks all notifications as read | Caller | Yes | None | 200, 401 |
| `DELETE`| `/notifications/{id}` | Dismisses notification | Caller | Yes | Path: `id` | 200, 404 |
| `WS` | `/ws/{user_id}` | WebSocket stream for live alerts | Caller | Token Query | WS Connection | 101, 403 |

---

### Module 9: System Governance & Maintenance (`/audit`, `/backups`, `/settings`)

| Method | Endpoint | Description | Roles | Auth Required | Request Body / Params | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| `GET` | `/audit` | Lists immutable audit log entries | Admin, Manager | Yes | `?action=&entity_type=&limit=` | 200, 403 |
| `GET` | `/backups` | Lists database backups on disk | Admin, Manager | Yes | None | 200, 403 |
| `POST` | `/backups` | Triggers immediate SQLite online backup | Admin, Manager | Yes | None | 201, 500 |
| `POST` | `/backups/{id}/restore`| Restores database snapshot | Admin | Yes | Path: `id` | 200, 403, 500 |
| `GET` | `/settings` | Retrieves system configuration keys | Admin | Yes | None | 200, 403 |
| `PUT` | `/settings` | Updates institutional configurations | Admin | Yes | `SettingsUpdateRequest(...)` | 200, 403 |

---

### Module 10: Multi-Tenant Platform Operations (`/platform`, `/superadmin`)
*Router file:* [`Backend/api/routers/platform.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/platform.py)

| Method | Endpoint | Description | Roles | Auth Required | Request Body / Params | Status Codes |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| `GET` | `/superadmin/institutions` | Lists all campus tenant institutions | Super Admin | Yes | None | 200, 403 |
| `POST` | `/superadmin/institutions` | Registers new university institution | Super Admin | Yes | `InstitutionCreateRequest(...)` | 201, 400, 403 |
| `GET` | `/superadmin/health` | Comprehensive cluster health status | Super Admin | Yes | None | 200, 403 |
| `GET` | `/superadmin/support` | Global cross-institution support tickets | Super Admin | Yes | None | 200, 403 |
