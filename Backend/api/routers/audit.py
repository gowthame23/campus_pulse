from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from api.dependencies import get_audit_service
from api.security import require_roles
from models.administrator import Administrator
from models.app_manager import AppManager

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/dashboard")
def get_audit_dashboard_summary(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    audit_service=Depends(get_audit_service),
):
    return audit_service.get_dashboard_metrics()


@router.get("")
def list_audit_logs(
    q: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    performed_by: Optional[str] = Query(None),
    role: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    audit_service=Depends(get_audit_service),
):
    from utils.pagination import paginate

    logs = audit_service.list_logs(
        user=current_user,
        q=q,
        module=module,
        action=action,
        entity_type=entity_type,
        performed_by=performed_by,
        role=role,
        status=status,
        date_from=date_from,
        date_to=date_to,
        ip_address=ip_address,
    )
    return paginate(logs, page=page, limit=limit)


@router.get("/timeline/{entity_type}/{entity_id}")
@router.get("/entity/{entity_type}/{entity_id}")
def get_entity_timeline(
    entity_type: str,
    entity_id: str,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    audit_service=Depends(get_audit_service),
):
    """Returns chronological entity timeline events for Administrator activity timeline."""
    return audit_service.get_entity_timeline(entity_type, entity_id)


@router.get("/export")
def export_audit_logs(
    format: str = Query("csv"),
    module: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    audit_service=Depends(get_audit_service),
):
    filters = {
        "module": module,
        "action": action,
        "entity_type": entity_type,
        "date_from": date_from,
        "date_to": date_to,
    }
    content = audit_service.export_logs(fmt=format, filters=filters, user=current_user)
    filename = f"audit_logs_export.{format}"
    media_type = (
        "text/csv"
        if format == "csv"
        else "application/json" if format == "json" else "application/pdf"
    )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/archive", status_code=status.HTTP_200_OK)
def archive_audit_logs(
    retention_days: int = Query(180, ge=30),
    current_user=Depends(require_roles(Administrator.ROLE)),
    audit_service=Depends(get_audit_service),
):
    """Archives logs older than retention threshold (Admin only)."""
    return audit_service.archive_logs(
        retention_days=retention_days, performer_id=current_user.user_id
    )


@router.get("/{audit_id}")
def get_audit_log(
    audit_id: str,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    audit_service=Depends(get_audit_service),
):
    log = audit_service.get_log(audit_id)
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Audit log record not found."
        )
    return log
