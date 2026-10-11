from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import (
    get_audit_service,
    get_auth_service,
    get_department_service,
    get_location_service,
)
from api.schemas import (
    AssignLocationAppManagerRequest,
    AssignLocationInChargeRequest,
    AssignLocationCoordinatorRequest,
    LocationCreateRequest,
    LocationResponse,
    LocationTypeCreateRequest,
    LocationTypeGroupResponse,
    LocationUpdateRequest,
    model_to_dict,
)
from api.security import get_current_user, require_roles
from models.administrator import Administrator
from models.app_manager import AppManager

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/in-charge/assignments")
def get_location_in_charge_assignments(
    current_user=Depends(get_current_user),
    auth_service=Depends(get_auth_service),
):
    return auth_service.get_location_in_charge_assignments()


@router.get("", response_model=list[LocationResponse])
def list_locations(
    include_archived: bool = False,
    current_user=Depends(get_current_user),
    location_service=Depends(get_location_service),
):
    locs = location_service.list_locations(
        include_archived=include_archived, user_role=current_user.role
    )
    role = (current_user.role or "").lower()
    if role == AppManager.ROLE.lower():
        locs = [
            l for l in locs
            if location_service.auth_service.is_app_manager_assigned(current_user.user_id, l.location_id)
        ]
    elif role == "location_in_charge":
        locs = [
            l for l in locs
            if location_service.auth_service.is_warden_assigned(current_user.user_id, l.location_id)
        ]
    elif role == "coordinator":
        # is_coordinator_assigned() checks one specific (location, department)
        # pair; a location-level list has no single department in context, so
        # check the coordinator's own assignments for any department match on
        # each location instead — same authorization data, no new mechanism.
        coord_assignments = location_service.auth_service.list_coordinator_assignments(
            coordinator_id=current_user.user_id
        )
        locs = [
            l for l in locs
            if any(
                location_service.auth_service.is_coordinator_assigned(
                    current_user.user_id, l.location_id, asgn["department_id"]
                )
                for asgn in coord_assignments
            )
        ]

    def _enrich_loc(loc, auth_service):
        d = model_to_dict(loc)
        d["app_manager_id"] = auth_service.get_location_app_manager_id(loc.location_id)
        return d

    return [_enrich_loc(l, location_service.auth_service) for l in locs]


@router.get("/types", response_model=list[LocationTypeGroupResponse])
def list_location_types(
    include_archived: bool = False,
    current_user=Depends(get_current_user),
    location_service=Depends(get_location_service),
):
    groups = location_service.list_location_types(
        include_archived=include_archived, user_role=current_user.role
    )
    def _enrich_loc(loc, auth_service):
        d = model_to_dict(loc)
        d["app_manager_id"] = auth_service.get_location_app_manager_id(loc.location_id)
        return d

    return [
        {
            "type_id": g.get("type_id"),
            "type_name": g["type_name"],
            "description": g.get("description"),
            "locations": [_enrich_loc(l, location_service.auth_service) for l in g["locations"]],
        }
        for g in groups
    ]


@router.post("/types", status_code=status.HTTP_201_CREATED)
def create_location_type(
    payload: LocationTypeCreateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    location_service=Depends(get_location_service),
    department_service=Depends(get_department_service),
):
    try:
        lt = location_service.create_location_type(
            payload.name, description=payload.description
        )
        if payload.departments:
            for dept_item in payload.departments:
                try:
                    department_service.create_department(
                        dept_item.name, dept_item.sla_days, dept_item.complaint_types, location_id=payload.name
                    )
                except Exception:
                    pass
        return model_to_dict(lt)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    except Exception as error:
        if hasattr(error, "status_code"):
            raise error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/{location_id}", response_model=LocationResponse)
