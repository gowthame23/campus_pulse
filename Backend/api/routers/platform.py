from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status
from services.tenant_service import get_tenant_service, TenantService
from api.dependencies import get_platform_service, get_auth_service
from api.security import require_roles, require_super_admin
from services.platform_service import PlatformService
from models.user import User

router = APIRouter(prefix="/platform", tags=["Platform Super Admin"])

class PackageUpdateRequest(BaseModel):
    package_id: str
    feature_overrides: Optional[dict] = None

class StatusOtpConfirm(BaseModel):
    action: str
    otp_code: str
    reason: Optional[str] = ""

class InstitutionOnboardRequest(BaseModel):
    name: str = Field(..., min_length=2)
    code: str = Field(..., min_length=2, max_length=10)
    admin_name: str = Field(..., min_length=2)
    admin_email: EmailStr = Field(...)
    contact_info: Optional[str] = None
    admin_password: str = Field(..., min_length=8)
    package_id: Optional[str] = 'intermediate'


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
        tenant_svc = get_tenant_service()
        # Onboard with isolated database provisioning
        tenant_inst = tenant_svc.onboard_institution(
            name=payload.name,
            code=payload.code,
            admin_name=payload.admin_name,
            admin_email=payload.admin_email,
            admin_password=payload.admin_password,
            package_id=payload.package_id or "intermediate",
            contact_info=payload.contact_info or "",
        )
        # Also ensure platform service has metadata mirror
        try:
            platform_service.onboard_institution(payload.dict(), auth_service=auth_service)
        except Exception:
            pass
        return tenant_inst
    except ValueError as e:
        import logging
        logging.getLogger("campus_pulse").error(f"ONBOARD_INSTITUTION_ERROR: {e}")
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
        import logging
        logging.getLogger("campus_pulse").error(f"ONBOARD_INSTITUTION_ERROR: {e}")
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


@router.get("/packages")
def list_packages(
    current_user: User = Depends(require_super_admin()),
):
    """List all available platform packages and their feature sets."""
    return get_tenant_service().list_packages()


@router.put("/institutions/{institution_id}/package")
def update_institution_package(
    institution_id: str,
    payload: PackageUpdateRequest,
    current_user: User = Depends(require_super_admin()),
):
    """Assign a new package tier and optional custom feature overrides to an institute."""
    try:
        return get_tenant_service().update_institution_package(
            institution_id=institution_id,
            package_id=payload.package_id,
            feature_overrides=payload.feature_overrides,
            actor_email=current_user.email,
        )
    except ValueError as e:
        import logging
        logging.getLogger("campus_pulse").error(f"ONBOARD_INSTITUTION_ERROR: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/institutions/{institution_id}/features")
def get_institution_features(
    institution_id: str,
    current_user: User = Depends(require_super_admin()),
):
    """List all currently enabled features for an institution."""
    return get_tenant_service().get_institution_features(institution_id)


@router.post("/institutions/{institution_id}/deactivate/request-otp")
def request_deactivation_otp(
    institution_id: str,
    current_user: User = Depends(require_super_admin()),
):
    """Send a 6-digit verification code to the Super Admin's registered email before deactivating."""
    try:
        return get_tenant_service().request_status_otp(
            institution_id=institution_id,
            action="deactivate",
            superadmin_email=current_user.email,
        )
    except ValueError as e:
        import logging
        logging.getLogger("campus_pulse").error(f"ONBOARD_INSTITUTION_ERROR: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/institutions/{institution_id}/deactivate/confirm")
def confirm_deactivation(
    institution_id: str,
    payload: StatusOtpConfirm,
    current_user: User = Depends(require_super_admin()),
):
    """Confirm deactivation with the submitted OTP code. Zero data deletion."""
    try:
        return get_tenant_service().confirm_status_change(
            institution_id=institution_id,
            action="deactivate",
            otp_code=payload.otp_code,
            superadmin_email=current_user.email,
            reason=payload.reason,
        )
    except ValueError as e:
        import logging
        logging.getLogger("campus_pulse").error(f"ONBOARD_INSTITUTION_ERROR: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/institutions/{institution_id}/reactivate/request-otp")
def request_reactivation_otp(
    institution_id: str,
    current_user: User = Depends(require_super_admin()),
):
    """Send a 6-digit verification code to the Super Admin's registered email before reactivating."""
    try:
        return get_tenant_service().request_status_otp(
            institution_id=institution_id,
            action="reactivate",
            superadmin_email=current_user.email,
        )
    except ValueError as e:
        import logging
        logging.getLogger("campus_pulse").error(f"ONBOARD_INSTITUTION_ERROR: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/institutions/{institution_id}/reactivate/confirm")
def confirm_reactivation(
    institution_id: str,
    payload: StatusOtpConfirm,
    current_user: User = Depends(require_super_admin()),
):
    """Confirm reactivation with the submitted OTP code. Restores access to existing data."""
    try:
        return get_tenant_service().confirm_status_change(
            institution_id=institution_id,
            action="reactivate",
            otp_code=payload.otp_code,
            superadmin_email=current_user.email,
            reason=payload.reason,
        )
    except ValueError as e:
        import logging
        logging.getLogger("campus_pulse").error(f"ONBOARD_INSTITUTION_ERROR: {e}")
        raise HTTPException(status_code=400, detail=str(e))
