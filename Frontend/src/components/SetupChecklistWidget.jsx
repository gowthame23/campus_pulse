import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  CheckCircle2,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Users,
  MapPin,
  Layers,
  Phone,
  ShieldAlert,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import Card from "./Card.jsx";
import Button from "./Button.jsx";
import { setupService } from "../services/setupService.js";

export default function SetupChecklistWidget() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    loadChecklist();
  }, []);

  const loadChecklist = async () => {
    try {
      const res = await setupService.getChecklist();
      setData(res);
      // Auto-collapse if already completely ready
      if (res?.is_complete) {
        setCollapsed(true);
      }
    } catch (err) {
      console.error("Failed to load setup checklist:", err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data) return null;
  if (!data) return null;

  const {
    is_complete,
    students,
    locations,
    uncovered_places,
    teams_no_backup,
    locations_no_warden,
    staff_no_phone,
    departments_few_emergency_contacts,
  } = data;

  const items = [
    {
      id: "students",
      label: `Students imported (${students?.count || 0})`,
      done: students?.is_ready,
      fixLink: students?.link || "/admin/users",
      fixLabel: "Import Students",
      desc: students?.is_ready ? `${students.count} students active` : "No students imported yet",
    },
    {
      id: "locations",
      label: `Locations added (${locations?.count || 0})`,
      done: locations?.is_ready,
      fixLink: locations?.link || "/admin/locations",
      fixLabel: "Add Locations",
      desc: locations?.is_ready ? `${locations.count} campus locations active` : "No locations registered",
    },
    {
      id: "coverage",
      label: `Departments / places with no team (${uncovered_places?.count || 0})`,
      done: uncovered_places?.is_ready,
      fixLink: uncovered_places?.link || "/admin/teams",
      fixLabel: "Fix in Teams",
      desc: uncovered_places?.is_ready
        ? "All department and location pairs have assigned teams"
        : `${uncovered_places?.count} uncovered location/department pairs`,
    },
    {
      id: "backups",
      label: `Teams with no backup (${teams_no_backup?.count || 0})`,
      done: teams_no_backup?.is_ready,
      fixLink: teams_no_backup?.link || "/admin/teams",
      fixLabel: "Assign Backups",
      desc: teams_no_backup?.is_ready
        ? "All active teams have assigned backup coordinators"
        : `${teams_no_backup?.count} teams lack a backup coordinator`,
    },
    {
      id: "wardens",
      label: `Locations with no Warden (${locations_no_warden?.count || 0})`,
      done: locations_no_warden?.is_ready,
      fixLink: locations_no_warden?.link || "/admin/locations",
      fixLabel: "Assign Wardens",
      desc: locations_no_warden?.is_ready
        ? "All locations have appointed Wardens"
        : `${locations_no_warden?.count} locations currently have no Warden`,
    },
    {
      id: "phones",
      label: `Coordinators / Wardens without phone number (${staff_no_phone?.count || 0})`,
      done: staff_no_phone?.is_ready,
      fixLink: staff_no_phone?.link || "/admin/users",
      fixLabel: "Add Phones",
      desc: staff_no_phone?.is_ready
        ? "All key staff have verified mobile numbers for emergencies"
        : `${staff_no_phone?.count} coordinators or wardens missing phone number`,
    },
    {
      id: "emergency",
      label: `Departments with < 2 emergency contacts (${departments_few_emergency_contacts?.count || 0})`,
      done: departments_few_emergency_contacts?.is_ready,
      fixLink: departments_few_emergency_contacts?.link || "/admin/emergency",
      fixLabel: "Add Contacts",
      desc: departments_few_emergency_contacts?.is_ready
        ? "All departments have at least 2 emergency call contacts"
        : `${departments_few_emergency_contacts?.count} departments need more emergency contacts`,
    },
  ];

  const completedCount = items.filter((i) => i.done).length;

  return (
    <Card className="border-2 border-slate-200 dark:border-slate-800 shadow-sm transition-all duration-200">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className={`flex h-8 w-8 items-center justify-center rounded-xl font-bold text-sm ${
            is_complete
              ? "bg-emerald-500 text-white"
              : "bg-blue-600 text-white"
          }`}>
            {is_complete ? "✓" : "⚡"}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                College Setup
              </h3>
              {is_complete && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">
                  <CheckCircle2 className="h-3 w-3" /> Setup complete — ready to use
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500">
              {is_complete
                ? "All onboarding checklist milestones achieved"
                : `${completedCount} of ${items.length} setup requirements fulfilled`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={loadChecklist}
            className="p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded"
            title="Refresh setup checklist"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setCollapsed((prev) => !prev)}
            className="!h-7 text-xs font-semibold flex items-center gap-1"
          >
            {collapsed ? (
              <>
                Expand Checklist <ChevronDown className="h-3.5 w-3.5 ml-0.5" />
              </>
            ) : (
              <>
                Collapse <ChevronUp className="h-3.5 w-3.5 ml-0.5" />
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Expanded Checklist Body */}
      {!collapsed && (
        <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800 space-y-2.5">
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((item) => (
              <div
                key={item.id}
                className={`p-3 rounded-xl border text-xs flex flex-col justify-between transition-colors ${
                  item.done
                    ? "border-emerald-200/80 dark:border-emerald-900/60 bg-emerald-50/40 dark:bg-emerald-950/20 text-slate-700 dark:text-slate-300"
                    : "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200"
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-start gap-2">
                    <span className="shrink-0 mt-0.5">
                      {item.done ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                      ) : (
                        <div className="h-4 w-4 rounded-full border-2 border-slate-300 dark:border-slate-600 flex items-center justify-center" />
                      )}
                    </span>
                    <span className="font-bold leading-tight">{item.label}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 pl-6">{item.desc}</p>
                </div>

                {!item.done && (
                  <div className="pt-2 pl-6 flex justify-end">
                    <Link
                      to={item.fixLink}
                      className="inline-flex items-center gap-1 text-[11px] font-bold text-primary hover:underline"
                    >
                      Fix <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}

