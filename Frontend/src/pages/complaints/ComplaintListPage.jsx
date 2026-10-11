import { useMemo, useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  RotateCw,
  ArrowRight,
  Plus,
  MapPin,
  Building,
  Layers,
  Search,
  X,
  Trash2,
  Eye,
  CheckCircle2,
  Clock,
} from "lucide-react";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import Table from "../../components/Table.jsx";
import PageHeader from "../../components/PageHeader.jsx";
import ConfirmDialog from "../../components/ConfirmDialog.jsx";
import Toast from "../../components/Toast.jsx";
import { getApiError } from "../../api/axios.js";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { useAuth } from "../../context/AuthContext.jsx";
import { complaintService } from "../../services/complaintService.js";
import { locationService } from "../../services/locationService.js";
import { departmentService } from "../../services/departmentService.js";
import { formatDate } from "../../utils/dateFormatter.js";
import { getStatusTone, getSlaTone } from "../../utils/statusColor.js";
import { COMPLAINT_STATUS } from "../../utils/constants.js";
import { getStudentStageText } from "../student/StudentDashboard.jsx";

const isClosedStatus = (statusStr) => {
  if (!statusStr) return false;
  const s = String(statusStr).toLowerCase();
  return s.startsWith("closed") || s === "rejected";
};

