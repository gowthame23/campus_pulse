class LocationService:
    def __init__(self, auth_service, validation_service, dependency_service):
        self.auth_service = auth_service
        self.validation_service = validation_service
        self.dependency_service = dependency_service

    def list_locations(self, include_archived=False, user_role=None):
        locs = self.auth_service.list_locations()
        if user_role == "student" or not include_archived:
            return [l for l in locs if not l.archived]
        return locs

    def list_location_types(self, include_archived=False, user_role=None):
        types_objects = self.auth_service.list_location_types()
        all_locs = self.list_locations(include_archived=include_archived, user_role=user_role)
        result = []
        for lt in types_objects:
            matching = [l for l in all_locs if (l.location_type or l.infer_location_type(l.name)) == lt.name]
            result.append({
                "type_id": lt.type_id,
                "type_name": lt.name,
                "description": lt.description,
                "locations": matching
            })
        return result

    def create_location_type(self, name, description=None):
        return self.auth_service.create_location_type(name, description=description)

    def get_location(self, location_id):
        loc = self.auth_service.get_location(location_id)
        if not loc:
            raise ValueError("Location not found.")
        return loc

    def create_location(self, name, location_type=None):
        self.validation_service.validate_unique_location_name(name)
        return self.auth_service.create_location(name, location_type=location_type)

    def update_location(self, location_id, name=None, location_type=None, app_manager_id=None, in_charge_id=None, coordinator_id=None, archived=None, archived_by_role=None, archived_by=None):
        loc = self.get_location(location_id)

        if name is not None and name != loc.name:
            self.validation_service.validate_unique_location_name(
                name, exclude_id=location_id
            )
            loc.name = name

        if location_type is not None:
            loc.location_type = location_type

        if app_manager_id is not None:
            if not app_manager_id or app_manager_id == "unassigned":
                self.auth_service.unassign_location_app_manager(location_id)
                loc.app_manager_id = None
            else:
                self.auth_service.assign_location_app_manager(location_id, app_manager_id)
                loc.app_manager_id = app_manager_id

        if in_charge_id is not None:
            if not in_charge_id or in_charge_id == "unassigned":
                self.auth_service.unassign_location_in_charge(location_id)
                loc.in_charge_id = None
            else:
                loc.in_charge_id = in_charge_id
                coord = self.auth_service.get_user(in_charge_id)
                if coord:
                    w_locs = getattr(coord, "assigned_locations", None) or []
                    if location_id not in w_locs:
                        w_locs.append(location_id)
                    coord.assigned_locations = list(set(w_locs))
                    if not getattr(coord, "location_id", None):
                        coord.location_id = location_id
                    self.auth_service.save_user(coord)

        if coordinator_id is not None:
            loc.coordinator_id = coordinator_id

        if archived is not None:
            if archived and not loc.archived:
                can_arch, reason = self.dependency_service.can_archive_location(
                    location_id
                )
                if not can_arch:
                    raise ValueError(f"Cannot archive location. Reason: {reason}")
                loc.archived_by_role = archived_by_role
                loc.archived_by = archived_by
            elif not archived:
                loc.archived_by_role = None
                loc.archived_by = None
            loc.archived = archived
            if archived:
                if getattr(loc, "app_manager_id", None):
                    self.auth_service.unassign_location_app_manager(location_id)
                    loc.app_manager_id = None
                if loc.in_charge_id:
                    self.auth_service.unassign_location_in_charge(location_id)
                    loc.in_charge_id = None
                loc.coordinator_id = None

        self.auth_service.save_location(loc)
        return loc

    def deactivate_location(self, location_id):
        loc = self.get_location(location_id)
        loc.active = False
        loc.status = "Inactive"
        if hasattr(loc, "archived"):
            loc.archived = True
        self.auth_service.save_location(loc)
        return loc

    def delete_location(self, location_id):
        loc = self.get_location(location_id)

        can_delete, reason = self.dependency_service.can_delete_location(location_id)
        if not can_delete:
            return self.deactivate_location(location_id)

        self.auth_service.delete_location_data(location_id)
        return loc
