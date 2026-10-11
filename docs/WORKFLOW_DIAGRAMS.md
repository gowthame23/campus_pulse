# CampusPulse — Workflow & Architecture Diagrams

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT (Browser)                         │
│                                                             │
│   React 18 + Vite  ──  Axios ─────────────────────────────┐│
│   (Port 5173)           JWT Bearer Token                   ││
└────────────────────────────────────────────────────────────┼┘
                                                             │
                         HTTP/REST API                       │
                                                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (Port 8000)                 │
│                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐  │
│  │ CORS + Rate │  │  JWT Session │  │  Request Logger   │  │
│  │  Limiter   │  │  Middleware  │  │  Middleware        │  │
│  └─────────────┘  └──────────────┘  └───────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │             44 API Routers (FastAPI)                │   │
│  │  /complaints  /resources  /visitors  /lost-found    │   │
│  │  /announcements  /work-orders  /assets  /feedback   │   │
│  │  /auth  /users  /departments  /locations  /audit    │   │
│  │  /analytics  /backups  /monitoring  /ai-center ...  │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │             46 Service Classes                       │   │
│  │  ComplaintService  ResourceService  AuthService      │   │
│  │  VisitorService    AuditService     NotificationSvc  │   │
│  │  WorkOrderService  AssetService     FeedbackService  │   │
│  └─────────────────────────────────────────────────────┘   │
│                         │                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         SQLiteRepository / sqlite3                  │   │
│  │         storage/campus_pulse.db                     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Complaint Lifecycle Flow

```mermaid
flowchart TD
    A([Student Logs In]) --> B[Create Complaint]
    B --> C{Dept has Coordinator?}
    C -->|Yes| D[Status: Submitted\nAuto-assigned to Coordinator]
    C -->|No| E[Status: Awaiting Assignment\nApp Manager Notified]
    E --> F[App Manager Assigns Coordinator]
    F --> D
    D --> G[Coordinator Accepts\nStatus: Assigned]
    G --> H[Coordinator Starts Work\nStatus: In Progress]
    H --> I{SLA Exceeded?}
    I -->|Yes, 0 days| J[Notify Coordinator]
    I -->|Yes, 2+ days| K[Escalate to App Manager]
    I -->|Yes, 4+ days| L[Escalate to Administrator]
    H --> M[Coordinator Resolves\nNotes + After-Repair Photos Required]
    M --> N[Status: Waiting Verification]
    N --> O{Student/Warden Verifies}
    O -->|Fixed| P[Status: Closed ✅]
    O -->|Not Fixed| Q{Reopen Count < Max?}
    Q -->|Yes| R[Status: Reopened\nReopen Count ++]
    R --> G
    Q -->|No| S[Reopen Blocked ❌]
    N --> T{Verification Timeout?}
    T -->|Yes, 5 days| U[Auto-Closed by System]
    P --> V[Feedback Submitted]
    P --> W[Audit Log Updated]
    P --> X[Analytics Updated]
```

---

## 3. Resource Booking Flow

```mermaid
flowchart TD
    A([User Logged In]) --> B[Browse Resources]
    B --> C[Select Resource + Time Slot]
    C --> D{Resource Available?}
    D -->|No| E[❌ Cannot Book — Status Error]
    D -->|Yes| F{Time Slot Conflict?}
    F -->|Yes| G[❌ 400 — Booking Conflict]
    F -->|No| H{Approval Required?}
    H -->|No| I[Booking Auto-Approved\nStatus: Approved ✅]
    H -->|Yes| J[Status: Pending\nStaff Notified]
    J --> K{Staff Reviews}
    K -->|Approve| L{Conflict check at approval}
    K -->|Reject| M[Status: Rejected\nReason Recorded]
    L -->|Conflict found| N[Auto-Rejected — Conflict]
    L -->|No conflict| I
    I --> O[User Checks In]
    O --> P[Status: Completed]
    I --> Q{No Show?}
    Q -->|Expired| R[Status: Expired / No Show]
    I --> S[User Cancels]
    S --> T[Status: Cancelled]
```

