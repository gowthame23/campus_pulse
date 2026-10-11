export default function Toast({ message, tone = "info", onClose }) {
  if (!message) return null;

  const tones = {
    info: "border-blue-200/80 dark:border-blue-900/50 bg-blue-50/80 dark:bg-blue-950/30 text-blue-900 dark:text-blue-200",
    success: "border-emerald-200/80 dark:border-emerald-900/50 bg-emerald-50/80 dark:bg-emerald-950/30 text-emerald-900 dark:text-emerald-200",
    danger: "border-rose-200/80 dark:border-rose-900/50 bg-rose-50/80 dark:bg-rose-950/30 text-rose-900 dark:text-rose-200",
    error: "border-rose-200/80 dark:border-rose-900/50 bg-rose-50/80 dark:bg-rose-950/30 text-rose-900 dark:text-rose-200",
    warning: "border-amber-200/80 dark:border-amber-900/50 bg-amber-50/80 dark:bg-amber-950/30 text-amber-900 dark:text-amber-200",
  };

  return (
    <div
      role="alert"
      className={`flex items-center justify-between gap-3 rounded-xl border p-3.5 text-xs sm:text-sm font-medium transition-all duration-200 shadow-2xs ${tones[tone] || tones.info}`}
    >
      <span className="leading-snug">{message}</span>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="text-xs font-semibold uppercase tracking-wider opacity-70 hover:opacity-100 transition-opacity cursor-pointer shrink-0"
        >
          Dismiss
        </button>
      )}
    </div>
  );
}
