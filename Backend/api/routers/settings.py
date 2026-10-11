from collections import defaultdict
from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from api.dependencies import (
    get_audit_service,
    get_auth_service,
    get_backup_service,
    get_complaint_service,
    get_config_service,
)
from api.schemas import BulkSettingsUpdateRequest, SettingItemUpdateRequest
from api.security import require_roles
from models.administrator import Administrator

router = APIRouter(prefix="/settings", tags=["settings"])


class ResolveDuplicateRequest(BaseModel):
    type: str  # "department" or "location"
    keep_id: str
    delete_ids: List[str]


# ==========================================
# SYSTEM CONFIGURATION ENDPOINTS (ADMIN ONLY)
# ==========================================
@router.get("")
def get_all_settings(
    current_user=Depends(require_roles(Administrator.ROLE)),
    config_service=Depends(get_config_service),
):
    """Returns system settings grouped by category."""
    return config_service.get_all_grouped()


@router.get("/system-health")
def get_system_health(
    current_user=Depends(require_roles(Administrator.ROLE)),
    auth_service=Depends(get_auth_service),
    complaint_service=Depends(get_complaint_service),
):
    import os

    db_file = os.environ.get("DATABASE_PATH", "storage/campus_pulse.db")
    db_size = os.path.getsize(db_file) if os.path.exists(db_file) else 0
    total_users = len(auth_service.list_users())
    return {
        "status": "Healthy",
        "database_status": "Connected",
        "database_size_bytes": db_size,
        "database_size_mb": round(db_size / (1024 * 1024), 2),
        "websocket_status": "Active",
        "total_users": total_users,
        "system_version": "1.0.0",
    }


@router.get("/about")
def get_about_info(
    current_user=Depends(require_roles(Administrator.ROLE)),
):
    return {
        "application_name": "Campus Pulse",
        "version": "1.0.0",
        "release_date": "2026-08-06",
        "database_version": "SQLite 3",
        "current_build_number": "20260806.1",
        "developer_contact": "gowthamejjurothu@gmail.com",
    }


@router.post("/backup")
@router.get("/backup")
def export_backup(
    current_user=Depends(require_roles(Administrator.ROLE)),
    backup_service=Depends(get_backup_service),
):
    try:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:20]
        bkp = backup_service.create_backup(
            backup_name=f"Settings_Export_{timestamp_str}",
            backup_type="Full",
            created_by=current_user.user_id,
            remarks="Settings backup created via admin export",
        )
        return {
            "version": "1.0.0",
            "exported_by": current_user.user_id,
            "backup_id": bkp["backup_id"],
            "file_name": bkp["file_name"],
            "file_size": bkp["file_size"],
            "created_at": bkp["created_at"],
            "status": bkp["status"],
            "data": {
                "backup_id": bkp["backup_id"],
                "file_name": bkp["file_name"],
                "file_size": bkp["file_size"],
                "created_at": bkp["created_at"],
                "status": bkp["status"],
            },
            "message": "Backup generated and archived in secure backup service.",
        }
    except Exception as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/restore")
def restore_backup(
    payload: dict,
    current_user=Depends(require_roles(Administrator.ROLE)),
    backup_service=Depends(get_backup_service),
):
    backup_id = payload.get("backup_id")
    if not backup_id:
        backups = backup_service.list_backups(status_filter="Completed")
        if backups:
            backup_id = backups[0]["backup_id"]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid backup archive found for restore operation.",
            )

    try:
        res = backup_service.restore_backup(backup_id, restored_by=current_user.user_id)
        return {
            "message": "Database backup restored successfully.",
            "restore_id": res.get("restore_id"),
            "backup_id": backup_id,
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/{category}")
def get_category_settings(
    category: str,
    current_user=Depends(require_roles(Administrator.ROLE)),
    config_service=Depends(get_config_service),
):
    """Returns system settings for a specific category (e.g. Security, Complaint)."""
    return config_service.list_settings_by_category(category)


@router.get("/key/{setting_key}")
def get_single_setting(
    setting_key: str,
    current_user=Depends(require_roles(Administrator.ROLE)),
    config_service=Depends(get_config_service),
):
    """Returns a single system setting by key."""
    setting = config_service.get_setting_dict(setting_key)
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{setting_key}' not found.",
        )
    return setting


