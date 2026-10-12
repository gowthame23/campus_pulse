import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ShieldAlert,
  Shield,
  MessageSquare,
  Lock,
  Unlock,
  AlertOctagon,
  CheckCircle2,
  Send,
  ArrowLeft,
  RefreshCw,
} from "lucide-react";
import Card from "../../components/Card.jsx";
import Button from "../../components/Button.jsx";
import PageHeader from "../../components/PageHeader.jsx";
import Loader from "../../components/Loader.jsx";
import Modal from "../../components/Modal.jsx";
import Toast from "../../components/Toast.jsx";
import { safetyReportService } from "../../services/safetyReportService.js";
import { getApiError } from "../../api/axios.js";
import { formatDate } from "../../utils/dateFormatter.js";

const OUTCOMES = [
  { value: "action_taken", label: "Action Taken", desc: "Security or administrative action was initiated" },
  { value: "could_not_confirm", label: "Could Not Confirm", desc: "Unable to verify facts (no penalty to student)" },
  { value: "not_a_safety_issue", label: "Not a Safety Issue", desc: "Redirected to standard facility complaint (no penalty)" },
  { value: "false_misuse", label: "Deliberate False Misuse", desc: "Intentional harassment/misuse (penalises student, unseals identity with mandatory written justification)" },
];

