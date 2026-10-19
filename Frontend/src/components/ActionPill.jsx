import React from "react";
import { Link } from "react-router-dom";

/**
 * ActionPill Component
 * 
 * Shape: wide and short (height 44-48px, never < 44px for touch), fully rounded corners (pill).
 * Content: left to right -> icon (20px) -> label (one line, truncated) -> optional count badge (hidden when 0).
 * Accessible: real <button> or <Link>, label readable by screen readers.
 */
export default function ActionPill({
  icon: Icon,
  label,
  count = 0,
  to,
  onClick,
  tone = "blue",
  active = false,
  className = "",
  ariaLabel,
  ...props
}) {
  const tones = {
    blue: {
      base: "bg-blue-50/80 dark:bg-blue-950/30 text-blue-700 dark:text-blue-300 border-blue-200/80 dark:border-blue-800/60 hover:bg-blue-100/80 dark:hover:bg-blue-900/40",
      active: "ring-2 ring-blue-500 bg-blue-100/90 dark:bg-blue-900/50",
      icon: "text-blue-600 dark:text-blue-400",
      badge: "bg-blue-600 text-white dark:bg-blue-500",
    },
    amber: {
      base: "bg-amber-50/80 dark:bg-amber-950/30 text-amber-800 dark:text-amber-300 border-amber-200/80 dark:border-amber-800/60 hover:bg-amber-100/80 dark:hover:bg-amber-900/40",
      active: "ring-2 ring-amber-500 bg-amber-100/90 dark:bg-amber-900/50",
      icon: "text-amber-600 dark:text-amber-400",
      badge: "bg-amber-600 text-white dark:bg-amber-500",
    },
    purple: {
      base: "bg-purple-50/80 dark:bg-purple-950/30 text-purple-800 dark:text-purple-300 border-purple-200/80 dark:border-purple-800/60 hover:bg-purple-100/80 dark:hover:bg-purple-900/40",
      active: "ring-2 ring-purple-500 bg-purple-100/90 dark:bg-purple-900/50",
      icon: "text-purple-600 dark:text-purple-400",
      badge: "bg-purple-600 text-white dark:bg-purple-500",
    },
    indigo: {
      base: "bg-indigo-50/80 dark:bg-indigo-950/30 text-indigo-800 dark:text-indigo-300 border-indigo-200/80 dark:border-indigo-800/60 hover:bg-indigo-100/80 dark:hover:bg-indigo-900/40",
      active: "ring-2 ring-indigo-500 bg-indigo-100/90 dark:bg-indigo-900/50",
      icon: "text-indigo-600 dark:text-indigo-400",
      badge: "bg-indigo-600 text-white dark:bg-indigo-500",
    },
    emerald: {
      base: "bg-emerald-50/80 dark:bg-emerald-950/30 text-emerald-800 dark:text-emerald-300 border-emerald-200/80 dark:border-emerald-800/60 hover:bg-emerald-100/80 dark:hover:bg-emerald-900/40",
      active: "ring-2 ring-emerald-500 bg-emerald-100/90 dark:bg-emerald-900/50",
      icon: "text-emerald-600 dark:text-emerald-400",
      badge: "bg-emerald-600 text-white dark:bg-emerald-500",
    },
    rose: {
      base: "bg-rose-50/80 dark:bg-rose-950/30 text-rose-800 dark:text-rose-300 border-rose-200/80 dark:border-rose-800/60 hover:bg-rose-100/80 dark:hover:bg-rose-900/40",
      active: "ring-2 ring-rose-500 bg-rose-100/90 dark:bg-rose-900/50",
      icon: "text-rose-600 dark:text-rose-400",
      badge: "bg-rose-600 text-white dark:bg-rose-500",
    },
    slate: {
      base: "bg-slate-50 dark:bg-slate-800/60 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-700/80 hover:bg-slate-100 dark:hover:bg-slate-800",
      active: "ring-2 ring-slate-500 bg-slate-100 dark:bg-slate-800",
      icon: "text-slate-600 dark:text-slate-400",
      badge: "bg-slate-700 text-white dark:bg-slate-600",
    },
  };

  const selectedTone = tones[tone] || tones.blue;

  const baseClasses = `
    group relative inline-flex items-center justify-between w-full h-[46px] min-h-[44px] max-h-[48px]
    px-3 sm:px-4 rounded-full border text-xs sm:text-sm font-semibold tracking-tight
    transition-all duration-150 select-none cursor-pointer
    active:scale-[0.98]
    focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-slate-900
    ${selectedTone.base}
    ${active ? selectedTone.active : ""}
    ${className}
  `.trim();

  const numCount = Number(count) || 0;
  const showBadge = numCount > 0;
  const accessibleLabel = ariaLabel || (showBadge ? `${label} (${numCount})` : label);

  const innerContent = (
    <>
      <div className="flex items-center gap-2 sm:gap-2.5 min-w-0 flex-1 mr-1">
        {Icon && (
          <span className={`inline-flex shrink-0 ${selectedTone.icon}`}>
            <Icon className="h-5 w-5" aria-hidden="true" />
          </span>
        )}
        <span className="truncate text-left leading-tight">
          {label}
        </span>
      </div>

      {showBadge && (
        <span
          data-testid="pill-badge"
          className={`shrink-0 min-w-[20px] h-5 px-1.5 rounded-full text-[11px] font-bold flex items-center justify-center leading-none shadow-2xs ${selectedTone.badge}`}
          aria-hidden="true"
        >
          {numCount > 99 ? "99+" : numCount}
        </span>
      )}
    </>
  );

  if (to) {
    return (
      <Link
        to={to}
        className={baseClasses}
        aria-label={accessibleLabel}
        {...props}
      >
        {innerContent}
      </Link>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className={baseClasses}
      aria-label={accessibleLabel}
      {...props}
    >
      {innerContent}
    </button>
  );
}

