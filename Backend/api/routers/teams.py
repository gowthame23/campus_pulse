from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_team_service, get_setup_import_service, get_audit_service
from api.schemas import TeamCreateRequest, TeamUpdateRequest
from api.security import require_roles, get_current_user
from models.administrator import Administrator
from models.app_manager import AppManager
from models.coordinator import Coordinator
from models.employee import Employee
from models.location_in_charge import LocationInCharge
from services.team_service import TeamService

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("", response_model=List[Dict[str, Any]])
def list_teams(
    active_only: bool = Query(True),
    current_user=Depends(
        require_roles(
            Administrator.ROLE,
            AppManager.ROLE,
            Coordinator.ROLE,
            LocationInCharge.ROLE,
            Employee.ROLE,
        )
    ),
    team_service: TeamService = Depends(get_team_service),
):
    """List all teams. If caller is coordinator or employee, can filter to own teams or view all."""
    return team_service.list_teams(active_only=active_only)


@router.get("/coverage-gaps", response_model=Dict[str, Any])
def get_coverage_gaps(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    team_service: TeamService = Depends(get_team_service),
):
    """Rule C8: lists uncovered (location, dept) pairs, teams with no backup, inactive coordinators, locations with no warden."""
    return team_service.get_coverage_gaps()


@router.get("/{team_id}", response_model=Dict[str, Any])
def get_team(
    team_id: str,
    current_user=Depends(
        require_roles(
            Administrator.ROLE,
            AppManager.ROLE,
            Coordinator.ROLE,
            LocationInCharge.ROLE,
            Employee.ROLE,
        )
    ),
    team_service: TeamService = Depends(get_team_service),
):
    team = team_service.get_team(team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found."
        )
    return team


@router.get("/{team_id}/members", response_model=List[Dict[str, Any]])
def get_team_members(
    team_id: str,
    current_user=Depends(
        require_roles(
            Administrator.ROLE,
            AppManager.ROLE,
            Coordinator.ROLE,
            LocationInCharge.ROLE,
            Employee.ROLE,
        )
    ),
    team_service: TeamService = Depends(get_team_service),
):
    """Lists every active member of the team with open jobs count and on-leave status for Assign modal."""
    team = team_service.get_team(team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found."
        )
    return team_service.get_team_members_with_load(team_id)


@router.post("", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    team_service: TeamService = Depends(get_team_service),
):
    """Rule C4: Only Admin / App Manager can create teams. Validates Rule C2 (unique pair per team)."""
    try:
        return team_service.create_team(
            name=payload.name,
            department_id=payload.department_id,
            coordinator_id=payload.coordinator_id,
            location_ids=payload.location_ids,
            backup_coordinator_id=payload.backup_coordinator_id,
            member_ids=payload.member_ids,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{team_id}", response_model=Dict[str, Any])
def update_team(
    team_id: str,
    payload: TeamUpdateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    team_service: TeamService = Depends(get_team_service),
):
    """Rule C4: Only Admin / App Manager can edit teams. Validates Rule C2, handles C5 & C6."""
    existing = team_service.get_team(team_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found."
        )

    name = payload.name if payload.name is not None else existing["name"]
    department_id = payload.department_id if payload.department_id is not None else existing["department_id"]
    coordinator_id = payload.coordinator_id if payload.coordinator_id is not None else existing["coordinator_id"]
    backup_coordinator_id = payload.backup_coordinator_id if payload.backup_coordinator_id is not None else existing.get("backup_coordinator_id")
    location_ids = payload.location_ids if payload.location_ids is not None else existing["location_ids"]
    member_ids = payload.member_ids if payload.member_ids is not None else existing["member_ids"]
    active = payload.active if payload.active is not None else bool(existing["active"])

    try:
        return team_service.update_team(
            team_id=team_id,
            name=name,
            department_id=department_id,
            coordinator_id=coordinator_id,
            location_ids=location_ids,
            backup_coordinator_id=backup_coordinator_id,
            member_ids=member_ids,
            active=active,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{team_id}", response_model=Dict[str, Any])
def deactivate_team(
    team_id: str,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    team_service: TeamService = Depends(get_team_service),
):
    existing = team_service.get_team(team_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found."
        )
    try:
        updated = team_service.update_team(
            team_id=team_id,
            name=existing["name"],
            department_id=existing["department_id"],
            coordinator_id=existing["coordinator_id"],
            location_ids=existing["location_ids"],
            backup_coordinator_id=existing.get("backup_coordinator_id"),
            member_ids=existing["member_ids"],
            active=False,
        )
        return {"message": "Team deactivated successfully.", "team": updated}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{team_id}/members/{user_id}/reset-password", response_model=Dict[str, Any])
def reset_team_member_password(
    team_id: str,
    user_id: str,
    current_user=Depends(
        require_roles(
            Administrator.ROLE,
            AppManager.ROLE,
            Coordinator.ROLE,
        )
    ),
    team_service: TeamService = Depends(get_team_service),
    setup_service=Depends(get_setup_import_service),
    audit_service=Depends(get_audit_service),
):
    team = team_service.get_team(team_id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Team not found."
        )
    members = getattr(team, "member_ids", None) or (team.get("member_ids") if isinstance(team, dict) else [])
    if user_id not in members and getattr(team, "coordinator_id", None) != user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User is not a member of this team."
        )
    try:
        slip = setup_service.reset_worker_password(user_id, actor_user=current_user)
        audit_service.log(
            current_user.user_id,
            "Reset Team Member Password",
            user_id,
            old_value={"team_id": team_id},
            new_value={"name": slip["name"], "phone": slip["phone"]},
        )
        return slip
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as v_err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(v_err))

