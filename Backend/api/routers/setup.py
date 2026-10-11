from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from api.dependencies import get_auth_service, get_complaint_service
from api.security import require_roles, get_current_user
from models.administrator import Administrator
from models.app_manager import AppManager
from models.coordinator import Coordinator

router = APIRouter(tags=["setup"])


@router.get("/coordinators/stats")
def get_coordinator_stats(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    complaint_service=Depends(get_complaint_service),
):
    return complaint_service.get_coordinator_stats()


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
