import gc
import os
import sys
import uuid
import pytest
import sqlite3
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_db_path
from api.security import hash_token
from middleware.rate_limiter import auth_limiter

client = TestClient(app)


def _reset_limiter():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()


def _get_student_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "student@example.com", "password": "Student@123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, token


def _get_admin_headers():
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": "admin@example.com", "password": "Admin@123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, token


# 1. PERSISTENT SESSIONS
def test_security_persistent_session_in_db():
    std_headers, token = _get_student_headers()
    conn = sqlite3.connect(get_db_path())
    row = conn.execute("SELECT * FROM user_sessions WHERE session_id = ?", (hash_token(token),)).fetchone()
    raw_row = conn.execute("SELECT 1 FROM user_sessions WHERE session_id = ?", (token,)).fetchone()
    conn.close()
    assert row is not None
    assert row[1] == "USR_STUDENT"  # user_id
    assert raw_row is None  # the bearer token itself is never stored


# 2. PASSWORD RESET ENUMERATION PROTECTION
def test_security_password_reset_enumeration_protection():
    # Registered email
    res1 = client.post("/auth/password-reset/request", json={"email": "student@example.com"})
    assert res1.status_code == 200
    assert "reset_id" in res1.json()
    assert "If the account exists" in res1.json()["message"]

    # Non-registered email -> exact same generic status 200
    res2 = client.post("/auth/password-reset/request", json={"email": "nonexistent_unknown_email_999@domain.com"})
    assert res2.status_code == 200
    assert "reset_id" in res2.json()
    assert "If the account exists" in res2.json()["message"]


# 3. OTP BRUTE FORCE PROTECTION ACROSS RESET IDS
def test_security_password_reset_otp_attempt_limits():
    email = "student@example.com"
    req_res = client.post("/auth/password-reset/request", json={"email": email})
    reset_id = req_res.json()["reset_id"]

    # Fail OTP 5 times
    for _ in range(5):
        client.post("/auth/password-reset/verify", json={"reset_id": reset_id, "otp": "000000"})

    # 6th attempt should be rejected
    fail_res = client.post("/auth/password-reset/verify", json={"reset_id": reset_id, "otp": "000000"})
    assert fail_res.status_code == 400

    # Requesting a NEW reset_id for same email cannot bypass account attempt limit
    req2 = client.post("/auth/password-reset/request", json={"email": email})
    assert req2.status_code == 400
    assert "too many" in req2.json()["detail"].lower()


# 4. SERVICE-LEVEL PASSWORD UPDATE GUARD
def test_security_profile_update_cannot_change_password():
    std_headers, _ = _get_student_headers()
    # Attempting to update password via generic profile update
    res = client.put("/users/USR_STUDENT", json={"password": "HackedPassword123!"}, headers=std_headers)
    # Password field is ignored by generic profile update; original password remains unchanged
    login_check = client.post("/auth/login", json={"username": "student@example.com", "password": "Student@123"})
    assert login_check.status_code == 200


# 5. NOTIFICATION CREATION RESTRICTION
def test_security_student_cannot_create_arbitrary_notification():
    std_headers, _ = _get_student_headers()
    res = client.post("/notifications", json={
        "receiver_id": "USR_ADMIN",
        "title": "Fake Alert",
        "message": "Student impersonating system notification"
    }, headers=std_headers)
    assert res.status_code == 403


# 6. FEEDBACK SECURITY
def test_security_feedback_unauthorized_access_rejected():
    std_headers, _ = _get_student_headers()
    # Analytics rejected for student -> 403
    ana_res = client.get("/feedback/analytics", headers=std_headers)
    assert ana_res.status_code == 403

    # Reports rejected for student -> 403
    rep_res = client.get("/feedback/reports", headers=std_headers)
    assert rep_res.status_code == 403


# 7. REPORTS SECURITY
def test_security_reports_unauthorized_access_rejected():
    std_headers, _ = _get_student_headers()
    # Summary rejected for student -> 403
    sum_res = client.get("/reports/summary", headers=std_headers)
    assert sum_res.status_code == 403

    # Schedules rejected for student -> 403
    sch_res = client.get("/reports/schedules", headers=std_headers)
    assert sch_res.status_code == 403


# 8. ANNOUNCEMENT ATTACHMENT RESTRICTION
def test_security_student_cannot_add_announcement_attachment():
    std_headers, _ = _get_student_headers()
    res = client.post("/announcements/ANN_001/attachments", json={
        "file_name": "malicious.exe",
        "file_path": "/uploads/malicious.exe",
        "file_size": 1024,
        "file_type": "exe"
    }, headers=std_headers)
    assert res.status_code == 403


# 9. WEBSOCKET AUTHENTICATION
def test_security_websocket_invalid_token_rejected():
    from fastapi.testclient import TestClient
    with pytest.raises(Exception):
        with client.websocket_connect("/notifications/ws/USR_STUDENT?token=INVALID_TOKEN"):
            pass


# 10. CROSS-WORKER SESSION REVOCATION
def test_security_cross_worker_session_revocation():
    import time
    # Worker A: authenticate session token X
    std_headers, token = _get_student_headers()
    me_res1 = client.get("/auth/me", headers=std_headers)
    assert me_res1.status_code == 200

    # Worker B: revoke token X directly in persistent DB
    conn = sqlite3.connect(get_db_path())
    conn.execute("UPDATE user_sessions SET status = 'Revoked' WHERE session_id = ?", (hash_token(token),))
    conn.commit()
    conn.close()

    # Worker A: authenticate token X again -> MUST FAIL
    me_res2 = client.get("/auth/me", headers=std_headers)
    assert me_res2.status_code == 401


# 11. EXPIRED SESSION REJECTION
def test_security_expired_session_rejected():
    import time
    std_headers, token = _get_student_headers()
    past_exp = str(time.time() - 3600)
    conn = sqlite3.connect(get_db_path())
    conn.execute("UPDATE user_sessions SET expires_at = ? WHERE session_id = ?", (past_exp, hash_token(token)))
    conn.commit()
    conn.close()

    res = client.get("/auth/me", headers=std_headers)
    assert res.status_code == 401