export default function ComplaintListPage() {
  const { user } = useAuth();
  const location = useLocation();

  const [query, setQuery] = useState(location.state?.query || "");
  const [status, setStatus] = useState(location.state?.status || "");
  const [activeLocationTab, setActiveLocationTab] = useState("all");
  const [selectedDepartment, setSelectedDepartment] = useState("");
  const [slaFilter, setSlaFilter] = useState(
    location.state?.sla || location.state?.slaFilter || "",
  );

  // Top-Level Lifecycle Tab: "remaining" (Default: Open/Pending/Active), "closed" (Closed & Auto-Closed), "all" (All Records)
  const [lifecycleTab, setLifecycleTab] = useState(() => {
    if (location.state?.status) {
      const s = String(location.state.status).toLowerCase();
      if (s.startsWith("closed") || s === "rejected") {
        return "closed";
      }
      if (s === "all") {
        return "all";
      }
    }
    return "remaining";
  });

  const [complaintToDelete, setComplaintToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [message, setMessage] = useState("");
  const [actionError, setActionError] = useState("");

  useEffect(() => {
    if (location.state?.status !== undefined) {
      const s = String(location.state.status).toLowerCase();
      if (s.startsWith("closed") || s === "rejected") {
        setLifecycleTab("closed");
      } else if (s === "all") {
        setLifecycleTab("all");
      } else {
        setLifecycleTab("remaining");
      }
      setStatus(location.state.status);
    }
    if (location.state?.sla !== undefined || location.state?.slaFilter !== undefined) {
      setSlaFilter(location.state.sla || location.state.slaFilter);
    }
    if (location.state?.query !== undefined) {
      setQuery(location.state.query);
    }
  }, [location.state]);

  const handleTabChange = (tab) => {
    setLifecycleTab(tab);
    // If the currently selected status contradicts the new tab, reset status so view isn't accidentally empty
    if (tab === "remaining" && isClosedStatus(status)) {
      setStatus("");
    } else if (tab === "closed" && status && !isClosedStatus(status) && status !== "active") {
      setStatus("");
    }
  };

  const [locations, setLocations] = useState([]);
  const [departments, setDepartments] = useState([]);

  const { data, loading, error, reload } = useAsyncData(
    async () => {
      const [compRes, locRes, deptRes] = await Promise.all([
        complaintService.list(),
        locationService.list().catch(() => ({ data: [] })),
        departmentService.list({ include_archived: true }).catch(() => ({ data: [] })),
      ]);
      setLocations(locRes.data || []);
      setDepartments(deptRes.data || []);
      return compRes.data || [];
    },
    [],
  );

  // Filter departments available ONLY in the currently selected location
  const availableDepartments = useMemo(() => {
    const names = new Set();

    if (!activeLocationTab || activeLocationTab === "all") {
      (departments || []).forEach((d) => {
        if (d.name && d.name.trim()) names.add(d.name.trim());
      });
      (data || []).forEach((c) => {
        const dName = c.department_name || c.department_id;
        if (dName && dName.trim()) names.add(dName.trim());
      });
      return Array.from(names).sort();
    }

    // Find selected location object
    const locObj = (locations || []).find(
      (l) => l.location_id === activeLocationTab || l.name === activeLocationTab,
    );
    const targetLocId = locObj ? locObj.location_id : activeLocationTab;
    const targetLocName = locObj ? locObj.name : activeLocationTab;

    // Filter departments matching target location
    const matchedDepts = (departments || []).filter(
      (d) =>
        d.location_id === targetLocId ||
        d.location_id === targetLocName,
    );

    matchedDepts.forEach((d) => {
      if (d.name && d.name.trim()) names.add(d.name.trim());
    });

    // Also include department names from actual complaint records for this location
    (data || []).forEach((c) => {
      const locMatch = (locations || []).find(
        (l) => l.location_id === c.location_id || l.name === c.location_id,
      );
      const cLocId = locMatch ? locMatch.location_id : c.location_id || "";
      const cLocName = locMatch ? locMatch.name : c.location_id || "";
      if (cLocId === targetLocId || cLocName === targetLocName) {
        const rawDeptId = c.department_id === "DEPT_ELECTRICAL" ? "DEPT_HOSTEL_ELECTRICAL" : c.department_id;
        const deptMatch = (departments || []).find(
          (d) => d.department_id === rawDeptId || d.name === rawDeptId || d.department_id === c.department_id || d.name === c.department_id,
        );
        const dName = c.department_name || (deptMatch ? deptMatch.name : (rawDeptId !== "DEPT_ELECTRICAL" ? rawDeptId : "Electrical"));
        if (dName && dName.trim() && dName !== "DEPT_ELECTRICAL" && dName !== "dept_electrical") {
          names.add(dName.trim());
        }
      }
    });

    return Array.from(names).sort();
  }, [departments, locations, activeLocationTab, data]);

  // Automatically reset selectedDepartment if it's no longer valid under selected location
  useEffect(() => {
    if (
      selectedDepartment &&
      !availableDepartments.includes(selectedDepartment)
    ) {
      setSelectedDepartment("");
    }
  }, [activeLocationTab, availableDepartments, selectedDepartment]);

  const getLocationCount = (locId) => {
    const rawData = data || [];
    const scopedData = rawData.filter((c) => {
      const isClosed = isClosedStatus(c.status);
      if (lifecycleTab === "remaining" && isClosed) return false;
      if (lifecycleTab === "closed" && !isClosed) return false;
      return true;
    });

    if (locId === "all") return scopedData.length;
    return scopedData.filter((c) => {
      const locMatch = locations.find(
        (l) => l.location_id === c.location_id || l.name === c.location_id,
      );
      const lId = locMatch ? locMatch.location_id : c.location_id || "";
      const lName = locMatch ? locMatch.name : c.location_id || "";
      return lId === locId || lName === locId;
    }).length;
  };

  const getDepartmentCount = (deptName) => {
    const rawData = data || [];
    const scopedData = rawData.filter((c) => {
      const isClosed = isClosedStatus(c.status);
      if (lifecycleTab === "remaining" && isClosed) return false;
      if (lifecycleTab === "closed" && !isClosed) return false;

      if (activeLocationTab !== "all") {
        const locMatch = locations.find(
          (l) => l.location_id === c.location_id || l.name === c.location_id,
        );
        const lId = locMatch ? locMatch.location_id : c.location_id || "";
        const lName = locMatch ? locMatch.name : c.location_id || "";
        if (lId !== activeLocationTab && lName !== activeLocationTab) return false;
      }
      return true;
    });

    if (!deptName) return scopedData.length;
    return scopedData.filter((c) => {
      const rawDeptId = c.department_id === "DEPT_ELECTRICAL" ? "DEPT_HOSTEL_ELECTRICAL" : c.department_id;
      const deptMatch = departments.find(
        (d) =>
          d.department_id === rawDeptId ||
          d.name === rawDeptId ||
          d.department_id === c.department_id ||
          d.name === c.department_id,
      );
      const dName =
        c.department_name ||
        (deptMatch ? deptMatch.name : (rawDeptId !== "DEPT_ELECTRICAL" ? rawDeptId : "Electrical"));
      return dName && dName.toLowerCase() === deptName.toLowerCase();
    }).length;
  };

  const remainingCount = useMemo(() => {
    return (data || []).filter((c) => !isClosedStatus(c.status)).length;
  }, [data]);

  const closedCount = useMemo(() => {
    return (data || []).filter((c) => isClosedStatus(c.status)).length;
  }, [data]);

  const totalCount = (data || []).length;

  const complaints = useMemo(() => {
    const rawData = data || [];

    return rawData.filter((complaint) => {
      // 0. Lifecycle Tab Division (Remaining vs Closed & Auto-Closed vs All)
      const isClosed = isClosedStatus(complaint.status);
      if (lifecycleTab === "remaining" && isClosed) {
        return false;
      }
      if (lifecycleTab === "closed" && !isClosed) {
        return false;
      }

      // 1. Status Filter
      if (status) {
        const sLower = status.toLowerCase();
        if (sLower === "active" || sLower === "open") {
          // Active problems are non-closed complaints
          if (isClosed) {
            return false;
          }
        } else if (sLower === "pending") {
          if (!["Pending", "Submitted", "Awaiting Coordinator Assignment"].includes(complaint.status)) {
            return false;
          }
        } else if (sLower === "closed") {
          if (!complaint.status?.startsWith("Closed")) {
            return false;
          }
        } else if (sLower === "escalated") {
          const isEscalated =
            complaint.status === "Escalated" ||
            complaint.priority === "Critical" ||
            complaint.is_escalated ||
            (complaint.sla_status && complaint.sla_status.toLowerCase().includes("breached"));
          if (!isEscalated) {
            return false;
          }
        } else if (complaint.status?.toLowerCase() !== sLower) {
          return false;
        }
      }

      // 2. SLA Filter
      if (slaFilter) {
        const slaLower = slaFilter.toLowerCase();
        if (slaLower === "overdue") {
          const isOverdue =
            complaint.is_overdue ||
            complaint.status === "Overdue" ||
            (complaint.sla_status &&
              (complaint.sla_status.toLowerCase().includes("overdue") ||
                complaint.sla_status.toLowerCase().includes("breached")));
          if (!isOverdue) {
            return false;
          }
        } else if (
          !complaint.sla_status ||
          !complaint.sla_status.toLowerCase().includes(slaLower)
        ) {
          return false;
        }
      }

      // Resolve Location Name & ID
      const locMatch = locations.find(
        (l) =>
          l.location_id === complaint.location_id ||
          l.name === complaint.location_id,
      );
      const locName = locMatch ? locMatch.name : complaint.location_id || "";
      const locId = locMatch ? locMatch.location_id : complaint.location_id || "";

      // 3. Location Dropdown Filter
      if (activeLocationTab !== "all") {
        if (locId !== activeLocationTab && locName !== activeLocationTab) {
          return false;
        }
      }

      // Resolve Department Name & ID
      const deptMatch = departments.find(
        (d) =>
          d.department_id === complaint.department_id ||
          d.name === complaint.department_id,
      );
      const deptName =
        complaint.department_name ||
        (deptMatch ? deptMatch.name : complaint.department_id || "");

      // 4. Department Dropdown Filter
      if (selectedDepartment) {
        if (
          deptName.toLowerCase() !== selectedDepartment.toLowerCase() &&
          complaint.department_id !== selectedDepartment
        ) {
          return false;
        }
      }

      // 5. Multi-field Search Query
      if (query.trim()) {
        const q = query.toLowerCase().trim();
        const idMatch = (complaint.complaint_id || "").toLowerCase().includes(q);
        const titleMatch = (complaint.title || "").toLowerCase().includes(q);
        const typeMatch = (complaint.complaint_type || "").toLowerCase().includes(q);
        const descMatch = (complaint.description || "").toLowerCase().includes(q);
        const statusMatch = (complaint.status || "").toLowerCase().includes(q);
        const slaMatch = (complaint.sla_status || "").toLowerCase().includes(q);
        const locSearchMatch =
          locName.toLowerCase().includes(q) ||
          (complaint.location_id || "").toLowerCase().includes(q);
        const deptSearchMatch =
          deptName.toLowerCase().includes(q) ||
          (complaint.department_id || "").toLowerCase().includes(q);
        const creatorMatch =
          (complaint.created_by || "").toLowerCase().includes(q) ||
          (complaint.user_name || "").toLowerCase().includes(q);
        const coordinatorMatch = (
          complaint.assigned_coordinator_name || ""
        ).toLowerCase().includes(q);

        if (
          !idMatch &&
          !titleMatch &&
          !typeMatch &&
          !descMatch &&
          !statusMatch &&
          !slaMatch &&
          !locSearchMatch &&
          !deptSearchMatch &&
          !creatorMatch &&
          !coordinatorMatch
        ) {
          return false;
        }
      }

      return true;
    });
  }, [
    data,
    query,
    status,
    slaFilter,
    activeLocationTab,
    selectedDepartment,
    locations,
    departments,
    lifecycleTab,
  ]);

  const handleDeleteConfirm = async () => {
    if (!complaintToDelete) return;
    setDeleting(true);
    setActionError("");
    try {
      await complaintService.delete(complaintToDelete.complaint_id);
      setMessage(`Complaint ${complaintToDelete.complaint_id} was deleted successfully.`);
      setComplaintToDelete(null);
      reload();
    } catch (err) {
      setActionError(getApiError(err, "Failed to delete complaint."));
    } finally {
      setDeleting(false);
    }
  };

  const columns = [
    {
      key: "complaint_id",
      header: "ID",
      render: (row) => (
        <Link
          className="font-semibold text-primary hover:underline flex items-center gap-1"
          to={`/complaints/${row.complaint_id}`}
        >
          {row.complaint_id}
          <ArrowRight className="h-3.5 w-3.5 shrink-0 text-primary" />
        </Link>
      ),
    },
    {
      key: "location",
      header: "Location",
      render: (row) => {
        const matched = locations.find(
          (l) => l.location_id === row.location_id || l.name === row.location_id,
        );
        const locName = matched ? matched.name : row.location_id;
        return locName ? (
          <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300">
            <MapPin className="h-3.5 w-3.5 text-primary shrink-0" />
            {locName}
          </span>
        ) : (
          "-"
        );
      },
    },
    {
      key: "department",
      header: "Department",
      render: (row) => {
        const matched = departments.find(
          (d) => d.department_id === row.department_id || d.name === row.department_id,
        );
        const deptName =
          row.department_name || (matched ? matched.name : row.department_id);
        return deptName ? (
          <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 dark:text-slate-300">
            <Building className="h-3.5 w-3.5 text-primary shrink-0" />
            {deptName}
          </span>
        ) : (
          "-"
        );
      },
    },
    { key: "complaint_type", header: "Type / Category" },
    {
      key: "status",
      header: "Status & Stage",
      render: (row) => (
        <div className="flex flex-col gap-1 items-start">
          <Badge tone={getStatusTone(row.status)}>{row.status}</Badge>
          <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium leading-tight">
            {getStudentStageText(row)}
          </span>
        </div>
      ),
    },
    {
      key: "sla_status",
      header: "SLA Status",
      render: (row) =>
        row.sla_status ? (
          <Badge tone={getSlaTone(row.sla_status)}>{row.sla_status}</Badge>
        ) : (
          "-"
        ),
    },
    {
      key: "created_at",
      header: "Date Filed",
      render: (row) => formatDate(row.created_at),
    },
    {
      key: "actions",
      header: "Actions",
      render: (row) => {
        const userRole = (user?.role || "").toLowerCase();
        const isOwner =
          user &&
          (user.user_id === row.created_by ||
            user.id === row.created_by ||
            user.email === row.created_by);
        const canDirectDelete = ["administrator", "app_manager"].includes(userRole);
        const canStudentDelete = userRole === "student" && isOwner;

        return (
          <div className="flex items-center gap-1.5">
            <Link
              to={`/complaints/${row.complaint_id}`}
              className="p-1.5 text-slate-500 hover:text-primary hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors"
              title="View Details"
            >
              <Eye className="h-4 w-4" />
            </Link>

            {canDirectDelete && (
              <button
                type="button"
                onClick={() => setComplaintToDelete(row)}
                className="p-1.5 text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-lg transition-colors cursor-pointer"
                title="Delete Complaint"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            )}

            {!canDirectDelete && canStudentDelete && row.status === "Submitted" && (
              <button
                type="button"
                onClick={() => setComplaintToDelete(row)}
                className="p-1.5 text-rose-600 hover:text-rose-700 hover:bg-rose-50 dark:hover:bg-rose-950/30 rounded-lg transition-colors cursor-pointer"
                title="Delete Complaint"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            )}
          </div>
        );
      },
    },
  ];

  return (
    <div className="grid gap-6">
      <PageHeader
        title="Complaints Tracker"
        description="Monitor, filter, and track campus complaints by location, department, status, or keyword."
        actions={
          <div className="flex items-center gap-2">
            {(user?.role === "student" || user?.role === "location_in_charge") && (
              <Link to="/complaints/new">
                <Button size="sm" className="min-h-10 font-bold gap-1">
                  <Plus className="h-4 w-4" />
                  File New Complaint
                </Button>
              </Link>
            )}
            <Button
              variant="subtle"
              size="sm"
              onClick={reload}
              className="min-h-10"
            >
              <RotateCw className="h-4 w-4 mr-1" />
              Refresh
            </Button>
          </div>
        }
      />

      {/* Grid List Table with Single Merged Filter Toolbar */}
      <Card>
        {/* Top-Level Division: Remaining/Active vs Closed & Auto-Closed vs All */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 mb-2 border-b border-slate-100 dark:border-slate-800">
          <div className="inline-flex items-center p-1 bg-slate-100 dark:bg-slate-800/80 rounded-xl gap-1">
            <button
              type="button"
              onClick={() => handleTabChange("remaining")}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                lifecycleTab === "remaining"
                  ? "bg-white dark:bg-slate-900 text-primary shadow-2xs font-semibold"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
              }`}
            >
              <Clock className="h-3.5 w-3.5 text-amber-500" />
              <span>Remaining / Active</span>
              <span
                className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${
                  lifecycleTab === "remaining"
                    ? "bg-primary/10 text-primary"
                    : "bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                }`}
              >
                {remainingCount}
              </span>
            </button>

            <button
              type="button"
              onClick={() => handleTabChange("closed")}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                lifecycleTab === "closed"
                  ? "bg-white dark:bg-slate-900 text-emerald-600 dark:text-emerald-400 shadow-2xs font-semibold"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
              }`}
            >
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
              <span>Closed & Auto-Closed</span>
              <span
                className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${
                  lifecycleTab === "closed"
                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                    : "bg-slate-200 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                }`}
              >
                {closedCount}
              </span>
            </button>

            <button
              type="button"
              onClick={() => handleTabChange("all")}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                lifecycleTab === "all"
                  ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-2xs font-semibold"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
              }`}
            >
              <Layers className="h-3.5 w-3.5 text-slate-400" />
              <span>All ({totalCount})</span>
            </button>
          </div>
        </div>

        {/* Single Merged Filter & Search Toolbar */}
        <div className="flex flex-wrap items-center gap-3 my-2">
          {/* Search Box - Takes flexible width */}
          <div className="relative flex-1 min-w-[220px]">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search complaints..."
              className="h-10 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 pl-10 pr-9 text-xs font-medium text-slate-800 dark:text-slate-100 placeholder:text-slate-400 outline-none focus:border-primary transition-colors"
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-xs font-bold"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* Merged Location Dropdown Filter */}
          <select
            value={activeLocationTab}
            onChange={(e) => setActiveLocationTab(e.target.value)}
            className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
          >
            <option value="all">📍 All Locations ({getLocationCount("all")})</option>
            {locations.map((loc) => {
              const cnt = getLocationCount(loc.location_id);
              return (
                <option key={loc.location_id} value={loc.location_id}>
                  📍 {loc.name} ({cnt})
                </option>
              );
            })}
          </select>

          {/* Merged Department Dropdown Filter (Dynamically scoped to selected location & lifecycle tab) */}
          <select
            value={selectedDepartment}
            onChange={(e) => setSelectedDepartment(e.target.value)}
            className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
          >
            <option value="">🏢 All Departments ({getDepartmentCount("")})</option>
            {availableDepartments.map((deptName) => {
              const cnt = getDepartmentCount(deptName);
              return (
                <option key={deptName} value={deptName}>
                  🏢 {deptName} ({cnt})
                </option>
              );
            })}
          </select>

          {/* Merged Status Filter Dropdown (Tailored to active tab) */}
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
          >
            {lifecycleTab === "remaining" && (
              <>
                <option value="">All Remaining Statuses ({remainingCount})</option>
                <option value="Escalated">🚨 Escalated / Critical</option>
                <option value="Submitted">Submitted (New)</option>
                <option value="Assigned">Assigned to Coordinator</option>
                <option value="In Progress">In Progress</option>
                <option value="Waiting for Verification">Waiting for Verification</option>
                <option value="Reopened">Reopened</option>
              </>
            )}
            {lifecycleTab === "closed" && (
              <>
                <option value="">All Closed Statuses ({closedCount})</option>
                <option value="Closed">Closed</option>
                <option value="Closed (Auto Closed)">Closed (Auto Closed)</option>
                <option value="Rejected">Rejected</option>
              </>
            )}
            {lifecycleTab === "all" && (
              <>
                <option value="">All Statuses ({totalCount})</option>
                <option value="active">📂 Active Problems</option>
                <option value="Escalated">🚨 Escalated / Critical</option>
                {Object.values(COMPLAINT_STATUS).map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </>
            )}
          </select>

          {/* Merged SLA State Dropdown */}
          <select
            value={slaFilter}
            onChange={(e) => setSlaFilter(e.target.value)}
            className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
          >
            <option value="">All SLA States</option>
            <option value="On Time">🟢 On Time</option>
            <option value="Due Today">🟡 Due Today</option>
            <option value="Overdue">🔴 Overdue</option>
          </select>
        </div>

        {loading && (
          <Loader label="Loading complaints list" variant="skeleton" />
        )}
        {error && (
          <EmptyState title="Could not load complaints" description={error} />
        )}

        {!loading && !error && complaints.length === 0 && (
          <EmptyState
            title={
              lifecycleTab === "remaining"
                ? "No remaining complaints"
                : lifecycleTab === "closed"
                ? "No closed complaints found"
                : "No complaints found"
            }
            description={
              lifecycleTab === "remaining"
                ? "You have no active complaints pending resolution. Any completed or auto-closed complaints are preserved in the 'Closed & Auto-Closed' tab."
                : lifecycleTab === "closed"
                ? "No complaints have been marked closed or auto-closed yet."
                : "Try adjusting your location, department, status, or search query."
            }
          />
        )}

        {!loading && !error && complaints.length > 0 && (
          <div className="mt-4">
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-3">
              Showing{" "}
              <span className="font-bold text-slate-800 dark:text-slate-200">
                {complaints.length}
              </span>{" "}
              {lifecycleTab === "remaining"
                ? "remaining active complaints"
                : lifecycleTab === "closed"
                ? "closed or auto-closed complaints"
                : "total complaints"}
            </p>
            <Table
              columns={columns}
              rows={complaints}
              getRowKey={(row) => row.complaint_id}
            />
          </div>
        )}
      </Card>

      {message && (
        <Toast message={message} tone="success" onClose={() => setMessage("")} />
      )}
      {actionError && (
        <Toast message={actionError} tone="danger" onClose={() => setActionError("")} />
      )}

      <ConfirmDialog
        open={Boolean(complaintToDelete)}
        title="Delete Complaint"
        message={`Are you sure you want to delete complaint ${complaintToDelete?.complaint_id}? This complaint will be soft-deleted.`}
        confirmLabel={deleting ? "Deleting..." : "Delete Complaint"}
        tone="danger"
        onCancel={() => setComplaintToDelete(null)}
        onConfirm={handleDeleteConfirm}
      />
    </div>
  );
}
