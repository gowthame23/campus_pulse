import sqlite3

conn = sqlite3.connect("Backend/storage/campus_pulse.db")

# Clear out any stale USR_COORDINATOR references
conn.execute("UPDATE departments SET coordinator_id = NULL WHERE coordinator_id = 'USR_COORDINATOR'")
conn.execute("UPDATE departments SET coordinator_2_id = NULL WHERE coordinator_2_id = 'USR_COORDINATOR'")

# Set Electrical coordinators
conn.execute("UPDATE departments SET coordinator_id = 'USR_EMP_A1', coordinator_2_id = 'USR_EMP_A2' WHERE department_id = 'DEPT_HOSTEL_ELECTRICAL'")

# Set Plumbing coordinators
conn.execute("UPDATE departments SET coordinator_id = 'USR_EMP_B1', coordinator_2_id = 'USR_EMP_B2' WHERE department_id = 'DEPT_HOSTEL_PLUMBING'")

# Ensure all other departments have None
conn.execute("UPDATE departments SET coordinator_id = NULL, coordinator_2_id = NULL WHERE department_id NOT IN ('DEPT_HOSTEL_ELECTRICAL', 'DEPT_HOSTEL_PLUMBING')")

# Sync coordinator_assignments table
conn.execute("DELETE FROM coordinator_assignments")
conn.execute("""
    INSERT INTO coordinator_assignments (assignment_id, coordinator_id, location_id, department_id, assigned_by, assigned_at, status)
    VALUES 
    ('CASG_ELEC_1', 'USR_EMP_A1', 'ALL', 'DEPT_HOSTEL_ELECTRICAL', 'admin', datetime('now'), 'Active'),
    ('CASG_ELEC_2', 'USR_EMP_A2', 'ALL', 'DEPT_HOSTEL_ELECTRICAL', 'admin', datetime('now'), 'Active'),
    ('CASG_PLUMB_1', 'USR_EMP_B1', 'ALL', 'DEPT_HOSTEL_PLUMBING', 'admin', datetime('now'), 'Active'),
    ('CASG_PLUMB_2', 'USR_EMP_B2', 'ALL', 'DEPT_HOSTEL_PLUMBING', 'admin', datetime('now'), 'Active')
""")

conn.commit()

depts = conn.execute("SELECT department_id, name, coordinator_id, coordinator_2_id FROM departments WHERE coordinator_id IS NOT NULL OR coordinator_2_id IS NOT NULL").fetchall()
print("Configured Department Coordinators:")
for d in depts:
    print(d)

conn.close()
