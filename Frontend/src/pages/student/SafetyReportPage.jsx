import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  Shield,
  ShieldAlert,
  PhoneCall,
  Send,
  MessageSquare,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Search,
} from "lucide-react";
import Card from "../../components/Card.jsx";
import Button from "../../components/Button.jsx";
import PageHeader from "../../components/PageHeader.jsx";
import Loader from "../../components/Loader.jsx";
import Toast from "../../components/Toast.jsx";
import { safetyReportService } from "../../services/safetyReportService.js";
import { getApiError } from "../../api/axios.js";
import { formatDate } from "../../utils/dateFormatter.js";

const CATEGORIES = [
  "Harassment or Abuse",
  "Physical Hazard / Danger",
  "Theft or Property Damage",
  "Threat or Intimidation",
  "Substance Misuse",
  "Other Urgent Safety Issue",
];

export default function SafetyReportPage() {
  const [statusConfig, setStatusConfig] = useState({ enabled: false, emergency_numbers: "112" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toast, setToast] = useState(null);

  // Mode: "new" or "lookup"
  const [mode, setMode] = useState("new");

  // Form State
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [createdCase, setCreatedCase] = useState(null);

  // Case Lookup & Chat State
  const [lookupCode, setLookupCode] = useState("");
  const [activeCase, setActiveCase] = useState(null);
  const [lookingUp, setLookingUp] = useState(false);
  const [replyText, setReplyText] = useState("");
  const [sendingReply, setSendingReply] = useState(false);

  useEffect(() => {
    async function checkStatus() {
      try {
        const res = await safetyReportService.getStatus();
        setStatusConfig(res.data || { enabled: false, emergency_numbers: "112" });
      } catch (err) {
        setStatusConfig({ enabled: false, emergency_numbers: "112" });
      } finally {
        setLoading(false);
      }
    }
    checkStatus();
  }, []);

  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    if (!description.trim()) {
      setError("Please describe the safety concern.");
      return;
    }
    setSubmitting(true);
    setError("");

    try {
      const res = await safetyReportService.create({
        category,
        description: description.trim(),
      });
      setCreatedCase(res.data);
      setDescription("");
      setToast({
        tone: "success",
        message: `Safety report submitted securely. Case code: ${res.data.case_code}`,
      });
    } catch (err) {
      setError(getApiError(err, "Failed to submit safety report."));
    } finally {
      setSubmitting(false);
    }
  };

  const handleLookup = async (codeToLookup) => {
    const code = (codeToLookup || lookupCode).trim().toUpperCase();
    if (!code) return;
    setLookingUp(true);
    setError("");

    try {
      const res = await safetyReportService.getByCaseCode(code);
      setActiveCase(res.data);
      setLookupCode(code);
    } catch (err) {
      setError(getApiError(err, "Could not find case. Please check your case code."));
      setActiveCase(null);
    } finally {
      setLookingUp(false);
    }
  };

  const handleSendReply = async (e) => {
    e.preventDefault();
    if (!replyText.trim() || !activeCase) return;
    setSendingReply(true);

    try {
      await safetyReportService.sendMessage(activeCase.case_code, replyText.trim());
      setReplyText("");
      // Refresh case
      const res = await safetyReportService.getByCaseCode(activeCase.case_code);
      setActiveCase(res.data);
    } catch (err) {
      setError(getApiError(err, "Failed to send message."));
    } finally {
      setSendingReply(false);
    }
  };

  if (loading) {
    return <Loader label="Checking safety system status..." variant="skeleton" />;
  }

  if (!statusConfig.enabled) {
    return (
      <div className="max-w-xl mx-auto py-12 text-center space-y-4">
        <div className="p-4 bg-slate-100 dark:bg-slate-800 rounded-full inline-block text-slate-500">
          <Shield className="h-10 w-10" />
        </div>
        <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100">
          Safety Reports Disabled
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400 max-w-md mx-auto">
          The anonymous safety reporting system is currently disabled by institution administration.
          If this is an immediate emergency, please call <strong>{statusConfig.emergency_numbers || "112"}</strong>.
        </p>
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 px-4 py-2 bg-primary text-white rounded-xl text-xs font-bold"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Return to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {toast && (
        <Toast tone={toast.tone} message={toast.message} onClose={() => setToast(null)} />
      )}

      <div>
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors mb-2"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to dashboard
        </Link>
        <PageHeader
          title="Confidential Safety Reporting"
          description="Direct and sealed reporting channel exclusively to campus executive admins."
        />
      </div>

      {/* Emergency Assistance Banner */}
      <div className="p-4 rounded-2xl bg-rose-500 text-white shadow-md flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-white/20 rounded-xl shrink-0">
            <PhoneCall className="h-6 w-6 animate-pulse" />
          </div>
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-rose-100">
              Immediate Danger or Medical Emergency?
            </div>
            <div className="text-sm font-black">
              Call Campus Emergency Services: {statusConfig.emergency_numbers || "112"}
            </div>
          </div>
        </div>
        <a
          href={`tel:${statusConfig.emergency_numbers || "112"}`}
          className="px-4 py-2 bg-white text-rose-600 hover:bg-rose-50 font-black rounded-xl text-xs shadow-xs shrink-0"
        >
          Call Now
        </a>
      </div>

      {/* Mode Switcher */}
      <div className="flex rounded-xl bg-slate-100 dark:bg-slate-800/80 p-1 text-xs font-bold">
        <button
          type="button"
          onClick={() => {
            setMode("new");
            setCreatedCase(null);
          }}
          className={`flex-1 py-2 rounded-lg transition-all ${
            mode === "new"
              ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-xs"
              : "text-slate-500 hover:text-slate-800"
          }`}
        >
          Submit New Safety Report
        </button>
        <button
          type="button"
          onClick={() => setMode("lookup")}
          className={`flex-1 py-2 rounded-lg transition-all ${
            mode === "lookup"
              ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-xs"
              : "text-slate-500 hover:text-slate-800"
          }`}
        >
          Check Existing Case & Chat
        </button>
      </div>

      {mode === "new" ? (
        createdCase ? (
          /* Submission Confirmation Card with Case Code */
          <Card className="p-6 text-center space-y-4 border-emerald-300 dark:border-emerald-800 bg-emerald-50/40 dark:bg-emerald-950/20">
            <div className="p-3 bg-emerald-100 dark:bg-emerald-900/40 rounded-full inline-block text-emerald-600">
              <CheckCircle2 className="h-10 w-10" />
            </div>
            <h3 className="text-xl font-black text-slate-900 dark:text-slate-100">
              Report Submitted Securely
            </h3>
            <p className="text-xs text-slate-600 dark:text-slate-400 max-w-md mx-auto">
              Your identity is completely sealed. Campus admins have been alerted. Save your
              unique confidential Case Code to check replies anonymously:
            </p>

            <div className="inline-block p-4 rounded-2xl bg-white dark:bg-slate-900 border-2 border-emerald-500 shadow-md">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-0.5">
                Confidential Case Code
              </span>
              <span className="text-3xl font-mono font-black text-emerald-600 tracking-wider select-all">
                {createdCase.case_code}
              </span>
            </div>

            <div className="pt-2 flex justify-center gap-3">
              <Button
                variant="primary"
                onClick={() => {
                  setLookupCode(createdCase.case_code);
                  setMode("lookup");
                  handleLookup(createdCase.case_code);
                }}
                className="text-xs font-bold py-2 px-5"
              >
                Open Anonymous Chat
              </Button>
            </div>
          </Card>
        ) : (
          /* Submission Form */
          <Card className="p-6 space-y-5">
            {/* Reassurance & Legal Guardrail Notice */}
            <div className="p-3.5 rounded-xl border border-blue-200 dark:border-blue-900/60 bg-blue-50/60 dark:bg-blue-950/20 text-xs space-y-1.5 text-blue-950 dark:text-blue-200">
              <div className="font-bold flex items-center gap-1.5">
                <Lock className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                Confidentiality & Non-Retaliation Policy
              </div>
              <p className="text-[11px] leading-relaxed text-blue-900/90 dark:text-blue-300">
                Reports are private and go only to the admin. Genuine reports are never penalised,
                even if they cannot be proven. Deliberately false reports may lead to action.
              </p>
            </div>

            <form onSubmit={handleCreateSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">
                  Category of Concern
                </label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="h-10 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-medium text-slate-900 dark:text-slate-100 outline-none focus:border-primary"
                >
                  {CATEGORIES.map((cat) => (
                    <option key={cat} value={cat}>
                      {cat}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">
                  Detailed Description & Location Details
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Provide as much detail as possible (what happened, where, and when)..."
                  rows={5}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 outline-none focus:border-primary"
                  required
                />
              </div>

              {error && (
                <div className="p-3 rounded-xl bg-rose-50 text-rose-700 text-xs font-semibold">
                  {error}
                </div>
              )}

              <Button
                type="submit"
                variant="primary"
                disabled={submitting}
                className="w-full font-bold py-2.5 text-xs flex items-center justify-center gap-1.5 shadow-sm"
              >
                <Shield className="h-4 w-4" />
                {submitting ? "Encrypting & Submitting..." : "Submit Anonymous Report"}
              </Button>
            </form>
          </Card>
        )
      ) : (
        /* Lookup Mode */
        <div className="space-y-5">
          <Card className="p-4">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleLookup();
              }}
              className="flex gap-2"
            >
              <input
                type="text"
                placeholder="Enter Case Code (e.g. SAFE-4821)..."
                value={lookupCode}
                onChange={(e) => setLookupCode(e.target.value)}
                className="h-10 flex-1 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3.5 text-xs font-mono uppercase font-bold text-slate-900 dark:text-slate-100 outline-none focus:border-primary"
              />
              <Button
                type="submit"
                variant="primary"
                disabled={lookingUp}
                className="font-bold text-xs px-5"
              >
                <Search className="h-4 w-4" />
                {lookingUp ? "Searching..." : "Track Case"}
              </Button>
            </form>
          </Card>

          {error && (
            <div className="p-3 rounded-xl bg-rose-50 text-rose-700 text-xs font-semibold">
              {error}
            </div>
          )}

          {activeCase && (
            <Card className="p-6 space-y-5">
              {/* Case Header */}
              <div className="flex items-start justify-between border-b border-slate-200 dark:border-slate-800 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-mono font-black text-primary">
                      {activeCase.case_code}
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                      {activeCase.status}
                    </span>
                  </div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 mt-1">
                    {activeCase.category}
                  </h3>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    Reported on {formatDate(activeCase.created_at)}
                  </div>
                </div>

                {activeCase.outcome && (
                  <div className="text-right">
                    <span className="text-[10px] font-semibold text-slate-400 block uppercase">
                      Admin Decision
                    </span>
                    <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 uppercase">
                      {activeCase.outcome.replace(/_/g, " ")}
                    </span>
                  </div>
                )}
              </div>

              {/* Messages Thread */}
              <div className="space-y-3 max-h-80 overflow-y-auto p-1">
                {(activeCase.messages || []).map((msg, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-xl max-w-[85%] text-xs space-y-1 ${
                      msg.sender_type === "admin"
                        ? "bg-primary/10 border border-primary/20 text-slate-900 dark:text-slate-100 ml-auto"
                        : "bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 mr-auto"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-4 text-[10px] font-bold opacity-75">
                      <span>{msg.sender_type === "admin" ? "🛡️ Campus Admin" : "🔒 You (Anonymous)"}</span>
                      <span>{formatDate(msg.created_at)}</span>
                    </div>
                    <p className="whitespace-pre-wrap">{msg.body}</p>
                  </div>
                ))}
              </div>

              {/* Reply Box */}
              <form onSubmit={handleSendReply} className="flex gap-2 pt-2 border-t border-slate-200 dark:border-slate-800">
                <input
                  type="text"
                  placeholder="Send confidential reply to admin..."
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  className="h-10 flex-1 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs text-slate-900 dark:text-slate-100 outline-none focus:border-primary"
                />
                <Button
                  type="submit"
                  variant="primary"
                  disabled={sendingReply || !replyText.trim()}
                  className="font-bold text-xs px-4"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </form>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

