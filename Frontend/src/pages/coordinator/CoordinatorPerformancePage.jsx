import { useState, useMemo, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  TrendingUp,
  RotateCw,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Award,
  Camera,
  Layers,
  MapPin,
  Building,
  User,
  ShieldAlert,
} from "lucide-react";
import PageHeader from "../../components/PageHeader.jsx";
import Card from "../../components/Card.jsx";
import Table from "../../components/Table.jsx";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Loader from "../../components/Loader.jsx";
import StatCard from "../../components/StatCard.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Toast from "../../components/Toast.jsx";
import { complaintService } from "../../services/complaintService.js";
import { locationService } from "../../services/locationService.js";
import { departmentService } from "../../services/departmentService.js";
import { getApiError } from "../../api/axios.js";

export default function CoordinatorPerformancePage() {
  const [stats, setStats] = useState([]);
  const [locations, setLocations] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toastMessage, setToastMessage] = useState("");

  // Filters
  const [selectedLocation, setSelectedLocation] = useState("");
  const [selectedDepartment, setSelectedDepartment] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const fetchData = async () => {
    setLoading(true);
    setError("");
    try {
      const params = {};
      if (selectedLocation) params.location_id = selectedLocation;
      if (selectedDepartment) params.department_id = selectedDepartment;
      if (fromDate) params.from = fromDate;
      if (toDate) params.to = toDate;

      const [statsRes, locRes, deptRes] = await Promise.all([
        complaintService.getCoordinatorStats(params).catch(() => ({ data: [] })),
        locationService.list().catch(() => ({ data: [] })),
        departmentService.list().catch(() => ({ data: [] })),
      ]);

      setStats(statsRes.data || []);
      setLocations(locRes.data || []);
      setDepartments(deptRes.data || []);
    } catch (err) {
      setError(getApiError(err, "Failed to load coordinator performance data."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [selectedLocation, selectedDepartment, fromDate, toDate]);

  const handleResetFilters = () => {
    setSelectedLocation("");
    setSelectedDepartment("");
    setFromDate("");
    setToDate("");
    setSearchQuery("");
  };

  const filteredStats = useMemo(() => {
    if (!searchQuery.trim()) return stats;
    const q = searchQuery.toLowerCase();
    return stats.filter(
      (s) =>
        (s.name && s.name.toLowerCase().includes(q)) ||
        (s.email && s.email.toLowerCase().includes(q)) ||
        (s.coordinator_id && s.coordinator_id.toLowerCase().includes(q)),
    );
  }, [stats, searchQuery]);

  // Aggregate Metrics
  const summary = useMemo(() => {
    const totalCoordinators = stats.length;
    let totalCompleted = 0;
    let totalOnTime = 0;
    let totalLate = 0;
    let totalFixTime = 0;
    let fixTimeCount = 0;
    let totalPhotoSkips = 0;

    stats.forEach((s) => {
      totalCompleted += s.completed || 0;
      totalOnTime += s.on_time || 0;
      totalLate += s.late || 0;
      totalPhotoSkips += s.photo_skip_count || 0;
      if (s.avg_time_to_fix > 0) {
        totalFixTime += s.avg_time_to_fix;
        fixTimeCount++;
      }
    });

    const onTimeRate =
      totalCompleted > 0
        ? Math.round((totalOnTime / totalCompleted) * 100)
        : 100;
    const avgFixTime =
      fixTimeCount > 0 ? (totalFixTime / fixTimeCount).toFixed(1) : "0.0";

    return {
      totalCoordinators,
      totalCompleted,
      totalOnTime,
      totalLate,
      onTimeRate,
      avgFixTime,
      totalPhotoSkips,
    };
  }, [stats]);

  const columns = [
    {
      header: "Coordinator",
      accessor: "name",
      render: (row) => (
        <div>
          <div className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
            <User className="h-3.5 w-3.5 text-primary shrink-0" />
            {row.name}
          </div>
          <div className="text-[11px] text-slate-400 font-mono mt-0.5">{row.email}</div>
        </div>
      ),
    },
    {
      header: "Accepted / Auto",
      accessor: "accepted",
      render: (row) => (
        <div className="text-xs">
          <span className="font-bold text-slate-800 dark:text-slate-200">{row.accepted || 0}</span>
          <span className="text-slate-400"> accepted</span>
          <div className="text-[11px] text-slate-400">
            {row.auto_assigned || 0} auto-assigned
          </div>
        </div>
      ),
    },
    {
      header: "Active Work",
      accessor: "in_progress",
      render: (row) => (
        <div className="text-xs">
          <span className="font-bold text-blue-600 dark:text-blue-400">{row.in_progress || 0}</span>
          <span className="text-slate-400"> working</span>
          {row.waiting_for_parts > 0 && (
            <div className="text-[11px] text-amber-600 dark:text-amber-400 font-semibold">
              {row.waiting_for_parts} waiting parts
            </div>
          )}
        </div>
      ),
    },
    {
      header: "Completed",
      accessor: "completed",
      render: (row) => (
        <span className="font-bold text-emerald-600 dark:text-emerald-400 text-xs">
          {row.completed || 0}
        </span>
      ),
    },
    {
      header: "On Time vs Late",
      accessor: "on_time",
      render: (row) => {
        const total = (row.on_time || 0) + (row.late || 0);
        const rate = total > 0 ? Math.round(((row.on_time || 0) / total) * 100) : 100;
        let tone = "success";
        if (rate < 70) tone = "danger";
        else if (rate < 85) tone = "warning";

        return (
          <div className="flex flex-col gap-1 items-start">
            <Badge tone={tone}>
              {rate}% On Time
            </Badge>
            <span className="text-[10px] text-slate-400">
              {row.on_time || 0} on time · {row.late || 0} late
            </span>
          </div>
        );
      },
    },
    {
      header: "Avg Response",
      accessor: "avg_time_to_accept",
      render: (row) => (
        <div className="text-xs">
          <div>
            <span className="font-semibold text-slate-700 dark:text-slate-300">
              {row.avg_time_to_accept || 0}h
            </span>{" "}
            <span className="text-slate-400 text-[10px]">to accept</span>
          </div>
          <div>
            <span className="font-semibold text-slate-700 dark:text-slate-300">
              {row.avg_time_to_fix || 0}h
            </span>{" "}
            <span className="text-slate-400 text-[10px]">to fix</span>
          </div>
        </div>
      ),
    },
    {
      header: "Quality Check",
      accessor: "warden_not_fixed",
      render: (row) => (
        <div className="text-xs space-y-0.5">
          <div className="flex items-center gap-1">
            <span className="text-slate-500 text-[11px]">Reopens:</span>
            <span className={`font-semibold ${row.reopens > 0 ? "text-amber-600" : "text-slate-700 dark:text-slate-300"}`}>
              {row.reopens || 0}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-slate-500 text-[11px]">Warden "Not Fixed":</span>
            <span className={`font-semibold ${row.warden_not_fixed > 0 ? "text-rose-600" : "text-slate-700 dark:text-slate-300"}`}>
              {row.warden_not_fixed || 0}
            </span>
          </div>
        </div>
      ),
    },
    {
      header: "Photo Adherence",
      accessor: "photo_percent",
      render: (row) => (
        <div className="text-xs space-y-0.5">
          <div className="flex items-center gap-1">
            <Camera className="h-3 w-3 text-slate-400" />
            <span className="font-bold text-slate-800 dark:text-slate-200">
              {row.photo_percent !== undefined ? `${row.photo_percent}%` : "100%"}
            </span>
          </div>
          <div className="text-[10px] text-slate-400">
            {row.photo_skip_count || 0} skip{row.photo_skip_count === 1 ? "" : "s"}
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {toastMessage && (
        <Toast
          message={toastMessage}
          tone="info"
          onClose={() => setToastMessage("")}
        />
      )}

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <PageHeader
            title="Coordinator Performance & SLA Reliability"
            description="Turnaround speed, verification accuracy, and quality metrics across all field coordinators."
          />
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <Button
            variant="outline"
            size="sm"
            onClick={fetchData}
            className="flex items-center gap-1.5"
          >
            <RotateCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs font-semibold text-rose-700 dark:border-rose-900/50 dark:bg-rose-950/30 dark:text-rose-400">
          {error}
        </div>
      )}

      {/* Top 4 Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
        <StatCard
          label="Active Coordinators"
          value={summary.totalCoordinators}
          subtext="Covering mapped campus zones"
        />
        <StatCard
          label="Completed Repairs"
          value={summary.totalCompleted}
          subtext={`${summary.totalOnTime} delivered within SLA`}
        />
        <StatCard
          label="On-Time Rate"
          value={`${summary.onTimeRate}%`}
          accent={summary.onTimeRate < 80}
          subtext={`${summary.totalLate} total late completions`}
        />
        <StatCard
          label="Avg Time to Fix"
          value={`${summary.avgFixTime}h`}
          subtext={`${summary.totalPhotoSkips} total photo skips logged`}
        />
      </div>

      {/* Filter Toolbar */}
      <Card className="!p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3 flex-1 min-w-[280px]">
            {/* Search */}
            <div className="relative min-w-[200px] flex-1">
              <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search coordinator by name or email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="h-9 w-full rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 pl-8 pr-3 text-xs outline-none focus:border-primary text-slate-800 dark:text-slate-200"
              />
            </div>

            {/* Location Filter */}
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="h-9 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-medium text-slate-700 dark:text-slate-200 outline-none focus:border-primary"
            >
              <option value="">All Locations</option>
              {locations.map((loc) => (
                <option key={loc.location_id} value={loc.location_id}>
                  {loc.name}
                </option>
              ))}
            </select>

            {/* Department Filter */}
            <select
              value={selectedDepartment}
              onChange={(e) => setSelectedDepartment(e.target.value)}
              className="h-9 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-medium text-slate-700 dark:text-slate-200 outline-none focus:border-primary"
            >
              <option value="">All Departments</option>
              {departments.map((dept) => (
                <option key={dept.department_id} value={dept.department_id}>
                  {dept.name}
                </option>
              ))}
            </select>

            {/* From Date */}
            <div className="flex items-center gap-1 text-xs text-slate-500">
              <span>From:</span>
              <input
                type="date"
                value={fromDate}
                onChange={(e) => setFromDate(e.target.value)}
                className="h-9 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 px-2 text-xs text-slate-700 dark:text-slate-200 outline-none focus:border-primary"
              />
            </div>

            {/* To Date */}
            <div className="flex items-center gap-1 text-xs text-slate-500">
              <span>To:</span>
              <input
                type="date"
                value={toDate}
                onChange={(e) => setToDate(e.target.value)}
                className="h-9 rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 px-2 text-xs text-slate-700 dark:text-slate-200 outline-none focus:border-primary"
              />
            </div>
          </div>

          {(selectedLocation || selectedDepartment || fromDate || toDate || searchQuery) && (
            <Button
              size="xs"
              variant="ghost"
              onClick={handleResetFilters}
              className="text-xs text-slate-500 hover:text-slate-800"
            >
              Reset Filters
            </Button>
          )}
        </div>
      </Card>

      {/* Main Table */}
      <Card className="!p-0 overflow-hidden">
        {loading ? (
          <div className="p-8">
            <Loader label="Loading coordinator metrics..." variant="skeleton" />
          </div>
        ) : filteredStats.length === 0 ? (
          <div className="p-8">
            <EmptyState
              title="No Coordinator Data Found"
              description="No performance records match your active location, department, or date range filters."
            />
          </div>
        ) : (
          <Table
            columns={columns}
            rows={filteredStats}
            data={filteredStats}
            getRowKey={(r) => r.coordinator_id}
          />
        )}
      </Card>
    </div>
  );
}

