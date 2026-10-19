import sqlite3
import json

def inspect():
    conn = sqlite3.connect('Backend/storage/campus_pulse.db')
    cur = conn.cursor()
    cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = cur.fetchall()
    print(f"Total Tables: {len(tables)}\n")
    
    schema_info = {}
    for name, sql in tables:
        count = conn.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
        cur.execute(f"PRAGMA table_info({name})")
        columns = [
            {
                "cid": col[0],
                "name": col[1],
                "type": col[2],
                "notnull": col[3],
                "dflt_value": col[4],
                "pk": col[5]
            }
            for col in cur.fetchall()
        ]
        cur.execute(f"PRAGMA foreign_key_list({name})")
        fks = [
            {
                "id": fk[0],
                "seq": fk[1],
                "table": fk[2],
                "from": fk[3],
                "to": fk[4],
                "on_update": fk[5],
                "on_delete": fk[6]
            }
            for fk in cur.fetchall()
        ]
        schema_info[name] = {
            "row_count": count,
            "sql": sql,
            "columns": columns,
            "foreign_keys": fks
        }
        print(f"Table: {name:<30} Rows: {count:<6} Columns: {len(columns)}")

    with open("Backend/storage/schema_inspection.json", "w") as f:
        json.dump(schema_info, f, indent=2)
    print("\nDetailed schema written to Backend/storage/schema_inspection.json")

if __name__ == "__main__":
    inspect()
