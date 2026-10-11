import sqlite3

conn = sqlite3.connect(r'c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co\Backend\storage\campus_pulse.db')
cur = conn.cursor()

cids = ['CMP-3251DA96', 'CMP-AFECFBE0']
placeholders = ','.join(['?']*len(cids))

for t in ['notification_user_dismissals', 'comments', 'attachments', 'affected_students', 'work_orders', 'asset_maintenance']:
    cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{t}'")
    if cur.fetchone():
        if t == 'notification_user_dismissals':
            cur.execute(f"""
                SELECT COUNT(*) FROM notification_user_dismissals
                WHERE notification_id IN (SELECT notification_id FROM notifications WHERE reference_id IN ({placeholders}) OR reference_id = 'CP-2026-TEST' OR reference_id LIKE 'REF-%')
            """, cids)
            print(f'{t}: {cur.fetchone()[0]}')
        else:
            cur.execute(f"SELECT COUNT(*) FROM {t} WHERE complaint_id IN ({placeholders})", cids)
            print(f'{t}: {cur.fetchone()[0]}')

conn.close()
