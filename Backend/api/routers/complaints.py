from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from core.constants import (
    STATUS_RAISED,
    STATUS_GOING_ON,
    STATUS_FIXED,
    INACTIVE_STATUSES,
    STATUS_CLOSED,
    STATUS_AUTO_CLOSED,
    STATUS_REJECTED,
    STATUS_CANCELLED,
)
from services.complaint_service import ComplaintConflictError

from api.dependencies import (
    get_audit_service,
    get_classification_service,
    get_comment_service,
    get_complaint_service,
    get_team_service,
    get_translation_service,
)
from api.schemas import (
    AnalyticsResponse,
    CommentCreateRequest,
    CommentResponse,
    ComplaintAssignRequest,
    ComplaintCreateRequest,
    ComplaintDeleteRequestPayload,
    ComplaintCancellationRequestPayload,
    ComplaintCancellationReviewPayload,
    ComplaintCancellationRejectPayload,
    ComplaintPriorityUpdateRequest,
    ComplaintReopenRequest,
    ComplaintRerouteRequest,
    ComplaintResolveRequest,
    ComplaintResponse,
    ComplaintReturnRequest,
    ComplaintStatusRequest,
    ComplaintUpdateRequest,
    ComplaintWrongLocationRequest,
    EscalateRequest,
    WardenVerifyRequest,
    AdminDecisionRequest,
    ComplaintFeedbackRequest,
    model_to_dict,
)
from api.security import get_current_user, require_roles
from models.administrator import Administrator
from models.app_manager import AppManager
from models.complaint import Complaint
from models.coordinator import Coordinator
from models.employee import Employee
from models.location_in_charge import LocationInCharge
from models.student import Student
from services.complaint_service import ComplaintConflictError
from utils.helper import csv_safe, generate_id, now_string, parse_date
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/complaints", tags=["complaints"])


def _broadcast_complaint_event(event_type: str, complaint, extra: dict = None):
    try:
        from utils.websocket_manager import manager
        payload = {
            "type": event_type,
            "event": event_type,
            "complaint_id": getattr(complaint, "complaint_id", str(complaint)),
            "status": getattr(complaint, "status", None),
            "location_id": getattr(complaint, "location_id", None),
            **(extra or {}),
        }
        manager.broadcast_sync(payload)
    except Exception as err:
        logger.debug(f"WS broadcast error: {err}")


def _build_format_caches(complaint_service):
    try:
        all_locs = complaint_service.auth_service.list_locations()
        loc_cache = {l.location_id: l for l in all_locs}
    except Exception:
        all_locs = []
        loc_cache = {}

    try:
        all_depts = complaint_service.auth_service.list_departments()
        dept_cache = {d.department_id: d for d in all_depts}
    except Exception:
        dept_cache = {}

    try:
        all_users = complaint_service.auth_service.list_users()
        user_cache = {u.user_id: u for u in all_users}
    except Exception:
        user_cache = {}

    team_cache = {}
    loc_dept_team_cache = {}
    if hasattr(complaint_service, "team_service"):
        try:
            teams = complaint_service.team_service.list_teams(active_only=False)
            for t in teams:
                team_cache[t["team_id"]] = t
                for lid in t.get("location_ids", []):
                    for did in t.get("department_ids", []):
                        if (lid, did) not in loc_dept_team_cache:
                            loc_dept_team_cache[(lid, did)] = t
        except Exception:
            pass

    coord_asgn_cache = {}
    try:
        assignments = complaint_service.auth_service.list_coordinator_assignments() or []
        for a in assignments:
            if a.get("is_active", 1):
                key = (a.get("location_id"), a.get("department_id"))
                if key not in coord_asgn_cache:
                    coord_asgn_cache[key] = a
    except Exception:
        pass

    affected_cache = complaint_service.get_affected_students_counts()
    return loc_cache, dept_cache, affected_cache, user_cache, team_cache, loc_dept_team_cache, coord_asgn_cache


def _get_critical_emergency_contacts(
    complaint,
    complaint_service,
    loc=None,
    dept=None,
    user_cache=None,
    loc_dept_team_cache=None,
    coord_asgn_cache=None,
):
    priority_str = (getattr(complaint, "priority", "") or "").lower()
    if priority_str != "critical":
        return []

    contacts = []
    auth_service = complaint_service.auth_service
    if loc is None:
        loc = auth_service.get_location(complaint.location_id)
    if dept is None:
        dept = auth_service.get_department(complaint.department_id)

    # 1. Warden / Location In-Charge
    warden_id = getattr(loc, "in_charge_id", None) if loc else None
    if warden_id:
        warden_u = user_cache.get(warden_id) if user_cache is not None else auth_service.get_user(warden_id)
        if warden_u:
            phone = getattr(warden_u, "phone_number", None) or getattr(warden_u, "phone", None)
            contacts.append({
                "role": "Warden / Location In-Charge",
                "name": warden_u.name,
                "user_id": warden_u.user_id,
                "phone": phone or "",
                "phone_available": bool(phone and phone.strip()),
                "location": getattr(loc, "name", complaint.location_id) if loc else complaint.location_id,
            })

    # 2. Department Coordinator (matching location & dept)
    coord_u = None
    if coord_asgn_cache is not None:
        active_asgn = coord_asgn_cache.get((complaint.location_id, complaint.department_id)) or coord_asgn_cache.get(("ALL", complaint.department_id))
    else:
        assignments = auth_service.list_coordinator_assignments(
            location_id=complaint.location_id, department_id=complaint.department_id
        ) or []
        active_asgn = next((a for a in assignments if a.get("is_active", 1)), None)

    if active_asgn:
        cid = active_asgn["coordinator_id"]
        coord_u = user_cache.get(cid) if user_cache is not None else auth_service.get_user(cid)

    if not coord_u and loc_dept_team_cache is not None:
        team = loc_dept_team_cache.get((complaint.location_id, complaint.department_id))
        if team and team.get("coordinator_id"):
            cid = team["coordinator_id"]
            coord_u = user_cache.get(cid) if user_cache is not None else auth_service.get_user(cid)
    elif not coord_u and hasattr(complaint_service, "team_service"):
        team = complaint_service.team_service.get_team_for_location_department(
            complaint.location_id, complaint.department_id
        )
        if team and team.get("coordinator_id"):
            cid = team["coordinator_id"]
            coord_u = user_cache.get(cid) if user_cache is not None else auth_service.get_user(cid)

    if not coord_u and dept and getattr(dept, "coordinator_id", None):
        cid = dept.coordinator_id
        coord_u = user_cache.get(cid) if user_cache is not None else auth_service.get_user(cid)

    if coord_u:
        phone = getattr(coord_u, "phone_number", None) or getattr(coord_u, "phone", None)
        contacts.append({
            "role": "Department Coordinator",
            "name": coord_u.name,
            "user_id": coord_u.user_id,
            "phone": phone or "",
            "phone_available": bool(phone and phone.strip()),
            "department": getattr(dept, "name", complaint.department_id) if dept else complaint.department_id,
        })

    # 3. App Manager
    app_mgr_id = getattr(loc, "app_manager_id", None) if loc else None
    if not app_mgr_id and loc:
        app_mgr_id = auth_service.get_location_app_manager_id(loc.location_id)
    if not app_mgr_id:
        mgrs = [u for u in user_cache.values() if u.role == "app_manager"] if user_cache else auth_service.list_users(role="app_manager")
        for m in mgrs:
            if loc and auth_service._manager_covers_location(m, loc.location_id, loc.name):
                app_mgr_id = m.user_id
                break
        if not app_mgr_id and mgrs:
            app_mgr_id = mgrs[0].user_id

    if app_mgr_id:
        app_mgr_u = user_cache.get(app_mgr_id) if user_cache is not None else auth_service.get_user(app_mgr_id)
        if app_mgr_u:
            phone = getattr(app_mgr_u, "phone_number", None) or getattr(app_mgr_u, "phone", None)
            contacts.append({
                "role": "App Manager",
                "name": app_mgr_u.name,
                "user_id": app_mgr_u.user_id,
                "phone": phone or "",
                "phone_available": bool(phone and phone.strip()),
            })

    return contacts


def _format_complaint(
    complaint,
    complaint_service,
    loc_cache=None,
    dept_cache=None,
    affected_cache=None,
    user_cache=None,
    team_cache=None,
    loc_dept_team_cache=None,
    coord_asgn_cache=None,
):
    data = model_to_dict(complaint)
    if loc_cache is not None:
        loc = loc_cache.get(complaint.location_id)
    else:
        loc = complaint_service.auth_service.get_location(complaint.location_id)
    if loc:
        data["location_id"] = loc.location_id
        data["location_name"] = loc.name
        if getattr(loc, "in_charge_id", None):
            data["location_in_charge_id"] = loc.in_charge_id
            in_charge = user_cache.get(loc.in_charge_id) if user_cache is not None else complaint_service.auth_service.get_user(loc.in_charge_id)
            if in_charge:
                data["location_in_charge_name"] = in_charge.name

    if dept_cache is not None:
        dept = dept_cache.get(complaint.department_id)
    else:
        dept = complaint_service.auth_service.get_department(complaint.department_id)
    if dept:
        data["department_id"] = dept.department_id
        data["department_name"] = dept.name
        if getattr(dept, "coordinator_id", None):
            data["assigned_coordinator_id"] = dept.coordinator_id
            coord = user_cache.get(dept.coordinator_id) if user_cache is not None else complaint_service.auth_service.get_user(dept.coordinator_id)
            if coord:
                data["assigned_coordinator_name"] = coord.name

    # Assigned Employee Visibility
    if complaint.assigned_to:
        emp_u = user_cache.get(complaint.assigned_to) if user_cache is not None else complaint_service.auth_service.get_user(complaint.assigned_to)
        emp_name = emp_u.name if emp_u else complaint.assigned_to
        data["assigned_employee_name"] = emp_name
        data["assigned_to_name"] = emp_name
    else:
        data["assigned_employee_name"] = "Awaiting assignment"
        data["assigned_to_name"] = "Awaiting assignment"

    # Team Visibility & Fallback Coordinator Resolution
    team = None
    if getattr(complaint, "team_id", None):
        team = team_cache.get(complaint.team_id) if team_cache is not None else (complaint_service.team_service.get_team(complaint.team_id) if hasattr(complaint_service, "team_service") else None)
    if not team:
        team = loc_dept_team_cache.get((complaint.location_id, complaint.department_id)) if loc_dept_team_cache is not None else (complaint_service.team_service.get_team_for_location_department(complaint.location_id, complaint.department_id) if hasattr(complaint_service, "team_service") else None)
    if team:
        data["team_id"] = team.get("team_id")
        data["team_name"] = team.get("name")
        if not data.get("assigned_coordinator_name"):
            coord_id = team.get("coordinator_id")
            if coord_id:
                coord_u = user_cache.get(coord_id) if user_cache is not None else complaint_service.auth_service.get_user(coord_id)
                if coord_u:
                    data["assigned_coordinator_id"] = coord_id
                    data["assigned_coordinator_name"] = coord_u.name

    # Emergency Contacts for Critical Complaints
    data["emergency_contacts"] = _get_critical_emergency_contacts(
        complaint,
        complaint_service,
        loc=loc,
        dept=dept,
        user_cache=user_cache,
        loc_dept_team_cache=loc_dept_team_cache,
        coord_asgn_cache=coord_asgn_cache,
    )

    if affected_cache is not None:
        data["affected_count"] = affected_cache.get(complaint.complaint_id, 0)
    else:
        data["affected_count"] = complaint_service.get_affected_count(
            complaint.complaint_id
        )
    return data