---

## 4. Visitor Management Flow

```mermaid
flowchart TD
    A([User]) --> B[Submit Visitor Request\nName, Phone, Gov ID, Purpose]
    B --> C{Visitor Blacklisted?}
    C -->|Yes| D[❌ Request Rejected — Blacklisted]
    C -->|No| E[Status: Pending\nWarden/Security Notified]
    E --> F{Staff Reviews}
    F -->|Reject| G[Status: Rejected\nVisitor Notified]
    F -->|Approve| H[Status: Approved\nOTP Gate Pass Generated]
    H --> I[Visitor Arrives at Gate]
    I --> J[Security Scans OTP/QR]
    J --> K{OTP Valid & Not Expired?}
    K -->|No| L[❌ Entry Denied]
    K -->|Yes| M[Check-In Recorded]
    M --> N[Visit in Progress]
    N --> O[Check-Out Recorded]
    O --> P[Visit Completed ✅]
    P --> Q{Security Incident?}
    Q -->|Yes| R[Visitor Blacklisted\nAdmin Notified]
```

---

## 5. Lost & Found Flow

```mermaid
flowchart TD
    A([User]) --> B{Report Type}
    B -->|Lost| C[Report Lost Item\nTitle, Category, Description, Location]
    B -->|Found| D[Report Found Item\nStore Location Noted]
    C --> E[Item Listed in Public Gallery]
    D --> E
    E --> F[AI Match Engine Runs\nCompares Lost vs Found Items]
    F --> G{Match Found?}
    G -->|Yes| H[Both Parties Notified]
    G -->|No| I[Item Stays in Gallery]
    H --> J[Claimant Submits Claim\nReason + Proof Description]
    J --> K[Staff Reviews Claim]
    K -->|Reject| L[Claim Rejected]
    K -->|Approve| M[Status: Ready for Return]
    M --> N[Staff Marks Returned\nConfirm Modal Required]
    N --> O[Status: Returned ✅\nReport Closed]
```

---

## 6. Authentication & Session Flow

```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant F as Frontend (React)
    participant B as Backend (FastAPI)
    participant DB as SQLite DB

    U->>F: Enter email + password
    F->>B: POST /auth/login {email, password}
    B->>DB: Look up user by email
    DB-->>B: User record
    B->>B: bcrypt.verify(password, hash)
    alt Invalid credentials
        B-->>F: 401 Unauthorized
        F-->>U: Show error message
    else Valid credentials
        B->>B: Create session token (token_urlsafe(32))
        B->>B: Store in _sessions dict with timestamp
        B->>DB: Log audit event (Login Success)
        B-->>F: 200 {access_token, user, permissions}
        F->>F: Store token in localStorage
        F-->>U: Redirect to Dashboard
    end

    Note over F,B: Subsequent API calls include Bearer token

    U->>F: Visit protected page
    F->>B: GET /complaints {Authorization: Bearer token}
    B->>B: get_current_user() - lookup token in _sessions
    alt Token not found
        B-->>F: 401 - Invalid or expired token
    else Token found
        B->>B: Check session age < 8 hours
        alt Session expired
            B-->>F: 401 - Session has expired
        else Valid session
            B->>DB: Load user record
            B->>B: Check user.active == True
            B->>B: Check user.first_login policy
            B-->>F: 200 + data
        end
    end
```

---

## 7. Core Entity Relationships (ER Diagram)

