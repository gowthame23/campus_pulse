from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_emergency_service, get_complaint_service, get_auth_service, get_team_service
from api.schemas import (
    EmergencyCategoryCreateRequest,
    EmergencyCategoryUpdateRequest,
    EmergencyContactCreateRequest,
    EmergencyContactUpdateRequest,
    EmergencyCreateRequest,
    EmergencyOutcomeRequest,
    EmergencyReachedRequest,
)
from api.security import get_current_user, require_roles
from models.administrator import Administrator
from models.app_manager import AppManager
from models.coordinator import Coordinator
from models.employee import Employee
from models.location_in_charge import LocationInCharge
from models.student import Student
from services.emergency_service import EmergencyService

router = APIRouter(prefix="/emergency", tags=["emergency"])


# =========================================================================
# CATEGORIES
# =========================================================================
@router.get("/categories", response_model=List[Dict[str, Any]])
def list_categories(
    active_only: bool = Query(True),
    current_user=Depends(get_current_user),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """List emergency categories."""
    return emergency_service.get_categories(active_only=active_only)


@router.post("/categories", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_category(
    payload: EmergencyCategoryCreateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Admin / App Manager creates emergency category."""
    try:
        return emergency_service.create_category(
            name=payload.name,
            department_id=payload.department_id,
            sort_order=payload.sort_order or 0,
            is_active=payload.is_active if payload.is_active is not None else True,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/categories/{category_id}", response_model=Dict[str, Any])
def update_category(
    category_id: str,
    payload: EmergencyCategoryUpdateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Admin / App Manager updates emergency category."""
    try:
        return emergency_service.update_category(
            category_id=category_id,
            name=payload.name,
            department_id=payload.department_id,
            sort_order=payload.sort_order,
            is_active=payload.is_active,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/categories/{category_id}", response_model=Dict[str, Any])
def delete_category(
    category_id: str,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Admin / App Manager deletes emergency category."""
    try:
        emergency_service.delete_category(category_id)
        return {"status": "success", "deleted_category_id": category_id}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =========================================================================
# CONTACTS
# =========================================================================
@router.get("/contacts", response_model=List[Dict[str, Any]])
def list_contacts(
    department_id: Optional[str] = Query(None),
    active_only: bool = Query(False),
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE, Coordinator.ROLE, LocationInCharge.ROLE)),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Admin / App Manager / Coordinator / Warden lists configured emergency contacts."""
    return emergency_service.get_contacts(department_id=department_id, active_only=active_only)


@router.post("/contacts", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_contact(
    payload: EmergencyContactCreateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Admin / App Manager creates emergency contact."""
    try:
        cid = emergency_service.create_contact(
            name=payload.name,
            phone=payload.phone,
            department_id=payload.department_id,
            location_id=payload.location_id,
            user_id=payload.user_id,
            sort_order=payload.sort_order or 0,
            active=payload.active if payload.active is not None else True,
            night_only=payload.night_only or False,
            day_only=payload.day_only or False,
        )
        return {"contact_id": cid, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/contacts/{contact_id}", response_model=Dict[str, Any])
def update_contact(
    contact_id: str,
    payload: EmergencyContactUpdateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Admin / App Manager updates emergency contact."""
    try:
        emergency_service.update_contact(
            contact_id=contact_id,
            name=payload.name,
            phone=payload.phone,
            department_id=payload.department_id,
            location_id=payload.location_id,
            user_id=payload.user_id,
            sort_order=payload.sort_order,
            active=payload.active,
            night_only=payload.night_only,
            day_only=payload.day_only,
        )
        return {"contact_id": contact_id, "status": "updated"}
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/contacts/{contact_id}", response_model=Dict[str, Any])
def delete_contact(
    contact_id: str,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Admin / App Manager deletes emergency contact."""
    try:
        emergency_service.delete_contact(contact_id)
        return {"status": "success", "deleted_contact_id": contact_id}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# =========================================================================
# STUDENT STATUS & CALL LIST
# =========================================================================
@router.get("/status", response_model=Dict[str, Any])
def get_emergency_status(
    current_user=Depends(get_current_user),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Returns student's misuse strike count, lockout status, and active emergency ID."""
    return emergency_service.get_student_status(current_user.user_id)


@router.get("/call-list", response_model=List[Dict[str, Any]])
def get_call_list(
    category: str = Query(..., description="Category ID or name"),
    location_id: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Generates the prioritized call list for the emergency screen.
    Rule 2.2e: Phone numbers appear ONLY here and on the Warden/Coordinator emergency view.
    """
    return emergency_service.get_call_list(
        user=current_user,
        category_id_or_name=category,
        location_id=location_id,
    )


# =========================================================================
# CREATE EMERGENCY COMPLAINT
# =========================================================================
@router.post("/create", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
def create_emergency(
    payload: EmergencyCreateRequest,
    current_user=Depends(get_current_user),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Auto-creates Critical emergency complaint immediately upon category selection.
    Sends urgent alerts to acting coordinator, warden, department contacts, and app manager.
    """
    try:
        return emergency_service.create_emergency(
            user=current_user,
            category_id_or_name=payload.category,
            location_id=payload.location_id,
        )
    except PermissionError as pe:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


# =========================================================================
# CALL FEEDBACK ("Did you reach someone?")
# =========================================================================
@router.post("/complaints/{complaint_id}/reached", response_model=Dict[str, Any])
def record_reached(
    complaint_id: str,
    payload: EmergencyReachedRequest,
    current_user=Depends(get_current_user),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Records whether caller reached someone. If 'No answer', immediately re-alerts staff."""
    try:
        return emergency_service.record_reached(
            complaint_id=complaint_id,
            reached=payload.reached,
            user=current_user,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


# =========================================================================
# STAFF ACKNOWLEDGMENT ("I'm on it")
# =========================================================================
@router.post("/complaints/{complaint_id}/acknowledge", response_model=Dict[str, Any])
def acknowledge_emergency(
    complaint_id: str,
    current_user=Depends(
        require_roles(
            Administrator.ROLE,
            AppManager.ROLE,
            Coordinator.ROLE,
            LocationInCharge.ROLE,
            Employee.ROLE,
        )
    ),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Staff member taps 'I'm on it' -> saves acknowledged_by/at and notifies student."""
    try:
        return emergency_service.acknowledge_emergency(
            complaint_id=complaint_id,
            user=current_user,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))


# =========================================================================
# OUTCOME SELECTOR ("Real" | "Mistake" | "Misuse")
# =========================================================================
@router.post("/complaints/{complaint_id}/outcome", response_model=Dict[str, Any])
def mark_outcome(
    complaint_id: str,
    payload: EmergencyOutcomeRequest,
    current_user=Depends(
        require_roles(
            Administrator.ROLE,
            AppManager.ROLE,
            Coordinator.ROLE,
            LocationInCharge.ROLE,
        )
    ),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Warden or Coordinator marks emergency outcome before closing."""
    try:
        return emergency_service.mark_outcome(
            complaint_id=complaint_id,
            outcome=payload.outcome,
            user=current_user,
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


# =========================================================================
# PINNED EMERGENCIES (Warden & Coordinator Dashboards, Rule 2.4c)
# =========================================================================
@router.get("/pinned", response_model=List[Dict[str, Any]])
def get_pinned_emergencies(
    current_user=Depends(
        require_roles(
            Administrator.ROLE,
            AppManager.ROLE,
            Coordinator.ROLE,
            LocationInCharge.ROLE,
            Employee.ROLE,
        )
    ),
    emergency_service: EmergencyService = Depends(get_emergency_service),
    complaint_service=Depends(get_complaint_service),
    auth_service=Depends(get_auth_service),
    team_service=Depends(get_team_service),
):
    """Returns active emergency complaints pinned at the top in red for Wardens & Coordinators,
    including team members' phones so they can call staff directly (Rule 2.4c).
    """
    user_role = (getattr(current_user, "role", "") or "").lower()
    all_complaints = complaint_service.list_all()
    emergencies = [
        c for c in all_complaints
        if getattr(c, "is_emergency", False) and c.status not in ("Closed", "Closed (Auto Closed)", "Rejected", "Cancelled")
    ]

    # Filter relevant to current user
    if user_role in ("location_in_charge", "warden"):
        w_loc = getattr(current_user, "location_id", None)
        if w_loc:
            emergencies = [c for c in emergencies if c.location_id == w_loc]
    elif user_role in ("coordinator", "employee"):
        my_teams = team_service.get_user_teams(current_user.user_id)
        team_ids = {t["team_id"] for t in my_teams}
        for t in team_service.list_teams():
            if t.get("coordinator_id") == current_user.user_id or t.get("backup_coordinator_id") == current_user.user_id:
                team_ids.add(t["team_id"])
        emergencies = [c for c in emergencies if c.team_id in team_ids]

    results = []
    for c in emergencies:
        cd = c.to_dict()
        loc = auth_service.get_location(c.location_id)
        cd["location_name"] = loc.name if loc else c.location_id
        dept = auth_service.get_department(c.department_id)
        cd["department_name"] = dept.name if dept else c.department_id

        # Attach team call contacts
        contacts = []
        if c.team_id:
            team = team_service.get_team(c.team_id)
            if team:
                member_ids = list(team.get("member_ids") or [])
                if team.get("coordinator_id"):
                    member_ids.append(team["coordinator_id"])
                if team.get("backup_coordinator_id"):
                    member_ids.append(team["backup_coordinator_id"])
                seen = set()
                for mid in member_ids:
                    if mid in seen:
                        continue
                    seen.add(mid)
                    u = auth_service.get_user(mid)
                    if u and getattr(u, "phone_number", None):
                        contacts.append({
                            "user_id": u.user_id,
                            "name": u.name,
                            "phone": u.phone_number,
                            "role": u.role,
                        })
        cd["team_contacts"] = contacts
        results.append(cd)

    return results


# =========================================================================
# STATS (Rule 2.8)
# =========================================================================
@router.get("/stats", response_model=Dict[str, Any])
def get_emergency_stats(
    current_user=Depends(
        require_roles(
            Administrator.ROLE,
            AppManager.ROLE,
            Coordinator.ROLE,
            LocationInCharge.ROLE,
        )
    ),
    emergency_service: EmergencyService = Depends(get_emergency_service),
):
    """Returns emergency stats per location and per team."""
    return emergency_service.get_stats()

