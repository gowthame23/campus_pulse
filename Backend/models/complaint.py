from core.constants import (
    AUTO_CLOSE_HOURS,
    STATUS_ADMIN_REVIEW,
    STATUS_ASSIGNED,
    STATUS_AUTO_CLOSED,
    STATUS_BLOCKED,
    STATUS_CANCELLED,
    STATUS_CANCELLATION_REQUESTED,
    STATUS_CLOSED,
    STATUS_IN_PROGRESS,
    STATUS_PENDING_WARDEN,
    STATUS_REJECTED,
    STATUS_REOPENED,
    STATUS_SUBMITTED,
    STATUS_WAITING_STUDENT,
    normalize_priority,
)
from utils.helper import add_days_string, generate_id, now_string


class Complaint:
    SUBMITTED = STATUS_SUBMITTED
    PENDING = STATUS_SUBMITTED
    ASSIGNED = STATUS_ASSIGNED
    IN_PROGRESS = STATUS_IN_PROGRESS
    RESOLVED = "Resolved"
    BLOCKED = STATUS_BLOCKED
    WAITING_VERIFICATION = STATUS_WAITING_STUDENT
    PENDING_WARDEN_VERIFICATION = STATUS_PENDING_WARDEN
    CLOSED = STATUS_CLOSED
    AUTO_CLOSED = STATUS_AUTO_CLOSED
    REOPENED = STATUS_REOPENED
    ADMIN_REVIEW = STATUS_ADMIN_REVIEW
    REJECTED = STATUS_REJECTED
    CANCELLED = STATUS_CANCELLED
    CANCELLATION_REQUESTED = STATUS_CANCELLATION_REQUESTED
    STATUS_CANCELLATION_REQUESTED = STATUS_CANCELLATION_REQUESTED
    AWAITING_ASSIGNMENT = "Awaiting Coordinator Assignment"

    def __init__(
        self,
        created_by,
        creator_role,
        location_id,
        department_id,
        complaint_type,
        description,
        complaint_id=None,
        status=None,
        assigned_to=None,
        created_at=None,
        updated_at=None,
        resolved_at=None,
        verification_due_at=None,
        reopen_count=0,
        auto_closed=False,
        escalated=False,
        admin_notified=False,
        resolution_notes="",
        verification_reports=None,
        history=None,
        archived=False,
        attachment_url=None,
        priority="Medium",
        category=None,
        visibility_type="Private",
        title="",
        sla_deadline=None,
        assigned_at=None,
        started_at=None,
        auto_assigned=False,
        blocked_reason=None,
        blocked_until=None,
        blocked_at=None,
        sla_reminders_sent=0,
        escalation_level=0,
        warden_escalation_level=0,
        team_location_id=None,
        team_department_id=None,
        is_urgent=False,
        urgent_reason=None,
        fixed_at=None,
        fixed_by=None,
        warden_verified_at=None,
        warden_verified_by=None,
        warden_verdict=None,
        warden_notes=None,
        student_stage_at=None,
        closed_at=None,
        closed_by=None,
        requires_warden_check=False,
        is_spot_check=False,
        auto_close_reminded=False,
        admin_review_reason=None,
        admin_decision=None,
        admin_decided_by=None,
        admin_decided_at=None,
        deletion_requested=False,
        deletion_requested_by=None,
        deletion_requested_name=None,
        deletion_requested_role=None,
        deletion_reason=None,
        deletion_requested_at=None,
        wrong_location_corrected_at=None,
        wrong_location_corrections=0,
        last_progress_code=None,
        photo_skipped=False,
        photo_skip_reason=None,
        reopen_notes=None,
        resolution_proof_url=None,
        affected_upgraded=False,
        exact_spot=None,
        awaiting_assign_since=None,
        assigned_by=None,
        assign_escalation_level=0,
        marked_by=None,
        team_id=None,
        returned_reason=None,
        assignee_on_leave_flag=False,
        assignee_removed_flag=False,
        is_emergency=False,
        emergency_category=None,
        reached=None,
        reached_at=None,
        acknowledged_by=None,
        acknowledged_at=None,
        emergency_outcome=None,
        emergency_realert_sent=False,
        is_deleted=False,
        deleted_at=None,
        deleted_by=None,
        cancellation_requested=False,
        cancellation_requested_by=None,
        cancellation_reason=None,
        cancellation_requested_at=None,
        cancellation_decided_by=None,
        cancellation_decided_at=None,
        cancellation_decision_note=None,
        previous_status=None,
    ):
        self.complaint_id = complaint_id or generate_id("CMP")
        self.archived = bool(archived)
        self.created_by = created_by
        self.creator_role = creator_role
        self.location_id = location_id
        self.department_id = department_id
        self.complaint_type = complaint_type
        self.description = description
        self.attachment_url = attachment_url
        self.status = status or self.SUBMITTED
        self.assigned_to = assigned_to
        self.created_at = created_at or now_string()
        self.updated_at = updated_at or self.created_at
        self.resolved_at = resolved_at
        self.verification_due_at = verification_due_at
        self.reopen_count = int(reopen_count)
        self.auto_closed = bool(auto_closed)
        self.escalated = bool(escalated)
        self.admin_notified = bool(admin_notified)
        self.resolution_notes = resolution_notes or ""
        self.verification_reports = verification_reports or []
        self.history = history or []
        self.priority = normalize_priority(priority)
        self.category = category or complaint_type or "General"
        self.visibility_type = visibility_type
        self.title = title or ""

        # Tracking and Workflow extensions
        self.sla_deadline = sla_deadline
        self.assigned_at = assigned_at
        self.started_at = started_at
        self.auto_assigned = bool(auto_assigned)
        self.blocked_reason = blocked_reason
        self.blocked_until = blocked_until
        self.blocked_at = blocked_at
        self.sla_reminders_sent = int(sla_reminders_sent)
        self.escalation_level = int(escalation_level)
        self.warden_escalation_level = int(warden_escalation_level)
        self.team_location_id = team_location_id
        self.team_department_id = team_department_id
        self.is_urgent = bool(is_urgent)
        self.urgent_reason = urgent_reason
        self.fixed_at = fixed_at
        self.fixed_by = fixed_by
        self.warden_verified_at = warden_verified_at
        self.warden_verified_by = warden_verified_by
        self.warden_verdict = warden_verdict
        self.warden_notes = warden_notes
        self.student_stage_at = student_stage_at
        self.closed_at = closed_at
        self.closed_by = closed_by
        self.requires_warden_check = bool(requires_warden_check)
        self.is_spot_check = bool(is_spot_check)
        self.auto_close_reminded = bool(auto_close_reminded)
        self.admin_review_reason = admin_review_reason
        self.admin_decision = admin_decision
        self.admin_decided_by = admin_decided_by
        self.admin_decided_at = admin_decided_at
        self.deletion_requested = bool(deletion_requested)
        self.deletion_requested_by = deletion_requested_by
        self.deletion_requested_name = deletion_requested_name
        self.deletion_requested_role = deletion_requested_role
        self.deletion_reason = deletion_reason
        self.deletion_requested_at = deletion_requested_at
        self.wrong_location_corrected_at = wrong_location_corrected_at
        self.wrong_location_corrections = int(wrong_location_corrections or 0)
        self.last_progress_code = last_progress_code
        self.photo_skipped = bool(photo_skipped)
        self.photo_skip_reason = photo_skip_reason
        self.reopen_notes = reopen_notes
        self.resolution_proof_url = resolution_proof_url
        self.affected_upgraded = bool(affected_upgraded)
        self.exact_spot = exact_spot
        self.awaiting_assign_since = awaiting_assign_since
        self.assigned_by = assigned_by
        self.assign_escalation_level = int(assign_escalation_level or 0)
        self.marked_by = marked_by
        self.team_id = team_id
        self.returned_reason = returned_reason
        self.assignee_on_leave_flag = bool(assignee_on_leave_flag)
        self.assignee_removed_flag = bool(assignee_removed_flag)
        self.is_emergency = bool(is_emergency)
        self.emergency_category = emergency_category
        self.reached = reached
        self.reached_at = reached_at
        self.acknowledged_by = acknowledged_by
        self.acknowledged_at = acknowledged_at
        self.emergency_outcome = emergency_outcome
        self.emergency_realert_sent = bool(emergency_realert_sent)
        self.is_deleted = bool(is_deleted)
        self.deleted_at = deleted_at
        self.deleted_by = deleted_by
        self.cancellation_requested = bool(cancellation_requested)
        self.cancellation_requested_by = cancellation_requested_by
        self.cancellation_reason = cancellation_reason
        self.cancellation_requested_at = cancellation_requested_at
        self.cancellation_decided_by = cancellation_decided_by
        self.cancellation_decided_at = cancellation_decided_at
        self.cancellation_decision_note = cancellation_decision_note
        self.previous_status = previous_status

    def add_history(self, message):
        self.updated_at = now_string()
        self.history.append({"at": self.updated_at, "message": message})

    def assign(self, coordinator_id):
        self.assigned_to = coordinator_id
        self.assigned_at = now_string()
        self.status = self.ASSIGNED
        self.add_history(f"Assigned to {coordinator_id}.")

    def start_progress(self):
        self.status = self.IN_PROGRESS
        self.started_at = now_string()
        self.add_history("Work started by coordinator.")

    def mark_resolved(self, notes=""):
        self.status = self.WAITING_VERIFICATION
        self.resolved_at = now_string()
        self.fixed_at = self.resolved_at
        self.resolution_notes = notes or ""
        self.add_history("Complaint marked done; waiting for verification.")

    def close(self, verifier_id):
        self.status = self.CLOSED
        self.closed_at = now_string()
        self.closed_by = verifier_id
        self.add_history(f"Closed after verification by {verifier_id}.")

    def auto_close(self):
        self.status = self.AUTO_CLOSED
        self.auto_closed = True
        self.closed_at = now_string()
        self.closed_by = "System Auto-Close"
        at = self.closed_at
        date = at[:10]
        time = at[11:19]
        self.add_history(
            f"Automatically Closed. Date: {date}, Time: {time}, Reason: Auto closed after {AUTO_CLOSE_HOURS} hours without verification."
        )

    def reopen(self, reporter_id, reason):
        self.status = self.REOPENED
        self.reopen_count += 1
        self.verification_due_at = None
        self.student_stage_at = None
        self.auto_close_reminded = False
        self.verification_reports.append(
            {
                "by": reporter_id,
                "result": "Not Fixed",
                "reason": reason,
                "at": now_string(),
            }
        )
        self.add_history(f"Reopened by {reporter_id}: {reason}")

    def to_dict(self):
        d = self.__dict__.copy()
        d["priority"] = normalize_priority(getattr(self, "priority", "Medium"))
        d["category"] = getattr(self, "category", self.complaint_type or "General")
        d["visibility_type"] = getattr(self, "visibility_type", "Private")
        d["title"] = getattr(self, "title", "")
        return d

    @classmethod
    def from_dict(cls, data):
        c = cls(
            created_by=data["created_by"],
            creator_role=data["creator_role"],
            location_id=data["location_id"],
            department_id=data["department_id"],
            complaint_type=data["complaint_type"],
            description=data["description"],
            complaint_id=data.get("complaint_id"),
            status=data.get("status"),
            assigned_to=data.get("assigned_to"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            resolved_at=data.get("resolved_at"),
            verification_due_at=data.get("verification_due_at"),
            reopen_count=data.get("reopen_count", 0),
            auto_closed=data.get("auto_closed", False),
            escalated=data.get("escalated", False),
            admin_notified=data.get("admin_notified", False),
            resolution_notes=data.get("resolution_notes", ""),
            verification_reports=data.get("verification_reports", []),
            history=data.get("history", []),
            archived=data.get("archived", False),
            attachment_url=data.get("attachment_url"),
            priority=data.get("priority", "Medium"),
            category=data.get("category", data.get("complaint_type", "General")),
            visibility_type=data.get("visibility_type", "Private"),
            title=data.get("title", ""),
            sla_deadline=data.get("sla_deadline"),
            assigned_at=data.get("assigned_at"),
            started_at=data.get("started_at"),
            auto_assigned=data.get("auto_assigned", False),
            blocked_reason=data.get("blocked_reason"),
            blocked_until=data.get("blocked_until"),
            blocked_at=data.get("blocked_at"),
            sla_reminders_sent=data.get("sla_reminders_sent", 0),
            escalation_level=data.get("escalation_level", 0),
            warden_escalation_level=data.get("warden_escalation_level", 0),
            team_location_id=data.get("team_location_id"),
            team_department_id=data.get("team_department_id"),
            is_urgent=data.get("is_urgent", False),
            urgent_reason=data.get("urgent_reason"),
            fixed_at=data.get("fixed_at"),
            fixed_by=data.get("fixed_by"),
            warden_verified_at=data.get("warden_verified_at"),
            warden_verified_by=data.get("warden_verified_by"),
            warden_verdict=data.get("warden_verdict"),
            warden_notes=data.get("warden_notes"),
            student_stage_at=data.get("student_stage_at"),
            closed_at=data.get("closed_at"),
            closed_by=data.get("closed_by"),
            requires_warden_check=data.get("requires_warden_check", False),
            is_spot_check=data.get("is_spot_check", False),
            auto_close_reminded=data.get("auto_close_reminded", False),
            admin_review_reason=data.get("admin_review_reason"),
            admin_decision=data.get("admin_decision"),
            admin_decided_by=data.get("admin_decided_by"),
            admin_decided_at=data.get("admin_decided_at"),
            deletion_requested=data.get("deletion_requested", False),
            deletion_requested_by=data.get("deletion_requested_by"),
            deletion_requested_name=data.get("deletion_requested_name"),
            deletion_requested_role=data.get("deletion_requested_role"),
            deletion_reason=data.get("deletion_reason"),
            deletion_requested_at=data.get("deletion_requested_at"),
            wrong_location_corrected_at=data.get("wrong_location_corrected_at"),
            wrong_location_corrections=data.get("wrong_location_corrections", 0),
            last_progress_code=data.get("last_progress_code"),
            photo_skipped=data.get("photo_skipped", False),
            photo_skip_reason=data.get("photo_skip_reason"),
            reopen_notes=data.get("reopen_notes"),
            resolution_proof_url=data.get("resolution_proof_url"),
            affected_upgraded=data.get("affected_upgraded", False),
            exact_spot=data.get("exact_spot"),
            awaiting_assign_since=data.get("awaiting_assign_since"),
            assigned_by=data.get("assigned_by"),
            assign_escalation_level=data.get("assign_escalation_level", 0),
            marked_by=data.get("marked_by"),
            team_id=data.get("team_id"),
            returned_reason=data.get("returned_reason"),
            assignee_on_leave_flag=data.get("assignee_on_leave_flag", False),
            assignee_removed_flag=data.get("assignee_removed_flag", False),
            is_emergency=data.get("is_emergency", False),
            emergency_category=data.get("emergency_category"),
            reached=data.get("reached"),
            reached_at=data.get("reached_at"),
            acknowledged_by=data.get("acknowledged_by"),
            acknowledged_at=data.get("acknowledged_at"),
            emergency_outcome=data.get("emergency_outcome"),
            emergency_realert_sent=data.get("emergency_realert_sent", False),
            is_deleted=data.get("is_deleted", False),
            deleted_at=data.get("deleted_at"),
            deleted_by=data.get("deleted_by"),
            cancellation_requested=data.get("cancellation_requested", False),
            cancellation_requested_by=data.get("cancellation_requested_by"),
            cancellation_reason=data.get("cancellation_reason"),
            cancellation_requested_at=data.get("cancellation_requested_at"),
            cancellation_decided_by=data.get("cancellation_decided_by"),
            cancellation_decided_at=data.get("cancellation_decided_at"),
            cancellation_decision_note=data.get("cancellation_decision_note"),
            previous_status=data.get("previous_status"),
        )
        return c
