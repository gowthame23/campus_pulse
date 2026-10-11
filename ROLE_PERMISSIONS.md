# CampusPulse — Role Permission Matrix

> **How to read this document:**
> - ✅ = Allowed
> - ❌ = Denied (Frontend hides the action + Backend returns 403)
> - 🔒 = Restricted (only own data / own assigned items)
> - ⚠️ = Partial (allowed with conditions, see notes)

---

## User Roles

| Role | Code | Description |
|---|---|---|
| **Student** | `student` | Campus resident — can raise and track own complaints |
| **Coordinator** | `coordinator` | Department staff — manages complaints assigned to them |
| **Location In-Charge (Warden)** | `location_in_charge` | Hostel/block warden — oversees location-specific issues |
| **App Manager** | `app_manager` | Platform operations manager — broad system access |
| **Administrator** | `administrator` | Full system control |

---

## Module 1 — Complaints

| Action | Student | Coordinator | Warden | App Manager | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| Create Complaint | ✅ | ❌ | ✅ | ❌ | ✅ |
| View Own Complaints | ✅ | ✅ | ✅ | ✅ | ✅ |
| View Community Complaints (same location) | ✅ | N/A | N/A | ✅ | ✅ |
| View All Complaints | ❌ | 🔒 Dept only | 🔒 Location only | ✅ | ✅ |
| Assign Complaint | ❌ | ✅ | ❌ | ✅ | ✅ |
| Update Status (Assigned/In Progress) | ❌ | 🔒 Own only | ❌ | ✅ | ✅ |
| Resolve Complaint | ❌ | 🔒 Own only | ❌ | ✅ | ✅ |
| Verify Fix | 🔒 Own only | ❌ | 🔒 Location only | ❌ | ❌ |
| Reopen Complaint | 🔒 Own only | ❌ | 🔒 Location only | ❌ | ❌ |
| Change Priority | ❌ | 🔒 Own dept | 🔒 Own location | ✅ | ✅ |
| Upload Attachment | 🔒 Own only | 🔒 Assigned only | 🔒 Location only | ✅ | ✅ |
| Add Internal Comment | ❌ | ✅ | ✅ | ✅ | ✅ |
| Add Public Comment | ✅ | ✅ | ✅ | ✅ | ✅ |
| View Internal Comments | ❌ | ✅ | ✅ | ✅ | ✅ |
| Escalate Complaint | ✅ | ✅ | ✅ | ✅ | ✅ |
| Archive Complaint | ❌ | ❌ | ❌ | ✅ | ✅ |
| Delete Complaint | ❌ | ❌ | ❌ | ❌ | ✅ (blocked by policy) |
| Export Complaints CSV | ✅ | ✅ | ✅ | ✅ | ✅ |
| View Analytics | ❌ | ❌ | ❌ | ✅ | ✅ |
| View Unassigned Complaints | ❌ | ❌ | ❌ | ✅ | ✅ |
| Mark "Also Affected" | ✅ | ❌ | ❌ | ❌ | ❌ |

**Backend Enforcement:**
- `POST /complaints` — `require_roles(Student.ROLE)` + coordinator/warden allowed via visibility
- `POST /complaints/{id}/assign` — `require_roles(Coordinator, AppManager, Administrator)`
- `PATCH /complaints/{id}/status` — `require_roles(Coordinator, AppManager, Administrator)` + ownership check
- `POST /complaints/{id}/resolve` — `require_roles(Coordinator, AppManager, Administrator)` + ownership check
- `POST /complaints/{id}/verify` — `require_roles(Student, LocationInCharge)` + `can_verify()` check
- `DELETE /complaints/{id}` — `require_roles(Administrator)` + permanently blocked

---

## Module 2 — Resource Booking

