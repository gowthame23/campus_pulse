import React, { useState, useEffect, useMemo } from "react";
import {
  Clock,
  Check,
  AlertTriangle,
  PlayCircle,
  User,
  Star,
  Hourglass,
  CheckCircle2,
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

  const rawStatus = String(complaint.status || "Starred").toLowerCase();

  // Normalize into 3 clean stages: Starred, Going On, Done
  const isStarred = rawStatus.includes("star") || rawStatus.includes("submit") || rawStatus.includes("pend");
  const isGoingOn = rawStatus.includes("going") || rawStatus.includes("progress") || rawStatus.includes("assign") || rawStatus.includes("part");
  const isDone = rawStatus.includes("done") || rawStatus.includes("close") || rawStatus.includes("verif") || rawStatus.includes("resolv");

  const coordinatorName = coordinatorUser?.name || complaint.assigned_to || "Department Coordinator";

  const stages = [
    {
      id: "starred",
      title: "⭐ Starred",
      status: isStarred ? "active" : "completed",
      actorName: complaint.creator_name || complaint.created_by || "Student",
      actorRole: "Submitter",
      timestamp: complaint.created_at,
      description: "Complaint logged and queued for department attention.",
    },
    {
      id: "going_on",
      title: "⏳ Going On",
      status: isDone ? "completed" : isGoingOn ? "active" : "pending",
      actorName: coordinatorName,
      actorRole: "Coordinator",
      timestamp: complaint.started_at || complaint.assigned_at,
      description: isDone
        ? "Work was completed by maintenance coordinator."
        : isGoingOn
        ? "Maintenance and repairs are actively underway."
        : "Awaiting coordinator to begin maintenance work.",
    },
    {
      id: "done",
      title: "✅ Done",
      status: isDone ? "completed" : "pending",
      actorName: coordinatorName,
      actorRole: "Coordinator",
      timestamp: complaint.fixed_at || complaint.resolved_at,
      description: isDone
        ? complaint.resolution_notes || "All repairs verified and completed."
        : "Work is not yet marked complete.",
    },
  ];

  return (
    <div className="space-y-4">
      {/* 3-Stage Progress Timeline */}
      <div className="rounded-2xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-[#101726] p-5 shadow-xs">
        <div className="flex items-center justify-between mb-5 border-b border-slate-100 dark:border-slate-800/80 pb-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 flex items-center gap-2">
            <Clock className="h-4 w-4 text-primary" />
            Complaint Progress Tracker
          </h2>
          <span className="text-xs font-bold text-primary">
            {isDone ? "Stage 3 of 3 (Done)" : isGoingOn ? "Stage 2 of 3 (Going On)" : "Stage 1 of 3 (Starred)"}
          </span>
        </div>

        <div className="relative pl-6 space-y-6 before:absolute before:left-3 before:top-2 before:bottom-3 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-800">
          {stages.map((stage) => {
            const isCompleted = stage.status === "completed";
            const isActive = stage.status === "active";

            return (
              <div key={stage.id} className="relative group">
                {/* Dot Icon */}
                <div
                  className={`absolute -left-[27px] top-0.5 h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold border-2 transition-all ${
                    isCompleted
                      ? "bg-emerald-600 border-white dark:border-[#101726] text-white shadow-2xs"
                      : isActive
                      ? "bg-primary border-primary/20 text-white ring-4 ring-primary/20 animate-pulse"
                      : "bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700 text-slate-400"
                  }`}
                >
                  {isCompleted ? (
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
                      <span
                        className={`text-sm font-bold ${
                          isActive
                            ? "text-primary dark:text-blue-400 font-extrabold"
                            : isCompleted
                            ? "text-slate-900 dark:text-slate-100"
                            : "text-slate-400 dark:text-slate-500"
                        }`}
                      >
                        {stage.title}
                      </span>
                      <Badge tone={isCompleted ? "success" : isActive ? "warning" : "default"}>
                        {isCompleted ? "Completed" : isActive ? "Active" : "Pending"}
                      </Badge>
                    </div>

                    <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                      {stage.description}
                    </p>

                    <div className="flex flex-wrap items-center gap-2 mt-1 text-[11px] text-slate-500 dark:text-slate-400 font-medium">
                      <span className="inline-flex items-center gap-1 font-semibold text-slate-700 dark:text-slate-300">
                        <User className="h-3 w-3 text-slate-400" />
                        {stage.actorName} ({stage.actorRole})
                      </span>
                      {stage.timestamp && (
                        <span>· {formatDate(stage.timestamp)}</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
