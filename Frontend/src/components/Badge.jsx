export default function Badge({ children, tone = "default", className = "" }) {
  const tones = {
    default:
      "bg-slate-100 dark:bg-slate-800/90 text-slate-700 dark:text-slate-300 border border-slate-200/70 dark:border-slate-700/60",
    success:
      "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200/70 dark:border-emerald-800/40",
    warning:
      "bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200/70 dark:border-amber-800/40",
    danger:
      "bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200/70 dark:border-rose-800/40",
    error:
      "bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 border border-rose-200/70 dark:border-rose-800/40",
    info:
      "bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200/70 dark:border-blue-800/40",
    orange:
      "bg-orange-50 dark:bg-orange-950/40 text-orange-700 dark:text-orange-300 border border-orange-200/70 dark:border-orange-800/40",
    amber:
      "bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200/70 dark:border-amber-800/40",
    purple:
      "bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-200/70 dark:border-purple-800/40",
  };

  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[11px] font-medium tracking-tight ${tones[tone] || tones.default} ${className}`}
    >
      {children}
    </span>
  );
}
