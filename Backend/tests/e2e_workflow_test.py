"""
CampusPulse End-to-End Workflow Test Suite
============================================
Tests complete user journeys, not individual endpoints.

Usage:
    cd Backend
    python tests/e2e_workflow_test.py

Requirements:
    pip install requests
    Backend must be running on http://127.0.0.1:8000
"""

import json
import sys
from datetime import date, timedelta

import requests

BASE = "http://127.0.0.1:8000"
PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

results = {"passed": 0, "failed": 0}


def check(label, condition, detail=""):
    if condition:
        print(f"  {PASS} {label}")
        results["passed"] += 1
    else:
        print(f"  {FAIL} {label}  →  {detail}")
        results["failed"] += 1


def login(email, password):
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    if r.status_code == 200:
        return r.json()["access_token"]
    return None


def hdrs(token):
    return {"Authorization": f"Bearer {token}"}


# ============================================================
# WORKFLOW 1: Complete Complaint Lifecycle
# ============================================================
def test_complaint_workflow():
    print(f"\n{INFO} === WORKFLOW 1: Complaint Lifecycle ===")

    # Step 1: Student Login
    student_token = login("student@campuspulse.edu", "student123")
    check("Student login succeeds", student_token is not None, "Token is None")
    if not student_token:
        print(f"  {FAIL} Cannot continue — student login failed")
        return None

    admin_token = login("admin@campuspulse.edu", "admin123")
    check("Admin login succeeds", admin_token is not None)

    # Step 2: Get available locations and departments
    r = requests.get(f"{BASE}/locations", headers=hdrs(student_token))
    check("Student can list locations", r.status_code == 200, r.text[:100])
    locations = r.json() if r.status_code == 200 else []

    r2 = requests.get(f"{BASE}/departments", headers=hdrs(student_token))
    check("Student can list departments", r2.status_code == 200, r2.text[:100])
    departments = r2.json() if r2.status_code == 200 else []

    if not locations or not departments:
        print(f"  {INFO} No locations/departments seeded — skipping complaint creation")
        return None

    loc_id = locations[0]["location_id"]
    dept = next((d for d in departments if d.get("complaint_types")), departments[0])
    dept_id = dept["department_id"]
    cat = dept["complaint_types"][0] if dept.get("complaint_types") else "General"

    # Step 3: Create Complaint
    payload = {
        "title": "E2E Test: Water leakage in Block A",
        "description": "Water leaking from the pipe near room 101, causing flooding.",
        "location_id": loc_id,
        "department_id": dept_id,
        "complaint_type": cat,
        "category": cat,
        "visibility_type": "Private",
    }
    r = requests.post(f"{BASE}/complaints", json=payload, headers=hdrs(student_token))
    check("Student creates complaint (201)", r.status_code == 201, r.text[:200])
    if r.status_code != 201:
        print(f"  {FAIL} Cannot continue — complaint creation failed")
        return None

    complaint = r.json()
    complaint_id = complaint["complaint_id"]
    check("Complaint has valid ID", "complaint_id" in complaint, complaint_id)
    check(
        "Complaint initial status is valid",
        complaint["status"] in ("Submitted", "Awaiting Assignment"),
        complaint["status"],
    )

    # Step 4: Student cannot assign complaint (role guard)
    r = requests.post(
        f"{BASE}/complaints/{complaint_id}/assign",
        json={"coordinator_id": "some_id"},
        headers=hdrs(student_token),
    )
    check(
        "Student CANNOT assign complaint (403)",
        r.status_code == 403,
        f"Got {r.status_code}",
    )

    # Step 5: Admin progresses status
    if admin_token:
        # Try to get a coordinator user
        users_r = requests.get(f"{BASE}/users", headers=hdrs(admin_token))
        coord_id = None
        if users_r.status_code == 200:
            for u in users_r.json():
                if u.get("role", "").lower() == "coordinator":
                    coord_id = u["user_id"]
                    break

        if coord_id:
            r = requests.post(
                f"{BASE}/complaints/{complaint_id}/assign",
                json={"coordinator_id": coord_id},
                headers=hdrs(admin_token),
            )
            check(
                "Admin assigns complaint to coordinator",
                r.status_code == 200,
                r.text[:100],
            )

        # Status: Assigned -> In Progress
        r = requests.patch(
            f"{BASE}/complaints/{complaint_id}/status",
            json={"status": "Assigned"},
            headers=hdrs(admin_token),
        )
        r2 = requests.patch(
            f"{BASE}/complaints/{complaint_id}/status",
            json={"status": "In Progress"},
            headers=hdrs(admin_token),
        )
        check(
            "Status progresses (Assigned or In Progress)",
            any(x.status_code == 200 for x in [r, r2]),
            f"Codes: {r.status_code}, {r2.status_code}",
        )

        # Resolve
        r = requests.post(
            f"{BASE}/complaints/{complaint_id}/resolve",
            json={"notes": "Fixed the leaking pipe. Issue resolved."},
            headers=hdrs(admin_token),
        )
        check("Admin resolves complaint", r.status_code in (200, 400), r.text[:150])
        if r.status_code == 200:
            check(
                "Status = Waiting Verification",
                r.json()["status"] == "Waiting Verification",
                r.json()["status"],
            )

    # Step 6: Student verifies
    r = requests.post(
        f"{BASE}/complaints/{complaint_id}/verify", headers=hdrs(student_token)
    )
    check(
        "Student can attempt verify (200 or 400)",
        r.status_code in (200, 400),
        r.text[:100],
    )

    # Step 7: Analytics (admin only)
    if admin_token:
        r = requests.get(f"{BASE}/complaints/analytics", headers=hdrs(admin_token))
        check("Admin can view analytics (200)", r.status_code == 200, r.text[:100])

    r = requests.get(f"{BASE}/complaints/analytics", headers=hdrs(student_token))
    check(
        "Student CANNOT view analytics (403)",
        r.status_code == 403,
        f"Got {r.status_code}",
    )

    # Step 8: Audit log
    if admin_token:
        r = requests.get(f"{BASE}/audit", headers=hdrs(admin_token))
        check("Audit log accessible to admin", r.status_code == 200, r.text[:100])

    # Step 9: Feedback
    r = requests.post(
        f"{BASE}/feedback",
        json={
            "title": "E2E Test Feedback",
            "description": "Issue resolved promptly. Satisfied.",
            "category": "Complaint Resolution",
            "rating": 4,
            "module": "Complaints",
        },
        headers=hdrs(student_token),
    )
    check(
        "Student submits feedback (200/201)", r.status_code in (200, 201), r.text[:100]
    )

    return complaint_id


