export default function Loader({ label = "Loading", variant = "spinner" }) {
  if (variant === "skeleton") {
    return (
      <div className="grid gap-4 w-full" aria-label={label}>
        <div className="h-12 animate-pulse rounded-xl bg-slate-200/80 w-1/3" />
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="h-28 animate-pulse rounded-xl bg-slate-200/80" />
          <div className="h-28 animate-pulse rounded-xl bg-slate-200/80" />
          <div className="h-28 animate-pulse rounded-xl bg-slate-200/80" />
          <div className="h-28 animate-pulse rounded-xl bg-slate-200/80" />
        </div>
        <div className="h-64 animate-pulse rounded-xl bg-slate-200/80" />
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center p-6" role="status">
      <div className="inline-flex items-center gap-3 rounded-xl border border-slate-200/80 bg-white px-5 py-3 shadow-md">
        <span className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-primary" />
        <span className="text-sm font-semibold text-slate-700">{label}...</span>
      </div>
    </div>
  );
}
