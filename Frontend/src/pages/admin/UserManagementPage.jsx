import { useMemo, useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import {
  UserPlus,
  RotateCw,
  User,
  Upload,
  ShieldAlert,
  Check,
  X,
  ShieldX,
  Key,
  Trash2,
  Eye,
  EyeOff,
  FileSpreadsheet,
  Download,
  CheckCircle,
  Search,
  Building,
  MapPin,
  Users,
  Shield,
  ShieldCheck,
  UserCheck,
  GraduationCap,
  Copy,
  Plus,
  CheckCheck,
  Edit2,
  RotateCcw,
  Filter,
  Archive,
  FileText,
  Wrench,
  AlertTriangle,
  ArrowRightLeft,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Input from "../../components/Input.jsx";
import Loader from "../../components/Loader.jsx";
import PageHeader from "../../components/PageHeader.jsx";
import Select from "../../components/Select.jsx";
import Table from "../../components/Table.jsx";
import TableToolbar from "../../components/TableToolbar.jsx";
import Toast from "../../components/Toast.jsx";
import Badge from "../../components/Badge.jsx";
import ConfirmDialog from "../../components/ConfirmDialog.jsx";
import BulkImportModal from "../../components/BulkImportModal.jsx";
import CredentialSlipModal from "../../components/CredentialSlipModal.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { departmentService } from "../../services/departmentService.js";
import { locationService } from "../../services/locationService.js";
import { programService } from "../../services/programService.js";
import { userService } from "../../services/userService.js";
import { setupService } from "../../services/setupService.js";
import { ROLES, getRoleDisplayName } from "../../utils/constants.js";
import { matchesSearch } from "../../utils/search.js";
import apiClient, { getApiError } from "../../api/axios.js";

export default function UserManagementPage() {
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);

  // Additional Multi-filter engine states
  const [programFilter, setProgramFilter] = useState("");
  const [locationFilter, setLocationFilter] = useState("");
  const [deptFilter, setDeptFilter] = useState("");
  const [yearFilter, setYearFilter] = useState("");

  // Dynamic Location Editing modal
  const [editLocationUser, setEditLocationUser] = useState(null);
  const [selectedLocationId, setSelectedLocationId] = useState("");
  const [savingLocation, setSavingLocation] = useState(false);

  // Multi-Location Management Modal (for App Managers & Wardens)
  const [manageLocationsUser, setManageLocationsUser] = useState(null);
  const [selectedLocationsList, setSelectedLocationsList] = useState([]);
  const [savingAssignedLocations, setSavingAssignedLocations] = useState(false);
  const [modalLocationQuery, setModalLocationQuery] = useState("");
  const [modalFilterStatus, setModalFilterStatus] = useState("all"); // 'all', 'self', 'other', 'unassigned'

  // Employee Department Modal
  const [manageEmployeeUser, setManageEmployeeUser] = useState(null);
  const [selectedDeptIdsList, setSelectedDeptIdsList] = useState([]);
  const [savingEmployeeDepts, setSavingEmployeeDepts] = useState(false);
  const [deptSearchQuery, setDeptSearchQuery] = useState("");
  const [deptFilterTab, setDeptFilterTab] = useState("all"); // 'all', 'eligible', 'available'
  const [modalError, setModalError] = useState("");

  // User Recycle Bin states
  const [showRecycleBin, setShowRecycleBin] = useState(false);
  const [recycleBinUsers, setRecycleBinUsers] = useState([]);
  const [loadingRecycleBin, setLoadingRecycleBin] = useState(false);

  // Password visibility toggles
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  // Bulk Import states
  const [csvFile, setCsvFile] = useState(null);
  const [importReport, setImportReport] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importProgram, setImportProgram] = useState("");
  const [importAcademicYear, setImportAcademicYear] = useState(
    `${new Date().getFullYear()}-${new Date().getFullYear() + 1}`
  );
  const [importYear, setImportYear] = useState("1");
  const [importLocationId, setImportLocationId] = useState("");
  const [updateExisting, setUpdateExisting] = useState(false);
  const [showStaffImportModal, setShowStaffImportModal] = useState(false);
  const [slipData, setSlipData] = useState(null);

  // Academic Program Management modal
  const [showProgramModal, setShowProgramModal] = useState(false);
  const [newProgramName, setNewProgramName] = useState("");
  const [newProgramDuration, setNewProgramDuration] = useState(4);
  const [newProgramDesc, setNewProgramDesc] = useState("");
  const [savingProgram, setSavingProgram] = useState(false);

  // Student Lifecycle Status modal
  const [statusModalUser, setStatusModalUser] = useState(null);
  const [selectedLifecycleStatus, setSelectedLifecycleStatus] = useState("Active");
  const [savingStatus, setSavingStatus] = useState(false);

  // Edit Staff Name Modal
  const [editNameUser, setEditNameUser] = useState(null);
  const [editNameValue, setEditNameValue] = useState("");
  const [nameModalError, setNameModalError] = useState("");
  const [savingName, setSavingName] = useState(false);

  // Edit Responsibility & Role Modal
  const [editRespUser, setEditRespUser] = useState(null);
  const [selectedRespRole, setSelectedRespRole] = useState("employee");
  const [selectedCoordType, setSelectedCoordType] = useState("none"); // "none", "coordinator_1", "coordinator_2"
  const [selectedCoordDeptId, setSelectedCoordDeptId] = useState("");
  const [savingResp, setSavingResp] = useState(false);
  const [respModalError, setRespModalError] = useState("");

  // Copy activation link tracker
  const [copiedLinkIndex, setCopiedLinkIndex] = useState(null);

  // Status/Password toggle action states
  const [confirmAction, setConfirmAction] = useState(null);

  const { data, loading, error: fetchError, reload } = useAsyncData(async () => {
    const [users, departments, locations, programs] = await Promise.all([
      userService.list(),
      departmentService.list().catch(() => ({ data: [] })),
      locationService.list().catch(() => ({ data: [] })),
      programService.list().catch(() => ({ data: [] })),
    ]);
    return {
      users: users.data || [],
      departments: departments.data || [],
      locations: locations.data || [],
      programs: programs.data || [],
    };
  }, []);

  const [searchParams, setSearchParams] = useSearchParams();
  const activeCategoryTab = searchParams.get("tab") || "students";

  const defaultRole =
    currentUser?.role === ROLES.APP_MANAGER
      ? ROLES.COORDINATOR
      : ROLES.APP_MANAGER;

  const {
    register,
    handleSubmit,
    reset,
    watch,
    formState: { errors, isSubmitting },
  } = useForm({
    defaultValues: { role: defaultRole, password: "", confirmPassword: "" },
  });

  // Top-level Category Tabs (Students, App Managers & Wardens, Employees & Coordinators, All)
  const CATEGORY_TABS = useMemo(
    () => [
      {
        key: "students",
        label: "Students",
        subLabel: "Resident & Day Students",
        icon: GraduationCap,
      },
      {
        key: "supervisors",
        label: "App Managers & Wardens",
        subLabel: "Location Leadership & Supervisors",
        icon: ShieldCheck,
      },
      {
        key: "staff",
        label: "Coordinators",
        subLabel: "Department Coordinators",
        icon: Wrench,
      },
      {
        key: "all",
        label: "All Accounts",
        subLabel: "Complete Institutional Directory",
        icon: Users,
      },
    ],
    []
  );

  const categoryCounts = useMemo(() => {
    const all = data?.users || [];
    return {
      students: all.filter((u) => (u.role || "").toLowerCase() === ROLES.STUDENT).length,
      supervisors: all.filter((u) => {
        const r = (u.role || "").toLowerCase();
        return r === ROLES.APP_MANAGER || r === ROLES.LOCATION_IN_CHARGE || r === "warden";
      }).length,
      staff: all.filter((u) => {
        const r = (u.role || "").toLowerCase();
        return r === ROLES.EMPLOYEE || r === ROLES.COORDINATOR || Boolean(u.coordinator_position);
      }).length,
      all: all.length,
    };
  }, [data?.users]);

  const handleCategoryTabChange = (newTab) => {
    setSearchParams({ tab: newTab });
    setQuery("");
    setStatusFilter("");
    setRoleFilter("");
    setActiveRoleTab("all");
    setProgramFilter("");
    setLocationFilter("");
    setDeptFilter("");
    setYearFilter("");
  };

  // Role options available based on creator hierarchy and active category tab
  const allowedRoles = useMemo(() => {
    const isAppMgr = currentUser?.role === ROLES.APP_MANAGER;

    if (activeCategoryTab === "students") {
      return [{ value: ROLES.STUDENT, label: "Student" }];
    }
    if (activeCategoryTab === "supervisors") {
      const opts = [{ value: ROLES.LOCATION_IN_CHARGE, label: "Warden" }];
      if (!isAppMgr) {
        opts.unshift({ value: ROLES.APP_MANAGER, label: "App Manager" });
      }
      return opts;
    }
    if (activeCategoryTab === "staff") {
      return [
        { value: ROLES.COORDINATOR, label: "Coordinator" },
      ];
    }

    if (!isAppMgr) {
      return [
        { value: ROLES.APP_MANAGER, label: "App Manager" },
        { value: ROLES.COORDINATOR, label: "Coordinator" },
        { value: ROLES.LOCATION_IN_CHARGE, label: "Warden" },
        { value: ROLES.STUDENT, label: "Student" },
      ];
    }
    return [
      { value: ROLES.COORDINATOR, label: "Coordinator" },
      { value: ROLES.LOCATION_IN_CHARGE, label: "Warden" },
      { value: ROLES.STUDENT, label: "Student" },
    ];
  }, [currentUser, activeCategoryTab]);

  // Sync role in creation form when active tab or allowed roles change
  useEffect(() => {
    if (allowedRoles.length > 0) {
      reset((prev) => ({
        ...prev,
        role: allowedRoles[0].value,
      }));
    }
  }, [activeCategoryTab, allowedRoles, reset]);

  const selectedProgramObj = useMemo(() => {
    if (!importProgram || !data?.programs) return null;
    return data.programs.find((p) => p.name === importProgram);
  }, [importProgram, data?.programs]);

  const yearOptions = useMemo(() => {
    const duration = selectedProgramObj?.duration_years || 4;
    return Array.from({ length: duration }, (_, i) => String(i + 1));
  }, [selectedProgramObj]);

  const [activeRoleTab, setActiveRoleTab] = useState("all");

  const roleTabs = useMemo(() => [
    { id: "all", label: "All Roles", icon: Users },
    { id: ROLES.ADMINISTRATOR, label: "Admin", icon: Shield },
    { id: ROLES.APP_MANAGER, label: "App Manager", icon: UserCheck },
    { id: ROLES.COORDINATOR, label: "Coordinator", icon: Users },
    { id: ROLES.LOCATION_IN_CHARGE, label: "Warden", icon: MapPin },
    { id: ROLES.STUDENT, label: "Student", icon: User },
  ], []);

  const getRoleCount = (tabId) => {
    const all = data?.users || [];
    if (tabId === "all") return all.length;
    return all.filter((u) => {
      const r = (u.role || "").toLowerCase();
      if (tabId === ROLES.LOCATION_IN_CHARGE) {
        return r === ROLES.LOCATION_IN_CHARGE || r === "warden";
      }
      return r === tabId.toLowerCase();
    }).length;
  };

  // Status/Role/Program/Location/Dept/Year filters & multi-field search run against filtered category
  const users = useMemo(() => {
    const rawUsers = data?.users || [];
    const rawLocations = data?.locations || [];
    const rawDepts = data?.departments || [];

    return rawUsers.filter((u) => {
      const uRole = (u.role || "").toLowerCase();

      // 1. Primary Category separation
      if (activeCategoryTab === "students") {
        if (uRole !== ROLES.STUDENT) return false;
      } else if (activeCategoryTab === "supervisors") {
        if (
          uRole !== ROLES.APP_MANAGER &&
          uRole !== ROLES.LOCATION_IN_CHARGE &&
          uRole !== "warden"
        ) {
          return false;
        }
      } else if (activeCategoryTab === "staff") {
        if (
          uRole !== ROLES.EMPLOYEE &&
          uRole !== ROLES.COORDINATOR &&
          !u.coordinator_position
        ) {
          return false;
        }
      }

      // 2. Program filter (chiefly students)
      if (programFilter && (u.program || "").toLowerCase() !== programFilter.toLowerCase()) return false;

      // 3. Location filter
      if (locationFilter) {
        const matchesSingle = u.location_id === locationFilter;
        const matchesMulti = (u.assigned_locations || []).includes(locationFilter);
        if (!matchesSingle && !matchesMulti) return false;
      }

      // 4. Dept filter (chiefly staff/coordinators)
      if (deptFilter) {
        const matchesSingle = u.department_id === deptFilter;
        const matchesMulti = (u.assigned_departments || []).includes(deptFilter);
        if (!matchesSingle && !matchesMulti) return false;
      }

      // 5. Year filter
      if (yearFilter && String(u.year || "") !== String(yearFilter)) return false;

      // 6. Status filter
      if (statusFilter === "active" && !u.active && u.status !== "Active") return false;
      if (statusFilter === "disabled" && (u.active || u.status === "Active")) return false;
      if (statusFilter === "graduated" && (u.status || "").toLowerCase() !== "graduated") return false;
      if (statusFilter === "left_college" && (u.status || "").toLowerCase() !== "left college") return false;
      if (statusFilter === "transferred" && (u.status || "").toLowerCase() !== "transferred") return false;

      // 7. Granular Sub-Role filter
      const effectiveRole = roleFilter || (activeRoleTab !== "all" ? activeRoleTab : "");
      if (effectiveRole && effectiveRole !== "all") {
        const targetRole = effectiveRole.toLowerCase();
        if (targetRole === "warden" || targetRole === ROLES.LOCATION_IN_CHARGE) {
          if (uRole !== ROLES.LOCATION_IN_CHARGE && uRole !== "warden") return false;
        } else if (targetRole === "coordinator") {
          if (uRole !== ROLES.COORDINATOR && !u.coordinator_position) return false;
        } else if (targetRole === "employee_only") {
          if (uRole !== ROLES.EMPLOYEE || u.coordinator_position) return false;
        } else if (uRole !== targetRole) {
          return false;
        }
      }

      // 8. Query Search (matches Name, Email, Role, User ID, Roll Number, Location, Department)
      if (query.trim()) {
        const q = query.toLowerCase().trim();
        const nameMatch = (u.name || "").toLowerCase().includes(q);
        const emailMatch = (u.email || "").toLowerCase().includes(q);
        const roleMatch = (u.role || "").replace(/_/g, " ").toLowerCase().includes(q);
        const idMatch =
          (u.user_id || "").toLowerCase().includes(q) ||
          (u.roll_number || "").toLowerCase().includes(q);

        if (nameMatch || emailMatch || roleMatch || idMatch) return true;

        // Location lookup
        const locObj = rawLocations.find((l) => l.location_id === u.location_id);
        const locName = u.location_name || locObj?.name || u.hostel || u.block || u.location_id || "";
        const locMatch = locName.toLowerCase().includes(q);

        // Department lookup
        const deptObj = rawDepts.find((d) => d.department_id === u.department_id);
        const deptName = u.department_name || deptObj?.name || u.department_id || "";
        const deptMatch = deptName.toLowerCase().includes(q);

        if (!locMatch && !deptMatch) {
          return false;
        }
      }

      return true;
    });
  }, [
    data,
    activeCategoryTab,
    query,
    statusFilter,
    roleFilter,
    activeRoleTab,
    programFilter,
    locationFilter,
    deptFilter,
    yearFilter,
  ]);

  const handleClearFilters = () => {
    setQuery("");
    setStatusFilter("");
    setRoleFilter("");
    setActiveRoleTab("all");
    setProgramFilter("");
    setLocationFilter("");
    setDeptFilter("");
    setYearFilter("");
  };

  const loadRecycleBin = async () => {
    setLoadingRecycleBin(true);
    try {
      const res = await userService.listRecycleBin();
      setRecycleBinUsers(res.data?.users || []);
    } catch (err) {
      setError(getApiError(err, "Failed to load recycle bin users."));
    } finally {
      setLoadingRecycleBin(false);
    }
  };

  const handleRestoreUser = async (userId, name) => {
    setError("");
    try {
      await userService.restoreUser(userId);
      setMessage(`Restored user account for ${name}.`);
      loadRecycleBin();
      reload();
    } catch (err) {
      setError(getApiError(err, "Failed to restore user account."));
    }
  };

  const handleSaveLocation = async () => {
    if (!editLocationUser) return;
    setSavingLocation(true);
    setError("");
    try {
      await userService.update(editLocationUser.user_id, {
        location_id: selectedLocationId || null,
      });
      setMessage(`Updated operational location for ${editLocationUser.name}.`);
      setEditLocationUser(null);
      reload();
    } catch (err) {
      setError(getApiError(err, "Failed to update user location."));
    } finally {
      setSavingLocation(false);
    }
  };

  const openManageLocationsModal = (user) => {
    setManageLocationsUser(user);
    setModalLocationQuery("");
    setModalFilterStatus("all");
    const uRole = (user.role || "").toLowerCase();
    let initialLocs = user.assigned_locations || [];
    if (!initialLocs.length) {
      if (uRole === "app_manager") {
        initialLocs = (data?.locations || [])
          .filter((l) => l.app_manager_id === user.user_id)
          .map((l) => l.location_id);
      } else if (uRole === "location_in_charge" || uRole === "warden") {
        initialLocs = (data?.locations || [])
          .filter((l) => l.in_charge_id === user.user_id)
          .map((l) => l.location_id);
      }
    }
    setSelectedLocationsList(initialLocs);
  };

  // Location Allotment Mapping - strictly role-scoped:
  // App Managers vs App Managers, OR Wardens vs Wardens
  const locationAllotmentInfo = useMemo(() => {
    if (!manageLocationsUser) return {};
    const uRole = (manageLocationsUser.role || "").toLowerCase();
    const isAppMgr = uRole === "app_manager";

    // Strictly filter peers of the EXACT SAME role category
    const peerUsers = (data?.users || []).filter((u) => {
      const r = (u.role || "").toLowerCase();
      if (isAppMgr) {
        return r === "app_manager";
      } else {
        return r === "location_in_charge" || r === "warden";
      }
    });

    const infoMap = {};

    (data?.locations || []).forEach((loc) => {
      // Direct assignment field check on location
      let assignedUserId = isAppMgr ? loc.app_manager_id : loc.in_charge_id;

      // Also check peer profiles' assigned_locations list
      if (!assignedUserId) {
        const peerWithLoc = peerUsers.find((p) =>
          (p.assigned_locations || []).includes(loc.location_id) ||
          p.location_id === loc.location_id
        );
        if (peerWithLoc) {
          assignedUserId = peerWithLoc.user_id;
        }
      }

      const assignedUser = peerUsers.find((p) => p.user_id === assignedUserId);

      if (!assignedUser) {
        infoMap[loc.location_id] = {
          status: "unassigned",
          assignedUser: null,
          isSelf: false,
        };
      } else if (assignedUser.user_id === manageLocationsUser.user_id) {
        infoMap[loc.location_id] = {
          status: "self",
          assignedUser,
          isSelf: true,
        };
      } else {
        infoMap[loc.location_id] = {
          status: "other",
          assignedUser,
          isSelf: false,
        };
      }
    });

    return infoMap;
  }, [manageLocationsUser, data?.locations, data?.users]);

  // Track locations currently selected that are already allotted to other peers
  const reallocatedFromOthers = useMemo(() => {
    if (!manageLocationsUser) return [];
    return selectedLocationsList
      .map((lid) => ({
        locationId: lid,
        locationName: (data?.locations || []).find((l) => l.location_id === lid)?.name || lid,
        info: locationAllotmentInfo[lid],
      }))
      .filter((item) => item.info?.status === "other");
  }, [manageLocationsUser, selectedLocationsList, locationAllotmentInfo, data?.locations]);

  const countSelf = useMemo(() => {
    return (data?.locations || []).filter((l) => locationAllotmentInfo[l.location_id]?.status === "self").length;
  }, [data?.locations, locationAllotmentInfo]);

  const countOther = useMemo(() => {
    return (data?.locations || []).filter((l) => locationAllotmentInfo[l.location_id]?.status === "other").length;
  }, [data?.locations, locationAllotmentInfo]);

  const countUnassigned = useMemo(() => {
    return (data?.locations || []).filter((l) => locationAllotmentInfo[l.location_id]?.status === "unassigned").length;
  }, [data?.locations, locationAllotmentInfo]);

  const displayedModalLocations = useMemo(() => {
    return (data?.locations || []).filter((loc) => {
      const info = locationAllotmentInfo[loc.location_id] || { status: "unassigned" };

      if (modalFilterStatus === "self" && info.status !== "self") return false;
      if (modalFilterStatus === "other" && info.status !== "other") return false;
      if (modalFilterStatus === "unassigned" && info.status !== "unassigned") return false;

      if (modalLocationQuery.trim()) {
        const q = modalLocationQuery.toLowerCase().trim();
        const nameMatch = (loc.name || "").toLowerCase().includes(q);
        const idMatch = (loc.location_id || "").toLowerCase().includes(q);
        const typeMatch = (loc.location_type || "").toLowerCase().includes(q);
        const peerMatch = info.assignedUser?.name?.toLowerCase().includes(q) || false;
        if (!nameMatch && !idMatch && !typeMatch && !peerMatch) return false;
      }

      return true;
    });
  }, [data?.locations, locationAllotmentInfo, modalFilterStatus, modalLocationQuery]);

  const handleToggleLocationItem = (locationId) => {
    setSelectedLocationsList((prev) =>
      prev.includes(locationId)
        ? prev.filter((id) => id !== locationId)
        : [...prev, locationId]
    );
  };

  const handleSelectAllLocations = () => {
    setSelectedLocationsList((data?.locations || []).map((l) => l.location_id));
  };

  const handleSelectUnallottedOnly = () => {
    const unallottedOrMine = (data?.locations || [])
      .filter((loc) => {
        const info = locationAllotmentInfo[loc.location_id];
        return info?.status === "unassigned" || info?.status === "self";
      })
      .map((loc) => loc.location_id);
    setSelectedLocationsList(unallottedOrMine);
  };

  const handleClearAllLocations = () => {
    setSelectedLocationsList([]);
  };

  const handleSaveAssignedLocations = async () => {
    if (!manageLocationsUser) return;
    setSavingAssignedLocations(true);
    setError("");
    try {
      await userService.assignLocations(manageLocationsUser.user_id, selectedLocationsList);
      if (reallocatedFromOthers.length > 0) {
        setMessage(
          `Updated assigned locations for ${manageLocationsUser.name}. Reassigned ${reallocatedFromOthers.length} ${
            reallocatedFromOthers.length === 1 ? "location" : "locations"
          } from previous assignments.`
        );
      } else {
        setMessage(`Updated assigned locations for ${manageLocationsUser.name} successfully.`);
      }
      setManageLocationsUser(null);
      reload();
    } catch (err) {
      setError(err?.response?.data?.detail || "Failed to update assigned locations.");
    } finally {
      setSavingAssignedLocations(false);
    }
  };

  const openManageEmployeeModal = (user) => {
    setManageEmployeeUser(user);
    setDeptSearchQuery("");
    setDeptFilterTab("all");
    setModalError("");

    let initialDepts = [];
    if (Array.isArray(user.assigned_departments) && user.assigned_departments.length > 0) {
      initialDepts = [...user.assigned_departments];
    } else if (user.department_id) {
      initialDepts = [user.department_id];
    }

    // Always ensure active coordinator department is preserved
    const coordDept = (data?.departments || []).find(
      (d) => d.coordinator_id === user.user_id || d.coordinator_2_id === user.user_id
    );
    if (coordDept && !initialDepts.includes(coordDept.department_id)) {
      initialDepts.push(coordDept.department_id);
    }
    setSelectedDeptIdsList(Array.from(new Set(initialDepts)));
  };

  const handleToggleDeptItem = (deptId) => {
    setSelectedDeptIdsList((prev) =>
      prev.includes(deptId)
        ? prev.filter((id) => id !== deptId)
        : [...prev, deptId]
    );
  };

  const handleSelectAllDepts = () => {
    setSelectedDeptIdsList((data?.departments || []).map((d) => d.department_id));
  };

  const handleClearAllDepts = () => {
    if (manageEmployeeUser?.coordinator_position) {
      const coordDepts = (data?.departments || [])
        .filter((d) => d.coordinator_id === manageEmployeeUser.user_id || d.coordinator_2_id === manageEmployeeUser.user_id)
        .map((d) => d.department_id);
      setSelectedDeptIdsList(coordDepts);
    } else {
      setSelectedDeptIdsList([]);
    }
  };

  const handleSaveEmployeeDepartments = async () => {
    if (!manageEmployeeUser) return;
    setSavingEmployeeDepts(true);
    setModalError("");
    setError("");
    try {
      await userService.assignDepartments(manageEmployeeUser.user_id, selectedDeptIdsList);
      setMessage(`Updated eligible departments for ${manageEmployeeUser.name} successfully.`);
      setManageEmployeeUser(null);
      reload();
    } catch (err) {
      const errMsg = getApiError(err, "Failed to update employee departments.");
      setModalError(errMsg);
      setError(errMsg);
    } finally {
      setSavingEmployeeDepts(false);
    }
  };

  const displayedDepartments = useMemo(() => {
    const all = data?.departments || [];
    return all.filter((d) => {
      const isEligible = selectedDeptIdsList.includes(d.department_id);
      if (deptFilterTab === "eligible" && !isEligible) return false;
      if (deptFilterTab === "available" && isEligible) return false;

      if (deptSearchQuery.trim()) {
        const q = deptSearchQuery.toLowerCase().trim();
        const nameMatch = (d.name || "").toLowerCase().includes(q);
        const idMatch = (d.department_id || "").toLowerCase().includes(q);
        const locMatch = (d.location_id || "").toLowerCase().includes(q);
        if (!nameMatch && !idMatch && !locMatch) return false;
      }
      return true;
    });
  }, [data?.departments, selectedDeptIdsList, deptFilterTab, deptSearchQuery]);

  const handleExportUsers = async (format = "csv") => {
    setError("");
    try {
      const response = await userService.exportUsers({
        format,
        search: query || undefined,
        role: roleFilter || (activeRoleTab !== "all" ? activeRoleTab : undefined),
        status: statusFilter || undefined,
        department_id: deptFilter || undefined,
        location_id: locationFilter || undefined,
        program: programFilter || undefined,
      });
      const blob = new Blob([response.data], {
        type: format === "csv" ? "text/csv" : "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `users_export_${new Date().toISOString().slice(0, 10)}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      setError(getApiError(err, `Failed to export users as ${format.toUpperCase()}.`));
    }
  };

  const onSubmit = async (values) => {
    setMessage("");
    setError("");

    if (values.password !== values.confirmPassword) {
      setError("Confirm Password does not match Temporary Password.");
      return;
    }

    const payload = {
      name: values.name,
      email: values.email,
      password: values.password,
      role: values.role,
      department_id: null,
      location_id: null,
    };
    try {
      const res = await userService.create(payload);
      const createdUser = res?.data;
      reset({ role: defaultRole, password: "", confirmPassword: "" });
      if (createdUser?.activation_link) {
        setMessage(`User account created successfully! Welcome & activation email dispatched to ${payload.email}.`);
      } else {
        setMessage("User account created successfully.");
      }
      reload();
    } catch (err) {
      setError(getApiError(err, "Unable to create user."));
    }
  };

  // CSV/Excel Template download helper
  const handleDownloadTemplate = async () => {
    setError("");
    try {
      const response = await apiClient.get("/users/import/template", {
        responseType: "text",
      });
      const blob = new Blob([response.data], { type: "text/csv" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "user_import_template.csv";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      setError("Failed to download CSV template.");
    }
  };

  // Academic Program Management
  const handleCreateProgram = async (e) => {
    e.preventDefault();
    if (!newProgramName.trim()) return;
    setSavingProgram(true);
    setError("");
    try {
      await programService.create({
        name: newProgramName.trim(),
        duration_years: Number(newProgramDuration) || 4,
        description: newProgramDesc.trim(),
      });
      setMessage(`Program "${newProgramName.trim()}" created successfully.`);
      setNewProgramName("");
      setNewProgramDuration(4);
      setNewProgramDesc("");
      setShowProgramModal(false);
      reload();
    } catch (err) {
      setError(getApiError(err, "Failed to create academic program."));
    } finally {
      setSavingProgram(false);
    }
  };

  const handleDeleteProgram = async (programId, name) => {
    try {
      await programService.delete(programId);
      setMessage(`Program "${name}" removed.`);
      reload();
    } catch (err) {
      setError(getApiError(err, "Failed to delete program."));
    }
  };

  // Student Lifecycle Status Update
  const handleUpdateStudentStatus = async () => {
    if (!statusModalUser) return;
    setSavingStatus(true);
    setError("");
    try {
      await userService.updateStatus(statusModalUser.user_id, selectedLifecycleStatus);
      setMessage(`Updated ${statusModalUser.name}'s lifecycle status to "${selectedLifecycleStatus}".`);
      setStatusModalUser(null);
      reload();
    } catch (err) {
      setError(getApiError(err, "Failed to update student lifecycle status."));
    } finally {
      setSavingStatus(false);
    }
  };

  // Edit Staff Name Handlers
  const openEditNameModal = (user) => {
    setEditNameUser(user);
    setEditNameValue(user.name || "");
    setNameModalError("");
  };

  const handleSaveName = async () => {
    if (!editNameUser || !editNameValue.trim()) return;
    setSavingName(true);
    setNameModalError("");
    try {
      await userService.updateResponsibilityAndRole(editNameUser.user_id, {
        name: editNameValue.trim(),
      });
      setMessage(`Staff member name updated to "${editNameValue.trim()}" successfully.`);
      setEditNameUser(null);
      reload();
    } catch (err) {
      setNameModalError(err?.response?.data?.detail || "Failed to update staff member name.");
    } finally {
      setSavingName(false);
    }
  };

  // Edit Responsibility & Role Handlers
  const openEditResponsibilityModal = (user) => {
    setEditRespUser(user);
    setSelectedRespRole((user.role || "employee").toLowerCase());

    const cPos = user.coordinator_position || "";
    if (user.coordinator_slot === 1 || cPos.startsWith("Coordinator 1")) {
      setSelectedCoordType("coordinator_1");
    } else if (user.coordinator_slot === 2 || cPos.startsWith("Coordinator 2")) {
      setSelectedCoordType("coordinator_2");
    } else if ((user.role || "").toLowerCase() === "coordinator") {
      setSelectedCoordType("coordinator_1");
    } else {
      setSelectedCoordType("none");
    }

    const initialDeptId =
      user.coordinator_department_id ||
      user.department_id ||
      (user.assigned_departments && user.assigned_departments[0]) ||
      (data?.departments && data.departments[0]?.department_id) ||
      "";
    setSelectedCoordDeptId(initialDeptId);
    setRespModalError("");
  };

  const handleSaveResponsibility = async () => {
    if (!editRespUser) return;
    setSavingResp(true);
    setRespModalError("");
    try {
      const payload = {
        role: selectedRespRole,
        coordinator_type: ["employee", "coordinator"].includes(selectedRespRole) ? selectedCoordType : "none",
        department_id: selectedCoordType !== "none" ? selectedCoordDeptId : null,
      };
      await userService.updateResponsibilityAndRole(editRespUser.user_id, payload);
      setMessage(`Updated responsibility and role for ${editRespUser.name} successfully.`);
      setEditRespUser(null);
      reload();
    } catch (err) {
      setRespModalError(err?.response?.data?.detail || "Failed to update responsibility and role.");
    } finally {
      setSavingResp(false);
    }
  };

  // Bulk Import execution
  const handleCsvImport = async (e) => {
    e.preventDefault();
    if (!csvFile) return;
    setImporting(true);
    setImportReport(null);
    setMessage("");
    setError("");
    try {
      const response = await userService.importUsers(csvFile, {
        default_program: importProgram || undefined,
        default_academic_year: importAcademicYear || undefined,
        default_year: importYear || undefined,
        default_location_id: importLocationId || undefined,
        update_existing: updateExisting,
      });
      setImportReport(response.data);
      setMessage(
        `Bulk Import Completed: ${response.data.success_count} accounts processed successfully!`,
      );
      setCsvFile(null);
      reload();
    } catch (err) {
      setError(
        getApiError(err, "Bulk Import failed. Please verify format (.xlsx, .xls, .csv)."),
      );
    } finally {
      setImporting(false);
    }
  };

  // Export Import Report Credentials to CSV
  const handleExportImportCredentials = (reportData) => {
    if (!reportData || !reportData.report) return;
    const successfulRows = reportData.report.filter((r) => r.status === "Success");
    if (successfulRows.length === 0) return;

    let csvContent = "Name,Email,Role,Identifier,Action,Temporary Password,Activation Link\n";
    successfulRows.forEach((r) => {
      const name = `"${(r.name || "").replace(/"/g, '""')}"`;
      const email = `"${(r.email || "").replace(/"/g, '""')}"`;
      const role = `"${(r.role || "").replace(/"/g, '""')}"`;
      const id = `"${(r.identifier || "").replace(/"/g, '""')}"`;
      const action = `"${(r.action || "created").replace(/"/g, '""')}"`;
      const pwd = `"${(r.temporary_password || "").replace(/"/g, '""')}"`;
      const link = `"${(r.activation_link || "").replace(/"/g, '""')}"`;
      csvContent += `${name},${email},${role},${id},${action},${pwd},${link}\n`;
    });

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `imported_user_credentials_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // User Actions (Status Toggle / Password Reset)
  const handleToggleStatus = (targetUser) => {
    const nextActive = !targetUser.active;

    // Reactivation Hierarchy Rule
    if (nextActive && !targetUser.active) {
      const deactRole = (targetUser.deactivated_by_role || "").toLowerCase();
      const currentRole = (currentUser?.role || "").toLowerCase();
      if (
        (deactRole === "administrator" || deactRole === "admin") &&
        currentRole === ROLES.APP_MANAGER
      ) {
        setError(
          "This account was deactivated by an Admin and cannot be reactivated by an App Manager."
        );
        return;
      }
    }

    setConfirmAction({
      title: `${nextActive ? "Enable" : "Disable"} User`,
      message: `Are you sure you want to mark ${targetUser.name} as ${nextActive ? "active" : "inactive"}?`,
      confirmLabel: nextActive ? "Enable" : "Disable",
      tone: nextActive ? "success" : "danger",
      action: async () => {
        try {
          await userService.toggleStatus(targetUser.user_id, nextActive);
          setMessage(`User status updated.`);
          reload();
        } catch (err) {
          setError(
            getApiError(err, "Failed to update user status."),
          );
        }
      },
    });
  };

  const handleResetPassword = (targetUser) => {
    setConfirmAction({
      title: "Reset Password",
      message: `Reset temporary password for ${targetUser.name}? Complexity requirements will be enforced on their next login.`,
      confirmLabel: "Reset Password",
      tone: "primary",
      action: async () => {
        try {
          await userService.resetPassword(targetUser.user_id, "tempPass123!");
          setMessage(`Password reset to 'tempPass123!' successfully.`);
        } catch (err) {
          setError(getApiError(err, "Failed to reset password."));
        }
      },
    });
  };

  const handleForceDelete = async (targetUser) => {
    setError("");
    if (Boolean(targetUser.active)) {
      setError(
        `Cannot force delete ${targetUser.name} while active. Please deactivate/disable the user account first.`
      );
      return;
    }
    let impactMessage = `Are you sure you want to permanently remove ${targetUser.name}'s account?`;
    try {
      const impact = await userService.getDeletionImpact(targetUser.user_id);
      const bySource = impact.data?.by_source || {};
      const entries = Object.entries(bySource);
      if (entries.length > 0) {
        const summary = entries
          .map(([label, count]) => `${count} ${label.replace(/_/g, " ")}`)
          .join(", ");
        impactMessage = `${targetUser.name} has existing historical records (${summary}). These will be preserved — the account will be soft-deleted (not physically removed) so this history stays valid and viewable.`;
      } else {
        impactMessage = `${targetUser.name} has no historical records referencing it. The account will be soft-deleted and hidden from active lists.`;
      }
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          "Unable to check the account's historical records before deletion.",
      );
      return;
    }
    setConfirmAction({
      title: "Force Delete User",
      message: impactMessage,
      confirmLabel: "Force Delete User",
      tone: "danger",
      action: async () => {
        try {
          await userService.forceDelete(targetUser.user_id);
          setMessage(`${targetUser.name} was force-deleted successfully.`);
          reload();
        } catch (err) {
          setError(
            err?.response?.data?.detail || "Failed to force delete user.",
          );
        }
      },
    });
  };

  const columns = useMemo(() => {
    // Shared Actions Renderer
    const renderActions = (row) => {
      const isUserActive = Boolean(row.active);
      const isSelf = row.user_id === currentUser?.user_id;
      const canManage =
        currentUser?.role === ROLES.ADMINISTRATOR ||
        (currentUser?.role === ROLES.APP_MANAGER &&
          ![ROLES.ADMINISTRATOR, ROLES.APP_MANAGER].includes(row.role));

      if (isSelf) {
        return (
          <span className="text-slate-400 font-semibold text-xs italic" title="You cannot deactivate or delete your own account">
            Current User (Self)
          </span>
        );
      }

      if (!canManage)
        return (
          <span className="text-slate-400 font-semibold text-xs">-</span>
        );

      const deactRole = (row.deactivated_by_role || "").toLowerCase();
      const myRole = (currentUser?.role || "").toLowerCase();
      const isBlockedReactivation =
        !isUserActive &&
        (deactRole === "administrator" || deactRole === "admin") &&
        myRole === ROLES.APP_MANAGER;

      return (
        <div className="flex items-center gap-1.5">
          {row.role === ROLES.STUDENT && (
            <Button
              variant="subtle"
              size="sm"
              onClick={() => {
                setStatusModalUser(row);
                setSelectedLifecycleStatus(row.status || (isUserActive ? "Active" : "Inactive"));
              }}
              className="!h-8 px-2 text-xs font-bold text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-950/40"
              title="Manage Student Lifecycle Status (Graduated, Transferred, etc.)"
            >
              <GraduationCap className="h-4 w-4" />
            </Button>
          )}
          {row.role !== ROLES.STUDENT && (
            <Button
              variant="subtle"
              size="sm"
              onClick={async () => {
                try {
                  const res = await setupService.resetWorkerPassword(row.user_id);
                  setSlipData(res);
                } catch (err) {
                  setError(err?.response?.data?.detail || "Failed to generate temporary password slip.");
                }
              }}
              className="!h-8 px-2 text-xs font-bold text-amber-600 hover:bg-amber-50 dark:hover:bg-amber-950/40"
              title="Generate Worker Login Slip (CP-XXXX)"
            >
              <FileText className="h-4 w-4" />
            </Button>
          )}
          <Button
            variant="subtle"
            size="sm"
            disabled={isBlockedReactivation}
            onClick={() => handleToggleStatus(row)}
            className={`!h-8 px-2 text-xs font-bold ${isBlockedReactivation ? "opacity-50 cursor-not-allowed" : ""}`}
            title={
              isBlockedReactivation
                ? "Deactivated by Admin - App Manager cannot reactivate"
                : isUserActive
                ? "Disable Account"
                : "Enable Account"
            }
          >
            {isUserActive ? (
              <ShieldX className="h-4 w-4 text-red-500" />
            ) : (
              <Check className={`h-4 w-4 ${isBlockedReactivation ? "text-slate-400" : "text-emerald-500"}`} />
            )}
          </Button>
          <Button
            variant="subtle"
            size="sm"
            onClick={() => handleResetPassword(row)}
            className="!h-8 px-2 text-xs font-bold text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800"
            title="Reset Password"
          >
            <Key className="h-4 w-4" />
          </Button>
          {currentUser?.role === ROLES.ADMINISTRATOR && (
            <Button
              variant="subtle"
              size="sm"
              disabled={isUserActive}
              onClick={() => handleForceDelete(row)}
              className={`!h-8 px-2 text-xs font-bold text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 ${isUserActive ? "opacity-40 cursor-not-allowed" : ""}`}
              title={isUserActive ? "Deactivate user account before Force Delete" : "Force Delete User"}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      );
    };

    const renderStatusBadge = (row) => {
      const isUserActive = Boolean(row.active);
      const st = row.status || (isUserActive ? "Active" : "Disabled");
      let tone = isUserActive ? "success" : "danger";
      if (st === "Graduated") tone = "info";
      else if (st === "Left College" || st === "Transferred") tone = "warning";
      return <Badge tone={tone}>{st}</Badge>;
    };

    // 1. STUDENTS TAB COLUMNS
    if (activeCategoryTab === "students") {
      return [
        {
          key: "name",
          header: "Student",
          render: (row) => (
            <div>
              <div className="font-bold text-slate-900 dark:text-slate-100">
                {row.name}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 font-mono mt-0.5">
                {row.email}
              </div>
            </div>
          ),
        },
        {
          key: "identifier",
          header: "Roll / Student ID",
          render: (row) => (
            <span className="font-mono text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
              {row.roll_number || row.user_id}
            </span>
          ),
        },
        {
          key: "academic",
          header: "Academic Program & Year",
          render: (row) => (
            <div className="text-xs">
              <span className="font-bold text-slate-800 dark:text-slate-200">
                {row.program || "General"}
              </span>
              <span className="text-slate-500 dark:text-slate-400 font-medium ml-1.5">
                • Year {row.year || 1}
              </span>
            </div>
          ),
        },
        {
          key: "location",
          header: "Resident Hostel / Location",
          render: (row) => {
            const locObj = (data?.locations || []).find((l) => l.location_id === row.location_id);
            const locName = row.location_name || locObj?.name || row.hostel || row.block || "";
            const canEditLoc =
              currentUser?.role === ROLES.ADMINISTRATOR ||
              currentUser?.role === ROLES.APP_MANAGER ||
              currentUser?.role === ROLES.LOCATION_IN_CHARGE;

            return (
              <div className="flex items-center gap-1.5">
                {locName ? (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                    <MapPin className="h-3.5 w-3.5 text-primary shrink-0" />
                    {locName}
                  </span>
                ) : (
                  <span className="text-slate-400 text-xs font-semibold">Unassigned</span>
                )}
                {canEditLoc && (
                  <button
                    type="button"
                    onClick={() => {
                      setEditLocationUser(row);
                      setSelectedLocationId(row.location_id || "");
                    }}
                    className="text-slate-400 hover:text-primary p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                    title="Edit Student Resident Location"
                  >
                    <Edit2 className="h-3.5 w-3.5" />
                  </button>
                )}
              </div>
            );
          },
        },
        {
          key: "lifecycle",
          header: "Lifecycle Status",
          render: (row) => renderStatusBadge(row),
        },
        {
          key: "actions",
          header: "Action controls",
          render: (row) => renderActions(row),
        },
      ];
    }

    // 2. SUPERVISORS TAB COLUMNS (App Managers & Wardens)
    if (activeCategoryTab === "supervisors") {
      return [
        {
          key: "name",
          header: "Supervisor",
          render: (row) => (
            <div>
              <div className="font-bold text-slate-900 dark:text-slate-100">
                {row.name}
              </div>
              <div className="text-xs text-slate-500 dark:text-slate-400 font-mono mt-0.5">
                {row.email}
              </div>
            </div>
          ),
        },
        {
          key: "role",
          header: "Leadership Role",
          render: (row) => {
            const isAppMgr = (row.role || "").toLowerCase() === "app_manager";
            return (
              <span
                className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold ${
                  isAppMgr
                    ? "bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border border-indigo-200/50 dark:border-indigo-800/50"
                    : "bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200/50 dark:border-amber-800/50"
                }`}
              >
                {isAppMgr ? <UserCheck className="h-3.5 w-3.5" /> : <MapPin className="h-3.5 w-3.5" />}
                {getRoleDisplayName(row.role)}
              </span>
            );
          },
        },
        {
          key: "locations",
          header: "Supervised / Managed Locations",
          render: (row) => {
            const uRole = (row.role || "").toLowerCase();
            const isAppMgr = uRole === "app_manager";
            let locNames = row.assigned_location_names || [];
            if (!locNames.length && (row.assigned_locations || []).length > 0) {
              locNames = row.assigned_locations.map((lid) => {
                const l = (data?.locations || []).find((loc) => loc.location_id === lid);
                return l ? l.name : lid;
              });
            }
            if (!locNames.length) {
              locNames = (data?.locations || [])
                .filter((loc) => (isAppMgr ? loc.app_manager_id : loc.in_charge_id) === row.user_id)
                .map((loc) => loc.name);
            }

            const btnTheme = isAppMgr
              ? "bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 border-indigo-200/50 dark:border-indigo-800/50"
              : "bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 hover:bg-amber-100 border-amber-200/50 dark:border-amber-800/50";
            const iconColor = isAppMgr ? "text-indigo-500" : "text-amber-500";

            return (
              <button
                type="button"
                onClick={() => openManageLocationsModal(row)}
                className={`group inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border shadow-xs text-left ${btnTheme}`}
                title="Click to view or edit assigned locations"
              >
                <MapPin className={`h-3.5 w-3.5 shrink-0 ${iconColor} group-hover:scale-110 transition-transform`} />
                <span>
                  {locNames.length > 0
                    ? (locNames.length <= 2 ? locNames.join(", ") : `${locNames.length} Locations Managed`)
                    : "Assign Locations"}
                </span>
                <Edit2 className="h-3 w-3 ml-0.5 opacity-60 group-hover:opacity-100" />
              </button>
            );
          },
        },
        {
          key: "status",
          header: "Account Status",
          render: (row) => renderStatusBadge(row),
        },
        {
          key: "actions",
          header: "Action controls",
          render: (row) => renderActions(row),
        },
      ];
    }

    // 3. STAFF TAB COLUMNS (Coordinators)
    if (activeCategoryTab === "staff") {
      return [
        {
          key: "name",
          header: "Staff Member",
          render: (row) => (
            <div className="flex items-center gap-2">
              <div>
                <div className="font-bold text-slate-900 dark:text-slate-100 flex items-center gap-1.5">
                  <span>{row.name}</span>
                  <button
                    type="button"
                    onClick={() => openEditNameModal(row)}
                    className="p-1 rounded-md text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 transition-colors"
                    title={`Edit name for ${row.name}`}
                  >
                    <Edit2 className="h-3 w-3" />
                  </button>
                </div>
                <div className="text-xs text-slate-500 dark:text-slate-400 font-mono mt-0.5">
                  {row.email}
                </div>
              </div>
            </div>
          ),
        },
        {
          key: "responsibility",
          header: "Responsibility / Role",
          render: (row) => {
            const coordPos = row.coordinator_position;
            const isCoord = coordPos || (row.role || "").toLowerCase() === "coordinator";
            return (
              <button
                type="button"
                onClick={() => openEditResponsibilityModal(row)}
                className={`group inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs font-bold transition-all border shadow-xs text-left ${
                  isCoord
                    ? "bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border-blue-200/50 dark:border-blue-800/50 hover:bg-blue-100/80 dark:hover:bg-blue-900/50"
                    : "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200/50 dark:border-emerald-800/50 hover:bg-emerald-100/80 dark:hover:bg-emerald-900/50"
                }`}
                title="Click to edit employee responsibility and role"
              >
                {isCoord ? (
                  <Users className="h-3.5 w-3.5 text-blue-500 shrink-0 group-hover:scale-110 transition-transform" />
                ) : (
                  <Wrench className="h-3.5 w-3.5 text-emerald-500 shrink-0 group-hover:scale-110 transition-transform" />
                )}
                <span>{coordPos || (isCoord ? "Department Coordinator" : "Operational Staff")}</span>
                <Edit2 className="h-3 w-3 ml-0.5 opacity-60 group-hover:opacity-100" />
              </button>
            );
          },
        },
        {
          key: "departments",
          header: "Eligible Departments",
          render: (row) => {
            const deptNames = Array.from(new Set(row.assigned_department_names || []));

            return (
              <button
                type="button"
                onClick={() => openManageEmployeeModal(row)}
                className="group inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-50/70 dark:bg-emerald-950/30 hover:bg-emerald-100/80 dark:hover:bg-emerald-900/50 transition-all border border-emerald-200/50 dark:border-emerald-800/50 shadow-xs text-left"
                title="Click to edit employee eligible departments"
              >
                <Building className="h-3.5 w-3.5 text-emerald-600 shrink-0 group-hover:scale-110 transition-transform" />
                <span className="font-bold text-emerald-800 dark:text-emerald-200">
                  {deptNames.length > 0
                    ? (deptNames.length <= 2 ? deptNames.join(", ") : `${deptNames.length} Departments`)
                    : "Assign Departments"}
                </span>
                <Edit2 className="h-3 w-3 ml-0.5 opacity-60 group-hover:opacity-100 text-emerald-700 dark:text-emerald-300" />
              </button>
            );
          },
        },
        {
          key: "status",
          header: "Account Status",
          render: (row) => renderStatusBadge(row),
        },
        {
          key: "actions",
          header: "Action controls",
          render: (row) => (
            <div className="flex items-center gap-1.5">
              <Button
                variant="subtle"
                size="sm"
                onClick={() => navigate("/admin/employee-assignments")}
                className="!h-8 px-2 text-xs font-bold text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-950/40"
                title="Open Department Coordinators Page"
              >
                <Wrench className="h-3.5 w-3.5 mr-1" />
                <span>Assignments</span>
              </Button>
              {renderActions(row)}
            </div>
          ),
        },
      ];
    }

    // 4. ALL ACCOUNTS TAB (Comprehensive)
    return [
      {
        key: "name",
        header: "Name",
        render: (row) => (
          <div className="flex items-center gap-1.5 font-bold text-slate-900 dark:text-slate-100">
            <span>{row.name}</span>
            <button
              type="button"
              onClick={() => openEditNameModal(row)}
              className="p-1 rounded-md text-slate-400 hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-emerald-50 dark:hover:bg-emerald-950/40 transition-colors"
              title={`Edit name for ${row.name}`}
            >
              <Edit2 className="h-3 w-3" />
            </button>
          </div>
        ),
      },
      { key: "email", header: "Email" },
      {
        key: "role",
        header: "Role",
        render: (row) => {
          return (
            <button
              type="button"
              onClick={() => openEditResponsibilityModal(row)}
              className="group inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 transition-all border border-slate-200/50 dark:border-slate-700/50"
              title="Click to edit role and responsibility"
            >
              <span className="capitalize font-medium">{getRoleDisplayName(row.role)}</span>
              <Edit2 className="h-3 w-3 opacity-60 group-hover:opacity-100" />
            </button>
          );
        },
      },
      {
        key: "location",
        header: "Location / Dept",
        render: (row) => {
          const uRole = (row.role || "").toLowerCase();

          // 1. App Manager: multi-locations
          if (uRole === "app_manager") {
            let locNames = row.assigned_location_names || [];
            if (!locNames.length && (row.assigned_locations || []).length > 0) {
              locNames = row.assigned_locations.map((lid) => {
                const l = (data?.locations || []).find((loc) => loc.location_id === lid);
                return l ? l.name : lid;
              });
            }
            if (!locNames.length) {
              locNames = (data?.locations || [])
                .filter((loc) => loc.app_manager_id === row.user_id)
                .map((loc) => loc.name);
            }
            return (
              <button
                type="button"
                onClick={() => openManageLocationsModal(row)}
                className="group inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900/60 transition-all border border-indigo-200/50 dark:border-indigo-800/50 shadow-sm text-left"
                title="Click to view or edit managed locations"
              >
                <MapPin className="h-3.5 w-3.5 text-indigo-500 shrink-0 group-hover:scale-110 transition-transform" />
                <span>{locNames.length > 0 ? (locNames.length <= 2 ? locNames.join(", ") : `${locNames.length} Locations Managed`) : "Assign Locations"}</span>
                <Edit2 className="h-3 w-3 ml-0.5 opacity-60 group-hover:opacity-100" />
              </button>
            );
          }

          // 2. Warden / Location In-Charge: multi-locations or single
          if (uRole === "location_in_charge" || uRole === "warden") {
            let locNames = row.assigned_location_names || [];
            if (!locNames.length && (row.assigned_locations || []).length > 0) {
              locNames = row.assigned_locations.map((lid) => {
                const l = (data?.locations || []).find((loc) => loc.location_id === lid);
                return l ? l.name : lid;
              });
            }
            if (!locNames.length) {
              locNames = (data?.locations || [])
                .filter((loc) => loc.in_charge_id === row.user_id)
                .map((loc) => loc.name);
            }
            return (
              <button
                type="button"
                onClick={() => openManageLocationsModal(row)}
                className="group inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 hover:bg-amber-100 dark:hover:bg-amber-900/60 transition-all border border-amber-200/50 dark:border-amber-800/50 shadow-sm text-left"
                title="Click to view or edit assigned locations"
              >
                <MapPin className="h-3.5 w-3.5 text-amber-500 shrink-0 group-hover:scale-110 transition-transform" />
                <span>{locNames.length > 0 ? (locNames.length <= 2 ? locNames.join(", ") : `${locNames.length} Locations Assigned`) : "Assign Locations"}</span>
                <Edit2 className="h-3 w-3 ml-0.5 opacity-60 group-hover:opacity-100" />
              </button>
            );
          }

          // 3. Coordinator: Multi-department staff
          if (uRole === "employee") {
            const coordPos = row.coordinator_position;
            const membershipsCnt = row.work_memberships_count;
            const deptNames = row.assigned_department_names || [];
            return (
              <button
                type="button"
                onClick={() => openManageEmployeeModal(row)}
                className="group inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/60 transition-all border border-emerald-200/50 dark:border-emerald-800/50 shadow-sm text-left"
                title="Click to view employee eligible departments"
              >
                <Building className="h-3.5 w-3.5 text-emerald-500 shrink-0 group-hover:scale-110 transition-transform" />
                <span>
                  {coordPos
                    ? coordPos
                    : deptNames.length > 0
                    ? (deptNames.length <= 2 ? deptNames.join(", ") : `${deptNames.length} Departments`)
                    : (membershipsCnt && membershipsCnt > 0 ? `${membershipsCnt} Departments` : "Assign Departments")}
                </span>
                <Edit2 className="h-3 w-3 ml-0.5 opacity-60 group-hover:opacity-100" />
              </button>
            );
          }

          // 4. Coordinator: assigned departments
          if (uRole === "coordinator") {
            const deptNames = row.assigned_department_names || [];
            if (deptNames.length > 0) {
              return (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300" title={deptNames.join(", ")}>
                  <Building className="h-3.5 w-3.5 text-blue-500 shrink-0" />
                  {deptNames.length <= 2 ? deptNames.join(", ") : `${deptNames.length} Departments`}
                </span>
              );
            }
            const deptObj = (data?.departments || []).find((d) => d.department_id === row.department_id);
            const deptName = row.department_name || deptObj?.name || "";
            if (deptName) {
              return (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300">
                  <Building className="h-3.5 w-3.5 text-blue-500 shrink-0" />
                  {deptName}
                </span>
              );
            }
            return <span className="text-slate-400 text-xs font-semibold">Unassigned</span>;
          }

          // 5. Administrator: Institution-wide
          if (uRole === "administrator") {
            return (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300">
                <Shield className="h-3.5 w-3.5 text-purple-500 shrink-0" />
                Institution-wide
              </span>
            );
          }

          // 6. Super Admin: Platform-wide
          if (uRole === "super_admin") {
            return (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-red-50 dark:bg-red-950/40 text-red-700 dark:text-red-300">
                <ShieldAlert className="h-3.5 w-3.5 text-red-500 shrink-0" />
                Platform-wide
              </span>
            );
          }

          // 7. Student / Resident
          const locObj = (data?.locations || []).find((l) => l.location_id === row.location_id);
          const locName = row.location_name || locObj?.name || row.hostel || row.block || "";

          const canEditLoc =
            currentUser?.role === ROLES.ADMINISTRATOR ||
            currentUser?.role === ROLES.APP_MANAGER ||
            currentUser?.role === ROLES.LOCATION_IN_CHARGE;

          return (
            <div className="flex items-center gap-1.5">
              {locName ? (
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                  <MapPin className="h-3.5 w-3.5 text-primary shrink-0" />
                  {locName}
                </span>
              ) : (
                <span className="text-slate-400 text-xs font-semibold">Unassigned</span>
              )}
              {canEditLoc && (
                <button
                  type="button"
                  onClick={() => {
                    setEditLocationUser(row);
                    setSelectedLocationId(row.location_id || "");
                  }}
                  className="text-slate-400 hover:text-primary p-1 rounded hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  title="Edit Student Resident Location"
                >
                  <Edit2 className="h-3.5 w-3.5" />
                </button>
              )}
            </div>
          );
        },
      },
      {
        key: "active",
        header: "Status",
        render: (row) => renderStatusBadge(row),
      },
      {
        key: "actions",
        header: "Action controls",
        render: (row) => renderActions(row),
      },
    ];
  }, [activeCategoryTab, currentUser, data]);

  return (
    <div className="grid gap-8">
      {/* Page Title & Breadcrumbs */}
      <div>
        <nav className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 mb-2">
          <span>Dashboard</span>
          <span>&gt;</span>
          <span className="text-slate-800 dark:text-slate-200 font-bold">Users</span>
        </nav>
        <PageHeader
          title="User Management"
          description="Manage registered users, configure settings, upload import lists, and reset password credentials."
        />
      </div>

      <Toast message={message} tone="success" onClose={() => setMessage("")} />
      <Toast message={error} tone="danger" onClose={() => setError("")} />

      {/* Top-Level User Category Navigation Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {CATEGORY_TABS.map((tab) => {
          const isSelected = activeCategoryTab === tab.key;
          const count = categoryCounts[tab.key] || 0;
          const IconComponent = tab.icon;

          return (
            <button
              key={tab.key}
              type="button"
              onClick={() => handleCategoryTabChange(tab.key)}
              className={`flex items-start justify-between p-4 rounded-2xl border text-left transition-all duration-200 cursor-pointer ${
                isSelected
                  ? "bg-white dark:bg-slate-900 border-primary shadow-md ring-2 ring-primary/20 scale-[1.01]"
                  : "bg-white/80 dark:bg-slate-900/60 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 hover:bg-white dark:hover:bg-slate-900 shadow-2xs"
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`p-2.5 rounded-xl transition-colors ${
                    isSelected
                      ? "bg-primary text-white shadow-xs"
                      : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                  }`}
                >
                  <IconComponent className="h-5 w-5" />
                </div>
                <div>
                  <h3
                    className={`text-sm font-bold ${
                      isSelected
                        ? "text-primary dark:text-primary"
                        : "text-slate-800 dark:text-slate-200"
                    }`}
                  >
                    {tab.label}
                  </h3>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">
                    {tab.subLabel}
                  </p>
                </div>
              </div>
              <span
                className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                  isSelected
                    ? "bg-primary/10 text-primary font-bold"
                    : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400"
                }`}
              >
                {count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Creation form wrapped in Card */}
      <Card>
        <div
          className={`flex justify-between items-center cursor-pointer select-none group ${
            isRegisterOpen ? "mb-4" : ""
          }`}
          onClick={() => setIsRegisterOpen((prev) => !prev)}
        >
          <div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
              <User className="h-5 w-5 text-primary" />
              {activeCategoryTab === "students" && "Register Student Account"}
              {activeCategoryTab === "supervisors" && "Register App Manager or Warden"}
              {activeCategoryTab === "staff" && "Register Coordinator"}
              {activeCategoryTab === "all" && "Register New Account"}
            </h2>
            <p className="text-xs font-medium text-slate-500 dark:text-slate-400 mt-1">
              {activeCategoryTab === "students" && "Create a new student resident account for hostel and academic services."}
              {activeCategoryTab === "supervisors" && "Create an operational supervisor account to manage campus locations and hostels."}
              {activeCategoryTab === "staff" && "Create an employee account for department complaints and maintenance operations."}
              {activeCategoryTab === "all" && "Create a new institutional user account manually for Campus Pulse."}
            </p>
          </div>

          <button
            type="button"
            className="p-2 rounded-lg text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors focus:outline-none"
            aria-label={isRegisterOpen ? "Collapse registration form" : "Open registration form"}
            title={isRegisterOpen ? "Click to collapse form" : "Click to open registration form"}
          >
            {isRegisterOpen ? (
              <ChevronUp className="h-5 w-5 text-primary" />
            ) : (
              <ChevronDown className="h-5 w-5" />
            )}
          </button>
        </div>

        {isRegisterOpen && (
          <>
            <hr className="border-slate-100 dark:border-slate-800 my-4" />

            <form
              className="grid gap-5 md:grid-cols-2 lg:grid-cols-4"
              onSubmit={handleSubmit(onSubmit)}
            >
              <Input
                label="Full Name"
                placeholder="John Doe"
                error={errors.name?.message}
                {...register("name", { required: "Name is required." })}
              />
              <Input
                label="Email Address"
                type="email"
                placeholder="johndoe@campus.edu"
                error={errors.email?.message}
                {...register("email", { required: "Email is required." })}
              />

              {/* Temporary Password with Eye Show/Hide Toggle */}
              <div className="relative">
                <Input
                  label="Temporary Password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  className="pr-10"
                  error={errors.password?.message}
                  {...register("password", {
                    required: "Temporary password is required.",
                    minLength: { value: 8, message: "Use at least 8 characters." },
                  })}
                />
                <button
                  type="button"
                  className="absolute right-3.5 top-[38px] text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 focus:outline-none transition-colors"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowPassword((prev) => !prev);
                  }}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? (
                    <EyeOff className="h-4.5 w-4.5" />
                  ) : (
                    <Eye className="h-4.5 w-4.5" />
                  )}
                </button>
              </div>

              {/* Confirm Temporary Password with Eye Show/Hide Toggle */}
              <div className="relative">
                <Input
                  label="Confirm Temporary Password"
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="••••••••"
                  className="pr-10"
                  error={errors.confirmPassword?.message}
                  {...register("confirmPassword", {
                    required: "Please confirm temporary password.",
                    validate: (val) =>
                      val === watch("password") || "Passwords do not match.",
                  })}
                />
                <button
                  type="button"
                  className="absolute right-3.5 top-[38px] text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 focus:outline-none transition-colors"
                  onClick={(e) => {
                    e.stopPropagation();
                    setShowConfirmPassword((prev) => !prev);
                  }}
                  aria-label={showConfirmPassword ? "Hide password" : "Show password"}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4.5 w-4.5" />
                  ) : (
                    <Eye className="h-4.5 w-4.5" />
                  )}
                </button>
              </div>

              <Select label="Role" {...register("role")}>
                {allowedRoles.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </Select>

              <div className="flex items-end md:col-span-2 lg:col-span-4">
                <Button
                  type="submit"
                  disabled={isSubmitting}
                  className="font-semibold px-6 w-full lg:w-auto"
                >
                  Create User Account
                </Button>
              </div>
            </form>
          </>
        )}
      </Card>

      {/* Excel / CSV Bulk User Import Card (Available to Administrator & App Manager) */}
      {(currentUser?.role === ROLES.ADMINISTRATOR || currentUser?.role === ROLES.APP_MANAGER) && (
        <Card>
          <div className="mb-4 flex flex-wrap justify-between items-start gap-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <FileSpreadsheet className="h-5 w-5 text-primary" />
                Bulk Import Users (Excel / CSV)
              </h2>
              <p className="text-xs font-medium text-slate-500 dark:text-slate-400 mt-1">
                Upload an Excel (.xlsx / .xls) or CSV spreadsheet to create multiple accounts at once.
                <span className="text-primary font-bold ml-1">
                  Temporary passwords will be created automatically for each imported user.
                </span>
              </p>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              <Button
                variant="primary"
                size="sm"
                onClick={() => setShowStaffImportModal(true)}
                className="h-10 text-xs font-bold flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 text-white"
              >
                <Upload className="h-4 w-4" />
                Bulk Import Staff
              </Button>
              <Button
                variant="subtle"
                size="sm"
                onClick={handleDownloadTemplate}
                className="h-10 text-xs font-bold flex items-center gap-1.5"
              >
                <Download className="h-4 w-4" />
                Download Student Template
              </Button>
            </div>
          </div>

          <hr className="border-slate-100 dark:border-slate-800 my-4" />

          <form
            onSubmit={handleCsvImport}
            className="grid gap-4"
          >
            {/* Student Enrollment & Movement Parameters */}
            <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <label className="text-xs font-bold text-slate-700 dark:text-slate-300">
                    Academic Program
                  </label>
                  <button
                    type="button"
                    onClick={() => setShowProgramModal(true)}
                    className="text-[11px] font-semibold text-primary hover:underline flex items-center gap-0.5"
                  >
                    <Plus className="h-3 w-3" /> Manage Programs
                  </button>
                </div>
                <select
                  value={importProgram}
                  onChange={(e) => {
                    setImportProgram(e.target.value);
                    setImportYear("1");
                  }}
                  className="h-10 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary"
                >
                  <option value="">Default (From CSV or Auto)</option>
                  {(data?.programs || []).map((p) => (
                    <option key={p.program_id} value={p.name}>
                      {p.name} ({p.duration_years} Years)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1.5">
                  Academic Year
                </label>
                <input
                  type="text"
                  value={importAcademicYear}
                  onChange={(e) => setImportAcademicYear(e.target.value)}
                  placeholder="e.g. 2024-2025"
                  className="h-10 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary"
                />
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1.5">
                  Current Year
                </label>
                <select
                  value={importYear}
                  onChange={(e) => setImportYear(e.target.value)}
                  className="h-10 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary"
                >
                  {yearOptions.map((yr) => (
                    <option key={yr} value={yr}>
                      Year {yr}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1.5">
                  Assigned Location / Hostel
                </label>
                <select
                  value={importLocationId}
                  onChange={(e) => setImportLocationId(e.target.value)}
                  className="h-10 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary"
                >
                  <option value="">Default (From CSV)</option>
                  {(data?.locations || []).map((loc) => (
                    <option key={loc.location_id} value={loc.location_id}>
                      {loc.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="sm:col-span-2 lg:col-span-4 pt-1">
                <label className="inline-flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={updateExisting}
                    onChange={(e) => setUpdateExisting(e.target.checked)}
                    className="rounded border-slate-300 text-primary focus:ring-primary h-4 w-4"
                  />
                  <span className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                    Enable Student Movement (Update existing students' program, year, and location instead of rejecting as duplicate)
                  </span>
                </label>
              </div>
            </div>

            <div className="flex flex-wrap items-end gap-4">
              <div className="flex-1 min-w-[240px]">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 block mb-2">
                  Select Excel or CSV File (.xlsx, .xls, .csv)
                </label>
                <input
                  type="file"
                  accept=".csv, .xlsx, .xls"
                  onChange={(e) => setCsvFile(e.target.files[0])}
                  className="h-12 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-4 py-2.5 text-sm font-medium text-slate-800 dark:text-slate-100 outline-none"
                />
              </div>
              <Button
                type="submit"
                disabled={importing || !csvFile}
                className="font-semibold px-6 h-12 flex items-center gap-2"
              >
                <Upload className="h-4 w-4" />
                {importing ? "Importing Accounts..." : "Upload & Import Users"}
              </Button>
            </div>
          </form>

          {/* Import Report with Passwords & Credentials Export */}
          {importReport && (
            <div className="mt-6 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-850 p-5 text-xs">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-4 border-b border-slate-200 dark:border-slate-800 pb-3">
                <div>
                  <h3 className="font-bold text-slate-900 dark:text-slate-100 text-sm flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-emerald-500" />
                    Bulk Import Execution Report
                  </h3>
                  <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                    Processed {importReport.total_rows || importReport.report?.length || 0} rows from file
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="rounded-lg bg-emerald-50 dark:bg-emerald-950/40 px-3 py-1 text-emerald-600 dark:text-emerald-400 font-bold border border-emerald-200 dark:border-emerald-900">
                    ✓ {importReport.success_count || importReport.imported_count || 0} Successful
                  </span>
                  <span className="rounded-lg bg-rose-50 dark:bg-rose-950/40 px-3 py-1 text-rose-600 dark:text-rose-400 font-bold border border-rose-200 dark:border-rose-900">
                    ✗ {importReport.failed_count || 0} Failed
                  </span>
                  {(importReport.success_count > 0 || importReport.imported_count > 0) && (
                    <Button
                      variant="subtle"
                      size="sm"
                      onClick={() => handleExportImportCredentials(importReport)}
                      className="!h-8 text-xs font-bold text-primary"
                    >
                      <Download className="h-3.5 w-3.5 mr-1" />
                      Export Credentials (CSV)
                    </Button>
                  )}
                </div>
              </div>

              {/* Imported Accounts Table */}
              {importReport.report && importReport.report.filter((r) => r.status === "Success").length > 0 && (
                <div className="mb-4">
                  <h4 className="font-bold text-slate-800 dark:text-slate-200 mb-2 uppercase tracking-wider text-[10px]">
                    Processed Accounts & Generated Credentials:
                  </h4>
                  <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
                    <table className="w-full text-left border-collapse">
                      <thead>
                        <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-100/50 dark:bg-slate-800/50 font-bold text-slate-600 dark:text-slate-300">
                          <th className="p-2.5">Row</th>
                          <th className="p-2.5">Name</th>
                          <th className="p-2.5">Email</th>
                          <th className="p-2.5">Role</th>
                          <th className="p-2.5">Action</th>
                          <th className="p-2.5">Temporary Password / Activation</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-medium text-slate-700 dark:text-slate-300">
                        {importReport.report
                          .filter((r) => r.status === "Success")
                          .map((item, idx) => (
                            <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-slate-800/40">
                              <td className="p-2.5 text-slate-400">#{item.row_index}</td>
                              <td className="p-2.5 font-semibold text-slate-900 dark:text-slate-100">{item.name}</td>
                              <td className="p-2.5">{item.email}</td>
                              <td className="p-2.5 capitalize">{item.role?.replace("_", " ")}</td>
                              <td className="p-2.5">
                                <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                                  item.action === "updated"
                                    ? "bg-amber-100 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-900"
                                    : "bg-emerald-100 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900"
                                }`}>
                                  {item.action === "updated" ? "Updated / Moved" : "Created"}
                                </span>
                              </td>
                              <td className="p-2.5">
                                <div className="flex flex-wrap items-center gap-2">
                                  {item.temporary_password && (
                                    <span className="font-mono bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded text-primary font-bold border border-slate-200 dark:border-slate-700">
                                      {item.temporary_password}
                                    </span>
                                  )}
                                  {item.activation_link && (
                                    <button
                                      type="button"
                                      onClick={() => {
                                        navigator.clipboard.writeText(item.activation_link);
                                        setCopiedLinkIndex(idx);
                                        setTimeout(() => setCopiedLinkIndex(null), 2000);
                                      }}
                                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-indigo-600 dark:text-indigo-400 hover:underline px-2 py-0.5 rounded bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-900"
                                      title={item.activation_link}
                                    >
                                      {copiedLinkIndex === idx ? (
                                        <>
                                          <CheckCheck className="h-3 w-3 text-emerald-500" />
                                          <span>Copied!</span>
                                        </>
                                      ) : (
                                        <>
                                          <Copy className="h-3 w-3" />
                                          <span>Copy Activation Link</span>
                                        </>
                                      )}
                                    </button>
                                  )}
                                </div>
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

            {/* Failed Rows Log */}
            {importReport.report && importReport.report.filter((r) => r.status === "Failed").length > 0 && (
              <div className="mt-3 max-h-40 overflow-y-auto rounded-lg border border-red-200 dark:border-red-900 bg-red-50/50 dark:bg-red-950/20 p-3">
                <span className="font-bold text-red-600 dark:text-red-400 block mb-1">
                  Failed Rows Log:
                </span>
                {importReport.report
                  .filter((r) => r.status === "Failed")
                  .map((fail, index) => (
                    <div key={index} className="text-red-700 dark:text-red-300 text-[11px] mb-1">
                      <strong>Row #{fail.row_index} ({fail.name || fail.identifier}):</strong> {fail.reason}
                    </div>
                  ))}
              </div>
            )}
          </div>
        )}
      </Card>
      )}

      {/* Grid List Table with Single Merged Filter Toolbar */}
      <Card>
        {/* Category-Tailored Filter Toolbar */}
        <div className="flex flex-wrap items-center gap-2.5 my-2">
          {/* Search Box */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={
                activeCategoryTab === "students"
                  ? "Search students by name, email, roll number, hostel..."
                  : activeCategoryTab === "supervisors"
                  ? "Search managers and wardens by name, email, location..."
                  : activeCategoryTab === "staff"
                  ? "Search employees and coordinators by name, department..."
                  : "Search all users by name, email, role, location..."
              }
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

          {/* 1. STUDENTS FILTERS */}
          {activeCategoryTab === "students" && (
            <>
              <select
                value={programFilter}
                onChange={(e) => setProgramFilter(e.target.value)}
                className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
              >
                <option value="">All Programs</option>
                {(data?.programs || []).map((p) => (
                  <option key={p.program_id} value={p.name}>
                    {p.name}
                  </option>
                ))}
              </select>

              <select
                value={yearFilter}
                onChange={(e) => setYearFilter(e.target.value)}
                className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
              >
                <option value="">All Years</option>
                <option value="1">Year 1</option>
                <option value="2">Year 2</option>
                <option value="3">Year 3</option>
                <option value="4">Year 4</option>
                <option value="5">Year 5</option>
              </select>

              <select
                value={locationFilter}
                onChange={(e) => setLocationFilter(e.target.value)}
                className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
              >
                <option value="">All Hostels / Locations</option>
                {(data?.locations || []).map((loc) => (
                  <option key={loc.location_id} value={loc.location_id}>
                    {loc.name}
                  </option>
                ))}
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
              >
                <option value="">All Lifecycle Statuses</option>
                <option value="active">Active Only</option>
                <option value="graduated">Graduated</option>
                <option value="left_college">Left College</option>
                <option value="transferred">Transferred</option>
                <option value="disabled">Disabled / Inactive</option>
              </select>

              <Button
                variant="subtle"
                size="sm"
                onClick={() => setShowProgramModal(true)}
                className="h-10 text-xs font-bold text-primary flex items-center gap-1 shrink-0"
                title="Manage academic degree programs"
              >
                <GraduationCap className="h-3.5 w-3.5" /> Programs
              </Button>
            </>
          )}

          {/* 2. SUPERVISORS FILTERS */}
          {activeCategoryTab === "supervisors" && (
            <>
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
              >
                <option value="">All Supervisors</option>
                <option value={ROLES.APP_MANAGER}>App Managers</option>
                <option value={ROLES.LOCATION_IN_CHARGE}>Wardens</option>
              </select>

              <select
                value={locationFilter}
                onChange={(e) => setLocationFilter(e.target.value)}
                className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
              >
                <option value="">All Supervised Locations</option>
                {(data?.locations || []).map((loc) => (
                  <option key={loc.location_id} value={loc.location_id}>
                    {loc.name}
                  </option>
                ))}
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
              >
                <option value="">All Statuses</option>
                <option value="active">Active Only</option>
                <option value="disabled">Disabled / Inactive</option>
              </select>
            </>
          )}

          {/* 3. STAFF FILTERS */}
          {activeCategoryTab === "staff" && (
            <>
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
              >
                <option value="">All Staff & Responsibilities</option>
                <option value="coordinator">Department Coordinators (Coord 1 / Coord 2)</option>
                <option value="employee_only">Operational Field Staff</option>
              </select>

              <select
                value={deptFilter}
                onChange={(e) => setDeptFilter(e.target.value)}
                className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
              >
                <option value="">All Departments</option>
                {(data?.departments || []).map((d) => (
                  <option key={d.department_id} value={d.department_id}>
                    {d.name}
                  </option>
                ))}
              </select>

              <select
                value={locationFilter}
                onChange={(e) => setLocationFilter(e.target.value)}
                className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
              >
                <option value="">All Work Locations</option>
                {(data?.locations || []).map((loc) => (
                  <option key={loc.location_id} value={loc.location_id}>
                    {loc.name}
                  </option>
                ))}
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
              >
                <option value="">All Statuses</option>
                <option value="active">Active Only</option>
                <option value="disabled">Disabled / Inactive</option>
              </select>

              <Button
                variant="subtle"
                size="sm"
                onClick={() => navigate("/admin/employee-assignments")}
                className="h-10 text-xs font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1 shrink-0"
                title="Open Department Coordinators Matrix"
              >
                <Wrench className="h-3.5 w-3.5" /> Department Assignments
              </Button>

              <Button
                variant="subtle"
                size="sm"
                onClick={() => setShowStaffImportModal(true)}
                className="h-10 text-xs font-bold text-indigo-600 dark:text-indigo-400 flex items-center gap-1 shrink-0"
                title="Bulk Import Staff"
              >
                <Upload className="h-3.5 w-3.5" /> Import Staff
              </Button>
            </>
          )}

          {/* 4. ALL ACCOUNTS FILTERS */}
          {activeCategoryTab === "all" && (
            <>
              <select
                value={activeRoleTab}
                onChange={(e) => setActiveRoleTab(e.target.value)}
                className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
              >
                {roleTabs.map((tab) => {
                  const count = getRoleCount(tab.id);
                  return (
                    <option key={tab.id} value={tab.id}>
                      {tab.label} ({count})
                    </option>
                  );
                })}
              </select>

              <select
                value={deptFilter}
                onChange={(e) => setDeptFilter(e.target.value)}
                className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
              >
                <option value="">All Departments</option>
                {(data?.departments || []).map((d) => (
                  <option key={d.department_id} value={d.department_id}>
                    {d.name}
                  </option>
                ))}
              </select>

              <select
                value={locationFilter}
                onChange={(e) => setLocationFilter(e.target.value)}
                className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
              >
                <option value="">All Locations</option>
                {(data?.locations || []).map((loc) => (
                  <option key={loc.location_id} value={loc.location_id}>
                    {loc.name}
                  </option>
                ))}
              </select>

              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
              >
                <option value="">All Statuses</option>
                <option value="active">Active Only</option>
                <option value="disabled">Disabled / Inactive</option>
              </select>
            </>
          )}

          {/* Clear Filters Button */}
          {(query || statusFilter || roleFilter || (activeCategoryTab === "all" && activeRoleTab !== "all") || programFilter || locationFilter || deptFilter || yearFilter) && (
            <Button
              variant="subtle"
              size="sm"
              onClick={handleClearFilters}
              className="h-10 text-xs font-bold text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 flex items-center gap-1 shrink-0"
              title="Reset all filters"
            >
              <RotateCcw className="h-3.5 w-3.5" /> Clear Filters
            </Button>
          )}

          {/* Export Filtered Users */}
          <div className="flex items-center gap-1 shrink-0">
            <Button
              variant="subtle"
              size="sm"
              onClick={() => handleExportUsers("csv")}
              className="h-10 text-xs font-bold text-primary flex items-center gap-1"
              title="Export filtered list to CSV"
            >
              <Download className="h-3.5 w-3.5" /> CSV
            </Button>
            <Button
              variant="subtle"
              size="sm"
              onClick={() => handleExportUsers("xlsx")}
              className="h-10 text-xs font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1"
              title="Export filtered list to Excel (XLSX)"
            >
              <FileSpreadsheet className="h-3.5 w-3.5" /> Excel
            </Button>
          </div>

          {/* User Recycle Bin Button */}
          {(currentUser?.role === ROLES.ADMINISTRATOR || currentUser?.role === ROLES.APP_MANAGER) && (
            <Button
              variant="subtle"
              size="sm"
              onClick={() => {
                loadRecycleBin();
                setShowRecycleBin(true);
              }}
              className="h-10 text-xs font-bold text-rose-600 dark:text-rose-400 flex items-center gap-1.5 shrink-0"
              title="View & restore soft-deleted user accounts"
            >
              <Archive className="h-4 w-4" /> Recycle Bin
            </Button>
          )}
        </div>

        {fetchError && (
          <div className="mb-4 rounded-xl border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/30 p-4 text-xs font-semibold text-red-700 dark:text-red-300">
            {fetchError}
          </div>
        )}

        {loading && <Loader label="Loading registered users" />}

        {!loading && users.length === 0 && (
          <EmptyState
            title="No Matching Users Found"
            description="Try changing your search query, role tab, location, department, or status filter."
          />
        )}

        {!loading && users.length > 0 && (
          <div>
            <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 mb-3">
              Showing <span className="font-bold text-slate-800 dark:text-slate-200">{users.length}</span> of{" "}
              <span className="font-bold text-slate-800 dark:text-slate-200">{(data?.users || []).length}</span> registered users
            </p>
            <Table
              columns={columns}
              rows={users}
              getRowKey={(row) => row.user_id}
              pageSize={10}
            />
          </div>
        )}
      </Card>

      {/* Program Management Modal */}
      {showProgramModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <GraduationCap className="h-5 w-5 text-primary" />
                Manage Academic Programs
              </h3>
              <button
                type="button"
                onClick={() => setShowProgramModal(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* List existing programs */}
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Existing Programs</p>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {(data?.programs || []).map((p) => (
                  <div
                    key={p.program_id}
                    className="flex items-center justify-between p-2.5 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/40 text-xs"
                  >
                    <div>
                      <span className="font-bold text-slate-800 dark:text-slate-200">{p.name}</span>
                      <span className="ml-2 text-slate-500 font-medium">({p.duration_years} Years)</span>
                      {p.description && <p className="text-[11px] text-slate-400 mt-0.5">{p.description}</p>}
                    </div>
                    <button
                      type="button"
                      onClick={() => handleDeleteProgram(p.program_id, p.name)}
                      className="text-slate-400 hover:text-rose-500 p-1 rounded"
                      title="Delete Program"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Add new program form */}
            <form onSubmit={handleCreateProgram} className="pt-3 border-t border-slate-100 dark:border-slate-800 space-y-3">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Create New Program</p>
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <Input
                    label="Program Name"
                    placeholder="e.g. M.Tech, Degree, B.Tech"
                    value={newProgramName}
                    onChange={(e) => setNewProgramName(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block mb-1.5">
                    Duration (Yrs)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="6"
                    value={newProgramDuration}
                    onChange={(e) => setNewProgramDuration(e.target.value)}
                    className="h-10 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary"
                    required
                  />
                </div>
              </div>
              <Input
                label="Description (Optional)"
                placeholder="e.g. 4-year undergraduate engineering degree"
                value={newProgramDesc}
                onChange={(e) => setNewProgramDesc(e.target.value)}
              />
              <div className="flex justify-end gap-2 pt-2">
                <Button variant="subtle" size="sm" type="button" onClick={() => setShowProgramModal(false)}>
                  Close
                </Button>
                <Button variant="primary" size="sm" type="submit" disabled={savingProgram || !newProgramName.trim()}>
                  {savingProgram ? "Saving..." : "Add Program"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Dynamic Location Editing Modal */}
      {editLocationUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <MapPin className="h-5 w-5 text-primary" />
                Edit Operational Location
              </h3>
              <button
                type="button"
                onClick={() => setEditLocationUser(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 text-xs space-y-1">
              <p className="font-bold text-slate-800 dark:text-slate-200">{editLocationUser.name}</p>
              <p className="text-slate-500">{editLocationUser.email} &bull; {editLocationUser.user_id}</p>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block">
                Assign Current Operational Location / Hostel / Block
              </label>
              <select
                value={selectedLocationId}
                onChange={(e) => setSelectedLocationId(e.target.value)}
                className="h-10 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary"
              >
                <option value="">-- Select Location --</option>
                {(data?.locations || []).map((loc) => (
                  <option key={loc.location_id} value={loc.location_id}>
                    {loc.name}
                  </option>
                ))}
              </select>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Updating location immediately changes complaint routing, warden visibility, and operational context for this account without re-importing.
              </p>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button variant="subtle" size="sm" type="button" onClick={() => setEditLocationUser(null)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleSaveLocation} disabled={savingLocation}>
                {savingLocation ? "Saving Location..." : "Update Location"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Multi-Location Assignment Modal (for App Managers & Wardens) */}
      {manageLocationsUser && (() => {
        const isModalUserAppMgr = (manageLocationsUser?.role || "").toLowerCase() === "app_manager";
        const peerRoleLabel = isModalUserAppMgr ? "App Manager" : "Warden";
        const peerRolePlural = isModalUserAppMgr ? "App Managers" : "Wardens";
        const otherRoleLabel = isModalUserAppMgr ? "Warden" : "App Manager";

        return (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="w-full max-w-2xl rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-2xl space-y-4 max-h-[90vh] flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 shrink-0">
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                    <MapPin className="h-5 w-5 text-primary" />
                    Manage Assigned Locations
                  </h3>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Strictly compared between <span className="font-semibold text-slate-700 dark:text-slate-300">{peerRolePlural}</span>. ({otherRoleLabel} assignments are independent).
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setManageLocationsUser(null)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* User Identity & Comparison Scope Card */}
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 text-xs space-y-1.5 shrink-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <p className="font-bold text-slate-800 dark:text-slate-200">{manageLocationsUser.name}</p>
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase bg-primary/10 text-primary">
                      {manageLocationsUser.role?.replace(/_/g, " ")}
                    </span>
                  </div>
                  <span className="text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                    {selectedLocationsList.length} of {(data?.locations || []).length} locations selected
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-500 text-[11px]">
                  <span>{manageLocationsUser.email} &bull; {manageLocationsUser.user_id}</span>
                  <span>Comparison: <strong className="text-primary">{peerRoleLabel} vs {peerRoleLabel}</strong></span>
                </div>
              </div>

              {/* Reallocation Warning Banner when peer-allotted locations are selected */}
              {reallocatedFromOthers.length > 0 && (
                <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-900 dark:text-amber-200 flex items-start gap-2.5 shrink-0 animate-in fade-in">
                  <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
                  <div className="space-y-1 w-full">
                    <p className="font-bold text-amber-900 dark:text-amber-100">
                      Reallocation Alert: {reallocatedFromOthers.length} {reallocatedFromOthers.length === 1 ? "location" : "locations"} already allotted to another {peerRoleLabel}
                    </p>
                    <p className="text-[11px] opacity-90 leading-relaxed">
                      Saving will reassign ownership to <strong>{manageLocationsUser.name}</strong> and remove {reallocatedFromOthers.length === 1 ? "it" : "them"} from the previous {peerRoleLabel}&apos;s profile cleanly:
                    </p>
                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {reallocatedFromOthers.map((item) => (
                        <span
                          key={item.locationId}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-100 dark:bg-amber-900/60 text-amber-950 dark:text-amber-200 border border-amber-300 dark:border-amber-700"
                        >
                          <ArrowRightLeft className="h-3 w-3" />
                          <span>{item.locationName}</span>
                          <span className="opacity-70">&larr; {item.info?.assignedUser?.name || "Other " + peerRoleLabel}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Search and Filters */}
              <div className="space-y-2 shrink-0">
                <div className="relative">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    value={modalLocationQuery}
                    onChange={(e) => setModalLocationQuery(e.target.value)}
                    placeholder={`Search locations by name, ID, or current ${peerRoleLabel}...`}
                    className="h-9 w-full pl-9 pr-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:border-primary"
                  />
                  {modalLocationQuery && (
                    <button
                      type="button"
                      onClick={() => setModalLocationQuery("")}
                      className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                  {/* Status Pills */}
                  <div className="flex flex-wrap gap-1">
                    <button
                      type="button"
                      onClick={() => setModalFilterStatus("all")}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                        modalFilterStatus === "all"
                          ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                          : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700"
                      }`}
                    >
                      All ({(data?.locations || []).length})
                    </button>
                    <button
                      type="button"
                      onClick={() => setModalFilterStatus("self")}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                        modalFilterStatus === "self"
                          ? "bg-emerald-600 text-white"
                          : "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 border border-emerald-200/50"
                      }`}
                    >
                      Allotted to User ({countSelf})
                    </button>
                    <button
                      type="button"
                      onClick={() => setModalFilterStatus("other")}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                        modalFilterStatus === "other"
                          ? "bg-amber-600 text-white"
                          : "bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 hover:bg-amber-100 border border-amber-200/50"
                      }`}
                    >
                      Allotted to other {peerRolePlural} ({countOther})
                    </button>
                    <button
                      type="button"
                      onClick={() => setModalFilterStatus("unassigned")}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                        modalFilterStatus === "unassigned"
                          ? "bg-primary text-white"
                          : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700"
                      }`}
                    >
                      Unallotted ({countUnassigned})
                    </button>
                  </div>

                  {/* Batch Selection Actions */}
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={handleSelectAllLocations}
                      className="text-xs text-primary hover:underline font-semibold"
                    >
                      Select All
                    </button>
                    <span className="text-slate-300">&bull;</span>
                    <button
                      type="button"
                      onClick={handleSelectUnallottedOnly}
                      className="text-xs text-emerald-600 dark:text-emerald-400 hover:underline font-semibold"
                      title="Select unallotted locations and currently held locations, avoiding reallocations from others"
                    >
                      Unallotted &amp; Mine
                    </button>
                    <span className="text-slate-300">&bull;</span>
                    <button
                      type="button"
                      onClick={handleClearAllLocations}
                      className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 font-semibold"
                    >
                      Clear
                    </button>
                  </div>
                </div>
              </div>

              {/* Location Cards List */}
              <div className="overflow-y-auto pr-1 space-y-2 flex-1 min-h-[220px]">
                {displayedModalLocations.length === 0 ? (
                  <div className="py-8 text-center text-xs text-slate-400">
                    No locations found matching your filter or search query.
                  </div>
                ) : (
                  displayedModalLocations.map((loc) => {
                    const isSelected = selectedLocationsList.includes(loc.location_id);
                    const info = locationAllotmentInfo[loc.location_id] || { status: "unassigned" };
                    const isOther = info.status === "other";
                    const isSelf = info.status === "self";
                    const isReallocating = isSelected && isOther;

                    let cardBorder = "border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900";
                    if (isReallocating) {
                      cardBorder = "border-amber-400/80 bg-amber-50/50 dark:bg-amber-950/20";
                    } else if (isSelected) {
                      cardBorder = "border-primary/50 bg-primary/5 dark:bg-primary/10";
                    }

                    return (
                      <label
                        key={loc.location_id}
                        className={`flex items-center justify-between p-3 rounded-xl border text-xs cursor-pointer transition-all ${cardBorder} hover:shadow-xs`}
                      >
                        <div className="flex items-center gap-3">
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => handleToggleLocationItem(loc.location_id)}
                            className="h-4 w-4 rounded border-slate-300 text-primary focus:ring-primary cursor-pointer shrink-0"
                          />
                          <div>
                            <div className="flex items-center gap-2">
                              <p className="font-bold text-slate-800 dark:text-slate-200">{loc.name}</p>
                              {loc.location_type && (
                                <span className="px-1.5 py-0.2 rounded text-[10px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-500">
                                  {loc.location_type}
                                </span>
                              )}
                            </div>
                            <p className="text-[11px] text-slate-400 font-mono">ID: {loc.location_id}</p>
                          </div>
                        </div>

                        {/* Allotment Status Badges */}
                        <div className="flex flex-col items-end gap-1">
                          {isSelf && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200/60 dark:border-emerald-800/60">
                              <Check className="h-3 w-3" />
                              Currently Allotted
                            </span>
                          )}

                          {isOther && (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200/60 dark:border-amber-800/60">
                              <AlertTriangle className="h-3 w-3 text-amber-600 dark:text-amber-400" />
                              Allotted to: {info.assignedUser?.name || "Another " + peerRoleLabel}
                            </span>
                          )}

                          {isReallocating && (
                            <span className="inline-flex items-center gap-1 text-[10px] font-bold text-amber-600 dark:text-amber-400">
                              <ArrowRightLeft className="h-3 w-3" />
                              Will reassign from {info.assignedUser?.name || "other"}
                            </span>
                          )}

                          {info.status === "unassigned" && (
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-500">
                              {isSelected ? "Newly Allotting" : "Available (Unallotted)"}
                            </span>
                          )}
                        </div>
                      </label>
                    );
                  })
                )}
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-800 shrink-0">
                <div className="text-[11px] text-slate-500">
                  {reallocatedFromOthers.length > 0 ? (
                    <span className="text-amber-600 dark:text-amber-400 font-semibold flex items-center gap-1">
                      <AlertTriangle className="h-3.5 w-3.5" />
                      {reallocatedFromOthers.length} {reallocatedFromOthers.length === 1 ? "reallocation" : "reallocations"} pending
                    </span>
                  ) : (
                    <span>{selectedLocationsList.length} locations selected</span>
                  )}
                </div>
                <div className="flex justify-end gap-2">
                  <Button variant="subtle" size="sm" type="button" onClick={() => setManageLocationsUser(null)}>
                    Cancel
                  </Button>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={handleSaveAssignedLocations}
                    disabled={savingAssignedLocations}
                  >
                    {savingAssignedLocations
                      ? "Saving Assignments..."
                      : reallocatedFromOthers.length > 0
                      ? `Save & Reallocate (${selectedLocationsList.length} Selected, ${reallocatedFromOthers.length} Transfer${reallocatedFromOthers.length > 1 ? "s" : ""})`
                      : `Save Locations (${selectedLocationsList.length} Selected)`}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        );
      })()}

      {/* Coordinator Department Eligibility Modal */}
      {manageEmployeeUser && (() => {
        const coordDept = (data?.departments || []).find(
          (d) => d.coordinator_id === manageEmployeeUser.user_id || d.coordinator_2_id === manageEmployeeUser.user_id
        );
        const countEligible = selectedDeptIdsList.length;
        const countAvailable = (data?.departments || []).length - countEligible;

        return (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="w-full max-w-2xl rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-2xl space-y-4 max-h-[90vh] flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 shrink-0">
                <div>
                  <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                    <Building className="h-5 w-5 text-emerald-500" />
                    Edit Eligible Departments
                  </h3>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Select all technical departments this employee is eligible to coordinate or service across campus.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setManageEmployeeUser(null)}
                  className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Modal Error Alert */}
              {modalError && (
                <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs flex items-center justify-between shrink-0 shadow-xs">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-rose-500 shrink-0" />
                    <span className="font-medium">{modalError}</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setModalError("")}
                    className="text-rose-400 hover:text-rose-600 dark:hover:text-rose-200 p-0.5 rounded"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              )}

              {/* Coordinator Summary Card */}
              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 text-xs space-y-1.5 shrink-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <p className="font-bold text-slate-800 dark:text-slate-200">{manageEmployeeUser.name}</p>
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300">
                      {manageEmployeeUser.role}
                    </span>
                  </div>
                  <span className="text-[11px] font-semibold text-slate-600 dark:text-slate-400">
                    {selectedDeptIdsList.length} of {(data?.departments || []).length} departments selected
                  </span>
                </div>
                <div className="flex items-center justify-between text-slate-500 text-[11px]">
                  <span>{manageEmployeeUser.email} &bull; {manageEmployeeUser.user_id}</span>
                  {manageEmployeeUser.coordinator_position && (
                    <span className="inline-flex items-center gap-1 font-semibold text-blue-600 dark:text-blue-400">
                      <Users className="h-3 w-3" />
                      {manageEmployeeUser.coordinator_position}
                    </span>
                  )}
                </div>
                {coordDept && (
                  <p className="text-[11px] text-blue-600 dark:text-blue-400 bg-blue-50/50 dark:bg-blue-950/30 p-1.5 rounded-lg border border-blue-200/50 dark:border-blue-800/50">
                    Note: <strong>{manageEmployeeUser.name}</strong> holds active coordinator responsibilities in <strong>{coordDept.name}</strong>. Eligibility for this department is locked to preserve coordinator routing.
                  </p>
                )}
              </div>

              {/* Department Cards List */}
              <div className="space-y-3 flex-1 flex flex-col min-h-0">
                {/* Search and Filters */}
                <div className="space-y-2 shrink-0">
                  <div className="relative">
                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                    <input
                      type="text"
                      value={deptSearchQuery}
                      onChange={(e) => setDeptSearchQuery(e.target.value)}
                      placeholder="Search departments by name, area, or ID..."
                      className="h-9 w-full pl-9 pr-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-xs text-slate-800 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:border-emerald-500"
                    />
                    {deptSearchQuery && (
                      <button
                        type="button"
                        onClick={() => setDeptSearchQuery("")}
                        className="absolute right-2.5 top-2.5 text-slate-400 hover:text-slate-600"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-2 text-xs">
                    {/* Status Pills */}
                    <div className="flex flex-wrap gap-1">
                      <button
                        type="button"
                        onClick={() => setDeptFilterTab("all")}
                        className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                          deptFilterTab === "all"
                            ? "bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900"
                            : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700"
                        }`}
                      >
                        All ({(data?.departments || []).length})
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeptFilterTab("eligible")}
                        className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                          deptFilterTab === "eligible"
                            ? "bg-emerald-600 text-white"
                            : "bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 border border-emerald-200/50"
                        }`}
                      >
                        Eligible ({countEligible})
                      </button>
                      <button
                        type="button"
                        onClick={() => setDeptFilterTab("available")}
                        className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all ${
                          deptFilterTab === "available"
                            ? "bg-slate-700 text-white"
                            : "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-700"
                        }`}
                      >
                        Available to Add ({countAvailable})
                      </button>
                    </div>

                    {/* Batch Actions */}
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={handleSelectAllDepts}
                        className="text-xs text-emerald-600 dark:text-emerald-400 hover:underline font-semibold"
                      >
                        Select All
                      </button>
                      <span className="text-slate-300">&bull;</span>
                      <button
                        type="button"
                        onClick={handleClearAllDepts}
                        className="text-xs text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 font-semibold"
                      >
                        Clear All
                      </button>
                    </div>
                  </div>
                </div>

                {/* Department Cards List */}
                <div className="overflow-y-auto pr-1 space-y-2 flex-1 min-h-[220px]">
                  {displayedDepartments.length === 0 ? (
                    <div className="py-8 text-center text-xs text-slate-400">
                      No departments found matching your filter or search query.
                    </div>
                  ) : (
                    displayedDepartments.map((dept) => {
                      const isSelected = selectedDeptIdsList.includes(dept.department_id);
                      const isCoordinatorDept = coordDept && coordDept.department_id === dept.department_id;

                      let cardBorder = "border-slate-100 dark:border-slate-800 bg-white dark:bg-slate-900";
                      if (isCoordinatorDept) {
                        cardBorder = "border-blue-300/80 bg-blue-50/40 dark:bg-blue-950/20";
                      } else if (isSelected) {
                        cardBorder = "border-emerald-500/50 bg-emerald-50/5 dark:bg-emerald-950/20";
                      }

                      return (
                        <label
                          key={dept.department_id}
                          className={`flex items-center justify-between p-3 rounded-xl border text-xs transition-all ${cardBorder} ${
                            isCoordinatorDept ? "cursor-default" : "cursor-pointer hover:shadow-xs"
                          }`}
                        >
                          <div className="flex items-center gap-3">
                            <input
                              type="checkbox"
                              checked={isSelected}
                              disabled={isCoordinatorDept}
                              onChange={() => handleToggleDeptItem(dept.department_id)}
                              className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed shrink-0"
                            />
                            <div>
                              <div className="flex items-center gap-2">
                                <p className="font-bold text-slate-800 dark:text-slate-200">{dept.name}</p>
                              </div>
                              <p className="text-[11px] text-slate-400 font-mono">ID: {dept.department_id}</p>
                            </div>
                          </div>

                          {/* Badges */}
                          <div className="flex items-center gap-1.5">
                            {isCoordinatorDept && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 border border-blue-200/60 dark:border-blue-800/60">
                                <Users className="h-3 w-3" />
                                Active Coordinator
                              </span>
                            )}
                            {isSelected ? (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200/60 dark:border-emerald-800/60">
                                <Check className="h-3 w-3" />
                                Eligible (Campus-wide)
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 dark:bg-slate-800 text-slate-500">
                                Available to Add
                              </span>
                            )}
                          </div>
                        </label>
                      );
                    })
                  )}
                </div>
              </div>

              {/* Footer */}
              <div className="flex items-center justify-between pt-3 border-t border-slate-100 dark:border-slate-800 shrink-0">
                <div className="text-[11px] text-slate-500">
                  <span className="font-semibold text-slate-700 dark:text-slate-300">
                    {selectedDeptIdsList.length} of {(data?.departments || []).length} departments selected &bull; Campus-wide coverage
                  </span>
                </div>
                <div className="flex items-center justify-end gap-2 shrink-0">
                  <Button variant="subtle" size="md" type="button" onClick={() => setManageEmployeeUser(null)}>
                    Cancel
                  </Button>
                  <Button
                    variant="primary"
                    size="md"
                    onClick={handleSaveEmployeeDepartments}
                    disabled={savingEmployeeDepts}
                    className="min-w-[190px] px-4 font-semibold text-xs whitespace-nowrap shadow-sm hover:shadow"
                  >
                    {savingEmployeeDepts
                      ? "Saving Departments..."
                      : `Save Eligible Departments (${selectedDeptIdsList.length})`}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        );
      })()}

      {/* User Recycle Bin Modal */}
      {showRecycleBin && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-3xl rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-2xl space-y-4 max-h-[85vh] flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800 shrink-0">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Archive className="h-5 w-5 text-rose-500" />
                User Account Recycle Bin (Restorable within 30 days)
              </h3>
              <button
                type="button"
                onClick={() => setShowRecycleBin(false)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {loadingRecycleBin ? (
              <Loader label="Loading soft-deleted user accounts..." />
            ) : recycleBinUsers.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-500 font-medium">
                No soft-deleted user accounts currently in the Recycle Bin.
              </div>
            ) : (
              <div className="overflow-y-auto flex-1 border border-slate-200 dark:border-slate-800 rounded-xl">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 font-bold text-slate-600 dark:text-slate-300">
                      <th className="p-3">User</th>
                      <th className="p-3">Role</th>
                      <th className="p-3">Deleted Date</th>
                      <th className="p-3">Deleted By</th>
                      <th className="p-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-medium text-slate-700 dark:text-slate-300">
                    {recycleBinUsers.map((u) => (
                      <tr key={u.user_id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                        <td className="p-3">
                          <p className="font-bold text-slate-900 dark:text-slate-100">{u.name}</p>
                          <p className="text-[11px] text-slate-500">{u.email}</p>
                        </td>
                        <td className="p-3 capitalize">{u.role?.replace("_", " ")}</td>
                        <td className="p-3 text-slate-500">{u.deleted_at ? new Date(u.deleted_at).toLocaleString() : "-"}</td>
                        <td className="p-3 text-slate-500">{u.deleted_by || "System Admin"}</td>
                        <td className="p-3 text-right">
                          <Button
                            variant="subtle"
                            size="sm"
                            onClick={() => handleRestoreUser(u.user_id, u.name)}
                            className="!h-8 px-3 text-xs font-bold text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-900 bg-emerald-50/50 dark:bg-emerald-950/30 hover:bg-emerald-100"
                          >
                            <RotateCcw className="h-3.5 w-3.5 mr-1" /> Restore
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="flex justify-end pt-2 border-t border-slate-100 dark:border-slate-800 shrink-0">
              <Button variant="subtle" size="sm" type="button" onClick={() => setShowRecycleBin(false)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Student Lifecycle Status Modal */}
      {statusModalUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <GraduationCap className="h-5 w-5 text-indigo-500" />
                Student Lifecycle Status
              </h3>
              <button
                type="button"
                onClick={() => setStatusModalUser(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/50 border border-slate-100 dark:border-slate-800 text-xs space-y-1">
              <p className="font-bold text-slate-800 dark:text-slate-200">{statusModalUser.name}</p>
              <p className="text-slate-500">{statusModalUser.email} &bull; {statusModalUser.roll_number || statusModalUser.user_id}</p>
              {statusModalUser.program && (
                <p className="text-slate-500">Program: {statusModalUser.program} {statusModalUser.year ? `(Year ${statusModalUser.year})` : ""}</p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-700 dark:text-slate-300 block">
                Select Lifecycle Status
              </label>
              <select
                value={selectedLifecycleStatus}
                onChange={(e) => setSelectedLifecycleStatus(e.target.value)}
                className="h-10 w-full rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary"
              >
                <option value="Active">Active (Current Student)</option>
                <option value="Graduated">Graduated (Completed Degree - Read Only History)</option>
                <option value="Left College">Left College (Withdrawn / Discontinued)</option>
                <option value="Transferred">Transferred (Moved to another institution)</option>
                <option value="Inactive">Inactive / Suspended</option>
              </select>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Non-active statuses prevent login and complaint filing, but preserve complete historical complaints, audit logs, and analytics.
              </p>
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button variant="subtle" size="sm" type="button" onClick={() => setStatusModalUser(null)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" onClick={handleUpdateStudentStatus} disabled={savingStatus}>
                {savingStatus ? "Saving..." : "Update Status"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {confirmAction && (
        <ConfirmDialog
          open={!!confirmAction}
          title={confirmAction.title}
          message={confirmAction.message}
          confirmLabel={confirmAction.confirmLabel}
          tone={confirmAction.tone}
          onCancel={() => setConfirmAction(null)}
          onConfirm={async () => {
            await confirmAction.action();
            setConfirmAction(null);
          }}
        />
      )}

      {/* Bulk Import Staff Modal (Part 3.2b) */}
      <BulkImportModal
        isOpen={showStaffImportModal}
        onClose={() => setShowStaffImportModal(false)}
        type="staff"
        onSuccess={() => {
          reload();
          setMessage("Staff imported successfully.");
        }}
      />

      {/* Credential Slip Modal for Worker Login Slip (Part 3.5c) */}
      <CredentialSlipModal
        isOpen={Boolean(slipData)}
        onClose={() => setSlipData(null)}
        credentialData={slipData}
      />

      {/* Edit Staff Member Name Modal */}
      {editNameUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-md rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                <Edit2 className="h-4 w-4 text-emerald-500" />
                Edit Staff Member Name
              </h3>
              <button
                type="button"
                onClick={() => setEditNameUser(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {nameModalError && (
              <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-500 shrink-0" />
                <span>{nameModalError}</span>
              </div>
            )}

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1">
                  Staff Member Name
                </label>
                <input
                  type="text"
                  value={editNameValue}
                  onChange={(e) => setEditNameValue(e.target.value)}
                  placeholder="e.g. Coordinator 1"
                  className="w-full px-3 py-2 text-sm rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 text-xs text-slate-500 space-y-1 font-mono">
                <div>Email: <span className="font-semibold text-slate-700 dark:text-slate-300">{editNameUser.email}</span></div>
                <div>User ID: <span className="font-semibold text-slate-700 dark:text-slate-300">{editNameUser.user_id}</span></div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button variant="subtle" size="sm" type="button" onClick={() => setEditNameUser(null)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSaveName}
                disabled={savingName || !editNameValue.trim()}
              >
                {savingName ? "Saving..." : "Save Name"}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Responsibility and Role Modal */}
      {editRespUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/70 backdrop-blur-sm animate-in fade-in duration-200">
          <div className="w-full max-w-lg rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <div>
                <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 flex items-center gap-2">
                  <Shield className="h-5 w-5 text-indigo-500" />
                  Edit Responsibility & Role
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  Update system role or assign department coordinator responsibility.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setEditRespUser(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 p-1 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {respModalError && (
              <div className="p-3 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-rose-500 shrink-0" />
                <span>{respModalError}</span>
              </div>
            )}

            {/* Target User Info */}
            <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-100 dark:border-slate-800 text-xs space-y-1">
              <div className="font-bold text-slate-800 dark:text-slate-200 flex items-center justify-between">
                <span>{editRespUser.name}</span>
                <span className="font-mono text-slate-400">{editRespUser.user_id}</span>
              </div>
              <div className="text-slate-500">{editRespUser.email}</div>
            </div>

            <div className="space-y-4 text-xs">
              {/* Field 1: System Role */}
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 mb-1.5">
                  System Role
                </label>
                <select
                  value={selectedRespRole}
                  onChange={(e) => setSelectedRespRole(e.target.value)}
                  className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-indigo-500 font-semibold"
                >
                  
                  <option value="coordinator">Coordinator (Department Coordinator)</option>
                  <option value="location_in_charge">Location In-Charge / Warden</option>
                  <option value="app_manager">App Manager</option>
                  <option value="student">Student</option>
                </select>
                <p className="text-[11px] text-slate-400 mt-1">
                  Change role to convert user into an employee or remove them from the staff role.
                </p>
              </div>

              {/* Field 2: Coordinator Position (Only for employee/coordinator) */}
              {["employee", "coordinator"].includes(selectedRespRole) && (
                <div className="space-y-3 p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30">
                  <label className="block text-xs font-bold text-slate-700 dark:text-slate-300">
                    Department Responsibility
                  </label>
                  <div className="grid grid-cols-1 gap-2">
                    <label className={`flex items-center gap-2 p-2.5 rounded-xl border cursor-pointer transition-all ${selectedCoordType === "none" ? "border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/30 text-emerald-900 dark:text-emerald-100" : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300"}`}>
                      <input
                        type="radio"
                        name="coordType"
                        value="none"
                        checked={selectedCoordType === "none"}
                        onChange={() => setSelectedCoordType("none")}
                        className="text-emerald-600 focus:ring-emerald-500"
                      />
                      <div>
                        <div className="font-bold flex items-center gap-1.5">
                          <Wrench className="h-3.5 w-3.5 text-emerald-500" />
                          Operational Staff (No Coordinator Position)
                        </div>
                        <div className="text-[11px] text-slate-500">Regular technical employee resolving assigned complaints across campus.</div>
                      </div>
                    </label>

                    <label className={`flex items-center gap-2 p-2.5 rounded-xl border cursor-pointer transition-all ${selectedCoordType === "coordinator_1" ? "border-blue-500 bg-blue-50/50 dark:bg-blue-950/30 text-blue-900 dark:text-blue-100" : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300"}`}>
                      <input
                        type="radio"
                        name="coordType"
                        value="coordinator_1"
                        checked={selectedCoordType === "coordinator_1"}
                        onChange={() => setSelectedCoordType("coordinator_1")}
                        className="text-blue-600 focus:ring-blue-500"
                      />
                      <div>
                        <div className="font-bold flex items-center gap-1.5">
                          <Users className="h-3.5 w-3.5 text-blue-500" />
                          Coordinator 1 (Primary Coordinator)
                        </div>
                        <div className="text-[11px] text-slate-500">First responder intake coordinator for the selected department.</div>
                      </div>
                    </label>

                    <label className={`flex items-center gap-2 p-2.5 rounded-xl border cursor-pointer transition-all ${selectedCoordType === "coordinator_2" ? "border-blue-500 bg-blue-50/50 dark:bg-blue-950/30 text-blue-900 dark:text-blue-100" : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300"}`}>
                      <input
                        type="radio"
                        name="coordType"
                        value="coordinator_2"
                        checked={selectedCoordType === "coordinator_2"}
                        onChange={() => setSelectedCoordType("coordinator_2")}
                        className="text-blue-600 focus:ring-blue-500"
                      />
                      <div>
                        <div className="font-bold flex items-center gap-1.5">
                          <Users className="h-3.5 w-3.5 text-blue-500" />
                          Coordinator 2 (Backup Coordinator)
                        </div>
                        <div className="text-[11px] text-slate-500">Backup coordinator taking over when Coordinator 1 is unavailable.</div>
                      </div>
                    </label>
                  </div>

                  {selectedCoordType !== "none" && (
                    <div className="pt-2">
                      <label className="block text-[11px] font-bold text-slate-700 dark:text-slate-300 mb-1">
                        Select Department to Coordinate
                      </label>
                      <select
                        value={selectedCoordDeptId}
                        onChange={(e) => setSelectedCoordDeptId(e.target.value)}
                        className="w-full px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 focus:outline-none focus:border-blue-500 font-semibold"
                      >
                        {(data?.departments || []).map((d) => (
                          <option key={d.department_id} value={d.department_id}>
                            {d.name} ({d.department_id})
                          </option>
                        ))}
                      </select>
                      <p className="text-[10px] text-blue-600 dark:text-blue-400 mt-1">
                        Coordinator will manage this department campus-wide across all locations.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button variant="subtle" size="sm" type="button" onClick={() => setEditRespUser(null)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSaveResponsibility}
                disabled={savingResp}
              >
                {savingResp ? "Saving Changes..." : "Save Responsibility & Role"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
