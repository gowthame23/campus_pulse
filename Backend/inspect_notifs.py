import sqlite3
from pathlib import Path

db_path = Path("Backend/storage/campus_pulse.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

total_notifs = cursor.execute("SELECT COUNT(*) FROM notifications").fetchone()[0]
print(f"Total notifications: {total_notifs}")

# Sample breakdown by module
modules = cursor.execute("SELECT module, COUNT(*) as cnt FROM notifications GROUP BY module").fetchall()
for m in modules:
    print(f"Module: {m['module']} -> {m['cnt']}")

# Sample breakdown by reference_type
refs = cursor.execute("SELECT reference_type, COUNT(*) as cnt FROM notifications GROUP BY reference_type").fetchall()
for r in refs:
    print(f"Ref Type: {r['reference_type']} -> {r['cnt']}")

# Look at notifications linked to complaints
complaint_notifs = cursor.execute("SELECT notification_id, user_id, title, message, reference_id, created_at FROM notifications WHERE module = 'Complaints' OR reference_type = 'Complaint' LIMIT 20").fetchall()
print("\nSample Complaint Notifications:")
for n in complaint_notifs:
    print(f"[{n['notification_id']}] user={n['user_id']} | title={n['title']} | ref={n['reference_id']} | {n['created_at']}")