def _visible_complaints(current_user, complaint_service, include_archived=False):
    u_role = (current_user.role or "").lower()
    if u_role == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin cannot access institutional operational data.",
        )

    all_complaints = complaint_service.list_all(include_archived=include_archived)

    if u_role == "administrator":
        return all_complaints

    # Pre-fetch locations and departments to avoid N+1 database connection cycles
    try:
        all_locs = complaint_service.auth_service.list_locations()
        loc_map = {l.location_id: l for l in all_locs}
    except Exception:
        all_locs = []
        loc_map = {}

    try:
        all_depts = complaint_service.auth_service.list_departments()
        dept_map = {d.department_id: d for d in all_depts}
    except Exception:
        dept_map = {}

    if u_role == "app_manager":
        assigned = list(getattr(current_user, "assigned_locations", None) or [])
        assigned_mgr_loc_ids = [l.location_id for l in all_locs if getattr(l, "app_manager_id", None) == current_user.user_id]
        assigned.extend(assigned_mgr_loc_ids)
        user_loc_id = getattr(current_user, "location_id", None)
        visible = []
        for c in all_complaints:
            if c.created_by == current_user.user_id or c.assigned_to == current_user.user_id:
                visible.append(c)
                continue
            c_loc = loc_map.get(c.location_id)
            c_loc_id = c_loc.location_id if c_loc else c.location_id
            c_loc_name = c_loc.name if c_loc else c.location_id

            is_assigned = False
            for a in assigned:
                if a == c_loc_id or (c_loc_name and a.lower() == c_loc_name.lower()):
                    is_assigned = True
                    break
            if not is_assigned and user_loc_id:
                if user_loc_id == c_loc_id or (c_loc_name and user_loc_id.lower() == c_loc_name.lower()):
                    is_assigned = True
            if is_assigned:
                visible.append(c)
        return visible

    visible = []
    if u_role == "student":
        user_loc_id = getattr(current_user, "location_id", None)
        for c in all_complaints:
            if c.created_by == current_user.user_id:
                visible.append(c)
            elif c.visibility_type in ("Community", "Public", "public", "community"):
                loc_obj = loc_map.get(c.location_id)
                access = (
                    getattr(loc_obj, "complaint_submission_policy", None)
                    or getattr(loc_obj, "public_complaint_access", "everyone")
                ) if loc_obj else "everyone"
                if access == "everyone" or c.location_id == user_loc_id:
                    visible.append(c)

    elif u_role == "employee":
        acting_team_ids = set()
        if hasattr(complaint_service, "team_service"):
            for t in complaint_service.team_service.list_teams(active_only=True):
                acting = complaint_service.team_service.get_acting_coordinator(t)
                if acting and acting.user_id == current_user.user_id:
                    acting_team_ids.add(t["team_id"])
        coord_assignments = complaint_service.auth_service.list_coordinator_assignments(coordinator_id=current_user.user_id) or []
        coord_dept_ids = {
            d.department_id for d in all_depts
            if current_user.user_id in (getattr(d, "coordinator_id", None), getattr(d, "coordinator_2_id", None))
        }
        for c in all_complaints:
            if (
                c.assigned_to == current_user.user_id
                or c.created_by == current_user.user_id
                or (getattr(c, "team_id", None) and c.team_id in acting_team_ids)
                or (c.department_id and c.department_id in coord_dept_ids)
            ):
                visible.append(c)
                continue
            is_coord_match = False
            for asgn in coord_assignments:
                a_loc = asgn.get("location_id")
                a_dept = asgn.get("department_id")
                loc_match = a_loc in ("ALL", None) or a_loc == c.location_id
                dept_match = a_dept in ("ALL", None) or a_dept == c.department_id
                if loc_match and dept_match:
                    is_coord_match = True
                    break
            if is_coord_match:
                visible.append(c)

    elif u_role == "coordinator":
        user_teams = complaint_service.team_service.get_user_teams(current_user.user_id)
        coord_teams = [
            t for t in complaint_service.team_service.list_teams(active_only=True)
            if t.get("coordinator_id") == current_user.user_id or t.get("backup_coordinator_id") == current_user.user_id
        ]
        my_team_ids = {t["team_id"] for t in (user_teams + coord_teams)}

        assignments = complaint_service.auth_service.list_coordinator_assignments(coordinator_id=current_user.user_id) or []
        has_assignments = len(assignments) > 0
        coord_dept_obj = dept_map.get(current_user.department_id) if current_user.department_id else None
        coord_loc_id = coord_dept_obj.location_id if coord_dept_obj else None

        for c in all_complaints:
            if c.assigned_to == current_user.user_id:
                visible.append(c)
                continue
            if getattr(c, "team_id", None) and c.team_id in my_team_ids:
                visible.append(c)
                continue
            is_assigned = False
            c_loc = loc_map.get(c.location_id)
            c_loc_id = c_loc.location_id if c_loc else c.location_id
            c_loc_type = getattr(c_loc, "location_type", None) or (c_loc.infer_location_type(c_loc.name) if c_loc else c.location_id)

            c_dept = dept_map.get(c.department_id)
            c_dept_id = c_dept.department_id if c_dept else c.department_id

            for asgn in assignments:
                a_loc = asgn.get("location_id")
                a_dept = asgn.get("department_id")

                loc_match = (
                    a_loc in ("ALL", None)
                    or a_loc == c_loc_id
                    or a_loc == c_loc_type
                    or (c_loc and a_loc.lower() == c_loc.name.lower())
                )
                dept_match = (
                    a_dept in ("ALL", None)
                    or a_dept == c_dept_id
                    or (c_dept and a_dept.lower() == c_dept.name.lower())
                )
                if loc_match and dept_match:
                    is_assigned = True
                    break

            if is_assigned:
                visible.append(c)
            else:
                if not has_assignments:
                    is_match = False
                    if c_dept and coord_dept_obj and c_dept.department_id == coord_dept_obj.department_id:
                        if coord_loc_id and c_loc_id == coord_loc_id:
                            is_match = True

                    if is_match:
                        if c.visibility_type == "Private":
                            if not c.assigned_to or c.assigned_to == current_user.user_id:
                                visible.append(c)
                        else:
                            visible.append(c)

    elif u_role == "location_in_charge":
        warden_loc_ids = {l.location_id for l in all_locs if getattr(l, "in_charge_id", None) == current_user.user_id}
        for c in all_complaints:
            if c.created_by == current_user.user_id or c.assigned_to == current_user.user_id:
                visible.append(c)
            elif c.location_id in warden_loc_ids:
                visible.append(c)
            elif complaint_service.auth_service.is_warden_assigned(current_user.user_id, c.location_id):
                visible.append(c)

    return visible


def is_complaint_visible(complaint, current_user, complaint_service):
    u_role = (current_user.role or "").lower()
    if u_role == "super_admin":
        return False
    if u_role == "administrator":
        return True

    if u_role == "student":
        if complaint.created_by == current_user.user_id or (getattr(current_user, "email", None) and complaint.created_by == current_user.email):
            return True
        if (complaint.visibility_type or "").capitalize() in ("Community", "Public"):
            user_loc_id = getattr(current_user, "location_id", None)
            if complaint.location_id == user_loc_id:
                return True
            loc_obj = complaint_service.auth_service.get_location(complaint.location_id)
            access = (
                getattr(loc_obj, "complaint_submission_policy", None)
                or getattr(loc_obj, "public_complaint_access", "everyone")
            ) if loc_obj else "everyone"
            if access == "everyone":
                return True
        return False

    if u_role == "location_in_charge":
        if complaint.created_by == current_user.user_id or complaint.assigned_to == current_user.user_id:
            return True
        if complaint_service.auth_service.is_warden_assigned(current_user.user_id, complaint.location_id):
            return True
        return False

    if u_role == "employee":
        if complaint.assigned_to == current_user.user_id or complaint.created_by == current_user.user_id:
            return True
        if complaint_service.auth_service.is_coordinator_assigned(current_user.user_id, complaint.location_id, complaint.department_id):
            return True
        if hasattr(complaint_service, "team_service") and complaint_service.team_service:
            team_id = getattr(complaint, "team_id", None)
            team = complaint_service.team_service.get_team(team_id) if team_id else complaint_service.team_service.get_team_for_location_department(complaint.location_id, complaint.department_id)
            if team:
                acting = complaint_service.team_service.get_acting_coordinator(team)
                if acting and acting.user_id == current_user.user_id:
                    return True
                if current_user.user_id in (team.get("coordinator_id"), team.get("backup_coordinator_id")):
                    return True
                if complaint_service.team_service.is_user_in_team(team["team_id"], current_user.user_id):
                    return True
        return False

    if u_role == "app_manager":
        if complaint.created_by == current_user.user_id or complaint.assigned_to == current_user.user_id:
            return True
        assigned = list(getattr(current_user, "assigned_locations", None) or [])
        loc = complaint_service.auth_service.get_location(complaint.location_id)
        if loc:
            if getattr(loc, "app_manager_id", None) == current_user.user_id:
                return True
            for a in assigned:
                if a == loc.location_id or (loc.name and a.lower() == loc.name.lower()):
                    return True
            user_loc_id = getattr(current_user, "location_id", None)
            if user_loc_id and (user_loc_id == loc.location_id or (loc.name and user_loc_id.lower() == loc.name.lower())):
                return True
        return False

    if u_role == "coordinator":
        if complaint.assigned_to == current_user.user_id:
            return True
        if hasattr(complaint_service, "team_service") and complaint_service.team_service:
            team_id = getattr(complaint, "team_id", None)
            team = complaint_service.team_service.get_team(team_id) if team_id else complaint_service.team_service.get_team_for_location_department(complaint.location_id, complaint.department_id)
            if team:
                if current_user.user_id in (team.get("coordinator_id"), team.get("backup_coordinator_id")):
                    return True
                if complaint_service.team_service.is_user_in_team(team["team_id"], current_user.user_id):
                    return True

        assignments = complaint_service.auth_service.list_coordinator_assignments(coordinator_id=current_user.user_id) or []
        has_assignments = len(assignments) > 0
        loc = complaint_service.auth_service.get_location(complaint.location_id)
        c_loc_id = loc.location_id if loc else complaint.location_id
        c_loc_type = getattr(loc, "location_type", None) or (loc.infer_location_type(loc.name) if loc else complaint.location_id)
        dept = complaint_service.auth_service.get_department(complaint.department_id)
        c_dept_id = dept.department_id if dept else complaint.department_id

        for asgn in assignments:
            a_loc = asgn.get("location_id")
            a_dept = asgn.get("department_id")
            loc_match = (
                a_loc in ("ALL", None)
                or a_loc == c_loc_id
                or a_loc == c_loc_type
                or (loc and a_loc.lower() == loc.name.lower())
            )
            dept_match = (
                a_dept in ("ALL", None)
                or a_dept == c_dept_id
                or (dept and a_dept.lower() == dept.name.lower())
            )
            if loc_match and dept_match:
                return True

        if not has_assignments:
            coord_dept_obj = complaint_service.auth_service.get_department(current_user.department_id) if current_user.department_id else None
            coord_loc_id = coord_dept_obj.location_id if coord_dept_obj else None
            is_match = False
            if dept and coord_dept_obj and dept.department_id == coord_dept_obj.department_id:
                if coord_loc_id and c_loc_id == coord_loc_id:
                    is_match = True
            if is_match:
                if complaint.visibility_type == "Private":
                    if not complaint.assigned_to or complaint.assigned_to == current_user.user_id:
                        return True
                else:
                    return True
        return False

    return False


