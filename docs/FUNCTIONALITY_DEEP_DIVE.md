# Campus Pulse — Complete Functionality Catalogue & Module Specifications

> **Document Type:** Comprehensive Feature Catalogue & Functional Architecture  
> **Status:** Verified against Source Code & Active Routing Systems  
> **Repository:** Campus Pulse (`CampusPulse_co`)  

---

## Overview

This document catalogs every functional capability verified within Campus Pulse. Each capability is detailed using the mandatory 14-point specification standard (A through N), establishing its user journey, frontend view layer, backend route handlers, database interactions, security controls, and source references.

---

## Module 1: Authentication & Session Management

### 1.1 Secure User Login

#### A. Functionality Name
Secure User Login & Session Token Issuance.

#### B. Problem it Solves
Authenticates campus users (students, faculty, staff, administrators), verifies cryptographic credentials, blocks brute-force intrusions, and issues a revocable bearer session token.

#### C. Authorized Users
All valid campus accounts (`student`, `coordinator`, `location_in_charge`, `app_manager`, `administrator`, `super_admin`).

#### D. User Journey
1. User navigates to `/login`.
2. Enters registered email address and password.
3. Clicks "Sign In".
4. If successful, browser stores session token and redirects user to their role-specific dashboard.
5. If invalid, receives a clear error banner without disclosing whether the email or password was wrong.

#### E. Frontend Implementation
- **Component:** [`Frontend/src/pages/auth/LoginPage.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/pages/auth/LoginPage.jsx).
- **Service:** `authService.login({ username, password })` in [`Frontend/src/services/authService.js`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/services/authService.js).
- **State Management:** Interacts with `AuthContext.jsx` to update `token`, `user`, and `isAuthenticated`.

#### F. Backend Implementation
- **Route:** `POST /auth/login` in [`Backend/api/routers/auth.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/auth.py).
- **Service:** `AuthService.authenticate()` in [`Backend/services/auth_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/auth_service.py).
- **Database Updates:** Queries `users` table; inserts row into `login_attempts`; inserts token hash into `user_sessions`.

#### G. Data Flow
`LoginPage.jsx` → `authService.login()` → HTTP POST `/auth/login` → `rate_limit_middleware` → `auth.py:login()` → `AuthService.authenticate()` → `sqlite3` queries `users` → `verify_password()` → `create_session()` → `user_sessions` INSERT → JSON response with token → `AuthContext` localStorage → Redirect.

#### H. Technologies Used
Python 3, FastAPI, Pydantic, SQLite (WAL), PBKDF2-HMAC-SHA256, React 19, Axios, React Router.

#### I. Why This Implementation Was Chosen
PBKDF2 with per-user salt is standard-library native, avoiding brittle C-extension dependencies while ensuring robust cryptographic security. Opaque session tokens allow instantaneous administrative revocation.

#### J. Why Not Other Methods?
Stateless JWTs cannot be immediately revoked upon administrative deactivation without complex token blacklisting caches.

#### K. Security and Edge Cases
- Rate limiting prevents brute force (lockout after 5 failed attempts).
- Inactive or suspended accounts receive `403 Forbidden` ("Your account has been deactivated").
- Constant-time hash comparison (`secrets.compare_digest`) prevents timing attacks.

#### L. Tests and Verification
- [`Backend/tests/test_workflow1_auth.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/tests/test_workflow1_auth.py): Verifies login, invalid credentials, deactivation blocks.
- [`Backend/tests/smoke_test.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/tests/smoke_test.py): Verifies logins for Administrator, App Manager, Coordinator, Student (19/19 PASSED).

#### M. Limitations and Status
Fully implemented, verified, and operational.

#### N. Source References
- Backend: [`Backend/api/routers/auth.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/auth.py), [`Backend/services/auth_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/auth_service.py), [`Backend/utils/passwords.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/utils/passwords.py).
- Frontend: [`Frontend/src/pages/auth/LoginPage.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/pages/auth/LoginPage.jsx), [`Frontend/src/context/AuthContext.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/context/AuthContext.jsx).

---

### 1.2 User Logout & Session Revocation

#### A. Functionality Name
User Logout & Session Destruction.

#### B. Problem it Solves
Terminates an authenticated session, destroys browser tokens, and removes active session hashes from the database to prevent replay attacks on shared university computers.

#### C. Authorized Users
Any authenticated user.

