import { useState, useEffect } from "react";
import { User, AlertCircle, Clock, Check, RefreshCw } from "lucide-react";
import Modal from "./Modal.jsx";
import Button from "./Button.jsx";
import { teamService } from "../services/teamService.js";
import { complaintService } from "../services/complaintService.js";

export default function AssignModal({ isOpen, onClose, complaint, onAssigned }) {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedMemberId, setSelectedMemberId] = useState("");
  const [reassignReason, setReassignReason] = useState("");
  const [assigning, setAssigning] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const isReassign = Boolean(complaint?.assigned_to);

  useEffect(() => {
    if (!isOpen || !complaint) return;
    setSelectedMemberId("");
    setReassignReason("");
    setErrorMessage("");
    loadMembers();
  }, [isOpen, complaint]);

  const loadMembers = async () => {
    if (!complaint) return;
    setLoading(true);
    setErrorMessage("");
    try {
      let teamId = complaint.team_id;
      if (!teamId) {
        // Find team by location & department
        const allTeams = await teamService.list({ active_only: true });
        const teamsData = allTeams.data || allTeams;
        const matched = teamsData.find(
          (t) =>
            t.department_id === complaint.department_id &&
            t.location_ids?.includes(complaint.location_id)
        );
        if (matched) {
          teamId = matched.team_id;
        }
      }

      if (teamId) {
        const res = await teamService.getMembers(teamId);
        const data = res.data || res;
        // Rule K3: Hide members on leave today
        const available = (data || []).filter((m) => !m.on_leave);
        setMembers(available);
      } else {
        setMembers([]);
      }
    } catch (err) {
      console.error("Failed to load team members:", err);
      setErrorMessage("Could not load team members. Please try again.");
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
        // Race condition: already assigned
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
      title={isReassign ? "Reassign Complaint" : "Assign Complaint"}
    >
      <div className="space-y-4">
        {complaint && (
          <div className="rounded-lg bg-slate-50 dark:bg-slate-800/60 p-3 text-sm">
            <div className="font-semibold text-slate-800 dark:text-slate-100">
              {complaint.title || complaint.category}
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Priority: <span className="font-medium">{complaint.priority}</span> | Status: {complaint.status}
              {complaint.assigned_to && (
                <span> | Currently: <span className="font-medium text-slate-700 dark:text-slate-300">{complaint.assigned_to}</span></span>
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
              Reassignment Reason <span className="text-rose-500">*</span>
            </label>
            <textarea
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 p-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 outline-none"
              rows={2}
              placeholder="Explain why this job is being reassigned..."
              value={reassignReason}
              onChange={(e) => setReassignReason(e.target.value)}
            />
          </div>
        )}

        <div>
          <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
            Select Team Member
          </div>

          {loading ? (
            <div className="flex items-center justify-center p-8">
              <RefreshCw className="h-5 w-5 animate-spin text-slate-400" />
              <span className="ml-2 text-sm text-slate-500">Loading members...</span>
            </div>
          ) : members.length === 0 ? (
            <div className="text-center py-6 text-sm text-slate-500 dark:text-slate-400">
              No active members available (or all members on leave).
            </div>
          ) : (
            <div className="max-h-64 overflow-y-auto space-y-2 pr-1">
              {members.map((member) => {
                const isSelected = selectedMemberId === member.user_id;
                return (
                  <button
                    key={member.user_id}
                    type="button"
                    onClick={() => {
                      setSelectedMemberId(member.user_id);
                      if (!isReassign) {
                        handleAssign(member.user_id);
                      }
                    }}
                    className={`w-full flex items-center justify-between p-3 rounded-lg border text-left transition-all ${
                      isSelected
                        ? "border-blue-500 bg-blue-50 dark:bg-blue-950/40 text-blue-900 dark:text-blue-200"
                        : "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200"
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="h-8 w-8 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center shrink-0">
                        <User className="h-4 w-4 text-slate-500" />
                      </div>
                      <div className="truncate">
                        <div className="text-sm font-semibold truncate">
                          {member.name}
                        </div>
                        <div className="text-xs text-slate-500 dark:text-slate-400">
                          {member.role === "coordinator" ? "Coordinator / Worker" : member.role}
                        </div>
                      </div>
                    </div>
                    <div className="text-right shrink-0 ml-3">
                      <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                        {member.open_jobs} open job{member.open_jobs === 1 ? "" : "s"}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {isReassign && (
          <div className="flex justify-end gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
            <Button variant="secondary" onClick={onClose} disabled={assigning}>
              Cancel
            </Button>
            <Button
              variant="primary"
              disabled={!selectedMemberId || !reassignReason.trim() || assigning}
              onClick={() => handleAssign()}
            >
              {assigning ? "Reassigning..." : "Confirm Reassignment"}
            </Button>
          </div>
        )}
      </div>
    </Modal>
  );
}

