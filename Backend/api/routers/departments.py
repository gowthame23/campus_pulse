from fastapi import APIRouter, Depends, HTTPException, status

from api.dependencies import (
    get_audit_service,
    get_auth_service,
    get_department_service,
)
from api.schemas import (
    AssignCoordinatorRequest,
    AssignDepartmentCoordinatorsRequest,
    AssignLocationsToDepartmentRequest,
    CoordinatorAssignmentCreateRequest,
    DepartmentCreateRequest,
    DepartmentResponse,
    DepartmentSlaConfigResponse,
    DepartmentSlaConfigUpdateRequest,
    DepartmentUpdateRequest,
    model_to_dict,
)
from api.security import get_current_user, require_roles
from models.administrator import Administrator
from models.app_manager import AppManager

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("/coordinators/assignments")
def list_coordinator_assignments(
    coordinator_id: str = None,
    location_id: str = None,
    department_id: str = None,
    current_user=Depends(get_current_user),
    auth_service=Depends(get_auth_service),
):
    return auth_service.list_coordinator_assignments(
        coordinator_id=coordinator_id,
        location_id=location_id,
        department_id=department_id,
    )


@router.post("/coordinators/assignments", status_code=status.HTTP_201_CREATED)
def create_coordinator_assignment(
    payload: CoordinatorAssignmentCreateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
):
    if (current_user.role or "").lower() == AppManager.ROLE.lower():
        if not auth_service.is_app_manager_assigned(current_user.user_id, payload.location_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="App Manager cannot assign a Coordinator outside their assigned scope.",
            )
    try:
        return auth_service.assign_coordinator(
            payload.coordinator_id,
            payload.location_id,
            payload.department_id,
            assigned_by=current_user.user_id,
            confirm_replacement=payload.confirm_replacement,
        )
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.delete("/coordinators/assignments/{assignment_id}")
def remove_coordinator_assignment(
    assignment_id: str,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
):
    if (current_user.role or "").lower() == AppManager.ROLE.lower():
        target = next(
            (
                a
                for a in auth_service.list_coordinator_assignments()
                if a.get("assignment_id") == assignment_id
            ),
            None,
        )
        if target and not auth_service.is_app_manager_assigned(
            current_user.user_id, target["location_id"]
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="App Manager cannot remove a Coordinator assignment outside their assigned scope.",
            )
    auth_service.remove_coordinator_assignment(assignment_id)
    return {"message": "Coordinator assignment removed."}


@router.get("/coordinators/unassigned-combinations")
def get_unassigned_combinations(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
):
    combos = auth_service.get_unassigned_location_departments()
    if (current_user.role or "").lower() == AppManager.ROLE.lower():
        combos = [
            c
            for c in combos
            if auth_service.is_app_manager_assigned(current_user.user_id, c["location_id"])
        ]
    return combos


@router.get("/coverage-gaps")
def get_coverage_gaps(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
):
    return auth_service.get_coverage_gaps()


@router.get("", response_model=list[DepartmentResponse])
def list_departments(
    include_archived: bool = False,
    location_id: str = None,
    current_user=Depends(get_current_user),
    department_service=Depends(get_department_service),
):
    depts = department_service.list_departments(
        include_archived=include_archived, user_role=current_user.role, location_id=location_id
    )
    return [department_service.enrich_department_dict(d) for d in depts]


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(
    department_id: str,
    current_user=Depends(get_current_user),
    department_service=Depends(get_department_service),
):
    try:
        department = department_service.get_department(department_id)
        return department_service.enrich_department_dict(department)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


from utils.logger import get_logger

logger = get_logger(__name__)


@router.post("", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreateRequest,
    current_user=Depends(require_roles(Administrator.ROLE)),
    department_service=Depends(get_department_service),
):
    logger.info("Department creation endpoint reached")
    logger.info(f"User: {current_user.user_id}")
    logger.info(f"Role: {current_user.role}")
    logger.info(f"Active: {current_user.active}")
    logger.info(f"First Login: {current_user.first_login}")

    try:
        department = department_service.create_department(
            payload.name,
            payload.sla_days,
            payload.complaint_types,
            location_id=payload.location_id,
            description=payload.description,
            location_ids=payload.location_ids,
            actor_user_id=current_user.user_id,
            actor_role=current_user.role,
        )
        return department_service.enrich_department_dict(department)
    except Exception as error:
        # Convert duplicate validation exceptions to 409
        if hasattr(error, "status_code"):
            raise error
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))


