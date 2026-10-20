import { useMemo, useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Building,
  Megaphone,
  Bell,
  Clock,
  ArrowRight,
  Shield,
  MapPin,
  CheckCircle2,
  ChevronRight,
  AlertTriangle,
  UserCheck,
  Check,
  XCircle,
  TrendingUp,
  Award,
  Users,
  Image as ImageIcon,
  Edit,
  AlertCircle,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import ActionPill from "../../components/ActionPill.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import StatCard from "../../components/StatCard.jsx";
import Badge from "../../components/Badge.jsx";
import Modal from "../../components/Modal.jsx";
import Textarea from "../../components/Textarea.jsx";
import Select from "../../components/Select.jsx";
import Toast from "../../components/Toast.jsx";
import AssignModal from "../../components/AssignModal.jsx";
import PinnedEmergenciesBanner from "../../components/PinnedEmergenciesBanner.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { useLanguage } from "../../context/LanguageContext.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { complaintService } from "../../services/complaintService.js";
import { teamService } from "../../services/teamService.js";
import { announcementService } from "../../services/announcementService.js";
import { notificationService } from "../../services/notificationService.js";
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
  return idStr;
};

export default function LocationDashboard() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const [toastMessage, setToastMessage] = useState("");
  const [toastTone, setToastTone] = useState("success");

  // Priority Change Modal State
  const [priorityModalTicket, setPriorityModalTicket] = useState(null);
  const [newPriority, setNewPriority] = useState("Medium");
  const [priorityChangeReason, setPriorityChangeReason] = useState("");
  const [submittingPriority, setSubmittingPriority] = useState(false);

  // Warden Rejection ("Not Fixed") Modal State
  const [rejectModalTicket, setRejectModalTicket] = useState(null);
  const [rejectReason, setRejectReason] = useState("");
  const [submittingReject, setSubmittingReject] = useState(false);

  // Verification Notes Modal State
  const [verifyModalTicket, setVerifyModalTicket] = useState(null);
  const [verifyNotes, setVerifyNotes] = useState("");
  const [submittingVerify, setSubmittingVerify] = useState(false);

  // Coordinator Stats
  const [coordinatorStats, setCoordinatorStats] = useState([]);
  const [loadingStats, setLoadingStats] = useState(false);

  // Watch List & Assign Modal State (Rule K4)
  const [assignModalComplaint, setAssignModalComplaint] = useState(null);
  const [filterLeaveOnly, setFilterLeaveOnly] = useState(false);

  const {
    data: dashboardData,
    loading,
    error,
    reload,
  } = useAsyncData(
    async () => {
      const [compRes, ancRes, notifRes, locRes, teamsRes] = await Promise.all([
        complaintService.list().catch(() => ({ data: [] })),
        announcementService.list().catch(() => ({ data: [] })),
        notificationService
          .listPaginated({ limit: 5 })
          .then((res) => ({ data: res.data.items }))
          .catch(() => ({ data: [] })),
        locationService.list().catch(() => ({ data: [] })),
        teamService.list({ active_only: true }).catch(() => ({ data: [] })),
      ]);
      return {
        complaints: compRes.data || [],
        announcements: ancRes.data || [],
        notifications: notifRes.data || [],
        locations: locRes.data || [],
        teams: teamsRes.data || teamsRes || [],
      };
    },
    { complaints: [], announcements: [], notifications: [], locations: [], teams: [] },
  );

  const complaints = dashboardData?.complaints || [];
  const announcements = dashboardData?.announcements || [];
  const notifications = dashboardData?.notifications || [];
  const locations = dashboardData?.locations || [];
  const teams = dashboardData?.teams || [];

  const watchListComplaints = useMemo(() => {
    return complaints.filter((c) => {
      const isNotClosed = !["Closed", "Closed (Auto Closed)", "Rejected"].includes(c.status);
      if (!isNotClosed) return false;
      if (filterLeaveOnly && !c.assignee_on_leave_flag) return false;
      return true;
    });
  }, [complaints, filterLeaveOnly]);


  const locationTitle = useMemo(() => {
    return user?.location_name || getLocationName(user?.location_id, locations) || "Assigned Location";
  }, [user, locations]);

  // Load coordinator performance stats
  useEffect(() => {
    async function loadStats() {
      setLoadingStats(true);
      try {
        const res = await complaintService.getCoordinatorStats();
        setCoordinatorStats(res.data || []);
      } catch (err) {
        setCoordinatorStats([]);
      } finally {
        setLoadingStats(false);
      }
    }
    loadStats();
  }, []);

  // Filter complaints needing this warden's verification
  const needsMyVerificationComplaints = useMemo(() => {
    return complaints.filter((c) => {
      const needsInspection = Boolean(c.requires_warden_check || c.status === "Pending Warden Verification");
      if (!needsInspection) return false;
      if (user?.location_id && c.location_id !== user.location_id) return false;
      return true;
    });
  }, [complaints, user]);

  const activeProblems = useMemo(() => {
    return complaints.filter(
      (c) => !["Closed", "Closed (Auto Closed)", "Rejected"].includes(c.status),
    );
  }, [complaints]);

  const overdueComplaints = useMemo(() => {
    return complaints.filter(
      (c) => c.is_overdue || c.status === "Overdue" || c.sla_status === "Breached",
    );
  }, [complaints]);

  const unclaimedComplaints = useMemo(() => {
    return complaints.filter((c) => {
      if (user?.location_id && c.location_id !== user.location_id) return false;
      return (
        (c.status === "Submitted" || c.status === "Pending" || !c.assigned_to) &&
        c.accept_due_at &&
        new Date(c.accept_due_at) < new Date()
      );
    });
  }, [complaints, user]);

  const blockedTooLongComplaints = useMemo(() => {
    return complaints.filter((c) => {
      if (user?.location_id && c.location_id !== user.location_id) return false;
      if (c.status !== "Waiting for Parts") return false;
      if (c.paused_at) {
        const pausedMs = Date.now() - new Date(c.paused_at).getTime();
        return pausedMs > 72 * 3600 * 1000;
      }
      return false;
    });
  }, [complaints, user]);

  const photoSkipComplaints = useMemo(() => {
    return complaints.filter((c) => {
      if (user?.location_id && c.location_id !== user.location_id) return false;
      return c.photo_skipped || (c.photo_skip_streak && c.photo_skip_streak >= 2);
    });
  }, [complaints, user]);

  // Action Handlers
  const handlePhotoMismatch = async (ticket) => {
    try {
      await complaintService.wardenVerify(
        ticket.complaint_id,
        "Not Fixed",
        "Photo does not match the actual reported issue or repair work.",
        { photo_mismatch: true }
      );
      setToastTone("success");
      setToastMessage(`Ticket ${ticket.complaint_id} flagged for photo mismatch and returned to coordinator.`);
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Photo mismatch submission failed.");
    }
  };

  const handleVerifyFixed = async () => {
    if (!verifyModalTicket) return;
    setSubmittingVerify(true);
    try {
      await complaintService.wardenVerify(verifyModalTicket.complaint_id, "Verified", verifyNotes.trim());
      setToastTone("success");
      setToastMessage(`Ticket ${verifyModalTicket.complaint_id} verified and sent for student confirmation.`);
      setVerifyModalTicket(null);
      setVerifyNotes("");
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Verification failed.");
    } finally {
      setSubmittingVerify(false);
    }
  };

  const handleReportNotFixed = async (e) => {
    e.preventDefault();
    if (!rejectModalTicket || !rejectReason.trim()) return;
    setSubmittingReject(true);
    try {
      await complaintService.wardenVerify(rejectModalTicket.complaint_id, "Not Fixed", rejectReason.trim());
      setToastTone("success");
      setToastMessage(`Ticket ${rejectModalTicket.complaint_id} rejected and returned to In Progress for rework.`);
      setRejectModalTicket(null);
      setRejectReason("");
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Rejection submission failed.");
    } finally {
      setSubmittingReject(false);
    }
  };

  const handlePrioritySubmit = async (e) => {
    e.preventDefault();
    if (!priorityModalTicket || !priorityChangeReason.trim()) return;
    setSubmittingPriority(true);
    try {
      await complaintService.changePriority(
        priorityModalTicket.complaint_id,
        newPriority,
        priorityChangeReason.trim(),
      );
      setToastTone("success");
      setToastMessage(`Priority of ${priorityModalTicket.complaint_id} updated to ${newPriority}.`);
      setPriorityModalTicket(null);
      setPriorityChangeReason("");
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Priority update failed.");
    } finally {
      setSubmittingPriority(false);
    }
  };

  if (loading) {
    return <Loader label="Loading location dashboard..." variant="skeleton" />;
  }
  if (error) {
    return <EmptyState title="Dashboard Unavailable" description={error} />;
  }

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

      {/* Pinned Emergencies at Top (Rule 2.4c) */}
      <PinnedEmergenciesBanner onActionDone={reload} />

      {/* Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Good morning, {user?.name || "Warden"}
            </h1>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-md bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
              <Building className="h-3 w-3 inline mr-1 text-purple-600" />
              {locationTitle}
            </span>
          </div>
          <p className="text-xs font-normal text-slate-500 dark:text-slate-400 mt-1">
            Facility Oversight & Verification Authority • {needsMyVerificationComplaints.length} tickets awaiting in-person inspection
          </p>
        </div>
        <div className="flex items-center gap-2.5 shrink-0">
          <Button
            onClick={() => navigate("/complaints")}
            variant="outline"
            size="md"
            className="font-medium shrink-0 flex items-center gap-1.5"
          >
            <Shield className="h-4 w-4" />
            Location Complaints
          </Button>
        </div>
      </div>

      {/* Main Action Pills Block */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-3">
        <ActionPill
          icon={UserCheck}
          label={t("pills.needs_verification", "Needs verification")}
          count={needsMyVerificationComplaints.length}
          onClick={() => {
            const el = document.getElementById("verification-section");
            if (el) el.scrollIntoView({ behavior: "smooth" });
          }}
          tone="purple"
        />
        <ActionPill
          icon={AlertTriangle}
          label={t("pills.overdue", "Overdue")}
          count={overdueComplaints.length}
          onClick={() => navigate("/complaints", { state: { sla: "Overdue" } })}
          tone="rose"
        />
        <ActionPill
          icon={Megaphone}
          label={t("pills.post_notice", "Post notice")}
          to="/announcements"
          tone="emerald"
        />
      </div>

      {/* Top Alerts Panel */}
      {(overdueComplaints.length > 0 || blockedTooLongComplaints.length > 0 || unclaimedComplaints.length > 0 || photoSkipComplaints.length > 0) && (
        <div className="space-y-2">
          {overdueComplaints.length > 0 && (
            <div className="p-3 rounded-xl border border-rose-200 dark:border-rose-900 bg-rose-50/70 dark:bg-rose-950/30 text-rose-900 dark:text-rose-200 text-xs font-semibold flex items-center justify-between">
              <span className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-600 shrink-0" />
                ⚠️ {overdueComplaints.length} overdue complaint(s) breaching resolution turnaround target!
              </span>
              <Button size="sm" variant="outline" onClick={() => navigate("/complaints", { state: { sla: "Overdue" } })} className="text-[11px] py-1">
                View Overdue
              </Button>
            </div>
          )}
          {blockedTooLongComplaints.length > 0 && (
            <div className="p-3 rounded-xl border border-amber-200 dark:border-amber-900 bg-amber-50/70 dark:bg-amber-950/30 text-amber-900 dark:text-amber-200 text-xs font-semibold flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Clock className="h-4 w-4 text-amber-600 shrink-0" />
                ⚠️ {blockedTooLongComplaints.length} complaint(s) waiting for parts for &gt;72 hours without resolution.
              </span>
              <Button size="sm" variant="outline" onClick={() => navigate("/complaints", { state: { status: "Waiting for Parts" } })} className="text-[11px] py-1">
                Inspect Blocked
              </Button>
            </div>
          )}
          {unclaimedComplaints.length > 0 && (
            <div className="p-3 rounded-xl border border-blue-200 dark:border-blue-900 bg-blue-50/70 dark:bg-blue-950/30 text-blue-900 dark:text-blue-200 text-xs font-semibold flex items-center justify-between">
              <span className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-blue-600 shrink-0" />
                ⚠️ {unclaimedComplaints.length} complaint(s) went unclaimed past acceptance deadline.
              </span>
              <Button size="sm" variant="outline" onClick={() => navigate("/complaints", { state: { status: "unassigned" } })} className="text-[11px] py-1">
                Review Unclaimed
              </Button>
            </div>
          )}
          {photoSkipComplaints.length > 0 && (
            <div className="p-3 rounded-xl border border-purple-200 dark:border-purple-900 bg-purple-50/70 dark:bg-purple-950/30 text-purple-900 dark:text-purple-200 text-xs font-semibold flex items-center justify-between">
              <span className="flex items-center gap-2">
                <ImageIcon className="h-4 w-4 text-purple-600 shrink-0" />
                📸 {photoSkipComplaints.length} complaint(s) with skipped photos or active skip streaks.
              </span>
            </div>
          )}
        </div>
      )}

      {/* 4 Key Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <StatCard
          label="Needs My Verification"
          value={needsMyVerificationComplaints.length}
          accent={needsMyVerificationComplaints.length > 0}
          subtext="Physical in-person inspection"
        />
        <StatCard
          label="Active Problems"
          value={activeProblems.length}
          subtext="Under repair across facility"
          onClick={() => navigate("/complaints", { state: { status: "active" } })}
        />
        <StatCard
          label="Overdue / SLA Risk"
          value={overdueComplaints.length}
          accent={overdueComplaints.length > 0}
          subtext={overdueComplaints.length > 0 ? "Breaching turnaround SLA" : "Within turnaround target"}
          onClick={() => navigate("/complaints", { state: { sla: "Overdue" } })}
        />
        <StatCard
          label="Coordinators Tracked"
          value={coordinatorStats.length}
          subtext="Field operations personnel"
        />
      </div>

      {/* Needs My Verification Section */}
      <div id="verification-section" className="rounded-xl border border-purple-200/80 dark:border-purple-900/60 bg-white dark:bg-[#101726] shadow-xs overflow-hidden">
        <div className="p-4 sm:p-5 border-b border-purple-100 dark:border-purple-900/40 bg-purple-50/40 dark:bg-purple-950/20 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-purple-100 dark:bg-purple-900/50 text-purple-700 dark:text-purple-300">
              <UserCheck className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-purple-950 dark:text-purple-100">
                Needs My Verification ({needsMyVerificationComplaints.length})
              </h2>
              <p className="text-xs text-purple-800/80 dark:text-purple-300/80">
                Complaints marked fixed by coordinators that require your physical in-person inspection.
              </p>
            </div>
          </div>
          <Button size="sm" variant="ghost" onClick={reload} className="text-xs">
            Refresh List
          </Button>
        </div>

        <div className="p-5">
          {needsMyVerificationComplaints.length === 0 ? (
            <div className="py-8 text-center text-slate-400 dark:text-slate-500">
              <CheckCircle2 className="h-8 w-8 mx-auto mb-2 text-emerald-500 opacity-80" />
              <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                All inspections up to date
              </p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                No tickets are currently pending your in-person verification.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {needsMyVerificationComplaints.map((c) => {
                const isSelfWork =
                  user?.user_id === c.assigned_to ||
                  user?.email === c.assigned_to ||
                  user?.user_id === c.created_by;

                return (
                  <div
                    key={c.complaint_id}
                    className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30 space-y-3 hover:border-purple-300 dark:hover:border-purple-800 transition-colors"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2">
                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <Link
                            to={`/complaints/${c.complaint_id}`}
                            className="text-sm font-bold text-slate-900 dark:text-slate-100 hover:text-primary transition-colors"
                          >
                            {c.title || "Untitled Issue"}
                          </Link>
                          <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-slate-200/80 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                            {c.complaint_id}
                          </span>
                          <Badge tone={getPriorityTone(c.priority)}>
                            {c.priority || "Medium"}
                          </Badge>
                          {c.is_spot_check && (
                            <Badge tone="purple">Spot Check (~10%)</Badge>
                          )}
                        </div>
                        <p className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                          <strong>Reported Problem:</strong> {c.description}
                        </p>
                        {c.resolution_notes && (
                          <div className="text-xs text-emerald-800 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/30 p-2.5 rounded-lg border border-emerald-200 dark:border-emerald-900/40 mt-1">
                            <strong>Coordinator Resolution Notes:</strong> "{c.resolution_notes}"
                          </div>
                        )}
                        <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 pt-1">
                          <span>Department: {c.department_name || c.department_id}</span>
                          <span>•</span>
                          <span>Fixed by: {c.fixed_by || c.assigned_to}</span>
                          <span>•</span>
                          <span>Completed on: {c.fixed_at ? formatDate(c.fixed_at) : "Recently"}</span>
                        </div>
                      </div>

                      {/* Action Buttons */}
                      <div className="flex flex-wrap items-center gap-2 shrink-0 pt-2 sm:pt-0">
                        {isSelfWork ? (
                          <span className="text-xs text-amber-600 dark:text-amber-400 italic font-medium px-2 py-1 bg-amber-50 dark:bg-amber-950/40 rounded-md border border-amber-200">
                            Self-verification guard active
                          </span>
                        ) : (
                          <>
                            <Button
                              size="sm"
                              variant="success"
                              onClick={() => {
                                setVerifyModalTicket(c);
                                setVerifyNotes("");
                              }}
                              className="font-bold text-xs flex items-center gap-1 shadow-2xs"
                            >
                              <Check className="h-3.5 w-3.5" />
                              Verified
                            </Button>
                            <Button
                              size="sm"
                              variant="danger"
                              onClick={() => {
                                setRejectModalTicket(c);
                                setRejectReason("");
                              }}
                              className="font-bold text-xs flex items-center gap-1 shadow-2xs"
                            >
                              <XCircle className="h-3.5 w-3.5" />
                              Not Fixed
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handlePhotoMismatch(c)}
                              className="font-semibold text-xs flex items-center gap-1 text-amber-700 dark:text-amber-300 border-amber-300 hover:bg-amber-50 dark:hover:bg-amber-950/30"
                            >
                              <ImageIcon className="h-3.5 w-3.5" />
                              Photo doesn't match
                            </Button>
                          </>
                        )}

                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setPriorityModalTicket(c);
                            setNewPriority(c.priority || "Medium");
                            setPriorityChangeReason("");
                          }}
                          className="text-xs flex items-center gap-1"
                        >
                          <Edit className="h-3 w-3" />
                          Change Priority
                        </Button>

                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => navigate(`/complaints/${c.complaint_id}`)}
                          className="text-xs"
                        >
                          View
                        </Button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Facility Watch List Section (Rule K4) */}
      <div className="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-[#101726] shadow-xs overflow-hidden">
        <div className="p-4 sm:p-5 border-b border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/30 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300">
              <Shield className="h-4 w-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                Facility Watch List ({watchListComplaints.length})
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Active issues across your facility showing team and assigned worker.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={filterLeaveOnly}
                onChange={(e) => setFilterLeaveOnly(e.target.checked)}
                className="rounded text-blue-600"
              />
              Filter: Assignee on leave
            </label>
            <Button size="sm" variant="ghost" onClick={reload} className="text-xs">
              Refresh
            </Button>
          </div>
        </div>

        <div className="p-5">
          {watchListComplaints.length === 0 ? (
            <div className="py-8 text-center text-slate-400 dark:text-slate-500">
              <CheckCircle2 className="h-8 w-8 mx-auto mb-2 text-emerald-500 opacity-80" />
              <p className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                No active complaints
              </p>
              <p className="text-[11px] text-slate-400 mt-0.5">
                All facility complaints have been resolved.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {watchListComplaints.map((c) => {
                const team = teams.find((t) => t.team_id === c.team_id);
                const canWardenAssign =
                  Number(c.assign_escalation_level || 0) >= 2 || !c.team_id || !c.assigned_to;

                return (
                  <div
                    key={c.complaint_id}
                    className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col sm:flex-row sm:items-center justify-between gap-3 hover:border-slate-300 dark:hover:border-slate-700 transition"
                  >
                    <div className="space-y-1 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <Link
                          to={`/complaints/${c.complaint_id}`}
                          className="text-sm font-bold text-slate-900 dark:text-slate-100 hover:text-primary transition-colors"
                        >
                          {c.title || c.category}
                        </Link>
                        <Badge tone={getPriorityTone(c.priority)}>
                          {c.priority || "Medium"}
                        </Badge>
                        <Badge tone={getStatusTone(c.status)}>
                          {c.status}
                        </Badge>
                        {c.assignee_on_leave_flag && (
                          <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-300">
                            Assignee on leave
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                        <span className="font-semibold text-slate-700 dark:text-slate-300">
                          Team: {c.team_name || team?.name || "General Maintenance"}
                        </span>
                        <span>•</span>
                        <span>Worker: {c.assigned_to || "Unassigned"}</span>
                        {c.sla_deadline && (
                          <>
                            <span>•</span>
                            <span>SLA: {formatDate(c.sla_deadline)}</span>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      {canWardenAssign && (
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() => setAssignModalComplaint(c)}
                          className="font-bold text-xs"
                        >
                          Assign
                        </Button>
                      )}
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => navigate(`/complaints/${c.complaint_id}`)}
                        className="text-xs"
                      >
                        View
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Coordinator Performance Stats Card */}
      <div className="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-[#101726] p-5 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
          <div className="flex items-center gap-2">
            <Award className="h-4 w-4 text-primary" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-900 dark:text-slate-100">
              Coordinator Performance & Operational Metrics
            </h2>
          </div>
          <span className="text-[11px] text-slate-400">
            30-day turnaround performance
          </span>
        </div>

        {loadingStats ? (
          <Loader label="Loading coordinator statistics..." variant="skeleton" />
        ) : coordinatorStats.length === 0 ? (
          <p className="text-xs text-slate-400 py-4 text-center">
            No coordinator performance metrics recorded yet.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-slate-100 dark:border-slate-800 text-[10px] font-bold uppercase text-slate-400">
                  <th className="py-2.5 px-3">Coordinator</th>
                  <th className="py-2.5 px-3 text-center">Assigned</th>
                  <th className="py-2.5 px-3 text-center">In Progress</th>
                  <th className="py-2.5 px-3 text-center">Resolved (30d)</th>
                  <th className="py-2.5 px-3 text-center">Avg Resolution Time</th>
                  <th className="py-2.5 px-3 text-center">Reopen Rate</th>
                  <th className="py-2.5 px-3 text-center">Overdue</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
                {coordinatorStats.map((cs) => (
                  <tr key={cs.coordinator_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/30">
                    <td className="py-2.5 px-3 font-medium text-slate-900 dark:text-slate-100">
                      <div>{cs.name}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{cs.email}</div>
                    </td>
                    <td className="py-2.5 px-3 text-center font-semibold text-slate-700 dark:text-slate-300">
                      {cs.assigned_count}
                    </td>
                    <td className="py-2.5 px-3 text-center font-semibold text-blue-600 dark:text-blue-400">
                      {cs.in_progress_count}
                    </td>
                    <td className="py-2.5 px-3 text-center font-semibold text-emerald-600 dark:text-emerald-400">
                      {cs.resolved_last_30_days}
                    </td>
                    <td className="py-2.5 px-3 text-center font-mono">
                      {cs.avg_resolution_hours ? `${cs.avg_resolution_hours}h` : "N/A"}
                    </td>
                    <td className="py-2.5 px-3 text-center font-mono">
                      <span className={cs.reopen_rate > 10 ? "text-rose-600 font-bold" : "text-slate-600 dark:text-slate-300"}>
                        {cs.reopen_rate}%
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-center font-bold">
                      <span className={cs.overdue_count > 0 ? "text-rose-600" : "text-slate-400"}>
                        {cs.overdue_count}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modals */}

      {/* Verify Fixed Modal */}
      {verifyModalTicket && (
        <Modal
          isOpen={Boolean(verifyModalTicket)}
          onClose={() => setVerifyModalTicket(null)}
          title="🛡️ Confirm Physical In-Person Verification"
        >
          <div className="space-y-4">
            <p className="text-xs text-slate-500">
              Confirm that you have physically inspected ticket <strong>{verifyModalTicket.complaint_id}</strong> on-site and the problem is completely fixed.
            </p>
            <Textarea
              label="Inspection Notes (Optional)"
              value={verifyNotes}
              onChange={(e) => setVerifyNotes(e.target.value)}
              placeholder="e.g. Inspected switchboard in person; safe, clean, and fully operational..."
              rows={3}
            />
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button type="button" variant="outline" onClick={() => setVerifyModalTicket(null)}>
                Cancel
              </Button>
              <Button type="button" variant="success" disabled={submittingVerify} onClick={handleVerifyFixed}>
                {submittingVerify ? "Confirming..." : "Confirm & Advance Ticket"}
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Not Fixed Modal */}
      {rejectModalTicket && (
        <Modal
          isOpen={Boolean(rejectModalTicket)}
          onClose={() => setRejectModalTicket(null)}
          title="⚠️ Report Work Not Fixed (Send for Rework)"
        >
          <form onSubmit={handleReportNotFixed} className="space-y-4">
            <p className="text-xs text-slate-500">
              Specify what remains broken or deficient on ticket <strong>{rejectModalTicket.complaint_id}</strong>. The coordinator will be notified to perform rework.
            </p>
            <Textarea
              label="Reason Not Fixed (Mandatory)"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g. Switch cover plate not mounted, exposed terminals still visible..."
              rows={4}
              required
            />
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button type="button" variant="outline" onClick={() => setRejectModalTicket(null)}>
                Cancel
              </Button>
              <Button type="submit" variant="danger" disabled={submittingReject || !rejectReason.trim()}>
                {submittingReject ? "Submitting..." : "Send for Rework"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Priority Change Modal */}
      {priorityModalTicket && (
        <Modal
          isOpen={Boolean(priorityModalTicket)}
          onClose={() => setPriorityModalTicket(null)}
          title="⚡ Change Complaint Priority"
        >
          <form onSubmit={handlePrioritySubmit} className="space-y-4">
            <p className="text-xs text-slate-500">
              Adjust priority on ticket <strong>{priorityModalTicket.complaint_id}</strong>. A mandatory reason is required for the audit record.
            </p>
            <Select
              label="New Priority Level"
              value={newPriority}
              onChange={(e) => setNewPriority(e.target.value)}
            >
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
              <option value="Critical">Critical</option>
            </Select>
            <Textarea
              label="Reason for Priority Change"
              value={priorityChangeReason}
              onChange={(e) => setPriorityChangeReason(e.target.value)}
              placeholder="Explain why priority is being modified (e.g. resident safety risk escalated)..."
              rows={3}
              required
            />
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button type="button" variant="outline" onClick={() => setPriorityModalTicket(null)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" disabled={submittingPriority || !priorityChangeReason.trim()}>
                {submittingPriority ? "Updating..." : "Update Priority"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Assign Modal (Rule K4) */}
      <AssignModal
        isOpen={Boolean(assignModalComplaint)}
        onClose={() => setAssignModalComplaint(null)}
        complaint={assignModalComplaint}
        onAssigned={reload}
      />
    </div>
  );
}

