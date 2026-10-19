export default function PageHeader({ title, description, actions, children }) {
  const actionContent = actions || children;
  return (
    <div className="mb-3 sm:mb-6 flex flex-wrap items-center justify-between gap-2.5 sm:gap-4 border-b border-slate-200/80 dark:border-slate-800 pb-3 sm:pb-5">
      <div className="min-w-0">
        <h1 className="text-lg sm:text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
          {title}
        </h1>
        {description && (
          <p className="mt-0.5 sm:mt-1 text-xs sm:text-sm text-slate-500 dark:text-slate-400 font-normal leading-normal line-clamp-1 sm:line-clamp-none">
            {description}
          </p>
        )}
      </div>
      {actionContent && (
        <div className="flex flex-wrap items-center gap-2 sm:gap-2.5 shrink-0">{actionContent}</div>
      )}
    </div>
  );
}
