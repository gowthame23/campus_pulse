from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from api.dependencies import (
    get_announcement_service,
    get_auth_service,
    get_config_service,
)
from api.security import block_super_admin, get_current_user, require_roles
from models.administrator import Administrator
from models.app_manager import AppManager
from models.coordinator import Coordinator
from models.location_in_charge import LocationInCharge

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"],
    dependencies=[Depends(block_super_admin)],
)


# ==========================================
# SCHEMAS
# ==========================================
class TargetItem(BaseModel):
    target_type: str = "Campus"
    target_value: str = "All"


class AnnouncementUpdateRequest(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    requires_acknowledgement: Optional[bool] = None
    publish_at: Optional[str] = None
    expire_at: Optional[str] = None


class AnnouncementCreateRequest(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = ""
    category: Optional[str] = "General"
    priority: Optional[str] = "Normal"
    target: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    is_pinned: Optional[bool] = False
    expires_at: Optional[str] = None
    expire_at: Optional[str] = None
    attachment_url: Optional[str] = None
    targets: Optional[List[TargetItem]] = None
    requires_acknowledgement: Optional[bool] = False
    publish_at: Optional[str] = None


class ScheduleRequest(BaseModel):
    publish_at: str
    expire_at: Optional[str] = None


class AcknowledgeRequest(BaseModel):
    remarks: Optional[str] = ""


class AttachmentCreateRequest(BaseModel):
    file_name: str
    file_path: str
    file_size: int
    file_type: str


class AdminContactResponse(BaseModel):
    available: bool
    email: Optional[str] = None
    name: Optional[str] = None
    message: Optional[str] = None


def _ensure_can_manage(announcement_id, current_user, ann_service):
    ann = ann_service.get_announcement(announcement_id)
    if not ann:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found."
        )
    if ann["created_by"] != current_user.user_id and current_user.role not in (
        Administrator.ROLE,
        AppManager.ROLE,
        LocationInCharge.ROLE,
        "warden",
        "admin",
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only manage announcements you created or have authority over.",
        )


# ==========================================
# 1. ANNOUNCEMENT CRUD API
# ==========================================
@router.post("", status_code=status.HTTP_201_CREATED)
def create_announcement(
    payload: AnnouncementCreateRequest,
    current_user=Depends(
        require_roles(
            Administrator.ROLE,
            AppManager.ROLE,
            LocationInCharge.ROLE,
            "warden",
            "admin",
        )
    ),
    ann_service=Depends(get_announcement_service),
):
    try:
        tgt_dicts = [t.dict() for t in payload.targets] if payload.targets else None
        return ann_service.create_announcement(
            title=payload.title,
            content=payload.content,
            description=payload.description,
            summary=payload.summary or "",
            category=payload.category or "General",
            priority=payload.priority or "Normal",
            target=payload.target,
            target_type=payload.target_type,
            target_id=payload.target_id,
            is_pinned=bool(payload.is_pinned),
            expires_at=payload.expires_at or payload.expire_at,
            attachment_url=payload.attachment_url,
            targets=tgt_dicts,
            requires_acknowledgement=bool(payload.requires_acknowledgement),
            publish_at=payload.publish_at,
            created_by=current_user.user_id,
            user_role=current_user.role,
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("")
@router.get("/search")
def list_announcements(
    q: Optional[str] = Query(None, alias="query"),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user=Depends(get_current_user),
    ann_service=Depends(get_announcement_service),
):
    return ann_service.list_announcements(
        user=current_user,
        category=category,
        priority=priority,
        status=status_filter,
        q=q,
    )


@router.get("/admin-contact", response_model=AdminContactResponse)
def get_admin_contact(
    current_user=Depends(get_current_user),
    auth_service=Depends(get_auth_service),
    config_service=Depends(get_config_service),
):
    # 1. Search for active Administrator user in users table
    try:
        admin_users = auth_service.list_users(role=Administrator.ROLE)
        if admin_users:
            target_admin = next(
                (u for u in admin_users if u.user_id == "USR_ADMIN"), admin_users[0]
            )
            if target_admin and target_admin.email:
                return AdminContactResponse(
                    available=True,
                    email=target_admin.email,
                    name=target_admin.name or "Campus Admin",
                    message="Official campus administration contact.",
                )
    except Exception:
        pass

    # 2. Check config / institution settings
    try:
        inst_email = config_service.get_setting("admin_contact_email") or config_service.get_setting("contact_email")
        if inst_email:
            return AdminContactResponse(
                available=True,
                email=str(inst_email),
                name="Campus Administration",
                message="Official campus administration contact.",
            )
    except Exception:
        pass

    # 3. Check institutions table
    try:
        with auth_service._connect() as conn:
            row = conn.execute(
                "SELECT admin_email, name FROM institutions WHERE status = 'Active' LIMIT 1"
            ).fetchone()
            if row and row["admin_email"]:
                return AdminContactResponse(
                    available=True,
                    email=row["admin_email"],
                    name=row["name"] or "Campus Administration",
                    message="Official campus administration contact.",
                )
    except Exception:
        pass

    return AdminContactResponse(
        available=False,
        email=None,
        name=None,
        message="Admin contact email is currently unavailable. Please visit the campus administrative office.",
    )


@router.get("/{announcement_id}")
def get_announcement(
    announcement_id: str,
    current_user=Depends(get_current_user),
    ann_service=Depends(get_announcement_service),
):
    ann = ann_service.get_announcement(announcement_id, user=current_user)
    if not ann:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Announcement not found."
        )
    return ann


@router.put("/{announcement_id}")
def update_announcement(
    announcement_id: str,
    payload: AnnouncementUpdateRequest,
    current_user=Depends(
        require_roles(
            Administrator.ROLE,
            AppManager.ROLE,
            LocationInCharge.ROLE,
            "warden",
            "admin",
        )
    ),
    ann_service=Depends(get_announcement_service),
):
    _ensure_can_manage(announcement_id, current_user, ann_service)
    try:
        return ann_service.update_announcement(
            announcement_id,
            payload.dict(exclude_unset=True),
            performer_id=current_user.user_id,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    current_user=Depends(
        require_roles(Administrator.ROLE, AppManager.ROLE, "admin")
    ),
    ann_service=Depends(get_announcement_service),
):
    try:
        return ann_service.delete_announcement(
            announcement_id, performer_id=current_user.user_id
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


# ==========================================
# 2. PUBLISH & SCHEDULING API
# ==========================================
@router.put("/{announcement_id}/publish")
def publish_announcement(
    announcement_id: str,
    current_user=Depends(
        require_roles(
            Administrator.ROLE,
            AppManager.ROLE,
            LocationInCharge.ROLE,
            "warden",
            "admin",
        )
    ),
    ann_service=Depends(get_announcement_service),
):
    _ensure_can_manage(announcement_id, current_user, ann_service)
    try:
        return ann_service.update_announcement(
            announcement_id,
            {"status": "Published", "published_by": current_user.user_id},
            performer_id=current_user.user_id,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.put("/{announcement_id}/schedule")
def schedule_announcement(
    announcement_id: str,
    payload: ScheduleRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    ann_service=Depends(get_announcement_service),
):
    try:
        return ann_service.update_announcement(
            announcement_id,
            {
                "status": "Scheduled",
                "publish_at": payload.publish_at,
                "expire_at": payload.expire_at,
            },
            performer_id=current_user.user_id,
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.put("/{announcement_id}/cancel")
def cancel_announcement(
    announcement_id: str,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    ann_service=Depends(get_announcement_service),
):
    try:
        return ann_service.update_announcement(
            announcement_id, {"status": "Cancelled"}, performer_id=current_user.user_id
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.put("/{announcement_id}/restore")
def restore_announcement(
    announcement_id: str,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    ann_service=Depends(get_announcement_service),
):
    try:
        return ann_service.update_announcement(
            announcement_id, {"status": "Published"}, performer_id=current_user.user_id
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


# ==========================================
# 3. ATTACHMENTS API
# ==========================================
@router.post("/{announcement_id}/attachments", status_code=status.HTTP_201_CREATED)
def add_attachment(
    announcement_id: str,
    payload: AttachmentCreateRequest,
    current_user=Depends(
        require_roles(
            Administrator.ROLE, AppManager.ROLE, LocationInCharge.ROLE
        )
    ),
    ann_service=Depends(get_announcement_service),
):
    _ensure_can_manage(announcement_id, current_user, ann_service)
    return ann_service.add_attachment(
        announcement_id=announcement_id,
        file_name=payload.file_name,
        file_path=payload.file_path,
        file_size=payload.file_size,
        file_type=payload.file_type,
        uploaded_by=current_user.user_id,
    )


@router.get("/{announcement_id}/attachments")
def get_attachments(
    announcement_id: str,
    current_user=Depends(get_current_user),
    ann_service=Depends(get_announcement_service),
):
    return ann_service.get_attachments(announcement_id)


@router.put("/{announcement_id}/archive")
@router.post("/{announcement_id}/archive")
@router.patch("/{announcement_id}/archive")
def archive_announcement(
    announcement_id: str,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    ann_service=Depends(get_announcement_service),
):
    try:
        return ann_service.update_announcement(
            announcement_id, {"status": "Archived"}, performer_id=current_user.user_id
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


# ==========================================
# 4. READ TRACKING & ACKNOWLEDGEMENT API
# ==========================================
@router.post("/{announcement_id}/read")
@router.put("/{announcement_id}/read")
def mark_read(
    announcement_id: str,
    request: Request,
    current_user=Depends(get_current_user),
    ann_service=Depends(get_announcement_service),
):
    client_ip = request.client.host if request.client else "unknown"
    return ann_service.mark_read(
        announcement_id,
        user_id=current_user.user_id,
        device="Browser",
        ip_address=client_ip,
    )


@router.get("/{announcement_id}/reads")
def get_readership(
    announcement_id: str,
    current_user=Depends(
        require_roles(
            Administrator.ROLE, AppManager.ROLE, Coordinator.ROLE, LocationInCharge.ROLE
        )
    ),
    ann_service=Depends(get_announcement_service),
):
    return ann_service.get_readership_metrics(announcement_id)


@router.put("/{announcement_id}/acknowledge")
def acknowledge_announcement(
    announcement_id: str,
    payload: Optional[AcknowledgeRequest] = None,
    current_user=Depends(get_current_user),
    ann_service=Depends(get_announcement_service),
):
    remarks = payload.remarks if payload else ""
    return ann_service.acknowledge(
        announcement_id, user_id=current_user.user_id, remarks=remarks
    )
