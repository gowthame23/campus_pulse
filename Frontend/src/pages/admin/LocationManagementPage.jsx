import { useState, useMemo } from "react";
import {
  PlusCircle,
  RotateCw,
  Edit2,
  Archive,
  Trash2,
  RefreshCw,
  Building,
  Search,
  X,
  ChevronDown,
  ChevronUp,
  Plus,
  Tag,
  Check,
  Upload,
  Layers,
  Shield,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import Input from "../../components/Input.jsx";
import Loader from "../../components/Loader.jsx";
import PageHeader from "../../components/PageHeader.jsx";
import Select from "../../components/Select.jsx";
import Table from "../../components/Table.jsx";
import TableToolbar from "../../components/TableToolbar.jsx";
import Toast from "../../components/Toast.jsx";
import Modal from "../../components/Modal.jsx";
import BulkImportModal from "../../components/BulkImportModal.jsx";
import { useAsyncData } from "../../hooks/useAsyncData.js";
import { locationService } from "../../services/locationService.js";
import { departmentService } from "../../services/departmentService.js";
import { userService } from "../../services/userService.js";
import { ROLES } from "../../utils/constants.js";

const LOCATION_TYPES = [
  "Hostel",
  "Academic Block",
  "Mess",
  "Student Activity Center",
  "Sports Complex",
  "Other / Not Sure",
];

const DEFAULT_DEPARTMENT_TEMPLATES = {
  Hostel: [
    {
      name: "Electrical",
      sla_days: 2,
      complaint_types: [
        "Power Failure",
        "Fan Not Working",
        "Light Not Working",
        "Switch Problem",
        "Socket Problem",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Plumbing",
      sla_days: 3,
      complaint_types: [
        "Water Leakage",
        "Tap Not Working / Tap Leakage",
        "No Water Supply",
        "Low Water Pressure",
        "Toilet Flush Not Working",
        "Toilet Blockage",
        "Wash Basin / Sink Blockage",
        "Drainage Blockage",
        "Shower Not Working",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Network",
      sla_days: 3,
      complaint_types: [
        "Wi-Fi Not Working",
        "Wi-Fi Connected but No Internet",
        "Slow Internet",
        "Frequent Wi-Fi Disconnection",
        "Weak Wi-Fi Signal",
        "Unable to Connect to Wi-Fi",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Housekeeping",
      sla_days: 1,
      complaint_types: [
        "Room Cleaning Required",
        "Washroom / Bathroom Cleaning",
        "Dustbin / Waste Removal",
        "Corridor / Common Area Cleaning",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Furniture & Fixtures",
      sla_days: 5,
      complaint_types: [
        "Cot / Bed Frame Issue",
        "Study Table / Chair Damaged",
        "Cupboard / Wardrobe Lock/Door Issue",
        "Door / Window Latch Problem",
        "Mirror / Shelf Issue",
        "Missing Furniture / Item",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Other / Not Sure",
      sla_days: 2,
      complaint_types: ["General Issue"],
      enabled: true,
    },
  ],
  "Academic Block": [
    {
      name: "Electrical & AV / Classroom Equipment",
      sla_days: 2,
      complaint_types: [
        "Power Failure / No Power Supply",
        "Projector Not Working / No Display",
        "HDMI / VGA Cable / Connectivity Issue",
        "Audio / Speaker / Mic Issue",
        "Fan Not Working",
        "Light Not Working",
        "Smart Board / Digital Board Issue",
        "AC / Air Conditioning Issue",
        "Switch / Socket Problem",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Plumbing",
      sla_days: 3,
      complaint_types: [
        "Water Leakage",
        "Tap Not Working / Tap Leakage",
        "No Water Supply",
        "Toilet Flush Not Working",
        "Toilet / Urinal Blockage",
        "Wash Basin / Sink Blockage",
        "Drainage Blockage",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Network / IT",
      sla_days: 3,
      complaint_types: [
        "Wi-Fi Not Working",
        "Ethernet / LAN Port Not Working",
        "Wi-Fi Connected but No Internet",
        "Slow Internet Connection",
        "Weak Wi-Fi Signal",
        "Unable to Connect to Campus Network",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Housekeeping",
      sla_days: 1,
      complaint_types: [
        "Classroom / Lab Cleaning Required",
        "Washroom Cleaning Required",
        "Dustbin / Waste Removal",
        "Corridor / Staircase Cleaning",
        "Board Cleaning / Dusting Required",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Furniture & Fixtures",
      sla_days: 5,
      complaint_types: [
        "Desk / Bench Damaged",
        "Chair / Podium Issue",
        "Door / Lock / Window Latch Issue",
        "Whiteboard / Blackboard Damaged",
        "Missing Furniture / Item",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Library Facilities & Systems",
      sla_days: 3,
      complaint_types: [
        "Wi-Fi / E-Library Desktop / OPAC System Issue",
        "RFID / Book Scanner / Printer Issue",
        "Reading Desk Power Socket / Lamp Issue",
        "AC / Ventilation Issue (Reading Area)",
        "Study Table / Chair / Bookshelf Damaged",
        "Noise Disturbance / Quiet Zone Violation",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Other / Not Sure",
      sla_days: 2,
      complaint_types: ["General Issue"],
      enabled: true,
    },
  ],
  Mess: [
    {
      name: "Hygiene & Housekeeping",
      sla_days: 1,
      complaint_types: [
        "Dining Table / Area Cleaning Required",
        "Handwash / Sink Area Unclean",
        "Dustbin Overflowing / Waste Removal",
        "Pest / Insect Issue",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Food Quality & Catering",
      sla_days: 1,
      complaint_types: [
        "Food Quality / Taste Issue",
        "Undercooked / Raw Food",
        "Foreign Object in Food",
        "Food / Utensil Shortage",
        "Counter / Service Delay",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Maintenance & Equipment",
      sla_days: 3,
      complaint_types: [
        "Water Cooler / Dispenser Issue",
        "Food Warmer / Bain-Marie Not Working",
        "Exhaust Fan / Ventilation Issue",
        "Lighting / Electrical Issue",
        "Fly Catcher Machine Not Working",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Furniture & Seating",
      sla_days: 5,
      complaint_types: [
        "Dining Table Damaged / Wobbly",
        "Chair / Bench Damaged",
        "Missing Furniture / Item",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Plumbing",
      sla_days: 3,
      complaint_types: [
        "Handwash Tap Leakage / Not Working",
        "Drinking Water Supply Issue",
        "Sink / Drainage Blockage",
        "Washroom Plumbing Issue",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Other / Not Sure",
      sla_days: 2,
      complaint_types: ["General Mess Issue"],
      enabled: true,
    },
  ],
  "Student Activity Center": [
    {
      name: "Sound, Lighting & Stage AV",
      sla_days: 2,
      complaint_types: [
        "Speaker / Sound System Issue",
        "Microphone / Audio Mixer Problem",
        "Stage Lights / Spotlights Not Working",
        "Projector / Display Screen Issue",
        "HDMI / Cable / Adapter Missing or Damaged",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Equipment & Sports Goods",
      sla_days: 3,
      complaint_types: [
        "Indoor Games Equipment Damaged (TT, Carrom, Chess, etc.)",
        "Gym Equipment Faulty / Broken",
        "Music Instrument / Studio Gear Damaged",
        "Missing Activity Equipment / Item",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Housekeeping & Facilities",
      sla_days: 1,
      complaint_types: [
        "Main Hall / Auditorium Cleaning Required",
        "Gymnasium / Activity Area Unclean",
        "Washroom Cleaning Required",
        "Dustbin Overflowing / Waste Removal",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Electrical & Air Conditioning",
      sla_days: 2,
      complaint_types: [
        "AC / Ventilation Not Working",
        "Power Failure / Trip",
        "Fan / Light Issue",
        "Socket / Power Point Problem",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Plumbing",
      sla_days: 3,
      complaint_types: [
        "Water Cooler / Dispenser Leakage or Not Working",
        "Washroom Tap / Flush Leakage",
        "Sink / Drainage Blockage",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Other / Not Sure",
      sla_days: 2,
      complaint_types: ["General SAC Issue"],
      enabled: true,
    },
  ],
  "Sports Complex": [
    {
      name: "Grounds, Courts & Fields",
      sla_days: 3,
      complaint_types: [
        "Court / Turf Surface Damaged",
        "Net / Post / Goalpost Damaged or Missing",
        "Field Marking / Fencing Issue",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Sports Equipment & Gear",
      sla_days: 3,
      complaint_types: [
        "Equipment Damaged / Broken",
        "Missing Sports Equipment / Item",
        "Locker / Storage Locker Lock Issue",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Lighting, Electrical & Floodlights",
      sla_days: 2,
      complaint_types: [
        "Ground / Court Floodlight Not Working",
        "Indoor Court Lighting / Fan Issue",
        "Power Outlet / Socket Problem",
        "Scoreboard / Display Issue",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Housekeeping & Locker Rooms",
      sla_days: 1,
      complaint_types: [
        "Locker Room / Changing Room Unclean",
        "Court / Gymnasium Cleaning Required",
        "Washroom Cleaning Required",
        "Dustbin Overflowing / Waste Removal",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Plumbing & Showers",
      sla_days: 3,
      complaint_types: [
        "Shower Leakage / Not Working",
        "Tap / Washbasin Leakage",
        "Water Cooler / Drinking Water Dispenser Issue",
        "Toilet / Drainage Blockage",
        "Other / Not Sure",
      ],
      enabled: true,
    },
    {
      name: "Other / Not Sure",
      sla_days: 2,
      complaint_types: ["General Sports Complex Issue"],
      enabled: true,
    },
  ],
  "Other / Not Sure": [
    {
      name: "General Maintenance",
      sla_days: 2,
      complaint_types: [
        "Electrical Issue",
        "Plumbing Issue",
        "Housekeeping Required",
        "Furniture / Fixture Issue",
        "Network Issue",
        "General Complaint / Other",
      ],
      enabled: true,
    },
  ],
};

const getInitialDepts = (typeKey) => {
  const templates =
    DEFAULT_DEPARTMENT_TEMPLATES[typeKey] ||
    DEFAULT_DEPARTMENT_TEMPLATES["Other / Not Sure"];
  return templates.map((d) => ({
    name: d.name,
    sla_days: d.sla_days,
    complaint_types: [...d.complaint_types],
    enabled: true,
    expanded: false,
    newIssueInput: "",
  }));
};

export default function LocationManagementPage() {
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedTypeFilter, setSelectedTypeFilter] = useState("");
  const [showBulkImport, setShowBulkImport] = useState(false);

  // Option 1: New Location under an existing Type
  const [createModalType, setCreateModalType] = useState(null); // e.g. "Hostel"
  const [newLocationName, setNewLocationName] = useState("");
  const [newPublicComplaintAccess, setNewPublicComplaintAccess] = useState("everyone");
  const [selectedDeptIds, setSelectedDeptIds] = useState([]);
  const [locDeptsConfig, setLocDeptsConfig] = useState([]);

  // Option 2: New Location Type creation
  const [showNewTypeModal, setShowNewTypeModal] = useState(false);
  const [newTypeName, setNewTypeName] = useState("");
  const [newTypeDescription, setNewTypeDescription] = useState("");
  const [typeDeptsConfig, setTypeDeptsConfig] = useState([]);

  // Edit State
  const [editTarget, setEditTarget] = useState(null);
  const [editName, setEditName] = useState("");
  const [editType, setEditType] = useState("");
  const [editPublicComplaintAccess, setEditPublicComplaintAccess] = useState("everyone");
  const [editDeptIds, setEditDeptIds] = useState([]);

  // Delete Confirmation State
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleteInput, setDeleteInput] = useState("");
  const [deleteDependencyError, setDeleteDependencyError] = useState("");

  const { data, loading, reload } = useAsyncData(async () => {
    const [typesRes, locationsRes, inChargesRes, appManagersRes, deptsRes] =
      await Promise.all([
        locationService
          .listTypes({ include_archived: showArchived })
          .catch(() => ({ data: [] })),
        locationService.list({ include_archived: showArchived }),
        userService.list(ROLES.LOCATION_IN_CHARGE).catch(() => ({ data: [] })),
        userService.list(ROLES.APP_MANAGER).catch(() => ({ data: [] })),
        departmentService.list({ include_archived: false }).catch(() => ({ data: [] })),
      ]);
    return {
      locationTypes: typesRes.data || [],
      locations: locationsRes.data || [],
      inCharges: inChargesRes.data || [],
      appManagers: appManagersRes.data || [],
      departments: deptsRes.data || [],
    };
  }, [showArchived]);

  const openCreateLocationModal = (type_name) => {
    setCreateModalType(type_name);
    setNewLocationName("");
    const allDeptIds = (data?.departments || []).map((d) => d.department_id);
    setSelectedDeptIds(allDeptIds);
    setLocDeptsConfig(getInitialDepts(type_name));
    setNewPublicComplaintAccess(
      (type_name || "").toLowerCase().includes("hostel") ? "location_only" : "everyone"
    );
  };

  const openCreateTypeModal = () => {
    setNewTypeName("");
    setNewTypeDescription("");
    setTypeDeptsConfig(getInitialDepts("Other / Not Sure"));
    setShowNewTypeModal(true);
  };

  // Option 1 Handler: Create Location under an existing Type
  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!newLocationName.trim()) {
      setError("Location name is required.");
      return;
    }

    const normalized = newLocationName.trim().toLowerCase();
    const duplicate = (data?.locations || []).some(
      (l) => l.name.trim().toLowerCase() === normalized,
    );
    if (duplicate) {
      setError(
        `Location "${newLocationName.trim()}" already exists. Please choose another name.`,
      );
      return;
    }

    try {
      await locationService.create({
        name: newLocationName.trim(),
        location_type: createModalType,
        department_ids: selectedDeptIds,
        complaint_submission_policy: newPublicComplaintAccess,
        public_complaint_access: newPublicComplaintAccess,
      });
      setCreateModalType(null);
      setNewLocationName("");
      setMessage(
        `New location "${newLocationName.trim()}" created successfully with ${selectedDeptIds.length} operating department(s).`,
      );
      reload();
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to create location.");
    }
  };

  // Option 2 Handler: Create a brand new Location Type
  const handleCreateTypeSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!newTypeName.trim()) {
      setError("Location Type name is required.");
      return;
    }

    const enabledDepts = typeDeptsConfig
      .filter((d) => d.enabled && d.name.trim())
      .map((d) => ({
        name: d.name.trim(),
        sla_days: Number(d.sla_days) || 2,
        complaint_types: d.complaint_types || [],
      }));

    try {
      await locationService.createType({
        name: newTypeName.trim(),
        description: newTypeDescription.trim(),
        departments: enabledDepts,
      });
      setShowNewTypeModal(false);
      setNewTypeName("");
      setNewTypeDescription("");
      setMessage(
        `Location Type "${newTypeName.trim()}" created successfully with ${enabledDepts.length} default department template(s).`,
      );
      reload();
    } catch (err) {
      setError(
        err?.response?.data?.detail || "Unable to create Location Type.",
      );
    }
  };

  const assignAppManager = async (locationId, appManagerId) => {
    setMessage("");
    setError("");
    try {
      if (!appManagerId) {
        await locationService.unassignAppManager(locationId);
        setMessage("Location App Manager unassigned successfully.");
      } else {
        await locationService.assignAppManager(locationId, appManagerId);
        setMessage("Location App Manager assigned successfully.");
      }
      reload();
    } catch (err) {
      setError(
        err?.response?.data?.detail || "Unable to assign App Manager.",
      );
    }
  };

  const assignInCharge = async (locationId, inChargeId) => {
    setMessage("");
    setError("");
    try {
      if (!inChargeId) {
        await locationService.unassignInCharge(locationId);
        setMessage("Warden unassigned successfully.");
      } else {
        await locationService.assignInCharge(locationId, inChargeId);
        setMessage("Warden assigned successfully.");
      }
      reload();
    } catch (err) {
      setError(
        err?.response?.data?.detail || "Unable to assign warden.",
      );
    }
  };


  const startEdit = (location) => {
    setEditTarget(location);
    setEditName(location.name);
    setEditType(location.location_type || getLocationType(location));
    setEditPublicComplaintAccess(
      location.complaint_submission_policy ||
      location.public_complaint_access ||
      ((location.location_type || "").toLowerCase().includes("hostel") ? "location_only" : "everyone")
    );
    setEditDeptIds(
      location.department_ids ||
      (location.departments || []).map((d) => d.department_id) ||
      []
    );
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");

    if (!editName.trim()) {
      setError("Location name is required.");
      return;
    }

    try {
      await locationService.update(editTarget.location_id, {
        name: editName.trim(),
        location_type: editType,
        complaint_submission_policy: editPublicComplaintAccess,
        public_complaint_access: editPublicComplaintAccess,
        department_ids: editDeptIds,
      });
      setEditTarget(null);
      setMessage(`Location "${editName.trim()}" updated successfully.`);
      reload();
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to update location.");
    }
  };

  const archiveLocation = async (locationId) => {
    if (locationId === "LOC_OTHER") {
      setError("The default 'Other / Not Sure' location is required by system triage and cannot be archived.");
      return;
    }
    setMessage("");
    setError("");
    try {
      await locationService.update(locationId, { archived: true });
      setMessage("Location archived successfully.");
      reload();
    } catch (err) {
      setError(err?.response?.data?.detail || "Unable to archive location.");
    }
  };

  const startDelete = (location) => {
    if (location?.location_id === "LOC_OTHER") {
      setError("The default 'Other / Not Sure' location is required by system triage and cannot be deleted.");
      return;
    }
    setDeleteTarget(location);
    setDeleteInput("");
    setDeleteDependencyError("");
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setMessage("");
    setError("");
    setDeleteDependencyError("");

    try {
      await locationService.delete(deleteTarget.location_id);
      setMessage(`Location "${deleteTarget.name}" deleted permanently.`);
      setDeleteTarget(null);
      reload();
    } catch (err) {
      const errMsg =
        err?.response?.data?.detail || "Unable to delete location.";
      if (
        errMsg.toLowerCase().includes("cannot delete") ||
        errMsg.toLowerCase().includes("active complaints") ||
        errMsg.toLowerCase().includes("assigned users")
      ) {
        setDeleteDependencyError(errMsg);
      } else {
        setError(errMsg);
        setDeleteTarget(null);
      }
    }
  };

  const handleArchiveFromError = async () => {
    if (!deleteTarget) return;
    await archiveLocation(deleteTarget.location_id);
    setDeleteDependencyError("");
    setDeleteTarget(null);
  };

  const renderCentralDepartmentSelector = (selectedIds, setSelectedIds) => {
    const allDepts = data?.departments || [];
    const toggleDept = (deptId) => {
      setSelectedIds((prev) =>
        prev.includes(deptId)
          ? prev.filter((id) => id !== deptId)
          : [...prev, deptId]
      );
    };

    const selectAll = () => {
      setSelectedIds(allDepts.map((d) => d.department_id));
    };

    const deselectAll = () => {
      setSelectedIds([]);
    };

    return (
      <div className="border border-slate-200 dark:border-slate-800 rounded-xl p-4 bg-slate-50/50 dark:bg-slate-900/50">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 flex items-center gap-1.5">
              <Layers className="h-4 w-4 text-primary" />
              Operating Departments ({selectedIds.length} Selected)
            </h4>
            <p className="text-[11px] text-slate-500 dark:text-slate-400">
              Select which campus-wide departments operate at this location.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={selectAll}
              className="text-[11px] font-semibold text-primary hover:underline cursor-pointer"
            >
              Select All
            </button>
            <span className="text-slate-300 dark:text-slate-700">|</span>
            <button
              type="button"
              onClick={deselectAll}
              className="text-[11px] font-semibold text-slate-500 hover:underline cursor-pointer"
            >
              Clear
            </button>
          </div>
        </div>

        {allDepts.length === 0 ? (
          <div className="text-xs text-slate-400 italic py-2">
            No central departments found.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-56 overflow-y-auto pr-1">
            {allDepts.map((dept) => {
              const isChecked = selectedIds.includes(dept.department_id);
              return (
                <label
                  key={dept.department_id}
                  className={`flex items-start gap-2.5 p-2 rounded-lg border text-xs cursor-pointer transition-all ${
                    isChecked
                      ? "bg-primary/5 border-primary/40 text-slate-900 dark:text-slate-100 font-semibold"
                      : "bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-slate-300"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={isChecked}
                    onChange={() => toggleDept(dept.department_id)}
                    className="mt-0.5 h-3.5 w-3.5 rounded border-slate-300 text-primary focus:ring-primary"
                  />
                  <div className="min-w-0">
                    <span className="block truncate font-semibold">
                      {dept.name}
                    </span>
                    {dept.description && (
                      <span className="text-[10px] text-slate-400 block truncate font-normal">
                        {dept.description}
                      </span>
                    )}
                  </div>
                </label>
              );
            })}
          </div>
        )}
      </div>
    );
  };

  // Render department management section inside modals
  const renderDepartmentConfigSection = (deptsList, setDeptsList) => {
    const toggleEnable = (idx) => {
      setDeptsList((prev) =>
        prev.map((d, i) => (i === idx ? { ...d, enabled: !d.enabled } : d)),
      );
    };

    const toggleExpand = (idx) => {
      setDeptsList((prev) =>
        prev.map((d, i) => (i === idx ? { ...d, expanded: !d.expanded } : d)),
      );
    };

    const updateSla = (idx, val) => {
      setDeptsList((prev) =>
        prev.map((d, i) => (i === idx ? { ...d, sla_days: val } : d)),
      );
    };

    const removeIssue = (deptIdx, issueIdx) => {
      setDeptsList((prev) =>
        prev.map((d, i) => {
          if (i !== deptIdx) return d;
          const nextIssues = [...d.complaint_types];
          nextIssues.splice(issueIdx, 1);
          return { ...d, complaint_types: nextIssues };
        }),
      );
    };

    const addIssue = (deptIdx) => {
      setDeptsList((prev) =>
        prev.map((d, i) => {
          if (i !== deptIdx) return d;
          if (!d.newIssueInput || !d.newIssueInput.trim()) return d;
          const trimmed = d.newIssueInput.trim();
          if (d.complaint_types.includes(trimmed)) return d;
          return {
            ...d,
            complaint_types: [...d.complaint_types, trimmed],
            newIssueInput: "",
          };
        }),
      );
    };

    const addCustomDepartment = () => {
      setDeptsList((prev) => [
        ...prev,
        {
          name: "New Department",
          sla_days: 2,
          complaint_types: ["General Issue"],
          enabled: true,
          expanded: true,
          newIssueInput: "",
        },
      ]);
    };

    return (
      <div className="mt-2 space-y-3">
        <div className="flex items-center justify-between border-b border-slate-200 dark:border-slate-800 pb-2">
          <div>
            <h4 className="text-xs font-bold text-slate-800 dark:text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
              <Building className="h-3.5 w-3.5 text-indigo-500" />
              Departments & Complaint Categories
            </h4>
            <p className="text-[11px] text-slate-500 font-medium">
              Configure which departments and complaint issues will be available for this location.
            </p>
          </div>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300">
            {deptsList.filter((d) => d.enabled).length} Active
          </span>
        </div>

        <div className="max-h-[300px] overflow-y-auto pr-1 space-y-2.5">
          {deptsList.map((dept, idx) => (
            <div
              key={idx}
              className={`rounded-xl border p-3 transition-all ${
                dept.enabled
                  ? "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 shadow-sm"
                  : "border-slate-200/50 dark:border-slate-800/50 bg-slate-50/50 dark:bg-slate-900/30 opacity-60"
              }`}
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5 min-w-0 flex-1">
                  <input
                    type="checkbox"
                    checked={dept.enabled}
                    onChange={() => toggleEnable(idx)}
                    className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500 shrink-0"
                  />
                  <input
                    type="text"
                    value={dept.name}
                    onChange={(e) => {
                      const val = e.target.value;
                      setDeptsList((prev) =>
                        prev.map((d, i) => (i === idx ? { ...d, name: val } : d)),
                      );
                    }}
                    placeholder="Department Name"
                    className="h-8 text-xs font-bold text-slate-800 dark:text-slate-100 bg-transparent border border-transparent hover:border-slate-300 dark:hover:border-slate-700 focus:border-indigo-500 rounded px-1.5 transition-colors outline-none w-full min-w-0"
                  />
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  <div className="flex items-center gap-1 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-lg">
                    <span className="text-[10px] font-semibold text-slate-500">SLA:</span>
                    <input
                      type="number"
                      min="1"
                      max="30"
                      value={dept.sla_days}
                      onChange={(e) => updateSla(idx, e.target.value)}
                      className="w-8 text-center text-xs font-bold text-slate-800 dark:text-slate-200 bg-transparent outline-none"
                    />
                    <span className="text-[10px] font-semibold text-slate-500">d</span>
                  </div>

                  <button
                    type="button"
                    onClick={() => toggleExpand(idx)}
                    className="flex items-center gap-1 text-[11px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300 bg-indigo-50 dark:bg-indigo-950/40 px-2 py-1 rounded-lg transition-colors"
                  >
                    <span>{dept.complaint_types.length} issues</span>
                    {dept.expanded ? (
                      <ChevronUp className="h-3.5 w-3.5" />
                    ) : (
                      <ChevronDown className="h-3.5 w-3.5" />
                    )}
                  </button>
                </div>
              </div>

              {dept.expanded && (
                <div className="mt-3 pt-3 border-t border-slate-100 dark:border-slate-800 space-y-2">
                  <div className="flex flex-wrap gap-1.5">
                    {dept.complaint_types.map((issue, issueIdx) => (
                      <span
                        key={issueIdx}
                        className="inline-flex items-center gap-1 text-[11px] font-medium bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 px-2 py-0.5 rounded-md"
                      >
                        <Tag className="h-3 w-3 text-slate-400" />
                        <span>{issue}</span>
                        <button
                          type="button"
                          onClick={() => removeIssue(idx, issueIdx)}
                          className="hover:text-red-500 ml-0.5 text-slate-400"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </span>
                    ))}
                  </div>

                  <div className="flex items-center gap-2 pt-1">
                    <input
                      type="text"
                      placeholder="Add custom complaint issue/type..."
                      value={dept.newIssueInput || ""}
                      onChange={(e) => {
                        const val = e.target.value;
                        setDeptsList((prev) =>
                          prev.map((d, i) =>
                            i === idx ? { ...d, newIssueInput: val } : d,
                          ),
                        );
                      }}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          addIssue(idx);
                        }
                      }}
                      className="h-8 text-xs flex-1 rounded-lg border border-slate-200 dark:border-slate-700 px-2.5 bg-white dark:bg-slate-900 outline-none focus:border-indigo-500"
                    />
                    <Button
                      type="button"
                      variant="subtle"
                      size="sm"
                      onClick={() => addIssue(idx)}
                      className="h-8 px-2.5 text-xs font-semibold shrink-0"
                    >
                      <Plus className="h-3.5 w-3.5 mr-1" />
                      Add Issue
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        <Button
          type="button"
          variant="subtle"
          size="sm"
          onClick={addCustomDepartment}
          className="w-full h-9 border border-dashed border-slate-300 dark:border-slate-700 text-xs font-bold text-indigo-600 dark:text-indigo-400 hover:bg-indigo-50 dark:hover:bg-indigo-950/30"
        >
          <Plus className="h-3.5 w-3.5 mr-1.5" />
          + Add Custom Department
        </Button>
      </div>
    );
  };

  const getLocationType = (loc) => {
    if (loc.location_type) return loc.location_type;
    const name = loc.name.toLowerCase();
    if (name.includes("hostel")) return "Hostel";
    if (name.includes("academic")) return "Academic Block";
    if (name.includes("mess")) return "Mess";
    if (name.includes("activity") || name.includes("sac"))
      return "Student Activity Center";
    if (name.includes("sports")) return "Sports Complex";
    return "Other / Not Sure";
  };

  const filteredLocations = useMemo(() => {
    let rawLocs = data?.locations || [];
    if (showArchived) {
      rawLocs = rawLocs.filter((loc) => loc.archived === true);
    } else {
      rawLocs = rawLocs.filter((loc) => !loc.archived);
    }
    if (!query.trim() && !selectedTypeFilter) return rawLocs;

    return rawLocs.filter((loc) => {
      const type = loc.location_type || getLocationType(loc);

      if (selectedTypeFilter && type !== selectedTypeFilter) {
        return false;
      }

      if (query.trim()) {
        const q = query.toLowerCase().trim();
        const nameMatch = (loc.name || "").toLowerCase().includes(q);
        const typeMatch = (type || "").toLowerCase().includes(q);

        const appMgr = (data?.appManagers || []).find(
          (u) => u.user_id === loc.app_manager_id,
        );
        const appMgrMatch = (appMgr?.name || "").toLowerCase().includes(q);

        const inCharge = (data?.inCharges || []).find(
          (u) => u.user_id === loc.in_charge_id,
        );
        const inChargeMatch = (inCharge?.name || "").toLowerCase().includes(q);

        if (
          !nameMatch &&
          !typeMatch &&
          !appMgrMatch &&
          !inChargeMatch
        ) {
          return false;
        }
      }

      return true;
    });
  }, [data, query, selectedTypeFilter, showArchived]);

  const columns = [
    {
      header: "Location Name",
      accessor: "name",
      render: (row) => (
        <div>
          <span className="font-bold text-slate-900 dark:text-slate-100 text-xs">
            {row.name}
          </span>
          {row.archived && (
            <span className="ml-2 px-1.5 py-0.5 text-[10px] font-bold rounded bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300">
              Archived
            </span>
          )}
        </div>
      ),
    },
    {
      header: "Submission Policy",
      accessor: "complaint_submission_policy",
      render: (row) => {
        const policy =
          row.complaint_submission_policy ||
          row.public_complaint_access ||
          ((row.location_type || "").toLowerCase().includes("hostel") ? "location_only" : "everyone");
        const isLocOnly = policy === "location_only";
        return isLocOnly ? (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
            Location Only
          </span>
        ) : (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
            Everyone
          </span>
        );
      },
    },
    {
      header: "Operating Departments",
      accessor: "departments",
      render: (row) => {
        const depts = row.departments || [];
        if (depts.length === 0) {
          return (
            <span className="text-[11px] text-slate-400 italic">None assigned</span>
          );
        }
        return (
          <div className="flex flex-wrap gap-1 max-w-[220px]">
            {depts.slice(0, 3).map((d) => (
              <span
                key={d.department_id}
                className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold bg-indigo-50 dark:bg-indigo-950/40 text-indigo-700 dark:text-indigo-300 border border-indigo-100 dark:border-indigo-900/50"
              >
                {d.name}
              </span>
            ))}
            {depts.length > 3 && (
              <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-bold bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                +{depts.length - 3} more
              </span>
            )}
          </div>
        );
      },
    },
    {
      header: "App Manager",
      accessor: "app_manager_id",
      render: (row) => {
        const isOther =
          row.location_id === "LOC_OTHER" ||
          (row.name || "").toLowerCase().includes("other");
        if (isOther) {
          return (
            <div className="py-1">
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md text-[11px] font-bold bg-purple-50 dark:bg-purple-950/40 text-purple-700 dark:text-purple-300 border border-purple-200 dark:border-purple-800">
                <Shield className="h-3 w-3" /> Admin Triage
              </span>
              <p className="text-[10px] text-slate-400 mt-0.5">Automated to Admin</p>
            </div>
          );
        }
        return (
          <Select
            value={row.app_manager_id || ""}
            onChange={(e) => assignAppManager(row.location_id, e.target.value)}
            className="!py-1 !px-2 !text-xs font-semibold"
          >
            <option value="">Unassigned</option>
            {(data?.appManagers || []).map((u) => (
              <option key={u.user_id} value={u.user_id}>
                {u.name} ({u.email})
              </option>
            ))}
          </Select>
        );
      },
    },
    {
      header: "In-Charge Warden",
      accessor: "in_charge_id",
      render: (row) => {
        const isOther =
          row.location_id === "LOC_OTHER" ||
          (row.name || "").toLowerCase().includes("other");
        if (isOther) {
          return (
            <span className="text-xs text-slate-400 italic">Admin Managed</span>
          );
        }
        return (
          <Select
            value={row.in_charge_id || ""}
            onChange={(e) => assignInCharge(row.location_id, e.target.value)}
            className="!py-1 !px-2 !text-xs font-semibold"
          >
            <option value="">Unassigned</option>
            {(data?.inCharges || []).map((u) => (
              <option key={u.user_id} value={u.user_id}>
                {u.name} ({u.email})
              </option>
            ))}
          </Select>
        );
      },
    },
    {
      header: "Actions",
      accessor: "location_id",
      render: (row) => {
        const isOther =
          row.location_id === "LOC_OTHER" ||
          (row.name || "").toLowerCase().includes("other");
        if (isOther) {
          return (
            <div className="flex items-center gap-1.5">
              <Button
                variant="subtle"
                size="sm"
                onClick={() => startEdit(row)}
                className="!p-1.5 text-primary hover:text-primary/80"
                title="Edit Operating Departments"
              >
                <Edit2 className="h-4 w-4" />
              </Button>
              <span className="text-[11px] text-slate-400 italic">System Protected</span>
            </div>
          );
        }
        return (
          <div className="flex items-center gap-1.5">
            {row.archived ? (
              <Button
                variant="subtle"
                size="sm"
                onClick={async () => {
                  try {
                    await locationService.update(row.location_id, {
                      archived: false,
                    });
                    setMessage(`Location "${row.name}" restored successfully.`);
                    reload();
                  } catch (err) {
                    setError(
                      err?.response?.data?.detail || "Unable to restore location.",
                    );
                  }
                }}
                className="!p-1.5 text-emerald-600 hover:text-emerald-700"
                title="Restore"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            ) : (
              <>
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
                  onClick={() => archiveLocation(row.location_id)}
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
        );
      },
    },
  ];

  return (
    <div className="grid gap-8">
      {/* Page Title & Breadcrumbs */}
      <div>
        <nav className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 mb-2">
          <span>Dashboard</span>
          <span>&gt;</span>
          <span className="text-slate-800 dark:text-slate-100 font-bold">
            Locations
          </span>
        </nav>
        <PageHeader
          title="Location Configuration"
          description="Manage Location Types, physical campus locations, blocks, departments, and in-charge warden assignments."
        />
      </div>

      <Toast message={message} tone="success" onClose={() => setMessage("")} />
      <Toast message={error} tone="danger" onClose={() => setError("")} />

      {/* Global Merged Toolbar */}
      <TableToolbar
        actions={
          <div className="flex flex-wrap items-center gap-3">
            {/* 🔍 Search Input */}
            <div className="relative min-w-[220px] flex-1">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search location name, manager, warden..."
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

            {/* 🏢 Location Type Filter Dropdown */}
            <select
              value={selectedTypeFilter}
              onChange={(e) => setSelectedTypeFilter(e.target.value)}
              className="h-10 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs font-semibold text-slate-700 dark:text-slate-200 outline-none focus:border-primary shrink-0"
            >
              <option value="">🏢 All Location Types</option>
              {LOCATION_TYPES.map((type) => (
                <option key={type} value={type}>
                  🏢 {type}
                </option>
              ))}
            </select>

            <Button
              variant="primary"
              size="sm"
              onClick={openCreateTypeModal}
              className="h-10 px-4 rounded-xl text-xs font-bold bg-indigo-600 hover:bg-indigo-700 text-white shrink-0"
            >
              <PlusCircle className="h-4 w-4 mr-1.5 shrink-0" />
              + New Location Type
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowBulkImport(true)}
              className="h-10 px-4 rounded-xl text-xs font-bold border-indigo-200 text-indigo-700 dark:border-indigo-800 dark:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-950/40 shrink-0"
            >
              <Upload className="h-4 w-4 mr-1.5 shrink-0" />
              Bulk Import Locations
            </Button>
            <label className="flex items-center gap-2 cursor-pointer select-none shrink-0">
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
            <Button
              variant="subtle"
              size="sm"
              onClick={reload}
              className="h-10 px-4 rounded-xl text-xs font-bold shrink-0"
            >
              <RotateCw className="h-4 w-4 mr-1.5 shrink-0" />
              Refresh
            </Button>
          </div>
        }
      />

      {loading && (
        <Loader
          label="Loading location types and locations"
          variant="skeleton"
        />
      )}

      {/* Render Location Types Hierarchy */}
      {!loading && (
        <div className="grid gap-6">
          {(() => {
            const canonicalTypes = LOCATION_TYPES;
            const fetchedTypes = (data?.locationTypes || []).map(
              (t) => t.type_name || t.name,
            );
            const allTypes = Array.from(
              new Set([...canonicalTypes, ...fetchedTypes]),
            );

            const typesToRender = selectedTypeFilter
              ? allTypes.filter((t) => t === selectedTypeFilter)
              : allTypes;

            return typesToRender.map((type_name) => {
              const groupLocations = filteredLocations.filter(
                (l) => getLocationType(l) === type_name,
              );

              if (query.trim() && groupLocations.length === 0) return null;

              return (
                <Card key={type_name} className="!p-6">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100 dark:border-slate-800 mb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-2.5 rounded-xl bg-primary/10 text-primary">
                        <Building className="h-5 w-5" />
                      </div>
                      <div>
                        <h2 className="text-base font-bold text-slate-900 dark:text-slate-100">
                          {type_name}
                        </h2>
                        <p className="text-xs text-slate-500 dark:text-slate-400 font-medium mt-0.5">
                          {groupLocations.length} physical location
                          {groupLocations.length === 1 ? "" : "s"} configured
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="primary"
                      size="sm"
                      onClick={() => openCreateLocationModal(type_name)}
                      className="font-bold shrink-0"
                    >
                      <PlusCircle className="h-4 w-4 mr-1.5" />
                      + New{" "}
                      {type_name === "Other / Not Sure"
                        ? "Location"
                        : type_name}
                    </Button>
                  </div>

                  {groupLocations.length === 0 ? (
                    <div className="py-6 text-center text-xs font-medium text-slate-400 dark:text-slate-500 bg-slate-50/50 dark:bg-slate-900/50 rounded-xl border border-dashed border-slate-200 dark:border-slate-800">
                      No locations configured under {type_name}. Click above to
                      add one.
                    </div>
                  ) : (
                    <Table
                      columns={columns}
                      rows={groupLocations}
                      getRowKey={(row) => row.location_id}
                    />
                  )}
                </Card>
              );
            });
          })()}
        </div>
      )}

      {/* Option 2 Modal: Create a brand new Location Type */}
      <Modal
        open={showNewTypeModal}
        title="Create New Location Type"
        onClose={() => setShowNewTypeModal(false)}
      >
        <form onSubmit={handleCreateTypeSubmit} className="grid gap-5">
          <Input
            label="Location Type Name"
            placeholder="e.g. Medical Center, Research Lab"
            value={newTypeName}
            onChange={(e) => setNewTypeName(e.target.value)}
            required
            autoFocus
          />
          <Input
            label="Description (Optional)"
            placeholder="e.g. Campus medical clinic and first-aid center"
            value={newTypeDescription}
            onChange={(e) => setNewTypeDescription(e.target.value)}
          />

          {renderDepartmentConfigSection(typeDeptsConfig, setTypeDeptsConfig)}

          <div className="mt-4 flex justify-end gap-3">
            <Button
              type="button"
              variant="subtle"
              onClick={() => setShowNewTypeModal(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" className="font-bold px-6">
              Create Location Type
            </Button>
          </div>
        </form>
      </Modal>

      {/* Option 1 Modal: Create Location under an existing Type */}
      <Modal
        open={!!createModalType}
        title={`New ${createModalType}`}
        onClose={() => setCreateModalType(null)}
      >
        <form onSubmit={handleCreateSubmit} className="grid gap-5">
          <Input
            label={`${createModalType} Name`}
            placeholder={`e.g. ${createModalType} Block B`}
            value={newLocationName}
            onChange={(e) => setNewLocationName(e.target.value)}
            required
            autoFocus
          />

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Who can submit complaints at this location?
            </label>
            <Select
              value={newPublicComplaintAccess}
              onChange={(e) => setNewPublicComplaintAccess(e.target.value)}
            >
              <option value="everyone">Option A: Allow complaints from everyone</option>
              <option value="location_only">Option B: Allow complaints only from their location</option>
            </Select>
            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
              {newPublicComplaintAccess === "location_only"
                ? "Restricted: Only eligible students belonging to or residing in this location can submit complaints."
                : "Open: Any authenticated student eligible to report complaints can submit an issue for this location."}
            </p>
          </div>

          {renderCentralDepartmentSelector(selectedDeptIds, setSelectedDeptIds)}

          <div className="mt-4 flex justify-end gap-3">
            <Button
              type="button"
              variant="subtle"
              onClick={() => setCreateModalType(null)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" className="font-bold px-6">
              Create Location
            </Button>
          </div>
        </form>
      </Modal>

      {/* Edit Modal */}
      <Modal
        open={!!editTarget}
        title="Edit Location"
        onClose={() => setEditTarget(null)}
      >
        <form onSubmit={handleEditSubmit} className="grid gap-5">
          <Input
            label="Location / Block Name"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            required
            autoFocus
          />
          <Select
            label="Location Type"
            value={editType}
            onChange={(e) => setEditType(e.target.value)}
            required
          >
            {(() => {
              const canonicalTypes = [
                "Hostel",
                "Academic Block",
                "Mess",
                "Student Activity Center",
                "Sports Complex",
                "Other / Not Sure",
              ];
              const fetchedTypes = (data?.locationTypes || []).map(
                (t) => t.type_name || t.name,
              );
              const allTypesList = Array.from(
                new Set([...canonicalTypes, ...fetchedTypes]),
              );
              return allTypesList.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ));
            })()}
          </Select>

          <div>
            <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
              Who can submit complaints at this location?
            </label>
            <Select
              value={editPublicComplaintAccess}
              onChange={(e) => setEditPublicComplaintAccess(e.target.value)}
            >
              <option value="everyone">Option A: Allow complaints from everyone</option>
              <option value="location_only">Option B: Allow complaints only from their location</option>
            </Select>
            <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
              {editPublicComplaintAccess === "location_only"
                ? "Restricted: Only eligible students belonging to or residing in this location can submit complaints."
                : "Open: Any authenticated student eligible to report complaints can submit an issue for this location."}
            </p>
          </div>

          {renderCentralDepartmentSelector(editDeptIds, setEditDeptIds)}

          <div className="mt-6 flex justify-end gap-3">
            <Button
              type="button"
              variant="subtle"
              onClick={() => setEditTarget(null)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" className="font-bold px-6">
              Save Changes
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        open={!!deleteTarget}
        title="Delete Location?"
        onClose={() => setDeleteTarget(null)}
      >
        <div className="text-sm text-slate-600 leading-normal">
          This action cannot be undone. To permanently delete the location{" "}
          <strong>{deleteTarget?.name}</strong>, type <strong>DELETE</strong> in
          the box below:
        </div>
        <input
          type="text"
          className="mt-4 h-11 w-full rounded-xl border border-slate-200 px-3 text-xs outline-none focus:border-red-500"
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
        title="Cannot Delete Location"
        onClose={() => setDeleteDependencyError("")}
      >
        <div className="text-sm text-slate-600 leading-normal">
          {deleteDependencyError}
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <Button
            variant="subtle"
            onClick={() => setDeleteDependencyError("")}
          >
            Cancel
          </Button>
          <Button variant="primary" onClick={handleArchiveFromError}>
            Archive Location Instead
          </Button>
        </div>
      </Modal>

      {/* Bulk Import Locations Modal (Part 3.2a) */}
      <BulkImportModal
        isOpen={showBulkImport}
        onClose={() => setShowBulkImport(false)}
        type="locations"
        onSuccess={() => {
          reload();
          setMessage("Locations imported successfully.");
        }}
      />
    </div>
  );
}
