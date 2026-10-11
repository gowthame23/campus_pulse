from fastapi import APIRouter, Depends

from api.dependencies import (
    get_announcement_service,
    get_complaint_service,
    get_department_service,
    get_lost_found_service,
    get_notification_service,
)
from api.security import require_roles
from models.administrator import Administrator
from models.app_manager import AppManager

router = APIRouter(prefix="/supervisor", tags=["supervisor"])


@router.get("/dashboard")
def supervisor_dashboard(
    current_user=Depends(require_roles(AppManager.ROLE, Administrator.ROLE)),
    complaint_service=Depends(get_complaint_service),
    department_service=Depends(get_department_service),
    announcement_service=Depends(get_announcement_service),
    notification_service=Depends(get_notification_service),
    lost_found_service=Depends(get_lost_found_service),
):
    assigned = getattr(current_user, "assigned_locations", []) or []

    complaints = complaint_service.list_all()
    # filter by assigned locations
    if assigned:
        complaints = [
            c
            for c in complaints
            if c.location_id in assigned
            or (c.location_id or "").lower() in [a.lower() for a in assigned]
        ]

    # Complaint summary
    summary = {
        "pending": sum(1 for c in complaints if c.status == "Pending"),
        "accepted": sum(1 for c in complaints if c.status == "Accepted"),
        "in_progress": sum(1 for c in complaints if c.status == "In Progress"),
        "waiting_verification": sum(
            1 for c in complaints if c.status == "Waiting for Verification"
        ),
        "overdue": sum(
            1
            for c in complaints
            if getattr(c, "is_overdue", False) or c.status == "Overdue"
        ),
    }

    # Department performance (simple aggregation)
    departments = [d.to_dict() for d in department_service.list_departments()]
    dept_map = {
        d["department_id"] if d.get("department_id") else d.get("name"): {
            "name": d.get("name", ""),
            "total": 0,
            "remaining": 0,
        }
        for d in departments
    }
    for c in complaints:
        key = c.department_id or "Unknown"
        if key not in dept_map:
            dept_map[key] = {"name": key, "total": 0, "remaining": 0}
        dept_map[key]["total"] += 1
        if c.status not in ("Closed", "Closed (Auto Closed)"):
            dept_map[key]["remaining"] += 1

    # High priority complaints
    high_priority = [
        c.to_dict()
        for c in complaints
        if c.priority in ("High", "Critical")
        or c.status == "Reopened"
        or getattr(c, "is_overdue", False)
    ]

    # Lost & Found summary
    try:
        lf = lost_found_service.list()
    except Exception:
        lf = []
    lost_count = sum(1 for i in lf if i.get("item_type") == "Lost")
    found_count = sum(1 for i in lf if i.get("item_type") == "Found")
    disputed = sum(1 for i in lf if i.get("status") == "Disputed")

    # Recent announcements and notifications (limited)
    try:
        anns = announcement_service.list()[:5]
    except Exception:
        anns = []
    try:
        notifs = notification_service.list_for_user(
            current_user.user_id, current_user.role
        )[:10]
    except Exception:
        notifs = []

    return {
        "assigned_locations": assigned,
        "complaint_summary": summary,
        "department_performance": list(dept_map.values()),
        "high_priority_complaints": high_priority[:10],
        "lost_found": {"lost": lost_count, "found": found_count, "disputed": disputed},
        "recent_announcements": anns,
        "recent_notifications": notifs,
    }
