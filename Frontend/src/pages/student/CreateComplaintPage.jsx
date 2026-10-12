import { useEffect, useMemo, useState, useRef } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft,
  Loader2,
  ClipboardCheck,
  AlertTriangle,
  Camera,
  Upload,
  Image as ImageIcon,
  X,
  Plus,
} from "lucide-react";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import Loader from "../../components/Loader.jsx";
import PageHeader from "../../components/PageHeader.jsx";
import Input from "../../components/Input.jsx";
import Select from "../../components/Select.jsx";
import Textarea from "../../components/Textarea.jsx";
import Toast from "../../components/Toast.jsx";
import Modal from "../../components/Modal.jsx";
import { useAuth } from "../../context/AuthContext.jsx";
import { useLanguage } from "../../context/LanguageContext.jsx";
import { complaintService } from "../../services/complaintService.js";
import { departmentService } from "../../services/departmentService.js";
import { locationService } from "../../services/locationService.js";
import { attachmentService } from "../../services/attachmentService.js";
import { getApiError } from "../../api/axios.js";

const QUICK_CATEGORIES = [
  { key: "electrical", label: "Electrical", icon: "⚡", keyword: "elec" },
  { key: "plumbing", label: "Plumbing", icon: "🚿", keyword: "plumb" },
  { key: "carpentry", label: "Carpentry", icon: "🚪", keyword: "carpent" },
  { key: "housekeeping", label: "Cleaning", icon: "🧹", keyword: "clean" },
  { key: "internet", label: "Wi-Fi", icon: "📶", keyword: "net" },
  { key: "mess", label: "Mess", icon: "🍽️", keyword: "mess" },
  { key: "general", label: "Other", icon: "📦", keyword: "maint" },
];

