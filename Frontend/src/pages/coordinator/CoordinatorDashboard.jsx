import { useMemo, useState } from "react";
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

export default function CoordinatorDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState("available"); // "available" | "my_work"
  const [toastMessage, setToastMessage] = useState("");
  const [toastTone, setToastTone] = useState("success");

  // Action Modals State
  const [selectedComplaint, setSelectedComplaint] = useState(null);

  const [showProgressModal, setShowProgressModal] = useState(false);
  const [progressNoteText, setProgressNoteText] = useState("");
  const [submittingProgressNote, setSubmittingProgressNote] = useState(false);

  const [showPauseModal, setShowPauseModal] = useState(false);
  const [pauseReasonText, setPauseReasonText] = useState("");
  const [submittingPause, setSubmittingPause] = useState(false);

  const [showResolveModal, setShowResolveModal] = useState(false);
  const [resolveNotesText, setResolveNotesText] = useState("");
  const [resolvePhotoFile, setResolvePhotoFile] = useState(null);
  const [submittingResolve, setSubmittingResolve] = useState(false);

  const {
    data: dashboardData,
    loading,
    error,
    reload,
  } = useAsyncData(
    async () => {
      const [compRes, ancRes, notifRes, locRes] = await Promise.all([
        complaintService.list().catch(() => ({ data: [] })),
        announcementService.list().catch(() => ({ data: [] })),
        notificationService
          .listPaginated({ limit: 5 })
          .then((res) => ({ data: res.data.items }))
          .catch(() => ({ data: [] })),
        locationService.list().catch(() => ({ data: [] })),
      ]);
      return {
        complaints: compRes.data || [],
        announcements: ancRes.data || [],
        notifications: notifRes.data || [],
        locations: locRes.data || [],
      };
    },
    { complaints: [], announcements: [], notifications: [], locations: [] },
  );

  const complaints = dashboardData?.complaints || [];
  const announcements = dashboardData?.announcements || [];
  const notifications = dashboardData?.notifications || [];
  const locations = dashboardData?.locations || [];

  // Filter 1: Available Work (Unassigned or unaccepted queue matching coordinator's department or location)
  const availableComplaints = useMemo(() => {
    return complaints.filter((c) => {
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
    });
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
        setToastMessage("Taken by another coordinator.");
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

  const handleResolveSubmit = async (e) => {
    e.preventDefault();
    if (!selectedComplaint) return;

    const p = (selectedComplaint.priority || "Medium").toLowerCase();
    const isHighOrCrit = p === "high" || p === "critical";

    if (isHighOrCrit && !resolvePhotoFile) {
      setToastTone("danger");
      setToastMessage("High/Critical priority tickets require an After Repair photo.");
      return;
    }

    if (!resolvePhotoFile && !resolveNotesText.trim()) {
      setToastTone("danger");
      setToastMessage("Resolution notes are required when no photo is provided.");
      return;
    }

    setSubmittingResolve(true);
    try {
      if (resolvePhotoFile) {
        await attachmentService.upload(selectedComplaint.complaint_id, [resolvePhotoFile], "After Repair");
      }
      await complaintService.resolve(selectedComplaint.complaint_id, resolveNotesText.trim());
      setToastTone("success");
      setToastMessage("Work marked completed and submitted for verification!");
      setShowResolveModal(false);
      setResolveNotesText("");
      setResolvePhotoFile(null);
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
            Good morning, {user?.name || "Coordinator"}
          </h1>
          <p className="text-xs font-normal text-slate-500 dark:text-slate-400 mt-1">
            Department Operations & Field Execution • {myWorkComplaints.length} active assigned tickets
          </p>
        </div>
        <div className="flex items-center gap-2.5 shrink-0">
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
          label="Paused (Waiting Parts)"
          value={myWorkComplaints.filter((c) => c.status === "Waiting for Parts").length}
          subtext="SLA paused for spare parts"
          onClick={() => setActiveTab("my_work")}
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
                Tickets awaiting pickup in your department/location queue. Click <strong>Accept</strong> to claim.
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
                    className="py-4 first:pt-0 last:pb-0 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50/50 dark:hover:bg-slate-900/30 p-2 rounded-xl transition-colors"
                  >
                    <div className="space-y-1 min-w-0">
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
                        size="sm"
                        variant="primary"
                        onClick={() => handleAccept(c.complaint_id)}
                        className="font-bold text-xs flex items-center gap-1.5 shadow-2xs"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5" />
                        Accept Ticket
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
                Active tickets assigned to you. Perform real-time work transitions below.
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
                    className="py-4 first:pt-0 last:pb-0 flex flex-col lg:flex-row lg:items-center justify-between gap-4 hover:bg-slate-50/50 dark:hover:bg-slate-900/30 p-2.5 rounded-xl transition-colors"
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
                        {c.sla_status && (
                          <Badge tone={getSlaTone(c.sla_status)}>
                            {c.sla_status}
                          </Badge>
                        )}
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
                        {c.due_date && (
                          <>
                            <span>•</span>
                            <span className="text-slate-600 dark:text-slate-300 font-medium">
                              SLA Due: {formatDate(c.due_date)}
                            </span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Action Buttons for this Ticket */}
                    <div className="flex flex-wrap items-center gap-2 shrink-0">
                      {c.status === "Assigned" && (
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() => handleStartWork(c.complaint_id)}
                          className="font-bold text-xs flex items-center gap-1 shadow-2xs"
                        >
                          <PlayCircle className="h-3.5 w-3.5" />
                          Start Work
                        </Button>
                      )}

                      {c.status === "In Progress" && (
                        <>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedComplaint(c);
                              setShowProgressModal(true);
                            }}
                            className="text-xs flex items-center gap-1"
                          >
                            <FileText className="h-3.5 w-3.5" />
                            Progress Note
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedComplaint(c);
                              setShowPauseModal(true);
                            }}
                            className="text-xs text-amber-700 dark:text-amber-300 border-amber-300 dark:border-amber-800 hover:bg-amber-50 flex items-center gap-1"
                          >
                            <PauseCircle className="h-3.5 w-3.5" />
                            Waiting Parts
                          </Button>
                          <Button
                            size="sm"
                            variant="success"
                            onClick={() => {
                              setSelectedComplaint(c);
                              setShowResolveModal(true);
                            }}
                            className="font-bold text-xs flex items-center gap-1"
                          >
                            <Check className="h-3.5 w-3.5" />
                            Mark Done
                          </Button>
                        </>
                      )}

                      {c.status === "Waiting for Parts" && (
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() => handleResumeWork(c.complaint_id)}
                          className="font-bold text-xs flex items-center gap-1"
                        >
                          <PlayCircle className="h-3.5 w-3.5" />
                          Resume Work
                        </Button>
                      )}

                      {c.status === "Pending Warden Verification" && (
                        <span className="text-[11px] text-purple-700 dark:text-purple-300 bg-purple-50 dark:bg-purple-950/40 px-2.5 py-1 rounded-md font-semibold border border-purple-200 dark:border-purple-800">
                          Awaiting Warden Inspection
                        </span>
                      )}

                      {c.status === "Waiting for Verification" && (
                        <span className="text-[11px] text-emerald-700 dark:text-emerald-300 bg-emerald-50 dark:bg-emerald-950/40 px-2.5 py-1 rounded-md font-semibold border border-emerald-200 dark:border-emerald-800">
                          Awaiting Student Confirmation
                        </span>
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
              placeholder="e.g. Awaiting specialized replacement valve from store..."
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
            <p className="text-xs text-slate-500">
              Complete physical work on ticket <strong>{selectedComplaint?.complaint_id}</strong>.
              {["high", "critical"].includes((selectedComplaint?.priority || "").toLowerCase()) && (
                <span className="block mt-1 font-bold text-amber-600 dark:text-amber-400">
                  ⚠️ High/Critical priority tickets require an "After Repair" photo attachment.
                </span>
              )}
            </p>
            <Textarea
              label="Resolution Notes"
              value={resolveNotesText}
              onChange={(e) => setResolveNotesText(e.target.value)}
              placeholder="Describe work completed, components replaced..."
              rows={3}
            />
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                After Repair Photo{" "}
                {["high", "critical"].includes((selectedComplaint?.priority || "").toLowerCase())
                  ? "(Required)"
                  : "(Recommended)"}
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setResolvePhotoFile(e.target.files?.[0] || null)}
                className="block w-full text-xs text-slate-500 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-primary file:text-white hover:file:bg-primary/90 cursor-pointer"
              />
              {resolvePhotoFile && (
                <p className="text-[11px] text-emerald-600 font-medium mt-1">
                  Selected: {resolvePhotoFile.name}
                </p>
              )}
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
