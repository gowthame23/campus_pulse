# Campus Pulse — API Reference & Route Documentation

Base URL: `http://localhost:8000`  
Interactive OpenAPI UI: `http://localhost:8000/docs`  
ReDoc UI: `http://localhost:8000/redoc`

**Verified Endpoint Count:** **318 Total Routes** (312 application endpoints across 26 routers + 2 WebSockets + 4 OpenAPI/docs routes).

---

## 1. Authentication & Security (`/auth`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/login` | Public | Authenticate with email/roll/employee ID and password; enforces rate limiting (5 failed attempts per 15 min triggers lockout). |
| `POST` | `/auth/logout` | Authenticated | Revoke user session and invalidate token. |
| `POST` | `/auth/change-password` | Authenticated | Change current user password with old password verification. |
| `POST` | `/auth/password-reset/request` | Public | Request an OTP for password reset (delivered via async SMTP or console log). |
| `POST` | `/auth/password-reset/verify` | Public | Verify OTP code and receive a short-lived reset token. |
| `POST` | `/auth/password-reset/complete` | Public | Complete password reset using verified reset token. |
| `POST` | `/auth/ws-ticket` | Authenticated | Generate a single-use, 60-second WebSocket connection ticket (tokens never pass in WS query strings). |

---

## 2. Complaint Management & Lifecycle (`/complaints`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/complaints` | Authenticated | Fetch complaints filtered by role, location, department, status, and SLA timeline. |
| `POST` | `/complaints` | Student, Warden | File a new complaint with location, department, exact spot, description, and optional attachments. |
| `GET` | `/complaints/{id}` | Authenticated | Retrieve full complaint details, history timeline, resolution notes, and attachments. |
| `POST` | `/complaints/{id}/accept` | Coordinator | Atomically accept an unassigned complaint from the department/location queue (409 Conflict if already claimed). |
| `POST` | `/complaints/{id}/start-work` | Coordinator | Transition status to `In Progress` and log start timestamp. |
| `POST` | `/complaints/{id}/progress-note` | Coordinator | Append progress notes visible to the student and warden. |
| `POST` | `/complaints/{id}/waiting-for-parts`| Coordinator | Set status to `Waiting for Parts` with mandatory reason and expected resume date. |
| `POST` | `/complaints/{id}/resume-work` | Coordinator | Resume work from waiting state, setting status back to `In Progress`. |
| `POST` | `/complaints/{id}/resolve` | Coordinator | Mark complaint as `Fixed`. Photo upload required for `High` and `Critical` priorities. |
| `POST` | `/complaints/{id}/warden-verify` | Warden | In-person verification for High/Critical tickets (or random spot check). Options: `Verified` (moves to Fixed) or `Not Fixed` (returns to In Progress). Self-verification blocked. |
| `POST` | `/complaints/{id}/confirm-close` | Student | Student confirms resolution and transitions ticket to `Closed`. |
| `POST` | `/complaints/{id}/reopen` | Student | Reopen a resolved ticket (max 3 times). On 3rd reopen, escalates automatically to `Admin Review` (`Disputed`). |
| `POST` | `/complaints/{id}/admin-decision` | Administrator | Final administrative decision on a disputed ticket (`Confirm Resolved` or `Reassign`). |
| `POST` | `/complaints/{id}/assign` | App Mgr, Admin | Manually reassign a complaint to a specific coordinator. |
| `POST` | `/complaints/{id}/escalate` | Staff | Manually escalate complaint priority or notify management. |
| `POST` | `/complaints/{id}/feedback` | Student | Submit 1–5 star rating and optional thank-you note upon closing complaint. |
| `GET` | `/complaints/{id}/feedback` | Authenticated | Retrieve feedback rating and thank-you message for a complaint. |
| `POST` | `/complaints/{id}/affected` | Student | Add caller to affected student count for communal complaints. |
| `DELETE` | `/complaints/{id}/affected` | Student | Remove caller from affected student count. |

---

## 3. Recognitions & Fixer of the Month (`/recognitions`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/recognitions/fixer-of-the-month` | Authenticated | Get current Fixer of the Month (highest rating + completed volume). |
| `GET` | `/recognitions/fixer-of-the-month/certificate` | Authenticated | Generate / download Fixer of the Month certificate data. |
| `GET` | `/recognitions/leaderboard` | Authenticated | Get ranked coordinator leaderboard based on speed, resolution rate, and student ratings. |

