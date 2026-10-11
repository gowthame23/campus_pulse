from utils.helper import generate_id


class Department:
    def __init__(
        self,
        name,
        sla_days,
        department_id=None,
        complaint_types=None,
        coordinator_id=None,
        active=True,
        archived=False,
        location_id=None,
        archived_by_role=None,
        archived_by=None,
    ):
        self.department_id = department_id or generate_id("DEPT")
        self.name = name
        self.sla_days = int(sla_days)
        self.complaint_types = complaint_types or []
        self.coordinator_id = coordinator_id
        self.active = active
        self.archived = archived
        self.location_id = location_id
        self.archived_by_role = archived_by_role
        self.archived_by = archived_by

    def to_dict(self):
        return {
            "department_id": self.department_id,
            "name": self.name,
            "sla_days": self.sla_days,
            "complaint_types": self.complaint_types,
            "coordinator_id": self.coordinator_id,
            "active": self.active,
            "archived": self.archived,
            "location_id": self.location_id,
            "archived_by_role": self.archived_by_role,
            "archived_by": self.archived_by,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["name"],
            data.get("sla_days", 3),
            data.get("department_id"),
            data.get("complaint_types", []),
            data.get("coordinator_id"),
            data.get("active", True),
            data.get("archived", False),
            data.get("location_id"),
            data.get("archived_by_role"),
            data.get("archived_by"),
        )
