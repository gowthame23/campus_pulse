import pytest
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from middleware.rate_limiter import auth_limiter
from api.dependencies import _service_cache

client = TestClient(app)

def _reset_limiter():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()
    _service_cache.clear()
    import sqlite3
    from utils.passwords import hash_password
    for db_p in ("storage/campus_pulse.db", "Backend/storage/campus_pulse.db", "storage/pytest_isolated.db", "Backend/storage/pytest_isolated.db"):
        if os.path.exists(db_p):
            try:
                conn = sqlite3.connect(db_p)
                conn.execute("DELETE FROM login_attempts")
                conn.execute("UPDATE users SET password = ?, active = 1, status = 'Active' WHERE email = ?", (hash_password("Student@123"), "student@example.com"))
                conn.execute("UPDATE users SET password = ?, active = 1, status = 'Active' WHERE email = ?", (hash_password("Admin@123"), "admin@example.com"))
                conn.commit()
                conn.close()
            except Exception:
                pass
    _service_cache.clear()


def login_user(email, password):
    _reset_limiter()
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_lost_found_report_deletion_cascade():
    # 1. Login as Student (Reporter) and create a Found report
    reporter_headers = login_user("student@example.com", "Student@123")
    create_res = client.post(
        "/lost-found/report",
        json={
            "type": "Found",
            "title": "Cascading Test Wallet",
            "description": "Black leather wallet with student ID inside",
            "category": "Wallet",
            "brand": "Wildhorn",
            "color": "Black",
            "exact_location": "Academic Block Room 101",
        },
        headers=reporter_headers,
    )
    assert create_res.status_code == 201, f"Create failed: {create_res.text}"
    item = create_res.json()
    item_id = item["item_id"]

    # 2. Login as Admin and attempt claim or insert legacy claim to test cascade
    admin_headers = login_user("admin@example.com", "Admin@123")
    
    # Insert legacy claim via DB to verify cascade behavior when report is deleted
    import sqlite3
    from api.dependencies import get_db_path
    claim_id = "CLM_CASCADE_TEST"
    conn = sqlite3.connect(get_db_path())
    conn.execute(
        "INSERT OR REPLACE INTO ownership_claims (claim_id, item_id, claimed_by, claim_reason, proof_description, status, created_at) VALUES (?, ?, ?, ?, ?, 'Pending', datetime('now'))",
        (claim_id, item_id, "admin@example.com", "Cascade test claim", "Test proof description")
    )
    conn.commit()
    conn.close()

    # 3. Delete the parent Lost & Found report as reporter
    del_res = client.delete(f"/lost-found/items/{item_id}", headers=reporter_headers)
    assert del_res.status_code == 200, f"Delete failed: {del_res.text}"

    # 4. Verify Parent Item is no longer accessible (404)
    item_get = client.get(f"/lost-found/items/{item_id}", headers=reporter_headers)
    assert item_get.status_code == 404

    # 5. Verify Associated Claim is no longer accessible (404)
    claim_get = client.get(f"/lost-found/claims/{claim_id}", headers=admin_headers)
    assert claim_get.status_code == 404

    # 6. Verify Notifications referencing item_id or claim_id are not present in inbox
    notifs_reporter = client.get("/notifications", headers=reporter_headers).json()
    notifs_admin = client.get("/notifications", headers=admin_headers).json()

    all_notifs = notifs_reporter + notifs_admin
    for n in all_notifs:
        ref_id = str(n.get("reference_id") or "")
        msg = str(n.get("message") or "")
        assert ref_id != item_id, f"Notification for deleted item {item_id} still present"
        assert ref_id != claim_id, f"Notification for claim {claim_id} of deleted item still present"
        assert item_id not in msg, f"Notification message referencing deleted item {item_id} still present"
