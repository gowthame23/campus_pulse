from typing import Optional
from fastapi import Request
import os

from services.analytics_service import AnalyticsService
from services.announcement_service import AnnouncementService
from services.attachment_service import AttachmentService
from services.audit_service import AuditService
from services.auth_service import AuthService
from services.backup_service import BackupService
from services.chat_service import ChatService
from services.classification_service import ClassificationService
from services.comment_service import CommentService
from services.complaint_service import ComplaintService
from services.config_service import ConfigService
from services.dashboard_service import DashboardService
from services.department_service import DepartmentService
from services.dependency_service import DependencyService
from services.feedback_service import FeedbackService
from services.global_search_service import GlobalSearchService
from services.location_service import LocationService
from services.lost_found_service import LostFoundService
from services.notification_service import NotificationService
from services.report_service import ReportService
from services.team_service import TeamService
from services.validation_service import ValidationService


from services.platform_service import PlatformService
from services.program_service import ProgramService
from services.public_complaint_service import PublicComplaintService
from services.emergency_service import EmergencyService
from services.setup_import_service import SetupImportService
from services.translation_service import TranslationService
from utils.db import get_db_connection


from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


def load_env(path=None):
    candidates = [
        path,
        os.environ.get("ENV_FILE"),
        BACKEND_DIR / ".env",
        BACKEND_DIR.parent / ".env",
        Path(".env"),
    ]
    for c in candidates:
        if c and os.path.exists(c):
            with open(c, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, val = line.split("=", 1)
                        os.environ.setdefault(key.strip(), val.strip())
            break


load_env()


def get_db_path() -> str:
    raw_path = os.environ.get("DATABASE_PATH", "storage/campus_pulse.db")
    p = Path(raw_path)
    if not p.is_absolute():
        p = (BACKEND_DIR / p).resolve()
    return str(p)



def _resolve_db_path(request: Request = None) -> str:
    """Resolves the isolated database path for the requesting tenant.
    If authenticated, uses the verified user's institution_id.
    Falls back to system default database if no specific tenant is resolved.
    """
    if request:
        inst_id = getattr(request.state, "institution_id", None)
        if not inst_id and hasattr(request.state, "user"):
            inst_id = getattr(request.state.user, "institution_id", None)
        if not inst_id:
            inst_id = request.headers.get("X-Institute-ID") or request.headers.get("X-Tenant-ID")
        if inst_id and str(inst_id).strip().upper() != "INST_ABC":
            clean_id = str(inst_id).strip().upper()
            from services.tenant_service import get_tenant_service
            tenant_db = get_tenant_service().get_tenant_db_path(clean_id)
            if os.path.exists(tenant_db):
                return tenant_db
    return get_db_path()

_service_cache = {}


def _get_services_for_db(path: str = None):
    if path is None:
        path = get_db_path()
    if path not in _service_cache:
        dash_svc = DashboardService(db_path=path)
        notif_svc = NotificationService(db_path=path)
        auth_svc = AuthService(db_path=path, notification_service=notif_svc)
        tm_svc = TeamService(db_path=path, auth_service=auth_svc, notification_service=notif_svc)

        # Seed Coordinator 1 / Coordinator 2 as working members of their home
        # teams. Without this, the two generic demo coordinator accounts can
        # log in but the complaint-assignment code correctly refuses to let
        # them act on complaints outside any team they're not actually a
        # member of -- which is correct behavior, but left them unable to do
        # anything useful out of the box. assign_work_membership() is the
        # same call the real "add team member" UI makes, and it's a no-op if
        # the membership already exists, so this is safe to run every boot.
        try:
            tm_svc.assign_work_membership("USR_COORD_1", "DEPT_HOSTEL_ELECTRICAL", "LOC_HOSTEL_1", created_by="system")
            tm_svc.assign_work_membership("USR_COORD_2", "DEPT_HOSTEL_PLUMBING", "LOC_HOSTEL_2", created_by="system")
        except Exception as err:
            import logging
            logging.getLogger(__name__).warning(f"Could not seed default coordinator work memberships: {err}")
        cmpl_svc = ComplaintService(auth_svc, notif_svc, db_path=path, team_service=tm_svc)
        anal_svc = AnalyticsService(db_path=path)
        aud_svc = AuditService(db_path=path)
        val_svc = ValidationService(auth_svc)
        dep_svc = DependencyService(auth_svc, cmpl_svc, notif_svc)
        dept_svc = DepartmentService(auth_svc, val_svc, dep_svc, team_service=tm_svc)

        loc_svc = LocationService(auth_svc, val_svc, dep_svc)
        lf_svc = LostFoundService(notification_service=notif_svc, audit_service=aud_svc, db_path=path, auth_service=auth_svc)
        anc_svc = AnnouncementService(notification_service=notif_svc, audit_service=aud_svc, db_path=path)
        fb_svc = FeedbackService(notification_service=notif_svc, audit_service=aud_svc, db_path=path)
        rep_svc = ReportService(notification_service=notif_svc, audit_service=aud_svc, db_path=path)
        gs_svc = GlobalSearchService(notification_service=notif_svc, audit_service=aud_svc, db_path=path)
        bk_svc = BackupService(notification_service=notif_svc, audit_service=aud_svc, db_path=path)
        cmt_svc = CommentService(db_path=path)
        cfg_svc = ConfigService(db_path=path)
        att_svc = AttachmentService(db_path=path)
        cht_svc = ChatService(db_path=path, audit_service=aud_svc)
        cls_svc = ClassificationService(db_path=path)
        pub_svc = PublicComplaintService(
            complaint_service=cmpl_svc,
            auth_service=auth_svc,
            notification_service=notif_svc,
            db_path=path,
        )
        plt_svc = PlatformService(db_path=path)
        prg_svc = ProgramService(db_path=path)
        emg_svc = EmergencyService(
            db_path=path,
            auth_service=auth_svc,
            team_service=tm_svc,
            notification_service=notif_svc,
            config_service=cfg_svc,
            complaint_service=cmpl_svc,
        )

        setup_svc = SetupImportService(
            auth_service=auth_svc,
            team_service=tm_svc,
            emergency_service=emg_svc,
            complaint_service=cmpl_svc,
        )

        trans_svc = TranslationService(db_connect_func=lambda: get_db_connection(path))

        _service_cache[path] = {
            "dashboard": dash_svc,
            "notification": notif_svc,
            "auth": auth_svc,
            "complaint": cmpl_svc,
            "analytics": anal_svc,
            "audit": aud_svc,
            "validation": val_svc,
            "dependency": dep_svc,
            "department": dept_svc,
            "location": loc_svc,
            "lost_found": lf_svc,
            "announcement": anc_svc,
            "feedback": fb_svc,
            "report": rep_svc,
            "global_search": gs_svc,
            "backup": bk_svc,
            "comment": cmt_svc,
            "config": cfg_svc,
            "attachment": att_svc,
            "chat": cht_svc,
            "classification": cls_svc,
            "public_complaint": pub_svc,
            "platform": plt_svc,
            "program": prg_svc,
            "team": tm_svc,
            "emergency": emg_svc,
            "setup_import": setup_svc,
            "translation": trans_svc,
        }
    return _service_cache[path]


# Backwards-compatible module globals using default db_path
db_path = get_db_path()
_default_svcs = _get_services_for_db(db_path)

dashboard_service = _default_svcs["dashboard"]
notification_service = _default_svcs["notification"]
auth_service = _default_svcs["auth"]
complaint_service = _default_svcs["complaint"]
analytics_service = _default_svcs["analytics"]
audit_service = _default_svcs["audit"]
validation_service = _default_svcs["validation"]
dependency_service = _default_svcs["dependency"]
department_service = _default_svcs["department"]
location_service = _default_svcs["location"]
lost_found_service = _default_svcs["lost_found"]
announcement_service = _default_svcs["announcement"]
feedback_service = _default_svcs["feedback"]
report_service = _default_svcs["report"]
global_search_service = _default_svcs["global_search"]
backup_service = _default_svcs["backup"]
comment_service = _default_svcs["comment"]
config_service = _default_svcs["config"]
attachment_service = _default_svcs["attachment"]
chat_service = _default_svcs["chat"]
classification_service = _default_svcs["classification"]
public_complaint_service = _default_svcs["public_complaint"]
platform_service = _default_svcs["platform"]
team_service = _default_svcs["team"]


def get_dashboard_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["dashboard"]


def get_auth_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["auth"]


def get_notification_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["notification"]


def get_complaint_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["complaint"]


def get_analytics_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["analytics"]


def get_lost_found_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["lost_found"]


def get_announcement_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["announcement"]


def get_feedback_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["feedback"]


def get_report_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["report"]


def get_global_search_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["global_search"]


def get_public_complaint_service(request: Request = None) -> PublicComplaintService:
    return _get_services_for_db(_resolve_db_path(request))["public_complaint"]


def get_backup_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["backup"]


def get_audit_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["audit"]


def get_department_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["department"]


def get_location_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["location"]


def get_comment_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["comment"]


def get_config_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["config"]


def get_attachment_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["attachment"]


def get_chat_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["chat"]


def get_classification_service(request: Request = None):
    return _get_services_for_db(_resolve_db_path(request))["classification"]


def get_platform_service(request: Request = None) -> PlatformService:
    return _get_services_for_db(_resolve_db_path(request))["platform"]


def get_program_service(request: Request = None) -> ProgramService:
    return _get_services_for_db(_resolve_db_path(request))["program"]


def get_team_service(request: Request = None) -> TeamService:
    return _get_services_for_db(_resolve_db_path(request))["team"]


def get_emergency_service(request: Request = None) -> EmergencyService:
    return _get_services_for_db(_resolve_db_path(request))["emergency"]


def get_setup_import_service(request: Request = None) -> SetupImportService:
    return _get_services_for_db(_resolve_db_path(request))["setup_import"]


def get_translation_service(request: Request = None) -> TranslationService:
    return _get_services_for_db(_resolve_db_path(request))["translation"]




from services.tenant_service import get_tenant_service, TenantService


def get_tenant_service_dep() -> TenantService:
    return get_tenant_service()
