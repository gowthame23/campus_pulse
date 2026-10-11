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