#### D. User Journey
1. User clicks the user profile avatar in the Navbar.
2. Clicks "Sign Out".
3. Token is invalidated on the server and removed from browser storage.
4. User is redirected to `/login`.

#### E. Frontend Implementation
- **Component:** [`Frontend/src/layouts/Navbar.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/layouts/Navbar.jsx).
- **Context Method:** `logout()` in `AuthContext.jsx`.

#### F. Backend Implementation
- **Route:** `POST /auth/logout` in `Backend/api/routers/auth.py`.
- **Logic:** Calls `delete_session(token)` in `Backend/api/security.py`, deleting matching session hash from `user_sessions`.

#### G. Data Flow
Navbar click → `AuthContext.logout()` → `POST /auth/logout` → `delete_session()` → `DELETE FROM user_sessions` → localStorage cleared → Redirect to `/login`.

#### H. Technologies Used
Python 3, FastAPI, SQLite, React 19, Axios.

#### I. Why This Implementation Was Chosen
Direct database deletion guarantees the token is useless immediately after the user clicks logout.

#### J. Why Not Other Methods?
Relying solely on client-side token deletion leaves the token valid on the network until expiration.

#### K. Security and Edge Cases
Even if network fails during logout, frontend purges client storage to protect the local device.

#### L. Tests and Verification
Verified in `Backend/tests/test_workflow1_auth.py`.

#### M. Limitations and Status
Fully implemented and verified.

#### N. Source References
- Backend: [`Backend/api/security.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/security.py#L90-L105).
- Frontend: [`Frontend/src/context/AuthContext.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/context/AuthContext.jsx).

---

## Module 2: Complaint Submission & Evidence Handling

### 2.1 Student Complaint Submission

#### A. Functionality Name
Campus Grievance Submission with Evidence Upload.

#### B. Problem it Solves
Enables students to lodge complaints regarding hostel amenities, academic block equipment, mess food quality, or sports infrastructure, with photographic evidence.

#### C. Authorized Users
`student`, `location_in_charge` (submitting on behalf of a resident).

#### D. User Journey
1. Student clicks "Report a Problem" on Student Dashboard.
2. Form opens on `/complaints/new`.
3. Selects Location (e.g., Hostel 1), Department (e.g., Plumbing), Priority (Normal/High), enters Title, Description.
4. Optionally attaches evidence image/PDF.
5. Clicks "Submit Complaint".
6. Success toast appears; redirects to `/complaints/:id`.

#### E. Frontend Implementation
- **Component:** [`Frontend/src/pages/student/CreateComplaintPage.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/pages/student/CreateComplaintPage.jsx).
- **Service:** `complaintService.create(formData)` in [`Frontend/src/services/complaintService.js`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/services/complaintService.js).

#### F. Backend Implementation
- **Route:** `POST /complaints` in [`Backend/api/routers/complaints.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/complaints.py).
- **Service:** `ComplaintService.create_complaint()` in [`Backend/services/complaint_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/complaint_service.py).
- **Database:** Inserts into `complaints`, `attachments`, `notifications`, `activity_events`.

#### G. Data Flow
`CreateComplaintPage.jsx` → `complaintService.create()` → `POST /complaints` → `require_roles("student", ...)` → `complaint_service.create_complaint()` → Resolves routing → SQLite INSERT `complaints` → SQLite INSERT `notifications` → 201 Created → Redirect.

#### H. Technologies Used
Python 3, FastAPI, SQLite, Pydantic, React 19, Tailwind CSS.

#### I. Why This Implementation Was Chosen
Decoupled routing engine evaluates assignments during creation, immediately routing issues to the relevant department coordinator without manual admin triaging.

#### J. Why Not Other Methods?
Manual triage queues create multi-day delays before a technician is assigned.

#### K. Security and Edge Cases
- Validation requires title (min 5 chars) and description (min 10 chars).
- Hostel-scoping rule prevents students from lodging hostel complaints in blocks they do not reside in.

#### L. Tests and Verification
- [`Backend/tests/test_workflow4_complaint_management.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/tests/test_workflow4_complaint_management.py): Passed (18/18 tests in regression suite).

#### M. Limitations and Status
Fully implemented, verified, and operational.

#### N. Source References
- Backend: [`Backend/api/routers/complaints.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/complaints.py), [`Backend/services/complaint_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/complaint_service.py).
- Frontend: [`Frontend/src/pages/student/CreateComplaintPage.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/pages/student/CreateComplaintPage.jsx).

---

## Module 3: Campus Announcements & Official Notices

### 3.1 Staff Announcement Composition & Publishing

#### A. Functionality Name
Official Campus Circular Composition, Targeting & Broadcast.

#### B. Problem it Solves
Permits authorized university officials to broadcast urgent alerts, exam schedules, hostel roll calls, and maintenance notices to targeted groups across campus.

#### C. Authorized Users
`administrator`, `app_manager`, `location_in_charge` (Hostel Wardens). **Students and Coordinators are strictly forbidden (403).**

#### D. User Journey
1. Staff member navigates to `/announcements`.
2. Clicks "Compose Notice" button.
3. Enters Title, Category (Academic, Exam, Hostel, Maintenance, Emergency), Priority, Target Audience (Campus Wide, Hostel, Department), and optional Mandatory Acknowledgement flag.
4. Clicks "Publish Notice".
5. Circular is published and pinned if priority is High/Critical.

#### E. Frontend Implementation
- **Component:** [`Frontend/src/pages/AnnouncementPage.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/pages/AnnouncementPage.jsx).
- **Service:** `announcementService.create(data)` in [`Frontend/src/services/announcementService.js`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/services/announcementService.js).
- **Guards:** Button and modal are hidden if `!canCreate`.

#### F. Backend Implementation
- **Route:** `POST /announcements` in [`Backend/api/routers/announcements.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/announcements.py).
- **Permissions:** `require_roles(Administrator.ROLE, AppManager.ROLE, LocationInCharge.ROLE, "warden", "admin")`.
- **Database:** Inserts into `announcements` and `announcement_targets`.

#### G. Data Flow
`AnnouncementPage.jsx` → `announcementService.create()` → `POST /announcements` → `require_roles(...)` → `ann_service.create_announcement()` → SQLite INSERT → 201 Created → Refresh feed.

#### H. Technologies Used
Python 3, FastAPI, SQLite, React 19, Lucide React, Tailwind CSS.

#### I. Why This Implementation Was Chosen
Role guards strictly prevent student pranks or unauthorized broadcasts while allowing Wardens to publish hostel-specific rules directly.

#### J. Why Not Other Methods?
Permitting coordinators to broadcast campus notices causes notification spam for issues outside their department.

#### K. Security and Edge Cases
Students and Coordinators calling `POST /announcements` receive `403 Forbidden`.

#### L. Tests and Verification
- [`Backend/tests/test_workflow8_announcements.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/tests/test_workflow8_announcements.py): 6/6 tests PASSED (Admin create, Staff create, Student blocked with 403, Coordinator blocked with 403).

#### M. Limitations and Status
Fully implemented, verified, and operational.

#### N. Source References
- Backend: [`Backend/api/routers/announcements.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/announcements.py#L107-L146).
- Frontend: [`Frontend/src/pages/AnnouncementPage.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/pages/AnnouncementPage.jsx).

---

### 3.2 Student Notice Access & Dynamic Administrator Contact

#### A. Functionality Name
Student Notice Feed & Dynamic Administration Contact Card.

#### B. Problem it Solves
Provides students with verified circulars and a secure, dynamically resolved administrative contact email without exposing composer forms or displaying hardcoded example emails.

#### C. Authorized Users
`student` (read access).

#### D. User Journey
1. Student navigates to `/announcements`.
2. Sees official circulars with unread badges and priority tags.
3. Views official header card displaying the College Administrator contact email (e.g., `mailto:gowthamejjurothu@gmail.com`).
4. If mandatory acknowledgement is required, clicks "Acknowledge" to record compliance.

#### E. Frontend Implementation
- **Component:** [`Frontend/src/pages/AnnouncementPage.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/pages/AnnouncementPage.jsx#L267-L300).
- **Service:** `announcementService.getAdminContact()` in `announcementService.js`.
- **UI:** Dynamic email link with fallback message if no administrator contact exists. Zero hardcoded email addresses.

#### F. Backend Implementation
- **Route:** `GET /announcements/admin-contact` in `Backend/api/routers/announcements.py`.
- **Logic:** Queries active `administrator` users in `users` table; falls back to `system_settings` and `institutions`.

#### G. Data Flow
`AnnouncementPage.jsx` useEffect → `announcementService.getAdminContact()` → `GET /announcements/admin-contact` → queries SQLite `users` → returns `{ available: true, email: "...", name: "..." }` → renders dynamic link.

#### H. Technologies Used
Python 3, FastAPI, SQLite, React 19.

#### I. Why This Implementation Was Chosen
Eliminates hardcoded emails from frontend source code, ensuring portability across institutional deployments.

#### J. Why Not Other Methods?
Static hardcoded emails break when the administrator changes or when deploying in multi-tenant environments.

#### K. Security and Edge Cases
If no administrator email is found, gracefully returns `available: false` with a fallback message directing students to visit the administrative office.

#### L. Tests and Verification
- [`Backend/tests/test_workflow8_announcements.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/tests/test_workflow8_announcements.py): `test_workflow_8_get_admin_contact_endpoint` PASSED.

#### M. Limitations and Status
Fully implemented, verified, and operational.

#### N. Source References
- Backend: [`Backend/api/routers/announcements.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/announcements.py#L167-L226).
- Frontend: [`Frontend/src/pages/AnnouncementPage.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/pages/AnnouncementPage.jsx#L267-L300).

---

## Module 4: Complaint Resolution, SLA Escalation & Verification

### 4.1 Coordinator Resolution with Proof Attachment

#### A. Functionality Name
Coordinator Work Completion & Proof Submission.

#### B. Problem it Solves
Allows maintenance staff to mark an issue resolved, document corrective action, and upload verification photos before the complaint can be closed.

#### C. Authorized Users
`coordinator` (assigned coordinator), `app_manager`, `administrator`. **Wardens cannot resolve complaints.**

#### D. User Journey
1. Assigned coordinator opens complaint on `/complaints/:id`.
2. Enters resolution remarks and attaches completion photo (`resolution_proof_url`).
3. Clicks "Mark as Resolved".
4. Two-tier verification routing:
   - If priority is **High** or **Critical**, or randomly selected for spot-check (~10% of Normal/Low): status transitions to `'Waiting for Verification'` awaiting Warden inspection.
   - If **Normal** or **Low** (and not spot-checked): skips warden tier and moves directly to student confirmation window.
5. If in Warden tier: The facility Warden verifies in person and either:
   - **Approves:** advances complaint to student confirmation window.
   - **Rejects:** returns complaint to `'In Progress'` with notes for the coordinator.
6. Student receives 48-hour window to confirm closure or reopen (up to 3 times).

#### E. Frontend Implementation
- **Component:** [`Frontend/src/pages/complaints/ComplaintDetailsPage.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/pages/complaints/ComplaintDetailsPage.jsx).
- **Service:** `complaintService.resolve(id, data)` in `complaintService.js`.

#### F. Backend Implementation
- **Route:** `PUT /complaints/:id/resolve` in `Backend/api/routers/complaints.py`.
- **Service:** `ComplaintService.resolve_complaint()`.

#### G. Data Flow
`ComplaintDetailsPage.jsx` → `complaintService.resolve()` → `PUT /complaints/:id/resolve` → evaluates two-tier rules → updates SQLite `complaints` status → dispatches warden or student notification → returns updated complaint.

#### H. Technologies Used
Python 3, FastAPI, SQLite, React 19.

#### I. Why This Implementation Was Chosen
The two-tier verification workflow (in-person inspection for severe issues plus random spot checks, followed by student confirmation) prevents rubber-stamping and guarantees work quality.

#### J. Why Not Other Methods?
Allowing staff to self-verify or unilaterally close tickets leads to unresolved grievances being prematurely marked complete.

#### K. Security and Edge Cases
Only the assigned coordinator or administrators can mark an issue resolved. Wardens cannot resolve tickets, nor can wardens verify tickets that they submitted themselves.

#### L. Tests and Verification
Verified in [`Backend/tests/test_workflow4_complaint_management.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/tests/test_workflow4_complaint_management.py) and [`Backend/tests/test_two_tier_verification.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/tests/test_two_tier_verification.py).

#### M. Limitations and Status
Fully implemented, verified, and operational.

#### N. Source References
- Backend: [`Backend/services/complaint_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/complaint_service.py).
- Frontend: [`Frontend/src/pages/complaints/ComplaintDetailsPage.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/pages/complaints/ComplaintDetailsPage.jsx).

---

### 4.2 Automated Auto-Close & SLA Escalation Scheduler

#### A. Functionality Name
Background Auto-Close & SLA Breach Escalation Engine.

#### B. Problem it Solves
Prevents complaints from remaining indefinitely in verification if the student forgets to approve, and automatically escalates neglected issues up the supervisory chain.

#### C. Authorized Users
Automated background daemon (`SchedulerService`).

#### D. User Journey
1. Background scheduler fires every 300 seconds (5 minutes).
2. Evaluates complaints awaiting verification where resolution timestamp is older than 48 hours. Transitions them to `'Closed (Auto Closed)'`.
3. Evaluates uncompleted complaints (`status NOT IN ('Resolved', 'Closed', 'Closed (Auto Closed)', 'Rejected')`) where `datetime.utcnow() > sla_deadline`.
4. Escalates tier-by-tier: alerts location Warden first, then App Manager, then Administrator, and marks `is_escalated = 1`.

#### E. Frontend Implementation
Automated backend process. Reflected on frontend via StatCards and status badges (`Closed (Auto Closed)`).

#### F. Backend Implementation
- **Module:** [`Backend/services/scheduler_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/scheduler_service.py).
- **Boot Hook:** Started in `Backend/api/main.py:lifespan()`.

#### G. Data Flow
Timer fires → `scheduler_service.py` executes query → SQLite UPDATE `complaints` → generates escalation notification records → logs run to logger.

#### H. Technologies Used
Python 3 standard library `threading.Thread`, SQLite.

#### I. Why This Implementation Was Chosen
Lightweight in-process background thread eliminates heavy external message broker dependencies (Celery, Redis) for a single-server deployment.

#### J. Why Not Other Methods?
Celery/Redis adds complex operational requirements, multi-container orchestration, and memory overhead.

#### K. Security and Edge Cases
Database timeout handles potential lock contention gracefully without crashing the ASGI worker process.

#### L. Tests and Verification
Verified in startup lifespan and scheduler logs.

#### M. Limitations and Status
Fully implemented, verified, and running live.

#### N. Source References
- Backend: [`Backend/services/scheduler_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/scheduler_service.py), [`Backend/api/main.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/main.py#L19-L35).

---

## Module 5: Lost & Found Management

### 5.1 Item Registration & Image Upload

#### A. Functionality Name
Lost & Found Item Reporting & Evidence Image Upload.

#### B. Problem it Solves
Provides a centralized, searchable campus repository for lost student items (ID cards, laptops, keys) to facilitate return.

#### C. Authorized Users
All authenticated users (`student`, staff, administrators).

#### D. User Journey
1. User navigates to `/lost-found`.
2. Clicks "Report Lost Item" or "Report Found Item".
3. Enters Title, Category, Location, Date, Description, Contact details, and uploads photo.
4. Item appears on public feed.

#### E. Frontend Implementation
- **Component:** [`Frontend/src/pages/LostFoundPage.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/pages/LostFoundPage.jsx).
- **Service:** `lostFoundService.create(itemData)` in [`Frontend/src/services/lostFoundService.js`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/services/lostFoundService.js).

#### F. Backend Implementation
- **Route:** `POST /lost-found` and `POST /lost-found/upload` in [`Backend/api/routers/lost_found.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/lost_found.py).
- **Service:** `LostFoundService` in [`Backend/services/lost_found_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/lost_found_service.py).
- **Database:** Inserts into `lost_found_items` and `lost_found_images`.

#### G. Data Flow
`LostFoundPage.jsx` → `POST /lost-found/upload` → file written to disk → `POST /lost-found` → SQLite INSERT `lost_found_items` → Feed update.

#### H. Technologies Used
Python 3, FastAPI, SQLite, React 19.

#### I. Why This Implementation Was Chosen
Direct integration with the campus location registry allows filtering lost items by specific hostel or academic block.

#### J. Why Not Other Methods?
Social media groups scatter notices and lack searchable metadata or resolved statuses.

#### K. Security and Edge Cases
Users can only edit or delete items they posted; administrators have global management rights.

#### L. Tests and Verification
- [`Backend/tests/test_workflow6_lost_found.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/tests/test_workflow6_lost_found.py): Verified.

#### M. Limitations and Status
Fully implemented, verified, and operational.

#### N. Source References
- Backend: [`Backend/api/routers/lost_found.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/api/routers/lost_found.py), [`Backend/services/lost_found_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/lost_found_service.py).
- Frontend: [`Frontend/src/pages/LostFoundPage.jsx`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Frontend/src/pages/LostFoundPage.jsx).
