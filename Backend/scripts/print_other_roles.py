import json

with open('scripts/user_inspection_dump.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for r in ['administrator', 'app_manager', 'coordinator', 'location_in_charge', 'super_admin']:
    ulist = [u for u in data if u['role'] == r]
    print(f"\n=== ROLE: {r} (Count: {len(ulist)}) ===")
    for u in ulist:
        print(f"  {u['user_id']:<20} | {u['email']:<32} | {u['name']:<25} | "
              f"created={u['cmps_created']} asgn={u['cmps_assigned']} loc_ic={u['locs_in_charge']} "
              f"loc_mgr={u['locs_app_mgr']} coord={u['coord_asgns']} notif={u['notifs_rec']}")
