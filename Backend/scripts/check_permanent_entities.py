import sqlite3

db_path = r'c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co\Backend\storage\campus_pulse.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT role, COUNT(*) FROM users GROUP BY role")
print("User counts by role:")
for r, c in cur.fetchall():
    print(f"  {r}: {c}")

cur.execute("SELECT location_type, COUNT(*) FROM locations GROUP BY location_type")
print("\nLocation counts by type:")
for t, c in cur.fetchall():
    print(f"  {t}: {c}")

cur.execute("SELECT department_id, name FROM departments")
print("\nDepartments:")
for d_id, d_name in cur.fetchall():
    print(f"  {d_id}: {d_name}")

cur.execute("SELECT COUNT(*) FROM coordinator_assignments")
print(f"\nCoordinator assignments count: {cur.fetchone()[0]}")

conn.close()