def _ensure_visible(complaint, current_user, complaint_service):
    u_role = (current_user.role or "").lower()
    if u_role == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin cannot access institutional operational data.",
        )
    if not is_complaint_visible(complaint, current_user, complaint_service):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Complaint is not visible to this user.",
        )


@router.get("", response_model=list[ComplaintResponse])
def list_complaints(
    status_filter: str | None = None,
    department_id: str | None = None,
    location_id: str | None = None,
    include_archived: bool = False,
    page: int | None = None,
    limit: int | None = None,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
):
    complaints = _visible_complaints(current_user, complaint_service, include_archived)
    if status_filter:
        complaints = [item for item in complaints if item.status == status_filter]
    if department_id:
        complaints = [
            item for item in complaints if item.department_id == department_id
        ]
    if location_id:
        complaints = [item for item in complaints if item.location_id == location_id]
    if not include_archived:
        complaints = [item for item in complaints if not item.archived]

    if page is not None and limit is not None and page > 0 and limit > 0:
        start_idx = (page - 1) * limit
        complaints = complaints[start_idx : start_idx + limit]

    caches = _build_format_caches(complaint_service)
    return [_format_complaint(complaint, complaint_service, *caches) for complaint in complaints]


@router.get("/paginated")
def list_complaints_paginated(
    status_filter: str | None = None,
    department_id: str | None = None,
    location_id: str | None = None,
    include_archived: bool = False,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
):
    from utils.pagination import paginate

    complaints = _visible_complaints(current_user, complaint_service, include_archived)
    if status_filter:
        complaints = [item for item in complaints if item.status == status_filter]
    if department_id:
        complaints = [
            item for item in complaints if item.department_id == department_id
        ]
    if location_id:
        complaints = [item for item in complaints if item.location_id == location_id]
    if not include_archived:
        complaints = [item for item in complaints if not item.archived]

    caches = _build_format_caches(complaint_service)
    formatted_items = [_format_complaint(c, complaint_service, *caches) for c in complaints]
    return paginate(formatted_items, page=page, limit=limit)


@router.get("/workload")
def get_workload_summary(
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
    team_service=Depends(get_team_service),
):
    u_role = (current_user.role or "").lower()
    if u_role in ("student", "super_admin"):
        if u_role == "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students are not authorized to view staff workload.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super Admin cannot access institutional operational data.",
            )

    visible_complaints = _visible_complaints(current_user, complaint_service)

    RESOLVED_STATUSES = {
        Complaint.RESOLVED,
        Complaint.CLOSED,
        Complaint.AUTO_CLOSED,
        Complaint.WAITING_VERIFICATION,
    }

    total_count = len(visible_complaints)
    resolved_count = 0
    left_count = 0
    unassigned_count = 0
    assigned_count = 0

    unassigned_list = []
    for c in visible_complaints:
        is_resolved = c.status in RESOLVED_STATUSES or c.resolved_at is not None
        if is_resolved:
            resolved_count += 1
        else:
            left_count += 1
            if not c.assigned_to or str(c.assigned_to).strip() == "":
                unassigned_count += 1
                unassigned_list.append(c)

        if c.assigned_to and str(c.assigned_to).strip() != "":
            assigned_count += 1

    all_users = complaint_service.auth_service.list_users()
    all_locations = complaint_service.auth_service.list_locations()
    all_departments = complaint_service.auth_service.list_departments()

    loc_map = {l.location_id: l.name for l in all_locations}
    dept_map = {d.department_id: d.name for d in all_departments}
    users_by_id = {u.user_id: u for u in all_users}

    # 1. Department-level workload aggregation
    departments_data = []
    coord_map = {}
    with complaint_service.auth_service._connect() as conn:
        dept_staff_counts = {}
        for r in conn.execute(
            "SELECT department_id, COUNT(DISTINCT user_id) as cnt FROM employee_work_memberships GROUP BY department_id"
        ).fetchall():
            dept_staff_counts[r[0]] = r[1]

        for d in all_departments:
            if getattr(d, "coordinator_id", None):
                coord_map[d.coordinator_id] = {
                    "position": "Coordinator 1",
                    "department_id": d.department_id,
                    "department_name": d.name,
                }
            if getattr(d, "coordinator_2_id", None):
                coord_map[d.coordinator_2_id] = {
                    "position": "Coordinator 2",
                    "department_id": d.department_id,
                    "department_name": d.name,
                }

        for dept in all_departments:
            if getattr(dept, "archived", False):
                continue

            dept_complaints = [c for c in visible_complaints if c.department_id == dept.department_id]
            d_total = len(dept_complaints)
            d_resolved = 0
            d_left = 0
            d_unassigned = 0
            d_assigned = 0

            for c in dept_complaints:
                is_res = c.status in RESOLVED_STATUSES or c.resolved_at is not None
                if is_res:
                    d_resolved += 1
                else:
                    d_left += 1
                    if not c.assigned_to or str(c.assigned_to).strip() == "":
                        d_unassigned += 1
                if c.assigned_to and str(c.assigned_to).strip() != "":
                    d_assigned += 1

            c1_id = getattr(dept, "coordinator_id", None)
            c2_id = getattr(dept, "coordinator_2_id", None)
            c1_user = users_by_id.get(c1_id) if c1_id else None
            c2_user = users_by_id.get(c2_id) if c2_id else None

            c1_leave = team_service.is_user_on_leave(c1_id) if c1_id else False
            c2_leave = team_service.is_user_on_leave(c2_id) if c2_id else False

            staff_cnt = dept_staff_counts.get(dept.department_id, 0)
            departments_data.append({
                "department_id": dept.department_id,
                "name": dept.name,
                "coordinator_1_id": c1_id,
                "coordinator_1_name": c1_user.name if c1_user else "Not Assigned",
                "coordinator_1_on_leave": c1_leave,
                "coordinator_2_id": c2_id,
                "coordinator_2_name": c2_user.name if c2_user else "Not Assigned",
                "coordinator_2_on_leave": c2_leave,
                "total": d_total,
                "unassigned": d_unassigned,
                "assigned": d_assigned,
                "left": d_left,
                "resolved": d_resolved,
                "staff_count": staff_cnt,
            })

    departments_data.sort(key=lambda d: (-d["total"], -d["staff_count"], d["name"]))

    # 2. Staff Workload lists
    app_managers = []
    wardens = []
    coordinators = []
    employees = []

    user_dept_names = {}
    with complaint_service.auth_service._connect() as conn:
        for r in conn.execute(
            "SELECT ewm.user_id, d.name FROM employee_work_memberships ewm JOIN departments d ON ewm.department_id = d.department_id"
        ).fetchall():
            uid, dname = r[0], r[1]
            if uid not in user_dept_names:
                user_dept_names[uid] = set()
            user_dept_names[uid].add(dname)

    for user in all_users:
        u_r = (user.role or "").lower()
        if u_r in ("student", "super_admin"):
            continue

        if u_role == "app_manager":
            assigned_locs = getattr(current_user, "assigned_locations", None) or []
            u_loc = getattr(user, "location_id", None)
            if u_r != "administrator":
                if u_loc and u_loc not in assigned_locs and u_loc != current_user.location_id:
                    continue
        elif u_role == "location_in_charge":
            if getattr(user, "location_id", None) != getattr(current_user, "location_id", None) and user.user_id != current_user.user_id:
                continue
        elif u_role == "coordinator":
            if getattr(user, "department_id", None) != getattr(current_user, "department_id", None) and user.user_id != current_user.user_id:
                continue

        staff_assigned = 0
        staff_left = 0
        staff_resolved = 0

        for c in visible_complaints:
            if c.assigned_to == user.user_id:
                staff_assigned += 1
                if c.status in RESOLVED_STATUSES or c.resolved_at is not None:
                    staff_resolved += 1
                else:
                    staff_left += 1

        on_leave = team_service.is_user_on_leave(user.user_id)
        coord_info = coord_map.get(user.user_id)
        coord_pos_str = f"{coord_info['position']} ({coord_info['department_name']})" if coord_info else None

        user_depts = sorted(list(user_dept_names.get(user.user_id, [])))
        if coord_info and coord_info["department_name"] not in user_depts:
            user_depts.append(coord_info["department_name"])

        staff_data = {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "location_id": getattr(user, "location_id", None),
            "location_name": loc_map.get(getattr(user, "location_id", None), getattr(user, "location_id", None) or ""),
            "department_id": getattr(user, "department_id", None) or (coord_info["department_id"] if coord_info else None),
            "department_name": dept_map.get(getattr(user, "department_id", None), getattr(user, "department_id", None) or "") or (coord_info["department_name"] if coord_info else ""),
            "department_names": user_depts,
            "coordinator_position": coord_pos_str,
            "on_leave": on_leave,
            "assigned": staff_assigned,
            "left": staff_left,
            "resolved": staff_resolved,
        }

        if u_r == "app_manager":
            app_managers.append(staff_data)
        elif u_r in ("location_in_charge", "warden"):
            wardens.append(staff_data)
        elif u_r == "coordinator" or coord_info is not None:
            coordinators.append(staff_data)

        if u_r == "employee":
            employees.append(staff_data)

    caches = _build_format_caches(complaint_service)
    formatted_unassigned = [
        _format_complaint(c, complaint_service, *caches)
        for c in unassigned_list
    ]

    return {
        "summary": {
            "total": total_count,
            "unassigned": unassigned_count,
            "assigned": assigned_count,
            "left": left_count,
            "resolved": resolved_count,
        },
        "departments": departments_data,
        "coordinators": coordinators,
        "employees": employees,
        "app_managers": app_managers,
        "wardens": wardens,
        "unassigned_complaints": formatted_unassigned,
    }


