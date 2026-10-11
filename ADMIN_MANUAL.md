# Campus Pulse — Administrator & App Manager Operations Manual

This guide covers setup and daily administration for **App Managers** (`app_manager`) and **Administrators** (`administrator`).

---

## 🛠️ 1. App Manager Operational Setup Guide

The App Manager is responsible for staffing operations, mapping coverage across physical locations and maintenance departments, and eliminating gaps so no complaint is orphaned.

### Step 1: Create Coordinators and Staff
1. Navigate to **User Management** (`/admin/users`).
2. Click **Create User**. Select the role `Coordinator`.
3. Fill in name, email, and employee ID. (Passwords are securely generated or set via environment initial seeds).

### Step 2: Multi-Department & Location Mapping
A single coordinator can hold responsibilities across multiple departments and multiple physical campus locations.
1. In **User Management**, select the coordinator and open **Manage Assignments**.
2. Alternatively, invoke the API endpoint:
   `POST /users/bulk-coordinator-assignments`
   ```json
   {
     "coordinator_id": "USR_COORD_1",
     "assignments": [
       {"department_id": "DEPT_ELEC", "location_id": "LOC_HOSTEL_1"},
       {"department_id": "DEPT_PLUMB", "location_id": "LOC_HOSTEL_1"},
       {"department_id": "DEPT_ELEC", "location_id": "LOC_ACAD_BLOCK"}
     ]
   }
   ```

### Step 3: Assign Wardens to Every Location
Every physical hostel or campus zone must have an assigned Warden. Wardens receive notifications for all complaints filed in their jurisdiction and perform in-person verifications.
1. Navigate to **Location Management** (`/admin/locations`).
2. Edit each location and assign the corresponding Warden (`in_charge_id`).
3. Note: A warden cannot accept or fix complaints, nor can they verify issues they reported.

### Step 4: Clear Coverage Gaps
1. Navigate to **Coverage Gaps** (`/admin/locations` or API `GET /locations/coverage-gaps`).
2. Review any locations marked with:
   - 🔴 **Missing Warden**: No in-charge assigned. Assign a warden immediately.
   - 🟡 **Missing Coordinator**: A department at this location has no assigned coordinator. Complaints filed here will generate coverage gap alerts until a coordinator is mapped.

---

## ⚡ 2. Core Complaint Lifecycle Operations

### 2.1 Two-Tier Verification Flow
1. **Work Completion**: When a coordinator marks a ticket as `Fixed`, they must attach an after-fix photo if the priority is `High` or `Critical`.
2. **Warden Verification**:
   - `High` and `Critical` tickets enter `Pending Verification`. The location warden must inspect the physical repair in person.
   - Approximately **10% of Medium and Low** tickets are randomly selected for spot checks.
   - The warden submits `Warden Verified` (moves to `Fixed` for student) or `Not Fixed` (returns ticket to `In Progress` with explanation).
3. **Student Closeout & Auto-Close**:
   - The student receives an alert and can confirm resolution (`Closed`).
   - If the student does not respond within **48 hours**, the system automatically closes the ticket (a warning reminder is sent at **24 hours**).

### 2.2 Reopens and Admin Review (Dispute Resolution)
- A student can reopen a resolved ticket up to **2 times**.
- Upon the **3rd reopen**, the ticket automatically transitions to **Admin Review** (status: `Disputed`) and notifies the Administrator.
- The Administrator reviews the audit log, photos, and chat history, then issues an official decision via `POST /complaints/{id}/admin-decision`:
  - `Confirm Resolved`: Finalizes closure of the dispute.
  - `Reassign`: Returns the issue to the department queue with administrative directives.

---

## 💾 3. Database Backup & Safe Restore Procedures

### 3.1 Live Database Backups
1. Navigate to **Backup Management** (`/admin/backups`).
2. Click **Create Backup**. The system creates a hot copy of `campus_pulse.db` in `storage/backups/` using SQLite online backup API.

### 3.2 Safe Offline Restore Flow
> [!WARNING]
> Restoring a database while a server is actively handling requests can corrupt the database or leave memory caches desynchronized. Campus Pulse enforces a **safe pending restore workflow**:

1. Click **Restore Backup** in the UI.
2. The system places the backup file at `storage/restore_pending.db` and writes an atomic marker file `storage/restore_pending.marker`.
3. The live database is **never overwritten** while Uvicorn is active.
4. Restart the backend process:
   ```bash
   # On startup, the server detects the marker, creates a pre-restore backup copy,
   # atomically swaps the file, and removes the marker.
   uvicorn api.main:app --workers 1 --port 8000
   ```

---

## 🧹 4. Database Maintenance & Cleanup Scripts

### 4.1 Purging Unused Legacy Tables
If your database contains speculative prototype tables, safely remove them using the verified script:
```bash
python scripts/drop_unused_tables.py --confirm
```
This utility:
- Requires `--confirm` to prevent accidental execution.
- Automatically saves a pre-drop backup (`campus_pulse_pre_drop_<timestamp>.db`).
- Drops only verified unused tables while strictly preserving all 39 active production tables.
- Runs SQLite `VACUUM` to reclaim disk space.

---

## 🚢 5. Deployment Guide: Pilot vs Production

| Parameter | Pilot Deployment | Production Scale Target |
| :--- | :--- | :--- |
| **Worker Count** | **Exactly 1 Uvicorn Worker** | Multi-worker / Kubernetes pods |
| **Database** | SQLite3 (`WAL` mode enabled) | PostgreSQL 16+ |
| **Rate Limiter** | SQLite-backed `login_rate_limits` table | Redis Cluster |
| **WebSockets** | In-memory broadcast manager | Redis Pub/Sub backplane |
| **File Storage** | Local filesystem (`storage/attachments/`) | AWS S3 or MinIO S3-compatible |
