from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, EmailStr, ConfigDict


class LoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: Dict
    role: str
    redirect: str
    first_login: bool = False
    permissions: List[str] = []


class ChangePasswordRequest(BaseModel):
    old_password: Optional[str] = None
    current_password: Optional[str] = None
    new_password: str = Field(min_length=8)
    confirm_password: Optional[str] = None


class AdminPasswordResetRequest(BaseModel):
    new_password: str = Field(min_length=8)


class PasswordResetStartRequest(BaseModel):
    email: EmailStr


class PasswordResetStartResponse(BaseModel):
    reset_id: str
    message: str
    simulated_otp: Optional[str] = None


class PasswordResetVerifyRequest(BaseModel):
    reset_id: str
    otp: str


class PasswordResetVerifyResponse(BaseModel):
    reset_token: str
    message: str


class PasswordResetCompleteRequest(BaseModel):
    reset_token: str
    new_password: str = Field(min_length=8)


class AccountActivationRequest(BaseModel):
    activation_token: Optional[str] = None
    token: Optional[str] = None
    password: Optional[str] = None
    new_password: Optional[str] = None
    confirm_password: Optional[str] = None



class UserCreateRequest(BaseModel):
    name: str
    email: EmailStr
    role: str
    password: Optional[str] = Field(None, min_length=8)
    confirm_password: Optional[str] = None
    phone_number: Optional[str] = None
    department_id: Optional[str] = None
    location_id: Optional[str] = None

    # Student specific
    roll_number: Optional[str] = None
    program: Optional[str] = None
    year: Optional[str] = None
    section: Optional[str] = None
    hostel: Optional[str] = None
    block: Optional[str] = None
    room_number: Optional[str] = None

    # Staff specific
    employee_id: Optional[str] = None
    designation: Optional[str] = None
    assigned_locations: Optional[List[str]] = None
    assigned_categories: Optional[List[str]] = None


class UserStatusUpdateRequest(BaseModel):
    status: str
    remarks: Optional[str] = None


class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    phone_number: Optional[str] = None
    profile_photo: Optional[str] = Field(None, max_length=7_000_000)
    status: Optional[str] = None
    department_id: Optional[str] = None
    location_id: Optional[str] = None
    active: Optional[bool] = None

    # Student fields (immutable: roll_number)
    roll_number: Optional[str] = None
    program: Optional[str] = None
    year: Optional[str] = None
    section: Optional[str] = None
    hostel: Optional[str] = None
    block: Optional[str] = None
    room_number: Optional[str] = None

    # Staff fields (immutable: employee_id)
    employee_id: Optional[str] = None
    designation: Optional[str] = None
    assigned_locations: Optional[List[str]] = None
    assigned_categories: Optional[List[str]] = None


class ExcelImportRowReport(BaseModel):
    row_index: int
    identifier: str
    name: str
    email: Optional[str] = None
    role: str
    temporary_password: Optional[str] = None
    activation_token: Optional[str] = None
    activation_link: Optional[str] = None
    activation_token: Optional[str] = None
    activation_link: Optional[str] = None
    action: Optional[str] = "created"
    status: str  # "Success" or "Failed"
    reason: Optional[str] = None


class ExcelImportReportResponse(BaseModel):
    total_rows: int
    success_count: int
    failed_count: int
    report: List[ExcelImportRowReport]


class UserResponse(BaseModel):
    user_id: str
    name: str
    full_name: Optional[str] = None
    email: str
    role: str
    phone_number: Optional[str] = None
    status: str = "Active"
    profile_photo: Optional[str] = None
    first_login: bool = True
    active: bool = True
    department_id: Optional[str] = None
    location_id: Optional[str] = None
    temporary_password: Optional[str] = None
    activation_token: Optional[str] = None
    activation_link: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    last_login: Optional[str] = None
    last_logout: Optional[str] = None
    created_by: Optional[str] = "system"
    is_deleted: Optional[bool] = False
    deleted_at: Optional[str] = None
    deleted_by: Optional[str] = None
    deactivated_by_user_id: Optional[str] = None
    deactivated_by_role: Optional[str] = None
    deactivated_at: Optional[str] = None

    # Student details
    roll_number: Optional[str] = None
    department: Optional[str] = None
    program: Optional[str] = None
    year: Optional[str] = None
    section: Optional[str] = None
    hostel: Optional[str] = None
    block: Optional[str] = None
    room_number: Optional[str] = None

    # Staff details
    employee_id: Optional[str] = None
    designation: Optional[str] = None
    location_name: Optional[str] = None
    department_name: Optional[str] = None
    assigned_locations: Optional[List[str]] = []
    assigned_location_names: Optional[List[str]] = []
    assigned_departments: Optional[List[str]] = []
    assigned_department_names: Optional[List[str]] = []
    coordinator_position: Optional[str] = None
    coordinator_department_id: Optional[str] = None
    coordinator_department_name: Optional[str] = None
    coordinator_slot: Optional[int] = None
    work_memberships_count: Optional[int] = 0
    assigned_categories: Optional[List[str]] = []
    language: Optional[str] = "en"
    safety_blocked_until: Optional[str] = None


