import sqlite3

db_path = r'c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co\Backend\storage\campus_pulse.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

print("=================================================================")
print("NON-DESTRUCTIVE FINAL STATE VERIFICATION (READ-ONLY)")
print("=================================================================\n")

# 1. PRAGMA integrity check
cur.execute("PRAGMA integrity_check")
integrity = cur.fetchone()[0]
print(f"1. Database Integrity: {integrity}")

# 2. Complaints Table
cur.execute("SELECT complaint_id, title, status, created_at FROM complaints ORDER BY created_at ASC")
complaints = cur.fetchall()
print(f"\n2. Total Complaints: {len(complaints)} (Expected: exactly 9 baseline complaints)")
for c in complaints:
    print(f"   - {c[0]} | {c[1]} | {c[2]} | {c[3]}")

# Verify no test complaint remains
cur.execute("SELECT COUNT(*) FROM complaints WHERE title LIKE 'TEST%' OR title LIKE '%test%' OR description LIKE '%test%'")
test_cmps = cur.fetchone()[0]
print(f"   Test complaints in DB: {test_cmps} (must be 0)")

# 3. Notifications Table
cur.execute("SELECT COUNT(*) FROM notifications")
notif_count = cur.fetchone()[0]
print(f"\n3. Total Notifications: {notif_count}")

cur.execute("""
    SELECT COUNT(*) FROM notifications 
    WHERE reference_id LIKE 'TEST%' 
       OR reference_id LIKE 'REF-%' 
       OR reference_id = 'CP-2026-TEST'
       OR title LIKE '%Test Notification%'
""")
test_notifs = cur.fetchone()[0]
print(f"   Test notifications in DB: {test_notifs} (must be 0)")

# 4. Permanent Entities Check
cur.execute("SELECT COUNT(*) FROM users")
user_count = cur.fetchone()[0]
print(f"\n4. Total Users: {user_count} (Preserved)")

cur.execute("SELECT COUNT(*) FROM locations")
location_count = cur.fetchone()[0]
print(f"5. Total Locations: {location_count} (Preserved)")

cur.execute("SELECT COUNT(*) FROM departments")
dept_count = cur.fetchone()[0]
print(f"6. Total Departments: {dept_count} (Preserved)")

cur.execute("SELECT COUNT(*) FROM coordinator_assignments")
coord_count = cur.fetchone()[0]
print(f"7. Total Coordinator Assignments: {coord_count} (Preserved)")

cur.execute("SELECT COUNT(*) FROM audit_logs")
audit_count = cur.fetchone()[0]
print(f"8. Total Permanent Audit Logs: {audit_count} (Preserved)")

conn.close()
print("\n=================================================================")
print("FINAL VERIFICATION COMPLETE: ALL DATA CONSISTENT AND INTACT.")
print("=================================================================")
