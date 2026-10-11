class DependencyService:
    def __init__(self, auth_service, complaint_service, notification_service):
        self.auth_service = auth_service
        self.complaint_service = complaint_service
        self.notification_service = notification_service

    def can_delete_department(self, department_id):
        complaints = [
            c
            for c in self.complaint_service.list_all()
            if c.department_id == department_id
        ]
        if len(complaints) > 0:
            return False, f"Department has {len(complaints)} existing complaints."
        return True, ""

    def can_delete_location(self, location_id):
        complaints = [
            c for c in self.complaint_service.list_all() if c.location_id == location_id
        ]
        if len(complaints) > 0:
            return False, f"Location has {len(complaints)} existing complaints."
        return True, ""

    def can_archive_location(self, location_id):
        from models.complaint import Complaint

        active_complaints = [
            c
            for c in self.complaint_service.list_all(include_archived=True)
            if c.location_id == location_id
            and c.status not in (Complaint.CLOSED, Complaint.AUTO_CLOSED)
        ]
        if len(active_complaints) > 0:
            return False, f"Location has {len(active_complaints)} active complaints."
        return True, ""
