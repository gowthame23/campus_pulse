import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Building,
  Layers,
  UserX,
  ShieldAlert,
  ArrowRight,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import { teamService } from "../../services/teamService.js";

export default function CoverageGapsPage() {
  const navigate = useNavigate();
  const [gaps, setGaps] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadGaps();
  }, []);

  const loadGaps = async () => {
    setLoading(true);
    setError("");
    try {
      const res = await teamService.getCoverageGaps();
      setGaps(res.data || res || {});
    } catch (err) {
      setError("Failed to load coverage gaps.");
    } finally {
      setLoading(false);
    }
  };

  const uncoveredPairs = gaps?.uncovered_pairs || [];
  const noBackupTeams = gaps?.teams_without_backup || [];
  const inactiveCoordTeams = gaps?.teams_with_inactive_coordinator || [];
  const noWardenLocations = gaps?.locations_without_warden || [];

  const totalGaps =
    uncoveredPairs.length +
    noBackupTeams.length +
    inactiveCoordTeams.length +
    noWardenLocations.length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <AlertTriangle className="h-6 w-6 text-amber-500" />
            Coverage Gaps
          </h1>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            Rule C8 operational audits: departments lacking coordinators, teams lacking backups, inactive coordinators, and warden vacancies.
          </p>
        </div>

        <Button variant="ghost" onClick={loadGaps} className="p-2 self-start sm:self-auto" title="Refresh">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      {error && (
        <div className="p-3 text-sm bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 rounded-lg border border-rose-200">
          {error}
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-sm text-slate-500">Checking coverage across all campus departments and locations...</div>
      ) : totalGaps === 0 ? (
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-12 text-center border border-slate-200 dark:border-slate-800 shadow-sm">
          <CheckCircle2 className="h-12 w-12 text-emerald-500 mx-auto mb-3" />
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100">
            Full Operational Coverage!
          </h2>
          <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">
            All campus departments are covered by active coordinators, every team has a backup coordinator, all coordinators are active, and all locations have assigned wardens.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* 1. Uncovered Campus Departments */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Layers className="h-4 w-4 text-rose-500" />
                <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Departments Without Coordinator ({uncoveredPairs.length})
                </h2>
              </div>
              <span className="text-xs text-rose-600 font-semibold">Critical Gap</span>
            </div>

            {uncoveredPairs.length === 0 ? (
              <p className="text-xs text-emerald-600 font-medium">All campus departments have assigned coordinators.</p>
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {uncoveredPairs.map((p, idx) => (
                  <div key={idx} className="py-3 flex items-center justify-between gap-3 text-xs">
                    <div>
                      <span className="font-bold text-slate-900 dark:text-slate-100">{p.department_name}</span>
                      <span className="text-slate-400 mx-2">—</span>
                      <span className="font-medium text-slate-500 dark:text-slate-400">Campus-wide Department (No coordinator appointed)</span>
                    </div>
                    <Button
                      size="sm"
                      variant="primary"
                      onClick={() => navigate("/admin/departments")}
                      className="text-xs font-semibold py-1 px-3 flex items-center gap-1"
                    >
                      Fix: Assign Coordinator
                      <ArrowRight className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 2. Teams Whose Coordinator Is Deactivated */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <UserX className="h-4 w-4 text-rose-500" />
                <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Teams with Inactive Coordinator ({inactiveCoordTeams.length})
                </h2>
              </div>
              <span className="text-xs text-rose-600 font-semibold">Action Required</span>
            </div>

            {inactiveCoordTeams.length === 0 ? (
              <p className="text-xs text-emerald-600 font-medium">All team coordinators are active.</p>
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {inactiveCoordTeams.map((t) => (
                  <div key={t.team_id} className="py-3 flex items-center justify-between gap-3 text-xs">
                    <div>
                      <div className="font-bold text-slate-900 dark:text-slate-100">{t.name}</div>
                      <div className="text-slate-500">Coordinator ID: {t.coordinator_id} is inactive / disabled</div>
                    </div>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => navigate("/admin/teams")}
                      className="text-xs font-semibold py-1 px-3 flex items-center gap-1"
                    >
                      Fix: Replace Coordinator
                      <ArrowRight className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 3. Teams with No Backup Coordinator */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-amber-500" />
                <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Teams with No Backup Coordinator ({noBackupTeams.length})
                </h2>
              </div>
              <span className="text-xs text-amber-600 font-semibold">Warning</span>
            </div>

            {noBackupTeams.length === 0 ? (
              <p className="text-xs text-emerald-600 font-medium">All teams have backup coordinators configured.</p>
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {noBackupTeams.map((t) => (
                  <div key={t.team_id} className="py-3 flex items-center justify-between gap-3 text-xs">
                    <div>
                      <div className="font-bold text-slate-900 dark:text-slate-100">{t.name}</div>
                      <div className="text-slate-500">If coordinator takes leave, complaints will escalate directly to Warden/Manager.</div>
                    </div>
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => navigate("/admin/teams")}
                      className="text-xs font-semibold py-1 px-3 flex items-center gap-1"
                    >
                      Fix: Assign Backup
                      <ArrowRight className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* 4. Locations with No Warden */}
          <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <Building className="h-4 w-4 text-indigo-500" />
                <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">
                  Locations Without Warden ({noWardenLocations.length})
                </h2>
              </div>
              <span className="text-xs text-indigo-600 font-semibold">Setup Gap</span>
            </div>

            {noWardenLocations.length === 0 ? (
              <p className="text-xs text-emerald-600 font-medium">All active locations have wardens assigned.</p>
            ) : (
              <div className="divide-y divide-slate-100 dark:divide-slate-800">
                {noWardenLocations.map((loc) => (
                  <div key={loc.location_id} className="py-3 flex items-center justify-between gap-3 text-xs">
                    <div>
                      <div className="font-bold text-slate-900 dark:text-slate-100">{loc.location_name}</div>
                      <div className="text-slate-500">No in-charge supervisor assigned.</div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => navigate("/admin/locations")}
                      className="text-xs font-semibold py-1 px-3 flex items-center gap-1"
                    >
                      Fix: Assign Warden
                      <ArrowRight className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