@router.post("/{department_id}/coordinator")
def assign_coordinator(
    department_id: str,
    payload: AssignCoordinatorRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
    department_service=Depends(get_department_service),
):
    dept = auth_service.get_department(department_id)
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Department not found."
        )

    if not payload.coordinator_id:
        department_service.update_department(department_id, coordinator_id="")
        return {"message": "Coordinator unassigned."}

    if dept.coordinator_id and dept.coordinator_id != payload.coordinator_id:
        if not payload.confirm_replacement:
            existing_user = auth_service.get_user(dept.coordinator_id)
            name = existing_user.name if existing_user else dept.coordinator_id
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Replace {name}? Department already has a coordinator. Please confirm replacement.",
            )

    try:
        department_service.update_department(
            department_id, coordinator_id=payload.coordinator_id
        )
        return {"message": "Coordinator assigned."}
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/{department_id}/eligible-coordinators")
def get_eligible_department_coordinators(
    department_id: str,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    department_service=Depends(get_department_service),
):
    try:
        return department_service.get_eligible_department_coordinators(department_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.put("/{department_id}/coordinators", response_model=DepartmentResponse)
def assign_department_coordinators(
    department_id: str,
    payload: AssignDepartmentCoordinatorsRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    department_service=Depends(get_department_service),
    audit_service=Depends(get_audit_service),
):
    try:
        dept = department_service.get_department(department_id)
        old_val = dept.to_dict()
        updated = department_service.assign_department_coordinators(
            department_id,
            coordinator_1_id=payload.coordinator_1_id,
            coordinator_2_id=payload.coordinator_2_id,
            actor_id=current_user.user_id,
        )
        audit_service.log(
            current_user.user_id,
            "ASSIGN_DEPARTMENT_COORDINATORS",
            department_id,
            old_value=old_val,
            new_value=updated.to_dict(),
        )
        return model_to_dict(updated)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.patch("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: str,
    payload: DepartmentUpdateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    department_service=Depends(get_department_service),
    audit_service=Depends(get_audit_service),
):
    try:
        dept = department_service.get_department(department_id)
        old_value = dept.to_dict()

        if (current_user.role or "").lower() == AppManager.ROLE.lower():
            if dept.location_id and not department_service.auth_service.is_app_manager_assigned(current_user.user_id, dept.location_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="App Manager cannot update departments outside assigned scope.",
                )

        # Restore authorization enforcement:
        # If department was archived by an Administrator, only an Administrator can restore it.
        if payload.archived is False and dept.archived:
            archived_by_role = (getattr(dept, "archived_by_role", None) or "").lower()
            if archived_by_role == Administrator.ROLE.lower() and (current_user.role or "").lower() != Administrator.ROLE.lower():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only an Admin can restore a department archived by an Admin.",
                )

        arch_role = current_user.role.lower() if payload.archived else None
        arch_user = current_user.user_id if payload.archived else None

        updated_dept = department_service.update_department(
            department_id,
            name=payload.name,
            sla_days=payload.sla_days,
            complaint_types=payload.complaint_types,
            coordinator_id=payload.coordinator_id,
            coordinator_2_id=payload.coordinator_2_id,
            archived=payload.archived,
            archived_by_role=arch_role,
            archived_by=arch_user,
            description=payload.description,
            location_ids=payload.location_ids,
            actor_user_id=current_user.user_id,
            actor_role=current_user.role,
        )

        audit_service.log(
            current_user.user_id,
            "Update Department",
            department_id,
            old_value=old_value,
            new_value=updated_dept.to_dict(),
        )
        return department_service.enrich_department_dict(updated_dept)
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    except Exception as error:
        if hasattr(error, "status_code"):
            raise error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.delete("/{department_id}", status_code=status.HTTP_200_OK)
def delete_department(
    department_id: str,
    current_user=Depends(require_roles(Administrator.ROLE)),
    department_service=Depends(get_department_service),
    audit_service=Depends(get_audit_service),
):
    try:
        dept = department_service.get_department(department_id)
        department_service.delete_department(department_id)
        audit_service.log(
            current_user.user_id,
            "Delete Department",
            department_id,
            old_value=dept.to_dict(),
            new_value=None,
        )
        return {"message": "Department deleted successfully."}
    except ValueError as error:
        # Business logic errors (e.g. dependency exists)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    except Exception as error:
        if hasattr(error, "status_code"):
            raise error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/{department_id}/locations")