class UserResponsibilityUpdateRequest(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    coordinator_type: Optional[str] = None  # "none", "coordinator_1", "coordinator_2"
    department_id: Optional[str] = None


class UserActivityResponse(BaseModel):
    activity_id: str
    user_id: str
    action: str
    performed_by: str
    timestamp: str
    remarks: Optional[str] = ""


class DepartmentCreateRequest(BaseModel):
    name: str
    sla_days: int = Field(gt=0)
    complaint_types: List[str] = []
    description: Optional[str] = None
    location_id: Optional[str] = None
    location_ids: Optional[List[str]] = None


class DepartmentResponse(BaseModel):
    department_id: str
    name: str
    sla_days: int
    complaint_types: List[str]
    description: Optional[str] = None
    coordinator_id: Optional[str] = None
    coordinator_2_id: Optional[str] = None
    active: bool = True
    archived: bool = False
    location_id: Optional[str] = None
    archived_by_role: Optional[str] = None
    archived_by: Optional[str] = None
    operating_locations: Optional[List[Dict[str, Any]]] = []
    location_count: Optional[int] = 0
    eligible_employee_count: Optional[int] = 0
    active_complaints_count: Optional[int] = 0
    coordinator_1: Optional[Dict[str, Any]] = None
    coordinator_2: Optional[Dict[str, Any]] = None
    location_ids: Optional[List[str]] = []


class DepartmentSlaConfigResponse(BaseModel):
    config_id: Optional[str] = None
    department_id: str
    normal_start_time: str = "10:00"
    normal_end_time: str = "16:00"
    normal_duration_hours: int = 72
    medium_start_time: str = "10:00"
    medium_end_time: str = "16:00"
    medium_duration_hours: int = 48
    high_start_time: str = "10:00"
    high_end_time: str = "18:00"
    high_duration_hours: int = 24
    critical_start_time: str = "00:00"
    critical_end_time: str = "23:59"
    critical_duration_hours: int = 4
    app_manager_escalation_hours: int = 24
    admin_escalation_hours: int = 48
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None


class DepartmentSlaConfigUpdateRequest(BaseModel):
    normal_start_time: Optional[str] = "10:00"
    normal_end_time: Optional[str] = "16:00"
    normal_duration_hours: Optional[int] = Field(72, gt=0)
    medium_start_time: Optional[str] = "10:00"
    medium_end_time: Optional[str] = "16:00"
    medium_duration_hours: Optional[int] = Field(48, gt=0)
    high_start_time: Optional[str] = "10:00"
    high_end_time: Optional[str] = "18:00"
    high_duration_hours: Optional[int] = Field(24, gt=0)
    critical_start_time: Optional[str] = "00:00"
    critical_end_time: Optional[str] = "23:59"
    critical_duration_hours: Optional[int] = Field(4, gt=0)
    app_manager_escalation_hours: int = Field(24, gt=0)
    admin_escalation_hours: Optional[int] = Field(None, gt=0)


class LocationCreateDepartmentItem(BaseModel):
    name: str
    sla_days: int = Field(2, gt=0)
    complaint_types: List[str] = []


class LocationCreateRequest(BaseModel):
    name: str
    location_type: Optional[str] = None
    coordinator_id: Optional[str] = None
    departments: Optional[List[Any]] = None
    department_ids: Optional[List[str]] = None
    public_complaint_access: Optional[str] = None
    complaint_submission_policy: Optional[str] = None


class LocationResponse(BaseModel):
    location_id: str
    name: str
    location_type: Optional[str] = None
    app_manager_id: Optional[str] = None
    in_charge_id: Optional[str] = None
    coordinator_id: Optional[str] = None
    active: bool = True
    archived: bool = False
    archived_by_role: Optional[str] = None
    archived_by: Optional[str] = None
    public_complaint_access: Optional[str] = "everyone"
    complaint_submission_policy: Optional[str] = "everyone"
    department_ids: Optional[List[str]] = []
    departments: Optional[List[Dict[str, Any]]] = []


class LocationTypeCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    departments: Optional[List[LocationCreateDepartmentItem]] = None


class LocationTypeGroupResponse(BaseModel):
    type_id: Optional[str] = None
    type_name: str
    description: Optional[str] = None
    locations: list[LocationResponse]


class AssignCoordinatorRequest(BaseModel):
    coordinator_id: str
    confirm_replacement: bool = False


class CoordinatorAssignmentCreateRequest(BaseModel):
    coordinator_id: str
    location_id: str
    department_id: str
    confirm_replacement: bool = False


class AssignLocationAppManagerRequest(BaseModel):
    app_manager_id: Optional[str] = None
    confirm_replacement: bool = False


class AssignLocationInChargeRequest(BaseModel):
    in_charge_id: str
    confirm_replacement: bool = False


class AssignLocationCoordinatorRequest(BaseModel):
    coordinator_id: str
    confirm_replacement: bool = False


class AssignLocationsRequest(BaseModel):
    location_ids: list[str]


class AssignDepartmentsRequest(BaseModel):
    department_ids: list[str]


class EmployeeWorkAssignmentsRequest(BaseModel):
    department_ids: list[str]
    location_ids: list[str]


class ComplaintCreateRequest(BaseModel):
    location_id: str
    department_id: str
    issue_id: Optional[str] = None
    complaint_type: Optional[str] = None
    category: Optional[str] = None
    visibility_type: str = "Private"
    visibility: Optional[str] = None
    title: Optional[str] = Field("", max_length=200)
    description: str = Field(..., max_length=5000)
    attachment_url: Optional[str] = None
    priority: Optional[str] = None
    is_urgent: bool = False
    urgent_reason: Optional[str] = None
    exact_spot: Optional[str] = None


class ComplaintAffectedRequest(BaseModel):
    room_note: Optional[str] = None


class ComplaintStatusRequest(BaseModel):
    status: str


class ComplaintAssignRequest(BaseModel):
    assigned_to: Optional[str] = None
    coordinator_id: Optional[str] = None
    assignee_id: Optional[str] = None
    reason: Optional[str] = None


class ComplaintReturnRequest(BaseModel):
    reason: str


class ComplaintRerouteRequest(BaseModel):
    destination_department_id: str
    reason: str



class ComplaintWrongLocationRequest(BaseModel):
    correct_location_id: str
    note: Optional[str] = None


class ComplaintResolveRequest(BaseModel):
    notes: Optional[str] = ""
    preset_code: Optional[str] = None
    proof_url: Optional[str] = None
    skip_photo: Optional[bool] = False
    photo_skipped: Optional[bool] = False
    photo_skip_reason: Optional[str] = None


class WardenVerifyRequest(BaseModel):
    approved: Optional[bool] = None
    verdict: Optional[str] = None
    notes: Optional[str] = ""
    photo_mismatch: Optional[bool] = False


class AdminDecisionRequest(BaseModel):
    decision: str
    notes: Optional[str] = ""
    reassign_to: Optional[str] = None
    assign_to: Optional[str] = None


class LostFoundModerateRequest(BaseModel):
    reason: str
    action: Optional[str] = "hide"


class ComplaintReopenRequest(BaseModel):
    reason: str


class ComplaintPriorityUpdateRequest(BaseModel):
    priority: str
    reason: str


class EscalateRequest(BaseModel):
    reason: str


class CommentCreateRequest(BaseModel):
    message: str = Field(..., max_length=2000)
    is_internal: Optional[bool] = False


class CommentResponse(BaseModel):
    comment_id: str
    complaint_id: str
    user_id: str
    message: str
    created_at: str
    is_internal: bool = False




class ComplaintResponse(BaseModel):
    complaint_id: str
    created_by: str
    creator_role: str
    location_id: str
    department_id: str
    complaint_type: str
    description: str
    attachment_url: Optional[str] = None
    status: str
    assigned_to: Optional[str] = None
    created_at: str
    updated_at: str
    resolved_at: Optional[str] = None
    verification_due_at: Optional[str] = None
    reopen_count: int
    auto_closed: bool
    escalated: bool
    admin_notified: bool
    resolution_notes: Optional[str] = ""
    verification_reports: List[Dict]
    history: List[Dict]
    archived: bool = False
    due_date: Optional[str] = None
    sla_status: Optional[str] = None
    priority: str = "Medium"
    category: Optional[str] = None
    visibility_type: str = "Private"
    title: str = ""
    affected_count: int = 0
    deletion_requested: Optional[bool] = False
    deletion_requested_by: Optional[str] = None
    deletion_requested_name: Optional[str] = None
    deletion_requested_role: Optional[str] = None
    deletion_reason: Optional[str] = None
    deletion_requested_at: Optional[str] = None

    # Tracking & Lifecycle extensions
    sla_deadline: Optional[str] = None
    assigned_at: Optional[str] = None
    started_at: Optional[str] = None
    fixed_at: Optional[str] = None
    fixed_by: Optional[str] = None
    warden_verified_at: Optional[str] = None
    warden_verified_by: Optional[str] = None
    warden_verdict: Optional[str] = None
    warden_notes: Optional[str] = None
    student_stage_at: Optional[str] = None
    closed_at: Optional[str] = None
    closed_by: Optional[str] = None
    requires_warden_check: Optional[bool] = False
    is_spot_check: Optional[bool] = False
    is_urgent: Optional[bool] = False
    urgent_reason: Optional[str] = None
    exact_spot: Optional[str] = None
    affected_upgraded: Optional[bool] = False
    auto_assigned: Optional[bool] = False
    blocked_reason: Optional[str] = None
    blocked_until: Optional[str] = None
    blocked_at: Optional[str] = None
    sla_reminders_sent: Optional[int] = 0
    escalation_level: Optional[int] = 0
    warden_escalation_level: Optional[int] = 0
    team_location_id: Optional[str] = None
    team_department_id: Optional[str] = None
    admin_review_reason: Optional[str] = None
    admin_decision: Optional[str] = None
    admin_decided_by: Optional[str] = None
    admin_decided_at: Optional[str] = None
    location_name: Optional[str] = None
    department_name: Optional[str] = None
    awaiting_assign_since: Optional[str] = None
    assigned_by: Optional[str] = None
    assign_escalation_level: Optional[int] = 0
    marked_by: Optional[str] = None
    team_id: Optional[str] = None
    returned_reason: Optional[str] = None
    assignee_on_leave_flag: Optional[bool] = False
    assignee_removed_flag: Optional[bool] = False
    assigned_coordinator_name: Optional[str] = None
    assigned_coordinator_id: Optional[str] = None
    location_in_charge_name: Optional[str] = None
    location_in_charge_id: Optional[str] = None
    progress_updates: Optional[List[Dict[str, Any]]] = None
    assigned_employee_name: Optional[str] = None
    assigned_to_name: Optional[str] = None
    team_name: Optional[str] = None
    emergency_contacts: Optional[List[Dict[str, Any]]] = None

    model_config = ConfigDict(extra="allow")


class ComplaintDeleteRequestPayload(BaseModel):
    reason: Optional[str] = ""


class ComplaintCancellationRequestPayload(BaseModel):
    reason: str


class ComplaintCancellationReviewPayload(BaseModel):
    note: Optional[str] = ""


class ComplaintCancellationRejectPayload(BaseModel):
    reason: str


class NotificationCreateRequest(BaseModel):
    receiver_id: str
    title: str
    message: str
    module: Optional[str] = "Complaint"
    notification_type: Optional[str] = "info"
    reference_type: Optional[str] = "Complaint"
    reference_id: Optional[str] = None
    priority: Optional[str] = "Medium"
    expires_at: Optional[str] = None


class NotificationResponse(BaseModel):
    notification_id: str
    receiver_id: Optional[str] = None
    recipient: Optional[str] = None
    sender_id: Optional[str] = None
    module: Optional[str] = "Complaint"
    notification_type: Optional[str] = "info"
    title: Optional[str] = ""
    message: str
    reference_type: Optional[str] = "Complaint"
    reference_id: Optional[str] = None
    complaint_id: Optional[str] = None
    priority: Optional[str] = "Medium"
    is_read: Optional[bool] = False
    read: Optional[bool] = False
    delivery_status: Optional[str] = "Delivered"
    read_at: Optional[str] = None
    expires_at: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class NotificationPreferencesRequest(BaseModel):
    in_app_enabled: Optional[bool] = True
    email_enabled: Optional[bool] = False
    push_enabled: Optional[bool] = False


class NotificationPreferencesResponse(BaseModel):
    preference_id: Optional[str] = None
    user_id: str
    in_app_enabled: bool = True
    email_enabled: bool = False
    push_enabled: bool = False


class AnalyticsResponse(BaseModel):
    total: int
    by_status: Dict[str, int]
    auto_closed: int
    escalated: int
    reopened: int
    unassigned: int
    average_resolution_time: Optional[float] = 0.0
    by_department: Optional[Dict[str, int]] = {}
    by_location: Optional[Dict[str, int]] = {}


def get_role_permissions(role: str) -> List[str]:
    role_lower = (role or "").lower()
    if role_lower == "student":
        return [
            "Login",
            "Create Complaint",
            "View Own Complaints",
            "View Community Complaints",
            "Upload Attachments",
            "Comment",
            "Verify Resolution",
            "Update Own Profile",
        ]
    elif role_lower == "coordinator":
        return [
            "Login",
            "View Assigned Complaints",
            "Update Status",
            "Resolve Complaint",
            "Upload Repair Images",
            "Internal Comments",
            "Public Replies",
        ]
    elif role_lower == "location_in_charge":
        return [
            "Login",
            "View Hostel Complaints",
            "Review Reopened Complaints",
            "Escalate Complaints",
            "View Location Analytics",
        ]
    elif role_lower == "app_manager":
        return [
            "Login",
            "Assign Coordinators",
            "Manage Departments",
            "Manage Locations",
            "Monitor Complaints",
            "View Reports",
            "Manage Wardens",
            "Create Users",
        ]
    elif role_lower == "administrator":
        return [
            "Login",
            "User Management",
            "Role Management",
            "Configuration",
            "Analytics",
            "Reports",
            "Audit Logs",
            "Backup",
            "Restore",
            "Archive",
            "Full Control",
        ]
    return ["Login"]


def user_to_response(user):
    if hasattr(user, "to_dict"):
        data = user.to_dict()
    elif isinstance(user, dict):
        data = user.copy()
    else:
        data = user.__dict__.copy()
    data.pop("password", None)
    temp_pw = getattr(user, "temporary_password", None) or (user.get("temporary_password") if isinstance(user, dict) else None)
    if temp_pw:
        data["temporary_password"] = temp_pw
    return data


def model_to_dict(model):
    if hasattr(model, "to_dict"):
        return model.to_dict()
    return model


class CoordinatorTransferRequest(BaseModel):
    old_coordinator_id: str
    new_coordinator_id: str


class DepartmentUpdateRequest(BaseModel):
    name: Optional[str] = None
    sla_days: Optional[int] = None
    complaint_types: Optional[List[str]] = None
    coordinator_id: Optional[str] = None
    coordinator_2_id: Optional[str] = None
    active: Optional[bool] = None
    archived: Optional[bool] = None
    description: Optional[str] = None
    location_ids: Optional[List[str]] = None


class AssignDepartmentCoordinatorsRequest(BaseModel):
    coordinator_1_id: Optional[str] = None
    coordinator_2_id: Optional[str] = None


class AssignLocationsToDepartmentRequest(BaseModel):
    location_ids: List[str]


class AssignDepartmentsToLocationRequest(BaseModel):
    department_ids: List[str]


class LocationUpdateRequest(BaseModel):
    name: Optional[str] = None
    location_type: Optional[str] = None
    app_manager_id: Optional[str] = None
    in_charge_id: Optional[str] = None
    coordinator_id: Optional[str] = None
    active: Optional[bool] = None
    archived: Optional[bool] = None
    public_complaint_access: Optional[str] = None
    complaint_submission_policy: Optional[str] = None
    department_ids: Optional[List[str]] = None


class ComplaintUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    location_id: Optional[str] = None
    department_id: Optional[str] = None
    complaint_type: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = Field(None, max_length=5000)
    attachment_url: Optional[str] = None
    visibility_type: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    archived: Optional[bool] = None


class SettingItemUpdateRequest(BaseModel):
    setting_key: Optional[str] = None
    setting_value: Any
    reason: Optional[str] = ""


class BulkSettingsUpdateRequest(BaseModel):
    settings: List[SettingItemUpdateRequest]
    reason: Optional[str] = ""
    admin_password: Optional[str] = (
        None  # Re-authentication confirmation for sensitive changes
    )


class AttachmentResponse(BaseModel):
    attachment_id: str
    complaint_id: str
    uploaded_by: str
    uploader_role: str
    category: str
    original_filename: str
    stored_filename: str
    file_path: str
    file_size: int
    uploaded_at: str
    source: Optional[str] = "gallery"
    sha256: Optional[str] = None
    exif_taken_at: Optional[str] = None
    kind: Optional[str] = None
    flags: Optional[Any] = None


class ComplaintFeedbackRequest(BaseModel):
    rating: int = Field(..., ge=-1, le=5)
    thank_you_note: Optional[str] = ""


class SafetyReportCreateRequest(BaseModel):
    category: str = Field(..., max_length=100)
    description: str = Field(..., max_length=5000)


class SafetyReportMessageRequest(BaseModel):
    body: str = Field(..., max_length=3000)


class SafetyReportDecisionRequest(BaseModel):
    outcome: str = Field(..., description="action_taken | could_not_confirm | not_a_safety_issue | false_misuse")
    notes: Optional[str] = ""


class SafetyReportRevealRequest(BaseModel):
    admin_password: str = Field(..., min_length=1, description="Admin account password for step-up re-authentication")
    reason: str = Field(..., min_length=5, description="Mandatory reason for reveal under abuse investigation")


class CreateLocationFromSpotRequest(BaseModel):
    location_id: str
    exact_spot: str
    child_name: Optional[str] = None


class LanguageUpdateRequest(BaseModel):
    language: str = Field(..., pattern="^(en|te|hi)$", description="Preferred language code: en, te, or hi")


class TeamCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    department_id: str
    coordinator_id: str
    backup_coordinator_id: Optional[str] = None
    location_ids: List[str] = Field(default_factory=list)
    member_ids: List[str] = Field(default_factory=list)


class TeamUpdateRequest(BaseModel):
    name: Optional[str] = None
    department_id: Optional[str] = None
    coordinator_id: Optional[str] = None
    backup_coordinator_id: Optional[str] = None
    location_ids: Optional[List[str]] = None
    member_ids: Optional[List[str]] = None
    active: Optional[bool] = None


class WorkMembershipCreateRequest(BaseModel):
    user_id: str
    department_id: str
    location_id: str


class LeaveCreateRequest(BaseModel):
    user_id: Optional[str] = None
    from_date: str = Field(..., description="YYYY-MM-DD")
    to_date: str = Field(..., description="YYYY-MM-DD")
    reason: Optional[str] = None
    department_id: Optional[str] = None


class EmergencyCategoryCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    department_id: Optional[str] = None
    sort_order: Optional[int] = 0
    is_active: Optional[bool] = True


class EmergencyCategoryUpdateRequest(BaseModel):
    name: Optional[str] = None
    department_id: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class EmergencyContactCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    phone: str = Field(..., min_length=3, max_length=50)
    department_id: Optional[str] = None
    location_id: Optional[str] = None
    user_id: Optional[str] = None
    sort_order: Optional[int] = 0
    active: Optional[bool] = True
    night_only: Optional[bool] = False
    day_only: Optional[bool] = False


class EmergencyContactUpdateRequest(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    department_id: Optional[str] = None
    location_id: Optional[str] = None
    user_id: Optional[str] = None
    sort_order: Optional[int] = None
    active: Optional[bool] = None
    night_only: Optional[bool] = None
    day_only: Optional[bool] = None


class EmergencyCreateRequest(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    location_id: Optional[str] = None


class EmergencyReachedRequest(BaseModel):
    reached: bool


class EmergencyOutcomeRequest(BaseModel):
    outcome: str = Field(..., description="real | mistake | misuse")

