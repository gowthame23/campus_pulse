import pytest
import sys
import os
import uuid
import threading

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

def _get_headers_for(username, password):
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": username, "password": password})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_concurrency_simultaneous_updates_and_status_changes():
    std_headers = _get_headers_for("student@example.com", "Student@123")
    admin_headers = _get_headers_for("admin@example.com", "Admin@123")

    # Create complaint
    uid = uuid.uuid4().hex[:6]
    c_res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_ELECTRICAL",
        "title": "Concurrency Test Complaint",
        "description": f"Testing concurrent requests {uid}"
    }, headers=std_headers)
    assert c_res.status_code == 201
    cid = c_res.json()["complaint_id"]

    results = []

    def worker_accept():
        r = client.post(f"/complaints/{cid}/accept", json={}, headers=admin_headers)
        results.append(("accept", r.status_code))

    def worker_resolve():
        r = client.post(f"/complaints/{cid}/resolve", json={"notes": "Resolved concurrently"}, headers=admin_headers)
        results.append(("resolve", r.status_code))

    t1 = threading.Thread(target=worker_accept)
    t2 = threading.Thread(target=worker_resolve)

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Both requests finish safely without server crash or DB corruption
    assert len(results) == 2
    status_codes = [r[1] for r in results]
    assert all(code in (200, 400, 409, 410, 422) for code in status_codes)
