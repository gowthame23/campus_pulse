import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { Link, useParams, useNavigate, useLocation } from "react-router-dom";
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
  Phone,
  PhoneCall,
  Globe,
  Sparkles,
  RefreshCw,
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
import AssignModal from "../../components/AssignModal.jsx";
import { getApiError } from "../../api/axios.js";
import { useAuth } from "../../context/AuthContext.jsx";
import { useLanguage } from "../../context/LanguageContext.jsx";

import { complaintService } from "../../services/complaintService.js";
import { attachmentService } from "../../services/attachmentService.js";
import { departmentService } from "../../services/departmentService.js";
import { locationService } from "../../services/locationService.js";
import { userService } from "../../services/userService.js";
import StageTimeline from "../../components/StageTimeline.jsx";
import ResponsiblePersonnelCard from "../../components/ResponsiblePersonnelCard.jsx";
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
  const { language, t } = useLanguage();
  const [complaint, setComplaint] = useState(null);
  const [showTranslation, setShowTranslation] = useState(false);
  const [translatedData, setTranslatedData] = useState(null);
  const [translating, setTranslating] = useState(false);
  const [translationError, setTranslationError] = useState("");
  const [departments, setDepartments] = useState([]);
  const [locations, setLocations] = useState([]);
  const [coordinators, setCoordinators] = useState([]);
  const locState = useLocation();
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState(
    locState?.state?.isOther
      ? "Thank you for your information. Your submission has been received and routed to Administration for review."
      : ""
  );
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

  // User directory for personnel lookup
  const [allUsers, setAllUsers] = useState([]);

  // Workflow action modals
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [progressNoteText, setProgressNoteText] = useState("");
  const [submittingProgressNote, setSubmittingProgressNote] = useState(false);

  const [showPauseModal, setShowPauseModal] = useState(false);
  const [pauseReasonText, setPauseReasonText] = useState("");
  const [submittingPause, setSubmittingPause] = useState(false);

  const [showResolveModal, setShowResolveModal] = useState(false);
  const [resolveNotesText, setResolveNotesText] = useState("");
  const [resolvePhotoFile, setResolvePhotoFile] = useState(null);
  const [submittingResolve, setSubmittingResolve] = useState(false);

  const [showWardenVerifyModal, setShowWardenVerifyModal] = useState(false);
  const [wardenVerdictChoice, setWardenVerdictChoice] = useState("Verified");
  const [wardenVerdictNotes, setWardenVerdictNotes] = useState("");
  const [submittingWardenVerify, setSubmittingWardenVerify] = useState(false);

  const [showStudentReopenModal, setShowStudentReopenModal] = useState(false);
  const [studentReopenReason, setStudentReopenReason] = useState("");
  const [submittingStudentReopen, setSubmittingStudentReopen] = useState(false);

  const [showAdminDecisionModal, setShowAdminDecisionModal] = useState(false);
  const [adminDecisionChoice, setAdminDecisionChoice] = useState("Close");
  const [adminDecisionNotes, setAdminDecisionNotes] = useState("");
  const [adminReassignCoord, setAdminReassignCoord] = useState("");
  const [submittingAdminDecision, setSubmittingAdminDecision] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);

  // Student Rating & Feedback state
  const [feedbacks, setFeedbacks] = useState([]);
  const [feedbackRating, setFeedbackRating] = useState(5);
  const [feedbackNote, setFeedbackNote] = useState("");
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

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
  const statusNormalized = useMemo(() => {
    const s = String(complaint?.status || "Complaint Raised").toLowerCase();
    if (s.includes("raised") || s.includes("star") || s.includes("submit") || s.includes("pend")) return "Complaint Raised";
    if (s.includes("going") || s.includes("progress") || s.includes("assign") || s.includes("part")) return "Going On";
    if (s.includes("fix") || s.includes("done") || s.includes("close") || s.includes("verif") || s.includes("resolv")) return "Fixed";
    return complaint?.status || "Complaint Raised";
  }, [complaint?.status]);

  const isAssigned = Boolean(complaint?.assigned_to) || !["Submitted", "Pending"].includes(complaint?.status);
  const canStudentEditOrDelete =
    isOwner &&
    (user?.role === ROLES.STUDENT || (user?.role || "").toLowerCase() === "student") &&
    complaint?.status === "Submitted" &&
    !isAssigned;
  const canStudentRequestCancellation =
    isOwner &&
    (user?.role === ROLES.STUDENT || (user?.role || "").toLowerCase() === "student") &&
    isAssigned &&
    complaint?.status !== "Cancelled" &&
    !complaint?.status?.startsWith("Closed") &&
    complaint?.status !== "Cancellation Requested";

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

  const [showCancellationModal, setShowCancellationModal] = useState(false);
  const [cancellationReasonInput, setCancellationReasonInput] = useState("");
  const [submittingCancellationRequest, setSubmittingCancellationRequest] = useState(false);

  const [showRejectCancellationModal, setShowRejectCancellationModal] = useState(false);
  const [rejectCancellationReason, setRejectCancellationReason] = useState("");
  const [submittingRejectCancellation, setSubmittingRejectCancellation] = useState(false);

  const handleCancellationRequestSubmit = async (e) => {
    e.preventDefault();
    if (!cancellationReasonInput.trim()) {
      setError("A cancellation reason is required.");
      return;
    }
    setSubmittingCancellationRequest(true);
    setError("");
    try {
      await complaintService.requestCancellation(complaintId, cancellationReasonInput.trim());
      setMessage("Cancellation request submitted for coordinator review.");
      setShowCancellationModal(false);
      load();
    } catch (err) {
      setError(getApiError(err, "Failed to submit cancellation request."));
    } finally {
      setSubmittingCancellationRequest(false);
    }
  };

  const handleApproveCancellation = async () => {
    askConfirm({
      title: "Approve Complaint Cancellation",
      message: `Are you sure you want to approve cancellation of complaint ${complaintId}? The complaint will be marked Cancelled and work stopped.`,
      confirmLabel: "Approve Cancellation",
      tone: "danger",
      action: async () => {
        try {
          await complaintService.approveCancellation(complaintId, "Approved by coordinator");
          setMessage("Complaint cancelled successfully.");
          load();
        } catch (err) {
          setError(getApiError(err, "Failed to approve cancellation."));
        }
      },
    });
  };

  const handleRejectCancellationSubmit = async (e) => {
    e.preventDefault();
    if (!rejectCancellationReason.trim()) {
      setError("A rejection reason is required.");
      return;
    }
    setSubmittingRejectCancellation(true);
    setError("");
    try {
      await complaintService.rejectCancellation(complaintId, rejectCancellationReason.trim());
      setMessage("Cancellation request rejected. Complaint restored to active workflow.");
      setShowRejectCancellationModal(false);
      load();
    } catch (err) {
      setError(getApiError(err, "Failed to reject cancellation."));
    } finally {
      setSubmittingRejectCancellation(false);
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

  const coordinatorUser = useMemo(() => {
    return (allUsers || []).find(
      (u) =>
        u.user_id === complaint?.assigned_to ||
        u.email === complaint?.assigned_to ||
        u.id === complaint?.assigned_to,
    ) || null;
  }, [allUsers, complaint?.assigned_to]);

  const wardenUser = useMemo(() => {
    return (
      (allUsers || []).find(
        (u) =>
          u.user_id === location?.in_charge_id ||
          u.id === location?.in_charge_id ||
          (u.role === "location_in_charge" && u.location_id === complaint?.location_id),
      ) || null
    );
  }, [allUsers, location?.in_charge_id, complaint?.location_id]);

  const userRole = (user?.role || "").toLowerCase();
  const isCoordinator = userRole === "coordinator";
  const isEmployee = userRole === "employee";
  const isWorker = isCoordinator || isEmployee;
  const isWarden = userRole === "location_in_charge" || userRole === "warden";
  const isAppManager = userRole === "app_manager";
  const isAdmin = userRole === "administrator" || userRole === "admin";
  const isStudent = userRole === "student";


  const isLocationWarden =
    isWarden &&
    (location?.in_charge_id === user?.user_id ||
      user?.location_id === complaint?.location_id ||
      isAdmin);

  const isSelfWorkOnTicket =
    user?.user_id === complaint?.assigned_to ||
    user?.email === complaint?.assigned_to ||
    user?.user_id === complaint?.created_by;

  const canWardenVerify =
    (isLocationWarden || isAdmin) &&
    complaint?.status === "Pending Warden Verification" &&
    !isSelfWorkOnTicket;

  const canStudentConfirmOrReopen =
    (isOwner || isAdmin) &&
    complaint?.status === "Waiting for Verification";

  const canAdminDecide =
    isAdmin && complaint?.status === "Admin Review";

  const canChangePriority =
    user && (isAdmin || isAppManager || isLocationWarden);

  async function load(silent = false) {
    if (!silent) setLoading(true);
    setError("");
    try {
      const [
        complaintResponse,
        departmentResponse,
        locationResponse,
        commentsResponse,
        attachmentsResponse,
        usersResponse,
        feedbackResponse,
      ] = await Promise.all([
        complaintService.getById(complaintId),
        departments.length > 0 ? Promise.resolve({ data: departments }) : departmentService.list().catch(() => ({ data: [] })),
        locations.length > 0 ? Promise.resolve({ data: locations }) : locationService.list().catch(() => ({ data: [] })),
        complaintService.getComments(complaintId).catch(() => ({ data: [] })),
        attachmentService.list(complaintId).catch(() => ({ data: [] })),
        allUsers.length > 0 ? Promise.resolve({ data: allUsers }) : userService.list().catch(() => ({ data: [] })),
        complaintService.getFeedback(complaintId).catch(() => ({ data: [] })),
      ]);
      setComplaint(complaintResponse.data);
      if (departments.length === 0) setDepartments(departmentResponse.data || []);
      if (locations.length === 0) setLocations(locationResponse.data || []);
      setComments(commentsResponse.data || []);
      setAttachments(attachmentsResponse.data || []);
      setFeedbacks(feedbackResponse.data || []);
      if (allUsers.length === 0) {
        const userList = usersResponse.data || [];
        setAllUsers(userList);
        setCoordinators(userList.filter((u) => (u.role || "").toLowerCase() === "coordinator"));
      }
      setSelectedPriority(complaintResponse.data.priority || "Medium");
    } catch (err) {
      if (!silent) setError(getApiError(err, "Unable to load complaint."));
    } finally {
      if (!silent) setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [complaintId, user?.role]);

  // Live real-time updates via WebSocket events, reconnects, or poll fallback
  useEffect(() => {
    const handleWsEvent = (evt) => {
      const detail = evt?.detail;
      if (!detail || !detail.complaint_id || detail.complaint_id === complaintId) {
        load(true);
      }
    };
    const handleLiveSync = () => load(true);

    window.addEventListener("campus-pulse-ws-event", handleWsEvent);
    window.addEventListener("campus-pulse-reconnected", handleLiveSync);
    window.addEventListener("campus-pulse-poll", handleLiveSync);

    return () => {
      window.removeEventListener("campus-pulse-ws-event", handleWsEvent);
      window.removeEventListener("campus-pulse-reconnected", handleLiveSync);
      window.removeEventListener("campus-pulse-poll", handleLiveSync);
    };
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

  const handleAcceptComplaint = async () => {
    setMessage("");
    setError("");
    try {
      await complaintService.accept(complaintId);
      setMessage("Complaint accepted and assigned to you.");
      load();
    } catch (err) {
      if (err.response?.status === 409) {
        setError("Taken by another coordinator. Refreshing status...");
      } else {
        setError(getApiError(err, "Failed to accept complaint."));
      }
      load();
    }
  };

  const handleDirectDone = async () => {
    setMessage("");
    setError("");
    try {
      await complaintService.resolve(complaintId, {
        notes: "Work completed by coordinator",
        skip_photo: true,
      });
      setMessage("Complaint marked as Fixed.");
      load();
    } catch (err) {
      setError(getApiError(err, "Failed to mark as fixed."));
    }
  };

  const handleStartWork = async () => {
    setMessage("");
    setError("");
    try {
      await complaintService.startWork(complaintId);
      setMessage("Work marked in progress.");
      load();
    } catch (err) {
      setError(getApiError(err, "Failed to start work."));
    }
  };

  const handleProgressNoteSubmit = async (e) => {
    e.preventDefault();
    if (!progressNoteText.trim()) return;
    setSubmittingProgressNote(true);
    setMessage("");
    setError("");
    try {
      await complaintService.addProgressNote(complaintId, progressNoteText.trim());
      setMessage("Progress note logged successfully.");
      setProgressNoteText("");
      setShowProgressModal(false);
      load();
    } catch (err) {
      setError(getApiError(err, "Failed to add progress note."));
    } finally {
      setSubmittingProgressNote(false);
    }
  };

  const handlePauseSubmit = async (e) => {
    e.preventDefault();
    if (!pauseReasonText.trim()) {
      setError("Please specify reason for pausing work.");
      return;
    }
    setSubmittingPause(true);
    setMessage("");
    setError("");
    try {
      await complaintService.pause(complaintId, pauseReasonText.trim());
      setMessage("Complaint paused (Waiting for Parts).");
      setPauseReasonText("");
      setShowPauseModal(false);
      load();
    } catch (err) {
      setError(getApiError(err, "Failed to pause work."));
    } finally {
      setSubmittingPause(false);
    }
  };

  const handleResumeWork = async () => {
    setMessage("");
    setError("");
    try {
      await complaintService.resume(complaintId);
      setMessage("Work resumed. Complaint returned to In Progress.");
      load();
    } catch (err) {
      setError(getApiError(err, "Failed to resume work."));
    }
  };

  const handleResolveSubmit = async (e) => {
    e.preventDefault();
    const p = (complaint.priority || "Medium").toLowerCase();
    const isHighOrCrit = p === "high" || p === "critical";
    const hasExistingAfterRepair = attachments.some(
      (a) => (a.category || "").toLowerCase() === "after repair",
    );

    if (isHighOrCrit && !hasExistingAfterRepair && !resolvePhotoFile) {
      setError(
        "High and Critical priority complaints require an 'After Repair' photo before resolving.",
      );
      return;
    }

    if (!hasExistingAfterRepair && !resolvePhotoFile && !resolveNotesText.trim()) {
      setError(
        "Resolution notes are mandatory when no 'After Repair' image is uploaded.",
      );
      return;
    }

    setSubmittingResolve(true);
    setMessage("");
    setError("");
    try {
      if (resolvePhotoFile) {
        await attachmentService.upload(
          complaintId,
          [resolvePhotoFile],
          "After Repair",
        );
      }
      await complaintService.resolve(complaintId, resolveNotesText.trim());
      setMessage("Complaint marked resolved!");
      setResolveNotesText("");
      setResolvePhotoFile(null);
      setShowResolveModal(false);
      load();
    } catch (err) {
      setError(getApiError(err, "Failed to mark complaint resolved."));
    } finally {
      setSubmittingResolve(false);
    }
  };

  const handleWardenVerifySubmit = async (verdict, notes) => {
    setSubmittingWardenVerify(true);
    setMessage("");
    setError("");
    try {
      await complaintService.wardenVerify(complaintId, verdict, notes);
      setMessage(`Warden verification submitted: ${verdict}.`);
      setShowWardenVerifyModal(false);
      setWardenVerdictNotes("");
      load();
    } catch (err) {
      setError(getApiError(err, "Failed to submit warden verification."));
    } finally {
      setSubmittingWardenVerify(false);
    }
  };

  const handleStudentConfirm = async () => {
    setMessage("");
    setError("");
    try {
      await complaintService.verify(complaintId);
      setMessage("Resolution verified and complaint permanently closed!");
      load();
    } catch (err) {
      setError(getApiError(err, "Failed to confirm resolution."));
    }
  };

  const handleFeedbackSubmit = async (e) => {
    e.preventDefault();
    setSubmittingFeedback(true);
    setMessage("");
    setError("");
    try {
      await complaintService.submitFeedback(complaintId, {
        rating: feedbackRating,
        thank_you_note: feedbackNote.trim() || undefined,
      });
      setMessage("Thank you! Your feedback has been shared with the coordinator.");
      const fbRes = await complaintService.getFeedback(complaintId).catch(() => ({ data: [] }));
      setFeedbacks(fbRes.data || []);
      setFeedbackNote("");
    } catch (err) {
      setError(getApiError(err, "Failed to submit feedback."));
    } finally {
      setSubmittingFeedback(false);
    }
  };

  const handleStudentReopenSubmit = async (e) => {
    e.preventDefault();
    if (!studentReopenReason.trim()) {
      setError("Please provide a reason why the issue is still not fixed.");
      return;
    }
    setSubmittingStudentReopen(true);
    setMessage("");
    setError("");
    try {
      await complaintService.reopen(complaintId, studentReopenReason.trim());
      setMessage("Complaint reopened.");
      setStudentReopenReason("");
      setShowStudentReopenModal(false);
      load();
    } catch (err) {
      setError(getApiError(err, "Failed to reopen complaint."));
    } finally {
      setSubmittingStudentReopen(false);
    }
  };

  const handleAdminDecisionSubmit = async (e) => {
    e.preventDefault();
    if (!adminDecisionNotes.trim()) {
      setError("Decision notes are required.");
      return;
    }
    if (adminDecisionChoice === "Reopen" && !adminReassignCoord) {
      setError("Please select a coordinator to assign the reopened ticket to.");
      return;
    }
    setSubmittingAdminDecision(true);
    setMessage("");
    setError("");
    try {
      await complaintService.adminDecision(
        complaintId,
        adminDecisionChoice,
        adminDecisionNotes.trim(),
        adminDecisionChoice === "Reopen" ? adminReassignCoord : null,
      );
      setMessage(
        `Admin review decision applied: ${adminDecisionChoice}.`,
      );
      setShowAdminDecisionModal(false);
      setAdminDecisionNotes("");
      load();
    } catch (err) {
      setError(getApiError(err, "Failed to apply admin decision."));
    } finally {
      setSubmittingAdminDecision(false);
    }
  };

  const handleTranslateComplaint = async (targetLang = null) => {
    const target = targetLang || language || "en";
    setTranslating(true);
    setTranslationError("");
    try {
      const res = await complaintService.translate(complaintId, target);
      setTranslatedData(res.data);
      setShowTranslation(true);
    } catch (err) {
      setTranslationError(getApiError(err, "Failed to translate complaint."));
    } finally {
      setTranslating(false);
    }
  };

  const toggleTranslation = () => {
    if (showTranslation) {
      setShowTranslation(false);
    } else {
      if (translatedData && translatedData.target_language === language) {
        setShowTranslation(true);
      } else {
        handleTranslateComplaint(language);
      }
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
          <p className="mt-1 text-xs font-medium text-slate-500 dark:text-slate-400 flex flex-wrap items-center gap-2">
            <span>{department?.name || complaint.department_name || complaint.department_id}</span>
            <span>•</span>
            <span>{location?.name || complaint.location_name || complaint.location_id}</span>
            <span>•</span>
            <span>{complaint.category || complaint.complaint_type || "General Issue"}</span>
            {complaint.exact_spot && (
              <>
                <span>•</span>
                <span className="font-semibold text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/40 px-1.5 py-0.5 rounded border border-amber-200 dark:border-amber-800">
                  📍 {complaint.exact_spot}
                </span>
              </>
            )}
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
          {canStudentRequestCancellation && (
            <button
              type="button"
              onClick={() => {
                setCancellationReasonInput("");
                setShowCancellationModal(true);
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-amber-600 hover:bg-amber-700 rounded-xl transition-all shadow-2xs cursor-pointer active:scale-95"
            >
              <AlertTriangle className="h-3.5 w-3.5" />
              Request Cancellation
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

      {/* Vertical Stage Timeline & Live Countdown Timers */}
      <StageTimeline
        complaint={complaint}
        coordinatorUser={coordinatorUser}
        wardenUser={wardenUser}
        attachments={attachments}
      />

      {/* Cancellation Review Alert Banner for Coordinator / Admin */}
      {(complaint?.status === "Cancellation Requested" || complaint?.cancellation_requested) && (
        <div className="bg-amber-50 dark:bg-amber-950/40 border-2 border-amber-400 dark:border-amber-700 rounded-xl p-4 text-amber-900 dark:text-amber-100 flex flex-wrap items-center justify-between gap-4 shadow-sm">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-6 w-6 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-bold text-amber-950 dark:text-amber-100">
                Cancellation Requested by {complaint.cancellation_requested_by_name || complaint.cancellation_requested_by || "Student"}
              </h3>
              <p className="text-xs text-amber-800 dark:text-amber-200 mt-1 font-medium">
                <strong>Reason:</strong> "{complaint.cancellation_reason || "No reason specified"}"
              </p>
              {complaint.cancellation_requested_at && (
                <span className="text-[11px] text-amber-700 dark:text-amber-300 font-semibold block mt-1">
                  Requested on {formatDate(complaint.cancellation_requested_at)}
                </span>
              )}
            </div>
          </div>
          {(isCoordinator || isAdmin || isAppManager) && (
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="danger"
                onClick={handleApproveCancellation}
                className="text-xs font-bold py-1.5 px-3 bg-rose-600 hover:bg-rose-700 text-white"
              >
                Approve Cancellation
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setRejectCancellationReason("");
                  setShowRejectCancellationModal(true);
                }}
                className="text-xs font-bold py-1.5 px-3 text-amber-950 dark:text-amber-100 border-amber-400 dark:border-amber-600 hover:bg-amber-100 dark:hover:bg-amber-900/60"
              >
                Reject Cancellation
              </Button>
            </div>
          )}
        </div>
      )}

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

              {complaint.exact_spot && (
                <div className="flex items-center gap-3 p-2.5 rounded-xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/60">
                  <MapPin className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0" />
                  <div>
                    <dt className="text-[10px] font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wider">
                      Exact Spot
                    </dt>
                    <dd className="font-bold text-slate-900 dark:text-slate-100 mt-0.5 text-xs">
                      {complaint.exact_spot}
                    </dd>
                  </div>
                </div>
              )}

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

            {/* Description Text Box with AI Translation */}
            <div className="mt-5 border-t border-slate-100 dark:border-slate-800/80 pt-4">
              <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                <dt className="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
                  {t("description") || "Problem Description"}
                </dt>
                <div className="flex items-center gap-2">
                  {showTranslation && (
                    <button
                      type="button"
                      onClick={() => setShowTranslation(false)}
                      className="text-xs font-medium text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 px-2.5 py-1 rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800 transition"
                    >
                      {t("translation.original") || "Original"}
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={toggleTranslation}
                    disabled={translating}
                    className="inline-flex items-center gap-1.5 text-xs font-medium text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 bg-indigo-50 dark:bg-indigo-950/50 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 px-2.5 py-1 rounded-lg border border-indigo-200/60 dark:border-indigo-800/50 transition disabled:opacity-50"
                  >
                    {translating ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>{t("translation.translating") || "Translating..."}</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                        <span>
                          {showTranslation
                            ? (t("translation.original") || "Original")
                            : (t("translation.view_translation") || `Translate (${(language || "en").toUpperCase()})`)}
                        </span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {translationError && (
                <div className="mb-2 text-xs text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/30 p-2.5 rounded-lg border border-rose-200 dark:border-rose-900/40 flex items-center justify-between">
                  <span>{translationError}</span>
                  <button
                    type="button"
                    onClick={() => handleTranslateComplaint(language)}
                    className="underline font-semibold ml-2 hover:text-rose-700"
                  >
                    {t("translation.retry") || "Retry"}
                  </button>
                </div>
              )}

              {showTranslation && translatedData ? (
                <div className="relative rounded-xl border border-indigo-200/80 dark:border-indigo-800/80 bg-indigo-50/40 dark:bg-indigo-950/20 p-4 transition-all">
                  <div className="flex items-center justify-between pb-2 mb-2 border-b border-indigo-100 dark:border-indigo-900/40 text-[11px] text-indigo-700 dark:text-indigo-300 font-medium">
                    <span className="flex items-center gap-1.5">
                      <Globe className="w-3.5 h-3.5" />
                      {t("translation.translated_badge", { lang: (translatedData.target_language || language).toUpperCase() }) || `Translated via AI to ${(translatedData.target_language || language).toUpperCase()}`}
                    </span>
                    <span className="text-[10px] text-slate-400 dark:text-slate-500 font-normal">
                      {translatedData.source_language ? `${t("translation.source_detected", { lang: translatedData.source_language.toUpperCase() }) || `Detected: ${translatedData.source_language.toUpperCase()}`}` : ""}
                      {translatedData.cached ? " • Cached" : ""}
                    </span>
                  </div>
                  <dd className="text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-normal whitespace-pre-wrap">
                    {translatedData.translated_text}
                  </dd>
                </div>
              ) : (
                <dd className="rounded-xl border border-slate-200/80 dark:border-slate-800 bg-slate-50/70 dark:bg-slate-800/40 p-4 text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-normal whitespace-pre-wrap">
                  {complaint.description}
                </dd>
              )}
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
            <div className="grid gap-3">
              {/* Coordinator 2-Step Action: Start -> Done */}
              {(isCoordinator || isAdmin || isAppManager) && (
                <div className="space-y-3">
                  {statusNormalized === "Complaint Raised" && (
                    <Button
                      type="button"
                      onClick={handleStartWork}
                      variant="primary"
                      className="w-full font-extrabold py-3.5 text-sm flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-md transition-all active:scale-95"
                    >
                      <PlayCircle className="h-5 w-5" />
                      Start
                    </Button>
                  )}

                  {statusNormalized === "Going On" && (
                    <Button
                      type="button"
                      onClick={handleDirectDone}
                      variant="primary"
                      className="w-full font-extrabold py-3.5 text-sm flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl shadow-md transition-all active:scale-95"
                    >
                      <CheckCircle2 className="h-5 w-5" />
                      Done
                    </Button>
                  )}

                  {statusNormalized === "Fixed" && (
                    <div className="w-full py-3 px-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 text-emerald-800 dark:text-emerald-300 font-bold text-center flex items-center justify-center gap-2 text-sm">
                      <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                      Fixed
                    </div>
                  )}
                </div>
              )}

              {/* Student Confirmation Controls when Fixed */}
              {(isOwner || isAdmin) && statusNormalized === "Fixed" && (
                <div className="p-3.5 rounded-xl border border-emerald-200 dark:border-emerald-900/60 bg-emerald-50/50 dark:bg-emerald-950/20 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-emerald-900 dark:text-emerald-100 flex items-center gap-1.5">
                      <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                      Is your issue resolved?
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 pt-1">
                    <Button
                      type="button"
                      variant="success"
                      onClick={handleStudentConfirm}
                      className="font-bold text-xs py-2.5 flex items-center justify-center gap-1.5"
                    >
                      <Check className="h-4 w-4" />
                      Yes, All Fixed
                    </Button>
                    <Button
                      type="button"
                      variant="danger"
                      onClick={() => setShowReopenModal(true)}
                      className="font-bold text-xs py-2.5 flex items-center justify-center gap-1.5"
                    >
                      Not Fixed
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </Card>

          {/* Critical Complaint Emergency Direct Contacts */}
          {(complaint.priority || "").toLowerCase() === "critical" && (
            <Card className="border-rose-200 dark:border-rose-900/60 bg-rose-50/50 dark:bg-rose-950/20 shadow-xs">
              <div className="flex items-center gap-2 mb-3 pb-2.5 border-b border-rose-100 dark:border-rose-900/40">
                <ShieldAlert className="h-4 w-4 text-rose-600 dark:text-rose-400" />
                <div>
                  <h2 className="text-xs font-bold uppercase tracking-wider text-rose-800 dark:text-rose-200">
                    Emergency Direct Contacts
                  </h2>
                  <p className="text-[11px] text-rose-700/80 dark:text-rose-300/80 font-medium mt-0.5">
                    Critical Priority — Designated escalation authorities for immediate response
                  </p>
                </div>
              </div>

              <div className="space-y-3 text-xs">
                {(complaint.emergency_contacts && complaint.emergency_contacts.length > 0) ? (
                  complaint.emergency_contacts.map((contact, idx) => (
                    <div
                      key={idx}
                      className="p-2.5 rounded-xl bg-white dark:bg-slate-900 border border-rose-200/80 dark:border-rose-900/50 flex items-center justify-between gap-3 shadow-2xs"
                    >
                      <div className="min-w-0">
                        <div className="text-[10px] font-bold uppercase tracking-wider text-rose-600 dark:text-rose-400">
                          {contact.role}
                        </div>
                        <div className="font-semibold text-slate-900 dark:text-slate-100 truncate text-xs mt-0.5">
                          {contact.name}
                        </div>
                        <div className="text-[11px] text-slate-500 dark:text-slate-400 font-mono mt-0.5">
                          {contact.phone_available ? contact.phone : "No phone registered"}
                        </div>
                      </div>

                      {contact.phone_available ? (
                        <a
                          href={`tel:${contact.phone}`}
                          className="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-rose-600 hover:bg-rose-700 text-white shadow-xs transition-colors"
                        >
                          <PhoneCall className="h-3.5 w-3.5" />
                          Call
                        </a>
                      ) : (
                        <span className="shrink-0 text-[10px] font-semibold text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-800 px-2 py-1 rounded-md">
                          Phone unavailable
                        </span>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="p-2.5 rounded-lg bg-white/60 dark:bg-slate-900/60 text-center text-rose-700 dark:text-rose-300 text-xs">
                    Authorities notified via priority broadcast
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* Responsible Personnel Card */}
          <ResponsiblePersonnelCard
            complaint={complaint}
            location={location}
            coordinatorUser={coordinatorUser}
            wardenUser={wardenUser}
          />

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
              {(!complaint.due_date || complaint.location_id === "LOC_OTHER" || complaint.department_id === "DEPT_OTHER_GENERAL") && (
                <div className="p-2.5 rounded-lg bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 text-[11px] text-amber-800 dark:text-amber-300">
                  <p className="font-semibold">Informational Submission / Under Review</p>
                  <p className="mt-0.5 text-amber-700 dark:text-amber-400">
                    This complaint was submitted under an unlisted location or category. Standard SLA countdown timers and technician assignment do not apply until an Administrator reviews the information and assigns a department.
                  </p>
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

      {/* Cancellation Reason Modal for Student */}
      {showCancellationModal && (
        <Modal
          isOpen={showCancellationModal}
          onClose={() => setShowCancellationModal(false)}
          title="⚠️ Request Complaint Cancellation"
        >
          <form onSubmit={handleCancellationRequestSubmit} className="space-y-4">
            <p className="text-xs text-slate-500">
              This complaint is currently assigned or in progress. Please explain why you want to cancel it. The assigned coordinator will review and process your request.
            </p>
            <Textarea
              label="Cancellation Reason"
              value={cancellationReasonInput}
              onChange={(e) => setCancellationReasonInput(e.target.value)}
              placeholder="Explain why you wish to cancel this complaint (e.g., issue resolved itself, entered in error, duplicate)..."
              rows={4}
              required
            />
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCancellationModal(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="danger"
                disabled={submittingCancellationRequest}
              >
                {submittingCancellationRequest ? "Submitting..." : "Submit Cancellation Request"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Reject Cancellation Reason Modal for Coordinator */}
      {showRejectCancellationModal && (
        <Modal
          isOpen={showRejectCancellationModal}
          onClose={() => setShowRejectCancellationModal(false)}
          title="❌ Reject Cancellation Request"
        >
          <form onSubmit={handleRejectCancellationSubmit} className="space-y-4">
            <p className="text-xs text-slate-500">
              Please specify the reason for rejecting the student's cancellation request. The complaint will remain active in the workflow.
            </p>
            <Textarea
              label="Rejection Reason"
              value={rejectCancellationReason}
              onChange={(e) => setRejectCancellationReason(e.target.value)}
              placeholder="State why the cancellation request is rejected (e.g. technician is already on site, critical safety hazard cannot be cancelled)..."
              rows={4}
              required
            />
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowRejectCancellationModal(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="danger"
                disabled={submittingRejectCancellation}
              >
                {submittingRejectCancellation ? "Rejecting..." : "Confirm Rejection"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Progress Note Modal */}
      {showProgressModal && (
        <Modal
          isOpen={showProgressModal}
          onClose={() => setShowProgressModal(false)}
          title="📝 Add Progress Note"
        >
          <form onSubmit={handleProgressNoteSubmit} className="space-y-4">
            <p className="text-xs text-slate-500">
              Record real-time field progress or status notes on this work ticket.
            </p>
            <Textarea
              label="Progress Update"
              value={progressNoteText}
              onChange={(e) => setProgressNoteText(e.target.value)}
              placeholder="e.g. Technician arrived, dismantled panel, testing wiring..."
              rows={4}
              required
            />
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowProgressModal(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={submittingProgressNote}
              >
                {submittingProgressNote ? "Saving..." : "Log Progress Note"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Pause / Waiting for Parts Modal */}
      {showPauseModal && (
        <Modal
          isOpen={showPauseModal}
          onClose={() => setShowPauseModal(false)}
          title="⏸️ Pause Work (Waiting for Parts)"
        >
          <form onSubmit={handlePauseSubmit} className="space-y-4">
            <p className="text-xs text-slate-500">
              Temporarily halt active turnaround SLA while waiting for replacement parts or materials.
            </p>
            <Textarea
              label="Parts / Materials Reason"
              value={pauseReasonText}
              onChange={(e) => setPauseReasonText(e.target.value)}
              placeholder="e.g. Awaiting 25A MCB switch delivery from central store..."
              rows={3}
              required
            />
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowPauseModal(false)}
              >
                Cancel
              </Button>
              <Button type="submit" variant="warning" disabled={submittingPause}>
                {submittingPause ? "Pausing..." : "Pause Ticket"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Mark Done / Resolve Modal */}
      {showResolveModal && (
        <Modal
          isOpen={showResolveModal}
          onClose={() => setShowResolveModal(false)}
          title="✅ Mark Work Completed"
        >
          <form onSubmit={handleResolveSubmit} className="space-y-4">
            <p className="text-xs text-slate-500">
              Complete physical repair work and submit for verification.
              {["high", "critical"].includes(
                (complaint?.priority || "").toLowerCase(),
              ) && (
                <span className="block mt-1 font-bold text-amber-600 dark:text-amber-400">
                  ⚠️ High/Critical priority complaints require an "After Repair" photo attachment.
                </span>
              )}
            </p>
            <Textarea
              label="Resolution Notes"
              value={resolveNotesText}
              onChange={(e) => setResolveNotesText(e.target.value)}
              placeholder="Describe work completed, components replaced, or safety tests done..."
              rows={3}
            />
            <div>
              <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                After Repair Photo{" "}
                {["high", "critical"].includes(
                  (complaint?.priority || "").toLowerCase(),
                )
                  ? "(Required)"
                  : "(Recommended)"}
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={(e) =>
                  setResolvePhotoFile(e.target.files?.[0] || null)
                }
                className="block w-full text-xs text-slate-500 file:mr-3 file:py-2 file:px-3 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-primary file:text-white hover:file:bg-primary/90 cursor-pointer"
              />
              {resolvePhotoFile && (
                <p className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium mt-1">
                  Selected: {resolvePhotoFile.name}
                </p>
              )}
            </div>
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowResolveModal(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="success"
                disabled={submittingResolve}
              >
                {submittingResolve ? "Submitting..." : "Submit Resolution"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Warden Verify Modal */}
      {showWardenVerifyModal && (
        <Modal
          isOpen={showWardenVerifyModal}
          onClose={() => setShowWardenVerifyModal(false)}
          title={`🛡️ Warden Verification: ${wardenVerdictChoice}`}
        >
          <div className="space-y-4">
            <p className="text-xs text-slate-500">
              {wardenVerdictChoice === "Verified"
                ? "Confirm in-person inspection of completed work. This will advance the ticket to student confirmation."
                : "Report work as unsatisfactory or issue not fixed. The ticket will return to In Progress for coordinator rework."}
            </p>
            <Textarea
              label={
                wardenVerdictChoice === "Verified"
                  ? "Inspection Notes (Optional)"
                  : "Reason Not Fixed (Required)"
              }
              value={wardenVerdictNotes}
              onChange={(e) => setWardenVerdictNotes(e.target.value)}
              placeholder={
                wardenVerdictChoice === "Verified"
                  ? "e.g. Inspected on-site; wire conduit properly secured and tested."
                  : "e.g. Wire cover plate is missing, corridor switch still sparks..."
              }
              rows={3}
              required={wardenVerdictChoice === "Not Fixed"}
            />
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowWardenVerifyModal(false)}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant={
                  wardenVerdictChoice === "Verified" ? "success" : "danger"
                }
                disabled={
                  submittingWardenVerify ||
                  (wardenVerdictChoice === "Not Fixed" &&
                    !wardenVerdictNotes.trim())
                }
                onClick={() =>
                  handleWardenVerifySubmit(
                    wardenVerdictChoice,
                    wardenVerdictNotes,
                  )
                }
              >
                {submittingWardenVerify
                  ? "Submitting..."
                  : `Confirm ${wardenVerdictChoice}`}
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* Student Reopen Modal */}
      {showStudentReopenModal && (
        <Modal
          isOpen={showStudentReopenModal}
          onClose={() => setShowStudentReopenModal(false)}
          title="⚠️ Report Issue Still Not Fixed"
        >
          <form onSubmit={handleStudentReopenSubmit} className="space-y-4">
            <p className="text-xs text-slate-500">
              Please explain why the issue is not satisfactory. Reopening returns the ticket for coordinator rework.
              <span className="block mt-1 font-bold text-slate-700 dark:text-slate-300">
                Cycle {(complaint?.reopen_count || 0) + 1} of 3. (After 3 reopens, the complaint escalates to Admin Review).
              </span>
            </p>
            <Textarea
              label="Reason Issue Not Fixed"
              value={studentReopenReason}
              onChange={(e) => setStudentReopenReason(e.target.value)}
              placeholder="Explain clearly what is still broken or why the repair is incomplete..."
              rows={4}
              required
            />
            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowStudentReopenModal(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="danger"
                disabled={submittingStudentReopen}
              >
                {submittingStudentReopen ? "Submitting..." : "Reopen Complaint"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {/* Admin Decision Modal */}
      {showAdminDecisionModal && (
        <Modal
          isOpen={showAdminDecisionModal}
          onClose={() => setShowAdminDecisionModal(false)}
          title="⚖️ Admin Review Decision"
        >
          <form onSubmit={handleAdminDecisionSubmit} className="space-y-4">
            <p className="text-xs text-slate-500">
              Disputed complaint review. Choose whether to permanently close the ticket or reopen and reassign.
            </p>
            <Select
              label="Review Action Decision"
              value={adminDecisionChoice}
              onChange={(e) => setAdminDecisionChoice(e.target.value)}
            >
              <option value="Close">Close — Work is acceptable or verified safe</option>
              <option value="Reopen">Reopen — Requires further work and staff reassignment</option>
            </Select>

            {adminDecisionChoice === "Reopen" && (
              <Select
                label="Reassign To Coordinator"
                value={adminReassignCoord}
                onChange={(e) => setAdminReassignCoord(e.target.value)}
                required
              >
                <option value="">Select Coordinator...</option>
                {coordinators.map((c) => (
                  <option key={c.user_id} value={c.user_id}>
                    {c.name} ({c.email})
                  </option>
                ))}
              </Select>
            )}

            <Textarea
              label="Admin Decision Notes"
              value={adminDecisionNotes}
              onChange={(e) => setAdminDecisionNotes(e.target.value)}
              placeholder="State the findings of your investigation and rationale for this decision..."
              rows={4}
              required
            />

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowAdminDecisionModal(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                disabled={submittingAdminDecision}
              >
                {submittingAdminDecision ? "Applying..." : "Submit Admin Decision"}
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

      <AssignModal
        isOpen={showAssignModal}
        onClose={() => setShowAssignModal(false)}
        complaint={complaint}
        onAssigned={(updated) => {
          if (updated && updated.complaint_id) {
            setComplaint(updated);
            setMessage("Complaint assigned successfully!");
          } else {
            load(true);
          }
        }}
      />
    </div>
  );
}

