from utils.helper import add_days_string, generate_id, now_string


class Complaint:
    SUBMITTED = "Submitted"
    PENDING = "Pending"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    WAITING_VERIFICATION = "Waiting for Verification"
    CLOSED = "Closed"
    AUTO_CLOSED = "Closed (Auto Closed)"
    REOPENED = "Reopened"
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
        self.status = status or self.PENDING
        self.assigned_to = assigned_to
        self.created_at = created_at or now_string()
        self.updated_at = updated_at or self.created_at
        self.resolved_at = resolved_at
        self.verification_due_at = verification_due_at
        self.reopen_count = int(reopen_count)
        self.auto_closed = bool(auto_closed)
        self.escalated = bool(escalated)
        self.admin_notified = bool(admin_notified)
        self.resolution_notes = resolution_notes
        self.verification_reports = verification_reports or []
        self.history = history or []
        self.priority = priority
        self.category = category or complaint_type or "General"
        self.visibility_type = visibility_type
        self.title = title

    def add_history(self, message):
        self.updated_at = now_string()
        self.history.append({"at": self.updated_at, "message": message})

    def assign(self, coordinator_id):
        self.assigned_to = coordinator_id
        self.status = self.ASSIGNED
        self.add_history(f"Assigned to {coordinator_id}.")

    def start_progress(self):
        self.status = self.IN_PROGRESS
        self.add_history("Work moved to in progress.")

    def mark_resolved(self, notes=""):
        self.status = self.WAITING_VERIFICATION
        self.resolved_at = now_string()
        self.verification_due_at = add_days_string(5)
        self.resolution_notes = notes
        self.add_history("Complaint resolved; waiting for verification.")

    def close(self, verifier_id):
        self.status = self.CLOSED
        self.add_history(f"Closed after verification by {verifier_id}.")

    def auto_close(self):
        self.status = self.AUTO_CLOSED
        self.auto_closed = True
        at = now_string()
        date = at[:10]
        time = at[11:19]
        self.add_history(
            f"Automatically Closed. Date: {date}, Time: {time}, Reason: Auto closed after 5 days without verification."
        )

    def reopen(self, reporter_id, reason):
        self.status = self.REOPENED
        self.reopen_count += 1
        self.verification_due_at = None
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
        d["priority"] = getattr(self, "priority", "Medium")
        d["category"] = getattr(self, "category", self.complaint_type or "General")
        d["visibility_type"] = getattr(self, "visibility_type", "Private")
        d["title"] = getattr(self, "title", "")
        d["deletion_requested"] = getattr(self, "deletion_requested", False)
        d["deletion_requested_by"] = getattr(self, "deletion_requested_by", None)
        d["deletion_requested_name"] = getattr(self, "deletion_requested_name", None)
        d["deletion_requested_role"] = getattr(self, "deletion_requested_role", None)
        d["deletion_reason"] = getattr(self, "deletion_reason", None)
        d["deletion_requested_at"] = getattr(self, "deletion_requested_at", None)
        return d

    @classmethod
    def from_dict(cls, data):
        c = cls(
            data["created_by"],
            data["creator_role"],
            data["location_id"],
            data["department_id"],
            data["complaint_type"],
            data["description"],
            data.get("complaint_id"),
            data.get("status"),
            data.get("assigned_to"),
            data.get("created_at"),
            data.get("updated_at"),
            data.get("resolved_at"),
            data.get("verification_due_at"),
            data.get("reopen_count", 0),
            data.get("auto_closed", False),
            data.get("escalated", False),
            data.get("admin_notified", False),
            data.get("resolution_notes", ""),
            data.get("verification_reports", []),
            data.get("history", []),
            data.get("archived", False),
            data.get("attachment_url"),
            priority=data.get("priority", "Medium"),
            category=data.get("category", data.get("complaint_type", "General")),
            visibility_type=data.get("visibility_type", "Private"),
            title=data.get("title", ""),
        )
        c.deletion_requested = data.get("deletion_requested", False)
        c.deletion_requested_by = data.get("deletion_requested_by")
        c.deletion_requested_name = data.get("deletion_requested_name")
        c.deletion_requested_role = data.get("deletion_requested_role")
        c.deletion_reason = data.get("deletion_reason")
        c.deletion_requested_at = data.get("deletion_requested_at")
        return c
