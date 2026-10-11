import pytest
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from middleware.rate_limiter import auth_limiter
from api.dependencies import _service_cache

client = TestClient(app)

def _reset_limiter():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()
    _service_cache.clear()
    import sqlite3
    from utils.passwords import hash_password
    for db_p in ("storage/campus_pulse.db", "Backend/storage/campus_pulse.db", "storage/pytest_isolated.db", "Backend/storage/pytest_isolated.db"):
        if os.path.exists(db_p):
            try:
                conn = sqlite3.connect(db_p)
                conn.execute("DELETE FROM login_attempts")
                conn.execute("UPDATE users SET password = ?, active = 1, status = 'Active' WHERE email = ?", (hash_password("Student@123"), "gowtham.e23@iiits.in"))
                conn.execute("UPDATE users SET password = ?, active = 1, status = 'Active' WHERE email = ?", (hash_password("Admin@123"), "gowthamejjurothu@gmail.com"))
                conn.commit()
                conn.close()
            except Exception:
                pass
    _service_cache.clear()


def login_user(email, password):
    _reset_limiter()
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_workload_endpoint_rbac_and_metrics():
    # 1. Student access should be forbidden (403)
    student_headers = login_user("gowtham.e23@iiits.in", "Student@123")
    res_student = client.get("/complaints/workload", headers=student_headers)
    assert res_student.status_code == 403
    assert "Students are not authorized to view staff workload." in res_student.json()["detail"]

    # 2. Admin access should succeed
    admin_headers = login_user("gowthamejjurothu@gmail.com", "Admin@123")
    res_admin = client.get("/complaints/workload", headers=admin_headers)
    assert res_admin.status_code == 200
    data = res_admin.json()

    assert "summary" in data
    summary = data["summary"]
    assert "total" in summary
    assert "unassigned" in summary
    assert "assigned" in summary
    assert "left" in summary
    assert "resolved" in summary

    # Verify math consistency
    assert summary["assigned"] + summary["unassigned"] == summary["total"]
    assert summary["left"] + summary["resolved"] == summary["total"]

    # Staff sections
    assert "app_managers" in data
    assert "wardens" in data
    assert "coordinators" in data
    assert "unassigned_complaints" in data

    # Verify individual staff row metrics (Must NOT contain unassigned key)
    for staff in data["wardens"] + data["coordinators"] + data["app_managers"]:
        assert "assigned" in staff
        assert "left" in staff
        assert "resolved" in staff
        assert "unassigned" not in staff, "Unassigned must NOT be attributed to an individual staff member row"


def test_resolved_endpoint_filtering_and_lifecycle():
    admin_headers = login_user("gowthamejjurothu@gmail.com", "Admin@123")

    # 1. Fetch resolved list
    res = client.get("/complaints/resolved", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data

    for item in data["items"]:
        status_clean = item.get("status")
        has_resolved_at = bool(item.get("resolved_at"))
        valid = (
            status_clean in ("Resolved", "Closed", "Closed (Auto Closed)", "Waiting for Verification")
            or has_resolved_at
        )
        assert valid, f"Complaint {item['complaint_id']} with status {status_clean} should not be in resolved view"

    # 2. Filter by query
    res_q = client.get("/complaints/resolved?q=CMP", headers=admin_headers)
    assert res_q.status_code == 200

    # 3. Student can view resolved items
    student_headers = login_user("gowtham.e23@iiits.in", "Student@123")
    res_st = client.get("/complaints/resolved", headers=student_headers)
    assert res_st.status_code == 200
