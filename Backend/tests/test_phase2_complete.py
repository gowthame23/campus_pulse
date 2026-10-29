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
from core.constants import (
    AFFECTED_PRIORITY_THRESHOLD,
    PHOTO_SKIP_STREAK_LIMIT,
    STATUS_ADMIN_REVIEW,
    STATUS_ASSIGNED,
    STATUS_AUTO_CLOSED,
    STATUS_CLOSED,
    STATUS_IN_PROGRESS,
    STATUS_PENDING_WARDEN,
    STATUS_REOPENED,
    STATUS_WAITING_STUDENT,
)

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
    try:
        return _login("gowthamejjurothu15@gmail.com", "Coord@123")
    except Exception:
        return _login("coordinator@example.com", "Coord@123")


@pytest.fixture(scope="module")
def warden_headers():
    try:
        return _login("naveen@campus.edu", "Warden@123")
    except Exception:
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


def _upload_image(cid, headers, category="After Repair"):
    return client.post(
        f"/complaints/{cid}/attachments",
        data={"category": category, "source": "camera", "kind": "after"},
        files={"files": ("proof.jpg", b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00fixed_content", "image/jpeg")},
        headers=headers,
    )


def test_photo_skip_streak_and_forced_check(admin_headers, coord_headers, warden_headers):
    student_headers, student_data = _create_user(
        admin_headers, "student", "std_photo", location_id="LOC_HOSTEL_1"
    )

    # Clean streak for test isolation
    from api.dependencies import get_auth_service
    auth_service = get_auth_service()
    coord_user = auth_service.get_user("USR_COORDINATOR")
    coord_user.photo_skip_streak = 0
    coord_user.force_next_warden_check = 0
    auth_service.save_user(coord_user)

    # Job 1: with student photo, coordinator skips
    c1 = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "electrical",
            "title": "Streak 1 photo job",
            "description": "Exposed socket with photo",
            "visibility_type": "Private",
            "priority": "Medium",
            "attachment_url": "/static/uploads/socket.jpg",
        },
        headers=student_headers,
    ).json()["complaint_id"]

    client.post(f"/complaints/{c1}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=coord_headers)
    res_skip1 = client.put(
        f"/complaints/{c1}/resolve",
        json={"skip_photo": True, "notes": "Socket fixed, no after photo needed."},
        headers=coord_headers,
    )
    assert res_skip1.status_code == 200, res_skip1.text
    coord_user = auth_service.get_user("USR_COORDINATOR")
    assert coord_user.photo_skip_streak == 1

    # Job 2: with student photo, coordinator skips again -> streak reaches limit (2)
    c2 = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "electrical",
            "title": "Streak 2 photo job",
            "description": "Switch spark with photo",
            "visibility_type": "Private",
            "priority": "Medium",
            "attachment_url": "/static/uploads/switch.jpg",
        },
        headers=student_headers,
    ).json()["complaint_id"]

    client.post(f"/complaints/{c2}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=coord_headers)
    res_skip2 = client.put(
        f"/complaints/{c2}/resolve",
        json={"skip_photo": True, "notes": "Replaced switch."},
        headers=coord_headers,
    )
    assert res_skip2.status_code == 200, res_skip2.text
    coord_user = auth_service.get_user("USR_COORDINATOR")
    assert coord_user.photo_skip_streak == 2
    assert coord_user.force_next_warden_check == 1

    # Job 3: with student photo, attempting to skip without typed reason -> 400
    c3 = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "electrical",
            "title": "Streak 3 photo job",
            "description": "Damaged wire",
            "visibility_type": "Private",
            "priority": "Medium",
            "attachment_url": "/static/uploads/wire.jpg",
        },
        headers=student_headers,
    ).json()["complaint_id"]

    client.post(f"/complaints/{c3}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=coord_headers)
    fail_skip = client.put(
        f"/complaints/{c3}/resolve",
        json={"skip_photo": True, "photo_skip_reason": ""},
        headers=coord_headers,
    )
    assert fail_skip.status_code == 400
    assert "typed reason is required" in fail_skip.json()["detail"].lower()

    # Job 3: skipping with typed reason -> succeeds and forces warden check
    ok_skip = client.put(
        f"/complaints/{c3}/resolve",
        json={"skip_photo": True, "photo_skip_reason": "Camera lens cracked on field work."},
        headers=coord_headers,
    )
    assert ok_skip.status_code == 200
    c3_data = ok_skip.json()
    assert c3_data["status"] == STATUS_PENDING_WARDEN
    assert c3_data["requires_warden_check"] is True

    # Real photo resets streak
    _upload_image(c3, coord_headers)
    # Next job with real photo
    c4 = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "electrical",
            "title": "Streak reset job",
            "description": "Bulb holder replaced",
            "visibility_type": "Private",
            "priority": "Medium",
            "attachment_url": "/static/uploads/bulb.jpg",
        },
        headers=student_headers,
    ).json()["complaint_id"]

    client.post(f"/complaints/{c4}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=coord_headers)
    _upload_image(c4, coord_headers)
    res_real = client.put(
        f"/complaints/{c4}/resolve",
        json={"notes": "Installed new holder."},
        headers=coord_headers,
    )
    assert res_real.status_code == 200
    coord_user = auth_service.get_user("USR_COORDINATOR")
    assert coord_user.photo_skip_streak == 0


def test_attachment_flags_exif_and_reused():
    from api.dependencies import get_attachment_service
    attachment_service = get_attachment_service()

    # Test OLDER_THAN_JOB flag logic
    ts_job_start = "2026-10-10 12:00:00"
    ts_old_photo = "2026-10-09 10:00:00"
    flags = attachment_service.detect_flags(
        content_bytes=b"unique_content_1",
        exif_taken_at=ts_old_photo,
        job_started_at=ts_job_start,
        complaint_id="CMP-TEST-1",
    )
    assert "OLDER_THAN_JOB" in flags

    # Test REUSED flag logic
    flags_reused = attachment_service.detect_flags(
        content_bytes=b"unique_content_1",
        sha256_hash="reused_test_hash_val",
        matching_other_complaint="CMP-TEST-2",
    )
    assert "REUSED" in flags_reused


def test_warden_verification_flow_and_photo_mismatch(admin_headers, coord_headers, warden_headers):
    student_headers, student_data = _create_user(
        admin_headers, "student", "std_wflow", location_id="LOC_HOSTEL_1"
    )

    c = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "electrical",
            "title": "Warden verify flow ticket",
            "description": "High priority circuit issue",
            "visibility_type": "Private",
            "priority": "High",
        },
        headers=student_headers,
    ).json()["complaint_id"]

    client.post(f"/complaints/{c}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=coord_headers)
    client.put(f"/complaints/{c}/resolve", json={"notes": "Checked wiring."}, headers=coord_headers)

    # 1. Reject by warden -> moves back to In Progress with unchanged deadline
    orig_deadline = client.get(f"/complaints/{c}", headers=admin_headers).json()["sla_deadline"]
    rej_res = client.post(
        f"/complaints/{c}/warden-verify",
        json={"approved": False, "notes": "Loose screws visible on inspection."},
        headers=warden_headers,
    )
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == STATUS_IN_PROGRESS
    assert rej_res.json()["sla_deadline"] == orig_deadline

    # Coordinator marks resolved again
    client.put(f"/complaints/{c}/resolve", json={"notes": "Tightened screws properly."}, headers=coord_headers)

    # 2. Photo mismatch verdict -> moves back to In Progress
    mm_res = client.post(
        f"/complaints/{c}/warden-verify",
        json={"photo_mismatch": True, "notes": "Photo does not match the room."},
        headers=warden_headers,
    )
    assert mm_res.status_code == 200
    assert mm_res.json()["status"] == STATUS_IN_PROGRESS

    # Coordinator resolves again
    client.put(f"/complaints/{c}/resolve", json={"notes": "Corrected photo uploaded."}, headers=coord_headers)

    # 3. Approved -> moves to Waiting for Verification
    app_res = client.post(
        f"/complaints/{c}/warden-verify",
        json={"approved": True, "notes": "Inspected and verified in person."},
        headers=warden_headers,
    )
    assert app_res.status_code == 200
    assert app_res.json()["status"] == STATUS_WAITING_STUDENT
    assert app_res.json()["student_stage_at"] is not None


def test_spot_check_determinism(admin_headers, coord_headers):
    student_headers, student_data = _create_user(
        admin_headers, "student", "std_spot", location_id="LOC_HOSTEL_1"
    )
    from api.dependencies import get_complaint_service
    complaint_service = get_complaint_service()

    # Case A: Force spot check = True
    complaint_service._spot_check_fn = lambda: 0.05
    cA = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "electrical",
            "title": "Spot check ticket A",
            "description": "Medium issue with spot check",
            "visibility_type": "Private",
            "priority": "Medium",
        },
        headers=student_headers,
    ).json()["complaint_id"]

    client.post(f"/complaints/{cA}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=coord_headers)
    resA = client.put(f"/complaints/{cA}/resolve", json={"notes": "Fixed A"}, headers=coord_headers)
    assert resA.json()["status"] == STATUS_PENDING_WARDEN
    assert resA.json()["is_spot_check"] is True

    # Case B: Force spot check = False
    complaint_service._spot_check_fn = lambda: 0.99
    cB = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "electrical",
            "title": "Spot check ticket B",
            "description": "Medium issue without spot check",
            "visibility_type": "Private",
            "priority": "Medium",
        },
        headers=student_headers,
    ).json()["complaint_id"]

    client.post(f"/complaints/{cB}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=coord_headers)
    resB = client.put(f"/complaints/{cB}/resolve", json={"notes": "Fixed B"}, headers=coord_headers)
    assert resB.json()["status"] == STATUS_WAITING_STUDENT
    assert resB.json()["is_spot_check"] is False

    # Restore default fn
    complaint_service._spot_check_fn = None


def test_admin_review_and_decisions(admin_headers, coord_headers, warden_headers):
    student_headers, student_data = _create_user(
        admin_headers, "student", "std_ar", location_id="LOC_HOSTEL_1"
    )

    c = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "electrical",
            "title": "Admin review decision test",
            "description": "Recurrent electrical tripping",
            "visibility_type": "Private",
            "priority": "High",
        },
        headers=student_headers,
    ).json()["complaint_id"]

    def _resolve_and_approve():
        comp = client.get(f"/complaints/{c}", headers=admin_headers).json()
        if not comp.get("assigned_to"):
            client.post(f"/complaints/{c}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=coord_headers)
        client.put(f"/complaints/{c}/resolve", json={"notes": "Cycle resolved"}, headers=coord_headers)
        client.post(f"/complaints/{c}/warden-verify", json={"approved": True, "notes": "Approved"}, headers=warden_headers)

    # Reopen 1 -> Reopened
    _resolve_and_approve()
    r1 = client.post(f"/complaints/{c}/reopen", json={"reason": "Tripped again 1"}, headers=student_headers)
    assert r1.status_code == 200
    assert r1.json()["status"] == STATUS_REOPENED

    # Reopen 2 -> Reopened
    _resolve_and_approve()
    r2 = client.post(f"/complaints/{c}/reopen", json={"reason": "Tripped again 2"}, headers=student_headers)
    assert r2.status_code == 200
    assert r2.json()["status"] == STATUS_REOPENED

    # Reopen 3 -> Admin Review
    _resolve_and_approve()
    r3 = client.post(f"/complaints/{c}/reopen", json={"reason": "Tripped again 3 - persistent"}, headers=student_headers)
    assert r3.status_code == 200
    assert r3.json()["status"] == STATUS_ADMIN_REVIEW
    assert "Exceeded maximum reopens" in r3.json()["admin_review_reason"]

    # Admin decision: close
    dec_res = client.post(
        f"/complaints/{c}/admin-decision",
        json={"decision": "close", "notes": "Verified wiring personally with Chief Engineer."},
        headers=admin_headers,
    )
    assert dec_res.status_code == 200
    assert dec_res.json()["status"] == STATUS_CLOSED


def test_affected_threshold_priority_and_similar_suggestions(admin_headers, warden_headers):
    student_headers, student_data = _create_user(
        admin_headers, "student", "std_aff_rep", location_id="LOC_HOSTEL_1"
    )

    # 1. Create a public complaint with Low priority
    c_res = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "electrical",
            "title": "Water heater tripping",
            "description": "Corridor heater turns off constantly",
            "visibility_type": "Community",
            "priority": "Low",
        },
        headers=student_headers,
    )
    assert c_res.status_code == 201
    cid = c_res.json()["complaint_id"]
    assert c_res.json()["priority"] == "Low"

    # 2. Check duplicate / similar endpoint
    sim_res = client.get(
        f"/complaints/similar?location_id=LOC_HOSTEL_1&category=electrical&q=water",
        headers=student_headers,
    )
    assert sim_res.status_code == 200
    sim_items = sim_res.json()
    assert any(item["complaint_id"] == cid for item in sim_items)

    # 3. Add affected students up to threshold
    from api.dependencies import get_complaint_service
    complaint_service = get_complaint_service()

    for i in range(1, AFFECTED_PRIORITY_THRESHOLD + 1):
        complaint_service.add_affected_student(cid, f"STU_AFF_{i}_{uuid.uuid4().hex[:4]}")

    c_updated = complaint_service.get_complaint(cid)
    # Threshold reached -> priority raised to Medium
    assert c_updated.priority == "Medium"
    assert getattr(c_updated, "affected_upgraded", False) is True

    # 4. Remove affected student
    rem_res = client.delete(f"/complaints/{cid}/affected", headers=student_headers)
    assert rem_res.status_code == 200