export default function SafetyReportsAdminPage() {
  const [reports, setReports] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState(null);

  // Chat reply state
  const [replyBody, setReplyBody] = useState("");
  const [sendingReply, setSendingReply] = useState(false);

  // Decision modal state
  const [showDecisionModal, setShowDecisionModal] = useState(false);
  const [chosenOutcome, setChosenOutcome] = useState("action_taken");
  const [decisionNotes, setDecisionNotes] = useState("");
  const [submittingDecision, setSubmittingDecision] = useState(false);

  // Reveal modal state
  const [showRevealModal, setShowRevealModal] = useState(false);
  const [revealReason, setRevealReason] = useState("");
  const [submittingReveal, setSubmittingReveal] = useState(false);

  const loadReports = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await safetyReportService.list();
      setReports(res.data || []);
      if (selectedCase) {
        const updated = await safetyReportService.getByCaseCode(selectedCase.case_code);
        setSelectedCase(updated.data);
      }
    } catch (err) {
      setError(getApiError(err, "Failed to load safety reports."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const handleSelectCase = async (caseCode) => {
    try {
      const res = await safetyReportService.getByCaseCode(caseCode);
      setSelectedCase(res.data);
    } catch (err) {
      setError(getApiError(err, "Could not open case."));
    }
  };

  const handleSendAdminReply = async (e) => {
    e.preventDefault();
    if (!replyBody.trim() || !selectedCase) return;
    setSendingReply(true);

    try {
      await safetyReportService.sendMessage(selectedCase.case_code, replyBody.trim());
      setReplyBody("");
      const res = await safetyReportService.getByCaseCode(selectedCase.case_code);
      setSelectedCase(res.data);
    } catch (err) {
      setError(getApiError(err, "Failed to send message."));
    } finally {
      setSendingReply(false);
    }
  };

  const handleDecisionSubmit = async (e) => {
    e.preventDefault();
    if (!selectedCase) return;
    setSubmittingDecision(true);

    try {
      await safetyReportService.decide(selectedCase.report_id, chosenOutcome, decisionNotes.trim());
      setShowDecisionModal(false);
      setDecisionNotes("");
      setToast({ tone: "success", message: "Case decision recorded successfully." });
      loadReports();
      const updated = await safetyReportService.getByCaseCode(selectedCase.case_code);
      setSelectedCase(updated.data);
    } catch (err) {
      setError(getApiError(err, "Failed to record case decision."));
    } finally {
      setSubmittingDecision(false);
    }
  };

  const handleRevealSubmit = async (e) => {
    e.preventDefault();
    if (!selectedCase || !revealReason.trim()) {
      setError("A written justification is mandatory to unseal confidential identity.");
      return;
    }
    setSubmittingReveal(true);

    try {
      const res = await safetyReportService.reveal(selectedCase.report_id, revealReason.trim());
      setShowRevealModal(false);
      setRevealReason("");
      setToast({ tone: "warning", message: "Reporter identity unsealed and audited." });
      const updated = await safetyReportService.getByCaseCode(selectedCase.case_code);
      setSelectedCase(updated.data);
    } catch (err) {
      setError(getApiError(err, "Failed to reveal reporter identity."));
    } finally {
      setSubmittingReveal(false);
    }
  };

  return (
    <div className="space-y-6">
      {toast && (
        <Toast tone={toast.tone} message={toast.message} onClose={() => setToast(null)} />
      )}

      <div className="flex items-center justify-between gap-4">
        <div>
          <Link
            to="/admin"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors mb-2"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to admin console
          </Link>
          <PageHeader
            title="Confidential Safety Reports (Admin Only)"
            description="Sealed safety cases. Anonymous identity is protected by default and can only be unsealed upon substantiated deliberate misuse."
          />
        </div>

        <button
          onClick={loadReports}
          className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all cursor-pointer shadow-xs"
        >
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-50 text-rose-800 text-xs font-semibold">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Reports List */}
        <div className="lg:col-span-1 space-y-3">
          <div className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            All Incident Reports ({reports.length})
          </div>

          {loading ? (
            <Loader label="Loading safety reports..." variant="skeleton" />
          ) : reports.length === 0 ? (
            <Card className="p-6 text-center text-xs text-slate-500">
              No safety reports submitted.
            </Card>
          ) : (
            <div className="space-y-2">
              {reports.map((rep) => {
                const isSelected = selectedCase?.report_id === rep.report_id;
                return (
                  <Card
                    key={rep.report_id}
                    onClick={() => handleSelectCase(rep.case_code)}
                    className={`p-3.5 cursor-pointer transition-all border ${
                      isSelected
                        ? "border-primary bg-primary/5 dark:bg-primary/10 shadow-xs"
                        : "hover:border-slate-300 dark:hover:border-slate-700"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <span className="font-mono text-xs font-black text-primary">
                        {rep.case_code}
                      </span>
                      <span
                        className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase ${
                          rep.status === "closed"
                            ? "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400"
                            : "bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300"
                        }`}
                      >
                        {rep.status}
                      </span>
                    </div>
                    <div className="text-xs font-bold text-slate-800 dark:text-slate-200 truncate">
                      {rep.category}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-1">
                      {formatDate(rep.created_at)}
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>

        {/* Selected Case Workspace */}
        <div className="lg:col-span-2">
          {selectedCase ? (
            <Card className="p-6 space-y-6">
              {/* Header */}
              <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-lg font-mono font-black text-primary">
                      {selectedCase.case_code}
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                      {selectedCase.status}
                    </span>
                  </div>
                  <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 mt-1">
                    {selectedCase.category}
                  </h2>
                  <div className="text-xs text-slate-400 mt-0.5">
                    Submitted: {formatDate(selectedCase.created_at)}
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setShowDecisionModal(true)}
                    className="text-xs font-bold"
                  >
                    Set Decision / Outcome
                  </Button>
                </div>
              </div>

              {/* Identity Protection Status */}
              <div
                className={`p-4 rounded-xl border flex items-center justify-between gap-4 ${
                  selectedCase.is_revealed
                    ? "bg-rose-50 dark:bg-rose-950/30 border-rose-300 dark:border-rose-800"
                    : "bg-slate-50 dark:bg-slate-900/40 border-slate-200 dark:border-slate-800"
                }`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`p-2 rounded-xl shrink-0 ${
                      selectedCase.is_revealed
                        ? "bg-rose-600 text-white"
                        : "bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300"
                    }`}
                  >
                    {selectedCase.is_revealed ? (
                      <Unlock className="h-5 w-5" />
                    ) : (
                      <Lock className="h-5 w-5" />
                    )}
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-900 dark:text-slate-100">
                      {selectedCase.is_revealed
                        ? "IDENTITY UNSEALED (AUDITED)"
                        : "REPORTER IDENTITY CONFIDENTIAL & SEALED"}
                    </div>
                    {selectedCase.is_revealed && selectedCase.revealed_reporter ? (
                      <div className="text-xs text-rose-800 dark:text-rose-300 mt-1">
                        Student: <strong>{selectedCase.revealed_reporter.name}</strong> (
                        {selectedCase.revealed_reporter.email})
                        <br />
                        Reason: <em>"{selectedCase.revealed_reporter.reveal_reason}"</em>
                      </div>
                    ) : (
                      <div className="text-[11px] text-slate-500">
                        Protected by safety policy. Sealed in isolated schema table.
                      </div>
                    )}
                  </div>
                </div>

                {!selectedCase.is_revealed && (
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => setShowRevealModal(true)}
                    className="text-xs font-bold shrink-0"
                  >
                    Unseal for Misuse
                  </Button>
                )}
              </div>

              {/* Outcome Badge if decided */}
              {selectedCase.outcome && (
                <div className="p-3.5 rounded-xl bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-300 dark:border-emerald-800 text-xs">
                  <div className="font-bold text-emerald-800 dark:text-emerald-300 uppercase">
                    Admin Outcome: {selectedCase.outcome.replace(/_/g, " ")}
                  </div>
                  {selectedCase.outcome_notes && (
                    <div className="text-emerald-700 dark:text-emerald-400 mt-1">
                      Notes: {selectedCase.outcome_notes}
                    </div>
                  )}
                </div>
              )}

              {/* Anonymous Two-Way Chat */}
              <div className="space-y-3">
                <div className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <MessageSquare className="h-4 w-4" />
                  Confidential Communication Thread
                </div>

                <div className="space-y-2.5 max-h-72 overflow-y-auto p-2 bg-slate-50 dark:bg-slate-900/60 rounded-xl border border-slate-200 dark:border-slate-800">
                  {(selectedCase.messages || []).map((msg, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-xl max-w-[85%] text-xs space-y-1 ${
                        msg.sender_type === "admin"
                          ? "bg-primary text-white ml-auto"
                          : "bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 mr-auto"
                      }`}
                    >
                      <div className="flex items-center justify-between gap-4 text-[10px] opacity-75 font-bold">
                        <span>{msg.sender_type === "admin" ? "🛡️ You (Administrator)" : "🔒 Student (Sealed Identity)"}</span>
                        <span>{formatDate(msg.created_at)}</span>
                      </div>
                      <p className="whitespace-pre-wrap">{msg.body}</p>
                    </div>
                  ))}
                </div>

                <form onSubmit={handleSendAdminReply} className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Send confidential response to reporter..."
                    value={replyBody}
                    onChange={(e) => setReplyBody(e.target.value)}
                    className="h-10 flex-1 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs text-slate-900 dark:text-slate-100 outline-none focus:border-primary"
                  />
                  <Button
                    type="submit"
                    variant="primary"
                    disabled={sendingReply || !replyBody.trim()}
                    className="text-xs font-bold px-4"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </form>
              </div>
            </Card>
          ) : (
            <Card className="p-12 text-center text-slate-400 text-xs">
              Select a safety report from the left panel to inspect details and respond.
            </Card>
          )}
        </div>
      </div>

      {/* Decision Modal */}
      {showDecisionModal && (
        <Modal
          isOpen={true}
          onClose={() => setShowDecisionModal(false)}
          title="Record Safety Report Decision"
        >
          <form onSubmit={handleDecisionSubmit} className="space-y-4 text-xs">
            <div>
              <label className="block font-bold text-slate-700 mb-2">Outcome Decision</label>
              <div className="space-y-2">
                {OUTCOMES.map((o) => (
                  <label
                    key={o.value}
                    className={`flex items-start gap-3 p-3 rounded-xl border cursor-pointer ${
                      chosenOutcome === o.value
                        ? "border-primary bg-primary/5 font-semibold text-slate-900"
                        : "border-slate-200 text-slate-600 hover:bg-slate-50"
                    }`}
                  >
                    <input
                      type="radio"
                      name="outcome"
                      value={o.value}
                      checked={chosenOutcome === o.value}
                      onChange={() => setChosenOutcome(o.value)}
                      className="mt-0.5 text-primary"
                    />
                    <div>
                      <div className="font-bold">{o.label}</div>
                      <div className="text-[11px] text-slate-500 font-normal">{o.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">Decision Notes / Actions</label>
              <textarea
                value={decisionNotes}
                onChange={(e) => setDecisionNotes(e.target.value)}
                rows={3}
                placeholder="Details of action taken or reasoning..."
                className="w-full rounded-xl border border-slate-300 p-2 text-xs"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowDecisionModal(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" disabled={submittingDecision}>
                {submittingDecision ? "Saving..." : "Save Decision"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Reveal Identity Modal */}
      {showRevealModal && (
        <Modal
          isOpen={true}
          onClose={() => setShowRevealModal(false)}
          title="⚠️ Unseal Reporter Identity (Mandatory Audit)"
        >
          <form onSubmit={handleRevealSubmit} className="space-y-4 text-xs">
            <div className="p-3 rounded-xl bg-rose-50 text-rose-800 border border-rose-200">
              <span className="font-bold block mb-1">Deliberate False Misuse Warning:</span>
              Reporter identities may ONLY be unsealed if the complaint was determined to be a
              deliberate false report or harassment. Every unseal event is permanently recorded in the
              administrator audit trail.
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">
                Mandatory Written Justification
              </label>
              <textarea
                value={revealReason}
                onChange={(e) => setRevealReason(e.target.value)}
                rows={4}
                placeholder="State the factual basis why this report constitutes deliberate false misuse..."
                className="w-full rounded-xl border border-rose-300 p-2.5 text-xs text-slate-900"
                required
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="outline" onClick={() => setShowRevealModal(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="danger" disabled={submittingReveal || !revealReason.trim()}>
                {submittingReveal ? "Unsealing..." : "Confirm & Unseal Identity"}
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

