from typing import Optional

from fastapi import APIRouter, Depends, Query, Response

from api.dependencies import get_analytics_service
from api.security import block_super_admin, get_current_user, require_roles
from models.administrator import Administrator
from models.app_manager import AppManager

router = APIRouter(
    prefix="/analytics", tags=["analytics"], dependencies=[Depends(block_super_admin)]
)


@router.get("/dashboard")
def get_dashboard_analytics(
    current_user=Depends(get_current_user),
    analytics_service=Depends(get_analytics_service),
):
    return analytics_service.get_dashboard_summary(current_user)


@router.get("/complaints")
def get_complaint_analytics(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    location_id: Optional[str] = Query(None),
    building_id: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    coordinator_id: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    complaint_type: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    analytics_service=Depends(get_analytics_service),
):
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "department_id": department_id,
        "location_id": location_id,
        "building_id": building_id,
        "category_id": category_id,
        "coordinator_id": coordinator_id,
        "priority": priority,
        "status": status,
        "complaint_type": complaint_type,
    }
    return analytics_service.get_complaint_analytics(filters, current_user)


@router.get("/sla")
def get_sla_analytics(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    analytics_service=Depends(get_analytics_service),
):
    filters = {
        "date_from": date_from,
        "date_to": date_to,
        "department_id": department_id,
    }
    return analytics_service.get_sla_analytics(filters, current_user)


@router.get("/departments")
def get_department_analytics(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    analytics_service=Depends(get_analytics_service),
):
    filters = {"date_from": date_from, "date_to": date_to}
    return analytics_service.get_department_analytics(filters, current_user)


@router.get("/coordinators")
def get_coordinator_analytics(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    analytics_service=Depends(get_analytics_service),
):
    filters = {"date_from": date_from, "date_to": date_to}
    return analytics_service.get_coordinator_analytics(filters, current_user)


@router.get("/hostels")
def get_hostel_analytics(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    analytics_service=Depends(get_analytics_service),
):
    filters = {"date_from": date_from, "date_to": date_to}
    return analytics_service.get_hostel_analytics(filters, current_user)


@router.get("/users")
def get_user_analytics(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    analytics_service=Depends(get_analytics_service),
):
    return analytics_service.get_user_analytics({}, current_user)


@router.get("/notifications")
def get_notification_analytics(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    analytics_service=Depends(get_analytics_service),
):
    return analytics_service.get_notification_analytics({}, current_user)


@router.get("/export")
def export_analytics_report(
    report_type: str = Query("complaints"),
    format: str = Query("csv"),
    department_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    analytics_service=Depends(get_analytics_service),
):
    filters = {
        "department_id": department_id,
        "date_from": date_from,
        "date_to": date_to,
    }
    content = analytics_service.export_report(
        report_type, fmt=format, filters=filters, user=current_user
    )
    filename = f"{report_type}_report.{format}"
    media_type = "text/csv" if format == "csv" else "application/pdf"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