@router.get("/resolved")
def get_resolved_complaints(
    location_id: str | None = None,
    department_id: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    q: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
):
    u_role = (current_user.role or "").lower()
    if u_role == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin cannot access institutional operational data.",
        )

    visible_complaints = _visible_complaints(current_user, complaint_service)
    RESOLVED_STATUSES = {
        Complaint.RESOLVED,
        Complaint.CLOSED,
        Complaint.AUTO_CLOSED,
        Complaint.WAITING_VERIFICATION,
    }

    resolved_complaints = [
        c for c in visible_complaints
        if c.status in RESOLVED_STATUSES or c.resolved_at is not None
    ]

    if location_id:
        resolved_complaints = [c for c in resolved_complaints if c.location_id == location_id]
    if department_id:
        resolved_complaints = [c for c in resolved_complaints if c.department_id == department_id]
    if category:
        resolved_complaints = [
            c for c in resolved_complaints
            if (getattr(c, "category", None) or c.complaint_type or "").lower() == category.lower()
        ]
    if priority:
        resolved_complaints = [
            c for c in resolved_complaints
            if (getattr(c, "priority", None) or "").lower() == priority.lower()
        ]

    def _parse_dt(val):
        if not val:
            return None
        from datetime import datetime
        v_str = str(val).strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                return datetime.strptime(v_str[:19] if "T" not in fmt and len(v_str) >= 19 else v_str, fmt)
            except ValueError:
                pass
        try:
            return datetime.fromisoformat(v_str)
        except Exception:
            return None

    if date_from:
        d_from = _parse_dt(date_from)
        if d_from:
            resolved_complaints = [
                c for c in resolved_complaints
                if _parse_dt(c.resolved_at or c.created_at) and _parse_dt(c.resolved_at or c.created_at) >= d_from
            ]

    if date_to:
        d_to = _parse_dt(date_to)
        if d_to:
            resolved_complaints = [
                c for c in resolved_complaints
                if _parse_dt(c.resolved_at or c.created_at) and _parse_dt(c.resolved_at or c.created_at) <= d_to
            ]

    if q and q.strip():
        search_term = q.strip().lower()
        resolved_complaints = [
            c for c in resolved_complaints
            if search_term in (getattr(c, "title", "") or "").lower()
            or search_term in (c.description or "").lower()
            or search_term in (c.complaint_id or "").lower()
            or search_term in (getattr(c, "resolution_notes", "") or "").lower()
        ]

    resolved_complaints.sort(
        key=lambda c: c.resolved_at or c.updated_at or c.created_at or "",
        reverse=True
    )

    total_count = len(resolved_complaints)
    start_idx = (page - 1) * limit
    paginated_items = resolved_complaints[start_idx : start_idx + limit]

    caches = _build_format_caches(complaint_service)
    formatted_items = [
        _format_complaint(c, complaint_service, *caches)
        for c in paginated_items
    ]

    return {
        "items": formatted_items,
        "total": total_count,
        "page": page,
        "limit": limit,
    }


@router.get("/export/csv")
def export_complaints_csv(
    status_filter: str | None = None,
    department_id: str | None = None,
    location_id: str | None = None,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
):
    import csv
    import io

    from fastapi.responses import StreamingResponse

    complaints = _visible_complaints(
        current_user, complaint_service, include_archived=False
    )
    if status_filter:
        complaints = [item for item in complaints if item.status == status_filter]
    if department_id:
        complaints = [
            item for item in complaints if item.department_id == department_id
        ]
    if location_id:
        complaints = [item for item in complaints if item.location_id == location_id]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Complaint ID",
            "Title",
            "Category",
            "Complaint Type",
            "Status",
            "Priority",
            "Location ID",
            "Department ID",
            "Assigned To",
            "Created By",
            "Created At",
            "Resolved At",
            "SLA Status",
            "Visibility",
        ]
    )

    for c in complaints:
        writer.writerow(
            [
                csv_safe(c.complaint_id),
                csv_safe(c.title or ""),
                csv_safe(c.category or ""),
                csv_safe(c.complaint_type or ""),
                csv_safe(c.status),
                csv_safe(c.priority or "Medium"),
                csv_safe(c.location_id),
                csv_safe(c.department_id),
                csv_safe(c.assigned_to or "Unassigned"),
                csv_safe(c.created_by),
                csv_safe(c.created_at),
                csv_safe(c.resolved_at or ""),
                csv_safe(getattr(c, "sla_status", "🟢 On Time")),
                csv_safe(c.visibility_type),
            ]
        )

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="complaints_export.csv"'},
    )


@router.get("/analytics", response_model=AnalyticsResponse)
def analytics(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    complaint_service=Depends(get_complaint_service),
):
    return complaint_service.analytics()


@router.get("/unassigned", response_model=list[ComplaintResponse])
def unassigned(
    current_user=Depends(require_roles(AppManager.ROLE, Administrator.ROLE)),
    complaint_service=Depends(get_complaint_service),
):
    return [
        _format_complaint(complaint, complaint_service)
        for complaint in complaint_service.unassigned_complaints()
    ]


@router.get("/duplicates")
def search_duplicate_complaints(
    location_id: str,
    department_id: str,
    issue_id: str | None = None,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
):
    return complaint_service.get_duplicate_complaints(
        location_id=location_id,
        department_id=department_id,
        issue_id=issue_id,
    )


@router.get("/similar", response_model=list[dict])
@router.get("/suggestions/list", response_model=list[dict])
def get_complaint_suggestions(
    location_id: Optional[str] = None,
    category: Optional[str] = None,
    q: Optional[str] = None,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
):
    all_complaints = complaint_service.list_all()
    suggestions = []

    inactive_statuses = set(INACTIVE_STATUSES) | {
        Complaint.CLOSED,
        Complaint.AUTO_CLOSED,
        STATUS_CLOSED,
        STATUS_AUTO_CLOSED,
        STATUS_REJECTED,
        STATUS_CANCELLED,
    }

    user_loc_id = getattr(current_user, "location_id", None)

    for c in all_complaints:
        if c.status in inactive_statuses:
            continue
        if c.visibility_type not in ("Community", "Public", "public", "community"):
            continue
        if location_id and c.location_id != location_id:
            continue
        if category and (c.category or "").lower() != category.lower():
            continue
        if not location_id and current_user.role == Student.ROLE and user_loc_id and c.location_id != user_loc_id:
            continue
        match = True
        if q and q.strip():
            query_lower = q.strip().lower()
            match = (query_lower in (c.title or "").lower()) or (
                query_lower in (c.description or "").lower()
            )
        if match:
            suggestions.append(
                {
                    "complaint_id": c.complaint_id,
                    "title": c.title,
                    "status": c.status,
                    "priority": c.priority,
                    "category": c.category,
                    "location_id": c.location_id,
                    "description": c.description,
                    "affected_count": complaint_service.get_affected_count(
                        c.complaint_id
                    ),
                    "created_at": c.created_at,
                }
            )
    return suggestions


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(
    complaint_id: str,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
):
    if (current_user.role or "").lower() == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin cannot access institutional operational data.",
        )
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    _ensure_visible(complaint, current_user, complaint_service)
    return _format_complaint(complaint, complaint_service)


