import { COMPLAINT_STATUS } from "./constants";

export function getStatusTone(status) {
  const tones = {
    [COMPLAINT_STATUS.RAISED]: "warning",   // Amber / Complaint Raised 🟡
    [COMPLAINT_STATUS.GOING_ON]: "info",     // Blue / Going On 🔵
    [COMPLAINT_STATUS.FIXED]: "success",     // Green / Fixed 🟢
    "Complaint Raised": "warning",
    "Going On": "info",
    "Fixed": "success",
    "Starred": "warning",
    "Done": "success",
    "Submitted": "warning",
    "Pending": "warning",
    "Assigned": "info",
    "In Progress": "info",
    "Waiting for Parts": "amber",
    "Waiting for Verification": "success",
    "Closed": "success",
    "Closed (Auto Closed)": "success",
    "Cancelled": "default",
    "Rejected": "danger",
  };
  if (tones[status]) return tones[status];
  const s = String(status || "").toLowerCase();
  if (s.includes("raised") || s.includes("star") || s.includes("submit") || s.includes("pend")) return "warning";
  if (s.includes("going") || s.includes("progress") || s.includes("assign")) return "info";
  if (s.includes("fix") || s.includes("done") || s.includes("close") || s.includes("resolv")) return "success";
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

export function getStatusLabel(status, t) {
  if (!status) return "";
  const s = String(status).trim();
  const map = {
    "Complaint Raised": t ? t("status.raised", "🟡 Complaint Raised") : "🟡 Complaint Raised",
    "Going On": t ? t("status.going_on", "🔵 Going On") : "🔵 Going On",
    "Fixed": t ? t("status.fixed", "🟢 Fixed") : "🟢 Fixed",
    "Starred": t ? t("status.raised", "🟡 Complaint Raised") : "🟡 Complaint Raised",
    "Submitted": t ? t("status.raised", "🟡 Complaint Raised") : "🟡 Complaint Raised",
    "Pending": t ? t("status.raised", "🟡 Complaint Raised") : "🟡 Complaint Raised",
    "Assigned": t ? t("status.going_on", "🔵 Going On") : "🔵 Going On",
    "In Progress": t ? t("status.going_on", "🔵 Going On") : "🔵 Going On",
    "Waiting for Parts": t ? t("status.going_on", "🔵 Going On") : "🔵 Going On",
    "Done": t ? t("status.fixed", "🟢 Fixed") : "🟢 Fixed",
    "Waiting for Verification": t ? t("status.fixed", "🟢 Fixed") : "🟢 Fixed",
    "Pending Warden Verification": t ? t("status.fixed", "🟢 Fixed") : "🟢 Fixed",
    "Closed": t ? t("status.fixed", "🟢 Fixed") : "🟢 Fixed",
    "Closed (Auto Closed)": t ? t("status.fixed", "🟢 Fixed") : "🟢 Fixed",
    "Cancelled": t ? t("status.cancelled", "Cancelled") : "Cancelled",
    "Rejected": t ? t("status.rejected", "Rejected") : "Rejected",
  };
  return map[s] || s;
}

export function getPriorityLabel(priority, t) {
  if (!priority) return "";
  if (!t) return priority;
  const p = priority.toLowerCase();
  const map = {
    "critical": t("priorities.critical", "Critical"),
    "high": t("priorities.high", "High"),
    "medium": t("priorities.medium", "Medium"),
    "low": t("priorities.low", "Low"),
  };
  return map[p] || priority;
}
