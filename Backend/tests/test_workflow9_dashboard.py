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

def test_workflow_9_student_dashboard():
    headers = _get_headers("gowtham.e23@iiits.in", "Student@123")
    res = client.get("/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "student"
    assert "cards" in data
    assert "recent_complaints" in data
    assert "lost_found_summary" in data

    res_explicit = client.get("/dashboard/student", headers=headers)
    assert res_explicit.status_code == 200
    assert res_explicit.json()["role"] == "student"

def test_workflow_9_coordinator_dashboard():
    headers = _get_headers("gowthamejjurothu15@gmail.com", "Coordinator@123")
    res = client.get("/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] in ("coordinator", "location_in_charge")
    assert "cards" in data
    assert "assigned_complaints" in data["cards"]

def test_workflow_9_supervisor_dashboard():
    headers = _get_headers("ejjurothugowtham@gmail.com", "Manager@123")
    res = client.get("/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] in ("supervisor", "app_manager")
    assert "cards" in data

def test_workflow_9_admin_dashboard():
    headers = _get_headers("gowthamejjurothu@gmail.com", "Admin@123")
    res = client.get("/dashboard", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["role"] == "administrator"
    assert "cards" in data
    assert "total_users" in data["cards"]
    assert "user_statistics" in data
    assert "system_statistics" in data

def test_workflow_9_unauthenticated():
    client.cookies.clear()
    res = client.get("/dashboard")
    assert res.status_code in (401, 403)


def test_workflow_9_cross_role_authorization_matrix():
    student_hdr = _get_headers("gowtham.e23@iiits.in", "Student@123")
    coord_hdr = _get_headers("gowthamejjurothu15@gmail.com", "Coordinator@123")
    mgr_hdr = _get_headers("ejjurothugowtham@gmail.com", "Manager@123")
    warden_hdr = _get_headers("naveen@campus.edu", "warden@123")
    admin_hdr = _get_headers("gowthamejjurothu@gmail.com", "Admin@123")

    # 1. Student accessing admin dashboard -> REJECTED (403), no statistics in body
    res_std_admin = client.get("/dashboard/admin", headers=student_hdr)
    assert res_std_admin.status_code == 403
    assert "user_statistics" not in res_std_admin.json()
    assert "total_users" not in str(res_std_admin.json())

    # 2. Coordinator accessing admin dashboard -> REJECTED (403)
    res_coord_admin = client.get("/dashboard/admin", headers=coord_hdr)
    assert res_coord_admin.status_code == 403

    # 3. Manager / Supervisor accessing admin dashboard -> REJECTED (403)
    res_mgr_admin = client.get("/dashboard/admin", headers=mgr_hdr)
    assert res_mgr_admin.status_code == 403

    # 4. Warden accessing admin dashboard -> REJECTED (403)
    res_warden_admin = client.get("/dashboard/admin", headers=warden_hdr)
    assert res_warden_admin.status_code == 403

    # 5. Student accessing staff dashboards -> REJECTED (403)
    assert client.get("/dashboard/supervisor", headers=student_hdr).status_code == 403
    assert client.get("/dashboard/coordinator", headers=student_hdr).status_code == 403
    assert client.get("/dashboard/warden", headers=student_hdr).status_code == 403

    # 6. Administrator accessing admin dashboard -> SUCCEEDS (200)
    res_admin_admin = client.get("/dashboard/admin", headers=admin_hdr)
    assert res_admin_admin.status_code == 200
    assert "total_users" in res_admin_admin.json()["cards"]
    assert "user_statistics" in res_admin_admin.json()

