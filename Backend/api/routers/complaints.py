from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from core.constants import (
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
)
from api.schemas import (
    AnalyticsResponse,
    CommentCreateRequest,
    CommentResponse,
    ComplaintAssignRequest,
    ComplaintCreateRequest,
    ComplaintDeleteRequestPayload,
    ComplaintPriorityUpdateRequest,
    ComplaintReopenRequest,
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
        loc_cache = {}

    try:
        all_depts = complaint_service.auth_service.list_departments()
        dept_cache = {d.department_id: d for d in all_depts}
    except Exception:
        dept_cache = {}

    affected_cache = complaint_service.get_affected_students_counts()
    return loc_cache, dept_cache, affected_cache


def _format_complaint(complaint, complaint_service, loc_cache=None, dept_cache=None, affected_cache=None):
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
            in_charge = complaint_service.auth_service.get_user(loc.in_charge_id)
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
            coord = complaint_service.auth_service.get_user(dept.coordinator_id)
            if coord:
                data["assigned_coordinator_name"] = coord.name

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
        for c in all_complaints:
            if c.created_by == current_user.user_id:
                visible.append(c)
            elif (
                c.visibility_type == "Community"
                and c.location_id == current_user.location_id
            ):
                visible.append(c)

    elif u_role == "employee":
        acting_team_ids = set()
        if hasattr(complaint_service, "team_service"):
            for t in complaint_service.team_service.list_teams(active_only=True):
                acting = complaint_service.team_service.get_acting_coordinator(t)
                if acting and acting.user_id == current_user.user_id:
                    acting_team_ids.add(t["team_id"])
        for c in all_complaints:
            if (
                c.assigned_to == current_user.user_id
                or c.created_by == current_user.user_id
                or (getattr(c, "team_id", None) and c.team_id in acting_team_ids)
            ):
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
        assigned_loc_ids = {l.location_id for l in all_locs if l.in_charge_id == current_user.user_id}
        for c in all_complaints:
            if c.location_id in assigned_loc_ids:
                visible.append(c)
            elif c.created_by == current_user.user_id or c.assigned_to == current_user.user_id:
                visible.append(c)

    return visible


def _ensure_visible(complaint, current_user, complaint_service):
    visible_ids = {
        item.complaint_id
        for item in _visible_complaints(
            current_user, complaint_service, include_archived=True
        )
    }
    if complaint.complaint_id not in visible_ids:
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

    loc_cache, dept_cache, affected_cache = _build_format_caches(complaint_service)
    return [_format_complaint(complaint, complaint_service, loc_cache, dept_cache, affected_cache) for complaint in complaints]


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

    loc_cache, dept_cache, affected_cache = _build_format_caches(complaint_service)
    formatted_items = [_format_complaint(c, complaint_service, loc_cache, dept_cache, affected_cache) for c in complaints]
    return paginate(formatted_items, page=page, limit=limit)


@router.get("/workload")
def get_workload_summary(
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
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

    app_managers = []
    wardens = []
    coordinators = []

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

        staff_data = {
            "user_id": user.user_id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "location_id": getattr(user, "location_id", None),
            "location_name": loc_map.get(getattr(user, "location_id", None), getattr(user, "location_id", None) or ""),
            "department_id": getattr(user, "department_id", None),
            "department_name": dept_map.get(getattr(user, "department_id", None), getattr(user, "department_id", None) or ""),
            "assigned": staff_assigned,
            "left": staff_left,
            "resolved": staff_resolved,
        }

        if u_r == "app_manager":
            app_managers.append(staff_data)
        elif u_r == "location_in_charge":
            wardens.append(staff_data)
        elif u_r == "coordinator":
            coordinators.append(staff_data)

    loc_cache, dept_cache, affected_cache = _build_format_caches(complaint_service)
    formatted_unassigned = [
        _format_complaint(c, complaint_service, loc_cache, dept_cache, affected_cache)
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
        "app_managers": app_managers,
        "wardens": wardens,
        "coordinators": coordinators,
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

    loc_cache, dept_cache, affected_cache = _build_format_caches(complaint_service)
    formatted_items = [
        _format_complaint(c, complaint_service, loc_cache, dept_cache, affected_cache)
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
        require_roles(Coordinator.ROLE, Administrator.ROLE)
    ),
    complaint_service=Depends(get_complaint_service),
):
    complaint = complaint_service.get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found."
        )
    _ensure_visible(complaint, current_user, complaint_service)

    # Coordinators can only accept complaints for their assigned location + department pairs
    if (current_user.role or "").lower() == "coordinator":
        if not complaint_service.auth_service.is_coordinator_assigned(
            current_user.user_id, complaint.location_id, complaint.department_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not mapped to handle complaints for this location and department.",
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
        require_roles(Coordinator.ROLE, Administrator.ROLE)
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
        if u_role == "coordinator" and complaint.team_id and hasattr(complaint_service, "team_service"):
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
        Complaint.IN_PROGRESS,
        Complaint.ASSIGNED,
        "In Progress",
        "Assigned",
        "Reopened",
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Complaint must be In Progress or Assigned before it can be resolved.",
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
        complaint.description = payload.description.strip()

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

    # 3. Student -> Direct Soft Delete if status is Submitted and student is creator
    elif u_role == "student":
        allowed_creators = {current_user.user_id}
        if getattr(current_user, "email", None):
            allowed_creators.add(current_user.email)
        if complaint.created_by not in allowed_creators:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own complaints.",
            )
        if complaint.status != Complaint.SUBMITTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Complaints can only be deleted while in Submitted status.",
            )
        old_value = complaint.to_dict()
        complaint.archived = True
        complaint.is_deleted = True
        from utils.helper import now_string
        complaint.deleted_at = now_string()
        complaint.deleted_by = current_user.user_id
        complaint.add_history(f"Soft deleted by student {current_user.name}.")
        complaint_service.save_complaint(complaint)
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

