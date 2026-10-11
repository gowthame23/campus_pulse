import sqlite3

db_path = r'c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co\Backend\storage\campus_pulse.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

try:
    conn.execute("BEGIN TRANSACTION")

    # 1. Fetch all complaints ordered by created_at
    cur.execute("SELECT complaint_id, title, created_at FROM complaints ORDER BY created_at ASC")
    all_complaints = cur.fetchall()
    
    baseline_complaints = all_complaints[:9]
    test_complaints = all_complaints[9:]
    
    test_ids = [c[0] for c in test_complaints]
    print(f"Total complaints before cleanup: {len(all_complaints)}")
    print(f"Baseline complaints to keep: {len(baseline_complaints)}")
    print(f"Test complaints to remove: {len(test_complaints)}")

    if not test_ids:
        print("No test complaints to delete.")
    else:
        test_placeholders = ','.join(['?'] * len(test_ids))

        # Find test notifications
        cur.execute(f"SELECT notification_id FROM notifications WHERE reference_type = 'Complaint' AND reference_id IN ({test_placeholders})", test_ids)
        test_notif_ids = [r[0] for r in cur.fetchall()]
        print(f"Test notifications to remove: {len(test_notif_ids)}")

        if test_notif_ids:
            notif_placeholders = ','.join(['?'] * len(test_notif_ids))
            # Delete from notification_user_dismissals
            cur.execute(f"DELETE FROM notification_user_dismissals WHERE notification_id IN ({notif_placeholders})", test_notif_ids)
            print(f"Deleted notification dismissals: {cur.rowcount}")

            # Delete from notifications
            cur.execute(f"DELETE FROM notifications WHERE notification_id IN ({notif_placeholders})", test_notif_ids)
            print(f"Deleted notifications: {cur.rowcount}")

        # Delete any rows in other complaint-related tables just in case
        for table in ['affected_students', 'attachments', 'comments']:
            cur.execute(f"DELETE FROM {table} WHERE complaint_id IN ({test_placeholders})", test_ids)
            print(f"Deleted {cur.rowcount} rows from {table}")

        # Delete complaints
        cur.execute(f"DELETE FROM complaints WHERE complaint_id IN ({test_placeholders})", test_ids)
        print(f"Deleted complaints: {cur.rowcount}")

    conn.commit()
    print("Transaction committed successfully.")

except Exception as e:
    conn.rollback()
    print(f"Transaction failed and rolled back: {e}")
    raise
finally:
    conn.close()