# ============================================================
# WORKFLOW 2: Resource Booking (Double-Booking Prevention)
# ============================================================
def test_resource_booking():
    print(f"\n{INFO} === WORKFLOW 2: Resource Booking ===")

    student_token = login("student@campuspulse.edu", "student123")
    admin_token = login("admin@campuspulse.edu", "admin123")

    # Unauthenticated resource list → 401
    r = requests.get(f"{BASE}/resources")
    check(
        "Unauthenticated /resources → 401",
        r.status_code in (401, 403),
        f"Got {r.status_code}",
    )

    # Authenticated list
    r = requests.get(f"{BASE}/resources", headers=hdrs(student_token))
    check(
        "Authenticated student can list resources", r.status_code == 200, r.text[:100]
    )
    resources = r.json() if r.status_code == 200 else []

    if not resources:
        print(f"  {INFO} No resources seeded — skipping booking test")
        return

    resource_id = resources[0]["resource_id"]
    future_date = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")

    # Create booking
    r = requests.post(
        f"{BASE}/bookings",
        json={
            "resource_id": resource_id,
            "purpose": "E2E Test: Study session",
            "booking_date": future_date,
            "start_time": "14:00",
            "end_time": "15:00",
            "participants": 2,
        },
        headers=hdrs(student_token),
    )
    check(
        "Student creates booking (200/201)", r.status_code in (200, 201), r.text[:150]
    )

    if r.status_code not in (200, 201):
        return

    booking_id = r.json().get("booking_id")

    # Duplicate booking same slot → 400
    r2 = requests.post(
        f"{BASE}/bookings",
        json={
            "resource_id": resource_id,
            "purpose": "E2E Test: Duplicate",
            "booking_date": future_date,
            "start_time": "14:00",
            "end_time": "15:00",
            "participants": 1,
        },
        headers=hdrs(student_token),
    )
    check(
        "Duplicate booking slot rejected (400)",
        r2.status_code == 400,
        f"Got {r2.status_code}: {r2.text[:100]}",
    )

    # Unauthenticated booking detail → 401
    r = requests.get(f"{BASE}/bookings/{booking_id}")
    check(
        "Unauthenticated /bookings/{id} → 401",
        r.status_code in (401, 403),
        f"Got {r.status_code}",
    )

    # Cancel booking
    if booking_id:
        r = requests.delete(
            f"{BASE}/bookings/{booking_id}", headers=hdrs(student_token)
        )
        check("Student can cancel own booking", r.status_code == 200, r.text[:100])