```mermaid
erDiagram
    USERS {
        string user_id PK
        string name
        string email
        string role
        string department_id FK
        string location_id FK
        bool active
        bool first_login
    }

    DEPARTMENTS {
        string department_id PK
        string name
        string coordinator_id FK
        int sla_days
        json complaint_types
    }

    LOCATIONS {
        string location_id PK
        string name
        string building
        string block
        int capacity
    }

    COMPLAINTS {
        string complaint_id PK
        string created_by FK
        string location_id FK
        string department_id FK
        string assigned_to FK
        string status
        string priority
        string category
        string visibility_type
        int reopen_count
        bool escalated
        bool archived
        datetime created_at
        datetime resolved_at
    }

    COMPLAINT_COMMENTS {
        string comment_id PK
        string complaint_id FK
        string user_id FK
        string message
        bool is_internal
    }

    RESOURCES {
        string resource_id PK
        string resource_name
        string category
        string building_id FK
        int capacity
        bool booking_required
        bool approval_required
        string status
    }

    RESOURCE_BOOKINGS {
        string booking_id PK
        string resource_id FK
        string booked_by FK
        string booking_date
        string start_time
        string end_time
        int participants
        string status
    }

    VISITOR_REQUESTS {
        string request_id PK
        string requested_by FK
        string visitor_name
        string visitor_phone
        string status
        string otp_code
    }

    LOST_FOUND_ITEMS {
        string item_id PK
        string reported_by FK
        string report_type
        string title
        string category
        string status
    }

    WORK_ORDERS {
        string work_order_id PK
        string complaint_id FK
        string assigned_to FK
        string status
        string priority
    }

    ASSETS {
        string asset_id PK
        string asset_name
        string category_id FK
        string status
        string assigned_to FK
        string location_id FK
    }

    AUDIT_LOGS {
        string audit_id PK
        string performed_by FK
        string module
        string action
        string entity_id
        json old_value
        json new_value
        string status
        datetime created_at
    }

    NOTIFICATIONS {
        string notification_id PK
        string user_id FK
        string message
        bool is_read
        datetime created_at
    }

    USERS ||--o{ COMPLAINTS : "creates"
    USERS ||--o{ COMPLAINTS : "assigned_to"
    DEPARTMENTS ||--o{ COMPLAINTS : "belongs_to"
    LOCATIONS ||--o{ COMPLAINTS : "raised_in"
    COMPLAINTS ||--o{ COMPLAINT_COMMENTS : "has"
    COMPLAINTS ||--o| WORK_ORDERS : "generates"
    RESOURCES ||--o{ RESOURCE_BOOKINGS : "booked_via"
    USERS ||--o{ RESOURCE_BOOKINGS : "books"
    USERS ||--o{ VISITOR_REQUESTS : "submits"
    USERS ||--o{ LOST_FOUND_ITEMS : "reports"
    USERS ||--o{ AUDIT_LOGS : "triggers"
    USERS ||--o{ NOTIFICATIONS : "receives"
    ASSETS ||--o| USERS : "assigned_to"
    ASSETS ||--o| LOCATIONS : "located_at"
```

---

## 8. Deployment Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 Production Deployment                    │
│                                                         │
│  ┌──────────────┐     ┌──────────────────────────────┐  │
│  │   Nginx      │────▶│  FastAPI (Uvicorn workers)   │  │
│  │   :80/:443   │     │  127.0.0.1:8000              │  │
│  │   Static     │     │  api/main.py                 │  │
│  │   + Reverse  │     └──────────────┬───────────────┘  │
│  │   Proxy      │                    │                   │
│  └──────┬───────┘                    ▼                   │
│         │              ┌─────────────────────────────┐  │
│         │              │  SQLite Database             │  │
│         │              │  storage/campus_pulse.db     │  │
│         │              └─────────────────────────────┘  │
│         ▼                                               │
│  ┌──────────────┐                                       │
│  │  React Build │                                       │
│  │  dist/       │                                       │
│  └──────────────┘                                       │
└─────────────────────────────────────────────────────────┘

Development:
  Terminal 1: cd Backend && python run_api.py  → :8000
  Terminal 2: cd Frontend && npm run dev       → :5173
```
