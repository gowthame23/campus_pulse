import pytest
import sys
import os
import uuid

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import db_path
from middleware.rate_limiter import auth_limiter

client = TestClient(app)

def _reset_limiter():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()

def _get_student_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "student@example.com", "password": "Student@123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def _get_admin_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "admin@example.com", "password": "Admin@123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_workflow_5_empty_public_complaints_returns_200_array():
    std_headers = _get_student_headers()
    res = client.get("/public-complaints?location_id=NON_EXISTENT_LOC_9999", headers=std_headers)
    assert res.status_code == 200
    assert res.json() == []

def test_workflow_5_public_complaint_flow_and_join():
    std_headers = _get_student_headers()
    admin_headers = _get_admin_headers()
    uid = uuid.uuid4().hex[:6]

    # 1. Create Public Complaint
    pub_res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_ELECTRICAL",
        "title": f"Public Power Failure {uid}",
        "description": f"Entire block power outage {uid}.",
        "visibility_type": "Public"
    }, headers=std_headers)
    assert pub_res.status_code == 201
    pub_id = pub_res.json()["complaint_id"]

    # 2. Create Private Complaint
    priv_res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_ELECTRICAL",
        "title": f"Private Personal Issue {uid}",
        "description": f"My room bulb flickers {uid}.",
        "visibility_type": "Private"
    }, headers=std_headers)
    assert priv_res.status_code == 201
    priv_id = priv_res.json()["complaint_id"]

    # 3. List public complaints
    list_res = client.get("/public-complaints", headers=std_headers)
    assert list_res.status_code == 200
    pub_ids = [c["complaint_id"] for c in list_res.json()]
    assert pub_id in pub_ids
    assert priv_id not in pub_ids

    # 4. Access private complaint directly via public endpoint -> 403 Forbidden
    detail_priv = client.get(f"/public-complaints/{priv_id}", headers=std_headers)
    assert detail_priv.status_code == 403

    # 5. Access public complaint detail (includes summary card)
    detail_pub = client.get(f"/public-complaints/{pub_id}", headers=std_headers)
    assert detail_pub.status_code == 200
    data = detail_pub.json()
    assert "summary_card" in data
    assert data["summary_card"]["status"] is not None

    # 6. Student joins public complaint
    join_res = client.post(f"/public-complaints/{pub_id}/join", json={"room_note": "Room A-204 also out"}, headers=std_headers)
    assert join_res.status_code == 200
    assert join_res.json()["affected_count"] >= 1

    # 7. Student joins same public complaint twice -> 409 Conflict
    join_again = client.post(f"/public-complaints/{pub_id}/join", json={}, headers=std_headers)
    assert join_again.status_code == 409

    # 8. Mark complaint resolved by admin then close it, then attempt join -> 400 Bad Request
    client.post(f"/complaints/{pub_id}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=admin_headers)
    resolve_res = client.post(f"/complaints/{pub_id}/resolve", json={"notes": "Power restored."}, headers=admin_headers)
    assert resolve_res.status_code == 200
    client.post(f"/complaints/{pub_id}/close", json={}, headers=std_headers)
    join_closed = client.post(f"/public-complaints/{pub_id}/join", json={}, headers=std_headers)
    assert join_closed.status_code == 400