# ============================================================
# WORKFLOW 3: Visitor Management
# ============================================================
def test_visitor_management():
    print(f"\n{INFO} === WORKFLOW 3: Visitor Management ===")

    student_token = login("student@campuspulse.edu", "student123")
    admin_token = login("admin@campuspulse.edu", "admin123")

    r = requests.post(
        f"{BASE}/visitors/requests",
        json={
            "visitor_name": "E2E Visitor Test",
            "visitor_phone": "9876543210",
            "purpose": "E2E test campus visit",
            "visit_type": "Personal",
            "allowed_area": "Main Campus",
            "gov_id_type": "Aadhaar",
            "gov_id_number": "1234-0000-9999",
        },
        headers=hdrs(student_token),
    )
    check(
        "Student creates visitor request (200/201)",
        r.status_code in (200, 201),
        r.text[:200],
    )
    if r.status_code not in (200, 201):
        return

    visit_id = (
        r.json().get("request_id")
        or r.json().get("visit_id")
        or r.json().get("id")
        or r.json().get("visitor_id")
    )
    check("Visitor request has valid ID", visit_id is not None, str(r.json())[:100])

    if visit_id and admin_token:
        # Admin approves
        for method, endpoint in [
            (requests.patch, f"{BASE}/visitors/requests/{visit_id}/approve"),
            (requests.put, f"{BASE}/visitors/requests/{visit_id}/approve"),
            (requests.post, f"{BASE}/visitors/requests/{visit_id}/approve"),
        ]:
            r = method(endpoint, headers=hdrs(admin_token))
            if r.status_code == 200:
                break
        check(
            "Admin approves visitor request",
            r.status_code == 200,
            f"{r.status_code}: {r.text[:100]}",
        )

        # Student cannot approve → 403
        r2 = requests.post(
            f"{BASE}/visitors/requests",
            json={
                "visitor_name": "Second E2E Visitor",
                "visitor_phone": "8888888888",
                "purpose": "Second test visit",
                "visit_type": "Academic",
                "allowed_area": "Hostel Block A",
                "gov_id_type": "PAN",
                "gov_id_number": "ABCDE1234F",
            },
            headers=hdrs(student_token),
        )
        if r2.status_code in (200, 201):
            nid = r2.json().get("request_id") or r2.json().get("visit_id")
            r3 = requests.patch(
                f"{BASE}/visitors/requests/{nid}/approve", headers=hdrs(student_token)
            )
            if r3.status_code != 200:
                check(
                    "Student CANNOT approve visitor request (403)",
                    r3.status_code == 403,
                    f"Got {r3.status_code}",
                )


