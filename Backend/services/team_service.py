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
    def is_user_on_leave(self, user_id: str, check_date: Optional[str] = None) -> bool:
        """Returns True if user_id is on an active leave on check_date (default: today)."""
        if not user_id:
            return False
        if not check_date:
            check_date = date.today().isoformat()
        with self._connect() as conn:
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
    ) -> Dict[str, Any]:
        """Sets a leave record for user_id.
        Who can set: self, App Manager, Admin, or warden for members at their locations.
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
                INSERT INTO user_leaves (leave_id, user_id, from_date, to_date, reason, set_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (leave_id, user_id, from_date, to_date, reason or "", set_by, now_str),
            )
            # Flag open jobs of this user as assignee on leave
            conn.execute(
                """
                UPDATE complaints
                SET assignee_on_leave_flag = 1
                WHERE assigned_to = ?
                  AND status IN ('Assigned', 'In Progress', 'Waiting for Parts')
                """,
                (user_id,),
            )

        # Notify backup coordinator if this user is a coordinator of any team
        user_obj = self.auth_service.get_user(user_id) if self.auth_service else None
        user_name = user_obj.name if user_obj else user_id
        teams = self.list_teams(active_only=True)
        for t in teams:
            if t["coordinator_id"] == user_id and t.get("backup_coordinator_id"):
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

    def get_acting_coordinator(self, team: Dict[str, Any]) -> Optional[Any]:
        """Rule B4:
        = the coordinator, if he is active and NOT on leave today
        otherwise = the backup, if the backup is set, active and NOT on leave
        otherwise = None (handled by escalation in Part F)
        """
        if not team or not self.auth_service:
            return None

        today = date.today().isoformat()
        coord_id = team.get("coordinator_id")
        if coord_id:
            coord_user = self.auth_service.get_user(coord_id)
            if coord_user and coord_user.active and not self.is_user_on_leave(coord_id, today):
                return coord_user

        backup_id = team.get("backup_coordinator_id")
        if backup_id:
            backup_user = self.auth_service.get_user(backup_id)
            if backup_user and backup_user.active and not self.is_user_on_leave(backup_id, today):
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
        """
        if not name or not name.strip():
            raise ValueError("Team name is required.")
        if not department_id:
            raise ValueError("Department is required.")
        if not coordinator_id:
            raise ValueError("Coordinator is required.")
        if not location_ids:
            raise ValueError("At least one location must be assigned to the team.")

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
        - (location, department) pairs with no team
        - teams with no backup (warning)
        - teams whose coordinator is deactivated
        - locations with no warden
        """
        with self._connect() as conn:
            # 1. (location, department) with no team
            depts = conn.execute("SELECT department_id, name FROM departments WHERE active = 1").fetchall()
            locs = conn.execute("SELECT location_id, name, in_charge_id FROM locations WHERE active = 1").fetchall()

            team_pairs = conn.execute(
                """
                SELECT DISTINCT t.department_id, tl.location_id
                FROM teams t
                JOIN team_locations tl ON t.team_id = tl.team_id
                WHERE t.active = 1
                """
            ).fetchall()
            covered = {(tp[0], tp[1]) for tp in team_pairs}

            missing_teams = []
            for d in depts:
                for l in locs:
                    if (d["department_id"], l["location_id"]) not in covered:
                        missing_teams.append({
                            "department_id": d["department_id"],
                            "department_name": d["name"],
                            "location_id": l["location_id"],
                            "location_name": l["name"],
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
                if not l["in_charge_id"]:
                    missing_wardens.append({"location_id": l["location_id"], "location_name": l["name"]})

            return {
                "uncovered_pairs": missing_teams,
                "teams_without_backup": no_backup_teams,
                "teams_with_inactive_coordinator": inactive_coord_teams,
                "locations_without_warden": missing_wardens,
            }
