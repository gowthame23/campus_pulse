import { COMPLAINT_STATUS } from "./constants";

export function getStatusTone(status) {
  const tones = {
    [COMPLAINT_STATUS.SUBMITTED]: "info",
    [COMPLAINT_STATUS.PENDING]: "warning", // Yellow
    [COMPLAINT_STATUS.ASSIGNED]: "info", // Blue
    [COMPLAINT_STATUS.IN_PROGRESS]: "info", // Blue
    [COMPLAINT_STATUS.WAITING_VERIFICATION]: "success", // Green (marked resolved by coordinator)
    [COMPLAINT_STATUS.CLOSED]: "success", // Green (verified fixed)
    [COMPLAINT_STATUS.AUTO_CLOSED]: "success", // Green (verified fixed by auto-close)
    [COMPLAINT_STATUS.REOPENED]: "orange", // Orange
    [COMPLAINT_STATUS.AWAITING_ASSIGNMENT]: "warning",
    [COMPLAINT_STATUS.WAITING_FOR_PARTS]: "amber",
    "Waiting for Parts": "amber",
    [COMPLAINT_STATUS.PENDING_WARDEN_VERIFICATION]: "purple",
    "Pending Warden Verification": "purple",
    [COMPLAINT_STATUS.ADMIN_REVIEW]: "danger",
    "Admin Review": "danger",
  };
  if (tones[status]) return tones[status];
  const s = String(status || "").toLowerCase();
  if (s.includes("warden")) return "purple";
  if (s.includes("parts")) return "amber";
  if (s.includes("admin review")) return "danger";
  return "default";
}

export function getSlaTone(slaStatus) {
  if (!slaStatus) return "default";
  const s = String(slaStatus).toLowerCase();
  if (s.includes("on time")) return "success";
  if (s.includes("due today")) return "warning";
  if (s.includes("overdue") || s.includes("breached") || s.includes("late")) return "danger";
  return "default";
}

export function getPriorityTone(priority) {
  if (!priority) return "default";
  const p = priority.toLowerCase();
  if (p === "critical") return "danger";
  if (p === "high") return "warning";
  if (p === "medium") return "info";
  if (p === "low") return "default";
  return "default";
}