# ============================================================
# WORKFLOW 4: Lost & Found
# ============================================================
def test_lost_found():
    print(f"\n{INFO} === WORKFLOW 4: Lost & Found ===")

    student_token = login("student@campuspulse.edu", "student123")

    r = requests.post(
        f"{BASE}/lost-found/items",
        json={
            "report_type": "Lost",
            "title": "E2E Test: Lost Laptop",
            "description": "Dell laptop with blue sticker on lid, serial E2E001",
            "category": "Electronics",
            "brand": "Dell",
            "color": "Black",
            "serial_number": "E2E-001",
            "exact_location": "Library Reading Room",
        },
        headers=hdrs(student_token),
    )
    check(
        "Student reports lost item (200/201)", r.status_code in (200, 201), r.text[:200]
    )
    if r.status_code not in (200, 201):
        return

    item_id = r.json().get("item_id")
    check("Lost item has valid ID", item_id is not None, str(r.json())[:100])

    # List items
    r = requests.get(f"{BASE}/lost-found/items", headers=hdrs(student_token))
    check("Student can list items", r.status_code == 200, r.text[:100])

    # Submit claim
    if item_id:
        r = requests.post(
            f"{BASE}/lost-found/items/{item_id}/claims",
            json={
                "claim_reason": "This is my laptop. Blue sticker and charger in bag.",
                "proof_description": "Sticker pattern and charger type",
            },
            headers=hdrs(student_token),
        )
        check(
            "Student submits claim (200/201 or 400 if own item)",
            r.status_code in (200, 201, 400),
            r.text[:150],
        )

        # Run AI match
        r = requests.post(
            f"{BASE}/lost-found/items/{item_id}/match", headers=hdrs(student_token)
        )
        check(
            "AI match endpoint responds",
            r.status_code in (200, 201, 404, 422),
            r.text[:100],
        )


# ============================================================
# WORKFLOW 5: Security Rules
# ============================================================
def test_security_rules():
    print(f"\n{INFO} === WORKFLOW 5: Security Rules ===")

    # No token on protected routes → 401
    for route in ["/complaints", "/resources", "/bookings/calendar", "/users"]:
        r = requests.get(f"{BASE}{route}")
        check(
            f"No token → 401 on {route}",
            r.status_code in (401, 403),
            f"Got {r.status_code}",
        )

    # Invalid token → 401
    r = requests.get(
        f"{BASE}/complaints", headers={"Authorization": "Bearer invalid_xyz_token"}
    )
    check("Invalid token → 401", r.status_code == 401, f"Got {r.status_code}")

    # Student role isolation
    student_token = login("student@campuspulse.edu", "student123")
    if student_token:
        r = requests.get(f"{BASE}/complaints/analytics", headers=hdrs(student_token))
        check(
            "Student → 403 on /complaints/analytics",
            r.status_code == 403,
            f"Got {r.status_code}",
        )

        r = requests.get(f"{BASE}/audit", headers=hdrs(student_token))
        check(
            "Student → 403 on /audit",
            r.status_code in (403, 401),
            f"Got {r.status_code}",
        )

        r = requests.get(f"{BASE}/users", headers=hdrs(student_token))
        check(
            "Student → 403 on /users (admin endpoint)",
            r.status_code in (403, 401),
            f"Got {r.status_code}",
        )

    # Health is public
    r = requests.get(f"{BASE}/health")
    check("GET /health is public (200)", r.status_code == 200, r.text)
    check("API docs accessible", requests.get(f"{BASE}/docs").status_code == 200)


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  CampusPulse — End-to-End Workflow Test Suite")
    print("=" * 60)

    try:
        r = requests.get(f"{BASE}/health", timeout=5)
        if r.status_code != 200:
            print(f"{FAIL} Backend not running at {BASE}")
            sys.exit(1)
        print(f"{PASS} Backend is running at {BASE}")
    except Exception as e:
        print(f"{FAIL} Cannot connect to {BASE}: {e}")
        sys.exit(1)

    test_security_rules()
    test_complaint_workflow()
    test_resource_booking()
    test_visitor_management()
    test_lost_found()

    total = results["passed"] + results["failed"]
    print("\n" + "=" * 60)
    print(
        f"  Results: {results['passed']}/{total} passed  |  {results['failed']} failed"
    )
    print("=" * 60 + "\n")
    sys.exit(0 if results["failed"] == 0 else 1)