@router.put("/key/{setting_key}")
def update_single_setting(
    setting_key: str,
    payload: SettingItemUpdateRequest,
    request: Request,
    current_user=Depends(require_roles(Administrator.ROLE)),
    config_service=Depends(get_config_service),
    audit_service=Depends(get_audit_service),
):
    """Updates a single setting after validation and records an immutable audit log."""
    try:
        client_ip = request.client.host if request.client else "unknown"
        updated = config_service.update_setting(
            key=setting_key,
            new_val=payload.setting_value,
            performer_id=current_user.user_id,
            ip_address=client_ip,
            reason=payload.reason,
        )
        audit_service.log(
            current_user.user_id,
            "Update System Setting",
            setting_key,
            old_value=None,
            new_value=updated,
        )
        return updated
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.put("")
def bulk_update_settings(
    payload: BulkSettingsUpdateRequest,
    request: Request,
    current_user=Depends(require_roles(Administrator.ROLE)),
    config_service=Depends(get_config_service),
    auth_service=Depends(get_auth_service),
    audit_service=Depends(get_audit_service),
):
    """Bulk update multiple settings transactionally."""
    try:
        # Sensitive re-authentication password check if provided
        if payload.admin_password:
            auth_service.authenticate(current_user.email, payload.admin_password)

        client_ip = request.client.host if request.client else "unknown"
        items = [
            {"setting_key": item.setting_key, "setting_value": item.setting_value}
            for item in payload.settings
        ]

        updated_grouped = config_service.bulk_update(
            settings_list=items,
            performer_id=current_user.user_id,
            ip_address=client_ip,
            reason=payload.reason,
        )
        audit_service.log(
            current_user.user_id,
            "Bulk Update System Settings",
            "System",
            old_value=None,
            new_value={"count": len(items)},
        )
        return updated_grouped
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/{category}/reset")
def reset_category_settings(
    category: str,
    current_user=Depends(require_roles(Administrator.ROLE)),
    config_service=Depends(get_config_service),
    audit_service=Depends(get_audit_service),
):
    """Restores default values for a setting category."""
    try:
        res = config_service.reset_category(category, performer_id=current_user.user_id)
        audit_service.log(
            current_user.user_id,
            f"Reset Category Settings ({category})",
            category,
            old_value=None,
            new_value=res,
        )
        return res
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.post("/reset-all")
def reset_all_settings(
    payload: Dict[str, str] = {},
    current_user=Depends(require_roles(Administrator.ROLE)),
    config_service=Depends(get_config_service),
    auth_service=Depends(get_auth_service),
    audit_service=Depends(get_audit_service),
):
    """Restores all system settings to their default values."""
    admin_password = payload.get("admin_password")
    if admin_password:
        auth_service.authenticate(current_user.email, admin_password)

    try:
        res = config_service.reset_all(performer_id=current_user.user_id)
        audit_service.log(
            current_user.user_id,
            "Reset All System Settings",
            "System",
            old_value=None,
            new_value=res,
        )
        return res
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


