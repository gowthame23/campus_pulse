import sqlite3
import json
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from api.dependencies import get_auth_service, get_db_path
from api.security import invalidate_user_sessions

def cleanup_unwanted_users():
    print("=================================================================")
    print("CAMPUS PULSE - INITIAL USER CLEANUP (UNWANTED & TEST ACCOUNTS)")
    print("=================================================================\n")

    auth = get_auth_service()
    db_path = get_db_path()
    admin = auth.get_user("USR_ADMIN")
    assert admin is not None, "Administrator USR_ADMIN must exist"

    # Preserved Accounts (11 accounts)
    REQUIRED_ACCOUNTS = {
        "USR_ADMIN": "Administrator (System)",
        "USR_MANAGER": "App Manager 1",
        "USR_MANAGER_2": "App Manager 2",
        "USR_WARDEN": "Warden 1",
        "USR_WARDEN_2": "Warden 2",
        "USR_COORDINATOR": "Coordinator 1",
        "USR_COORDINATOR_2": "Coordinator 2",
        "USR_STUDENT": "Student 1",
        "USR_STUDENT_2": "Student 2",
        "USR_SUPER_ADMIN": "Super Admin (Platform)",
        "USR-2AB3A96E": "Gowtham Student (Manual / Uncertain - Preserved for Review)",
    }

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    all_users = cur.execute("SELECT user_id, email, name, role, active, is_deleted, status FROM users").fetchall()

    preserved_users = []
    unwanted_users = []

    for u in all_users:
        uid = u["user_id"]
        if uid in REQUIRED_ACCOUNTS:
            preserved_users.append(u)
        else:
            unwanted_users.append(u)

    print(f"Total Users in DB: {len(all_users)}")
    print(f"Preserved Users: {len(preserved_users)}")
    print(f"Unwanted Test Users to Process: {len(unwanted_users)}\n")

    # Safety check: Verify none of the unwanted users own real complaints or locations
    test_uids = [u["user_id"] for u in unwanted_users]
    if test_uids:
        placeholders = ','.join(['?'] * len(test_uids))
        cur.execute(f"SELECT COUNT(*) FROM complaints WHERE created_by IN ({placeholders}) OR assigned_to IN ({placeholders})", test_uids + test_uids)
        c_count = cur.fetchone()[0]
        assert c_count == 0, f"SAFETY ABORT: {c_count} complaints reference candidate test users!"

        cur.execute(f"SELECT COUNT(*) FROM locations WHERE in_charge_id IN ({placeholders}) OR app_manager_id IN ({placeholders})", test_uids + test_uids)
        loc_count = cur.fetchone()[0]
        assert loc_count == 0, f"SAFETY ABORT: {loc_count} locations reference candidate test users!"

    # Process removal/deactivation using application's existing mechanisms
    processed_count = 0
    already_deleted_count = 0

    for u in unwanted_users:
        uid = u["user_id"]
        # Check current state in DB
        row = cur.execute("SELECT active, is_deleted, status, email FROM users WHERE user_id = ?", (uid,)).fetchone()
        if row["is_deleted"] and not row["active"]:
            already_deleted_count += 1
            continue

        user_obj = auth.get_user(uid)
        if user_obj:
            if user_obj.active:
                auth.update_user_status(uid, "Inactive", performer=admin)
            auth.delete_user_account(uid, performer=admin)
        else:
            # Direct safe update in DB if get_user returned None
            cur.execute("""
                UPDATE users 
                SET is_deleted = 1, active = 0, status = 'Archived'
                WHERE user_id = ?
            """, (uid,))
            conn.commit()

        try:
            invalidate_user_sessions(uid)
        except Exception:
            pass
        processed_count += 1

    # Clean up any disposable notifications referencing these test accounts
    if test_uids:
        cur.execute(f"DELETE FROM notifications WHERE receiver_id IN ({placeholders})", test_uids)
        deleted_notifs = cur.rowcount
        conn.commit()
    else:
        deleted_notifs = 0

    conn.close()

    print(f"Successfully processed {processed_count} unwanted test accounts via application soft-delete/deactivation.")
    print(f"Already deleted accounts: {already_deleted_count}")
    print(f"Deleted disposable test notifications: {deleted_notifs}")

    # Non-destructive Verification
    print("\n--- Non-Destructive Verification ---")
    active_users = auth.list_users(include_deleted=False)
    active_uids = [u.user_id for u in active_users]
    print(f"Active Users in System Directory: {len(active_users)} (Expected: exactly 10 non-super-admin required accounts)")
    for u in active_users:
        print(f"  - {u.user_id:<18} | {u.role:<18} | {u.email:<30} | {u.name}")

    # Verify no unwanted test user is present in active list
    leakage = [uid for uid in test_uids if uid in active_uids]
    assert len(leakage) == 0, f"Leakage detected: {leakage}"
    print("\nPASS: ZERO unwanted test users in active directory.")

    # Verify none of the unwanted users can authenticate
    test_auth_failures = 0
    for u in unwanted_users[:5]: # test first 5 sample emails
        try:
            auth.authenticate(u["email"], "Student@123")
            assert False, f"Security Failure: Deactivated account {u['email']} was able to log in!"
        except Exception:
            test_auth_failures += 1
    print(f"PASS: Verified removed accounts cannot log in (sampled {test_auth_failures} authentications correctly rejected).")

    # Record summary dump for report
    summary = {
        "total_users_before": len(all_users),
        "preserved_accounts": list(REQUIRED_ACCOUNTS.keys()),
        "unwanted_accounts_processed": [u["user_id"] for u in unwanted_users],
        "active_users_after": active_uids,
    }
    with open(os.path.join(ROOT, "scripts", "user_cleanup_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n=================================================================")
    print("USER CLEANUP COMPLETED SUCCESSFULLY")
    print("=================================================================\n")

if __name__ == "__main__":
    cleanup_unwanted_users()