# 12. LOGOUT SESSION INVALIDATION
def test_security_logout_invalidates_session():
    std_headers, token = _get_student_headers()
    logout_res = client.post("/auth/logout", headers=std_headers)
    assert logout_res.status_code == 200

    res = client.get("/auth/me", headers=std_headers)
    assert res.status_code == 401


# 13. WORKER RESTART PERSISTENCE
def test_security_worker_restart_persistence():
    std_headers, token = _get_student_headers()
    # Create fresh TestClient to simulate new worker process
    fresh_client = TestClient(app)
    res = fresh_client.get("/auth/me", headers=std_headers)
    assert res.status_code == 200


# 14. LOST & FOUND AUTHORIZATION GUARDS & SIMPLIFIED LIFECYCLE
def test_security_lost_found_authorization_guards():
    std_headers, token = _get_student_headers()
    admin_headers, _ = _get_admin_headers()

    # 1. Create found item by student
    item_res = client.post("/lost-found/report", json={
        "type": "Found",
        "title": "Unclaimed Wallet",
        "description": "Black leather wallet found near library",
        "location_id": "LOC_LIB_01"
    }, headers=std_headers)
    assert item_res.status_code == 201
    item_id = item_res.json()["item_id"]

    # 2. Claims workflow is disabled per simplified Lost & Found architecture -> 400
    claim_res = client.post(f"/lost-found/items/{item_id}/claim", json={
        "claim_reason": "I lost this wallet",
        "proof_description": "Contains my student ID"
    }, headers=admin_headers)
    assert claim_res.status_code in (400, 403, 404)

    # 3. Unauthorized non-owner student cannot delete another student's report -> 403
    _reset_limiter()
    student2_login = client.post("/auth/login", json={"username": "student_alt@example.com", "password": "Student@123"})
    if student2_login.status_code == 200:
        std2_headers = {"Authorization": f"Bearer {student2_login.json()['access_token']}"}
        del_res = client.delete(f"/lost-found/items/{item_id}", headers=std2_headers)
        assert del_res.status_code in (403, 401)

    # 4. Legitimate reporter or admin can delete/close the report -> 200
    del_legit = client.delete(f"/lost-found/items/{item_id}", headers=std_headers)
    assert del_legit.status_code in (200, 204)


# 15. ANONYMOUS LOST & FOUND ACCESS DENIAL
def test_security_anonymous_lost_found_access_denied():
    client.cookies.clear()
    assert client.get("/lost-found/items/LFI_999").status_code in (401, 403, 404)
    assert client.get("/lost-found/items/LFI_999/images").status_code in (401, 403, 404)
    assert client.get("/lost-found/claims/CLM_999").status_code in (401, 403, 404)
    assert client.get("/lost-found/matches/LFI_999").status_code in (401, 403, 404)


# 16. SETTINGS BACKUP & RESTORE SECURITY
def test_security_settings_backup_no_hashes_and_audited_restore():
    admin_headers, _ = _get_admin_headers()
    std_headers, _ = _get_student_headers()

    # Non-admin rejected -> 403
    assert client.get("/settings/backup", headers=std_headers).status_code == 403
    assert client.post("/settings/restore", json={}, headers=std_headers).status_code == 403

    # Admin GET /settings/backup -> clean metadata response without password hashes
    bup_res = client.get("/settings/backup", headers=admin_headers)
    assert bup_res.status_code == 200
    res_data = bup_res.json()
    assert "backup_id" in res_data
    assert "password_hash" not in str(res_data)

    # Admin POST /settings/restore -> uses BackupService
    rst_res = client.post("/settings/restore", json={"backup_id": res_data["backup_id"]}, headers=admin_headers)
    assert rst_res.status_code in (200, 202)
    assert "restore" in rst_res.json()["message"].lower()


# 17. METADATA ENDPOINT AUTHENTICATION
def test_security_metadata_endpoints_require_authentication():
    # Anonymous requests to metadata endpoints -> 401 or 403
    client.cookies.clear()
    assert client.get("/announcements/ANN_001/attachments").status_code in (401, 403)
    assert client.get("/reports/templates").status_code in (401, 403)
    assert client.get("/feedback/templates").status_code in (401, 403)
    assert client.get("/feedback/templates/TPL_001/questions").status_code in (401, 403)

    # Authenticated campus user -> 200 OK
    std_headers, _ = _get_student_headers()
    assert client.get("/reports/templates", headers=std_headers).status_code == 200
    assert client.get("/feedback/templates", headers=std_headers).status_code == 200


# 18. ANALYTICS ROLE AUTHORIZATION MATRIX
def test_security_analytics_authorization_matrix():
    std_headers, _ = _get_student_headers()
    _reset_limiter()
    coord_login = client.post("/auth/login", json={"username": "coordinator@example.com", "password": "Coordinator@123"})
    coord_headers = {"Authorization": f"Bearer {coord_login.json()['access_token']}"}

    _reset_limiter()
    warden_login = client.post("/auth/login", json={"username": "warden@example.com", "password": "warden@123"})
    warden_headers = {"Authorization": f"Bearer {warden_login.json()['access_token']}"}

    _reset_limiter()
    mgr_login = client.post("/auth/login", json={"username": "manager@example.com", "password": "Manager@123"})
    mgr_headers = {"Authorization": f"Bearer {mgr_login.json()['access_token']}"}

    admin_headers, _ = _get_admin_headers()

    analytics_endpoints = [
        "/analytics/users",
        "/analytics/coordinators",
        "/analytics/departments",
        "/analytics/hostels",
        "/analytics/notifications",
    ]

    for ep in analytics_endpoints:
        # Student -> 403
        r_std = client.get(ep, headers=std_headers)
        assert r_std.status_code == 403
        assert "insufficient permissions" in str(r_std.json()).lower()

        # Coordinator -> 403
        r_coord = client.get(ep, headers=coord_headers)
        assert r_coord.status_code == 403

        # Warden -> 403
        r_warden = client.get(ep, headers=warden_headers)
        assert r_warden.status_code == 403

        # App Manager -> 200
        r_mgr = client.get(ep, headers=mgr_headers)
        assert r_mgr.status_code == 200

        # Administrator -> 200
        r_admin = client.get(ep, headers=admin_headers)
        assert r_admin.status_code == 200


