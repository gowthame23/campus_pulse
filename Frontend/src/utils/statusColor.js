import { COMPLAINT_STATUS } from "./constants";

export function getStatusTone(status) {
  const tones = {
    [COMPLAINT_STATUS.STARRED]: "warning", // Amber / Starred ⭐
    [COMPLAINT_STATUS.GOING_ON]: "info",   // Blue / Going On ⏳
    [COMPLAINT_STATUS.DONE]: "success",    // Green / Done ✅
    "Starred": "warning",
    "Going On": "info",
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
  if (s.includes("star") || s.includes("submit") || s.includes("pend")) return "warning";
  if (s.includes("going") || s.includes("progress") || s.includes("assign")) return "info";
  if (s.includes("done") || s.includes("close") || s.includes("resolv")) return "success";
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
    "Starred": t ? t("status.starred", "⭐ Starred") : "⭐ Starred",
    "Going On": t ? t("status.going_on", "⏳ Going On") : "⏳ Going On",
    "Done": t ? t("status.done", "✅ Done") : "✅ Done",
    "Submitted": t ? t("status.starred", "⭐ Starred") : "⭐ Starred",
    "Pending": t ? t("status.starred", "⭐ Starred") : "⭐ Starred",
    "Assigned": t ? t("status.going_on", "⏳ Going On") : "⏳ Going On",
    "In Progress": t ? t("status.going_on", "⏳ Going On") : "⏳ Going On",
    "Waiting for Parts": t ? t("status.going_on", "⏳ Going On") : "⏳ Going On",
    "Waiting for Verification": t ? t("status.done", "✅ Done") : "✅ Done",
    "Pending Warden Verification": t ? t("status.done", "✅ Done") : "✅ Done",
    "Closed": t ? t("status.done", "✅ Done") : "✅ Done",
    "Closed (Auto Closed)": t ? t("status.done", "✅ Done") : "✅ Done",
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
