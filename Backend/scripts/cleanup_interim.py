import sqlite3

conn = sqlite3.connect(r'c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co\Backend\storage\campus_pulse.db')
cur = conn.cursor()
cur.execute("SELECT complaint_id, title FROM complaints WHERE complaint_id = 'CMP-1DD571FD'")
rows = cur.fetchall()
print("Found:", rows)
if rows:
    cur.execute("DELETE FROM notifications WHERE reference_id = 'CMP-1DD571FD'")
    cur.execute("DELETE FROM complaints WHERE complaint_id = 'CMP-1DD571FD'")
    conn.commit()
    print("Deleted CMP-1DD571FD and its notifications.")
conn.close()
