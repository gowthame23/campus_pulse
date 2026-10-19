import { useState, useEffect } from "react";
import {
  Wrench,
  Clock,
  AlertTriangle,
  MapPin,
  CheckCircle2,
  Calendar,
  MoreVertical,
  Play,
  Pause,
  RotateCcw,
  Navigation,
  FileText,
  Camera,
  Check,
  TrendingUp,
  RefreshCw,
  X,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import ActionPill from "../../components/ActionPill.jsx";
import Modal from "../../components/Modal.jsx";
import LeaveModal from "../../components/LeaveModal.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { useLanguage } from "../../context/LanguageContext.jsx";
import { complaintService } from "../../services/complaintService.js";
import { locationService } from "../../services/locationService.js";
import { teamService } from "../../services/teamService.js";
import { formatDate } from "../../utils/dateFormatter.js";
import {
  getStatusTone,
  getPriorityTone,
  getStatusLabel,
  getPriorityLabel,
} from "../../utils/statusColor.js";

export default function EmployeeDashboard() {
  const { user } = useAuth();
  const { t } = useLanguage();

  const presetNotes = [
    { code: "NEED_PARTS", label: t("presets.need_parts", "Need parts") },
    { code: "WAITING_ACCESS", label: t("presets.waiting_access", "Waiting for access") },
    { code: "WORKSHOP", label: t("presets.workshop", "Sent to workshop") },
    { code: "INVESTIGATING", label: t("presets.investigating", "Investigating on site") },
  ];

  const [complaints, setComplaints] = useState([]);
  const [locations, setLocations] = useState([]);
  const [teams, setTeams] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("jobs"); // "jobs" | "stats"

  // Modals state
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);

  // Mark Done Modal
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [resolveNotes, setResolveNotes] = useState("");
  const [resolvePreset, setResolvePreset] = useState("");
  const [proofUrl, setProofUrl] = useState("");
  const [skipPhoto, setSkipPhoto] = useState(false);
  const [skipPhotoReason, setSkipPhotoReason] = useState("");
  const [resolving, setResolving] = useState(false);
  const [resolveError, setResolveError] = useState("");

  // More Menu / Action Modals
  const [showReturnModal, setShowReturnModal] = useState(false);
  const [returnReason, setReturnReason] = useState("");
  const [returning, setReturning] = useState(false);

  const [showPartsModal, setShowPartsModal] = useState(false);
  const [partsReason, setPartsReason] = useState("");
  const [partsExpectedDate, setPartsExpectedDate] = useState("");
  const [pausingParts, setPausingParts] = useState(false);

  const [showWrongLocModal, setShowWrongLocModal] = useState(false);
  const [newLocationId, setNewLocationId] = useState("");
  const [wrongLocNote, setWrongLocNote] = useState("");
  const [reportingWrongLoc, setReportingWrongLoc] = useState(false);

  const [openMenuJobId, setOpenMenuJobId] = useState(null);
  const [toastMsg, setToastMsg] = useState("");

  const showToast = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(""), 4000);
  };

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [compRes, locRes, teamRes, statsRes] = await Promise.all([
        complaintService.list({ include_archived: false }),
        locationService.list(),
        teamService.list({ active_only: true }),
        complaintService.getCoordinatorStats(),
      ]);

      const allComps = compRes.data?.complaints || compRes.data || [];
      // Rule K2: Only jobs assigned to this worker
      const myJobs = allComps.filter(
        (c) => c.assigned_to === user?.user_id && !["Closed", "Closed (Auto Closed)"].includes(c.status)
      );
      setComplaints(myJobs);

      setLocations(locRes.data || locRes || []);
      setTeams(teamRes.data || teamRes || []);
      setStats(statsRes.data || statsRes || null);
    } catch (err) {
      console.error("Failed to load employee dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  const myTeams = teams.filter((t) => t.member_ids?.includes(user?.user_id));
  const myTeam = myTeams[0] || null;
  const coveringTeam = teams.find(
    (t) =>
      t.backup_coordinator_id === user?.user_id &&
      t.acting_coordinator_id === user?.user_id &&
      t.coordinator_on_leave
  );

  // Handler: Start Job
  const handleStartJob = async (job) => {
    try {
      await complaintService.updateStatus(job.complaint_id, "In Progress");
      showToast(t("employee.toast_job_started", "Job started — status set to In Progress."));
      loadData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to start job.");
    }
  };

  // Handler: Add Preset Note
  const handlePresetNote = async (job, noteObj) => {
    try {
      await complaintService.recordProgress(job.complaint_id, noteObj.label, null, noteObj.code);
      showToast(t("employee.toast_progress_note", { note: noteObj.label }));
      loadData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to record progress.");
    }
  };

  // Handler: Return to Coordinator
  const handleConfirmReturn = async () => {
    if (!returnReason.trim()) return;
    setReturning(true);
    try {
      await complaintService.returnToCoordinator(selectedJob.complaint_id, returnReason.trim());
      showToast(t("employee.toast_returned", "Returned complaint to coordinator."));
      setShowReturnModal(false);
      setSelectedJob(null);
      setReturnReason("");
      loadData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to return complaint.");
    } finally {
      setReturning(false);
    }
  };

  // Handler: Waiting for parts
  const handleConfirmParts = async () => {
    if (!partsReason.trim()) return;
    setPausingParts(true);
    try {
      await complaintService.block(
        selectedJob.complaint_id,
        partsReason.trim(),
        partsExpectedDate || null
      );
      showToast(t("employee.toast_waiting_parts", "Job marked as Waiting for Parts."));
      setShowPartsModal(false);
      setSelectedJob(null);
      setPartsReason("");
      setPartsExpectedDate("");
      loadData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to pause for parts.");
    } finally {
      setPausingParts(false);
    }
  };

  // Handler: Report wrong location
  const handleConfirmWrongLocation = async () => {
    if (!newLocationId) return;
    setReportingWrongLoc(true);
    try {
      await complaintService.reportWrongLocation(
        selectedJob.complaint_id,
        newLocationId,
        wrongLocNote.trim()
      );
      showToast(t("employee.toast_location_updated", "Location updated. Re-routed to the correct team."));
      setShowWrongLocModal(false);
      setSelectedJob(null);
      setNewLocationId("");
      setWrongLocNote("");
      loadData();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to update location.");
    } finally {
      setReportingWrongLoc(false);
    }
  };

  // Handler: Mark Done
  const handleOpenResolve = (job) => {
    setSelectedJob(job);
    setResolveNotes("");
    setResolvePreset("");
    setProofUrl("");
    setSkipPhoto(false);
    setSkipPhotoReason("");
    setResolveError("");
    setShowResolveModal(true);
  };

  const handleConfirmResolve = async (e) => {
    e.preventDefault();
    if (!selectedJob) return;

    const studentHadPhoto = Boolean(selectedJob.attachment_url);
    if (studentHadPhoto && !proofUrl.trim() && !skipPhoto) {
      setResolveError("Photo is required when student provided a photo (or check Skip Photo).");
      return;
    }
    if (!studentHadPhoto && !proofUrl.trim() && !resolveNotes.trim() && !resolvePreset) {
      setResolveError("Please provide resolution notes or select a preset note.");
      return;
    }

    setResolving(true);
    setResolveError("");
    try {
      await complaintService.resolve(selectedJob.complaint_id, {
        notes: resolveNotes.trim() || undefined,
        preset_code: resolvePreset || undefined,
        proof_url: proofUrl.trim() || undefined,
        skip_photo: skipPhoto,
        photo_skip_reason: skipPhoto ? skipPhotoReason.trim() : undefined,
      });
      showToast(t("employee.toast_resolved", "Complaint marked as resolved!"));
      setShowResolveModal(false);
      setSelectedJob(null);
      loadData();
    } catch (err) {
      setResolveError(err.response?.data?.detail || "Failed to mark resolved.");
    } finally {
      setResolving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto pb-12">
      {/* Toast */}
      {toastMsg && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 text-white px-4 py-3 rounded-xl shadow-lg border border-slate-700 text-sm flex items-center gap-2">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Top Bar (Part K2) */}
      <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 sm:p-6 border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="text-xl font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Wrench className="h-5 w-5 text-blue-600" />
            {user?.name || t("roles.employee", "Employee")}
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium">
              {t("roles.employee", "Employee")}
            </span>
          </div>
          <div className="text-xs text-slate-500 dark:text-slate-400 mt-1.5 flex flex-wrap items-center gap-1.5">
            <span className="font-semibold">{t("employee.department", "Department:")}</span>
            <span className="px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950/50 text-blue-700 dark:text-blue-300 font-semibold text-[11px] border border-blue-200 dark:border-blue-800">
              {user?.department_name || user?.department_id || t("employee.campus_maintenance", "Campus Maintenance")}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Button
            variant="secondary"
            className="flex-1 sm:flex-none flex items-center justify-center gap-1.5 text-xs font-semibold"
            onClick={() => setShowLeaveModal(true)}
          >
            <Calendar className="h-4 w-4 text-amber-500" />
            {t("employee.on_leave_btn", "I am on leave")}
          </Button>
          <Button
            variant="ghost"
            className="p-2"
            onClick={loadData}
            title={t("common.refresh", "Refresh")}
          >
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </div>
      </div>

      {/* Rule 1.5: Acting Coordinator Coverage Banner */}
      {coveringTeam && (
        <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-200 rounded-2xl p-4 flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0" />
          <div className="text-sm">
            {t("employee.covering_banner", {
              name: coveringTeam.coordinator_name || t("roles.coordinator", "Coordinator"),
              date: coveringTeam.coordinator_leave_until || "leave ends"
            })}
          </div>
        </div>
      )}

      {/* Main Action Pill Block & View Switcher */}
      <div className="grid grid-cols-2 gap-2 sm:gap-3 max-w-md">
        <ActionPill
          icon={Wrench}
          label={t("employee.my_jobs_tab", "My Jobs")}
          count={complaints.filter((c) => !["Closed", "Closed (Auto Closed)", "Rejected"].includes(c.status)).length}
          active={activeTab === "jobs"}
          onClick={() => setActiveTab("jobs")}
          tone="blue"
        />
        <ActionPill
          icon={TrendingUp}
          label={t("employee.my_stats_tab", "My Stats")}
          active={activeTab === "stats"}
          onClick={() => setActiveTab("stats")}
          tone="purple"
        />
      </div>

      {/* TAB 1: MY JOBS */}
      {activeTab === "jobs" && (
        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-12 text-slate-500">{t("employee.loading_jobs", "Loading assigned jobs...")}</div>
          ) : complaints.length === 0 ? (
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-12 text-center border border-slate-200 dark:border-slate-800">
              <CheckCircle2 className="h-12 w-12 text-emerald-500 mx-auto mb-3" />
              <div className="text-lg font-bold text-slate-800 dark:text-slate-100">
                {t("employee.all_caught_up", "All caught up!")}
              </div>
              <div className="text-sm text-slate-500 mt-1">
                {t("employee.no_jobs_desc", "You currently have no open jobs assigned.")}
              </div>
            </div>
          ) : (
            complaints.map((job) => {
              const loc = locations.find((l) => l.location_id === job.location_id);
              const locName = loc ? loc.name : job.location_id;
              const isMenuOpen = openMenuJobId === job.complaint_id;

              return (
                <div
                  key={job.complaint_id}
                  className="bg-white dark:bg-slate-900 rounded-2xl p-4 sm:p-5 border border-slate-200 dark:border-slate-800 shadow-sm relative transition-all"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2 mb-1.5">
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-semibold ${
                            getPriorityTone(job.priority) || "bg-slate-100 text-slate-700"
                          }`}
                        >
                          {getPriorityLabel(job.priority, t)}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-semibold ${
                            getStatusTone(job.status) || "bg-slate-100 text-slate-700"
                          }`}
                        >
                          {getStatusLabel(job.status, t)}
                        </span>
                        {job.assignee_on_leave_flag && (
                          <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-300">
                            {t("employee.on_leave_badge", "On Leave")}
                          </span>
                        )}
                      </div>

                      <div className="text-base font-bold text-slate-900 dark:text-slate-100 truncate">
                        {job.title || job.category}
                      </div>

                      <div className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex flex-wrap items-center gap-3">
                        <span className="flex items-center gap-1">
                          <MapPin className="h-3.5 w-3.5 text-slate-400" />
                          {locName} {job.exact_spot ? `• ${job.exact_spot}` : ""}
                        </span>
                        {job.sla_deadline && (
                          <span className="flex items-center gap-1">
                            <Clock className="h-3.5 w-3.5 text-slate-400" />
                            {t("employee.sla", "SLA:")} {formatDate(job.sla_deadline)}
                          </span>
                        )}
                      </div>

                      {job.description && (
                        <div className="text-sm text-slate-600 dark:text-slate-300 mt-2 line-clamp-2">
                          {job.description}
                        </div>
                      )}
                    </div>

                    {/* More Menu Toggle */}
                    <div className="relative">
                      <button
                        type="button"
                        onClick={() => setOpenMenuJobId(isMenuOpen ? null : job.complaint_id)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition cursor-pointer"
                      >
                        <MoreVertical className="h-5 w-5" />
                      </button>

                      {isMenuOpen && (
                        <div className="absolute right-0 mt-1 w-52 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-xl z-20 py-1 text-xs">
                          {job.status !== "In Progress" && (
                            <button
                              type="button"
                              onClick={() => {
                                setOpenMenuJobId(null);
                                handleStartJob(job);
                              }}
                              className="w-full px-3 py-2 text-left flex items-center gap-2 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 cursor-pointer"
                            >
                              <Play className="h-3.5 w-3.5 text-emerald-500" />
                              {t("employee.start_job", "Start Job (In Progress)")}
                            </button>
                          )}

                          <div className="border-t border-slate-100 dark:border-slate-700 my-1" />
                          <div className="px-3 py-1 text-[10px] font-semibold text-slate-400 uppercase">
                            {t("employee.preset_notes", "Preset Notes")}
                          </div>
                          {presetNotes.map((preset) => (
                            <button
                              key={preset.code}
                              type="button"
                              onClick={() => {
                                setOpenMenuJobId(null);
                                handlePresetNote(job, preset);
                              }}
                              className="w-full px-3 py-1.5 text-left flex items-center gap-2 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 cursor-pointer"
                            >
                              <FileText className="h-3 w-3 text-blue-500" />
                              {preset.label}
                            </button>
                          ))}

                          <div className="border-t border-slate-100 dark:border-slate-700 my-1" />

                          <button
                            type="button"
                            onClick={() => {
                              setOpenMenuJobId(null);
                              setSelectedJob(job);
                              setShowPartsModal(true);
                            }}
                            className="w-full px-3 py-2 text-left flex items-center gap-2 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 cursor-pointer"
                          >
                            <Pause className="h-3.5 w-3.5 text-amber-500" />
                            {t("employee.waiting_parts", "Waiting for parts")}
                          </button>

                          <button
                            type="button"
                            onClick={() => {
                              setOpenMenuJobId(null);
                              setSelectedJob(job);
                              setShowWrongLocModal(true);
                            }}
                            className="w-full px-3 py-2 text-left flex items-center gap-2 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 cursor-pointer"
                          >
                            <Navigation className="h-3.5 w-3.5 text-indigo-500" />
                            {t("employee.wrong_location", "Wrong location")}
                          </button>

                          <button
                            type="button"
                            onClick={() => {
                              setOpenMenuJobId(null);
                              setSelectedJob(job);
                              setShowReturnModal(true);
                            }}
                            className="w-full px-3 py-2 text-left flex items-center gap-2 hover:bg-slate-100 dark:hover:bg-slate-700 text-rose-600 dark:text-rose-400 cursor-pointer"
                          >
                            <RotateCcw className="h-3.5 w-3.5" />
                            {t("employee.return_coordinator", "Return to coordinator")}
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Big Green Mark Done Button */}
                  <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
                    <span className="text-xs text-slate-500 dark:text-slate-400">
                      {t("employee.id", "ID:")} #{job.complaint_id.slice(-6)}
                    </span>
                    <Button
                      variant="primary"
                      className="bg-emerald-600 hover:bg-emerald-700 text-white font-bold px-5 py-2 text-sm rounded-xl flex items-center gap-2 shadow-sm cursor-pointer"
                      onClick={() => handleOpenResolve(job)}
                    >
                      <Check className="h-4 w-4" />
                      {t("employee.mark_done", "Mark Done")}
                    </Button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* TAB 2: MY STATS */}
      {activeTab === "stats" && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-200 dark:border-slate-800">
              <div className="text-xs font-semibold text-slate-500 uppercase">{t("employee.stats_open_jobs", "Open Jobs")}</div>
              <div className="text-2xl font-black text-slate-900 dark:text-slate-100 mt-1">
                {stats?.open_jobs ?? complaints.length}
              </div>
            </div>
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-200 dark:border-slate-800">
              <div className="text-xs font-semibold text-slate-500 uppercase">{t("employee.stats_completed_month", "Completed This Month")}</div>
              <div className="text-2xl font-black text-emerald-600 mt-1">
                {stats?.completed_this_month ?? 0}
              </div>
            </div>
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-200 dark:border-slate-800">
              <div className="text-xs font-semibold text-slate-500 uppercase">{t("employee.stats_avg_fix_time", "Avg Time to Fix")}</div>
              <div className="text-2xl font-black text-blue-600 mt-1">
                {stats?.avg_time_to_fix ? `${stats.avg_time_to_fix}h` : "N/A"}
              </div>
            </div>
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-200 dark:border-slate-800">
              <div className="text-xs font-semibold text-slate-500 uppercase">{t("employee.stats_on_time_rate", "On-time Rate")}</div>
              <div className="text-2xl font-black text-indigo-600 mt-1">
                {stats?.on_time_rate ?? 100}%
              </div>
            </div>
            <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 border border-slate-200 dark:border-slate-800">
              <div className="text-xs font-semibold text-slate-500 uppercase">{t("employee.stats_warden_rejections", "Warden Rejections")}</div>
              <div className="text-2xl font-black text-rose-600 mt-1">
                {stats?.warden_rejections ?? 0}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MARK DONE MODAL */}
      <Modal
        isOpen={showResolveModal}
        onClose={() => setShowResolveModal(false)}
        title={t("employee.modal_resolve_title", "Mark Job as Resolved")}
      >
        <form onSubmit={handleConfirmResolve} className="space-y-4">
          {resolveError && (
            <div className="p-3 text-sm bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 rounded-lg border border-rose-200">
              {resolveError}
            </div>
          )}

          {selectedJob && (
            <div className="p-3 bg-slate-50 dark:bg-slate-800/60 rounded-xl text-sm">
              <div className="font-semibold">{selectedJob.title || selectedJob.category}</div>
              <div className="text-xs text-slate-500 mt-0.5">
                {t("employee.student_photo", "Student Photo:")}{" "}
                <span className="font-medium text-slate-700 dark:text-slate-300">
                  {selectedJob.attachment_url ? t("employee.photo_provided", "Provided (After photo mandatory or skip)") : t("common.none", "None")}
                </span>
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
              {t("employee.photo_url_label", "After-repair Photo URL")}
            </label>
            <input
              type="text"
              placeholder={t("employee.photo_url_placeholder", "https://... or uploaded image URL")}
              value={proofUrl}
              onChange={(e) => setProofUrl(e.target.value)}
              disabled={skipPhoto}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {selectedJob?.attachment_url && (
            <div className="space-y-2 p-3 bg-amber-50 dark:bg-amber-950/30 rounded-xl border border-amber-200 dark:border-amber-800">
              <label className="flex items-center gap-2 text-xs font-semibold text-amber-900 dark:text-amber-200 cursor-pointer">
                <input
                  type="checkbox"
                  checked={skipPhoto}
                  onChange={(e) => setSkipPhoto(e.target.checked)}
                  className="rounded text-blue-600"
                />
                {t("employee.skip_photo", "Skip after-repair photo")}
              </label>
              {skipPhoto && (
                <input
                  type="text"
                  placeholder={t("employee.skip_photo_placeholder", "Reason for skipping photo...")}
                  value={skipPhotoReason}
                  onChange={(e) => setSkipPhotoReason(e.target.value)}
                  className="w-full text-xs rounded border border-amber-300 bg-white dark:bg-slate-900 p-1.5 text-slate-900 dark:text-slate-100 outline-none"
                  required
                />
              )}
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
              {t("employee.resolution_notes_label", "Resolution Notes")}
            </label>
            <textarea
              rows={2}
              placeholder={t("employee.resolution_notes_placeholder", "What was fixed...")}
              value={resolveNotes}
              onChange={(e) => setResolveNotes(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
            <Button variant="secondary" onClick={() => setShowResolveModal(false)} disabled={resolving}>
              {t("common.cancel", "Cancel")}
            </Button>
            <Button variant="primary" type="submit" disabled={resolving} className="bg-emerald-600 hover:bg-emerald-700 text-white cursor-pointer font-bold">
              {resolving ? t("employee.submitting", "Submitting...") : t("employee.confirm_mark_done", "Mark Done")}
            </Button>
          </div>
        </form>
      </Modal>

      {/* RETURN TO COORDINATOR MODAL */}
      <Modal
        isOpen={showReturnModal}
        onClose={() => setShowReturnModal(false)}
        title={t("employee.modal_return_title", "Return Job to Coordinator")}
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-500">
            {t("employee.modal_return_desc", "This complaint will return to the 'To assign' queue, and the coordinator will be notified.")}
          </p>
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
              {t("employee.return_reason_label", "Reason for Return")} <span className="text-rose-500">*</span>
            </label>
            <textarea
              rows={3}
              placeholder={t("employee.return_reason_placeholder", "e.g. Requires specialized tools, wrong specialty...")}
              value={returnReason}
              onChange={(e) => setReturnReason(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowReturnModal(false)} disabled={returning}>
              {t("common.cancel", "Cancel")}
            </Button>
            <Button
              variant="danger"
              disabled={!returnReason.trim() || returning}
              onClick={handleConfirmReturn}
              className="cursor-pointer font-bold"
            >
              {returning ? t("employee.submitting", "Submitting...") : t("employee.return_queue_btn", "Return to Queue")}
            </Button>
          </div>
        </div>
      </Modal>

      {/* WAITING FOR PARTS MODAL */}
      <Modal
        isOpen={showPartsModal}
        onClose={() => setShowPartsModal(false)}
        title={t("employee.modal_parts_title", "Waiting for Parts")}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
              {t("employee.parts_needed_label", "Parts Details / Reason")} <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              placeholder={t("employee.parts_needed_placeholder", "e.g. 25W LED tube light ordered from supplier")}
              value={partsReason}
              onChange={(e) => setPartsReason(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
              {t("employee.expected_date_label", "Expected Arrival Date (Optional)")}
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
              {t("common.cancel", "Cancel")}
            </Button>
            <Button
              variant="primary"
              disabled={!partsReason.trim() || pausingParts}
              onClick={handleConfirmParts}
              className="cursor-pointer font-bold"
            >
              {pausingParts ? t("employee.submitting", "Submitting...") : t("employee.confirm_pause", "Pause for Parts")}
            </Button>
          </div>
        </div>
      </Modal>

      {/* WRONG LOCATION MODAL */}
      <Modal
        isOpen={showWrongLocModal}
        onClose={() => setShowWrongLocModal(false)}
        title={t("employee.modal_wrong_loc_title", "Report Wrong Location")}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
              {t("employee.actual_location_label", "Correct Location")} <span className="text-rose-500">*</span>
            </label>
            <select
              value={newLocationId}
              onChange={(e) => setNewLocationId(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">{t("employee.select_location", "Select location...")}</option>
              {locations.map((loc) => (
                <option key={loc.location_id} value={loc.location_id}>
                  {loc.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase mb-1">
              {t("employee.additional_details_label", "Note (Optional)")}
            </label>
            <input
              type="text"
              placeholder={t("employee.additional_details_placeholder", "e.g. Found in Block B instead of Block A")}
              value={wrongLocNote}
              onChange={(e) => setWrongLocNote(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowWrongLocModal(false)} disabled={reportingWrongLoc}>
              {t("common.cancel", "Cancel")}
            </Button>
            <Button
              variant="primary"
              disabled={!newLocationId || reportingWrongLoc}
              onClick={handleConfirmWrongLocation}
              className="cursor-pointer font-bold"
            >
              {reportingWrongLoc ? t("employee.submitting", "Submitting...") : t("employee.reroute_btn", "Submit New Location")}
            </Button>
          </div>
        </div>
      </Modal>

      {/* LEAVE MODAL */}
      <LeaveModal
        isOpen={showLeaveModal}
        onClose={() => setShowLeaveModal(false)}
        onLeaveChanged={loadData}
      />
    </div>
  );
}

