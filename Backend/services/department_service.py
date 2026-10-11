class DepartmentService:
    def __init__(self, auth_service, validation_service, dependency_service):
        self.auth_service = auth_service
        self.validation_service = validation_service
        self.dependency_service = dependency_service

    def list_departments(self, include_archived=False, user_role=None, location_id=None):
        depts = self.auth_service.list_departments()
        if location_id:
            loc = self.auth_service.get_location(location_id)
            if loc:
                loc_id = loc.location_id
                loc_type = getattr(loc, "location_type", None) or loc.infer_location_type(loc.name)
            else:
                loc_id = location_id
                loc_type = location_id

            specific_depts = [d for d in depts if d.location_id == loc_id]
            if specific_depts:
                depts = specific_depts
            else:
                # Map canonical location types to their seed template location IDs
                type_to_template_id = {
                    "Hostel": "LOC_HOSTEL_A",
                    "Academic Block": "LOC_ACADEMIC",
                    "Mess": "LOC_MESS",
                    "Student Activity Center": "LOC_SAC",
                    "Sports Complex": "LOC_SPORTS",
                    "Other / Not Sure": "LOC_OTHER",
                }
                template_id = type_to_template_id.get(loc_type)

                depts = [
                    d for d in depts
                    if d.location_id == loc_id or d.location_id == loc_type or (template_id and d.location_id == template_id)
                ]
        if user_role == "student" or not include_archived:
            return [d for d in depts if not d.archived]
        return depts

    def get_department(self, department_id):
        dept = self.auth_service.get_department(department_id)
        if not dept:
            raise ValueError("Department not found.")
        return dept

    def create_department(self, name, sla_days, complaint_types, location_id=None):
        self.validation_service.validate_unique_department_name(name, location_id=location_id)
        return self.auth_service.create_department(name, sla_days, complaint_types, location_id=location_id)

    def update_department(
        self,
        department_id,
        name=None,
        sla_days=None,
        complaint_types=None,
        coordinator_id=None,
        archived=None,
        archived_by_role=None,
        archived_by=None,
    ):
        dept = self.get_department(department_id)

        if name is not None and name != dept.name:
            self.validation_service.validate_unique_department_name(
                name, exclude_id=department_id, location_id=dept.location_id
            )
            dept.name = name

        if sla_days is not None:
            dept.sla_days = sla_days

        if complaint_types is not None:
            dept.complaint_types = complaint_types

        # Coordinator Assignment
        if coordinator_id is not None:
            if not coordinator_id or coordinator_id == "unassigned":
                dept.coordinator_id = None
                self.save_department(dept)
                with self.auth_service._connect() as conn:
                    conn.execute("UPDATE coordinator_assignments SET status = 'Inactive' WHERE department_id = ?", (department_id,))
                    conn.commit()
            else:
                loc_target = dept.location_id or "ALL"
                self.auth_service.assign_coordinator(
                    coordinator_id, loc_target, department_id, confirm_replacement=True
                )
                dept.coordinator_id = coordinator_id
                self.save_department(dept)
                coord = self.auth_service.get_user(coordinator_id)
                if coord:
                    coord.department_id = department_id
                    self.auth_service.save_user(coord)

        # Archiving flow
        if archived is not None:
            if archived and not dept.archived:
                dept.archived_by_role = archived_by_role
                dept.archived_by = archived_by
            elif not archived:
                dept.archived_by_role = None
                dept.archived_by = None
            dept.archived = archived
            if archived:
                # Remove coordinator assignment
                if dept.coordinator_id:
                    coord = self.auth_service.get_user(dept.coordinator_id)
                    if coord:
                        coord.department_id = None
                        self.auth_service.save_user(coord)
                    dept.coordinator_id = None
            else:
                if coordinator_id:
                    dept.coordinator_id = coordinator_id
                    coord = self.auth_service.get_user(coordinator_id)
                    if coord:
                        coord.department_id = department_id
                        self.auth_service.save_user(coord)

        self.auth_service.save_department(dept)
        return dept

    def delete_department(self, department_id):
        dept = self.get_department(department_id)

        # Bulk Delete Protection
        can_delete, reason = self.dependency_service.can_delete_department(
            department_id
        )
        if not can_delete:
            raise ValueError(
                f"Cannot delete department. Reason: {reason} Please archive instead."
            )

        self.auth_service.delete_department_data(department_id)
        return dept

    def _db_conn(self):
        import os
        import sqlite3

        db_p = getattr(self.auth_service, "db_path", None) or os.environ.get(
            "DATABASE_PATH", "storage/campus_pulse.db"
        )
        conn = sqlite3.connect(db_p)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_issues_table(self, conn):
        conn.execute("""
            CREATE TABLE IF NOT EXISTS department_issues (
                issue_id TEXT PRIMARY KEY,
                department_id TEXT NOT NULL,
                issue_name TEXT NOT NULL,
                description TEXT,
                active INTEGER DEFAULT 1,
                created_at TEXT
            )
        """)

    def list_department_issues(self, department_id=None):
        with self._db_conn() as conn:
            self._ensure_issues_table(conn)
            query = "SELECT * FROM department_issues WHERE 1=1"
            params = []
            if department_id:
                query += " AND department_id = ?"
                params.append(department_id)
            query += " ORDER BY issue_name ASC"
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def create_department_issue(self, department_id, issue_name, description=""):
        from utils.helper import generate_id, now_string
        iid = generate_id("ISS")
        created_at = now_string()
        with self._db_conn() as conn:
            self._ensure_issues_table(conn)
            conn.execute(
                "INSERT INTO department_issues (issue_id, department_id, issue_name, description, active, created_at) VALUES (?, ?, ?, ?, 1, ?)",
                (iid, department_id, issue_name.strip(), description or "", created_at),
            )
            conn.commit()
        return iid

    def update_department_issue(self, issue_id, issue_name=None, description=None, active=None):
        with self._db_conn() as conn:
            self._ensure_issues_table(conn)
            row = conn.execute("SELECT * FROM department_issues WHERE issue_id = ?", (issue_id,)).fetchone()
            if not row:
                raise ValueError("Issue not found")
            name = issue_name if issue_name is not None else row["issue_name"]
            desc = description if description is not None else row["description"]
            act = int(active) if active is not None else row["active"]
            conn.execute(
                "UPDATE department_issues SET issue_name = ?, description = ?, active = ? WHERE issue_id = ?",
                (name, desc, act, issue_id),
            )
            conn.commit()
            return True
