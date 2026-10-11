import sqlite3

conn = sqlite3.connect(r'c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co\Backend\storage\campus_pulse.db')
cur = conn.cursor()

cur.execute("SELECT user_id, name, email FROM users WHERE email LIKE '%temp%' OR name LIKE '%Temp%'")
temp_users = cur.fetchall()
print('Temp users in DB:', temp_users)

cur.execute('SELECT complaint_id, title, created_at FROM complaints ORDER BY created_at ASC')
cmps = cur.fetchall()
print('Complaints in DB:', len(cmps))
for c in cmps[:9]:
    print('  Baseline:', c[0], c[1])
for c in cmps[9:]:
    print('  Test complaint to remove:', c[0], c[1])

cur.execute("""
    SELECT COUNT(*) FROM notifications 
    WHERE reference_id IN (SELECT complaint_id FROM complaints ORDER BY created_at ASC LIMIT -1 OFFSET 9)
       OR reference_id = 'CP-2026-TEST'
       OR reference_id LIKE 'REF-%'
       OR title LIKE '%Test Notification%'
""")
notif_count = cur.fetchone()[0]
print('Test notifications to remove:', notif_count)

conn.close()
