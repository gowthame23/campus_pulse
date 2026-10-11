import sqlite3

db_path = r'c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co\Backend\storage\campus_pulse.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute('SELECT complaint_id, title, status, created_at FROM complaints ORDER BY created_at ASC')
all_complaints = cur.fetchall()

print(f'Total complaints: {len(all_complaints)}')

# The first 9 complaints
baseline_complaints = all_complaints[:9]
test_complaints = all_complaints[9:]

print('\nBaseline Complaints (to preserve):')
for c in baseline_complaints:
    print(f'  {c[0]} | {c[1][:40]} | {c[2]} | {c[3]}')

print(f'\nTest complaints count to remove: {len(test_complaints)}')
print('First 5 test complaints:')
for c in test_complaints[:5]:
    print(f'  {c[0]} | {c[1][:40]} | {c[2]} | {c[3]}')
print('Last 5 test complaints:')
for c in test_complaints[-5:]:
    print(f'  {c[0]} | {c[1][:40]} | {c[2]} | {c[3]}')

test_ids = [c[0] for c in test_complaints]
test_ids_placeholders = ','.join(['?']*len(test_ids))

# Check related tables
cur.execute(f"SELECT COUNT(*) FROM notifications WHERE reference_type = ? AND reference_id IN ({test_ids_placeholders})", ['Complaint'] + test_ids)
notif_count = cur.fetchone()[0]
print(f'\nNotifications referencing test complaints: {notif_count}')

cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='notification_user_dismissals'")
if cur.fetchone():
    cur.execute(f"""
        SELECT COUNT(*) FROM notification_user_dismissals 
        WHERE notification_id IN (
            SELECT notification_id FROM notifications WHERE reference_type = 'Complaint' AND reference_id IN ({test_ids_placeholders})
        )
    """, test_ids)
    dismiss_count = cur.fetchone()[0]
    print(f'Notification dismissals referencing test notifications: {dismiss_count}')
else:
    print('notification_user_dismissals table does not exist')

for table in ['complaint_history', 'comments', 'attachments', 'affected_students']:
    cur.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
    if cur.fetchone():
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table} WHERE complaint_id IN ({test_ids_placeholders})", test_ids)
            print(f'{table} rows referencing test complaints: {cur.fetchone()[0]}')
        except Exception as e:
            print(f'{table} error: {e}')

conn.close()
