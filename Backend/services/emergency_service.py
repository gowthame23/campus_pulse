import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from core.constants import (
    CATEGORY_PRIORITY_MAP,
    EMERGENCY_OUTCOME_MISTAKE,
    EMERGENCY_OUTCOME_MISUSE,
    EMERGENCY_OUTCOME_REAL,
    EMERGENCY_STRIKE_LOCKOUT_DAYS,
    EMERGENCY_STRIKE_THRESHOLD,
    EMERGENCY_STRIKE_WINDOW_DAYS,
    EMERGENCY_UNACKNOWLEDGED_ALERT_MINUTES,
    get_sla_hours,
    normalize_priority,
)
from utils.helper import generate_id, now, now_string, parse_date
from utils.logger import get_logger

logger = get_logger(__name__)


class EmergencyService:
    def __init__(
        self,
        db_path="storage/campus_pulse.db",
        auth_service=None,
        team_service=None,
        notification_service=None,
        config_service=None,
        complaint_service=None,
    ):
        self.db_path = Path(db_path)
        self.auth_service = auth_service
        self.team_service = team_service
        self.notification_service = notification_service
        self.config_service = config_service
        self.complaint_service = complaint_service

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # =========================================================================
    # CATEGORIES
    # =========================================================================
    def get_categories(self, active_only: bool = True):
        with self._connect() as conn:
            query = "SELECT * FROM emergency_categories"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY sort_order ASC, name ASC"
            rows = conn.execute(query).fetchall()

            categories = []
            for r in rows:
                c = dict(r)
                dept_name = None
                if c.get("department_id") and self.auth_service:
                    dept = self.auth_service.get_department(c["department_id"])
                    dept_name = dept.name if dept else None
                c["department_name"] = dept_name
                categories.append(c)
            return categories

    def get_category(self, category_id_or_name: str):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM emergency_categories WHERE category_id = ? OR LOWER(name) = LOWER(?) LIMIT 1",
                (category_id_or_name, category_id_or_name),
            ).fetchone()
            if row:
                c = dict(row)
                if c.get("department_id") and self.auth_service:
                    dept = self.auth_service.get_department(c["department_id"])
                    c["department_name"] = dept.name if dept else None
                return c
            return None

    def create_category(self, name: str, department_id: str = None, sort_order: int = 0, is_active: bool = True):
        clean_name = name.strip()
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT category_id FROM emergency_categories WHERE LOWER(name) = LOWER(?) LIMIT 1",
                (clean_name,),
            ).fetchone()
            if existing:
                cid = existing["category_id"]
                conn.execute(
                    """
                    UPDATE emergency_categories
                    SET department_id = COALESCE(?, department_id),
                        sort_order = CASE WHEN ? != 0 THEN ? ELSE sort_order END,
                        is_active = ?
                    WHERE category_id = ?
                    """,
                    (department_id or None, sort_order, sort_order, int(is_active), cid),
                )
                conn.commit()
                return self.get_category(cid)

            cid = generate_id("EMCAT")
            now_ts = now_string()
            conn.execute(
                """
                INSERT INTO emergency_categories (category_id, name, department_id, is_active, sort_order, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (cid, clean_name, department_id or None, int(is_active), sort_order, now_ts),
            )
            conn.commit()
        return self.get_category(cid)

    def update_category(self, category_id: str, name: str = None, department_id: str = None, sort_order: int = None, is_active: bool = None):
        existing = self.get_category(category_id)
        if not existing:
            raise ValueError(f"Category {category_id} not found")
        u_name = name.strip() if name is not None else existing["name"]
        u_dept = department_id if department_id is not None else existing.get("department_id")
        u_sort = sort_order if sort_order is not None else existing.get("sort_order", 0)
        u_act = int(is_active) if is_active is not None else existing.get("is_active", 1)
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE emergency_categories
                SET name = ?, department_id = ?, sort_order = ?, is_active = ?
                WHERE category_id = ?
                """,
                (u_name, u_dept, u_sort, u_act, category_id),
            )
            conn.commit()
        return self.get_category(category_id)

    def delete_category(self, category_id: str):
        with self._connect() as conn:
            conn.execute("DELETE FROM emergency_categories WHERE category_id = ?", (category_id,))
            conn.commit()
        return True

    # =========================================================================
    # CONTACTS
    # =========================================================================
    def get_contacts(self, department_id: str = None, active_only: bool = True):
        with self._connect() as conn:
            query = "SELECT * FROM emergency_contacts WHERE 1=1"
            params = []
            if department_id:
                query += " AND department_id = ?"
                params.append(department_id)
            if active_only:
                query += " AND active = 1"
            query += " ORDER BY sort_order ASC, name ASC"
            rows = conn.execute(query, params).fetchall()

            contacts = []
            for r in rows:
                c = dict(r)
                if c.get("department_id") and self.auth_service:
                    dept = self.auth_service.get_department(c["department_id"])
                    c["department_name"] = dept.name if dept else None
                if c.get("location_id") and self.auth_service:
                    loc = self.auth_service.get_location(c["location_id"])
                    c["location_name"] = loc.name if loc else None
                contacts.append(c)
            return contacts

    def create_contact(
        self,
        name: str,
        phone: str,
        department_id: str = None,
        location_id: str = None,
        user_id: str = None,
        sort_order: int = 0,
        active: bool = True,
        night_only: bool = False,
        day_only: bool = False,
    ):
        cid = generate_id("EMCNT")
        now_ts = now_string()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO emergency_contacts (
                    contact_id, department_id, location_id, user_id, name, phone,
                    sort_order, active, night_only, day_only, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cid,
                    department_id or None,
                    location_id or None,
                    user_id or None,
                    name.strip(),
                    phone.strip(),
                    sort_order,
                    int(active),
                    int(night_only),
                    int(day_only),
                    now_ts,
                ),
            )
            conn.commit()
        return cid

    def update_contact(
        self,
        contact_id: str,
        name: str = None,
        phone: str = None,
        department_id: str = None,
        location_id: str = None,
        user_id: str = None,
        sort_order: int = None,
        active: bool = None,
        night_only: bool = None,
        day_only: bool = None,
    ):
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM emergency_contacts WHERE contact_id = ?", (contact_id,)).fetchone()
            if not row:
                raise ValueError(f"Contact {contact_id} not found")
            c = dict(row)
            u_name = name.strip() if name is not None else c["name"]
            u_phone = phone.strip() if phone is not None else c["phone"]
            u_dept = department_id if department_id is not None else c["department_id"]
            u_loc = location_id if location_id is not None else c["location_id"]
            u_usr = user_id if user_id is not None else c["user_id"]
            u_sort = sort_order if sort_order is not None else c["sort_order"]
            u_act = int(active) if active is not None else c["active"]
            u_night = int(night_only) if night_only is not None else c["night_only"]
            u_day = int(day_only) if day_only is not None else c["day_only"]

            conn.execute(
                """
                UPDATE emergency_contacts
                SET name = ?, phone = ?, department_id = ?, location_id = ?, user_id = ?,
                    sort_order = ?, active = ?, night_only = ?, day_only = ?
                WHERE contact_id = ?
                """,
                (u_name, u_phone, u_dept, u_loc, u_usr, u_sort, u_act, u_night, u_day, contact_id),
            )
            conn.commit()
        return True

    def delete_contact(self, contact_id: str):
        with self._connect() as conn:
            conn.execute("DELETE FROM emergency_contacts WHERE contact_id = ?", (contact_id,))
            conn.commit()
        return True

    # =========================================================================
    # STUDENT LOCKOUT & STRIKES
    # =========================================================================
    def get_student_status(self, user_id: str):
        """Check if student's emergency shortcut is paused due to 3 misuse strikes within 90 days."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT strike_id, complaint_id, created_at
                FROM emergency_strikes
                WHERE user_id = ?
                  AND datetime(created_at) >= datetime('now', '-90 days')
                ORDER BY created_at ASC
                """,
                (user_id,),
            ).fetchall()

            strikes = [dict(r) for r in rows]
            is_locked = False
            locked_until = None

            if len(strikes) >= EMERGENCY_STRIKE_THRESHOLD:
                # 3rd strike triggers 30-day lockout from that 3rd strike
                third_strike = strikes[EMERGENCY_STRIKE_THRESHOLD - 1]
                t_dt = parse_date(third_strike["created_at"])
                if t_dt:
                    pause_end = t_dt + timedelta(days=EMERGENCY_STRIKE_LOCKOUT_DAYS)
                    if now() < pause_end:
                        is_locked = True
                        locked_until = pause_end.strftime("%Y-%m-%d %H:%M:%S")

            recent_row = conn.execute(
                """
                SELECT complaint_id, is_emergency, emergency_category, reached, created_at
                FROM complaints
                WHERE created_by = ? AND is_emergency = 1
                ORDER BY created_at DESC LIMIT 1
                """,
                (user_id,),
            ).fetchone()

            active_emergency_id = None
            if recent_row:
                active_emergency_id = recent_row["complaint_id"]

            return {
                "user_id": user_id,
                "is_locked": is_locked,
                "locked_until": locked_until,
                "strikes_count": len(strikes),
                "active_emergency_id": active_emergency_id,
            }

    # =========================================================================
    # CALL LIST GENERATION (Rule 2.3d)
    # =========================================================================
    def _is_night_time(self) -> bool:
        """Determines if current time is within configured night hours window."""
        start_str = "20:00"
        end_str = "08:00"
        if self.config_service:
            try:
                start_str = self.config_service.get_value("night_hours_start") or "20:00"
                end_str = self.config_service.get_value("night_hours_end") or "08:00"
            except Exception:
                pass

        cur_time_str = now().strftime("%H:%M")
        if start_str > end_str:
            # e.g. 20:00 to 08:00
            return cur_time_str >= start_str or cur_time_str < end_str
        else:
            return start_str <= cur_time_str < end_str

    def get_call_list(self, user, category_id_or_name: str, location_id: str = None):
        """Generates sorted, deduplicated, day/night filtered emergency call list."""
        category = self.get_category(category_id_or_name)
        cat_name = category["name"] if category else category_id_or_name
        dept_id = category.get("department_id") if category else None

        # Resolve student location
        loc_id = location_id or getattr(user, "location_id", None)
        if not loc_id and self.auth_service and hasattr(self.auth_service, "get_student_profile"):
            prof = self.auth_service.get_student_profile(user.user_id)
            if prof:
                loc_id = prof.get("location_id")
        loc_obj = self.auth_service.get_location(loc_id) if (loc_id and self.auth_service) else None
        loc_name = loc_obj.name if loc_obj else "Campus"

        # 1. 112 National Emergency Hotline
        hotline_row = {
            "name": "112 Emergency Services",
            "role": "National Emergency Hotline",
            "phone": "112",
            "is_hotline": True,
        }

        # 2. Campus Security
        sec_name = "Campus Security"
        sec_phone = "+91 98765 43210"
        if self.config_service:
            try:
                sec_name = self.config_service.get_value("campus_security_name") or sec_name
                sec_phone = self.config_service.get_value("campus_security_phone") or sec_phone
            except Exception:
                pass
        security_row = {
            "name": sec_name,
            "role": "Security Desk",
            "phone": sec_phone,
            "is_security": True,
        }

        # 3. Your Warden
        warden_row = None
        if loc_obj and getattr(loc_obj, "in_charge_id", None) and self.auth_service:
            warden_user = self.auth_service.get_user(loc_obj.in_charge_id)
            if warden_user:
                w_phone = getattr(warden_user, "phone_number", None) or getattr(warden_user, "phone", "")
                if w_phone:
                    warden_row = {
                        "name": warden_user.name,
                        "role": f"Your Warden – {loc_obj.name}",
                        "phone": w_phone,
                        "user_id": warden_user.user_id,
                    }

        # 4. Acting Coordinator
        coord_row = None
        dept_obj = self.auth_service.get_department(dept_id) if (dept_id and self.auth_service) else None
        dept_label = dept_obj.name if dept_obj else cat_name
        if loc_id and dept_id and self.team_service:
            team = self.team_service.get_team_for_location_department(loc_id, dept_id)
            if team:
                acting_coord = self.team_service.get_acting_coordinator(team)
                if acting_coord:
                    c_phone = getattr(acting_coord, "phone_number", None) or getattr(acting_coord, "phone", "")
                    if c_phone:
                        coord_row = {
                            "name": acting_coord.name,
                            "role": f"Coordinator – {dept_label}",
                            "phone": c_phone,
                            "user_id": acting_coord.user_id,
                        }

        # 5. Department Emergency Contacts
        dept_contact_rows = []
        is_night = self._is_night_time()
        if dept_id:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT * FROM emergency_contacts
                    WHERE department_id = ? AND active = 1
                    ORDER BY sort_order ASC
                    """,
                    (dept_id,),
                ).fetchall()

                # Filter day/night
                candidates = []
                for r in rows:
                    c = dict(r)
                    if is_night and c.get("day_only"):
                        continue
                    if not is_night and c.get("night_only"):
                        continue
                    candidates.append(c)

                # Sort: location-specific first, then general (location_id IS NULL)
                def sort_key(item):
                    is_loc_match = 0 if (loc_id and item.get("location_id") == loc_id) else 1
                    return (is_loc_match, item.get("sort_order", 0))

                candidates.sort(key=sort_key)
                for item in candidates:
                    dept_contact_rows.append({
                        "name": item["name"],
                        "role": dept_label,
                        "phone": item["phone"],
                        "user_id": item.get("user_id"),
                    })

        # Order selection based on category
        cat_lower = (cat_name or "").strip().lower()
        is_fire_or_medical = any(x in cat_lower for x in ("fire", "smoke", "medical"))

        raw_list = []
        if is_fire_or_medical:
            # 1. 112
            # 2. Campus security (if set)
            # 3. Your Warden
            # 4. Department contacts and Coordinator (if a department is mapped)
            raw_list.append(hotline_row)
            if security_row and security_row.get("phone"):
                raw_list.append(security_row)
            if warden_row:
                raw_list.append(warden_row)
            raw_list.extend(dept_contact_rows)
            if coord_row:
                raw_list.append(coord_row)
        else:
            # 1. Department emergency contacts (location-specific first, day/night filtered)
            # 2. Team's acting Coordinator (backup if Coordinator on leave)
            # 3. Your Warden (Warden of the student's own location)
            # 4. Campus security (if set)
            # 5. 112 (always last row, always visible)
            raw_list.extend(dept_contact_rows)
            if coord_row:
                raw_list.append(coord_row)
            if warden_row:
                raw_list.append(warden_row)
            if security_row and security_row.get("phone"):
                raw_list.append(security_row)
            raw_list.append(hotline_row)

        # Deduplicate while preserving order (and ensuring 112 stays at top/bottom as intended)
        deduped = []
        seen_phones = set()
        for item in raw_list:
            clean_phone = item["phone"].replace(" ", "").replace("-", "").lower()
            if clean_phone not in seen_phones:
                seen_phones.add(clean_phone)
                deduped.append(item)

        return deduped

    # =========================================================================
    # CREATE EMERGENCY COMPLAINT (Rule 2.3e)
    # =========================================================================
    def create_emergency(self, user, category_id_or_name: str, location_id: str = None):
        """Auto-creates Critical emergency complaint immediately upon category selection."""
        # Check lockout
        status = self.get_student_status(user.user_id)
        if status["is_locked"]:
            raise PermissionError(f"Emergency shortcut paused until {status['locked_until']}")

        category = self.get_category(category_id_or_name)
        cat_name = category["name"] if category else category_id_or_name
        dept_id = category.get("department_id") if category else None

        # Resolve student location
        loc_id = location_id or getattr(user, "location_id", None)
        if not loc_id and self.auth_service and hasattr(self.auth_service, "get_student_profile"):
            prof = self.auth_service.get_student_profile(user.user_id)
            if prof:
                loc_id = prof.get("location_id")
        if not loc_id and self.auth_service:
            locs = self.auth_service.list_locations()
            if locs:
                loc_id = locs[0].location_id

        loc_obj = self.auth_service.get_location(loc_id) if (loc_id and self.auth_service) else None
        loc_name = loc_obj.name if loc_obj else "Campus"

        # Check frequent submissions (> 2 in 24 hours -> alert warden, Rule 2.5e)
        warden_id = getattr(loc_obj, "in_charge_id", None) if loc_obj else None
        with self._connect() as conn:
            cnt_24h = conn.execute(
                """
                SELECT COUNT(*) FROM complaints
                WHERE created_by = ? AND is_emergency = 1
                  AND datetime(created_at) >= datetime('now', '-24 hours')
                """,
                (user.user_id,),
            ).fetchone()[0]

            if cnt_24h >= 2 and warden_id and self.notification_service:
                self.notification_service.notify(
                    warden_id,
                    f"Student {user.name} has submitted {cnt_24h + 1} emergencies in the last 24 hours.",
                    title="⚠️ Multiple Emergency Reports",
                    notification_type="alert",
                )

        # Auto-create complaint
        cid = generate_id("CMP")
        now_ts = now_string()
        now_dt = now()
        sla_hours = get_sla_hours("Critical", category=cat_name)
        sla_deadline = (now_dt + timedelta(hours=sla_hours)).strftime("%Y-%m-%d %H:%M:%S")

        # Resolve department if missing
        if not dept_id:
            dept_id = "DEPT_OTHER"

        # Team routing
        team = None
        acting_coord = None
        if self.team_service:
            team = self.team_service.get_team_for_location_department(loc_id, dept_id)
            if team:
                acting_coord = self.team_service.get_acting_coordinator(team)

        team_id = team["team_id"] if team else None

        # Build complaint dict
        initial_history = [
            {"at": now_ts, "message": f"🚨 Emergency complaint created by {user.name}."},
        ]
        if team:
            initial_history.append({"at": now_ts, "message": f"Routed to team '{team['name']}'."})

        complaint_dict = {
            "complaint_id": cid,
            "created_by": user.user_id,
            "creator_role": user.role,
            "location_id": loc_id,
            "department_id": dept_id,
            "complaint_type": "Emergency",
            "description": f"Emergency: {cat_name}",
            "status": "Submitted",
            "assigned_to": None,
            "created_at": now_ts,
            "updated_at": now_ts,
            "resolved_at": None,
            "verification_due_at": None,
            "reopen_count": 0,
            "auto_closed": False,
            "escalated": False,
            "admin_notified": False,
            "resolution_notes": "",
            "verification_reports": [],
            "history": initial_history,
            "archived": False,
            "priority": "Critical",
            "category": cat_name,
            "visibility_type": "Private",
            "title": f"🚨 Emergency: {cat_name}",
            "sla_deadline": sla_deadline,
            "assigned_at": None,
            "started_at": None,
            "auto_assigned": False,
            "is_urgent": True,
            "urgent_reason": "Emergency report",
            "awaiting_assign_since": now_ts,
            "team_id": team_id,
            "is_emergency": True,
            "emergency_category": cat_name,
            "reached": None,
            "reached_at": None,
            "acknowledged_by": None,
            "acknowledged_at": None,
            "emergency_outcome": None,
            "emergency_realert_sent": False,
        }

        # Save to database
        if self.complaint_service:
            from models.complaint import Complaint
            c_model = Complaint.from_dict(complaint_dict)
            self.complaint_service.save_complaint(c_model)
        else:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO complaints (
                        complaint_id, created_by, creator_role, location_id, department_id,
                        complaint_type, description, status, created_at, updated_at,
                        priority, category, visibility_type, title, sla_deadline, is_urgent,
                        awaiting_assign_since, team_id, is_emergency, emergency_category,
                        history, verification_reports, resolution_notes
                    ) VALUES (
                        ?, ?, ?, ?, ?, ?, ?, 'Submitted', ?, ?, 'Critical', ?, 'Private', ?, ?, 1,
                        ?, ?, 1, ?, ?, '[]', ''
                    )
                    """,
                    (
                        cid, user.user_id, user.role, loc_id, dept_id,
                        "Emergency", f"Emergency: {cat_name}", now_ts, now_ts,
                        cat_name, f"🚨 Emergency: {cat_name}", sla_deadline,
                        now_ts, team_id, cat_name, json.dumps(initial_history),
                    ),
                )
                conn.commit()

        # Send urgent alerts (Push + In-App, Rule 2.3g)
        alert_msg = f"🚨 EMERGENCY: {cat_name} at {loc_name} — reported by {user.name}"
        alerted_users = set()

        # 1. Acting coordinator
        if acting_coord:
            alerted_users.add(acting_coord.user_id)

        # 2. Department emergency contacts who are registered app users
        with self._connect() as conn:
            cnt_rows = conn.execute(
                "SELECT user_id FROM emergency_contacts WHERE department_id = ? AND active = 1 AND user_id IS NOT NULL",
                (dept_id,),
            ).fetchall()
            for r in cnt_rows:
                if r["user_id"]:
                    alerted_users.add(r["user_id"])

        # 3. Location Warden
        if warden_id:
            alerted_users.add(warden_id)

        # 4. App Managers
        if self.auth_service:
            for u in self.auth_service.list_users():
                if (getattr(u, "role", "") or "").lower() == "app_manager":
                    alerted_users.add(u.user_id)

        # Dispatch notifications
        if self.notification_service:
            for uid in alerted_users:
                try:
                    self.notification_service.publish(
                        receiver_id=uid,
                        title="🚨 URGENT EMERGENCY",
                        message=alert_msg,
                        module="Complaint",
                        notification_type="alert",
                        reference_type="Complaint",
                        reference_id=cid,
                        priority="Critical",
                    )
                except Exception as err:
                    logger.warning(f"Failed to alert {uid} of emergency: {err}")

        return complaint_dict

    # =========================================================================
    # REACHED / CALL FEEDBACK (Rule 2.3f)
    # =========================================================================
    def record_reached(self, complaint_id: str, reached: bool, user):
        """Records whether caller reached someone. If 'No answer', immediately re-alerts."""
        now_ts = now_string()
        reached_val = 1 if reached else 0
        reached_at_val = now_ts if reached else None

        with self._connect() as conn:
            row = conn.execute("SELECT * FROM complaints WHERE complaint_id = ?", (complaint_id,)).fetchone()
            if not row:
                raise ValueError(f"Complaint {complaint_id} not found")
            c = dict(row)

            # Update history
            hist = []
            try:
                hist = json.loads(c.get("history") or "[]")
            except Exception:
                pass
            note = f"Caller reported: Reached staff directly." if reached else f"Caller reported: No answer on emergency call!"
            hist.append({"at": now_ts, "message": note})

            conn.execute(
                """
                UPDATE complaints
                SET reached = ?, reached_at = ?, history = ?, updated_at = ?
                WHERE complaint_id = ?
                """,
                (reached_val, reached_at_val, json.dumps(hist), now_ts, complaint_id),
            )
            conn.commit()

        # If not reached ("No answer"), immediately re-alert staff (Rule 2.3f)
        if not reached and self.notification_service:
            cat_name = c.get("emergency_category") or "Emergency"
            loc_id = c.get("location_id")
            loc_obj = self.auth_service.get_location(loc_id) if (loc_id and self.auth_service) else None
            loc_name = loc_obj.name if loc_obj else "Campus"
            realert_msg = f"🚨 EMERGENCY UNANSWERED: {cat_name} at {loc_name} — caller reported No Answer! Immediate response required."

            # Find recipients
            recipients = set()
            team_id = c.get("team_id")
            if team_id and self.team_service:
                team = self.team_service.get_team(team_id)
                if team:
                    ac = self.team_service.get_acting_coordinator(team)
                    if ac:
                        recipients.add(ac.user_id)
            if loc_obj and getattr(loc_obj, "in_charge_id", None):
                recipients.add(loc_obj.in_charge_id)
            if self.auth_service:
                for u in self.auth_service.list_users():
                    if (getattr(u, "role", "") or "").lower() == "app_manager":
                        recipients.add(u.user_id)

            for uid in recipients:
                try:
                    self.notification_service.publish(
                        receiver_id=uid,
                        title="🚨 EMERGENCY UNANSWERED",
                        message=realert_msg,
                        module="Complaint",
                        notification_type="alert",
                        reference_type="Complaint",
                        reference_id=complaint_id,
                        priority="Critical",
                    )
                except Exception as e:
                    logger.warning(f"Failed to re-alert {uid}: {e}")

        return {"complaint_id": complaint_id, "reached": reached}

    # =========================================================================
    # STAFF ACKNOWLEDGMENT ("I'm on it", Rule 2.4a)
    # =========================================================================
    def acknowledge_emergency(self, complaint_id: str, user):
        """Staff member clicks 'I'm on it'."""
        now_ts = now_string()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM complaints WHERE complaint_id = ?", (complaint_id,)).fetchone()
            if not row:
                raise ValueError(f"Complaint {complaint_id} not found")
            c = dict(row)

            hist = []
            try:
                hist = json.loads(c.get("history") or "[]")
            except Exception:
                pass
            time_part = now_ts[11:16]
            hist.append({"at": now_ts, "message": f"{user.name} is on it at {time_part}."})

            conn.execute(
                """
                UPDATE complaints
                SET acknowledged_by = ?, acknowledged_at = ?, history = ?, updated_at = ?
                WHERE complaint_id = ?
                """,
                (user.user_id, now_ts, json.dumps(hist), now_ts, complaint_id),
            )
            conn.commit()

        # Notify student (submitter)
        if self.notification_service and c.get("created_by"):
            try:
                self.notification_service.notify(
                    c["created_by"],
                    f"{user.name} is on it for your emergency.",
                    complaint_id=complaint_id,
                    title="Staff is on it",
                    notification_type="info",
                )
            except Exception as e:
                logger.warning(f"Failed to notify student: {e}")

        return {
            "complaint_id": complaint_id,
            "acknowledged_by": user.user_id,
            "acknowledged_by_name": user.name,
            "acknowledged_at": now_ts,
        }

    # =========================================================================
    # 10-MINUTE UNACKNOWLEDGED CHECK (Rule 2.4b)
    # =========================================================================
    def check_unacknowledged_emergencies(self):
        """Re-alerts once if nobody clicked 'I'm on it' within 10 minutes."""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM complaints
                WHERE is_emergency = 1
                  AND acknowledged_at IS NULL
                  AND emergency_realert_sent = 0
                  AND datetime(created_at) <= datetime('now', '-10 minutes')
                """
            ).fetchall()

            for r in rows:
                c = dict(r)
                cid = c["complaint_id"]
                cat_name = c.get("emergency_category") or "Emergency"
                loc_id = c.get("location_id")
                loc_obj = self.auth_service.get_location(loc_id) if (loc_id and self.auth_service) else None
                loc_name = loc_obj.name if loc_obj else "Campus"

                # Mark realert sent
                conn.execute(
                    "UPDATE complaints SET emergency_realert_sent = 1 WHERE complaint_id = ?",
                    (cid,),
                )

                # Re-alert staff + App Manager + Admin (once)
                recipients = set()
                team_id = c.get("team_id")
                if team_id and self.team_service:
                    team = self.team_service.get_team(team_id)
                    if team:
                        ac = self.team_service.get_acting_coordinator(team)
                        if ac:
                            recipients.add(ac.user_id)
                if loc_obj and getattr(loc_obj, "in_charge_id", None):
                    recipients.add(loc_obj.in_charge_id)
                if self.auth_service:
                    for u in self.auth_service.list_users():
                        role_l = (getattr(u, "role", "") or "").lower()
                        if role_l in ("app_manager", "administrator", "admin"):
                            recipients.add(u.user_id)

                realert_msg = f"⚠️ UNACKNOWLEDGED EMERGENCY: {cat_name} at {loc_name} has not been acknowledged for over 10 minutes!"
                if self.notification_service:
                    for uid in recipients:
                        try:
                            self.notification_service.publish(
                                receiver_id=uid,
                                title="⚠️ EMERGENCY UNACKNOWLEDGED (10m)",
                                message=realert_msg,
                                module="Complaint",
                                notification_type="alert",
                                reference_type="Complaint",
                                reference_id=cid,
                                priority="Critical",
                            )
                        except Exception as e:
                            logger.warning(f"Failed to 10m realert {uid}: {e}")
            conn.commit()

    # =========================================================================
    # OUTCOME & MISUSE STRIKES (Rule 2.5b, 2.5c)
    # =========================================================================
    def mark_outcome(self, complaint_id: str, outcome: str, user):
        """Warden or Coordinator marks outcome ('real', 'mistake', 'misuse')."""
        valid_outcomes = (EMERGENCY_OUTCOME_REAL, EMERGENCY_OUTCOME_MISTAKE, EMERGENCY_OUTCOME_MISUSE)
        clean_outcome = str(outcome).strip().lower()
        if clean_outcome not in valid_outcomes:
            raise ValueError(f"Invalid outcome '{outcome}'. Must be one of {valid_outcomes}.")

        now_ts = now_string()
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM complaints WHERE complaint_id = ?", (complaint_id,)).fetchone()
            if not row:
                raise ValueError(f"Complaint {complaint_id} not found")
            c = dict(row)

            student_id = c["created_by"]
            hist = []
            try:
                hist = json.loads(c.get("history") or "[]")
            except Exception:
                pass
            outcome_label = "Real emergency" if clean_outcome == "real" else ("Genuine mistake" if clean_outcome == "mistake" else "Misuse")
            hist.append({"at": now_ts, "message": f"Emergency outcome marked as '{outcome_label}' by {user.name}."})

            if clean_outcome == EMERGENCY_OUTCOME_MISUSE:
                # Rule 2.5b: Misuse -> is_emergency cleared (0), priority reset to normal priority, deadline recalculated
                cat_key = (c.get("emergency_category") or c.get("category") or "").strip().lower()
                normal_priority = CATEGORY_PRIORITY_MAP.get(cat_key, "Medium")
                normal_priority = normalize_priority(normal_priority)

                created_dt = parse_date(c["created_at"]) or now()
                sla_hours = get_sla_hours(normal_priority, category=cat_key)
                new_deadline = (created_dt + timedelta(hours=sla_hours)).strftime("%Y-%m-%d %H:%M:%S")

                conn.execute(
                    """
                    UPDATE complaints
                    SET emergency_outcome = ?, is_emergency = 0, priority = ?, sla_deadline = ?,
                        history = ?, updated_at = ?
                    WHERE complaint_id = ?
                    """,
                    (clean_outcome, normal_priority, new_deadline, json.dumps(hist), now_ts, complaint_id),
                )

                # Record misuse strike
                sid = generate_id("STRK")
                conn.execute(
                    """
                    INSERT INTO emergency_strikes (strike_id, user_id, complaint_id, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (sid, student_id, complaint_id, now_ts),
                )

                # Count strikes in last 90 days
                cnt_strikes = conn.execute(
                    """
                    SELECT COUNT(*) FROM emergency_strikes
                    WHERE user_id = ? AND datetime(created_at) >= datetime('now', '-90 days')
                    """,
                    (student_id,),
                ).fetchone()[0]
            else:
                # "real" or "mistake"
                conn.execute(
                    """
                    UPDATE complaints
                    SET emergency_outcome = ?, history = ?, updated_at = ?
                    WHERE complaint_id = ?
                    """,
                    (clean_outcome, json.dumps(hist), now_ts, complaint_id),
                )
            conn.commit()

        # Send notifications after database transaction has committed
        if clean_outcome == EMERGENCY_OUTCOME_MISUSE and self.notification_service:
            if cnt_strikes == 1:
                self.notification_service.notify(
                    student_id,
                    "Warning: You received a strike for reporting an emergency that was marked as Misuse.",
                    complaint_id=complaint_id,
                    title="⚠️ Emergency Misuse Warning",
                    notification_type="alert",
                )
            elif cnt_strikes == 2:
                self.notification_service.notify(
                    student_id,
                    "Warning: You received a 2nd strike for emergency misuse.",
                    complaint_id=complaint_id,
                    title="⚠️ Emergency Misuse 2nd Strike",
                    notification_type="alert",
                )
                loc_id = c.get("location_id")
                loc_obj = self.auth_service.get_location(loc_id) if (loc_id and self.auth_service) else None
                if loc_obj and getattr(loc_obj, "in_charge_id", None):
                    self.notification_service.notify(
                        loc_obj.in_charge_id,
                        f"Student {student_id} received a 2nd emergency misuse strike.",
                        complaint_id=complaint_id,
                        title="Student Misuse Strike Alert",
                        notification_type="alert",
                    )
            elif cnt_strikes >= 3:
                pause_date = (now() + timedelta(days=EMERGENCY_STRIKE_LOCKOUT_DAYS)).strftime("%Y-%m-%d")
                self.notification_service.notify(
                    student_id,
                    f"Emergency shortcut paused until {pause_date} due to 3 misuse strikes within 90 days.",
                    complaint_id=complaint_id,
                    title="🚨 Emergency Shortcut Paused",
                    notification_type="alert",
                )

        return {"complaint_id": complaint_id, "outcome": clean_outcome}

    # =========================================================================
    # STATS (Rule 2.8)
    # =========================================================================
    def get_stats(self):
        """Returns emergency statistics per location and per team."""
        with self._connect() as conn:
            # 1. Location stats
            loc_rows = conn.execute(
                """
                SELECT
                    location_id,
                    COUNT(*) as total_emergencies,
                    SUM(CASE WHEN reached = 1 THEN 1 ELSE 0 END) as reached_count,
                    SUM(CASE WHEN emergency_outcome = 'real' THEN 1 ELSE 0 END) as real_count,
                    SUM(CASE WHEN emergency_outcome = 'mistake' THEN 1 ELSE 0 END) as mistake_count,
                    SUM(CASE WHEN emergency_outcome = 'misuse' THEN 1 ELSE 0 END) as misuse_count
                FROM complaints
                WHERE is_emergency = 1 OR emergency_outcome IS NOT NULL
                GROUP BY location_id
                """
            ).fetchall()

            location_stats = []
            for r in loc_rows:
                loc_dict = dict(r)
                lid = loc_dict["location_id"]
                loc_obj = self.auth_service.get_location(lid) if self.auth_service else None
                loc_dict["location_name"] = loc_obj.name if loc_obj else lid

                # Calculate avg time to acknowledge
                ack_rows = conn.execute(
                    """
                    SELECT created_at, acknowledged_at
                    FROM complaints
                    WHERE location_id = ? AND (is_emergency = 1 OR emergency_outcome IS NOT NULL) AND acknowledged_at IS NOT NULL
                    """,
                    (lid,),
                ).fetchall()
                durations = []
                for ar in ack_rows:
                    c_dt = parse_date(ar["created_at"])
                    a_dt = parse_date(ar["acknowledged_at"])
                    if c_dt and a_dt:
                        diff_sec = (a_dt - c_dt).total_seconds()
                        if diff_sec >= 0:
                            durations.append(diff_sec)
                avg_ack = round(sum(durations) / len(durations) / 60, 1) if durations else None
                loc_dict["avg_acknowledge_minutes"] = avg_ack

                total = loc_dict["total_emergencies"] or 1
                loc_dict["reached_percentage"] = round((loc_dict["reached_count"] / total) * 100, 1)
                location_stats.append(loc_dict)

            # 2. Team stats
            team_rows = conn.execute(
                """
                SELECT
                    team_id,
                    COUNT(*) as total_emergencies,
                    SUM(CASE WHEN reached = 1 THEN 1 ELSE 0 END) as reached_count,
                    SUM(CASE WHEN emergency_outcome = 'real' THEN 1 ELSE 0 END) as real_count,
                    SUM(CASE WHEN emergency_outcome = 'mistake' THEN 1 ELSE 0 END) as mistake_count,
                    SUM(CASE WHEN emergency_outcome = 'misuse' THEN 1 ELSE 0 END) as misuse_count
                FROM complaints
                WHERE (is_emergency = 1 OR emergency_outcome IS NOT NULL) AND team_id IS NOT NULL
                GROUP BY team_id
                """
            ).fetchall()

            team_stats = []
            for r in team_rows:
                td = dict(r)
                tid = td["team_id"]
                team = self.team_service.get_team(tid) if self.team_service else None
                td["team_name"] = team["name"] if team else tid

                ack_rows = conn.execute(
                    """
                    SELECT created_at, acknowledged_at
                    FROM complaints
                    WHERE team_id = ? AND (is_emergency = 1 OR emergency_outcome IS NOT NULL) AND acknowledged_at IS NOT NULL
                    """,
                    (tid,),
                ).fetchall()
                durations = []
                for ar in ack_rows:
                    c_dt = parse_date(ar["created_at"])
                    a_dt = parse_date(ar["acknowledged_at"])
                    if c_dt and a_dt:
                        diff_sec = (a_dt - c_dt).total_seconds()
                        if diff_sec >= 0:
                            durations.append(diff_sec)
                avg_ack = round(sum(durations) / len(durations) / 60, 1) if durations else None
                td["avg_acknowledge_minutes"] = avg_ack

                total = td["total_emergencies"] or 1
                td["reached_percentage"] = round((td["reached_count"] / total) * 100, 1)
                team_stats.append(td)

            return {
                "by_location": location_stats,
                "by_team": team_stats,
            }

