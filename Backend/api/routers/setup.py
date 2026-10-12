from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form
from pydantic import BaseModel

from api.dependencies import (
    get_auth_service,
    get_complaint_service,
    get_setup_import_service,
    get_audit_service,
)
from api.security import require_roles, get_current_user
from models.administrator import Administrator
from models.app_manager import AppManager
from models.coordinator import Coordinator
from models.location_in_charge import LocationInCharge

router = APIRouter(tags=["setup"])


@router.get("/coordinators/stats")
def get_coordinator_stats(
    location_id: Optional[str] = None,
    department_id: Optional[str] = None,
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE, LocationInCharge.ROLE, Coordinator.ROLE, "employee")),
    complaint_service=Depends(get_complaint_service),
):
    return complaint_service.get_coordinator_stats(
        location_id=location_id,
        department_id=department_id,
        from_date=from_date,
        to_date=to_date,
        current_user=current_user,
    )


class CoordinatorAssignmentsUpdateRequest(BaseModel):
    assignments: List[Dict[str, Any]]


@router.get("/coordinators/{coordinator_id}/assignments")
def get_coordinator_assignments(
    coordinator_id: str,
    current_user=Depends(get_current_user),
    auth_service=Depends(get_auth_service),
):
    return auth_service.list_coordinator_assignments(coordinator_id=coordinator_id)


@router.put("/coordinators/{coordinator_id}/assignments")
def update_coordinator_assignments(
    coordinator_id: str,
    payload: CoordinatorAssignmentsUpdateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
):
    try:
        updated = auth_service.set_coordinator_assignments(
            coordinator_id, payload.assignments, assigned_by=current_user.user_id
        )
        return {"assignments": updated}
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/setup/coverage-gaps")
def get_coverage_gaps(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
):
    return auth_service.get_coverage_gaps()


@router.get("/setup/checklist")
def get_college_setup_checklist(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    setup_service=Depends(get_setup_import_service),
):
    """Returns real-time status of the College Setup checklist for Admin / App Manager."""
    return setup_service.get_setup_checklist()


@router.get("/setup/import/template")
def download_import_template(
    import_type: str = Query("locations", alias="type"),
    format_type: str = Query("csv", alias="format"),
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    setup_service=Depends(get_setup_import_service),
):
    """Download CSV or Excel template for locations, staff, teams, or emergency_contacts."""
    from fastapi.responses import Response

    try:
        content_bytes, media_type, filename = setup_service.get_template(import_type, format_type)
        return Response(
            content=content_bytes,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/setup/import/preview")
def preview_bulk_import(
    file: UploadFile = File(...),
    import_type: str = Form(..., alias="type"),
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    setup_service=Depends(get_setup_import_service),
):
    """Preview spreadsheet rows with row-by-row validation (red flags and exact reasons)."""
    file_bytes = file.file.read()
    try:
        return setup_service.preview_import(
            import_type=import_type,
            file_contents=file_bytes,
            filename=file.filename or f"{import_type}.csv",
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/setup/import/execute")
def execute_bulk_import(
    file: UploadFile = File(...),
    import_type: str = Form(..., alias="type"),
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    setup_service=Depends(get_setup_import_service),
    audit_service=Depends(get_audit_service),
):
    """Execute import of all valid rows in the spreadsheet, skipping invalid rows."""
    file_bytes = file.file.read()
    try:
        result = setup_service.execute_import(
            import_type=import_type,
            file_contents=file_bytes,
            filename=file.filename or f"{import_type}.csv",
            creator=current_user,
        )
        audit_service.log(
            current_user.user_id,
            f"Bulk Import {import_type.title()}",
            f"Total: {result['total_rows']}, Success: {result['success_count']}, Failed: {result['failed_count']}",
            old_value=None,
            new_value={
                "import_type": import_type,
                "total_rows": result["total_rows"],
                "success_count": result["success_count"],
                "failed_count": result["failed_count"],
            },
        )
        return result
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/setup/workers/{user_id}/reset-password")
def reset_worker_password(
    user_id: str,
    current_user=Depends(require_roles(Coordinator.ROLE, AppManager.ROLE, Administrator.ROLE)),
    setup_service=Depends(get_setup_import_service),
    audit_service=Depends(get_audit_service),
):
    """Reset password for a worker/employee without email and return a temporary password slip."""
    try:
        slip = setup_service.reset_worker_password(user_id, actor_user=current_user)
        audit_service.log(
            current_user.user_id,
            "Reset Worker Password",
            user_id,
            old_value=None,
            new_value={"name": slip["name"], "phone": slip["phone"]},
        )
        return slip
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as v_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(v_err))
