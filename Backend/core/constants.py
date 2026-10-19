"""Campus Pulse — Core System Constants

Single source of truth for statuses, priorities, roles, SLA timers, and configuration thresholds.
"""

# Priorities
PRIORITIES = ("Low", "Medium", "High", "Critical")

# SLA Resolution Windows (hours from filing time)
SLA_HOURS = {
    "Critical": 4,
    "High": 24,
    "Medium": 48,
    "Low": 72,
}

# Assign Deadlines (hours before escalation when complaint is awaiting coordinator assignment)
ASSIGN_DEADLINE_HOURS = {
    "Critical": 0.5,
    "High": 2,
    "Medium": 4,
    "Low": 8,
}
ACCEPT_DEADLINE_HOURS = ASSIGN_DEADLINE_HOURS

# SLA Reminders (proactive alerts to coordinator at fractions of SLA window)
SLA_REMINDER_FRACTIONS = (0.5, 0.9)

# Maximum Blocked Time (alert warden and app manager if blocked past this)
MAX_BLOCKED_HOURS = 72

# Complaint Lifecycle Statuses — 3 Canonical States: Complaint Raised, Going On, Fixed
STATUS_RAISED = "Complaint Raised"                  # New / Filed by student
STATUS_GOING_ON = "Going On"                        # In Progress / Work started by coordinator
STATUS_FIXED = "Fixed"                              # Fixed / Work done by coordinator

STATUS_STARRED = STATUS_RAISED
STATUS_DONE = STATUS_FIXED

# Canonical 3 statuses list
CANONICAL_STATUSES = (STATUS_RAISED, STATUS_GOING_ON, STATUS_FIXED)

# Aliases mapped to the 3 canonical statuses
STATUS_SUBMITTED = STATUS_RAISED
STATUS_ASSIGNED = STATUS_GOING_ON
STATUS_IN_PROGRESS = STATUS_GOING_ON
STATUS_BLOCKED = STATUS_GOING_ON
STATUS_PENDING_WARDEN = STATUS_FIXED
STATUS_WAITING_STUDENT = STATUS_FIXED
STATUS_WAITING_VERIFICATION = STATUS_FIXED
STATUS_REOPENED = STATUS_GOING_ON
STATUS_ADMIN_REVIEW = STATUS_GOING_ON
STATUS_CLOSED = STATUS_FIXED
STATUS_AUTO_CLOSED = STATUS_FIXED
STATUS_REJECTED = "Rejected"
STATUS_CANCELLED = "Cancelled"
STATUS_CANCELLATION_REQUESTED = "Cancellation Requested"

# Legacy status compatibility: old 'Resolved' rows are treated as 'Fixed'
STATUS_LEGACY_RESOLVED = STATUS_FIXED

def normalize_status(status: str) -> str:
    """Normalize any legacy or incoming status string to one of the 3 canonical statuses:
    'Complaint Raised', 'Going On', 'Fixed'."""
    if not status:
        return STATUS_RAISED
    s = str(status).strip()
    if s in (STATUS_RAISED, STATUS_GOING_ON, STATUS_FIXED, STATUS_CANCELLED, STATUS_REJECTED):
        return s
    s_lower = s.lower()
    if any(k in s_lower for k in ("raised", "submitted", "pending", "awaiting", "starred", "new")):
        return STATUS_RAISED
    if any(k in s_lower for k in ("fixed", "closed", "auto closed", "resolved", "verified", "done")):
        return STATUS_FIXED
    if "cancel" in s_lower:
        return STATUS_CANCELLED
    if "reject" in s_lower:
        return STATUS_REJECTED
    return STATUS_GOING_ON

# Status Categories
INACTIVE_STATUSES = (
    STATUS_FIXED,
    "Closed",
    "Closed (Auto Closed)",
    "Auto-Closed",
    STATUS_REJECTED,
    STATUS_CANCELLED,
)

TERMINAL_STATUSES = (
    STATUS_FIXED,
    "Closed",
    "Closed (Auto Closed)",
    "Auto-Closed",
    STATUS_REJECTED,
    STATUS_CANCELLED,
)

# Statuses where the SLA countdown clock is actively ticking
SLA_ACTIVE_STATUSES = (
    STATUS_RAISED,
    STATUS_GOING_ON,
)

# Inactivity and Auto-Close Parameters
AUTO_CLOSE_HOURS = 48
AUTO_CLOSE_REMINDER_HOURS = 24
AFFECTED_CONFIRM_AFTER_HOURS = 24       # after this, any affected student may confirm
AFFECTED_PRIORITY_THRESHOLD = 10        # "I am affected" count that raises priority one level
MAX_REOPENS = 3
SPOT_CHECK_RATE = 0.10
PHOTO_SKIP_STREAK_LIMIT = 2

