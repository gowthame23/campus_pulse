import sqlite3

db_path = r'c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co\Backend\storage\campus_pulse.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute('SELECT complaint_id FROM complaints ORDER BY created_at ASC')
all_complaints = [r[0] for r in cur.fetchall()]
baseline_ids = all_complaints[:9]
test_ids = all_complaints[9:]
test_placeholders = ','.join(['?']*len(test_ids))

for t in ['work_orders', 'asset_maintenance', 'comments', 'attachments', 'affected_students']:
    cur.execute(f"SELECT COUNT(*) FROM {t} WHERE complaint_id IN ({test_placeholders})", test_ids)
    print(f'{t}: {cur.fetchone()[0]} rows referencing test complaints')

conn.close()
