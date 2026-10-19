import { ArrowRight } from "lucide-react";

export default function StatCard({
  label,
  value,
  subtext,
  accent = false,
  onClick,
}) {
  const accentClass = accent
    ? "border-primary/40 dark:border-primary/50 bg-primary/[0.02] dark:bg-primary/[0.04]"
    : "border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-[#101726]";

  const interactiveClass = onClick
    ? "cursor-pointer hover:border-slate-300 dark:hover:border-slate-700 hover:shadow-xs transition-all duration-150 active:scale-[0.99]"
    : "";

  return (
    <div
      onClick={onClick}
      className={`relative group rounded-xl border px-3.5 py-3 sm:px-4 sm:py-3.5 shadow-2xs ${accentClass} ${interactiveClass}`}
    >
      <div className="flex items-center justify-between gap-2.5">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 truncate">
            {label}
          </span>
          <span className="text-sm sm:text-base font-extrabold text-slate-900 dark:text-slate-100 tabular-nums px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 shrink-0">
            {value}
          </span>
          {accent && (
            <span className="h-2 w-2 rounded-full bg-amber-500 shrink-0" title="Action required" />
          )}
        </div>
        {onClick && (
          <ArrowRight className="h-4 w-4 text-slate-400 group-hover:text-primary group-hover:translate-x-0.5 transition-all shrink-0" />
        )}
      </div>
      {subtext && (
        <p className="mt-1.5 text-xs font-normal text-slate-400 dark:text-slate-500 truncate">
          {subtext}
        </p>
      )}
    </div>
  );
}
