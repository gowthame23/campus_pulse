import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  Phone,
  CheckCircle,
  Clock,
  UserCheck,
  ChevronDown,
  ShieldAlert,
  Loader2,
} from "lucide-react";
import { emergencyService } from "../services/emergencyService.js";
import Modal from "./Modal.jsx";
import Button from "./Button.jsx";

export default function PinnedEmergenciesBanner({ onActionDone }) {
  const [emergencies, setEmergencies] = useState([]);
  const [loading, setLoading] = useState(false);
  const [actingComplaintId, setActingComplaintId] = useState(null);
  const [outcomeTarget, setOutcomeTarget] = useState(null);
  const [selectedOutcome, setSelectedOutcome] = useState("real");
  const [submittingOutcome, setSubmittingOutcome] = useState(false);

  useEffect(() => {
    loadEmergencies();
    const interval = setInterval(loadEmergencies, 15000); // 15s poll for emergency freshness
    return () => clearInterval(interval);
  }, []);

  const loadEmergencies = async () => {
    try {
      const res = await emergencyService.getPinnedEmergencies();
      setEmergencies(res.data || []);
    } catch (err) {
      console.error("Failed to load pinned emergencies:", err);
    }
  };

  const handleImOnIt = async (complaintId) => {
    setActingComplaintId(complaintId);
    try {
      await emergencyService.acknowledgeEmergency(complaintId);
      loadEmergencies();
      if (onActionDone) onActionDone();
    } catch (err) {
      console.error("Failed to acknowledge emergency:", err);
    } finally {
      setActingComplaintId(null);
    }
  };

  const handleMarkOutcomeSubmit = async (e) => {
    e.preventDefault();
    if (!outcomeTarget) return;
    setSubmittingOutcome(true);
    try {
      await emergencyService.markOutcome(outcomeTarget.complaint_id, selectedOutcome);
      setOutcomeTarget(null);
      loadEmergencies();
      if (onActionDone) onActionDone();
    } catch (err) {
      console.error("Failed to mark outcome:", err);
    } finally {
      setSubmittingOutcome(false);
    }
  };

  if (!emergencies || emergencies.length === 0) return null;

  return (
    <>
      <div className="space-y-3 mb-6">
        {emergencies.map((emg) => {
          const isAcked = Boolean(emg.acknowledged_at);
          const ackedName = emg.acknowledged_by_name || emg.acknowledged_by;
          const ackTime = emg.acknowledged_at ? emg.acknowledged_at.slice(11, 16) : "";

          return (
            <div
              key={emg.complaint_id}
              className="p-4 rounded-2xl bg-rose-500/10 dark:bg-rose-950/30 border-2 border-rose-500 dark:border-rose-700 shadow-md animate-in fade-in"
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 pb-3 border-b border-rose-200 dark:border-rose-900/60">
                <div className="flex items-start gap-3">
                  <div className="p-2.5 rounded-xl bg-rose-600 text-white shrink-0 shadow-md shadow-rose-600/30 animate-pulse">
                    <AlertTriangle className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-xs font-black tracking-wider uppercase px-2 py-0.5 rounded-md bg-rose-600 text-white">
                        CRITICAL EMERGENCY
                      </span>
                      <span className="text-xs font-bold text-rose-900 dark:text-rose-200">
                        #{emg.complaint_id}
                      </span>
                      {emg.emergency_category && (
                        <span className="text-xs font-bold text-rose-800 dark:text-rose-300">
                          • {emg.emergency_category}
                        </span>
                      )}
                    </div>
                    <h3 className="text-sm font-extrabold text-slate-900 dark:text-slate-100 mt-1">
                      {emg.title || emg.description}
                    </h3>
                    <p className="text-xs text-slate-600 dark:text-slate-300 font-medium">
                      Location: <strong className="text-slate-900 dark:text-slate-100">{emg.location_name || emg.location_id}</strong>
                      {emg.created_at && (
                        <span className="ml-2 text-slate-500">• Filed at {emg.created_at.slice(11, 16)}</span>
                      )}
                    </p>
                  </div>
                </div>

                {/* Response Action Buttons */}
                <div className="flex flex-wrap items-center gap-2 shrink-0">
                  {!isAcked ? (
                    <button
                      onClick={() => handleImOnIt(emg.complaint_id)}
                      disabled={actingComplaintId === emg.complaint_id}
                      className="px-4 py-2 bg-rose-600 hover:bg-rose-700 active:bg-rose-800 text-white font-extrabold text-xs rounded-xl shadow-md shadow-rose-600/30 flex items-center gap-1.5 transition-all active:scale-95"
                    >
                      {actingComplaintId === emg.complaint_id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <UserCheck className="h-4 w-4" />
                      )}
                      I'm on it
                    </button>
                  ) : (
                    <div className="px-3 py-1.5 rounded-xl bg-emerald-100 dark:bg-emerald-950/60 border border-emerald-300 dark:border-emerald-800 text-emerald-900 dark:text-emerald-200 text-xs font-bold flex items-center gap-1.5">
                      <CheckCircle className="h-3.5 w-3.5 text-emerald-600" />
                      <span>{ackedName} is on it at {ackTime}</span>
                    </div>
                  )}

                  <button
                    onClick={() => {
                      setOutcomeTarget(emg);
                      setSelectedOutcome("real");
                    }}
                    className="px-3 py-2 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 border border-slate-300 dark:border-slate-600 font-bold text-xs rounded-xl transition-all"
                  >
                    Mark Outcome
                  </button>

                  <Link
                    to={`/complaints/${emg.complaint_id}`}
                    className="px-3 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 font-bold text-xs rounded-xl transition-all"
                  >
                    View Details
                  </Link>
                </div>
              </div>

              {/* Team Members Calling List (Rule 2.4c) */}
              {emg.team_contacts && emg.team_contacts.length > 0 && (
                <div className="mt-3 pt-2.5">
                  <div className="text-[11px] font-bold uppercase tracking-wider text-rose-800 dark:text-rose-300 mb-2 flex items-center gap-1.5">
                    <Phone className="h-3 w-3" />
                    Team Direct Calling Line (Call Responders Directly):
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {emg.team_contacts.map((contact, cIdx) => (
                      <a
                        key={cIdx}
                        href={`tel:${contact.phone}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 hover:border-emerald-500 font-bold text-xs shadow-xs transition-colors"
                      >
                        <span className="text-emerald-600">📞</span>
                        <span>{contact.name}</span>
                        <span className="text-[10px] text-slate-500 font-normal">({contact.role})</span>
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Outcome Selector Modal (Rule 2.5b) */}
      {outcomeTarget && (
        <Modal
          isOpen={Boolean(outcomeTarget)}
          onClose={() => setOutcomeTarget(null)}
          title="Mark Emergency Outcome"
        >
          <form onSubmit={handleMarkOutcomeSubmit} className="space-y-4">
            <p className="text-xs text-slate-600 dark:text-slate-300">
              Before closing this emergency, record whether this was a real emergency, an accidental mistake, or misuse.
            </p>

            <div className="space-y-2">
              <label
                className={`flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${
                  selectedOutcome === "real"
                    ? "border-emerald-600 bg-emerald-50/50 dark:bg-emerald-950/20"
                    : "border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800"
                }`}
              >
                <input
                  type="radio"
                  name="outcome"
                  value="real"
                  checked={selectedOutcome === "real"}
                  onChange={() => setSelectedOutcome("real")}
                  className="mt-1"
                />
                <div>
                  <div className="text-xs font-bold text-slate-900 dark:text-slate-100">
                    Real emergency
                  </div>
                  <div className="text-[11px] text-slate-500">
                    A genuine safety, electrical, plumbing, or life issue occurred.
                  </div>
                </div>
              </label>

              <label
                className={`flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${
                  selectedOutcome === "mistake"
                    ? "border-amber-600 bg-amber-50/50 dark:bg-amber-950/20"
                    : "border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800"
                }`}
              >
                <input
                  type="radio"
                  name="outcome"
                  value="mistake"
                  checked={selectedOutcome === "mistake"}
                  onChange={() => setSelectedOutcome("mistake")}
                  className="mt-1"
                />
                <div>
                  <div className="text-xs font-bold text-slate-900 dark:text-slate-100">
                    Genuine mistake
                  </div>
                  <div className="text-[11px] text-slate-500">
                    User made an accidental mistake. No strikes are added to the student.
                  </div>
                </div>
              </label>

              <label
                className={`flex items-start gap-3 p-3 rounded-xl border-2 cursor-pointer transition-all ${
                  selectedOutcome === "misuse"
                    ? "border-rose-600 bg-rose-50/50 dark:bg-rose-950/20"
                    : "border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800"
                }`}
              >
                <input
                  type="radio"
                  name="outcome"
                  value="misuse"
                  checked={selectedOutcome === "misuse"}
                  onChange={() => setSelectedOutcome("misuse")}
                  className="mt-1"
                />
                <div>
                  <div className="text-xs font-bold text-rose-700 dark:text-rose-400">
                    Misuse
                  </div>
                  <div className="text-[11px] text-slate-500">
                    Intentional prank or frivolous report. Adds a strike to the student (3 strikes in 90 days pauses emergency button for 30 days), and downgrades priority to category default.
                  </div>
                </div>
              </label>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setOutcomeTarget(null)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                loading={submittingOutcome}
              >
                Save Outcome
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </>
  );
}
