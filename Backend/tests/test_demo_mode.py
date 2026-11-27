import os
import sys

from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from api.main import app
from services.auth_service import DEMO_ACCOUNTS, AuthService
from utils.passwords import verify_password

client = TestClient(app, raise_server_exceptions=False)


def test_demo_accounts_endpoint_hidden_without_demo_mode(monkeypatch):
    monkeypatch.delenv("DEMO_MODE", raising=False)
    res = client.get("/auth/demo-accounts")
    assert res.status_code == 200
    assert res.json() == {"enabled": False, "accounts": []}


def test_demo_accounts_endpoint_lists_ten_accounts(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    res = client.get("/auth/demo-accounts")
    assert res.status_code == 200
    body = res.json()
    assert body["enabled"] is True
    assert len(body["accounts"]) == 10
    assert all(a["email"].endswith("@campuspulse.edu") for a in body["accounts"])


def test_demo_mode_seeds_all_demo_accounts_in_production(monkeypatch, tmp_path):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("ENVIRONMENT", "production")
    # Real addresses configured on the host must not leak into a demo deployment.
    monkeypatch.setenv("SUPER_ADMIN_EMAIL", "real.owner@example.org")
    monkeypatch.setenv("ADMIN_EMAIL", "real.admin@example.org")
    monkeypatch.setenv("STUDENT_EMAIL", "real.student@example.org")
    monkeypatch.delenv("SEED_USR_ADMIN_PASSWORD", raising=False)

    svc = AuthService(db_path=str(tmp_path / "demo.db"))
    for demo in DEMO_ACCOUNTS:
        user = svc.get_user(demo["user_id"])
        assert user is not None, demo["user_id"]
        assert user.email == demo["email"]
        assert verify_password(demo["password"], user.password)
        assert not user.first_login

    # A visitor changing a demo password is undone on the next start.
    svc.change_password("USR_STUDENT", "Changed@456", old_password="Student@123")
    assert not verify_password("Student@123", svc.get_user("USR_STUDENT").password)
    svc2 = AuthService(db_path=str(tmp_path / "demo.db"))
    assert verify_password("Student@123", svc2.get_user("USR_STUDENT").password)


def test_institution_list_reflects_otp_status_change(monkeypatch):
    """Deactivating an institute must show up in the registry list the super admin sees."""
    monkeypatch.setenv("DEMO_MODE", "true")  # code is returned instead of emailed
    res = client.post("/auth/login", json={"email": "superadmin@campuspulse.edu", "password": "Superadmin@123"})
    assert res.status_code == 200
    token = res.json().get("access_token") or res.json().get("token")
    headers = {"Authorization": f"Bearer {token}"}

    def status_in_list():
        insts = client.get("/platform/institutions", headers=headers).json()
        return next(i["status"] for i in insts if i["institution_id"] == "INST_ABC")

    try:
        for action, expected in (("deactivate", "Inactive"), ("reactivate", "Active")):
            if status_in_list() == expected:
                continue
            otp = client.post(f"/platform/institutions/INST_ABC/{action}/request-otp", headers=headers).json()["demo_otp"]
            res = client.post(
                f"/platform/institutions/INST_ABC/{action}/confirm",
                headers=headers,
                json={"action": action, "otp_code": otp, "reason": "test"},
            )
            assert res.status_code == 200, res.text
            assert status_in_list() == expected
    finally:
        # Leave the shared test institute active for the rest of the suite.
        from services.tenant_service import get_tenant_service
        from services.platform_service import PlatformService

        with get_tenant_service()._connect_platform() as conn:
            conn.execute("UPDATE institutes SET status = 'Active' WHERE institution_id = 'INST_ABC'")
            conn.commit()
        PlatformService(db_path=os.environ["DATABASE_PATH"]).set_institution_status("INST_ABC", "Active")
