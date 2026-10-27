import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from core.constants import (
    ROLE_ADMINISTRATOR,
    ROLE_APP_MANAGER,
    ROLE_COORDINATOR,
    ROLE_WARDEN,
    ROLE_EMPLOYEE,
)


class TeamService:
    def __init__(self, db_path: str = "storage/campus_pulse.db", auth_service=None, notification_service=None):
        self.db_path = Path(db_path)
        self.auth_service = auth_service
        self.notification_service = notification_service

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    # ---------------------------------------------------------
    # Leaves
    # ---------------------------------------------------------
    def is_user_on_leave(
        self,
        user_id: str,
        department_id: Optional[str] = None,
        check_date: Optional[str] = None,
    ) -> bool:
        """Returns True if user_id is on an active leave on check_date (default: today).
        If department_id is supplied, checks for leaves specifically for that department
        or general (campus-wide) leaves.
        """
        if not user_id:
            return False
        if not check_date:
            check_date = date.today().isoformat()
        with self._connect() as conn:
            if department_id:
                row = conn.execute(
                    """
                    SELECT 1 FROM user_leaves
                    WHERE user_id = ?
                      AND date(from_date) <= date(?)
                      AND date(?) <= date(to_date)
                      AND (department_id IS NULL OR department_id = '' OR department_id = 'ALL' OR department_id = ?)
                    LIMIT 1
                    """,
                    (user_id, check_date, check_date, department_id),
                ).fetchone()
            else:
                row = conn.execute(
                    """
                    SELECT 1 FROM user_leaves
                    WHERE user_id = ?
                      AND date(from_date) <= date(?)
                      AND date(?) <= date(to_date)
                    LIMIT 1
                    """,
                    (user_id, check_date, check_date),
                ).fetchone()
            return row is not None

    def get_user_leaves(self, user_id: Optional[str] = None, active_only: bool = False) -> List[Dict[str, Any]]:
        today = date.today().isoformat()
        query = "SELECT * FROM user_leaves WHERE 1=1"
        params = []
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        if active_only:
            query += " AND date(from_date) <= date(?) AND date(?) <= date(to_date)"
            params.extend([today, today])
        query += " ORDER BY from_date DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def set_leave(
        self,
        user_id: str,
        from_date: str,
        to_date: str,
        reason: Optional[str] = None,
        set_by: str = "system",
        caller_user: Optional[Any] = None,
        department_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Sets a leave record for user_id.
        Who can set: self, App Manager, Admin, or warden for members at their locations.
        Can optionally be scoped to a specific department_id.
        """
        # Authorization check
        if caller_user:
            is_self = caller_user.user_id == user_id
            c_role = (caller_user.role or "").lower()
            is_admin_mgr = c_role in (ROLE_ADMINISTRATOR, ROLE_APP_MANAGER, "administrator", "app_manager", "admin")
            is_warden = c_role in (ROLE_WARDEN, "warden", "location_in_charge")
            if not (is_self or is_admin_mgr or is_warden):
                raise PermissionError("You are not authorized to set leave for this user.")

            if is_warden and not is_self:
                warden_locs = set()
                if getattr(caller_user, "location_id", None):
                    warden_locs.add(caller_user.location_id)
                assigned = getattr(caller_user, "assigned_locations", None)
                if isinstance(assigned, list):
                    warden_locs.update(assigned)
                elif isinstance(assigned, str):
                    try:
                        import json
                        parsed = json.loads(assigned)
                        if isinstance(parsed, list):
                            warden_locs.update(parsed)
                    except Exception:
                        if assigned:
                            warden_locs.add(assigned)

                with self._connect() as conn:
                    w_rows = conn.execute(
                        "SELECT location_id FROM locations WHERE in_charge_id = ?",
                        (caller_user.user_id,)
                    ).fetchall()
                    for wr in w_rows:
                        warden_locs.add(wr[0])

                    t_locs = conn.execute("""
                        SELECT DISTINCT tl.location_id
                        FROM team_locations tl
                        JOIN teams t ON t.team_id = tl.team_id
                        WHERE (t.coordinator_id = ? OR t.backup_coordinator_id = ? OR t.team_id IN (
                            SELECT team_id FROM team_members WHERE user_id = ?
                        ))
                    """, (user_id, user_id, user_id)).fetchall()
                    target_locs = {r[0] for r in t_locs}

                    ca_locs = conn.execute(
                        "SELECT DISTINCT location_id FROM coordinator_assignments WHERE coordinator_id = ? AND (status IS NULL OR status = 'Active')",
                        (user_id,)
                    ).fetchall()
                    target_locs.update(r[0] for r in ca_locs)

                    u_row = conn.execute("SELECT location_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
                    if u_row and u_row[0]:
                        target_locs.add(u_row[0])
                    sp_row = conn.execute("SELECT assigned_locations FROM staff_profiles WHERE user_id = ?", (user_id,)).fetchone()
                    if sp_row and sp_row[0]:
                        try:
                            import json
                            p_locs = json.loads(sp_row[0])
                            if isinstance(p_locs, list):
                                target_locs.update(p_locs)
                        except Exception:
                            target_locs.add(sp_row[0])

                user_covers_warden_loc = bool(target_locs & warden_locs) or ("ALL" in target_locs and bool(warden_locs))
                if not user_covers_warden_loc:
                    raise PermissionError("Wardens can only set leave for members covering their assigned locations.")

        leave_id = f"LV_{uuid.uuid4().hex[:8].upper()}"
        now_str = datetime.now().isoformat()

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_leaves (leave_id, user_id, from_date, to_date, reason, set_by, created_at, department_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (leave_id, user_id, from_date, to_date, reason or "", set_by, now_str, department_id or None),
            )
            # Flag open jobs of this user as assignee on leave only if leave is active today
            today_iso = date.today().isoformat()
            if from_date <= today_iso <= to_date:
                if department_id and department_id != "ALL":
                    conn.execute(
                        """
                        UPDATE complaints
                        SET assignee_on_leave_flag = 1
                        WHERE assigned_to = ?
                          AND department_id = ?
                          AND status IN ('Assigned', 'In Progress', 'Waiting for Parts')
                        """,
                        (user_id, department_id),
                    )
                else:
                    conn.execute(
                        """
                        UPDATE complaints
                        SET assignee_on_leave_flag = 1
                        WHERE assigned_to = ?
                          AND status IN ('Assigned', 'In Progress', 'Waiting for Parts')
                        """,
                        (user_id,),
                    )

        # Notify backup coordinator if this user is a coordinator of any matching team
        user_obj = self.auth_service.get_user(user_id) if self.auth_service else None
        user_name = user_obj.name if user_obj else user_id
        teams = self.list_teams(active_only=True)
        for t in teams:
            team_dept = t.get("department_id")
            dept_matches = (not department_id) or (department_id in ("ALL", team_dept))
            if dept_matches and t["coordinator_id"] == user_id and t.get("backup_coordinator_id"):
                backup_id = t["backup_coordinator_id"]
                if self.notification_service:
                    self.notification_service.notify(
                        backup_id,
                        f"Coordinator {user_name} is on leave from {from_date} to {to_date}. You are acting coordinator for {t['name']}.",
                        title="Acting Coordinator Coverage",
                    )

        return {
            "leave_id": leave_id,
            "user_id": user_id,
            "from_date": from_date,
            "to_date": to_date,
            "reason": reason,
            "set_by": set_by,
            "created_at": now_str,
        }

    def cancel_leave(self, leave_id: str, caller_user: Optional[Any] = None) -> bool:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM user_leaves WHERE leave_id = ?", (leave_id,)).fetchone()
            if not row:
                raise ValueError("Leave record not found.")
            l_dict = dict(row)
            if caller_user:
                is_self = caller_user.user_id == l_dict["user_id"]
                c_role = (caller_user.role or "").lower()
                is_admin_mgr = c_role in (ROLE_ADMINISTRATOR, ROLE_APP_MANAGER)
                if not (is_self or is_admin_mgr):
                    raise PermissionError("You are not authorized to cancel this leave.")

            conn.execute("DELETE FROM user_leaves WHERE leave_id = ?", (leave_id,))
            # Reset leave flags on complaints if user has no other active leaves
            user_id = l_dict["user_id"]
            today = date.today().isoformat()
            rem = conn.execute(
                """
                SELECT 1 FROM user_leaves
                WHERE user_id = ?
                  AND date(from_date) <= date(?)
                  AND date(?) <= date(to_date)
                LIMIT 1
                """,
                (user_id, today, today),
            ).fetchone()
            if not rem:
                conn.execute(
                    """
                    UPDATE complaints
                    SET assignee_on_leave_flag = 0
                    WHERE assigned_to = ?
                    """,
                    (user_id,),
                )
        return True

    # ---------------------------------------------------------
    # Teams
    # ---------------------------------------------------------
    def get_team(self, team_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM teams WHERE team_id = ?", (team_id,)).fetchone()
            if not row:
                return None
            t = dict(row)
            loc_rows = conn.execute("SELECT location_id FROM team_locations WHERE team_id = ?", (team_id,)).fetchall()
            t["location_ids"] = [r[0] for r in loc_rows]
            mem_rows = conn.execute("SELECT user_id FROM team_members WHERE team_id = ?", (team_id,)).fetchall()
            t["member_ids"] = [r[0] for r in mem_rows]

            today = date.today().isoformat()
            coord_id = t.get("coordinator_id")
            coord_leave_row = None
            coord_name = None
            if coord_id and self.auth_service:
                coord_user = self.auth_service.get_user(coord_id)
                if coord_user:
                    coord_name = coord_user.name
                coord_leave_row = conn.execute(
                    "SELECT to_date FROM user_leaves WHERE user_id = ? AND date(from_date) <= date(?) AND date(?) <= date(to_date) ORDER BY to_date DESC LIMIT 1",
                    (coord_id, today, today),
                ).fetchone()

            t["coordinator_name"] = coord_name
            t["coordinator_on_leave"] = bool(coord_leave_row)
            t["coordinator_leave_until"] = coord_leave_row[0] if coord_leave_row else None

            acting_coord = self.get_acting_coordinator(t)
            t["acting_coordinator_id"] = acting_coord.user_id if acting_coord else None
            t["acting_coordinator_name"] = acting_coord.name if acting_coord else None
            return t

    def get_team_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        if not name:
            return None
        with self._connect() as conn:
            row = conn.execute("SELECT team_id FROM teams WHERE LOWER(name) = ? LIMIT 1", (name.strip().lower(),)).fetchone()
            if row:
                return self.get_team(row[0])
        return None

    def list_teams(self, active_only: bool = True) -> List[Dict[str, Any]]:
        query = "SELECT * FROM teams WHERE 1=1"
        if active_only:
            query += " AND active = 1"
        query += " ORDER BY name ASC"

        today = date.today().isoformat()
        with self._connect() as conn:
            rows = conn.execute(query).fetchall()
            teams = []
            for r in rows:
                t = dict(r)
                loc_rows = conn.execute("SELECT location_id FROM team_locations WHERE team_id = ?", (t["team_id"],)).fetchall()
                t["location_ids"] = [lr[0] for lr in loc_rows]
                mem_rows = conn.execute("SELECT user_id FROM team_members WHERE team_id = ?", (t["team_id"],)).fetchall()
                t["member_ids"] = [mr[0] for mr in mem_rows]

                coord_id = t.get("coordinator_id")
                coord_leave_row = None
                coord_name = None
                if coord_id and self.auth_service:
                    coord_user = self.auth_service.get_user(coord_id)
                    if coord_user:
                        coord_name = coord_user.name
                    coord_leave_row = conn.execute(
                        "SELECT to_date FROM user_leaves WHERE user_id = ? AND date(from_date) <= date(?) AND date(?) <= date(to_date) ORDER BY to_date DESC LIMIT 1",
                        (coord_id, today, today),
                    ).fetchone()

                t["coordinator_name"] = coord_name
                t["coordinator_on_leave"] = bool(coord_leave_row)
                t["coordinator_leave_until"] = coord_leave_row[0] if coord_leave_row else None

                acting_coord = self.get_acting_coordinator(t)
                t["acting_coordinator_id"] = acting_coord.user_id if acting_coord else None
                t["acting_coordinator_name"] = acting_coord.name if acting_coord else None
                teams.append(t)
            return teams

    def get_team_for_location_department(self, location_id: str, department_id: str) -> Optional[Dict[str, Any]]:
        """Finds the single active team covering the given (location_id, department_id) pair."""
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT t.*
                FROM teams t
                JOIN team_locations tl ON t.team_id = tl.team_id
                WHERE t.department_id = ?
                  AND (tl.location_id = ? OR tl.location_id = 'ALL')
                  AND t.active = 1
                ORDER BY CASE WHEN tl.location_id = ? THEN 0 ELSE 1 END
                LIMIT 1
                """,
                (department_id, location_id, location_id),
            ).fetchone()
            if not row:
                return None
            team = dict(row)
            loc_rows = conn.execute("SELECT location_id FROM team_locations WHERE team_id = ?", (team["team_id"],)).fetchall()
            team["location_ids"] = [r[0] for r in loc_rows]
            mem_rows = conn.execute("SELECT user_id FROM team_members WHERE team_id = ?", (team["team_id"],)).fetchall()
            team["member_ids"] = [r[0] for r in mem_rows]
            return team


    def sync_expired_leaves(self):
        """Clears assignee_on_leave_flag on complaints whose assignees are no longer on active leave."""
        today_iso = date.today().isoformat()
        with self._connect() as conn:
            conn.execute("""
                UPDATE complaints
                SET assignee_on_leave_flag = 0
                WHERE assignee_on_leave_flag = 1
                  AND (
                      assigned_to IS NULL
                      OR assigned_to NOT IN (
                          SELECT user_id FROM user_leaves
                          WHERE date(from_date) <= date(?)
                            AND date(?) <= date(to_date)
                      )
                  )
            """, (today_iso, today_iso))

    def get_acting_coordinator(self, team: Dict[str, Any]) -> Optional[Any]:
        """Rule B4:
        = the coordinator, if active and NOT on leave in this department today
        otherwise = the backup, if set, active and NOT on leave in this department
        otherwise = None (handled by escalation in Part F)
        """
        if not team or not self.auth_service:
            return None

        today = date.today().isoformat()
        dept_id = team.get("department_id")
        coord_id = team.get("coordinator_id")
        if coord_id:
            coord_user = self.auth_service.get_user(coord_id)
            if coord_user and coord_user.active and not self.is_user_on_leave(coord_id, department_id=dept_id, check_date=today):
                return coord_user

        backup_id = team.get("backup_coordinator_id")
        if backup_id:
            backup_user = self.auth_service.get_user(backup_id)
            if backup_user and backup_user.active and not self.is_user_on_leave(backup_id, department_id=dept_id, check_date=today):
                return backup_user

        return None

    def is_user_in_team(self, team_id: str, user_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute("SELECT 1 FROM team_members WHERE team_id = ? AND user_id = ?", (team_id, user_id)).fetchone()
            return row is not None

    def get_user_teams(self, user_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT t.* FROM teams t
                JOIN team_members tm ON t.team_id = tm.team_id
                WHERE tm.user_id = ? AND t.active = 1
                """,
                (user_id,),
            ).fetchall()
            teams = []
            for r in rows:
                t = dict(r)
                loc_rows = conn.execute("SELECT location_id FROM team_locations WHERE team_id = ?", (t["team_id"],)).fetchall()
                t["location_ids"] = [lr[0] for lr in loc_rows]
                mem_rows = conn.execute("SELECT user_id FROM team_members WHERE team_id = ?", (t["team_id"],)).fetchall()
                t["member_ids"] = [mr[0] for mr in mem_rows]
                teams.append(t)
            return teams

    def get_team_members_with_load(self, team_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            mem_rows = conn.execute("SELECT user_id FROM team_members WHERE team_id = ?", (team_id,)).fetchall()
            member_ids = [r[0] for r in mem_rows]

            result = []
            for mid in member_ids:
                u = self.auth_service.get_user(mid) if self.auth_service else None
                if not u or not getattr(u, "active", True) or getattr(u, "is_deleted", False):
                    continue
                on_leave = self.is_user_on_leave(mid)
                open_jobs_row = conn.execute(
                    """
                    SELECT COUNT(*) FROM complaints
                    WHERE assigned_to = ?
                      AND status IN ('Assigned', 'In Progress', 'Waiting for Parts')
                    """,
                    (mid,),
                ).fetchone()
                open_jobs = open_jobs_row[0] if open_jobs_row else 0
                result.append({
                    "user_id": mid,
                    "name": getattr(u, "name", mid),
                    "email": getattr(u, "email", ""),
                    "role": getattr(u, "role", "employee"),
                    "department_id": getattr(u, "department_id", None),
                    "open_jobs": open_jobs,
                    "on_leave": on_leave,
                })
            return result

    def validate_coordinator_uniqueness(
        self,
        coordinator_id: Optional[str],
        backup_coordinator_id: Optional[str] = None,
        exclude_team_id: Optional[str] = None,
    ) -> None:
        """Rules:
        1. An employee CANNOT be both Coordinator 1 and Coordinator 2 within the SAME team.
        2. An employee CAN coordinate multiple departments/teams simultaneously.
        3. An employee may occupy Coordinator 1 in one department/team and Coordinator 2 in another.
        """
        if coordinator_id and backup_coordinator_id and coordinator_id == backup_coordinator_id:
            raise ValueError("The same employee cannot be both Coordinator 1 and Coordinator 2 on the same team.")

    def create_team(
        self,
        name: str,
        department_id: str,
        coordinator_id: str,
        location_ids: List[str],
        backup_coordinator_id: Optional[str] = None,
        member_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Creates a new team in a single transaction, validating Rule C2:
        each (location, department) pair belongs to EXACTLY ONE active team.
        Also validates Global One-Coordinator-Position Rule.
        """
        if not name or not name.strip():
            raise ValueError("Team name is required.")
        if not department_id:
            raise ValueError("Department is required.")
        if not coordinator_id:
            raise ValueError("Coordinator is required.")
        if not location_ids:
            raise ValueError("At least one location must be assigned to the team.")

        # Global One-Coordinator-Position Rule validation
        self.validate_coordinator_uniqueness(coordinator_id, backup_coordinator_id, exclude_team_id=None)

        member_ids = list(member_ids or [])
        if coordinator_id not in member_ids:
            member_ids.append(coordinator_id)
        if backup_coordinator_id and backup_coordinator_id not in member_ids:
            member_ids.append(backup_coordinator_id)

        team_id = f"TEAM_{uuid.uuid4().hex[:8].upper()}"
        now_str = datetime.now().isoformat()

        with self._connect() as conn:
            # Rule C2: Check conflict for every (location, department)
            dept_row = conn.execute("SELECT name FROM departments WHERE department_id = ?", (department_id,)).fetchone()
            dept_name = dept_row["name"] if dept_row else department_id

            for loc_id in location_ids:
                conflict = conn.execute(
                    """
                    SELECT t.name
                    FROM teams t
                    JOIN team_locations tl ON t.team_id = tl.team_id
                    WHERE t.department_id = ?
                      AND tl.location_id = ?
                      AND t.active = 1
                    LIMIT 1
                    """,
                    (department_id, loc_id),
                ).fetchone()
                if conflict:
                    loc_row = conn.execute("SELECT name FROM locations WHERE location_id = ?", (loc_id,)).fetchone()
                    loc_name = loc_row["name"] if loc_row else loc_id
                    raise ValueError(f"{loc_name} – {dept_name} already belongs to team {conflict['name']}.")

            conn.execute(
                """
                INSERT INTO teams (team_id, name, department_id, coordinator_id, backup_coordinator_id, active, created_at)
                VALUES (?, ?, ?, ?, ?, 1, ?)
                """,
                (team_id, name.strip(), department_id, coordinator_id, backup_coordinator_id, now_str),
            )
            for lid in location_ids:
                conn.execute(
                    "INSERT INTO team_locations (team_id, location_id) VALUES (?, ?)",
                    (team_id, lid),
                )
                conn.execute(
                    """
                    INSERT INTO location_departments (id, location_id, department_id, created_at, created_by, is_active)
                    VALUES (?, ?, ?, ?, 'system', 1)
                    ON CONFLICT(location_id, department_id) DO UPDATE SET is_active = 1
                    """,
                    (f"LD_{uuid.uuid4().hex[:12]}", lid, department_id, now_str),
                )
            for mid in member_ids:
                conn.execute(
                    "INSERT INTO team_members (team_id, user_id) VALUES (?, ?)",
                    (team_id, mid),
                )

        return self.get_team(team_id)

    def update_team(
        self,
        team_id: str,
        name: str,
        department_id: str,
        coordinator_id: str,
        location_ids: List[str],
        backup_coordinator_id: Optional[str] = None,
        member_ids: Optional[List[str]] = None,
        active: bool = True,
    ) -> Dict[str, Any]:
        """Updates team in a single transaction.
        Checks C2 pair uniqueness.
        Handles C5 (changing coordinator) and C6 (removing member).
        """
        old_team = self.get_team(team_id)
        if not old_team:
            raise ValueError("Team not found.")

        member_ids = list(member_ids or [])
        if coordinator_id not in member_ids:
            member_ids.append(coordinator_id)
        if backup_coordinator_id and backup_coordinator_id not in member_ids:
            member_ids.append(backup_coordinator_id)

        with self._connect() as conn:
            # Rule C2: Check conflict if active
            if active:
                self.validate_coordinator_uniqueness(coordinator_id, backup_coordinator_id, exclude_team_id=team_id)
                dept_row = conn.execute("SELECT name FROM departments WHERE department_id = ?", (department_id,)).fetchone()
                dept_name = dept_row["name"] if dept_row else department_id
                for loc_id in location_ids:
                    conflict = conn.execute(
                        """
                        SELECT t.name
                        FROM teams t
                        JOIN team_locations tl ON t.team_id = tl.team_id
                        WHERE t.department_id = ?
                          AND tl.location_id = ?
                          AND t.active = 1
                          AND t.team_id != ?
                        LIMIT 1
                        """,
                        (department_id, loc_id, team_id),
                    ).fetchone()
                    if conflict:
                        loc_row = conn.execute("SELECT name FROM locations WHERE location_id = ?", (loc_id,)).fetchone()
                        loc_name = loc_row["name"] if loc_row else loc_id
                        raise ValueError(f"{loc_name} – {dept_name} already belongs to team {conflict['name']}.")

            # Update team record
            conn.execute(
                """
                UPDATE teams
                SET name = ?, department_id = ?, coordinator_id = ?, backup_coordinator_id = ?, active = ?
                WHERE team_id = ?
                """,
                (name.strip(), department_id, coordinator_id, backup_coordinator_id, 1 if active else 0, team_id),
            )

            # Rule C5: Changing coordinator -> complaints waiting to be assigned now show for the new coordinator
            old_coord = old_team.get("coordinator_id")
            if old_coord != coordinator_id:
                # Link unassigned complaints of this team
                conn.execute(
                    """
                    UPDATE complaints
                    SET team_id = ?
                    WHERE department_id = ?
                      AND location_id IN (SELECT location_id FROM team_locations WHERE team_id = ?)
                      AND status = 'Submitted'
                      AND (assigned_to IS NULL OR assigned_to = '')
                    """,
                    (team_id, department_id, team_id),
                )

            # Rule C6: Removing a member -> his open jobs get the flag "Assignee removed — reassign"
            old_members = set(old_team.get("member_ids") or [])
            new_members = set(member_ids)
            removed_members = old_members - new_members
            for rem_uid in removed_members:
                conn.execute(
                    """
                    UPDATE complaints
                    SET assignee_removed_flag = 1
                    WHERE team_id = ?
                      AND assigned_to = ?
                      AND status IN ('Assigned', 'In Progress', 'Waiting for Parts')
                    """,
                    (team_id, rem_uid),
                )

            # Update locations
            conn.execute("DELETE FROM team_locations WHERE team_id = ?", (team_id,))
            for lid in location_ids:
                conn.execute("INSERT INTO team_locations (team_id, location_id) VALUES (?, ?)", (team_id, lid))

            # Update members
            conn.execute("DELETE FROM team_members WHERE team_id = ?", (team_id,))
            for mid in member_ids:
                conn.execute("INSERT INTO team_members (team_id, user_id) VALUES (?, ?)", (team_id, mid))

        return self.get_team(team_id)

    def delete_team(self, team_id: str) -> bool:
        with self._connect() as conn:
            conn.execute("UPDATE teams SET active = 0 WHERE team_id = ?", (team_id,))
        return True

    # ---------------------------------------------------------
    # Coverage Gaps (Rule C8)
    # ---------------------------------------------------------
    def get_coverage_gaps(self) -> Dict[str, Any]:
        """Returns:
        - departments with no coordinator or team (campus-wide)
        - teams with no backup (warning)
        - teams whose coordinator is deactivated
        - locations with no warden
        """
        with self._connect() as conn:
            # 1. Departments with no coordinator or team (campus-wide)
            depts = conn.execute("SELECT department_id, name, coordinator_id FROM departments WHERE active = 1").fetchall()
            locs = conn.execute("SELECT location_id, name, in_charge_id FROM locations WHERE active = 1").fetchall()

            # Active teams with an assigned coordinator
            active_team_depts = {
                t[0] for t in conn.execute(
                    "SELECT DISTINCT department_id FROM teams WHERE active = 1 AND coordinator_id IS NOT NULL"
                ).fetchall()
            }
            # Departments with directly assigned active Coordinator 1
            active_dept_coords = {
                d[0] for d in conn.execute(
                    """
                    SELECT d.department_id FROM departments d
                    JOIN users u ON d.coordinator_id = u.user_id
                    WHERE d.active = 1 AND u.active = 1 AND (u.is_deleted IS NULL OR u.is_deleted = 0)
                    """
                ).fetchall()
            }
            # Departments with active coordinator assignment mapping
            active_asgn_depts = {
                ca[0] for ca in conn.execute(
                    """
                    SELECT DISTINCT ca.department_id FROM coordinator_assignments ca
                    JOIN users u ON ca.coordinator_id = u.user_id
                    WHERE (ca.status IS NULL OR ca.status = 'Active')
                      AND u.active = 1 AND (u.is_deleted IS NULL OR u.is_deleted = 0)
                    """
                ).fetchall()
            }

            covered_depts = active_team_depts | active_dept_coords | active_asgn_depts

            missing_departments = []
            for d in depts:
                if d["department_id"] not in covered_depts:
                    missing_departments.append({
                        "department_id": d["department_id"],
                        "department_name": d["name"],
                        "location_id": "ALL",
                        "location_name": "Campus-wide",
                    })

            # 2. Teams with no backup
            no_backup_teams = []
            # 3. Teams whose coordinator is deactivated
            inactive_coord_teams = []
            all_teams = conn.execute("SELECT * FROM teams WHERE active = 1").fetchall()
            for tr in all_teams:
                t_dict = dict(tr)
                if not t_dict.get("backup_coordinator_id"):
                    no_backup_teams.append(t_dict)
                coord_row = conn.execute("SELECT active FROM users WHERE user_id = ?", (t_dict["coordinator_id"],)).fetchone()
                if not coord_row or coord_row["active"] == 0:
                    inactive_coord_teams.append(t_dict)

            # 4. Locations with no warden
            missing_wardens = []
            for l in locs:
                if not l["in_charge_id"] and l["location_id"] != "LOC_OTHER" and not (l["name"] or "").strip().lower().startswith("other"):
                    missing_wardens.append({"location_id": l["location_id"], "location_name": l["name"]})

            return {
                "uncovered_departments": missing_departments,
                "uncovered_pairs": missing_departments,  # Retained for backwards compatibility
                "teams_without_backup": no_backup_teams,
                "teams_with_inactive_coordinator": inactive_coord_teams,
                "locations_without_warden": missing_wardens,
            }

    # ---------------------------------------------------------
    # Coordinator Selection & Eligibility (Phase 3)
    # ---------------------------------------------------------
    def get_eligible_coordinators(
        self, team_id: Optional[str] = None, position: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Returns employees and their eligibility for holding a coordinator role.
        An employee can coordinate multiple departments/teams simultaneously.
        Only within the same team, the same employee cannot be both Coordinator 1 and Coordinator 2.
        """
        with self._connect() as conn:
            active_teams = conn.execute(
                "SELECT team_id, name, department_id, coordinator_id, backup_coordinator_id FROM teams WHERE active = 1"
            ).fetchall()
            coord_map = {}
            for t in active_teams:
                for cid, pos in [(t["coordinator_id"], "Coordinator 1"), (t["backup_coordinator_id"], "Coordinator 2")]:
                    if cid:
                        if cid not in coord_map:
                            coord_map[cid] = []
                        coord_map[cid].append({
                            "team_id": t["team_id"],
                            "team_name": t["name"],
                            "position": pos,
                        })

            users_rows = conn.execute("""
                SELECT user_id, name, email, role, department_id, active 
                FROM users 
                WHERE role IN ('employee', 'coordinator') AND active = 1 AND (is_deleted = 0 OR is_deleted IS NULL)
                ORDER BY name ASC
            """).fetchall()

            target_team = next((t for t in active_teams if t["team_id"] == team_id), None) if team_id else None

            results = []
            for u in users_rows:
                uid = u["user_id"]
                holding_list = coord_map.get(uid, [])
                is_eligible = True
                ineligible_reason = None

                # Disallow selecting the same employee for both positions within this same team
                if target_team:
                    if position == "primary" and target_team["backup_coordinator_id"] == uid:
                        is_eligible = False
                        ineligible_reason = "Already selected as Coordinator 2 on this team."
                    elif position == "backup" and target_team["coordinator_id"] == uid:
                        is_eligible = False
                        ineligible_reason = "Already selected as Coordinator 1 on this team."

                results.append({
                    "user_id": uid,
                    "name": u["name"],
                    "email": u["email"],
                    "role": u["role"],
                    "department_id": u["department_id"],
                    "is_eligible": is_eligible,
                    "ineligible_reason": ineligible_reason,
                    "current_position": holding_list[0]["position"] if holding_list else None,
                    "current_team_name": holding_list[0]["team_name"] if holding_list else None,
                    "assigned_teams": holding_list,
                })
            return results

    # ---------------------------------------------------------
    # Employee Work Memberships (Phase 2)
    # ---------------------------------------------------------
    def list_work_memberships(
        self,
        user_id: Optional[str] = None,
        location_id: Optional[str] = None,
        department_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = """
            SELECT 
                ewm.membership_id,
                ewm.user_id,
                u.name as user_name,
                u.email as user_email,
                ewm.department_id,
                d.name as department_name,
                ewm.location_id,
                l.name as location_name,
                l.location_type,
                ewm.created_at,
                ewm.created_by
            FROM employee_work_memberships ewm
            JOIN users u ON ewm.user_id = u.user_id
            JOIN departments d ON ewm.department_id = d.department_id
            JOIN locations l ON ewm.location_id = l.location_id
            WHERE 1=1
        """
        params = []
        if user_id:
            query += " AND ewm.user_id = ?"
            params.append(user_id)
        if location_id:
            query += " AND ewm.location_id = ?"
            params.append(location_id)
        if department_id:
            query += " AND ewm.department_id = ?"
            params.append(department_id)
        query += " ORDER BY u.name ASC, d.name ASC, l.name ASC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def assign_work_membership(
        self,
        user_id: str,
        department_id: str,
        location_id: str,
        created_by: str = "admin",
        caller_user: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Assigns an employee to work in a specific (department, location) pair.
        Enforces App Manager location scoping. Synchronizes with team_members.
        """
        if caller_user and getattr(caller_user, "role", "").lower() == "app_manager":
            allowed_locs = [
                loc.location_id
                for loc in (
                    self.auth_service.get_app_manager_locations(caller_user.user_id)
                    if self.auth_service
                    else []
                )
            ]
            if location_id not in allowed_locs:
                raise PermissionError("App Managers can only assign memberships for locations within their assigned scope.")

        with self._connect() as conn:
            u = conn.execute(
                "SELECT user_id, name FROM users WHERE user_id = ? AND active = 1 AND (is_deleted = 0 OR is_deleted IS NULL)",
                (user_id,),
            ).fetchone()
            if not u:
                raise ValueError("Active employee user not found.")
            d = conn.execute(
                "SELECT department_id, name FROM departments WHERE department_id = ?",
                (department_id,),
            ).fetchone()
            if not d:
                raise ValueError("Department not found.")
            l = conn.execute(
                "SELECT location_id, name FROM locations WHERE location_id = ?",
                (location_id,),
            ).fetchone()
            if not l:
                raise ValueError("Location not found.")

            existing = conn.execute(
                "SELECT membership_id FROM employee_work_memberships WHERE user_id = ? AND department_id = ? AND location_id = ?",
                (user_id, department_id, location_id),
            ).fetchone()
            if existing:
                res = self.list_work_memberships(user_id=user_id, location_id=location_id, department_id=department_id)
                return res[0] if res else {"membership_id": existing["membership_id"]}

            membership_id = f"EWM_{uuid.uuid4().hex[:12]}"
            now_str = datetime.now().isoformat()
            conn.execute(
                """
                INSERT INTO employee_work_memberships (membership_id, user_id, department_id, location_id, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (membership_id, user_id, department_id, location_id, now_str, created_by),
            )

            # Sync with active team covering this (dept, loc)
            team_row = conn.execute(
                """
                SELECT t.team_id
                FROM teams t
                JOIN team_locations tl ON t.team_id = tl.team_id
                WHERE t.department_id = ? AND (tl.location_id = ? OR tl.location_id = 'ALL') AND t.active = 1
                LIMIT 1
                """,
                (department_id, location_id),
            ).fetchone()
            if team_row:
                conn.execute(
                    "INSERT OR IGNORE INTO team_members (team_id, user_id) VALUES (?, ?)",
                    (team_row["team_id"], user_id),
                )

        res = self.list_work_memberships(user_id=user_id, location_id=location_id, department_id=department_id)
        return res[0] if res else {"membership_id": membership_id}

    def remove_work_membership(self, membership_id: str, caller_user: Optional[Any] = None) -> bool:
        """Removes an employee's department-location work membership.
        Enforces App Manager location scoping. Synchronizes with team_members.
        """
        with self._connect() as conn:
            m_row = conn.execute(
                "SELECT membership_id, user_id, department_id, location_id FROM employee_work_memberships WHERE membership_id = ?",
                (membership_id,),
            ).fetchone()
            if not m_row:
                raise ValueError("Work membership not found.")

            m_dict = dict(m_row)
            user_id = m_dict["user_id"]
            dept_id = m_dict["department_id"]
            loc_id = m_dict["location_id"]

            if caller_user and getattr(caller_user, "role", "").lower() == "app_manager":
                allowed_locs = [
                    loc.location_id
                    for loc in (
                        self.auth_service.get_app_manager_locations(caller_user.user_id)
                        if self.auth_service
                        else []
                    )
                ]
                if loc_id not in allowed_locs:
                    raise PermissionError("App Managers can only remove memberships for locations within their assigned scope.")

            conn.execute("DELETE FROM employee_work_memberships WHERE membership_id = ?", (membership_id,))

            # Check if user has other memberships in any team covering (dept, loc)
            team_rows = conn.execute(
                """
                SELECT t.team_id, t.coordinator_id, t.backup_coordinator_id
                FROM teams t
                JOIN team_locations tl ON t.team_id = tl.team_id
                WHERE t.department_id = ? AND (tl.location_id = ? OR tl.location_id = 'ALL') AND t.active = 1
                """,
                (dept_id, loc_id),
            ).fetchall()

            for trow in team_rows:
                tid = trow["team_id"]
                if trow["coordinator_id"] == user_id or trow["backup_coordinator_id"] == user_id:
                    continue
                remaining = conn.execute(
                    """
                    SELECT 1 FROM employee_work_memberships ewm
                    JOIN team_locations tl ON ewm.location_id = tl.location_id
                    WHERE tl.team_id = ? AND ewm.department_id = ? AND ewm.user_id = ?
                    LIMIT 1
                    """,
                    (tid, dept_id, user_id),
                ).fetchone()
                if not remaining:
                    conn.execute("DELETE FROM team_members WHERE team_id = ? AND user_id = ?", (tid, user_id))

        return True

    def list_employees_overview(self, caller_user: Optional[Any] = None) -> List[Dict[str, Any]]:
        """Returns all employees with their work memberships, coordinator assignments, open jobs, and leave status."""
        with self._connect() as conn:
            dept_coords = conn.execute(
                "SELECT department_id, name, coordinator_id, coordinator_2_id FROM departments WHERE active = 1"
            ).fetchall()
            coord_roles_map = {}
            for d in dept_coords:
                if d["coordinator_id"]:
                    cid = d["coordinator_id"]
                    if cid not in coord_roles_map:
                        coord_roles_map[cid] = []
                    coord_roles_map[cid].append({
                        "position": f"Coordinator 1 ({d['name']})",
                        "department_name": d["name"],
                        "department_id": d["department_id"],
                    })
                if d["coordinator_2_id"]:
                    cid = d["coordinator_2_id"]
                    if cid not in coord_roles_map:
                        coord_roles_map[cid] = []
                    coord_roles_map[cid].append({
                        "position": f"Coordinator 2 ({d['name']})",
                        "department_name": d["name"],
                        "department_id": d["department_id"],
                    })

            coord_asgns = conn.execute("""
                SELECT ca.coordinator_id, ca.department_id, d.name as department_name, ca.location_id, l.name as location_name
                FROM coordinator_assignments ca
                LEFT JOIN departments d ON ca.department_id = d.department_id
                LEFT JOIN locations l ON ca.location_id = l.location_id
                WHERE (ca.status IS NULL OR ca.status = 'Active')
            """).fetchall()
            for ca in coord_asgns:
                cid = ca["coordinator_id"]
                dept_n = ca["department_name"] or "Department"
                if cid not in coord_roles_map:
                    coord_roles_map[cid] = []
                # Check if already present
                if not any(r["department_id"] == ca["department_id"] for r in coord_roles_map[cid]):
                    coord_roles_map[cid].append({
                        "position": f"Coordinator ({dept_n})",
                        "department_name": dept_n,
                        "location_name": ca["location_name"] or "Campus",
                        "department_id": ca["department_id"],
                    })

            users_rows = conn.execute("""
                SELECT user_id, name, email, phone_number as phone, role, department_id, active 
                FROM users 
                WHERE role IN ('employee', 'coordinator') AND active = 1 AND (is_deleted = 0 OR is_deleted IS NULL)
                ORDER BY name ASC
            """).fetchall()

            m_rows = conn.execute("""
                SELECT 
                    ewm.membership_id,
                    ewm.user_id,
                    ewm.department_id,
                    d.name as department_name,
                    ewm.location_id,
                    l.name as location_name,
                    ewm.created_at
                FROM employee_work_memberships ewm
                JOIN departments d ON ewm.department_id = d.department_id
                JOIN locations l ON ewm.location_id = l.location_id
                ORDER BY d.name ASC, l.name ASC
            """).fetchall()

            user_memberships = {}
            for mr in m_rows:
                uid = mr["user_id"]
                if uid not in user_memberships:
                    user_memberships[uid] = []
                user_memberships[uid].append(dict(mr))

            results = []
            for u in users_rows:
                uid = u["user_id"]
                coord_roles = coord_roles_map.get(uid, [])
                coord_pos = coord_roles[0] if coord_roles else None
                m_list = user_memberships.get(uid, [])

                oj_row = conn.execute(
                    "SELECT COUNT(*) FROM complaints WHERE assigned_to = ? AND status IN ('Assigned', 'In Progress', 'Waiting for Parts')",
                    (uid,),
                ).fetchone()
                open_jobs = oj_row[0] if oj_row else 0
                on_leave = self.is_user_on_leave(uid)

                results.append({
                    "user_id": uid,
                    "name": u["name"],
                    "email": u["email"],
                    "phone": u["phone"],
                    "role": u["role"],
                    "department_id": u["department_id"],
                    "active": bool(u["active"]),
                    "coordinator_role": coord_pos,
                    "coordinator_roles": coord_roles,
                    "memberships": m_list,
                    "open_jobs": open_jobs,
                    "on_leave": on_leave,
                })

            return results