export default function CreateComplaintPage() {
  const { user } = useAuth();
  const { t } = useLanguage();
  const [departments, setDepartments] = useState([]);
  const [locations, setLocations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [affectedModalComplaint, setAffectedModalComplaint] = useState(null);
  const [affectedInfo, setAffectedInfo] = useState("");
  const [toast, setToast] = useState(null);

  // Photo Upload State
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [filePreviews, setFilePreviews] = useState([]);
  const [showUrlInput, setShowUrlInput] = useState(false);
  const galleryInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  const navigate = useNavigate();
  const [locSearch, setLocSearch] = useState("");
  const [recentPlaceIds, setRecentPlaceIds] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("cp_recent_places") || "[]");
    } catch {
      return [];
    }
  });

  const [outsideHostelConfirmed, setOutsideHostelConfirmed] = useState(false);
  const [selectedCategoryKey, setSelectedCategoryKey] = useState(null);

  const handleQuickCategory = (cat) => {
    setSelectedCategoryKey(cat.key);
    const deptList = availableDepartments.length > 0 ? availableDepartments : departments;
    const matchedDept = deptList.find(d => 
      d.name.toLowerCase().includes(cat.keyword) || 
      (d.complaint_types || []).some(t => t.toLowerCase().includes(cat.keyword))
    );
    if (matchedDept) {
      setValue("department_id", matchedDept.department_id);
      const matchedIssue = (matchedDept.complaint_types || []).find(t => 
        t.toLowerCase().includes(cat.keyword)
      ) || matchedDept.complaint_types?.[0] || cat.label;
      setValue("complaint_type", matchedIssue);
    } else {
      setValue("complaint_type", cat.label);
    }
  };

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm({
    defaultValues: { visibility_type: "Public" },
  });

  const selectedDepartmentId = watch("department_id");
  const titleVal = watch("title");
  const locationVal = watch("location_id");
  const visibilityVal = watch("visibility_type");

  // Pre-select student's own place if available
  useEffect(() => {
    if (user?.location_id && !locationVal) {
      setValue("location_id", user.location_id);
    }
  }, [user, locationVal, setValue]);

  // Derive dynamic options solely from active backend database configuration
  const availableDepartments = useMemo(() => {
    if (!locationVal) return [];

    // Resolve location_id and location_type (supports both ID and name)
    const locObj = (locations || []).find(l => l.location_id === locationVal || l.name === locationVal);
    const locId = locObj ? locObj.location_id : locationVal;
    const locType = locObj ? (locObj.location_type || locObj.name) : locationVal;

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
  }, [locationVal, departments, locations]);

  // Check if student is filing for a hostel outside their own
  const isOutsideHostel = useMemo(() => {
    if (!user?.location_id || !locationVal || user.location_id === locationVal) return false;
    const userLoc = (locations || []).find(l => l.location_id === user.location_id);
    const selectedLoc = (locations || []).find(l => l.location_id === locationVal);
    if (!userLoc || !selectedLoc) return false;
    const isUserHostel = (userLoc.location_type || "").toLowerCase().includes("hostel") || userLoc.name.toLowerCase().includes("hostel");
    const isSelectedHostel = (selectedLoc.location_type || "").toLowerCase().includes("hostel") || selectedLoc.name.toLowerCase().includes("hostel");
    return isUserHostel && isSelectedHostel;
  }, [user, locationVal, locations]);

  // Group active locations by Location Type for clean UI selection, filtering by locSearch
  const groupedLocations = useMemo(() => {
    const types = [
      "Hostel",
      "Academic Block",
      "Mess",
      "Student Activity Center",
      "Sports Complex",
      "Other / Not Sure",
    ];
    const getLocationType = (loc) => {
      if (loc.location_type) return loc.location_type;
      const name = loc.name.toLowerCase();
      if (name.includes("hostel")) return "Hostel";
      if (name.includes("academic")) return "Academic Block";
      if (name.includes("mess")) return "Mess";
      if (name.includes("activity") || name.includes("sac")) return "Student Activity Center";
      if (name.includes("sports")) return "Sports Complex";
      return "Other / Not Sure";
    };

    const s = locSearch.trim().toLowerCase();
    return types.map(t => {
      let filtered = (locations || []).filter(l => {
        const matchesType = getLocationType(l) === t;
        const matchesSearch = !s || l.name.toLowerCase().includes(s);
        return matchesType && matchesSearch;
      });
      return {
        type_name: t,
        locations: filtered,
      };
    }).filter(g => g.locations.length > 0);
  }, [locations, locSearch]);

  const availableIssues = useMemo(() => {
    if (!locationVal || !selectedDepartmentId) return [];

    // Find selected department object in available list
    const deptObj = availableDepartments.find(
      d => d.department_id === selectedDepartmentId || d.id === selectedDepartmentId
    );
    if (!deptObj) return [];

    // Return issues configured in the department database record
    return deptObj.complaint_types || [];
  }, [locationVal, selectedDepartmentId, availableDepartments]);

  useEffect(() => {
    async function loadOptions() {
      try {
        const [departmentResponse, locationResponse] = await Promise.all([
          departmentService.list().catch(() => ({ data: [] })),
          locationService.list().catch(() => ({ data: [] })),
        ]);
        setDepartments(departmentResponse.data || []);
        setLocations(locationResponse.data || []);
      } catch (err) {
        setError(
          getApiError(err, "Unable to load complaint options."),
        );
      } finally {
        setLoading(false);
      }
    }
    loadOptions();
  }, []);

  // Duplicate Suggestions Search
  useEffect(() => {
    if (
      visibilityVal === "Public" &&
      locationVal &&
      titleVal &&
      titleVal.trim().length >= 3
    ) {
      const delayDebounceFn = setTimeout(async () => {
        try {
          const res = await complaintService.suggestions(
            locationVal,
            titleVal.trim(),
          );
          setSuggestions(res.data || []);
        } catch (err) {
          setSuggestions([]);
        }
      }, 300);
      return () => clearTimeout(delayDebounceFn);
    } else {
      setSuggestions([]);
    }
  }, [titleVal, locationVal, visibilityVal]);

  const handleMarkAffectedSubmit = async () => {
    if (!affectedModalComplaint) return;
    try {
      await complaintService.markAffected(affectedModalComplaint.complaint_id, {
        info: affectedInfo,
      });
      setToast({
        type: "success",
        message:
          "Registered as affected student. Affected student count updated!",
      });
      setAffectedModalComplaint(null);
      setAffectedInfo("");
      navigate(`/complaints/${affectedModalComplaint.complaint_id}`);
    } catch (err) {
      setToast({
        type: "error",
        message: getApiError(err, "Could not mark as affected."),
      });
    }
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;

    if (selectedFiles.length + files.length > 5) {
      setToast({
        type: "error",
        message: "Maximum of 5 photos allowed per complaint.",
      });
      return;
    }

    const validFiles = [];
    const newPreviews = [...filePreviews];

    files.forEach((file) => {
      if (file.size > 5 * 1024 * 1024) {
        setToast({
          type: "error",
          message: `File "${file.name}" exceeds 5 MB limit.`,
        });
        return;
      }
      const isPdf = file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");
      if (!file.type.startsWith("image/") && !isPdf) {
        setToast({
          type: "error",
          message: `File "${file.name}" is not a supported format (JPG, PNG, PDF allowed).`,
        });
        return;
      }
      validFiles.push(file);
      newPreviews.push({
        name: file.name,
        size: (file.size / 1024).toFixed(1) + " KB",
        url: isPdf ? null : URL.createObjectURL(file),
        isPdf,
        file,
      });
    });

    setSelectedFiles((prev) => [...prev, ...validFiles]);
    setFilePreviews(newPreviews);
  };

  const removeFile = (index) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
    setFilePreviews((prev) => prev.filter((_, i) => i !== index));
  };

  const onSubmit = async (values) => {
    setError("");
    try {
      const isUrgent = !!values.is_urgent;
      const payload = {
        ...values,
        category: values.complaint_type,
        visibility_type: values.visibility_type || "Public",
        priority: isUrgent ? "High" : (values.priority || "Normal"),
        is_urgent: isUrgent,
        exact_spot: values.exact_spot?.trim() || null,
      };

      // Save to recent places
      try {
        const prev = JSON.parse(localStorage.getItem("cp_recent_places") || "[]");
        const next = [values.location_id, ...prev.filter(id => id !== values.location_id)].slice(0, 5);
        localStorage.setItem("cp_recent_places", JSON.stringify(next));
      } catch {}

      const response = await complaintService.create(payload);
      const complaintId = response.data.complaint_id;

      // Upload gallery/camera files if selected
      if (selectedFiles.length > 0) {
        try {
          await attachmentService.upload(complaintId, selectedFiles, "Additional");
        } catch (uploadErr) {
          console.error("Photo upload error:", uploadErr);
        }
      }

      navigate(`/complaints/${complaintId}`);
    } catch (err) {
      setError(getApiError(err, "Unable to submit complaint."));
    }
  };

  return (
    <div className="grid gap-6 max-w-2xl">
      {toast && (
        <Toast
          tone={toast.type}
          message={toast.message}
          onClose={() => setToast(null)}
        />
      )}

      <div>
        <Link
          to="/"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to dashboard
        </Link>
        <PageHeader
          title="Create New Complaint"
          description="Follow the guided workflow to report your issue. Use 'Other / Not Sure' if you are uncertain."
        />
      </div>

      <Card>
        {loading ? (
          <Loader label="Loading complaint form..." variant="skeleton" />
        ) : (
          <form className="grid gap-5" onSubmit={handleSubmit(onSubmit)}>
            {/* Step 1 - Select Location */}
            <div className="space-y-3">
              {/* Recent places pills */}
              {recentPlaceIds.length > 0 && (
                <div>
                  <span className="text-[11px] font-semibold text-slate-500 dark:text-slate-400 block mb-1.5">
                    📍 You recently reported from:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {recentPlaceIds.map((rId) => {
                      const rLoc = locations.find((l) => l.location_id === rId);
                      if (!rLoc) return null;
                      return (
                        <button
                          key={rId}
                          type="button"
                          onClick={() => {
                            setValue("location_id", rId);
                            setValue("department_id", "");
                            setValue("complaint_type", "");
                          }}
                          className={`px-2.5 py-1 text-xs rounded-lg border font-medium transition-colors cursor-pointer ${
                            locationVal === rId
                              ? "bg-primary text-white border-primary shadow-xs"
                              : "bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 border-slate-200 dark:border-slate-700 hover:bg-slate-200 dark:hover:bg-slate-700"
                          }`}
                        >
                          {rLoc.name}
                        </button>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Location search filter */}
              <input
                type="text"
                placeholder="Search locations (e.g. Mess, Block A, Room 204)..."
                value={locSearch}
                onChange={(e) => setLocSearch(e.target.value)}
                className="h-9 w-full rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 px-3 text-xs text-slate-900 dark:text-slate-100 placeholder-slate-400 focus:border-primary focus:ring-1 focus:ring-primary outline-none"
              />

              <Select
                label="Step 1 — Select Location"
                error={errors.location_id?.message}
                {...register("location_id", {
                  required: "Location is required.",
                  onChange: () => {
                    setValue("department_id", "");
                    setValue("complaint_type", "");
                  },
                })}
              >
                <option value="">Choose Location</option>
                {groupedLocations.map((group) => (
                  <optgroup key={group.type_name} label={group.type_name}>
                    {group.locations.map((loc) => (
                      <option key={loc.location_id} value={loc.location_id}>
                        {loc.name}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </Select>

              {/* Outside hostel confirmation banner */}
              {isOutsideHostel && !outsideHostelConfirmed && (
                <div className="p-3 rounded-xl border border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/30 flex items-center justify-between gap-3 text-xs">
                  <div className="text-amber-800 dark:text-amber-300">
                    <span className="font-bold">⚠️ Different Location:</span> This is{" "}
                    <strong>{locations.find((l) => l.location_id === locationVal)?.name || locationVal}</strong>. You live in{" "}
                    <strong>{locations.find((l) => l.location_id === user?.location_id)?.name || user?.location_id}</strong>. Report for {locations.find((l) => l.location_id === locationVal)?.name || locationVal}?
                  </div>
                  <button
                    type="button"
                    onClick={() => setOutsideHostelConfirmed(true)}
                    className="shrink-0 px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white font-semibold rounded-lg text-xs cursor-pointer shadow-xs"
                  >
                    Yes, continue
                  </button>
                </div>
              )}

              {/* Exact Spot input */}
              <div>
                <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">
                  Exact Spot (Optional)
                </label>
                <input
                  type="text"
                  placeholder="e.g. Floor 2, Right bathroom, 2nd tap from door, Room 204..."
                  className="h-10 w-full rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 px-3.5 text-xs font-medium text-slate-900 dark:text-slate-100 outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  {...register("exact_spot")}
                />
                <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
                  Helps the coordinator locate the issue immediately without having to call or ask.
                </p>
              </div>
            </div>

            {/* Quick Category Buttons */}
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">
                Quick Category (One-Tap Pick)
              </label>
              <div className="grid grid-cols-4 sm:grid-cols-7 gap-2">
                {QUICK_CATEGORIES.map((cat) => (
                  <button
                    key={cat.key}
                    type="button"
                    onClick={() => handleQuickCategory(cat)}
                    className={`flex flex-col items-center justify-center p-2 rounded-xl border transition-all text-center cursor-pointer ${
                      selectedCategoryKey === cat.key
                        ? "border-primary bg-primary/10 text-primary font-bold shadow-xs scale-102"
                        : "border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800"
                    }`}
                  >
                    <span className="text-xl mb-1">{cat.icon}</span>
                    <span className="text-[10px] font-semibold truncate w-full">{cat.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Step 2 - Select Department */}
            <Select
              label="Step 2 — Select Department"
              error={errors.department_id?.message}
              disabled={!locationVal}
              {...register("department_id", {
                required: "Department is required.",
                onChange: () => {
                  setValue("complaint_type", "");
                },
              })}
            >
              <option value="">
                {locationVal ? "Choose Department" : "Select Location First..."}
              </option>
              {availableDepartments.map((dept) => (
                <option key={dept.department_id} value={dept.department_id}>
                  {dept.name}
                </option>
              ))}
            </Select>

            {/* Step 3 - Select Issue */}
            <Select
              label="Step 3 — Select Issue"
              error={errors.complaint_type?.message}
              disabled={!selectedDepartmentId}
              {...register("complaint_type", {
                required: "Issue type is required.",
              })}
            >
              <option value="">
                {selectedDepartmentId ? "Choose Issue" : "Select Department First..."}
              </option>
              {availableIssues.map((issue, idx) => (
                <option key={`${issue}-${idx}`} value={issue}>
                  {issue}
                </option>
              ))}
            </Select>

            {/* Step 4 - Select Visibility */}
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">
                Step 4 — Visibility
              </label>
              <div className="flex gap-4">
                <label className="flex items-center gap-2 cursor-pointer border rounded-xl p-3 flex-1 border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors">
                  <input
                    type="radio"
                    value="Public"
                    {...register("visibility_type")}
                  />
                  <div>
                    <div className="font-bold text-xs text-slate-900 dark:text-slate-100">
                      🌍 Public
                    </div>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400">
                      Visible to campus, duplicate check enabled
                    </div>
                  </div>
                </label>
                <label className="flex items-center gap-2 cursor-pointer border rounded-xl p-3 flex-1 border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800/60 transition-colors">
                  <input
                    type="radio"
                    value="Private"
                    {...register("visibility_type")}
                  />
                  <div>
                    <div className="font-bold text-xs text-slate-900 dark:text-slate-100">
                      🔒 Private
                    </div>
                    <div className="text-[10px] text-slate-500 dark:text-slate-400">
                      Only visible to you and assigned staff
                    </div>
                  </div>
                </label>
              </div>
            </div>

            {/* Step 5 - Title & Description */}
            <div>
              <label className="block text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-1.5">
                Step 5 — Complaint Title
              </label>
              <input
                type="text"
                placeholder="Brief summary of the issue (e.g. Power Failure in Room A-204)..."
                className="h-11 w-full rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 px-3.5 text-xs font-medium text-slate-900 dark:text-slate-100 outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                {...register("title", { required: "Title is required." })}
              />
              {errors.title && (
                <p className="mt-1 text-xs text-rose-500 font-medium">
                  {errors.title.message}
                </p>
              )}
            </div>

            {/* Duplicate Complaint Detection */}
            {visibilityVal === "Public" && suggestions.length > 0 && (
              <div className="border border-amber-200 bg-amber-50/50 rounded-2xl p-4">
                <div className="flex items-center gap-2 text-amber-800 font-bold text-sm mb-2">
                  <AlertTriangle className="h-5 w-5 text-amber-600" /> ⚠ Similar
                  Complaint Found
                </div>
                <div className="space-y-3">
                  {suggestions.map((s) => (
                    <div
                      key={s.complaint_id}
                      className="bg-white border border-amber-100 rounded-xl p-3 text-xs shadow-xs"
                    >
                      <div className="flex justify-between items-start font-bold text-slate-900">
                        <span>{s.title}</span>
                        <span className="text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full text-[10px]">
                          {s.status}
                        </span>
                      </div>
                      <div className="text-slate-500 mt-1">
                        Location: {s.location_id || "Campus"} • Affected
                        Students: <strong>{s.affected_count || 1}</strong>
                      </div>
                      <div className="mt-3 flex gap-2">
                        <button
                          type="button"
                          onClick={() => setAffectedModalComplaint(s)}
                          className="px-3 py-1.5 bg-primary text-white font-bold rounded-lg text-xs hover:bg-primary/90"
                        >
                          I'm Also Affected
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div>
              <Textarea
                label="Detailed Description"
                placeholder="Provide exact details of the issue so coordinators can fix it quickly..."
                error={errors.description?.message}
                {...register("description", {
                  required: "Description is required.",
                })}
              />
              <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400 flex items-center gap-1">
                <span>💡 Tip:</span> Use the 🎤 on your keyboard to speak instead of typing.
              </p>
            </div>

            {/* Urgent Priority Flag */}
            <div className="flex items-start gap-3 p-3.5 rounded-xl border border-rose-200/80 dark:border-rose-900/40 bg-rose-50/50 dark:bg-rose-950/20">
              <input
                type="checkbox"
                id="is_urgent"
                className="mt-0.5 h-4 w-4 rounded border-rose-300 text-rose-600 focus:ring-rose-500 cursor-pointer"
                {...register("is_urgent")}
              />
              <label htmlFor="is_urgent" className="text-xs text-rose-900 dark:text-rose-200 cursor-pointer select-none">
                <span className="font-bold block">Mark as Urgent (High Priority)</span>
                <span className="text-[11px] text-rose-700/80 dark:text-rose-300/80">
                  Sets priority to High. Check this if the issue poses an immediate safety hazard, power failure, or campus outage.
                </span>
              </label>
            </div>

            {/* Step 6 — Photo Upload (Gallery / Camera / URL) */}
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                Step 6 — Upload Photos / Attachments (Optional)
              </label>

              {/* Hidden file inputs */}
              <input
                type="file"
                ref={galleryInputRef}
                accept="image/jpeg,image/png,image/jpg,application/pdf"
                multiple
                className="hidden"
                onChange={handleFileChange}
              />
              <input
                type="file"
                ref={cameraInputRef}
                accept="image/*"
                capture="environment"
                className="hidden"
                onChange={handleFileChange}
              />

              {/* Upload Buttons */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
                <button
                  type="button"
                  onClick={() => galleryInputRef.current?.click()}
                  className="flex items-center justify-center gap-2 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50/70 dark:bg-slate-800/40 p-3 text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 hover:border-primary transition-all cursor-pointer"
                >
                  <Upload className="h-4 w-4 text-primary" />
                  Choose from Gallery / Files
                </button>

                <button
                  type="button"
                  onClick={() => cameraInputRef.current?.click()}
                  className="flex items-center justify-center gap-2 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50/70 dark:bg-slate-800/40 p-3 text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 hover:border-primary transition-all cursor-pointer"
                >
                  <Camera className="h-4 w-4 text-primary" />
                  Take Photo with Camera
                </button>
              </div>

              {/* Previews Grid */}
              {filePreviews.length > 0 && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-3">
                  {filePreviews.map((preview, idx) => (
                    <div
                      key={idx}
                      className="relative group rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 p-2 shadow-xs flex flex-col items-center"
                    >
                      <img
                        src={preview.url}
                        alt={preview.name}
                        className="h-20 w-full object-cover rounded-lg mb-1.5"
                      />
                      <span className="text-[10px] font-semibold text-slate-700 dark:text-slate-200 truncate w-full text-center">
                        {preview.name}
                      </span>
                      <span className="text-[9px] text-slate-400 dark:text-slate-500">
                        {preview.size}
                      </span>
                      <button
                        type="button"
                        onClick={() => removeFile(idx)}
                        className="absolute -top-1.5 -right-1.5 rounded-full bg-rose-600 p-1 text-white shadow-md hover:bg-rose-700 transition-colors cursor-pointer"
                        title="Remove photo"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* URL Fallback toggle */}
              <div className="text-right">
                <button
                  type="button"
                  onClick={() => setShowUrlInput(!showUrlInput)}
                  className="text-[11px] font-semibold text-primary hover:underline cursor-pointer"
                >
                  {showUrlInput ? "Hide Photo URL field" : "+ Or paste image URL"}
                </button>
              </div>

              {showUrlInput && (
                <input
                  type="text"
                  placeholder="https://example.com/photo.jpg or image link"
                  className="mt-2 h-10 w-full rounded-xl border border-slate-200/80 dark:border-slate-800 bg-white dark:bg-slate-900 px-3.5 text-xs font-medium text-slate-900 dark:text-slate-100 outline-none focus:border-primary focus:ring-1 focus:ring-primary"
                  {...register("attachment_url")}
                />
              )}
            </div>

            {error && (
              <Toast
                message={error}
                tone="danger"
                onClose={() => setError("")}
              />
            )}

            <Button
              type="submit"
              disabled={isSubmitting}
              className="font-bold py-2.5 flex items-center justify-center gap-1.5"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Submitting...
                </>
              ) : (
                <>
                  <ClipboardCheck className="h-4.5 w-4.5" />
                  Submit Complaint
                </>
              )}
            </Button>
          </form>
        )}
      </Card>

      {/* I'm Also Affected Modal */}
      {affectedModalComplaint && (
        <Modal
          isOpen={true}
          onClose={() => setAffectedModalComplaint(null)}
          title="I'm Also Affected"
        >
          <div className="space-y-4">
            <p className="text-xs text-slate-600">
              Linking your report to{" "}
              <strong>{affectedModalComplaint.title}</strong> will increase the
              affected student count automatically instead of creating a
              duplicate ticket.
            </p>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Additional Information (Optional)
              </label>
              <textarea
                value={affectedInfo}
                onChange={(e) => setAffectedInfo(e.target.value)}
                placeholder="e.g. Same issue in my room A-204 as well..."
                className="w-full rounded-xl border border-slate-300 p-2.5 text-xs"
                rows={3}
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setAffectedModalComplaint(null)}
                className="rounded-xl px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleMarkAffectedSubmit}
                className="rounded-xl bg-primary px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-primary/90"
              >
                Submit Affected Report
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
