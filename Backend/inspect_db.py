import sqlite3
import json
from pathlib import Path

db_path = Path("Backend/storage/campus_pulse.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

tables = [row[0] for row in cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
print(f"Total tables: {len(tables)}")

table_counts = {}
for t in tables:
    cnt = cursor.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    table_counts[t] = cnt

print(json.dumps(table_counts, indent=2))