@router.get("/{complaint_id}/emergency-contacts")
def get_complaint_emergency_contacts(
    complaint_id: str,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
):
    if (current_user.role or "").lower() == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin cannot access institutional operational data.",
        )
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    _ensure_visible(complaint, current_user, complaint_service)
    contacts = _get_critical_emergency_contacts(complaint, complaint_service)
    return {
        "complaint_id": complaint_id,
        "priority": complaint.priority,
        "contacts": contacts,
    }


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED)
def create_complaint(
    payload: ComplaintCreateRequest,
    current_user=Depends(require_roles(Student.ROLE, LocationInCharge.ROLE)),
    complaint_service=Depends(get_complaint_service),
    classification_service=Depends(get_classification_service),
):
    logger.info(
        f"Creating complaint for user {current_user.user_id} ({current_user.role})"
    )
    try:
        cat = payload.category or payload.complaint_type
        ct = payload.complaint_type or payload.category

        # Auto-classification: always runs on submission for visibility/audit.
        # It only fills in complaint_type when the caller left it blank, and
        # only ever logs a department_id suggestion — department_id is a
        # required, routing-critical field validated by complaint_service, so
        # it is never silently overridden here.
        try:
            prediction = classification_service.predict(payload.description)
            if not ct and prediction.complaint_type:
                ct = prediction.complaint_type
                cat = cat or ct
                logger.info(
                    f"Auto-classified complaint_type='{ct}' "
                    f"(confidence={prediction.complaint_type_confidence:.2f}, "
                    f"trained_on={prediction.trained_on}) for user {current_user.user_id}"
                )
            if prediction.department_id and prediction.department_id != payload.department_id:
                logger.info(
                    f"classification_service suggests department_id='{prediction.department_id}' "
                    f"(confidence={prediction.department_confidence:.2f}); submitted "
                    f"department_id='{payload.department_id}' was kept as selected by the user."
                )
        except Exception:
            logger.exception(
                "Complaint auto-classification failed; continuing without it."
            )

        complaint = complaint_service.create_complaint(
            current_user,
            payload.location_id,
            payload.department_id,
            ct,
            payload.description,
            payload.title,
            attachment_url=payload.attachment_url,
            category=cat,
            visibility_type=payload.visibility_type,
            issue_id=payload.issue_id,
            visibility=payload.visibility,
            priority=payload.priority,
            is_urgent=payload.is_urgent,
            urgent_reason=payload.urgent_reason,
            exact_spot=payload.exact_spot,
        )
        _broadcast_complaint_event("complaint_created", complaint)
        _broadcast_complaint_event("health_map_changed", complaint)
        return _format_complaint(complaint, complaint_service)
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as error:
        logger.error(f"Complaint creation failed: {error}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


class ComplaintProgressRequest(BaseModel):
    note_code: Optional[str] = None
    note: Optional[str] = None
    photo_url: Optional[str] = None


class ComplaintBlockRequest(BaseModel):
    reason: str
    expected_date: Optional[str] = None


@router.post("/{complaint_id}/take", response_model=ComplaintResponse)
@router.post("/{complaint_id}/accept", response_model=ComplaintResponse)
def accept_complaint(
    complaint_id: str,
    current_user=Depends(
        require_roles(Coordinator.ROLE, Administrator.ROLE, Employee.ROLE)
    ),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    _ensure_visible(complaint, current_user, complaint_service)

    u_role = (current_user.role or "").lower()
    if u_role in ("coordinator", "employee"):
        is_coord = complaint_service.auth_service.is_coordinator_assigned(
            current_user.user_id, complaint.location_id, complaint.department_id
        )
        if not is_coord and getattr(complaint, "team_id", None) and hasattr(complaint_service, "team_service"):
            team = complaint_service.team_service.get_team(complaint.team_id)
            if team:
                acting = complaint_service.team_service.get_acting_coordinator(team)
                if acting and acting.user_id == current_user.user_id:
                    is_coord = True
        if not is_coord:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to coordinate complaints for this department.",
            )

    try:
        complaint = complaint_service.accept_complaint(complaint_id, current_user.user_id)
        try:
            from utils.websocket_manager import manager
            event = {
                "event": "complaint_accepted",
                "complaint_id": complaint_id,
                "assigned_to": current_user.user_id,
                "status": "In Progress",
            }
            manager.push_sync("coordinator", event)
            manager.push_sync(complaint.created_by, event)
            loc = complaint_service.auth_service.get_location(complaint.location_id)
            if loc and getattr(loc, "in_charge_id", None):
                manager.push_sync(loc.in_charge_id, event)
            _broadcast_complaint_event("complaint_accepted", complaint, {"assigned_to": current_user.user_id})
            _broadcast_complaint_event("complaint_updated", complaint)
        except Exception:
            pass
        return _format_complaint(complaint, complaint_service)
    except ComplaintConflictError as c_err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(c_err))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/{complaint_id}/start-work", response_model=ComplaintResponse)
