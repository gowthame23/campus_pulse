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
  };
  return tones[status] || "default";
}

export function getSlaTone(slaStatus) {
  if (!slaStatus) return "default";
  if (slaStatus.includes("On Time")) return "success";
  if (slaStatus.includes("Due Today")) return "warning";
  if (slaStatus.includes("Overdue")) return "danger";
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
