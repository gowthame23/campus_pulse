import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


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

    def get_location_department_ids(self, location_id: str) -> List[str]:
        with self.auth_service._connect() as conn:
            rows = conn.execute(
                "SELECT department_id FROM location_departments WHERE location_id = ? AND is_active = 1",
                (location_id,),
            ).fetchall()
            return [r["department_id"] for r in rows]

    def list_location_departments(self, location_id: str) -> List[Dict[str, Any]]:
        with self.auth_service._connect() as conn:
            rows = conn.execute(
                """
                SELECT d.* FROM departments d
                JOIN location_departments ld ON d.department_id = ld.department_id
                WHERE ld.location_id = ? AND ld.is_active = 1 AND d.active = 1 AND (d.archived = 0 OR d.archived IS NULL)
                ORDER BY d.name ASC
                """,
                (location_id,),
            ).fetchall()
            return [self.auth_service.repository._row_to_department(r) for r in rows]

    def is_department_associated_with_location(self, location_id: str, department_id: str) -> bool:
        if not location_id or not department_id:
            return False
        with self.auth_service._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM location_departments WHERE location_id = ? AND department_id = ? AND is_active = 1",
                (location_id, department_id),
            ).fetchone()
            return row is not None

    def assign_departments_to_location(
        self,
        location_id: str,
        department_ids: List[str],
        actor_user_id: Optional[str] = None,
        actor_role: Optional[str] = None,
    ) -> List[str]:
        loc = self.get_location(location_id)
        if not loc:
            raise ValueError("Location not found.")

        # App Managers may manage location-department associations only within their authorized locations
        if actor_role and actor_role.lower() == "app_manager":
            if not self.auth_service.is_app_manager_assigned(actor_user_id, location_id):
                raise PermissionError(
                    "Unauthorized: App Managers can only configure departments for locations in their authorized scope."
                )

        clean_ids = []
        seen = set()
        for d in (department_ids or []):
            if d and isinstance(d, str):
                did = d.strip()
                if did and did not in seen:
                    seen.add(did)
                    clean_ids.append(did)

        # Validate that each department exists in the system
        for did in clean_ids:
            dept = self.auth_service.get_department(did)
            if not dept:
                raise ValueError(f"Department '{did}' does not exist.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.auth_service._connect() as conn:
            if not clean_ids:
                conn.execute(
                    "UPDATE location_departments SET is_active = 0 WHERE location_id = ?",
                    (location_id,),
                )
            else:
                placeholders = ",".join(["?"] * len(clean_ids))
                conn.execute(
                    f"UPDATE location_departments SET is_active = 0 WHERE location_id = ? AND department_id NOT IN ({placeholders})",
                    [location_id] + clean_ids,
                )
                for did in clean_ids:
                    row = conn.execute(
                        "SELECT id FROM location_departments WHERE location_id = ? AND department_id = ?",
                        (location_id, did),
                    ).fetchone()
                    if row:
                        conn.execute(
                            "UPDATE location_departments SET is_active = 1 WHERE location_id = ? AND department_id = ?",
                            (location_id, did),
                        )
                    else:
                        map_id = f"LD_{uuid.uuid4().hex[:12]}"
                        conn.execute(
                            """
                            INSERT INTO location_departments (id, location_id, department_id, created_at, created_by, is_active)
                            VALUES (?, ?, ?, ?, ?, 1)
                            """,
                            (map_id, location_id, did, now_str, actor_user_id or "system"),
                        )
            conn.commit()

        return self.get_location_department_ids(location_id)

    def enrich_location_dict(self, loc_dict_or_obj):
        if hasattr(loc_dict_or_obj, "to_dict"):
            d = loc_dict_or_obj.to_dict()
        elif isinstance(loc_dict_or_obj, dict):
            d = dict(loc_dict_or_obj)
        else:
            d = dict(loc_dict_or_obj)
        loc_id = d.get("location_id")
        if loc_id:
            dept_ids = self.get_location_department_ids(loc_id)
            d["department_ids"] = dept_ids
            d["departments"] = self.list_location_departments(loc_id)
        else:
            d["department_ids"] = []
            d["departments"] = []
        return d

    def create_location(
        self,
        name,
        location_type=None,
        public_complaint_access=None,
        complaint_submission_policy=None,
        department_ids=None,
        actor_user_id=None,
        actor_role=None,
    ):
        self.validation_service.validate_unique_location_name(name)
        policy = complaint_submission_policy or public_complaint_access
        if policy and policy not in ("everyone", "location_only"):
            raise ValueError("Invalid complaint submission policy. Must be 'everyone' or 'location_only'.")
        loc = self.auth_service.create_location(
            name,
            location_type=location_type,
            public_complaint_access=policy,
            complaint_submission_policy=policy,
        )
        if department_ids is not None:
            self.assign_departments_to_location(
                loc.location_id,
                department_ids,
                actor_user_id=actor_user_id,
                actor_role=actor_role,
            )
        return loc

    def update_location(
        self,
        location_id,
        name=None,
        location_type=None,
        app_manager_id=None,
        in_charge_id=None,
        coordinator_id=None,
        archived=None,
        archived_by_role=None,
        archived_by=None,
        public_complaint_access=None,
        complaint_submission_policy=None,
        department_ids=None,
        actor_user_id=None,
        actor_role=None,
    ):
        loc = self.get_location(location_id)

        if name is not None and name != loc.name:
            self.validation_service.validate_unique_location_name(
                name, exclude_id=location_id
            )
            loc.name = name

        if location_type is not None:
            loc.location_type = location_type

        policy = complaint_submission_policy if complaint_submission_policy is not None else public_complaint_access
        if policy is not None:
            if policy not in ("everyone", "location_only"):
                raise ValueError("Invalid complaint submission policy. Must be 'everyone' or 'location_only'.")
            loc.complaint_submission_policy = policy
            loc.public_complaint_access = policy

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

        if department_ids is not None:
            self.assign_departments_to_location(
                location_id,
                department_ids,
                actor_user_id=actor_user_id,
                actor_role=actor_role,
            )

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

