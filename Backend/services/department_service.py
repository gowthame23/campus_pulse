import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


class DepartmentService:
    def __init__(self, auth_service, validation_service, dependency_service, team_service=None):
        self.auth_service = auth_service
        self.validation_service = validation_service
        self.dependency_service = dependency_service
        self.team_service = team_service


    def list_departments(self, include_archived=False, user_role=None, location_id=None):
        if location_id:
            loc = self.auth_service.get_location(location_id)
            loc_id = loc.location_id if loc else location_id
            with self.auth_service._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT DISTINCT d.* FROM departments d
                    WHERE d.active = 1 AND (d.archived = 0 OR d.archived IS NULL)
                      AND (
                        d.department_id IN (
                            SELECT department_id FROM location_departments 
                            WHERE location_id = ? AND is_active = 1
                        )
                        OR (d.location_id IS NOT NULL AND d.location_id = ?)
                        OR (
                            d.department_id NOT IN (
                                SELECT department_id FROM location_departments WHERE is_active = 1
                            )
                            AND (d.location_id IS NULL OR d.location_id = '')
                        )
                      )
                    ORDER BY d.name ASC
                    """,
                    (loc_id, loc_id),
                ).fetchall()
            from models.department import Department
            depts = [Department.from_dict(self.auth_service.repository._row_to_department(r)) for r in rows]
        else:
            depts = self.auth_service.list_departments()

        if user_role == "student" or not include_archived:
            return [d for d in depts if not d.archived and d.active]
        return depts

    def get_department(self, department_id):
        dept = self.auth_service.get_department(department_id)
        if not dept:
            raise ValueError("Department not found.")
        return dept

    def get_department_operating_locations(self, department_id: str) -> List[Dict[str, Any]]:
        with self.auth_service._connect() as conn:
            rows = conn.execute(
                """
                SELECT l.* FROM locations l
                JOIN location_departments ld ON l.location_id = ld.location_id
                WHERE ld.department_id = ? AND ld.is_active = 1 AND l.active = 1 AND (l.archived = 0 OR l.archived IS NULL)
                ORDER BY l.name ASC
                """,
                (department_id,),
            ).fetchall()
            return [self.auth_service.repository._row_to_location(r) for r in rows]

    def get_department_operating_location_ids(self, department_id: str) -> List[str]:
        with self.auth_service._connect() as conn:
            rows = conn.execute(
                "SELECT location_id FROM location_departments WHERE department_id = ? AND is_active = 1",
                (department_id,),
            ).fetchall()
            return [r["location_id"] for r in rows]

    def assign_locations_to_department(
        self,
        department_id: str,
        location_ids: List[str],
        actor_user_id: Optional[str] = None,
        actor_role: Optional[str] = None,
    ) -> List[str]:
        dept = self.get_department(department_id)
        if not dept:
            raise ValueError("Department not found.")

        clean_ids = []
        seen = set()
        for l in (location_ids or []):
            if l and isinstance(l, str):
                lid = l.strip()
                if lid and lid not in seen:
                    seen.add(lid)
                    clean_ids.append(lid)

        # Validate that each location exists
        for lid in clean_ids:
            loc = self.auth_service.get_location(lid)
            if not loc:
                raise ValueError(f"Location '{lid}' does not exist.")

        # App Managers can only associate/disassociate locations within their authorized scope
        if actor_role and actor_role.lower() == "app_manager":
            existing_loc_ids = set(self.get_department_operating_location_ids(department_id))
            all_affected = existing_loc_ids.union(seen)
            for lid in all_affected:
                if not self.auth_service.is_app_manager_assigned(actor_user_id, lid):
                    raise PermissionError(
                        f"Unauthorized: App Managers can only manage department assignments for locations in their scope. Location '{lid}' is outside your authorized scope."
                    )

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.auth_service._connect() as conn:
            if not clean_ids:
                conn.execute(
                    "UPDATE location_departments SET is_active = 0 WHERE department_id = ?",
                    (department_id,),
                )
            else:
                placeholders = ",".join(["?"] * len(clean_ids))
                conn.execute(
                    f"UPDATE location_departments SET is_active = 0 WHERE department_id = ? AND location_id NOT IN ({placeholders})",
                    [department_id] + clean_ids,
                )
                for lid in clean_ids:
                    row = conn.execute(
                        "SELECT id FROM location_departments WHERE location_id = ? AND department_id = ?",
                        (lid, department_id),
                    ).fetchone()
                    if row:
                        conn.execute(
                            "UPDATE location_departments SET is_active = 1 WHERE location_id = ? AND department_id = ?",
                            (lid, department_id),
                        )
                    else:
                        map_id = f"LD_{uuid.uuid4().hex[:12]}"
                        conn.execute(
                            """
                            INSERT INTO location_departments (id, location_id, department_id, created_at, created_by, is_active)
                            VALUES (?, ?, ?, ?, ?, 1)
                            """,
                            (map_id, lid, department_id, now_str, actor_user_id or "system"),
                        )
            conn.commit()

        return self.get_department_operating_location_ids(department_id)

    def get_eligible_department_employees(self, department_id: str) -> List[Dict[str, Any]]:
        with self.auth_service._connect() as conn:
            query = """
                SELECT DISTINCT u.user_id, u.name, u.email, u.phone_number, u.role, u.department_id, u.active, u.status
                FROM users u
                LEFT JOIN employee_work_memberships ewm ON u.user_id = ewm.user_id
                WHERE (u.department_id = ? OR ewm.department_id = ?)
                  AND u.active = 1 AND (u.is_deleted = 0 OR u.is_deleted IS NULL)
                  AND u.role IN ('employee', 'coordinator')
                ORDER BY u.name ASC
            """
            rows = conn.execute(query, (department_id, department_id)).fetchall()

        team_svc = getattr(self, "team_service", None)
        if not team_svc and hasattr(self.auth_service, "team_service"):
            team_svc = self.auth_service.team_service

        results = []
        for r in rows:
            u_dict = dict(r)
            uid = u_dict["user_id"]
            with self.auth_service._connect() as conn:
                loc_rows = conn.execute(
                    "SELECT DISTINCT location_id FROM employee_work_memberships WHERE user_id = ? AND department_id = ?",
                    (uid, department_id),
                ).fetchall()
                loc_ids = [lr["location_id"] for lr in loc_rows]
                active_jobs = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND status IN ('Assigned', 'In Progress')",
                    (uid,),
                ).fetchone()[0]

            is_on_leave = False
            if team_svc:
                try:
                    is_on_leave = team_svc.is_user_on_leave(uid)
                except Exception:
                    pass

            u_dict["authorized_locations"] = loc_ids
            u_dict["active_workload"] = active_jobs
            u_dict["is_on_leave"] = is_on_leave
            results.append(u_dict)

        return results

    def enrich_department_dict(self, dept_dict_or_obj) -> Dict[str, Any]:
        if hasattr(dept_dict_or_obj, "to_dict"):
            d = dept_dict_or_obj.to_dict()
        elif isinstance(dept_dict_or_obj, dict):
            d = dict(dept_dict_or_obj)
        else:
            d = dict(dept_dict_or_obj)

        dept_id = d.get("department_id")
        if not dept_id:
            return d

        op_locs = self.get_department_operating_locations(dept_id)
        d["operating_locations"] = op_locs
        d["location_ids"] = [l["location_id"] for l in op_locs]
        d["location_count"] = len(op_locs)

        with self.auth_service._connect() as conn:
            active_count = conn.execute(
                "SELECT COUNT(*) FROM complaints WHERE department_id = ? AND status NOT IN ('Resolved', 'Closed', 'Archived')",
                (dept_id,),
            ).fetchone()[0]
            d["active_complaints_count"] = active_count

            emp_count = conn.execute(
                """
                SELECT COUNT(DISTINCT u.user_id)
                FROM users u
                LEFT JOIN employee_work_memberships ewm ON u.user_id = ewm.user_id
                WHERE (u.department_id = ? OR ewm.department_id = ?)
                  AND u.active = 1 AND (u.is_deleted = 0 OR u.is_deleted IS NULL)
                  AND u.role IN ('employee', 'coordinator')
                """,
                (dept_id, dept_id),
            ).fetchone()[0]
            d["eligible_employee_count"] = emp_count

        c1_id = d.get("coordinator_id")
        if c1_id:
            c1 = self.auth_service.get_user(c1_id)
            d["coordinator_1"] = {
                "user_id": c1.user_id,
                "name": c1.name,
                "email": c1.email,
                "phone_number": getattr(c1, "phone_number", None),
            } if c1 else None
        else:
            d["coordinator_1"] = None

        c2_id = d.get("coordinator_2_id")
        if c2_id:
            c2 = self.auth_service.get_user(c2_id)
            d["coordinator_2"] = {
                "user_id": c2.user_id,
                "name": c2.name,
                "email": c2.email,
                "phone_number": getattr(c2, "phone_number", None),
            } if c2 else None
        else:
            d["coordinator_2"] = None

        return d

    def create_department(
        self,
        name,
        sla_days,
        complaint_types,
        location_id=None,
        description=None,
        location_ids=None,
        actor_user_id=None,
        actor_role=None,
    ):
        self.validation_service.validate_unique_department_name(name, location_id=location_id)
        dept = self.auth_service.create_department(
            name, sla_days, complaint_types, location_id=location_id, description=description
        )
        locs_to_assign = location_ids if location_ids is not None else ([location_id] if location_id else None)
        if not locs_to_assign:
            all_locs = self.auth_service.list_locations()
            locs_to_assign = [l.location_id for l in all_locs if getattr(l, "active", True)]
        if locs_to_assign:
            self.assign_locations_to_department(
                dept.department_id, locs_to_assign, actor_user_id=actor_user_id, actor_role=actor_role
            )
        if complaint_types:
            with self._db_conn() as conn:
                self._ensure_issues_table(conn)
                for c_type in complaint_types:
                    c_name = str(c_type).strip()
                    if not c_name:
                        continue
                    from utils.helper import generate_id, now_string
                    conn.execute(
                        "INSERT INTO department_issues (issue_id, department_id, issue_name, description, active, created_at) VALUES (?, ?, ?, '', 1, ?)",
                        (generate_id("ISS"), dept.department_id, c_name, now_string()),
                    )
                conn.commit()
        return dept

    def update_department(
        self,
        department_id,
        name=None,
        sla_days=None,
        complaint_types=None,
        coordinator_id=None,
        coordinator_2_id=None,
        archived=None,
        archived_by_role=None,
        archived_by=None,
        description=None,
        location_ids=None,
        actor_user_id=None,
        actor_role=None,
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
            with self._db_conn() as conn:
                self._ensure_issues_table(conn)
                for c_type in complaint_types:
                    c_name = str(c_type).strip()
                    if not c_name:
                        continue
                    existing = conn.execute(
                        "SELECT issue_id FROM department_issues WHERE department_id = ? AND issue_name = ?",
                        (department_id, c_name),
                    ).fetchone()
                    if not existing:
                        from utils.helper import generate_id, now_string
                        conn.execute(
                            "INSERT INTO department_issues (issue_id, department_id, issue_name, description, active, created_at) VALUES (?, ?, ?, '', 1, ?)",
                            (generate_id("ISS"), department_id, c_name, now_string()),
                        )
                conn.commit()

        if description is not None:
            dept.description = description

        # Coordinator 1 Assignment
        if coordinator_id is not None:
            if not coordinator_id or coordinator_id == "unassigned":
                dept.coordinator_id = None
                with self.auth_service._connect() as conn:
                    conn.execute("UPDATE coordinator_assignments SET status = 'Inactive' WHERE department_id = ? AND location_id = 'ALL' AND coordinator_id = ?", (department_id, dept.coordinator_id or ""))
                    conn.commit()
            else:
                loc_target = dept.location_id or "ALL"
                self.auth_service.assign_coordinator(
                    coordinator_id, loc_target, department_id, confirm_replacement=True
                )
                dept.coordinator_id = coordinator_id
                coord = self.auth_service.get_user(coordinator_id)
                if coord:
                    coord.department_id = department_id
                    self.auth_service.save_user(coord)

        # Coordinator 2 Assignment
        if coordinator_2_id is not None:
            if not coordinator_2_id or coordinator_2_id == "unassigned":
                dept.coordinator_2_id = None
            else:
                dept.coordinator_2_id = coordinator_2_id

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
                # Remove coordinator assignments
                if dept.coordinator_id:
                    coord = self.auth_service.get_user(dept.coordinator_id)
                    if coord:
                        coord.department_id = None
                        self.auth_service.save_user(coord)
                    dept.coordinator_id = None
                if dept.coordinator_2_id:
                    dept.coordinator_2_id = None
            else:
                if coordinator_id:
                    dept.coordinator_id = coordinator_id
                if coordinator_2_id:
                    dept.coordinator_2_id = coordinator_2_id

        self.auth_service.save_department(dept)

        if location_ids is not None:
            self.assign_locations_to_department(
                department_id, location_ids, actor_user_id=actor_user_id, actor_role=actor_role
            )

        return dept

    def get_eligible_department_coordinators(self, department_id: str):
        dept = self.get_department(department_id)
        all_depts = self.auth_service.list_departments()

        # Build mapping of current coordinators across all departments
        # An employee can coordinate multiple departments simultaneously.
        current_coord_positions = {}
        for d in all_depts:
            c1 = getattr(d, "coordinator_id", None)
            if c1:
                if c1 not in current_coord_positions:
                    current_coord_positions[c1] = []
                current_coord_positions[c1].append({
                    "department_id": d.department_id,
                    "department_name": d.name,
                    "position": "Coordinator 1",
                })
            c2 = getattr(d, "coordinator_2_id", None)
            if c2:
                if c2 not in current_coord_positions:
                    current_coord_positions[c2] = []
                current_coord_positions[c2].append({
                    "department_id": d.department_id,
                    "department_name": d.name,
                    "position": "Coordinator 2",
                })

        users = self.auth_service.list_users()
        employees = [
            u
            for u in users
            if (u.role or "").lower() in ("employee", "coordinator")
            and getattr(u, "active", True)
            and not getattr(u, "is_deleted", False)
            and getattr(u, "status", "Active") == "Active"
        ]

        team_svc = getattr(self, "team_service", None)
        if not team_svc and hasattr(self.auth_service, "team_service"):
            team_svc = self.auth_service.team_service

        results = []
        for emp in employees:
            uid = emp.user_id
            assigned_list = current_coord_positions.get(uid, [])
            this_dept_pos = next((p["position"] for p in assigned_list if p["department_id"] == department_id), None)
            other_positions = [f"{p['position']} ({p['department_name']})" for p in assigned_list if p["department_id"] != department_id]

            is_on_leave = False
            if team_svc:
                try:
                    is_on_leave = team_svc.is_user_on_leave(uid, department_id=department_id)
                except Exception:
                    pass

            # Every active employee is eligible to coordinate multiple departments.
            # Only inside the same department, C1 and C2 cannot be the same employee.
            results.append({
                "user_id": uid,
                "name": emp.name,
                "email": emp.email,
                "role": emp.role,
                "current_position": this_dept_pos,
                "other_positions": other_positions,
                "assigned_departments_count": len(assigned_list),
                "is_eligible": True,
                "ineligible_reason": None,
                "is_on_leave": is_on_leave,
            })

        results.sort(key=lambda x: (not x["is_eligible"], x["name"]))
        return results

    def assign_department_coordinators(
        self,
        department_id: str,
        coordinator_1_id: Optional[str] = None,
        coordinator_2_id: Optional[str] = None,
        actor_id: Optional[str] = None,
    ):
        dept = self.get_department(department_id)

        # Normalize empty strings to None
        c1 = (coordinator_1_id or "").strip() or None
        c2 = (coordinator_2_id or "").strip() or None

        # Rule: The same employee cannot occupy both Coordinator 1 and Coordinator 2 within the same department.
        if c1 and c2 and c1 == c2:
            raise ValueError("Coordinator 1 and Coordinator 2 cannot be the same employee in the same department.")

        # Validate Coordinator 1
        if c1:
            u1 = self.auth_service.get_user(c1)
            if not u1 or (u1.role or "").lower() not in ("employee", "coordinator"):
                raise ValueError(f"Coordinator 1 must be an active employee. Invalid user: {c1}")
            if not u1.active or getattr(u1, "is_deleted", False) or getattr(u1, "status", "Active") != "Active":
                raise ValueError(f"Coordinator 1 ({u1.name}) is inactive or disabled.")

        # Validate Coordinator 2
        if c2:
            u2 = self.auth_service.get_user(c2)
            if not u2 or (u2.role or "").lower() not in ("employee", "coordinator"):
                raise ValueError(f"Coordinator 2 must be an active employee. Invalid user: {c2}")
            if not u2.active or getattr(u2, "is_deleted", False) or getattr(u2, "status", "Active") != "Active":
                raise ValueError(f"Coordinator 2 ({u2.name}) is inactive or disabled.")

        dept.coordinator_id = c1
        dept.coordinator_2_id = c2
        self.auth_service.save_department(dept)

        # Sync with coordinator_assignments table for campus-wide coordinator mapping
        with self.auth_service._connect() as conn:
            conn.execute("UPDATE coordinator_assignments SET status = 'Inactive' WHERE department_id = ?", (department_id,))
            now_iso = datetime.now().isoformat()
            if c1:
                row = conn.execute(
                    "SELECT assignment_id FROM coordinator_assignments WHERE coordinator_id = ? AND location_id = 'ALL' AND department_id = ?",
                    (c1, department_id),
                ).fetchone()
                if row:
                    conn.execute(
                        "UPDATE coordinator_assignments SET status = 'Active', assigned_by = ?, assigned_at = ? WHERE assignment_id = ?",
                        (actor_id or "admin", now_iso, row["assignment_id"]),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO coordinator_assignments (assignment_id, coordinator_id, location_id, department_id, assigned_by, assigned_at, status)
                        VALUES (?, ?, 'ALL', ?, ?, ?, 'Active')
                        """,
                        (f"CASG_{uuid.uuid4().hex[:12]}", c1, department_id, actor_id or "admin", now_iso),
                    )
            if c2:
                row = conn.execute(
                    "SELECT assignment_id FROM coordinator_assignments WHERE coordinator_id = ? AND location_id = 'ALL' AND department_id = ?",
                    (c2, department_id),
                ).fetchone()
                if row:
                    conn.execute(
                        "UPDATE coordinator_assignments SET status = 'Active', assigned_by = ?, assigned_at = ? WHERE assignment_id = ?",
                        (actor_id or "admin", now_iso, row["assignment_id"]),
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO coordinator_assignments (assignment_id, coordinator_id, location_id, department_id, assigned_by, assigned_at, status)
                        VALUES (?, ?, 'ALL', ?, ?, ?, 'Active')
                        """,
                        (f"CASG_{uuid.uuid4().hex[:12]}", c2, department_id, actor_id or "admin", now_iso),
                    )
            conn.commit()

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
