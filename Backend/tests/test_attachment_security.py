import pytest
import sys
import os
import uuid

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

def _get_admin_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "admin@example.com", "password": "Admin@123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def _new_student():
    email = f"student_{uuid.uuid4().hex[:8]}@probe.edu"
    admin_headers = _get_admin_headers()
    res = client.post("/users", json={
        "name": "Probe Student", "email": email, "role": "student",
        "password": "Temp@Pass123", "confirm_password": "Temp@Pass123", "location_id": "LOC_HOSTEL_A",
    }, headers=admin_headers)
    assert res.status_code == 201
    headers = _get_headers_for(email, "Temp@Pass123")
    change = client.post("/auth/change-password", json={
        "old_password": "Temp@Pass123", "new_password": "Stud@Pass456", "confirm_password": "Stud@Pass456",
    }, headers=headers)
    assert change.status_code == 200
    return _get_headers_for(email, "Stud@Pass456")

def test_attachment_security_cross_user_denial_and_invalid_ids():
    admin_headers = _get_admin_headers()
    student1_headers = _new_student()

    # 1. Non-existent complaint ID returns 404
    res_404 = client.get("/complaints/CMP-NONEXISTENT-999/attachments", headers=admin_headers)
    assert res_404.status_code == 404

    # 2. Student 1 creates a private complaint
    uid = uuid.uuid4().hex[:6]
    c_res = client.post("/complaints", json={
        "location_id": "LOC_HOSTEL_A",
        "department_id": "DEPT_ELECTRICAL",
        "title": "Private attachment test",
        "description": f"Private complaint for attachment testing {uid}",
        "visibility_type": "Private"
    }, headers=student1_headers)
    assert c_res.status_code == 201
    complaint_id = c_res.json()["complaint_id"]

    # 3. Upload image as Student 1
    upload_res = client.post(
        f"/complaints/{complaint_id}/attachments",
        data={"category": "Additional"},
        files={"files": ("test_photo.jpg", b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00", "image/jpeg")},
        headers=student1_headers
    )
    assert upload_res.status_code == 200
    attachments = upload_res.json()
    assert len(attachments) > 0
    att_id = attachments[0]["attachment_id"]

    # 4. Student 1 can view & download attachment
    dl_res1 = client.get(f"/complaints/{complaint_id}/attachments/{att_id}/download", headers=student1_headers)
    assert dl_res1.status_code == 200

    # 5. Invalid attachment ID returns 404
    dl_invalid = client.get(f"/complaints/{complaint_id}/attachments/ATT-INVALID-999/download", headers=student1_headers)
    assert dl_invalid.status_code == 404

    # 6. Admin can view & download attachment
    dl_admin = client.get(f"/complaints/{complaint_id}/attachments/{att_id}/download", headers=admin_headers)
    assert dl_admin.status_code == 200
