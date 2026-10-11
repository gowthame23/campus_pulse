# Campus Pulse — AI System Prompt & Architectural Handoff Context

> **Target Audience:** Incoming AI Assistants & Senior Engineers  
> **Repository:** Campus Pulse (`CampusPulse_co`)  
> **Status:** Ground-Truth Verified against Source Code (October 2026)  
> **Instructions for the AI:** You are inheriting the **Campus Pulse** codebase. Read this entire document before answering questions or proposing modifications. **Do not hallucinate features, do not suggest replacing the stack, and always inspect actual source code before answering.**

---

## 1. What Campus Pulse Is & Its Core Mission

**Campus Pulse** is a production-grade, multi-role campus operations and facility complaint management platform built for collegiate institutions.
- **Problem Solved:** Decentralized, untracked university maintenance (hostels, academic blocks, mess halls, sports facilities) where student grievances are dropped, resolved without verification, or ignored without SLA escalation.
- **Operating Philosophy:**
  - **Zero-Drop Routing:** Issues are automatically assigned to coordinators or escalated through facility wardens, app managers, and campus administrators.
  - **Student-First Closure:** Technicians cannot unilaterally close issues. Work completion initiates a mandatory **48-hour student verification window** before closure or auto-closure.
  - **Transparent Accountability:** Every status change, assignment, and administrative mutation is recorded in an immutable audit trail.

---

## 2. Actual Technology Stack

- **Backend:** Python 3 (running on Python 3.14.2) with **FastAPI** (`0.109.0+`) served by **Uvicorn** (`0.27.0+`).
- **Frontend:** **React 19** (`19.2.7`) with **Vite** (`8.1.3`), **React Router DOM v7** (`7.18.1`), and **Tailwind CSS v4** (`4.3.2`).
- **Database:** **SQLite 3** running with **Write-Ahead Logging (WAL)** (`Backend/storage/campus_pulse.db`).
- **HTTP Transport:** Axios (`1.18.1`) with centralized Bearer token interceptor (`Frontend/src/api/axios.js`).
- **Testing:** Pytest (`8.0+`) for backend API & workflows; Vitest (`3.0+`) for frontend React components.

---

## 3. The 6 User Roles & Strict Permissions

The application defines 6 user roles in `models/user.py` and enforces them via `api/security.py`:

```
Super Admin (Platform Level)
  └── Administrator (College Level)
        ├── App Manager (Multi-Facility Operations)
        │     └── Location In-Charge / Warden (Single Facility / Hostel)
        └── Coordinator (Departmental Technician / Handler)
              └── Student (Grievance Reporter / Resident)
```

1. **`super_admin`:** Multi-tenant platform manager (`/superadmin`). Strictly **blocked with 403 Forbidden** from accessing campus operational complaints (`complaints.py:96-100`).
2. **`administrator`:** Full institutional control (`/admin`). Manages users, locations, departments, backups, audit logs, and settings.
3. **`app_manager`:** Operational supervisor (`/manager`). Oversees assigned facilities (e.g., Hostel 1, Academic 1, Mess 1); reallocates complaint queues.
4. **`location_in_charge` (Warden):** Facility supervisor (`/location`). Manages issues in their specific building; posts hostel circulars.
5. **`coordinator`:** Service department technician (`/coordinator`). Resolves assigned complaints, uploads proof. **STRICTLY PROHIBITED FROM POSTING ANNOUNCEMENTS (403 Forbidden).**
6. **`student`:** Resident student (`/student`). Reports complaints (hostel issues restricted to assigned hostel); verifies or reopens resolutions; views notices. **STRICTLY PROHIBITED FROM POSTING ANNOUNCEMENTS (403 Forbidden).**

---

## 4. Key Business Rules & Workflows

### 4.1 Complaint Lifecycle State Machine
```
Submitted ──> Assigned ──> In Progress ──> Resolved ──> Waiting for Verification ──> Closed
    │             │                                             │
    └── Rejected ─┘                                             └── Reopened (Max 3x)
```
- **Resolution Proof:** A coordinator resolving a complaint must provide either an "After Repair" image attachment OR detailed resolution notes (`complaint_service.py:350-356`).
- **Verification Window:** Marking resolved sets status to `'Waiting for Verification'` with an auto-close due date (default: 48 hours / 5 days configured via `auto_close_days`).
- **Reopen Limit:** Students can reopen an issue up to 3 times (`max_reopen_count`). The 2nd reopen triggers an automated critical escalation alert to the Administrator.
- **Background Daemon:** Runs every 300 seconds (`services/scheduler_service.py`) to auto-close expired verification tickets and flag overdue SLA escalations.

### 4.2 Complaint Routing Engine
1. Matches `(location_id, department_id)` in `coordinator_assignments`.
2. Fallback: Routes to `locations.warden_id` (Facility Warden).
3. Fallback: Routes to `locations.app_manager_id`.
4. Fallback: Stays unassigned and alerts Administrator.

