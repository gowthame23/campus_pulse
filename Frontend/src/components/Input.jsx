import React, { useState } from "react";
import { Eye, EyeOff } from "lucide-react";

const Input = React.forwardRef(
  ({ label, error, id, type = "text", icon, className = "", ...props }, ref) => {
    const isPassword = type === "password";
    const [showPassword, setShowPassword] = useState(false);

    const inputType = isPassword ? (showPassword ? "text" : "password") : type;

    return (
      <label
        className="grid gap-2 text-sm font-semibold text-slate-900 dark:text-slate-100"
        htmlFor={id}
      >
        {label && <span>{label}</span>}
        <div className="relative w-full">
          {icon && (
            <div className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 flex items-center justify-center text-slate-400">
              {icon}
            </div>
          )}
          <input
            id={id}
            ref={ref}
            type={inputType}
            className={`h-12 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 ${
              icon ? "pl-10" : "px-4"
            } ${
              isPassword ? "pr-11" : ""
            } text-sm font-medium text-slate-800 dark:text-slate-100 outline-none transition-all duration-150 focus:border-primary focus:ring-2 focus:ring-primary/10 disabled:bg-slate-50 dark:disabled:bg-slate-800 disabled:cursor-not-allowed ${
              error
                ? "border-campus-danger focus:border-campus-danger focus:ring-campus-danger/10"
                : ""
            } ${className}`}
            {...props}
          />
          {isPassword && (
            <button
              type="button"
              tabIndex={-1}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                setShowPassword((prev) => !prev);
              }}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 focus:outline-none cursor-pointer transition-colors p-1"
              aria-label={showPassword ? "Hide password" : "Show password"}
              title={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? (
                <EyeOff className="h-4.5 w-4.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200" />
              ) : (
                <Eye className="h-4.5 w-4.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200" />
              )}
            </button>
          )}
        </div>
        {error && (
          <span className="text-xs font-medium text-campus-danger lowercase tracking-normal">
            {error}
          </span>
        )}
      </label>
    );
  },
);

Input.displayName = "Input";
export default Input;
