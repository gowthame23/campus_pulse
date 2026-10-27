from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_team_service
from api.schemas import LeaveCreateRequest
from api.security import get_current_user, require_roles
from models.administrator import Administrator
from models.app_manager import AppManager
from models.coordinator import Coordinator
from models.location_in_charge import LocationInCharge
from services.team_service import TeamService

router = APIRouter(prefix="/leaves", tags=["leaves"])


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def set_leave(
    payload: LeaveCreateRequest,
    current_user=Depends(
        require_roles(
            Administrator.ROLE,
            AppManager.ROLE,
            Coordinator.ROLE,
            LocationInCharge.ROLE,
        )
    ),
    team_service: TeamService = Depends(get_team_service),
):
    """Rule G2: Anyone (employee, coordinator, warden) can mark themselves on leave.
    Admin / App Manager can set leave for any user.
    """
    target_user_id = payload.user_id or current_user.user_id
    if payload.from_date > payload.to_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="from_date cannot be after to_date.",
        )

    try:
        return team_service.set_leave(
            user_id=target_user_id,
            from_date=payload.from_date,
            to_date=payload.to_date,
            reason=payload.reason,
            set_by=current_user.user_id,
            caller_user=current_user,
            department_id=payload.department_id,
        )
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.get("/my", response_model=List[Dict[str, Any]])
def get_my_leaves(
    active_only: bool = Query(False),
    current_user=Depends(get_current_user),
    team_service: TeamService = Depends(get_team_service),
):
    """Returns leaves for current user."""
    return team_service.get_user_leaves(user_id=current_user.user_id, active_only=active_only)


@router.get("", response_model=List[Dict[str, Any]])
def list_leaves(
    user_id: Optional[str] = Query(None),
    active_only: bool = Query(False),
    current_user=Depends(
        require_roles(
            Administrator.ROLE,
            AppManager.ROLE,
            Coordinator.ROLE,
            LocationInCharge.ROLE,
        )
    ),
    team_service: TeamService = Depends(get_team_service),
):
    """Lists leaves. Coordinator can view team leaves, Admin/Manager can view all."""
    return team_service.get_user_leaves(user_id=user_id, active_only=active_only)


@router.delete("/{leave_id}", response_model=Dict[str, Any])
def cancel_leave(
    leave_id: str,
    current_user=Depends(get_current_user),
    team_service: TeamService = Depends(get_team_service),
):
    """Cancels a leave record. Can be cancelled by the user themselves or Admin/App Manager."""
    try:
        team_service.cancel_leave(leave_id, caller_user=current_user)
        return {"message": "Leave cancelled successfully.", "leave_id": leave_id}
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))