| Action | Student | Coordinator | Warden | App Manager | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| Browse Resources | ✅ | ✅ | ✅ | ✅ | ✅ |
| View Resource Detail | ✅ | ✅ | ✅ | ✅ | ✅ |
| View Booking Calendar | ✅ | ✅ | ✅ | ✅ | ✅ |
| Create Booking | ✅ | ✅ | ✅ | ✅ | ✅ |
| Cancel Own Booking | ✅ | ✅ | ✅ | ✅ | ✅ |
| Approve Booking | ❌ | ❌ | ❌ | ✅ | ✅ |
| Reject Booking | ❌ | ❌ | ❌ | ✅ | ✅ |
| Check-In Booking | ✅ | ✅ | ✅ | ✅ | ✅ |
| Create/Edit Resource | ❌ | ❌ | ❌ | ✅ | ✅ |
| Delete Resource | ❌ | ❌ | ❌ | ✅ | ✅ |
| Set Resource Schedule | ❌ | ❌ | ❌ | ✅ | ✅ |

**Business Rules Enforced:**
- Double booking prevented — `check_conflict()` returns 400 if overlapping Approved/Pending booking exists
- Booking outside operating hours rejected
- Resource capacity enforced — participants cannot exceed capacity
- Cancelled/Expired bookings do not block new bookings

---

## Module 3 — Visitor Management

| Action | Student | Coordinator | Warden | App Manager | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| Submit Visit Request | ✅ | ✅ | ✅ | ✅ | ✅ |
| View Own Requests | ✅ | ✅ | ✅ | ✅ | ✅ |
| View All Requests | ❌ | ❌ | ✅ | ✅ | ✅ |
| Approve/Reject Request | ❌ | ❌ | ✅ | ✅ | ✅ |
| Gate Check-In / Out | ❌ | ❌ | ✅ | ✅ | ✅ |
| Blacklist Visitor | ❌ | ❌ | ❌ | ✅ | ✅ |
| Remove from Blacklist | ❌ | ❌ | ❌ | ❌ | ✅ |
| View Blacklist | ❌ | ❌ | ✅ | ✅ | ✅ |
| View Dashboard Metrics | ❌ | ❌ | ✅ | ✅ | ✅ |

---

## Module 4 — Work Orders (Maintenance)

| Action | Student | Coordinator | Warden | App Manager | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| View Work Orders | ❌ | ✅ | ✅ | ✅ | ✅ |
| Create Work Order | ❌ | ✅ | ✅ | ✅ | ✅ |
| Update Work Order | ❌ | 🔒 Assigned | ✅ | ✅ | ✅ |
| Complete Work Order | ❌ | ✅ | ✅ | ✅ | ✅ |
| Verify & Close | ❌ | ✅ | ✅ | ✅ | ✅ |
| Delete Work Order | ❌ | ❌ | ❌ | ✅ | ✅ |
| Export Work Orders | ❌ | ✅ | ✅ | ✅ | ✅ |

---

## Module 5 — Asset Management

| Action | Student | Coordinator | Warden | App Manager | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| View Assets | ❌ | ✅ | ✅ | ✅ | ✅ |
| Register Asset | ❌ | ❌ | ❌ | ✅ | ✅ |
| Assign Asset | ❌ | ❌ | ❌ | ✅ | ✅ |
| Transfer Asset | ❌ | ❌ | ❌ | ✅ | ✅ |
| Dispose Asset | ❌ | ❌ | ❌ | ✅ | ✅ |
| View Maintenance Logs | ❌ | ✅ | ✅ | ✅ | ✅ |
| Log Maintenance | ❌ | ❌ | ❌ | ✅ | ✅ |

---

## Module 6 — Lost & Found

| Action | Student | Coordinator | Warden | App Manager | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| Report Lost/Found Item | ✅ | ✅ | ✅ | ✅ | ✅ |
| View Public Gallery | ✅ | ✅ | ✅ | ✅ | ✅ |
| Submit Claim | ✅ | ✅ | ✅ | ✅ | ✅ |
| Approve Claim | ❌ | ❌ | ✅ | ✅ | ✅ |
| Mark Item Returned | ❌ | ❌ | ✅ | ✅ | ✅ |
| Run AI Match | ✅ | ✅ | ✅ | ✅ | ✅ |