### 4.3 Official Announcements
- **Creation Entry Point:** Only rendered for Admin, App Manager, and Warden. Removed from Student UI.
- **Dynamic Admin Contact:** Non-staff viewing `/announcements` see the official Administrator email resolved dynamically via `GET /announcements/admin-contact`. **No hardcoded emails exist in the frontend.**

---

## 5. Authentication & Security Architecture

1. **Stateful Database Sessions (No Stateless JWTs):**
   - Issues 32-byte high-entropy token (`secrets.token_urlsafe(32)`).
   - Stores `SHA-256(token)` in SQLite table `user_sessions`.
   - Incoming requests check `Authorization: Bearer <token>`, hash it, and lookup `user_sessions`.
   - **Benefit:** Instant session invalidation on logout or administrative deactivation.
2. **Password Security:**
   - PBKDF2-HMAC-SHA256 with 100,000 iterations and 16-byte random salt (`utils/passwords.py`).
   - Constant-time verification (`secrets.compare_digest`).
3. **Account Activation Tokens (No SMS OTPs):**
   - Uses 32-byte cryptographic URL tokens in `activation_tokens` table.
   - Sent via email links; consumed upon initial password setup.
4. **Object-Level Authorization:**
   - Enforced by `_visible_complaints()` in `api/routers/complaints.py`. Students cannot view other students' private complaints by manipulating IDs.

---

## 6. What Is Implemented vs. Scaffolded / Incomplete

- **Fully Implemented & Verified:**
  - Complete complaint lifecycle, multi-location assignment, and auto-close scheduler.
  - Student, Coordinator, Warden, App Manager, Admin dashboards.
  - Role-guarded announcements with dynamic admin contact.
  - Lost & Found item reporting and photo attachments.
  - In-app notification engine and WebSocket connections.
  - Database backup and restore operations via SQLite Online Backup API.
  - Audit logging of all administrative actions.
- **Scaffolded / Enterprise Schema Placeholders:**
  - The SQLite database contains 196 tables. Approximately 130 tables (e.g., `visitors`, `work_orders`, `ai_predictions`, `marketplace_packages`, `failover_targets`) are scaffolded database schemas from enterprise planning. They are **not wired to active API endpoints or UI views**. Do not attempt to fix or delete them.

---

## 7. Known Architectural Limitations & Tech Debt

1. **SQLite Single-Writer Concurrency:**
   - WAL mode allows unlimited concurrent readers, but database writes serialize to a single writer. Adequate for single-campus use, but requires migration to PostgreSQL if scaling to tens of thousands of concurrent users.
2. **Synchronous SMTP Calls:**
   - `utils/email.py` performs synchronous network handshakes with port 587. Should be offloaded to FastAPI `BackgroundTasks`.
3. **In-Memory WebSocket Connections:**
   - `websocket_manager.py` maintains connections in a local Python dict. Multiple Gunicorn workers will require Redis Pub/Sub to broadcast across workers.

---

## 8. Critical Instructions for the AI Assistant

1. **DO NOT Refactor or Replace the Stack:** Do not suggest replacing FastAPI, React, SQLite, or Tailwind. The project is fully functional on these technologies.
2. **DO NOT Invent Roles or Modify Role Enums:** Roles are strictly `super_admin`, `administrator`, `app_manager`, `location_in_charge`, `coordinator`, and `student`.
3. **DO NOT Hardcode Credentials or Secrets:** Use environment variables from `Backend/.env`.
4. **ALWAYS Inspect Code First:** Before suggesting any change, inspect the actual file paths referenced in the detailed documentation.

---

## 9. Detailed Reference Documentation Index

For exhaustive technical specifics, refer to the files in `docs/project_knowledge/`:
- **Complete Architecture & Workflows:** [`CAMPUS_PULSE_MASTER_CONTEXT.md`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/docs/project_knowledge/CAMPUS_PULSE_MASTER_CONTEXT.md)
- **All 277 API Endpoints:** [`CAMPUS_PULSE_API_REFERENCE.md`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/docs/project_knowledge/CAMPUS_PULSE_API_REFERENCE.md)
- **Database Schema & Catalogs:** [`CAMPUS_PULSE_DATABASE_REFERENCE.md`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/docs/project_knowledge/CAMPUS_PULSE_DATABASE_REFERENCE.md)
- **Mermaid Workflow Diagrams:** [`CAMPUS_PULSE_WORKFLOWS.md`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/docs/project_knowledge/CAMPUS_PULSE_WORKFLOWS.md)
- **Defects & Technical Debt Register:** [`CAMPUS_PULSE_ISSUES_AND_GAPS.md`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/docs/project_knowledge/CAMPUS_PULSE_ISSUES_AND_GAPS.md)
