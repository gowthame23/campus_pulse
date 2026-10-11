# Campus Pulse - System Architecture & Design System

Campus Pulse follows a clean, decoupled 5-tier architecture to ensure strict separation of concerns, testability, and enterprise data safety.

---

## 🏛️ Architectural Layer Breakdown

```text
[ React Frontend (Vite + Tailwind CSS) ]
                   │  HTTP REST (Axios)
                   ▼
       [ FastAPI Router Controllers ]
                   │
                   ▼
     [ Service Layer (Business Rules) ]
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
[ Validation Service ] [ Dependency Service ]
         │                   │
         └─────────┬─────────┘
                   ▼
   [ Repository Persistence Layer ]
                   │
                   ▼
         [ SQLite Database File ]
```

### Layer Responsibilities

1. **Router Controllers (`Backend/api/routers/`):**
   - Handles HTTP requests, parameter extraction, dependency injection (`security.py`), and response serialization schemas (`schemas.py`).
   - Delegates business execution strictly to the Service layer.

2. **Service Layer (`Backend/services/`):**
   - Implements domain workflows (`AuthService`, `DepartmentService`, `LocationService`, `ComplaintService`, `NotificationService`).
   - Performs SLA state calculations (`_enrich_sla`) and automated escalation schedule rules (`apply_automatic_rules`).

3. **Validation & Dependency Services (`validation_service.py`, `dependency_service.py`):**
   - Validates entity relationships before deletion or archive operations.
   - Prevents orphan foreign key records across complaints and user profiles.

4. **Repository Layer (`Backend/storage/`):**
   - Manages SQLite Repository Layer, Database Access, Transactions, and Schema Management (SQLite does not support connection pooling like client-server databases, so we use direct database file connections).

---

## 🎨 Design System & Aesthetics

- **Typography:** Modern clean sans-serif typography (`Inter`, system UI font stack).
- **Color Palette:**
  - **Primary:** Deep slate blue (`var(--primary)`)
  - **Accent Tones:** Emerald (Success), Amber (Warning / SLA Alert), Rose/Red (Danger / Overdue).
- **Glassmorphism & Micro-animations:** Subtraction borders, subtle card hover shadows, rounded pill badges (`rounded-full`), and smooth transitions.
- **Form Controls:** Controlled components with clear error helper hints and disabled state spinners.
- **Typed Destructive Confirmation:** GitHub-style typed `DELETE` text input modal for high-impact entity removals.
