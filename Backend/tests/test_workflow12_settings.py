import pytest
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from middleware.rate_limiter import auth_limiter

client = TestClient(app)

def _reset_limiter():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()

def _get_headers(email, password):
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": email, "password": password})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_workflow_12_admin_settings_access():
    admin_headers = _get_headers("admin@example.com", "Admin@123")

    # 1. Get all settings
    all_res = client.get("/settings", headers=admin_headers)
    assert all_res.status_code == 200
    assert isinstance(all_res.json(), dict)

    # 2. Get system health
    health_res = client.get("/settings/system-health", headers=admin_headers)
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "Healthy"

    # 3. Get about info
    about_res = client.get("/settings/about", headers=admin_headers)
    assert about_res.status_code == 200
    assert about_res.json()["application_name"] == "Campus Pulse"

    # 4. Export backup
    bup_res = client.post("/settings/backup", headers=admin_headers)
    assert bup_res.status_code == 200
    assert "data" in bup_res.json()

    # 5. Update single setting
    upd_res = client.put("/settings/key/AUTO_CLOSE_DAYS", json={"setting_value": "7"}, headers=admin_headers)
    assert upd_res.status_code == 200

def test_workflow_12_non_admin_forbidden():
    std_headers = _get_headers("student@example.com", "Student@123")
    coord_headers = _get_headers("coordinator@example.com", "Coordinator@123")

    # Student -> 403 Forbidden
    res_std = client.get("/settings", headers=std_headers)
    assert res_std.status_code == 403

    # Coordinator -> 403 Forbidden
    res_coord = client.get("/settings", headers=coord_headers)
    assert res_coord.status_code == 403
