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

def test_workflow_11_admin_audit_access():
    admin_headers = _get_headers("admin@example.com", "Admin@123")

    # 1. List audit logs
    list_res = client.get("/audit", headers=admin_headers)
    assert list_res.status_code == 200
    assert "items" in list_res.json()

    # 2. Get dashboard metrics
    dash_res = client.get("/audit/dashboard", headers=admin_headers)
    assert dash_res.status_code == 200

    # 3. Get entity timeline
    time_res = client.get("/audit/timeline/Complaint/CP-2026-001", headers=admin_headers)
    assert time_res.status_code == 200
    assert isinstance(time_res.json(), list)

    # 4. Export audit logs
    exp_res = client.get("/audit/export?format=csv", headers=admin_headers)
    assert exp_res.status_code == 200
    assert exp_res.headers["content-type"].startswith("text/csv")

def test_workflow_11_non_admin_forbidden():
    std_headers = _get_headers("student@example.com", "Student@123")
    coord_headers = _get_headers("coordinator@example.com", "Coord@123")

    # Student -> 403 Forbidden
    res_std = client.get("/audit", headers=std_headers)
    assert res_std.status_code == 403

    # Coordinator -> 403 Forbidden
    res_coord = client.get("/audit", headers=coord_headers)
    assert res_coord.status_code == 403