# ==========================================
# DUPLICATES & BACKUP RESTORE (EXISTING)
# ==========================================
@router.get("/duplicates")
def get_duplicates(
    current_user=Depends(require_roles(Administrator.ROLE)),
    auth_service=Depends(get_auth_service),
    complaint_service=Depends(get_complaint_service),
):
    users = auth_service.list_users()
    complaints = complaint_service.list_all(include_archived=True)
    user_by_id = {u.user_id: u for u in users}

    complaint_dept_counts = defaultdict(int)
    complaint_loc_counts = defaultdict(int)
    for c in complaints:
        if c.department_id:
            complaint_dept_counts[c.department_id] += 1
        if c.location_id:
            complaint_loc_counts[c.location_id] += 1

    user_dept_counts = defaultdict(int)
    user_loc_counts = defaultdict(int)
    for u in users:
        if u.department_id:
            user_dept_counts[u.department_id] += 1
        if u.location_id:
            user_loc_counts[u.location_id] += 1

    departments = auth_service.list_departments()
    dept_map = defaultdict(list)
    for dept in departments:
        dept_map[dept.name.strip().lower()].append(dept)

    dept_duplicates = []
    for name, dept_list in dept_map.items():
        if len(dept_list) > 1:
            records = []
            for d in dept_list:
                coord_user = (
                    user_by_id.get(d.coordinator_id) if d.coordinator_id else None
                )
                records.append(
                    {
                        "department_id": d.department_id,
                        "name": d.name,
                        "coordinator_name": (
                            coord_user.name if coord_user else "Unassigned"
                        ),
                        "active": d.active,
                        "archived": d.archived,
                        "complaints_count": complaint_dept_counts[d.department_id],
                        "users_count": user_dept_counts[d.department_id],
                    }
                )
            dept_duplicates.append({"name": dept_list[0].name, "records": records})

    locations = auth_service.list_locations()
    loc_map = defaultdict(list)
    for loc in locations:
        loc_map[loc.name.strip().lower()].append(loc)

    loc_duplicates = []
    for name, loc_list in loc_map.items():
        if len(loc_list) > 1:
            records = []
            for l in loc_list:
                in_charge = user_by_id.get(l.in_charge_id) if l.in_charge_id else None
                records.append(
                    {
                        "location_id": l.location_id,
                        "name": l.name,
                        "in_charge_name": in_charge.name if in_charge else "Unassigned",
                        "active": l.active,
                        "archived": l.archived,
                        "complaints_count": complaint_loc_counts[l.location_id],
                        "users_count": user_loc_counts[l.location_id],
                    }
                )
            loc_duplicates.append({"name": loc_list[0].name, "records": records})

    return {"departments": dept_duplicates, "locations": loc_duplicates}


@router.post("/resolve-duplicate")
def resolve_duplicate(
    payload: ResolveDuplicateRequest,
    current_user=Depends(require_roles(Administrator.ROLE)),
    auth_service=Depends(get_auth_service),
    audit_service=Depends(get_audit_service),
):
    if payload.type not in ("department", "location"):
        raise HTTPException(
            status_code=400, detail="Invalid duplicate resolution type."
        )

    db_data = auth_service.repository.load()

    if payload.type == "department":
        complaints = db_data.get("complaints", [])
        moved_complaints = 0
        for comp in complaints:
            if comp.get("department_id") in payload.delete_ids:
                comp["department_id"] = payload.keep_id
                moved_complaints += 1

        users = db_data.get("users", [])
        moved_users = 0
        for user in users:
            if user.get("department_id") in payload.delete_ids:
                user["department_id"] = payload.keep_id
                moved_users += 1

        auth_service.repository.save(db_data)
        for delete_id in payload.delete_ids:
            auth_service.delete_department_data(delete_id)

        return {
            "message": "Duplicate departments resolved.",
            "consolidated_complaints": moved_complaints,
            "consolidated_users": moved_users,
        }

    else:
        complaints = db_data.get("complaints", [])
        moved_complaints = 0
        for comp in complaints:
            if comp.get("location_id") in payload.delete_ids:
                comp["location_id"] = payload.keep_id
                moved_complaints += 1

        users = db_data.get("users", [])
        moved_users = 0
        for user in users:
            if user.get("location_id") in payload.delete_ids:
                user["location_id"] = payload.keep_id
                moved_users += 1

        auth_service.repository.save(db_data)
        for delete_id in payload.delete_ids:
            auth_service.delete_location_data(delete_id)

        return {
            "message": "Duplicate locations resolved.",
            "consolidated_complaints": moved_complaints,
            "consolidated_users": moved_users,
        }
