import pytest
from fastapi.testclient import TestClient

from api.main import app
from services.auth_service import AuthService
from services.platform_service import PlatformService

client = TestClient(app)
auth_service = AuthService()
platform_service = PlatformService()


def get_token(email, password):
    res = client.post("/auth/login", json={"email": email, "password": password})
    if res.status_code == 200:
        data = res.json()
        return data.get("access_token") or data.get("token")
    return None


def get_auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# Pre-fetch role tokens
def test_sa_01_super_admin_login():
    token = get_token("superadmin@campuspulse.edu", "Superadmin@123")
    assert token is not None


def test_sa_02_invalid_super_admin_login():
    token = get_token("superadmin@campuspulse.edu", "WrongPassword123")
    assert token is None


def test_sa_03_super_admin_dashboard_access():
    token = get_token("superadmin@campuspulse.edu", "Superadmin@123")
    res = client.get("/platform/dashboard", headers=get_auth_headers(token))
    assert res.status_code == 200
    data = res.json()
    assert "total_registered_institutions" in data
    assert "active_institutions" in data
    assert "open_support_issues" in data
    # Data Isolation Check: No student count or complaint count in response
    assert "student_count" not in data
    assert "complaint_count" not in data


def test_sa_04_institution_list_access():
    token = get_token("superadmin@campuspulse.edu", "Superadmin@123")
    res = client.get("/platform/institutions", headers=get_auth_headers(token))
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(inst["code"] == "ABC" for inst in data)


def test_sa_05_institution_detail_access():
    token = get_token("superadmin@campuspulse.edu", "Superadmin@123")
    res = client.get("/platform/institutions/INST_ABC", headers=get_auth_headers(token))
    assert res.status_code == 200
    data = res.json()
    assert data["institution_id"] == "INST_ABC"
    assert data["name"] == "ABC Institute of Technology"


def test_sa_06_support_issue_creation():
    admin_token = get_token("admin@example.com", "Admin@123")
    payload = {
        "module": "Complaints",
        "title": "SLA Engine Timeout Issue",
        "description": "Complaints escalation triggering 5 seconds late.",
        "error_reference": "ERR-99128",
        "priority": "High",
    }
    res = client.post("/platform/support", json=payload, headers=get_auth_headers(admin_token))
    assert res.status_code == 201
    data = res.json()
    assert data["issue_id"].startswith("SUP-")
    assert data["status"] == "Open"


def test_sa_07_support_issue_viewing():
    sa_token = get_token("superadmin@campuspulse.edu", "Superadmin@123")
    res = client.get("/platform/support", headers=get_auth_headers(sa_token))
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_sa_08_support_issue_status_update():
    sa_token = get_token("superadmin@campuspulse.edu", "Superadmin@123")
    # Fetch first issue
    tickets = client.get("/platform/support", headers=get_auth_headers(sa_token)).json()
    issue_id = tickets[0]["issue_id"]

    patch_payload = {
        "status": "Resolved",
        "resolution_notes": "Patched SLA timer threadpool configuration.",
    }
    res = client.patch(f"/platform/support/{issue_id}", json=patch_payload, headers=get_auth_headers(sa_token))
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "Resolved"
    assert data["resolution_notes"] == "Patched SLA timer threadpool configuration."


def test_sa_09_health_endpoint():
    sa_token = get_token("superadmin@campuspulse.edu", "Superadmin@123")
    res = client.get("/platform/health", headers=get_auth_headers(sa_token))
    assert res.status_code == 200
    data = res.json()
    assert data["application_status"] == "Healthy"
    assert data["database_connectivity"] is True


def test_sa_10_version_endpoint():
    sa_token = get_token("superadmin@campuspulse.edu", "Superadmin@123")
    res = client.get("/platform/version", headers=get_auth_headers(sa_token))
    assert res.status_code == 200
    data = res.json()
    assert data["application_version"] == "1.0.0"


# Authorization Checks: 5 Institutional roles must be denied Super Admin endpoints
def test_sa_11_administrator_cannot_access_super_admin_dashboard():
    admin_token = get_token("admin@example.com", "Admin@123")
    res = client.get("/platform/dashboard", headers=get_auth_headers(admin_token))
    assert res.status_code == 403


def test_sa_12_app_manager_cannot_access_super_admin_dashboard():
    mgr_token = get_token("manager@example.com", "Manager@123")
    res = client.get("/platform/dashboard", headers=get_auth_headers(mgr_token))
    assert res.status_code == 403


def test_sa_13_warden_cannot_access_super_admin_dashboard():
    warden_token = get_token("warden@example.com", "warden@123")
    res = client.get("/platform/dashboard", headers=get_auth_headers(warden_token))
    assert res.status_code == 403


def test_sa_14_coordinator_cannot_access_super_admin_dashboard():
    coord_token = get_token("coordinator@example.com", "Coordinator@123")
    res = client.get("/platform/dashboard", headers=get_auth_headers(coord_token))
    assert res.status_code == 403


def test_sa_15_student_cannot_access_super_admin_dashboard():
    student_token = get_token("student@example.com", "Student@123")
    res = client.get("/platform/dashboard", headers=get_auth_headers(student_token))
    assert res.status_code == 403


# Data Isolation Checks: Super Admin cannot access operational endpoints
def test_sa_16_super_admin_cannot_access_users():
    sa_token = get_token("superadmin@campuspulse.edu", "Superadmin@123")
    res = client.get("/users", headers=get_auth_headers(sa_token))
    assert res.status_code == 403


def test_sa_17_super_admin_cannot_access_complaints():
    sa_token = get_token("superadmin@campuspulse.edu", "Superadmin@123")
    res = client.get("/complaints", headers=get_auth_headers(sa_token))
    assert res.status_code == 403


def test_sa_18_super_admin_cannot_access_attachments():
    sa_token = get_token("superadmin@campuspulse.edu", "Superadmin@123")
    res = client.get("/complaints/CP-2026-001/attachments", headers=get_auth_headers(sa_token))
    assert res.status_code == 403


def test_sa_19_super_admin_cannot_access_student_records():
    sa_token = get_token("superadmin@campuspulse.edu", "Superadmin@123")
    res = client.get("/users/USR_STUDENT", headers=get_auth_headers(sa_token))
    assert res.status_code == 403


def test_sa_20_super_admin_cannot_modify_institution_complaints():
    sa_token = get_token("superadmin@campuspulse.edu", "Superadmin@123")
    res = client.patch("/complaints/CP-2026-001/status", json={"status": "Closed"}, headers=get_auth_headers(sa_token))
    assert res.status_code == 403


def test_sa_21_institution_support_isolation():
    # Institution A admin can create support ticket
    admin_token = get_token("admin@example.com", "Admin@123")
    res = client.get("/platform/support", headers=get_auth_headers(admin_token))
    assert res.status_code == 200
    tickets = res.json()
    for t in tickets:
        assert t["institution_id"] == "INST_ABC"


def test_sa_22_super_admin_can_see_platform_support_metadata():
    sa_token = get_token("superadmin@campuspulse.edu", "Superadmin@123")
    res = client.get("/platform/support", headers=get_auth_headers(sa_token))
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)


def test_sa_23_support_issue_cannot_expose_secrets():
    sa_token = get_token("superadmin@campuspulse.edu", "Superadmin@123")
    res = client.get("/platform/support", headers=get_auth_headers(sa_token))
    data_str = str(res.json())
    assert "Superadmin@123" not in data_str
    assert "Admin@123" not in data_str
    assert "jwt_secret" not in data_str.lower()
