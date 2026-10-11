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

def _get_admin_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "gowthamejjurothu@gmail.com", "password": "Admin@123"})
    if login_res.status_code != 200:
        pytest.fail(f"Admin login failed: {login_res.text}")
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def _get_app_manager_headers():
    _reset_limiter()
    admin_headers = _get_admin_headers()
    uid = uuid.uuid4().hex[:6]
    email = f"mgr_{uid}@campuspulse.edu"
    pwd = "AppManager@123"
    
    # Create app manager
    create_res = client.post("/users", json={
        "name": "Test App Manager",
        "email": email,
        "password": pwd,
        "role": "app_manager"
    }, headers=admin_headers)
    assert create_res.status_code == 201
    
    # Login as app manager
    login_res = client.post("/auth/login", json={"username": email, "password": pwd})
    token = login_res.json()["access_token"]
    app_headers = {"Authorization": f"Bearer {token}"}

    # Change password to complete first_login requirement
    new_pwd = "NewAppManagerPass123!"
    change_res = client.post("/auth/change-password", json={
        "current_password": pwd,
        "new_password": new_pwd
    }, headers=app_headers)
    
    # Re-login with new password
    login_res2 = client.post("/auth/login", json={"username": email, "password": new_pwd})
    token2 = login_res2.json()["access_token"]
    return {"Authorization": f"Bearer {token2}"}, email


# 1. Dynamic Student Location Editing
def test_dynamic_location_update():
    admin_headers = _get_admin_headers()
    
    # Get available locations
    loc_res = client.get("/locations", headers=admin_headers)
    locations = loc_res.json()
    if not locations or len(locations) < 2:
        loc1_res = client.post("/locations", json={"name": "Test Hostel Block 1", "type": "hostel"}, headers=admin_headers)
        loc2_res = client.post("/locations", json={"name": "Test Hostel Block 2", "type": "hostel"}, headers=admin_headers)
        loc1 = loc1_res.json()["location_id"]
        loc2 = loc2_res.json()["location_id"]
    else:
        loc1 = locations[0]["location_id"]
        loc2 = locations[1]["location_id"]

    uid = uuid.uuid4().hex[:6]
    email = f"std_loc_{uid}@campuspulse.edu"
    
    # Create student with loc1
    res = client.post("/users", json={
        "name": "Dynamic Loc Student",
        "email": email,
        "role": "student",
        "roll_number": f"ROLL_LOC_{uid}",
        "department_id": "DEPT_ELECTRICAL",
        "location_id": loc1
    }, headers=admin_headers)
    assert res.status_code == 201, res.text
    user_data = res.json()
    user_id = user_data["user_id"]
    assert user_data["location_id"] == loc1

    # Update location to loc2
    update_res = client.patch(f"/users/{user_id}", json={
        "location_id": loc2
    }, headers=admin_headers)
    assert update_res.status_code == 200, update_res.text
    assert update_res.json()["location_id"] == loc2

    # Fetch user details to verify persistence
    get_res = client.get(f"/users/{user_id}", headers=admin_headers)
    assert get_res.status_code == 200
    assert get_res.json()["location_id"] == loc2


# 2. Reactivation Hierarchy Enforcement
def test_reactivation_hierarchy_rule():
    admin_headers = _get_admin_headers()
    app_mgr_headers, mgr_email = _get_app_manager_headers()
    
    uid = uuid.uuid4().hex[:6]
    target_email = f"target_deact_{uid}@campuspulse.edu"
    
    # Create user
    res = client.post("/users", json={
        "name": "Target User",
        "email": target_email,
        "role": "coordinator"
    }, headers=admin_headers)
    assert res.status_code == 201
    user_id = res.json()["user_id"]

    # Administrator deactivates the user account
    deact_res = client.patch(f"/users/{user_id}/status", json={"status": "Inactive"}, headers=admin_headers)
    assert deact_res.status_code == 200
    assert deact_res.json()["active"] is False
    assert deact_res.json()["deactivated_by_role"] == "administrator"

    # App Manager attempts to reactivate the account -> Should be 403 Forbidden
    react_res = client.patch(f"/users/{user_id}/status", json={"status": "Active"}, headers=app_mgr_headers)
    assert react_res.status_code == 403
    assert "deactivated by an Administrator" in react_res.json()["detail"] or "Only an Administrator can reactivate" in react_res.json()["detail"]

    # Administrator reactivates the account -> Success
    admin_react_res = client.patch(f"/users/{user_id}/status", json={"status": "Active"}, headers=admin_headers)
    assert admin_react_res.status_code == 200
    assert admin_react_res.json()["active"] is True