# Preset Progress Note Codes (one-tap for coordinator, localized per viewer language)
PRESET_PROGRESS_NOTES = {
    "PART_ORDERED": "Parts ordered / Waiting for spare parts",
    "COME_BACK_TOMORROW": "Work in progress; will return tomorrow",
    "ROOM_LOCKED": "Room was locked / Student unavailable",
    "NEED_SPECIALIST": "Requires external specialist or tools",
    "INSPECTION_DONE": "Initial inspection completed; repair underway",
    "CLEANUP_PENDING": "Repair finished; testing and cleanup pending",
}

# Roles
ROLE_STUDENT = "student"
ROLE_EMPLOYEE = "employee"
ROLE_COORDINATOR = "coordinator"
ROLE_WARDEN = "location_in_charge"
ROLE_LOCATION_IN_CHARGE = "location_in_charge"
ROLE_APP_MANAGER = "app_manager"
ROLE_ADMINISTRATOR = "administrator"
ROLE_SUPER_ADMIN = "super_admin"

ROLE_ALIASES = {
    "admin": ROLE_ADMINISTRATOR,
    "administrator": ROLE_ADMINISTRATOR,
    "manager": ROLE_APP_MANAGER,
    "app_manager": ROLE_APP_MANAGER,
    "warden": ROLE_WARDEN,
    "location_in_charge": ROLE_WARDEN,
    "coordinator": ROLE_COORDINATOR,
    "employee": ROLE_EMPLOYEE,
    "student": ROLE_STUDENT,
    "super_admin": ROLE_SUPER_ADMIN,
    "supervisor": ROLE_APP_MANAGER,
}

# Rule 1.1 & 1.3: The ONLY role names shown to users anywhere are:
# Admin | App Manager | Coordinator | Employee | Warden | Student (Super Admin platform-level)
ROLE_DISPLAY_NAMES = {
    "administrator": "Admin",
    "admin": "Admin",
    "app_manager": "App Manager",
    "manager": "App Manager",
    "supervisor": "App Manager",
    "coordinator": "Coordinator",
    "employee": "Employee",
    "location_in_charge": "Warden",
    "warden": "Warden",
    "student": "Student",
    "super_admin": "Super Admin",
}


def get_role_display_name(role: str) -> str:
    """Return canonical user-facing display name for a role string."""
    if not role:
        return ""
    clean = str(role).strip().lower()
    return ROLE_DISPLAY_NAMES.get(clean, clean.capitalize())

# Category to Default Priority Map
CATEGORY_PRIORITY_MAP = {
    "electrical hazard": "High",
    "electrical": "Medium",
    "safety hazard": "High",
    "safety": "High",
    "water supply": "High",
    "plumbing": "Medium",
    "no water": "High",
    "medical": "Critical",
    "emergency": "Critical",
    "fire hazard": "Critical",
    "hygiene": "Medium",
    "housekeeping": "Low",
    "internet": "Medium",
    "network": "Medium",
    "carpentry": "Medium",
    "furniture": "Low",
    "civil": "Medium",
    "general": "Medium",
}

# Optional category-level SLA hour overrides
CATEGORY_SLA_OVERRIDES = {}


def get_sla_hours(priority: str, category: str = None) -> float:
    """Returns SLA resolution window in hours for a given priority and optional category override.
    For Critical priority, always uses the shorter of the priority SLA or category override.
    """
    p = normalize_priority(priority)
    base_hours = SLA_HOURS.get(p, 48)
    if category:
        cat_clean = str(category).strip().lower()
        if cat_clean in CATEGORY_SLA_OVERRIDES:
            cat_hours = float(CATEGORY_SLA_OVERRIDES[cat_clean])
            if p == "Critical":
                return min(cat_hours, float(SLA_HOURS["Critical"]))
            return cat_hours
    return float(base_hours)


def normalize_role(role_name: str) -> str:
    """Normalize any role string or alias to the canonical database role string."""
    if not role_name:
        return ""
    clean = str(role_name).strip().lower()
    return ROLE_ALIASES.get(clean, clean)


def normalize_priority(priority: str) -> str:
    """Normalize priority strings like 'Normal', 'Urgent' to standard 4 priorities."""
    if not priority:
        return "Medium"
    p = str(priority).strip().capitalize()
    if p in ("Normal", "Medium"):
        return "Medium"
    if p in ("Urgent", "High"):
        return "High"
    if p == "Critical":
        return "Critical"
    if p == "Low":
        return "Low"
    return "Medium"


# Emergency Constants
EMERGENCY_UNACKNOWLEDGED_ALERT_MINUTES = 10
EMERGENCY_STRIKE_LOCKOUT_DAYS = 30
EMERGENCY_STRIKE_WINDOW_DAYS = 90
EMERGENCY_STRIKE_THRESHOLD = 3
EMERGENCY_OUTCOME_REAL = "real"
EMERGENCY_OUTCOME_MISTAKE = "mistake"
EMERGENCY_OUTCOME_MISUSE = "misuse"