---

## Module 7 — Announcements

| Action | Student | Coordinator | Warden | App Manager | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| View Announcements | ✅ | ✅ | ✅ | ✅ | ✅ |
| Create Announcement | ❌ | ❌ | ✅ | ✅ | ✅ |
| Edit/Delete Announcement | ❌ | ❌ | 🔒 Own only | ✅ | ✅ |
| Pin Announcement | ❌ | ❌ | ❌ | ✅ | ✅ |

---

## Module 8 — Analytics

| Action | Student | Coordinator | Warden | App Manager | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| View Complaint Analytics | ❌ | ❌ | ❌ | ✅ | ✅ |
| View Coordinator Rankings | ❌ | ❌ | ❌ | ✅ | ✅ |
| View Hostel Density | ❌ | ❌ | ❌ | ✅ | ✅ |
| Export Analytics CSV | ❌ | ❌ | ❌ | ✅ | ✅ |
| View SLA Report | ❌ | ❌ | ❌ | ✅ | ✅ |

---

## Module 9 — User Management

| Action | Student | Coordinator | Warden | App Manager | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| View Own Profile | ✅ | ✅ | ✅ | ✅ | ✅ |
| Edit Own Profile | ✅ | ✅ | ✅ | ✅ | ✅ |
| Change Own Password | ✅ | ✅ | ✅ | ✅ | ✅ |
| View All Users | ❌ | ❌ | ❌ | ✅ | ✅ |
| Create User | ❌ | ❌ | ❌ | ✅ | ✅ |
| Edit Any User | ❌ | ❌ | ❌ | ✅ | ✅ |
| Deactivate User | ❌ | ❌ | ❌ | ✅ | ✅ |
| Delete User | ❌ | ❌ | ❌ | ❌ | ✅ |
| Reset Another User's Password | ❌ | ❌ | ❌ | ✅ | ✅ |

---

## Module 10 — System Administration

| Action | Student | Coordinator | Warden | App Manager | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| View Audit Log | ❌ | ❌ | ❌ | ✅ | ✅ |
| View System Settings | ❌ | ❌ | ❌ | ✅ | ✅ |
| Modify System Settings | ❌ | ❌ | ❌ | ✅ | ✅ |
| Create/Restore Backup | ❌ | ❌ | ❌ | ✅ | ✅ |
| Access Security Center | ❌ | ❌ | ❌ | ✅ | ✅ |
| Configure Features | ❌ | ❌ | ❌ | ✅ | ✅ |
| Manage Departments | ❌ | ❌ | ❌ | ✅ | ✅ |
| Manage Locations | ❌ | ❌ | ❌ | ✅ | ✅ |
| Access AI Center | ❌ | ❌ | ❌ | ✅ | ✅ |
| Manage Plugins | ❌ | ❌ | ❌ | ✅ | ✅ |
| View Monitoring | ❌ | ❌ | ❌ | ✅ | ✅ |

---

## Frontend + Backend Enforcement Pattern

Every permission is enforced at **two layers**:

```
Frontend (hide UI)    →   Backend (reject API call)
─────────────────────────────────────────────────────
isStaffAdmin check        require_roles(...) dependency
Role-specific buttons     get_current_user() validation
Conditional rendering     _ensure_visible() ownership check
```

**Example — Complaint Analytics:**
- Frontend: `{isStaffAdmin && <AnalyticsSection />}` — students never see the section
- Backend: `Depends(require_roles(Administrator.ROLE, AppManager.ROLE))` — returns 403 even if API is called directly

---

## Reopen Limits

| Setting | Default | Configurable |
|---|---|---|
| Max complaint reopens | 3 | Yes (`max_reopen_count` in Settings) |
| Auto-close after verification timeout | 5 days | Yes (`auto_close_days` in Settings) |
| Session expiry | 8 hours | No (hardcoded) |
| SLA days per department | Per department | Yes (per-department setting) |
