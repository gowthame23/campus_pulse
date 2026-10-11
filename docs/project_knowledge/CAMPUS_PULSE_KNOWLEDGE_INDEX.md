# Campus Pulse — Project Knowledge Index & Master Navigation Guide

> **Document Type:** Master Directory & Evidence Index  
> **Repository:** Campus Pulse (`CampusPulse_co`)  
> **Status:** Production-Verified against Active Codebase  
> **Audience:** AI Coding Assistants, Lead Architects, Product Reviewers, New Engineers  

---

## 1. Executive Directory Overview

This documentation suite represents an exhaustive, source-code-driven knowledge extraction of **Campus Pulse**, an enterprise campus operations and complaint lifecycle management platform. Every claim, schema definition, route mapping, and business rule within these files is backed by direct evidence from the repository files, SQLite system catalogs, or automated test executions.

All deliverables requested in the knowledge extraction specification have been generated in this dedicated directory:

| Document Deliverable | Filename | Purpose & Target Content | Primary Evidence Sources |
| :--- | :--- | :--- | :--- |
| **Deliverable A: Master Context** | [`CAMPUS_PULSE_MASTER_CONTEXT.md`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/docs/project_knowledge/CAMPUS_PULSE_MASTER_CONTEXT.md) | The definitive technical reference covering architecture, all 6 roles, permissions, 20 layers, data model, security, frontend, jobs, and deployment. | Codebase root, `Backend/api/`, `Backend/services/`, `Frontend/src/` |
| **Deliverable B: API Reference** | [`CAMPUS_PULSE_API_REFERENCE.md`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/docs/project_knowledge/CAMPUS_PULSE_API_REFERENCE.md) | Structured catalog of all 277 registered REST endpoints across 24 domain routers with HTTP methods, scopes, schemas, and test coverage. | `Backend/api/main.py`, `Backend/api/routers/*.py` |
| **Deliverable C: Database Reference** | [`CAMPUS_PULSE_DATABASE_REFERENCE.md`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/docs/project_knowledge/CAMPUS_PULSE_DATABASE_REFERENCE.md) | Complete SQLite relational model (196 tables), foreign keys, indexes, PRAGMA WAL mode, constraints, and active vs. placeholder schema analysis. | `Backend/storage/campus_pulse.db`, SQLite `PRAGMA` catalogs |
| **Deliverable D: Workflows Reference** | [`CAMPUS_PULSE_WORKFLOWS.md`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/docs/project_knowledge/CAMPUS_PULSE_WORKFLOWS.md) | Mermaid state and sequence diagrams for the complete complaint lifecycle, multi-location assignment, escalation, verification, and notices. | `complaint_service.py`, `auth_service.py`, `test_workflow*.py` |
| **Deliverable E: Issues & Gaps Register** | [`CAMPUS_PULSE_ISSUES_AND_GAPS.md`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/docs/project_knowledge/CAMPUS_PULSE_ISSUES_AND_GAPS.md) | Consolidated defect and risk registry with unique IDs, severity, evidence, reproduction paths, and documentation contradictions. | Bug analysis, concurrency limits, schema audit |
| **Deliverable F: Knowledge Index** | `CAMPUS_PULSE_KNOWLEDGE_INDEX.md` | *(This Document)* Master navigation guide, evidence confidence labeling, and coverage checklist. | Knowledge Base Meta |
| **Deliverable G: Context for ChatGPT** | [`CAMPUS_PULSE_CONTEXT_FOR_CHATGPT.md`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/docs/project_knowledge/CAMPUS_PULSE_CONTEXT_FOR_CHATGPT.md) | Compact, high-signal handoff prompt designed to prime external AI models with core facts, rules, and constraints without hallucinations. | Distilled Architectural Summary |

---

## 2. Core Architectural Facts (The "Must-Knows")

Any developer or AI assistant continuing work on Campus Pulse must understand these foundational facts:

1. **Active Technology Stack:**
   - **Backend:** Python 3 (CPython 3.10-3.14, verified on Python 3.14.2) using **FastAPI** (`0.109.0+`) running on **Uvicorn** (`0.27.0+`).
   - **Frontend:** **React 19** (`19.2.7`) with **Vite** (`8.1.3`), **React Router DOM v7** (`7.18.1`), and **Tailwind CSS v4** (`4.3.2`).
   - **Database:** **SQLite 3** operating in **WAL (Write-Ahead Logging)** mode (`Backend/storage/campus_pulse.db`).
