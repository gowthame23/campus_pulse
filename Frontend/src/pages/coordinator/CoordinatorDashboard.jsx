import { useMemo, useState, useEffect, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Wrench,
  Megaphone,
  Bell,
  Clock,
  ArrowRight,
  AlertTriangle,
  MapPin,
  CheckCircle2,
  ChevronRight,
  Plus,
  PlayCircle,
  PauseCircle,
  FileText,
  Check,
  Building,
  Hourglass,
  Camera,
  MoreVertical,
  Upload,
  TrendingUp,
  X,
  Layers,
  HelpCircle,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import StatCard from "../../components/StatCard.jsx";
import Badge from "../../components/Badge.jsx";
import Modal from "../../components/Modal.jsx";
import Textarea from "../../components/Textarea.jsx";
import Toast from "../../components/Toast.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { complaintService } from "../../services/complaintService.js";
import { attachmentService } from "../../services/attachmentService.js";
import { announcementService } from "../../services/announcementService.js";
import { notificationService } from "../../services/notificationService.js";
import { locationService } from "../../services/locationService.js";
import { departmentService } from "../../services/departmentService.js";
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

const getWaitingTime = (createdAt) => {
  if (!createdAt) return "";
  const diff = Math.max(0, Date.now() - new Date(createdAt).getTime());
  const hours = Math.floor(diff / (1000 * 60 * 60));
  const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  if (hours > 24) {
    const days = Math.floor(hours / 24);
    return `Waiting ${days}d ${hours % 24}h`;
  }
  if (hours > 0) return `Waiting ${hours}h ${mins}m`;
  return `Waiting ${mins}m`;
};

const getDeadlineBadge = (c) => {
  const deadline = c.sla_deadline || c.due_date;
  if (!deadline) return null;
  const diff = new Date(deadline).getTime() - Date.now();
  const isOverdue = diff <= 0;
  const absDiff = Math.abs(diff);
  const hours = Math.floor(absDiff / (1000 * 60 * 60));
  const mins = Math.floor((absDiff % (1000 * 60 * 60)) / (1000 * 60));
  if (isOverdue) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-rose-100 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-300 dark:border-rose-800 animate-pulse">
        <AlertTriangle className="h-3 w-3" />
        LATE by {hours}h {mins}m
      </span>
    );
  }
  if (hours < 4) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-300 dark:border-amber-800">
        <Clock className="h-3 w-3" />
        Due in {hours}h {mins}m
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
      <Clock className="h-3 w-3" />
      Due in {hours}h {mins}m
    </span>
  );
};

const PRESET_NOTES = [
  "Investigating the issue on site",
  "Spare parts ordered",
  "Technician dispatched to location",
  "Repair work actively underway",
];

const RESOLUTION_PRESETS = [
  "Issue resolved and tested on site",
  "Replaced faulty components",
  "Cleaning and servicing completed",
  "Restored to normal operation",
];

