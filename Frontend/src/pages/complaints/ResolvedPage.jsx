import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import {
  CheckCircle2,
  Search,
  Filter,
  X,
  RotateCw,
  Eye,
  Calendar,
  MapPin,
  Building,
  Layers,
} from "lucide-react";
import Card from "../../components/Card.jsx";
import Table from "../../components/Table.jsx";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Loader from "../../components/Loader.jsx";
import { complaintService } from "../../services/complaintService.js";
import { locationService } from "../../services/locationService.js";
import { departmentService } from "../../services/departmentService.js";
import { getApiError } from "../../api/axios.js";
import { formatDate } from "../../utils/dateFormatter.js";
import { getSlaTone, getStatusTone } from "../../utils/statusColor.js";

export default function ResolvedPage() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Filters
  const [locationId, setLocationId] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [category, setCategory] = useState("");
  const [priority, setPriority] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);

  // Dropdown reference lists
  const [locations, setLocations] = useState([]);
  const [departments, setDepartments] = useState([]);

  useEffect(() => {
    async function fetchRefData() {
      try {
        const [locRes, deptRes] = await Promise.all([
          locationService.list(),
          departmentService.list(),
        ]);
        const locData = locRes.data || locRes;
        const deptData = deptRes.data || deptRes;
        setLocations(Array.isArray(locData) ? locData : locData.items || []);
        setDepartments(Array.isArray(deptData) ? deptData : deptData.items || []);
      } catch (e) {
        // ignore fallback
      }
    }
    fetchRefData();
  }, []);

  const fetchResolved = async () => {
    setLoading(true);
    setError("");
    try {
      const params = {
        page,
        limit: 20,
      };
      if (locationId) params.location_id = locationId;
      if (departmentId) params.department_id = departmentId;
      if (category) params.category = category;
      if (priority) params.priority = priority;
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (query) params.q = query;

      const res = await complaintService.getResolved(params);
      const resData = res.data || res;
      setItems(resData.items || []);
      setTotal(resData.total || 0);
    } catch (err) {
      setError(getApiError(err, "Failed to load resolved complaints."));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchResolved();
  }, [locationId, departmentId, category, priority, dateFrom, dateTo, page]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    fetchResolved();
  };

  const clearFilters = () => {
    setLocationId("");
    setDepartmentId("");
    setCategory("");
    setPriority("");
    setDateFrom("");
    setDateTo("");
    setQuery("");
    setPage(1);
  };

  const hasActiveFilters =
    locationId || departmentId || category || priority || dateFrom || dateTo || query;

  return (
    <div className="space-y-4 sm:space-y-6">
      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-400">
          {error}
        </div>
      )}

      {/* Filter Toolbar */}
      <Card className="p-4 space-y-4">
        <form onSubmit={handleSearch} className="flex flex-wrap items-center gap-2.5 sm:gap-3">
          <div className="relative w-full sm:flex-1 sm:min-w-[200px]">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search resolved title, ID, resolution notes..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full rounded-xl border border-slate-300 bg-white pl-9 pr-4 py-2 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-primary dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
            />
          </div>

          {/* Location Filter */}
          <select
            value={locationId}
            onChange={(e) => { setLocationId(e.target.value); setPage(1); }}
            className="w-full sm:w-auto rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
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
            value={departmentId}
            onChange={(e) => { setDepartmentId(e.target.value); setPage(1); }}
            className="w-full sm:w-auto rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          >
            <option value="">All Departments</option>
            {departments.map((dept) => (
              <option key={dept.department_id} value={dept.department_id}>
                {dept.name}
              </option>
            ))}
          </select>

          {/* Priority Filter */}
          <select
            value={priority}
            onChange={(e) => { setPriority(e.target.value); setPage(1); }}
            className="w-full sm:w-auto rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
          >
            <option value="">All Priorities</option>
            <option value="Low">Low</option>
            <option value="Medium">Medium</option>
            <option value="High">High</option>
            <option value="Urgent">Urgent</option>
          </select>

          {/* Date Range - Non-overlapping layout */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-2 w-full sm:w-auto">
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 w-10 sm:w-auto shrink-0">
                From:
              </span>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => { setDateFrom(e.target.value); setPage(1); }}
                className="flex-1 sm:w-36 rounded-xl border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 outline-none focus:border-primary"
              />
            </div>
            <div className="flex items-center gap-2 w-full sm:w-auto">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 w-10 sm:w-auto shrink-0">
                To:
              </span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => { setDateTo(e.target.value); setPage(1); }}
                className="flex-1 sm:w-36 rounded-xl border border-slate-300 bg-white px-2.5 py-1.5 text-xs text-slate-800 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 outline-none focus:border-primary"
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
            <Button type="submit" variant="primary" size="sm" className="flex-1 sm:flex-initial">
              Apply Search
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={fetchResolved}
              className="flex items-center gap-1.5"
            >
              <RotateCw className="h-3.5 w-3.5" />
              Refresh
            </Button>
            {hasActiveFilters && (
              <Button
                type="button"
                variant="subtle"
                size="sm"
                onClick={clearFilters}
                className="flex items-center gap-1 text-slate-500 hover:text-slate-800 dark:hover:text-slate-200"
              >
                <X className="h-3.5 w-3.5" />
                Clear
              </Button>
            )}
          </div>
        </form>
      </Card>

      {/* Resolved Complaints Table */}
      <Card className="p-5">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Resolved Complaints ({total})
            </h3>
          </div>
        </div>

        {loading ? (
          <div className="py-12">
            <Loader label="Loading resolved complaint records..." />
          </div>
        ) : items.length === 0 ? (
          <div className="rounded-xl border border-dashed border-slate-200 py-12 text-center dark:border-slate-800">
            <CheckCircle2 className="mx-auto h-10 w-10 text-slate-400" />
            <p className="mt-3 text-sm font-semibold text-slate-700 dark:text-slate-300">
              No resolved complaints found matching criteria.
            </p>
            <p className="text-xs text-slate-400">Try adjusting your filters or search terms.</p>
          </div>
        ) : (
          <Table
            columns={[
              {
                header: "Resolved Complaint",
                accessor: "title",
                render: (c) => (
                  <div>
                    <Link
                      to={`/complaints/${c.complaint_id}`}
                      className="font-semibold text-primary hover:underline"
                    >
                      {c.title || c.category || c.complaint_id}
                    </Link>
                    <div className="text-xs text-slate-500 line-clamp-1">{c.description}</div>
                    <div className="mt-1 text-[11px] text-slate-400">ID: {c.complaint_id}</div>
                  </div>
                ),
              },
              {
                header: "Location & Dept",
                accessor: "location_name",
                render: (c) => (
                  <div className="text-xs">
                    <div className="font-medium text-slate-800 dark:text-slate-200">
                      {c.location_name || c.location_id}
                    </div>
                    <div className="text-slate-500">{c.department_name || c.department_id}</div>
                  </div>
                ),
              },
              {
                header: "Resolved Date & Notes",
                accessor: "resolved_at",
                render: (c) => (
                  <div className="text-xs">
                    <div className="font-medium text-emerald-700 dark:text-emerald-400">
                      Resolved: {formatDate(c.resolved_at || c.updated_at)}
                    </div>
                    {c.resolution_notes && (
                      <div className="mt-0.5 text-slate-500 italic line-clamp-2">
                        "{c.resolution_notes}"
                      </div>
                    )}
                  </div>
                ),
              },
              {
                header: "Status / SLA",
                accessor: "status",
                render: (c) => (
                  <div className="flex flex-col gap-1">
                    <Badge tone={getStatusTone(c.status)}>{c.status}</Badge>
                    <Badge tone={getSlaTone(c.sla_status)}>
                      {c.sla_status || "🟢 On Time"}
                    </Badge>
                  </div>
                ),
              },
              {
                header: "Action",
                accessor: "complaint_id",
                render: (c) => (
                  <Link to={`/complaints/${c.complaint_id}`}>
                    <Button size="xs" variant="outline" leftIcon={<Eye className="h-3.5 w-3.5" />}>
                      View
                    </Button>
                  </Link>
                ),
              },
            ]}
            rows={items || []}
            data={items || []}
          />
        )}
      </Card>
    </div>
  );
}
