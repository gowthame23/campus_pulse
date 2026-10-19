import json
import re

def generate_pg_ddl():
    with open('Backend/storage/schema_inspection.json') as f:
        schema = json.load(f)

    ddl_statements = []
    ddl_statements.append("-- =============================================================")
    ddl_statements.append("-- Campus Pulse — PostgreSQL Production Schema")
    ddl_statements.append("-- Generated from verified SQLite baseline schema (215 tables)")
    ddl_statements.append("-- =============================================================\n")
    ddl_statements.append("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";\n")

    # Priority tables to create first (for foreign keys & dependencies)
    priority_order = [
        "institutions", "organizations", "organization_units",
        "location_types", "locations", "departments", "users",
        "teams", "team_members", "team_locations", "user_leaves",
        "complaints", "comments", "highlights", "attachments",
        "notifications", "notification_preferences",
        "emergency_categories", "emergency_calls", "emergency_hotlines",
        "safety_reports", "safety_report_identity", "safety_report_messages",
        "lost_found_items", "ownership_claims",
        "scheduler_lock", "system_settings", "department_sla_configs"
    ]

    all_tables = list(schema.keys())
    sorted_tables = [t for t in priority_order if t in all_tables]
    remaining = [t for t in all_tables if t not in sorted_tables]
    sorted_tables.extend(sorted(remaining))

    for table_name in sorted_tables:
        info = schema[table_name]
        cols = info['columns']
        
        col_defs = []
        pks = []

        for c in sorted(cols, key=lambda x: x['cid']):
            c_name = c['name']
            c_type = c['type'].upper()
            is_pk = c['pk'] > 0
            not_null = bool(c['notnull'])
            dflt = c['dflt_value']

            # Type mapping
            if c_type == 'INTEGER':
                pg_type = 'INTEGER'
            elif c_type == 'REAL':
                pg_type = 'DOUBLE PRECISION'
            else:
                pg_type = 'TEXT'

            line = f'    "{c_name}" {pg_type}'
            
            # Default value handling
            if dflt is not None:
                d_str = str(dflt).strip()
                if d_str.upper() == "CURRENT_TIMESTAMP":
                    line += " DEFAULT CURRENT_TIMESTAMP"
                elif d_str.upper() in ("'ACTIVE'", "'PENDING'", "'SUBMITTED'", "'OPEN'", "'INACTIVE'"):
                    line += f" DEFAULT {d_str}"
                elif d_str in ("0", "1"):
                    line += f" DEFAULT {d_str}"
                elif d_str.startswith("'") and d_str.endswith("'"):
                    line += f" DEFAULT {d_str}"
                else:
                    line += f" DEFAULT '{d_str}'"

            if not_null and not is_pk:
                line += " NOT NULL"

            col_defs.append(line)
            if is_pk:
                pks.append((c['pk'], c_name))

        # Handle Primary Keys
        if pks:
            pks_sorted = [f'"{x[1]}"' for x in sorted(pks, key=lambda x: x[0])]
            col_defs.append(f'    PRIMARY KEY ({", ".join(pks_sorted)})')

        table_ddl = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n' + ',\n'.join(col_defs) + '\n);'
        ddl_statements.append(table_ddl)

    # Core compound indexes for high performance
    ddl_statements.append("\n-- Performance Optimization Compound Indexes")
    ddl_statements.append('CREATE INDEX IF NOT EXISTS "idx_complaints_status_deleted" ON "complaints" ("status", "is_deleted");')
    ddl_statements.append('CREATE INDEX IF NOT EXISTS "idx_complaints_assigned_deleted" ON "complaints" ("assigned_employee_id", "is_deleted");')
    ddl_statements.append('CREATE INDEX IF NOT EXISTS "idx_complaints_dept_loc" ON "complaints" ("department_id", "location_id");')
    ddl_statements.append('CREATE INDEX IF NOT EXISTS "idx_complaints_created_by" ON "complaints" ("created_by");')
    ddl_statements.append('CREATE INDEX IF NOT EXISTS "idx_notifications_user_unread" ON "notifications" ("user_id", "is_read");')
    ddl_statements.append('CREATE INDEX IF NOT EXISTS "idx_user_activities_user" ON "user_activities" ("user_id", "created_at");')

    full_sql = '\n\n'.join(ddl_statements) + '\n'

    with open('Backend/storage/postgres_schema.sql', 'w', encoding='utf-8') as f:
        f.write(full_sql)

    print(f"Generated PostgreSQL DDL for {len(sorted_tables)} tables in Backend/storage/postgres_schema.sql")

if __name__ == '__main__':
    generate_pg_ddl()
