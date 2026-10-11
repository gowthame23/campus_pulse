# 🚀 Campus Pulse v1.0.0 — Release Notes

> **Release Tag:** `v1.0.0`
> **Release Date:** August 6, 2026
> **Status:** Production-Ready (Main Branch Frozen)

---

## ✨ 1. New Features

### 📋 Complaint Management Engine
- **Full Lifecycle Handling**: Complete workflow support for `Submitted` → `In Progress` → `Resolved` → `Closed` / `Reopened`.
- **Role-Based Routing**: Auto-routing based on department and location; manual coordinator assignment.
- **SLA & Due Date Tracking**: Dynamic calculation of SLA breach status (`🟢 On Time`, `🟡 Due Today`, `🔴 Overdue`).
- **Public & Community Complaints**: Public complaint board with duplicate detection and community impact counters.

### 👥 Multi-Role Authorization System
- Strict Role-Based Access Control (RBAC) across 5 distinct roles:
  1. **Student**: Complaint creation, verification, public complaints, notifications, lost & found.
  2. **Coordinator**: Departmental complaint management, assignment, resolution, SLA tracking.
  3. **Location In-Charge / Warden**: Location-scoped complaint management (`LOC_HOSTEL_A`), resolution tracking.
  4. **App Manager**: Cross-department oversight, user administration, analytics.
  5. **Administrator**: Full platform administration, audit logs, system health, settings, data cleanup.

### 🔍 Lost & Found Module
- Report lost and found items with detailed metadata, images, and brand/serial tracking.
- Ownership claim submission and review workflow.
- Domain-bound WebSocket chat between claimers and reporters upon claim approval.

### 📢 Announcements & Real-Time Notifications
- Audience-targeted campus announcements with read tracking and mandatory acknowledgements.
- In-app notification center with real-time WebSocket delivery (`/notifications/ws/{user_id}`).

### 📊 Analytics & Reporting
- Comprehensive dashboard with role-tailored key performance indicators (KPIs).
- CSV export for complaints, locations, departments, user activity, and lost & found reports.
- Full system audit logging tracking all administrative, authentication, and status operations.

---

## 🔒 2. Security Fixes & Enhancements

- **Password Hashing**: PBKDF2-SHA256 algorithm with 260,000 iterations and unique random salts.
- **SQLite Referential Integrity**: Enforced `PRAGMA foreign_keys = ON` across all database connections.
- **3-Step OTP Password Reset**: Implemented secure `/auth/password-reset/request`, `/verify`, and `/complete` endpoints. Removed `simulated_otp` payload leaks from responses and deprecated the unauthenticated `/auth/reset-password` endpoint (`410 GONE`).
- **Rate Limiting**: Sliding window log rate limiter (5 requests / min with 15-minute lockout) on all sensitive authentication endpoints.
- **Dynamic CORS**: Environment-configurable origins via `CORS_ORIGINS`.
- **Attachment Access Controls**: Enforced strict cross-user download and delete guards (`_ensure_attachment_access`).

---

## ⚠️ 3. Known Limitations

1. **SQLite Concurrency**: SQLite default single-writer model is suitable for single-process app deployments. For multi-worker horizontal scaling, PostgreSQL is recommended (see `DEPLOYMENT_GUIDE.md`).
2. **In-Memory Session Store**: Default session store retains active user tokens in server memory. Server restarts require users to re-authenticate.

---

## 🌿 4. Branching Strategy Notice

- **Main Branch (`master` / `main`)**: Frozen for v1.0.0 production stability. Only critical bug hotfixes will be committed to `main`.
- **Develop Branch (`develop`)**: All future feature development and non-critical updates will take place on `develop`.
