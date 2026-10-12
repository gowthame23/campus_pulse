import { useMemo, useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Wrench,
  Clock,
  AlertTriangle,
  MapPin,
  CheckCircle2,
  Calendar,
  MoreVertical,
  Play,
  PlayCircle,
  Pause,
  RotateCcw,
  Navigation,
  FileText,
  Camera,
  Check,
  TrendingUp,
  RefreshCw,
  Building,
  User,
  Users,
  Shield,
  Key,
  Phone,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import ActionPill from "../../components/ActionPill.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import StatCard from "../../components/StatCard.jsx";
import Badge from "../../components/Badge.jsx";
import Modal from "../../components/Modal.jsx";
import Toast from "../../components/Toast.jsx";
import AssignModal from "../../components/AssignModal.jsx";
import LeaveModal from "../../components/LeaveModal.jsx";
import FixerOfTheMonthWidget from "../../components/FixerOfTheMonthWidget.jsx";
import PinnedEmergenciesBanner from "../../components/PinnedEmergenciesBanner.jsx";
import CredentialSlipModal from "../../components/CredentialSlipModal.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { useLanguage } from "../../context/LanguageContext.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { complaintService } from "../../services/complaintService.js";
import { announcementService } from "../../services/announcementService.js";
import { notificationService } from "../../services/notificationService.js";
import { locationService } from "../../services/locationService.js";
import { departmentService } from "../../services/departmentService.js";
import { teamService } from "../../services/teamService.js";
import { setupService } from "../../services/setupService.js";
import { leaveService } from "../../services/leaveService.js";
import { formatDate } from "../../utils/dateFormatter.js";
import { getStatusTone, getPriorityTone } from "../../utils/statusColor.js";

const getLocationName = (locId, locations = []) => {
  if (!locId) return "";
  const match = (locations || []).find((l) => l.location_id === locId || l.name === locId);
  if (match && match.name) return match.name;
  return locId;
};

const PRESET_WORKER_NOTES = [
  { code: "NEED_PARTS", label: "Need parts" },
  { code: "WAITING_ACCESS", label: "Waiting for access" },
  { code: "WORKSHOP", label: "Sent to workshop" },
  { code: "INVESTIGATING", label: "Investigating on site" },
];

export default function CoordinatorDashboard() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState("to_assign"); // "to_assign" | "team_board" | "my_jobs" | "stats"
  const [toastMessage, setToastMessage] = useState("");
  const [toastTone, setToastTone] = useState("success");

  // Modals state
  const [assignModalComplaint, setAssignModalComplaint] = useState(null);
  const [showLeaveModal, setShowLeaveModal] = useState(false);

  // My Jobs Action Modals
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [resolveNotesText, setResolveNotesText] = useState("");
  const [resolvePreset, setResolvePreset] = useState("");
  const [proofUrl, setProofUrl] = useState("");
  const [isPhotoSkipped, setIsPhotoSkipped] = useState(false);
  const [photoSkipReason, setPhotoSkipReason] = useState("");
  const [submittingResolve, setSubmittingResolve] = useState(false);
  const [resolveError, setResolveError] = useState("");

  const [showPartsModal, setShowPartsModal] = useState(false);
  const [partsReason, setPartsReason] = useState("");
  const [partsExpectedDate, setPartsExpectedDate] = useState("");
  const [pausingParts, setPausingParts] = useState(false);

  const [showWrongLocModal, setShowWrongLocModal] = useState(false);
  const [newLocationId, setNewLocationId] = useState("");
  const [wrongLocNote, setWrongLocNote] = useState("");
  const [reportingWrongLoc, setReportingWrongLoc] = useState(false);

  const [showReturnModal, setShowReturnModal] = useState(false);
  const [returnReason, setReturnReason] = useState("");
  const [returning, setReturning] = useState(false);

  const [openMenuComplaintId, setOpenMenuComplaintId] = useState(null);

  const {
    data: dashboardData,
    loading,
    reload,
  } = useAsyncData(
    async () => {
      const [compRes, locRes, deptRes, teamsRes, leavesRes, statsRes] = await Promise.all([
        complaintService.list({ include_archived: false }).catch(() => ({ data: [] })),
        locationService.list().catch(() => ({ data: [] })),
        departmentService.list().catch(() => ({ data: [] })),
        teamService.list({ active_only: true }).catch(() => ({ data: [] })),
        leaveService.list({ active_only: true }).catch(() => ({ data: [] })),
        complaintService.getCoordinatorStats().catch(() => ({ data: {} })),
      ]);

      return {
        complaints: compRes.data?.complaints || compRes.data || [],
        locations: locRes.data || locRes || [],
        departments: deptRes.data || deptRes || [],
        teams: teamsRes.data || teamsRes || [],
        leaves: leavesRes.data || leavesRes || [],
        stats: statsRes.data || statsRes || {},
      };
    },
    { complaints: [], locations: [], departments: [], teams: [], leaves: [], stats: {} }
  );

  const complaints = dashboardData?.complaints || [];
  const locations = dashboardData?.locations || [];
  const departments = dashboardData?.departments || [];
  const teams = dashboardData?.teams || [];
  const leaves = dashboardData?.leaves || [];
  const stats = dashboardData?.stats || {};

  // Find teams where user is coordinator or backup
  const myPrimaryTeams = useMemo(
    () => teams.filter((t) => t.coordinator_id === user?.user_id),
    [teams, user]
  );

  const todayStr = new Date().toISOString().slice(0, 10);

  // Rule B4: Acting Coordinator Banners
  // When user is backup_coordinator_id and the primary coordinator is on leave today
  const actingTeams = useMemo(() => {
    return teams.filter((t) => {
      if (t.backup_coordinator_id !== user?.user_id) return false;
      const primaryOnLeave = leaves.some(
        (l) => l.user_id === t.coordinator_id && l.from_date <= todayStr && todayStr <= l.to_date
      );
      return primaryOnLeave;
    });
  }, [teams, leaves, user, todayStr]);

  // All team IDs this coordinator currently controls (primary or acting)
  const controlledTeamIds = useMemo(() => {
    const ids = new Set(myPrimaryTeams.map((t) => t.team_id));
    actingTeams.forEach((t) => ids.add(t.team_id));
    return ids;
  }, [myPrimaryTeams, actingTeams]);

  // Main section 1: "To assign" (queue of unassigned complaints for his teams)
  // Sorted by deadline soonest first (Part K1)
  const toAssignComplaints = useMemo(() => {
    return complaints
      .filter((c) => {
        const isNotClosed = !c.status?.startsWith("Closed");
        const needsAssign = !c.assigned_to || c.status === "Submitted" || c.status === "Awaiting Coordinator Assignment";
        if (!isNotClosed || !needsAssign) return false;
        if (c.team_id && controlledTeamIds.has(c.team_id)) return true;
        // Check if complaint matches any controlled team's department and location
        return teams.some(
          (t) =>
            controlledTeamIds.has(t.team_id) &&
            t.department_id === c.department_id &&
            t.location_ids?.includes(c.location_id)
        );
      })
      .sort((a, b) => {
        const getDeadlineMs = (comp) => {
          const deadlineHours = { Critical: 0.5, High: 2, Medium: 4, Low: 8 }[comp.priority] || 4;
          const start = new Date(comp.awaiting_assign_since || comp.created_at || 0).getTime();
          return start + deadlineHours * 3600 * 1000;
        };
        return getDeadlineMs(a) - getDeadlineMs(b);
      });
  }, [complaints, controlledTeamIds, teams]);

  // Main section 2: "Team board" (active jobs across the team)
  const teamBoardComplaints = useMemo(() => {
    return complaints.filter((c) => {
      const isNotClosed = !c.status?.startsWith("Closed");
      const hasWorker = Boolean(c.assigned_to) && c.status !== "Submitted";
      if (!isNotClosed || !hasWorker) return false;
      if (c.team_id && controlledTeamIds.has(c.team_id)) return true;
      return teams.some(
        (t) =>
          controlledTeamIds.has(t.team_id) &&
          t.department_id === c.department_id &&
          t.location_ids?.includes(c.location_id)
      );
    });
  }, [complaints, controlledTeamIds, teams]);

  // Main section 3: "My jobs" (jobs assigned to the coordinator himself)
  const myJobs = useMemo(() => {
    return complaints.filter((c) => {
      const isMine = c.assigned_to === user?.user_id;
      const isNotClosed = !c.status?.startsWith("Closed");
      return isMine && isNotClosed;
    });
  }, [complaints, user]);

  // Countdown badge for "To assign" (Part K1)
  const getAssignCountdownBadge = (c) => {
    const priority = c.priority || "Medium";
    const hours = { Critical: 0.5, High: 2, Medium: 4, Low: 8 }[priority] || 4;
    const start = new Date(c.awaiting_assign_since || c.created_at || Date.now()).getTime();
    const deadlineMs = start + hours * 3600 * 1000;
    const diff = deadlineMs - Date.now();
    const isOverdue = diff <= 0;
    const absDiff = Math.abs(diff);
    const m = Math.floor(absDiff / (1000 * 60));
    const h = Math.floor(m / 60);
    const remM = m % 60;
    const timeStr = h > 0 ? `${h}h ${remM}m` : `${remM}m`;

    if (isOverdue) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-bold bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-300 dark:border-rose-800 animate-pulse">
          <AlertTriangle className="h-3.5 w-3.5" />
          {priority} — Overdue by {timeStr}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
        <Clock className="h-3.5 w-3.5" />
        {priority} — {timeStr} left to assign
      </span>
    );
  };

  // Actions for My Jobs
  const handleStartWork = async (job) => {
    try {
      await complaintService.updateStatus(job.complaint_id, "In Progress");
      setToastTone("success");
      setToastMessage("Job started (In Progress).");
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Failed to start work.");
    }
  };

  const handlePresetNote = async (job, presetObj) => {
    try {
      await complaintService.recordProgress(job.complaint_id, presetObj.label, null, presetObj.code);
      setToastTone("success");
      setToastMessage(`Progress note logged: ${presetObj.label}`);
      setOpenMenuComplaintId(null);
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Failed to log progress note.");
    }
  };

  const handleOpenResolveModal = (c) => {
    setSelectedComplaint(c);
    setResolveNotesText("");
    setResolvePreset("");
    setProofUrl("");
    setIsPhotoSkipped(false);
    setPhotoSkipReason("");
    setResolveError("");
    setShowResolveModal(true);
    setOpenMenuComplaintId(null);
  };

  const handleConfirmResolve = async (e) => {
    e.preventDefault();
    if (!selectedComplaint) return;

    const studentHadPhoto = Boolean(selectedComplaint.attachment_url);
    if (studentHadPhoto && !proofUrl.trim() && !isPhotoSkipped) {
      setResolveError("Photo is required when student provided a photo (or check Skip Photo).");
      return;
    }
    if (!studentHadPhoto && !proofUrl.trim() && !resolveNotesText.trim() && !resolvePreset) {
      setResolveError("Please provide resolution notes or select a preset note.");
      return;
    }

    setSubmittingResolve(true);
    setResolveError("");
    try {
      await complaintService.resolve(selectedComplaint.complaint_id, {
        notes: resolveNotesText.trim() || undefined,
        preset_code: resolvePreset || undefined,
        proof_url: proofUrl.trim() || undefined,
        skip_photo: isPhotoSkipped,
        photo_skip_reason: isPhotoSkipped ? photoSkipReason.trim() : undefined,
      });
      setToastTone("success");
      setToastMessage("Complaint marked resolved!");
      setShowResolveModal(false);
      setSelectedComplaint(null);
      reload();
    } catch (err) {
      setResolveError(err.response?.data?.detail || "Failed to resolve complaint.");
    } finally {
      setSubmittingResolve(false);
    }
  };

  const handleConfirmParts = async () => {
    if (!partsReason.trim()) return;
    setPausingParts(true);
    try {
      await complaintService.block(selectedComplaint.complaint_id, partsReason.trim(), partsExpectedDate || null);
      setToastTone("success");
      setToastMessage("Complaint marked Waiting for Parts.");
      setShowPartsModal(false);
      setSelectedComplaint(null);
      setPartsReason("");
      setPartsExpectedDate("");
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Failed to pause for parts.");
    } finally {
      setPausingParts(false);
    }
  };

  const handleConfirmWrongLocation = async () => {
    if (!newLocationId) return;
    setReportingWrongLoc(true);
    try {
      await complaintService.reportWrongLocation(selectedComplaint.complaint_id, newLocationId, wrongLocNote.trim());
      setToastTone("success");
      setToastMessage("Wrong location updated. Re-routed to the correct team.");
      setShowWrongLocModal(false);
      setSelectedComplaint(null);
      setNewLocationId("");
      setWrongLocNote("");
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Failed to update location.");
    } finally {
      setReportingWrongLoc(false);
    }
  };

  const handleConfirmReturn = async () => {
    if (!returnReason.trim()) return;
    setReturning(true);
    try {
      await complaintService.returnToCoordinator(selectedComplaint.complaint_id, returnReason.trim());
      setToastTone("success");
      setToastMessage("Returned job to queue.");
      setShowReturnModal(false);
      setSelectedComplaint(null);
      setReturnReason("");
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Failed to return job.");
    } finally {
      setReturning(false);
    }
  };

  const [teamMembersList, setTeamMembersList] = useState([]);
  const [loadingMembers, setLoadingMembers] = useState(false);
  const [slipData, setSlipData] = useState(null);

  useEffect(() => {
    if (activeTab === "team_members") {
      loadAllTeamMembers();
    }
  }, [activeTab, myPrimaryTeams, actingTeams]);

  const loadAllTeamMembers = async () => {
    setLoadingMembers(true);
    try {
      const allMembers = [];
      for (const t of [...myPrimaryTeams, ...actingTeams]) {
        const res = await teamService.getMembers(t.team_id);
        const mList = res.data || res || [];
        mList.forEach((m) => {
          allMembers.push({ ...m, team_id: t.team_id, team_name: t.name });
        });
      }
      const unique = [];
      const seen = new Set();
      for (const m of allMembers) {
        if (!seen.has(m.user_id)) {
          seen.add(m.user_id);
          unique.push(m);
        }
      }
      setTeamMembersList(unique);
    } catch (err) {
      console.error("Failed to load team members:", err);
    } finally {
      setLoadingMembers(false);
    }
  };

  const handleResetWorkerPassword = async (member) => {
    try {
      const res = await setupService.resetTeamMemberPassword(member.team_id, member.user_id);
      setSlipData(res);
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Failed to reset worker password.");
    }
  };

  const teamNameDisplay = myPrimaryTeams.length > 0 ? myPrimaryTeams.map((t) => t.name).join(", ") : "Maintenance Team";

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Toast Notification */}
      {toastMessage && (
        <Toast message={toastMessage} tone={toastTone} onClose={() => setToastMessage("")} />
      )}

      {/* Pinned Emergencies at Top (Rule 2.4c) */}
      <PinnedEmergenciesBanner onActionDone={reload} />

      {/* Acting Coordinator Banner (Rule B4 & K1) */}
      {actingTeams.map((t) => {
        const l = leaves.find((lev) => lev.user_id === t.coordinator_id);
        const leaveTo = l ? l.to_date : "return";
        return (
          <div
            key={t.team_id}
            className="p-4 rounded-2xl bg-amber-500/10 border-2 border-amber-500/40 text-amber-900 dark:text-amber-200 text-sm font-bold flex items-center justify-between gap-3 shadow-sm"
          >
            <div className="flex items-center gap-2.5">
              <Shield className="h-5 w-5 text-amber-600 shrink-0" />
              <span>
                Acting coordinator for Team {t.name} (Coordinator on leave until {leaveTo})
              </span>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-500/20 text-amber-800 dark:text-amber-200">
              Active Coverage
            </span>
          </div>
        );
      })}

      {/* Top Bar (Rule K1) */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 sm:p-6 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Users className="h-5 w-5 text-blue-600" />
            {user?.name || "Coordinator"}
          </div>
          <div className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Team: <span className="font-semibold text-slate-800 dark:text-slate-200">{teamNameDisplay}</span>
          </div>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Button
            variant="secondary"
            className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 text-xs font-semibold"
            onClick={() => setShowLeaveModal(true)}
          >
            <Calendar className="h-4 w-4 text-amber-500" />
            I am on leave
          </Button>
          <Button variant="ghost" className="p-2" onClick={reload} title="Refresh">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Main Action Pills Block */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 sm:gap-3">
        <ActionPill
          icon={Clock}
          label={t("pills.to_assign", "To assign")}
          count={toAssignComplaints.length}
          active={activeTab === "to_assign"}
          onClick={() => setActiveTab("to_assign")}
          tone="amber"
        />
        <ActionPill
          icon={Users}
          label={t("pills.team_board", "Team board")}
          active={activeTab === "team_board"}
          onClick={() => setActiveTab("team_board")}
          tone="purple"
        />
        <ActionPill
          icon={Wrench}
          label={t("pills.my_jobs", "My jobs")}
          count={myJobs.length}
          active={activeTab === "my_jobs"}
          onClick={() => setActiveTab("my_jobs")}
          tone="blue"
        />
      </div>

      {/* 4 Summary Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <StatCard
          label="To Assign"
          value={toAssignComplaints.length}
          accent={toAssignComplaints.length > 0}
          subtext="Needs worker assignment"
          onClick={() => setActiveTab("to_assign")}
        />
        <StatCard
          label="Team Board"
          value={teamBoardComplaints.length}
          subtext="Active jobs across team"
          onClick={() => setActiveTab("team_board")}
        />
        <StatCard
          label="My Jobs"
          value={myJobs.length}
          subtext="Assigned to me directly"
          onClick={() => setActiveTab("my_jobs")}
        />
        <StatCard
          label="Avg Time to Assign"
          value={stats?.avg_time_to_assign ? `${stats.avg_time_to_assign}h` : "N/A"}
          subtext="Team responsiveness"
          onClick={() => setActiveTab("stats")}
        />
      </div>

      {/* Fixer of the Month Staff Recognition Banner */}
      <FixerOfTheMonthWidget />

      {/* Main Four-Tab Interface (Part K1) */}
      <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm overflow-hidden">
        {/* Tab Switcher */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/50 overflow-x-auto">
          <button
            type="button"
            onClick={() => setActiveTab("to_assign")}
            className={`flex items-center gap-2 px-6 py-3.5 text-xs font-bold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === "to_assign"
                ? "border-blue-600 text-blue-600 dark:text-blue-400 bg-white dark:bg-slate-900"
                : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            <Clock className="h-4 w-4" />
            To assign
            <span className={`px-2 py-0.5 text-[10px] rounded-full font-bold ${
              activeTab === "to_assign" ? "bg-blue-600 text-white" : "bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
            }`}>
              {toAssignComplaints.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("team_board")}
            className={`flex items-center gap-2 px-6 py-3.5 text-xs font-bold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === "team_board"
                ? "border-blue-600 text-blue-600 dark:text-blue-400 bg-white dark:bg-slate-900"
                : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            <Users className="h-4 w-4" />
            Team board
            <span className={`px-2 py-0.5 text-[10px] rounded-full font-bold ${
              activeTab === "team_board" ? "bg-blue-600 text-white" : "bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
            }`}>
              {teamBoardComplaints.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("my_jobs")}
            className={`flex items-center gap-2 px-6 py-3.5 text-xs font-bold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === "my_jobs"
                ? "border-blue-600 text-blue-600 dark:text-blue-400 bg-white dark:bg-slate-900"
                : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            <Wrench className="h-4 w-4" />
            My jobs
            <span className={`px-2 py-0.5 text-[10px] rounded-full font-bold ${
              activeTab === "my_jobs" ? "bg-blue-600 text-white" : "bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
            }`}>
              {myJobs.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("stats")}
            className={`flex items-center gap-2 px-6 py-3.5 text-xs font-bold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === "stats"
                ? "border-blue-600 text-blue-600 dark:text-blue-400 bg-white dark:bg-slate-900"
                : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            <TrendingUp className="h-4 w-4" />
            Stats & Performance
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("team_members")}
            className={`flex items-center gap-2 px-6 py-3.5 text-xs font-bold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
              activeTab === "team_members"
                ? "border-blue-600 text-blue-600 dark:text-blue-400 bg-white dark:bg-slate-900"
                : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            <Users className="h-4 w-4" />
            Team Workforce
          </button>
        </div>

        {/* TAB 1: TO ASSIGN (Queue) */}
        {activeTab === "to_assign" && (
          <div className="p-5 space-y-4">
            <div className="flex items-center justify-between pb-2">
              <span className="text-xs text-slate-500 font-medium">
                Complaints waiting for assignment, sorted by deadline (soonest first).
              </span>
              <Button size="sm" variant="ghost" onClick={reload} className="text-xs">
                Refresh Queue
              </Button>
            </div>

            {toAssignComplaints.length === 0 ? (
              <EmptyState
                title="All Complaints Assigned"
                description="Your team's intake queue is completely clear! No complaints are currently waiting to be assigned."
              />
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {toAssignComplaints.map((c) => (
                  <div
                    key={c.complaint_id}
                    className="py-4 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-3 rounded-xl hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors"
                  >
                    <div className="space-y-1.5 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <Link
                          to={`/complaints/${c.complaint_id}`}
                          className="text-sm font-bold text-slate-900 dark:text-slate-100 hover:text-blue-600 transition-colors"
                        >
                          {c.title || c.category}
                        </Link>
                        <Badge tone={getPriorityTone(c.priority)}>
                          {c.priority || "Medium"}
                        </Badge>
                        {getAssignCountdownBadge(c)}
                      </div>

                      {c.description && (
                        <p className="text-xs text-slate-500 line-clamp-1">{c.description}</p>
                      )}

                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3.5 w-3.5" />
                          {getLocationName(c.location_id, locations)}
                          {c.exact_spot ? ` • ${c.exact_spot}` : ""}
                        </span>
                        <span>•</span>
                        <span>Filed {formatDate(c.created_at)}</span>
                        {c.returned_reason && (
                          <>
                            <span>•</span>
                            <span className="text-rose-600 font-semibold">
                              Returned: {c.returned_reason}
                            </span>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <Button
                        size="md"
                        variant="primary"
                        onClick={() => setAssignModalComplaint(c)}
                        className="font-bold text-xs flex items-center gap-1.5 shadow-sm py-2 px-4"
                      >
                        <User className="h-4 w-4" />
                        Assign to...
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => navigate(`/complaints/${c.complaint_id}`)}
                        className="text-xs"
                      >
                        Details
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: TEAM BOARD (Active Jobs) */}
        {activeTab === "team_board" && (
          <div className="p-5 space-y-4">
            <div className="flex items-center justify-between pb-2">
              <span className="text-xs text-slate-500 font-medium">
                Active jobs across the team with assigned worker and status.
              </span>
              <Button size="sm" variant="ghost" onClick={reload} className="text-xs">
                Refresh Board
              </Button>
            </div>

            {teamBoardComplaints.length === 0 ? (
              <EmptyState
                title="No Active Jobs on Board"
                description="No open jobs currently assigned across the team."
              />
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {teamBoardComplaints.map((c) => (
                  <div
                    key={c.complaint_id}
                    className="py-4 first:pt-0 last:pb-0 flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-3 rounded-xl hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors"
                  >
                    <div className="space-y-1.5 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <Link
                          to={`/complaints/${c.complaint_id}`}
                          className="text-sm font-bold text-slate-900 dark:text-slate-100 hover:text-blue-600 transition-colors"
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
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-300">
                            Assignee on leave
                          </span>
                        )}
                        {c.assignee_removed_flag && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-300">
                            Assignee removed — reassign
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                        <span className="flex items-center gap-1 font-semibold text-slate-800 dark:text-slate-200">
                          <User className="h-3.5 w-3.5 text-blue-500" />
                          Worker: {c.assigned_to}
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3.5 w-3.5" />
                          {getLocationName(c.location_id, locations)}
                        </span>
                        {c.sla_deadline && (
                          <>
                            <span>•</span>
                            <span className="flex items-center gap-1">
                              <Clock className="h-3.5 w-3.5 text-slate-400" />
                              SLA: {formatDate(c.sla_deadline)}
                            </span>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0 flex-wrap">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => setAssignModalComplaint(c)}
                        className="text-xs font-semibold"
                      >
                        Reassign
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => handleOpenResolveModal(c)}
                        className="text-xs"
                      >
                        Mark Done on Behalf
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => navigate(`/complaints/${c.complaint_id}`)}
                        className="text-xs"
                      >
                        Details
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: MY JOBS (Self-assigned) */}
        {activeTab === "my_jobs" && (
          <div className="p-5 space-y-4">
            <div className="flex items-center justify-between pb-2">
              <span className="text-xs text-slate-500 font-medium">
                Jobs assigned to you directly. Fast execution with big Mark Done button.
              </span>
              <Button size="sm" variant="ghost" onClick={reload} className="text-xs">
                Refresh My Jobs
              </Button>
            </div>

            {myJobs.length === 0 ? (
              <EmptyState
                title="No Personal Assignments"
                description="You currently have no jobs assigned to yourself. You can assign complaints to yourself from the 'To assign' queue."
              />
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {myJobs.map((c) => {
                  const isMenuOpen = openMenuComplaintId === c.complaint_id;
                  return (
                    <div
                      key={c.complaint_id}
                      className="py-4 first:pt-0 last:pb-0 flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-3 rounded-xl hover:bg-slate-50/50 dark:hover:bg-slate-900/30 transition-colors"
                    >
                      <div className="space-y-1.5 min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <Link
                            to={`/complaints/${c.complaint_id}`}
                            className="text-sm font-bold text-slate-900 dark:text-slate-100 hover:text-blue-600 transition-colors"
                          >
                            {c.title || c.category}
                          </Link>
                          <Badge tone={getPriorityTone(c.priority)}>
                            {c.priority || "Medium"}
                          </Badge>
                          <Badge tone={getStatusTone(c.status)}>
                            {c.status}
                          </Badge>
                        </div>

                        {c.description && (
                          <p className="text-xs text-slate-500 line-clamp-1">{c.description}</p>
                        )}

                        <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
                          <span className="flex items-center gap-1">
                            <MapPin className="h-3.5 w-3.5" />
                            {getLocationName(c.location_id, locations)}
                          </span>
                          <span>•</span>
                          <span>Assigned {c.assigned_at ? formatDate(c.assigned_at) : "Recently"}</span>
                        </div>
                      </div>

                      {/* Big Mark Done button & More Menu */}
                      <div className="flex items-center gap-2.5 shrink-0 flex-wrap relative">
                        {c.status === "Assigned" && (
                          <Button
                            size="md"
                            variant="primary"
                            onClick={() => handleStartWork(c)}
                            className="font-bold text-xs flex items-center gap-1.5 shadow-sm py-2 px-4"
                          >
                            <Play className="h-4 w-4" />
                            Start Work
                          </Button>
                        )}

                        <Button
                          size="md"
                          variant="success"
                          onClick={() => handleOpenResolveModal(c)}
                          className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-sm py-2 px-5 rounded-xl"
                        >
                          <Check className="h-4 w-4" />
                          Mark Done
                        </Button>

                        {/* More Menu Toggle */}
                        <div className="relative">
                          <button
                            type="button"
                            onClick={() => setOpenMenuComplaintId(isMenuOpen ? null : c.complaint_id)}
                            className="p-2 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition"
                          >
                            <MoreVertical className="h-5 w-5" />
                          </button>

                          {isMenuOpen && (
                            <div className="absolute right-0 mt-1 w-52 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-xl z-20 py-1 text-xs">
                              <div className="px-3 py-1 text-[10px] font-semibold text-slate-400 uppercase">
                                Preset Notes
                              </div>
                              {PRESET_WORKER_NOTES.map((preset) => (
                                <button
                                  key={preset.code}
                                  type="button"
                                  onClick={() => handlePresetNote(c, preset)}
                                  className="w-full px-3 py-1.5 text-left flex items-center gap-2 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300"
                                >
                                  <FileText className="h-3 w-3 text-blue-500" />
                                  {preset.label}
                                </button>
                              ))}

                              <div className="border-t border-slate-100 dark:border-slate-700 my-1" />

                              <button
                                type="button"
                                onClick={() => {
                                  setOpenMenuComplaintId(null);
                                  setSelectedComplaint(c);
                                  setShowPartsModal(true);
                                }}
                                className="w-full px-3 py-2 text-left flex items-center gap-2 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200"
                              >
                                <Pause className="h-3.5 w-3.5 text-amber-500" />
                                Waiting for parts
                              </button>

                              <button
                                type="button"
                                onClick={() => {
                                  setOpenMenuComplaintId(null);
                                  setSelectedComplaint(c);
                                  setShowWrongLocModal(true);
                                }}
                                className="w-full px-3 py-2 text-left flex items-center gap-2 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200"
                              >
                                <Navigation className="h-3.5 w-3.5 text-indigo-500" />
                                Wrong location
                              </button>

                              <button
                                type="button"
                                onClick={() => {
                                  setOpenMenuComplaintId(null);
                                  setSelectedComplaint(c);
                                  setShowReturnModal(true);
                                }}
                                className="w-full px-3 py-2 text-left flex items-center gap-2 hover:bg-slate-100 dark:hover:bg-slate-700 text-rose-600 dark:text-rose-400"
                              >
                                <RotateCcw className="h-3.5 w-3.5" />
                                Return to queue
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* TAB 4: STATS & PERFORMANCE (Rule J1 & J2) */}
        {activeTab === "stats" && (
          <div className="p-5 space-y-6">
            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-3">
                Team Stats (This Month)
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                  <div className="text-xs text-slate-500">Total Assigned</div>
                  <div className="text-2xl font-black text-slate-900 dark:text-slate-100 mt-1">
                    {stats?.team_stats?.total_assigned_this_month ?? 0}
                  </div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                  <div className="text-xs text-slate-500">Avg Time to Assign</div>
                  <div className="text-2xl font-black text-blue-600 mt-1">
                    {stats?.team_stats?.avg_time_to_assign ? `${stats.team_stats.avg_time_to_assign}h` : "N/A"}
                  </div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                  <div className="text-xs text-slate-500">Overdue Now</div>
                  <div className="text-2xl font-black text-rose-600 mt-1">
                    {stats?.team_stats?.overdue_now ?? 0}
                  </div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                  <div className="text-xs text-slate-500">Escalated to Backup / Warden</div>
                  <div className="text-2xl font-black text-amber-600 mt-1">
                    {(stats?.team_stats?.escalations_to_backup_count ?? 0) + (stats?.team_stats?.escalations_to_warden_count ?? 0)}
                  </div>
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 uppercase tracking-wider mb-3">
                My Worker Stats (Personal)
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                  <div className="text-xs text-slate-500">Open Jobs</div>
                  <div className="text-2xl font-black text-slate-900 dark:text-slate-100 mt-1">
                    {stats?.worker_stats?.open_jobs ?? myJobs.length}
                  </div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                  <div className="text-xs text-slate-500">Completed This Month</div>
                  <div className="text-2xl font-black text-emerald-600 mt-1">
                    {stats?.worker_stats?.completed_this_month ?? 0}
                  </div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                  <div className="text-xs text-slate-500">Avg Time to Fix</div>
                  <div className="text-2xl font-black text-blue-600 mt-1">
                    {stats?.worker_stats?.avg_time_to_fix ? `${stats.worker_stats.avg_time_to_fix}h` : "N/A"}
                  </div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
                  <div className="text-xs text-slate-500">On-time Rate</div>
                  <div className="text-2xl font-black text-indigo-600 mt-1">
                    {stats?.worker_stats?.on_time_rate ?? 100}%
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 5: TEAM WORKFORCE (Members & Worker Passwords, Part 3.5e) */}
        {activeTab === "team_members" && (
          <div className="p-5 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Team Members & Workforce
                </h3>
                <p className="text-xs text-slate-500">
                  Manage worker accounts, coverage, and reset temporary passwords for in-person handoff.
                </p>
              </div>
              <Button size="sm" variant="ghost" onClick={loadAllTeamMembers} className="text-xs">
                Refresh Workforce
              </Button>
            </div>

            {loadingMembers ? (
              <div className="p-8 text-center text-xs text-slate-500">Loading team workforce...</div>
            ) : teamMembersList.length === 0 ? (
              <EmptyState
                title="No Workers in Team"
                description="Your team does not have any workers assigned yet. Please contact your App Manager or Admin to assign workers to your team."
              />
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 font-bold border-y border-slate-200 dark:border-slate-700">
                    <tr>
                      <th className="py-2.5 px-3">Name</th>
                      <th className="py-2.5 px-3">Role</th>
                      <th className="py-2.5 px-3">Phone</th>
                      <th className="py-2.5 px-3">Team</th>
                      <th className="py-2.5 px-3">Status</th>
                      <th className="py-2.5 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {teamMembersList.map((m) => (
                      <tr key={m.user_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                        <td className="py-3 px-3 font-bold text-slate-900 dark:text-slate-100">
                          {m.name}
                        </td>
                        <td className="py-3 px-3 text-slate-600 dark:text-slate-300">
                          Employee
                        </td>
                        <td className="py-3 px-3 text-slate-700 dark:text-slate-300 font-mono">
                          {m.phone || "—"}
                        </td>
                        <td className="py-3 px-3 text-slate-500">
                          {m.team_name}
                        </td>
                        <td className="py-3 px-3">
                          <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            m.on_leave
                              ? "bg-amber-100 text-amber-800"
                              : "bg-emerald-100 text-emerald-800"
                          }`}>
                            {m.on_leave ? "On Leave" : "Available"}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-right">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleResetWorkerPassword(m)}
                            className="text-xs font-bold border-amber-300 text-amber-700 dark:border-amber-800 dark:text-amber-300 hover:bg-amber-50 dark:hover:bg-amber-950/40"
                            title="Generate and print login slip with CP-XXXX temporary password"
                          >
                            <Key className="h-3.5 w-3.5 mr-1 text-amber-600" />
                            Reset Password Slip
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ASSIGN MODAL (Rule K3) */}
      <AssignModal
        isOpen={Boolean(assignModalComplaint)}
        onClose={() => setAssignModalComplaint(null)}
        complaint={assignModalComplaint}
        onAssigned={() => {
          reload();
          setToastTone("success");
          setToastMessage("Complaint assigned successfully.");
        }}
      />

      {/* LEAVE MODAL (Rule G2 & K1) */}
      <LeaveModal
        isOpen={showLeaveModal}
        onClose={() => setShowLeaveModal(false)}
        onLeaveChanged={reload}
      />

      {/* Credential Slip Modal for Worker Login Slip (Part 3.5e) */}
      <CredentialSlipModal
        isOpen={Boolean(slipData)}
        onClose={() => setSlipData(null)}
        credentialData={slipData}
      />

      {/* MARK DONE MODAL */}
      <Modal
        isOpen={showResolveModal}
        onClose={() => setShowResolveModal(false)}
        title="Mark Job as Resolved"
      >
        <form onSubmit={handleConfirmResolve} className="space-y-4">
          {resolveError && (
            <div className="p-3 text-sm bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 rounded-lg border border-rose-200">
              {resolveError}
            </div>
          )}

          {selectedComplaint && (
            <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl text-sm">
              <div className="font-semibold">{selectedComplaint.title || selectedComplaint.category}</div>
              <div className="text-xs text-slate-500 mt-0.5">
                Worker: <span className="font-medium text-slate-700 dark:text-slate-300">{selectedComplaint.assigned_to}</span>
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
              After-repair Photo URL
            </label>
            <input
              type="text"
              placeholder="https://... or uploaded image URL"
              value={proofUrl}
              onChange={(e) => setProofUrl(e.target.value)}
              disabled={isPhotoSkipped}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {selectedComplaint?.attachment_url && (
            <div className="space-y-2 p-3 bg-amber-50 dark:bg-amber-950/30 rounded-xl border border-amber-200 dark:border-amber-800">
              <label className="flex items-center gap-2 text-xs font-semibold text-amber-900 dark:text-amber-200 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isPhotoSkipped}
                  onChange={(e) => setIsPhotoSkipped(e.target.checked)}
                  className="rounded text-blue-600"
                />
                Skip after-repair photo
              </label>
              {isPhotoSkipped && (
                <input
                  type="text"
                  placeholder="Reason for skipping photo..."
                  value={photoSkipReason}
                  onChange={(e) => setPhotoSkipReason(e.target.value)}
                  className="w-full text-xs rounded border border-amber-300 bg-white dark:bg-slate-900 p-1.5 text-slate-900 dark:text-slate-100 outline-none"
                  required
                />
              )}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
              Resolution Notes
            </label>
            <textarea
              rows={2}
              placeholder="What was fixed..."
              value={resolveNotesText}
              onChange={(e) => setResolveNotesText(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
            <Button variant="secondary" onClick={() => setShowResolveModal(false)} disabled={submittingResolve}>
              Cancel
            </Button>
            <Button variant="primary" type="submit" disabled={submittingResolve} className="bg-emerald-600 hover:bg-emerald-700 text-white">
              {submittingResolve ? "Resolving..." : "Confirm Done"}
            </Button>
          </div>
        </form>
      </Modal>

      {/* WAITING FOR PARTS MODAL */}
      <Modal
        isOpen={showPartsModal}
        onClose={() => setShowPartsModal(false)}
        title="Waiting for Parts"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
              Parts Details / Reason <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              placeholder="e.g. Spare motor ordered"
              value={partsReason}
              onChange={(e) => setPartsReason(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
              Expected Arrival Date (Optional)
            </label>
            <input
              type="date"
              value={partsExpectedDate}
              onChange={(e) => setPartsExpectedDate(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowPartsModal(false)} disabled={pausingParts}>
              Cancel
            </Button>
            <Button
              variant="primary"
              disabled={!partsReason.trim() || pausingParts}
              onClick={handleConfirmParts}
            >
              {pausingParts ? "Pausing..." : "Pause for Parts"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* WRONG LOCATION MODAL */}
      <Modal
        isOpen={showWrongLocModal}
        onClose={() => setShowWrongLocModal(false)}
        title="Report Wrong Location"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
              Correct Location <span className="text-rose-500">*</span>
            </label>
            <select
              value={newLocationId}
              onChange={(e) => setNewLocationId(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Select location...</option>
              {locations.map((loc) => (
                <option key={loc.location_id} value={loc.location_id}>
                  {loc.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
              Note (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. Found in Block B instead of Block A"
              value={wrongLocNote}
              onChange={(e) => setWrongLocNote(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowWrongLocModal(false)} disabled={reportingWrongLoc}>
              Cancel
            </Button>
            <Button
              variant="primary"
              disabled={!newLocationId || reportingWrongLoc}
              onClick={handleConfirmWrongLocation}
            >
              {reportingWrongLoc ? "Updating..." : "Submit New Location"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* RETURN TO QUEUE MODAL */}
      <Modal
        isOpen={showReturnModal}
        onClose={() => setShowReturnModal(false)}
        title="Return Complaint to Queue"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-500">
            This complaint will return to the "To assign" queue, and the assign timer will reset.
          </p>
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
              Reason for Return <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={3}
              placeholder="Reason for returning this job..."
              value={returnReason}
              onChange={(e) => setReturnReason(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowReturnModal(false)} disabled={returning}>
              Cancel
            </Button>
            <Button
              variant="danger"
              disabled={!returnReason.trim() || returning}
              onClick={handleConfirmReturn}
            >
              {returning ? "Returning..." : "Return Job"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
