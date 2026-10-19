import React from "react";

const Select = React.forwardRef(
  ({ label, error, id, children, options, className = "", ...props }, ref) => {
    return (
      <label
        className="grid gap-2 text-sm font-semibold text-slate-900 dark:text-slate-100"
        htmlFor={id}
      >
        {label && <span>{label}</span>}
        <select
          id={id}
          ref={ref}
          className={`h-12 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 text-sm font-medium text-slate-800 dark:text-slate-100 outline-none transition-all duration-150 focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-slate-50 dark:disabled:bg-slate-800 disabled:cursor-not-allowed [&>option]:bg-white [&>option]:text-slate-900 dark:[&>option]:bg-slate-900 dark:[&>option]:text-slate-100 ${error ? "border-campus-danger focus:border-campus-danger focus:ring-campus-danger/10" : ""} ${className}`}
          {...props}
        >
          {Array.isArray(options)
            ? options.map((opt) => (
                <option
                  key={typeof opt === "object" ? opt.value : opt}
                  value={typeof opt === "object" ? opt.value : opt}
                  disabled={typeof opt === "object" ? opt.disabled : false}
                >
                  {typeof opt === "object" ? opt.label : opt}
                </option>
              ))
            : children}
        </select>
        {error && (
          <span className="text-xs font-medium text-campus-danger lowercase tracking-normal">
            {error}
          </span>
        )}
      </label>
    );
  },
);

Select.displayName = "Select";
export default Select;
