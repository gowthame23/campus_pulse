# Campus Pulse - Database Schema Documentation

Campus Pulse uses SQLite as its relational persistence store (managed via `SQLiteRepository`).

---

## 🗄️ Entity Tables

### 1. `users` Table

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `user_id` | TEXT | PRIMARY KEY | Unique user identifier (`USR-XXXXXXXX`) |
| `name` | TEXT | NOT NULL | User's full name |
| `email` | TEXT | NOT NULL, UNIQUE | User email address |
| `password` | TEXT | NOT NULL | Hashed password string |
| `role` | TEXT | NOT NULL | `student`, `coordinator`, `location_in_charge`, `app_manager`, `administrator` |
| `first_login` | INTEGER | NOT NULL | Boolean flag (`1` = password change required) |
| `active` | INTEGER | NOT NULL | Account state (`1` = Active, `0` = Deactivated) |
| `department_id` | TEXT | NULLABLE | Foreign reference to `departments.department_id` |
| `location_id` | TEXT | NULLABLE | Foreign reference to `locations.location_id` |
| `created_at` | TEXT | NOT NULL | ISO date string (`YYYY-MM-DD HH:MM:SS`) |

---

### 2. `departments` Table

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `department_id` | TEXT | PRIMARY KEY | Department identifier (`DEPT_X`) |
| `name` | TEXT | NOT NULL | Department name |
| `sla_days` | INTEGER | NOT NULL | Max resolution SLA days |
| `complaint_types` | TEXT | NOT NULL | JSON string array of complaint categories |
| `coordinator_id` | TEXT | NULLABLE | Foreign reference to assigned coordinator user |
| `active` | INTEGER | NOT NULL DEFAULT 1 | Active state flag |
| `archived` | INTEGER | NOT NULL DEFAULT 0 | Archive state flag (`1` = Archived) |

---

### 3. `locations` Table

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `location_id` | TEXT | PRIMARY KEY | Location identifier (`LOC_X`) |
| `name` | TEXT | NOT NULL | Physical campus location / block name |
| `in_charge_id` | TEXT | NULLABLE | Foreign reference to location in-charge user |
| `active` | INTEGER | NOT NULL DEFAULT 1 | Active state flag |
| `archived` | INTEGER | NOT NULL DEFAULT 0 | Archive state flag |

---

### 4. `complaints` Table

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `complaint_id` | TEXT | PRIMARY KEY | Unique complaint identifier (`CMP-XXXXXXXX`) |
| `created_by` | TEXT | NOT NULL | User ID of reporter |
| `creator_role` | TEXT | NOT NULL | Role of reporter |
| `location_id` | TEXT | NOT NULL | Foreign reference to `locations.location_id` |
| `department_id` | TEXT | NOT NULL | Foreign reference to `departments.department_id` |
| `complaint_type` | TEXT | NOT NULL | Complaint category name |
| `description` | TEXT | NOT NULL | Full problem description |
| `attachment_url` | TEXT | NULLABLE | Photo / document attachment URL |
| `status` | TEXT | NOT NULL | `Submitted`, `Assigned`, `In Progress`, `Waiting for Verification`, `Closed`, `Closed (Auto Closed)`, `Reopened`, `Awaiting Coordinator Assignment` |
| `assigned_to` | TEXT | NULLABLE | Foreign reference to assigned coordinator |
| `created_at` | TEXT | NOT NULL | Filing date string |
| `updated_at` | TEXT | NOT NULL | Last status update timestamp |
| `resolved_at` | TEXT | NULLABLE | Work completion timestamp |
| `verification_due_at` | TEXT | NULLABLE | 5-day auto-close verification deadline |
| `reopen_count` | INTEGER | NOT NULL DEFAULT 0 | Counter for reopen events |
| `auto_closed` | INTEGER | NOT NULL DEFAULT 0 | Boolean flag for auto-close |
| `escalated` | INTEGER | NOT NULL DEFAULT 0 | Boolean flag for App Manager SLA escalation |
| `admin_notified` | INTEGER | NOT NULL DEFAULT 0 | Boolean flag for Administrator SLA escalation |
| `resolution_notes` | TEXT | NULLABLE | Notes left by coordinator upon resolution |
| `verification_reports` | TEXT | NOT NULL | JSON string array of verification feedback |
| `history` | TEXT | NOT NULL | JSON string array of timeline events |
| `archived` | INTEGER | NOT NULL DEFAULT 0 | Archive state flag |
| `priority` | TEXT | NOT NULL DEFAULT 'Medium' | Alert Priority level (`Low`, `Medium`, `High`, `Urgent`) |
| `category` | TEXT | NULLABLE | Isolated category field |
| `visibility_type` | TEXT | NOT NULL DEFAULT 'Private' | Privacy scope (`Private`, `Community`) |

---

### 5. `audit_logs` Table

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `log_id` | TEXT | PRIMARY KEY | Unique log identifier (`AUD-XXXXXXXX`) |
| `user_id` | TEXT | NOT NULL | Actor user ID |
| `action` | TEXT | NOT NULL | Action title (`Update Department`, `Delete User`, etc.) |
| `target_id` | TEXT | NOT NULL | Target entity ID |
| `details` | TEXT | NULLABLE | JSON string representing audit states |
| `created_at` | TEXT | NOT NULL | Timestamp string |

---

### 6. `comments` Table

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `comment_id` | TEXT | PRIMARY KEY | Unique comment ID (`CMT-XXXXXXXX`) |
| `complaint_id` | TEXT | NOT NULL | Target complaint reference |
| `user_id` | TEXT | NOT NULL | Creator user reference |
| `message` | TEXT | NOT NULL | Comment message contents |
| `created_at` | TEXT | NOT NULL | Date string |

---

### 7. `highlights` Table

| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `highlight_id` | TEXT | PRIMARY KEY | Unique announcement ID (`HLT-XXXXXXXX`) |
| `title` | TEXT | NOT NULL | Alert summary title |
| `description` | TEXT | NOT NULL | Alert details |
| `target_location` | TEXT | NULLABLE | Location restriction ID |
| `priority` | TEXT | NOT NULL | Highlight priority level (`Low`, `Medium`, `High`, `Urgent`) |
| `created_by` | TEXT | NOT NULL | Publisher user reference |
| `created_at` | TEXT | NOT NULL | Publishing date string |
| `expiry_date` | TEXT | NULLABLE | Event expiration deadline |
