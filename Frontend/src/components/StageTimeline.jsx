import { useState, useEffect } from "react";
import {
  Clock,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  PauseCircle,
  PlayCircle,
  User,
  Check,
  Building,
  Hourglass,
} from "lucide-react";
import Badge from "./Badge.jsx";
import { formatDate } from "../utils/dateFormatter.js";

function useCountdown(targetIso) {
  const [timeLeft, setTimeLeft] = useState(null);

  useEffect(() => {
    if (!targetIso) {
      setTimeLeft(null);
      return;
    }

    function calculate() {
      const target = new Date(targetIso).getTime();
      const now = Date.now();
      const diff = target - now;

      if (isNaN(target)) {
        setTimeLeft(null);
        return;
      }

      const isOverdue = diff <= 0;
      const absDiff = Math.abs(diff);
      const hours = Math.floor(absDiff / (1000 * 60 * 60));
      const minutes = Math.floor((absDiff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((absDiff % (1000 * 60)) / 1000);

      setTimeLeft({
        isOverdue,
        hours,
        minutes,
        seconds,
        totalHours: diff / (1000 * 60 * 60),
      });
    }

    calculate();
    const interval = setInterval(calculate, 1000);
    return () => clearInterval(interval);
  }, [targetIso]);

  return timeLeft;
}

function useElapsedTime(startIso) {
  const [elapsed, setElapsed] = useState("");
  useEffect(() => {
    if (!startIso) {
      setElapsed("");
      return;
    }
    function update() {
      const start = new Date(startIso).getTime();
      const now = Date.now();
      const diff = Math.max(0, now - start);
      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      if (hours > 0) {
        setElapsed(`${hours}h ${minutes}m so far`);
      } else {
        setElapsed(`${minutes}m so far`);
      }
    }
    update();
    const interval = setInterval(update, 10000);
    return () => clearInterval(interval);
  }, [startIso]);
  return elapsed;
}

function formatExpectedTime(targetIso) {
  if (!targetIso) return "";
  try {
    const d = new Date(targetIso);
    return d.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  } catch {
    return "";
  }
}

export function CountdownTimerBadge({ targetIso, label, warningHours = 4, dangerHours = 1 }) {
  const countdown = useCountdown(targetIso);
  if (!countdown) return null;

  let tone = "success";
  if (countdown.isOverdue || countdown.totalHours <= dangerHours) {
    tone = "danger";
  } else if (countdown.totalHours <= warningHours) {
    tone = "warning";
  }

  const timeString = `${String(countdown.hours).padStart(2, "0")}h ${String(countdown.minutes).padStart(2, "0")}m ${String(countdown.seconds).padStart(2, "0")}s`;

  return (
    <div className="flex items-center gap-2 p-2.5 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/40">
      <Hourglass className={`h-4 w-4 shrink-0 ${tone === "danger" ? "text-rose-500 animate-pulse" : tone === "warning" ? "text-amber-500" : "text-emerald-500"}`} />
      <div className="flex flex-col">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {label}
        </span>
        <span className={`text-xs font-mono font-bold ${tone === "danger" ? "text-rose-600 dark:text-rose-400" : tone === "warning" ? "text-amber-600 dark:text-amber-400" : "text-emerald-600 dark:text-emerald-400"}`}>
          {countdown.isOverdue ? `Overdue by ${timeString}` : `${timeString} left`}
        </span>
      </div>
    </div>
  );
}

export default function StageTimeline({ complaint, coordinatorUser, wardenUser, attachments = [] }) {
  if (!complaint) return null;

  const status = complaint.status || "Submitted";
  const priority = (complaint.priority || "Medium").toLowerCase();
  const isHighOrCrit = priority === "high" || priority === "critical";
  const requiresWarden =
    complaint.requires_warden_check ||
    complaint.is_spot_check ||
    isHighOrCrit ||
    Boolean(complaint.warden_verified_at);

  const isPaused = status === "Waiting for Parts";
  const wasPaused = Boolean(complaint.paused_at) && !isPaused;

  const workingElapsed = useElapsedTime(complaint.work_started_at);
  const expectedResolutionTime = formatExpectedTime(complaint.sla_due_at || complaint.target_resolution_at);

  // Extract inline progress notes from complaint history
  const progressNotes = useMemo(() => {
    if (!complaint?.history) return [];
    return complaint.history
      .filter((h) => {
        const text = typeof h === "string" ? h : h?.action || h?.message || "";
        return text.toLowerCase().includes("progress update") || text.toLowerCase().includes("progress note");
      })
      .map((h) => (typeof h === "string" ? h : h?.action || h?.message || ""));
  }, [complaint]);

  // Extract before and after photos
  const beforePhoto = useMemo(() => {
    return (attachments || []).find(
      (a) =>
        a.category === "Before Repair" ||
        a.category === "Original" ||
        a.category === "Student Submission" ||
        (!a.category && a.uploaded_by === complaint.created_by)
    );
  }, [attachments, complaint]);

  const afterPhoto = useMemo(() => {
    return (attachments || []).find(
      (a) =>
        a.category === "After Repair" ||
        (a.category !== "Before Repair" && a.uploaded_by && a.uploaded_by !== complaint.created_by)
    );
  }, [attachments, complaint]);

  const isOverdue = Boolean(complaint.is_overdue || complaint.sla_status === "Breached");

  // Build the vertical stages list
  const stages = [
    {
      id: "submitted",
      title: "Filed",
      actorName: complaint.student_name || complaint.created_by || "Student",
      actorRole: "Student",
      timestamp: complaint.created_at,
      status: "completed",
      description: "Complaint filed into campus intake queue",
      isLate: false,
    },
    {
      id: "assigned",
      title: "Accepted",
      actorName:
        coordinatorUser?.name ||
        complaint.coordinator_name ||
        complaint.assigned_to ||
        "Coordinator Team",
      actorRole: "Coordinator",
      timestamp: complaint.assigned_at,
      status: complaint.assigned_to ? "completed" : status === "Submitted" ? "active" : "pending",
      description: complaint.assigned_to
        ? `Accepted by ${coordinatorUser?.name || complaint.assigned_to}`
        : "Available in team accept queue",
      isLate: status === "Submitted" && isOverdue,
    },
    {
      id: "work_started",
      title: "Working",
      actorName:
        coordinatorUser?.name ||
        complaint.coordinator_name ||
        complaint.assigned_to ||
        "Coordinator",
      actorRole: "Coordinator",
      timestamp: complaint.work_started_at,
      status: complaint.work_started_at
        ? "completed"
        : status === "Assigned"
          ? "active"
          : ["In Progress", "Waiting for Parts", "Pending Warden Verification", "Waiting for Verification", "Closed", "Closed (Auto Closed)"].includes(status)
            ? "completed"
            : "pending",
      description: complaint.work_started_at
        ? `${workingElapsed ? `${workingElapsed} ` : ""}${expectedResolutionTime ? `· expected by ${expectedResolutionTime}` : ""}`
        : "Pending start of repair work",
      isLate: (status === "In Progress" || status === "Assigned") && isOverdue,
    },
  ];

  // If paused or previously paused, show Waiting for Parts
  if (isPaused || wasPaused || complaint.paused_at) {
    stages.push({
      id: "paused",
      title: "Waiting for Parts",
      actorName:
        coordinatorUser?.name ||
        complaint.coordinator_name ||
        complaint.assigned_to ||
        "Coordinator",
      actorRole: "Coordinator",
      timestamp: complaint.paused_at,
      status: isPaused ? "active" : "completed",
      description: complaint.pause_reason
        ? `Work paused: ${complaint.pause_reason}`
        : "Work paused awaiting required spare parts",
      isLate: isPaused && isOverdue,
    });
  }

  // Fixed stage
  stages.push({
    id: "fixed",
    title: "Fixed",
    actorName:
      coordinatorUser?.name ||
      complaint.fixed_by ||
      complaint.assigned_to ||
      "Coordinator",
    actorRole: "Coordinator",
    timestamp: complaint.fixed_at || complaint.resolved_at,
    status:
      complaint.fixed_at || complaint.resolved_at
        ? "completed"
        : status === "In Progress" || isPaused
          ? "active"
          : "pending",
    description: complaint.resolution_notes
      ? `Work marked done: ${complaint.resolution_notes}`
      : "Repair completed by department coordinator",
    isLate: false,
  });

  // Warden verification stage if applicable
  if (requiresWarden) {
    let wardenStatus = "pending";
    if (complaint.warden_verified_at) {
      wardenStatus = "completed";
    } else if (status === "Pending Warden Verification") {
      wardenStatus = "active";
    }

    stages.push({
      id: "warden_verified",
      title: complaint.is_spot_check ? "Warden Spot Check" : "Warden Verified",
      actorName:
        wardenUser?.name ||
        complaint.warden_verified_by ||
        "Location Warden",
      actorRole: "Location In-Charge",
      timestamp: complaint.warden_verified_at,
      status: wardenStatus,
      description: complaint.warden_verdict
        ? `Verdict: ${complaint.warden_verdict} ${complaint.warden_notes ? `— "${complaint.warden_notes}"` : ""}`
        : complaint.is_spot_check
          ? "Randomly selected for in-person warden verification (~10%)"
          : "Requires mandatory in-person verification by location warden",
      isLate: status === "Pending Warden Verification" && isOverdue,
    });
  }

  // Student Closed stage
  stages.push({
    id: "student_closed",
    title: status.includes("Auto") ? "Auto-Closed" : "Confirmed / Closed",
    actorName:
      complaint.closed_by ||
      (status.includes("Auto") ? "System Auto-Close" : complaint.created_by || "Student"),
    actorRole: status.includes("Auto") ? "System" : "Student",
    timestamp: complaint.closed_at,
    status:
      status.startsWith("Closed")
        ? "completed"
        : status === "Waiting for Verification"
          ? "active"
          : "pending",
    description: status.startsWith("Closed")
      ? `Confirmed fixed and permanently closed ${complaint.reopen_count ? `(${complaint.reopen_count} of 3 reopens used)` : ""}`
      : "Awaiting final confirmation from reporting student (48h timer)",
    isLate: status === "Waiting for Verification" && isOverdue,
  });

  // Live countdown timers to display
  const showAcceptTimer =
    (status === "Submitted" || status === "Pending") &&
    Boolean(complaint.accept_due_at);
  const showSlaTimer =
    ["Assigned", "In Progress", "Waiting for Parts"].includes(status) &&
    Boolean(complaint.sla_due_at || complaint.target_resolution_at);
  const showVerifyTimer =
    status === "Waiting for Verification" &&
    Boolean(complaint.verification_due_at);

  return (
    <div className="space-y-5">
      {/* Top Banner: Public Affected Count & Reopen Status */}
      <div className="flex flex-wrap items-center gap-2.5">
        {(complaint.affected_count > 0 || complaint.visibility_type === "Community") && (
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-blue-200 dark:border-blue-900 bg-blue-50 dark:bg-blue-950/40 text-blue-800 dark:text-blue-300 text-xs font-bold">
            <span>👥</span>
            <span>{complaint.affected_count || 1} students affected</span>
          </div>
        )}
        {complaint.reopen_count > 0 && (
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-amber-200 dark:border-amber-900 bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 text-xs font-bold">
            <span>🔁</span>
            <span>{complaint.reopen_count} of 3 reopens used</span>
          </div>
        )}
        {status === "Waiting for Verification" && (
          <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-emerald-200 dark:border-emerald-900 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 text-xs font-bold">
            <Clock className="h-3.5 w-3.5" />
            <span>Auto-closes in 48h if unconfirmed</span>
          </div>
        )}
      </div>

      {/* Live Countdown Timers Panel */}
      {(showAcceptTimer || showSlaTimer || showVerifyTimer) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {showAcceptTimer && (
            <CountdownTimerBadge
              targetIso={complaint.accept_due_at}
              label="Acceptance Deadline"
              warningHours={2}
              dangerHours={0.5}
            />
          )}
          {showSlaTimer && (
            <CountdownTimerBadge
              targetIso={complaint.sla_due_at || complaint.target_resolution_at}
              label="Resolution SLA Target"
              warningHours={8}
              dangerHours={2}
            />
          )}
          {showVerifyTimer && (
            <CountdownTimerBadge
              targetIso={complaint.verification_due_at}
              label="Student Auto-Close Countdown"
              warningHours={12}
              dangerHours={4}
            />
          )}
        </div>
      )}

      {/* Admin Review Alert Banner */}
      {status === "Admin Review" && (
        <div className="p-4 rounded-xl border border-rose-300 dark:border-rose-900 bg-rose-50 dark:bg-rose-950/30 text-rose-900 dark:text-rose-200 shadow-xs">
          <div className="flex items-start gap-3">
            <ShieldAlert className="h-5 w-5 text-rose-600 dark:text-rose-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold">Under Administrator Review</h3>
              <p className="text-xs mt-1 text-rose-800 dark:text-rose-300 font-medium">
                {complaint.admin_review_reason ||
                  "This complaint has reached the maximum student reopens (3/3) and is escalated to campus administration for final disposition."}
              </p>
              {complaint.admin_decision && (
                <div className="mt-2 text-xs font-semibold bg-white/60 dark:bg-rose-900/40 p-2 rounded-lg">
                  Administrator Decision: {complaint.admin_decision}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Vertical Stage Timeline */}
      <div className="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-[#101726] p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4 border-b border-slate-100 dark:border-slate-800/80 pb-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 flex items-center gap-2">
            <Clock className="h-4 w-4 text-primary" />
            Live Tracking Timeline
          </h2>
          <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400">
            {stages.filter((s) => s.status === "completed").length} of {stages.length} stages completed
          </span>
        </div>

        <div className="relative pl-6 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-3 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-800">
          {stages.map((stage) => {
            const isCompleted = stage.status === "completed";
            const isActive = stage.status === "active";
            const isLate = stage.isLate;

            return (
              <div key={stage.id} className="relative group">
                {/* Dot */}
                <div
                  className={`absolute -left-[27px] top-0.5 h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-all ${
                    isLate
                      ? "bg-rose-600 border-rose-200 text-white ring-4 ring-rose-200 animate-pulse"
                      : isCompleted
                        ? "bg-emerald-600 border-white dark:border-[#101726] text-white shadow-2xs"
                        : isActive
                          ? "bg-primary border-primary/20 text-white ring-4 ring-primary/20 animate-pulse"
                          : "bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-400"
                  }`}
                >
                  {isLate ? (
                    <AlertTriangle className="h-3.5 w-3.5" />
                  ) : isCompleted ? (
                    <Check className="h-3.5 w-3.5" />
                  ) : isActive ? (
                    <PlayCircle className="h-3.5 w-3.5" />
                  ) : (
                    <span className="h-2 w-2 rounded-full bg-slate-300 dark:bg-slate-600" />
                  )}
                </div>

                {/* Content */}
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-1.5 sm:gap-4">
                  <div className="space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`text-sm font-bold ${isLate ? "text-rose-600 dark:text-rose-400 font-extrabold" : isActive ? "text-primary dark:text-blue-400 font-extrabold" : isCompleted ? "text-slate-900 dark:text-slate-100" : "text-slate-400 dark:text-slate-500"}`}>
                        {stage.title}
                      </span>
                      <Badge
                        tone={
                          isLate
                            ? "danger"
                            : isCompleted
                              ? "success"
                              : isActive
                                ? "warning"
                                : "default"
                        }
                      >
                        {isLate ? "Overdue" : isCompleted ? "Completed" : isActive ? "Active" : "Pending"}
                      </Badge>
                      {isLate && (
                        <span className="text-[11px] font-bold text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 px-2 py-0.5 rounded border border-rose-200 dark:border-rose-900">
                          LATE · Responsible: {stage.actorName} ({stage.actorRole})
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                      {stage.description}
                    </p>

                    <div className="flex flex-wrap items-center gap-2 mt-1 text-[11px] text-slate-500 dark:text-slate-400 font-medium">
                      <span className="inline-flex items-center gap-1 font-semibold text-slate-700 dark:text-slate-300">
                        <User className="h-3 w-3 text-slate-400" />
                        {stage.actorName} ({stage.actorRole})
                      </span>
                    </div>

                    {/* Inline Progress Notes under Working stage */}
                    {stage.id === "work_started" && progressNotes.length > 0 && (
                      <div className="mt-2 space-y-1.5 border-l-2 border-primary/40 pl-3">
                        <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block">
                          Progress Notes:
                        </span>
                        {progressNotes.map((note, idx) => (
                          <div
                            key={idx}
                            className="text-xs text-slate-700 dark:text-slate-300 bg-slate-50 dark:bg-slate-900/60 p-2 rounded-lg border border-slate-200/60 dark:border-slate-800"
                          >
                            {note}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Side-by-side Photo Comparison under Fixed stage */}
                    {stage.id === "fixed" && (beforePhoto || afterPhoto || complaint.photo_skipped) && (
                      <div className="mt-3 pt-2 border-t border-slate-100 dark:border-slate-800/80">
                        <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 block mb-2">
                          Repair Photo Comparison:
                        </span>
                        {complaint.photo_skipped && (
                          <div className="mb-2 p-2 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 text-amber-800 text-xs font-medium">
                            ⚠️ Skip – student photo not relevant {complaint.photo_skip_reason ? `("${complaint.photo_skip_reason}")` : ""}
                          </div>
                        )}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg">
                          {beforePhoto ? (
                            <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden bg-slate-50 dark:bg-slate-900">
                              <div className="p-2 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
                                <span className="text-xs font-bold text-slate-700 dark:text-slate-300">Before Repair</span>
                                <Badge tone="default">Student</Badge>
                              </div>
                              <img
                                src={beforePhoto.url || `/api/attachments/${beforePhoto.attachment_id}/download`}
                                alt="Before Repair"
                                className="w-full h-32 object-cover"
                              />
                            </div>
                          ) : (
                            <div className="border border-dashed border-slate-200 dark:border-slate-800 rounded-xl p-4 text-center text-xs text-slate-400">
                              No before photo filed
                            </div>
                          )}

                          {afterPhoto ? (
                            <div className="border border-slate-200 dark:border-slate-800 rounded-xl overflow-hidden bg-slate-50 dark:bg-slate-900">
                              <div className="p-2 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
                                <span className="text-xs font-bold text-slate-700 dark:text-slate-300">After Repair</span>
                                <Badge tone={afterPhoto.is_camera ? "success" : "info"}>
                                  {afterPhoto.is_camera ? "Taken live" : "From gallery"}
                                </Badge>
                              </div>
                              <img
                                src={afterPhoto.url || `/api/attachments/${afterPhoto.attachment_id}/download`}
                                alt="After Repair"
                                className="w-full h-32 object-cover"
                              />
                              {afterPhoto.flags && afterPhoto.flags.length > 0 && (
                                <div className="p-1.5 bg-amber-50 dark:bg-amber-950/50 text-[10px] text-amber-800 border-t border-amber-200 font-semibold">
                                  ⚠️ {afterPhoto.flags.join(", ")}
                                </div>
                              )}
                            </div>
                          ) : complaint.photo_skipped ? null : (
                            <div className="border border-dashed border-slate-200 dark:border-slate-800 rounded-xl p-4 text-center text-xs text-slate-400">
                              Awaiting after photo
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>

                  {stage.timestamp && (
                    <div className="text-[11px] font-mono text-slate-400 dark:text-slate-500 shrink-0">
                      {formatDate(stage.timestamp)}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
