import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  Activity,
  AlertTriangle,
  Clock,
  CheckCircle2,
  RefreshCw,
  Search,
  Building,
  Tv,
  ArrowLeft,
  Flame,
} from "lucide-react";
import Card from "../../components/Card.jsx";
import Badge from "../../components/Badge.jsx";
import Loader from "../../components/Loader.jsx";
import PageHeader from "../../components/PageHeader.jsx";
import { analyticsService } from "../../services/analyticsService.js";
import { getApiError } from "../../api/axios.js";

export default function HealthMapPage({ tvModeOverride = false }) {
  const routerLocation = useLocation();
  const navigate = useNavigate();
  const isTvMode = tvModeOverride || routerLocation.pathname === "/health-map/tv";

  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [data, setData] = useState({ summary: {}, locations: [] });
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all"); // "all", "red", "yellow", "green"
  const [search, setSearch] = useState("");
  const [lastUpdated, setLastUpdated] = useState(new Date());

  const loadData = async (isBackground = false) => {
    if (!isBackground) setLoading(true);
    else setRefreshing(true);
    setError("");

    try {
      const res = await analyticsService.getHealthMap();
      setData(res.data || { summary: {}, locations: [] });
      setLastUpdated(new Date());
    } catch (err) {
      setError(getApiError(err, "Failed to load Campus Health Map."));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    // Auto-refresh every 60s
    const timer = setInterval(() => {
      loadData(true);
    }, 60000);
    return () => clearInterval(timer);
  }, []);

  const summary = data.summary || {};
  const locations = data.locations || [];

  const filteredLocations = locations.filter((loc) => {
    if (filter !== "all" && loc.color !== filter) return false;
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      const matchName = loc.location_name?.toLowerCase().includes(q);
      const matchType = loc.location_type?.toLowerCase().includes(q);
      const matchCat = (loc.top_categories || []).some((c) =>
        c.category?.toLowerCase().includes(q)
      );
      if (!matchName && !matchType && !matchCat) return false;
    }
    return true;
  });

  const getStatusColorClass = (color) => {
    switch (color) {
      case "red":
        return "border-rose-400/80 bg-rose-50/70 dark:bg-rose-950/30 text-rose-900 dark:text-rose-100";
      case "yellow":
        return "border-amber-400/80 bg-amber-50/70 dark:bg-amber-950/30 text-amber-900 dark:text-amber-100";
      case "green":
      default:
        return "border-emerald-400/80 bg-emerald-50/70 dark:bg-emerald-950/30 text-emerald-900 dark:text-emerald-100";
    }
  };

  const getBadgeTone = (color) => {
    switch (color) {
      case "red":
        return "danger";
      case "yellow":
        return "warning";
      case "green":
      default:
        return "success";
    }
  };

  // TV Mode Layout
  if (isTvMode) {
    return (
      <div className="min-h-screen bg-slate-950 text-slate-100 p-8 flex flex-col justify-between font-sans select-none">
        {/* TV Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-6">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-primary/20 rounded-2xl border border-primary/40">
              <Activity className="h-10 w-10 text-primary animate-pulse" />
            </div>
            <div>
              <h1 className="text-3xl font-black tracking-tight text-white flex items-center gap-3">
                CAMPUS HEALTH MAP <span className="text-xs px-2.5 py-1 bg-red-600 font-bold rounded-md uppercase tracking-widest">LIVE TV</span>
              </h1>
              <p className="text-sm font-medium text-slate-400 mt-1">
                Real-time facility status across all hostel & academic buildings
              </p>
            </div>
          </div>

          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="px-5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-3">
                <span className="h-3 w-3 rounded-full bg-rose-500 animate-ping" />
                <span className="text-xl font-black text-rose-400">{summary.red_count || 0}</span>
                <span className="text-xs font-bold text-slate-400 uppercase">Attention</span>
              </div>
              <div className="px-5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-3">
                <span className="h-3 w-3 rounded-full bg-amber-500" />
                <span className="text-xl font-black text-amber-400">{summary.yellow_count || 0}</span>
                <span className="text-xs font-bold text-slate-400 uppercase">Warning</span>
              </div>
              <div className="px-5 py-2.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-3">
                <span className="h-3 w-3 rounded-full bg-emerald-500" />
                <span className="text-xl font-black text-emerald-400">{summary.green_count || 0}</span>
                <span className="text-xs font-bold text-slate-400 uppercase">Healthy</span>
              </div>
            </div>

            <div className="text-right">
              <div className="text-2xl font-mono font-bold text-slate-200">
                {lastUpdated.toLocaleTimeString()}
              </div>
              <div className="text-[11px] font-semibold text-slate-500">
                Auto-refreshes every 60s
              </div>
            </div>
          </div>
        </div>

        {/* TV Grid */}
        <div className="my-8 flex-1 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 auto-rows-fr">
          {locations.map((loc) => (
            <div
              key={loc.location_id}
              className={`rounded-2xl border-2 p-6 flex flex-col justify-between transition-all ${
                loc.color === "red"
                  ? "bg-rose-950/40 border-rose-600/80 shadow-lg shadow-rose-950/50"
                  : loc.color === "yellow"
                  ? "bg-amber-950/30 border-amber-500/70 shadow-md shadow-amber-950/40"
                  : "bg-slate-900/90 border-emerald-600/60"
              }`}
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-3">
                  <h2 className="text-xl font-bold tracking-tight text-white truncate">
                    {loc.location_name}
                  </h2>
                  <span
                    className={`px-2.5 py-1 text-xs font-black uppercase rounded-lg ${
                      loc.color === "red"
                        ? "bg-rose-600 text-white"
                        : loc.color === "yellow"
                        ? "bg-amber-500 text-slate-950"
                        : "bg-emerald-600 text-white"
                    }`}
                  >
                    {loc.color === "red" ? "Action Needed" : loc.color === "yellow" ? "Warning" : "Optimal"}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-2 my-4 text-center">
                  <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                    <div className="text-2xl font-black text-white">{loc.open_count}</div>
                    <div className="text-[10px] font-bold text-slate-400 uppercase">Open</div>
                  </div>
                  <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                    <div className={`text-2xl font-black ${loc.overdue_count > 0 ? "text-rose-400" : "text-slate-400"}`}>
                      {loc.overdue_count}
                    </div>
                    <div className="text-[10px] font-bold text-slate-400 uppercase">Overdue</div>
                  </div>
                  <div className="bg-slate-950/60 p-2.5 rounded-xl border border-slate-800">
                    <div className={`text-2xl font-black ${loc.near_deadline_count > 0 ? "text-amber-400" : "text-slate-400"}`}>
                      {loc.near_deadline_count}
                    </div>
                    <div className="text-[10px] font-bold text-slate-400 uppercase">Near SLA</div>
                  </div>
                </div>

                {/* Pattern Alert */}
                {loc.pattern_alerts?.length > 0 && (
                  <div className="mb-3 p-2.5 rounded-xl bg-rose-900/60 border border-rose-500/80 text-rose-200 text-xs font-bold flex items-center gap-2">
                    <Flame className="h-4 w-4 shrink-0 text-rose-400 animate-bounce" />
                    <span className="truncate">{loc.pattern_alerts[0].message}</span>
                  </div>
                )}
              </div>

              {/* Top Categories */}
              <div className="border-t border-slate-800/80 pt-3">
                <div className="text-[11px] font-semibold text-slate-400 mb-1.5 uppercase">
                  Top Issue Areas
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {(loc.top_categories || []).length > 0 ? (
                    loc.top_categories.map((c, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded-md bg-slate-800 border border-slate-700 text-xs font-medium text-slate-300"
                      >
                        {c.category} ({c.count})
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-500 italic">No active issues</span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* TV Footer */}
        <div className="border-t border-slate-800 pt-4 flex items-center justify-between text-xs text-slate-500">
          <span>Campus Pulse Operations & Incident Response System</span>
          <button
            onClick={() => navigate("/health-map")}
            className="hover:text-slate-300 transition-colors"
          >
            Exit TV Mode
          </button>
        </div>
      </div>
    );
  }

  // Standard Interactive View
  return (
    <div className="grid gap-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <Link
            to="/"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to dashboard
          </Link>
          <PageHeader
            title="Campus Health Map"
            description="Live health status of campus facilities. Red cards indicate overdue complaints or high backlog requiring root-cause inspection."
          />
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => loadData(true)}
            disabled={refreshing}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 cursor-pointer shadow-xs transition-all active:scale-95"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${refreshing ? "animate-spin text-primary" : ""}`} />
            Refresh
          </button>
          <Link
            to="/health-map/tv"
            target="_blank"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 text-xs font-bold hover:bg-slate-800 transition-all shadow-xs"
          >
            <Tv className="h-3.5 w-3.5" />
            Launch TV Mode
          </Link>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <Card className="p-4 flex items-center gap-3">
          <div className="p-2.5 bg-slate-100 dark:bg-slate-800 rounded-xl text-slate-600 dark:text-slate-300">
            <Building className="h-5 w-5" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900 dark:text-slate-100">
              {summary.total_locations || locations.length}
            </div>
            <div className="text-xs font-semibold text-slate-500">Monitored Locations</div>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-3 border-rose-200 dark:border-rose-900/60 bg-rose-50/30 dark:bg-rose-950/20">
          <div className="p-2.5 bg-rose-100 dark:bg-rose-900/50 rounded-xl text-rose-600 dark:text-rose-400">
            <AlertTriangle className="h-5 w-5" />
          </div>
          <div>
            <div className="text-2xl font-black text-rose-600 dark:text-rose-400">
              {summary.red_count || 0}
            </div>
            <div className="text-xs font-semibold text-rose-700 dark:text-rose-300">Critical / Overdue</div>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-3 border-amber-200 dark:border-amber-900/60 bg-amber-50/30 dark:bg-amber-950/20">
          <div className="p-2.5 bg-amber-100 dark:bg-amber-900/50 rounded-xl text-amber-600 dark:text-amber-400">
            <Clock className="h-5 w-5" />
          </div>
          <div>
            <div className="text-2xl font-black text-amber-600 dark:text-amber-400">
              {summary.yellow_count || 0}
            </div>
            <div className="text-xs font-semibold text-amber-700 dark:text-amber-300">Near Deadline</div>
          </div>
        </Card>

        <Card className="p-4 flex items-center gap-3 border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/30 dark:bg-emerald-950/20">
          <div className="p-2.5 bg-emerald-100 dark:bg-emerald-900/50 rounded-xl text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="h-5 w-5" />
          </div>
          <div>
            <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
              {summary.green_count || 0}
            </div>
            <div className="text-xs font-semibold text-emerald-700 dark:text-emerald-300">Healthy Buildings</div>
          </div>
        </Card>
      </div>

      {/* Filters & Search */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setFilter("all")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              filter === "all"
                ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900 shadow-xs"
                : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200"
            }`}
          >
            All Buildings ({locations.length})
          </button>
          <button
            onClick={() => setFilter("red")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              filter === "red"
                ? "bg-rose-600 text-white shadow-xs"
                : "bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 hover:bg-rose-100"
            }`}
          >
            🔴 Critical ({summary.red_count || 0})
          </button>
          <button
            onClick={() => setFilter("yellow")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              filter === "yellow"
                ? "bg-amber-500 text-white shadow-xs"
                : "bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 hover:bg-amber-100"
            }`}
          >
            🟡 Warning ({summary.yellow_count || 0})
          </button>
          <button
            onClick={() => setFilter("green")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              filter === "green"
                ? "bg-emerald-600 text-white shadow-xs"
                : "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100"
            }`}
          >
            🟢 Healthy ({summary.green_count || 0})
          </button>
        </div>

        <div className="relative min-w-[220px]">
          <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
          <input
            type="text"
            placeholder="Search building or issue..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8.5 w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 pl-8.5 pr-3 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 outline-none focus:border-primary"
          />
        </div>
      </div>

      {loading ? (
        <Loader label="Evaluating campus facility status..." variant="skeleton" />
      ) : error ? (
        <div className="p-4 rounded-xl border border-rose-300 bg-rose-50 text-rose-800 text-xs font-semibold">
          {error}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredLocations.map((loc) => (
            <Card
              key={loc.location_id}
              className={`p-4 transition-all hover:shadow-md cursor-pointer border-2 ${getStatusColorClass(loc.color)}`}
              onClick={() => navigate(`/complaints?location_id=${loc.location_id}`)}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <div>
                  <h3 className="font-bold text-sm tracking-tight text-slate-900 dark:text-slate-100">
                    {loc.location_name}
                  </h3>
                  <span className="text-[11px] text-slate-500 font-medium">
                    {loc.location_type || "Facility"}
                  </span>
                </div>
                <Badge tone={getBadgeTone(loc.color)}>
                  {loc.color === "red" ? "Critical" : loc.color === "yellow" ? "Warning" : "Healthy"}
                </Badge>
              </div>

              {/* Counts */}
              <div className="grid grid-cols-3 gap-2 my-3 text-center">
                <div className="bg-white/80 dark:bg-slate-800/80 p-2 rounded-lg border border-slate-200/80 dark:border-slate-700">
                  <div className="text-lg font-bold text-slate-900 dark:text-slate-100">{loc.open_count}</div>
                  <div className="text-[9px] font-semibold text-slate-500 uppercase">Open</div>
                </div>
                <div className="bg-white/80 dark:bg-slate-800/80 p-2 rounded-lg border border-slate-200/80 dark:border-slate-700">
                  <div className={`text-lg font-bold ${loc.overdue_count > 0 ? "text-rose-600 dark:text-rose-400" : "text-slate-600"}`}>
                    {loc.overdue_count}
                  </div>
                  <div className="text-[9px] font-semibold text-slate-500 uppercase">Overdue</div>
                </div>
                <div className="bg-white/80 dark:bg-slate-800/80 p-2 rounded-lg border border-slate-200/80 dark:border-slate-700">
                  <div className={`text-lg font-bold ${loc.near_deadline_count > 0 ? "text-amber-600 dark:text-amber-400" : "text-slate-600"}`}>
                    {loc.near_deadline_count}
                  </div>
                  <div className="text-[9px] font-semibold text-slate-500 uppercase">Near SLA</div>
                </div>
              </div>

              {/* Pattern Alerts */}
              {loc.pattern_alerts?.length > 0 && (
                <div className="mb-3 p-2 rounded-lg bg-rose-100/80 dark:bg-rose-950/60 border border-rose-300 dark:border-rose-900 text-rose-900 dark:text-rose-200 text-[11px] font-semibold flex items-center gap-1.5">
                  <Flame className="h-3.5 w-3.5 text-rose-600 shrink-0" />
                  <span className="truncate">{loc.pattern_alerts[0].message}</span>
                </div>
              )}

              {/* Top Categories */}
              <div className="border-t border-slate-200/60 dark:border-slate-700/60 pt-2.5">
                <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">
                  Frequent Issues
                </div>
                <div className="flex flex-wrap gap-1">
                  {(loc.top_categories || []).length > 0 ? (
                    loc.top_categories.map((c, idx) => (
                      <span
                        key={idx}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 font-medium text-slate-700 dark:text-slate-300"
                      >
                        {c.category}: <strong>{c.count}</strong>
                      </span>
                    ))
                  ) : (
                    <span className="text-[10px] text-slate-400 italic">No open issues</span>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

