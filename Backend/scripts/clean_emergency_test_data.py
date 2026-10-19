import sqlite3

db_path = "Backend/storage/campus_pulse.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

# 1. Delete test categories (EMCAT-%)
cur = conn.execute("DELETE FROM emergency_categories WHERE category_id LIKE 'EMCAT-%'")
print(f"Deleted {cur.rowcount} test emergency categories.")

# 2. Delete test contacts (EMCNT-%)
cur = conn.execute("DELETE FROM emergency_contacts WHERE contact_id LIKE 'EMCNT-%'")
print(f"Deleted {cur.rowcount} test emergency contacts.")

# 3. Delete accidental test complaint from clicking General Misuse Test
cur = conn.execute("DELETE FROM complaints WHERE complaint_id = 'CMP-7CB1333D'")
print(f"Deleted {cur.rowcount} test complaint.")

# 4. Delete notifications for that complaint
cur = conn.execute("DELETE FROM notifications WHERE reference_id = 'CMP-7CB1333D'")
print(f"Deleted {cur.rowcount} test notifications.")

conn.commit()

# Verify remaining categories
remaining_cats = conn.execute("SELECT category_id, name, department_id, is_active, sort_order FROM emergency_categories ORDER BY sort_order ASC, name ASC").fetchall()
print(f"\n=== CLEAN REMAINING CATEGORIES ({len(remaining_cats)}) ===")
for c in remaining_cats:
    print(f"  {c['category_id']}: {c['name']} (dept: {c['department_id']}, sort: {c['sort_order']})")

remaining_contacts = conn.execute("SELECT * FROM emergency_contacts").fetchall()
print(f"\nRemaining contacts count: {len(remaining_contacts)}")

remaining_complaints = conn.execute("SELECT * FROM complaints").fetchall()
print(f"Remaining complaints count: {len(remaining_complaints)}")

conn.close()
