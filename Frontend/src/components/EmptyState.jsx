import Button from "./Button.jsx";

export default function EmptyState({
  title = "No records found",
  description = "New items will appear here when available.",
  actionLabel,
  onAction,
}) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-5 sm:p-8 text-center shadow-sm">
      <div className="mx-auto mb-2.5 sm:mb-4 flex h-10 w-10 sm:h-12 sm:w-12 items-center justify-center rounded-xl bg-slate-50 dark:bg-slate-800 text-slate-400 dark:text-slate-500">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5 sm:h-6 sm:w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1.5}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0a2 2 0 01-2 2H6a2 2 0 01-2-2m16 0l-3.586 3.586a2 2 0 01-2.828 0L4 13"
          />
        </svg>
      </div>
      <h3 className="text-sm sm:text-base font-bold text-slate-800 dark:text-slate-100">{title}</h3>
      <p className="mx-auto mt-1 max-w-sm text-xs sm:text-sm text-slate-400 dark:text-slate-400 font-medium">
        {description}
      </p>
      {actionLabel && onAction && (
        <div className="mt-3.5 sm:mt-5">
          <Button onClick={onAction}>{actionLabel}</Button>
        </div>
      )}
    </div>
  );
}
