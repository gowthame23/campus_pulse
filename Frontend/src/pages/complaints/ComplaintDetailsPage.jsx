import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Calendar,
  MapPin,
  User,
  History,
  ShieldAlert,
  Wrench,
  CheckCircle2,
  HelpCircle,
  AlertCircle,
  FileText,
  Trash2,
  Plus,
  Tag,
  Edit,
  Clock,
  Check,
  Building,
  Eye,
  MessageSquare,
  AlertTriangle,
} from "lucide-react";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card from "../../components/Card.jsx";
import ConfirmDialog from "../../components/ConfirmDialog.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import Modal from "../../components/Modal.jsx";
import Select from "../../components/Select.jsx";
import Textarea from "../../components/Textarea.jsx";
import Toast from "../../components/Toast.jsx";
import { getApiError } from "../../api/axios.js";
import { useAuth } from "../../context/AuthContext.jsx";
import { complaintService } from "../../services/complaintService.js";
import { attachmentService } from "../../services/attachmentService.js";
import { departmentService } from "../../services/departmentService.js";
import { locationService } from "../../services/locationService.js";
import { userService } from "../../services/userService.js";
import { COMPLAINT_STATUS, ROLES } from "../../utils/constants.js";
import { formatDate } from "../../utils/dateFormatter.js";
import { getStatusTone, getSlaTone } from "../../utils/statusColor.js";

const LIFECYCLE_STEPS = [
  { label: "Submitted", desc: "Report filed" },
  { label: "Assigned", desc: "Staff assigned" },
  { label: "In Progress", desc: "Work underway" },
  { label: "Resolved", desc: "Work completed" },
  { label: "Verification", desc: "Student review" },
  { label: "Closed", desc: "Completed" },
];

const getLifecycleStepIndex = (status) => {
  if (!status) return 0;
  const s = status.toLowerCase();
  if (s.startsWith("closed")) return 5;
  if (s.includes("verification")) return 4;
  if (s.includes("resolved")) return 3;
  if (s.includes("progress")) return 2;
  if (s.includes("assigned")) return 1;
  return 0; // Submitted, Pending, Awaiting Coordinator Assignment, Reopened
};

