import os
import sys
import uuid
import pytest
from datetime import datetime, timedelta

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


def _login(username, password):
    _reset_limiter()
    res = client.post("/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, f"Login failed for {username}: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="module")
def admin_headers():
    return _login("admin@example.com", "Admin@123")


@pytest.fixture(scope="module")
def app_mgr_headers():
    return _login("manager@example.com", "Manager@123")


@pytest.fixture(scope="module")
def coord_headers():
    return _login("coordinator@example.com", "Coord@123")


@pytest.fixture(scope="module")
def warden_headers():
    return _login("warden@example.com", "Warden@123")


def _create_user(admin_headers, role, email_prefix, location_id=None, department_id=None):
    uid = uuid.uuid4().hex[:8]
    email = f"{email_prefix}_{uid}@example.com"
    payload = {
        "name": f"User {uid}",
        "email": email,
        "role": role,
        "password": "Temp@Pass123",
        "confirm_password": "Temp@Pass123",
    }
    if location_id:
        payload["location_id"] = location_id
    if department_id:
        payload["department_id"] = department_id
    res = client.post("/users", json=payload, headers=admin_headers)
    assert res.status_code == 201, res.text

    headers = _login(email, "Temp@Pass123")
    res2 = client.post(
        "/auth/change-password",
        json={
            "old_password": "Temp@Pass123",
            "new_password": "Perm@Pass456",
            "confirm_password": "Perm@Pass456",
        },
        headers=headers,
    )
    assert res2.status_code == 200, res2.text
    return _login(email, "Perm@Pass456"), res.json()


def test_language_update(admin_headers):
    student_headers, s_data = _create_user(admin_headers, "Student", "p5_lang")

    # Invalid language code
    res = client.put("/users/me/language", json={"language": "fr"}, headers=student_headers)
    assert res.status_code == 422

    # Valid language 'te'
    res = client.put("/users/me/language", json={"language": "te"}, headers=student_headers)
    assert res.status_code == 200
    assert res.json()["language"] == "te"

    # Profile reflects language
    me_res = client.get("/auth/me", headers=student_headers)
    assert me_res.status_code == 200
    assert me_res.json()["language"] == "te"


def test_exact_spot_and_frequent_spots(admin_headers):
    student_headers, s_data = _create_user(
        admin_headers, "Student", "p5_spot", location_id="LOC_HOSTEL_1", department_id="DEPT_HOSTEL_ELECTRICAL"
    )

    spot_name = f"Corridor Spot {uuid.uuid4().hex[:6]}"

    # Create 5 complaints with distinct titles/descriptions at the same exact_spot
    for i in range(5):
        res = client.post(
            "/complaints",
            json={
                "title": f"Electrical Issue #{i} at {spot_name}",
                "description": f"Unique details for incident occurrence #{i} in the hallway.",
                "location_id": "LOC_HOSTEL_1",
                "department_id": "DEPT_HOSTEL_ELECTRICAL",
                "category": "electrical",
                "exact_spot": spot_name,
            },
            headers=student_headers,
        )
        assert res.status_code == 201, res.text
        if i == 0:
            assert res.json()["exact_spot"] == spot_name

    # Check frequent spots endpoint
    freq_res = client.get("/locations/frequent-spots", headers=admin_headers)
    assert freq_res.status_code == 200
    spots = freq_res.json()
    match = [s for s in spots if s["exact_spot"] == spot_name]
    assert len(match) == 1
    assert match[0]["count"] >= 5

    # One-tap create child location from spot
    child_res = client.post(
        "/locations/create-from-spot",
        json={"location_id": "LOC_HOSTEL_1", "exact_spot": spot_name},
        headers=admin_headers,
    )
    assert child_res.status_code == 201
    child_loc = child_res.json()
    assert spot_name in child_loc["name"]


