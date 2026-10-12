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
  AlertTriangle,
  Layers,
  UserCheck,
  TrendingUp,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import StatCard from "../../components/StatCard.jsx";
import Badge from "../../components/Badge.jsx";
import Modal from "../../components/Modal.jsx";
import Textarea from "../../components/Textarea.jsx";
import Toast from "../../components/Toast.jsx";
import SetupChecklistWidget from "../../components/SetupChecklistWidget.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { complaintService } from "../../services/complaintService.js";
import { announcementService } from "../../services/announcementService.js";
import { notificationService } from "../../services/notificationService.js";
import { userService } from "../../services/userService.js";
import { locationService } from "../../services/locationService.js";
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

export default function ManagerDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [toastMessage, setToastMessage] = useState("");
  const [toastTone, setToastTone] = useState("success");

  // Reassign Modal State
  const [reassignTarget, setReassignTarget] = useState(null);
  const [reassignCoordinatorId, setReassignCoordinatorId] = useState("");
  const [reassignReason, setReassignReason] = useState("");
  const [submittingReassign, setSubmittingReassign] = useState(false);

  const {
    data: dashboardData,
    loading,
    error,
    reload,
  } = useAsyncData(
    async () => {
      const [compRes, ancRes, notifRes, locRes, userRes] = await Promise.all([
        complaintService.list().catch(() => ({ data: [] })),
        announcementService.list().catch(() => ({ data: [] })),
        notificationService
          .listPaginated({ limit: 5 })
          .then((res) => ({ data: res.data.items }))
          .catch(() => ({ data: [] })),
        locationService.list().catch(() => ({ data: [] })),
        userService.list().catch(() => ({ data: [] })),
      ]);
      return {
        complaints: compRes.data || [],
        announcements: ancRes.data || [],
        notifications: notifRes.data || [],
        locations: locRes.data || [],
        users: userRes.data || [],
      };
    },
    { complaints: [], announcements: [], notifications: [], locations: [], users: [] },
  );

  const complaints = dashboardData?.complaints || [];
  const announcements = dashboardData?.announcements || [];
  const notifications = dashboardData?.notifications || [];
  const locations = dashboardData?.locations || [];
  const users = dashboardData?.users || [];

  const coordinators = useMemo(() => {
    return users.filter((u) => u.role === "coordinator" && u.active !== false);
  }, [users]);

  const activeProblems = useMemo(() => {
    return complaints.filter(
      (c) => !["Closed", "Closed (Auto Closed)", "Rejected", "Cancelled"].includes(c.status),
    );
  }, [complaints]);

  const overdueComplaints = useMemo(() => {
    return complaints.filter((c) => c.is_overdue || c.status === "Overdue" || c.sla_status === "Breached");
  }, [complaints]);

  const escalatedComplaints = useMemo(() => {
    return complaints.filter(
      (c) => c.priority === "Critical" || c.status === "Escalated",
    );
  }, [complaints]);

  const locationsCount = useMemo(() => {
    return locations.length || user?.assigned_locations?.length || 0;
  }, [locations, user]);

  const handleReassignSubmit = async (e) => {
    e.preventDefault();
    if (!reassignTarget || !reassignCoordinatorId) return;
    setSubmittingReassign(true);
    try {
      await complaintService.assign(
        reassignTarget.complaint_id,
        reassignCoordinatorId,
        reassignReason.trim() || "Managerial reassignment",
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

  if (loading)
    return (
      <Loader label="Loading manager dashboard..." variant="skeleton" />
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
            Good morning, {user?.name || "Manager"}
          </h1>
          <p className="text-xs font-normal text-slate-500 dark:text-slate-400 mt-1">
            Operations & Service Level Oversight • {complaints.length} campus complaints monitored
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
            className="font-medium shrink-0"
          >
            Coverage Gaps
          </Button>
          <Button
            onClick={() => navigate("/complaints")}
            variant="primary"
            size="md"
            className="font-medium shrink-0 flex items-center gap-1.5"
          >
            <FileText className="h-4 w-4" />
            Manage Complaints
          </Button>
        </div>
      </div>

      {/* Setup Checklist (Part 3.4) */}
      <SetupChecklistWidget />

      {/* 4 Key Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <StatCard
          label="Active Problems"
          value={activeProblems.length}
          subtext="Open campus issues"
          onClick={() => navigate("/complaints", { state: { status: "active" } })}
        />
        <StatCard
          label="Overdue / SLA Risk"
          value={overdueComplaints.length}
          accent={overdueComplaints.length > 0}
          subtext={overdueComplaints.length > 0 ? "Requires manager escalation" : "All within turnaround targets"}
          onClick={() => navigate("/complaints", { state: { sla: "Overdue" } })}
        />
        <StatCard
          label="Critical / Escalated"
          value={escalatedComplaints.length}
          accent={escalatedComplaints.length > 0}
          subtext="Urgent campus problems"
          onClick={() =>
            navigate("/complaints", { state: { status: "Escalated" } })
          }
        />
        <StatCard
          label="Campus Locations"
          value={locationsCount}
          subtext="Under management"
          onClick={() => navigate("/admin/locations")}
        />
      </div>

      {/* Overdue Alert Banner */}
      {(overdueComplaints.length > 0 || escalatedComplaints.length > 0) && (
        <div className="flex items-center justify-between gap-4 p-4 rounded-xl border border-rose-200/80 dark:border-rose-900/40 bg-rose-50/70 dark:bg-rose-950/20 text-rose-900 dark:text-rose-200 text-xs">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-rose-100 dark:bg-rose-900/50 text-rose-700 dark:text-rose-400 shrink-0">
              <AlertTriangle className="h-4 w-4" />
            </div>
            <div>
              <span className="font-semibold">
                SLA Alert: {overdueComplaints.length} overdue complaint(s) across campus.
              </span>
              <p className="text-[11px] text-rose-800/80 dark:text-rose-300/80 mt-0.5">
                Reassign coordinators or adjust priorities to maintain SLA compliance.
              </p>
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => navigate("/complaints", { state: { sla: "Overdue" } })}
            className="!h-8 text-xs font-semibold shrink-0 border-rose-300 dark:border-rose-800 text-rose-900 dark:text-rose-200 hover:bg-rose-100/60"
          >
            Review Overdue
            <ArrowRight className="h-3 w-3 ml-1" />
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
                Campus Announcements
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
                Activity Alerts
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

        {/* Right Column: Complaint Ownership & Reassign */}
        <div className="space-y-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200/80 dark:border-slate-800/80">
              <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                <UserCheck className="h-3.5 w-3.5 text-blue-600" />
                Active Complaint Ownership & Triage
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
                {activeProblems.slice(0, 8).map((c) => (
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
    </div>
  );
}