2. **Stateful Session Architecture:**
   - The application does **not** use stateless JWTs.
   - It issues high-entropy opaque bearer tokens (`secrets.token_urlsafe(32)`), hashes them with SHA-256, and validates them against the `user_sessions` SQLite table.
   - This enables **immediate session invalidation** upon password changes or administrative deactivation.
3. **No SMS OTPs:**
   - The application does **not** use 6-digit numeric SMS OTPs.
   - It utilizes 32-byte cryptographic **Activation Tokens** (`activation_tokens`) delivered via email for account initialization and password resets.
4. **The Six User Roles:**
   - `super_admin`: Platform-level multi-tenant administration (strictly blocked from campus operational data).
   - `administrator`: Campus-level authority (user management, facilities, backups, settings).
   - `app_manager`: Multi-location operations supervisor (reassigns complaints across assigned hostels/complexes).
   - `location_in_charge`: Facility-specific warden (manages facility complaints, posts hostel circulars).
   - `coordinator`: Departmental technician/head (resolves complaints, uploads proof; **strictly forbidden from posting announcements**).
   - `student`: Resident student (submits issues, upvotes public notices, verifies or reopens resolutions; **strictly forbidden from posting announcements**).
5. **Zero-Drop Routing & 48-Hour Student Verification:**
   - Complaints follow an automated routing matrix: Coordinator Assignment → Facility Warden → App Manager → Administrator.
   - Staff cannot arbitrarily close issues. When marked resolved, issues enter `'Waiting for Verification'` for 48 hours. If the student takes no action, the background scheduler auto-closes them. If the student rejects within 48 hours, the issue is reopened (up to 3 times before administrative escalation).

---

## 3. Evidence Coverage Checklist

The following repository directories, modules, and systems were thoroughly inspected for this audit:

- [x] **Backend Entry Points:** `Backend/run_api.py`, `Backend/api/main.py`.
- [x] **API Routers (24 modules):** `auth.py`, `users.py`, `departments.py`, `locations.py`, `issues.py`, `complaints.py`, `public_complaints.py`, `dashboard.py`, `notifications.py`, `settings.py`, `attachments.py`, `analytics.py`, `audit.py`, `lost_found.py`, `announcements.py`, `feedback.py`, `reports.py`, `search.py`, `backups.py`, `chat.py`, `supervisor.py`, `master.py`, `programs.py`, `platform.py`.
- [x] **Core Business Services (26 services):** `auth_service.py`, `complaint_service.py`, `notification_service.py`, `announcement_service.py`, `attachment_service.py`, `audit_service.py`, `backup_service.py`, `scheduler_service.py`, `location_service.py`, `department_service.py`, etc.
- [x] **Domain Models (9 models):** `user.py`, `student.py`, `coordinator.py`, `location_in_charge.py`, `app_manager.py`, `administrator.py`, `location.py`, `department.py`, `complaint.py`.
- [x] **Security & Middleware:** `Backend/api/security.py`, `Backend/middleware/rate_limiter.py`.
- [x] **Database File & Schema:** `Backend/storage/campus_pulse.db` (196 tables cataloged via `PRAGMA table_info`, `foreign_key_list`, `index_list`).
- [x] **Frontend Shell & Config:** `Frontend/index.html`, `Frontend/package.json`, `Frontend/vite.config.js`, `Frontend/src/main.jsx`, `Frontend/src/App.jsx`.
- [x] **Frontend Routing & Guards:** `Frontend/src/routes/AppRoutes.jsx`, `Frontend/src/routes/ProtectedRoute.jsx`.
- [x] **Frontend UI Pages (40 pages):** Auth pages, Dashboards (Student, Admin, Manager, Coordinator, Location, SuperAdmin), Complaints, Announcements, Lost & Found, Notifications, Settings, Backups, Users.
- [x] **Frontend Component Library (18 components):** `Button`, `Modal`, `Table`, `Toast`, `Badge`, `Card`, `StatCard`, etc.
- [x] **Test Infrastructure:** 31 test files in `Backend/tests/` (executed smoke tests, workflow 8, workflow 4, role location assignments) and Vitest in `Frontend/src/__tests__/`.
