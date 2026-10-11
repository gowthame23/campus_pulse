import pytest
import sys
import os
import uuid
from datetime import datetime, timedelta

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_db_path
from middleware.rate_limiter import auth_limiter
from services.auth_service import AuthService

client = TestClient(app)

def _reset_limiter():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()
    from api.dependencies import _service_cache, get_db_path
    _service_cache.clear()
    import sqlite3
    db_p = get_db_path()
    if os.path.exists(db_p):
        try:
            conn = sqlite3.connect(db_p)
            conn.execute("DELETE FROM login_attempts")
            conn.commit()
            conn.close()
        except Exception:
            pass
    _service_cache.clear()

def _get_student_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "gowtham.e23@iiits.in", "password": "Student@123"})
    if login_res.status_code != 200:
        print("LOGIN STUDENT FAIL:", login_res.status_code, login_res.text)
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def _get_admin_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "gowthamejjurothu@gmail.com", "password": "Admin@123"})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_workflow_6_student_report_success():
    std_headers = _get_student_headers()
    uid = uuid.uuid4().hex[:6]
    payload = {
        "type": "LOST",
        "title": f"Black Wallet {uid}",
        "description": "Black leather Tommy Hilfiger wallet with student ID.",
        "location_id": "LOC_HOSTEL_A",
        "lost_date": "2026-08-05",
        "photos": ["https://example.com/photo1.jpg"]
    }
    res = client.post("/lost-found/report", json=payload, headers=std_headers)
    assert res.status_code == 201
    data = res.json()
    assert "item_id" in data
    assert data["report_type"] in ("Lost", "LOST")

def test_workflow_6_non_student_cannot_report():
    admin_headers = _get_admin_headers()
    payload = {
        "type": "FOUND",
        "title": "Found Wallet Admin Test",
        "description": "Found near main gate.",
        "location_id": "LOC_HOSTEL_A"
    }
    res = client.post("/lost-found/report", json=payload, headers=admin_headers)
    assert res.status_code == 403

def test_workflow_6_inactive_location_rejection():
    admin_headers = _get_admin_headers()
    std_headers = _get_student_headers()

    # Create inactive location
    loc_res = client.post("/locations", json={"name": f"Inactive Loc {uuid.uuid4().hex[:6]}"}, headers=admin_headers)
    loc_id = loc_res.json()["location_id"]
    client.patch(f"/locations/{loc_id}/deactivate", headers=admin_headers)

    res = client.post("/lost-found/report", json={
        "type": "LOST",
        "title": "Lost keys in inactive loc",
        "description": "Keychain with blue strap.",
        "location_id": loc_id
    }, headers=std_headers)
    assert res.status_code == 400
    assert "inactive" in res.json()["detail"].lower()

def test_workflow_6_future_date_rejection():
    std_headers = _get_student_headers()
    future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    res = client.post("/lost-found/report", json={
        "type": "LOST",
        "title": "Lost item future date",
        "description": "Testing future date check.",
        "location_id": "LOC_HOSTEL_A",
        "lost_date": future_date
    }, headers=std_headers)
    assert res.status_code == 400
    assert "future" in res.json()["detail"].lower()

def test_workflow_6_matches_returns_array():
    std_headers = _get_student_headers()
    uid = uuid.uuid4().hex[:6]

    # 1. Report Lost item
    lost_res = client.post("/lost-found/report", json={
        "type": "LOST",
        "title": f"Blue Water Bottle {uid}",
        "description": "Milton stainless steel bottle.",
        "location_id": "LOC_HOSTEL_A"
    }, headers=std_headers)
    lost_id = lost_res.json()["item_id"]

    # 2. Get matches
    match_res = client.get(f"/lost-found/matches/{lost_id}", headers=std_headers)
    assert match_res.status_code == 200
    assert isinstance(match_res.json(), list)

