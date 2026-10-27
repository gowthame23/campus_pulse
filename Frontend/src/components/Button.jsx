import { motion } from "framer-motion";

export default function Button({
  children,
  className = "",
  type = "button",
  variant = "primary",
  size = "md",
  leftIcon,
  rightIcon,
  disabled,
  ...props
}) {
  const variants = {
    primary:
      "bg-primary text-white hover:bg-primary-hover active:bg-primary-hover/90 shadow-2xs hover:shadow-md",
    secondary:
      "bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-100 hover:bg-slate-200 dark:hover:bg-slate-700/80 active:bg-slate-300 dark:active:bg-slate-700 border border-slate-200/80 dark:border-slate-700/60 shadow-2xs",
    outline:
      "border border-slate-200 dark:border-slate-700 bg-transparent text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800/60 active:bg-slate-100 dark:active:bg-slate-800",
    subtle:
      "bg-slate-100/90 dark:bg-slate-800/80 text-slate-700 dark:text-slate-200 hover:bg-slate-200/80 dark:hover:bg-slate-700 active:bg-slate-200 dark:active:bg-slate-600",
    ghost:
      "bg-transparent text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800/80 hover:text-slate-900 dark:hover:text-slate-100",
    success:
      "bg-emerald-600 text-white hover:bg-emerald-700 active:bg-emerald-800 shadow-2xs hover:shadow-md",
    warning:
      "bg-amber-600 text-white hover:bg-amber-700 active:bg-amber-800 shadow-2xs hover:shadow-md",
    danger:
      "bg-rose-600 text-white hover:bg-rose-700 active:bg-rose-800 shadow-2xs hover:shadow-md",
    destructive:
      "bg-rose-600 text-white hover:bg-rose-700 active:bg-rose-800 shadow-2xs hover:shadow-md",
  };

  const sizes = {
    xs: "h-7 px-2 text-[11px] font-semibold gap-1",
    sm: "h-8.5 px-3 text-xs gap-1.5",
    md: "h-10 px-4 text-xs font-semibold gap-2",
    lg: "h-11 px-5 text-sm font-semibold gap-2.5",
  };

  return (
    <motion.button
      type={type}
      disabled={disabled}
      whileHover={disabled ? undefined : { y: -1 }}
      whileTap={disabled ? undefined : { scale: 0.96 }}
      transition={{ type: "spring", stiffness: 500, damping: 30 }}
      className={`inline-flex items-center justify-center font-medium rounded-xl transition-colors duration-150 cursor-pointer disabled:cursor-not-allowed disabled:opacity-40 disabled:pointer-events-none select-none ${variants[variant] || variants.primary} ${sizes[size] || sizes.md} ${className}`}
      {...props}
    >
      {leftIcon && <span className="inline-flex shrink-0">{leftIcon}</span>}
      {children}
      {rightIcon && <span className="inline-flex shrink-0">{rightIcon}</span>}
    </motion.button>
  );
}
