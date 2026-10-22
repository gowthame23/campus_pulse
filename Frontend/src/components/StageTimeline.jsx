import { useState, useEffect } from "react";
import { Check, Hourglass } from "lucide-react";
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
    <div className="flex items-center gap-2 p-2 rounded-lg border border-slate-200/80 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-900/40">
      <Hourglass className={`h-3.5 w-3.5 shrink-0 ${tone === "danger" ? "text-rose-500 animate-pulse" : tone === "warning" ? "text-amber-500" : "text-emerald-500"}`} />
      <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400">
        {label}:
      </span>
      <span className={`text-xs font-mono font-bold ${tone === "danger" ? "text-rose-600 dark:text-rose-400" : tone === "warning" ? "text-amber-600 dark:text-amber-400" : "text-emerald-600 dark:text-emerald-400"}`}>
        {countdown.isOverdue ? `Overdue (${timeString})` : timeString}
      </span>
    </div>
  );
}

export default function StageTimeline({ complaint }) {
  if (!complaint) return null;

  const rawStatus = String(complaint.status || "Complaint Raised").toLowerCase();
  const isOtherTriage =
    complaint.department_id === "DEPT_OTHER_GENERAL" ||
    complaint.department_id === "DEPT_OTHER" ||
    complaint.location_id === "LOC_OTHER" ||
    rawStatus.includes("under review");

  if (isOtherTriage) {
    return (
      <div className="rounded-xl border border-purple-200/80 dark:border-purple-800/60 bg-purple-50/50 dark:bg-purple-950/20 p-3 shadow-xs flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-purple-500 animate-pulse" />
          <span className="text-xs font-bold text-purple-900 dark:text-purple-200">
            Admin Triage & Review
          </span>
        </div>
        <span className="text-[11px] text-purple-700 dark:text-purple-300 font-medium">
          No SLA • Directly Routed to Administration
        </span>
      </div>
    );
  }

  const isFixed =
    rawStatus.includes("fix") ||
    rawStatus.includes("done") ||
    rawStatus.includes("close") ||
    rawStatus.includes("verif") ||
    rawStatus.includes("resolv");
  const isGoingOn =
    !isFixed &&
    (rawStatus.includes("going") ||
      rawStatus.includes("progress") ||
      rawStatus.includes("assign") ||
      rawStatus.includes("part"));

  const steps = [
    {
      id: "raised",
      label: "Complaint Raised",
      state: isFixed || isGoingOn ? "completed" : "active",
      time: complaint.created_at,
    },
    {
      id: "going_on",
      label: "Going On",
      state: isFixed ? "completed" : isGoingOn ? "active" : "pending",
      time: isFixed || isGoingOn ? (complaint.started_at || complaint.assigned_at) : null,
    },
    {
      id: "fixed",
      label: "Fixed",
      state: isFixed ? "completed" : "pending",
      time: isFixed ? (complaint.fixed_at || complaint.resolved_at) : null,
    },
  ];

  return (
    <div className="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-[#101726] p-3.5 shadow-xs">
      <div className="flex items-center justify-between relative px-2">
        {/* Progress Background Track */}
        <div className="absolute top-3.5 left-8 right-8 h-0.5 bg-slate-200 dark:bg-slate-800 z-0" />
        {/* Completed Progress Track */}
        <div
          className="absolute top-3.5 left-8 h-0.5 bg-emerald-500 transition-all duration-300 z-0"
          style={{
            width: isFixed ? "calc(100% - 4rem)" : isGoingOn ? "calc(50% - 2rem)" : "0%",
          }}
        />

        {steps.map((step) => {
          const isComp = step.state === "completed";
          const isAct = step.state === "active";

          return (
            <div key={step.id} className="relative z-10 flex flex-col items-center text-center flex-1">
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold transition-all ${
                  isComp
                    ? "bg-emerald-500 text-white shadow-xs"
                    : isAct
                    ? "bg-primary text-white ring-4 ring-primary/20 shadow-xs"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-400 border border-slate-300 dark:border-slate-700"
                }`}
              >
                {isComp ? (
                  <Check className="h-3.5 w-3.5" />
                ) : isAct ? (
                  <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                ) : (
                  <span className="w-1.5 h-1.5 rounded-full bg-slate-300 dark:bg-slate-600" />
                )}
              </div>

              <span
                className={`mt-1.5 text-xs font-bold tracking-tight ${
                  isAct
                    ? "text-primary dark:text-blue-400 font-extrabold"
                    : isComp
                    ? "text-slate-900 dark:text-slate-100 font-semibold"
                    : "text-slate-400 dark:text-slate-500"
                }`}
              >
                {step.label}
              </span>

              {step.time ? (
                <span className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5 truncate max-w-[90px]">
                  {formatDate(step.time)}
                </span>
              ) : (
                <span className="text-[10px] text-slate-400 dark:text-slate-600 mt-0.5 italic">
                  {isAct ? "In Progress" : "Pending"}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
