import os
import sys
import uuid
import pytest
import sqlite3
import hashlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from services.tenant_service import TenantService, get_tenant_service, STANDARD_PACKAGES

client = TestClient(app)


@pytest.fixture(scope="module")
def tenant_svc():
    return get_tenant_service()


def test_packages_and_features(tenant_svc):
    packages = tenant_svc.list_packages()
    assert len(packages) >= 3
    package_ids = {p["package_id"] for p in packages}
    assert "basic" in package_ids
    assert "intermediate" in package_ids
    assert "premium" in package_ids

    # Check basic tier does not have lost_and_found or anonymous_reports
    basic_features = set(STANDARD_PACKAGES["basic"]["features"])
    assert "student_complaints" in basic_features
    assert "sla_monitoring" in basic_features
    assert "anonymous_reports" not in basic_features
    assert "lost_and_found" not in basic_features

    # Check intermediate has anonymous_reports but not lost_and_found
    inter_features = set(STANDARD_PACKAGES["intermediate"]["features"])
    assert "anonymous_reports" in inter_features
    assert "warden_inspection" in inter_features
    assert "lost_and_found" not in inter_features

    # Check premium has all
    prem_features = set(STANDARD_PACKAGES["premium"]["features"])
    assert "anonymous_reports" in prem_features
    assert "lost_and_found" in prem_features


def test_tenant_db_isolation(tenant_svc):
    code_a = f"INSTA_{uuid.uuid4().hex[:4].upper()}"
    code_b = f"INSTB_{uuid.uuid4().hex[:4].upper()}"

    # Onboard Tenant A
    res_a = tenant_svc.onboard_institution(
        name="Alpha University",
        code=code_a,
        admin_name="Alpha Admin",
        admin_email=f"admin_{code_a.lower()}@alpha.edu",
        admin_password="Password@123",
        package_id="basic",
    )
    inst_a_id = res_a["institution_id"]
    db_path_a = tenant_svc.get_tenant_db_path(inst_a_id)
    assert os.path.exists(db_path_a)

    # Onboard Tenant B
    res_b = tenant_svc.onboard_institution(
        name="Beta Institute",
        code=code_b,
        admin_name="Beta Admin",
        admin_email=f"admin_{code_b.lower()}@beta.edu",
        admin_password="Password@123",
        package_id="premium",
    )
    inst_b_id = res_b["institution_id"]
    db_path_b = tenant_svc.get_tenant_db_path(inst_b_id)
    assert os.path.exists(db_path_b)
    assert db_path_a != db_path_b

    # Verify physical data isolation by querying each SQLite file directly
    with sqlite3.connect(db_path_a) as conn_a:
        conn_a.row_factory = sqlite3.Row
        users_a = [r["email"] for r in conn_a.execute("SELECT email FROM users").fetchall()]
        assert f"admin_{code_a.lower()}@alpha.edu" in users_a
        assert f"admin_{code_b.lower()}@beta.edu" not in users_a

    with sqlite3.connect(db_path_b) as conn_b:
        conn_b.row_factory = sqlite3.Row
        users_b = [r["email"] for r in conn_b.execute("SELECT email FROM users").fetchall()]
        assert f"admin_{code_b.lower()}@beta.edu" in users_b
        assert f"admin_{code_a.lower()}@alpha.edu" not in users_b


def test_feature_gatekeeping_and_overrides(tenant_svc):
    code = f"FEAT_{uuid.uuid4().hex[:4].upper()}"
    res = tenant_svc.onboard_institution(
        name="Gamma College",
        code=code,
        admin_name="Gamma Admin",
        admin_email=f"admin_{code.lower()}@gamma.edu",
        admin_password="Password@123",
        package_id="basic",
    )
    inst_id = res["institution_id"]

    # Basic tier: student_complaints is True, lost_and_found is False
    assert tenant_svc.is_feature_enabled(inst_id, "student_complaints") is True
    assert tenant_svc.is_feature_enabled(inst_id, "lost_and_found") is False
    assert tenant_svc.is_feature_enabled(inst_id, "anonymous_reports") is False

    # Upgrade to intermediate
    tenant_svc.update_institution_package(inst_id, package_id="intermediate")
    assert tenant_svc.is_feature_enabled(inst_id, "anonymous_reports") is True
    assert tenant_svc.is_feature_enabled(inst_id, "lost_and_found") is False

    # Upgrade to premium
    tenant_svc.update_institution_package(inst_id, package_id="premium")
    assert tenant_svc.is_feature_enabled(inst_id, "lost_and_found") is True

    # Custom override: disable lost_and_found specifically
    tenant_svc.update_institution_package(
        inst_id,
        package_id="premium",
        feature_overrides={"lost_and_found": False}
    )
    assert tenant_svc.is_feature_enabled(inst_id, "lost_and_found") is False
    assert tenant_svc.is_feature_enabled(inst_id, "anonymous_reports") is True


def test_otp_deactivation_reactivation(tenant_svc):
    code = f"OTP_{uuid.uuid4().hex[:4].upper()}"
    res = tenant_svc.onboard_institution(
        name="Delta Polytechnic",
        code=code,
        admin_name="Delta Admin",
        admin_email=f"admin_{code.lower()}@delta.edu",
        admin_password="Password@123",
        package_id="basic",
    )
    inst_id = res["institution_id"]

    assert tenant_svc.is_institution_active(inst_id) is True

    # 1. Request OTP for deactivation
    req = tenant_svc.request_status_otp(
        institution_id=inst_id,
        action="deactivate",
        superadmin_email="superadmin@example.com"
    )
    assert req["status"] == "success"
    otp = req.get("_dev_otp")

    # 2. Test invalid OTP
    with pytest.raises(ValueError, match="Invalid verification code"):
        tenant_svc.confirm_status_change(
            institution_id=inst_id,
            action="deactivate",
            otp_code="000000",
            superadmin_email="superadmin@example.com"
        )
    assert tenant_svc.is_institution_active(inst_id) is True

    # 3. Confirm deactivation with correct OTP
    res = tenant_svc.confirm_status_change(
        institution_id=inst_id,
        action="deactivate",
        otp_code=otp,
        superadmin_email="superadmin@example.com",
        reason="Administrative audit"
    )
    assert res["status"] == "Inactive"
    assert tenant_svc.is_institution_active(inst_id) is False

    # 4. Request reactivation OTP
    req2 = tenant_svc.request_status_otp(
        institution_id=inst_id,
        action="reactivate",
        superadmin_email="superadmin@example.com"
    )
    assert req2["status"] == "success"
    otp2 = req2.get("_dev_otp")

    res2 = tenant_svc.confirm_status_change(
        institution_id=inst_id,
        action="reactivate",
        otp_code=otp2,
        superadmin_email="superadmin@example.com",
        reason="Audit completed successfully"
    )
    assert res2["status"] == "Active"
    assert tenant_svc.is_institution_active(inst_id) is True


def test_platform_api_package_endpoints():
    res = client.get("/platform/packages")
    assert res.status_code in (200, 401, 403)
    if res.status_code == 200:
        data = res.json()
        assert "packages" in data
        assert len(data["packages"]) >= 3
