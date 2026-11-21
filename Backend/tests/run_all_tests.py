import sys
import os
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

def run():
    print("\n" + "=" * 65)
    print("  Campus Pulse — Full Production Test Suite (Workflows 1-15)")
    print("=" * 65)

    modules = [
        ("Workflow 1: Auth & Authorization", "tests.test_workflow1_auth"),
        ("Workflow 2: User Management", "tests.test_workflow2_user_management"),
        ("Workflow 4: Complaint Management", "tests.test_workflow4_complaint_management"),
        ("Workflow 5: Public Complaints", "tests.test_workflow5_public_complaints"),
        ("Workflow 6: Lost & Found", "tests.test_workflow6_lost_found"),
        ("Workflow 7: Notifications", "tests.test_workflow7_notifications"),
        ("Workflow 8: Announcements", "tests.test_workflow8_announcements"),
        ("Workflow 9: Dashboard Management", "tests.test_workflow9_dashboard"),
        ("Workflow 10: Reports & Analytics", "tests.test_workflow10_reports"),
        ("Workflow 11: Audit Logs", "tests.test_workflow11_audit"),
        ("Workflow 12: Platform Settings", "tests.test_workflow12_settings"),
        ("Workflow 13: Database Design", "tests.test_workflow13_database"),
        ("Workflow 14: API Standards", "tests.test_workflow14_api_standards"),
        ("Workflow 15: Architecture & Domain", "tests.test_workflow15_architecture"),
        ("Workflow 16: Super Admin Platform Layer", "tests.test_workflow16_super_admin"),
    ]

    passed = 0
    failed = 0

    for title, mod_name in modules:
        try:
            start_t = time.time()
            mod = __import__(mod_name, fromlist=["*"])
            test_funcs = [getattr(mod, f) for f in dir(mod) if f.startswith("test_") and callable(getattr(mod, f))]
            for func in test_funcs:
                func()
            dur = (time.time() - start_t) * 1000
            print(f"  [PASS] {title:<40} ({len(test_funcs)} tests, {dur:.1f} ms)")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {title:<40} Error: {e}")
            failed += 1

    print("=" * 65)
    print(f"  Summary: {passed} PASSED | {failed} FAILED")
    print("=" * 65 + "\n")
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(run())
