# Campus Pulse — End-to-End Workflows, State Machines & Execution Sequences

> **Document Type:** Core Workflows Specification & Sequence Diagrams  
> **Repository:** Campus Pulse (`CampusPulse_co`)  
> **Status:** Ground-Truth Verified against Source Code  

---

## 1. Complaint Lifecycle State Machine

The complaint state machine defines all permitted states, actors, and transition preconditions implemented in [`Backend/services/complaint_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/complaint_service.py) and [`Backend/models/complaint.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/models/complaint.py).

```mermaid
stateDiagram-v2
    [*] --> Submitted : Student / Warden Creates
    Submitted --> Assigned : Routing Engine / Admin Assigns
    Assigned --> In_Progress : Coordinator Takes Responsibility
    In_Progress --> Resolved : Coordinator Completes (Proof Required)
    Resolved --> Waiting_for_Verification : System Starts 48h Window
    Waiting_for_Verification --> Closed : Student Approves
    Waiting_for_Verification --> Closed_Auto : 48h Timer Expires (Scheduler)
    Waiting_for_Verification --> Reopened : Student Rejects (Max 3x)
    Reopened --> In_Progress : Coordinator Reassesses
    Submitted --> Rejected : Admin / Warden Rejects Invalid Issue
    Assigned --> Rejected : Coordinator Rejects Invalid Issue
    Closed --> [*]
    Closed_Auto --> [*]
    Rejected --> [*]
```

---

### Step-by-Step Transition Analysis

| From State | To State | Initiating Actor | Endpoint / Function | Preconditions & Validation Rules | Database Mutations | Notifications Dispatched |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `[*]` | `Submitted` | Student, Warden | `POST /complaints` | Valid location & dept; title min 5 chars; desc min 10 chars; hostel residency match | `complaints` INSERT; `attachments` INSERT | Student confirmation; location resident alert (if public) |
| `Submitted` | `Assigned` | System / Admin | `assign_work()` | Coordinator active in department/location assignment table | `complaints.assigned_to`, `complaints.status = 'Assigned'` | Assigned Coordinator alerted |
| `Assigned` | `In Progress` | Coordinator | `PUT /complaints/:id/status` | Current status is `Assigned`; caller is assigned staff or admin | `complaints.status = 'In Progress'`, `updated_at` | Complainant Student alerted |
| `In Progress` | `Resolved` / `Waiting for Verification` | Coordinator, Staff | `PUT /complaints/:id/resolve` | Current status is `In Progress`; must provide "After Repair" image OR resolution notes | `complaints.status = 'Waiting for Verification'`, `resolved_at`, `verification_due_at` | Student alerted with verification action |
| `Waiting for Verification` | `Closed` | Student Author | `PUT /complaints/:id/verify` | Current status is `Waiting for Verification`; caller is complaint creator | `complaints.status = 'Closed'`, `closed_at`, `verification_reports` | Coordinator & Student closure confirmation |
| `Waiting for Verification` | `Closed (Auto Closed)` | Background Daemon | `apply_automatic_rules()` | `datetime.utcnow() > verification_due_at` (48 hours elapsed) | `complaints.status = 'Closed (Auto Closed)'`, `closed_at` | System event logged; student and staff notified |
| `Waiting for Verification` | `Reopened` | Student Author | `POST /complaints/:id/reopen` | Current status is `Waiting for Verification`; `reopen_count < max_reopen_count` (3) | `complaints.status = 'Reopened'`, `reopen_count += 1` | Coordinator alerted; if `reopen_count >= 2`, Admin alerted |
| `Submitted` / `Assigned` | `Rejected` | Admin, Warden, Coord | `PUT /complaints/:id/status` | Valid rejection reason entered; caller has authority | `complaints.status = 'Rejected'`, `rejection_reason` | Student alerted with rejection reason |

---

## 2. Multi-Location & Coordinator Routing Sequence

This workflow traces how a newly submitted complaint is routed to the appropriate department coordinator across decentralized campus locations.

```mermaid
sequenceDiagram
    autonumber
    actor Student as Student
    participant Router as API Router (complaints.py)
    participant Svc as ComplaintService
    participant Auth as AuthService
    participant DB as SQLite (campus_pulse.db)
    participant Notif as NotificationService
    actor Staff as Coordinator / Warden

    Student->>Router: POST /complaints (location_id, department_id, description)
    Router->>Svc: create_complaint(user, location_id, department_id, ...)
    Svc->>Auth: get_location(location_id) & get_department(department_id)
    Auth-->>Svc: Confirms both active
    
    rect rgb(240, 248, 255)
        Note over Svc,Auth: Routing Engine Evaluation
        Svc->>Auth: list_coordinator_assignments(location_id, department_id)
        alt Coordinator Assigned for Location & Department
            Auth-->>Svc: Returns Coordinator ID (e.g., USR_COORDINATOR)
            Svc->>Svc: Set assigned_to = Coordinator ID, status = 'Assigned'
        else Fallback to Facility Warden
            Svc->>Auth: Check locations.warden_id
            alt Facility Warden Assigned
                Auth-->>Svc: Returns Warden ID (e.g., USR_WARDEN)
                Svc->>Svc: Set assigned_to = Warden ID, status = 'Assigned'
            else Fallback to Unassigned
                Svc->>Svc: Set assigned_to = NULL, status = 'Submitted'
            end
        end
    end

    Svc->>DB: INSERT INTO complaints (...)
    DB-->>Svc: Success
    Svc->>Notif: notify(student_id, "Complaint Submitted")
    opt If Assigned
        Svc->>Notif: assigned(complaint_id, assigned_to)
        Notif->>Staff: In-App / WebSocket Notification
    end
    Svc-->>Router: Returns Complaint Object
    Router-->>Student: 201 Created (JSON Response)
```