def get_location(
    location_id: str,
    current_user=Depends(get_current_user),
    location_service=Depends(get_location_service),
):
    role = (current_user.role or "").lower()
    if role == AppManager.ROLE.lower():
        if not location_service.auth_service.is_app_manager_assigned(current_user.user_id, location_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="App Manager cannot access locations outside assigned scope.",
            )
    elif role == "location_in_charge":
        if not location_service.auth_service.is_warden_assigned(current_user.user_id, location_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Location In-Charge / Warden cannot access unassigned locations.",
            )
    elif role == "coordinator":
        coord_assignments = location_service.auth_service.list_coordinator_assignments(
            coordinator_id=current_user.user_id
        )
        is_assigned = any(
            location_service.auth_service.is_coordinator_assigned(
                current_user.user_id, location_id, asgn["department_id"]
            )
            for asgn in coord_assignments
        )
        if not is_assigned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Coordinator cannot access unassigned locations.",
            )
    try:
        location = location_service.get_location(location_id)
        return model_to_dict(location)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(
    payload: LocationCreateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    location_service=Depends(get_location_service),
    department_service=Depends(get_department_service),
):
    try:
        location = location_service.create_location(
            payload.name, location_type=payload.location_type
        )
        # Auto-assign App Manager, Warden, and Coordinator so new locations reflect across all dashboards
        try:
            location_service.auth_service.assign_location_app_manager(location.location_id, "USR_MANAGER")
            if (current_user.role or "").lower() == AppManager.ROLE.lower() and current_user.user_id != "USR_MANAGER":
                location_service.auth_service.assign_location_app_manager(location.location_id, current_user.user_id)
            location_service.update_location(location.location_id, in_charge_id="USR_WARDEN")
            location_service.auth_service.assign_location_coordinator(location.location_id, "USR_COORDINATOR")
        except Exception:
            pass

        # Create department records for this specific location if provided
        if payload.departments:
            for dept_item in payload.departments:
                try:
                    department_service.create_department(
                        dept_item.name, dept_item.sla_days, dept_item.complaint_types, location_id=location.location_id
                    )
                except Exception:
                    pass

        return model_to_dict(location)
    except Exception as error:
        if hasattr(error, "status_code"):
            raise error
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


@router.post("/{location_id}/app-manager")
def assign_location_app_manager(
    location_id: str,
    payload: AssignLocationAppManagerRequest,
    current_user=Depends(require_roles(Administrator.ROLE)),
    auth_service=Depends(get_auth_service),
):
    loc = auth_service.get_location(location_id)
    if not loc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found."
        )

    if not payload.app_manager_id or payload.app_manager_id.lower() == "unassigned":
        auth_service.unassign_location_app_manager(location_id)
        return {"message": "Location App Manager unassigned."}

    auth_service.assign_location_app_manager(location_id, payload.app_manager_id)
    return {"message": "Location App Manager assigned."}


@router.delete("/{location_id}/app-manager")
def unassign_location_app_manager(
    location_id: str,
    current_user=Depends(require_roles(Administrator.ROLE)),
    auth_service=Depends(get_auth_service),
):
    loc = auth_service.get_location(location_id)
    if not loc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found."
        )
    auth_service.unassign_location_app_manager(location_id)
    return {"message": "Location App Manager unassigned."}


@router.post("/{location_id}/in-charge")
def assign_location_in_charge(
    location_id: str,
    payload: AssignLocationInChargeRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
    location_service=Depends(get_location_service),
):
    loc = auth_service.get_location(location_id)
    if not loc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found."
        )

    if (current_user.role or "").lower() == AppManager.ROLE.lower():
        if not auth_service.is_app_manager_assigned(current_user.user_id, location_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="App Manager cannot assign a Location In-Charge outside their assigned scope.",
            )

    if loc.in_charge_id and loc.in_charge_id != payload.in_charge_id:
        if not payload.confirm_replacement:
            existing_user = auth_service.get_user(loc.in_charge_id)
            name = existing_user.name if existing_user else loc.in_charge_id
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Replace {name}? Location already has an in-charge. Please confirm replacement.",
            )

    try:
        location_service.update_location(location_id, in_charge_id=payload.in_charge_id)
        return {"message": "Location in-charge assigned."}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.delete("/{location_id}/in-charge")
def unassign_location_in_charge(
    location_id: str,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
):
    if (current_user.role or "").lower() == AppManager.ROLE.lower():
        if not auth_service.is_app_manager_assigned(current_user.user_id, location_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="App Manager cannot unassign a Location In-Charge outside their assigned scope.",
            )
    try:
        auth_service.unassign_location_in_charge(location_id)
        return {"message": "Location in-charge unassigned."}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/coordinator/assignments")
def get_location_coordinator_assignments(
    current_user=Depends(get_current_user),
    auth_service=Depends(get_auth_service),
):
    return auth_service.get_location_coordinator_assignments()


