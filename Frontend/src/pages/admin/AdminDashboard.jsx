import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  FileText,
  Megaphone,
  Bell,
  Clock,
  ArrowRight,
  Shield,
  MapPin,
  CheckCircle2,
  ChevronRight,
  Users,
  Settings,
  AlertTriangle,
  UserCheck,
  TrendingUp,
  Scale,
  RotateCw,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import ActionPill from "../../components/ActionPill.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import StatCard from "../../components/StatCard.jsx";
import Badge from "../../components/Badge.jsx";
import Modal from "../../components/Modal.jsx";
import Textarea from "../../components/Textarea.jsx";
import Toast from "../../components/Toast.jsx";
import SetupChecklistWidget from "../../components/SetupChecklistWidget.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { useLanguage } from "../../context/LanguageContext.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { complaintService } from "../../services/complaintService.js";
import { announcementService } from "../../services/announcementService.js";
import { notificationService } from "../../services/notificationService.js";
import { userService } from "../../services/userService.js";
import { locationService } from "../../services/locationService.js";
import { setupService } from "../../services/setupService.js";
import { formatDate } from "../../utils/dateFormatter.js";
import { getStatusTone, getPriorityTone, getSlaTone } from "../../utils/statusColor.js";

const getLocationName = (locId, locations = []) => {
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
    LOC_SPORTS: "Sports Complex",
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

export default function AdminDashboard() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const [toastMessage, setToastMessage] = useState("");
  const [toastTone, setToastTone] = useState("success");

  // Reassign Modal State
  const [reassignTarget, setReassignTarget] = useState(null);
  const [reassignCoordinatorId, setReassignCoordinatorId] = useState("");
  const [reassignReason, setReassignReason] = useState("");
  const [submittingReassign, setSubmittingReassign] = useState(false);

  // Admin Review Decision Modal State
  const [reviewTarget, setReviewTarget] = useState(null);
  const [reviewDecision, setReviewDecision] = useState("close"); // "close" | "reopen"
  const [reviewNotes, setReviewNotes] = useState("");
  const [submittingReview, setSubmittingReview] = useState(false);

  const {
    data: dashboardData,
    loading,
    error,
    reload,
  } = useAsyncData(
    async () => {
      const [compRes, ancRes, notifRes, userRes, locRes, setupRes] = await Promise.all([
        complaintService.list().catch(() => ({ data: [] })),
        announcementService.list().catch(() => ({ data: [] })),
        notificationService
          .listPaginated({ limit: 5 })
          .then((res) => ({ data: res.data.items }))
          .catch(() => ({ data: [] })),
        userService.list().catch(() => ({ data: [] })),
        locationService.list().catch(() => ({ data: [] })),
        setupService.getChecklist().catch(() => null),
      ]);
      return {
        complaints: compRes.data || [],
        announcements: ancRes.data || [],
        notifications: notifRes.data || [],
        users: userRes.data || [],
        locations: locRes.data || [],
        setupChecklist: setupRes || null,
      };
    },
    { complaints: [], announcements: [], notifications: [], users: [], locations: [], setupChecklist: null },
  );

  const setupGapsCount = useMemo(() => {
    const s = dashboardData?.setupChecklist;
    if (!s || s.is_complete) return 0;
    return (
      (s.uncovered_places?.length || 0) +
      (s.teams_no_backup?.length || 0) +
      (s.locations_no_warden?.length || 0) +
      (s.staff_no_phone?.length || 0) +
      (s.departments_few_emergency_contacts?.length || 0)
    );
  }, [dashboardData]);

  const complaints = dashboardData?.complaints || [];
  const announcements = dashboardData?.announcements || [];
  const notifications = dashboardData?.notifications || [];
  const users = dashboardData?.users || [];
  const locations = dashboardData?.locations || [];

  const coordinators = useMemo(() => {
    return users.filter((u) => u.role === "coordinator" && u.active !== false);
  }, [users]);

  const activeProblems = useMemo(() => {
    return complaints.filter(
      (c) => !["Closed", "Closed (Auto Closed)", "Rejected", "Cancelled"].includes(c.status),
    );
  }, [complaints]);

  const adminReviewComplaints = useMemo(() => {
    return complaints.filter(
      (c) => c.status === "Admin Review" || c.status === "admin_review",
    );
  }, [complaints]);

  const overdueComplaints = useMemo(() => {
    return complaints.filter((c) => c.is_overdue || c.status === "Overdue" || c.sla_status === "Breached");
  }, [complaints]);

  const escalations = useMemo(() => {
    return complaints.filter(
      (c) => c.priority === "Critical" || c.status === "Escalated",
    );
  }, [complaints]);

  const usersCount = useMemo(() => {
    return users.length || 0;
  }, [users]);

  // Actions
  const handleReassignSubmit = async (e) => {
    e.preventDefault();
    if (!reassignTarget || !reassignCoordinatorId) return;
    setSubmittingReassign(true);
    try {
      await complaintService.assign(
        reassignTarget.complaint_id,
        reassignCoordinatorId,
        reassignReason.trim() || "Administrative workload rebalance",
      );
      setToastTone("success");
      setToastMessage(`Complaint ${reassignTarget.complaint_id} reassigned successfully.`);
      setReassignTarget(null);
      setReassignCoordinatorId("");
      setReassignReason("");
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Failed to reassign complaint.");
    } finally {
      setSubmittingReassign(false);
    }
  };

  const handleReviewDecisionSubmit = async (e) => {
    e.preventDefault();
    if (!reviewTarget) return;
    setSubmittingReview(true);
    try {
      await complaintService.adminDecision(
        reviewTarget.complaint_id,
        reviewDecision,
        reviewNotes.trim() || `Administrative decision: ${reviewDecision}`,
      );
      setToastTone("success");
      setToastMessage(`Admin review decision recorded: ${reviewDecision === "close" ? "Approved Closed" : "Reopened to Coordinator"}.`);
      setReviewTarget(null);
      setReviewNotes("");
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Failed to submit review decision.");
    } finally {
      setSubmittingReview(false);
    }
  };

  if (loading)
    return (
      <Loader label="Loading admin dashboard..." variant="skeleton" />
    );
  if (error)
    return <EmptyState title="Dashboard Unavailable" description={error} />;

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {toastMessage && (
        <Toast
          message={toastMessage}
          tone={toastTone}
          onClose={() => setToastMessage("")}
        />
      )}

      {/* Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            Good morning, {user?.name || "Admin"}
          </h1>
          <p className="text-xs font-normal text-slate-500 dark:text-slate-400 mt-1">
            Institutional Operations & System Governance • {complaints.length} tickets and {usersCount} campus members
          </p>
        </div>
        <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
          <Button
            onClick={() => navigate("/coordinators/performance")}
            variant="outline"
            size="md"
            className="font-medium shrink-0 flex items-center gap-1.5"
          >
            <TrendingUp className="h-4 w-4" />
            Coordinator Stats
          </Button>
          <Button
            onClick={() => navigate("/admin/departments")}
            variant="outline"
            size="md"
            className="font-medium shrink-0 flex items-center gap-1.5"
          >
            Coverage Gaps
          </Button>
        </div>
      </div>

      {/* Main Action Pills Block (Max 4) */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-3">
        <ActionPill
          icon={FileText}
          label={t("pills.all_complaints", "All complaints")}
          count={activeProblems.length}
          to="/complaints"
          tone="blue"
        />
        <ActionPill
          icon={Users}
          label={t("pills.teams_setup", "Teams & setup")}
          count={setupGapsCount}
          to="/admin/teams"
          tone="emerald"
        />
        <ActionPill
          icon={TrendingUp}
          label={t("pills.reports", "Reports")}
          to="/reports"
          tone="purple"
        />
      </div>

      {/* Setup Checklist (Part 3.4) */}
      <SetupChecklistWidget />

      {/* 4 Key Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <StatCard
          label="Active Problems"
          value={activeProblems.length}
          subtext="Campus open tickets"
          onClick={() => navigate("/complaints", { state: { status: "active" } })}
        />
        <StatCard
          label="Admin Review Queue"
          value={adminReviewComplaints.length}
          accent={adminReviewComplaints.length > 0}
          subtext={adminReviewComplaints.length > 0 ? "Disputes requiring decision" : "No pending disputes"}
          onClick={() => navigate("/complaints", { state: { status: "Admin Review" } })}
        />
        <StatCard
          label="Overdue / SLA Risk"
          value={overdueComplaints.length}
          accent={overdueComplaints.length > 0}
          subtext={overdueComplaints.length > 0 ? "Breached SLA deadline" : "Turnaround within SLA"}
          onClick={() => navigate("/complaints", { state: { sla: "Overdue" } })}
        />
        <StatCard
          label="Campus Accounts"
          value={usersCount}
          subtext="Registered campus users"
          onClick={() => navigate("/admin/users")}
        />
      </div>

      {/* Critical Escalations / Admin Review Notice */}
      {(adminReviewComplaints.length > 0 || overdueComplaints.length > 0) && (
        <div className="flex items-center justify-between gap-4 p-4 rounded-xl border border-rose-200/80 dark:border-rose-900/40 bg-rose-50/70 dark:bg-rose-950/20 text-rose-900 dark:text-rose-200 text-xs">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-rose-100 dark:bg-rose-900/50 text-rose-700 dark:text-rose-400 shrink-0">
              <Scale className="h-4 w-4" />
            </div>
            <div>
              <span className="font-semibold">
                Administrative Attention: {adminReviewComplaints.length} ticket(s) in Admin Review queue, {overdueComplaints.length} overdue ticket(s).
              </span>
              <p className="text-[11px] text-rose-800/80 dark:text-rose-300/80 mt-0.5">
                Review disputes or reassign coordinators to maintain operational flow.
              </p>
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => navigate("/complaints")}
            className="!h-8 text-xs font-semibold shrink-0 border-rose-300 dark:border-rose-800 text-rose-900 dark:text-rose-200 hover:bg-rose-100/60"
          >
            Inspect All
          </Button>
        </div>
      )}

      {/* Operational Workspace Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Notices & Live Alerts */}
        <div className="space-y-6">
          {/* Announcements */}
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/80 dark:border-slate-800/80">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                <Megaphone className="h-3.5 w-3.5 text-amber-500" />
                Institutional Notices
              </h2>
              <Link
                to="/announcements"
                className="text-xs font-medium text-primary hover:underline"
              >
                View All
              </Link>
            </div>

            {announcements.length === 0 ? (
              <p className="text-xs text-slate-400 dark:text-slate-500 py-4 text-center">
                No active announcements today.
              </p>
            ) : (
              <div className="space-y-2.5">
                {announcements.slice(0, 3).map((a) => (
                  <div
                    key={a.announcement_id || a.id}
                    className="p-3 rounded-xl bg-white dark:bg-[#101726] border border-slate-200/80 dark:border-slate-800/80 text-xs shadow-2xs space-y-1"
                  >
                    <div className="flex items-center justify-between gap-2 font-medium text-slate-900 dark:text-slate-100">
                      <span className="truncate">{a.title}</span>
                      <Badge tone={a.priority === "Critical" ? "danger" : "warning"}>
                        {a.priority || "Normal"}
                      </Badge>
                    </div>
                    <p className="text-slate-500 dark:text-slate-400 line-clamp-2 text-[11px] leading-relaxed">
                      {a.content || a.description}
                    </p>
                    <div className="text-[10px] text-slate-400 dark:text-slate-500 pt-1 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {formatDate(a.created_at)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Activity Alerts */}
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/80 dark:border-slate-800/80">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                <Bell className="h-3.5 w-3.5 text-primary" />
                Audit & Activity Alerts
              </h2>
              <Link
                to="/notifications"
                className="text-xs font-medium text-primary hover:underline"
              >
                View All
              </Link>
            </div>

            {notifications.length === 0 ? (
              <p className="text-xs text-slate-400 dark:text-slate-500 py-4 text-center">
                No recent activity.
              </p>
            ) : (
              <div className="space-y-2">
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
                    className="flex items-start justify-between gap-2 p-2.5 rounded-xl bg-white dark:bg-[#101726] border border-slate-200/70 dark:border-slate-800/80 hover:border-slate-300 dark:hover:border-slate-700 cursor-pointer transition-colors text-xs"
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
          </div>
        </div>

        {/* Right Column: Admin Review Queue & Complaint Assignees */}
        <div className="space-y-6">
          {/* Admin Review Queue Section */}
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/80 dark:border-slate-800/80">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                <Scale className="h-3.5 w-3.5 text-purple-600" />
                Admin Review Queue (Disputes)
              </h2>
              <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 dark:bg-purple-950/60 dark:text-purple-300">
                {adminReviewComplaints.length} Pending
              </span>
            </div>

            {adminReviewComplaints.length === 0 ? (
              <div className="p-4 rounded-xl border border-dashed border-slate-200 dark:border-slate-800 text-center text-xs text-slate-400">
                No tickets currently escalated to Admin Review.
              </div>
            ) : (
              <div className="space-y-2.5">
                {adminReviewComplaints.map((c) => (
                  <div
                    key={c.complaint_id}
                    className="p-3.5 rounded-xl border border-purple-200 dark:border-purple-900/60 bg-purple-50/50 dark:bg-purple-950/20 text-xs space-y-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <Link
                        to={`/complaints/${c.complaint_id}`}
                        className="font-bold text-slate-900 dark:text-slate-100 hover:text-primary transition-colors truncate"
                      >
                        {c.title}
                      </Link>
                      <Badge tone="purple">Admin Review</Badge>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                      <span>ID: {c.complaint_id}</span>
                      <span>•</span>
                      <span>{getLocationName(c.location_id, locations)}</span>
                      <span>•</span>
                      <span className="text-purple-700 font-semibold">
                        Reopened {c.reopen_count || 3} times
                      </span>
                    </div>

                    <div className="flex items-center gap-2 pt-1">
                      <Button
                        size="xs"
                        variant="primary"
                        onClick={() => {
                          setReviewTarget(c);
                          setReviewDecision("close");
                          setReviewNotes("");
                        }}
                        className="text-xs font-semibold"
                      >
                        Decide Dispute
                      </Button>
                      <Button
                        size="xs"
                        variant="outline"
                        onClick={() => navigate(`/complaints/${c.complaint_id}`)}
                        className="text-xs"
                      >
                        View Timeline
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Active Complaints & Current Assignees (Read-only list with Reassign) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/80 dark:border-slate-800/80">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                <UserCheck className="h-3.5 w-3.5 text-blue-600" />
                Active Complaint Ownership
              </h2>
              <Link
                to="/complaints"
                className="text-xs font-medium text-primary hover:underline"
              >
                All Tickets
              </Link>
            </div>

            {activeProblems.length === 0 ? (
              <p className="text-xs text-slate-400 py-4 text-center">
                All campus complaints are resolved.
              </p>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
                {activeProblems.slice(0, 6).map((c) => (
                  <div
                    key={c.complaint_id}
                    className="p-3 rounded-xl bg-white dark:bg-[#101726] border border-slate-200/70 dark:border-slate-800/80 text-xs flex items-center justify-between gap-3"
                  >
                    <div className="min-w-0 space-y-1">
                      <div className="flex items-center gap-2">
                        <Link
                          to={`/complaints/${c.complaint_id}`}
                          className="font-bold text-slate-900 dark:text-slate-100 hover:text-primary transition-colors truncate"
                        >
                          {c.title}
                        </Link>
                        <Badge tone={getStatusTone(c.status)}>
                          {c.status}
                        </Badge>
                      </div>

                      <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
                        <span>{getLocationName(c.location_id, locations)}</span>
                        <span>•</span>
                        <span className="font-semibold text-slate-700 dark:text-slate-300">
                          {c.assigned_to_name || c.assigned_to || "Unassigned"}
                        </span>
                      </div>
                    </div>

                    <Button
                      size="xs"
                      variant="outline"
                      onClick={() => {
                        setReassignTarget(c);
                        setReassignCoordinatorId(c.assigned_to || "");
                        setReassignReason("");
                      }}
                      className="shrink-0 text-[11px]"
                    >
                      Reassign
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Reassign Modal */}
      {reassignTarget && (
        <Modal
          isOpen={true}
          onClose={() => setReassignTarget(null)}
          title={`Reassign Complaint: ${reassignTarget.complaint_id}`}
        >
          <form onSubmit={handleReassignSubmit} className="space-y-4">
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900 text-xs space-y-1">
              <div className="font-bold text-slate-800 dark:text-slate-200">
                {reassignTarget.title}
              </div>
              <div className="text-slate-500">
                Current Assignee: {reassignTarget.assigned_to_name || reassignTarget.assigned_to || "Unassigned"}
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Assign to Coordinator
              </label>
              <select
                value={reassignCoordinatorId}
                onChange={(e) => setReassignCoordinatorId(e.target.value)}
                className="w-full h-10 rounded-xl border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-xs text-slate-800 dark:text-slate-100 outline-none focus:border-primary"
                required
              >
                <option value="">-- Choose Coordinator --</option>
                {coordinators.map((coord) => (
                  <option key={coord.user_id} value={coord.user_id}>
                    {coord.name} ({coord.email})
                  </option>
                ))}
              </select>
            </div>

            <Textarea
              label="Reason for Reassignment"
              value={reassignReason}
              onChange={(e) => setReassignReason(e.target.value)}
              placeholder="e.g. Workload balancing, specialized skill requirement..."
              rows={3}
              required
            />

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
                onClick={() => setReassignTarget(null)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={!reassignCoordinatorId || submittingReassign}
              >
                {submittingReassign ? "Reassigning..." : "Confirm Reassignment"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Admin Review Decision Modal */}
      {reviewTarget && (
        <Modal
          isOpen={true}
          onClose={() => setReviewTarget(null)}
          title={`Admin Review: ${reviewTarget.complaint_id}`}
        >
          <form onSubmit={handleReviewDecisionSubmit} className="space-y-4">
            <div className="p-3 rounded-xl bg-purple-50 dark:bg-purple-950/40 text-xs space-y-1">
              <div className="font-bold text-slate-900 dark:text-slate-100">
                {reviewTarget.title}
              </div>
              <div className="text-slate-500">
                This ticket reached Admin Review after 3 reopens or persistent dispute between student and staff.
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Administrative Verdict
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setReviewDecision("close")}
                  className={`p-3 rounded-xl text-xs font-bold border transition-colors ${
                    reviewDecision === "close"
                      ? "border-emerald-500 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
                      : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-600"
                  }`}
                >
                  ✅ Approve Fixed (Close)
                </button>
                <button
                  type="button"
                  onClick={() => setReviewDecision("reopen")}
                  className={`p-3 rounded-xl text-xs font-bold border transition-colors ${
                    reviewDecision === "reopen"
                      ? "border-rose-500 bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300"
                      : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-600"
                  }`}
                >
                  🔄 Not Fixed (Reopen to Coordinator)
                </button>
              </div>
            </div>

            <Textarea
              label="Administrative Finding / Notes"
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              placeholder="Explain the inspection findings or resolution rationale..."
              rows={3}
              required
            />

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
                onClick={() => setReviewTarget(null)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={submittingReview}
              >
                {submittingReview ? "Recording..." : "Enforce Decision"}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
