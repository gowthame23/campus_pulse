import { useState, useEffect } from "react";
import { Calendar, AlertCircle, Trash2, CheckCircle2 } from "lucide-react";
import Modal from "./Modal.jsx";
import Button from "./Button.jsx";
import { leaveService } from "../services/leaveService.js";

export default function LeaveModal({ isOpen, onClose, onLeaveChanged }) {
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [reason, setReason] = useState("");
  const [myLeaves, setMyLeaves] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const todayStr = new Date().toISOString().slice(0, 10);

  useEffect(() => {
    if (!isOpen) return;
    setFromDate(todayStr);
    setToDate(todayStr);
    setReason("");
    setError("");
    setSuccess("");
    loadMyLeaves();
  }, [isOpen]);

  const loadMyLeaves = async () => {
    setLoading(true);
    try {
      const res = await leaveService.getMyLeaves();
      setMyLeaves(res.data || res || []);
    } catch (err) {
      console.error("Failed to load leaves:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateLeave = async (e) => {
    e.preventDefault();
    if (!fromDate || !toDate) {
      setError("Please select both from and to dates.");
      return;
    }
    if (fromDate > toDate) {
      setError("From date cannot be after to date.");
      return;
    }

    setSaving(true);
    setError("");
    setSuccess("");
    try {
      await leaveService.setLeave({
        from_date: fromDate,
        to_date: toDate,
        reason: reason.trim() || undefined,
      });
      setSuccess("Leave registered successfully.");
      setReason("");
      await loadMyLeaves();
      if (onLeaveChanged) onLeaveChanged();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to set leave.");
    } finally {
      setSaving(false);
    }
  };

  const handleCancelLeave = async (leaveId) => {
    if (!confirm("Are you sure you want to cancel this leave?")) return;
    setError("");
    try {
      await leaveService.cancelLeave(leaveId);
      await loadMyLeaves();
      if (onLeaveChanged) onLeaveChanged();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to cancel leave.");
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Leave Management">
      <div className="space-y-6">
        {error && (
          <div className="p-3 text-sm bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 rounded-lg border border-rose-200 dark:border-rose-800">
            {error}
          </div>
        )}
        {success && (
          <div className="p-3 text-sm bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 rounded-lg border border-emerald-200 dark:border-emerald-800">
            {success}
          </div>
        )}

        {/* Create Leave Form */}
        <form onSubmit={handleCreateLeave} className="space-y-3 bg-slate-50 dark:bg-slate-800/40 p-4 rounded-xl border border-slate-200 dark:border-slate-800">
          <div className="text-sm font-semibold text-slate-800 dark:text-slate-100 flex items-center gap-2">
            <Calendar className="h-4 w-4 text-blue-500" />
            Mark Leave Period
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                From Date
              </label>
              <input
                type="date"
                min={todayStr}
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 outline-none"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
                To Date
              </label>
              <input
                type="date"
                min={fromDate || todayStr}
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 outline-none"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-600 dark:text-slate-400 mb-1">
              Reason (Optional)
            </label>
            <input
              type="text"
              placeholder="e.g. Sick leave, personal travel..."
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full text-sm rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 py-2 text-slate-900 dark:text-slate-100 focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>

          <Button type="submit" variant="primary" className="w-full" disabled={saving}>
            {saving ? "Saving..." : "Set Leave"}
          </Button>
        </form>

        {/* Existing Leaves List */}
        <div>
          <div className="text-xs font-semibold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-2">
            Your Scheduled / Active Leaves
          </div>

          {loading ? (
            <div className="text-center py-4 text-xs text-slate-500">Loading leaves...</div>
          ) : myLeaves.length === 0 ? (
            <div className="text-center py-4 text-xs text-slate-500 dark:text-slate-400">
              No leave records found.
            </div>
          ) : (
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {myLeaves.map((l) => {
                const isActive = l.from_date <= todayStr && todayStr <= l.to_date;
                return (
                  <div
                    key={l.leave_id}
                    className="flex items-center justify-between p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900"
                  >
                    <div>
                      <div className="text-sm font-medium text-slate-800 dark:text-slate-200 flex items-center gap-2">
                        <span>{l.from_date} to {l.to_date}</span>
                        {isActive && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300">
                            Active Today
                          </span>
                        )}
                      </div>
                      {l.reason && (
                        <div className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                          {l.reason}
                        </div>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => handleCancelLeave(l.leave_id)}
                      className="p-1.5 text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded transition"
                      title="Cancel leave"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
}