def test_affected_student_confirmation_after_24_hours(admin_headers, coord_headers, warden_headers):
    rep_headers, rep_data = _create_user(
        admin_headers, "student", "std_rep_conf", location_id="LOC_HOSTEL_1"
    )
    aff_headers, aff_data = _create_user(
        admin_headers, "student", "std_aff_conf", location_id="LOC_HOSTEL_1"
    )

    c = client.post(
        "/complaints",
        json={
            "location_id": "LOC_HOSTEL_1",
            "department_id": "DEPT_HOSTEL_ELECTRICAL",
            "category": "electrical",
            "title": "Water cooler filter replacement",
            "description": "Filter needs change",
            "visibility_type": "Community",
            "priority": "Medium",
        },
        headers=rep_headers,
    ).json()["complaint_id"]

    # Affected student marks affected
    client.post(f"/complaints/{c}/affected", headers=aff_headers)

    client.post(f"/complaints/{c}/assign", json={"assigned_to": "USR_COORDINATOR"}, headers=coord_headers)
    client.put(f"/complaints/{c}/resolve", json={"notes": "Filter replaced."}, headers=coord_headers)

    # Complaint is in Waiting for Verification
    # Before 24h: affected student confirms -> 403
    fail_conf = client.post(f"/complaints/{c}/verify", headers=aff_headers)
    assert fail_conf.status_code == 403
    assert "after 24" in fail_conf.json()["detail"].lower()

    # Fast forward student_stage_at to 25 hours ago
    from api.dependencies import get_complaint_service
    complaint_service = get_complaint_service()
    comp_obj = complaint_service.get_complaint(c)
    past_stage = (datetime.now() - timedelta(hours=25)).strftime("%Y-%m-%d %H:%M:%S")
    comp_obj.student_stage_at = past_stage
    complaint_service.save_complaint(comp_obj)

    # After 24h: affected student confirms -> 200 Closed
    ok_conf = client.post(f"/complaints/{c}/verify", headers=aff_headers)
    assert ok_conf.status_code == 200
    assert ok_conf.json()["status"] == STATUS_CLOSED