@router.post("/{location_id}/coordinator")
def assign_location_coordinator(
    location_id: str,
    payload: AssignLocationCoordinatorRequest,
    current_user=Depends(require_roles(Administrator.ROLE)),
    auth_service=Depends(get_auth_service),
):
    loc = auth_service.get_location(location_id)
    if not loc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Location not found."
        )

    if loc.coordinator_id and loc.coordinator_id != payload.coordinator_id:
        if not payload.confirm_replacement:
            existing_user = auth_service.get_user(loc.coordinator_id)
            name = existing_user.name if existing_user else loc.coordinator_id
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Replace {name}? Location already has a coordinator. Please confirm replacement.",
            )

    try:
        auth_service.assign_location_coordinator(location_id, payload.coordinator_id)
        return {"message": "Location coordinator assigned."}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.delete("/{location_id}/coordinator")
def unassign_location_coordinator(
    location_id: str,
    current_user=Depends(require_roles(Administrator.ROLE)),
    auth_service=Depends(get_auth_service),
):
    try:
        auth_service.unassign_location_coordinator(location_id)
        return {"message": "Location coordinator unassigned."}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.patch("/{location_id}", response_model=LocationResponse)
def update_location(
    location_id: str,
    payload: LocationUpdateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    location_service=Depends(get_location_service),
    audit_service=Depends(get_audit_service),
):
    try:
        loc = location_service.get_location(location_id)
        old_value = loc.to_dict()

        if (current_user.role or "").lower() == AppManager.ROLE.lower():
            if not location_service.auth_service.is_app_manager_assigned(current_user.user_id, location_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="App Manager cannot update locations outside assigned scope.",
                )

        # Restore authorization enforcement:
        # If location was archived by an Administrator, only an Administrator can restore it.
        if payload.archived is False and loc.archived:
            archived_by_role = (getattr(loc, "archived_by_role", None) or "").lower()
            if archived_by_role == Administrator.ROLE.lower() and (current_user.role or "").lower() != Administrator.ROLE.lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only an Administrator can restore a location archived by an Administrator.",
                )

        if payload.app_manager_id is not None and (current_user.role or "").lower() != Administrator.ROLE.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only an Administrator can assign or unassign an App Manager.",
            )

        arch_role = current_user.role.lower() if payload.archived else None
        arch_user = current_user.user_id if payload.archived else None

        updated_loc = location_service.update_location(
            location_id,
            name=payload.name,
            location_type=payload.location_type,
            app_manager_id=payload.app_manager_id,
            in_charge_id=payload.in_charge_id,
            coordinator_id=payload.coordinator_id,
            archived=payload.archived,
            archived_by_role=arch_role,
            archived_by=arch_user,
        )

        audit_service.log(
            current_user.user_id,
            "Update Location",
            location_id,
            old_value=old_value,
            new_value=updated_loc.to_dict(),
        )
        return model_to_dict(updated_loc)
    except ValueError as error:
        if "Cannot archive" in str(error):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(error)
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    except Exception as error:
        if hasattr(error, "status_code"):
            raise error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.patch("/{location_id}/deactivate", response_model=LocationResponse)
def deactivate_location_endpoint(
    location_id: str,
    current_user=Depends(require_roles(Administrator.ROLE)),
    location_service=Depends(get_location_service),
    audit_service=Depends(get_audit_service),
):
    try:
        loc = location_service.get_location(location_id)
        old_val = model_to_dict(loc)
        deactivated_loc = location_service.deactivate_location(location_id)
        audit_service.log(
            current_user.user_id,
            "Deactivate Location",
            location_id,
            old_value=old_val,
            new_value=model_to_dict(deactivated_loc),
        )
        return model_to_dict(deactivated_loc)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.delete("/{location_id}", status_code=status.HTTP_200_OK)
def delete_location(
    location_id: str,
    current_user=Depends(require_roles(Administrator.ROLE)),
    location_service=Depends(get_location_service),
    audit_service=Depends(get_audit_service),
):
    try:
        loc = location_service.get_location(location_id)
        location_service.delete_location(location_id)
        audit_service.log(
            current_user.user_id,
            "Delete Location",
            location_id,
            old_value=loc.to_dict(),
            new_value=None,
        )
        return {"message": "Location deleted successfully."}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    except Exception as error:
        if hasattr(error, "status_code"):
            raise error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
