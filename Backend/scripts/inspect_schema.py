import sqlite3

db_path = r'c:\Users\gowth\OneDrive\Desktop\GOWTHAM\CampusPulse\CampusPulse_co\Backend\storage\campus_pulse.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cur.fetchall()]

complaint_tables = []
for t in tables:
    cur.execute(f"PRAGMA table_info('{t}')")
    cols = [c[1] for c in cur.fetchall()]
    if 'complaint_id' in cols:
        complaint_tables.append(t)

print('Tables containing complaint_id column:')
for t in complaint_tables:
    print(' -', t)

# Also check for tables with foreign keys referencing complaints
print('\nForeign keys referencing complaints table:')
for t in tables:
    cur.execute(f"PRAGMA foreign_key_list('{t}')")
    fks = cur.fetchall()
    for fk in fks:
        if fk[2] == 'complaints':
            print(f' - {t} -> {fk}')

conn.close()
