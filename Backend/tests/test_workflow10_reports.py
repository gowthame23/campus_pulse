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

def test_workflow_10_admin_reports():
    headers = _get_headers("admin@example.com", "Admin@123")

    # 1. Complaints report
    c_res = client.get("/reports/complaints", headers=headers)
    assert c_res.status_code == 200
    c_data = c_res.json()
    assert "total_complaints" in c_data
    assert "open_complaints" in c_data
    assert "by_status" in c_data

    # 2. Locations report
    l_res = client.get("/reports/locations", headers=headers)
    assert l_res.status_code == 200
    assert isinstance(l_res.json(), list)

    # 3. Departments report
    d_res = client.get("/reports/departments", headers=headers)
    assert d_res.status_code == 200
    assert isinstance(d_res.json(), list)

    # 4. Coordinator performance report
    p_res = client.get("/reports/performance", headers=headers)
    assert p_res.status_code == 200
    assert isinstance(p_res.json(), list)

    # 5. Lost & Found report
    lf_res = client.get("/reports/lost-found", headers=headers)
    assert lf_res.status_code == 200
    assert "lost_reports" in lf_res.json()

    # 6. Users report
    u_res = client.get("/reports/users", headers=headers)
    assert u_res.status_code == 200
    assert "total_users" in u_res.json()

def test_workflow_10_student_forbidden():
    headers = _get_headers("student@example.com", "Student@123")
    res = client.get("/reports/complaints", headers=headers)
    assert res.status_code == 403
