export default function PageHeader({ title, description, actions, children }) {
  const actionContent = actions || children;
  return (
    <div className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-slate-200/80 dark:border-slate-800 pb-5">
      <div>
        <h1 className="text-xl sm:text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
          {title}
        </h1>
        {description && (
          <p className="mt-1 text-xs sm:text-sm text-slate-500 dark:text-slate-400 font-normal leading-normal">
            {description}
          </p>
        )}
      </div>
      {actionContent && (
        <div className="flex flex-wrap items-center gap-2.5">{actionContent}</div>
      )}
    </div>
  );
}
