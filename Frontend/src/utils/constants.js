export const ROLES = {
  STUDENT: "student",
  COORDINATOR: "coordinator",
  LOCATION_IN_CHARGE: "location_in_charge",
  APP_MANAGER: "app_manager",
  ADMINISTRATOR: "administrator",
  SUPER_ADMIN: "super_admin",
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
