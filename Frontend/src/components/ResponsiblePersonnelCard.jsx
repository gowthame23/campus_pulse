import { User, Mail, Shield, Building, MapPin, Users, Wrench } from "lucide-react";
import Card from "./Card.jsx";

export default function ResponsiblePersonnelCard({
  complaint,
  location,
  coordinatorUser,
  wardenUser,
}) {
  if (!complaint) return null;

  const assignedEmpName =
    complaint.assigned_employee_name ||
    complaint.assigned_to_name ||
    (complaint.assigned_to && !complaint.assigned_to.includes("@") ? complaint.assigned_to : null);
  const isUnassigned =
    !assignedEmpName ||
    assignedEmpName === "Awaiting assignment" ||
    !complaint.assigned_to;

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
    location?.in_charge_name ||
    null;
  const wardenEmail =
    wardenUser?.email ||
    location?.in_charge_email ||
    null;

  const teamName = complaint.team_name || null;
  const deptName = complaint.department_name || null;
  const locName = location?.name || complaint.location_name || complaint.location_id;

  return (
    <Card>
      <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3.5 flex items-center gap-2">
        <User className="h-4 w-4 text-primary" />
        Responsible Personnel & Assignments
      </h2>

      <div className="space-y-3.5 text-xs">
        {/* Assigned Employee / Field Worker */}
        <div className="pb-3 border-b border-slate-100 dark:border-slate-800/80">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              Assigned Field Employee
            </span>
            <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
              isUnassigned
                ? "bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800"
                : "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300"
            }`}>
              {isUnassigned ? "Action Required" : "Assigned"}
            </span>
          </div>
          {!isUnassigned ? (
            <div className="mt-1">
              <div className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                <Wrench className="h-3.5 w-3.5 text-primary" />
                {assignedEmpName}
              </div>
              <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                Designated Field Technician
              </div>
            </div>
          ) : (
            <div className="mt-1 flex items-center gap-1.5 text-amber-600 dark:text-amber-400 font-semibold italic">
              <span>⚠️</span>
              <span>Awaiting assignment</span>
            </div>
          )}
        </div>

        {/* Responsible Department & Location */}
        <div className="pb-3 border-b border-slate-100 dark:border-slate-800/80">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              Department & Location
            </span>
            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
              Operational Scope
            </span>
          </div>
          <div className="mt-1 space-y-1">
            {deptName && (
              <div className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                <Building className="h-3.5 w-3.5 text-primary" />
                {deptName}
              </div>
            )}
            {locName && (
              <div className="text-[11px] text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5 text-slate-400" />
                {locName}
              </div>
            )}
          </div>
        </div>

        {/* Assigned Coordinator */}
        <div className="pb-3 border-b border-slate-100 dark:border-slate-800/80">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              Responsible Coordinator
            </span>
            <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300">
              Dispatch & Oversight
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
              Location Warden
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
                {locName}
              </div>
            </div>
          ) : (
            <div className="mt-1 text-slate-400 dark:text-slate-500 italic">
              No Warden assigned to {locName}
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
