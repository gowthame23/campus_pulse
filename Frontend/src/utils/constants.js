export const ROLES = {
  STUDENT: "student",
  COORDINATOR: "coordinator",
  LOCATION_IN_CHARGE: "location_in_charge",
  APP_MANAGER: "app_manager",
  ADMINISTRATOR: "administrator",
  SUPER_ADMIN: "super_admin",
};

// Canonical User-Facing Display Names
// Admin | App Manager | Coordinator | Warden | Student (Super Admin platform-level)
export const ROLE_DISPLAY_NAMES = {
  administrator: "Admin",
  admin: "Admin",
  app_manager: "App Manager",
  manager: "App Manager",
  supervisor: "App Manager",
  coordinator: "Coordinator",
  location_in_charge: "Warden",
  warden: "Warden",
  student: "Student",
  super_admin: "Super Admin",
};

export const getRoleDisplayName = (role) => {
  if (!role) return "";
  const clean = String(role).trim().toLowerCase();
  return ROLE_DISPLAY_NAMES[clean] || role;
};

// 3 Canonical Complaint Lifecycle Statuses: Complaint Raised, Going On, Fixed
export const COMPLAINT_STATUS = {
  RAISED: "Complaint Raised",
  GOING_ON: "Going On",
  FIXED: "Fixed",
  // Standard Backend API Statuses & Mappings
  SUBMITTED: "Submitted",
  PENDING: "Pending",
  ASSIGNED: "Assigned",
  IN_PROGRESS: "In Progress",
  WAITING_FOR_PARTS: "Waiting for Parts",
  WAITING_VERIFICATION: "Waiting for Verification",
  PENDING_WARDEN_VERIFICATION: "Pending Warden Verification",
  RESOLVED: "Resolved",
  CLOSED: "Closed",
  AUTO_CLOSED: "Auto Closed",
  REOPENED: "Reopened",
  ADMIN_REVIEW: "Admin Review",
  CANCELLED: "Cancelled",
  AWAITING_ASSIGNMENT: "Awaiting Assignment",
  STARRED: "Complaint Raised",
  DONE: "Fixed",
};

export const PRESET_PROGRESS_NOTES = {
  INVESTIGATING: "Investigating the issue on site",
  PARTS_ORDERED: "Spare parts ordered",
  TECHNICIAN_DISPATCHED: "Technician dispatched to location",
  WORK_UNDERWAY: "Repair work actively underway",
};