---

## 4. Campus Health Map & Analytics (`/analytics`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/analytics/health-map` | Authenticated | Real-time health cards per location (green/yellow/red) with 21-day pattern alerts (>=5 complaints). |
| `GET` | `/analytics/overview` | Admin, Mgr | Systemwide KPI overview (open, overdue, resolution times, SLA compliance). |
| `GET` | `/analytics/trends` | Admin, Mgr | Monthly and weekly complaint trend breakdowns. |

---

## 5. Sealed Safety Reports (`/safety-reports`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/safety-reports/enabled` | Public | Check if Sealed Safety Reports are currently enabled by Institution Administrator. |
| `POST` | `/safety-reports` | Authenticated | Submit sealed report; returns anonymous tracking code `SAFE-XXXX`. Identity sealed in separate table. |
| `GET` | `/safety-reports` | Admin | List sealed reports (status, date, category; reporter identity remains sealed). |
| `GET` | `/safety-reports/{report_code}/status` | Public / Token | Track report progress using anonymous `SAFE-XXXX` code. |
| `POST` | `/safety-reports/{report_code}/message`| Student / Admin | 2-way anonymous communication thread between reporter and administration. |
| `POST` | `/safety-reports/{report_code}/status` | Admin | Update status (`Investigating`, `Action Taken`, `Dismissed`). |
| `POST` | `/safety-reports/{report_code}/unseal` | Admin | Unseal reporter identity strictly on flagged `false_misuse` with mandatory written audit reason. |

---

## 6. Web Push Notifications (`/push`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/push/vapid-public-key` | Public | Retrieve application VAPID public key for browser push subscription. |
| `POST` | `/push/subscribe` | Authenticated | Register a Web Push subscription endpoint and encryption keys (`p256dh`, `auth`). |
| `POST` | `/push/unsubscribe` | Authenticated | Remove an active Web Push subscription. |

---

## 7. Location & Organization Coverage (`/locations` & `/departments`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/locations` | Authenticated | List all active campus locations with assigned wardens and coordinators. |
| `POST` | `/locations` | Admin | Create a new campus location (Hostel, Academic Block, Lab, etc.). |
| `GET` | `/locations/coverage-gaps` | App Mgr, Admin | Scan and report locations missing assigned wardens or coordinators. |
| `GET` | `/departments` | Authenticated | List departments with default SLA days and active complaint categories. |
| `POST` | `/departments` | Admin | Create or configure department SLA parameters. |

---

## 8. User Lifecycle & Coordinator Assignment (`/users`)

| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/users` | App Mgr, Admin | List user profiles with multi-role filters. |
| `POST` | `/users` | App Mgr, Admin | Create a new user account enforcing role hierarchy. |
| `PATCH` | `/users/{id}` | App Mgr, Admin | Update user name, email, active status, or primary department/location. |
| `POST` | `/users/bulk-coordinator-assignments`| App Mgr, Admin | Assign a coordinator to multiple departments and physical locations simultaneously. |
| `POST` | `/users/transfer-coordinator` | App Mgr, Admin | Reassign open complaint queue from an outgoing coordinator before deactivation. |

---

## 9. Real-Time Communications & WebSockets

- **Notifications WebSocket**: `ws://localhost:8000/notifications/ws?ticket=<single_use_ticket>`
  - Real-time in-app alerts for status updates, assignments, verifications, and escalations.
- **Personal Chat WebSocket**: `ws://localhost:8000/chat/ws?ticket=<single_use_ticket>`
  - Real-time direct messaging between campus staff and coordinators.

---

## 7. Error Handling Standard

API endpoints return consistent JSON responses with standard HTTP status codes:

- `200 OK`: Request succeeded.
- `201 Created`: Resource successfully created.
- `400 Bad Request`: Payload validation failed or required fields missing (`{"detail": "..."}`).
- `401 Unauthorized`: Missing, expired, or invalid Bearer token.
- `403 Forbidden`: Authenticated user lacks required role or ownership permission.
- `404 Not Found`: Target entity does not exist.
- `409 Conflict`: Concurrency conflict (e.g. ticket already accepted by another coordinator).
- `429 Too Many Requests`: Rate limit exceeded or account temporarily locked.
