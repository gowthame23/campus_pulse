import { motion } from "framer-motion";

export default function Card({ children, className = "", hoverable = false, onClick, ...props }) {
  const isInteractive = hoverable || !!onClick;

  return (
    <motion.section
      onClick={onClick}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      whileHover={isInteractive ? { y: -3, boxShadow: "0 10px 24px -8px rgba(15, 23, 42, 0.12)" } : undefined}
      whileTap={isInteractive ? { scale: 0.995 } : undefined}
      className={`rounded-xl border border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-[#101726] p-5 sm:p-6 shadow-2xs text-slate-900 dark:text-slate-100 transition-colors ${isInteractive ? "cursor-pointer hover:border-slate-300 dark:hover:border-slate-700" : ""} ${className}`}
      {...props}
    >
      {children}
    </motion.section>
  );
}
