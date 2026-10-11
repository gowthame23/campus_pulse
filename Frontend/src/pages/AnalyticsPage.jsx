import { useState, useMemo, useEffect } from "react";
import {
  Download,
  BarChart3,
  Clock,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
  Filter,
  Shield,
  Award,
  Building,
  UserCheck,
} from "lucide-react";
import Button from "../components/Button.jsx";
import Card from "../components/Card.jsx";
import Loader from "../components/Loader.jsx";
import PageHeader from "../components/PageHeader.jsx";
import StatCard from "../components/StatCard.jsx";
import DashboardChart from "../components/DashboardChart.jsx";
import Toast from "../components/Toast.jsx";
import { useAsyncData } from "../hooks/useAsyncData.js";
import { analyticsService } from "../services/analyticsService.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function AnalyticsPage() {
  const { user } = useAuth();
  const isStaffAdmin = [
    "administrator",
    "app_manager",
    "coordinator",
    "location_in_charge",
  ].includes(user?.role);
  const [reportType, setReportType] = useState("complaints");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [exportError, setExportError] = useState("");

  const [dashboardData, setDashboardData] = useState(null);
  const [deptData, setDeptData] = useState([]);
  const [coordData, setCoordData] = useState([]);
  const [hostelData, setHostelData] = useState([]);
  const [slaData, setSlaData] = useState(null);

  const {
    data: analytics,
    loading,
    error,
    reload,
  } = useAsyncData(
    async () =>
      (
        await analyticsService.getComplaints({
          date_from: dateFrom,
          date_to: dateTo,
          department_id: departmentId,
        })
      ).data,
    [dateFrom, dateTo, departmentId],
  );

  useEffect(() => {
    analyticsService
      .getDashboard()
      .then((res) => setDashboardData(res.data))
      .catch(() => {});
    analyticsService
      .getDepartments()
      .then((res) => setDeptData(res.data))
      .catch(() => {});
    analyticsService
      .getCoordinators()
      .then((res) => setCoordData(res.data))
      .catch(() => {});
    analyticsService
      .getHostels()
      .then((res) => setHostelData(res.data))
      .catch(() => {});
    analyticsService
      .getSla()
      .then((res) => setSlaData(res.data))
      .catch(() => {});
  }, [dateFrom, dateTo, departmentId]);

  const handleExport = async (type) => {
    try {
      const response = await analyticsService.exportReport(type, "csv", {
        date_from: dateFrom,
        date_to: dateTo,
        department_id: departmentId,
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        `${type}_report_${new Date().toISOString().slice(0, 10)}.csv`,
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      setExportError("Failed to export report CSV. Please try again.");
    }
  };

  const deptChartData = useMemo(() => {
    return (deptData || []).map((d) => ({
      name: d.department_name,
      value: d.assigned_complaints,
    }));
  }, [deptData]);

  const statusEntries = useMemo(
    () => Object.entries(analytics?.by_status || {}),
    [analytics],
  );
  const priorityEntries = useMemo(
    () => Object.entries(analytics?.by_priority || {}),
    [analytics],
  );

  if (loading && !analytics)
    return (
      <Loader label="Computing real-time analytics..." variant="skeleton" />
    );

  return (
    <div className="grid gap-6">
      <Toast
        message={exportError}
        tone="danger"
        onClose={() => setExportError("")}
      />
      {error && (
        <Toast
          message="Failed to load analytics data. Please refresh."
          tone="danger"
          onClose={() => {}}
        />
      )}
      <PageHeader
        title="Analytics & Executive Intelligence"
        description="Real-time KPI metrics, SLA performance tracking, coordinator rankings, and exportable reports."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="subtle"
              size="sm"
              onClick={reload}
              className="h-9 font-semibold"
            >
              <RefreshCw className="h-4 w-4 mr-1 shrink-0" />
              Refresh
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => handleExport(reportType)}
              className="h-9 font-bold flex items-center gap-1.5"
            >
              <Download className="h-4 w-4" />
              Export CSV ({reportType})
            </Button>
          </div>
        }
      />

      {/* Role-Specific Metric Cards */}
      {dashboardData && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6">
          {Object.entries(dashboardData.metrics || {}).map(([key, val]) => (
            <StatCard
              key={key}
              label={key.replace(/_/g, " ").toUpperCase()}
              value={typeof val === "number" ? val : String(val)}
              accent={key.includes("total") || key.includes("assigned")}
            />
          ))}
        </div>
      )}

      {/* Global Filter Toolbar */}
      <Card className="flex flex-wrap items-center justify-between gap-4 bg-slate-50/50">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-slate-400" />
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Global Filters:
          </span>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-xs font-medium">
          <div>
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">
              Date From
            </label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-slate-800 focus:outline-none"
            />
          </div>

          <div>
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">
              Date To
            </label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="px-2.5 py-1 bg-white border border-slate-200 rounded-lg text-slate-800 focus:outline-none"
            />
          </div>

          <div>
            <label className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-0.5">
              Report Type Export
            </label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="px-2.5 py-1 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg font-bold text-slate-800 dark:text-slate-100 focus:outline-none"
            >
              <option value="complaints">Complaints Summary</option>
              <option value="department">Department Performance</option>
              <option value="coordinator">Coordinator Performance</option>
              <option value="hostel">Hostel Analytics</option>
              <option value="sla">SLA Compliance</option>
            </select>
          </div>
        </div>
      </Card>

      {/* SLA & Resolution Overview */}
      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="flex flex-col justify-between border-l-4 border-l-emerald-500">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                SLA Compliance Rate
              </span>
              <Shield className="h-5 w-5 text-emerald-500" />
            </div>
            <div className="text-3xl font-extrabold text-slate-900 mt-2">
              {slaData?.sla_achievement_pct || 100}%
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Resolution achievement on target deadlines
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 flex justify-between text-xs font-semibold">
            <span className="text-emerald-700">
              On Time: {slaData?.on_time || 0}
            </span>
            <span className="text-rose-600">
              Overdue: {slaData?.overdue || 0}
            </span>
          </div>
        </Card>

        <Card className="flex flex-col justify-between border-l-4 border-l-sky-500">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Avg Resolution Time
              </span>
              <Clock className="h-5 w-5 text-sky-500" />
            </div>
            <div className="text-3xl font-extrabold text-slate-900 mt-2">
              {analytics?.average_resolution_hours || 0} hrs
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Mean duration from creation to closure
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 flex justify-between text-xs font-semibold">
            <span className="text-slate-600">
              Reopened Total: {analytics?.reopened_count || 0}
            </span>
            <span className="text-slate-600">
              Max Reopens: {analytics?.max_reopens || 0}
            </span>
          </div>
        </Card>

        <Card className="flex flex-col justify-between border-l-4 border-l-indigo-500">
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                Community Voice
              </span>
              <Award className="h-5 w-5 text-indigo-500" />
            </div>
            <div className="text-3xl font-extrabold text-slate-900 mt-2">
              {analytics?.community_total || 0}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Public community complaints with student upvotes
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 flex justify-between text-xs font-semibold">
            <span className="text-indigo-600">Affected Count Tracked</span>
          </div>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Status Distribution */}
        <Card>
          <div className="mb-4">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              Complaints by Status
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Real-time lifecycle breakdown across filtered complaints
            </p>
          </div>
          <div className="grid gap-3">
            {statusEntries.length === 0 && (
              <p className="text-xs text-slate-400">No status data recorded.</p>
            )}
            {statusEntries.map(([statusName, count]) => (
              <div key={statusName} className="grid gap-1">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-slate-700">{statusName}</span>
                  <span className="font-bold text-slate-900">{count}</span>
                </div>
                <div className="h-2.5 rounded-full bg-slate-100 overflow-hidden">
                  <div
                    className="h-2.5 rounded-full bg-primary transition-all duration-300"
                    style={{
                      width: `${(count / Math.max(1, analytics?.total_complaints || 1)) * 100}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Department Volume Chart */}
        <Card>
          <div className="mb-4">
            <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <Building className="h-5 w-5 text-primary" />
              Department Complaint Distribution
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Volume of assigned complaints per department
            </p>
          </div>
          {deptChartData.length === 0 ? (
            <div className="flex h-48 items-center justify-center text-xs text-slate-400 font-medium">
              No department chart data.
            </div>
          ) : (
            <DashboardChart
              type="bar"
              data={deptChartData}
              accentColor="var(--primary)"
            />
          )}
        </Card>
      </div>

      {/* Coordinator Performance & Rankings Table — Staff/Admin only */}
      {isStaffAdmin && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <UserCheck className="h-5 w-5 text-primary" />
                Coordinator Performance Rankings
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Resolution efficiency, SLA compliance, and performance ranking
                metrics
              </p>
            </div>
            <Button
              variant="subtle"
              size="sm"
              onClick={() => handleExport("coordinator")}
              className="text-xs font-bold"
            >
              Export Table CSV
            </Button>
          </div>

          <div className="overflow-x-auto border border-slate-100 rounded-xl">
            <table className="min-w-full text-left border-collapse text-xs font-semibold">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100 text-slate-500">
                  <th className="p-3">Coordinator Name</th>
                  <th className="p-3 text-center">Assigned</th>
                  <th className="p-3 text-center">Resolved</th>
                  <th className="p-3 text-center">Pending</th>
                  <th className="p-3 text-center">SLA Breaches</th>
                  <th className="p-3 text-center">Avg Res Time</th>
                  <th className="p-3 text-center">Ranking</th>
                </tr>
              </thead>
              <tbody>
                {coordData.length === 0 && (
                  <tr>
                    <td
                      colSpan="7"
                      className="p-4 text-center text-slate-400 font-medium"
                    >
                      No coordinator records found.
                    </td>
                  </tr>
                )}
                {coordData.map((c) => (
                  <tr
                    key={c.coordinator_id}
                    className="border-b border-slate-100 last:border-0 hover:bg-slate-50/50"
                  >
                    <td className="p-3 font-bold text-slate-900">
                      {c.coordinator_name}
                    </td>
                    <td className="p-3 text-center font-bold text-slate-700">
                      {c.assigned}
                    </td>
                    <td className="p-3 text-center font-bold text-emerald-600">
                      {c.resolved}
                    </td>
                    <td className="p-3 text-center font-bold text-amber-600">
                      {c.pending}
                    </td>
                    <td className="p-3 text-center font-bold text-rose-600">
                      {c.sla_breaches}
                    </td>
                    <td className="p-3 text-center font-semibold text-slate-700">
                      {c.average_resolution_hours} hrs
                    </td>
                    <td className="p-3 text-center">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                          c.ranking === "Best Performer"
                            ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                            : c.ranking === "Needs Improvement"
                              ? "bg-rose-100 text-rose-800 border-rose-300"
                              : "bg-slate-100 text-slate-700 border-slate-200"
                        }`}
                      >
                        {c.ranking}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Hostel Analytics Density Table — Staff/Admin only */}
      {isStaffAdmin && (
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-bold text-slate-900">
                Hostel &amp; Location Incident Density
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Complaints logged per hostel block and capacity density
              </p>
            </div>
            <Button
              variant="subtle"
              size="sm"
              onClick={() => handleExport("hostel")}
              className="text-xs font-bold"
            >
              Export Hostel CSV
            </Button>
          </div>

          <div className="overflow-x-auto border border-slate-100 rounded-xl">
            <table className="min-w-full text-left border-collapse text-xs font-semibold">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100 text-slate-500">
                  <th className="p-3">Hostel Name</th>
                  <th className="p-3 text-center">Total Complaints</th>
                  <th className="p-3 text-center">Critical</th>
                  <th className="p-3 text-center">Resolved</th>
                  <th className="p-3 text-center">Pending</th>
                  <th className="p-3">Top Incident Category</th>
                </tr>
              </thead>
              <tbody>
                {hostelData.map((h) => (
                  <tr
                    key={h.hostel_id}
                    className="border-b border-slate-100 last:border-0 hover:bg-slate-50/50"
                  >
                    <td className="p-3 font-bold text-slate-800">
                      {h.hostel_name}
                    </td>
                    <td className="p-3 text-center font-bold text-slate-900">
                      {h.total_complaints}
                    </td>
                    <td className="p-3 text-center font-bold text-rose-600">
                      {h.critical_complaints}
                    </td>
                    <td className="p-3 text-center font-bold text-emerald-600">
                      {h.resolved}
                    </td>
                    <td className="p-3 text-center font-bold text-amber-600">
                      {h.pending}
                    </td>
                    <td className="p-3 font-semibold text-slate-700">
                      {h.most_common_category}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
