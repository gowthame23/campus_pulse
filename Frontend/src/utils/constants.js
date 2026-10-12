export const ROLES = {
  STUDENT: "student",
  EMPLOYEE: "employee",
  COORDINATOR: "coordinator",
  LOCATION_IN_CHARGE: "location_in_charge",
  APP_MANAGER: "app_manager",
  ADMINISTRATOR: "administrator",
  SUPER_ADMIN: "super_admin",
};

// Rule 1.1 & 1.3: Canonical User-Facing Display Names
// Admin | App Manager | Coordinator | Employee | Warden | Student (Super Admin platform-level)
export const ROLE_DISPLAY_NAMES = {
  administrator: "Admin",
  admin: "Admin",
  app_manager: "App Manager",
  manager: "App Manager",
  supervisor: "App Manager",
  coordinator: "Coordinator",
  employee: "Employee",
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


export const COMPLAINT_STATUS = {
  SUBMITTED: "Submitted",
  PENDING: "Pending",
  ASSIGNED: "Assigned",
  IN_PROGRESS: "In Progress",
  WAITING_VERIFICATION: "Waiting for Verification",
  CLOSED: "Closed",
  AUTO_CLOSED: "Closed (Auto Closed)",
  REOPENED: "Reopened",
  AWAITING_ASSIGNMENT: "Awaiting Coordinator Assignment",
  WAITING_FOR_PARTS: "Waiting for Parts",
  PENDING_WARDEN_VERIFICATION: "Pending Warden Verification",
  ADMIN_REVIEW: "Admin Review",
};

export const PRESET_PROGRESS_NOTES = {
  INVESTIGATING: "Investigating the issue on site",
  PARTS_ORDERED: "Spare parts ordered",
  TECHNICIAN_DISPATCHED: "Technician dispatched to location",
  WORK_UNDERWAY: "Repair work actively underway",
};
