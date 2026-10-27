import { useState, useEffect } from "react";
import { User, AlertCircle, Clock, Check, RefreshCw, Briefcase, Calendar, ChevronDown, ChevronUp } from "lucide-react";
import Modal from "./Modal.jsx";
import Button from "./Button.jsx";
import { complaintService } from "../services/complaintService.js";
import { useLanguage } from "../context/LanguageContext.jsx";
import { getStatusLabel, getPriorityLabel } from "../utils/statusColor.js";

export default function AssignModal({ isOpen, onClose, complaint, onAssigned }) {
  const { t } = useLanguage();
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedMemberId, setSelectedMemberId] = useState("");
  const [reassignReason, setReassignReason] = useState("");
  const [assigning, setAssigning] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [expandedMemberId, setExpandedMemberId] = useState(null);

  const isReassign = Boolean(complaint?.assigned_to);

  useEffect(() => {
    if (!isOpen || !complaint) return;
    setSelectedMemberId("");
    setReassignReason("");
    setErrorMessage("");
    setExpandedMemberId(null);
    loadMembers();
  }, [isOpen, complaint]);

  const loadMembers = async () => {
    if (!complaint) return;
    setLoading(true);
    setErrorMessage("");
    try {
      const res = await complaintService.getEligibleAssignees(complaint.complaint_id);
      const eligibleList = res.data || res || [];
      setMembers(eligibleList);
    } catch (err) {
      console.error("Failed to load eligible employees:", err);
      setErrorMessage("Could not load eligible employees. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleAssign = async (targetId) => {
    const memberId = targetId || selectedMemberId;
    if (!memberId) return;

    if (isReassign && !reassignReason.trim()) {
      setErrorMessage("A reason is mandatory for reassignment.");
      return;
    }

    setAssigning(true);
    setErrorMessage("");
    try {
      const res = await complaintService.assignWork(
        complaint.complaint_id,
        memberId,
        reassignReason.trim()
      );
      if (onAssigned) {
        onAssigned(res.data || res);
      }
      onClose();
    } catch (err) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      if (status === 409) {
        alert(detail || "Already assigned by another coordinator.");
        if (onAssigned) onAssigned(null);
        onClose();
      } else if (status === 400) {
        setErrorMessage(detail || "Assignment failed.");
      } else {
        setErrorMessage(detail || "An error occurred during assignment.");
      }
    } finally {
      setAssigning(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={isReassign ? t("coordinator.modal_reassign_title", "Reassign Complaint") : t("coordinator.modal_assign_title", "Assign Complaint")}
    >
      <div className="space-y-4">
        {complaint && (
          <div className="rounded-lg bg-slate-50 dark:bg-slate-800/60 p-3 text-sm">
            <div className="font-semibold text-slate-800 dark:text-slate-100">
              {complaint.title || complaint.category}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-1 flex flex-wrap gap-2">
              <span>{t("priority", "Priority")}: <span className="font-medium">{getPriorityLabel(complaint.priority, t)}</span></span>
              <span>•</span>
              <span>{t("status", "Status")}: {getStatusLabel(complaint.status, t)}</span>
              {complaint.assigned_to && (
                <>
                  <span>•</span>
                  <span>{t("coordinator.worker", "Current Worker:")} <span className="font-medium text-slate-700 dark:text-slate-300">{complaint.assigned_to}</span></span>
                </>
              )}
            </div>
          </div>
        )}

        {errorMessage && (
          <div className="flex items-center gap-2 p-3 text-sm bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 rounded-lg border border-rose-200 dark:border-rose-800">
            <AlertCircle className="h-4 w-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        {isReassign && (
          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1">
              {t("coordinator.reassign_reason_label", "Reassignment Reason")} <span className="text-rose-500">*</span>
            </label>
            <textarea
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 outline-none"
              rows={2}
              placeholder={t("coordinator.reassign_reason_placeholder", "Explain why this job is being reassigned...")}
              value={reassignReason}
              onChange={(e) => setReassignReason(e.target.value)}
            />
          </div>
        )}

        <div>
          <div className="flex items-center justify-between text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
            <span>{t("coordinator.available_members", "Eligible Coordinators & Workload")}</span>
            <span className="text-[11px] font-normal text-slate-500 dark:text-slate-400">
              Department & Location Filtered
            </span>
          </div>

          {loading ? (
            <div className="flex items-center justify-center p-8">
              <RefreshCw className="h-5 w-5 animate-spin text-slate-400" />
              <span className="ml-2 text-sm text-slate-500">{t("common.loading", "Loading eligible workforce...")}</span>
            </div>
          ) : members.length === 0 ? (
            <div className="text-center py-6 text-sm text-slate-500 dark:text-slate-400 bg-slate-50 dark:bg-slate-800/40 rounded-lg border border-dashed border-slate-200 dark:border-slate-700">
              {t("coordinator.no_available_members", "No active employees assigned to this department and location.")}
            </div>
          ) : (
            <div className="max-h-72 overflow-y-auto space-y-2 pr-1">
              {members.map((member) => {
                const isSelected = selectedMemberId === member.user_id;
                const isOnLeave = Boolean(member.on_leave);
                const isExpanded = expandedMemberId === member.user_id;

                return (
                  <div
                    key={member.user_id}
                    className={`rounded-lg border transition-all ${
                      isOnLeave
                        ? "border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 opacity-70"
                        : isSelected
                        ? "border-blue-500 bg-blue-50/60 dark:bg-blue-950/40"
                        : "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-slate-900"
                    }`}
                  >
                    <div className="p-3 flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3 min-w-0">
                        <div className="h-8 w-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center shrink-0">
                          <User className="h-4 w-4 text-slate-500" />
                        </div>
                        <div className="truncate">
                          <div className="text-sm font-semibold truncate text-slate-900 dark:text-slate-100">
                            {member.name}
                          </div>
                          <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-2">
                            <span>{member.role === "coordinator" ? "Coordinator / Technician" : "Technician"}</span>
                            {member.phone && <span>• {member.phone}</span>}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        {isOnLeave ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold bg-rose-100 text-rose-800 dark:bg-rose-950/60 dark:text-rose-300">
                            <Calendar className="h-3 w-3" />
                            On Leave {member.leave_until ? `until ${member.leave_until}` : ""}
                          </span>
                        ) : member.active_jobs_count === 0 ? (
                          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                            <Check className="h-3 w-3" />
                            Available (0 active)
                          </span>
                        ) : (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setExpandedMemberId(isExpanded ? null : member.user_id);
                            }}
                            className="inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-semibold bg-amber-100 hover:bg-amber-200 text-amber-900 dark:bg-amber-950/60 dark:hover:bg-amber-900/80 dark:text-amber-200 transition-colors cursor-pointer"
                            title="Click to view cross-department workload"
                          >
                            <Briefcase className="h-3 w-3" />
                            <span>{member.active_jobs_count} active job{member.active_jobs_count === 1 ? "" : "s"}</span>
                            {isExpanded ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                          </button>
                        )}

                        <Button
                          variant={isSelected ? "primary" : "secondary"}
                          size="sm"
                          disabled={isOnLeave || assigning}
                          onClick={() => {
                            setSelectedMemberId(member.user_id);
                            if (!isReassign) {
                              handleAssign(member.user_id);
                            }
                          }}
                          className="!py-1 !px-2.5 !text-xs font-semibold"
                        >
                          {isSelected ? (isReassign ? "Selected" : "Assigning...") : (isReassign ? "Select" : "Assign")}
                        </Button>
                      </div>
                    </div>

                    {/* Cross-Department Active Jobs Breakdown */}
                    {isExpanded && member.active_jobs?.length > 0 && (
                      <div className="px-3 pb-3 pt-1 border-t border-slate-100 dark:border-slate-800/80 bg-slate-50/70 dark:bg-slate-800/40 text-xs">
                        <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center justify-between">
                          <span>Cross-Department Active Jobs</span>
                          <span className="font-normal text-slate-400">Confidential Work Summary</span>
                        </div>
                        <div className="space-y-1.5">
                          {member.active_jobs.map((job) => (
                            <div
                              key={job.complaint_id}
                              className="flex items-center justify-between p-1.5 rounded bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 text-[11px]"
                            >
                              <div className="truncate max-w-[200px] font-medium">
                                <span className="font-mono text-slate-500 mr-1.5">#{job.complaint_id.slice(-6)}</span>
                                {job.title}
                              </div>
                              <div className="flex items-center gap-2 text-slate-500 shrink-0">
                                <span className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-[10px] font-semibold">
                                  {job.department_name}
                                </span>
                                <span className="text-[10px]">{job.location_name}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {isReassign && (
          <div className="flex justify-end gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
            <Button variant="secondary" onClick={onClose} disabled={assigning}>
              {t("common.cancel", "Cancel")}
            </Button>
            <Button
              variant="primary"
              disabled={!selectedMemberId || !reassignReason.trim() || assigning}
              onClick={() => handleAssign()}
              className="cursor-pointer font-bold"
            >
              {assigning ? t("submitting", "Reassigning...") : t("coordinator.btn_reassign", "Confirm Reassignment")}
            </Button>
          </div>
        )}
      </div>
    </Modal>
  );
}