def test_workflow_6_full_mark_returned():
    std_headers = _get_student_headers()
    admin_headers = _get_admin_headers()
    uid = uuid.uuid4().hex[:6]

    # 1. Student A reports Found item
    found_res = client.post("/lost-found/report", json={
        "type": "FOUND",
        "title": f"Found Watch {uid}",
        "description": "Silver Fastrack watch found near mess hall.",
        "location_id": "LOC_HOSTEL_A"
    }, headers=std_headers)
    found_id = found_res.json()["item_id"]

    # 2. Claim submission is disabled -> returns 400
    claim_res = client.post(f"/lost-found/{found_id}/claim", json={
        "claim_reason": "It belongs to me",
        "proof_description": "Scratch on back cover"
    }, headers=std_headers)
    assert claim_res.status_code == 400
    assert "disabled" in claim_res.json()["detail"].lower()

    # 3. Item marked returned by owner or admin
    ret_res = client.post(f"/lost-found/{found_id}/return", json={}, headers=admin_headers)
    assert ret_res.status_code == 200
    assert ret_res.json()["status"] in ("Returned", "Closed")

def test_workflow_6_security_ownership_authorization():
    import sqlite3
    uid = uuid.uuid4().hex[:6]

    # Student A headers
    _reset_limiter()
    res_a = client.post("/auth/login", json={"username": "gowtham.e23@iiits.in", "password": "Student@123"})
    std_a_headers = {"Authorization": f"Bearer {res_a.json()['access_token']}"}

    # Student B setup (create student B and set is_first_login = 0)
    admin_headers = _get_admin_headers()
    u_res = client.post("/users", json={
        "name": f"Student B {uid}",
        "email": f"studentb_{uid}@iiits.in",
        "password": "Student@123",
        "role": "student"
    }, headers=admin_headers)
    assert u_res.status_code == 201
    user_b_id = u_res.json()["user_id"]

    conn = sqlite3.connect(get_db_path())
    conn.execute("UPDATE users SET first_login = 0 WHERE user_id = ?", (user_b_id,))
    conn.commit()
    conn.close()

    _reset_limiter()
    res_b = client.post("/auth/login", json={"username": f"studentb_{uid}@iiits.in", "password": "Student@123"})
    assert res_b.status_code == 200
    std_b_headers = {"Authorization": f"Bearer {res_b.json()['access_token']}"}

    # A & G: Student A creates Item A (Lost post)
    create_res = client.post("/lost-found/report", json={
        "type": "LOST",
        "title": f"Security Test Item {uid}",
        "description": "Calculated item for security boundary test.",
        "location_id": "LOC_HOSTEL_A"
    }, headers=std_a_headers)
    assert create_res.status_code == 201
    item_a_id = create_res.json()["item_id"]

    # Student A uploads image for Item A
    img_res = client.post(f"/lost-found/items/{item_a_id}/images", json={
        "image_url": "https://example.com/item_a.jpg",
        "image_type": "Overview"
    }, headers=std_a_headers)
    assert img_res.status_code == 201
    img_id = img_res.json()["image_id"]

    # H: Users can view Lost & Found info
    get_res = client.get(f"/lost-found/items/{item_a_id}", headers=std_b_headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == f"Security Test Item {uid}"

    # D: Student B CANNOT update Item A -> 403 Forbidden
    upd_b = client.put(f"/lost-found/items/{item_a_id}", json={"title": "Hacked Title"}, headers=std_b_headers)
    assert upd_b.status_code == 403

    # F: Student B CANNOT delete Student A's images -> 403 Forbidden
    del_img_b = client.delete(f"/lost-found/images/{img_id}", headers=std_b_headers)
    assert del_img_b.status_code == 403

    # E: Student B CANNOT delete Item A -> 403 Forbidden
    del_b = client.delete(f"/lost-found/items/{item_a_id}", headers=std_b_headers)
    assert del_b.status_code == 403

    # I: Claim submission is disabled -> returns 400 Bad Request
    claim_b = client.post(f"/lost-found/{item_a_id}/claim", json={
        "claim_reason": "I lost this exact item last week",
        "proof_description": "SerialNumber 12345"
    }, headers=std_b_headers)
    assert claim_b.status_code == 400

    # B: Student A CAN update Item A
    upd_a = client.put(f"/lost-found/items/{item_a_id}", json={"title": f"Updated Title {uid}"}, headers=std_a_headers)
    assert upd_a.status_code == 200
    assert upd_a.json()["title"] == f"Updated Title {uid}"

    # Student A CAN delete image
    del_img_a = client.delete(f"/lost-found/images/{img_id}", headers=std_a_headers)
    assert del_img_a.status_code == 200

    # C & J & L: Student A CAN delete Item A
    del_a = client.delete(f"/lost-found/items/{item_a_id}", headers=std_a_headers)
    assert del_a.status_code == 200
