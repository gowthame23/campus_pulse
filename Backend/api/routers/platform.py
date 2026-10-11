from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

from api.dependencies import get_platform_service, get_auth_service
from api.security import require_roles, require_super_admin
from services.platform_service import PlatformService
from models.user import User

router = APIRouter(prefix="/platform", tags=["Platform Super Admin"])


class InstitutionOnboardRequest(BaseModel):
    name: str = Field(..., min_length=2)
    code: str = Field(..., min_length=2, max_length=10)
    admin_name: str = Field(..., min_length=2)
    admin_email: EmailStr = Field(...)
    contact_info: Optional[str] = None
    admin_password: str = Field(..., min_length=8)


class SupportTicketCreate(BaseModel):
    module: Optional[str] = "General"
    title: str = Field(..., min_length=3)
    description: str = Field(..., min_length=5)
    error_reference: Optional[str] = None
    priority: Optional[str] = "Medium"


class SupportTicketUpdate(BaseModel):
    status: Optional[str] = None
    resolution_notes: Optional[str] = None


@router.get("/dashboard")
def get_dashboard(
    current_user: User = Depends(require_super_admin()),
    platform_service: PlatformService = Depends(get_platform_service),
):
    return platform_service.get_platform_dashboard()


@router.get("/institutions")
def list_institutions(
    current_user: User = Depends(require_super_admin()),
    platform_service: PlatformService = Depends(get_platform_service),
):
    return platform_service.get_institutions()


@router.get("/institutions/{institution_id}")
def get_institution_detail(
    institution_id: str,
    current_user: User = Depends(require_super_admin()),
    platform_service: PlatformService = Depends(get_platform_service),
):
    inst = platform_service.get_institution(institution_id)
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found.")
    return inst


@router.post("/institutions", status_code=status.HTTP_201_CREATED)
def onboard_institution(
    payload: InstitutionOnboardRequest,
    current_user: User = Depends(require_super_admin()),
    platform_service: PlatformService = Depends(get_platform_service),
    auth_service=Depends(get_auth_service),
):
    try:
        return platform_service.onboard_institution(payload.dict(), auth_service=auth_service)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/support")
def get_support_tickets(
    current_user: User = Depends(require_roles("super_admin", "administrator")),
    platform_service: PlatformService = Depends(get_platform_service),
):
    if current_user.role == "super_admin":
        return platform_service.get_support_tickets(institution_id=None)
    else:
        # For Institution Admin, default to INST_ABC
        institution_id = getattr(current_user, "institution_id", None) or "INST_ABC"
        return platform_service.get_support_tickets(institution_id=institution_id)


@router.post("/support", status_code=status.HTTP_201_CREATED)
def create_support_ticket(
    payload: SupportTicketCreate,
    current_user: User = Depends(require_roles("administrator")),
    platform_service: PlatformService = Depends(get_platform_service),
):
    institution_id = getattr(current_user, "institution_id", None) or "INST_ABC"
    try:
        return platform_service.create_support_ticket(institution_id, payload.dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/support/{issue_id}")
def update_support_ticket(
    issue_id: str,
    payload: SupportTicketUpdate,
    current_user: User = Depends(require_super_admin()),
    platform_service: PlatformService = Depends(get_platform_service),
):
    try:
        return platform_service.update_support_ticket(
            issue_id, status=payload.status, resolution_notes=payload.resolution_notes
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/health")
def get_health_status(
    current_user: User = Depends(require_super_admin()),
    platform_service: PlatformService = Depends(get_platform_service),
):
    return platform_service.get_system_health()


@router.get("/version")
def get_version_info(
    current_user: User = Depends(require_super_admin()),
    platform_service: PlatformService = Depends(get_platform_service),
):
    return platform_service.get_version_info()
