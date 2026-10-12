"""
CampusPulse Smoke Test
======================
Quick verification that the backend is running correctly after deployment.

Usage:
    cd Backend
    python tests/smoke_test.py

Requirements:
    pip install requests
    Backend must be running on http://127.0.0.1:8000
"""

import sys

import requests


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://127.0.0.1:8000"
PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

results = {"passed": 0, "failed": 0}


def check(description, condition, detail=""):
    if condition:
        print(f"  {PASS} {description}")
        results["passed"] += 1
    else:
        print(f"  {FAIL} {description}" + (f"  →  {detail}" if detail else ""))
        results["failed"] += 1


def main():
    print("\n=======================================================")
    print("  CampusPulse — Smoke Test")
    print("=======================================================")

    # 1. Server Availability
    try:
        r = requests.get(f"{BASE}/health", timeout=5)
        check("GET /health → 200", r.status_code == 200, f"Got {r.status_code}")
        check("/health returns {status: ok}", r.json().get("status") == "ok")
    except Exception as e:
        check("Backend reachable", False, str(e))
        return 1

    # 2. Docs Availability
    r_docs = requests.get(f"{BASE}/docs", timeout=5)
    check("GET /docs → 200 (Swagger UI accessible)", r_docs.status_code == 200)

    r_openapi = requests.get(f"{BASE}/openapi.json", timeout=5)
    check("GET /openapi.json → 200", r_openapi.status_code == 200)
    if r_openapi.status_code == 200:
        routes = r_openapi.json().get("paths", {})
        check(
            "API has core routes registered", len(routes) > 20, f"Found {len(routes)} paths"
        )

    # 3. Seed Accounts Login
    print(f"\n{INFO} Checking dev seed accounts...")
    dev_users = [
        ("Administrator", "admin@example.com", "Admin@123"),
        ("Supervisor", "manager@example.com", "Manager@123"),
        ("Coordinator", "coordinator@example.com", "Coordinator@123"),
        ("Student", "student@example.com", "Student@123"),
    ]

    tokens = {}
    for role, email, pwd in dev_users:
        r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": pwd})
        token = r.json().get("access_token") or r.json().get("token")
        ok = r.status_code == 200 and token is not None
        check(f"{role} login succeeds ({email})", ok, f"HTTP {r.status_code}")
        if ok:
            tokens[role] = token

    # 4. Auth Protection on Core Routes
    print(f"\n{INFO} Checking auth protection on core routes...")
    for endpoint in [
        "/complaints",
        "/users",
        "/audit",
        "/locations",
        "/departments",
        "/issues",
    ]:
        r = requests.get(f"{BASE}{endpoint}")
        check(
            f"{endpoint} requires auth (401/403)",
            r.status_code in (401, 403),
            f"Got {r.status_code}",
        )

    # 5. Core Route Functionality with Admin Token
    if "Administrator" in tokens:
        headers = {"Authorization": f"Bearer {tokens['Administrator']}"}
        print(f"\n{INFO} Checking admin core endpoints...")
        r_users = requests.get(f"{BASE}/users", headers=headers)
        check("GET /users returns 200 for Admin", r_users.status_code == 200)

        r_complaints = requests.get(f"{BASE}/complaints", headers=headers)
        check("GET /complaints returns 200 for Admin", r_complaints.status_code == 200)

        r_issues = requests.get(f"{BASE}/issues", headers=headers)
        check("GET /issues returns 200 for Admin", r_issues.status_code == 200)

        r_announcements = requests.get(f"{BASE}/announcements", headers=headers)
        check(
            "GET /announcements returns 200 for Admin", r_announcements.status_code == 200
        )

    # Summary
    total = results["passed"] + results["failed"]
    print("\n=======================================================")
    print(
        f"  Smoke Test: {results['passed']}/{total} passed  |  {results['failed']} failed"
    )
    print("=======================================================\n")
    if results["failed"] == 0:
        print("  ✅ All smoke tests passed — system is healthy!")
    else:
        print("  ❌ Some tests failed — review output above")
    print("=" * 55 + "\n")
    return 0 if results["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
