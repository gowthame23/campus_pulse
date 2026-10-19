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
  // Backward compatibility mappings
  STARRED: "Complaint Raised",
  DONE: "Fixed",
  SUBMITTED: "Complaint Raised",
  PENDING: "Complaint Raised",
  ASSIGNED: "Going On",
  IN_PROGRESS: "Going On",
  WAITING_VERIFICATION: "Fixed",
  CLOSED: "Fixed",
  AUTO_CLOSED: "Fixed",
  REOPENED: "Going On",
  AWAITING_ASSIGNMENT: "Complaint Raised",
  WAITING_FOR_PARTS: "Going On",
  PENDING_WARDEN_VERIFICATION: "Fixed",
  ADMIN_REVIEW: "Going On",
};

export const PRESET_PROGRESS_NOTES = {
  INVESTIGATING: "Investigating the issue on site",
  PARTS_ORDERED: "Spare parts ordered",
  TECHNICIAN_DISPATCHED: "Technician dispatched to location",
  WORK_UNDERWAY: "Repair work actively underway",
};
