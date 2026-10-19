import re

def translate_query_sqlite_to_pg(sql: str) -> str:
    s = sql.strip()
    # 1. Ignore or strip PRAGMAs
    if re.match(r'^PRAGMA\s+', s, re.I):
        return 'SELECT 1'
    
    # 2. Translate INSERT OR IGNORE
    if re.search(r'\bINSERT\s+OR\s+IGNORE\s+INTO\b', s, re.I):
        s = re.sub(r'\bINSERT\s+OR\s+IGNORE\s+INTO\b', 'INSERT INTO', s, flags=re.I)
        if 'ON CONFLICT' not in s.upper():
            s = s.rstrip(';') + ' ON CONFLICT DO NOTHING;'

    # 3. Translate INSERT OR REPLACE
    if re.search(r'\bINSERT\s+OR\s+REPLACE\s+INTO\b', s, re.I):
        s = re.sub(r'\bINSERT\s+OR\s+REPLACE\s+INTO\b', 'INSERT INTO', s, flags=re.I)

    # 4. Translate datetime('now') and strftime
    s = re.sub(r"\bdatetime\s*\(\s*['\"]now['\"]\s*\)", 'CURRENT_TIMESTAMP', s, flags=re.I)
    s = re.sub(r"\bdate\s*\(\s*['\"]now['\"]\s*\)", 'CURRENT_DATE', s, flags=re.I)
    
    # strftime('%Y-%m', col) -> to_char(col, 'YYYY-MM')
    s = re.sub(r"\bstrftime\s*\(\s*'%Y-%m'\s*,\s*([^)]+)\)", r"to_char(\1::timestamp, 'YYYY-MM')", s, flags=re.I)
    s = re.sub(r"\bstrftime\s*\(\s*'%Y-%m-%d'\s*,\s*([^)]+)\)", r"to_char(\1::timestamp, 'YYYY-MM-DD')", s, flags=re.I)

    # 5. Translate sqlite_master
    s = re.sub(r'\bsqlite_master\b', 'information_schema.tables', s, flags=re.I)

    # 6. Replace ? with %s while escaping existing % signs outside placeholders
    parts = s.split('?')
    if len(parts) > 1:
        escaped_parts = [p.replace('%', '%%') for p in parts]
        s = '%s'.join(escaped_parts)
    return s

def test_translation():
    tests = [
        ('SELECT * FROM users WHERE email = ? AND active = ?',
         'SELECT * FROM users WHERE email = %s AND active = %s'),
        ('INSERT OR IGNORE INTO users (user_id, name) VALUES (?, ?);',
         'INSERT INTO users (user_id, name) VALUES (%s, %s) ON CONFLICT DO NOTHING;'),
        ("SELECT * FROM logs WHERE msg LIKE '%error%' AND level = ?",
         "SELECT * FROM logs WHERE msg LIKE '%%error%%' AND level = %s"),
        ('PRAGMA foreign_keys = ON;',
         'SELECT 1'),
        ("SELECT strftime('%Y-%m', created_at) as month, count(*) FROM complaints GROUP BY month",
         "SELECT to_char(created_at::timestamp, 'YYYY-MM') as month, count(*) FROM complaints GROUP BY month"),
    ]
    for orig, expected in tests:
        res = translate_query_sqlite_to_pg(orig)
        print(f"Orig:     {orig}")
        print(f"Result:   {res}")
        print(f"Expected: {expected}")
        assert res == expected, f"Mismatch: '{res}' != '{expected}'"
        print("MATCH!\n")
    print("All translation tests passed successfully!")

if __name__ == '__main__':
    test_translation()