def start_work_on_complaint(
    complaint_id: str,
    current_user=Depends(
        require_roles(Coordinator.ROLE, Administrator.ROLE, Employee.ROLE)
    ),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    _ensure_visible(complaint, current_user, complaint_service)
    try:
        complaint = complaint_service.start_work(complaint_id, current_user.user_id)
        _broadcast_complaint_event("complaint_updated", complaint)
        return _format_complaint(complaint, complaint_service)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/{complaint_id}/progress", response_model=ComplaintResponse)
@router.post("/{complaint_id}/progress-notes", response_model=ComplaintResponse)
def record_complaint_progress(
    complaint_id: str,
    payload: ComplaintProgressRequest,
    current_user=Depends(
        require_roles(Coordinator.ROLE, Administrator.ROLE, Employee.ROLE)
    ),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    _ensure_visible(complaint, current_user, complaint_service)
    try:
        complaint = complaint_service.record_progress(
            complaint_id,
            current_user.user_id,
            note=payload.note,
            photo_url=payload.photo_url,
            note_code=payload.note_code,
        )
        _broadcast_complaint_event("complaint_updated", complaint)
        return _format_complaint(complaint, complaint_service)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/{complaint_id}/block", response_model=ComplaintResponse)
@router.post("/{complaint_id}/pause", response_model=ComplaintResponse)
def block_complaint(
    complaint_id: str,
    payload: ComplaintBlockRequest,
    current_user=Depends(
        require_roles(Coordinator.ROLE, Administrator.ROLE, Employee.ROLE)
    ),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    _ensure_visible(complaint, current_user, complaint_service)
    try:
        complaint = complaint_service.block_complaint(
            complaint_id, current_user.user_id, payload.reason, payload.expected_date
        )
        _broadcast_complaint_event("complaint_updated", complaint)
        return _format_complaint(complaint, complaint_service)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/{complaint_id}/unblock", response_model=ComplaintResponse)
@router.post("/{complaint_id}/resume", response_model=ComplaintResponse)
def unblock_complaint(
    complaint_id: str,
    current_user=Depends(
        require_roles(Coordinator.ROLE, Administrator.ROLE, Employee.ROLE)
    ),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    _ensure_visible(complaint, current_user, complaint_service)
    try:
        complaint = complaint_service.unblock_complaint(complaint_id, current_user.user_id)
        _broadcast_complaint_event("complaint_updated", complaint)
        return _format_complaint(complaint, complaint_service)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/{complaint_id}/close", response_model=ComplaintResponse)
@router.post("/{complaint_id}/confirm", response_model=ComplaintResponse)
def close_complaint(
    complaint_id: str,
    current_user=Depends(
        require_roles(Student.ROLE, LocationInCharge.ROLE, Administrator.ROLE)
    ),
    complaint_service=Depends(get_complaint_service),
):
    # Backwards-compatible alias for the explicit verification endpoint.
    try:
        complaint = complaint_service.verify_fixed(complaint_id, current_user)
        return _format_complaint(complaint, complaint_service)
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

@router.get("/{complaint_id}/eligible-assignees")
def get_eligible_assignees(
    complaint_id: str,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    _ensure_visible(complaint, current_user, complaint_service)
    try:
        return complaint_service.get_eligible_assignees(complaint_id)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/{complaint_id}/reassign", response_model=ComplaintResponse)
@router.post("/{complaint_id}/assign", response_model=ComplaintResponse)
def assign_complaint(

    complaint_id: str,
    payload: ComplaintAssignRequest,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
    audit_service=Depends(get_audit_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )

    _ensure_visible(complaint, current_user, complaint_service)

    target_id = payload.assigned_to or payload.assignee_id or payload.coordinator_id
    if not target_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target assignee is required.",
        )

    old_assigned = complaint.assigned_to
    is_reassign = bool(old_assigned and old_assigned != target_id)

    try:
        complaint = complaint_service.assign_work(
            complaint_id, target_id, reason=payload.reason, actor_id=current_user.user_id
        )
        action_name = "REASSIGN_COMPLAINT" if is_reassign else "ASSIGN_COMPLAINT"
        audit_service.log(
            current_user.user_id,
            action_name,
            complaint_id,
            old_value={"assigned_to": old_assigned},
            new_value={"assigned_to": target_id, "reason": payload.reason},
        )
        return _format_complaint(complaint, complaint_service)
    except ComplaintConflictError as c_err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(c_err))
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/{complaint_id}/reroute", response_model=ComplaintResponse)
def reroute_complaint(
    complaint_id: str,
    payload: ComplaintRerouteRequest,
    current_user=Depends(require_roles(Administrator.ROLE, Coordinator.ROLE, Employee.ROLE, AppManager.ROLE)),
    complaint_service=Depends(get_complaint_service),
    audit_service=Depends(get_audit_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )

    _ensure_visible(complaint, current_user, complaint_service)

    u_role = (current_user.role or "").lower()
    if u_role in ("coordinator", "employee"):
        if not complaint_service.is_coordinator_in_scope(current_user, complaint):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to reroute complaints from this department.",
            )

    old_dept_id = complaint.department_id
    try:
        updated = complaint_service.reroute_complaint(
            complaint_id=complaint_id,
            destination_department_id=payload.destination_department_id,
            reason=payload.reason,
            actor_id=current_user.user_id,
        )
        audit_service.log(
            current_user.user_id,
            "REROUTE_COMPLAINT",
            complaint_id,
            old_value={"department_id": old_dept_id},
            new_value={"department_id": payload.destination_department_id, "reason": payload.reason},
        )
        _broadcast_complaint_event("complaint_rerouted", updated, {
            "source_department_id": old_dept_id,
            "destination_department_id": payload.destination_department_id,
            "reason": payload.reason,
        })
        _broadcast_complaint_event("complaint_updated", updated)
        return _format_complaint(updated, complaint_service)
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as v_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(v_err))
    except ComplaintConflictError as c_err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(c_err))


@router.post("/{complaint_id}/return", response_model=ComplaintResponse)
def return_complaint_to_coordinator(
    complaint_id: str,
    payload: ComplaintReturnRequest,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
    audit_service=Depends(get_audit_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )

    _ensure_visible(complaint, current_user, complaint_service)

    try:
        complaint = complaint_service.return_to_coordinator(
            complaint_id, current_user.user_id, reason=payload.reason
        )
        audit_service.log(
            current_user.user_id,
            "RETURN_COMPLAINT",
            complaint_id,
            new_value={"reason": payload.reason},
        )
        return _format_complaint(complaint, complaint_service)
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/{complaint_id}/wrong-location", response_model=ComplaintResponse)
def report_wrong_location(
    complaint_id: str,
    payload: ComplaintWrongLocationRequest,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
    audit_service=Depends(get_audit_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )

    u_role = (current_user.role or "").lower()
    is_assignee = complaint.assigned_to == current_user.user_id
    is_warden = (
        u_role in ("location_in_charge", "warden")
        and complaint_service.auth_service.is_warden_assigned(current_user.user_id, complaint.location_id)
    )
    is_mgr_or_admin = u_role in ("app_manager", "administrator")

    if not (is_assignee or is_warden or is_mgr_or_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the assigned coordinator, Warden, App Manager, or Admin can report a wrong location.",
        )

    old_location_id = complaint.location_id
    try:
        complaint = complaint_service.correct_location(
            complaint_id,
            payload.correct_location_id,
            user=current_user,
            note=payload.note,
        )
        audit_service.log(
            current_user.user_id,
            "CORRECT_LOCATION",
            complaint_id,
            old_value={"location_id": old_location_id},
            new_value={"location_id": payload.correct_location_id, "note": payload.note},
        )
        return _format_complaint(complaint, complaint_service)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{complaint_id}/status", response_model=ComplaintResponse)
def update_status(
    complaint_id: str,
    payload: ComplaintStatusRequest,
    current_user=Depends(
        require_roles(Coordinator.ROLE, Administrator.ROLE, Employee.ROLE)
    ),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )

    u_role = current_user.role.lower()
    if u_role in ("coordinator", "employee") and complaint.assigned_to != current_user.user_id:
        is_coord = False
        if complaint.team_id and hasattr(complaint_service, "team_service"):
            team = complaint_service.team_service.get_team(complaint.team_id)
            if team:
                acting = complaint_service.team_service.get_acting_coordinator(team)
                if acting and acting.user_id == current_user.user_id:
                    is_coord = True
        if not is_coord:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only change status for complaints assigned to you or in your team.",
            )

    if payload.status == Complaint.ASSIGNED:
        if complaint.status not in (
            Complaint.PENDING,
            Complaint.SUBMITTED,
            Complaint.REOPENED,
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only transition to Assigned from Pending, Submitted, or Reopened status.",
            )
        try:
            if u_role in ("coordinator", "employee"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Please assign this complaint using the assign endpoint.",
                )
            else:
                complaint.status = Complaint.ASSIGNED
                complaint.add_history(
                    f"Status changed to Assigned by {current_user.name}."
                )
                complaint_service.save_complaint(complaint)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    elif payload.status == Complaint.IN_PROGRESS:
        if complaint.status not in (Complaint.ASSIGNED, Complaint.REOPENED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only transition to In Progress from Assigned or Reopened status.",
            )
        try:
            if u_role in ("coordinator", "employee"):
                complaint = complaint_service.start_work(
                    complaint_id, current_user.user_id
                )
            else:
                complaint.status = Complaint.IN_PROGRESS
                complaint.add_history(
                    f"Status changed to In Progress by {current_user.name}."
                )
                complaint_service.save_complaint(complaint)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported status transition.",
        )

    return _format_complaint(complaint, complaint_service)


@router.put("/{complaint_id}/resolve", response_model=ComplaintResponse)
@router.post("/{complaint_id}/resolve", response_model=ComplaintResponse)
def resolve_complaint(
    complaint_id: str,
    payload: ComplaintResolveRequest,
    current_user=Depends(
        require_roles(Coordinator.ROLE, Administrator.ROLE, Employee.ROLE)
    ),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    if complaint.status not in (
        STATUS_GOING_ON,
        "Going On",
        Complaint.IN_PROGRESS,
        Complaint.ASSIGNED,
        "In Progress",
        "Assigned",
        "Reopened",
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint must be Going On before it can be resolved.",
        )

    u_role = current_user.role.lower()
    if u_role == "employee" and complaint.assigned_to != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only resolve complaints assigned to you.",
        )
    if u_role == "coordinator" and complaint.assigned_to != current_user.user_id:
        is_team_coord = False
        if complaint.team_id and hasattr(complaint_service, "team_service"):
            team = complaint_service.team_service.get_team(complaint.team_id)
            if team:
                acting = complaint_service.team_service.get_acting_coordinator(team)
                if acting and acting.user_id == current_user.user_id:
                    is_team_coord = True
        if not is_team_coord:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only resolve complaints assigned to you or in your team.",
            )
    try:
        complaint = complaint_service.mark_resolved(
            complaint_id,
            current_user.user_id,
            notes=payload.notes or "",
            preset_code=payload.preset_code,
            proof_url=payload.proof_url,
            skip_photo=bool(payload.skip_photo or payload.photo_skipped),
            photo_skip_reason=payload.photo_skip_reason,
        )
        _broadcast_complaint_event("complaint_updated", complaint)
        _broadcast_complaint_event("health_map_changed", complaint)
        return _format_complaint(complaint, complaint_service)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.put("/{complaint_id}/warden-verify", response_model=ComplaintResponse)
@router.post("/{complaint_id}/warden-verify", response_model=ComplaintResponse)
def warden_verify_complaint(
    complaint_id: str,
    payload: WardenVerifyRequest,
    current_user=Depends(
        require_roles(LocationInCharge.ROLE, Administrator.ROLE)
    ),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    _ensure_visible(complaint, current_user, complaint_service)
    try:
        complaint = complaint_service.warden_verify(
            complaint_id,
            current_user,
            verdict=payload.verdict,
            notes=payload.notes or "",
            approved=payload.approved,
            photo_mismatch=bool(payload.photo_mismatch),
        )
        _broadcast_complaint_event("complaint_updated", complaint)
        _broadcast_complaint_event("health_map_changed", complaint)
        return _format_complaint(complaint, complaint_service)
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.put("/{complaint_id}/verify", response_model=ComplaintResponse)
@router.post("/{complaint_id}/verify", response_model=ComplaintResponse)
def verify_complaint(
    complaint_id: str,
    current_user=Depends(require_roles(Student.ROLE, LocationInCharge.ROLE, Administrator.ROLE)),
    complaint_service=Depends(get_complaint_service),
):
    try:
        complaint = complaint_service.verify_fixed(complaint_id, current_user)
        _broadcast_complaint_event("complaint_updated", complaint)
        _broadcast_complaint_event("health_map_changed", complaint)
        return _format_complaint(complaint, complaint_service)
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/{complaint_id}/reopen", response_model=ComplaintResponse)
def reopen_complaint(
    complaint_id: str,
    payload: ComplaintReopenRequest,
    current_user=Depends(require_roles(Student.ROLE, LocationInCharge.ROLE, Administrator.ROLE)),
    complaint_service=Depends(get_complaint_service),
):
    try:
        complaint = complaint_service.reopen_complaint(
            complaint_id, current_user, payload.reason
        )
        _broadcast_complaint_event("complaint_updated", complaint)
        _broadcast_complaint_event("health_map_changed", complaint)
        return _format_complaint(complaint, complaint_service)
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/{complaint_id}/admin-decision", response_model=ComplaintResponse)
def admin_decision_on_complaint(
    complaint_id: str,
    payload: AdminDecisionRequest,
    current_user=Depends(require_roles(Administrator.ROLE)),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    try:
        reassign_target = payload.reassign_to or payload.assign_to
        complaint = complaint_service.admin_decision(
            complaint_id, current_user, payload.decision, payload.notes, reassign_target
        )
        _broadcast_complaint_event("complaint_updated", complaint)
        _broadcast_complaint_event("health_map_changed", complaint)
        return _format_complaint(complaint, complaint_service)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))



@router.patch("/{complaint_id}", response_model=ComplaintResponse)
def update_complaint(
    complaint_id: str,
    payload: ComplaintUpdateRequest,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
    audit_service=Depends(get_audit_service),
    translation_service=Depends(get_translation_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )

    _ensure_visible(complaint, current_user, complaint_service)
    u_role = (current_user.role or "").lower()

    # Rule: only the owner, an Administrator or an App Manager can edit a complaint
    if u_role not in ("administrator", "app_manager") and complaint.created_by != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own complaints.",
        )

    # Rule: Student can only edit while status is Submitted
    if u_role == "student" and complaint.status != Complaint.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaints can only be edited while in Submitted status.",
        )

    if complaint.status in (
        Complaint.CLOSED,
        Complaint.AUTO_CLOSED,
        Complaint.WAITING_VERIFICATION,
        Complaint.RESOLVED,
    ):
        if payload.status is None and payload.archived is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot edit complaint details after resolution unless reopened.",
            )

    old_value = complaint.to_dict()

    # Hierarchy validation for edited fields
    auth_service = complaint_service.auth_service
    loc_or_dept_changed = False
    if payload.location_id and payload.location_id != complaint.location_id:
        loc = auth_service.get_location(payload.location_id)
        if not loc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Location does not exist."
            )
        if u_role == "student":
            loc_type = (getattr(loc, "location_type", "") or getattr(loc, "name", "")).lower()
            if "hostel" in loc_type:
                student_loc_id = getattr(current_user, "location_id", None)
                if not student_loc_id:
                    profile = auth_service.get_student_profile(current_user.user_id)
                    student_loc_id = profile.get("location_id") if profile else None
                student_loc = auth_service.get_location(student_loc_id) if student_loc_id else None
                is_match = False
                if student_loc_id and loc.location_id == student_loc_id:
                    is_match = True
                elif student_loc and (
                    loc.location_id == student_loc.location_id
                    or loc.name.lower() == student_loc.name.lower()
                ):
                    is_match = True
                if not is_match:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Students can only submit complaints for their assigned hostel.",
                    )
        complaint.location_id = payload.location_id
        loc_or_dept_changed = True

    if payload.department_id and payload.department_id != complaint.department_id:
        dept = auth_service.get_department(payload.department_id)
        if not dept:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Department does not exist."
            )
        complaint.department_id = payload.department_id
        loc_or_dept_changed = True

    if loc_or_dept_changed and complaint.assigned_to:
        is_still_auth = auth_service.is_coordinator_assigned(
            complaint.assigned_to, complaint.location_id, complaint.department_id
        )
        if not is_still_auth:
            old_assigned = complaint.assigned_to
            complaint.assigned_to = None
            if complaint.status in (Complaint.ASSIGNED, Complaint.IN_PROGRESS):
                complaint.status = Complaint.SUBMITTED
            complaint.add_history(
                f"Complaint unassigned from coordinator {old_assigned} and returned to Submitted because location/department was modified."
            )

    if payload.complaint_type or payload.category:
        c_type = payload.complaint_type or payload.category
        complaint.complaint_type = c_type
        complaint.category = payload.category or c_type

    if payload.description is not None:
        if not payload.description.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Description is required."
            )
        new_desc = payload.description.strip()
        if complaint.description != new_desc:
            complaint.description = new_desc
            try:
                translation_service.invalidate_complaint_translations(complaint_id)
            except Exception as e:
                logger.warning(f"Failed to invalidate translations for {complaint_id}: {e}")

    if payload.title is not None:
        complaint.title = payload.title.strip()

    if payload.attachment_url is not None:
        complaint.attachment_url = payload.attachment_url

    if payload.visibility_type is not None:
        complaint.visibility_type = payload.visibility_type

    if payload.archived is not None:
        if u_role not in ("administrator", "app_manager"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Admins or App Managers can archive complaints.",
            )
        complaint.archived = payload.archived
        complaint.add_history(
            f"Complaint {'archived' if payload.archived else 'restored'}."
        )

    if payload.status is not None or payload.assigned_to is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use the status or assignment endpoint for workflow changes.",
        )

    complaint.add_history(f"Complaint details updated by {current_user.name}.")
    complaint_service.save_complaint(complaint)
    new_value = complaint.to_dict()

    audit_service.log(
        current_user.user_id,
        "Update Complaint",
        complaint_id,
        old_value=old_value,
        new_value=new_value,
    )
    return _format_complaint(complaint, complaint_service)


