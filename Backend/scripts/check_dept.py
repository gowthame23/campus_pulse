import sqlite3

db_path = r'c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co\Backend\storage\campus_pulse.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT * FROM departments WHERE department_id = 'DEPT-7C5A7022'")
print("DEPT-7C5A7022:", cur.fetchall())

cur.execute("SELECT * FROM coordinator_assignments WHERE department_id = 'DEPT-7C5A7022'")
print("Coordinator assignments for DEPT-7C5A7022:", cur.fetchall())

cur.execute("SELECT * FROM complaints WHERE department_id = 'DEPT-7C5A7022'")
print("Complaints for DEPT-7C5A7022:", cur.fetchall())

conn.close()
