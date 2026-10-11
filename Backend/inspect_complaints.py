import sqlite3
from pathlib import Path

db_path = Path("Backend/storage/campus_pulse.db")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

rows = cursor.execute("SELECT * FROM complaints ORDER BY created_at ASC LIMIT 35").fetchall()
print(f"Total complaints: {len(rows)}")

for idx, r in enumerate(rows, 1):
    cid = r["complaint_id"]
    title = r["title"] or ""
    desc = r["description"] or ""
    created = r["created_at"] or ""
    creator = r["created_by"] or ""
    status = r["status"] or ""
    loc = r["location_id"] or ""
    dept = r["department_id"] or ""
    
    # Check if title or desc indicates disposable test
    is_test_flag = any(kw in (title + desc).lower() for kw in ["test", "ownership deletion", "sparking in room", "400941", "b0a7e8", "96292c", "b59ae3", "333e90", "a1bbb2", "712694"])
    
    print(f"{idx:02d}. [{cid}] {created} | by {creator} | loc={loc} | dept={dept} | {status} | {'[TEST]' if is_test_flag else '[REAL/UNKNOWN]'} | {title[:35]} | {desc[:40]}")
