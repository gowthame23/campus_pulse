import { useMemo, useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import {
  PlusCircle,
  RotateCw,
  Edit2,
  Archive,
  Trash2,
  RefreshCw,
  MapPin,
  Building,
  AlertTriangle,
  CheckCircle2,
  Network,
  Layers,
  Clock,
  Sliders,
  Shield,
  UserCheck,
  Users,
  MessageSquare,
  ChevronDown,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import Badge from "../../components/Badge.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Input from "../../components/Input.jsx";
import Loader from "../../components/Loader.jsx";
import PageHeader from "../../components/PageHeader.jsx";
import Select from "../../components/Select.jsx";
import Table from "../../components/Table.jsx";
import Toast from "../../components/Toast.jsx";
import Modal from "../../components/Modal.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { departmentService } from "../../services/departmentService.js";
import { userService } from "../../services/userService.js";
import { locationService } from "../../services/locationService.js";
import { useAuth } from "../../context/AuthContext.jsx";
import { ROLES } from "../../utils/constants.js";
import { getApiError } from "../../api/axios.js";

// Clean, user-friendly Time Select Component that avoids browser-native ugly drop-down lists
function CleanTimeSelect({ value, onChange, className = "" }) {
  // Common hourly options with standard formatting
  const timeOptions = useMemo(() => {
    const list = [];
    for (let h = 0; h < 24; h++) {
      const hh = String(h).padStart(2, "0");
      const hour12 = h === 0 ? 12 : h > 12 ? h - 12 : h;
      const ampm = h >= 12 ? "PM" : "AM";
      list.push({ value: `${hh}:00`, label: `${hour12}:00 ${ampm}` });
      if (h === 23) {
        list.push({ value: `23:59`, label: `11:59 PM (Midnight)` });
      }
    }
    return list;
  }, []);

  return (
    <div className="relative inline-flex items-center">
      <select
        value={value || "10:00"}
        onChange={(e) => onChange(e.target.value)}
        className={`appearance-none h-8.5 pl-2.5 pr-7 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs font-semibold text-slate-800 dark:text-slate-200 shadow-2xs hover:border-primary/50 focus:border-primary focus:ring-1 focus:ring-primary/20 outline-none transition-all cursor-pointer ${className}`}
      >
        {timeOptions.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
        {/* Fallback if a custom value isn't in hourly presets */}
        {value && !timeOptions.some((o) => o.value === value) && (
          <option value={value}>{value}</option>
        )}
      </select>
      <Clock className="pointer-events-none absolute right-2 h-3.5 w-3.5 text-slate-400" />
    </div>
  );
}

export default function DepartmentManagementPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const isAdmin = ["administrator", "super_admin"].includes((user?.role || "").toLowerCase());

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState("");
  const [viewMode, setViewMode] = useState("grid"); // "grid" | "hierarchy"
  const [expandedLocations, setExpandedLocations] = useState({});

  const toggleLocationExpand = (locId) => {
    setExpandedLocations((prev) => ({
      ...prev,
      [locId]: !prev[locId],
    }));
  };

  const expandAllLocations = (locList) => {
    const next = {};
    (locList || []).forEach((l) => {
      next[l.location_id] = true;
    });
    setExpandedLocations(next);
  };

  const collapseAllLocations = () => {
    setExpandedLocations({});
  };

  useEffect(() => {
    if (selectedLocation) {
      setExpandedLocations((prev) => ({
        ...prev,
        [selectedLocation]: true,
      }));
    }
  }, [selectedLocation]);

  // Department SLA Config State
  const [slaDeptId, setSlaDeptId] = useState("");
  const [slaLoading, setSlaLoading] = useState(false);
  const [slaSaving, setSlaSaving] = useState(false);
  const [isEscalationOpen, setIsEscalationOpen] = useState(false);
  const [slaConfig, setSlaConfig] = useState({
    normal_start_time: "10:00",
    normal_end_time: "16:00",
    normal_duration_hours: 72,
    medium_start_time: "10:00",
    medium_end_time: "16:00",
    medium_duration_hours: 48,
    high_start_time: "10:00",
    high_end_time: "18:00",
    high_duration_hours: 24,
    critical_start_time: "00:00",
    critical_end_time: "23:59",
    critical_duration_hours: 4,
    app_manager_escalation_hours: 24,
    admin_escalation_hours: 48,
  });

  // Create Department State
  const [createLocationIds, setCreateLocationIds] = useState([]);

  // Edit State
  const [editTarget, setEditTarget] = useState(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editSla, setEditSla] = useState("");
  const [editComplaintTypes, setEditComplaintTypes] = useState("");
  const [editLocationIds, setEditLocationIds] = useState([]);

  // Operating Locations Modal State
  const [viewLocationsTarget, setViewLocationsTarget] = useState(null);
  const [modalLocationIds, setModalLocationIds] = useState([]);
  const [locModalSaving, setLocModalSaving] = useState(false);

  // Eligible Workforce Modal State
  const [viewWorkforceTarget, setViewWorkforceTarget] = useState(null);
  const [eligibleStaff, setEligibleStaff] = useState([]);
  const [eligibleStaffLoading, setEligibleStaffLoading] = useState(false);

  // Delete Confirmation State
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteInput, setDeleteInput] = useState("");
  const [deleteDependencyError, setDeleteDependencyError] = useState("");

  // Categories Modal State
  const [viewCategoriesTarget, setViewCategoriesTarget] = useState(null);
  const [categoryModalDept, setCategoryModalDept] = useState(null);
  const [categoryList, setCategoryList] = useState([]);
  const [newCategoryInput, setNewCategoryInput] = useState("");
  const [categoryModalSaving, setCategoryModalSaving] = useState(false);

  // Manage Department Coordinators Modal State
  const [assignCoordsTarget, setAssignCoordsTarget] = useState(null);
  const [eligibleCoords, setEligibleCoords] = useState([]);
  const [eligibleCoordsLoading, setEligibleCoordsLoading] = useState(false);
  const [c1Selected, setC1Selected] = useState("");
  const [c2Selected, setC2Selected] = useState("");
  const [coordsModalError, setCoordsModalError] = useState("");
  const [savingCoords, setSavingCoords] = useState(false);

  // Edit Timings & SLA Modal State
  const [timingModalDept, setTimingModalDept] = useState(null);
  const [timingModalConfig, setTimingModalConfig] = useState(null);
  const [timingModalLoading, setTimingModalLoading] = useState(false);
  const [timingModalSaving, setTimingModalSaving] = useState(false);
  const [timingModalError, setTimingModalError] = useState("");

  const { data, loading, reload } = useAsyncData(async () => {
    const [locationsRes, coordinatorsRes, coverageGapsRes] = await Promise.all([
      locationService.list().catch(() => ({ data: [] })),
      userService.list().catch(() => ({ data: [] })),
      departmentService
        .getCoverageGaps()
        .catch(() => ({ data: { unassigned_pairs: [], unassigned_warden_locations: [] } })),
    ]);

    const departmentsRes = await departmentService.list({
      include_archived: showArchived,
      location_id: selectedLocation || undefined,
    });

    return {
      locations: locationsRes.data || [],
      departments: departmentsRes.data || [],
      coordinators: coordinatorsRes.data || [],
      coverageGaps: coverageGapsRes.data || { unassigned_pairs: [], unassigned_warden_locations: [] },
    };
  }, [showArchived, selectedLocation]);

  useEffect(() => {
    if (data?.departments?.length > 0 && !slaDeptId) {
      setSlaDeptId(data.departments[0].department_id);
    }
  }, [data?.departments, slaDeptId]);

  useEffect(() => {
    if (!slaDeptId) return;
    let isSubscribed = true;
    const fetchSla = async () => {
      try {
        setSlaLoading(true);
        const res = await departmentService.getSlaConfig(slaDeptId);
        if (isSubscribed && res?.data) {
          setSlaConfig(res.data);
        }
      } catch (err) {
        console.error("Failed to load SLA config:", err);
      } finally {
        if (isSubscribed) setSlaLoading(false);
      }
    };
    fetchSla();
    return () => { isSubscribed = false; };
  }, [slaDeptId]);

  const handleSaveSlaConfig = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");

    const appMgrHours = Number(slaConfig.app_manager_escalation_hours);
    const adminHours = Number(slaConfig.admin_escalation_hours);

    // Mandatory Escalation Ordering Rule:
    // app_manager_escalation_hours < admin_escalation_hours
    if (appMgrHours >= adminHours) {
      setError("App Manager escalation time must be less than Admin escalation time.");
      return;
    }

    try {
      setSlaSaving(true);
      const payload = {
        normal_start_time: slaConfig.normal_start_time,
        normal_end_time: slaConfig.normal_end_time,
        normal_duration_hours: Number(slaConfig.normal_duration_hours),
        medium_start_time: slaConfig.medium_start_time,
        medium_end_time: slaConfig.medium_end_time,
        medium_duration_hours: Number(slaConfig.medium_duration_hours),
        high_start_time: slaConfig.high_start_time,
        high_end_time: slaConfig.high_end_time,
        high_duration_hours: Number(slaConfig.high_duration_hours),
        critical_start_time: slaConfig.critical_start_time,
        critical_end_time: slaConfig.critical_end_time,
        critical_duration_hours: Number(slaConfig.critical_duration_hours),
        app_manager_escalation_hours: appMgrHours,
        ...(isAdmin ? { admin_escalation_hours: adminHours } : {}),
      };

      const res = await departmentService.updateSlaConfig(slaDeptId, payload);
      if (res?.data) {
        setSlaConfig(res.data);
      }
      setMessage("Department SLA and Escalation Settings saved successfully.");
    } catch (err) {
      setError(
        err?.response?.data?.detail || "Unable to save department SLA settings."
      );
    } finally {
      setSlaSaving(false);
    }
  };

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm();

  const renderLocationSelector = (selectedIds, setSelectedIds) => {
    const allLocations = data?.locations || [];
    const toggleLoc = (locId) => {
      setSelectedIds((prev) =>
        prev.includes(locId)
          ? prev.filter((id) => id !== locId)
          : [...prev, locId]
      );
    };

    const selectAll = () => {
      setSelectedIds(allLocations.map((l) => l.location_id));
    };

    const deselectAll = () => {
      setSelectedIds([]);
    };

    return (
      <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-4 bg-slate-50/50 dark:bg-slate-900/50">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
              <MapPin className="h-4 w-4 text-primary" />
              Operating Campus Locations ({selectedIds.length} Selected)
            </h4>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              Select which campus locations this department operates in.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={selectAll}
              className="px-2.5 py-1 text-[11px] font-semibold rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100"
            >
              Select All
            </button>
            <button
              type="button"
              onClick={deselectAll}
              className="px-2.5 py-1 text-[11px] font-semibold rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-700 dark:text-slate-300 hover:bg-slate-100"
            >
              Clear
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2 max-h-48 overflow-y-auto pr-1">
          {allLocations.map((loc) => {
            const isChecked = selectedIds.includes(loc.location_id);
            return (
              <label
                key={loc.location_id}
                className={`flex items-center gap-2.5 p-2 rounded-lg border text-xs cursor-pointer transition-colors ${
                  isChecked
                    ? "bg-primary/10 border-primary/40 text-primary font-bold dark:bg-primary/20"
                    : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 hover:border-slate-300"
                }`}
              >
                <input
                  type="checkbox"
                  checked={isChecked}
                  onChange={() => toggleLoc(loc.location_id)}
                  className="rounded border-slate-300 text-primary focus:ring-primary h-3.5 w-3.5"
                />
                <span className="truncate">{loc.name}</span>
                <span className="text-[10px] text-slate-400 ml-auto shrink-0 uppercase">
                  {loc.location_type || "Campus"}
                </span>
              </label>
            );
          })}
        </div>
      </div>
    );
  };

  const createDepartment = async (values) => {
    setMessage("");
    setError("");

    if (!values.name || !values.name.trim()) {
      setError("Department name is required.");
      return;
    }

    // Check duplicate campus-wide across all central departments
    const normalized = values.name.trim().toLowerCase();
    const duplicate = (data?.departments || []).some(
      (d) => d.name.trim().toLowerCase() === normalized,
    );
    if (duplicate) {
      setError(
        `Department "${values.name.trim()}" already exists. Departments are campus-wide entities; you can associate it with locations rather than creating a duplicate.`,
      );
      return;
    }

    try {
      await departmentService.create({
        name: values.name.trim(),
        description: values.description ? values.description.trim() : "",
        sla_days: Number(values.sla_days),
        complaint_types: values.complaint_types
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        location_ids: createLocationIds,
      });
      reset();
      setCreateLocationIds([]);
      setMessage("Central department created successfully.");
      reload();
    } catch (err) {
      setError(getApiError(err, "Unable to create department."));
    }
  };

  const assignCoordinator = async (departmentId, coordinatorId) => {
    setMessage("");
    setError("");
    try {
      await departmentService.assignCoordinator(departmentId, coordinatorId);
      setMessage("Coordinator assigned successfully.");
      reload();
    } catch (err) {
      setError(getApiError(err, "Unable to assign coordinator."));
    }
  };

  const openAssignCoordsModal = async (department) => {
    setAssignCoordsTarget(department);
    setC1Selected(department.coordinator_id || "");
    setC2Selected(department.coordinator_2_id || "");
    setCoordsModalError("");
    setEligibleCoordsLoading(true);
    try {
      const res = await departmentService.getEligibleCoordinators(department.department_id);
      setEligibleCoords(res.data || res || []);
    } catch (err) {
      console.error("Failed to load eligible coordinators:", err);
      setCoordsModalError("Failed to load eligible coordinators.");
    } finally {
      setEligibleCoordsLoading(false);
    }
  };

  const handleSaveCoordinators = async (e) => {
    if (e) e.preventDefault();
    if (!assignCoordsTarget) return;

    if (c1Selected && c2Selected && c1Selected === c2Selected) {
      setCoordsModalError("Coordinator 1 and Coordinator 2 cannot be the same employee.");
      return;
    }

    setSavingCoords(true);
    setCoordsModalError("");
    try {
      await departmentService.assignDepartmentCoordinators(assignCoordsTarget.department_id, {
        coordinator_1_id: c1Selected || null,
        coordinator_2_id: c2Selected || null,
      });
      setMessage(`Department coordinators updated successfully.`);
      setAssignCoordsTarget(null);
      reload();
    } catch (err) {
      setCoordsModalError(getApiError(err, "Unable to update department coordinators."));
    } finally {
      setSavingCoords(false);
    }
  };

  const openOperatingLocationsModal = (department) => {
    setViewLocationsTarget(department);
    setModalLocationIds(department.location_ids || []);
  };

  const handleSaveLocationsModal = async () => {
    if (!viewLocationsTarget) return;
    setLocModalSaving(true);
    try {
      await departmentService.assignLocations(viewLocationsTarget.department_id, modalLocationIds);
      setMessage(`Operating locations updated for ${viewLocationsTarget.name}.`);
      setViewLocationsTarget(null);
      reload();
    } catch (err) {
      setError(getApiError(err, "Unable to update operating locations."));
    } finally {
      setLocModalSaving(false);
    }
  };

  const openWorkforceModal = async (department) => {
    setViewWorkforceTarget(department);
    setEligibleStaffLoading(true);
    try {
      const res = await departmentService.getEligibleEmployees(department.department_id);
      setEligibleStaff(res.data || res || []);
    } catch (err) {
      console.error("Failed to load eligible workforce:", err);
      setEligibleStaff([]);
    } finally {
      setEligibleStaffLoading(false);
    }
  };

  const openTimingsModal = async (department) => {
    setTimingModalDept(department);
    setTimingModalError("");
    setTimingModalLoading(true);
    try {
      const res = await departmentService.getSlaConfig(department.department_id);
      if (res?.data) {
        setTimingModalConfig({
          ...res.data,
          sla_days: department.sla_days || 3,
        });
      } else {
        setTimingModalConfig({
          normal_start_time: "10:00",
          normal_end_time: "16:00",
          normal_duration_hours: 72,
          medium_start_time: "10:00",
          medium_end_time: "16:00",
          medium_duration_hours: 48,
          high_start_time: "10:00",
          high_end_time: "18:00",
          high_duration_hours: 24,
          critical_start_time: "00:00",
          critical_end_time: "23:59",
          critical_duration_hours: 4,
          app_manager_escalation_hours: 24,
          admin_escalation_hours: 48,
          sla_days: department.sla_days || 3,
        });
      }
    } catch (err) {
      console.error("Failed to load department timings config:", err);
      setTimingModalConfig({
        normal_start_time: "10:00",
        normal_end_time: "16:00",
        normal_duration_hours: 72,
        medium_start_time: "10:00",
        medium_end_time: "16:00",
        medium_duration_hours: 48,
        high_start_time: "10:00",
        high_end_time: "18:00",
        high_duration_hours: 24,
        critical_start_time: "00:00",
        critical_end_time: "23:59",
        critical_duration_hours: 4,
        app_manager_escalation_hours: 24,
        admin_escalation_hours: 48,
        sla_days: department.sla_days || 3,
      });
    } finally {
      setTimingModalLoading(false);
    }
  };

  const handleSaveTimingModal = async (e) => {
    if (e) e.preventDefault();
    if (!timingModalDept || !timingModalConfig) return;
    setTimingModalError("");

    const appMgrHours = Number(timingModalConfig.app_manager_escalation_hours);
    const adminHours = Number(timingModalConfig.admin_escalation_hours);

    if (appMgrHours >= adminHours) {
      setTimingModalError("App Manager escalation time must be strictly less than Admin escalation time.");
      return;
    }

    setTimingModalSaving(true);
    try {
      const payload = {
        normal_start_time: timingModalConfig.normal_start_time,
        normal_end_time: timingModalConfig.normal_end_time,
        normal_duration_hours: Number(timingModalConfig.normal_duration_hours),
        medium_start_time: timingModalConfig.medium_start_time,
        medium_end_time: timingModalConfig.medium_end_time,
        medium_duration_hours: Number(timingModalConfig.medium_duration_hours),
        high_start_time: timingModalConfig.high_start_time,
        high_end_time: timingModalConfig.high_end_time,
        high_duration_hours: Number(timingModalConfig.high_duration_hours),
        critical_start_time: timingModalConfig.critical_start_time,
        critical_end_time: timingModalConfig.critical_end_time,
        critical_duration_hours: Number(timingModalConfig.critical_duration_hours),
        app_manager_escalation_hours: appMgrHours,
        ...(isAdmin ? { admin_escalation_hours: adminHours } : {}),
      };

      await departmentService.updateSlaConfig(timingModalDept.department_id, payload);

      // If sla_days changed, also update the main department record
      if (
        timingModalConfig.sla_days &&
        Number(timingModalConfig.sla_days) !== Number(timingModalDept.sla_days)
      ) {
        await departmentService.update(timingModalDept.department_id, {
          sla_days: Number(timingModalConfig.sla_days),
        });
      }

      setMessage(`Timings & SLA configured successfully for ${timingModalDept.name}.`);
      setTimingModalDept(null);
      reload();
    } catch (err) {
      setTimingModalError(getApiError(err, "Unable to save department timings."));
    } finally {
      setTimingModalSaving(false);
    }
  };

  const startEdit = (department) => {
    setEditTarget(department);
    setEditName(department.name || "");
    setEditDescription(department.description || "");
    setEditSla(department.sla_days || 3);
    setEditComplaintTypes((department.complaint_types || []).join(", "));
    setEditLocationIds(department.location_ids || []);
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!editName.trim()) {
      setError("Department name is required.");
      return;
    }

    // Campus-wide duplicate check
    const normalized = editName.trim().toLowerCase();
    const duplicate = (data?.departments || []).some(
      (d) =>
        d.department_id !== editTarget.department_id &&
        d.name.trim().toLowerCase() === normalized,
    );
    if (duplicate) {
      setError(
        `Department "${editName.trim()}" already exists. Please choose another name.`,
      );
      return;
    }

    try {
      await departmentService.update(editTarget.department_id, {
        name: editName.trim(),
        description: editDescription.trim(),
        sla_days: Number(editSla),
        complaint_types: editComplaintTypes
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
        location_ids: editLocationIds,
      });
      setEditTarget(null);
      setMessage("Department updated successfully.");
      reload();
    } catch (err) {
      setError(getApiError(err, "Unable to update department."));
    }
  };

  const archiveDepartment = async (departmentId) => {
    setMessage("");
    setError("");
    try {
      await departmentService.update(departmentId, { archived: true });
      setMessage("Department archived successfully.");
      reload();
    } catch (err) {
      setError(getApiError(err, "Unable to archive department."));
    }
  };

  const restoreDepartment = async (departmentId) => {
    setMessage("");
    setError("");
    try {
      await departmentService.update(departmentId, { archived: false });
      setMessage("Department restored successfully.");
      reload();
    } catch (err) {
      setError(getApiError(err, "Unable to restore department."));
    }
  };

  const startDelete = (department) => {
    setDeleteTarget(department);
    setDeleteInput("");
  };

  const handleDelete = async () => {
    if (!deleteTarget || deleteInput !== "DELETE") return;
    const targetId = deleteTarget.department_id;
    setDeleteTarget(null);
    setMessage("");
    setError("");

    try {
      await departmentService.delete(targetId);
      setMessage("Department deleted successfully.");
      reload();
    } catch (err) {
      const errMsg = getApiError(err, "Unable to delete department.");
      if (errMsg.includes("Cannot delete department.")) {
        setDeleteDependencyError(errMsg);
      } else {
        setError(errMsg);
      }
    }
  };

  const handleArchiveFromError = async () => {
    const targetId =
      deleteDependencyError.match(/DEPT-[A-F0-9]+/i)?.[0] ||
      deleteTarget?.department_id;
    setDeleteDependencyError("");
    if (!targetId) return;

    try {
      await departmentService.update(targetId, { archived: true });
      setMessage("Department archived successfully.");
      reload();
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to archive department.");
    }
  };

  // Category modal handlers
  const openEditCategoriesModal = (dept) => {
    setCategoryModalDept(dept);
    setCategoryList(Array.isArray(dept.complaint_types) ? [...dept.complaint_types] : []);
    setNewCategoryInput("");
  };

  const handleAddCategoryItem = () => {
    const trimmed = newCategoryInput.trim();
    if (!trimmed) return;
    const items = trimmed
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const updated = [...categoryList];
    for (const item of items) {
      if (!updated.includes(item)) {
        updated.push(item);
      }
    }
    setCategoryList(updated);
    setNewCategoryInput("");
  };

  const handleRemoveCategoryItem = (catToRemove) => {
    setCategoryList((prev) => prev.filter((c) => c !== catToRemove));
  };

  const handleSaveCategories = async () => {
    if (!categoryModalDept) return;
    setCategoryModalSaving(true);
    try {
      await departmentService.update(categoryModalDept.department_id, {
        complaint_types: categoryList,
      });
      setMessage(`Updated covered categories for ${categoryModalDept.name}.`);
      setCategoryModalDept(null);
      reload();
    } catch (err) {
      setError(getApiError(err, "Failed to update department categories."));
    } finally {
      setCategoryModalSaving(false);
    }
  };

  // Loaded departments filtered by location API
  const filteredDepartments = useMemo(() => {
    const list = data?.departments || [];
    if (!selectedLocation) return list;
    return list.filter(
      (d) =>
        (d.location_ids || []).includes(selectedLocation) ||
        d.location_id === selectedLocation
    );
  }, [data, selectedLocation]);

  const mappingGridColumns = [
    {
      key: "name",
      header: "Department",
      render: (row) => (
        <div>
          <div className="font-bold text-xs text-slate-900 dark:text-slate-100">
            {row.name}
          </div>
          {row.description && row.description !== "Campus-wide department" ? (
            <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-1" title={row.description}>
              {row.description}
            </div>
          ) : null}
        </div>
      ),
    },
    {
      key: "complaint_types",
      header: "Covered Categories",
      render: (row) => {
        const types = row.complaint_types || [];
        return (
          <div className="py-1 space-y-1.5 min-w-[170px] max-w-[260px]">
            {types.length === 0 ? (
              <span className="text-xs text-slate-400 italic">None configured</span>
            ) : (
              <div className="flex flex-col gap-1 max-h-36 overflow-y-auto pr-1">
                {types.map((cat, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() =>
                      navigate(
                        `/complaints?category=${encodeURIComponent(cat)}&department_id=${encodeURIComponent(row.department_id)}`
                      )
                    }
                    className="inline-flex items-center justify-between gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200/90 dark:border-slate-700/60 hover:bg-primary/10 hover:border-primary/40 hover:text-primary transition-all text-left group cursor-pointer shadow-2xs"
                    title={`View complaints for category: ${cat}`}
                  >
                    <span className="truncate">{cat}</span>
                    <span className="text-[10px] text-slate-400 group-hover:text-primary shrink-0 opacity-70 group-hover:translate-x-0.5 transition-transform">
                      &rarr;
                    </span>
                  </button>
                ))}
              </div>
            )}
            <button
              type="button"
              onClick={() => openEditCategoriesModal(row)}
              className="inline-flex items-center gap-1 text-[11px] font-semibold text-primary hover:text-primary/80 transition-colors pt-0.5 cursor-pointer"
              title="Edit covered categories"
            >
              <Edit2 className="h-3 w-3" />
              <span>Edit Categories</span>
            </button>
          </div>
        );
      },
    },
    {
      key: "coordinators",
      header: "Department Coordinators (1 & 2)",
      render: (row) => {
        const u1 = (data?.coordinators || []).find((u) => u.user_id === row.coordinator_id);
        const u2 = (data?.coordinators || []).find((u) => u.user_id === row.coordinator_2_id);
        const name1 = u1?.name || (row.coordinator_id ? row.coordinator_id : null);
        const name2 = u2?.name || (row.coordinator_2_id ? row.coordinator_2_id : null);

        return (
          <div className="space-y-1 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="font-semibold text-slate-500 w-16 shrink-0">Coord 1:</span>
              {name1 ? (
                <button
                  type="button"
                  onClick={() =>
                    navigate(
                      `/chat?userId=${encodeURIComponent(row.coordinator_id)}&name=${encodeURIComponent(name1)}`
                    )
                  }
                  className="group inline-flex items-center gap-1 font-semibold text-slate-900 dark:text-slate-100 hover:text-primary transition-colors text-left"
                  title={`Open 1-on-1 chat with ${name1}`}
                >
                  <span className="group-hover:underline underline-offset-2">{name1}</span>
                  <MessageSquare className="h-3 w-3 text-slate-400 group-hover:text-primary shrink-0 opacity-60 group-hover:opacity-100 transition-opacity" />
                </button>
              ) : (
                <span className="text-rose-500 italic">Unassigned</span>
              )}
            </div>
            <div className="flex items-center gap-1.5">
              <span className="font-semibold text-slate-500 w-16 shrink-0">Coord 2:</span>
              {name2 ? (
                <button
                  type="button"
                  onClick={() =>
                    navigate(
                      `/chat?userId=${encodeURIComponent(row.coordinator_2_id)}&name=${encodeURIComponent(name2)}`
                    )
                  }
                  className="group inline-flex items-center gap-1 font-medium text-slate-700 dark:text-slate-300 hover:text-primary transition-colors text-left"
                  title={`Open 1-on-1 chat with ${name2}`}
                >
                  <span className="group-hover:underline underline-offset-2">{name2}</span>
                  <MessageSquare className="h-3 w-3 text-slate-400 group-hover:text-primary shrink-0 opacity-60 group-hover:opacity-100 transition-opacity" />
                </button>
              ) : (
                <span className="text-amber-500 italic">Unassigned</span>
              )}
            </div>
          </div>
        );
      },
    },
    {
      key: "eligible_workforce",
      header: "Eligible Staff",
      render: (row) => (
        <button
          type="button"
          onClick={() => openWorkforceModal(row)}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 hover:bg-blue-100 transition-colors cursor-pointer"
          title="Click to view eligible employees"
        >
          <Users className="h-3.5 w-3.5" />
          <span>{row.eligible_employee_count || 0} Staff</span>
        </button>
      ),
    },
    {
      key: "active_complaints",
      header: "Active Complaints",
      render: (row) => (
        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
          {row.active_complaints_count || 0}
        </span>
      ),
    },
    {
      key: "sla_days",
      header: "SLA Limit",
      render: (row) => `${row.sla_days} days`,
    },
    {
      key: "actions",
      header: "Actions",
      render: (row) => (
        <div className="flex items-center gap-1.5">
          {row.archived ? (
            <Button
              variant="subtle"
              size="sm"
              onClick={() => restoreDepartment(row.department_id)}
              className="!p-1.5"
              title="Restore Department"
            >
              <RefreshCw className="h-3.5 w-3.5 text-emerald-600" />
            </Button>
          ) : (
            <>
              <Button
                variant="subtle"
                size="sm"
                onClick={() => openAssignCoordsModal(row)}
                className="!p-1.5 text-blue-600 hover:text-blue-700 dark:text-blue-400"
                title="Manage Department Coordinators (Coord 1 & 2)"
              >
                <UserCheck className="h-3.5 w-3.5" />
              </Button>
              <Button
                variant="subtle"
                size="sm"
                onClick={() => openWorkforceModal(row)}
                className="!p-1.5 text-indigo-600 hover:text-indigo-700 dark:text-indigo-400"
                title="View Eligible Workforce"
              >
                <Users className="h-3.5 w-3.5" />
              </Button>
              <Button
                variant="subtle"
                size="sm"
                onClick={() => openTimingsModal(row)}
                className="!p-1.5 text-amber-600 hover:text-amber-700 dark:text-amber-400"
                title="Configure Department Timings & SLA"
              >
                <Clock className="h-3.5 w-3.5" />
              </Button>
              <Button
                variant="subtle"
                size="sm"
                onClick={() => startEdit(row)}
                className="!p-1.5"
                title="Edit Department"
              >
                <Edit2 className="h-3.5 w-3.5 text-slate-500" />
              </Button>
              <Button
                variant="subtle"
                size="sm"
                onClick={() => archiveDepartment(row.department_id)}
                className="!p-1.5"
                title="Archive Department"
              >
                <Archive className="h-3.5 w-3.5 text-amber-500" />
              </Button>
              <Button
                variant="subtle"
                size="sm"
                onClick={() => startDelete(row)}
                className="!p-1.5 hover:text-red-600"
                title="Delete Department"
              >
                <Trash2 className="h-3.5 w-3.5 text-rose-500" />
              </Button>
            </>
          )}
        </div>
      ),
    },

  ];

  const columns = [
    {
      key: "name",
      header: "Department",
      render: (row) => (
        <div>
          <div className="font-bold text-xs text-slate-900 dark:text-slate-100">
            {row.name}
          </div>
          {row.description && (
            <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-1" title={row.description}>
              {row.description}
            </div>
          )}
        </div>
      ),
    },
    {
      key: "sla_days",
      header: "SLA Limit",
      render: (row) => `${row.sla_days} days`,
    },
    {
      key: "complaint_types",
      header: "Complaint Categories",
      render: (row) => {
        const types = row.complaint_types || [];
        return (
          <div className="py-1 space-y-1.5 min-w-[170px] max-w-[260px]">
            {types.length === 0 ? (
              <span className="text-xs text-slate-400 italic">None configured</span>
            ) : (
              <div className="flex flex-col gap-1 max-h-36 overflow-y-auto pr-1">
                {types.map((cat, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() =>
                      navigate(
                        `/complaints?category=${encodeURIComponent(cat)}&department_id=${encodeURIComponent(row.department_id)}`
                      )
                    }
                    className="inline-flex items-center justify-between gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border border-slate-200/90 dark:border-slate-700/60 hover:bg-primary/10 hover:border-primary/40 hover:text-primary transition-all text-left group cursor-pointer shadow-2xs"
                    title={`View complaints for category: ${cat}`}
                  >
                    <span className="truncate">{cat}</span>
                    <span className="text-[10px] text-slate-400 group-hover:text-primary shrink-0 opacity-70 group-hover:translate-x-0.5 transition-transform">
                      &rarr;
                    </span>
                  </button>
                ))}
              </div>
            )}
            <button
              type="button"
              onClick={() => openEditCategoriesModal(row)}
              className="inline-flex items-center gap-1 text-[11px] font-semibold text-primary hover:text-primary/80 transition-colors pt-0.5 cursor-pointer"
              title="Edit covered categories"
            >
              <Edit2 className="h-3 w-3" />
              <span>Edit Categories</span>
            </button>
          </div>
        );
      },
    },
    {
      key: "coordinators",
      header: "Coordinators (1 & 2)",
      render: (row) => {
        const u1 = (data?.coordinators || []).find((u) => u.user_id === row.coordinator_id);
        const u2 = (data?.coordinators || []).find((u) => u.user_id === row.coordinator_2_id);
        const name1 = u1?.name || (row.coordinator_id ? row.coordinator_id : null);
        const name2 = u2?.name || (row.coordinator_2_id ? row.coordinator_2_id : null);

        return (
          <div className="space-y-1 text-xs">
            <div className="flex items-center gap-1.5">
              <span className="font-semibold text-slate-500 w-14 shrink-0">Coord 1:</span>
              {name1 ? (
                <button
                  type="button"
                  onClick={() =>
                    navigate(
                      `/chat?userId=${encodeURIComponent(row.coordinator_id)}&name=${encodeURIComponent(name1)}`
                    )
                  }
                  className="group inline-flex items-center gap-1 font-semibold text-slate-900 dark:text-slate-100 hover:text-primary transition-colors text-left"
                  title={`Open 1-on-1 chat with ${name1}`}
                >
                  <span className="group-hover:underline underline-offset-2">{name1}</span>
                  <MessageSquare className="h-3 w-3 text-slate-400 group-hover:text-primary shrink-0 opacity-60 group-hover:opacity-100 transition-opacity" />
                </button>
              ) : (
                <span className="text-rose-500 italic">Unassigned</span>
              )}
            </div>
            <div className="flex items-center gap-1.5">
              <span className="font-semibold text-slate-500 w-14 shrink-0">Coord 2:</span>
              {name2 ? (
                <button
                  type="button"
                  onClick={() =>
                    navigate(
                      `/chat?userId=${encodeURIComponent(row.coordinator_2_id)}&name=${encodeURIComponent(name2)}`
                    )
                  }
                  className="group inline-flex items-center gap-1 font-medium text-slate-700 dark:text-slate-300 hover:text-primary transition-colors text-left"
                  title={`Open 1-on-1 chat with ${name2}`}
                >
                  <span className="group-hover:underline underline-offset-2">{name2}</span>
                  <MessageSquare className="h-3 w-3 text-slate-400 group-hover:text-primary shrink-0 opacity-60 group-hover:opacity-100 transition-opacity" />
                </button>
              ) : (
                <span className="text-amber-500 italic">Unassigned</span>
              )}
            </div>
          </div>
        );
      },
    },
    {
      key: "eligible_workforce",
      header: "Eligible Staff",
      render: (row) => (
        <button
          type="button"
          onClick={() => openWorkforceModal(row)}
          className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-lg text-xs font-semibold bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800 hover:bg-blue-100 transition-colors cursor-pointer"
          title="Click to view eligible employees"
        >
          <Users className="h-3 w-3" />
          <span>{row.eligible_employee_count || 0} Staff</span>
        </button>
      ),
    },
    {
      key: "active_complaints",
      header: "Active",
      render: (row) => (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
          {row.active_complaints_count || 0}
        </span>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      render: (row) => (
        <div className="flex items-center gap-1.5">
          {row.archived ? (
            <Button
              variant="subtle"
              size="sm"
              onClick={() => restoreDepartment(row.department_id)}
              className="!p-1.5"
              title="Restore"
            >
              <RefreshCw className="h-4 w-4 text-slate-500" />
            </Button>
          ) : (
            <>
              <Button
                variant="subtle"
                size="sm"
                onClick={() => openAssignCoordsModal(row)}
                className="!p-1.5 text-blue-600 hover:text-blue-700 dark:text-blue-400"
                title="Manage Department Coordinators (Coord 1 & 2)"
              >
                <UserCheck className="h-4 w-4" />
              </Button>
              <Button
                variant="subtle"
                size="sm"
                onClick={() => openWorkforceModal(row)}
                className="!p-1.5 text-indigo-600 hover:text-indigo-700 dark:text-indigo-400"
                title="View Eligible Workforce"
              >
                <Users className="h-4 w-4" />
              </Button>
              <Button
                variant="subtle"
                size="sm"
                onClick={() => openTimingsModal(row)}
                className="!p-1.5 text-amber-600 hover:text-amber-700 dark:text-amber-400"
                title="Configure Department Timings & SLA"
              >
                <Clock className="h-4 w-4" />
              </Button>
              <Button
                variant="subtle"
                size="sm"
                onClick={() => startEdit(row)}
                className="!p-1.5"
                title="Edit"
              >
                <Edit2 className="h-4 w-4 text-slate-500" />
              </Button>

              <Button
                variant="subtle"
                size="sm"
                onClick={() => archiveDepartment(row.department_id)}
                className="!p-1.5"
                title="Archive"
              >
                <Archive className="h-4 w-4 text-slate-500" />
              </Button>
              <Button
                variant="subtle"
                size="sm"
                onClick={() => startDelete(row)}
                className="!p-1.5 hover:!bg-red-50 text-red-500"
                title="Delete"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="grid gap-8">
      {/* Page Title & Breadcrumbs */}
      <div>
        <nav className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 mb-2">
          <span>Dashboard</span>
          <span>&gt;</span>
          <span className="text-slate-800 dark:text-slate-200 font-bold">Departments</span>
        </nav>
        <PageHeader
          title="Department Configuration"
          description="Configure campus-wide department profiles, operating location assignments, resolution SLAs, and coordinators."
        />
      </div>

      <Toast message={message} tone="success" onClose={() => setMessage("")} />
      <Toast message={error} tone="danger" onClose={() => setError("")} />

      {/* Coverage Gaps Alert Panel */}
      {data?.coverageGaps?.unassigned_pairs?.length > 0 && (
        <div className="p-4 rounded-xl border border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/40 text-amber-900 dark:text-amber-200 shadow-xs space-y-3">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-lg bg-amber-200/80 dark:bg-amber-900/60 text-amber-800 dark:text-amber-300 shrink-0">
                <AlertTriangle className="h-5 w-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold">
                  Coverage gaps: {data.coverageGaps.unassigned_pairs.length} department/location pair{data.coverageGaps.unassigned_pairs.length === 1 ? "" : "s"} have no coordinator assigned.
                </h3>
                <p className="text-xs text-amber-800/80 dark:text-amber-300/80 mt-0.5">
                  Complaints filed in these areas cannot be auto-routed and will sit in the unassigned queue. Assign coordinators using the mapping grid below.
                </p>
              </div>
            </div>
            <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-200/80 dark:bg-amber-900 text-amber-900 dark:text-amber-100 shrink-0">
              {data.coverageGaps.unassigned_pairs.length} Gaps
            </span>
          </div>

          <div className="flex flex-wrap gap-2 pt-1">
            {data.coverageGaps.unassigned_pairs.map((gap, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-white dark:bg-slate-900 border border-amber-300/80 dark:border-amber-700 text-slate-800 dark:text-slate-200"
              >
                <MapPin className="h-3 w-3 text-amber-600 shrink-0" />
                <span className="font-bold">{gap.department_name}</span>
                <span className="text-slate-400">@</span>
                <span>{gap.location_name}</span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Register form card */}
      <Card>
        <div className="mb-4">
          <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <PlusCircle className="h-5 w-5 text-primary" />
            Configure New Central Department
          </h2>
          <p className="text-xs font-medium text-slate-500 dark:text-slate-400 mt-1">
            Create a campus-wide reusable department entity and associate it with operating locations.
          </p>
        </div>

        <hr className="border-slate-100 dark:border-slate-800 my-4" />

        <form
          className="grid gap-5 md:grid-cols-2 lg:grid-cols-4"
          onSubmit={handleSubmit(createDepartment)}
        >
          <Input
            label="Department Name"
            placeholder="Electrical"
            error={errors.name?.message}
            {...register("name", { required: "Department name is required." })}
          />
          <Input
            label="Description (Optional)"
            placeholder="Campus-wide electrical maintenance, repairs, fixtures"
            {...register("description")}
          />
          <Input
            label="SLA Resolution Days"
            type="number"
            min="1"
            placeholder="3"
            error={errors.sla_days?.message}
            {...register("sla_days", { required: "SLA is required." })}
          />
          <Input
            label="Complaint Types (comma separated)"
            placeholder="Door, Window, Chair"
            error={errors.complaint_types?.message}
            {...register("complaint_types", {
              required: "At least one type is required.",
            })}
          />

          <div className="flex items-end lg:col-span-4">
            <Button
              type="submit"
              disabled={isSubmitting}
              className="font-semibold px-6 w-full lg:w-auto"
            >
              Create Department
            </Button>
          </div>
        </form>
      </Card>

      {/* Department SLA Configuration & Escalation Settings Card */}
      <Card>
        <button
          type="button"
          onClick={() => setIsEscalationOpen(!isEscalationOpen)}
          className="w-full flex items-center justify-between text-left transition-colors focus:outline-none"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-primary/10 text-primary">
              <Clock className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                Escalation Settings
              </h2>
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Click to {isEscalationOpen ? "hide" : "configure"} priority resolution windows, operational working hours, and multi-tier escalation thresholds
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 dark:text-slate-400">
            <span className="hidden sm:inline">{isEscalationOpen ? "Collapse" : "Expand"}</span>
            <ChevronDown className={`h-5 w-5 transition-transform duration-200 ${isEscalationOpen ? "rotate-180" : ""}`} />
          </div>
        </button>

        {isEscalationOpen && (
          <div className="mt-4 pt-4 border-t border-slate-100 dark:border-slate-800">
            {/* Department Selector */}
            <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
                Select a department below to customize its resolution times and notification escalation ladder.
              </p>
              <div className="flex items-center gap-2 min-w-[280px]">
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300 shrink-0">
                  Department:
                </label>
                <select
                  value={slaDeptId}
                  onChange={(e) => setSlaDeptId(e.target.value)}
                  className="h-10 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shadow-xs cursor-pointer"
                >
                  {(data?.departments || []).map((dept) => (
                    <option key={dept.department_id} value={dept.department_id}>
                      {dept.name} {dept.location_id ? `(${dept.location_id})` : ""}
                    </option>
                  ))}
                </select>
              </div>
            </div>

        {slaLoading ? (
          <div className="py-8 flex justify-center">
            <Loader />
          </div>
        ) : (
          <form onSubmit={handleSaveSlaConfig} className="space-y-6">
            {/* Priority SLA Rows */}
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3 flex items-center gap-1.5">
                <Sliders className="h-3.5 w-3.5 text-primary" />
                Priority SLA Durations & Active Hours
              </h3>
              <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider border-b border-slate-200 dark:border-slate-800">
                    <tr>
                      <th className="px-4 py-3">Priority Level</th>
                      <th className="px-4 py-3">Window Start Time</th>
                      <th className="px-4 py-3">Window End Time</th>
                      <th className="px-4 py-3">Resolution Target (Hours)</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800 text-slate-700 dark:text-slate-300 font-medium">
                    {/* Normal / Low */}
                    <tr>
                      <td className="px-4 py-3 font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-slate-400 inline-block"></span>
                        Normal / Low
                      </td>
                      <td className="px-4 py-2">
                        <CleanTimeSelect
                          value={slaConfig.normal_start_time || "10:00"}
                          onChange={(val) =>
                            setSlaConfig({ ...slaConfig, normal_start_time: val })
                          }
                        />
                      </td>
                      <td className="px-4 py-2">
                        <CleanTimeSelect
                          value={slaConfig.normal_end_time || "16:00"}
                          onChange={(val) =>
                            setSlaConfig({ ...slaConfig, normal_end_time: val })
                          }
                        />
                      </td>
                      <td className="px-4 py-2">
                        <div className="flex items-center gap-1.5">
                          <input
                            type="number"
                            min="1"
                            value={slaConfig.normal_duration_hours || 72}
                            onChange={(e) =>
                              setSlaConfig({ ...slaConfig, normal_duration_hours: e.target.value })
                            }
                            className="h-8.5 w-24 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-2.5 text-xs font-mono font-semibold"
                          />
                          <span className="text-slate-400 text-[11px]">hours</span>
                        </div>
                      </td>
                    </tr>

                    {/* Medium */}
                    <tr>
                      <td className="px-4 py-3 font-bold text-blue-700 dark:text-blue-300 flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block"></span>
                        Medium
                      </td>
                      <td className="px-4 py-2">
                        <CleanTimeSelect
                          value={slaConfig.medium_start_time || "10:00"}
                          onChange={(val) =>
                            setSlaConfig({ ...slaConfig, medium_start_time: val })
                          }
                        />
                      </td>
                      <td className="px-4 py-2">
                        <CleanTimeSelect
                          value={slaConfig.medium_end_time || "16:00"}
                          onChange={(val) =>
                            setSlaConfig({ ...slaConfig, medium_end_time: val })
                          }
                        />
                      </td>
                      <td className="px-4 py-2">
                        <div className="flex items-center gap-1.5">
                          <input
                            type="number"
                            min="1"
                            value={slaConfig.medium_duration_hours || 48}
                            onChange={(e) =>
                              setSlaConfig({ ...slaConfig, medium_duration_hours: e.target.value })
                            }
                            className="h-8.5 w-24 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-2.5 text-xs font-mono font-semibold"
                          />
                          <span className="text-slate-400 text-[11px]">hours</span>
                        </div>
                      </td>
                    </tr>

                    {/* High */}
                    <tr>
                      <td className="px-4 py-3 font-bold text-amber-700 dark:text-amber-300 flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block"></span>
                        High
                      </td>
                      <td className="px-4 py-2">
                        <CleanTimeSelect
                          value={slaConfig.high_start_time || "10:00"}
                          onChange={(val) =>
                            setSlaConfig({ ...slaConfig, high_start_time: val })
                          }
                        />
                      </td>
                      <td className="px-4 py-2">
                        <CleanTimeSelect
                          value={slaConfig.high_end_time || "18:00"}
                          onChange={(val) =>
                            setSlaConfig({ ...slaConfig, high_end_time: val })
                          }
                        />
                      </td>
                      <td className="px-4 py-2">
                        <div className="flex items-center gap-1.5">
                          <input
                            type="number"
                            min="1"
                            value={slaConfig.high_duration_hours || 24}
                            onChange={(e) =>
                              setSlaConfig({ ...slaConfig, high_duration_hours: e.target.value })
                            }
                            className="h-8.5 w-24 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-2.5 text-xs font-mono font-semibold"
                          />
                          <span className="text-slate-400 text-[11px]">hours</span>
                        </div>
                      </td>
                    </tr>

                    {/* Critical */}
                    <tr className="bg-rose-50/40 dark:bg-rose-950/20">
                      <td className="px-4 py-3 font-bold text-rose-700 dark:text-rose-300 flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block animate-pulse"></span>
                        Critical
                      </td>
                      <td className="px-4 py-2">
                        <CleanTimeSelect
                          value={slaConfig.critical_start_time || "00:00"}
                          onChange={(val) =>
                            setSlaConfig({ ...slaConfig, critical_start_time: val })
                          }
                          className="border-rose-200 dark:border-rose-900/60 text-rose-700 dark:text-rose-300"
                        />
                      </td>
                      <td className="px-4 py-2">
                        <CleanTimeSelect
                          value={slaConfig.critical_end_time || "23:59"}
                          onChange={(val) =>
                            setSlaConfig({ ...slaConfig, critical_end_time: val })
                          }
                          className="border-rose-200 dark:border-rose-900/60 text-rose-700 dark:text-rose-300"
                        />
                      </td>
                      <td className="px-4 py-2">
                        <div className="flex items-center gap-1.5">
                          <input
                            type="number"
                            min="1"
                            value={slaConfig.critical_duration_hours || 4}
                            onChange={(e) =>
                              setSlaConfig({ ...slaConfig, critical_duration_hours: e.target.value })
                            }
                            className="h-8.5 w-24 rounded-lg border border-rose-200 dark:border-rose-900/60 bg-white dark:bg-slate-900 px-2.5 text-xs font-mono font-semibold text-rose-700 dark:text-rose-300"
                          />
                          <span className="text-slate-400 text-[11px]">hours</span>
                        </div>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            {/* Escalation Settings - Directly Below SLA Settings */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40 space-y-4">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                  <Shield className="h-3.5 w-3.5 text-primary" />
                  Escalation Thresholds
                </h3>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                  Automated background alerts: Upon resolution deadline breach, the App Manager is immediately alerted (Level 1).
                  If still unresolved after the additional thresholds below, subsequent alerts are dispatched.
                </p>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                    App Manager 2nd Alert after overdue by (hours)
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      min="1"
                      value={slaConfig.app_manager_escalation_hours || 24}
                      onChange={(e) =>
                        setSlaConfig({
                          ...slaConfig,
                          app_manager_escalation_hours: e.target.value,
                        })
                      }
                      className="h-9 w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-xs font-mono font-semibold"
                      required
                    />
                    <span className="text-xs text-slate-400 font-semibold shrink-0">hours</span>
                  </div>
                  <span className="text-[11px] text-slate-400 mt-1 block">
                    Level 2 escalation reminder to App Manager (default: 24h past deadline)
                  </span>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300">
                      Notify Admin after overdue by (hours)
                    </label>
                    {!isAdmin && (
                      <span className="text-[10px] font-semibold text-slate-500 bg-slate-200 dark:bg-slate-700 px-1.5 py-0.5 rounded">
                        Admin Only (Read-Only)
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      min="1"
                      value={slaConfig.admin_escalation_hours || 48}
                      disabled={!isAdmin}
                      readOnly={!isAdmin}
                      onChange={(e) =>
                        setSlaConfig({
                          ...slaConfig,
                          admin_escalation_hours: e.target.value,
                        })
                      }
                      className={`h-9 w-full rounded-xl border border-slate-200 dark:border-slate-700 px-3 text-xs font-mono font-semibold ${
                        isAdmin
                          ? "bg-white dark:bg-slate-900"
                          : "bg-slate-100 dark:bg-slate-800 text-slate-500 cursor-not-allowed"
                      }`}
                      required
                    />
                    <span className="text-xs text-slate-400 font-semibold shrink-0">hours</span>
                  </div>
                  <span className="text-[11px] text-slate-400 mt-1 block">
                    Level 3 institutional oversight escalation to Admin (default: 48h past deadline)
                  </span>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-blue-50/90 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-900/60 space-y-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-blue-900 dark:text-blue-200">
                    <Shield className="h-4 w-4 text-primary" />
                    <span>Escalation Flow</span>
                    <span className="text-[11px] font-normal text-slate-500 dark:text-slate-400">
                      (Times dynamically update from your settings above &bull; click any stage to redirect to complaints)
                    </span>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-1.5 text-[11px] font-medium text-slate-700 dark:text-slate-300">
                  {/* Step 1: Deadline Breach / SLA window */}
                  <button
                    type="button"
                    onClick={() =>
                      navigate(
                        `/complaints?department_id=${encodeURIComponent(slaDeptId)}&sla=overdue`
                      )
                    }
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-white dark:bg-slate-900 border border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300 hover:bg-blue-100/70 hover:border-blue-400 font-semibold transition-all cursor-pointer shadow-2xs group"
                    title={`Click to view overdue complaints past resolution target (${slaConfig.normal_duration_hours || 72}h Normal / ${slaConfig.medium_duration_hours || 48}h Medium / ${slaConfig.high_duration_hours || 24}h High / ${slaConfig.critical_duration_hours || 4}h Critical)`}
                  >
                    <Clock className="h-3 w-3 text-blue-500" />
                    <span>
                      Deadline Breach ({slaConfig.normal_duration_hours || 72}h Normal / {slaConfig.high_duration_hours || 24}h High)
                    </span>
                    <span className="text-[10px] text-blue-400 group-hover:translate-x-0.5 transition-transform">&rarr;</span>
                  </button>

                  <span className="text-blue-400 font-bold">&rarr;</span>

                  {/* Step 2: Level 1 Immediate Alert */}
                  <button
                    type="button"
                    onClick={() =>
                      navigate(
                        `/complaints?department_id=${encodeURIComponent(slaDeptId)}&sla=overdue`
                      )
                    }
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-white dark:bg-slate-900 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-300 hover:bg-amber-100/70 hover:border-amber-400 font-semibold transition-all cursor-pointer shadow-2xs group"
                    title="Click to view Level 1 overdue complaints (App Manager immediate alert)"
                  >
                    <AlertTriangle className="h-3 w-3 text-amber-500" />
                    <span>App Manager (Immediate Alert)</span>
                    <span className="text-[10px] text-amber-400 group-hover:translate-x-0.5 transition-transform">&rarr;</span>
                  </button>

                  <span className="text-blue-400 font-bold">&rarr;</span>

                  {/* Step 3: Level 2 App Manager 2nd Alert */}
                  <button
                    type="button"
                    onClick={() =>
                      navigate(
                        `/complaints?department_id=${encodeURIComponent(slaDeptId)}&status=escalated`
                      )
                    }
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-white dark:bg-slate-900 border border-orange-200 dark:border-orange-800 text-orange-800 dark:text-orange-300 hover:bg-orange-100/70 hover:border-orange-400 font-semibold transition-all cursor-pointer shadow-2xs group"
                    title={`Click to view Level 2 escalated complaints (+${slaConfig.app_manager_escalation_hours || 24}h overdue)`}
                  >
                    <span className="font-mono text-orange-600 dark:text-orange-400 font-bold">
                      +{slaConfig.app_manager_escalation_hours || 24}h
                    </span>
                    <span>App Manager (2nd Alert)</span>
                    <span className="text-[10px] text-orange-400 group-hover:translate-x-0.5 transition-transform">&rarr;</span>
                  </button>

                  <span className="text-blue-400 font-bold">&rarr;</span>

                  {/* Step 4: Level 3 Administrator Critical Escalation */}
                  <button
                    type="button"
                    onClick={() =>
                      navigate(
                        `/complaints?department_id=${encodeURIComponent(slaDeptId)}&status=escalated`
                      )
                    }
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-white dark:bg-slate-900 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-300 hover:bg-rose-100/70 hover:border-rose-400 font-semibold transition-all cursor-pointer shadow-2xs group"
                    title={`Click to view Level 3 critical escalations (+${slaConfig.admin_escalation_hours || 48}h overdue)`}
                  >
                    <span className="font-mono text-rose-600 dark:text-rose-400 font-bold">
                      +{slaConfig.admin_escalation_hours || 48}h
                    </span>
                    <span>Administrator (Critical Escalation)</span>
                    <span className="text-[10px] text-rose-400 group-hover:translate-x-0.5 transition-transform">&rarr;</span>
                  </button>
                </div>
              </div>
            </div>

            <div className="flex justify-end">
              <Button
                type="submit"
                disabled={slaSaving || slaLoading || !slaDeptId}
                variant="primary"
                className="font-bold px-6"
              >
                {slaSaving ? "Saving Settings..." : "Save SLA & Escalation Settings"}
              </Button>
            </div>
          </form>
        )}
          </div>
        )}
      </Card>

      {/* Location-Grouped Department Hierarchy */}
      <Card>
        {/* Toolbar: Location Filter Dropdown + Show Archived Checkbox + Refresh */}
        <div className="flex flex-wrap items-center justify-between gap-3 my-2">
          {/* Location Dropdown Filter */}
          <div className="flex items-center gap-2 flex-1 min-w-[260px]">
            <label className="text-xs font-bold text-slate-700 dark:text-slate-300 shrink-0">
              📍 Filter by Location:
            </label>
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="h-10 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shadow-xs cursor-pointer"
            >
              <option value="">All Locations Overview</option>
              {(data?.locations || []).map((loc) => (
                <option key={loc.location_id} value={loc.location_id}>
                  {loc.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3 shrink-0 flex-wrap">
            {/* View Mode Toggle */}
            <div className="flex items-center p-1 bg-slate-100 dark:bg-slate-800 rounded-xl text-xs font-semibold">
              <button
                type="button"
                onClick={() => setViewMode("grid")}
                className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer flex items-center gap-1.5 ${
                  viewMode === "grid"
                    ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-xs"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
                }`}
              >
                <Network className="h-3.5 w-3.5" />
                Mapping Grid
              </button>
              <button
                type="button"
                onClick={() => setViewMode("hierarchy")}
                className={`px-3 py-1.5 rounded-lg transition-colors cursor-pointer flex items-center gap-1.5 ${
                  viewMode === "hierarchy"
                    ? "bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 shadow-xs"
                    : "text-slate-600 dark:text-slate-400 hover:text-slate-900"
                }`}
              >
                <Layers className="h-3.5 w-3.5" />
                Grouped by Location
              </button>
            </div>

            {/* Show Archived Checkbox */}
            <label className="flex items-center gap-2 cursor-pointer select-none px-2 shrink-0">
              <input
                type="checkbox"
                checked={showArchived}
                onChange={(e) => setShowArchived(e.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary"
              />
              <span className="text-xs font-bold text-slate-600 dark:text-slate-300">
                Archived
              </span>
            </label>

            {/* Refresh Button */}
            <Button
              variant="subtle"
              size="sm"
              onClick={reload}
              className="h-10 px-3.5 rounded-xl text-xs font-bold shrink-0"
            >
              <RotateCw className="h-4 w-4 mr-1.5 shrink-0" />
              Refresh
            </Button>
          </div>
        </div>
      </Card>

      {loading && (
        <Loader label="Loading location hierarchy and departments" variant="skeleton" />
      )}

      {/* Render Location Hierarchy Cards or Mapping Grid based on viewMode */}
      {!loading && (
        <div className="grid gap-6">
          {(() => {
            const rawLocations = data?.locations || [];
            const allDepartments = data?.departments || [];
            const rawDepartments = showArchived
              ? allDepartments.filter((d) => d.archived === true)
              : allDepartments.filter((d) => !d.archived);

            const filteredByLoc = filteredDepartments;

            if (viewMode === "grid") {
              return (
                <Card className="!p-6">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100 dark:border-slate-800 mb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                        <Network className="h-5 w-5" />
                      </div>
                      <div>
                        <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
                          Central Department Directory
                        </h2>
                        <p className="text-xs text-slate-500 dark:text-slate-400 font-medium mt-0.5">
                          Campus-wide departments, operating location coverage, eligible workforce, and coordinators
                        </p>
                      </div>
                    </div>
                    <div className="text-xs text-slate-500 font-semibold">
                      Showing {filteredByLoc.length} central department{filteredByLoc.length === 1 ? "" : "s"}
                    </div>
                  </div>

                  {filteredByLoc.length === 0 ? (
                    <EmptyState
                      title={showArchived ? "No archived departments found" : "No departments found"}
                      description={showArchived ? "There are currently no archived departments." : "Try selecting another location or configure a new department above."}
                    />
                  ) : (
                    <Table
                      columns={mappingGridColumns}
                      rows={filteredByLoc}
                      getRowKey={(row) => row.department_id}
                    />
                  )}
                </Card>
              );
            }

            const sortedLocations = [...rawLocations].sort((a, b) =>
              (a.name || "").localeCompare(b.name || "")
            );

            const targetLocations = selectedLocation
              ? sortedLocations.filter((l) => l.location_id === selectedLocation)
              : sortedLocations;

            if (targetLocations.length === 0 || rawDepartments.length === 0) {
              return (
                <EmptyState
                  title={showArchived ? "No archived departments found" : "No departments found"}
                  description={showArchived ? "There are currently no archived departments." : "Try selecting another location or toggling 'Archived'."}
                />
              );
            }

            return (
              <div className="grid gap-5">
                {/* Location Quick Navigation Directory */}
                <div className="p-3.5 sm:p-4 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/90 dark:border-slate-800 shadow-2xs space-y-3">
                  <div className="flex items-center justify-between gap-3 flex-wrap">
                    <div className="flex items-center gap-2 text-xs font-bold text-slate-800 dark:text-slate-200">
                      <div className="p-1.5 rounded-lg bg-primary/10 text-primary">
                        <Building className="h-4 w-4" />
                      </div>
                      <span>Campus Locations Directory ({sortedLocations.length})</span>
                      <span className="hidden sm:inline text-[11px] font-normal text-slate-500 dark:text-slate-400">
                        &bull; Click any location to filter and expand its departments
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => expandAllLocations(sortedLocations)}
                        className="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors cursor-pointer text-[11px] font-bold border border-slate-200/70 dark:border-slate-700"
                        title="Expand all locations"
                      >
                        Expand All
                      </button>
                      <button
                        type="button"
                        onClick={collapseAllLocations}
                        className="px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors cursor-pointer text-[11px] font-bold border border-slate-200/70 dark:border-slate-700"
                        title="Collapse all locations"
                      >
                        Collapse All
                      </button>
                    </div>
                  </div>

                  {/* Location Pills Navigation */}
                  <div className="flex items-center gap-2 overflow-x-auto pb-1 pt-0.5 no-scrollbar flex-wrap">
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedLocation("");
                      }}
                      className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer shadow-2xs ${
                        !selectedLocation
                          ? "bg-primary text-white shadow-sm ring-2 ring-primary/20"
                          : "bg-slate-50 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 border border-slate-200/90 dark:border-slate-700 hover:border-primary/50"
                      }`}
                    >
                      <span>All Locations</span>
                      <span
                        className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                          !selectedLocation
                            ? "bg-white/20 text-white"
                            : "bg-slate-200/80 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                        }`}
                      >
                        {sortedLocations.length}
                      </span>
                    </button>

                    {sortedLocations.map((loc) => {
                      const count = rawDepartments.filter(
                        (d) =>
                          (d.location_ids || []).includes(loc.location_id) ||
                          d.location_id === loc.location_id
                      ).length;
                      const isSelected = selectedLocation === loc.location_id;
                      const isExpanded = isSelected || !!expandedLocations[loc.location_id];

                      return (
                        <button
                          key={loc.location_id}
                          type="button"
                          onClick={() => {
                            if (selectedLocation === loc.location_id) {
                              toggleLocationExpand(loc.location_id);
                            } else {
                              setSelectedLocation(loc.location_id);
                              setExpandedLocations((prev) => ({
                                ...prev,
                                [loc.location_id]: true,
                              }));
                            }
                          }}
                          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer shadow-2xs ${
                            isSelected
                              ? "bg-primary text-white shadow-sm ring-2 ring-primary/20"
                              : isExpanded
                              ? "bg-primary/10 text-primary border border-primary/30 dark:bg-primary/20 dark:border-primary/50 font-bold"
                              : "bg-slate-50 dark:bg-slate-800/80 text-slate-700 dark:text-slate-300 border border-slate-200/90 dark:border-slate-700 hover:border-slate-300"
                          }`}
                          title={`Click to view departments operating at ${loc.name}`}
                        >
                          <MapPin className="h-3 w-3 shrink-0" />
                          <span>{loc.name}</span>
                          <span
                            className={`text-[10px] px-1.5 py-0.2 rounded-full font-bold ${
                              isSelected
                                ? "bg-white/20 text-white"
                                : "bg-slate-200/80 dark:bg-slate-700 text-slate-600 dark:text-slate-300"
                            }`}
                          >
                            {count}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Collapsible Location Cards */}
                {targetLocations.map((loc) => {
                  const locDepts = rawDepartments.filter(
                    (d) =>
                      (d.location_ids || []).includes(loc.location_id) ||
                      d.location_id === loc.location_id
                  );
                  const isExpanded = selectedLocation === loc.location_id || !!expandedLocations[loc.location_id];

                  return (
                    <Card
                      key={loc.location_id}
                      className="!p-0 overflow-hidden border border-slate-200/90 dark:border-slate-800 shadow-2xs transition-shadow duration-200 hover:shadow-xs"
                    >
                      {/* Clickable Header for Expand / Collapse */}
                      <button
                        type="button"
                        onClick={() => toggleLocationExpand(loc.location_id)}
                        className="w-full flex items-center justify-between p-4 sm:p-5 text-left bg-white dark:bg-slate-900 hover:bg-slate-50/90 dark:hover:bg-slate-800/50 transition-colors cursor-pointer select-none"
                        aria-expanded={isExpanded}
                      >
                        <div className="flex items-center gap-3.5 min-w-0">
                          <div
                            className={`p-2.5 rounded-xl transition-all duration-200 ${
                              isExpanded
                                ? "bg-primary text-white shadow-xs scale-105"
                                : "bg-primary/10 text-primary"
                            }`}
                          >
                            <MapPin className="h-5 w-5" />
                          </div>
                          <div className="min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <h2 className="text-base font-bold text-slate-900 dark:text-slate-100 truncate">
                                🏢 {loc.name}
                              </h2>
                              {loc.type && (
                                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200/80 dark:border-slate-700">
                                  {loc.type}
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-slate-500 dark:text-slate-400 font-medium mt-0.5">
                              {locDepts.length} central department{locDepts.length === 1 ? "" : "s"} operating at this location
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-2.5 shrink-0">
                          <span className="hidden sm:inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 border border-slate-200/80 dark:border-slate-700">
                            {locDepts.length} Depts
                          </span>
                          <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-200/80 dark:border-slate-700 transition-colors">
                            <span>{isExpanded ? "Collapse" : "Expand"}</span>
                            <ChevronDown
                              className={`h-4 w-4 transition-transform duration-200 ${
                                isExpanded ? "rotate-180 text-primary" : ""
                              }`}
                            />
                          </div>
                        </div>
                      </button>

                      {/* Expanded Departments Table */}
                      {isExpanded && (
                        <div className="p-4 sm:p-6 border-t border-slate-100 dark:border-slate-800 bg-slate-50/30 dark:bg-slate-900/40">
                          {locDepts.length === 0 ? (
                            <div className="py-6 text-center text-xs font-medium text-slate-400 dark:text-slate-500 bg-slate-50/50 dark:bg-slate-900/50 rounded-xl border border-dashed border-slate-200 dark:border-slate-800">
                              No departments operating at {loc.name} yet. Use "Manage Locations" or the Locations page to assign departments.
                            </div>
                          ) : (
                            <Table
                              columns={columns}
                              rows={locDepts}
                              getRowKey={(row) => row.department_id}
                            />
                          )}
                        </div>
                      )}
                    </Card>
                  );
                })}
              </div>
            );
          })()}
        </div>
      )}

      {/* Edit Modal */}
      <Modal
        open={!!editTarget}
        title="Edit Department"
        onClose={() => setEditTarget(null)}
      >
        <form onSubmit={handleEditSubmit} className="grid gap-5">
          <Input
            label="Department Name"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            required
          />
          <Input
            label="Description"
            value={editDescription}
            onChange={(e) => setEditDescription(e.target.value)}
            placeholder="Department role and scope"
          />
          <Input
            label="SLA Resolution Days"
            type="number"
            min="1"
            value={editSla}
            onChange={(e) => setEditSla(e.target.value)}
            required
          />
          <Input
            label="Complaint Types (comma separated)"
            value={editComplaintTypes}
            onChange={(e) => setEditComplaintTypes(e.target.value)}
            required
          />

          <div className="mt-6 flex justify-end gap-3">
            <Button variant="subtle" onClick={() => setEditTarget(null)}>
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Save Changes
            </Button>
          </div>
        </form>
      </Modal>

      {/* Operating Locations Modal */}
      <Modal
        open={!!viewLocationsTarget}
        title={`Operating Locations — ${viewLocationsTarget?.name || ""}`}
        onClose={() => setViewLocationsTarget(null)}
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Configure which campus locations <strong>{viewLocationsTarget?.name}</strong> operates in.
            Students at selected locations will be able to file complaints to this department.
          </p>

          {renderLocationSelector(modalLocationIds, setModalLocationIds)}

          <div className="mt-6 flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
            <Button
              variant="subtle"
              onClick={() => setViewLocationsTarget(null)}
              disabled={locModalSaving}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={handleSaveLocationsModal}
              disabled={locModalSaving}
            >
              {locModalSaving ? "Saving..." : "Save Locations"}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Eligible Workforce Modal */}
      <Modal
        open={!!viewWorkforceTarget}
        title={`Eligible Staff — ${viewWorkforceTarget?.name || ""}`}
        onClose={() => setViewWorkforceTarget(null)}
      >
        <div className="space-y-4">
          <div className="p-3 bg-blue-50 dark:bg-blue-950/40 rounded-xl border border-blue-200 dark:border-blue-800 text-xs text-blue-900 dark:text-blue-200 leading-relaxed">
            <strong>Department Workforce:</strong> Employees and coordinators eligible to resolve complaints in {viewWorkforceTarget?.name}.
          </div>

          {eligibleStaffLoading ? (
            <div className="flex items-center justify-center p-6 text-sm text-slate-500">
              <RefreshCw className="h-4 w-4 animate-spin mr-2" />
              Loading eligible workforce...
            </div>
          ) : eligibleStaff.length === 0 ? (
            <div className="py-6 text-center text-xs text-slate-500">
              No staff members currently registered or eligible for this department.
            </div>
          ) : (
            <div className="max-h-80 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-800">
              {eligibleStaff.map((staff) => (
                <div key={staff.user_id} className="py-2.5 flex items-center justify-between text-xs">
                  <div>
                    <div className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                      {staff.name}
                      <span className="capitalize px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                        {staff.role}
                      </span>
                      {staff.is_on_leave && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-200">
                          On Leave
                        </span>
                      )}
                    </div>
                    <div className="text-slate-500 text-[11px] mt-0.5">
                      {staff.email} {staff.phone_number ? `• ${staff.phone_number}` : ""}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="px-2 py-0.5 rounded-full text-[11px] font-bold bg-primary/10 text-primary">
                      {staff.active_workload || 0} active tickets
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="mt-6 flex justify-end">
            <Button variant="subtle" onClick={() => setViewWorkforceTarget(null)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        open={!!deleteTarget}
        title="Delete Department?"
        onClose={() => setDeleteTarget(null)}
      >
        <div className="text-sm text-slate-600 dark:text-slate-300 leading-normal">
          This action cannot be undone. To permanently delete the department{" "}
          <strong>{deleteTarget?.name}</strong>, type <strong>DELETE</strong> in
          the box below:
        </div>
        <input
          type="text"
          className="mt-4 h-11 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs outline-none focus:border-red-500 text-slate-800 dark:text-slate-100"
          placeholder="Type DELETE to confirm"
          value={deleteInput}
          onChange={(e) => setDeleteInput(e.target.value)}
        />
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="subtle" onClick={() => setDeleteTarget(null)}>
            Cancel
          </Button>
          <Button
            variant="danger"
            disabled={deleteInput !== "DELETE"}
            onClick={handleDelete}
          >
            Delete permanently
          </Button>
        </div>
      </Modal>

      {/* Delete Dependency Warning Modal */}
      <Modal
        open={!!deleteDependencyError}
        title="Cannot Delete Department"
        onClose={() => setDeleteDependencyError("")}
      >
        <div className="text-sm text-slate-600 dark:text-slate-300 leading-normal">
          {deleteDependencyError}
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="subtle" onClick={() => setDeleteDependencyError("")}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleArchiveFromError}>
            Archive Department Instead
          </Button>
        </div>
      </Modal>

      {/* Assign Department Coordinators Modal */}
      <Modal
        open={!!assignCoordsTarget}
        title={`Campus Coordinators — ${assignCoordsTarget?.name || ""}`}
        onClose={() => setAssignCoordsTarget(null)}
      >
        <div className="space-y-4">
          <div className="p-3 bg-blue-50 dark:bg-blue-950/40 rounded-xl border border-blue-200 dark:border-blue-800 text-xs text-blue-900 dark:text-blue-200 leading-relaxed">
            <strong>Campus-Wide Coordination Policy:</strong>
            <p className="mt-1">
              Each department has exactly two coordinator positions: <strong>Coordinator 1</strong> (Primary) and <strong>Coordinator 2</strong> (Backup). Coordinators supervise department complaints campus-wide. Employees can coordinate multiple departments simultaneously, but cannot hold both positions within the same department.
            </p>
          </div>

          {coordsModalError && (
            <div className="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-xl text-xs text-rose-700 dark:text-rose-300">
              {coordsModalError}
            </div>
          )}

          {eligibleCoordsLoading ? (
            <div className="flex items-center justify-center p-6 text-sm text-slate-500">
              <RefreshCw className="h-4 w-4 animate-spin mr-2" />
              Loading eligible workforce...
            </div>
          ) : (
            <form onSubmit={handleSaveCoordinators} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Coordinator 1 (Primary Coordinator)
                </label>
                <Select
                  value={c1Selected}
                  onChange={(e) => setC1Selected(e.target.value)}
                  className="w-full text-xs"
                >
                  <option value="">Unassigned</option>
                  {eligibleCoords.map((emp) => {
                    const isDisabled = !emp.is_eligible && emp.user_id !== c1Selected;
                    const assignmentsLabel = (emp.current_assignments && emp.current_assignments.length > 0)
                      ? ` [Coords: ${emp.current_assignments.map(a => `${a.department_name} (${a.position})`).join(", ")}]`
                      : "";
                    return (
                      <option
                        key={emp.user_id}
                        value={emp.user_id}
                        disabled={isDisabled}
                      >
                        {emp.name} ({emp.email}){assignmentsLabel}
                        {emp.is_on_leave ? " — On Leave" : ""}
                        {isDisabled && emp.ineligible_reason ? ` — Ineligible: ${emp.ineligible_reason}` : ""}
                      </option>
                    );
                  })}
                </Select>
                <p className="text-[11px] text-slate-400 mt-0.5">Primary intake coordinator who receives and assigns new department complaints.</p>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Coordinator 2 (Backup Coordinator)
                </label>
                <Select
                  value={c2Selected}
                  onChange={(e) => setC2Selected(e.target.value)}
                  className="w-full text-xs"
                >
                  <option value="">Unassigned</option>
                  {eligibleCoords.map((emp) => {
                    const isDisabled = !emp.is_eligible && emp.user_id !== c2Selected;
                    const assignmentsLabel = (emp.current_assignments && emp.current_assignments.length > 0)
                      ? ` [Coords: ${emp.current_assignments.map(a => `${a.department_name} (${a.position})`).join(", ")}]`
                      : "";
                    return (
                      <option
                        key={emp.user_id}
                        value={emp.user_id}
                        disabled={isDisabled}
                      >
                        {emp.name} ({emp.email}){assignmentsLabel}
                        {emp.is_on_leave ? " — On Leave" : ""}
                        {isDisabled && emp.ineligible_reason ? ` — Ineligible: ${emp.ineligible_reason}` : ""}
                      </option>
                    );
                  })}
                </Select>
                <p className="text-[11px] text-slate-400 mt-0.5">Backup coordinator who takes over when Coordinator 1 is on leave or unavailable.</p>
              </div>

              <div className="mt-6 flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                <Button variant="subtle" onClick={() => setAssignCoordsTarget(null)} disabled={savingCoords}>
                  Cancel
                </Button>
                <Button type="submit" variant="primary" disabled={savingCoords}>
                  {savingCoords ? "Saving Coordinators..." : "Save Coordinators"}
                </Button>
              </div>
            </form>
          )}
        </div>
      </Modal>

      {/* View All Categories Modal */}

      <Modal
        open={!!viewCategoriesTarget}
        title={`Categories — ${viewCategoriesTarget?.name || ""}`}
        onClose={() => setViewCategoriesTarget(null)}
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-500 dark:text-slate-400">
            All complaint categories registered for this department:
          </p>
          <div className="flex flex-wrap gap-2 max-h-60 overflow-y-auto p-1">
            {(viewCategoriesTarget?.complaint_types || []).map((cat, idx) => (
              <span
                key={idx}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-primary/10 text-primary border border-primary/20"
              >
                {cat}
              </span>
            ))}
          </div>
          <div className="mt-6 flex justify-end">
            <Button variant="subtle" onClick={() => setViewCategoriesTarget(null)}>
              Close
            </Button>
          </div>
        </div>
      </Modal>

      {/* Edit Covered Categories Modal */}
      <Modal
        open={!!categoryModalDept}
        title={`Edit Covered Categories — ${categoryModalDept?.name || ""}`}
        onClose={() => setCategoryModalDept(null)}
        className="max-w-lg"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Manage complaint and service categories covered by <strong>{categoryModalDept?.name}</strong>. Students and staff will choose from these issues when filing requests.
          </p>

          {/* Quick Add input */}
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={newCategoryInput}
              onChange={(e) => setNewCategoryInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleAddCategoryItem();
                }
              }}
              placeholder="Enter category name (e.g. Door, Window, Chair)..."
              className="flex-1 h-9 px-3 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-xs text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:border-primary"
            />
            <Button
              type="button"
              variant="primary"
              size="sm"
              onClick={handleAddCategoryItem}
              className="shrink-0 font-semibold"
            >
              + Add
            </Button>
          </div>

          {/* Line by line category items list */}
          <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-3 bg-slate-50/50 dark:bg-slate-900/50 max-h-72 overflow-y-auto space-y-2">
            {categoryList.length === 0 ? (
              <p className="text-xs text-slate-400 italic text-center py-4">
                No categories registered yet. Add at least one category above.
              </p>
            ) : (
              categoryList.map((cat, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between gap-2 px-3 py-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200/80 dark:border-slate-700 shadow-2xs group"
                >
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">
                    {cat}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleRemoveCategoryItem(cat)}
                    className="p-1 rounded text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors cursor-pointer"
                    title={`Remove ${cat}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))
            )}
          </div>

          <div className="flex items-center justify-between pt-2">
            <span className="text-xs text-slate-500 font-medium">
              {categoryList.length} categorie{categoryList.length === 1 ? "" : "s"} configured
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="subtle"
                type="button"
                onClick={() => setCategoryModalDept(null)}
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                type="button"
                disabled={categoryModalSaving || categoryList.length === 0}
                onClick={handleSaveCategories}
                className="font-semibold px-4"
              >
                {categoryModalSaving ? "Saving..." : "Save Categories"}
              </Button>
            </div>
          </div>
        </div>
      </Modal>

      {/* Edit Department Timings & SLA Modal */}
      <Modal
        open={!!timingModalDept}
        title={`Edit Department Timings & SLA — ${timingModalDept?.name || ""}`}
        onClose={() => setTimingModalDept(null)}
        className="max-w-4xl"
      >
        <div className="space-y-4">
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Customize working hours, resolution targets, and escalation triggers for <strong>{timingModalDept?.name}</strong>.
          </p>

          {timingModalError && (
            <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-xs text-rose-700 dark:text-rose-300 font-medium flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>{timingModalError}</span>
            </div>
          )}

          {timingModalLoading || !timingModalConfig ? (
            <div className="py-12 flex justify-center">
              <Loader />
            </div>
          ) : (
            <form onSubmit={handleSaveTimingModal} className="space-y-5">
              {/* Overall SLA Days */}
              <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/40 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <label className="text-xs font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                    <Clock className="h-4 w-4 text-primary" />
                    Overall Standard Department SLA (Days)
                  </label>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400">
                    Baseline turnaround expectation displayed on student tickets and dashboard metrics.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="number"
                    min="1"
                    value={timingModalConfig.sla_days || 3}
                    onChange={(e) =>
                      setTimingModalConfig({
                        ...timingModalConfig,
                        sla_days: e.target.value,
                      })
                    }
                    className="h-9 w-24 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-xs font-mono font-semibold"
                    required
                  />
                  <span className="text-xs text-slate-400 font-semibold">days</span>
                </div>
              </div>

              {/* Priority Working Hours & Duration Table */}
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-2 flex items-center gap-1.5">
                  <Sliders className="h-3.5 w-3.5 text-primary" />
                  Priority Working Hours & Target Durations
                </h4>
                <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-50 dark:bg-slate-800/60 text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider border-b border-slate-200 dark:border-slate-800">
                      <tr>
                        <th className="px-3.5 py-2.5">Priority</th>
                        <th className="px-3.5 py-2.5">Start Time</th>
                        <th className="px-3.5 py-2.5">End Time</th>
                        <th className="px-3.5 py-2.5">Resolution Target</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-medium">
                      {/* Normal / Low */}
                      <tr>
                        <td className="px-3.5 py-2.5 font-bold text-slate-800 dark:text-slate-200 flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-slate-400 inline-block"></span>
                          Normal / Low
                        </td>
                        <td className="px-3.5 py-2">
                          <CleanTimeSelect
                            value={timingModalConfig.normal_start_time || "10:00"}
                            onChange={(val) =>
                              setTimingModalConfig({
                                ...timingModalConfig,
                                normal_start_time: val,
                              })
                            }
                          />
                        </td>
                        <td className="px-3.5 py-2">
                          <CleanTimeSelect
                            value={timingModalConfig.normal_end_time || "16:00"}
                            onChange={(val) =>
                              setTimingModalConfig({
                                ...timingModalConfig,
                                normal_end_time: val,
                              })
                            }
                          />
                        </td>
                        <td className="px-3.5 py-2">
                          <div className="flex items-center gap-1.5">
                            <input
                              type="number"
                              min="1"
                              value={timingModalConfig.normal_duration_hours || 72}
                              onChange={(e) =>
                                setTimingModalConfig({
                                  ...timingModalConfig,
                                  normal_duration_hours: e.target.value,
                                })
                              }
                              className="h-8.5 w-20 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-2 text-xs font-mono font-semibold"
                            />
                            <span className="text-slate-400 text-[11px]">hours</span>
                          </div>
                        </td>
                      </tr>

                      {/* Medium */}
                      <tr>
                        <td className="px-3.5 py-2.5 font-bold text-blue-700 dark:text-blue-300 flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-blue-500 inline-block"></span>
                          Medium
                        </td>
                        <td className="px-3.5 py-2">
                          <CleanTimeSelect
                            value={timingModalConfig.medium_start_time || "10:00"}
                            onChange={(val) =>
                              setTimingModalConfig({
                                ...timingModalConfig,
                                medium_start_time: val,
                              })
                            }
                          />
                        </td>
                        <td className="px-3.5 py-2">
                          <CleanTimeSelect
                            value={timingModalConfig.medium_end_time || "16:00"}
                            onChange={(val) =>
                              setTimingModalConfig({
                                ...timingModalConfig,
                                medium_end_time: val,
                              })
                            }
                          />
                        </td>
                        <td className="px-3.5 py-2">
                          <div className="flex items-center gap-1.5">
                            <input
                              type="number"
                              min="1"
                              value={timingModalConfig.medium_duration_hours || 48}
                              onChange={(e) =>
                                setTimingModalConfig({
                                  ...timingModalConfig,
                                  medium_duration_hours: e.target.value,
                                })
                              }
                              className="h-8.5 w-20 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-2 text-xs font-mono font-semibold"
                            />
                            <span className="text-slate-400 text-[11px]">hours</span>
                          </div>
                        </td>
                      </tr>

                      {/* High */}
                      <tr>
                        <td className="px-3.5 py-2.5 font-bold text-amber-700 dark:text-amber-300 flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block"></span>
                          High
                        </td>
                        <td className="px-3.5 py-2">
                          <CleanTimeSelect
                            value={timingModalConfig.high_start_time || "10:00"}
                            onChange={(val) =>
                              setTimingModalConfig({
                                ...timingModalConfig,
                                high_start_time: val,
                              })
                            }
                          />
                        </td>
                        <td className="px-3.5 py-2">
                          <CleanTimeSelect
                            value={timingModalConfig.high_end_time || "18:00"}
                            onChange={(val) =>
                              setTimingModalConfig({
                                ...timingModalConfig,
                                high_end_time: val,
                              })
                            }
                          />
                        </td>
                        <td className="px-3.5 py-2">
                          <div className="flex items-center gap-1.5">
                            <input
                              type="number"
                              min="1"
                              value={timingModalConfig.high_duration_hours || 24}
                              onChange={(e) =>
                                setTimingModalConfig({
                                  ...timingModalConfig,
                                  high_duration_hours: e.target.value,
                                })
                              }
                              className="h-8.5 w-20 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-2 text-xs font-mono font-semibold"
                            />
                            <span className="text-slate-400 text-[11px]">hours</span>
                          </div>
                        </td>
                      </tr>

                      {/* Critical */}
                      <tr className="bg-rose-50/40 dark:bg-rose-950/20">
                        <td className="px-3.5 py-2.5 font-bold text-rose-700 dark:text-rose-300 flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block animate-pulse"></span>
                          Critical (24/7)
                        </td>
                        <td className="px-3.5 py-2">
                          <CleanTimeSelect
                            value={timingModalConfig.critical_start_time || "00:00"}
                            onChange={(val) =>
                              setTimingModalConfig({
                                ...timingModalConfig,
                                critical_start_time: val,
                              })
                            }
                            className="border-rose-200 dark:border-rose-900/60 text-rose-700 dark:text-rose-300"
                          />
                        </td>
                        <td className="px-3.5 py-2">
                          <CleanTimeSelect
                            value={timingModalConfig.critical_end_time || "23:59"}
                            onChange={(val) =>
                              setTimingModalConfig({
                                ...timingModalConfig,
                                critical_end_time: val,
                              })
                            }
                            className="border-rose-200 dark:border-rose-900/60 text-rose-700 dark:text-rose-300"
                          />
                        </td>
                        <td className="px-3.5 py-2">
                          <div className="flex items-center gap-1.5">
                            <input
                              type="number"
                              min="1"
                              value={timingModalConfig.critical_duration_hours || 4}
                              onChange={(e) =>
                                setTimingModalConfig({
                                  ...timingModalConfig,
                                  critical_duration_hours: e.target.value,
                                })
                              }
                              className="h-8.5 w-20 rounded-lg border border-rose-200 dark:border-rose-900/60 bg-white dark:bg-slate-900 px-2 text-xs font-mono font-semibold text-rose-700 dark:text-rose-300"
                            />
                            <span className="text-slate-400 text-[11px]">hours</span>
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Escalation Thresholds */}
              <div className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/60 dark:bg-slate-800/40 space-y-3">
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                    <Shield className="h-3.5 w-3.5 text-primary" />
                    Automated Escalation Chain
                  </h4>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                    Target expired &rarr; Immediate App Manager Alert &rarr; +{timingModalConfig.app_manager_escalation_hours || 24}h &rarr; App Manager (2nd Alert) &rarr; +{timingModalConfig.admin_escalation_hours || 48}h &rarr; Admin Escalation.
                  </p>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                      App Manager 2nd Alert after overdue by (hours)
                    </label>
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        min="1"
                        value={timingModalConfig.app_manager_escalation_hours || 24}
                        onChange={(e) =>
                          setTimingModalConfig({
                            ...timingModalConfig,
                            app_manager_escalation_hours: e.target.value,
                          })
                        }
                        className="h-9 w-full rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 px-3 text-xs font-mono font-semibold"
                        required
                      />
                      <span className="text-xs text-slate-400 font-semibold shrink-0">hours</span>
                    </div>
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="block text-xs font-bold text-slate-700 dark:text-slate-300">
                        Notify Admin after overdue by (hours)
                      </label>
                      {!isAdmin && (
                        <span className="text-[10px] font-semibold text-slate-500 bg-slate-200 dark:bg-slate-700 px-1.5 py-0.5 rounded">
                          Admin Only
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        min="1"
                        value={timingModalConfig.admin_escalation_hours || 48}
                        disabled={!isAdmin}
                        readOnly={!isAdmin}
                        onChange={(e) =>
                          setTimingModalConfig({
                            ...timingModalConfig,
                            admin_escalation_hours: e.target.value,
                          })
                        }
                        className={`h-9 w-full rounded-xl border border-slate-200 dark:border-slate-700 px-3 text-xs font-mono font-semibold ${
                          isAdmin
                            ? "bg-white dark:bg-slate-900"
                            : "bg-slate-100 dark:bg-slate-800 text-slate-500 cursor-not-allowed"
                        }`}
                        required
                      />
                      <span className="text-xs text-slate-400 font-semibold shrink-0">hours</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="mt-6 flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
                <Button
                  type="button"
                  variant="subtle"
                  onClick={() => setTimingModalDept(null)}
                  disabled={timingModalSaving}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  disabled={timingModalSaving}
                >
                  {timingModalSaving ? "Saving Settings..." : "Save Timings & SLA"}
                </Button>
              </div>
            </form>
          )}
        </div>
      </Modal>
    </div>
  );
}