def test_complaint_feedback(admin_headers, coord_headers, warden_headers):
    student_headers, s_data = _create_user(
        admin_headers, "Student", "p5_fb", location_id="LOC_HOSTEL_1", department_id="DEPT_HOSTEL_ELECTRICAL"
    )

    create_res = client.post(
        "/complaints",
        json={
            "title": f"Switch board fault {uuid.uuid4().hex[:4]}",
            "description": "Danger of electric shock in study room",
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "electrical",
        },
        headers=student_headers,
    )
    assert create_res.status_code == 201
    cmp_id = create_res.json()["complaint_id"]

    # Trying feedback before closure should fail
    fb_res = client.post(
        f"/complaints/{cmp_id}/feedback",
        json={"rating": 5, "thank_you_note": "Great job"},
        headers=student_headers,
    )
    assert fb_res.status_code == 400

    # Coordinator assigns and resolves
    client.post(f"/complaints/{cmp_id}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=coord_headers)
    client.put(
        f"/complaints/{cmp_id}/resolve",
        json={"skip_photo": True, "notes": "Switch replaced successfully."},
        headers=coord_headers,
    )

    # Check status: if pending warden, warden verifies
    cmp_status = client.get(f"/complaints/{cmp_id}", headers=student_headers).json()["status"]
    if cmp_status == "Pending Warden Verification":
        client.post(
            f"/complaints/{cmp_id}/warden-verify",
            json={"approved": True, "notes": "Verified in person."},
            headers=warden_headers,
        )

    # Student confirms/closes
    close_res = client.post(f"/complaints/{cmp_id}/confirm", headers=student_headers)
    assert close_res.status_code == 200

    # Now feedback must succeed
    fb_ok = client.post(
        f"/complaints/{cmp_id}/feedback",
        json={"rating": 5, "thank_you_note": "Thank you so much for fixing it fast!"},
        headers=student_headers,
    )
    assert fb_ok.status_code == 201
    assert fb_ok.json()["rating"] == 5

    # Duplicate feedback by same student must fail
    fb_dup = client.post(
        f"/complaints/{cmp_id}/feedback",
        json={"rating": 4},
        headers=student_headers,
    )
    assert fb_dup.status_code == 400

    # Retrieve feedback
    get_res = client.get(f"/complaints/{cmp_id}/feedback", headers=student_headers)
    assert get_res.status_code == 200
    assert len(get_res.json()) >= 1


def test_fixer_of_the_month_and_badges(admin_headers):
    student_headers, _ = _create_user(admin_headers, "Student", "p5_rec_stu")

    # Staff view: returns full leaderboard
    staff_res = client.get("/recognitions/fixer-of-the-month", headers=admin_headers)
    assert staff_res.status_code == 200
    assert "leaderboard" in staff_res.json()
    assert not staff_res.json()["is_student_view"]

    # Student view: returns only winner, leaderboard is empty
    stu_res = client.get("/recognitions/fixer-of-the-month", headers=student_headers)
    assert stu_res.status_code == 200
    assert stu_res.json()["is_student_view"]
    assert stu_res.json()["leaderboard"] == []

    # Badges endpoint
    badges_res = client.get("/recognitions/badges", headers=admin_headers)
    assert badges_res.status_code == 200
    assert "badges" in badges_res.json()


def test_campus_health_map(admin_headers):
    student_headers, _ = _create_user(admin_headers, "Student", "p5_hm_stu")

    # Admin view
    admin_hm = client.get("/dashboard/health-map", headers=admin_headers)
    assert admin_hm.status_code == 200
    data = admin_hm.json()
    assert "summary" in data
    assert "locations" in data

    # Student view blocked by default
    stu_hm = client.get("/dashboard/health-map", headers=student_headers)
    assert stu_hm.status_code == 403


def test_safety_reports_lifecycle(admin_headers):
    student_headers, _ = _create_user(admin_headers, "Student", "p5_safe_stu")

    # 1. Disabled by default
    res = client.post(
        "/safety-reports",
        json={"category": "Hostel Security", "description": "Broken perimeter fence"},
        headers=student_headers,
    )
    assert res.status_code == 403

    # 2. Enable safety reports via put setting key
    enable_res = client.put(
        "/settings/key/safety_reports_enabled",
        json={"setting_value": "true", "reason": "Enable for pilot testing"},
        headers=admin_headers,
    )
    assert enable_res.status_code == 200

    # 3. Submit anonymous safety report
    submit_res = client.post(
        "/safety-reports",
        json={"category": "Hostel Security", "description": "Broken perimeter fence near Gate 4"},
        headers=student_headers,
    )
    assert submit_res.status_code == 201
    data = submit_res.json()
    case_code = data["case_code"]
    rep_id = data["report_id"]
    assert case_code.startswith("SAFE-")

    # 4. Administrator sees reports list (identity sealed)
    list_res = client.get("/safety-reports", headers=admin_headers)
    assert list_res.status_code == 200
    assert any(r["case_code"] == case_code for r in list_res.json())

    # 5. Anonymous two-way chat
    admin_msg = client.post(
        f"/safety-reports/{case_code}/messages",
        json={"body": "Can you describe the location closer to Gate 4?"},
        headers=admin_headers,
    )
    assert admin_msg.status_code == 200
    assert admin_msg.json()["sender_type"] == "admin"

    stu_reply = client.post(
        f"/safety-reports/{case_code}/messages",
        json={"body": "It is behind the cycle stand."},
        headers=student_headers,
    )
    assert stu_reply.status_code == 200
    assert stu_reply.json()["sender_type"] == "reporter"

    # 6. View thread
    view_res = client.get(f"/safety-reports/{case_code}", headers=student_headers)
    assert view_res.status_code == 200
    assert len(view_res.json()["messages"]) >= 3
    assert not view_res.json()["is_revealed"]

    # 7. Non-admin cannot reveal identity
    rev_non_admin = client.post(
        f"/safety-reports/{rep_id}/reveal",
        json={"reason": "Check who reported"},
        headers=student_headers,
    )
    assert rev_non_admin.status_code in (401, 403)

    # 8. Admin cannot reveal before false_misuse outcome
    rev_early = client.post(
        f"/safety-reports/{rep_id}/reveal",
        json={"reason": "Check who reported"},
        headers=admin_headers,
    )
    assert rev_early.status_code == 400

    # 9. Admin marks outcome as false_misuse
    dec_res = client.post(
        f"/safety-reports/{rep_id}/decision",
        json={"outcome": "false_misuse", "notes": "Prank report"},
        headers=admin_headers,
    )
    assert dec_res.status_code == 200

    # 10. Admin reveals identity under false_misuse
    rev_ok = client.post(
        f"/safety-reports/{rep_id}/reveal",
        json={"reason": "Intentional false report disrupting emergency operations."},
        headers=admin_headers,
    )
    assert rev_ok.status_code == 200
    assert "reporter" in rev_ok.json()
    assert "blocked_until" in rev_ok.json()

    # 11. Reporter student is now blocked from filing future safety reports
    blocked_submit = client.post(
        "/safety-reports",
        json={"category": "Noise", "description": "Loud music"},
        headers=student_headers,
    )
    assert blocked_submit.status_code == 403
    assert "blocked" in blocked_submit.json()["detail"].lower()

