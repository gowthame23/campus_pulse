from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.dependencies import get_report_service
from api.security import block_super_admin, get_current_user, require_roles
from models.administrator import Administrator
from models.app_manager import AppManager
from models.coordinator import Coordinator
from models.location_in_charge import LocationInCharge

router = APIRouter(
    prefix="/reports", tags=["reports"], dependencies=[Depends(block_super_admin)]
)


# ==========================================
# SCHEMAS
# ==========================================
class TemplateCreateRequest(BaseModel):
    template_name: str
    report_type: str
    description: Optional[str] = ""


class ScheduleCreateRequest(BaseModel):
    template_id: str
    frequency: str = "Weekly"
    day_of_week: Optional[str] = None
    email_recipients: Optional[str] = None


class ReportGenerateRequest(BaseModel):
    report_name: str
    report_type: str = "Complaint"
    file_format: str = "CSV"
    filters: Optional[Dict[str, Any]] = None


# ==========================================
# 1. REPORT TEMPLATES & SCHEDULES API
# ==========================================
@router.get("/templates")
def list_templates(
    report_type: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    report_service=Depends(get_report_service),
):
    return report_service.list_templates(report_type=report_type)


@router.post("/templates", status_code=status.HTTP_201_CREATED)
def create_template(
    payload: TemplateCreateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    report_service=Depends(get_report_service),
):
    return report_service.create_template(
        template_name=payload.template_name,
        report_type=payload.report_type,
        description=payload.description,
    )


@router.get("/schedules")
def list_schedules(
    current_user=Depends(
        require_roles(
            Administrator.ROLE, AppManager.ROLE, Coordinator.ROLE, LocationInCharge.ROLE
        )
    ),
    report_service=Depends(get_report_service),
):
    return report_service.list_schedules()


@router.post("/schedules", status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: ScheduleCreateRequest,
    current_user=Depends(
        require_roles(
            Administrator.ROLE, AppManager.ROLE, Coordinator.ROLE, LocationInCharge.ROLE
        )
    ),
    report_service=Depends(get_report_service),
):
    return report_service.create_schedule(
        template_id=payload.template_id,
        created_by=current_user.user_id,
        frequency=payload.frequency,
        day_of_week=payload.day_of_week,
        email_recipients=payload.email_recipients,
    )


# ==========================================
# 2. REPORT GENERATION & DOWNLOADS API
# ==========================================
@router.post("", status_code=status.HTTP_201_CREATED)
def generate_report(
    payload: ReportGenerateRequest,
    current_user=Depends(
        require_roles(
            Administrator.ROLE, AppManager.ROLE, Coordinator.ROLE, LocationInCharge.ROLE
        )
    ),
    report_service=Depends(get_report_service),
):
    try:
        return report_service.generate_report(
            report_name=payload.report_name,
            report_type=payload.report_type,
            generated_by=current_user.user_id,
            file_format=payload.file_format,
            filters=payload.filters,
            user=current_user,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/summary")
def get_report_summary(
    current_user=Depends(
        require_roles(
            Administrator.ROLE, AppManager.ROLE, Coordinator.ROLE, LocationInCharge.ROLE
        )
    ),
    report_service=Depends(get_report_service),
):
    return report_service.get_summary()


@router.get("")
def list_reports(
    report_type: Optional[str] = Query(None),
    my_reports: bool = Query(False),
    q: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    report_service=Depends(get_report_service),
):
    gen_by = (
        current_user.user_id if (my_reports or current_user.role == "student") else None
    )
    return report_service.list_reports(
        report_type=report_type, generated_by=gen_by, q=q
    )


@router.get("/complaints")
def get_complaints_report(
    location_id: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    status_filter: Optional[str] = Query(None, alias="status"),
    priority: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    report_service=Depends(get_report_service),
):
    try:
        return report_service.get_complaint_report(
            user_role=current_user.role,
            user_id=current_user.user_id,
            location_id=location_id,
            department_id=department_id,
            from_date=from_date,
            to_date=to_date,
            status=status_filter,
            priority=priority,
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=403, detail=str(p_err))


@router.get("/locations")
@router.get("/by-location")
def get_locations_report(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    current_user=Depends(get_current_user),
    report_service=Depends(get_report_service),
):
    try:
        return report_service.get_location_report(
            user_role=current_user.role,
            user_id=current_user.user_id,
            from_date=from_date,
            to_date=to_date,
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=403, detail=str(p_err))


@router.get("/departments")
@router.get("/by-department")
def get_departments_report(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    current_user=Depends(get_current_user),
    report_service=Depends(get_report_service),
):
    try:
        return report_service.get_department_report(
            user_role=current_user.role,
            user_id=current_user.user_id,
            from_date=from_date,
            to_date=to_date,
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=403, detail=str(p_err))


@router.get("/performance")
@router.get("/coordinators")
def get_coordinators_performance_report(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    current_user=Depends(get_current_user),
    report_service=Depends(get_report_service),
):
    try:
        return report_service.get_coordinator_performance_report(
            user_role=current_user.role,
            user_id=current_user.user_id,
            from_date=from_date,
            to_date=to_date,
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=403, detail=str(p_err))


@router.get("/lost-found")
def get_lost_found_report(
    location_id: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    current_user=Depends(get_current_user),
    report_service=Depends(get_report_service),
):
    try:
        return report_service.get_lost_found_report(
            user_role=current_user.role,
            user_id=current_user.user_id,
            from_date=from_date,
            to_date=to_date,
            location_id=location_id,
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=403, detail=str(p_err))


@router.get("/users")
def get_users_report(
    current_user=Depends(get_current_user),
    report_service=Depends(get_report_service),
):
    try:
        return report_service.get_user_report(
            user_role=current_user.role,
            user_id=current_user.user_id,
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=403, detail=str(p_err))


@router.get("/{report_id}")
def get_report(
    report_id: str,
    current_user=Depends(get_current_user),
    report_service=Depends(get_report_service),
):
    rpt = report_service.get_report(report_id)
    if not rpt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found."
        )
    staff_roles = (
        Administrator.ROLE.lower(),
        AppManager.ROLE.lower(),
        Coordinator.ROLE.lower(),
        LocationInCharge.ROLE.lower(),
    )
    if current_user.role.lower() not in staff_roles and rpt.get("generated_by") != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view this report.",
        )
    return rpt


@router.get("/{report_id}/download")
def download_report(
    report_id: str,
    current_user=Depends(get_current_user),
    report_service=Depends(get_report_service),
):
    rpt = report_service.get_report(report_id)
    if not rpt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Report not found."
        )
    staff_roles = (
        Administrator.ROLE.lower(),
        AppManager.ROLE.lower(),
        Coordinator.ROLE.lower(),
        LocationInCharge.ROLE.lower(),
    )
    if current_user.role.lower() not in staff_roles and rpt.get("generated_by") != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to download this report.",
        )
    try:
        filepath, filename = report_service.download_report(
            report_id, downloaded_by=current_user.user_id
        )
        return FileResponse(
            path=filepath, filename=filename, media_type="application/octet-stream"
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
