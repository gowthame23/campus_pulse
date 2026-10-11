import sqlite3
import json

db_path = r'c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co\Backend\storage\campus_pulse.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Find chat table
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
all_tables = [r[0] for r in cur.fetchall()]
chat_table = None
for candidate in ['chat_messages', 'messages', 'personal_messages', 'chats']:
    if candidate in all_tables:
        chat_table = candidate
        break

print(f"Chat table identified: {chat_table}")

users = cur.execute("SELECT user_id, name, email, role, status, active, created_at, created_by FROM users ORDER BY role, user_id").fetchall()
print(f"Total Users Found: {len(users)}\n")

user_details = []
for u in users:
    uid = u["user_id"]
    email = u["email"]
    role = u["role"]
    name = u["name"]

    # Complaints created
    cur.execute("SELECT COUNT(*) FROM complaints WHERE created_by = ?", (uid,))
    cmps_created = cur.fetchone()[0]

    # Complaints assigned
    cur.execute("SELECT COUNT(*) FROM complaints WHERE assigned_to = ?", (uid,))
    cmps_assigned = cur.fetchone()[0]

    # Locations where in_charge
    cur.execute("SELECT COUNT(*) FROM locations WHERE in_charge_id = ?", (uid,))
    locs_in_charge = cur.fetchone()[0]

    # Locations where app_manager
    cur.execute("SELECT COUNT(*) FROM locations WHERE app_manager_id = ?", (uid,))
    locs_app_mgr = cur.fetchone()[0]

    # Coordinator assignments
    cur.execute("SELECT COUNT(*) FROM coordinator_assignments WHERE coordinator_id = ?", (uid,))
    coord_asgns = cur.fetchone()[0]

    # Notifications received
    cur.execute("SELECT COUNT(*) FROM notifications WHERE receiver_id = ?", (uid,))
    notifs_rec = cur.fetchone()[0]

    # Chat messages sent or received
    chat_msgs = 0
    if chat_table:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {chat_table} WHERE sender_id = ? OR recipient_id = ?", (uid, uid))
            chat_msgs = cur.fetchone()[0]
        except Exception:
            pass

    # Audit logs
    cur.execute("SELECT COUNT(*) FROM audit_logs WHERE user_id = ? OR entity_id = ? OR target_id = ?", (uid, uid, uid))
    audit_logs = cur.fetchone()[0]

    info = {
        "user_id": uid,
        "name": name,
        "email": email,
        "role": role,
        "status": u["status"],
        "active": u["active"],
        "created_at": u["created_at"],
        "created_by": u["created_by"],
        "cmps_created": cmps_created,
        "cmps_assigned": cmps_assigned,
        "locs_in_charge": locs_in_charge,
        "locs_app_mgr": locs_app_mgr,
        "coord_asgns": coord_asgns,
        "notifs_rec": notifs_rec,
        "chat_msgs": chat_msgs,
        "audit_logs": audit_logs,
    }
    user_details.append(info)

# Print grouped by role
by_role = {}
for u in user_details:
    by_role.setdefault(u["role"], []).append(u)

for r, ulist in by_role.items():
    print(f"\n=== ROLE: {r} (Count: {len(ulist)}) ===")
    for u in ulist:
        print(f"  {u['user_id']:<20} | {u['email']:<32} | {u['name']:<25} | "
              f"created={u['cmps_created']} asgn={u['cmps_assigned']} loc_ic={u['locs_in_charge']} "
              f"loc_mgr={u['locs_app_mgr']} coord={u['coord_asgns']} notif={u['notifs_rec']} "
              f"chat={u['chat_msgs']} audit={u['audit_logs']}")

conn.close()

with open(r'c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co\Backend\scripts\user_inspection_dump.json', 'w', encoding='utf-8') as f:
    json.dump(user_details, f, indent=2)
