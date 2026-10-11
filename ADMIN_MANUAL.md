# Campus Pulse - Administrator & Manager Operations Manual (v1.0)

This manual outlines operational guidelines for **App Managers** (`app_manager`) and **Administrators** (`administrator`).

---

## ⚡ 1. Role Capabilities Matrix

| Action / Capability | App Manager | Administrator |
|---|:---:|:---:|
| User Account Creation (`Student`, `Coordinator`, `Location In-Charge`) | ✅ | ✅ |
| Admin / App Manager Account Creation | ❌ | ✅ |
| Deactivate / Reactivate User Accounts | ✅ | ✅ |
| Transfer Coordinator Responsibilities & Reassign Complaints | ✅ | ✅ |
| Department & Location Configurations | Read-Only | Full CRUD |
| Data Duplicate Consolidation Wizard (`/admin/cleanup`) | Read-Only | ✅ |
| Database Backup Export & Restore (`GET/POST /settings`) | ❌ | ✅ |
| System Audit Trail Inspection (`/admin/audit`) | ✅ | ✅ |

---

## 👥 2. User Lifecycle & Coordinator Transfers

### 2.1 User Creation & Bulk CSV Import
- **Individual Creation:** Navigate to **Users** $\rightarrow$ **Create User**. Select role, name, email, and department/location mapping.
- **Bulk CSV Import:** Navigate to **Users** $\rightarrow$ **Import CSV**. Download standard template (`/users/template`), populate user rows, and upload.

### 2.2 Safe Coordinator Deactivation Wizard
- If a Coordinator has active complaints assigned, direct deactivation is blocked with HTTP `400`.
- Navigate to **Users** $\rightarrow$ **Transfer Responsibilities**.
- Select the outgoing coordinator and choose a target active coordinator. The system transfers all assigned complaints, adds history logs, notifies the recipient, and deactivates the old account cleanly.

---

## 🧹 3. Data Integrity & Duplicate Consolidation (`/admin/cleanup`)

1. Open **Data Cleanup** from the sidebar menu.
2. The scanner automatically detects identical department or location names.
3. Select the primary record to **Keep** (`radio button`).
4. Click **Resolve & Consolidate**.
5. The system automatically migrates all active/closed complaints and registered user mappings to the kept ID before purging stale duplicate records.

---

## 💾 4. Database Backup Export & Recovery

1. Navigate to **Data Cleanup & Backup** (`/admin/cleanup`).
2. **Export Snapshot:** Click **Export Backup**. A timestamped `.json` file containing all application records and audit logs will be downloaded.
3. **Restore Snapshot:** Click **Restore Backup**, select a valid backup `.json` file, and confirm.

---

## 🛡️ 5. Compliance & System Audit Logs (`/admin/audit`)

- View chronological system audit events.
- Filter logs by Action Type, User ID, or date.
- Click **View State Diff** on any entry to view the exact previous (`old_value`) and updated (`new_value`) JSON payloads.

---

## 📊 6. Admin Dashboard Metrics

The Admin Dashboard provides real-time overview analytics on key metrics:
- **Open Complaints:** Total unresolved complaints currently active.
- **Resolved Complaints:** Total verification-ready or finalized resolved issues.
- **Urgent Cases:** Total issues flagged as "Urgent" priority level.
- **Average Resolution Time:** System-wide average resolution duration in days.
- **Complaints by Department:** Distribution of complaints routed per department.
- **Complaints by Location:** Distribution of complaints registered per block/hostel.

---

## 📢 7. Highlights & Announcements Management

App Managers and Administrators can publish announcements for physical blocks or campus-wide audience:
- **Create:** Open the notice board from the sidebar menu, click **Create Announcement**, populate title, details, and target location.
- **Scope & Expiry:** Limit broadcasts to specific hostels or blocks. Optionally specify an expiry date; the system automatically removes highlights once expired.
- **Permissions:**
  - Wardens can only publish and modify highlights targeting their specific location block.
  - Coordinators can only modify announcements they created.
  - App Managers and Admins possess full system-wide publish and purge access.
