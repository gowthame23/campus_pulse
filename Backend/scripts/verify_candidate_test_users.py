import sqlite3

db_path = r'c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co\Backend\storage\campus_pulse.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Accounts to keep unconditionally
REQUIRED_IDS = {
    "USR_ADMIN",
    "USR_MANAGER",
    "USR_MANAGER_2",
    "USR_WARDEN",
    "USR_WARDEN_2",
    "USR_COORDINATOR",
    "USR_COORDINATOR_2",
    "USR_STUDENT",
    "USR_STUDENT_2",
    "USR_SUPER_ADMIN",
    "USR-2AB3A96E", # Gowtham Student - uncertain/user account -> PRESERVE for manual review
}

all_users = cur.execute("SELECT user_id, email, name, role FROM users").fetchall()
test_users = [u for u in all_users if u["user_id"] not in REQUIRED_IDS]

print(f"Total Users: {len(all_users)}")
print(f"Required / Preserved Users: {len(REQUIRED_IDS)}")
print(f"Candidate Disposable Test Users to Remove: {len(test_users)}\n")

test_user_ids = [u["user_id"] for u in test_users]
test_user_placeholders = ','.join(['?'] * len(test_user_ids))

# 1. Any complaints created or assigned?
cur.execute(f"SELECT COUNT(*) FROM complaints WHERE created_by IN ({test_user_placeholders}) OR assigned_to IN ({test_user_placeholders})", test_user_ids + test_user_ids)
c_count = cur.fetchone()[0]
print(f"Complaints referencing candidate test users: {c_count}")

# 2. Any locations referencing candidate test users?
cur.execute(f"SELECT COUNT(*) FROM locations WHERE in_charge_id IN ({test_user_placeholders}) OR app_manager_id IN ({test_user_placeholders})", test_user_ids + test_user_ids)
loc_count = cur.fetchone()[0]
print(f"Locations referencing candidate test users: {loc_count}")

# 3. Any coordinator assignments?
cur.execute(f"SELECT COUNT(*) FROM coordinator_assignments WHERE coordinator_id IN ({test_user_placeholders})", test_user_ids)
ca_count = cur.fetchone()[0]
print(f"Coordinator assignments referencing candidate test users: {ca_count}")

# 4. Any notifications?
cur.execute(f"SELECT COUNT(*) FROM notifications WHERE receiver_id IN ({test_user_placeholders}) OR sender_id IN ({test_user_placeholders})", test_user_ids + test_user_ids)
notif_count = cur.fetchone()[0]
print(f"Notifications referencing candidate test users: {notif_count}")

# 5. Any notification user dismissals?
cur.execute(f"SELECT COUNT(*) FROM notification_user_dismissals WHERE user_id IN ({test_user_placeholders})", test_user_ids)
nud_count = cur.fetchone()[0]
print(f"Notification dismissals referencing candidate test users: {nud_count}")

# 6. Any student profiles or staff profiles?
cur.execute(f"SELECT COUNT(*) FROM student_profiles WHERE user_id IN ({test_user_placeholders})", test_user_ids)
sp_count = cur.fetchone()[0]
cur.execute(f"SELECT COUNT(*) FROM staff_profiles WHERE user_id IN ({test_user_placeholders})", test_user_ids)
stf_count = cur.fetchone()[0]
print(f"Profiles: student_profiles={sp_count}, staff_profiles={stf_count}")

conn.close()
