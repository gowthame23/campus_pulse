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

# Team Accept Queue Deadlines (hours before auto-assigning to least-loaded coordinator)
ACCEPT_DEADLINE_HOURS = {
    "Critical": 0.5,
    "High": 2,
    "Medium": 4,
    "Low": 8,
}

# SLA Reminders (proactive alerts to coordinator at fractions of SLA window)
SLA_REMINDER_FRACTIONS = (0.5, 0.9)

# Maximum Blocked Time (alert warden and app manager if blocked past this)
MAX_BLOCKED_HOURS = 72

# Complaint Lifecycle Statuses
STATUS_SUBMITTED = "Submitted"                      # Filed, unassigned or in team Accept queue
STATUS_ASSIGNED = "Assigned"                        # Assigned to single coordinator, not yet started
STATUS_IN_PROGRESS = "In Progress"                  # Coordinator accepted / started work
STATUS_BLOCKED = "Waiting for Parts"                # Coordinator blocked with reason & expected date
STATUS_PENDING_WARDEN = "Pending Warden Verification"  # Fixed; awaiting in-person warden sign-off
STATUS_WAITING_STUDENT = "Waiting for Verification" # Fixed/warden-verified; awaiting student sign-off
STATUS_REOPENED = "Reopened"                        # Student disputed fix; back to coordinator
STATUS_ADMIN_REVIEW = "Admin Review"                # Reopened >= 3 times; escalated to administrator
STATUS_CLOSED = "Closed"                            # Verified and closed
STATUS_AUTO_CLOSED = "Closed (Auto Closed)"         # Student inactive 48h after resolution
STATUS_REJECTED = "Rejected"                        # Rejected
STATUS_CANCELLED = "Cancelled"                      # Cancelled by submitter

# Legacy status compatibility: old 'Resolved' rows are treated as 'Waiting for Verification'
STATUS_LEGACY_RESOLVED = "Resolved"

# Status Categories
INACTIVE_STATUSES = (
    STATUS_LEGACY_RESOLVED,
    STATUS_WAITING_STUDENT,
    STATUS_PENDING_WARDEN,
    STATUS_CLOSED,
    STATUS_AUTO_CLOSED,
    "Auto-Closed",
    STATUS_REJECTED,
    STATUS_CANCELLED,
)

TERMINAL_STATUSES = (
    STATUS_CLOSED,
    STATUS_AUTO_CLOSED,
    "Auto-Closed",
    STATUS_REJECTED,
    STATUS_CANCELLED,
)

# Statuses where the SLA countdown clock is actively ticking (blocked does NOT pause clock)
SLA_ACTIVE_STATUSES = (
    STATUS_SUBMITTED,
    STATUS_ASSIGNED,
    STATUS_IN_PROGRESS,
    STATUS_BLOCKED,
    STATUS_REOPENED,
)

# Inactivity and Auto-Close Parameters
AUTO_CLOSE_HOURS = 48
AUTO_CLOSE_REMINDER_HOURS = 24
MAX_REOPENS = 3
SPOT_CHECK_RATE = 0.10

# Roles
ROLE_STUDENT = "student"
ROLE_COORDINATOR = "coordinator"
ROLE_WARDEN = "location_in_charge"
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
    "student": ROLE_STUDENT,
    "super_admin": ROLE_SUPER_ADMIN,
    "supervisor": ROLE_APP_MANAGER,
}

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