export default function ComplaintDetailsPage() {
  const { complaintId } = useParams();
  const { user } = useAuth();
  const [complaint, setComplaint] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [locations, setLocations] = useState([]);
  const [coordinators, setCoordinators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [confirmAction, setConfirmAction] = useState(null);
  const {
    register,
    handleSubmit,
    reset,
    formState: { isSubmitting, errors },
  } = useForm();

  const [comments, setComments] = useState([]);
  const [commentText, setCommentText] = useState("");
  const [submittingComment, setSubmittingComment] = useState(false);
  const [selectedPriority, setSelectedPriority] = useState("Medium");
  const [priorityReason, setPriorityReason] = useState("");
  const [updatingPriority, setUpdatingPriority] = useState(false);

  const [attachments, setAttachments] = useState([]);
  const [attachmentUrls, setAttachmentUrls] = useState({});
  const [uploadCategory, setUploadCategory] = useState("Before Repair");

  const navigate = useNavigate();

  // Student Edit / Delete state
  const [showEditModal, setShowEditModal] = useState(false);
  const [editLocation, setEditLocation] = useState("");
  const [editDepartment, setEditDepartment] = useState("");
  const [editType, setEditType] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editSubmitting, setEditSubmitting] = useState(false);

  const isOwner =
    user &&
    complaint &&
    (user.user_id === complaint.created_by ||
      user.id === complaint.created_by ||
      user.email === complaint.created_by);
  const canStudentEditOrDelete =
    isOwner &&
    (user?.role === ROLES.STUDENT || (user?.role || "").toLowerCase() === "student") &&
    complaint?.status === "Submitted";

  const availableEditDepartments = useMemo(() => {
    if (!editLocation) return [];

    const locObj = (locations || []).find(
      (l) => l.location_id === editLocation || l.name === editLocation,
    );
    const locId = locObj ? locObj.location_id : editLocation;
    const locType = locObj ? locObj.location_type || locObj.name : editLocation;

    const typeToTemplateId = {
      Hostel: "LOC_HOSTEL_A",
      "Academic Block": "LOC_ACADEMIC",
      Mess: "LOC_MESS",
      "Student Activity Center": "LOC_SAC",
      "Sports Complex": "LOC_SPORTS",
      "Other / Not Sure": "LOC_OTHER",
    };
    const templateId =
      typeToTemplateId[locType] || (locObj ? typeToTemplateId[locObj.name] : null);

    return (departments || []).filter(
      (d) =>
        d.location_id === locId ||
        d.location_id === locType ||
        (templateId && d.location_id === templateId),
    );
  }, [editLocation, departments, locations]);

  const availableEditIssues = useMemo(() => {
    if (!editLocation || !editDepartment) return [];

    const deptObj = availableEditDepartments.find(
      (d) =>
        d.department_id === editDepartment ||
        d.id === editDepartment ||
        d.name === editDepartment,
    );
    if (!deptObj) return [];

    return deptObj.complaint_types || [];
  }, [editLocation, editDepartment, availableEditDepartments]);

  const openEditModal = () => {
    if (!complaint) return;

    const locMatch = (locations || []).find(
      (l) => l.location_id === complaint.location_id || l.name === complaint.location_id,
    );
    const locVal = locMatch ? locMatch.location_id : complaint.location_id || "";

    const deptMatch = (departments || []).find(
      (d) => d.department_id === complaint.department_id || d.name === complaint.department_id,
    );
    const deptVal = deptMatch ? deptMatch.department_id : complaint.department_id || "";

    setEditLocation(locVal);
    setEditDepartment(deptVal);
    setEditType(complaint.category || complaint.complaint_type || "");
    setEditDescription(complaint.description || "");
    setShowEditModal(true);
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!editDescription.trim()) {
      setError("Description is required.");
      return;
    }
    setEditSubmitting(true);
    setError("");
    try {
      const payload = {
        location_id: editLocation,
        department_id: editDepartment,
        complaint_type: editType,
        category: editType,
        description: editDescription.trim(),
      };
      await complaintService.update(complaintId, payload);
      setMessage("Complaint updated successfully!");
      setShowEditModal(false);
      load();
    } catch (err) {
      setError(getApiError(err, "Failed to update complaint."));
    } finally {
      setEditSubmitting(false);
    }
  };

  const [showDeletionModal, setShowDeletionModal] = useState(false);
  const [deletionReasonInput, setDeletionReasonInput] = useState("");
  const [submittingDeletionRequest, setSubmittingDeletionRequest] = useState(false);

  const canDirectDelete = user && [ROLES.ADMINISTRATOR, ROLES.APP_MANAGER].includes(user.role);
  const canRequestDelete =
    user && [ROLES.COORDINATOR, ROLES.LOCATION_IN_CHARGE].includes(user.role);
  const canDeleteTicket = canDirectDelete || canRequestDelete || canStudentEditOrDelete;

  const handleDeleteComplaint = () => {
    if (canDirectDelete || canStudentEditOrDelete) {
      askConfirm({
        title: "Delete Complaint",
        message:
          "Are you sure you want to delete this complaint? This complaint will be soft-deleted.",
        confirmLabel: "Delete Complaint",
        tone: "danger",
        action: async () => {
          try {
            await complaintService.delete(complaintId);
            navigate("/complaints", { replace: true });
          } catch (err) {
            setError(getApiError(err, "Failed to delete complaint."));
          }
        },
      });
    } else if (canRequestDelete) {
      setDeletionReasonInput("");
      setShowDeletionModal(true);
    }
  };

  const handleDeletionRequestSubmit = async (e) => {
    e.preventDefault();
    if (!deletionReasonInput.trim()) {
      setError("A reason for deletion is required.");
      return;
    }
    setSubmittingDeletionRequest(true);
    setError("");
    try {
      await complaintService.requestDeletion(complaintId, deletionReasonInput.trim());
      setMessage("Deletion request submitted to App Manager for approval.");
      setShowDeletionModal(false);
      load();
    } catch (err) {
      setError(getApiError(err, "Failed to submit deletion request."));
    } finally {
      setSubmittingDeletionRequest(false);
    }
  };

  const handleApproveDeletion = async () => {
    askConfirm({
      title: "Approve Complaint Deletion",
      message: `Confirm deletion of complaint ${complaintId} requested by ${complaint?.deletion_requested_name || "staff"}?`,
      confirmLabel: "Approve & Delete",
      tone: "danger",
      action: async () => {
        try {
          await complaintService.approveDeletion(complaintId);
          navigate("/complaints", { replace: true });
        } catch (err) {
          setError(getApiError(err, "Failed to approve deletion."));
        }
      },
    });
  };

  const handleRejectDeletion = async () => {
    try {
      await complaintService.rejectDeletion(complaintId);
      setMessage("Deletion request rejected.");
      load();
    } catch (err) {
      setError(getApiError(err, "Failed to reject deletion request."));
    }
  };

  const canCoordinate = [
    ROLES.COORDINATOR,
    ROLES.APP_MANAGER,
    ROLES.ADMINISTRATOR,
  ].includes(user?.role);
  const canVerify =
    [ROLES.STUDENT, ROLES.LOCATION_IN_CHARGE].includes(user?.role) &&
    complaint?.status === COMPLAINT_STATUS.WAITING_VERIFICATION;
  const department = useMemo(
    () =>
      departments.find(
        (item) => item.department_id === complaint?.department_id,
      ),
    [departments, complaint],
  );
  const location = useMemo(
    () => locations.find((item) => item.location_id === complaint?.location_id),
    [locations, complaint],
  );

  const canChangePriority =
    user &&
    (user.role === ROLES.ADMINISTRATOR ||
      user.role === ROLES.APP_MANAGER ||
      user.role === ROLES.COORDINATOR ||
      user.role === ROLES.LOCATION_IN_CHARGE);

  async function load() {
    setLoading(true);
    setError("");
    try {
      const [
        complaintResponse,
        departmentResponse,
        locationResponse,
        commentsResponse,
        attachmentsResponse,
      ] = await Promise.all([
        complaintService.getById(complaintId),
        departmentService.list().catch(() => ({ data: [] })),
        locationService.list().catch(() => ({ data: [] })),
        complaintService.getComments(complaintId).catch(() => ({ data: [] })),
        attachmentService.list(complaintId).catch(() => ({ data: [] })),
      ]);
      setComplaint(complaintResponse.data);
      setDepartments(departmentResponse.data);
      setLocations(locationResponse.data);
      setComments(commentsResponse.data);
      setAttachments(attachmentsResponse.data);
      setSelectedPriority(complaintResponse.data.priority || "Medium");
      if ([ROLES.APP_MANAGER, ROLES.ADMINISTRATOR].includes(user?.role)) {
        const usersResponse = await userService.list(ROLES.COORDINATOR);
        setCoordinators(usersResponse.data);
      }
    } catch (err) {
      setError(getApiError(err, "Unable to load complaint."));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [complaintId, user?.role]);

  useEffect(() => {
    let active = true;
    const loadedUrls = {};

    Promise.all(
      attachments.map(async (attachment) => {
        try {
          const response = await attachmentService.download(
            complaintId,
            attachment.attachment_id,
          );
          const blobUrl = URL.createObjectURL(response.data);
          if (active) {
            loadedUrls[attachment.attachment_id] = blobUrl;
          } else {
            URL.revokeObjectURL(blobUrl);
          }
        } catch {
          // Keep unavailable attachments without a preview URL.
        }
      }),
    ).then(() => {
      if (active) {
        setAttachmentUrls(loadedUrls);
      } else {
        Object.values(loadedUrls).forEach((url) => URL.revokeObjectURL(url));
      }
    });

    return () => {
      active = false;
      Object.values(loadedUrls).forEach((url) => URL.revokeObjectURL(url));
    };
  }, [attachments, complaintId]);

  const runAction = async (action, success) => {
    setMessage("");
    setError("");
    try {
      const response = await action();
      setComplaint(response.data);
      reset();
      setMessage(success);
    } catch (err) {
      setError(getApiError(err, "Action failed."));
    }
  };

  const handleTakeComplaint = async () => {
    setMessage("");
    setError("");
    try {
      const response = await complaintService.take(complaintId);
      setComplaint(response.data);
      setMessage("Complaint taken successfully.");
    } catch (err) {
      setError(getApiError(err, "Action failed."));
    }
  };

  const [isCommentInternal, setIsCommentInternal] = useState(false);
  const [escalateReason, setEscalateReason] = useState("");
  const [escalating, setEscalating] = useState(false);

  const canEscalate =
    user &&
    [ROLES.COORDINATOR, ROLES.LOCATION_IN_CHARGE, ROLES.APP_MANAGER].includes(
      user.role,
    ) &&
    !["Closed", "Closed (Auto Closed)"].includes(complaint?.status);

  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    if (!commentText.trim()) return;
    setSubmittingComment(true);
    setError("");
    try {
      const response = await complaintService.addComment(
        complaintId,
        commentText.trim(),
        isCommentInternal,
      );
      setComments((prev) => [...prev, response.data]);
      setCommentText("");
      setIsCommentInternal(false);
    } catch (err) {
      setError(getApiError(err, "Failed to submit comment."));
    } finally {
      setSubmittingComment(false);
    }
  };

  const handleEscalateSubmit = async (e) => {
    e.preventDefault();
    if (!escalateReason.trim()) {
      setError("A reason is required to escalate.");
      return;
    }
    setEscalating(true);
    setMessage("");
    setError("");
    try {
      const response = await complaintService.escalate(
        complaintId,
        escalateReason.trim(),
      );
      setComplaint(response.data);
      setEscalateReason("");
      setMessage("Complaint escalated successfully.");
    } catch (err) {
      setError(getApiError(err, "Failed to escalate complaint."));
    } finally {
      setEscalating(false);
    }
  };

  const [uploadingFile, setUploadingFile] = useState(false);

  const canUploadAttachments = useMemo(() => {
    if (!user || !complaint) return false;
    const uRole = (user.role || "").toLowerCase();

    // Status Closed: read-only
    if (["Closed", "Closed (Auto Closed)"].includes(complaint.status))
      return false;

    if (uRole === "student") {
      // Student can upload in Submitted, In Progress, Reopened statuses
      return complaint.created_by === user.user_id;
    }
    if (uRole === "coordinator") {
      // Coordinator can upload if assigned to the complaint
      return complaint.assigned_to === user.user_id;
    }
    return false;
  }, [user, complaint]);

  const handleAttachmentUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    if (files.length > 5) {
      setError("Maximum of 5 files can be uploaded at once.");
      return;
    }

    setUploadingFile(true);
    setError("");
    setMessage("");

    try {
      const cat =
        user.role.toLowerCase() === "student" ? "Additional" : uploadCategory;
      const res = await attachmentService.upload(complaintId, files, cat);
      setAttachments((prev) => [...prev, ...res.data]);
      setMessage("Files uploaded successfully.");

      // Reload complaint to get updated history timeline
      const compRes = await complaintService.getById(complaintId);
      setComplaint(compRes.data);
    } catch (err) {
      setError(getApiError(err, "Failed to upload attachments."));
    } finally {
      setUploadingFile(false);
      e.target.value = "";
    }
  };

  const handleAttachmentDelete = async (attachmentId) => {
    setError("");
    setMessage("");
    try {
      await attachmentService.delete(complaintId, attachmentId);
      setAttachments((prev) =>
        prev.filter((a) => a.attachment_id !== attachmentId),
      );
      setMessage("Image deleted successfully.");

      // Reload complaint to get updated history timeline
      const compRes = await complaintService.getById(complaintId);
      setComplaint(compRes.data);
    } catch (err) {
      setError(getApiError(err, "Failed to delete image."));
    }
  };

  const handlePriorityUpdate = async (e) => {
    e.preventDefault();
    if (!priorityReason.trim()) {
      setError("A reason is required to change priority.");
      return;
    }
    setUpdatingPriority(true);
    setMessage("");
    setError("");
    try {
      const response = await complaintService.changePriority(
        complaintId,
        selectedPriority,
        priorityReason.trim(),
      );
      setComplaint(response.data);
      setPriorityReason("");
      setMessage("Priority updated successfully.");
    } catch (err) {
      setError(getApiError(err, "Failed to update priority."));
    } finally {
      setUpdatingPriority(false);
    }
  };

  const askConfirm = (config) => setConfirmAction(config);
  const resolveComplaint = (values) => {
    const afterRepair = attachments.filter(
      (a) => a.category === "After Repair",
    );
    if (afterRepair.length === 0 && !values.notes?.trim()) {
      setError(
        "Resolution Summary notes are mandatory when no 'After Repair' image is uploaded.",
      );
      return;
    }
    askConfirm({
      title: "Resolve Complaint",
      message: "Confirm this work is resolved and ready for verification.",
      confirmLabel: "Resolve",
      tone: "success",
      action: () =>
        runAction(
          () => complaintService.resolve(complaintId, values.notes || ""),
          "Complaint marked resolved.",
        ),
    });
  };
  const reopenComplaint = (values) =>
    askConfirm({
      title: "Reopen Complaint",
      message: "Confirm the issue is not fixed and should be reopened.",
      confirmLabel: "Reopen",
      tone: "danger",
      action: () =>
        runAction(
          () => complaintService.reopen(complaintId, values.reason),
          "Complaint reopened.",
        ),
    });
  const assignComplaint = (values) =>
    runAction(
      () =>
        complaintService.assign(
          complaintId,
          values.coordinator_id || user.user_id,
        ),
      "Complaint assigned.",
    );

  if (loading) return <Loader label="Loading complaint" variant="skeleton" />;
  if (error && !complaint)
    return <EmptyState title="Complaint unavailable" description={error} />;

  const currentStepIdx = getLifecycleStepIndex(complaint.status);
  const isReopened = (complaint.status || "").toLowerCase().includes("reopened");

  return (
    <div className="grid gap-6">
      {/* Page Header */}
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-200/80 dark:border-slate-800 pb-5">
        <div>
          <Link
            to="/complaints"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 dark:text-slate-400 hover:text-primary transition-colors"
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to Complaints Tracker
          </Link>
          <div className="flex flex-wrap items-center gap-2.5 mt-2">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              {complaint.title || "Untitled Complaint"}
            </h1>
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
              {complaint.complaint_id}
            </span>
          </div>
          <p className="mt-1 text-xs font-medium text-slate-500 dark:text-slate-400 flex items-center gap-2">
            <span>{department?.name || complaint.department_name || complaint.department_id}</span>
            <span>•</span>
            <span>{location?.name || complaint.location_name || complaint.location_id}</span>
            <span>•</span>
            <span>{complaint.category || complaint.complaint_type || "General Issue"}</span>
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {canStudentEditOrDelete && (
            <button
              type="button"
              onClick={openEditModal}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-xl transition-all shadow-2xs cursor-pointer active:scale-95"
            >
              <Edit className="h-3.5 w-3.5" />
              Edit
            </button>
          )}
          {canDeleteTicket && (
            <button
              type="button"
              onClick={handleDeleteComplaint}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-rose-600 hover:bg-rose-700 rounded-xl transition-all shadow-2xs cursor-pointer active:scale-95"
            >
              <Trash2 className="h-3.5 w-3.5" />
              {canRequestDelete ? "Request Deletion" : "Delete"}
            </button>
          )}
          {complaint.sla_status && (
            <Badge tone={getSlaTone(complaint.sla_status)}>
              {complaint.sla_status}
            </Badge>
          )}
          <Badge tone={getStatusTone(complaint.status)}>
            {complaint.status}
          </Badge>
        </div>
      </div>

      {/* Horizontal Lifecycle Stepper */}
      <div className="rounded-xl border border-slate-200/80 dark:border-slate-800/80 bg-white dark:bg-[#101726] p-4 sm:p-5 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500">
              Workflow Status
            </span>
            {isReopened && (
              <span className="text-[11px] font-semibold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded-full border border-amber-200/60 dark:border-amber-900/60 flex items-center gap-1">
                <AlertTriangle className="h-3 w-3" />
                Reopened ({complaint.reopen_count}x)
              </span>
            )}
            {complaint.escalated && (
              <span className="text-[11px] font-semibold text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 px-2 py-0.5 rounded-full border border-rose-200/60 dark:border-rose-900/60 flex items-center gap-1">
                <ShieldAlert className="h-3 w-3" />
                Escalated
              </span>
            )}
          </div>
          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
            Step {Math.min(currentStepIdx + 1, 6)} of 6:{" "}
            <span className="font-bold text-slate-800 dark:text-slate-200">
              {LIFECYCLE_STEPS[currentStepIdx]?.label}
            </span>
          </span>
        </div>

        {/* Stepper Progress Bar */}
        <div className="relative">
          {/* Track line behind steps */}
          <div className="absolute top-4 left-6 right-6 h-0.5 bg-slate-200 dark:bg-slate-800 -translate-y-1/2 z-0 hidden sm:block" />
          
          <div className="grid grid-cols-2 sm:grid-cols-6 gap-3 relative z-10">
            {LIFECYCLE_STEPS.map((step, idx) => {
              const isPast = idx < currentStepIdx;
              const isCurrent = idx === currentStepIdx;
              const isUpcoming = idx > currentStepIdx;

              return (
                <div
                  key={step.label}
                  className="flex flex-col items-center sm:items-center text-center"
                >
                  <div
                    className={`h-8 w-8 rounded-full flex items-center justify-center text-xs font-bold transition-all shadow-xs ${
                      isPast
                        ? "bg-emerald-600 text-white"
                        : isCurrent
                          ? "bg-primary text-white ring-4 ring-primary/20 scale-105"
                          : "bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 border border-slate-200 dark:border-slate-700"
                    }`}
                  >
                    {isPast ? (
                      <Check className="h-4 w-4" />
                    ) : (
                      <span>{idx + 1}</span>
                    )}
                  </div>
                  <span
                    className={`mt-2 text-xs font-semibold ${
                      isCurrent
                        ? "text-primary dark:text-blue-400 font-bold"
                        : isPast
                          ? "text-slate-800 dark:text-slate-200"
                          : "text-slate-400 dark:text-slate-500"
                    }`}
                  >
                    {step.label}
                  </span>
                  <span className="text-[10px] text-slate-400 dark:text-slate-500 hidden sm:inline">
                    {step.desc}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Deletion Request Alert Banner for App Manager / Admin */}
      {complaint?.deletion_requested && canDirectDelete && (
        <div className="bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/50 rounded-xl p-4 text-amber-900 dark:text-amber-200 flex flex-wrap items-center justify-between gap-3 shadow-xs">
          <div className="flex items-start gap-3">
            <AlertCircle className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold text-amber-900 dark:text-amber-100">
                Deletion Requested by {complaint.deletion_requested_name || complaint.deletion_requested_by} ({complaint.deletion_requested_role})
              </h3>
              <p className="text-xs text-amber-800 dark:text-amber-300 mt-1 font-medium">
                <strong>Reason:</strong> "{complaint.deletion_reason || "No reason specified"}"
              </p>
              {complaint.deletion_requested_at && (
                <span className="text-[10px] text-amber-600 dark:text-amber-400 font-semibold block mt-1">
                  Requested on {formatDate(complaint.deletion_requested_at)}
                </span>
              )}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="danger"
              onClick={handleApproveDeletion}
              className="text-xs font-bold py-1.5 px-3"
            >
              Approve & Delete
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={handleRejectDeletion}
              className="text-xs font-bold py-1.5 px-3 text-amber-900 dark:text-amber-200 border-amber-300 dark:border-amber-800 hover:bg-amber-100 dark:hover:bg-amber-900/40"
            >
              Reject Request
            </Button>
          </div>
        </div>
      )}

      <Toast message={message} tone="success" onClose={() => setMessage("")} />
      <Toast message={error} tone="danger" onClose={() => setError("")} />

      {/* Main 2-Column Operational Grid (65% / 35%) */}
      <div className="grid gap-6 lg:grid-cols-[65%_35%] items-start">
        {/* Left Column: Complaint Details, Attachments, Timeline, Comments */}
        <div className="grid gap-6">
          {/* Complaint Information Card */}
          <Card>
            <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-4 flex items-center gap-2 uppercase tracking-wider text-xs">
              <FileText className="h-4 w-4 text-primary" />
              Complaint Overview
            </h2>
            <dl className="grid gap-4 sm:grid-cols-2 text-sm">
              <div className="flex items-center gap-3">
                <Building className="h-4 w-4 text-slate-400 shrink-0" />
                <div>
                  <dt className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                    Department
                  </dt>
                  <dd className="font-medium text-slate-800 dark:text-slate-200 mt-0.5">
                    {department?.name || complaint.department_name || complaint.department_id}
                  </dd>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <MapPin className="h-4 w-4 text-slate-400 shrink-0" />
                <div>
                  <dt className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                    Location
                  </dt>
                  <dd className="font-medium text-slate-800 dark:text-slate-200 mt-0.5">
                    {location?.name || complaint.location_name || complaint.location_id}
                  </dd>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Tag className="h-4 w-4 text-primary shrink-0" />
                <div>
                  <dt className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                    Category / Issue
                  </dt>
                  <dd className="font-medium text-slate-800 dark:text-slate-100 mt-0.5">
                    {complaint.category || complaint.complaint_type || "General Issue"}
                  </dd>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <Calendar className="h-4 w-4 text-slate-400 shrink-0" />
                <div>
                  <dt className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                    Date Filed
                  </dt>
                  <dd className="font-medium text-slate-800 dark:text-slate-200 mt-0.5">
                    {formatDate(complaint.created_at)}
                  </dd>
                </div>
              </div>
            </dl>

            {/* Description Text Box */}
            <div className="mt-5 border-t border-slate-100 dark:border-slate-800/80 pt-4">
              <dt className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2">
                Problem Description
              </dt>
              <dd className="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 p-4 text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-normal">
                {complaint.description}
              </dd>
            </div>

            {/* Categorized Complaint Attachments Section */}
            {(() => {
              const beforeRepairAttachments = attachments.filter(
                (a) => a.category === "Before Repair",
              );
              const additionalAttachments = attachments.filter(
                (a) => a.category === "Additional",
              );
              const afterRepairAttachments = attachments.filter(
                (a) => a.category === "After Repair",
              );

              const renderAttachmentCard = (att) => {
                const isOwner = att.uploaded_by === user?.user_id;
                const canDelete =
                  isOwner &&
                  user?.role?.toLowerCase() === "student" &&
                  complaint?.status?.toLowerCase() === "submitted";
                const imgSrc = attachmentUrls[att.attachment_id];

                return (
                  <div
                    key={att.attachment_id}
                    className="relative group rounded-xl overflow-hidden border border-slate-200 dark:border-slate-800 shadow-2xs aspect-square bg-slate-100 dark:bg-slate-900 flex flex-col justify-between"
                  >
                    <a
                      href={imgSrc}
                      target="_blank"
                      rel="noreferrer"
                      className="w-full h-full block"
                    >
                      <img
                        src={imgSrc}
                        alt={att.original_filename}
                        className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-200"
                      />
                    </a>

                    {/* Tooltip Overlay */}
                    <div className="absolute inset-0 bg-slate-900/70 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex flex-col justify-end p-2 text-[10px] text-white font-medium pointer-events-none">
                      <div className="truncate font-bold mb-0.5">
                        {att.original_filename}
                      </div>
                      <div className="text-slate-300">
                        By: {att.uploaded_by} ({att.uploader_role})
                      </div>
                      <div className="text-slate-300">
                        {formatDate(att.uploaded_at)}
                      </div>
                    </div>

                    {/* Delete Trigger */}
                    {canDelete && (
                      <button
                        onClick={() =>
                          handleAttachmentDelete(att.attachment_id)
                        }
                        className="absolute top-1.5 right-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg p-1 transition-colors shadow-2xs z-10 cursor-pointer"
                        title="Delete Image"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                );
              };

              return (
                <div className="mt-6 border-t border-slate-100 dark:border-slate-800/80 pt-5">
                  <dt className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-3">
                    Photo Evidence & Attachments ({attachments.length}/20)
                  </dt>

                  {attachments.length === 0 ? (
                    <dd className="text-xs font-medium text-slate-400 dark:text-slate-500 py-1">
                      No photo evidence uploaded yet.
                    </dd>
                  ) : (
                    <div className="grid gap-5">
                      {beforeRepairAttachments.length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-1.5">
                            <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
                            Before Repair ({beforeRepairAttachments.length})
                          </h4>
                          <div className="grid gap-3 grid-cols-2 sm:grid-cols-4">
                            {beforeRepairAttachments.map(renderAttachmentCard)}
                          </div>
                        </div>
                      )}

                      {additionalAttachments.length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-1.5">
                            <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
                            Additional Evidence ({additionalAttachments.length})
                          </h4>
                          <div className="grid gap-3 grid-cols-2 sm:grid-cols-4">
                            {additionalAttachments.map(renderAttachmentCard)}
                          </div>
                        </div>
                      )}

                      {afterRepairAttachments.length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold text-slate-700 dark:text-slate-300 mb-2 flex items-center gap-1.5">
                            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                            After Repair ({afterRepairAttachments.length})
                          </h4>
                          <div className="grid gap-3 grid-cols-2 sm:grid-cols-4">
                            {afterRepairAttachments.map(renderAttachmentCard)}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Upload Input Area */}
                  {canUploadAttachments && attachments.length < 20 && (
                    <div className="mt-4 border-t border-slate-100 dark:border-slate-800/80 pt-3 flex flex-wrap items-center gap-3">
                      {user?.role?.toLowerCase() === "coordinator" && (
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">
                            Category:
                          </span>
                          <select
                            className="text-xs font-semibold text-slate-700 dark:text-slate-200 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg px-2.5 py-1.5 outline-none"
                            value={uploadCategory}
                            onChange={(e) => setUploadCategory(e.target.value)}
                          >
                            <option value="Before Repair">Before Repair</option>
                            <option value="After Repair">After Repair</option>
                          </select>
                        </div>
                      )}

                      <label className="inline-flex items-center justify-center border border-slate-300 dark:border-slate-700 rounded-xl px-3 py-1.5 bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 hover:border-primary cursor-pointer transition-colors text-xs font-semibold text-slate-700 dark:text-slate-200 gap-1.5 shadow-2xs">
                        <Plus className="h-3.5 w-3.5 text-slate-500 dark:text-slate-400" />
                        {uploadingFile ? "Uploading..." : "Add Attachments"}
                        <input
                          type="file"
                          multiple
                          onChange={handleAttachmentUpload}
                          disabled={uploadingFile}
                          accept=".jpg,.jpeg,.png,.pdf"
                          className="hidden"
                        />
                      </label>
                      <span className="text-[10px] text-slate-400 font-medium">
                        Max 5 per upload. JPG/PNG/PDF, max 5MB.
                      </span>
                    </div>
                  )}
                </div>
              );
            })()}

            {/* Resolution Notes Box */}
            {complaint.resolution_notes && (
              <div className="mt-5 border-t border-slate-100 dark:border-slate-800/80 pt-4">
                <dt className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-2">
                  Resolution Summary & Staff Notes
                </dt>
                <dd className="rounded-xl border border-emerald-200 dark:border-emerald-900/50 bg-emerald-50/50 dark:bg-emerald-950/20 p-4 text-sm text-emerald-900 dark:text-emerald-200 leading-relaxed font-medium">
                  {complaint.resolution_notes}
                </dd>
              </div>
            )}
          </Card>

          {/* Activity & Audit History Timeline */}
          {complaint.history && complaint.history.length > 0 && (
            <Card>
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-4 flex items-center gap-2">
                <History className="h-4 w-4 text-primary" />
                Activity & Audit History ({complaint.history.length})
              </h2>
              <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200 dark:before:bg-slate-800">
                {complaint.history.map((item, idx) => (
                  <div key={idx} className="relative">
                    <span className="absolute -left-[22px] top-1.5 h-3 w-3 rounded-full border-2 border-white dark:border-[#101726] bg-primary" />
                    <div className="text-xs text-slate-800 dark:text-slate-200 font-medium">
                      {item.message}
                    </div>
                    <div className="text-[10px] text-slate-400 dark:text-slate-500 mt-0.5">
                      {formatDate(item.at)}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Discussion & Comments Section */}
          <Card>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-4 flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-primary" />
              Discussion & Comments ({comments.length})
            </h2>

            <div className="grid gap-3 mb-4 max-h-80 overflow-y-auto pr-1">
              {comments.length === 0 ? (
                <p className="text-xs font-medium text-slate-400 dark:text-slate-500 py-3 text-center">
                  No comments or questions posted yet.
                </p>
              ) : (
                comments.map((comment) => (
                  <div
                    key={comment.comment_id}
                    className={`p-3 rounded-xl border text-sm transition-colors ${
                      comment.user_id === user?.user_id
                        ? "bg-primary/5 dark:bg-primary/10 border-primary/20 dark:border-primary/30 ml-6"
                        : "bg-slate-50/80 dark:bg-slate-800/60 border-slate-200/80 dark:border-slate-800 mr-6"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-800 dark:text-slate-200 text-xs">
                          {comment.user_id}
                        </span>
                        {comment.is_internal && (
                          <span className="text-[9px] font-semibold uppercase tracking-wider bg-amber-100 dark:bg-amber-950/40 text-amber-700 dark:text-amber-400 px-1.5 py-0.5 rounded-md border border-amber-200/50 dark:border-amber-900/50">
                            Internal Staff Note
                          </span>
                        )}
                      </div>
                      <span className="text-[10px] text-slate-400 dark:text-slate-500 font-medium">
                        {formatDate(comment.created_at)}
                      </span>
                    </div>
                    <p className="text-slate-700 dark:text-slate-300 font-normal leading-relaxed text-xs">
                      {comment.message}
                    </p>
                  </div>
                ))
              )}
            </div>

            <form
              onSubmit={handleCommentSubmit}
              className="flex gap-2 items-start border-t border-slate-100 dark:border-slate-800/80 pt-4"
            >
              <div className="flex-1">
                <Textarea
                  placeholder="Post an update, clarify details, or ask a question..."
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  className="min-h-[55px] text-xs"
                  required
                />
                {user?.role !== ROLES.STUDENT && (
                  <label className="inline-flex items-center gap-2 mt-2 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={isCommentInternal}
                      onChange={(e) => setIsCommentInternal(e.target.checked)}
                      className="rounded border-slate-300 dark:border-slate-700 text-primary focus:ring-primary/30 h-3.5 w-3.5"
                    />
                    <span className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                      Internal Note (hidden from students)
                    </span>
                  </label>
                )}
              </div>
              <Button
                type="submit"
                variant="primary"
                disabled={submittingComment}
                className="font-semibold h-10 px-4 self-end shrink-0 text-xs"
              >
                Send
              </Button>
            </form>
          </Card>
        </div>

        {/* Right Column: SLA Target, Assignments, Actions Panel */}
        <div className="grid gap-6">
          {/* Operations Action Center */}
          <Card>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3 flex items-center gap-2">
              <Wrench className="h-4 w-4 text-primary" />
              Action Center
            </h2>
            <div className="grid gap-3">
              {user &&
                (user.role === ROLES.COORDINATOR || user.role === ROLES.LOCATION_IN_CHARGE) &&
                complaint.status === "Submitted" &&
                !complaint.assigned_to && (
                  <Button
                    type="button"
                    onClick={handleTakeComplaint}
                    variant="primary"
                    className="w-full font-bold py-2.5 text-xs"
                  >
                    Take Complaint
                  </Button>
                )}
              {canCoordinate &&
                ![
                  COMPLAINT_STATUS.WAITING_VERIFICATION,
                  COMPLAINT_STATUS.CLOSED,
                  COMPLAINT_STATUS.AUTO_CLOSED,
                ].includes(complaint.status) && (
                  <>
                    {/* Accept / Assign: only from Pending, Submitted, Reopened */}
                    {[
                      COMPLAINT_STATUS.PENDING,
                      COMPLAINT_STATUS.SUBMITTED,
                      COMPLAINT_STATUS.REOPENED,
                      COMPLAINT_STATUS.AWAITING_ASSIGNMENT,
                    ].includes(complaint.status) && (
                      <form
                        className="grid gap-3"
                        onSubmit={handleSubmit(assignComplaint)}
                      >
                        {[ROLES.APP_MANAGER, ROLES.ADMINISTRATOR].includes(
                          user?.role,
                        ) && (
                          <Select
                            label="Assign Coordinator"
                            {...register("coordinator_id")}
                          >
                            <option value="">Choose coordinator</option>
                            {coordinators.map((item) => (
                              <option key={item.user_id} value={item.user_id}>
                                {item.name}
                              </option>
                            ))}
                          </Select>
                        )}
                        <Button
                          type="submit"
                          variant="warning"
                          disabled={isSubmitting}
                          className="w-full font-bold text-xs"
                        >
                          {[ROLES.APP_MANAGER, ROLES.ADMINISTRATOR].includes(
                            user?.role,
                          )
                            ? "Assign Coordinator"
                            : "Accept & Assign to Self"}
                        </Button>
                      </form>
                    )}

                    {/* Start Work: only from Assigned */}
                    {complaint.status === COMPLAINT_STATUS.ASSIGNED && (
                      <Button
                        onClick={() =>
                          runAction(
                            () =>
                              complaintService.updateStatus(
                                complaintId,
                                COMPLAINT_STATUS.IN_PROGRESS,
                              ),
                            "Work started.",
                          )
                        }
                        variant="subtle"
                        className="w-full font-bold py-2.5 text-xs"
                      >
                        Start Work (In Progress)
                      </Button>
                    )}

                    {/* Resolve: only from In Progress */}
                    {complaint.status === COMPLAINT_STATUS.IN_PROGRESS && (
                      <form
                        className="grid gap-3 border-t border-slate-100 dark:border-slate-800/80 pt-3"
                        onSubmit={handleSubmit(resolveComplaint)}
                      >
                        <Textarea
                          label="Resolution Summary"
                          placeholder="Specify work details..."
                          {...register("notes")}
                        />
                        <Button
                          type="submit"
                          variant="success"
                          disabled={isSubmitting}
                          className="w-full font-bold text-xs"
                        >
                          Mark Resolved
                        </Button>
                      </form>
                    )}
                  </>
                )}

              {canVerify && (
                <>
                  <Button
                    onClick={() =>
                      askConfirm({
                        title: "Verify Resolution",
                        message:
                          "Confirm this complaint has been resolved correctly and can now be closed.",
                        confirmLabel: "Verify Fixed",
                        tone: "success",
                        action: () =>
                          runAction(
                            () => complaintService.verify(complaintId),
                            "Complaint verified and closed.",
                          ),
                      })
                    }
                    variant="success"
                    className="w-full font-bold py-2.5 flex items-center justify-center gap-1.5 text-xs"
                  >
                    <CheckCircle2 className="h-4 w-4" />
                    Verify as Fixed
                  </Button>

                  <form
                    className="grid gap-3 border-t border-slate-100 dark:border-slate-800/80 pt-3"
                    onSubmit={handleSubmit(reopenComplaint)}
                  >
                    <Textarea
                      label="Reason Not Fixed"
                      placeholder="Specify what remains broken..."
                      error={errors.reason?.message}
                      {...register("reason", {
                        required: "Please specify the reason for reopening.",
                      })}
                    />
                    <Button
                      type="submit"
                      variant="danger"
                      disabled={isSubmitting}
                      className="w-full font-bold text-xs"
                    >
                      Report Not Fixed
                    </Button>
                  </form>
                </>
              )}

              {!canCoordinate && !canVerify && (
                <div className="flex flex-col items-center justify-center p-3 text-center">
                  <AlertCircle className="h-5 w-5 text-slate-300 dark:text-slate-600" />
                  <p className="text-xs font-medium text-slate-400 dark:text-slate-500 mt-1.5">
                    No active actions required for your role at this stage.
                  </p>
                </div>
              )}

              {complaint.visibility_type === "Community" && (
                <div className="border-t border-slate-100 dark:border-slate-800/80 pt-3 grid gap-2.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                      Affected Students
                    </span>
                    <span className="bg-primary/10 text-primary text-xs font-bold px-2 py-0.5 rounded-full">
                      {complaint.affected_count || 0} Affected
                    </span>
                  </div>
                  {user?.role === ROLES.STUDENT &&
                    !["Closed", "Closed (Auto Closed)"].includes(
                      complaint.status,
                    ) && (
                      <Button
                        onClick={async () => {
                          try {
                            setError("");
                            setMessage("");
                            const res =
                              await complaintService.markAffected(complaintId);
                            setComplaint(res.data);
                            setMessage(
                              "You have been marked as affected by this issue.",
                            );
                          } catch (err) {
                            setError(
                              getApiError(err, "Could not mark as affected."),
                            );
                          }
                        }}
                        variant="subtle"
                        className="w-full font-bold py-2 flex items-center justify-center gap-1.5 text-xs"
                      >
                        <Plus className="h-4 w-4" />
                        I'm Affected Too
                      </Button>
                    )}
                </div>
              )}
            </div>
          </Card>

          {/* Personnel & Responsibilities Card */}
          <Card>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3 flex items-center gap-2">
              <User className="h-4 w-4 text-primary" />
              Personnel & Assignments
            </h2>
            <div className="space-y-3 text-xs">
              <div className="flex items-start justify-between gap-2 pb-2.5 border-b border-slate-100 dark:border-slate-800/80">
                <span className="text-slate-400 dark:text-slate-500 font-medium">
                  Assigned Staff:
                </span>
                <span className="font-semibold text-slate-800 dark:text-slate-200 text-right">
                  {complaint.assigned_to || (
                    <span className="text-amber-500 font-medium">Unassigned</span>
                  )}
                </span>
              </div>
              <div className="flex items-start justify-between gap-2 pb-2.5 border-b border-slate-100 dark:border-slate-800/80">
                <span className="text-slate-400 dark:text-slate-500 font-medium">
                  Reported By:
                </span>
                <span className="font-semibold text-slate-800 dark:text-slate-200 text-right">
                  {complaint.created_by || "Student"}
                </span>
              </div>
              <div className="flex items-start justify-between gap-2 pb-2.5 border-b border-slate-100 dark:border-slate-800/80">
                <span className="text-slate-400 dark:text-slate-500 font-medium">
                  Visibility:
                </span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {complaint.visibility_type || "Private"}
                </span>
              </div>
              <div className="flex items-start justify-between gap-2">
                <span className="text-slate-400 dark:text-slate-500 font-medium">
                  Reopen Count:
                </span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {complaint.reopen_count || 0}
                </span>
              </div>
            </div>
          </Card>

          {/* SLA & Timeline Summary Card */}
          <Card>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3 flex items-center gap-2">
              <Clock className="h-4 w-4 text-primary" />
              SLA & Timeline
            </h2>
            <div className="space-y-3 text-xs">
              <div className="flex items-start justify-between gap-2 pb-2.5 border-b border-slate-100 dark:border-slate-800/80">
                <span className="text-slate-400 dark:text-slate-500 font-medium">
                  Target Due Date:
                </span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {complaint.due_date ? formatDate(complaint.due_date) : "N/A"}
                </span>
              </div>
              <div className="flex items-start justify-between gap-2 pb-2.5 border-b border-slate-100 dark:border-slate-800/80">
                <span className="text-slate-400 dark:text-slate-500 font-medium">
                  Priority Level:
                </span>
                <span className="font-semibold text-slate-800 dark:text-slate-200">
                  {complaint.priority || "Medium"}
                </span>
              </div>
              {complaint.resolved_at && (
                <div className="flex items-start justify-between gap-2">
                  <span className="text-slate-400 dark:text-slate-500 font-medium">
                    Resolved At:
                  </span>
                  <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                    {formatDate(complaint.resolved_at)}
                  </span>
                </div>
              )}
            </div>
          </Card>

          {/* Secondary Actions: Priority Update */}
          {canChangePriority && (
            <Card>
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 dark:text-slate-500 mb-3 flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-warning" />
                Update Priority
              </h2>
              <form onSubmit={handlePriorityUpdate} className="grid gap-3">
                <Select
                  label="Select Priority"
                  value={selectedPriority}
                  onChange={(e) => setSelectedPriority(e.target.value)}
                >
                  <option value="Low">Low</option>
                  <option value="Medium">Medium</option>
                  <option value="High">High</option>
                  <option value="Critical">Critical</option>
                </Select>
                <Textarea
                  label="Reason for Change"
                  placeholder="Specify why priority is changing..."
                  value={priorityReason}
                  onChange={(e) => setPriorityReason(e.target.value)}
                  className="text-xs"
                  required
                />
                <Button
                  type="submit"
                  variant="primary"
                  disabled={updatingPriority}
                  className="w-full font-bold text-xs"
                >
                  {updatingPriority ? "Updating..." : "Update Priority"}
                </Button>
              </form>
            </Card>
          )}

          {/* Secondary Actions: Escalation */}
          {canEscalate && (
            <Card>
              <h2 className="text-xs font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400 mb-3 flex items-center gap-2">
                <ShieldAlert className="h-4 w-4 text-rose-600" />
                Escalate Complaint
              </h2>
              <form onSubmit={handleEscalateSubmit} className="grid gap-3">
                <Textarea
                  label="Reason for Escalation"
                  placeholder="Specify reason for higher authority escalation..."
                  value={escalateReason}
                  onChange={(e) => setEscalateReason(e.target.value)}
                  className="text-xs"
                  required
                />
                <Button
                  type="submit"
                  variant="danger"
                  disabled={escalating}
                  className="w-full font-bold text-xs"
                >
                  {escalating ? "Escalating..." : "Escalate to Next Level"}
                </Button>
              </form>
            </Card>
          )}
        </div>
      </div>

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

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
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

      {/* Deletion Reason Modal for Coordinator / Warden */}
      {showDeletionModal && (
        <Modal
          isOpen={showDeletionModal}
          onClose={() => setShowDeletionModal(false)}
          title="🗑️ Request Complaint Deletion"
        >
          <form onSubmit={handleDeletionRequestSubmit} className="space-y-4">
            <p className="text-xs text-slate-500">
              Please provide a clear reason for requesting deletion of this complaint. Your request will be sent to the assigned App Manager for approval.
            </p>
            <Textarea
              label="Reason for Deletion"
              value={deletionReasonInput}
              onChange={(e) => setDeletionReasonInput(e.target.value)}
              placeholder="Explain why this complaint should be deleted (e.g. duplicate issue, test data, invalid entry)..."
              rows={4}
              required
            />
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowDeletionModal(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="danger"
                disabled={submittingDeletionRequest}
              >
                {submittingDeletionRequest ? "Submitting..." : "Send Deletion Request"}
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
