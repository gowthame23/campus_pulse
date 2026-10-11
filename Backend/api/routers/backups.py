from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.dependencies import get_backup_service
from api.security import require_roles
from models.administrator import Administrator
from models.app_manager import AppManager

router = APIRouter(prefix="/backups", tags=["backups"])


# ==========================================
# SCHEMAS
# ==========================================
class BackupCreateRequest(BaseModel):
    backup_name: str
    backup_type: str = "Full"
    remarks: Optional[str] = ""


# ==========================================
# 1. BACKUPS & DOWNLOADS API
# ==========================================
@router.get("/summary")
def get_backup_summary(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    backup_service=Depends(get_backup_service),
):
    return backup_service.get_summary()


@router.get("")
def list_backups(
    backup_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    backup_service=Depends(get_backup_service),
):
    return backup_service.list_backups(
        backup_type=backup_type, status_filter=status_filter
    )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_backup(
    payload: BackupCreateRequest,
    current_user=Depends(require_roles(Administrator.ROLE)),
    backup_service=Depends(get_backup_service),
):
    try:
        return backup_service.create_backup(
            backup_name=payload.backup_name,
            backup_type=payload.backup_type,
            created_by=current_user.user_id,
            remarks=payload.remarks,
        )
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/restore-history")
def list_restore_history(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    backup_service=Depends(get_backup_service),
):
    return backup_service.list_restore_history()


@router.get("/schedules")
def list_schedules(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    backup_service=Depends(get_backup_service),
):
    return backup_service.list_schedules()


@router.get("/{backup_id}")
def get_backup(
    backup_id: str,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    backup_service=Depends(get_backup_service),
):
    bkp = backup_service.get_backup(backup_id)
    if not bkp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Backup archive not found."
        )
    return bkp


@router.get("/{backup_id}/download")
def download_backup(
    backup_id: str,
    current_user=Depends(require_roles(Administrator.ROLE)),
    backup_service=Depends(get_backup_service),
):
    try:
        bkp, filepath = backup_service.get_backup_file_path(backup_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))
    return FileResponse(
        path=filepath,
        filename=bkp["file_name"],
        media_type="application/octet-stream",
    )


# ==========================================
# 2. VERIFICATION & RESTORE ENGINE API
# ==========================================
@router.post("/{backup_id}/verify")
def verify_backup(
    backup_id: str,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    backup_service=Depends(get_backup_service),
):
    try:
        return backup_service.verify_backup(backup_id)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/{backup_id}/restore", status_code=status.HTTP_202_ACCEPTED)
def restore_backup(
    backup_id: str,
    current_user=Depends(require_roles(Administrator.ROLE)),
    backup_service=Depends(get_backup_service),
):
    try:
        return backup_service.restore_backup(
            backup_id, restored_by=current_user.user_id
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
