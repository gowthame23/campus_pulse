import { User, Mail, Shield, Building, MapPin } from "lucide-react";
import Card from "./Card.jsx";

export default function ResponsiblePersonnelCard({
  complaint,
  location,
  coordinatorUser,
  wardenUser,
}) {
  if (!complaint) return null;

  const coordName =
    coordinatorUser?.name ||
    complaint.coordinator_name ||
    complaint.assigned_to ||
    null;
  const coordEmail =
    coordinatorUser?.email ||
    complaint.coordinator_email ||
    (complaint.assigned_to && complaint.assigned_to.includes("@") ? complaint.assigned_to : null);

  const wardenName =
    wardenUser?.name ||
    location?.in_charge_name ||
    null;
  const wardenEmail =
    wardenUser?.email ||
    location?.in_charge_email ||
    null;

  return (
    <Card>
      <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3.5 flex items-center gap-2">
        <User className="h-4 w-4 text-primary" />
        Responsible Personnel & Assignments
      </h2>

      <div className="space-y-3.5 text-xs">
        {/* Assigned Coordinator */}
        <div className="pb-3 border-b border-slate-100 dark:border-slate-800/80">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              Assigned Coordinator
            </span>
            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300">
              Field Execution
            </span>
          </div>
          {coordName ? (
            <div className="mt-1">
              <div className="font-semibold text-slate-900 dark:text-slate-100">
                {coordName}
              </div>
              <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1 mt-0.5 font-mono">
                <Mail className="h-3 w-3 text-slate-400" />
                {coordEmail || "Email on campus record"}
              </div>
            </div>
          ) : (
            <div className="mt-1 text-amber-600 dark:text-amber-400 font-medium italic">
              Unassigned — Available in department intake queue
            </div>
          )}
        </div>

        {/* Warden of Location */}
        <div className="pb-3 border-b border-slate-100 dark:border-slate-800/80">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              Location In-Charge (Warden)
            </span>
            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300">
              Verification Authority
            </span>
          </div>
          {wardenName ? (
            <div className="mt-1">
              <div className="font-semibold text-slate-900 dark:text-slate-100">
                {wardenName}
              </div>
              <div className="text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1 mt-0.5 font-mono">
                <Mail className="h-3 w-3 text-slate-400" />
                {wardenEmail || "Email on campus record"}
              </div>
              <div className="text-[10px] text-slate-400 dark:text-slate-500 flex items-center gap-1 mt-0.5">
                <MapPin className="h-3 w-3" />
                {location?.name || complaint.location_name || complaint.location_id}
              </div>
            </div>
          ) : (
            <div className="mt-1 text-slate-400 dark:text-slate-500 italic">
              No Warden assigned to this location
            </div>
          )}
        </div>

        {/* Reporting Student */}
        <div className="flex items-start justify-between gap-2 pt-1">
          <span className="text-slate-400 dark:text-slate-500 font-medium">
            Reported By:
          </span>
          <span className="font-semibold text-slate-800 dark:text-slate-200 text-right">
            {complaint.student_name || complaint.created_by || "Student"}
          </span>
        </div>

        {/* Reopen Counter */}
        <div className="flex items-center justify-between gap-2 pt-1 border-t border-slate-100 dark:border-slate-800/80">
          <span className="text-slate-400 dark:text-slate-500 font-medium">
            Reopen Cycles:
          </span>
          <span className={`font-bold font-mono ${complaint.reopen_count >= 3 ? "text-rose-600 dark:text-rose-400" : "text-slate-800 dark:text-slate-200"}`}>
            {complaint.reopen_count || 0} / 3 maximum
          </span>
        </div>
      </div>
    </Card>
  );
}
