export default function Card({ children, className = "", hoverable = false, onClick, ...props }) {
  const hoverClass = hoverable || onClick
    ? "hover:border-slate-300 dark:hover:border-slate-700 hover:shadow-xs transition-all duration-150 cursor-pointer"
    : "";

  return (
    <section
      onClick={onClick}
      className={`rounded-xl border border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-[#101726] p-5 sm:p-6 shadow-2xs text-slate-900 dark:text-slate-100 ${hoverClass} ${className}`}
      {...props}
    >
      {children}
    </section>
  );
}
