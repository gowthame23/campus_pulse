import { useState, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  FileText,
  ArrowRight,
  Megaphone,
  Bell,
  Clock,
  Plus,
  CheckCircle2,
  AlertCircle,
  MapPin,
  ChevronRight,
  RotateCcw,
  ShieldAlert,
  Check,
  Search,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import ActionPill from "../../components/ActionPill.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import StatCard from "../../components/StatCard.jsx";
import Badge from "../../components/Badge.jsx";
import Card from "../../components/Card.jsx";
import Modal from "../../components/Modal.jsx";
import Toast from "../../components/Toast.jsx";
import EmergencyButton from "../../components/EmergencyButton.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { useLanguage } from "../../context/LanguageContext.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { complaintService } from "../../services/complaintService.js";
import { announcementService } from "../../services/announcementService.js";
import { notificationService } from "../../services/notificationService.js";
import { locationService } from "../../services/locationService.js";
import { COMPLAINT_STATUS } from "../../utils/constants.js";
import { formatDate } from "../../utils/dateFormatter.js";
import { getStatusTone, getPriorityTone } from "../../utils/statusColor.js";

export const getStudentStageText = (complaint) => {
  const status = complaint?.status;
  if (!status) return "";
  if (status === "Submitted" || status === "Pending") {
    return "Waiting for coordinator to accept";
  }
  if (["Assigned", "In Progress", "Waiting for Parts", "Work Started"].includes(status)) {
    return status === "Waiting for Parts" ? "Coordinator waiting for parts" : "Coordinator working on it";
  }
  if (status === "Pending Warden Verification") {
    return "Warden inspecting the fix";
  }
  if (status === "Waiting for Verification") {
    let hoursLeft = "48h";
    if (complaint.resolved_at) {
      const deadline = new Date(complaint.resolved_at).getTime() + 48 * 3600 * 1000;
      const diffMs = deadline - Date.now();
      if (diffMs > 0) {
        const hours = Math.ceil(diffMs / (3600 * 1000));
        hoursLeft = `${hours}h`;
      } else {
        hoursLeft = "0h";
      }
    }
    return `Ready for your confirmation (closes in ${hoursLeft} if no response)`;
  }
  if (status === "Admin Review" || (complaint.reopen_count >= 3 && status === "Reopened")) {
    return "This complaint is under Admin review. An Admin will review and resolve it.";
  }
  if (status === "Closed" || status === "Closed (Auto Closed)") {
    return "Resolved & Closed";
  }
  return status;
};

const getLocationName = (locId, locations = [], fallbackName = "") => {
  if (fallbackName) return fallbackName;
  if (!locId) return "";
  const match = (locations || []).find((l) => l.location_id === locId || l.name === locId);
  if (match && match.name) return match.name;
  const idStr = String(locId).trim();
  const knownMap = {
    LOC_HOSTEL_A: "Hostel Block A",
    LOC_HOSTEL_B: "Hostel Block B",
    LOC_HOSTEL_C: "Hostel Block C",
    LOC_ACADEMIC: "Academic Block",
    LOC_MESS: "Mess Hall",
    LOC_SAC: "Student Activity Center",
    SPORTS: "Sports Complex",
    LOC_OTHER: "Other Campus Location",
  };
  if (knownMap[idStr]) return knownMap[idStr];
  if (idStr.startsWith("LOC_")) {
    return idStr
      .replace(/^LOC_/, "")
      .replace(/_/g, " ")
      .toLowerCase()
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }
  return idStr;
};

export default function StudentDashboard() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState("need_attention");
  const [toast, setToast] = useState(null);
  const [reopenTarget, setReopenTarget] = useState(null);
  const [reopenReason, setReopenReason] = useState("");
  const [actionSubmitting, setActionSubmitting] = useState(false);

  const {
    data: complaintsData,
    loading: complaintsLoading,
    error: complaintsError,
    reload: reloadComplaints,
  } = useAsyncData(async () => {
    const res = await complaintService.list().catch(() => ({ data: [] }));
    return res.data || [];
  }, []);

  const {
    data: announcementsData,
    loading: announcementsLoading,
  } = useAsyncData(async () => {
    const res = await announcementService.list().catch(() => ({ data: [] }));
    return res.data || [];
  }, []);

  const {
    data: notificationsData,
    loading: notificationsLoading,
    reload: reloadNotifications,
  } = useAsyncData(async () => {
    const res = await notificationService
      .listPaginated({ limit: 5 })
      .catch(() => ({ data: { items: [] } }));
    return res.data?.items || [];
  }, []);

  const { data: locationsData } = useAsyncData(async () => {
    const res = await locationService.list().catch(() => ({ data: [] }));
    return res.data || [];
  }, []);

  const complaints = complaintsData || [];
  const announcements = announcementsData || [];
  const notifications = notificationsData || [];
  const locations = locationsData || [];

  const unreadAnnouncements = useMemo(() => {
    return announcements.filter((a) => !a.is_read);
  }, [announcements]);

  const unreadAnnouncementsCount = unreadAnnouncements.length;

  const isClosedStatus = (statusStr) => {
    if (!statusStr) return false;
    const s = String(statusStr).toLowerCase();
    return s.startsWith("closed") || s === "rejected";
  };

  const activeComplaints = useMemo(() => {
    return complaints.filter((c) => !isClosedStatus(c.status));
  }, [complaints]);

  const closedCount = useMemo(() => {
    return complaints.filter((c) => isClosedStatus(c.status)).length;
  }, [complaints]);

  const needAttentionComplaints = useMemo(() => {
    return complaints.filter(
      (c) =>
        (c.created_by === user?.user_id || c.student_id === user?.user_id) &&
        (c.status === "Waiting for Verification" ||
          c.status === COMPLAINT_STATUS.WAITING_VERIFICATION ||
          c.status === "Admin Review" ||
          c.status === "Reopened"),
    );
  }, [complaints, user]);

  const handleConfirmClose = async (complaintId) => {
    setActionSubmitting(true);
    try {
      await complaintService.verify(complaintId);
      setToast({ type: "success", message: "Complaint confirmed and marked closed." });
      reloadComplaints();
      reloadNotifications();
    } catch (err) {
      setToast({
        type: "danger",
        message: err?.response?.data?.detail || "Could not confirm resolution.",
      });
    } finally {
      setActionSubmitting(false);
    }
  };

  const handleReopenSubmit = async (e) => {
    e.preventDefault();
    if (!reopenTarget) return;
    if (!reopenReason.trim()) {
      setToast({ type: "danger", message: "Please provide a reason why the issue is not fixed." });
      return;
    }
    setActionSubmitting(true);
    try {
      await complaintService.reopen(reopenTarget.complaint_id, reopenReason.trim());
      setToast({ type: "success", message: "Complaint reopened. Coordinator has been notified." });
      setReopenTarget(null);
      setReopenReason("");
      reloadComplaints();
      reloadNotifications();
    } catch (err) {
      setToast({
        type: "danger",
        message: err?.response?.data?.detail || "Failed to reopen complaint.",
      });
    } finally {
      setActionSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {toast && (
        <Toast
          message={toast.message}
          tone={toast.type}
          onClose={() => setToast(null)}
        />
      )}


      {/* Main Action Pills Block (Max 4) */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2 sm:gap-3">
        <ActionPill
          icon={Plus}
          label={t("pills.report_problem", "Report a problem")}
          to="/complaints/create"
          tone="blue"
        />
        <ActionPill
          icon={Search}
          label={t("pills.lost_found", "Lost & Found")}
          to="/lost-found"
          tone="amber"
        />
        <ActionPill
          icon={FileText}
          label={t("pills.my_complaints", "My complaints")}
          count={complaintsLoading ? undefined : activeComplaints.length}
          to="/complaints"
          tone="indigo"
        />
        <ActionPill
          icon={Megaphone}
          label={t("pills.notices", "Notices")}
          count={announcementsLoading ? undefined : unreadAnnouncementsCount}
          to="/announcements"
          tone="emerald"
        />
      </div>

      {/* 3 Key Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
        {complaintsLoading ? (
          <>
            <div className="h-24 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200/50 dark:border-slate-800" />
            <div className="h-24 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200/50 dark:border-slate-800" />
            <div className="h-24 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800/60 border border-slate-200/50 dark:border-slate-800" />
          </>
        ) : (
          <>
            <StatCard
              label="Need Attention"
              value={needAttentionComplaints.length}
              accent={needAttentionComplaints.length > 0}
              subtext={
                needAttentionComplaints.length > 0
                  ? "Requires verification to close"
                  : "All verifications complete"
              }
              onClick={() => setActiveTab("need_attention")}
            />
            <StatCard
              label="Active Problems"
              value={activeComplaints.length}
              subtext="Currently open or in progress"
              onClick={() =>
                navigate("/complaints", { state: { status: "active" } })
              }
            />
            <StatCard
              label="Resolved & Closed"
              value={closedCount}
              subtext="Completed tickets archive"
              onClick={() =>
                navigate("/complaints", { state: { status: "Closed" } })
              }
            />
          </>
        )}
      </div>

      {/* Urgent Attention / Action Cards */}
      {needAttentionComplaints.length > 0 && (
        <Card className="!p-5 border-amber-200/80 dark:border-amber-900/40 bg-amber-50/40 dark:bg-amber-950/10">
          <div className="flex items-center justify-between gap-3 pb-3 border-b border-amber-200/60 dark:border-amber-900/30">
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-amber-100 dark:bg-amber-900/50 text-amber-700 dark:text-amber-400">
                <AlertCircle className="h-4 w-4" />
              </div>
              <h2 className="text-sm font-bold text-amber-900 dark:text-amber-200">
                Action Required: Verify Resolved Work ({needAttentionComplaints.length})
              </h2>
            </div>
            <span className="text-[11px] text-amber-700 dark:text-amber-400">
              Please inspect the completed work and confirm or reopen
            </span>
          </div>

          <div className="space-y-3 pt-3">
            {needAttentionComplaints.map((c) => {
              const isAdminReview =
                c.status === "Admin Review" ||
                (c.reopen_count >= 3 && c.status === "Reopened");

              return (
                <div
                  key={c.complaint_id}
                  className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-amber-200/70 dark:border-amber-900/40 shadow-xs space-y-3"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <Link
                          to={`/complaints/${c.complaint_id}`}
                          className="font-bold text-sm text-slate-900 dark:text-slate-100 hover:text-primary transition-colors hover:underline"
                        >
                          {c.title}
                        </Link>
                        <Badge tone={getPriorityTone(c.priority)}>
                          {c.priority}
                        </Badge>
                        <span className="text-[11px] text-slate-400 dark:text-slate-500">
                          #{c.complaint_id?.slice(-8)}
                        </span>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3.5 w-3.5 text-primary" />
                          {getLocationName(c.location_id, locations, c.location_name)}
                        </span>
                        <span>•</span>
                        <span>{c.department_id || "General"}</span>
                        <span>•</span>
                        <span>Reopen count: <strong>{c.reopen_count || 0} / 3</strong></span>
                      </div>
                    </div>

                    <div className="shrink-0">
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 dark:bg-emerald-950/50 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                        <Clock className="h-3.5 w-3.5" />
                        {getStudentStageText(c)}
                      </span>
                    </div>
                  </div>

                  {/* Admin Review Banner or Confirmation Action Buttons */}
                  {isAdminReview ? (
                    <div className="p-3 rounded-lg border border-purple-200 dark:border-purple-800 bg-purple-50 dark:bg-purple-950/30 text-purple-900 dark:text-purple-200 text-xs flex items-center gap-2">
                      <ShieldAlert className="h-4 w-4 text-purple-600 shrink-0" />
                      <span>
                        This complaint is under Admin review. An Admin will review and resolve it.
                      </span>
                    </div>
                  ) : (
                    <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-100 dark:border-slate-800">
                      <div className="text-[11px] text-slate-500 dark:text-slate-400">
                        Does this fix resolve your issue? Confirming closes the ticket.
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setReopenTarget(c);
                            setReopenReason("");
                          }}
                          disabled={actionSubmitting}
                          className="!h-8 text-xs font-semibold text-rose-700 dark:text-rose-400 border-rose-300 dark:border-rose-800 hover:bg-rose-50 dark:hover:bg-rose-950/30 flex items-center gap-1"
                        >
                          <RotateCcw className="h-3.5 w-3.5" />
                          Still not fixed / Reopen
                        </Button>
                        <Button
                          variant="primary"
                          size="sm"
                          onClick={() => handleConfirmClose(c.complaint_id)}
                          disabled={actionSubmitting}
                          className="!h-8 text-xs font-semibold bg-emerald-600 hover:bg-emerald-700 text-white flex items-center gap-1"
                        >
                          <CheckCircle2 className="h-3.5 w-3.5" />
                          Confirm & Close
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Student Complaints Track List */}
      <Card>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100 dark:border-slate-800 mb-4">
          <div>
            <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">
              My Reported Problems
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
              Live status and progress updates for your complaints
            </p>
          </div>

          <div className="flex items-center gap-1.5 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl text-xs font-semibold overflow-x-auto max-w-full scrollbar-none">
            <button
              type="button"
              onClick={() => setActiveTab("need_attention")}
              className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer whitespace-nowrap shrink-0 ${
                activeTab === "need_attention"
                  ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
              }`}
            >
              Need Confirmation ({needAttentionComplaints.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("active")}
              className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer whitespace-nowrap shrink-0 ${
                activeTab === "active"
                  ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
              }`}
            >
              In Progress ({activeComplaints.length})
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("all")}
              className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer whitespace-nowrap shrink-0 ${
                activeTab === "all"
                  ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
              }`}
            >
              All ({complaints.length})
            </button>
          </div>
        </div>

        {complaintsLoading ? (
          <div className="space-y-3 py-2">
            <div className="h-20 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800/60" />
            <div className="h-20 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800/60" />
            <div className="h-20 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800/60" />
          </div>
        ) : complaintsError ? (
          <div className="py-6 text-center space-y-3">
            <p className="text-xs text-rose-500 font-medium">{complaintsError}</p>
            <Button size="sm" variant="outline" onClick={() => reloadComplaints()}>
              Retry
            </Button>
          </div>
        ) : (() => {
          let listToDisplay = complaints;
          if (activeTab === "need_attention") listToDisplay = needAttentionComplaints;
          if (activeTab === "active") listToDisplay = activeComplaints;

          if (listToDisplay.length === 0) {
            return (
              <EmptyState
                title="No complaints in this view"
                description={
                  activeTab === "need_attention"
                    ? "No complaints currently require your verification."
                    : activeTab === "active"
                    ? "You have no active unresolved issues right now."
                    : "You haven't filed any campus complaints yet."
                }
              />
            );
          }

          return (
            <div className="space-y-3">
              {listToDisplay.map((c) => (
                <div
                  key={c.complaint_id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700 transition-colors"
                >
                  <div className="space-y-1.5 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <Link
                        to={`/complaints/${c.complaint_id}`}
                        className="font-bold text-xs sm:text-sm text-slate-900 dark:text-slate-100 hover:text-primary transition-colors hover:underline truncate"
                      >
                        {c.title}
                      </Link>
                      <Badge tone={getPriorityTone(c.priority)}>
                        {c.priority}
                      </Badge>
                      <Badge tone={getStatusTone(c.status)}>
                        {c.status}
                      </Badge>
                      {c.visibility_type === "Community" && (
                        <Badge tone="info">Community</Badge>
                      )}
                    </div>

                    <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400 flex-wrap">
                      <span className="flex items-center gap-1">
                        <MapPin className="h-3 w-3 text-primary" />
                        {getLocationName(c.location_id, locations, c.location_name)}
                      </span>
                      <span>•</span>
                      <span>{c.department_id || "General"}</span>
                      <span>•</span>
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDate(c.created_at)}
                      </span>
                    </div>

                    {/* Clear Lifecycle Stage Pill */}
                    <div className="pt-1">
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
                        📌 {getStudentStageText(c)}
                      </span>
                    </div>
                  </div>

                  <div className="shrink-0 flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => navigate(`/complaints/${c.complaint_id}`)}
                      className="!h-8 text-xs font-semibold"
                    >
                      View Details
                      <ChevronRight className="h-3.5 w-3.5 ml-1" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          );
        })()}
      </Card>

      {/* Recent Activity */}
      <Card className="!p-4 sm:!p-5 border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-slate-900/60 shadow-2xs space-y-3">
        <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
          <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
            <Bell className="h-3.5 w-3.5 text-primary" />
            Recent Activity
          </h2>
          <Link
            to="/notifications"
            className="text-xs font-medium text-primary hover:underline"
          >
            View All
          </Link>
        </div>

        {notificationsLoading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 py-1">
            <div className="h-14 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800/60" />
            <div className="h-14 animate-pulse rounded-xl bg-slate-100 dark:bg-slate-800/60" />
          </div>
        ) : notifications.length === 0 ? (
          <p className="text-xs text-slate-400 dark:text-slate-500 py-3 text-center">
            No recent activity.
          </p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            {notifications.slice(0, 4).map((n) => (
              <div
                key={n.notification_id || n.id}
                onClick={() => {
                  if (n.reference_id && n.reference_type === "Complaint") {
                    navigate(`/complaints/${n.reference_id}`);
                  } else {
                    navigate("/notifications");
                  }
                }}
                className="flex items-start justify-between gap-2 p-2.5 rounded-xl bg-slate-50/80 dark:bg-slate-800/50 border border-slate-200/70 dark:border-slate-800/80 hover:border-slate-300 dark:hover:border-slate-700 cursor-pointer transition-colors text-xs"
              >
                <div className="space-y-0.5 min-w-0 pr-1">
                  <div className="font-medium text-slate-800 dark:text-slate-200 truncate">
                    {n.title || n.message}
                  </div>
                  <div className="text-[11px] text-slate-400 dark:text-slate-500 line-clamp-1">
                    {n.message}
                  </div>
                </div>
                <span className="text-[10px] text-slate-400 shrink-0">
                  {formatDate(n.created_at)}
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Student Reopen Modal */}
      {reopenTarget && (
        <Modal
          open={true}
          onClose={() => setReopenTarget(null)}
          title="Reopen Complaint"
        >
          <form onSubmit={handleReopenSubmit} className="space-y-4">
            <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200 text-xs">
              <span className="font-bold block mb-1">
                Attempt {(reopenTarget.reopen_count || 0) + 1} of 3
              </span>
              <span>
                Please clearly explain what remains unfinished. If this complaint is reopened 3 times, it will automatically escalate directly to Admin Review.
              </span>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                Why is the issue still not fixed? <span className="text-rose-500">*</span>
              </label>
              <textarea
                rows={4}
                required
                value={reopenReason}
                onChange={(e) => setReopenReason(e.target.value)}
                placeholder="e.g. The technician visited, but the water leak is still dripping from the main valve..."
                className="w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3 text-xs outline-none focus:border-primary text-slate-900 dark:text-slate-100"
              />
            </div>

            <div className="flex justify-end gap-2.5 pt-2 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="subtle"
                onClick={() => setReopenTarget(null)}
                disabled={actionSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={actionSubmitting || !reopenReason.trim()}
                className="bg-rose-600 hover:bg-rose-700 text-white font-semibold"
              >
                {actionSubmitting ? "Submitting..." : "Submit Reopen Request"}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
