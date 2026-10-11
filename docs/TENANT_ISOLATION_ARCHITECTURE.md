# CAMPUS PULSE — TENANT ISOLATION & MULTI-INSTITUTION ARCHITECTURE

## 1. Executive Architecture Summary
Campus Pulse is engineered to support single-tenant institutional operations as well as multi-institution platform governance.
The Super Admin platform layer operates at the global governance tier (`institution_id IS NULL`), while operational data (complaints, users, locations, departments) belongs to institutional boundaries.

---

## 2. System Entity Ownership Audit

| Database Table | Scope Boundary | Description |
| :--- | :--- | :--- |
| `institutions` | **Platform Global** | Master registry of onboarded universities/campuses. |
| `support_tickets` | **Platform Global** | Governance tickets between Institution Admins & Super Admin. |
| `platform_settings` | **Platform Global** | Platform-wide system configurations and release flags. |
| `users` | **Institutional** | User accounts belonging to a specific campus. |
| `student_profiles` | **Institutional** | Student roll numbers, academic programs, and hostel assignments. |
| `staff_profiles` | **Institutional** | Employee IDs, designations, and department assignments. |
| `locations` | **Institutional** | Campus buildings, hostels, mess halls, and sports complexes. |
| `departments` | **Institutional** | Campus operational departments (Electrical, Plumbing, IT, etc.). |
| `department_issues` | **Institutional** | Predefined complaint categories per department. |
| `complaints` | **Institutional** | Ticket lifecycle records for campus operational issues. |
| `comments` | **Institutional** | Updates, internal notes, and discussions on complaints. |
| `attachments` | **Institutional** | Evidence photos and repair documentation. |
| `notifications` | **Institutional** | In-app alerts delivered to campus users. |
| `user_sessions` | **Institutional** | Active login sessions persisted in database. |
| `password_resets` | **Institutional** | Password reset OTP tokens and attempt tracking. |
| `lost_found_items` | **Institutional** | Community lost & found item posts. |
| `lost_found_images` | **Institutional** | Overview and evidence photos for lost & found posts. |
| `lost_found_claims` | **Institutional** | Student ownership claims on lost & found items. |
| `announcements` | **Institutional** | Official campus broadcast notices. |
| `feedback` | **Institutional** | Service feedback submissions and staff responses. |

---

## 3. Recommended Tenant Isolation Models

### Model A: Shared Database with Logical Tenant Guard (Preferred Stage 1)
- Every institutional table includes an `institution_id` foreign key.
- FastAPI dependency `require_institution_scope` automatically injects `WHERE institution_id = current_user.institution_id` on every query.
- Super Admin (`institution_id IS NULL`) is prevented from querying institutional operational endpoints via HTTP 403 Forbidden guards.

### Model B: Schema-Per-Tenant or Database-Per-Tenant (Stage 2 High-Security Scale)
- Each university operates on an isolated SQLite database file (e.g. `storage/institutions/iiits.db`).
- A central platform routing service dynamically resolves the database connection per request host header / API key.

---

## 4. Super Admin Boundary & Data Protection Invariants
1. **Zero Exposure**: Super Admin accounts cannot view or modify student complaints, student profiles, or personal feedback.
2. **Platform Governance Only**: Super Admin manages institution onboarding, system health monitoring, version deployment, and platform support tickets.
