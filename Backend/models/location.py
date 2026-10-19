from utils.helper import generate_id


LOCATION_TYPES = [
    "Hostel",
    "Academic Block",
    "Mess",
    "Student Activity Center",
    "Sports Complex",
    "Other / Not Sure",
]


class Location:
    def __init__(
        self,
        name,
        location_id=None,
        in_charge_id=None,
        active=True,
        archived=False,
        location_type=None,
        coordinator_id=None,
        archived_by_role=None,
        archived_by=None,
        app_manager_id=None,
        parent_id=None,
        public_complaint_access=None,
        complaint_submission_policy=None,
    ):
        self.location_id = location_id or generate_id("LOC")
        self.name = name
        self.parent_id = parent_id
        self.in_charge_id = in_charge_id
        self.app_manager_id = app_manager_id
        self.active = active
        self.archived = archived
        self.location_type = location_type or self.infer_location_type(name)
        self.coordinator_id = coordinator_id
        self.archived_by_role = archived_by_role
        self.archived_by = archived_by

        # Unified complaint submission policy: 'everyone' vs 'location_only'
        policy = complaint_submission_policy or public_complaint_access
        if policy:
            p_str = str(policy).strip().lower()
            if p_str in ("everyone", "allow_all", "all", "public", "allow_everyone"):
                policy = "everyone"
            elif p_str in ("location_only", "allow_only_location", "restricted", "resident_only", "location"):
                policy = "location_only"
        else:
            policy = "location_only" if self.location_type == "Hostel" else "everyone"
        self.complaint_submission_policy = policy
        self.public_complaint_access = policy

    @staticmethod
    def infer_location_type(name):
        if not name:
            return "Other / Not Sure"
        n = name.lower()
        if "hostel" in n:
            return "Hostel"
        elif "academic" in n:
            return "Academic Block"
        elif "mess" in n:
            return "Mess"
        elif "student activity" in n or "sac" in n:
            return "Student Activity Center"
        elif "sports" in n:
            return "Sports Complex"
        return "Other / Not Sure"

    def to_dict(self):
        return {
            "location_id": self.location_id,
            "name": self.name,
            "location_type": self.location_type,
            "in_charge_id": self.in_charge_id,
            "app_manager_id": self.app_manager_id,
            "coordinator_id": self.coordinator_id,
            "active": self.active,
            "archived": self.archived,
            "archived_by_role": self.archived_by_role,
            "archived_by": self.archived_by,
            "parent_id": self.parent_id,
            "public_complaint_access": self.public_complaint_access,
            "complaint_submission_policy": self.complaint_submission_policy,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["name"],
            data.get("location_id"),
            data.get("in_charge_id"),
            data.get("active", True),
            data.get("archived", False),
            data.get("location_type"),
            data.get("coordinator_id"),
            data.get("archived_by_role"),
            data.get("archived_by"),
            app_manager_id=data.get("app_manager_id"),
            parent_id=data.get("parent_id"),
            public_complaint_access=data.get("public_complaint_access"),
            complaint_submission_policy=data.get("complaint_submission_policy"),
        )


class LocationType:
    def __init__(self, name, type_id=None, description=None):
        self.type_id = type_id or generate_id("LOC_TYPE")
        self.name = name
        self.description = description

    def to_dict(self):
        return {
            "type_id": self.type_id,
            "name": self.name,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["name"],
            data.get("type_id"),
            data.get("description"),
        )
