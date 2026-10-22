import { User, Mail } from "lucide-react";
import Card from "./Card.jsx";

export default function ResponsiblePersonnelCard({
  complaint,
  coordinatorUser,
  wardenUser,
}) {
  if (!complaint) return null;

  const coordName =
    coordinatorUser?.name ||
    complaint.assigned_coordinator_name ||
    complaint.coordinator_name ||
    null;
  const coordEmail =
    coordinatorUser?.email ||
    complaint.coordinator_email ||
    null;

  const wardenName =
    wardenUser?.name ||
    complaint.location_in_charge_name ||
    null;
  const wardenEmail =
    wardenUser?.email ||
    null;

  return (
    <Card>
      <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3 flex items-center gap-2">
        <User className="h-4 w-4 text-primary" />
        Assigned Staff
      </h2>

      <div className="space-y-2 text-xs">
        {/* Coordinator */}
        <div className="flex items-center justify-between gap-2 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-100 dark:border-slate-800">
          <div className="min-w-0">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Department Coordinator
            </span>
            <div className="font-semibold text-slate-900 dark:text-slate-100 truncate mt-0.5">
              {coordName || <span className="text-amber-500 italic font-normal">Unassigned</span>}
            </div>
          </div>
          {coordEmail && (
            <span className="text-[11px] text-slate-400 font-mono shrink-0 truncate max-w-[140px]">
              {coordEmail}
            </span>
          )}
        </div>

        {/* Warden */}
        <div className="flex items-center justify-between gap-2 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-100 dark:border-slate-800">
          <div className="min-w-0">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
              Location Warden
            </span>
            <div className="font-semibold text-slate-900 dark:text-slate-100 truncate mt-0.5">
              {wardenName || <span className="text-slate-400 italic font-normal">None Assigned</span>}
            </div>
          </div>
          {wardenEmail && (
            <span className="text-[11px] text-slate-400 font-mono shrink-0 truncate max-w-[140px]">
              {wardenEmail}
            </span>
          )}
        </div>

        {/* Reopen counter if complaint was reopened */}
        {complaint.reopen_count > 0 && (
          <div className="flex items-center justify-between text-[11px] pt-1 text-slate-500">
            <span>Reopen Cycles:</span>
            <span className="font-bold text-rose-600">{complaint.reopen_count} / 3</span>
          </div>
        )}
      </div>
    </Card>
  );
}
