import sqlite3

db_path = r'c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co\Backend\storage\campus_pulse.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

try:
    conn.execute("BEGIN TRANSACTION")

    # 1. Fetch all complaints
    cur.execute("SELECT complaint_id, title, created_at FROM complaints ORDER BY created_at ASC")
    all_complaints = cur.fetchall()
    
    baseline_complaints = all_complaints[:9]
    test_complaints = all_complaints[9:]
    test_ids = [c[0] for c in test_complaints]

    print(f"Total complaints before second cleanup: {len(all_complaints)}")
    print(f"Baseline complaints to keep: {len(baseline_complaints)}")
    print(f"Test complaints to remove: {len(test_complaints)}")

    # 2. Identify test notifications
    cur.execute("""
        SELECT notification_id FROM notifications 
        WHERE reference_id IN (SELECT complaint_id FROM complaints WHERE title LIKE 'TEST_%' OR complaint_id NOT IN (
            SELECT complaint_id FROM complaints ORDER BY created_at ASC LIMIT 9
        ))
        OR reference_id = 'CP-2026-TEST'
        OR reference_id LIKE 'REF-%'
        OR title LIKE '%Test Notification%'
    """)
    test_notif_ids = [r[0] for r in cur.fetchall()]
    print(f"Test notifications to remove: {len(test_notif_ids)}")

    if test_notif_ids:
        placeholders = ','.join(['?'] * len(test_notif_ids))
        cur.execute(f"DELETE FROM notification_user_dismissals WHERE notification_id IN ({placeholders})", test_notif_ids)
        print(f"Deleted notification dismissals: {cur.rowcount}")

        cur.execute(f"DELETE FROM notifications WHERE notification_id IN ({placeholders})", test_notif_ids)
        print(f"Deleted test notifications: {cur.rowcount}")

    # 3. Clean up test complaints
    if test_ids:
        c_placeholders = ','.join(['?'] * len(test_ids))
        for table in ['affected_students', 'comments', 'attachments']:
            cur.execute(f"DELETE FROM {table} WHERE complaint_id IN ({c_placeholders})", test_ids)
            print(f"Deleted {cur.rowcount} rows from {table}")

        cur.execute(f"DELETE FROM complaints WHERE complaint_id IN ({c_placeholders})", test_ids)
        print(f"Deleted complaints: {cur.rowcount}")

    conn.commit()
    print("\nSecond Cleanup: Transaction committed successfully.")

except Exception as e:
    conn.rollback()
    print(f"Second Cleanup failed and rolled back: {e}")
    raise
finally:
    conn.close()
