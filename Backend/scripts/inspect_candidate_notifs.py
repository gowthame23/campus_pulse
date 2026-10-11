import sqlite3

db_path = r'c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co\Backend\storage\campus_pulse.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

REQUIRED_IDS = {
    "USR_ADMIN", "USR_MANAGER", "USR_MANAGER_2", "USR_WARDEN", "USR_WARDEN_2",
    "USR_COORDINATOR", "USR_COORDINATOR_2", "USR_STUDENT", "USR_STUDENT_2",
    "USR_SUPER_ADMIN", "USR-2AB3A96E"
}

all_users = cur.execute("SELECT user_id FROM users").fetchall()
test_user_ids = [u["user_id"] for u in all_users if u["user_id"] not in REQUIRED_IDS]
placeholders = ','.join(['?'] * len(test_user_ids))

cur.execute(f"SELECT notification_id, receiver_id, title, message FROM notifications WHERE receiver_id IN ({placeholders})", test_user_ids)
rows = cur.fetchall()
print(f"Notifications found: {len(rows)}")
for r in rows:
    print(f"  {r['notification_id']} | {r['receiver_id']} | {r['title']} | {r['message'][:50]}")

conn.close()
