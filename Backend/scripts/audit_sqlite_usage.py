import os
import re

patterns = {
    'PRAGMA': re.compile(r'\bPRAGMA\b', re.I),
    'INSERT OR IGNORE': re.compile(r'\bINSERT\s+OR\s+IGNORE\b', re.I),
    'INSERT OR REPLACE': re.compile(r'\bINSERT\s+OR\s+REPLACE\b', re.I),
    'ON CONFLICT': re.compile(r'\bON\s+CONFLICT\b', re.I),
    'AUTOINCREMENT': re.compile(r'\bAUTOINCREMENT\b', re.I),
    'lastrowid': re.compile(r'\blastrowid\b', re.I),
    'datetime_now': re.compile(r'\bdatetime\s*\(\s*[\'"]now[\'"]', re.I),
    'strftime': re.compile(r'\bstrftime\b', re.I),
    'sqlite_master': re.compile(r'\bsqlite_master\b', re.I),
    'sqlite3': re.compile(r'\bsqlite3\b', re.I),
}

findings = {k: [] for k in patterns}

for root, dirs, files in os.walk('Backend'):
    # Ignore virtualenvs, caches, node_modules if any
    if any(ignore in root for ignore in ['.pytest_cache', '__pycache__', '.venv', 'venv']):
        continue
    for f in files:
        if f.endswith('.py'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fl:
                for line_no, line in enumerate(fl, start=1):
                    for k, pat in patterns.items():
                        if pat.search(line):
                            findings[k].append({
                                'file': p.replace('\\', '/'),
                                'line': line_no,
                                'content': line.strip()
                            })

print("=== SQLITE-SPECIFIC PATTERN AUDIT ===")
for k, items in findings.items():
    print(f"{k:<20}: {len(items)} occurrences across {len(set(x['file'] for x in items))} files")

import json
with open('Backend/storage/sqlite_pattern_audit.json', 'w') as out:
    json.dump(findings, out, indent=2)
print("\nSaved detailed audit to Backend/storage/sqlite_pattern_audit.json")