@router.delete("/{complaint_id}")
def delete_complaint(
    complaint_id: str,
    payload: ComplaintDeleteRequestPayload = None,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
    audit_service=Depends(get_audit_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )

    _ensure_visible(complaint, current_user, complaint_service)
    u_role = (current_user.role or "").lower()
    reason = (payload.reason if payload and payload.reason else "").strip() or "No reason provided."

    # 1. Administrator or App Manager -> Direct Soft Delete
    if u_role in ("administrator", "app_manager"):
        old_value = complaint.to_dict()
        complaint.archived = True
        complaint.is_deleted = True
        complaint.deletion_requested = False
        from utils.helper import now_string
        complaint.deleted_at = now_string()
        complaint.deleted_by = current_user.user_id
        complaint.add_history(f"Deleted by {current_user.name} ({current_user.role}).")
        complaint_service.save_complaint(complaint)

        audit_service.log_event(
            module="Complaint",
            entity_type="Complaint",
            entity_id=complaint_id,
            action="DELETE",
            performed_by=current_user.user_id,
            performed_role=current_user.role,
            old_value=old_value,
            new_value={"is_deleted": True, "deleted_at": complaint.deleted_at},
            description=f"Admin soft-deleted complaint {complaint_id}",
        )
        return {"message": "Complaint deleted successfully.", "complaint_id": complaint_id, "status": "deleted"}

    # 2. Coordinator or Location In-Charge (Warden) -> Submit Deletion Request to App Manager
    elif u_role in ("coordinator", "location_in_charge"):
        from utils.helper import now_string
        complaint.deletion_requested = True
        complaint.deletion_requested_by = current_user.user_id
        complaint.deletion_requested_name = current_user.name
        complaint.deletion_requested_role = current_user.role
        complaint.deletion_reason = reason
        complaint.deletion_requested_at = now_string()
        complaint.add_history(f"Deletion requested by {current_user.name} ({current_user.role}): {reason}")
        complaint_service.save_complaint(complaint)

        # Send High Priority Notification to App Manager(s)
        try:
            auth_svc = complaint_service.auth_service
            app_managers = auth_svc.list_users(role="app_manager")
            target_managers = [
                mgr for mgr in app_managers
                if auth_svc.is_app_manager_assigned(mgr.user_id, complaint.location_id)
            ]
            if not target_managers:
                target_managers = app_managers

            for mgr in target_managers:
                complaint_service.notification_service.create_notification(
                    receiver_id=mgr.user_id,
                    title=f"Deletion Requested: {complaint_id}",
                    message=f"{current_user.name} ({current_user.role}) requested deletion of ticket {complaint_id}: \"{reason}\". Click to review.",
                    reference_type="Complaint",
                    reference_id=complaint_id,
                    priority="High",
                )
        except Exception:
            pass

        return {
            "message": "Deletion request submitted to App Manager for approval.",
            "complaint_id": complaint_id,
            "status": "deletion_requested",
        }

    # 3. Student -> Direct Soft Delete if status is Submitted and complaint is not assigned
    elif u_role == "student":
        allowed_creators = {current_user.user_id}
        if getattr(current_user, "email", None):
            allowed_creators.add(current_user.email)
        if complaint.created_by not in allowed_creators:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own complaints.",
            )
        if complaint.status != Complaint.SUBMITTED or complaint.assigned_to:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Complaints can only be deleted in Submitted status without an assignee. Assigned complaints cannot be deleted directly; please submit a cancellation request instead.",
            )
        old_value = complaint.to_dict()
        complaint.archived = True
        complaint.is_deleted = True
        from utils.helper import now_string
        complaint.deleted_at = now_string()
        complaint.deleted_by = current_user.user_id
        complaint.add_history(f"Soft deleted by student {current_user.name}.")
        complaint_service.save_complaint(complaint)
        audit_service.log_event(
            module="Complaint",
            entity_type="Complaint",
            entity_id=complaint_id,
            action="DELETE",
            performed_by=current_user.user_id,
            performed_role=current_user.role,
            old_value=old_value,
            new_value={"is_deleted": True, "deleted_at": complaint.deleted_at},
            description=f"Student soft-deleted unassigned complaint {complaint_id}",
        )
        return {"message": "Complaint deleted successfully.", "complaint_id": complaint_id, "status": "deleted"}
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized to delete complaint.")