export default function CoordinatorDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState("available"); // "available" | "my_work"
  const [toastMessage, setToastMessage] = useState("");
  const [toastTone, setToastTone] = useState("success");

  // Action Modals State
  const [selectedComplaint, setSelectedComplaint] = useState(null);

  // Progress Note Modal
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [progressNoteText, setProgressNoteText] = useState("");
  const [submittingProgressNote, setSubmittingProgressNote] = useState(false);

  // Pause Modal
  const [showPauseModal, setShowPauseModal] = useState(false);
  const [pauseReasonText, setPauseReasonText] = useState("");
  const [submittingPause, setSubmittingPause] = useState(false);

  // Wrong Location Modal
  const [showWrongLocationModal, setShowWrongLocationModal] = useState(false);
  const [wrongLocationNotes, setWrongLocationNotes] = useState("");
  const [submittingWrongLocation, setSubmittingWrongLocation] = useState(false);

  // Mark Done Modal
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [resolveNotesText, setResolveNotesText] = useState("");
  const [resolvePreset, setResolvePreset] = useState("");
  const [resolvePhotoFile, setResolvePhotoFile] = useState(null);
  const [isPhotoSkipped, setIsPhotoSkipped] = useState(false);
  const [photoSkipReason, setPhotoSkipReason] = useState("");
  const [submittingResolve, setSubmittingResolve] = useState(false);

  // More Menu Popover
  const [openMenuComplaintId, setOpenMenuComplaintId] = useState(null);

  // Hidden File Inputs for Camera and Gallery
  const cameraInputRef = useRef(null);
  const galleryInputRef = useRef(null);

  // Own Performance Stats
  const [ownStats, setOwnStats] = useState(null);

  const {
    data: dashboardData,
    loading,
    error,
    reload,
  } = useAsyncData(
    async () => {
      const [compRes, ancRes, notifRes, locRes, deptRes, statsRes] = await Promise.all([
        complaintService.list().catch(() => ({ data: [] })),
        announcementService.list().catch(() => ({ data: [] })),
        notificationService
          .listPaginated({ limit: 5 })
          .then((res) => ({ data: res.data.items }))
          .catch(() => ({ data: [] })),
        locationService.list().catch(() => ({ data: [] })),
        departmentService.list().catch(() => ({ data: [] })),
        complaintService.getCoordinatorStats().catch(() => ({ data: [] })),
      ]);

      const myStats = (statsRes.data || []).find(
        (s) => s.coordinator_id === user?.user_id || s.email === user?.email,
      );
      if (myStats) setOwnStats(myStats);

      return {
        complaints: compRes.data || [],
        announcements: ancRes.data || [],
        notifications: notifRes.data || [],
        locations: locRes.data || [],
        departments: deptRes.data || [],
      };
    },
    { complaints: [], announcements: [], notifications: [], locations: [], departments: [] },
  );

  const complaints = dashboardData?.complaints || [];
  const announcements = dashboardData?.announcements || [];
  const notifications = dashboardData?.notifications || [];
  const locations = dashboardData?.locations || [];
  const departments = dashboardData?.departments || [];

  // Filter 1: Available Work (Unassigned or unaccepted queue matching coordinator's department or location)
  // Sorted OLDEST FIRST
  const availableComplaints = useMemo(() => {
    return complaints
      .filter((c) => {
        const isUnclaimed =
          !c.assigned_to ||
          c.status === "Submitted" ||
          c.status === "Pending" ||
          c.status === "Awaiting Coordinator Assignment";
        const isNotClosed = !c.status?.startsWith("Closed");

        if (!isUnclaimed || !isNotClosed) return false;

        // Department or location match
        if (user?.department_id && c.department_id === user.department_id) return true;
        if (user?.department && c.department_name === user.department) return true;
        if (user?.location_id && c.location_id === user.location_id) return true;

        // If coordinator has no specific dept restriction, include all unclaimed
        return !user?.department_id && !user?.location_id;
      })
      .sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0));
  }, [complaints, user]);

  // Filter 2: My Work (Tickets I accepted or am assigned to)
  const myWorkComplaints = useMemo(() => {
    return complaints.filter((c) => {
      const isMine =
        c.assigned_to === user?.user_id ||
        c.assigned_to === user?.email ||
        (user?.id && c.assigned_to === user.id);
      const isNotClosed = !c.status?.startsWith("Closed");
      return isMine && isNotClosed;
    });
  }, [complaints, user]);

  const overdueComplaints = useMemo(
    () =>
      myWorkComplaints.filter(
        (c) => c.is_overdue || c.status === "Overdue" || c.sla_status === "Breached",
      ),
    [myWorkComplaints],
  );

  const inProgressCount = useMemo(
    () => myWorkComplaints.filter((c) => c.status === "In Progress").length,
    [myWorkComplaints],
  );

  // Mapped departments and locations for display
  const mappedDepartments = useMemo(() => {
    if (user?.department) return [user.department];
    if (user?.department_name) return [user.department_name];
    const dept = departments.find((d) => d.coordinator_id === user?.user_id);
    if (dept) return [dept.name];
    return ["General Operations"];
  }, [user, departments]);

  const mappedLocations = useMemo(() => {
    if (user?.location_name) return [user.location_name];
    if (user?.location_id) return [getLocationName(user.location_id, locations)];
    return ["All Campus Locations"];
  }, [user, locations]);

  // Actions
  const handleAccept = async (complaintId) => {
    try {
      await complaintService.accept(complaintId);
      setToastTone("success");
      setToastMessage("Ticket accepted and moved to My Work.");
      reload();
      setActiveTab("my_work");
    } catch (err) {
      if (err.response?.status === 409) {
        setToastTone("danger");
        const detail = err.response?.data?.detail;
        setToastMessage(detail || "Taken by another coordinator.");
      } else {
        setToastTone("danger");
        setToastMessage(err.response?.data?.detail || "Could not accept ticket.");
      }
      reload();
    }
  };

  const handleStartWork = async (complaintId) => {
    try {
      await complaintService.startWork(complaintId);
      setToastTone("success");
      setToastMessage("Work started (In Progress).");
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Failed to start work.");
    }
  };

  const handleResumeWork = async (complaintId) => {
    try {
      await complaintService.resume(complaintId);
      setToastTone("success");
      setToastMessage("Work resumed. Ticket returned to In Progress.");
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Failed to resume work.");
    }
  };

  const handleQuickPresetNote = async (complaintId, presetText) => {
    try {
      await complaintService.addProgressNote(complaintId, presetText);
      setToastTone("success");
      setToastMessage(`Progress note logged: "${presetText}"`);
      setOpenMenuComplaintId(null);
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Failed to log progress note.");
    }
  };

  const handleProgressNoteSubmit = async (e) => {
    e.preventDefault();
    if (!selectedComplaint || !progressNoteText.trim()) return;
    setSubmittingProgressNote(true);
    try {
      await complaintService.addProgressNote(selectedComplaint.complaint_id, progressNoteText.trim());
      setToastTone("success");
      setToastMessage("Progress note logged.");
      setShowProgressModal(false);
      setProgressNoteText("");
      setSelectedComplaint(null);
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Failed to log progress note.");
    } finally {
      setSubmittingProgressNote(false);
    }
  };

  const handlePauseSubmit = async (e) => {
    e.preventDefault();
    if (!selectedComplaint || !pauseReasonText.trim()) return;
    setSubmittingPause(true);
    try {
      await complaintService.pause(selectedComplaint.complaint_id, pauseReasonText.trim());
      setToastTone("success");
      setToastMessage("Ticket paused (Waiting for Parts).");
      setShowPauseModal(false);
      setPauseReasonText("");
      setSelectedComplaint(null);
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Failed to pause ticket.");
    } finally {
      setSubmittingPause(false);
    }
  };

  const handleWrongLocationSubmit = async (e) => {
    e.preventDefault();
    if (!selectedComplaint) return;
    setSubmittingWrongLocation(true);
    try {
      await complaintService.addProgressNote(
        selectedComplaint.complaint_id,
        `[WRONG LOCATION REPORTED]: ${wrongLocationNotes.trim() || "Item does not belong to this location."}`,
      );
      setToastTone("info");
      setToastMessage("Wrong location report noted. Warden and App Manager alerted.");
      setShowWrongLocationModal(false);
      setWrongLocationNotes("");
      setSelectedComplaint(null);
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Failed to report wrong location.");
    } finally {
      setSubmittingWrongLocation(false);
    }
  };

  const handleOpenResolveModal = (complaint) => {
    setSelectedComplaint(complaint);
    setResolveNotesText("");
    setResolvePreset("");
    setResolvePhotoFile(null);
    setIsPhotoSkipped(false);
    setPhotoSkipReason("");
    setShowResolveModal(true);
    setOpenMenuComplaintId(null);
  };

  const handleResolveSubmit = async (e) => {
    e.preventDefault();
    if (!selectedComplaint) return;

    const studentHasPhoto = Boolean(
      selectedComplaint.attachment_url ||
      (selectedComplaint.attachments && selectedComplaint.attachments.length > 0)
    );

    // If student had photo and coordinator chose to skip
    if (isPhotoSkipped) {
      const streak = ownStats?.photo_skip_streak || 0;
      if (streak >= 2 && !photoSkipReason.trim()) {
        setToastTone("danger");
        setToastMessage("Reason is required because your photo skip streak is 2 or more.");
        return;
      }
      if (!photoSkipReason.trim()) {
        setToastTone("danger");
        setToastMessage("Please specify why the student's photo is not relevant.");
        return;
      }
    }

    // High/Critical priority check
    const p = (selectedComplaint.priority || "Medium").toLowerCase();
    const isHighOrCrit = p === "high" || p === "critical";
    if (isHighOrCrit && !resolvePhotoFile && !isPhotoSkipped) {
      setToastTone("danger");
      setToastMessage("High/Critical priority tickets require an After Repair photo.");
      return;
    }

    const finalNotes = resolveNotesText.trim() || resolvePreset || "Work completed and verified on site.";

    setSubmittingResolve(true);
    try {
      if (resolvePhotoFile && !isPhotoSkipped) {
        await attachmentService.upload(selectedComplaint.complaint_id, [resolvePhotoFile], "After Repair");
      }

      const payload = isPhotoSkipped
        ? {
            notes: finalNotes,
            skip_photo: true,
            photo_skipped: true,
            photo_skip_reason: photoSkipReason.trim(),
          }
        : {
            notes: finalNotes,
            preset_code: resolvePreset || undefined,
          };

      await complaintService.resolve(selectedComplaint.complaint_id, payload);
      setToastTone("success");
      setToastMessage("Work marked completed and submitted for verification!");
      setShowResolveModal(false);
      setSelectedComplaint(null);
      reload();
    } catch (err) {
      setToastTone("danger");
      setToastMessage(err.response?.data?.detail || "Failed to resolve complaint.");
    } finally {
      setSubmittingResolve(false);
    }
  };

  if (loading) {
    return <Loader label="Loading coordinator dashboard..." variant="skeleton" />;
  }
  if (error) {
    return <EmptyState title="Dashboard Unavailable" description={error} />;
  }

  const studentHasPhoto = Boolean(
    selectedComplaint?.attachment_url ||
    (selectedComplaint?.attachments && selectedComplaint.attachments.length > 0)
  );

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

      {/* Coordinator Coverage & Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              Good morning, {user?.name || "Coordinator"}
            </h1>
            <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20">
              Field Execution
            </span>
          </div>

          {/* Mapped Departments & Locations Pill Bar */}
          <div className="flex flex-wrap items-center gap-2 pt-1 text-xs text-slate-600 dark:text-slate-400">
            <span className="flex items-center gap-1 font-semibold text-slate-800 dark:text-slate-200">
              <Building className="h-3.5 w-3.5 text-primary" />
              {mappedDepartments.join(", ")}
            </span>
            <span>•</span>
            <span className="flex items-center gap-1 font-semibold text-slate-800 dark:text-slate-200">
              <MapPin className="h-3.5 w-3.5 text-amber-500" />
              {mappedLocations.join(", ")}
            </span>
            <span>•</span>
            <span>{myWorkComplaints.length} active assigned tickets</span>
          </div>
        </div>

        <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
          <Button
            onClick={() => navigate("/coordinators/performance")}
            variant="outline"
            size="md"
            className="font-medium shrink-0 flex items-center gap-1.5"
          >
            <TrendingUp className="h-4 w-4" />
            Performance & SLA
          </Button>
          <Button
            onClick={() => navigate("/complaints")}
            variant="outline"
            size="md"
            className="font-medium shrink-0 flex items-center gap-1.5"
          >
            All Complaints
          </Button>
        </div>
      </div>

      {/* 4 Key Metrics Row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <StatCard
          label="Available in Queue"
          value={availableComplaints.length}
          accent={availableComplaints.length > 0}
          subtext="Ready to accept and claim"
          onClick={() => setActiveTab("available")}
        />
        <StatCard
          label="My Active Work"
          value={myWorkComplaints.length}
          subtext={`${inProgressCount} currently in progress`}
          onClick={() => setActiveTab("my_work")}
        />
        <StatCard
          label="Overdue / SLA Risk"
          value={overdueComplaints.length}
          accent={overdueComplaints.length > 0}
          subtext={overdueComplaints.length > 0 ? "Exceeding turnaround SLA" : "All within target SLA"}
          onClick={() => setActiveTab("my_work")}
        />
        <StatCard
          label="Photo Quality & Skips"
          value={`${ownStats?.photo_percent !== undefined ? ownStats.photo_percent + "%" : "100%"}`}
          subtext={`Streak: ${ownStats?.photo_skip_streak || 0} / 2 limit`}
          onClick={() => navigate("/coordinators/performance")}
        />
      </div>

      {/* Overdue Alert Banner */}
      {overdueComplaints.length > 0 && (
        <div className="flex items-center justify-between gap-4 p-4 rounded-xl border border-rose-200/80 dark:border-rose-900/40 bg-rose-50/70 dark:bg-rose-950/20 text-rose-900 dark:text-rose-200 text-xs shadow-2xs">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-rose-100 dark:bg-rose-900/50 text-rose-700 dark:text-rose-400 shrink-0">
              <AlertTriangle className="h-4 w-4" />
            </div>
            <div>
              <span className="font-semibold">
                SLA Alert: You have {overdueComplaints.length} overdue ticket(s) requiring immediate attention.
              </span>
              <p className="text-[11px] text-rose-800/80 dark:text-rose-300/80 mt-0.5">
                Complete repairs or post progress updates to resolve overdue alerts.
              </p>
            </div>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setActiveTab("my_work")}
            className="!h-8 text-xs font-semibold shrink-0 border-rose-300 dark:border-rose-800 text-rose-900 dark:text-rose-200 hover:bg-rose-100/60"
          >
            Review Overdue
          </Button>
        </div>
      )}

      {/* Main Two-Tab Work Interface */}
      <div className="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-[#101726] shadow-xs overflow-hidden">
        {/* Tab Switcher */}
        <div className="flex border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/50">
          <button
            type="button"
            onClick={() => setActiveTab("available")}
            className={`flex items-center gap-2 px-6 py-3.5 text-xs font-bold border-b-2 transition-all cursor-pointer ${
              activeTab === "available"
                ? "border-primary text-primary bg-white dark:bg-[#101726]"
                : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            <Clock className="h-4 w-4" />
            Available Work
            <span className={`px-2 py-0.5 text-[10px] rounded-full font-bold ${
              activeTab === "available" ? "bg-primary text-white" : "bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
            }`}>
              {availableComplaints.length}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab("my_work")}
            className={`flex items-center gap-2 px-6 py-3.5 text-xs font-bold border-b-2 transition-all cursor-pointer ${
              activeTab === "my_work"
                ? "border-primary text-primary bg-white dark:bg-[#101726]"
                : "border-transparent text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
            }`}
          >
            <Wrench className="h-4 w-4" />
            My Work
            <span className={`px-2 py-0.5 text-[10px] rounded-full font-bold ${
              activeTab === "my_work" ? "bg-primary text-white" : "bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
            }`}>
              {myWorkComplaints.length}
            </span>
          </button>
        </div>

        {/* Tab 1: Available Work */}
        {activeTab === "available" && (
          <div className="p-5 space-y-4">
            <div className="flex items-center justify-between pb-2">
              <span className="text-xs text-slate-500 font-medium">
                Team intake queue (oldest first). First to click <strong>Accept</strong> claims the ticket.
              </span>
              <Button size="sm" variant="ghost" onClick={reload} className="text-xs">
                Refresh Queue
              </Button>
            </div>

            {availableComplaints.length === 0 ? (
              <EmptyState
                title="No Available Tickets"
                description="Your intake queue is completely clear! All incoming complaints have been claimed."
              />
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-800/80">
                {availableComplaints.map((c) => (
                  <div
                    key={c.complaint_id}
                    className="py-4 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/50 dark:hover:bg-slate-900/30 p-3 rounded-xl transition-colors"
                  >
                    <div className="space-y-1.5 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <Link
                          to={`/complaints/${c.complaint_id}`}
                          className="text-sm font-bold text-slate-900 dark:text-slate-100 hover:text-primary transition-colors"
                        >
                          {c.title || "Untitled Issue"}
                        </Link>
                        <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                          {c.complaint_id}
                        </span>
                        <Badge tone={getPriorityTone(c.priority)}>
                          {c.priority || "Medium"}
                        </Badge>
                        <Badge tone={getStatusTone(c.status)}>
                          {c.status}
                        </Badge>
                        <span className="text-[11px] font-semibold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded">
                          {getWaitingTime(c.created_at)}
                        </span>
                      </div>

                      <p className="text-xs text-slate-500 line-clamp-1">
                        {c.description}
                      </p>

                      <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 pt-0.5">
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {getLocationName(c.location_id, locations)}
                        </span>
                        <span>•</span>
                        <span>{c.category || c.complaint_type || "General"}</span>
                        <span>•</span>
                        <span>Filed {formatDate(c.created_at)}</span>
                        {c.accept_due_at && (
                          <>
                            <span>•</span>
                            <span className="text-amber-600 dark:text-amber-400 font-semibold">
                              Accept by {formatDate(c.accept_due_at)}
                            </span>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <Button
                        size="md"
                        variant="primary"
                        onClick={() => handleAccept(c.complaint_id)}
                        className="font-bold text-xs flex items-center gap-1.5 shadow-sm py-2 px-4"
                      >
                        <CheckCircle2 className="h-4 w-4" />
                        Accept
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

        {/* Tab 2: My Work */}
        {activeTab === "my_work" && (
          <div className="p-5 space-y-4">
            <div className="flex items-center justify-between pb-2">
              <span className="text-xs text-slate-500 font-medium">
                Active tickets assigned to you. Big one-tap primary buttons for fast mobile execution.
              </span>
              <Button size="sm" variant="ghost" onClick={reload} className="text-xs">
                Refresh My Work
              </Button>
            </div>

            {myWorkComplaints.length === 0 ? (
              <EmptyState
                title="No Active Assignments"
                description="You have no active work assigned. Switch to 'Available Work' to claim tickets from your department intake queue."
              />
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-800/80">
                {myWorkComplaints.map((c) => (
                  <div
                    key={c.complaint_id}
                    className="py-4 first:pt-0 last:pb-0 flex flex-col lg:flex-row lg:items-center justify-between gap-4 hover:bg-slate-50/50 dark:hover:bg-slate-900/30 p-3 rounded-xl transition-colors"
                  >
                    <div className="space-y-1.5 min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <Link
                          to={`/complaints/${c.complaint_id}`}
                          className="text-sm font-bold text-slate-900 dark:text-slate-100 hover:text-primary transition-colors"
                        >
                          {c.title || "Untitled Issue"}
                        </Link>
                        <span className="text-[11px] font-mono px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                          {c.complaint_id}
                        </span>
                        <Badge tone={getPriorityTone(c.priority)}>
                          {c.priority || "Medium"}
                        </Badge>
                        <Badge tone={getStatusTone(c.status)}>
                          {c.status}
                        </Badge>
                        {getDeadlineBadge(c)}
                      </div>

                      <p className="text-xs text-slate-500 line-clamp-1">
                        {c.description}
                      </p>

                      <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400">
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {getLocationName(c.location_id, locations)}
                        </span>
                        <span>•</span>
                        <span>{c.category || c.complaint_type || "General"}</span>
                        <span>•</span>
                        <span>Assigned {c.assigned_at ? formatDate(c.assigned_at) : "Recently"}</span>
                      </div>
                    </div>

                    {/* Primary Big Action & More Menu */}
                    <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
                      {/* One Big Primary Action Button */}
                      {c.status === "Assigned" && (
                        <Button
                          size="md"
                          variant="primary"
                          onClick={() => handleStartWork(c.complaint_id)}
                          className="font-bold text-xs flex items-center gap-1.5 shadow-sm py-2 px-5"
                        >
                          <PlayCircle className="h-4 w-4" />
                          Start Work
                        </Button>
                      )}

                      {c.status === "In Progress" && (
                        <Button
                          size="md"
                          variant="success"
                          onClick={() => handleOpenResolveModal(c)}
                          className="font-bold text-xs flex items-center gap-1.5 shadow-sm py-2 px-5"
                        >
                          <Check className="h-4 w-4" />
                          Mark Done
                        </Button>
                      )}

                      {c.status === "Waiting for Parts" && (
                        <Button
                          size="md"
                          variant="primary"
                          onClick={() => handleResumeWork(c.complaint_id)}
                          className="font-bold text-xs flex items-center gap-1.5 shadow-sm py-2 px-5"
                        >
                          <PlayCircle className="h-4 w-4" />
                          Resume Work
                        </Button>
                      )}

                      {c.status === "Pending Warden Verification" && (
                        <span className="text-[11px] text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-purple-950/40 px-3 py-1.5 rounded-lg font-semibold border border-purple-200 dark:border-purple-800">
                          Awaiting Warden Inspection
                        </span>
                      )}

                      {c.status === "Waiting for Verification" && (
                        <span className="text-[11px] text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/40 px-3 py-1.5 rounded-lg font-semibold border border-emerald-200 dark:border-emerald-800">
                          Awaiting Student Confirmation
                        </span>
                      )}

                      {/* Details Button */}
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => navigate(`/complaints/${c.complaint_id}`)}
                        className="text-xs"
                      >
                        Details
                      </Button>

                      {/* More Dropdown Menu */}
                      <div className="relative">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() =>
                            setOpenMenuComplaintId(
                              openMenuComplaintId === c.complaint_id ? null : c.complaint_id,
                            )
                          }
                          className="!p-1.5 text-slate-500 hover:text-slate-800"
                          title="More options"
                        >
                          <MoreVertical className="h-4 w-4" />
                        </Button>

                        {openMenuComplaintId === c.complaint_id && (
                          <div className="absolute right-0 top-8 z-30 w-56 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-[#101726] p-2 shadow-lg space-y-1">
                            <div className="px-2 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                              Quick Presets
                            </div>

                            {PRESET_NOTES.map((preset, idx) => (
                              <button
                                key={idx}
                                type="button"
                                onClick={() => handleQuickPresetNote(c.complaint_id, preset)}
                                className="w-full text-left px-2 py-1.5 text-xs rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors flex items-center gap-1.5"
                              >
                                <span className="h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
                                {preset}
                              </button>
                            ))}

                            <div className="border-t border-slate-100 dark:border-slate-800 my-1" />

                            <button
                              type="button"
                              onClick={() => {
                                setSelectedComplaint(c);
                                setShowProgressModal(true);
                                setOpenMenuComplaintId(null);
                              }}
                              className="w-full text-left px-2 py-1.5 text-xs rounded-lg text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors flex items-center gap-1.5"
                            >
                              <FileText className="h-3.5 w-3.5 text-slate-400" />
                              Custom Progress Note
                            </button>

                            {c.status === "In Progress" && (
                              <button
                                type="button"
                                onClick={() => {
                                  setSelectedComplaint(c);
                                  setShowPauseModal(true);
                                  setOpenMenuComplaintId(null);
                                }}
                                className="w-full text-left px-2 py-1.5 text-xs rounded-lg text-amber-700 dark:text-amber-300 hover:bg-amber-50 dark:hover:bg-amber-950/40 transition-colors flex items-center gap-1.5"
                              >
                                <PauseCircle className="h-3.5 w-3.5" />
                                Waiting for Parts (Pause)
                              </button>
                            )}

                            <button
                              type="button"
                              onClick={() => {
                                setSelectedComplaint(c);
                                setShowWrongLocationModal(true);
                                setOpenMenuComplaintId(null);
                              }}
                              className="w-full text-left px-2 py-1.5 text-xs rounded-lg text-rose-700 dark:text-rose-300 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors flex items-center gap-1.5"
                            >
                              <MapPin className="h-3.5 w-3.5" />
                              Report Wrong Location
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Action Modals */}

      {/* Progress Note Modal */}
      {showProgressModal && (
        <Modal
          isOpen={showProgressModal}
          onClose={() => {
            setShowProgressModal(false);
            setSelectedComplaint(null);
          }}
          title="📝 Add Progress Note"
        >
          <form onSubmit={handleProgressNoteSubmit} className="space-y-4">
            <p className="text-xs text-slate-500">
              Record real-time field progress on ticket <strong>{selectedComplaint?.complaint_id}</strong>.
            </p>
            <Textarea
              label="Progress Update"
              value={progressNoteText}
              onChange={(e) => setProgressNoteText(e.target.value)}
              placeholder="e.g. Work underway, testing circuit breaker..."
              rows={4}
              required
            />
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowProgressModal(false);
                  setSelectedComplaint(null);
                }}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary" disabled={submittingProgressNote}>
                {submittingProgressNote ? "Saving..." : "Log Progress Note"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Pause Modal */}
      {showPauseModal && (
        <Modal
          isOpen={showPauseModal}
          onClose={() => {
            setShowPauseModal(false);
            setSelectedComplaint(null);
          }}
          title="⏸️ Pause Work (Waiting for Parts)"
        >
          <form onSubmit={handlePauseSubmit} className="space-y-4">
            <p className="text-xs text-slate-500">
              Temporarily pause work on ticket <strong>{selectedComplaint?.complaint_id}</strong> while awaiting replacement components.
            </p>
            <Textarea
              label="Reason for Delay"
              value={pauseReasonText}
              onChange={(e) => setPauseReasonText(e.target.value)}
              placeholder="e.g. Awaiting specialized replacement valve from central stores..."
              rows={3}
              required
            />
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowPauseModal(false);
                  setSelectedComplaint(null);
                }}
              >
                Cancel
              </Button>
              <Button type="submit" variant="warning" disabled={submittingPause}>
                {submittingPause ? "Pausing..." : "Pause Ticket"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Wrong Location Modal */}
      {showWrongLocationModal && (
        <Modal
          isOpen={showWrongLocationModal}
          onClose={() => {
            setShowWrongLocationModal(false);
            setSelectedComplaint(null);
          }}
          title="📍 Report Wrong Location"
        >
          <form onSubmit={handleWrongLocationSubmit} className="space-y-4">
            <p className="text-xs text-slate-500">
              Flag that ticket <strong>{selectedComplaint?.complaint_id}</strong> was filed for the wrong room/location.
              This notifies the Warden and App Manager for re-routing.
            </p>
            <Textarea
              label="Location Note / Correct Room"
              value={wrongLocationNotes}
              onChange={(e) => setWrongLocationNotes(e.target.value)}
              placeholder="e.g. Actual room is Block B Room 302, not Block A..."
              rows={3}
              required
            />
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowWrongLocationModal(false);
                  setSelectedComplaint(null);
                }}
              >
                Cancel
              </Button>
              <Button type="submit" variant="danger" disabled={submittingWrongLocation}>
                {submittingWrongLocation ? "Reporting..." : "Flag Wrong Location"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Mark Done Modal */}
      {showResolveModal && (
        <Modal
          isOpen={showResolveModal}
          onClose={() => {
            setShowResolveModal(false);
            setSelectedComplaint(null);
          }}
          title="✅ Mark Work Completed"
        >
          <form onSubmit={handleResolveSubmit} className="space-y-4">
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 text-xs space-y-1">
              <div className="font-bold text-slate-900 dark:text-slate-100">
                {selectedComplaint?.title}
              </div>
              <div className="text-slate-500">
                {selectedComplaint?.description}
              </div>
              {["high", "critical"].includes((selectedComplaint?.priority || "").toLowerCase()) && (
                <div className="font-bold text-amber-600 dark:text-amber-400 pt-1">
                  ⚠️ High/Critical priority tickets require an After Repair photo or explicit skip reason.
                </div>
              )}
            </div>

            {/* Hidden file inputs: camera first with capture, gallery as fallback */}
            <input
              type="file"
              ref={cameraInputRef}
              accept="image/*"
              capture="environment"
              className="hidden"
              onChange={(e) => {
                setResolvePhotoFile(e.target.files?.[0] || null);
                setIsPhotoSkipped(false);
              }}
            />
            <input
              type="file"
              ref={galleryInputRef}
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                setResolvePhotoFile(e.target.files?.[0] || null);
                setIsPhotoSkipped(false);
              }}
            />

            {/* Photo Section */}
            {!isPhotoSkipped ? (
              <div className="space-y-2">
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                  After Repair Photo{" "}
                  {studentHasPhoto ? "(Matches student's before photo)" : "(Optional)"}
                </label>

                <div className="grid grid-cols-2 gap-2.5">
                  <button
                    type="button"
                    onClick={() => cameraInputRef.current?.click()}
                    className="flex items-center justify-center gap-1.5 p-3 rounded-xl border border-dashed border-primary bg-primary/5 text-primary text-xs font-bold hover:bg-primary/10 transition-colors"
                  >
                    <Camera className="h-4 w-4" />
                    Take Photo (Camera)
                  </button>
                  <button
                    type="button"
                    onClick={() => galleryInputRef.current?.click()}
                    className="flex items-center justify-center gap-1.5 p-3 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-700 dark:text-slate-300 text-xs font-bold hover:bg-slate-100 transition-colors"
                  >
                    <Upload className="h-4 w-4" />
                    From Gallery
                  </button>
                </div>

                {resolvePhotoFile && (
                  <div className="flex items-center justify-between p-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 text-emerald-700 dark:text-emerald-300 text-xs">
                    <span className="font-semibold truncate">Selected: {resolvePhotoFile.name}</span>
                    <button
                      type="button"
                      onClick={() => setResolvePhotoFile(null)}
                      className="text-rose-600 hover:text-rose-800 p-1"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                )}

                {/* Skip button only when student had a photo */}
                {studentHasPhoto && (
                  <div className="pt-1">
                    <button
                      type="button"
                      onClick={() => {
                        setIsPhotoSkipped(true);
                        setResolvePhotoFile(null);
                      }}
                      className="text-[11px] font-semibold text-amber-600 dark:text-amber-400 hover:underline flex items-center gap-1"
                    >
                      Skip – student photo not relevant
                    </button>
                  </div>
                )}
              </div>
            ) : (
              /* Photo Skipped Mode */
              <div className="p-3 rounded-xl border border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 text-amber-900 dark:text-amber-200 space-y-2">
                <div className="flex items-center justify-between text-xs font-bold">
                  <span>Photo Skipped — Reason Required</span>
                  <button
                    type="button"
                    onClick={() => setIsPhotoSkipped(false)}
                    className="text-primary hover:underline font-semibold text-[11px]"
                  >
                    Cancel Skip & Take Photo
                  </button>
                </div>
                <p className="text-[11px] text-amber-800/80 dark:text-amber-300/80">
                  Student provided a photo. Explain why an "After" photo is not relevant:
                </p>
                <input
                  type="text"
                  value={photoSkipReason}
                  onChange={(e) => setPhotoSkipReason(e.target.value)}
                  placeholder="e.g. Student attached a meme/blank image, issue was software setting..."
                  className="w-full h-9 rounded-xl border border-amber-300 dark:border-amber-700 bg-white dark:bg-slate-900 px-3 text-xs outline-none focus:border-amber-500 text-slate-800 dark:text-slate-100"
                  required
                />
              </div>
            )}

            {/* Resolution Preset or Note */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                Resolution Preset (One-Tap)
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5 mb-2">
                {RESOLUTION_PRESETS.map((p, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => setResolvePreset(resolvePreset === p ? "" : p)}
                    className={`p-2 rounded-xl text-left text-xs transition-colors border ${
                      resolvePreset === p
                        ? "border-primary bg-primary/10 text-primary font-bold"
                        : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300"
                    }`}
                  >
                    {p}
                  </button>
                ))}
              </div>

              <Textarea
                label="Additional Completion Details"
                value={resolveNotesText}
                onChange={(e) => setResolveNotesText(e.target.value)}
                placeholder="Describe work completed, components replaced..."
                rows={2}
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setShowResolveModal(false);
                  setSelectedComplaint(null);
                }}
              >
                Cancel
              </Button>
              <Button type="submit" variant="success" disabled={submittingResolve}>
                {submittingResolve ? "Submitting..." : "Submit Resolution"}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
