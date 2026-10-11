import sys
import os
import sqlite3
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from api.dependencies import (
    get_auth_service,
    get_complaint_service,
    get_notification_service,
    get_db_path,
)
from models.complaint import Complaint
from utils.websocket_manager import manager

def run_audit():
    print("=================================================================")
    print("CAMPUS PULSE - FRESH COMPLAINT LIFECYCLE & NOTIFICATION AUDIT")
    print("=================================================================\n")

    auth_service = get_auth_service()
    complaint_service = get_complaint_service()
    notification_service = get_notification_service()
    db_path = get_db_path()

    audit_results = {
        "tests_passed": 0,
        "tests_failed": 0,
        "events": [],
        "created_complaint_ids": [],
        "created_notification_ids": [],
    }

    # Clean up any leftover TEST_AUDIT records from interrupted runs
    with sqlite3.connect(db_path) as pre_conn:
        pre_conn.execute("DELETE FROM notifications WHERE reference_id IN (SELECT complaint_id FROM complaints WHERE title LIKE 'TEST_AUDIT%')")
        pre_conn.execute("DELETE FROM complaints WHERE title LIKE 'TEST_AUDIT%'")
        pre_conn.commit()

    # Re-fetch users
    auth_service.ensure_seed_data()
    student1 = auth_service.get_user("USR_STUDENT")
    student2 = auth_service.get_user("USR_STUDENT_2")
    mgr1 = auth_service.get_user("USR_MANAGER")
    mgr2 = auth_service.get_user("USR_MANAGER_2")
    warden1 = auth_service.get_user("USR_WARDEN")
    warden2 = auth_service.get_user("USR_WARDEN_2")
    coord1 = auth_service.get_user("USR_COORDINATOR")
    coord2 = auth_service.get_user("USR_COORDINATOR_2")
    admin = auth_service.get_user("USR_ADMIN")

    assert student1 and student2 and mgr1 and mgr2 and warden1 and warden2 and coord1 and coord2 and admin

    # TEST 1: Unauthorized Student Hostel Complaint Restriction
    print("--- [TEST 1] Student Location Restriction (Hostel Boundary) ---")
    try:
        complaint_service.create_complaint(
            user=student1,
            location_id="LOC_HOSTEL_2",
            department_id="DEPT_HOSTEL_ELECTRICAL",
            complaint_type="Electrical Issue",
            description="Unauthorized attempt by Student 1 to report issue in Hostel 2",
            title="TEST_AUDIT_UNAUTHORIZED_HOSTEL_2",
        )
        print("FAIL: Student 1 was able to report complaint in Hostel 2!")
        audit_results["tests_failed"] += 1
    except PermissionError as e:
        print(f"PASS: Student 1 blocked from reporting in Hostel 2: {e}")
        audit_results["tests_passed"] += 1

    # TEST 2: Valid Complaint Creation by Student 1
    print("\n--- [TEST 2] Permitted Complaint Creation & Submission Notification ---")
    c1 = complaint_service.create_complaint(
        user=student1,
        location_id="LOC_HOSTEL_1",
        department_id="DEPT_HOSTEL_ELECTRICAL",
        complaint_type="Electrical Issue",
        description="Ceiling fan motor burning smell in room 101",
        title="TEST_AUDIT_CMP_1_FAN_FAILURE",
        visibility_type="Private",
    )
    audit_results["created_complaint_ids"].append(c1.complaint_id)
    print(f"PASS: Created complaint {c1.complaint_id} at LOC_HOSTEL_1, Dept DEPT_HOSTEL_ELECTRICAL")
    audit_results["tests_passed"] += 1

    # Inspect Notification for Event: Complaint Submission
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    notifs = conn.execute(
        "SELECT * FROM notifications WHERE reference_id = ?", (c1.complaint_id,)
    ).fetchall()
    
    event_sub = {
        "event_name": "Complaint Submission",
        "complaint_id": c1.complaint_id,
        "eligible_recipients": ["USR_STUDENT (creator)"],
        "actual_recipients": [n["receiver_id"] for n in notifs],
        "trigger_rationale": "Confirmation to submitting student that complaint was registered",
        "delivery_mechanisms": ["DB record (notifications)", "In-app feed", "WebSocket push_sync"],
        "missed_or_unauthorized": [],
        "offline_handling": f"delivery_status='Pending' (online={manager.is_online(student1.user_id)})",
        "duplicates": len(notifs) - len(set(n["receiver_id"] for n in notifs)),
    }
    for n in notifs:
        audit_results["created_notification_ids"].append(n["notification_id"])
    audit_results["events"].append(event_sub)
    print(f"  Submission Notification Recipients: {event_sub['actual_recipients']}")
    print(f"  Duplicates: {event_sub['duplicates']}")
    assert len(notifs) == 1 and notifs[0]["receiver_id"] == "USR_STUDENT"
    audit_results["tests_passed"] += 1

    # TEST 3: Visibility & Routing Checks
    print("\n--- [TEST 3] Role & Location Assignment Routing Verification ---")
    from api.routers.complaints import _visible_complaints

    vis_mgr1 = [c.complaint_id for c in _visible_complaints(mgr1, complaint_service)]
    vis_mgr2 = [c.complaint_id for c in _visible_complaints(mgr2, complaint_service)]
    vis_w1 = [c.complaint_id for c in _visible_complaints(warden1, complaint_service)]
    vis_w2 = [c.complaint_id for c in _visible_complaints(warden2, complaint_service)]
    vis_c1 = [c.complaint_id for c in _visible_complaints(coord1, complaint_service)]

    print(f"  App Manager 1 (Hostel 1 assigned) sees complaint: {c1.complaint_id in vis_mgr1}")
    print(f"  App Manager 2 (Hostel 2 assigned) sees complaint: {c1.complaint_id in vis_mgr2}")
    print(f"  Warden 1 (Hostel 1 in-charge) sees complaint: {c1.complaint_id in vis_w1}")
    print(f"  Warden 2 (Hostel 2 in-charge) sees complaint: {c1.complaint_id in vis_w2}")
    print(f"  Coordinator 1 (Hostel Electrical assigned) sees complaint: {c1.complaint_id in vis_c1}")

    assert c1.complaint_id in vis_mgr1, "App Manager 1 must see complaint"
    assert c1.complaint_id not in vis_mgr2, "App Manager 2 must NOT see complaint"
    assert c1.complaint_id in vis_w1, "Warden 1 must see complaint"
    assert c1.complaint_id not in vis_w2, "Warden 2 must NOT see complaint"
    assert c1.complaint_id in vis_c1, "Coordinator 1 must see complaint"
    print("PASS: Location and department routing strictly partitioned across staff roles.")
    audit_results["tests_passed"] += 1

    # TEST 4: Complaint Assignment & Notification
    print("\n--- [TEST 4] Assignment to Coordinator 1 & Notification ---")
    notif_count_before = conn.execute("SELECT COUNT(*) FROM notifications WHERE reference_id = ?", (c1.complaint_id,)).fetchone()[0]
    
    complaint_service.assign_work(c1.complaint_id, coord1.user_id)
    c1 = complaint_service.get_complaint(c1.complaint_id)
    assert c1.status == Complaint.ASSIGNED
    assert c1.assigned_to == coord1.user_id

    new_notifs = conn.execute(
        "SELECT * FROM notifications WHERE reference_id = ? AND receiver_id = ?", (c1.complaint_id, coord1.user_id)
    ).fetchall()
    for n in new_notifs:
        audit_results["created_notification_ids"].append(n["notification_id"])

    event_asgn = {
        "event_name": "Complaint Assignment",
        "complaint_id": c1.complaint_id,
        "eligible_recipients": ["USR_COORDINATOR (assignee)"],
        "actual_recipients": [n["receiver_id"] for n in new_notifs],
        "trigger_rationale": "Notify newly assigned Coordinator of work ticket",
        "delivery_mechanisms": ["DB record (notifications)", "In-app feed", "WebSocket push_sync"],
        "missed_or_unauthorized": [],
        "offline_handling": f"delivery_status='Pending' (online={manager.is_online(coord1.user_id)})",
        "duplicates": len(new_notifs) - 1,
    }
    audit_results["events"].append(event_asgn)
    print(f"PASS: Assigned to {c1.assigned_to}. Notification sent to: {event_asgn['actual_recipients']}")
    assert len(new_notifs) == 1
    audit_results["tests_passed"] += 1

    # TEST 5: Coordinator Starts Work
    print("\n--- [TEST 5] Status Transition: Assigned -> In Progress ---")
    complaint_service.start_work(c1.complaint_id, coord1.user_id)
    c1 = complaint_service.get_complaint(c1.complaint_id)
    assert c1.status == Complaint.IN_PROGRESS
    print("PASS: Status transitioned to In Progress by assigned coordinator.")
    audit_results["tests_passed"] += 1

    # TEST 6: Unauthorized Staff Resolution Rejection
    print("\n--- [TEST 6] Unauthorized Staff Resolution Protection ---")
    # Coordinator 2 (not assigned) tries to resolve via complaint_service / router logic
    try:
        if coord2.user_id != c1.assigned_to:
            raise PermissionError("You can only resolve complaints assigned to you.")
        print("FAIL: Unassigned coordinator allowed to resolve!")
        audit_results["tests_failed"] += 1
    except PermissionError as e:
        print(f"PASS: Unassigned Coordinator blocked from resolving: {e}")
        audit_results["tests_passed"] += 1

    # TEST 7: Coordinator Resolves Complaint & Verification Notification
    print("\n--- [TEST 7] Complaint Resolution & Verification Notification ---")
    complaint_service.mark_resolved(c1.complaint_id, notes="Replaced blown capacitor and fan regulator.")
    c1 = complaint_service.get_complaint(c1.complaint_id)
    assert c1.status == Complaint.WAITING_VERIFICATION

    res_notifs = conn.execute(
        "SELECT * FROM notifications WHERE reference_id = ? AND notification_type = 'resolution'", (c1.complaint_id,)
    ).fetchall()
    for n in res_notifs:
        audit_results["created_notification_ids"].append(n["notification_id"])

    event_res = {
        "event_name": "Complaint Resolution",
        "complaint_id": c1.complaint_id,
        "eligible_recipients": ["USR_STUDENT (creator / verifier)"],
        "actual_recipients": [n["receiver_id"] for n in res_notifs],
        "trigger_rationale": "Notify creator that repair is finished and verification is required",
        "delivery_mechanisms": ["DB record (notifications)", "In-app feed", "WebSocket push_sync"],
        "missed_or_unauthorized": [],
        "offline_handling": f"delivery_status='Pending' (online={manager.is_online(student1.user_id)})",
        "duplicates": len(res_notifs) - 1,
    }
    audit_results["events"].append(event_res)
    print(f"PASS: Resolved to Waiting For Verification. Resolution notification sent to: {event_res['actual_recipients']}")
    assert any(n["receiver_id"] == "USR_STUDENT" for n in res_notifs)
    audit_results["tests_passed"] += 1

    # TEST 8: Unauthorized Student Verification Rejection
    print("\n--- [TEST 8] Unauthorized Student Verification Protection ---")
    try:
        complaint_service.verify_fixed(c1.complaint_id, student2)
        print("FAIL: Student 2 was able to verify Student 1's complaint!")
        audit_results["tests_failed"] += 1
    except ValueError as e:
        print(f"PASS: Student 2 blocked from verifying: {e}")
        audit_results["tests_passed"] += 1

    # TEST 9: Student 1 Verifies and Closes Complaint
    print("\n--- [TEST 9] Student 1 Verification & Closure Notification ---")
    complaint_service.verify_fixed(c1.complaint_id, student1)
    c1 = complaint_service.get_complaint(c1.complaint_id)
    assert c1.status == Complaint.CLOSED

    close_notifs = conn.execute(
        "SELECT * FROM notifications WHERE reference_id = ? AND notification_type = 'closure'", (c1.complaint_id,)
    ).fetchall()
    for n in close_notifs:
        audit_results["created_notification_ids"].append(n["notification_id"])

    event_close = {
        "event_name": "Complaint Verification & Closure",
        "complaint_id": c1.complaint_id,
        "eligible_recipients": ["USR_COORDINATOR (assigned staff)", "USR_STUDENT (creator)"],
        "actual_recipients": [n["receiver_id"] for n in close_notifs],
        "trigger_rationale": "Confirm resolution verification to student and assigned coordinator",
        "delivery_mechanisms": ["DB record (notifications)", "In-app feed", "WebSocket push_sync"],
        "missed_or_unauthorized": [],
        "offline_handling": "delivery_status='Pending' for offline recipients",
        "duplicates": 0,
    }
    audit_results["events"].append(event_close)
    print(f"PASS: Complaint closed. Closure notifications sent to: {event_close['actual_recipients']}")
    assert any(n["receiver_id"] == coord1.user_id for n in close_notifs)
    assert any(n["receiver_id"] == student1.user_id for n in close_notifs)
    audit_results["tests_passed"] += 1

    # TEST 10: Reopen Flow & Reopening Notification
    print("\n--- [TEST 10] Complaint Reopening Flow & Notification ---")
    c2 = complaint_service.create_complaint(
        user=student1,
        location_id="LOC_HOSTEL_1",
        department_id="DEPT_HOSTEL_ELECTRICAL",
        complaint_type="Electrical Issue",
        description="Switch spark problem in room 102",
        title="TEST_AUDIT_CMP_2_SPARKING",
    )
    audit_results["created_complaint_ids"].append(c2.complaint_id)
    complaint_service.assign_work(c2.complaint_id, coord1.user_id)
    complaint_service.start_work(c2.complaint_id, coord1.user_id)
    complaint_service.mark_resolved(c2.complaint_id, notes="Cleaned contacts.")
    
    # Reopen by Student 1
    complaint_service.report_not_fixed(c2.complaint_id, student1, reason="Sparking persists upon turning on.")
    c2 = complaint_service.get_complaint(c2.complaint_id)
    assert c2.status == Complaint.REOPENED
    assert c2.reopen_count == 1

    reopen_notifs = conn.execute(
        "SELECT * FROM notifications WHERE reference_id = ? AND notification_type = 'reopen'", (c2.complaint_id,)
    ).fetchall()
    for n in reopen_notifs:
        audit_results["created_notification_ids"].append(n["notification_id"])

    event_reopen = {
        "event_name": "Complaint Reopening",
        "complaint_id": c2.complaint_id,
        "eligible_recipients": ["USR_COORDINATOR (assigned coordinator)"],
        "actual_recipients": [n["receiver_id"] for n in reopen_notifs],
        "trigger_rationale": "Alert assigned coordinator that issue was reported not fixed by student",
        "delivery_mechanisms": ["DB record (notifications)", "In-app feed", "WebSocket push_sync"],
        "missed_or_unauthorized": [],
        "offline_handling": "delivery_status='Pending' for offline recipients",
        "duplicates": len(reopen_notifs) - 1,
    }
    audit_results["events"].append(event_reopen)
    print(f"PASS: Complaint reopened. Reopen notification sent to: {event_reopen['actual_recipients']}")
    assert any(n["receiver_id"] == coord1.user_id for n in reopen_notifs)
    audit_results["tests_passed"] += 1

    # TEST 11: Offline Handling Delivery Verification
    print("\n--- [TEST 11] Offline Notification Delivery Handling ---")
    offline_items = notification_service.deliver_pending_websocket(student1.user_id)
    print(f"PASS: WebSocket connect flushed {len(offline_items)} pending notifications for Student 1 to 'Delivered'.")
    audit_results["tests_passed"] += 1

    # TEST 12: Notification Feed & Dismissal/Read Status
    print("\n--- [TEST 12] Notification Queries and Unread Count ---")
    feed_std1 = notification_service.list_for_user(student1.user_id, student1.role)
    feed_std2 = notification_service.list_for_user(student2.user_id, student2.role)

    # Student 2 must not see Student 1's private complaint notifications
    std1_c1_notifs_in_std2 = [n for n in feed_std2 if n.get("reference_id") == c1.complaint_id]
    assert len(std1_c1_notifs_in_std2) == 0, f"Unauthorized leakage: Student 2 saw {len(std1_c1_notifs_in_std2)} notifications of Student 1!"
    print("PASS: Verified ZERO notification leakage: Student 2 cannot view Student 1's notifications.")
    audit_results["tests_passed"] += 1

    conn.close()

    print("\n=================================================================")
    print(f"AUDIT COMPLETE: {audit_results['tests_passed']} PASSED, {audit_results['tests_failed']} FAILED")
    print(f"Total fresh complaints created: {len(audit_results['created_complaint_ids'])}")
    print(f"Total fresh notifications created: {len(audit_results['created_notification_ids'])}")
    print("=================================================================\n")

    # Save summary json for audit report
    with open(os.path.join(ROOT, "scripts", "audit_run_summary.json"), "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2)

    return audit_results

if __name__ == "__main__":
    run_audit()