def get_department_locations(
    department_id: str,
    current_user=Depends(get_current_user),
    department_service=Depends(get_department_service),
):
    try:
        dept = department_service.get_department(department_id)
        locs = department_service.get_department_operating_locations(department_id)
        return {
            "department_id": department_id,
            "department_name": dept.name,
            "locations": locs,
            "location_ids": [l["location_id"] for l in locs],
        }
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.put("/{department_id}/locations")
def assign_department_locations(
    department_id: str,
    payload: AssignLocationsToDepartmentRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    department_service=Depends(get_department_service),
    audit_service=Depends(get_audit_service),
):
    try:
        dept = department_service.get_department(department_id)
        old_loc_ids = department_service.get_department_operating_location_ids(department_id)
        updated_ids = department_service.assign_locations_to_department(
            department_id,
            payload.location_ids,
            actor_user_id=current_user.user_id,
            actor_role=current_user.role,
        )
        locs = department_service.get_department_operating_locations(department_id)
        audit_service.log(
            current_user.user_id,
            "ASSIGN_DEPARTMENT_LOCATIONS",
            department_id,
            old_value={"location_ids": old_loc_ids},
            new_value={"location_ids": updated_ids},
        )
        return {
            "department_id": department_id,
            "department_name": dept.name,
            "location_ids": updated_ids,
            "locations": locs,
        }
    except PermissionError as error:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/{department_id}/eligible-employees")
def get_eligible_department_employees(
    department_id: str,
    current_user=Depends(get_current_user),
    department_service=Depends(get_department_service),
):
    try:
        department_service.get_department(department_id)
        return department_service.get_eligible_department_employees(department_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))


@router.get("/{department_id}/sla-config", response_model=DepartmentSlaConfigResponse)
def get_department_sla_config(
    department_id: str,
    current_user=Depends(get_current_user),
    department_service=Depends(get_department_service),
):
    dept = department_service.get_department(department_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")

    repo = department_service.auth_service.repository
    config = repo.get_department_sla_config(department_id)
    return config


@router.put("/{department_id}/sla-config", response_model=DepartmentSlaConfigResponse)
def update_department_sla_config(
    department_id: str,
    payload: DepartmentSlaConfigUpdateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    department_service=Depends(get_department_service),
    audit_service=Depends(get_audit_service),
):
    dept = department_service.get_department(department_id)
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found.")

    user_role = (current_user.role or "").lower()
    is_admin = user_role in ("administrator", "super_admin")

    repo = department_service.auth_service.repository
    existing_config = repo.get_department_sla_config(department_id)

    # App Manager scope check
    if not is_admin:
        if dept.location_id and not department_service.auth_service.is_app_manager_assigned(current_user.user_id, dept.location_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="App Manager cannot configure department SLA outside assigned scope.",
            )

    # Determine Admin escalation hours
    current_admin_hours = existing_config.get("admin_escalation_hours", 48)
    if not is_admin:
        # App Manager must NOT edit admin_escalation_hours
        if payload.admin_escalation_hours is not None and payload.admin_escalation_hours != current_admin_hours:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="App Manager cannot modify Admin escalation threshold.",
            )
        admin_hours = current_admin_hours
    else:
        admin_hours = payload.admin_escalation_hours if payload.admin_escalation_hours is not None else current_admin_hours

    app_mgr_hours = payload.app_manager_escalation_hours

    # Strict Ordering Validation Rule:
    # app_manager_escalation_hours < admin_escalation_hours
    if app_mgr_hours >= admin_hours:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="App Manager escalation time must be less than Admin escalation time.",
        )

    config_data = {
        "department_id": department_id,
        "normal_start_time": payload.normal_start_time,
        "normal_end_time": payload.normal_end_time,
        "normal_duration_hours": payload.normal_duration_hours,
        "medium_start_time": payload.medium_start_time,
        "medium_end_time": payload.medium_end_time,
        "medium_duration_hours": payload.medium_duration_hours,
        "high_start_time": payload.high_start_time,
        "high_end_time": payload.high_end_time,
        "high_duration_hours": payload.high_duration_hours,
        "critical_start_time": payload.critical_start_time,
        "critical_end_time": payload.critical_end_time,
        "critical_duration_hours": payload.critical_duration_hours,
        "app_manager_escalation_hours": app_mgr_hours,
        "admin_escalation_hours": admin_hours,
        "updated_by": current_user.user_id,
    }

    saved = repo.save_department_sla_config(config_data)

    audit_service.log(
        current_user.user_id,
        "Update Department SLA Config",
        department_id,
        old_value=existing_config,
        new_value=saved,
    )

    return saved

