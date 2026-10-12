import { useEffect, useState } from "react";
import { Award, Trophy, Star, ShieldCheck, Download, ChevronRight } from "lucide-react";
import Card from "./Card.jsx";
import { recognitionService } from "../services/recognitionService.js";
import { useAuth } from "../context/AuthContext.jsx";
import { ROLES } from "../utils/constants.js";

export default function FixerOfTheMonthWidget({ scope = "campus" }) {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showLeaderboard, setShowLeaderboard] = useState(false);

  const isStaff = [
    ROLES.COORDINATOR,
    ROLES.LOCATION_IN_CHARGE,
    ROLES.APP_MANAGER,
    ROLES.ADMINISTRATOR,
  ].includes(user?.role || "");

  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const res = await recognitionService.getFixerOfTheMonth(scope);
        if (active) setData(res.data);
      } catch (err) {
        // Quietly fail for widget
      } finally {
        if (active) setLoading(false);
      }
    }
    load();
    return () => {
      active = false;
    };
  }, [scope]);

  if (loading || !data || !data.winner) return null;

  const winner = data.winner;
  const leaderboard = data.leaderboard || [];

  return (
    <Card className="p-4 bg-gradient-to-br from-amber-500/10 via-amber-500/5 to-transparent border-amber-200/80 dark:border-amber-800/60 relative overflow-hidden">
      <div className="absolute top-2 right-2 opacity-10 dark:opacity-5 pointer-events-none">
        <Trophy className="h-32 w-32 text-amber-500" />
      </div>

      <div className="flex items-start justify-between gap-3 relative z-10 mb-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-xl bg-amber-500 text-white shadow-xs">
            <Trophy className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700 dark:text-amber-400 block">
              Fixer of the Month • {data.month}
            </span>
            <h4 className="text-sm font-black text-slate-900 dark:text-slate-100">
              {winner.name || "Outstanding Coordinator"}
            </h4>
          </div>
        </div>

        {isStaff && (
          <a
            href={`/api/recognitions/certificate?month=${data.month}&coordinator_id=${winner.coordinator_id}`}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-bold text-amber-800 dark:text-amber-300 bg-amber-100/80 dark:bg-amber-950/60 hover:bg-amber-200/80 rounded-lg transition-colors"
            title="Download printable certificate"
          >
            <Download className="h-3 w-3" />
            Certificate
          </a>
        )}
      </div>

      <div className="grid grid-cols-3 gap-2 my-2.5 relative z-10 text-center">
        <div className="bg-white/80 dark:bg-slate-800/80 p-2 rounded-lg border border-amber-200/50 dark:border-amber-900/40">
          <div className="text-sm font-black text-slate-900 dark:text-slate-100">
            {winner.on_time_rate}%
          </div>
          <div className="text-[9px] font-semibold text-slate-500 uppercase">On-Time</div>
        </div>
        <div className="bg-white/80 dark:bg-slate-800/80 p-2 rounded-lg border border-amber-200/50 dark:border-amber-900/40">
          <div className="text-sm font-black text-slate-900 dark:text-slate-100">
            {winner.reopen_free_rate}%
          </div>
          <div className="text-[9px] font-semibold text-slate-500 uppercase">Reopen-Free</div>
        </div>
        <div className="bg-white/80 dark:bg-slate-800/80 p-2 rounded-lg border border-amber-200/50 dark:border-amber-900/40">
          <div className="text-sm font-black text-amber-600 dark:text-amber-400">
            {winner.score}%
          </div>
          <div className="text-[9px] font-semibold text-slate-500 uppercase">Index Score</div>
        </div>
      </div>

      {isStaff && leaderboard.length > 1 && (
        <div className="mt-3 pt-2.5 border-t border-amber-200/60 dark:border-amber-900/40 relative z-10">
          <button
            type="button"
            onClick={() => setShowLeaderboard(!showLeaderboard)}
            className="text-[11px] font-bold text-amber-800 dark:text-amber-300 hover:underline flex items-center justify-between w-full cursor-pointer"
          >
            <span>{showLeaderboard ? "Hide Staff Leaderboard" : "View Staff Leaderboard"}</span>
            <ChevronRight className={`h-3 w-3 transition-transform ${showLeaderboard ? "rotate-90" : ""}`} />
          </button>

          {showLeaderboard && (
            <div className="mt-2 space-y-1.5 max-h-40 overflow-y-auto pr-1">
              {leaderboard.map((rank, i) => (
                <div
                  key={rank.coordinator_id}
                  className={`flex items-center justify-between text-xs p-1.5 rounded-lg ${
                    rank.coordinator_id === winner.coordinator_id
                      ? "bg-amber-100/70 dark:bg-amber-950/40 font-bold text-amber-900 dark:text-amber-200"
                      : "bg-white/60 dark:bg-slate-800/60 text-slate-700 dark:text-slate-300"
                  }`}
                >
                  <span className="flex items-center gap-1.5">
                    <span className="text-[10px] font-mono text-slate-400">#{i + 1}</span>
                    <span>{rank.name}</span>
                  </span>
                  <span className="font-mono text-[11px]">{rank.score}%</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

