import React from "react";

const Textarea = React.forwardRef(
  ({ label, error, id, className = "", ...props }, ref) => {
    return (
      <label
        className="grid gap-2 text-sm font-semibold text-slate-900 dark:text-slate-100"
        htmlFor={id}
      >
        {label && <span>{label}</span>}
        <textarea
          id={id}
          ref={ref}
          className={`min-h-24 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-3 text-sm font-medium text-slate-800 dark:text-slate-100 outline-none transition-all duration-150 focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-slate-50 dark:disabled:bg-slate-800 disabled:cursor-not-allowed ${error ? "border-campus-danger focus:border-campus-danger focus:ring-campus-danger/10" : ""} ${className}`}
          {...props}
        />
        {error && (
          <span className="text-xs font-medium text-campus-danger lowercase tracking-normal">
            {error}
          </span>
        )}
      </label>
    );
  },
);

Textarea.displayName = "Textarea";
export default Textarea;