# 19. PLATFORM INSTITUTION ONBOARDING & ADMIN CREATION
def test_security_platform_institution_onboarding():
    _reset_limiter()
    sa_login = client.post("/auth/login", json={"username": "superadmin@campuspulse.edu", "password": "Superadmin@123"})
    assert sa_login.status_code == 200
    sa_headers = {"Authorization": f"Bearer {sa_login.json()['access_token']}"}

    # 1. Missing admin_password -> 422 Unprocessable Entity
    bad_payload_no_pass = {
        "name": "Missing Pass Institute",
        "code": "MPI",
        "admin_name": "MPI Admin",
        "admin_email": "admin@mpi.edu"
    }
    res_nopass = client.post("/platform/institutions", json=bad_payload_no_pass, headers=sa_headers)
    assert res_nopass.status_code == 422

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT institution_id FROM institutions WHERE code = 'MPI'")
    assert cursor.fetchone() is None
    conn.close()

    # 2. Invalid admin_email -> 422 Unprocessable Entity
    bad_payload_invalid_email = {
        "name": "Invalid Email Institute",
        "code": "IEI",
        "admin_name": "IEI Admin",
        "admin_email": "invalid-email-string",
        "admin_password": "ValidPassword123!"
    }
    res_bademail = client.post("/platform/institutions", json=bad_payload_invalid_email, headers=sa_headers)
    assert res_bademail.status_code == 422

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT institution_id FROM institutions WHERE code = 'IEI'")
    assert cursor.fetchone() is None
    conn.close()

    # 3. Weak admin_password (under 8 chars) -> 422 Unprocessable Entity
    bad_payload_short_pass = {
        "name": "Short Pass Institute",
        "code": "SPI",
        "admin_name": "SPI Admin",
        "admin_email": "admin@spi.edu",
        "admin_password": "short"
    }
    res_shortpass = client.post("/platform/institutions", json=bad_payload_short_pass, headers=sa_headers)
    assert res_shortpass.status_code == 422

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT institution_id FROM institutions WHERE code = 'SPI'")
    assert cursor.fetchone() is None
    conn.close()

    # 4. Weak admin_password (no special char / uppercase -> fails complexity check in service) -> 400 Bad Request & atomicity rollback
    bad_payload_simple_pass = {
        "name": "Simple Pass Institute",
        "code": "SIMP",
        "admin_name": "SIMP Admin",
        "admin_email": "admin@simp.edu",
        "admin_password": "simplepassword"
    }
    res_simplepass = client.post("/platform/institutions", json=bad_payload_simple_pass, headers=sa_headers)
    assert res_simplepass.status_code == 400
    assert "complexity" in res_simplepass.json()["detail"].lower()

    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT institution_id FROM institutions WHERE code = 'SIMP'")
    assert cursor.fetchone() is None
    conn.close()

    # 5. Successful onboarding with valid payload
    payload = {
        "name": "Testing Institute of Technology",
        "code": "TIT",
        "admin_name": "TIT Administrator",
        "admin_email": "admin_tit@tit.edu",
        "admin_password": "TitAdminPassword123!",
        "contact_info": "+91-9988776655",
    }

    res = client.post("/platform/institutions", json=payload, headers=sa_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["institution_id"] == "INST_TIT"

    # Verify administrator was created and can authenticate
    _reset_limiter()
    admin_login = client.post("/auth/login", json={"username": "admin_tit@tit.edu", "password": "TitAdminPassword123!"})
    assert admin_login.status_code == 200
    assert admin_login.json()["user"]["role"] == "administrator"
    assert admin_login.json()["user"]["first_login"] is True

    # Duplicate code rejection -> 400
    res_dup = client.post("/platform/institutions", json=payload, headers=sa_headers)
    assert res_dup.status_code == 400
    assert "already exists" in res_dup.json()["detail"].lower()


# 20. SUPERVISOR DASHBOARD AUTHORIZATION
def test_security_supervisor_dashboard_authorization():
    std_headers, _ = _get_student_headers()
    admin_headers, _ = _get_admin_headers()

    _reset_limiter()
    coord_login = client.post("/auth/login", json={"username": "coordinator@example.com", "password": "Coordinator@123"})
    coord_headers = {"Authorization": f"Bearer {coord_login.json()['access_token']}"}

    _reset_limiter()
    warden_login = client.post("/auth/login", json={"username": "warden@example.com", "password": "warden@123"})
    warden_headers = {"Authorization": f"Bearer {warden_login.json()['access_token']}"}

    _reset_limiter()
    mgr_login = client.post("/auth/login", json={"username": "manager@example.com", "password": "Manager@123"})
    mgr_headers = {"Authorization": f"Bearer {mgr_login.json()['access_token']}"}

    # Student -> 403 (Proper HTTP 403 status code, no supervisor data in payload)
    res_std = client.get("/supervisor/dashboard", headers=std_headers)
    assert res_std.status_code == 403
    assert "complaint_summary" not in res_std.json()

    # Coordinator -> 403
    assert client.get("/supervisor/dashboard", headers=coord_headers).status_code == 403

    # Warden -> 403
    assert client.get("/supervisor/dashboard", headers=warden_headers).status_code == 403

    # App Manager -> 200
    res_mgr = client.get("/supervisor/dashboard", headers=mgr_headers)
    assert res_mgr.status_code == 200
    assert "complaint_summary" in res_mgr.json()

    # Administrator -> 200
    res_admin = client.get("/supervisor/dashboard", headers=admin_headers)
    assert res_admin.status_code == 200
    assert "complaint_summary" in res_admin.json()



# 21. HELPERS FOR MULTI-USER AUTHORIZATION TESTS
def _login_headers(email, password):
    _reset_limiter()
    res = client.post("/auth/login", json={"username": email, "password": password})
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def _new_student():
    email = f"student_{uuid.uuid4().hex[:8]}@probe.edu"
    admin_headers, _ = _get_admin_headers()
    res = client.post("/users", json={
        "name": "Probe Student", "email": email, "role": "student",
        "password": "Temp@Pass123", "confirm_password": "Temp@Pass123", "location_id": "LOC_HOSTEL_A",
    }, headers=admin_headers)
    assert res.status_code == 201
    headers = _login_headers(email, "Temp@Pass123")
    change = client.post("/auth/change-password", json={
        "old_password": "Temp@Pass123", "new_password": "Stud@Pass456", "confirm_password": "Stud@Pass456",
    }, headers=headers)
    assert change.status_code == 200
    return res.json()["user_id"], email, _login_headers(email, "Stud@Pass456")


def _new_complaint(headers, location="LOC_HOSTEL_A", department="DEPT_ELECTRICAL", title="Probe issue"):
    res = client.post("/complaints", json={
        "location_id": location, "department_id": department, "title": title,
        "description": "probe description " + uuid.uuid4().hex[:6], "visibility_type": "Private",
    }, headers=headers)
    assert res.status_code == 201
    return res.json()["complaint_id"]


# 22. BACKUPS: ADMIN-ONLY CREATE/DOWNLOAD, VALIDATED TYPE
def test_security_backups_admin_only_and_type_validated():
    mgr_headers = _login_headers("manager@example.com", "Manager@123")
    admin_headers, _ = _get_admin_headers()
    assert client.post("/backups", json={"backup_name": "m"}, headers=mgr_headers).status_code == 403

    created = client.post("/backups", json={"backup_name": "sec-test"}, headers=admin_headers)
    assert created.status_code == 201
    try:
        backup_id = created.json()["backup_id"]
        assert client.get(f"/backups/{backup_id}/download", headers=mgr_headers).status_code == 403
        assert client.get(f"/backups/{backup_id}/download", headers=admin_headers).status_code == 200
        bad = client.post("/backups", json={"backup_name": "x", "backup_type": "../escape"}, headers=admin_headers)
        assert bad.status_code == 400
    finally:
        gc.collect()  # release the download's file handle so Windows can delete it
        os.remove(created.json()["file_path"])


# 23. REPORTS: ROLE-GATED GENERATION, VALIDATED TYPE, AUDIT REPORT WORKS
def test_security_reports_generation_role_gated_and_validated():
    std_headers, _ = _get_student_headers()
    admin_headers, _ = _get_admin_headers()
    body = {"report_name": "sec-test", "report_type": "Complaint", "file_format": "CSV"}
    assert client.post("/reports", json=body, headers=std_headers).status_code == 403
    assert client.post("/reports", json=dict(body, report_type="../escape"), headers=admin_headers).status_code == 400

    audit = client.post("/reports", json=dict(body, report_type="Audit"), headers=admin_headers)
    assert audit.status_code == 201
    os.remove(audit.json()["file_path"])


# 24. COMPLAINT OBJECT-LEVEL AUTHORIZATION
def test_security_complaint_object_level_authorization():
    std_headers, _ = _get_student_headers()
    warden_headers = _login_headers("warden@example.com", "warden@123")
    mgr_headers = _login_headers("manager@example.com", "Manager@123")
    admin_headers, _ = _get_admin_headers()
    sa_headers = _login_headers("superadmin@campuspulse.edu", "Superadmin@123")

    # Complaint at a location the warden and App Manager do not manage
    mess_id = _new_complaint(std_headers, location="LOC_MESS", department="DEPT_MESS_FOOD")
    assert client.post(f"/complaints/{mess_id}/accept", headers=warden_headers).status_code == 403
    assert client.post(f"/complaints/{mess_id}/escalate", json={"reason": "x"}, headers=mgr_headers).status_code == 403

    # Another student's private complaint
    _, _, owner_headers = _new_student()
    _, _, other_headers = _new_student()
    private_id = _new_complaint(owner_headers)
    assert client.post(f"/complaints/{private_id}/affected", headers=other_headers).status_code == 403

    # Staff cannot directly edit or delete a student's complaint; Warden delete triggers deletion request
    assert client.patch(f"/complaints/{private_id}", json={"description": "edited"}, headers=warden_headers).status_code == 403
    warden_del_res = client.request("DELETE", f"/complaints/{private_id}", json={"reason": "Audit test deletion request"}, headers=warden_headers)
    print("WARDEN DELETE RES:", warden_del_res.status_code, warden_del_res.text)
    assert warden_del_res.status_code == 200
    assert warden_del_res.json()["status"] == "deletion_requested"
    assert client.get(f"/complaints/{private_id}", headers=owner_headers).status_code == 200
    assert client.patch(f"/complaints/{private_id}", json={"description": "edited by owner"}, headers=owner_headers).status_code == 200

    # Super Admin cannot touch institutional complaints; assignee must be a Coordinator
    priority = {"priority": "High", "reason": "x"}
    assert client.patch(f"/complaints/{private_id}/priority", json=priority, headers=sa_headers).status_code == 403
    assert client.post(f"/complaints/{private_id}/assign", json={"coordinator_id": "USR_STUDENT"}, headers=admin_headers).status_code == 400


# 25. ANNOUNCEMENT OWNERSHIP AND MISSING IDS
def test_security_announcement_ownership_and_missing_ids():
    admin_headers, _ = _get_admin_headers()
    coord_headers = _login_headers("coordinator@example.com", "Coordinator@123")
    created = client.post("/announcements", json={
        "title": "Ownership test", "content": "c", "description": "d", "category": "General",
        "priority": "Normal", "target_type": "Campus", "target": "All",
    }, headers=admin_headers)
    assert created.status_code == 201
    ann_id = created.json()["announcement_id"]
    attachment = {"file_name": "a.pdf", "file_path": "a.pdf", "file_size": 1, "file_type": "pdf"}

    assert client.put(f"/announcements/{ann_id}", json={"title": "hacked"}, headers=coord_headers).status_code == 403
    assert client.put(f"/announcements/{ann_id}/publish", headers=coord_headers).status_code == 403
    assert client.post(f"/announcements/{ann_id}/attachments", json=attachment, headers=coord_headers).status_code == 403
    assert client.put(f"/announcements/{ann_id}", json={"title": "Ownership test v2"}, headers=admin_headers).status_code == 200

    assert client.put("/announcements/NO_SUCH_ID/cancel", headers=admin_headers).status_code == 400
    assert client.post("/announcements/NO_SUCH_ID/attachments", json=attachment, headers=admin_headers).status_code == 404


# 26. SUPER ADMIN ISOLATION FROM INSTITUTIONAL ROUTERS
def test_security_super_admin_blocked_from_institutional_routers():
    sa_headers = _login_headers("superadmin@campuspulse.edu", "Superadmin@123")
    for path in ("/lost-found/items", "/public-complaints", "/announcements", "/reports",
                 "/analytics/complaints", "/feedback", "/search/history"):
        assert client.get(path, headers=sa_headers).status_code == 403


# 27. FEEDBACK ONLY FOR OWN CLOSED COMPLAINTS
def test_security_feedback_requires_own_closed_complaint():
    std_headers, _ = _get_student_headers()
    body = {"feedback_type": "Complaint", "rating": 1, "title": "t", "comments": "c"}
    assert client.post("/feedback", json=dict(body, reference_id="CMP-DOES-NOT-EXIST"), headers=std_headers).status_code == 400

    _, _, other_headers = _new_student()
    open_id = _new_complaint(other_headers)
    assert client.post("/feedback", json=dict(body, reference_id=open_id), headers=std_headers).status_code == 400


# 28. CSV EXPORTS NEUTRALIZE SPREADSHEET FORMULAS
def test_security_csv_export_neutralizes_formulas():
    std_headers, _ = _get_student_headers()
    admin_headers, _ = _get_admin_headers()
    _new_complaint(std_headers, title='=HYPERLINK("http://evil.example","x")')
    csv_text = client.get("/complaints/export/csv", headers=admin_headers).text
    assert "'=HYPERLINK" in csv_text
    assert ',"=HYPERLINK' not in csv_text


# 29. LOGIN DOES NOT REVEAL ACCOUNT STATUS; TEMP PASSWORDS ARE RANDOM AND NOT AUDITED
def test_security_login_status_temp_passwords_and_import_audit():
    admin_headers, _ = _get_admin_headers()
    user_id, email, _ = _new_student()
    client.patch(f"/users/{user_id}/status", json={"status": "Inactive", "remarks": "probe"}, headers=admin_headers)
    _reset_limiter()
    wrong = client.post("/auth/login", json={"username": email, "password": "Wrong@Pass1"})
    assert wrong.status_code == 401
    right = client.post("/auth/login", json={"username": email, "password": "Stud@Pass456"})
    assert right.status_code == 403

    temp_passwords = []
    for _ in range(2):
        res = client.post("/users", json={
            "name": "No Password", "email": f"nopass_{uuid.uuid4().hex[:8]}@probe.edu", "role": "student",
        }, headers=admin_headers)
        assert res.status_code == 201
        temp_passwords.append(res.json()["temporary_password"])
    assert temp_passwords[0] != temp_passwords[1]
    assert "Temp@1234" not in temp_passwords

    csv_bytes = f"name,email,role\nImport One,imp_{uuid.uuid4().hex[:8]}@probe.edu,student\n".encode()
    imported = client.post("/users/import", files={"file": ("u.csv", csv_bytes, "text/csv")}, headers=admin_headers)
    assert imported.status_code == 200
    temp_pw = imported.json()["report"][0]["temporary_password"]
    conn = sqlite3.connect(get_db_path())
    audited = conn.execute(
        "SELECT new_value FROM audit_logs WHERE action LIKE 'Excel Import%' ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    conn.close()
    assert temp_pw and temp_pw not in str(audited)


# 30. PAGINATION, INPUT SIZE LIMITS AND RESPONSE HEADERS
def test_security_pagination_size_limits_and_headers():
    admin_headers, _ = _get_admin_headers()
    std_headers, _ = _get_student_headers()
    assert client.get("/users/paginated?limit=101", headers=admin_headers).status_code == 422
    assert client.get("/users/paginated?page=0", headers=admin_headers).status_code == 422

    long_complaint = {"location_id": "LOC_HOSTEL_A", "department_id": "DEPT_ELECTRICAL", "title": "t", "description": "A" * 5001}
    assert client.post("/complaints", json=long_complaint, headers=std_headers).status_code == 422
    assert client.post("/chat/message", json={"conversation_id": "chat:a:b", "content": "A" * 2001}, headers=std_headers).status_code == 400

    health = client.get("/health")
    assert health.headers["X-Content-Type-Options"] == "nosniff"
    assert health.headers["X-Frame-Options"] == "DENY"
    assert health.headers["Cache-Control"] == "no-store"


# 31. SHARED NOTIFICATIONS CANNOT BE DELETED FOR EVERYONE BY A STUDENT
def test_security_broadcast_notification_not_deletable_by_student():
    admin_headers, _ = _get_admin_headers()
    std_headers, _ = _get_student_headers()

    created = client.post("/notifications", json={
        "receiver_id": "All", "title": "Broadcast probe", "message": "hello",
    }, headers=admin_headers)
    assert created.status_code == 201
    nid = created.json()["notification_id"]

    # Student A clears broadcast for Student A
    assert client.delete(f"/notifications/{nid}", headers=std_headers).status_code == 200

    # Student A no longer sees the broadcast
    assert client.get(f"/notifications/{nid}", headers=std_headers).status_code == 404

    # Admin and other users still see the broadcast notification
    assert client.get(f"/notifications/{nid}", headers=admin_headers).status_code == 200
    assert client.delete(f"/notifications/{nid}", headers=admin_headers).status_code == 200


# 32. PRODUCTION DOES NOT SEED PUBLIC DEMO PASSWORDS
def test_security_production_seed_requires_supplied_passwords(tmp_path, monkeypatch):
    from services.auth_service import AuthService

    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("SEED_USR_ADMIN_PASSWORD", raising=False)
    service = AuthService(db_path=str(tmp_path / "prod.db"))
    assert service.repository.load()["users"] == []

    monkeypatch.setenv("SEED_USR_ADMIN_PASSWORD", "Boot@Strap2026")
    service = AuthService(db_path=str(tmp_path / "prod.db"))
    users = service.repository.load()["users"]
    assert [u["user_id"] for u in users] == ["USR_ADMIN"]
    assert service.authenticate("admin@example.com", "Boot@Strap2026")


# 33. SCHEMA VALIDATION FOR USER CREATION & PASSWORD RESET
def test_security_user_create_and_password_reset_schema_validation():
    admin_headers, _ = _get_admin_headers()

    # Invalid email in PasswordResetStartRequest -> 422
    res_pr = client.post("/auth/password-reset/request", json={"email": "not-an-email"})
    assert res_pr.status_code == 422

    # Invalid email in UserCreateRequest -> 422
    bad_user_payload = {
        "name": "Invalid Email User",
        "email": "invalid-user-email",
        "role": "student",
        "password": "ValidPassword123!"
    }
    res_uc = client.post("/users", json=bad_user_payload, headers=admin_headers)
    assert res_uc.status_code == 422



# 33. ADMIN PROFILE UPDATE CANNOT BYPASS ROLE / STATUS / LOCATION RULES
def test_security_admin_profile_update_enforces_role_status_location_rules():
    admin_headers, _ = _get_admin_headers()
    student_id, _, _ = _new_student()
    url = f"/users/{student_id}"
    assert client.put(url, json={"role": "administrator"}, headers=admin_headers).status_code == 400
    assert client.put(url, json={"role": "super_admin"}, headers=admin_headers).status_code == 400
    assert client.put(url, json={"role": "bogus"}, headers=admin_headers).status_code == 400
    assert client.put(url, json={"location_id": "LOC_NOPE"}, headers=admin_headers).status_code == 400
    assert client.put("/users/USR_ADMIN", json={"role": "student"}, headers=admin_headers).status_code == 400

    # status is not editable here; the guarded /status endpoint is the only path
    res = client.put("/users/USR_ADMIN", json={"status": "Inactive"}, headers=admin_headers)
    assert res.status_code == 200 and res.json()["status"] == "Active"
    assert client.get("/auth/me", headers=admin_headers).status_code == 200


# 34. ADMIN/MANAGER PASSWORD RESET REVOKES THE TARGET'S SESSIONS
def test_security_admin_password_reset_revokes_sessions():
    student_id, _, student_headers = _new_student()
    mgr_headers = _login_headers("manager@example.com", "Manager@123")
    assert client.get("/auth/me", headers=student_headers).status_code == 200
    res = client.put(f"/users/{student_id}/reset-password", json={"new_password": "Reset@Pass789"}, headers=mgr_headers)
    assert res.status_code == 200
    assert client.get("/auth/me", headers=student_headers).status_code == 401


# 35. PASSWORD-RESET SECRETS ARE HASHED, REQUESTS ARE CAPPED, TEMPLATE ROUTE REACHABLE
def test_security_password_reset_secrets_hashed_and_capped(monkeypatch):
    sent = []
    monkeypatch.setattr("utils.email.send_otp_email", lambda email, otp: sent.append(otp))
    _, email, _ = _new_student()

    _reset_limiter()
    first = client.post("/auth/password-reset/request", json={"email": email}).json()
    otp = sent[-1]
    conn = sqlite3.connect(get_db_path())
    stored = conn.execute("SELECT otp FROM password_resets WHERE reset_id = ?", (first["reset_id"],)).fetchone()[0]
    assert stored != otp

    verified = client.post("/auth/password-reset/verify", json={"reset_id": first["reset_id"], "otp": otp})
    assert verified.status_code == 200
    token = verified.json()["reset_token"]
    assert conn.execute("SELECT COUNT(*) FROM password_resets WHERE reset_id = ?", (token,)).fetchone()[0] == 0
    conn.execute("DELETE FROM password_resets WHERE email = ?", (email,))
    conn.commit()
    conn.close()

    _reset_limiter()
    codes = []
    for _ in range(6):
        codes.append(client.post("/auth/password-reset/request", json={"email": email}).status_code)
    assert codes[:5] == [200] * 5 and codes[5] == 400
    conn = sqlite3.connect(get_db_path())
    conn.execute("DELETE FROM password_resets WHERE email = ?", (email,))
    conn.commit()
    conn.close()

    assert client.get("/users/template").status_code == 200
    assert client.get("/users/import/template").status_code == 200


# 36. LOST & FOUND NON-PUBLIC ITEMS ARE NOT READABLE BY ID FOR OTHER STUDENTS
def test_security_lost_found_private_item_not_readable_by_other_student():
    admin_headers, _ = _get_admin_headers()
    _, _, owner_headers = _new_student()
    _, _, other_headers = _new_student()
    created = client.post("/lost-found/items", json={
        "type": "Lost", "title": "Private probe", "description": "d", "category": "Other", "location_id": "LOC_HOSTEL_A",
    }, headers=owner_headers)
    assert created.status_code == 201
    item_id = created.json()["item_id"]
    assert client.put(f"/lost-found/items/{item_id}", json={"visibility": "Private"}, headers=admin_headers).status_code == 200

    assert client.get(f"/lost-found/items/{item_id}", headers=other_headers).status_code == 404
    assert client.get(f"/lost-found/items/{item_id}/images", headers=other_headers).status_code == 404
    assert client.get(f"/lost-found/items/{item_id}", headers=owner_headers).status_code == 200


# 37. SUPER ADMIN IS INVISIBLE AND UNMANAGEABLE FROM THE INSTITUTION ADMIN PORTAL
def test_security_super_admin_hidden_from_institution_users():
    admin_headers, _ = _get_admin_headers()
    sa_id = "USR_SUPER_ADMIN"
    assert sa_id not in [u["user_id"] for u in client.get("/users", headers=admin_headers).json()]
    assert sa_id not in [u["user_id"] for u in client.get("/users/paginated?limit=100", headers=admin_headers).json()["items"]]
    assert client.get("/users?role=student&q=superadmin", headers=admin_headers).json() == []

    assert client.get(f"/users/{sa_id}", headers=admin_headers).status_code == 404
    assert client.get(f"/users/{sa_id}/activities", headers=admin_headers).status_code == 404
    assert client.put(f"/users/{sa_id}", json={"name": "Hacked"}, headers=admin_headers).status_code == 404
    assert client.patch(f"/users/{sa_id}/status", json={"status": "Inactive"}, headers=admin_headers).status_code == 404
    assert client.delete(f"/users/{sa_id}", headers=admin_headers).status_code == 404
    mgr_headers = _login_headers("manager@example.com", "Manager@123")
    assert client.put(f"/users/{sa_id}/reset-password", json={"new_password": "Hack@Pass123"}, headers=mgr_headers).status_code == 404

    sa_headers = _login_headers("superadmin@campuspulse.edu", "Superadmin@123")
    assert client.get(f"/users/{sa_id}", headers=sa_headers).status_code == 200

    # its logins/actions are absent from the institution activity and audit views
    for path in ("/users/activities/all", "/users/audit-logs/list", "/audit?limit=100"):
        body = client.get(path, headers=admin_headers)
        assert body.status_code == 200 and sa_id not in body.text, path


# 38. LOST & FOUND DELETION STRICT OWNERSHIP ENFORCEMENT
def test_security_lost_found_delete_ownership_strict():
    _, _, creator_headers = _new_student()
    _, _, other_student_headers = _new_student()

    _reset_limiter()
    coord_login = client.post("/auth/login", json={"username": "coordinator@example.com", "password": "Coordinator@123"})
    coord_headers = {"Authorization": f"Bearer {coord_login.json()['access_token']}"}

    _reset_limiter()
    warden_login = client.post("/auth/login", json={"username": "warden@example.com", "password": "warden@123"})
    warden_headers = {"Authorization": f"Bearer {warden_login.json()['access_token']}"}

    _reset_limiter()
    mgr_login = client.post("/auth/login", json={"username": "manager@example.com", "password": "Manager@123"})
    mgr_headers = {"Authorization": f"Bearer {mgr_login.json()['access_token']}"}

    admin_headers, _ = _get_admin_headers()

    _reset_limiter()
    sa_login = client.post("/auth/login", json={"username": "superadmin@campuspulse.edu", "password": "Superadmin@123"})
    sa_headers = {"Authorization": f"Bearer {sa_login.json()['access_token']}"}

    # Creator posts Lost & Found item
    created = client.post("/lost-found/items", json={
        "type": "Found",
        "title": "Strict Ownership Wallet",
        "description": "Black wallet found near library",
        "category": "Personal",
        "location_id": "LOC_LIB_01"
    }, headers=creator_headers)
    assert created.status_code == 201
    item_id = created.json()["item_id"]

    # 1. Other Student -> 403
    res_std = client.delete(f"/lost-found/items/{item_id}", headers=other_student_headers)
    assert res_std.status_code == 403

    # 2. Coordinator -> 403
    res_coord = client.delete(f"/lost-found/items/{item_id}", headers=coord_headers)
    assert res_coord.status_code == 403

    # 3. Warden / Location In-Charge -> 403
    res_warden = client.delete(f"/lost-found/items/{item_id}", headers=warden_headers)
    assert res_warden.status_code == 403

    # 4. App Manager -> 403
    res_mgr = client.delete(f"/lost-found/items/{item_id}", headers=mgr_headers)
    assert res_mgr.status_code == 403

    # 5. Administrator -> 403 on hard delete
    res_admin = client.delete(f"/lost-found/items/{item_id}", headers=admin_headers)
    assert res_admin.status_code == 403

    # 6. Super Admin -> 403
    res_sa = client.delete(f"/lost-found/items/{item_id}", headers=sa_headers)
    assert res_sa.status_code == 403

    # Verify item remains unchanged and active in DB
    item_check = client.get(f"/lost-found/items/{item_id}", headers=creator_headers)
    assert item_check.status_code == 200
    assert item_check.json()["item_id"] == item_id

    # 7. App Manager / Admin can moderate (soft-hide) with mandatory reason
    mod_fail = client.post(f"/lost-found/items/{item_id}/moderate", json={"reason": ""}, headers=mgr_headers)
    assert mod_fail.status_code == 400

    mod_ok = client.post(f"/lost-found/items/{item_id}/moderate", json={"reason": "Contains duplicate personal item", "action": "hide"}, headers=mgr_headers)
    assert mod_ok.status_code == 200
    assert mod_ok.json()["is_hidden"] is True

    # 8. Creator can delete own item -> 200 OK
    res_creator = client.delete(f"/lost-found/items/{item_id}", headers=creator_headers)
    assert res_creator.status_code == 200
    assert "deleted" in res_creator.json()["message"].lower()



# 38. ACTIVATION TOKENS ARE STORED HASHED AND NEVER LEAK INTO THE AUDIT LOG
def test_security_activation_token_hashed_and_not_leaked_in_audit_log():
    from services.auth_service import AuthService

    admin_headers, _ = _get_admin_headers()
    csv_bytes = f"name,email,role\nAct Probe,act_{uuid.uuid4().hex[:8]}@probe.edu,student\n".encode()
    imported = client.post("/users/import", files={"file": ("u.csv", csv_bytes, "text/csv")}, headers=admin_headers)
    assert imported.status_code == 200
    row = imported.json()["report"][0]
    act_token = row.get("activation_token")
    assert act_token

    # the raw token is not stored anywhere in the database
    conn = sqlite3.connect(get_db_path())
    stored = conn.execute(
        "SELECT token FROM activation_tokens WHERE user_id = ?", (row["user_id"] if "user_id" in row else row.get("email"),)
    ).fetchall() if "user_id" in row else conn.execute(
        "SELECT token FROM activation_tokens ORDER BY created_at DESC LIMIT 1"
    ).fetchall()
    assert stored and stored[0][0] != act_token

    audited = conn.execute(
        "SELECT new_value FROM audit_logs WHERE action = 'Excel Import Users' ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    conn.close()
    assert audited and act_token not in str(audited[0])

    # the token still activates the account (hashing round-trips correctly)
    service = AuthService(db_path=get_db_path())
    verified = service.verify_activation_token(act_token)
    assert verified["valid"] is True


# 39. PER-ACCOUNT BRUTE-FORCE LOCKOUT: PROGRESSIVE, TEMPORARY, RECOVERABLE
def test_security_login_lockout_progressive_and_temporary():
    from services.auth_service import AuthService

    email = _new_student()[1]
    _reset_limiter()

    # 5 wrong passwords lock the account; the 6th (even with the right password) is refused
    for _ in range(5):
        r = client.post("/auth/login", json={"username": email, "password": "WrongPass@1"})
        assert r.status_code == 401
    locked = client.post("/auth/login", json={"username": email, "password": "Stud@Pass456"})
    assert locked.status_code == 403
    assert "try again" in locked.json()["detail"].lower()

    # a nonexistent account behaves identically (no enumeration signal)
    _reset_limiter()
    ghost = f"nobody_{uuid.uuid4().hex[:8]}@probe.edu"
    for _ in range(5):
        r = client.post("/auth/login", json={"username": ghost, "password": "WrongPass@1"})
        assert r.status_code == 401
    ghost_locked = client.post("/auth/login", json={"username": ghost, "password": "anything"})
    assert ghost_locked.status_code == 403

    # the lock is temporary and bounded: forcing it to expire lets the real user in
    conn = sqlite3.connect(get_db_path())
    conn.execute("UPDATE login_attempts SET locked_until = 0 WHERE identity = ?", (email.lower(),))
    conn.commit()
    conn.close()
    _reset_limiter()
    ok = client.post("/auth/login", json={"username": email, "password": "Stud@Pass456"})
    assert ok.status_code == 200

    # a successful login resets the failure counter
    conn = sqlite3.connect(get_db_path())
    row = conn.execute("SELECT failed_count FROM login_attempts WHERE identity = ?", (email.lower(),)).fetchone()
    conn.close()
    assert row is None or row[0] == 0


def test_security_login_lockout_does_not_block_password_reset_recovery(monkeypatch):
    sent = []
    monkeypatch.setattr("utils.email.send_otp_email", lambda email, otp: sent.append(otp))
    _, email, _ = _new_student()
    _reset_limiter()
    for _ in range(5):
        client.post("/auth/login", json={"username": email, "password": "WrongPass@1"})
    assert client.post("/auth/login", json={"username": email, "password": "Stud@Pass456"}).status_code == 403

    _reset_limiter()
    req = client.post("/auth/password-reset/request", json={"email": email})
    assert req.status_code == 200
    otp = sent[-1]
    verified = client.post("/auth/password-reset/verify", json={"reset_id": req.json()["reset_id"], "otp": otp})
    assert verified.status_code == 200
    completed = client.post("/auth/password-reset/complete", json={
        "reset_token": verified.json()["reset_token"], "new_password": "Recovered@Pass1",
    })
    assert completed.status_code == 200

    _reset_limiter()
    assert client.post("/auth/login", json={"username": email, "password": "Recovered@Pass1"}).status_code == 200
    conn = sqlite3.connect(get_db_path())
    conn.execute("DELETE FROM password_resets WHERE email = ?", (email,))
    conn.commit()
    conn.close()


# 40. PASSWORD HASHES ARE TRANSPARENTLY UPGRADED ON LOGIN WITHOUT A RESET
def test_security_password_hash_upgraded_on_login():
    import hashlib
    from utils.passwords import needs_rehash

    _, email, _ = _new_student()
    salt = "aabbccddeeff00112233445566778899"
    weak_digest = hashlib.pbkdf2_hmac("sha256", b"Stud@Pass456", salt.encode("utf-8"), 1000).hex()
    weak_hash = f"pbkdf2_sha256$1000${salt}${weak_digest}"
    assert needs_rehash(weak_hash)

    conn = sqlite3.connect(get_db_path())
    conn.execute("UPDATE users SET password = ? WHERE email = ?", (weak_hash, email))
    conn.commit()
    _reset_limiter()
    res = client.post("/auth/login", json={"username": email, "password": "Stud@Pass456"})
    assert res.status_code == 200

    stored = conn.execute("SELECT password FROM users WHERE email = ?", (email,)).fetchone()[0]
    conn.close()
    assert not needs_rehash(stored)
    assert stored != weak_hash

    _reset_limiter()
    assert client.post("/auth/login", json={"username": email, "password": "Stud@Pass456"}).status_code == 200