def test_lost_found_moderation_soft_hide(admin_headers):
    student_headers, student_data = _create_user(
        admin_headers, "student", "std_lf_mod", location_id="LOC_HOSTEL_1"
    )

    item = client.post(
        "/lost-found/report",
        json={
            "report_type": "Lost",
            "title": "Moderation test item",
            "category": "Electronics",
            "date_lost": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "description": "Lost blue headphones",
            "visibility": "Public",
            "building_id": "LOC_HOSTEL_1",
        },
        headers=student_headers,
    ).json()
    item_id = item["item_id"]

    # Student cannot moderate -> 403
    s_mod = client.post(
        f"/lost-found/items/{item_id}/moderate",
        json={"reason": "Spam report", "action": "hide"},
        headers=student_headers,
    )
    assert s_mod.status_code == 403

    # Admin moderates -> 200
    a_mod = client.post(
        f"/lost-found/items/{item_id}/moderate",
        json={"reason": "Inappropriate description flagged", "action": "hide"},
        headers=admin_headers,
    )
    assert a_mod.status_code == 200
    assert a_mod.json()["is_hidden"] == 1
    assert a_mod.json()["moderation_reason"] == "Inappropriate description flagged"

    # Soft-hidden item excluded from other students' list
    other_headers, other_data = _create_user(admin_headers, "student", "std_lf_other", location_id="LOC_HOSTEL_1")
    items_list = client.get("/lost-found/items", headers=other_headers).json()
    assert not any(i["item_id"] == item_id for i in items_list)