@router.post("/{complaint_id}/approve-deletion", response_model=ComplaintResponse)
def approve_deletion(
    complaint_id: str,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    complaint_service=Depends(get_complaint_service),
    audit_service=Depends(get_audit_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    old_value = complaint.to_dict()
    complaint.archived = True
    complaint.is_deleted = True
    complaint.deletion_requested = False
    from utils.helper import now_string
    complaint.deleted_at = now_string()
    complaint.deleted_by = current_user.user_id
    complaint.add_history(f"Deletion approved by {current_user.name} ({current_user.role}). Complaint soft-deleted.")
    complaint_service.save_complaint(complaint)

    if complaint.deletion_requested_by:
        try:
            complaint_service.notification_service.create_notification(
                receiver_id=complaint.deletion_requested_by,
                title=f"Deletion Approved: {complaint_id}",
                message=f"Your deletion request for ticket {complaint_id} was approved by {current_user.name}.",
                reference_type="Complaint",
                reference_id=complaint_id,
                priority="Normal",
            )
        except Exception:
            pass

    audit_service.log(
        current_user.user_id,
        "Approve Complaint Deletion",
        complaint_id,
        old_value=old_value,
        new_value={"is_deleted": True, "deleted_at": complaint.deleted_at},
    )
    return _format_complaint(complaint, complaint_service)


@router.post("/{complaint_id}/reject-deletion", response_model=ComplaintResponse)
def reject_deletion(
    complaint_id: str,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    req_by = complaint.deletion_requested_by
    complaint.deletion_requested = False
    complaint.add_history(f"Deletion request rejected by {current_user.name} ({current_user.role}).")
    complaint_service.save_complaint(complaint)

    if req_by:
        try:
            complaint_service.notification_service.create_notification(
                receiver_id=req_by,
                title=f"Deletion Request Rejected: {complaint_id}",
                message=f"Your deletion request for ticket {complaint_id} was rejected by {current_user.name}.",
                reference_type="Complaint",
                reference_id=complaint_id,
                priority="Normal",
            )
        except Exception:
            pass

    return _format_complaint(complaint, complaint_service)


@router.post("/{complaint_id}/request-cancellation", response_model=ComplaintResponse)
def request_cancellation(
    complaint_id: str,
    payload: ComplaintCancellationRequestPayload,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
    audit_service=Depends(get_audit_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    _ensure_visible(complaint, current_user, complaint_service)
    try:
        old_val = complaint.to_dict()
        updated = complaint_service.request_cancellation(
            complaint_id=complaint_id,
            user=current_user,
            reason=payload.reason,
        )
        audit_service.log_event(
            module="Complaint",
            entity_type="Complaint",
            entity_id=complaint_id,
            action="REQUEST_CANCELLATION",
            performed_by=current_user.user_id,
            performed_role=current_user.role,
            old_value=old_val,
            new_value={"status": updated.status, "cancellation_reason": payload.reason},
            description=f"Cancellation requested for {complaint_id}: {payload.reason}",
        )
        _broadcast_complaint_event("complaint_cancellation_requested", updated, {"reason": payload.reason})
        _broadcast_complaint_event("complaint_updated", updated)
        return _format_complaint(updated, complaint_service)
    except ComplaintConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{complaint_id}/approve-cancellation", response_model=ComplaintResponse)
def approve_cancellation(
    complaint_id: str,
    payload: Optional[ComplaintCancellationReviewPayload] = None,
    current_user=Depends(require_roles(Coordinator.ROLE, Administrator.ROLE, AppManager.ROLE, Employee.ROLE)),
    complaint_service=Depends(get_complaint_service),
    audit_service=Depends(get_audit_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    _ensure_visible(complaint, current_user, complaint_service)
    note = payload.note if payload and payload.note else ""
    try:
        old_val = complaint.to_dict()
        updated = complaint_service.approve_cancellation(
            complaint_id=complaint_id,
            user=current_user,
            note=note,
        )
        audit_service.log_event(
            module="Complaint",
            entity_type="Complaint",
            entity_id=complaint_id,
            action="APPROVE_CANCELLATION",
            performed_by=current_user.user_id,
            performed_role=current_user.role,
            old_value=old_val,
            new_value={"status": updated.status, "note": note},
            description=f"Cancellation approved for {complaint_id}",
        )
        _broadcast_complaint_event("complaint_cancelled", updated, {"note": note})
        _broadcast_complaint_event("complaint_updated", updated)
        return _format_complaint(updated, complaint_service)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{complaint_id}/reject-cancellation", response_model=ComplaintResponse)
def reject_cancellation(
    complaint_id: str,
    payload: ComplaintCancellationRejectPayload,
    current_user=Depends(require_roles(Coordinator.ROLE, Administrator.ROLE, AppManager.ROLE, Employee.ROLE)),
    complaint_service=Depends(get_complaint_service),
    audit_service=Depends(get_audit_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    _ensure_visible(complaint, current_user, complaint_service)
    try:
        old_val = complaint.to_dict()
        updated = complaint_service.reject_cancellation(
            complaint_id=complaint_id,
            user=current_user,
            reason=payload.reason,
        )
        audit_service.log_event(
            module="Complaint",
            entity_type="Complaint",
            entity_id=complaint_id,
            action="REJECT_CANCELLATION",
            performed_by=current_user.user_id,
            performed_role=current_user.role,
            old_value=old_val,
            new_value={"status": updated.status, "reason": payload.reason},
            description=f"Cancellation rejected for {complaint_id}: {payload.reason}",
        )
        _broadcast_complaint_event("complaint_cancellation_rejected", updated, {"reason": payload.reason})
        _broadcast_complaint_event("complaint_updated", updated)
        return _format_complaint(updated, complaint_service)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/coordinators/stats")
@router.get("/coordinator-stats")
def get_coordinator_stats_endpoint(
    location_id: Optional[str] = None,
    department_id: Optional[str] = None,
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
):
    return complaint_service.get_coordinator_stats(
        location_id=location_id,
        department_id=department_id,
        from_date=from_date,
        to_date=to_date,
        current_user=current_user,
    )


@router.put("/{complaint_id}/priority", response_model=ComplaintResponse)
@router.patch("/{complaint_id}/priority", response_model=ComplaintResponse)
def update_priority(
    complaint_id: str,
    payload: ComplaintPriorityUpdateRequest,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
    audit_service=Depends(get_audit_service),
):
    if current_user.role == Student.ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students cannot change complaint priority.",
        )

    if current_user.role == Coordinator.ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Coordinators cannot change complaint priority.",
        )

    if (current_user.role or "").lower() == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin cannot access institutional operational data.",
        )

    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )

    if (current_user.role or "").lower() == AppManager.ROLE.lower():
        if not complaint_service.auth_service.is_app_manager_assigned(current_user.user_id, complaint.location_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="App Managers can only change priority for complaints in their assigned locations.",
            )

    if current_user.role == LocationInCharge.ROLE:
        if not complaint_service.auth_service.is_warden_assigned(current_user.user_id, complaint.location_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Wardens can only change priority for complaints in their assigned locations.",
            )

    if current_user.role == Coordinator.ROLE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Coordinators cannot change complaint priority.",
        )

    allowed_priorities = {"Low", "Medium", "High", "Critical"}
    if payload.priority not in allowed_priorities:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid priority. Allowed priorities: {', '.join(allowed_priorities)}",
        )

    if not payload.reason.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reason for priority change is required.",
        )

    old_priority = complaint.priority
    complaint = complaint_service.change_priority(
        complaint_id, current_user, payload.priority, payload.reason
    )

    audit_service.log(
        current_user.user_id,
        "Update Priority",
        complaint_id,
        old_value={"priority": old_priority},
        new_value={
            "priority": payload.priority,
            "reason": payload.reason,
            "changed_by": current_user.user_id,
        },
    )

    return _format_complaint(complaint, complaint_service)


@router.get("/{complaint_id}/comments", response_model=list[CommentResponse])
def get_comments(
    complaint_id: str,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
    comment_service=Depends(get_comment_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    _ensure_visible(complaint, current_user, complaint_service)

    comments = comment_service.get_comments(complaint_id)
    if current_user.role == Student.ROLE:
        comments = [c for c in comments if not c["is_internal"]]
    return comments


@router.post(
    "/{complaint_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    complaint_id: str,
    payload: CommentCreateRequest,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
    comment_service=Depends(get_comment_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    _ensure_visible(complaint, current_user, complaint_service)

    if not payload.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment message cannot be empty.",
        )

    if payload.is_internal:
        if current_user.role not in (
            Coordinator.ROLE,
            LocationInCharge.ROLE,
            AppManager.ROLE,
            Administrator.ROLE,
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Students are not authorized to create internal comments.",
            )

    res = comment_service.add_comment(
        complaint_id,
        current_user.user_id,
        payload.message,
        is_internal=payload.is_internal,
    )
    complaint.add_history(f"Comment Added by {current_user.name}.")
    complaint_service.save_complaint(complaint)
    return res


@router.post("/{complaint_id}/affected", response_model=ComplaintResponse)
def mark_affected(
    complaint_id: str,
    current_user=Depends(require_roles(Student.ROLE, LocationInCharge.ROLE)),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    _ensure_visible(complaint, current_user, complaint_service)

    if current_user.role == Student.ROLE and current_user.location_id and complaint.location_id != current_user.location_id:
        raise HTTPException(
            status_code=403,
            detail="You can only mark yourself as affected for community complaints in your own location block.",
        )

    try:
        complaint = complaint_service.add_affected_student(complaint_id, current_user.user_id)
        _broadcast_complaint_event("affected_changed", complaint, {"affected_count": getattr(complaint, "affected_count", 1)})
        _broadcast_complaint_event("complaint_updated", complaint)
        return _format_complaint(complaint, complaint_service)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{complaint_id}/affected", response_model=ComplaintResponse)
def unmark_affected(
    complaint_id: str,
    current_user=Depends(require_roles(Student.ROLE, LocationInCharge.ROLE)),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found.")
    _ensure_visible(complaint, current_user, complaint_service)

    try:
        complaint = complaint_service.remove_affected_student(complaint_id, current_user.user_id)
        _broadcast_complaint_event("affected_changed", complaint, {"affected_count": getattr(complaint, "affected_count", 0)})
        _broadcast_complaint_event("complaint_updated", complaint)
        return _format_complaint(complaint, complaint_service)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{complaint_id}/escalate", response_model=ComplaintResponse)
def escalate_complaint(
    complaint_id: str,
    payload: EscalateRequest,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    _ensure_visible(complaint, current_user, complaint_service)

    u_role = (current_user.role or "").lower()
    if u_role == "app_manager":
        if not complaint_service.auth_service.is_app_manager_assigned(current_user.user_id, complaint.location_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="App Managers can only escalate complaints in their assigned locations.",
            )

    try:
        complaint = complaint_service.escalate_complaint(
            complaint_id, current_user, payload.reason
        )
        return _format_complaint(complaint, complaint_service)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))


@router.post("/{complaint_id}/feedback", status_code=status.HTTP_201_CREATED)
def submit_complaint_feedback(
    complaint_id: str,
    payload: ComplaintFeedbackRequest,
    current_user=Depends(require_roles(Student.ROLE)),
    complaint_service=Depends(get_complaint_service),
    audit_service=Depends(get_audit_service),
):
    """Students can rate (-1 to 5) and leave a thank you note once per complaint."""
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    # Must be closed
    if complaint.status not in (STATUS_CLOSED, STATUS_AUTO_CLOSED, "Closed", "Closed (Auto Closed)"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback can only be submitted once the complaint is closed.",
        )

    # Must be the student who filed it or an affected student
    is_author = current_user.user_id == complaint.created_by or getattr(current_user, "email", None) == complaint.created_by
    is_affected = complaint_service.is_student_affected(complaint_id, current_user.user_id)
    if not is_author and not is_affected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the student who reported this complaint or an affected student can submit feedback.",
        )

    db = complaint_service.repository
    now_ts = now_string()
    feedback_id = generate_id("FBK")

    with db.get_connection() as conn:
        existing = conn.execute(
            "SELECT feedback_id FROM complaint_feedback WHERE complaint_id = ? AND student_id = ?",
            (complaint_id, current_user.user_id),
        ).fetchone()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already submitted feedback for this complaint.",
            )

        conn.execute(
            """
            INSERT INTO complaint_feedback (feedback_id, complaint_id, student_id, rating, thank_you_note, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (feedback_id, complaint_id, current_user.user_id, payload.rating, payload.thank_you_note or "", now_ts),
        )
        conn.commit()

    # Notify coordinator if thank you note is provided
    if payload.thank_you_note and payload.thank_you_note.strip() and complaint.assigned_to:
        complaint_service.notification_service.notify(
            complaint.assigned_to,
            f"A student left a thank you note: \"{payload.thank_you_note.strip()}\"",
            complaint_id=complaint_id,
            title="Thank You Note Received",
        )

    audit_service.log(
        current_user.user_id,
        "SUBMIT_FEEDBACK",
        complaint_id,
        new_value={"feedback_id": feedback_id, "rating": payload.rating, "has_thank_you": bool(payload.thank_you_note)},
    )

    return {
        "message": "Feedback submitted successfully.",
        "feedback_id": feedback_id,
        "rating": payload.rating,
        "thank_you_note": payload.thank_you_note or "",
    }


@router.get("/{complaint_id}/feedback")
def get_complaint_feedback(
    complaint_id: str,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
):
    """Retrieve feedback entries for a complaint."""
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")
    _ensure_visible(complaint, current_user, complaint_service)

    db = complaint_service.repository
    with db.get_connection() as conn:
        rows = conn.execute(
            """
            SELECT fb.feedback_id, fb.complaint_id, fb.student_id, fb.rating, fb.thank_you_note, fb.created_at, u.name as student_name
            FROM complaint_feedback fb
            LEFT JOIN users u ON u.user_id = fb.student_id
            WHERE fb.complaint_id = ?
            ORDER BY fb.created_at DESC
            """,
            (complaint_id,),
        ).fetchall()

    return [dict(r) for r in rows]


class ComplaintTranslationRequest(BaseModel):
    target_language: Optional[str] = None


@router.post("/{complaint_id}/translate")
def translate_complaint(
    complaint_id: str,
    payload: Optional[ComplaintTranslationRequest] = None,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
    translation_service=Depends(get_translation_service),
):
    """
    Translates complaint description into target_language (default: current_user.language or 'en').
    Enforces strict complaint-level RBAC via _ensure_visible.
    Returns translated text, source language, target language, and cache metadata.
    Does NOT modify the underlying complaint or its audit logs.
    """
    if (current_user.role or "").lower() == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin cannot access institutional operational data.",
        )
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    _ensure_visible(complaint, current_user, complaint_service)

    target_lang = (
        payload.target_language if payload and payload.target_language else None
    ) or getattr(current_user, "language", "en") or "en"
    if target_lang not in ("en", "te", "hi"):
        target_lang = "en"

    complaint_dict = (
        complaint.to_dict()
        if hasattr(complaint, "to_dict")
        else (dict(complaint) if isinstance(complaint, dict) else complaint.__dict__)
    )

    result = translation_service.translate_complaint_description(
        complaint_dict, target_lang
    )
    return {
        "complaint_id": complaint_id,
        "original_description": complaint.description,
        **result,
    }