---

## 3. SLA Escalation & Background Daemon Workflow

This workflow traces the 300-second periodic scheduler executed by [`Backend/services/scheduler_service.py`](file:///c:/Users/gowth/OneDrive/Desktop/GOWTHAM/CampusPulse/CampusPulse_co/Backend/services/scheduler_service.py).

```mermaid
sequenceDiagram
    autonumber
    participant Daemon as Background Scheduler Thread (300s)
    participant CompSvc as ComplaintService
    participant DB as SQLite Storage
    participant Notif as NotificationService
    actor Admin as App Manager / Admin

    loop Every 300 Seconds
        Daemon->>CompSvc: apply_automatic_rules()
        CompSvc->>DB: SELECT * FROM complaints WHERE status NOT IN ('Closed', 'Rejected')
        DB-->>CompSvc: Returns Active Complaints

        rect rgb(255, 245, 245)
            Note over CompSvc: SLA Breach Evaluation
            loop For Each Active Complaint
                alt Overdue: current_time > sla_deadline
                    CompSvc->>DB: UPDATE complaints SET is_escalated = 1
                    alt Overdue >= 2 Days
                        CompSvc->>Notif: Alert App Manager (Overdue 2+ Days)
                        Notif->>Admin: Priority In-App Alert
                    end
                    alt Overdue >= 4 Days
                        CompSvc->>Notif: Alert Campus Administrator (Critical Delay)
                        Notif->>Admin: Critical Dashboard Banner
                    end
                end
                alt Waiting for Verification Expired (> 48h)
                    CompSvc->>DB: UPDATE complaints SET status = 'Closed (Auto Closed)'
                    CompSvc->>Notif: Notify Student & Staff of Auto-Closure
                end
            end
        end
    end
```

---

## 4. User Account Lifecycle & Session Security Workflow

This workflow traces how user accounts are created, activated via cryptographic tokens, authenticated via PBKDF2, and securely deactivated.

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Administrator
    participant API as FastAPI Backend
    participant AuthSvc as AuthService
    participant Mail as SMTP Transport (email.py)
    actor Student as Student
    participant DB as SQLite Storage

    Admin->>API: POST /users (name, email, role="student")
    API->>AuthSvc: create_user(data)
    AuthSvc->>AuthSvc: Generate Salt & Temp Password Hash
    AuthSvc->>DB: INSERT INTO users (status='Pending', active=0)
    AuthSvc->>AuthSvc: Generate 32-Byte Token (secrets.token_urlsafe)
    AuthSvc->>DB: INSERT INTO activation_tokens (user_id, token, expires_at)
    AuthSvc->>Mail: send_activation_email(email, token)
    Mail-->>Student: Email with Link /activate?token=<token>
    
    Note over Student,API: Account Activation Phase
    Student->>API: POST /auth/activate (token, new_password)
    API->>AuthSvc: activate_account(token, new_password)
    AuthSvc->>DB: SELECT * FROM activation_tokens WHERE token = ?
    AuthSvc->>AuthSvc: Hash new_password with PBKDF2 (100,000 iter)
    AuthSvc->>DB: UPDATE users SET status='Active', active=1, password_hash=?, salt=?
    AuthSvc->>DB: DELETE FROM activation_tokens WHERE token = ?
    API-->>Student: 200 OK (Account Activated)

    Note over Student,API: Authentication & Invalidation
    Student->>API: POST /auth/login (email, new_password)
    API->>AuthSvc: authenticate() & create_session()
    AuthSvc->>DB: INSERT INTO user_sessions (session_token=SHA256(raw_token), user_id)
    API-->>Student: 200 OK (access_token = raw_token)

    opt Administrative Deactivation
        Admin->>API: PUT /users/:id/deactivate
        API->>AuthSvc: deactivate_user(user_id)
        AuthSvc->>DB: UPDATE users SET status='Inactive', active=0
        AuthSvc->>DB: DELETE FROM user_sessions WHERE user_id = ?
        Note over Student,API: All Active Sessions Immediately Revoked
    end
```

---

## 5. Official Announcement Publishing & Access Workflow

This workflow traces circular publishing, RBAC enforcement, dynamic administrator contact retrieval, and mandatory student acknowledgements.

```mermaid
sequenceDiagram
    autonumber
    actor Staff as Admin / App Manager / Warden
    actor Student as Student
    participant Page as AnnouncementPage.jsx
    participant API as announcements.py
    participant DB as SQLite Storage

    Note over Staff: Staff Notice Publishing
    Staff->>Page: Fills Title, Body, Category, Target, ReqAck
    Staff->>API: POST /announcements (JSON + Bearer Token)
    API->>API: require_roles("administrator", "app_manager", "location_in_charge")
    API->>DB: INSERT INTO announcements (...)
    API->>DB: INSERT INTO announcement_targets (...)
    API-->>Staff: 201 Created

    Note over Student: Student Access & Guarding
    Student->>Page: Opens /announcements
    Page->>Page: canCreate = false -> Hides "Compose Notice" button & modal
    Page->>API: GET /announcements/admin-contact
    API->>DB: Query active Administrator in users table
    DB-->>API: Returns USR_ADMIN (admin@example.com)
    API-->>Page: 200 OK { available: true, email: "admin@example.com" }
    Page->>Student: Renders Admin Contact mailto link (Zero Hardcoded Emails)
    
    opt Mandatory Acknowledgement
        Student->>Page: Clicks "Acknowledge Notice"
        Page->>API: PUT /announcements/:id/acknowledge
        API->>DB: INSERT INTO announcement_acknowledgements (announcement_id, user_id)
        API-->>Student: 200 OK (Acknowledged)
    end
```