# 3. Self-Deletion Protection
def test_self_deletion_blocked():
    admin_headers = _get_admin_headers()
    
    # Get admin user info from /auth/me
    me_res = client.get("/auth/me", headers=admin_headers)
    assert me_res.status_code == 200
    admin_id = me_res.json()["user_id"]

    # Attempt to soft delete own admin account -> Should fail 400
    del_res = client.delete(f"/users/{admin_id}", headers=admin_headers)
    assert del_res.status_code == 400
    assert "cannot delete your own account" in del_res.json()["detail"]


# 4. User Recycle Bin & 30-Day Restoration
def test_recycle_bin_and_restoration():
    admin_headers = _get_admin_headers()
    uid = uuid.uuid4().hex[:6]
    email = f"recycle_{uid}@campuspulse.edu"

    # 1. Create a user
    res = client.post("/users", json={
        "name": "Restorable User",
        "email": email,
        "role": "coordinator"
    }, headers=admin_headers)
    assert res.status_code == 201
    user_id = res.json()["user_id"]

    # 2. Deactivate first (required for deletion)
    client.patch(f"/users/{user_id}/status", json={"status": "Inactive"}, headers=admin_headers)

    # 3. Soft delete the user
    del_res = client.delete(f"/users/{user_id}", headers=admin_headers)
    assert del_res.status_code == 200

    # 4. List Recycle Bin -> list of soft deleted users
    bin_res = client.get("/users/recycle-bin", headers=admin_headers)
    assert bin_res.status_code == 200
    bin_users = bin_res.json()
    found = [u for u in bin_users if u["user_id"] == user_id]
    assert len(found) == 1
    assert found[0]["deleted_by"] is not None

    # 5. Restore user account
    restore_res = client.post(f"/users/{user_id}/restore", headers=admin_headers)
    assert restore_res.status_code == 200
    assert restore_res.json()["is_deleted"] is False
    assert restore_res.json()["active"] is True

    # 6. Verify user is back in active users list
    list_res = client.get(f"/users/{user_id}", headers=admin_headers)
    assert list_res.status_code == 200
    assert list_res.json()["is_deleted"] is False


# 5. Multi-Filter Engine
def test_multi_filter_users():
    admin_headers = _get_admin_headers()
    uid = uuid.uuid4().hex[:6]
    email = f"filter_std_{uid}@campuspulse.edu"

    # Create student with specific program and department
    create_res = client.post("/users", json={
        "name": "Filter Test Student",
        "email": email,
        "role": "student",
        "roll_number": f"ROLL_F_{uid}",
        "department_id": "DEPT_ELECTRICAL",
        "program": "B.Tech",
        "year": "3"
    }, headers=admin_headers)
    assert create_res.status_code == 201, create_res.text

    # Filter by program
    p_res = client.get("/users?program=B.Tech", headers=admin_headers)
    assert p_res.status_code == 200
    assert any(u["email"] == email for u in p_res.json())

    # Filter by department
    d_res = client.get("/users?department_id=DEPT_ELECTRICAL", headers=admin_headers)
    assert d_res.status_code == 200
    assert any(u["email"] == email for u in d_res.json())


# 6. User List CSV & XLSX Export
def test_user_export_formats():
    admin_headers = _get_admin_headers()

    # CSV Export
    csv_res = client.get("/users/export?format=csv", headers=admin_headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers["content-type"]
    assert "User ID,Name,Email,Role" in csv_res.text

    # XLSX Export
    xlsx_res = client.get("/users/export?format=xlsx", headers=admin_headers)
    assert xlsx_res.status_code == 200
    assert "spreadsheetml" in xlsx_res.headers["content-type"]
    assert len(xlsx_res.content) > 0


# 7. Download Sample Excel & CSV Import Templates
def test_sample_template_download():
    admin_headers = _get_admin_headers()

    # CSV Template
    csv_tmpl = client.get("/users/import/sample-template?format=csv", headers=admin_headers)
    assert csv_tmpl.status_code == 200
    assert "Name,Email,Roll Number,Role" in csv_tmpl.text
    # Ensure no escalation fields in sample template
    assert "Escalation To" not in csv_tmpl.text

    # XLSX Template
    xlsx_tmpl = client.get("/users/import/sample-template?format=xlsx", headers=admin_headers)
    assert xlsx_tmpl.status_code == 200
    assert len(xlsx_tmpl.content) > 0
