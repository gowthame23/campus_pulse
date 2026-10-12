import { useState, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import {
  Globe,
  ChevronRight,
  Building,
  Layers,
  ArrowLeft,
  Users,
  Bell,
  AlertTriangle,
  MessageSquare,
  Filter,
  Search,
  RotateCw,
  MapPin,
  Edit,
  Trash2,
} from "lucide-react";
// Page rendered inside the global MainLayout provided by ProtectedRoute
import Card from "../../components/Card.jsx";
import Badge from "../../components/Badge.jsx";
import Loader from "../../components/Loader.jsx";
import Toast from "../../components/Toast.jsx";
import Modal from "../../components/Modal.jsx";
import Button from "../../components/Button.jsx";
import Select from "../../components/Select.jsx";
import Textarea from "../../components/Textarea.jsx";
import ConfirmDialog from "../../components/ConfirmDialog.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { complaintService } from "../../services/complaintService.js";
import { locationService } from "../../services/locationService.js";
import { departmentService } from "../../services/departmentService.js";
import { formatDate } from "../../utils/dateFormatter.js";
import { getStatusTone } from "../../utils/statusColor.js";

export default function PublicComplaintsPage() {
  const [level, setLevel] = useState(1); // Level 1: Locations, Level 2: Depts, Level 3: Complaints, Level 4: Details
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [selectedDept, setSelectedDept] = useState(null);
  const [selectedComplaint, setSelectedComplaint] = useState(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");

  const [locations, setLocations] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);

  const [following, setFollowing] = useState(false);
  const [showAffectedModal, setShowAffectedModal] = useState(false);
  const [affectedInfo, setAffectedInfo] = useState("");

  const { user } = useAuth();
  const [confirmAction, setConfirmAction] = useState(null);

  // Student Edit State for Public Complaints
  const [showEditModal, setShowEditModal] = useState(false);
  const [editLocation, setEditLocation] = useState("");
  const [editDepartment, setEditDepartment] = useState("");
  const [editType, setEditType] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editSubmitting, setEditSubmitting] = useState(false);

  const isOwner = user && selectedComplaint && (user.user_id === selectedComplaint.created_by || user.email === selectedComplaint.created_by);
  const canStudentEditOrDelete = isOwner && (user?.role === "student" || (user?.role || "").toLowerCase() === "student") && selectedComplaint?.status === "Submitted";

  const availableEditDepartments = useMemo(() => {
    if (!editLocation) return [];

    const locObj = (locations || []).find(l => l.location_id === editLocation || l.name === editLocation);
    const locId = locObj ? locObj.location_id : editLocation;
    const locType = locObj ? (locObj.location_type || locObj.name) : editLocation;

    const typeToTemplateId = {
      "Hostel": "LOC_HOSTEL_A",
      "Academic Block": "LOC_ACADEMIC",
      "Mess": "LOC_MESS",
      "Student Activity Center": "LOC_SAC",
      "Sports Complex": "LOC_SPORTS",
      "Other / Not Sure": "LOC_OTHER",
    };
    const templateId = typeToTemplateId[locType] || (locObj ? typeToTemplateId[locObj.name] : null);

    return (departments || []).filter(d =>
      d.location_id === locId ||
      d.location_id === locType ||
      (templateId && d.location_id === templateId)
    );
  }, [editLocation, departments, locations]);

  const availableEditIssues = useMemo(() => {
    if (!editLocation || !editDepartment) return [];

    const deptObj = availableEditDepartments.find(
      d => d.department_id === editDepartment || d.id === editDepartment || d.name === editDepartment
    );
    if (!deptObj) return [];

    return deptObj.complaint_types || [];
  }, [editLocation, editDepartment, availableEditDepartments]);

  const openEditModal = () => {
    if (!selectedComplaint) return;

    const locMatch = (locations || []).find(
      l => l.location_id === selectedComplaint.location_id || l.name === selectedComplaint.location_id
    );
    const locVal = locMatch ? locMatch.location_id : (selectedComplaint.location_id || "");

    const deptMatch = (departments || []).find(
      d => d.department_id === selectedComplaint.department_id || d.name === selectedComplaint.department_id
    );
    const deptVal = deptMatch ? deptMatch.department_id : (selectedComplaint.department_id || "");

    setEditLocation(locVal);
    setEditDepartment(deptVal);
    setEditType(selectedComplaint.category || selectedComplaint.complaint_type || "");
    setEditDescription(selectedComplaint.description || "");
    setShowEditModal(true);
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!editDescription.trim()) {
      setToast({ type: "error", message: "Description is required." });
      return;
    }
    setEditSubmitting(true);
    try {
      const payload = {
        location_id: editLocation,
        department_id: editDepartment,
        complaint_type: editType,
        category: editType,
        description: editDescription.trim(),
      };
      const res = await complaintService.update(selectedComplaint.complaint_id, payload);
      setSelectedComplaint(res.data);
      setToast({ type: "success", message: "Complaint updated successfully!" });
      setShowEditModal(false);
      fetchData();
    } catch (err) {
      setToast({ type: "error", message: err?.response?.data?.detail || "Failed to update complaint." });
    } finally {
      setEditSubmitting(false);
    }
  };

  const handleDeleteComplaint = () => {
    if (!selectedComplaint) return;
    setConfirmAction({
      title: "Delete Complaint",
      message: "Are you sure you want to delete this complaint? It will be soft-deleted and removed from active public complaints.",
      confirmLabel: "Delete Complaint",
      tone: "danger",
      action: async () => {
        try {
          await complaintService.delete(selectedComplaint.complaint_id);
          setToast({ type: "success", message: "Complaint deleted successfully." });
          setSelectedComplaint(null);
          setLevel(3);
          fetchData();
        } catch (err) {
          setToast({ type: "error", message: err?.response?.data?.detail || "Failed to delete complaint." });
        }
      },
    });
  };

  useEffect(() => {
    fetchData();

    const handleLiveSync = () => fetchData(true);
    window.addEventListener("campus-pulse-ws-event", handleLiveSync);
    window.addEventListener("campus-pulse-reconnected", handleLiveSync);
    window.addEventListener("campus-pulse-poll", handleLiveSync);

    return () => {
      window.removeEventListener("campus-pulse-ws-event", handleLiveSync);
      window.removeEventListener("campus-pulse-reconnected", handleLiveSync);
      window.removeEventListener("campus-pulse-poll", handleLiveSync);
    };
  }, []);

  const fetchData = async (silent = false) => {
    if (!silent) setLoading(true);
    try {
      const [locRes, deptRes, compRes] = await Promise.all([
        locationService.list().catch(() => ({ data: [] })),
        departmentService.list().catch(() => ({ data: [] })),
        complaintService.list().catch(() => ({ data: [] })),
      ]);
      setLocations(locRes.data || []);
      setDepartments(deptRes.data || []);

      // Filter only Public complaints
      const pubComps = (compRes.data || []).filter(
        (c) => c.visibility_type === "Public" || c.visibility === "Public",
      );
      setComplaints(pubComps);
    } catch (err) {
      if (!silent) {
        setToast({
          type: "error",
          message: "Failed to load public complaints data.",
        });
      }
    } finally {
      if (!silent) setLoading(false);
    }
  };

  // Flexible matching helpers
  const isLocationMatch = (c, locObj) => {
    if (!locObj) return true;
    const term = (locObj.id || locObj.name || "").toLowerCase().replace(/[^a-z0-9]/g, "");
    const cId = (c.location_id || "").toLowerCase().replace(/[^a-z0-9]/g, "");
    const cName = (c.location_name || "").toLowerCase().replace(/[^a-z0-9]/g, "");
    if (term.includes("hostel")) return cId.includes("hostel") || cName.includes("hostel");
    if (term.includes("mess")) return cId.includes("mess") || cName.includes("mess");
    if (term.includes("academic")) return cId.includes("academic") || cName.includes("academic");
    return cId.includes(term) || cName.includes(term) || term.includes(cId);
  };

  const isDeptMatch = (c, deptObj) => {
    if (!deptObj) return true;
    const term = (deptObj.id || deptObj.name || "").toLowerCase().replace(/[^a-z0-9]/g, "");
    const cId = (c.department_id || "").toLowerCase().replace(/[^a-z0-9]/g, "");
    const cName = (c.department_name || "").toLowerCase().replace(/[^a-z0-9]/g, "");
    return cId.includes(term) || cName.includes(term) || term.includes(cId);
  };

  // Level 1: Location Summaries (hides locations with 0 complaints, keeps parent if child has complaints)
  const locationSummaries = useMemo(() => {
    const map = {};

    // Build location map entirely from API data
    locations.forEach((l) => {
      const id = l.name || l.location_id;
      if (!map[id]) {
        map[id] = {
          id: id,
          name: l.name || l.location_id,
          openCount: 0,
          affectedCount: 0,
        };
      }
    });

    complaints.forEach((c) => {
      const matchedLocKey = Object.keys(map).find((k) => isLocationMatch(c, { id: k, name: map[k].name }));
      if (matchedLocKey && map[matchedLocKey]) {
        if (!["Closed", "Closed (Auto Closed)"].includes(c.status)) {
          map[matchedLocKey].openCount += 1;
          map[matchedLocKey].affectedCount += (c.affected_count || 1);
        }
      }
    });

    // Hide locations with 0 active/open complaints
    return Object.values(map)
      .filter((loc) => loc.openCount > 0)
      .sort((a, b) => b.affectedCount - a.affectedCount);
  }, [locations, complaints]);

  // Level 2: Department Summaries for selected location (hides departments with 0 complaints)
  const deptSummaries = useMemo(() => {
    if (!selectedLocation) return [];

    const baseDepts = departments.length > 0
      ? departments.map((d) => ({ id: d.department_id, name: d.name }))
      : [
          { id: "DEPT_HOSTEL_ELECTRICAL", name: "Electrical" },
          { id: "DEPT_PLUMBING", name: "Plumbing" },
          { id: "DEPT_MAINTENANCE", name: "Maintenance" },
          { id: "DEPT_HOUSEKEEPING", name: "Housekeeping" },
          { id: "DEPT_NETWORK", name: "Network" },
        ];

    return baseDepts
      .map((dept) => {
        let openCount = 0;
        let affectedCount = 0;

        complaints.forEach((c) => {
          if (isLocationMatch(c, selectedLocation) && isDeptMatch(c, dept)) {
            if (!["Closed", "Closed (Auto Closed)"].includes(c.status)) {
              openCount += 1;
              affectedCount += (c.affected_count || 1);
            }
          }
        });

        return {
          id: dept.id,
          name: dept.name,
          openCount,
          affectedCount,
        };
      })
      .filter((dept) => dept.openCount > 0); // Hide departments with 0 complaints
  }, [selectedLocation, departments, complaints]);

  // Options for Top Dropdowns (derived strictly from active complaint summaries)
  const allLocationOptions = useMemo(() => {
    return locationSummaries.map((loc) => ({ id: loc.id, name: loc.name }));
  }, [locationSummaries]);

  const allDeptOptions = useMemo(() => {
    return deptSummaries.map((dept) => ({ id: dept.id, name: dept.name }));
  }, [deptSummaries]);

  const handleLocationSelect = (locId) => {
    if (!locId) {
      setSelectedLocation(null);
      setSelectedDept(null);
      setSelectedComplaint(null);
      setLevel(1);
    } else {
      const found = allLocationOptions.find((l) => l.id === locId) || { id: locId, name: locId };
      setSelectedLocation(found);
      setSelectedComplaint(null);
      if (level === 3 && selectedDept) {
        setLevel(3);
      } else {
        setLevel(2); // Always go to Step 2 (Select Department) for selected location
      }
    }
  };

  const handleDeptSelect = (deptId) => {
    if (!deptId) {
      setSelectedDept(null);
      setSelectedComplaint(null);
      if (selectedLocation) {
        setLevel(2);
      } else {
        setLevel(1);
      }
    } else {
      const found = allDeptOptions.find((d) => d.id === deptId) || { id: deptId, name: deptId };
      setSelectedDept(found);
      setSelectedComplaint(null);
      if (!selectedLocation) {
        setSelectedLocation({ id: "Hostel", name: "Hostel" });
      }
      setLevel(3); // Go to Step 3 (Complaints list) for selected department
    }
  };

  const getBackLabel = (lvl) => {
    if (lvl === 2) return "Back to Locations (Step 1)";
    if (lvl === 3) return "Back to Departments (Step 2)";
    if (lvl === 4) return "Back to Complaints List (Step 3)";
    return "Back";
  };

  const handleBackClick = () => {
    if (level === 4) {
      setLevel(3);
    } else if (level === 3) {
      setLevel(2);
      setSelectedDept(null);
    } else if (level === 2) {
      setLevel(1);
      setSelectedLocation(null);
      setSelectedDept(null);
    }
  };

  const resetAllFilters = () => {
    setSelectedLocation(null);
    setSelectedDept(null);
    setSelectedComplaint(null);
    setSearchQuery("");
    setStatusFilter("");
    setLevel(1);
  };

  // Level 3: Filtered Complaint List
  const filteredComplaints = useMemo(() => {
    return complaints.filter((c) => {
      const locMatch = !selectedLocation || isLocationMatch(c, selectedLocation);
      const deptMatch = !selectedDept || isDeptMatch(c, selectedDept);
      const statusMatch = !statusFilter || c.status === statusFilter;
      const searchMatch = !searchQuery || [
        c.title, c.complaint_id, c.description, c.location_name, c.department_name
      ].some((v) => v && v.toLowerCase().includes(searchQuery.toLowerCase()));

      return locMatch && deptMatch && statusMatch && searchMatch;
    });
  }, [selectedLocation, selectedDept, searchQuery, statusFilter, complaints]);

  const [submittingAffected, setSubmittingAffected] = useState(false);

  const handleMarkAffected = async () => {
    if (!selectedComplaint || submittingAffected) return;
    setSubmittingAffected(true);
    try {
      await complaintService.markAffected(selectedComplaint.complaint_id, {
        info: affectedInfo,
      });
      setToast({
        type: "success",
        message: "Registered as affected student! Count updated.",
      });
      setShowAffectedModal(false);
      setAffectedInfo("");
      setSelectedComplaint((prev) =>
        prev
          ? { ...prev, affected_count: (prev.affected_count || 1) + 1 }
          : null,
      );
    } catch (err) {
      setToast({
        type: "error",
        message: err?.response?.data?.detail || "Could not mark as affected.",
      });
    } finally {
      setSubmittingAffected(false);
    }
  };

  const handleFollowToggle = () => {
    setFollowing(!following);
    setToast({
      type: "success",
      message: following
        ? "Unfollowed complaint updates."
        : "Now following public complaint updates!",
    });
  };

  if (loading) return <Loader label="Loading public complaints..." />;

  return (
    <div className="space-y-6">
        {toast && (
          <Toast
            tone={toast.type}
            message={toast.message}
            onClose={() => setToast(null)}
          />
        )}

        <div>
          {level > 1 && (
            <button
              onClick={handleBackClick}
              className="inline-flex items-center gap-1.5 text-xs font-bold text-primary hover:underline mb-2 transition-colors"
            >
              <ArrowLeft className="h-4 w-4" /> {getBackLabel(level)}
            </button>
          )}
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 dark:bg-indigo-950/50 text-indigo-600 dark:text-indigo-400">
              <Globe className="h-5 w-5" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">
                🌍 Public Complaints
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Explore transparent community issues, track official progress
                updates, and mark affected status.
              </p>
            </div>
          </div>
        </div>

        {/* Sequential Step Progress Indicator */}
        <div className="flex flex-wrap items-center gap-2 text-xs font-bold text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-900 p-3 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xs">
          <button
            onClick={() => { setLevel(1); setSelectedLocation(null); setSelectedDept(null); }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all ${
              level === 1 ? "bg-primary text-white shadow-xs font-extrabold" : "bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200"
            }`}
          >
            <span>Step 1 — Select Location</span>
          </button>

          <ChevronRight className="h-4 w-4 text-slate-400 dark:text-slate-600 shrink-0" />

          <button
            onClick={() => { if (selectedLocation) setLevel(2); }}
            disabled={!selectedLocation}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all ${
              level === 2 ? "bg-primary text-white shadow-xs font-extrabold" : selectedLocation ? "bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 cursor-pointer" : "bg-slate-50 dark:bg-slate-800/40 text-slate-300 dark:text-slate-600 cursor-not-allowed"
            }`}
          >
            <span>Step 2 — Select Department {selectedLocation ? `(${selectedLocation.name})` : ""}</span>
          </button>

          <ChevronRight className="h-4 w-4 text-slate-400 dark:text-slate-600 shrink-0" />

          <button
            onClick={() => { if (selectedLocation && selectedDept) setLevel(3); }}
            disabled={!selectedLocation || !selectedDept}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all ${
              level === 3 ? "bg-primary text-white shadow-xs font-extrabold" : selectedLocation && selectedDept ? "bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 cursor-pointer" : "bg-slate-50 dark:bg-slate-800/40 text-slate-300 dark:text-slate-600 cursor-not-allowed"
            }`}
          >
            <span>Step 3 — Complaints List {selectedDept ? `(${selectedDept.name})` : ""}</span>
          </button>

          {level === 4 && (
            <>
              <ChevronRight className="h-4 w-4 text-slate-400 dark:text-slate-600 shrink-0" />
              <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-primary text-white font-extrabold shadow-xs">
                <span>Step 4 — Ticket Details</span>
              </span>
            </>
          )}
        </div>

        {/* Top Filter Bar — Always Visible Across All Levels */}
        <Card className="p-4 bg-slate-50/90 dark:bg-slate-900/90 border border-slate-200 dark:border-slate-800 shadow-xs">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-2.5">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider">
              <Filter className="h-4 w-4 text-primary" />
              <span>Location & Filter Options (Available at Every Level)</span>
            </div>
            {(selectedLocation || selectedDept || searchQuery || statusFilter || level > 1) && (
              <button
                type="button"
                onClick={resetAllFilters}
                className="text-xs font-semibold text-primary hover:underline flex items-center gap-1"
              >
                <RotateCw className="h-3 w-3" />
                Reset All Filters
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            {/* 📍 Location Dropdown */}
            <div>
              <label className="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">
                📍 Step 1 — Select Location
              </label>
              <select
                value={selectedLocation?.id || ""}
                onChange={(e) => handleLocationSelect(e.target.value)}
                className="h-10 w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-800 dark:text-slate-100 outline-none focus:border-primary focus:ring-1 focus:ring-primary cursor-pointer shadow-xs"
              >
                <option value="">All Locations (Overview)</option>
                {allLocationOptions.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name}
                  </option>
                ))}
              </select>
            </div>

            {/* 🏢 Department Dropdown */}
            <div>
              <label className="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">
                🏢 Step 2 — Select Department
              </label>
              <select
                value={selectedDept?.id || ""}
                disabled={!selectedLocation}
                onChange={(e) => handleDeptSelect(e.target.value)}
                className={`h-10 w-full rounded-xl border border-slate-200 dark:border-slate-700 px-3 text-xs font-semibold outline-none focus:border-primary focus:ring-1 focus:ring-primary shadow-xs ${
                  !selectedLocation
                    ? "bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 cursor-not-allowed"
                    : "bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-100 cursor-pointer"
                }`}
              >
                <option value="">
                  {selectedLocation ? "Select a Department..." : "Select Location First (Step 1)"}
                </option>
                {allDeptOptions.map((dept) => (
                  <option key={dept.id} value={dept.id}>
                    {dept.name} ({dept.openCount} open)
                  </option>
                ))}
              </select>
            </div>

            {/* 📌 Status Filter Dropdown */}
            <div>
              <label className="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">
                📌 Status
              </label>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value);
                  if (e.target.value && level === 1 && !selectedLocation) {
                    setLevel(3);
                  }
                }}
                className="h-10 w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-800 dark:text-slate-100 outline-none focus:border-primary focus:ring-1 focus:ring-primary cursor-pointer shadow-xs"
              >
                <option value="">All Statuses</option>
                <option value="Submitted">Submitted</option>
                <option value="In Progress">In Progress</option>
                <option value="Resolved">Resolved</option>
                <option value="Closed">Closed</option>
              </select>
            </div>

            {/* 🔍 Search Input */}
            <div>
              <label className="block text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">
                🔍 Search Public Complaints
              </label>
              <div className="relative">
                <Search className="pointer-events-none absolute left-3 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search title, ID, location..."
                  value={searchQuery}
                  onChange={(e) => {
                    setSearchQuery(e.target.value);
                    if (e.target.value && level === 1) {
                      setLevel(3);
                    }
                  }}
                  className="h-10 w-full rounded-xl border border-slate-200 bg-white pl-9 pr-3 text-xs font-semibold text-slate-800 outline-none focus:border-primary focus:ring-1 focus:ring-primary shadow-xs"
                />
              </div>
            </div>
          </div>
        </Card>

        {/* Level 1: Locations */}
        {level === 1 && (
          <div className="space-y-4">
            <h2 className="text-sm font-bold text-slate-700 uppercase tracking-wider">
              Level 1 — Select Location
            </h2>
            {locationSummaries.length === 0 ? (
              <Card className="p-8 text-center bg-slate-50 border border-slate-200 rounded-2xl">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 text-emerald-600 mb-3">
                  <Globe className="h-6 w-6" />
                </div>
                <h3 className="text-base font-bold text-slate-800">No Open Public Complaints</h3>
                <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
                  There are currently no open public complaints registered in the system.
                </p>
              </Card>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {locationSummaries.map((loc) => (
                  <Card
                    key={loc.id}
                    className="cursor-pointer hover:border-primary hover:shadow-md transition-all flex flex-col justify-between"
                    onClick={() => {
                      setSelectedLocation(loc);
                      setLevel(2);
                    }}
                  >
                    <div>
                      <div className="text-lg font-bold text-slate-900 mb-2">
                        {loc.name}
                      </div>
                      <div className="space-y-1 text-xs text-slate-600">
                        <div className="flex justify-between">
                          <span>Affected Students:</span>
                          <strong className="text-indigo-600">
                            {loc.affectedCount}
                          </strong>
                        </div>
                        <div className="flex justify-between">
                          <span>Open Complaints:</span>
                          <strong className="text-slate-800">
                            {loc.openCount}
                          </strong>
                        </div>
                      </div>
                    </div>
                    <div className="mt-4 flex items-center justify-between text-xs font-bold text-primary">
                      <span>View Departments</span>
                      <ChevronRight className="h-4 w-4" />
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Level 2: Departments */}
        {level === 2 && selectedLocation && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-xs text-slate-500 font-semibold">
              <span>{selectedLocation.name}</span>
              <ChevronRight className="h-3 w-3" />
              <span className="text-slate-900">Departments</span>
            </div>
            <h2 className="text-sm font-bold text-slate-700 uppercase tracking-wider">
              Level 2 — Select Department
            </h2>
            <div className="grid gap-4 sm:grid-cols-3">
              {deptSummaries.map((dept) => (
                <Card
                  key={dept.name}
                  className="cursor-pointer hover:border-primary hover:shadow-md transition-all"
                  onClick={() => {
                    setSelectedDept(dept);
                    setLevel(3);
                  }}
                >
                  <div className="text-base font-bold text-slate-900 mb-2">
                    {dept.name}
                  </div>
                  <div className="space-y-1 text-xs text-slate-600">
                    <div className="flex justify-between">
                      <span>Affected Students:</span>
                      <strong className="text-indigo-600">
                        {dept.affectedCount}
                      </strong>
                    </div>
                    <div className="flex justify-between">
                      <span>Open Complaints:</span>
                      <strong className="text-slate-800">
                        {dept.openCount}
                      </strong>
                    </div>
                  </div>
                  <div className="mt-4 flex items-center justify-between text-xs font-bold text-primary">
                    <span>View Complaints List</span>
                    <ChevronRight className="h-4 w-4" />
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Level 3: Complaint List */}
        {level === 3 && selectedLocation && selectedDept && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-xs text-slate-500 font-semibold">
              <span>{selectedLocation.name}</span>
              <ChevronRight className="h-3 w-3" />
              <span>{selectedDept.name}</span>
              <ChevronRight className="h-3 w-3" />
              <span className="text-slate-900">Complaints List</span>
            </div>
            <h2 className="text-sm font-bold text-slate-700 uppercase tracking-wider">
              Level 3 — Public Complaints List
            </h2>

            <div className="grid gap-3">
              {filteredComplaints.length === 0 ? (
                <Card className="text-center py-8 text-slate-500 text-sm">
                  No public complaints filed for this department location yet.
                </Card>
              ) : (
                filteredComplaints.map((c) => (
                  <Card
                    key={c.complaint_id}
                    className="cursor-pointer hover:border-primary transition-all flex flex-wrap items-center justify-between gap-4"
                    onClick={() => {
                      setSelectedComplaint(c);
                      setLevel(4);
                    }}
                  >
                    <div className="space-y-1">
                      <div className="font-bold text-slate-900 text-base">
                        {c.title}
                      </div>
                      <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                        <span className="font-semibold text-slate-700">
                          Type: <strong className="text-indigo-700">{c.category || c.complaint_type || "General Issue"}</strong>
                        </span>
                        <span>•</span>
                        <span>
                          Affected Students:{" "}
                          <strong className="text-indigo-600">
                            {c.affected_count || 1}
                          </strong>
                        </span>
                        <span>•</span>
                        <span>
                          Priority: <strong>{c.priority || "Normal"}</strong>
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge tone={getStatusTone(c.status)}>{c.status}</Badge>
                      <ChevronRight className="h-5 w-5 text-slate-400" />
                    </div>
                  </Card>
                ))
              )}
            </div>
          </div>
        )}

        {/* Level 4: Complaint Details */}
        {level === 4 && selectedComplaint && (
          <div className="space-y-6">
            <div className="flex items-center gap-2 text-xs text-slate-500 font-semibold">
              <span>{selectedLocation?.name}</span>
              <ChevronRight className="h-3 w-3" />
              <span>{selectedDept?.name}</span>
              <ChevronRight className="h-3 w-3" />
              <span className="text-slate-900">
                {selectedComplaint.complaint_id}
              </span>
            </div>

            <Card className="space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
                <div>
                  <h1 className="text-xl font-bold text-slate-900">
                    {selectedComplaint.title}
                  </h1>
                  <div className="mt-1 flex items-center gap-3 text-xs text-slate-500 font-medium">
                    <span>
                      ID: <strong>{selectedComplaint.complaint_id}</strong>
                    </span>
                    <span>•</span>
                    <span>
                      Filed: {formatDate(selectedComplaint.created_at)}
                    </span>
                    <span>•</span>
                    <span>
                      Affected Students:{" "}
                      <strong className="text-indigo-600">
                        {selectedComplaint.affected_count || 1}
                      </strong>
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {canStudentEditOrDelete && (
                    <button
                      type="button"
                      onClick={handleDeleteComplaint}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 rounded-xl transition-all shadow-xs cursor-pointer active:scale-95"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Delete
                    </button>
                  )}
                  <Badge tone={getStatusTone(selectedComplaint.status)}>
                    {selectedComplaint.status}
                  </Badge>
                  <Badge tone="warning">
                    {selectedComplaint.priority || "Normal"}
                  </Badge>
                </div>
              </div>

              {/* Location, Department & Issue Type Metadata Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 bg-slate-50 p-4 rounded-xl border border-slate-100 text-xs">
                <div>
                  <span className="text-slate-400 font-semibold block">Location</span>
                  <span className="font-bold text-slate-800">
                    {selectedComplaint.location_name || selectedComplaint.location_id || selectedLocation?.name || "Campus"}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 font-semibold block">Department</span>
                  <span className="font-bold text-slate-800">
                    {selectedComplaint.department_name || selectedComplaint.department_id || selectedDept?.name || "General"}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 font-semibold block">Type / Issue</span>
                  <span className="font-bold text-indigo-700">
                    {selectedComplaint.category || selectedComplaint.complaint_type || "General Issue"}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 font-semibold block">Created Date</span>
                  <span className="font-bold text-slate-800">
                    {formatDate(selectedComplaint.created_at)}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 font-semibold block">Status</span>
                  <span className="font-bold text-slate-800">
                    {selectedComplaint.status}
                  </span>
                </div>
              </div>

              {/* Description */}
              <div>
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
                  Description
                </h3>
                <p className="text-sm text-slate-700 bg-slate-50 p-4 rounded-xl border border-slate-100">
                  {selectedComplaint.description}
                </p>
              </div>

              {/* Official Progress Updates */}
              <div>
                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <MessageSquare className="h-4 w-4 text-primary" /> Official
                  Progress Updates (Coordinator & Warden)
                </h3>
                <div className="space-y-3">
                  {(
                    selectedComplaint.history || [
                      {
                        at: selectedComplaint.created_at,
                        message:
                          "Official progress update: Repair work has been initiated by Coordinator.",
                      },
                    ]
                  ).map((update, idx) => (
                    <div
                      key={idx}
                      className="rounded-xl border border-blue-100 bg-blue-50/40 p-3 text-xs"
                    >
                      <div className="flex justify-between font-bold text-slate-800">
                        <span>👨🔧 Staff Progress Update</span>
                        <span className="text-[10px] text-slate-400">
                          {formatDate(update.at)}
                        </span>
                      </div>
                      <p className="mt-1 text-slate-600">{update.message}</p>
                    </div>
                  ))}
                </div>
                <div className="mt-2 text-[11px] text-slate-400 italic">
                  Note: Official updates are provided by Coordinators and
                  Wardens. Students cannot post comments or replies.
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-4 border-t border-slate-100">
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={() => setShowAffectedModal(true)}
                    className="flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-xs font-bold text-white shadow-sm hover:bg-primary/90"
                  >
                    <Users className="h-4 w-4" /> I'm Also Affected
                  </button>

                  <button
                    onClick={handleFollowToggle}
                    className={`flex items-center gap-2 rounded-xl border px-5 py-2.5 text-xs font-bold transition-all ${
                      following
                        ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                        : "border-slate-300 text-slate-700 hover:bg-slate-50"
                    }`}
                  >
                    <Bell className="h-4 w-4" />{" "}
                    {following ? "Following Complaint" : "Follow Complaint"}
                  </button>
                </div>

                <Link
                  to={`/complaints/${selectedComplaint.complaint_id}`}
                  className="text-xs font-bold text-primary hover:underline flex items-center gap-1"
                >
                  Open Full Ticket Details →
                </Link>
              </div>
            </Card>
          </div>
        )}

        {/* Affected Modal */}
        {showAffectedModal && (
          <Modal
            isOpen={true}
            onClose={() => setShowAffectedModal(false)}
            title="I'm Also Affected"
          >
            <div className="space-y-4">
              <p className="text-xs text-slate-600">
                Increment the affected student count for{" "}
                <strong>{selectedComplaint?.title}</strong> and receive progress
                updates.
              </p>
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Additional Information (Optional)
                </label>
                <textarea
                  value={affectedInfo}
                  onChange={(e) => setAffectedInfo(e.target.value)}
                  placeholder="e.g. Affected in my block/room as well..."
                  className="w-full rounded-xl border border-slate-300 p-2.5 text-xs"
                  rows={3}
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button
                  onClick={() => setShowAffectedModal(false)}
                  className="rounded-xl px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  onClick={handleMarkAffected}
                  disabled={submittingAffected}
                  className="rounded-xl bg-primary px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-primary/90 disabled:opacity-50"
                >
                  {submittingAffected ? "Submitting..." : "Submit Affected Report"}
                </button>
              </div>
            </div>
          </Modal>
        )}

        {/* Edit Complaint Modal for Students */}
        {showEditModal && (
          <Modal
            isOpen={showEditModal}
            onClose={() => setShowEditModal(false)}
            title="✏️ Edit Complaint Details"
          >
            <form onSubmit={handleEditSubmit} className="space-y-4">
              <p className="text-xs text-slate-500 mb-3">
                Update details while status is <strong>Submitted</strong>. Correcting information re-validates against our campus taxonomy.
              </p>

              <Select
                label="Step 1 — Select Location"
                value={editLocation}
                onChange={(e) => {
                  setEditLocation(e.target.value);
                  setEditDepartment("");
                  setEditType("");
                }}
              >
                <option value="">Choose Location</option>
                {locations.map((loc) => (
                  <option key={loc.location_id} value={loc.location_id}>
                    {loc.name}
                  </option>
                ))}
              </Select>

              <Select
                label="Step 2 — Select Department"
                disabled={!editLocation}
                value={editDepartment}
                onChange={(e) => {
                  setEditDepartment(e.target.value);
                  setEditType("");
                }}
              >
                <option value="">{editLocation ? "Choose Department" : "Select Location First..."}</option>
                {availableEditDepartments.map((dept) => (
                  <option key={dept.id} value={dept.id}>
                    {dept.name}
                  </option>
                ))}
              </Select>

              <Select
                label="Step 3 — Select Issue / Type"
                disabled={!editDepartment}
                value={editType}
                onChange={(e) => setEditType(e.target.value)}
              >
                <option value="">{editDepartment ? "Choose Issue" : "Select Department First..."}</option>
                {availableEditIssues.map((issue, idx) => (
                  <option key={`${issue}-${idx}`} value={issue}>
                    {issue}
                  </option>
                ))}
              </Select>

              <Textarea
                label="Step 4 — Description"
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                placeholder="Describe your issue clearly..."
                rows={4}
                required
              />

              <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
                <Button
                  type="button"
                  variant="subtle"
                  onClick={() => setShowEditModal(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  disabled={editSubmitting}
                >
                  {editSubmitting ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </form>
          </Modal>
        )}

        <ConfirmDialog
          open={Boolean(confirmAction)}
          title={confirmAction?.title}
          message={confirmAction?.message}
          confirmLabel={confirmAction?.confirmLabel}
          tone={confirmAction?.tone}
          onCancel={() => setConfirmAction(null)}
          onConfirm={() => {
            const action = confirmAction?.action;
            setConfirmAction(null);
            action?.();
          }}
        />
    </div>
  );
}
