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
      className={`relative group rounded-xl border p-4 sm:p-5 shadow-2xs ${accentClass} ${interactiveClass}`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 truncate">
          {label}
        </span>
        {onClick && (
          <ArrowRight className="h-3.5 w-3.5 text-slate-400 group-hover:text-primary group-hover:translate-x-0.5 transition-all shrink-0" />
        )}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-slate-100 tabular-nums leading-none">
          {value}
        </span>
        {accent && (
          <span className="h-2 w-2 rounded-full bg-amber-500 shrink-0" title="Action required" />
        )}
      </div>
      {subtext && (
        <p className="mt-2 text-xs font-normal text-slate-400 dark:text-slate-500 truncate">
          {subtext}
        </p>
      )}
    </div>
  );
}
