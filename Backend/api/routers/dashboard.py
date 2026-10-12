from fastapi import APIRouter, Depends

from api.dependencies import get_dashboard_service
from api.security import get_current_user, require_roles
from models.administrator import Administrator
from models.app_manager import AppManager
from models.coordinator import Coordinator
from models.location_in_charge import LocationInCharge
from models.student import Student

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def get_user_dashboard(
    current_user=Depends(get_current_user),
    dashboard_service=Depends(get_dashboard_service),
):
    return dashboard_service.get_dashboard(
        user_id=current_user.user_id,
        role=current_user.role,
    )


@router.get("/student")
def get_student_dashboard(
    current_user=Depends(
        require_roles(Student.ROLE, Administrator.ROLE, AppManager.ROLE)
    ),
    dashboard_service=Depends(get_dashboard_service),
):
    return dashboard_service.get_student_dashboard(user_id=current_user.user_id)


@router.get("/coordinator")
def get_coordinator_dashboard(
    current_user=Depends(
        require_roles(
            Coordinator.ROLE, LocationInCharge.ROLE, Administrator.ROLE
        )
    ),
    dashboard_service=Depends(get_dashboard_service),
):
    return dashboard_service.get_coordinator_dashboard(user_id=current_user.user_id)


@router.get("/warden")
def get_warden_dashboard(
    current_user=Depends(
        require_roles("warden", LocationInCharge.ROLE, Administrator.ROLE)
    ),
    dashboard_service=Depends(get_dashboard_service),
):
    return dashboard_service.get_warden_dashboard(user_id=current_user.user_id)


@router.get("/supervisor")
def get_supervisor_dashboard(
    current_user=Depends(
        require_roles("supervisor", AppManager.ROLE, Administrator.ROLE)
    ),
    dashboard_service=Depends(get_dashboard_service),
):
    return dashboard_service.get_supervisor_dashboard(user_id=current_user.user_id)


@router.get("/admin")
def get_admin_dashboard(
    current_user=Depends(require_roles(Administrator.ROLE)),
    dashboard_service=Depends(get_dashboard_service),
):
    return dashboard_service.get_admin_dashboard(user_id=current_user.user_id)


from datetime import datetime
from fastapi import HTTPException, status
from api.dependencies import get_complaint_service, get_config_service, get_location_service


@router.get("/health-map")
def get_campus_health_map(
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
    location_service=Depends(get_location_service),
    config_service=Depends(get_config_service),
):
    """
    Campus Health Map grouping active complaints by building/location.
    Red: overdue complaints > 0 or open >= 5.
    Yellow: near-deadline > 0 or open >= 2.
    Green: healthy.
    Flags recurring pattern alerts if >= threshold complaints of same category in 21 days.
    """
    user_role = (current_user.role or "").lower()
    if user_role == Student.ROLE.lower():
        is_enabled = config_service.get_setting("show_health_map_to_students")
        if str(is_enabled).strip().lower() not in ("true", "1", "yes"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Campus health map view is not currently enabled for students.",
            )

    threshold_str = config_service.get_setting("health_map_pattern_threshold")
    try:
        pattern_threshold = int(threshold_str)
    except (ValueError, TypeError):
        pattern_threshold = 5

    locations = location_service.list_locations(include_archived=False)
    db = complaint_service.repository
    now_ts = datetime.now()

    with db.get_connection() as conn:
        active_rows = conn.execute("""
            SELECT complaint_id, location_id, category, sla_deadline, status, created_at
            FROM complaints
            WHERE status NOT IN ('Closed', 'Closed (Auto Closed)', 'Rejected', 'Cancelled')
              AND archived = 0
        """).fetchall()

        pattern_rows = conn.execute("""
            SELECT location_id, category, COUNT(*) as cat_count
            FROM complaints
            WHERE created_at >= datetime('now', '-21 days')
            GROUP BY location_id, category
            HAVING COUNT(*) >= ?
        """, (pattern_threshold,)).fetchall()

    pattern_alerts = {}
    for pr in pattern_rows:
        loc_id = pr["location_id"]
        if loc_id not in pattern_alerts:
            pattern_alerts[loc_id] = []
        pattern_alerts[loc_id].append({
            "category": pr["category"],
            "count": pr["cat_count"],
            "threshold": pattern_threshold,
            "message": f"Recurring problem pattern: {pr['cat_count']} complaints in {pr['category']} over the last 21 days.",
        })

    loc_complaints = {}
    for r in active_rows:
        loc_id = r["location_id"]
        if loc_id not in loc_complaints:
            loc_complaints[loc_id] = []
        loc_complaints[loc_id].append(r)

    cards = []
    for loc in locations:
        loc_id = loc.location_id
        items = loc_complaints.get(loc_id, [])
        open_count = len(items)

        overdue_count = 0
        near_deadline_count = 0
        category_counts = {}

        for item in items:
            cat = item["category"] or "General"
            category_counts[cat] = category_counts.get(cat, 0) + 1

            is_od = False
            if item["sla_deadline"]:
                try:
                    dl = datetime.fromisoformat(item["sla_deadline"].replace("Z", ""))
                    if dl < now_ts:
                        is_od = True
                    elif (dl - now_ts).total_seconds() <= 12 * 3600:
                        near_deadline_count += 1
                except Exception:
                    pass
            if is_od:
                overdue_count += 1

        sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        top_categories = [{"category": c[0], "count": c[1]} for c in sorted_cats]

        if overdue_count > 0 or open_count >= 5:
            color = "red"
        elif near_deadline_count > 0 or open_count >= 2:
            color = "yellow"
        else:
            color = "green"

        cards.append({
            "location_id": loc_id,
            "location_name": loc.name,
            "location_type": loc.location_type,
            "open_count": open_count,
            "overdue_count": overdue_count,
            "near_deadline_count": near_deadline_count,
            "top_categories": top_categories,
            "color": color,
            "pattern_alerts": pattern_alerts.get(loc_id, []),
        })

    red_count = sum(1 for c in cards if c["color"] == "red")
    yellow_count = sum(1 for c in cards if c["color"] == "yellow")
    green_count = sum(1 for c in cards if c["color"] == "green")

    return {
        "summary": {
            "total_locations": len(cards),
            "red_count": red_count,
            "yellow_count": yellow_count,
            "green_count": green_count,
            "overall_status": "critical" if red_count > 0 else ("warning" if yellow_count > 0 else "healthy"),
        },
        "locations": cards,
    }


