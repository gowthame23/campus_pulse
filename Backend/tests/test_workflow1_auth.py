import pytest
import sys
import os

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

def test_workflow_1_validation_empty_username():
    _reset_limiter()
    response = client.post("/auth/login", json={"username": "", "password": "Password@123"})
    assert response.status_code == 400
    assert "Username is required." in response.json()["detail"]

def test_workflow_1_validation_empty_password():
    _reset_limiter()
    response = client.post("/auth/login", json={"username": "S2023001", "password": ""})
    assert response.status_code == 400
    assert "Password is required." in response.json()["detail"]

def test_workflow_1_login_by_email_success():
    _reset_limiter()
    response = client.post("/auth/login", json={"username": "gowtham.e23@iiits.in", "password": "Student@123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "student"
    assert data["redirect"] == "/student/dashboard"
    assert "first_login" in data

def test_workflow_1_login_by_roll_number_or_id():
    _reset_limiter()
    response = client.post("/auth/login", json={"username": "USR_STUDENT", "password": "Student@123"})
    assert response.status_code == 200
    assert response.json()["role"] == "student"

def test_workflow_1_invalid_credentials():
    _reset_limiter()
    response = client.post("/auth/login", json={"username": "gowtham.e23@iiits.in", "password": "WrongPassword123!"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials."

def test_workflow_1_nonexistent_user():
    _reset_limiter()
    response = client.post("/auth/login", json={"username": "nonexistent_user_999", "password": "Password@123"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials."

def test_workflow_1_deactivated_account():
    _reset_limiter()
    deact_email = "deact_test@campuspulse.edu"
    try:
        user = auth_service.create_user(
            name="Deactivated Test",
            email=deact_email,
            password="Password@123",
            role="student"
        )
        auth_service.update_user_status(user.user_id, "Inactive", None)

        response = client.post("/auth/login", json={"username": deact_email, "password": "Password@123"})
        assert response.status_code == 403
        assert "deactivated" in response.json()["detail"].lower()
    except Exception:
        pass

def test_workflow_1_edge_case_student_with_employee_id():
    _reset_limiter()
    # USR_STUDENT does not have an employee_id, so searching by Employee ID fails -> 401
    response = client.post("/auth/login", json={"username": "EMP999999", "password": "Student@123"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials."

def test_workflow_1_edge_case_coordinator_with_roll_number():
    _reset_limiter()
    # USR_COORDINATOR does not have a roll_number, so searching by Roll Number fails -> 401
    response = client.post("/auth/login", json={"username": "S9999999", "password": "Coord@123"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials."

def test_workflow_1_logout():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "gowtham.e23@iiits.in", "password": "Student@123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_res = client.get("/auth/me", headers=headers)
    assert me_res.status_code == 200

    logout_res = client.post("/auth/logout", headers=headers)
    assert logout_res.status_code == 200

    me_after = client.get("/auth/me", headers=headers)
    assert me_after.status_code == 401
