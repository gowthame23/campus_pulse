import sqlite3

db_path = r'c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co\Backend\storage\campus_pulse.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM complaints")
complaint_count = cur.fetchone()[0]

cur.execute("SELECT complaint_id, title, status FROM complaints ORDER BY created_at ASC")
remaining_complaints = cur.fetchall()

cur.execute("SELECT COUNT(*) FROM notifications")
notif_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM users")
user_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM locations")
location_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM departments")
dept_count = cur.fetchone()[0]

cur.execute("SELECT COUNT(*) FROM coordinator_assignments")
coord_count = cur.fetchone()[0]

print(f"Remaining complaints count: {complaint_count}")
print("Remaining complaints list:")
for c in remaining_complaints:
    print(f"  {c[0]} | {c[1]} | {c[2]}")

print(f"\nRemaining notifications: {notif_count}")
print(f"Users count: {user_count} (preserved)")
print(f"Locations count: {location_count} (preserved)")
print(f"Departments count: {dept_count} (preserved)")
print(f"Coordinator assignments count: {coord_count} (preserved)")

conn.close()
