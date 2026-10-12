import pytest
import sys
import os
import io

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import db_path
from middleware.rate_limiter import auth_limiter
from services.auth_service import AuthService

client = TestClient(app)
auth_service = AuthService(db_path=db_path)

def _reset_limiter():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()

def _get_admin_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "admin@example.com", "password": "Admin@123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def _get_student_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "student@example.com", "password": "Student@123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

import uuid

def test_workflow_2_student_creation_success():
    headers = _get_admin_headers()
    uid = uuid.uuid4().hex[:6]
    payload = {
        "name": "New Test Student",
        "email": f"std_{uid}@campuspulse.edu",
        "role": "student",
        "roll_number": f"ROLL_{uid}",
        "department_id": "DEPT_ELECTRICAL",
        "hostel": "Hostel Block A"
    }
    res = client.post("/users", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert "temporary_password" in data
    assert data["role"] == "student"
    assert data["first_login"] is True

def test_workflow_2_duplicate_roll_number_fails():
    headers = _get_admin_headers()
    uid = uuid.uuid4().hex[:6]
    roll = f"ROLL_DUP_{uid}"
    # Create first
    client.post("/users", json={
        "name": "Original Student",
        "email": f"orig_{uid}@campuspulse.edu",
        "role": "student",
        "roll_number": roll,
        "department_id": "DEPT_ELECTRICAL"
    }, headers=headers)

    # Try creating second with same roll number
    payload = {
        "name": "Duplicate Student",
        "email": f"dup_{uid}@campuspulse.edu",
        "role": "student",
        "roll_number": roll,
        "department_id": "DEPT_ELECTRICAL"
    }
    res = client.post("/users", json=payload, headers=headers)
    assert res.status_code == 400
    assert "Roll Number must be unique" in res.json()["detail"] or "already exists" in res.json()["detail"]

def test_workflow_2_staff_creation_success():
    headers = _get_admin_headers()
    uid = uuid.uuid4().hex[:6]
    payload = {
        "name": "New Test Warden",
        "email": "warden_" + uid + "@campuspulse.edu",
        "role": "location_in_charge",
        "employee_id": "EMP_W_" + uid,
        "location_id": "LOC_HOSTEL_A"
    }
    res = client.post("/users", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert "temporary_password" in data
    assert data["role"] == "location_in_charge"

def test_workflow_2_non_admin_cannot_create_user():
    headers = _get_student_headers()
    uid = uuid.uuid4().hex[:6]
    payload = {
        "name": "Unauthorized Student",
        "email": f"unauth_{uid}@campuspulse.edu",
        "role": "student",
        "roll_number": f"ROLL_UNAUTH_{uid}"
    }
    res = client.post("/users", json=payload, headers=headers)
    assert res.status_code == 403

def test_workflow_2_deactivation_blocks_login():
    admin_headers = _get_admin_headers()
    uid = uuid.uuid4().hex[:6]
    email = f"deact_{uid}@campuspulse.edu"
    res = client.post("/users", json={
        "name": "Deactivation Login Test",
        "email": email,
        "role": "student",
        "roll_number": f"ROLL_DEACT_{uid}",
        "department_id": "DEPT_ELECTRICAL"
    }, headers=admin_headers)
    user_data = res.json()
    user_id = user_data["user_id"]
    temp_pw = user_data["temporary_password"]

    # Deactivate user
    deact_res = client.patch(f"/users/{user_id}/status", json={"status": "Inactive"}, headers=admin_headers)
    assert deact_res.status_code == 200

    # Try login -> must return 403 Forbidden
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": email, "password": temp_pw})
    assert login_res.status_code == 403
    assert "deactivated" in login_res.json()["detail"].lower()

def test_workflow_2_excel_import():
    headers = _get_admin_headers()
    uid = uuid.uuid4().hex[:6]
    csv_content = (
        "name,email,role,roll_number,employee_id,department_id,location_id\n"
        f"Import Student 1,imp_std1_{uid}@campuspulse.edu,student,ROLL_IMP1_{uid},,DEPT_ELECTRICAL,\n"
        f"Import Staff 1,imp_stf1_{uid}@campuspulse.edu,location_in_charge,,EMP_IMP1_{uid},,LOC_HOSTEL_A\n"
        f"Invalid Duplicate Student,imp_std1_{uid}@campuspulse.edu,student,ROLL_IMP1_{uid},,DEPT_ELECTRICAL,\n"
    )
    files = {"file": ("test_import.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
    res = client.post("/users/import", files=files, headers=headers)
    assert res.status_code == 200
    report = res.json()
    assert report["total_rows"] == 3
    assert report["success_count"] == 2
    assert report["failed_count"] == 1
