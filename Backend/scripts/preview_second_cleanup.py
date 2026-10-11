import sqlite3

conn = sqlite3.connect(r'c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co\Backend\storage\campus_pulse.db')
cur = conn.cursor()

cur.execute('SELECT complaint_id, title, created_at FROM complaints ORDER BY created_at ASC')
all_complaints = cur.fetchall()
print(f'Total complaints now: {len(all_complaints)}')
print('Baseline complaints (to keep):')
for c in all_complaints[:9]:
    print(f'  {c[0]} | {c[1][:40]} | {c[2]}')

test_complaints = all_complaints[9:]
if test_complaints:
    print(f'\nTest complaints created during testing ({len(test_complaints)} to delete):')
    for c in test_complaints:
        print(f'  {c[0]} | {c[1][:40]} | {c[2]}')

# Check notifications referencing these test complaints
test_cid_placeholders = ','.join(['?'] * len(test_complaints))
test_cids = [c[0] for c in test_complaints]

cur.execute(f"SELECT COUNT(*) FROM notifications WHERE reference_id IN ({test_cid_placeholders})", test_cids)
test_notif_count = cur.fetchone()[0]
print(f'\nNotifications referencing test complaints: {test_notif_count}')

# Check notifications referencing test refs like CP-2026-TEST or REF-%
cur.execute("SELECT notification_id, title, reference_id FROM notifications WHERE reference_id = 'CP-2026-TEST' OR reference_id LIKE 'REF-%'")
other_test_notifs = cur.fetchall()
print(f'Other test notifications from notification test: {len(other_test_notifs)}')

# Check temp users
cur.execute("SELECT user_id, name, email FROM users WHERE name LIKE '%Temp%' OR email LIKE '%temp%'")
temp_users = cur.fetchall()
print(f'Temp users found: {temp_users}')

conn.close()
