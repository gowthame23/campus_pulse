# Campus Pulse - Campus Complaint & SLA Management System (v1.0)

**Campus Pulse** is a production-grade, multi-role campus complaint resolution and SLA tracking platform. Built with FastAPI (Python) and React (Vite + Tailwind CSS), it provides automated complaint routing, real-time lifecycle tracking, multi-stage SLA breach escalations, duplicate cleanup tools, and complete audit trail capabilities.

---

## 🚀 Key Features

- **Multi-Role Access Control:**
  - 🎓 **Students:** File complaints with optional photo attachments, track resolution timelines, and verify completed work.
  - 👔 **Coordinators:** Manage department queue, update statuses (`In Progress`, `Waiting Verification`), and receive SLA breach warnings.
  - 🛠️ **Location In-Charge (Wardens):** File and verify location-specific issues.
  - 📊 **App Managers:** User account lifecycle management, coordinator transfers, and global complaint oversight.
  - ⚡ **Administrators:** Full system control, department/location configurations, data duplicate consolidation, database backup/restore, and audit logs.

- **Automated SLA Monitoring & Escalations:**
  - Dynamic SLA status computation: 🟢 **On Time**, 🟡 **Due Today**, 🔴 **Overdue**.
  - Multi-stage escalations: past due alert $\rightarrow$ 2+ days overdue escalation to App Manager $\rightarrow$ 4+ days overdue escalation to Administrator.

- **Data Integrity & Safety Safeguards:**
  - GitHub-style typed confirmation for destructive operations (`DELETE`).
  - Safe duplicate consolidation tool migrates active complaints and mapped users before purging duplicate records.
  - Prevents self-deactivation, self-deletion, and deletion of the final active Administrator account.

- **Compliance & Audit Logging:**
  - Automated state diff logging for all backend mutations (`/admin/audit`).
  - Execution duration, user ID, role, and IP address request logging middleware.

---

## 📁 Repository Structure

```text
CampusPulse/
├── Backend/
│   ├── api/
│   │   ├── routers/       # Auth, Users, Departments, Locations, Complaints, Notifications, Settings
│   │   ├── dependencies.py
│   │   ├── security.py    # Authentication & Role Authorization dependencies
│   │   └── main.py        # FastAPI app & Logging Middleware
│   ├── models/            # Domain models (User, Department, Location, Complaint)
│   ├── services/          # Business logic (Auth, Department, Location, Complaint, Notification, Dependency, Validation, Audit)
│   ├── storage/           # SQLite repository & Schema initializer
│   ├── logs/              # Application log output
└── Frontend/
    ├── src/
    │   ├── components/    # Reusable UI components (StatCard, Modal, Badge, Table, Toast, Loader)
    │   ├── pages/         # Route pages for Students, Coordinators, Managers, Admins
    │   ├── services/      # Axios API service integrations
    │   └── routes/        # AppRoutes & ProtectedRoute guards
```

---

## 🛠️ Quick Start

Refer to [INSTALL.md](INSTALL.md) for full installation and environment configuration steps.

1. **Start Backend:**
   ```bash
   cd Backend
   pip install -r requirements.txt
   uvicorn api.main:app --reload --port 8000
   ```

2. **Start Frontend:**
   ```bash
   cd Frontend
   npm install
   npm run dev
   ```

3. **Open Application:**
   Visit `http://localhost:5173` in your browser.

---

## 📖 Documentation Quick Links

- [Installation Guide](INSTALL.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Database Schema](DATABASE_SCHEMA.md)
- [Architecture & Design System](ARCHITECTURE.md)
- [Role Permissions & RBAC Matrix](ROLE_PERMISSIONS.md)
- [Production Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Administrator Operations Manual](ADMIN_MANUAL.md)
- [Workflow Diagrams](docs/WORKFLOW_DIAGRAMS.md)
- [Multi-Tenant Isolation Architecture](docs/TENANT_ISOLATION_ARCHITECTURE.md)
- [Changelog](CHANGELOG.md)
- [Release Notes](RELEASE_NOTES_v1.0.0.md)
