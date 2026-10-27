import hashlib
import json
import os
import re
import sqlite3
from pathlib import Path

from models.administrator import Administrator
from models.app_manager import AppManager
from models.coordinator import Coordinator
from models.department import Department
from models.location import Location
from models.location_in_charge import LocationInCharge
from models.student import Student
from models.user import User
from storage.sqlite_repository import SQLiteRepository
from utils.helper import generate_id, now_string
from utils.logger import get_logger
from utils.passwords import (
    generate_temp_password,
    hash_password,
    is_password_hash,
    needs_rehash,
    validate_password_complexity,
    verify_password,
)

_DUMMY_PASSWORD_HASH = hash_password("timing-equalization-only")
logger = get_logger(__name__)

class AuthService:
    EMAIL_REGEX = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

    def __init__(self, db_path=None, notification_service=None):
        if db_path is None:
            from utils.db import get_db_path
            db_path = get_db_path()
        elif not Path(db_path).is_absolute():
            from utils.db import BACKEND_DIR
            db_path = str((BACKEND_DIR / db_path).resolve())
        self.db_path = Path(db_path)
        self.repository = SQLiteRepository(str(self.db_path), self._default_data())
        if not notification_service:
            from services.notification_service import NotificationService

            self.notification_service = NotificationService(db_path=db_path)
        else:
            self.notification_service = notification_service
        self.ensure_seed_data()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _default_data(self):
        return {"users": [], "departments": [], "locations": []}

    def ensure_seed_data(self):
        data = self.repository.load()
        changed = False
        if "locations" not in data or data["locations"] is None:
            data["locations"] = []

        existing_loc_ids = {l["location_id"]: l for l in data["locations"]}
        existing_loc_names = {l["name"].strip().lower(): l for l in data["locations"] if l.get("name")}

        template_locations = [
            Location("Other / Not Sure", location_id="LOC_OTHER", location_type="Other / Not Sure", in_charge_id="USR_ADMIN", app_manager_id="USR_ADMIN").to_dict(),
        ]
        for tloc in template_locations:
            if tloc["location_id"] not in existing_loc_ids and tloc["name"].strip().lower() not in existing_loc_names:
                data["locations"].append(tloc)
                existing_loc_ids[tloc["location_id"]] = tloc
                existing_loc_names[tloc["name"].strip().lower()] = tloc
                changed = True

        # Phase 3 Initial Locations & Assignments (2 locations per operational type)
        initial_locations_spec = [
            # Group 1: Assigned to App Manager 1 and Warden 1
            {"id": "LOC_HOSTEL_1", "name": "Hostel 1", "type": "Hostel", "mgr": "USR_MANAGER", "warden": "USR_WARDEN"},
            {"id": "LOC_ACADEMIC_1", "name": "Academic Block 1", "type": "Academic Block", "mgr": "USR_MANAGER", "warden": "USR_WARDEN"},
            {"id": "LOC_MESS_1", "name": "Mess 1", "type": "Mess", "mgr": "USR_MANAGER", "warden": "USR_WARDEN"},
            {"id": "LOC_SAC_1", "name": "Student Activity Center 1", "type": "Student Activity Center", "mgr": "USR_MANAGER", "warden": "USR_WARDEN"},
            {"id": "LOC_SPORTS_1", "name": "Sports Complex 1", "type": "Sports Complex", "mgr": "USR_MANAGER", "warden": "USR_WARDEN"},

            # Group 2: Assigned to App Manager 2 and Warden 2
            {"id": "LOC_HOSTEL_2", "name": "Hostel 2", "type": "Hostel", "mgr": "USR_MANAGER_2", "warden": "USR_WARDEN_2"},
            {"id": "LOC_ACADEMIC_2", "name": "Academic Block 2", "type": "Academic Block", "mgr": "USR_MANAGER_2", "warden": "USR_WARDEN_2"},
            {"id": "LOC_MESS_2", "name": "Mess 2", "type": "Mess", "mgr": "USR_MANAGER_2", "warden": "USR_WARDEN_2"},
            {"id": "LOC_SAC_2", "name": "Student Activity Center 2", "type": "Student Activity Center", "mgr": "USR_MANAGER_2", "warden": "USR_WARDEN_2"},
            {"id": "LOC_SPORTS_2", "name": "Sports Complex 2", "type": "Sports Complex", "mgr": "USR_MANAGER_2", "warden": "USR_WARDEN_2"},
        ]
        for lspec in initial_locations_spec:
            loc_match = existing_loc_ids.get(lspec["id"]) or existing_loc_names.get(lspec["name"].strip().lower())
            if not loc_match:
                new_loc = Location(
                    lspec["name"],
                    location_id=lspec["id"],
                    in_charge_id=lspec["warden"],
                    app_manager_id=lspec["mgr"],
                    location_type=lspec["type"]
                ).to_dict()
                data["locations"].append(new_loc)
                existing_loc_ids[lspec["id"]] = new_loc
                existing_loc_names[lspec["name"].strip().lower()] = new_loc
                changed = True
            else:
                if not loc_match.get("app_manager_id"):
                    loc_match["app_manager_id"] = lspec["mgr"]
                    changed = True
                if not loc_match.get("in_charge_id"):
                    loc_match["in_charge_id"] = lspec["warden"]
                    changed = True
                if not loc_match.get("location_type"):
                    loc_match["location_type"] = lspec["type"]
                    changed = True

        if not data.get("departments"):
            data["departments"] = [
                Department("Electrical", 2, department_id="DEPT_HOSTEL_ELECTRICAL", complaint_types=[
                    "Power Failure", "Fan Not Working", "Light Not Working", "Switch Problem", "Socket Problem",
                    "Projector Not Working / No Display", "Audio / Speaker / Mic Issue", "AC / Air Conditioning Issue", "Other / Not Sure"
                ], coordinator_id="USR_COORD_1", coordinator_2_id="USR_COORD_2").to_dict(),
                Department("Plumbing", 3, department_id="DEPT_HOSTEL_PLUMBING", complaint_types=[
                    "Water Leakage", "Tap Not Working / Tap Leakage", "No Water Supply", "Low Water Pressure",
                    "Toilet Flush Not Working", "Toilet Blockage", "Wash Basin / Sink Blockage", "Drainage Blockage",
                    "Shower Not Working", "Water Cooler / Dispenser Issue", "Other / Not Sure"
                ], coordinator_id="USR_COORD_1", coordinator_2_id="USR_COORD_2").to_dict(),
                Department("Housekeeping", 1, department_id="DEPT_HOSTEL_HOUSEKEEPING", complaint_types=[
                    "Room Cleaning Required", "Washroom / Bathroom Cleaning", "Dustbin / Waste Removal",
                    "Corridor / Common Area Cleaning", "Classroom / Lab Cleaning Required", "Other / Not Sure"
                ]).to_dict(),
                Department("Furniture & Carpentry", 5, department_id="DEPT_HOSTEL_FURNITURE", complaint_types=[
                    "Cot / Bed Frame Issue", "Study Table / Chair Damaged", "Cupboard / Wardrobe Lock/Door Issue",
                    "Door / Window Latch Problem", "Desk / Bench Damaged", "Missing Furniture / Item", "Other / Not Sure"
                ]).to_dict(),
                Department("Network & IT", 3, department_id="DEPT_HOSTEL_NETWORK", complaint_types=[
                    "Wi-Fi Not Working", "Wi-Fi Connected but No Internet", "Slow Internet",
                    "Frequent Wi-Fi Disconnection", "Weak Wi-Fi Signal", "Ethernet / LAN Port Not Working", "Other / Not Sure"
                ]).to_dict(),
                Department("Food Quality & Catering", 1, department_id="DEPT_MESS_FOOD", complaint_types=[
                    "Food Quality / Taste Issue", "Undercooked / Raw Food", "Foreign Object in Food",
                    "Food / Utensil Shortage", "Counter / Service Delay", "Other / Not Sure"
                ]).to_dict(),
                Department("Maintenance & Equipment", 3, department_id="DEPT_MESS_MAINTENANCE", complaint_types=[
                    "Water Cooler / Dispenser Issue", "Food Warmer / Bain-Marie Not Working", "Exhaust Fan / Ventilation Issue",
                    "Lighting / Electrical Issue", "Fly Catcher Machine Not Working", "Other / Not Sure"
                ]).to_dict(),
                Department("Other / Not Sure", 2, department_id="DEPT_OTHER_GENERAL", complaint_types=[
                    "Issue Not Listed / General Complaint", "Urgent Safety or Security Issue",
                    "Infrastructure / Outdoor Maintenance", "General Campus Cleanliness"
                ]).to_dict(),
            ]
            changed = True

        seed_users_spec = [
            {
                "id": "USR_SUPER_ADMIN",
                "class": User,
                "name": "Platform Super Admin",
                "email": os.environ.get("SUPER_ADMIN_EMAIL", "superadmin@campuspulse.edu"),
                "password_env": "SUPER_ADMIN_PASSWORD",
                "default_password": "Superadmin@123",
                "first_login": False,
                "kwargs": {"role": "super_admin"},
            },
            {
                "id": "USR_ADMIN",
                "class": Administrator,
                "name": "Platform Administrator",
                "email": os.environ.get("ADMIN_EMAIL", "gowthamejjurothu@gmail.com"),
                "password_env": "ADMIN_PASSWORD",
                "default_password": "Admin@123",
                "first_login": False,
                "kwargs": {},
            },
            {
                "id": "USR_MANAGER",
                "class": AppManager,
                "name": "App Manager 1",
                "email": os.environ.get("MANAGER_EMAIL", "ejjurothugowtham@gmail.com"),
                "password_env": "MANAGER_PASSWORD",
                "default_password": "Manager@123",
                "first_login": False,
                "kwargs": {
                    "location_id": "LOC_HOSTEL_1",
                    "assigned_locations": ["LOC_HOSTEL_1", "LOC_ACADEMIC_1", "LOC_MESS_1", "LOC_SAC_1", "LOC_SPORTS_1"]
                },
            },
            {
                "id": "USR_MANAGER_2",
                "class": AppManager,
                "name": "App Manager 2",
                "email": os.environ.get("MANAGER_2_EMAIL", "appmanager2@campus.edu"),
                "password_env": "MANAGER_2_PASSWORD",
                "default_password": "Manager@123",
                "first_login": False,
                "kwargs": {
                    "location_id": "LOC_HOSTEL_2",
                    "assigned_locations": ["LOC_HOSTEL_2", "LOC_ACADEMIC_2", "LOC_MESS_2", "LOC_SAC_2", "LOC_SPORTS_2"]
                },
            },
            {
                "id": "USR_COORD_1",
                "class": Coordinator,
                "name": "Coordinator 1",
                "email": "coordinator1@campuspulse.edu",
                "password_env": None,
                "default_password": "Coord@123",
                "first_login": False,
                "kwargs": {},
            },
            {
                "id": "USR_COORD_2",
                "class": Coordinator,
                "name": "Coordinator 2",
                "email": "coordinator2@campuspulse.edu",
                "password_env": None,
                "default_password": "Coord@123",
                "first_login": False,
                "kwargs": {},
            },
            {
                "id": "USR_STUDENT",
                "class": Student,
                "name": "Student 1",
                "email": os.environ.get("STUDENT_EMAIL", "gowtham.e23@iiits.in"),
                "password_env": "STUDENT_PASSWORD",
                "default_password": "Student@123",
                "first_login": False,
                "kwargs": {"location_id": "LOC_HOSTEL_1"},
            },
            {
                "id": "USR_STUDENT_2",
                "class": Student,
                "name": "Student 2",
                "email": "student2@campus.edu",
                "password_env": None,
                "default_password": "Student@123",
                "first_login": False,
                "kwargs": {"location_id": "LOC_HOSTEL_2"},
            },
            {
                "id": "USR_WARDEN",
                "class": LocationInCharge,
                "name": "Warden 1",
                "email": os.environ.get("WARDEN_EMAIL", "naveen@campus.edu"),
                "password_env": "WARDEN_PASSWORD",
                "default_password": "Warden@123",
                "first_login": False,
                "kwargs": {
                    "location_id": "LOC_HOSTEL_1",
                    "assigned_locations": ["LOC_HOSTEL_1", "LOC_ACADEMIC_1", "LOC_MESS_1", "LOC_SAC_1", "LOC_SPORTS_1"]
                },
            },
            {
                "id": "USR_WARDEN_2",
                "class": LocationInCharge,
                "name": "Warden 2",
                "email": os.environ.get("WARDEN_2_EMAIL", "warden2@campus.edu"),
                "password_env": "WARDEN_2_PASSWORD",
                "default_password": "Warden@123",
                "first_login": False,
                "kwargs": {
                    "location_id": "LOC_HOSTEL_2",
                    "assigned_locations": ["LOC_HOSTEL_2", "LOC_ACADEMIC_2", "LOC_MESS_2", "LOC_SAC_2", "LOC_SPORTS_2"]
                },
            },
        ]

        if "users" not in data or data["users"] is None:
            data["users"] = []

        existing_users = data["users"]
        user_by_id = {u["user_id"]: u for u in existing_users if "user_id" in u}
        user_by_email = {
            u["email"].strip().lower(): u for u in existing_users if u.get("email")
        }

        is_production = os.environ.get("ENVIRONMENT", "").lower() == "production"
        # Local/demo convenience: explicitly opt in (e.g. in your local .env, or
        # set by tests/conftest.py) to keep the well-known Admin@123-style demo
        # passwords for a fresh non-production database. Without this flag, a
        # fresh non-production boot that wasn't given an explicit password env
        # var gets a random one instead of a predictable default -- so
        # forgetting ENVIRONMENT=production on a real deployment no longer
        # hands out documented, guessable admin credentials.
        allow_demo_passwords = os.environ.get("ALLOW_DEMO_SEED_PASSWORDS", "").lower() in ("1", "true", "yes")
        for spec in seed_users_spec:
            explicit_password = os.environ.get(spec["password_env"]) if spec.get("password_env") else None
            force_first_login = False

            if allow_demo_passwords:
                spec["password"] = explicit_password or spec["default_password"]
            elif is_production:
                spec["password"] = os.environ.get(f"SEED_{spec['id']}_PASSWORD")
                if not spec["password"]:
                    continue
            elif explicit_password:
                spec["password"] = explicit_password
            else:
                spec["password"] = generate_temp_password()
                force_first_login = True
                env_note = (
                    f"no {spec['password_env']} set and" if spec.get("password_env")
                    else "no explicit password configured and"
                )
                logger.warning(
                    f"{env_note} ALLOW_DEMO_SEED_PASSWORDS is not enabled -- generated a random "
                    f"first-login password for {spec['id']} ({spec['email']}): {spec['password']}"
                )

            email_lower = spec["email"].strip().lower()
            target_user = user_by_id.get(spec["id"]) or user_by_email.get(email_lower)

            if not target_user:
                user_dict = spec["class"](
                    spec["id"],
                    spec["name"],
                    spec["email"],
                    hash_password(spec["password"]),
                    first_login=spec["first_login"] or force_first_login,
                    status="Active",
                    **spec["kwargs"],
                ).to_dict()
                existing_users.append(user_dict)
                user_by_id[spec["id"]] = user_dict
                user_by_email[email_lower] = user_dict
                changed = True
            else:
                if target_user.get("user_id") == spec["id"] and target_user.get("email") != spec["email"]:
                    target_user["email"] = spec["email"]
                    changed = True
                if target_user.get("name") in ("App Manager", "Warden", "Coordinator", "Student", "Student User"):
                    target_user["name"] = spec["name"]
                    changed = True
                if spec["kwargs"].get("assigned_locations") and not target_user.get("assigned_locations"):
                    target_user["assigned_locations"] = spec["kwargs"]["assigned_locations"]
                    changed = True
                if spec["kwargs"].get("location_id") and not target_user.get("location_id"):
                    target_user["location_id"] = spec["kwargs"]["location_id"]
                    changed = True

        data["users"] = existing_users

        if changed:
            self.repository.save(data)

        # Sync all users to SQLite users table so foreign keys and lookups are consistently satisfied
        for u_dict in existing_users:
            try:
                self.save_user(self._user_from_dict(u_dict))
            except Exception:
                pass

        # Ensure seed profiles and assignments in SQLite
        with self._connect() as conn:
            conn.execute("UPDATE users SET email = ? WHERE user_id = 'USR_ADMIN'", (os.environ.get("ADMIN_EMAIL", "gowthamejjurothu@gmail.com"),))
            conn.execute("UPDATE users SET email = ? WHERE user_id = 'USR_MANAGER'", (os.environ.get("MANAGER_EMAIL", "ejjurothugowtham@gmail.com"),))
            conn.execute("UPDATE users SET email = ?, name = 'Student 1' WHERE user_id = 'USR_STUDENT'", (os.environ.get("STUDENT_EMAIL", "gowtham.e23@iiits.in"),))
            conn.execute("UPDATE users SET email = ? WHERE user_id = 'USR_WARDEN'", (os.environ.get("WARDEN_EMAIL", "naveen@campus.edu"),))

            # Sync locations table in SQLite
            for l in data.get("locations", []):
                conn.execute("""
                    INSERT INTO locations (location_id, name, location_type, in_charge_id, coordinator_id, app_manager_id, active, archived)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(location_id) DO UPDATE SET
                        name=excluded.name,
                        location_type=excluded.location_type,
                        in_charge_id=COALESCE(locations.in_charge_id, excluded.in_charge_id),
                        app_manager_id=COALESCE(locations.app_manager_id, excluded.app_manager_id),
                        active=excluded.active,
                        archived=excluded.archived
                """, (
                    l["location_id"],
                    l["name"],
                    l.get("location_type"),
                    l.get("in_charge_id"),
                    l.get("coordinator_id"),
                    l.get("app_manager_id"),
                    int(l.get("active", True)),
                    int(l.get("archived", False)),
                ))

            # Sync department_issues table with seed departments
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
            for dept in data.get("departments", []):
                dept_id = dept["department_id"]
                for issue in dept.get("complaint_types", []):
                    normalized_issue = issue.replace(" ", "_").replace("/", "_").replace("&", "_")
                    issue_id = f"ISS_{dept_id}_{normalized_issue}"
                    conn.execute("""
                        INSERT OR IGNORE INTO department_issues (issue_id, department_id, issue_name, description, active, created_at)
                        VALUES (?, ?, ?, ?, 1, ?)
                    """, (issue_id[:50], dept_id, issue, f"Predefined issue for {dept['name']}", "2026-08-13 00:00:00"))

            # Profiles
            conn.execute("""
                INSERT OR IGNORE INTO student_profiles (user_id, roll_number, department, program, year, section, hostel, block, room_number)
                VALUES ('USR_STUDENT', 'S2023001', 'CSE', 'B.Tech', '3rd', 'A', 'Hostel 1', 'Block 1', '101')
                """)
            conn.execute("""
                INSERT OR IGNORE INTO student_profiles (user_id, roll_number, department, program, year, section, hostel, block, room_number)
                VALUES ('USR_STUDENT_2', 'S2023002', 'ECE', 'B.Tech', '2nd', 'B', 'Hostel 2', 'Block 2', '202')
                """)
            conn.execute("UPDATE users SET location_id = 'LOC_HOSTEL_1' WHERE user_id = 'USR_STUDENT' AND (location_id IS NULL OR location_id = '')")
            conn.execute("UPDATE users SET location_id = 'LOC_HOSTEL_2' WHERE user_id = 'USR_STUDENT_2' AND (location_id IS NULL OR location_id = '')")

            # Staff profiles for the coordinators (clean setup)
            conn.execute("DELETE FROM users WHERE role = 'employee' OR user_id LIKE 'USR_EMP_%'")
            conn.execute("DELETE FROM staff_profiles WHERE user_id LIKE 'USR_EMP_%'")
            coordinator_profiles = [
                ('USR_COORD_1', 'EMP_COORD_1', 'Coordinator', None, '[]'),
                ('USR_COORD_2', 'EMP_COORD_2', 'Coordinator', None, '[]'),
            ]
            for uid, empid, desig, dept, locs in coordinator_profiles:
                conn.execute("""
                    INSERT INTO staff_profiles (user_id, employee_id, designation, department, assigned_locations)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        designation=excluded.designation,
                        department=excluded.department,
                        assigned_locations=excluded.assigned_locations
                """, (uid, empid, desig, dept, locs))

            conn.execute("""
                INSERT INTO staff_profiles (user_id, employee_id, designation, department, assigned_locations)
                VALUES ('USR_MANAGER', 'EMP002', 'Operations Manager 1', 'Administration', '["LOC_HOSTEL_1", "LOC_ACADEMIC_1", "LOC_MESS_1", "LOC_SAC_1", "LOC_SPORTS_1"]')
                ON CONFLICT(user_id) DO UPDATE SET
                    assigned_locations=excluded.assigned_locations
                """)
            conn.execute("""
                INSERT INTO staff_profiles (user_id, employee_id, designation, department, assigned_locations)
                VALUES ('USR_MANAGER_2', 'EMP004', 'Operations Manager 2', 'Administration', '["LOC_HOSTEL_2", "LOC_ACADEMIC_2", "LOC_MESS_2", "LOC_SAC_2", "LOC_SPORTS_2"]')
                ON CONFLICT(user_id) DO UPDATE SET
                    assigned_locations=excluded.assigned_locations
                """)
            conn.execute("""
                INSERT INTO staff_profiles (user_id, employee_id, designation, department, assigned_locations)
                VALUES ('USR_WARDEN', 'EMP003', 'Hostel Warden 1', 'Hostel Administration', '["LOC_HOSTEL_1", "LOC_ACADEMIC_1", "LOC_MESS_1", "LOC_SAC_1", "LOC_SPORTS_1"]')
                ON CONFLICT(user_id) DO UPDATE SET
                    assigned_locations=excluded.assigned_locations
                """)
            conn.execute("""
                INSERT INTO staff_profiles (user_id, employee_id, designation, department, assigned_locations)
                VALUES ('USR_WARDEN_2', 'EMP005', 'Hostel Warden 2', 'Hostel Administration', '["LOC_HOSTEL_2", "LOC_ACADEMIC_2", "LOC_MESS_2", "LOC_SAC_2", "LOC_SPORTS_2"]')
                ON CONFLICT(user_id) DO UPDATE SET
                    assigned_locations=excluded.assigned_locations
                """)
            conn.execute("""
                INSERT OR IGNORE INTO staff_profiles (user_id, employee_id, designation, department)
                VALUES ('USR_ADMIN', 'EMP000', 'Chief Administrator', 'IT')
                """)

            # Coordinator initial department-based assignments
            init_coord_assignments = [
                ("ASGN_COORD_1_ELEC", "USR_COORD_1", "DEPT_HOSTEL_ELECTRICAL", "LOC_HOSTEL_1"),
                ("ASGN_COORD_2_ELEC", "USR_COORD_2", "DEPT_HOSTEL_ELECTRICAL", "LOC_HOSTEL_1"),
                ("ASGN_COORD_1_PLUMB", "USR_COORD_1", "DEPT_HOSTEL_PLUMBING", "LOC_HOSTEL_2"),
                ("ASGN_COORD_2_PLUMB", "USR_COORD_2", "DEPT_HOSTEL_PLUMBING", "LOC_HOSTEL_2"),
            ]
            for asgn_id, cid, did, lid in init_coord_assignments:
                conn.execute("""
                    INSERT OR IGNORE INTO coordinator_assignments
                    (assignment_id, coordinator_id, department_id, location_id, assigned_at, assigned_by, status)
                    VALUES (?, ?, ?, ?, '2026-10-16 00:00:00', 'USR_ADMIN', 'Active')
                """, (asgn_id, cid, did, lid))
            conn.commit()

    def _user_from_dict(self, data):
        raw_status = data.get("status", User.STATUS_ACTIVE)
        raw_active = data.get("active")
        is_deleted = bool(data.get("is_deleted", False))
        if is_deleted or raw_status in (User.STATUS_INACTIVE, User.STATUS_SUSPENDED, User.STATUS_ARCHIVED):
            is_active = False
        elif raw_active is not None:
            is_active = bool(raw_active)
        else:
            is_active = (raw_status == User.STATUS_ACTIVE)

        common_kwargs = {
            "phone_number": data.get("phone_number"),
            "status": raw_status,
            "profile_photo": data.get("profile_photo"),
            "first_login": data.get("first_login", False),
            "active": is_active,
            "department_id": data.get("department_id"),
            "location_id": data.get("location_id"),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "last_login": data.get("last_login"),
            "last_logout": data.get("last_logout"),
            "created_by": data.get("created_by", "system"),
            "is_deleted": data.get("is_deleted", False),
            "deleted_at": data.get("deleted_at"),
            "deleted_by": data.get("deleted_by"),
            "deactivated_by_user_id": data.get("deactivated_by_user_id"),
            "deactivated_by_role": data.get("deactivated_by_role"),
            "deactivated_at": data.get("deactivated_at"),
            "roll_number": data.get("roll_number"),
            "student_department": data.get("student_department")
            or data.get("department"),
            "program": data.get("program"),
            "year": data.get("year"),
            "section": data.get("section"),
            "hostel": data.get("hostel"),
            "block": data.get("block"),
            "room_number": data.get("room_number"),
            "employee_id": data.get("employee_id"),
            "designation": data.get("designation"),
            "staff_department": data.get("staff_department") or data.get("department"),
            "assigned_locations": data.get("assigned_locations", []),
            "assigned_categories": data.get("assigned_categories", []),
            "photo_skip_streak": int(data.get("photo_skip_streak", 0) or 0),
            "force_next_warden_check": int(data.get("force_next_warden_check", 0) or 0),
            "language": data.get("language") or "en",
            "safety_blocked_until": data.get("safety_blocked_until"),
        }

        role_classes = {
            Student.ROLE: Student,
            Coordinator.ROLE: Coordinator,
            Administrator.ROLE: Administrator,
            AppManager.ROLE: AppManager,
            LocationInCharge.ROLE: LocationInCharge,
            "employee": Coordinator,
        }

        role_str = data.get("role")
        user_cls = role_classes.get(role_str, User)

        if user_cls in (
            Student,
            Coordinator,
            Administrator,
            AppManager,
            LocationInCharge,
        ):
            u = user_cls(
                data["user_id"],
                data.get("name") or data.get("full_name") or "",
                data["email"],
                data["password"],
                **common_kwargs,
            )
        else:
            u = User(
                data["user_id"],
                data.get("name") or data.get("full_name") or "",
                data["email"],
                data["password"],
                role_str,
                **common_kwargs,
            )
        return u

    _USER_COLUMNS = """
        u.*,
        sp.roll_number, sp.department as student_dept, sp.program, sp.year, sp.section, sp.hostel, sp.block, sp.room_number,
        st.employee_id, st.designation, st.department as staff_dept, st.assigned_locations, st.assigned_categories
    """

    def get_user(self, user_id):
        with self._connect() as conn:
            row = conn.execute(
                f"""
                SELECT {self._USER_COLUMNS}
                FROM users u
                LEFT JOIN student_profiles sp ON u.user_id = sp.user_id
                LEFT JOIN staff_profiles st ON u.user_id = st.user_id
                WHERE u.user_id = ? AND (u.is_deleted = 0 OR u.is_deleted IS NULL)
                """,
                (user_id,),
            ).fetchone()
            if not row:
                if user_id in ("USR_COORDINATOR", "USR_COORDINATOR_1"):
                    return self.get_user("USR_COORD_1")
                if user_id == "USR_COORDINATOR_2":
                    return self.get_user("USR_COORD_2")
                return None
            return self._user_from_joined_row(row)

    def _user_from_joined_row(self, row):
        data = dict(row)
        data["name"] = row["name"]
        data["student_department"] = row["student_dept"]
        data["staff_department"] = row["staff_dept"]
        data["department"] = (
            row["student_dept"] or row["staff_dept"] or row["department_id"]
        )
        if row["assigned_locations"]:
            try:
                data["assigned_locations"] = json.loads(row["assigned_locations"])
            except Exception:
                data["assigned_locations"] = []
        if row["assigned_categories"]:
            try:
                data["assigned_categories"] = json.loads(row["assigned_categories"])
            except Exception:
                data["assigned_categories"] = []

        return self._user_from_dict(data)

    def get_student_profile(self, user_id):
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM student_profiles WHERE user_id = ?", (user_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_user_by_email(self, email):
        clean_email = (email or "").strip().lower()
        if not clean_email:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT user_id FROM users WHERE LOWER(email) = ? AND (is_deleted = 0 OR is_deleted IS NULL)",
                (clean_email,),
            ).fetchone()
            if row:
                return self.get_user(row["user_id"])

        return None

    def get_user_by_roll_number(self, roll_number):
        if not roll_number:
            return None
        clean_roll = roll_number.strip().lower()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT user_id FROM student_profiles WHERE LOWER(roll_number) = ?",
                (clean_roll,),
            ).fetchone()
            if row:
                return self.get_user(row["user_id"])
        return None

    def get_user_by_employee_id(self, employee_id):
        if not employee_id:
            return None
        clean_emp = employee_id.strip().lower()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT user_id FROM staff_profiles WHERE LOWER(employee_id) = ?",
                (clean_emp,),
            ).fetchone()
            if row:
                return self.get_user(row["user_id"])
        return None

    def get_user_by_phone(self, phone):
        if not phone:
            return None
        clean_phone = phone.strip()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT user_id FROM users WHERE phone_number = ? AND (is_deleted = 0 OR is_deleted IS NULL)",
                (clean_phone,),
            ).fetchone()
            if row:
                return self.get_user(row["user_id"])
        return None

    def list_users(self, role=None, search=None, filters=None, include_deleted=False):
        query = f"""
            SELECT {self._USER_COLUMNS}
            FROM users u
            LEFT JOIN student_profiles sp ON u.user_id = sp.user_id
            LEFT JOIN staff_profiles st ON u.user_id = st.user_id
            WHERE 1=1
        """
        params = []
        if not include_deleted:
            query += " AND (u.is_deleted = 0 OR u.is_deleted IS NULL)"
        if role:
            query += " AND u.role = ?"
            params.append(role)
        else:
            # The platform Super Admin is not part of any institution's user directory.
            query += " AND u.role != 'super_admin'"

        filters = filters or {}
        if filters.get("status"):
            # Filter against the `active` flag, not the `status` text column —
            # some existing disable paths only ever set `active`, leaving
            # `status` stale/inconsistent, so matching on `status` text misses
            # real disabled users.
            status_val = str(filters["status"]).strip().lower()
            if status_val == "active":
                query += " AND u.active = 1"
            elif status_val in ("disabled", "inactive"):
                query += " AND u.active = 0"
        if filters.get("department"):
            query += (
                " AND (u.department_id = ? OR sp.department = ? OR st.department = ?)"
            )
            params.extend(
                [filters["department"], filters["department"], filters["department"]]
            )
        if filters.get("location") or filters.get("location_id"):
            loc_val = filters.get("location") or filters.get("location_id")
            query += " AND (u.location_id = ? OR sp.hostel = ? OR u.location_id IN (SELECT location_id FROM locations WHERE LOWER(name) = LOWER(?)))"
            params.extend([loc_val, loc_val, loc_val])
        if filters.get("program"):
            query += " AND sp.program = ?"
            params.append(filters["program"])
        if filters.get("hostel"):
            query += " AND sp.hostel = ?"
            params.append(filters["hostel"])
        if filters.get("block"):
            query += " AND sp.block = ?"
            params.append(filters["block"])
        if filters.get("year"):
            query += " AND sp.year = ?"
            params.append(filters["year"])
        if filters.get("section"):
            query += " AND sp.section = ?"
            params.append(filters["section"])
        if filters.get("designation"):
            query += " AND st.designation = ?"
            params.append(filters["designation"])

        if search and search.strip():
            term = f"%{search.strip().lower()}%"
            query += """ AND (
                LOWER(u.name) LIKE ? OR
                LOWER(u.email) LIKE ? OR
                LOWER(u.phone_number) LIKE ? OR
                LOWER(sp.roll_number) LIKE ? OR
                LOWER(st.employee_id) LIKE ? OR
                LOWER(sp.hostel) LIKE ? OR
                LOWER(sp.block) LIKE ? OR
                LOWER(u.department_id) LIKE ?
            )"""
            params.extend([term] * 8)

        query += " ORDER BY u.created_at DESC"

        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._user_from_joined_row(r) for r in rows if r["user_id"]]

    @staticmethod
    def normalize_phone(phone):
        if not phone:
            return None
        cleaned = re.sub(r"[\s\-\(\)\.]", "", str(phone).strip())
        if cleaned.startswith("+91") and len(cleaned) == 13:
            cleaned = cleaned[3:]
        elif cleaned.startswith("91") and len(cleaned) == 12:
            cleaned = cleaned[2:]
        elif cleaned.startswith("+"):
            cleaned = cleaned[1:]
        return cleaned if cleaned else None

    def validate_user_fields(
        self,
        email,
        phone,
        name,
        roll_number=None,
        employee_id=None,
        role=None,
        current_user_id=None,
        is_admin=False,
    ):
        # 1. Full Name Validation
        if not name or not name.strip():
            raise ValueError("Full Name is required.")
        if len(name.strip()) > 100:
            raise ValueError("Full Name cannot exceed 100 characters.")

        # 2. Email Validation
        if not email or not str(email).strip():
            if (role or "").lower() == "employee":
                clean_email = None
            else:
                raise ValueError("Email is required.")
        else:
            clean_email = str(email).strip().lower()
            if not re.match(self.EMAIL_REGEX, clean_email):
                raise ValueError("Invalid email format.")
            existing_email_user = self.get_user_by_email(clean_email)
            if existing_email_user and existing_email_user.user_id != current_user_id:
                raise ValueError("A user with this email address already exists.")

        # 3. Phone Validation
        if phone:
            clean_phone = self.normalize_phone(phone)
            if not clean_phone or not clean_phone.isdigit() or not (10 <= len(clean_phone) <= 15):
                raise ValueError(
                    "Phone number must be numeric and between 10 to 15 digits."
                )
            existing_phone_user = self.get_user_by_phone(clean_phone)
            if existing_phone_user and existing_phone_user.user_id != current_user_id:
                raise ValueError("A user with this phone number already exists.")
        elif (role or "").lower() in ("employee", "coordinator", "location_in_charge") and not email:
            raise ValueError("Phone number is required when email is not provided.")

        # 4. Roll Number Validation (Student)
        if role == Student.ROLE or roll_number:
            if not roll_number or not roll_number.strip():
                raise ValueError("Roll Number is required for students.")
            clean_roll = roll_number.strip()
            existing_roll_user = self.get_user_by_roll_number(clean_roll)
            if existing_roll_user and existing_roll_user.user_id != current_user_id:
                raise ValueError(
                    "Roll Number must be unique. A student with this Roll Number already exists."
                )
            if current_user_id and not is_admin:
                existing_user = self.get_user(current_user_id)
                if (
                    existing_user
                    and existing_user.roll_number
                    and existing_user.roll_number != clean_roll
                ):
                    raise ValueError(
                        "Roll Number is immutable and can only be modified by an Admin."
                    )

        # 5. Employee ID Validation (Staff)
        if (
            role
            in (
                Coordinator.ROLE,
                LocationInCharge.ROLE,
                AppManager.ROLE,
                Administrator.ROLE,
            )
            or employee_id
        ):
            if not employee_id or not employee_id.strip():
                raise ValueError("Employee ID is required for staff members.")
            clean_emp = employee_id.strip()
            existing_emp_user = self.get_user_by_employee_id(clean_emp)
            if existing_emp_user and existing_emp_user.user_id != current_user_id:
                raise ValueError(
                    "Employee ID must be unique. A staff member with this Employee ID already exists."
                )
            if current_user_id and not is_admin:
                existing_user = self.get_user(current_user_id)
                if (
                    existing_user
                    and existing_user.employee_id
                    and existing_user.employee_id != clean_emp
                ):
                    raise ValueError(
                        "Employee ID is immutable and can only be modified by an Admin."
                    )

    def save_user(self, user):
        user_dict = user.to_dict()
        user_id = user.user_id

        conn = self._connect()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO users (
                        user_id, name, email, password, role, phone_number, status, profile_photo,
                        first_login, active, department_id, location_id, created_at, updated_at,
                        last_login, last_logout, created_by, is_deleted, deleted_at, deleted_by,
                        deactivated_by_user_id, deactivated_by_role, deactivated_at,
                        photo_skip_streak, force_next_warden_check, language, safety_blocked_until
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        name=excluded.name,
                        email=excluded.email,
                        password=excluded.password,
                        role=excluded.role,
                        phone_number=excluded.phone_number,
                        status=excluded.status,
                        profile_photo=excluded.profile_photo,
                        first_login=excluded.first_login,
                        active=excluded.active,
                        department_id=excluded.department_id,
                        location_id=excluded.location_id,
                        updated_at=excluded.updated_at,
                        last_login=excluded.last_login,
                        last_logout=excluded.last_logout,
                        is_deleted=excluded.is_deleted,
                        deleted_at=excluded.deleted_at,
                        deleted_by=excluded.deleted_by,
                        deactivated_by_user_id=excluded.deactivated_by_user_id,
                        deactivated_by_role=excluded.deactivated_by_role,
                        deactivated_at=excluded.deactivated_at,
                        photo_skip_streak=excluded.photo_skip_streak,
                        force_next_warden_check=excluded.force_next_warden_check,
                        language=excluded.language,
                        safety_blocked_until=excluded.safety_blocked_until
                    """,
                    (
                        user_id,
                        user_dict["name"],
                        user_dict["email"],
                        user_dict["password"],
                        user_dict["role"],
                        user_dict.get("phone_number"),
                        user_dict.get("status", "Active"),
                        user_dict.get("profile_photo"),
                        int(user_dict.get("first_login", True)),
                        int(
                            user_dict.get("active", True)
                            and user_dict.get("status") == "Active"
                        ),
                        user_dict.get("department_id"),
                        user_dict.get("location_id"),
                        user_dict.get("created_at") or now_string(),
                        user_dict.get("updated_at") or now_string(),
                        user_dict.get("last_login"),
                        user_dict.get("last_logout"),
                        user_dict.get("created_by", "system"),
                        int(user_dict.get("is_deleted", False)),
                        user_dict.get("deleted_at"),
                        user_dict.get("deleted_by"),
                        user_dict.get("deactivated_by_user_id"),
                        user_dict.get("deactivated_by_role"),
                        user_dict.get("deactivated_at"),
                        int(user_dict.get("photo_skip_streak", 0) or 0),
                        int(user_dict.get("force_next_warden_check", 0) or 0),
                        user_dict.get("language") or "en",
                        user_dict.get("safety_blocked_until"),
                    ),
                )

                if user.role == Student.ROLE or user.roll_number:
                    conn.execute(
                        """
                        INSERT INTO student_profiles (user_id, roll_number, department, program, year, section, hostel, block, room_number)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET
                            roll_number=excluded.roll_number,
                            department=excluded.department,
                            program=excluded.program,
                            year=excluded.year,
                            section=excluded.section,
                            hostel=excluded.hostel,
                            block=excluded.block,
                            room_number=excluded.room_number
                        """,
                        (
                            user_id,
                            user_dict.get("roll_number") or f"ROLL_{user_id}",
                            user_dict.get("department") or user_dict.get("department_id"),
                            user_dict.get("program"),
                            user_dict.get("year"),
                            user_dict.get("section"),
                            user_dict.get("hostel"),
                            user_dict.get("block"),
                            user_dict.get("room_number"),
                        ),
                    )

                if (
                    user.role
                    in (
                        Coordinator.ROLE,
                        LocationInCharge.ROLE,
                        AppManager.ROLE,
                        Administrator.ROLE,
                    )
                    or user.employee_id
                ):
                    conn.execute(
                        """
                        INSERT INTO staff_profiles (user_id, employee_id, designation, department, assigned_locations, assigned_categories)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(user_id) DO UPDATE SET
                            employee_id=excluded.employee_id,
                            designation=excluded.designation,
                            department=excluded.department,
                            assigned_locations=excluded.assigned_locations,
                            assigned_categories=excluded.assigned_categories
                        """,
                        (
                            user_id,
                            user_dict.get("employee_id") or f"EMP_{user_id}",
                            user_dict.get("designation"),
                            user_dict.get("staff_department")
                            or user_dict.get("department_id"),
                            json.dumps(user_dict.get("assigned_locations", [])),
                            json.dumps(user_dict.get("assigned_categories", [])),
                        ),
                    )
                conn.commit()
        finally:
            conn.close()

    def create_user(
        self,
        name,
        email,
        password,
        role,
        department_id=None,
        location_id=None,
        creator=None,
        # Student details
        roll_number=None,
        program=None,
        year=None,
        section=None,
        hostel=None,
        block=None,
        room_number=None,
        # Staff details
        employee_id=None,
        designation=None,
        phone_number=None,
    ):
        # 1. Creator Permission Hierarchy Rules
        creator_role = (creator.role if creator else "administrator").lower()
        target_role = (role or "").lower()

        if creator_role not in ("administrator", "app_manager"):
            raise PermissionError(
                "Your role is not authorized to create user accounts."
            )

        # The system must always have exactly one active Administrator.
        # Since one already exists, creating another is always rejected here
        # regardless of creator role.
        if target_role == "administrator":
            raise PermissionError(
                "Cannot create another Admin account. The system "
                "must always have exactly one active Admin."
            )

        # App Managers cannot create other App Manager accounts.
        if creator_role == "app_manager" and target_role == "app_manager":
            raise PermissionError(
                "App Managers cannot create other App Manager accounts."
            )

        if target_role not in ("app_manager", "coordinator", "location_in_charge", "student", "employee"):
            raise PermissionError(
                f"Cannot create a user with role '{role}'."
            )

        # Department & Location Active Checks
        if department_id:
            with self._connect() as conn:
                dept_row = conn.execute("SELECT active, status FROM departments WHERE department_id = ? OR LOWER(name) = ?", (department_id, department_id.lower())).fetchone()
                if dept_row and (dict(dept_row).get("active") == 0 or dict(dept_row).get("status") == "Inactive"):
                    raise ValueError("Selected department is inactive.")
        if location_id:
            with self._connect() as conn:
                loc_row = conn.execute("SELECT active FROM locations WHERE location_id = ? OR LOWER(name) = ?", (location_id, location_id.lower())).fetchone()
                if loc_row and dict(loc_row).get("active") == 0:
                    raise ValueError("Selected location is inactive.")

        # Role-specific assignments checks (Location/department assignment is performed separately after creation)
        pass

        # For workers without email, auto-generate placeholder email and worker temp password
        is_worker_without_email = (
            (role or "").lower() == "employee"
            and (not email or not str(email).strip() or str(email).strip().endswith("@worker.campuspulse"))
        )
        if is_worker_without_email:
            if not phone_number:
                raise ValueError("Phone number is required for employees without email.")
            clean_p = self.normalize_phone(phone_number)
            email = f"{clean_p}@worker.campuspulse"
            if not password or not str(password).strip():
                import secrets
                temp_password = f"CP-{secrets.randbelow(9000) + 1000}"
            else:
                temp_password = str(password).strip()
        else:
            # Temporary password generation & complexity validation
            if password and str(password).strip():
                temp_password = str(password).strip()
                if not validate_password_complexity(temp_password):
                    raise ValueError("Password does not meet complexity requirements.")
            else:
                temp_password = generate_temp_password()

        # Auto-generate employee_id or roll_number if not provided for staff/student roles
        if role in (Coordinator.ROLE, LocationInCharge.ROLE, AppManager.ROLE, Administrator.ROLE) and not employee_id:
            import secrets, string
            for _ in range(50):
                cand = f"EMP{''.join(secrets.choice(string.digits) for _ in range(6))}"
                if not self.get_user_by_employee_id(cand):
                    employee_id = cand
                    break
            if not employee_id:
                employee_id = f"EMP{secrets.token_hex(4).upper()}"
        elif role == Student.ROLE and not roll_number:
            import secrets, string
            roll_number = f"S{''.join(secrets.choice(string.digits) for _ in range(7))}"

        self.validate_user_fields(
            email=email,
            phone=phone_number,
            name=name,
            roll_number=roll_number,
            employee_id=employee_id,
            role=role,
            is_admin=(creator_role == "administrator"),
        )

        user_id = generate_id("USR")
        hashed_pwd = hash_password(temp_password)

        role_classes = {
            Student.ROLE: Student,
            Coordinator.ROLE: Coordinator,
            Administrator.ROLE: Administrator,
            AppManager.ROLE: AppManager,
            LocationInCharge.ROLE: LocationInCharge,
            "employee": Coordinator,
        }
        user_cls = role_classes.get(role, User)

        clean_phone_val = self.normalize_phone(phone_number) if phone_number else None
        user = user_cls(
            user_id=user_id,
            name=name.strip(),
            email=email.strip().lower(),
            password=hashed_pwd,
            role=role,
            phone_number=clean_phone_val,
            status=User.STATUS_ACTIVE,
            first_login=True,
            active=True,
            department_id=department_id,
            location_id=location_id,
            created_at=now_string(),
            created_by=creator.user_id if creator else "system",
            roll_number=roll_number.strip() if roll_number else None,
            student_department=department_id,
            program=program,
            year=year,
            section=section,
            hostel=hostel,
            block=block,
            room_number=room_number,
            employee_id=employee_id.strip() if employee_id else None,
            designation=designation,
            staff_department=department_id,
        )

        user.temporary_password = temp_password
        self.save_user(user)
        self.log_activity(
            user_id,
            "User Created",
            creator.user_id if creator else "system",
            f"Role: {role}",
        )
        return user

    def get_user_by_identity(self, identity):
        if not identity:
            return None
        clean_id = str(identity).strip()
        # 0. Phone Number
        clean_phone = self.normalize_phone(clean_id)
        if clean_phone and clean_phone.isdigit() and len(clean_phone) >= 10:
            user = self.get_user_by_phone(clean_phone)
            if user:
                return user
        # 1. Roll Number (Student)
        user = self.get_user_by_roll_number(clean_id)
        if user:
            return user
        # 2. Employee ID (Staff/Admin)
        user = self.get_user_by_employee_id(clean_id)
        if user:
            return user
        # 3. Email
        user = self.get_user_by_email(clean_id)
        if user:
            return user
        # 4. User ID
        user = self.get_user(clean_id)
        if user:
            return user
        # 5. Legacy test runner aliases to canonical test users
        legacy_test_aliases = {
            "admin@example.com": "USR_ADMIN",
            "student@example.com": "USR_STUDENT",
            "warden@example.com": "USR_WARDEN",
            "manager@example.com": "USR_MANAGER",
            "coordinator@example.com": "USR_COORD_1",
        }
        alias_target = legacy_test_aliases.get(clean_id.lower())
        if alias_target:
            return self.get_user(alias_target)
        return None

    def _resolve_user_identity(self, identity):
        return self.get_user_by_identity(identity)

    # Per-account brute-force protection. Tracked by normalized identity (not
    # user_id) so a nonexistent account behaves identically to a real one —
    # an attacker can't tell the two apart by whether a lockout appears.
    _LOCKOUT_THRESHOLD = 5
    _LOCKOUT_BASE_SECONDS = 60  # first lock: 1 minute
    _LOCKOUT_MAX_SECONDS = 900  # capped at 15 minutes, never indefinite

    def _login_attempts_conn(self):
        conn = self._connect()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS login_attempts (
                identity TEXT NOT NULL,
                ip TEXT NOT NULL DEFAULT 'unknown',
                failed_count INTEGER NOT NULL DEFAULT 0,
                locked_until REAL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (identity, ip)
            )
            """
        )
        # Migrate any pre-existing table from the old (identity-only PK, no
        # `ip` column) schema. Lockout state is short-lived/non-critical, so
        # a clean rebuild (rather than a data-preserving ALTER) is safe here.
        cols = {row[1] for row in conn.execute("PRAGMA table_info(login_attempts)").fetchall()}
        if "ip" not in cols:
            with conn:
                conn.execute("ALTER TABLE login_attempts RENAME TO login_attempts_old")
                conn.execute(
                    """
                    CREATE TABLE login_attempts (
                        identity TEXT NOT NULL,
                        ip TEXT NOT NULL DEFAULT 'unknown',
                        failed_count INTEGER NOT NULL DEFAULT 0,
                        locked_until REAL,
                        updated_at TEXT NOT NULL,
                        PRIMARY KEY (identity, ip)
                    )
                    """
                )
                conn.execute("DROP TABLE login_attempts_old")
        return conn

    @staticmethod
    def _norm_ip(ip):
        # Keyed per (identity, ip) so an attacker who doesn't control the
        # victim's IP can only lock out login attempts *from their own IP*,
        # never the victim's real account/IP -- it can no longer be used to
        # remotely deny a legitimate user access to their own account.
        return (ip or "unknown").strip() or "unknown"

    def _check_login_lockout(self, identity, ip=None):
        import time
        ip = self._norm_ip(ip)
        with self._login_attempts_conn() as conn:
            row = conn.execute(
                "SELECT locked_until FROM login_attempts WHERE identity = ? AND ip = ?",
                (identity, ip),
            ).fetchone()
            if row and row["locked_until"] and time.time() < row["locked_until"]:
                wait_seconds = int(row["locked_until"] - time.time())
                raise PermissionError(
                    f"Too many failed login attempts. Try again in {wait_seconds} seconds."
                )

    def _register_login_failure(self, identity, ip=None):
        import time
        ip = self._norm_ip(ip)
        now_ts = time.time()
        with self._login_attempts_conn() as conn:
            row = conn.execute(
                "SELECT failed_count FROM login_attempts WHERE identity = ? AND ip = ?",
                (identity, ip),
            ).fetchone()
            failed_count = (row["failed_count"] if row else 0) + 1
            locked_until = None
            if failed_count >= self._LOCKOUT_THRESHOLD:
                # Progressive but capped: each additional block of failures past
                # the threshold doubles the lockout, up to the 15-minute cap, so
                # it always expires and can never lock a legitimate user out
                # indefinitely.
                breaches = (failed_count - self._LOCKOUT_THRESHOLD) // self._LOCKOUT_THRESHOLD
                duration = min(self._LOCKOUT_BASE_SECONDS * (2 ** breaches), self._LOCKOUT_MAX_SECONDS)
                locked_until = now_ts + duration
            conn.execute(
                """
                INSERT INTO login_attempts (identity, ip, failed_count, locked_until, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(identity, ip) DO UPDATE SET
                    failed_count = excluded.failed_count,
                    locked_until = excluded.locked_until,
                    updated_at = excluded.updated_at
                """,
                (identity, ip, failed_count, locked_until, now_string()),
            )

    def _clear_login_failures(self, identity, ip=None):
        with self._login_attempts_conn() as conn:
            if ip is None:
                # Successful login/password change clears every IP's failure
                # count for this identity -- clearing is not attacker-triggerable
                # on its own, so this stays safe while letting a legitimate user
                # who just proved their password recover from any stray lockouts.
                conn.execute("DELETE FROM login_attempts WHERE identity = ?", (identity,))
            else:
                conn.execute(
                    "DELETE FROM login_attempts WHERE identity = ? AND ip = ?",
                    (identity, self._norm_ip(ip)),
                )

    def authenticate(self, identity_or_email, password, ip=None):
        if not identity_or_email or not str(identity_or_email).strip():
            raise ValueError("Username is required.")
        if not password or not str(password).strip():
            raise ValueError("Password is required.")

        identity = str(identity_or_email).strip().lower()
        self._check_login_lockout(identity, ip=ip)

        user = self.get_user_by_identity(identity_or_email)
        if not user or user.is_deleted:
            verify_password(password, _DUMMY_PASSWORD_HASH)
            self._register_login_failure(identity, ip=ip)
            raise ValueError("Invalid credentials.")

        if not user.check_password(password):
            self._register_login_failure(identity, ip=ip)
            raise ValueError("Invalid credentials.")

        if user.status in (User.STATUS_INACTIVE, User.STATUS_SUSPENDED, User.STATUS_ARCHIVED) or not user.active:
            raise PermissionError("Your account has been deactivated.")

        self._clear_login_failures(identity)

        if not is_password_hash(user.password) or needs_rehash(user.password):
            user.password = hash_password(password)

        user.last_login = now_string()
        self.save_user(user)
        self.log_activity(user.user_id, "User Login", user.user_id, "Successful login")
        return user

    def logout_user(self, user_id):
        user = self.get_user(user_id)
        if user:
            user.last_logout = now_string()
            self.save_user(user)
            self.log_activity(user_id, "User Logout", user_id, "Logged out")

    def change_password(self, user_id, new_password, old_password=None):
        user = self.get_user(user_id) or self.get_user_by_email(user_id) or self.get_user_by_identity(user_id)
        if not user:
            raise ValueError("User not found.")
        if old_password and not user.check_password(old_password):
            raise ValueError("Old password is incorrect.")
        if old_password and old_password == new_password:
            raise ValueError("New password cannot be equal to old password.")
        if not validate_password_complexity(new_password):
            raise ValueError(
                "Password must contain at least 8 characters, an uppercase letter, a lowercase letter, a number, and a special character."
            )
        user.change_password(new_password)
        user.first_login = False
        self.save_user(user)

        # Verify database persistence immediately in a fresh database query
        persisted = self.get_user(user.user_id)
        if not persisted or not persisted.check_password(new_password):
            raise RuntimeError("Database update failed: password change could not be verified in database.")

        # Clear login lockout/failures for this account
        clean_email = user.email.strip().lower()
        self._clear_login_failures(clean_email)
        try:
            from middleware.rate_limiter import record_login_attempt
            record_login_attempt("127.0.0.1", clean_email, success=True, db_path=self.db_path)
        except Exception:
            pass

        self.log_activity(user.user_id, "Password Change", user.user_id, "User changed password")
        self.notification_service.notify(
            user.user_id, "Your password was updated successfully."
        )
        return persisted

    def reset_password(self, email, new_password):
        user = self.get_user_by_email(email)
        if not user:
            raise ValueError("Email verification failed.")
        if not validate_password_complexity(new_password):
            raise ValueError(
                "Password must contain at least 8 characters, an uppercase letter, a lowercase letter, a number, and a special character."
            )
        user.password = hash_password(new_password)
        user.first_login = False
        user.updated_at = now_string()
        self.save_user(user)

        # Verify database persistence immediately in a fresh database query
        persisted = self.get_user(user.user_id)
        if not persisted or not persisted.check_password(new_password):
            raise RuntimeError("Database update failed: password reset could not be verified in database.")

        # A successful, verified reset is proof of ownership: clear any
        # brute-force lockout so the legitimate owner can log in right away.
        clean_email = user.email.strip().lower()
        self._clear_login_failures(clean_email)
        try:
            from middleware.rate_limiter import record_login_attempt
            record_login_attempt("127.0.0.1", clean_email, success=True, db_path=self.db_path)
        except Exception:
            pass
        self.log_activity(
            user.user_id, "Password Reset", "system", "OTP Reset completed"
        )
        self.notification_service.notify(
            user.user_id, f"Your password reset completed successfully."
        )
        return persisted

    def update_user_status(self, user_id, new_status, performer, remarks=None):
        user = self.get_user(user_id)
        if not user:
            raise ValueError("User not found.")
        p_role = (performer.role or "").lower()
        if p_role == "app_manager" and user.role in ("administrator", "app_manager"):
            raise PermissionError("App Managers are not authorized to manage Admin or App Manager accounts.")

        valid_statuses = (
            User.STATUS_ACTIVE,
            User.STATUS_INACTIVE,
            User.STATUS_SUSPENDED,
            User.STATUS_ARCHIVED,
            User.STATUS_GRADUATED,
            User.STATUS_LEFT_COLLEGE,
            User.STATUS_TRANSFERRED,
        )
        if new_status not in valid_statuses:
            raise ValueError(f"Invalid status. Allowed: {', '.join(valid_statuses)}")

        # Reactivation Hierarchy Enforcement:
        # App Manager cannot reactivate an account originally deactivated by an Administrator
        if new_status == User.STATUS_ACTIVE:
            prev_deactivator_role = (getattr(user, "deactivated_by_role", "") or "").lower()
            if prev_deactivator_role in ("administrator", "admin") and p_role == "app_manager":
                raise PermissionError("This account was deactivated by an Admin. Only an Admin can reactivate it.")

        old_status = user.status
        user.status = new_status
        user.active = new_status == User.STATUS_ACTIVE
        user.updated_at = now_string()

        if not user.active:
            user.deactivated_by_user_id = performer.user_id
            user.deactivated_by_role = p_role
            user.deactivated_at = now_string()

            # Invalidate all active sessions for deactivated user
            try:
                from api.security import invalidate_user_sessions
                invalidate_user_sessions(user_id)
            except Exception:
                pass

            with self._connect() as conn:
                conn.execute("UPDATE coordinator_assignments SET status = 'Inactive' WHERE coordinator_id = ?", (user_id,))
                conn.commit()
            locs = [l for l in self.list_locations() if l.in_charge_id == user_id or getattr(l, "app_manager_id", None) == user_id]
            for loc in locs:
                if loc.in_charge_id == user_id:
                    loc.in_charge_id = None
                if getattr(loc, "app_manager_id", None) == user_id:
                    loc.app_manager_id = None
                self.save_location(loc)
        else:
            # Clear deactivation fields on reactivation
            user.deactivated_by_user_id = None
            user.deactivated_by_role = None
            user.deactivated_at = None

        self.save_user(user)

        self.log_activity(
            user_id,
            "Status Change",
            performer.user_id,
            f"Changed from {old_status} to {new_status}",
        )
        return user

    def update_user_profile(self, user_id, updates_dict, performer):
        user = self.get_user(user_id)
        if not user:
            raise ValueError("User not found.")

        p_role = (performer.role or "").lower()
        is_self = performer.user_id == user_id
        is_admin = p_role == "administrator"

        if not is_self and p_role == "app_manager" and user.role in ("administrator", "app_manager"):
            raise PermissionError("App Managers are not authorized to manage Admin or App Manager accounts.")

        if not is_self and not is_admin and p_role != "app_manager":
            raise PermissionError("You are not authorized to edit this profile.")

        # Enforcement of editable fields by role (password explicitly excluded for security)
        allowed_fields = set()
        if is_admin:
            allowed_fields = {
                "name",
                "phone_number",
                "profile_photo",
                "email",
                "role",
                "roll_number",
                "student_department",
                "program",
                "year",
                "section",
                "hostel",
                "block",
                "room_number",
                "employee_id",
                "designation",
                "staff_department",
                "assigned_locations",
                "assigned_categories",
                "department_id",
                "location_id",
            }
        elif (user.role or "").lower() == "student" and is_self:
            allowed_fields = {"phone_number", "profile_photo"}
        elif is_self:  # Staff / Coordinator / Warden / Manager editing own profile
            allowed_fields = {"phone_number", "profile_photo"}
        else:  # App Manager editing other staff
            allowed_fields = {
                "name",
                "phone_number",
                "profile_photo",
                "department_id",
                "location_id",
                "designation",
            }

        # Status changes go through update_user_status (which has its own guards).
        req_role = updates_dict.get("role")
        if "role" in allowed_fields and req_role is not None and req_role != user.role:
            if user.role in ("administrator", "super_admin") or req_role not in (
                "app_manager", "coordinator", "location_in_charge", "student", "employee"
            ):
                raise ValueError("Invalid role change.")
        new_loc_id = updates_dict.get("location_id")
        if "location_id" in allowed_fields and new_loc_id and not self.get_location(new_loc_id):
            raise ValueError("Location not found.")

        # Validate inputs if changing restricted fields
        new_name = updates_dict.get("name", user.name)
        new_email = updates_dict.get("email", user.email)
        new_phone = updates_dict.get("phone_number", user.phone_number)
        new_roll = updates_dict.get("roll_number", user.roll_number)
        new_emp = updates_dict.get("employee_id", user.employee_id)

        self.validate_user_fields(
            email=new_email,
            phone=new_phone,
            name=new_name,
            roll_number=new_roll,
            employee_id=new_emp,
            role=user.role,
            current_user_id=user_id,
            is_admin=is_admin,
        )

        old_role = user.role
        old_loc = getattr(user, "location_id", None)
        if not old_loc:
            c_asgns = self.list_coordinator_assignments(coordinator_id=user_id)
            if c_asgns:
                old_loc = c_asgns[0]["location_id"]
            else:
                w_locs = [l.location_id for l in self.list_locations() if l.in_charge_id == user_id]
                if w_locs:
                    old_loc = w_locs[0]

        for key, val in updates_dict.items():
            if key in allowed_fields:
                setattr(user, key, val)

        new_role = user.role
        new_loc = user.location_id

        # Role change synchronization
        if old_role != new_role:
            if (old_role or "").lower() == "coordinator" and (new_role or "").lower() != "coordinator":
                with self._connect() as conn:
                    conn.execute("UPDATE coordinator_assignments SET status = 'Inactive' WHERE coordinator_id = ?", (user_id,))
                    conn.commit()
            if (old_role or "").lower() == "location_in_charge" and (new_role or "").lower() != "location_in_charge":
                locs = [l for l in self.list_locations() if l.in_charge_id == user_id]
                for loc in locs:
                    loc.in_charge_id = None
                    self.save_location(loc)
            if (old_role or "").lower() == "app_manager" and (new_role or "").lower() != "app_manager":
                locs = [l for l in self.list_locations() if getattr(l, "app_manager_id", None) == user_id]
                for loc in locs:
                    loc.app_manager_id = None
                    self.save_location(loc)

        # Location change synchronization for Coordinators / Wardens
        if old_loc != new_loc and new_loc:
            if (new_role or "").lower() == "coordinator":
                # Deactivate previous location assignments for this coordinator
                with self._connect() as conn:
                    conn.execute("UPDATE coordinator_assignments SET status = 'Inactive' WHERE coordinator_id = ?", (user_id,))
                    conn.commit()
                # Find matching department in new location if possible
                if user.department_id:
                    old_dept = self.get_department(user.department_id)
                    if old_dept:
                        new_depts = [
                            d for d in self.list_departments()
                            if (getattr(d, "location_id", None) == new_loc or getattr(d, "location_name", "").lower() == new_loc.lower())
                            and d.name.lower() == old_dept.name.lower()
                        ]
                        if new_depts:
                            user.department_id = new_depts[0].department_id
                            self.assign_coordinator(user_id, new_loc, user.department_id, assigned_by=performer.user_id)
                        else:
                            user.department_id = None
            elif (new_role or "").lower() == "location_in_charge":
                # Unassign from old location
                if old_loc:
                    old_loc_obj = self.get_location(old_loc)
                    if old_loc_obj and old_loc_obj.in_charge_id == user_id:
                        old_loc_obj.in_charge_id = None
                        self.save_location(old_loc_obj)
                # Assign to new location
                new_loc_obj = self.get_location(new_loc)
                if new_loc_obj:
                    new_loc_obj.in_charge_id = user_id
                    self.save_location(new_loc_obj)

        user.updated_at = now_string()
        self.save_user(user)
        self.log_activity(
            user_id, "Profile Update", performer.user_id, "Profile fields updated"
        )
        return user

    def check_user_dependencies(self, user_id):
        """Counts every existing reference to this user across the schema, so
        a caller can decide whether a physical delete would orphan historical
        records. Never used to perform the delete itself — reporting only."""
        checks = [
            ("complaints_created", "complaints", "created_by"),
            ("complaints_assigned", "complaints", "assigned_to"),
            ("notifications_received", "notifications", "receiver_id"),
            ("notifications_sent", "notifications", "sender_id"),
            ("audit_logs_performed", "audit_logs", "performed_by"),
            ("audit_logs_target", "audit_logs", "target_user"),
            ("coordinator_assignments", "coordinator_assignments", "coordinator_id"),
            ("location_in_charge_of", "locations", "in_charge_id"),
            ("location_coordinator_of", "locations", "coordinator_id"),
            ("department_coordinator_of", "departments", "coordinator_id"),
            ("comments", "comments", "user_id"),
            ("attachments_uploaded", "attachments", "uploaded_by"),
            ("login_history", "login_history", "user_id"),
            ("user_activities", "user_activities", "user_id"),
            ("feedback_submitted", "feedback", "submitted_by"),
            ("announcements_created", "announcements", "created_by"),
            ("lost_found_reported", "lost_found_items", "reported_by"),
        ]
        results = {}
        with self._connect() as conn:
            for label, table, column in checks:
                try:
                    row = conn.execute(
                        f"SELECT COUNT(*) FROM {table} WHERE {column} = ?", (user_id,)
                    ).fetchone()
                    count = row[0] if row else 0
                except Exception:
                    count = 0
                if count:
                    results[label] = count
        total = sum(results.values())
        return {
            "user_id": user_id,
            "total_references": total,
            "has_dependencies": total > 0,
            "by_source": results,
        }

    def delete_user_account(self, user_id, performer):
        if performer.user_id == user_id:
            raise ValueError("You cannot delete your own account.")

        user = self.get_user(user_id)
        if not user:
            raise ValueError("User not found.")

        p_role = (performer.role or "").lower()
        if p_role == "app_manager":
            if user.role in ("administrator", "app_manager"):
                raise PermissionError(
                    "App Managers cannot delete Admin or App Manager accounts."
                )
        elif p_role != "administrator":
            raise PermissionError("Your role is not authorized to delete accounts.")

        if user.active:
            raise ValueError(
                "Cannot delete an active user. Please deactivate/disable the user account first."
            )

        user.is_deleted = True
        user.active = False
        user.deleted_at = now_string()
        user.deleted_by = performer.user_id
        user.status = User.STATUS_ARCHIVED
        user.assigned_locations = []
        if not user.email.startswith("deleted_"):
            user.email = f"deleted_{user.user_id}_{user.email}"

        # Deactivate all active coordinator assignments for deleted user
        with self._connect() as conn:
            conn.execute("UPDATE coordinator_assignments SET status = 'Inactive' WHERE coordinator_id = ?", (user_id,))
            conn.commit()

        locs = [l for l in self.list_locations() if l.in_charge_id == user_id or getattr(l, "app_manager_id", None) == user_id]
        for loc in locs:
            if loc.in_charge_id == user_id:
                loc.in_charge_id = None
            if getattr(loc, "app_manager_id", None) == user_id:
                loc.app_manager_id = None
            self.save_location(loc)

        self.save_user(user)

        # Invalidate active sessions for deleted user immediately
        try:
            from api.security import invalidate_user_sessions
            invalidate_user_sessions(user_id)
        except Exception:
            pass

        self.log_activity(
            user_id,
            "User Soft Delete",
            performer.user_id,
            f"Soft deleted by {performer.name}",
        )
        return user

    def list_recycle_bin_users(self):
        """Returns soft-deleted users deleted within the 30-day restoration window."""
        query = f"""
            SELECT {self._USER_COLUMNS}
            FROM users u
            LEFT JOIN student_profiles sp ON u.user_id = sp.user_id
            LEFT JOIN staff_profiles st ON u.user_id = st.user_id
            WHERE u.is_deleted = 1
            ORDER BY u.deleted_at DESC
        """
        import time
        from datetime import datetime
        now_ts = time.time()
        thirty_days_sec = 30 * 86400

        valid_recycle_users = []
        with self._connect() as conn:
            rows = conn.execute(query).fetchall()
            for r in rows:
                u = self._user_from_joined_row(r)
                if u.deleted_at:
                    try:
                        clean_ts = u.deleted_at.replace("T", " ")[:19]
                        del_dt = datetime.strptime(clean_ts, "%Y-%m-%d %H:%M:%S")
                        del_ts = del_dt.timestamp()
                    except Exception:
                        del_ts = now_ts
                    
                    if (now_ts - del_ts) <= thirty_days_sec:
                        valid_recycle_users.append(u)
                else:
                    valid_recycle_users.append(u)
        return valid_recycle_users

    def restore_user_account(self, user_id, performer):
        """Restores a soft-deleted user if within the 30-day window."""
        p_role = (performer.role or "").lower()
        if p_role not in ("administrator", "admin", "app_manager"):
            raise PermissionError("Your role is not authorized to restore users.")

        with self._connect() as conn:
            row = conn.execute(
                f"""
                SELECT {self._USER_COLUMNS}
                FROM users u
                LEFT JOIN student_profiles sp ON u.user_id = sp.user_id
                LEFT JOIN staff_profiles st ON u.user_id = st.user_id
                WHERE u.user_id = ?
                """,
                (user_id,),
            ).fetchone()

        if not row:
            raise ValueError("User not found.")

        user = self._user_from_joined_row(row)
        if not user.is_deleted:
            raise ValueError("User is not deleted.")

        # Role Hierarchy Enforcement on Restore:
        # App Managers cannot restore Administrator, Super Admin, or App Manager accounts.
        target_role = (user.role or "").lower()
        if p_role == "app_manager" and target_role in ("administrator", "super_admin", "app_manager"):
            raise PermissionError("App Managers are not authorized to restore Administrator or App Manager accounts.")

        import time
        from datetime import datetime
        now_ts = time.time()
        thirty_days_sec = 30 * 86400
        if user.deleted_at:
            try:
                clean_ts = user.deleted_at.replace("T", " ")[:19]
                del_dt = datetime.strptime(clean_ts, "%Y-%m-%d %H:%M:%S")
                del_ts = del_dt.timestamp()
                if (now_ts - del_ts) > thirty_days_sec:
                    raise ValueError("Restoration period of 30 days has expired for this deleted user.")
            except ValueError:
                raise
            except Exception:
                pass

        user.is_deleted = False
        user.active = True
        user.status = User.STATUS_ACTIVE
        user.deleted_at = None
        user.deleted_by = None

        if user.email.startswith(f"deleted_{user.user_id}_"):
            user.email = user.email.replace(f"deleted_{user.user_id}_", "", 1)

        self.save_user(user)
        self.log_activity(
            user_id,
            "User Restored",
            performer.user_id,
            f"Account restored from Recycle Bin by {performer.name}",
        )
        return user

    def list_academic_programs(self):
        """Returns sorted list of distinct academic programs."""
        with self._connect() as conn:
            rows = conn.execute("SELECT DISTINCT program FROM student_profiles WHERE program IS NOT NULL AND program != ''").fetchall()
            programs = [r[0] for r in rows if r[0]]
            if not programs:
                programs = ["B.Tech", "M.Tech", "MBA", "MCA", "Ph.D"]
            return sorted(list(set(programs)))

    def log_activity(self, user_id, action, performed_by, remarks=None):
        aid = generate_id("ACT")
        ts = now_string()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_activities (activity_id, user_id, action, performed_by, timestamp, remarks)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (aid, user_id, action, performed_by, ts, remarks or ""),
            )

    def get_user_activities(self, user_id=None):
        with self._connect() as conn:
            if user_id:
                rows = conn.execute(
                    "SELECT * FROM user_activities WHERE user_id = ? ORDER BY timestamp DESC",
                    (user_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM user_activities "
                    "WHERE user_id NOT IN (SELECT user_id FROM users WHERE role = 'super_admin') "
                    "ORDER BY timestamp DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    def list_departments(self):
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM departments ORDER BY name").fetchall()
        return [
            Department.from_dict(self.repository._row_to_department(row)) for row in rows
        ]

    def list_locations(self):
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM locations ORDER BY name").fetchall()
        return [
            Location.from_dict(self.repository._row_to_location(row)) for row in rows
        ]

    def list_location_types(self):
        from models.location import LocationType, LOCATION_TYPES
        stored = [
            LocationType.from_dict(item)
            for item in self.repository.load().get("location_types", [])
        ]
        stored_names = {t.name for t in stored}
        for seed_name in LOCATION_TYPES:
            if seed_name not in stored_names:
                stored.append(LocationType(seed_name, type_id=f"LOC_TYPE_{seed_name.upper().replace(' ', '_').replace('/', '_')}"))
        return stored

    def get_location_type(self, type_id_or_name):
        if not type_id_or_name:
            return None
        for lt in self.list_location_types():
            if lt.type_id == type_id_or_name or lt.name.lower() == type_id_or_name.lower():
                return lt
        return None

    def create_location_type(self, name, description=None):
        from models.location import LocationType
        existing = self.get_location_type(name)
        if existing:
            raise ValueError(f"Location type '{name}' already exists.")
        lt = LocationType(name, description=description)
        self.save_location_type(lt)
        return lt

    def save_location_type(self, location_type):
        lts = self.list_location_types()
        for idx, item in enumerate(lts):
            if item.type_id == location_type.type_id or item.name == location_type.name:
                lts[idx] = location_type
                break
        else:
            lts.append(location_type)

        self.repository.save({"location_types": [t.to_dict() for t in lts]})

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO location_types (type_id, name, description)
                VALUES (?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    description=excluded.description
                """,
                (location_type.type_id, location_type.name, location_type.description)
            )

    def get_department(self, department_id):
        if not department_id:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM departments WHERE department_id = ? OR LOWER(name) = LOWER(?)",
                (department_id, department_id),
            ).fetchone()
            if row:
                return Department.from_dict(self.repository._row_to_department(row))
        dept_alias = {
            "DEPT_ELECTRICAL": "DEPT_HOSTEL_ELECTRICAL",
            "DEPT_PLUMBING": "DEPT_HOSTEL_PLUMBING",
            "DEPT_HOUSEKEEPING": "DEPT_HOSTEL_HOUSEKEEPING",
            "DEPT_FURNITURE": "DEPT_HOSTEL_FURNITURE",
            "DEPT_NETWORK": "DEPT_HOSTEL_NETWORK",
            "DEPT_FOOD": "DEPT_MESS_FOOD",
            "DEPT_OTHER": "DEPT_OTHER_GENERAL",
            "DEPT_HOSTEL_OTHER": "DEPT_OTHER_GENERAL",
            "OTHER": "DEPT_OTHER_GENERAL",
        }
        alias_target = dept_alias.get(str(department_id).strip().upper())
        if alias_target:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM departments WHERE department_id = ?",
                    (alias_target,),
                ).fetchone()
                if row:
                    return Department.from_dict(self.repository._row_to_department(row))
        if department_id.strip():
            return Department(department_id, 3, department_id=department_id)
        return None

    def get_location(self, location_id):
        if not location_id:
            return None
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM locations WHERE location_id = ? OR LOWER(name) = LOWER(?)",
                (location_id, location_id),
            ).fetchone()
            if row:
                return Location.from_dict(self.repository._row_to_location(row))
        loc_alias = {
            "LOC_HOSTEL_A": "LOC_HOSTEL_1",
            "LOC_HOSTEL_B": "LOC_HOSTEL_2",
            "LOC_HOSTEL": "LOC_HOSTEL_1",
            "LOC_ACADEMIC": "LOC_ACADEMIC_1",
            "LOC_MESS": "LOC_MESS_2",
            "LOC_SAC": "LOC_SAC_1",
            "LOC_SPORTS": "LOC_SPORTS_1",
        }
        target_id = loc_alias.get(str(location_id).strip().upper())
        if target_id:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT * FROM locations WHERE location_id = ?",
                    (target_id,),
                ).fetchone()
                if row:
                    return Location.from_dict(self.repository._row_to_location(row))
        return None

    def create_location(self, name, location_type=None, public_complaint_access=None, complaint_submission_policy=None):
        location = Location(
            name,
            location_type=location_type,
            public_complaint_access=public_complaint_access,
            complaint_submission_policy=complaint_submission_policy,
        )
        self.save_location(location)
        return location

    def save_location(self, location):
        locs = self.list_locations()
        for idx, item in enumerate(locs):
            if item.location_id == location.location_id:
                locs[idx] = location
                break
        else:
            locs.append(location)

        # Save to storage repo and sync to sqlite locations table
        self.repository.save({"locations": [l.to_dict() for l in locs]})

        policy = getattr(
            location,
            "complaint_submission_policy",
            getattr(location, "public_complaint_access", "everyone"),
        ) or "everyone"

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO locations (location_id, name, location_type, in_charge_id, coordinator_id, app_manager_id, active, archived, parent_id, public_complaint_access, complaint_submission_policy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(location_id) DO UPDATE SET
                    name=excluded.name,
                    location_type=excluded.location_type,
                    in_charge_id=excluded.in_charge_id,
                    coordinator_id=excluded.coordinator_id,
                    app_manager_id=excluded.app_manager_id,
                    active=excluded.active,
                    archived=excluded.archived,
                    parent_id=excluded.parent_id,
                    public_complaint_access=excluded.public_complaint_access,
                    complaint_submission_policy=excluded.complaint_submission_policy
                """,
                (
                    location.location_id,
                    location.name,
                    location.location_type,
                    location.in_charge_id,
                    location.coordinator_id,
                    getattr(location, "app_manager_id", None),
                    int(location.active),
                    int(getattr(location, "archived", False)),
                    getattr(location, "parent_id", None),
                    policy,
                    policy,
                ),
            )

    def delete_location_data(self, location_id):
        """Remove a location from both JSON storage and SQLite."""
        # Remove from JSON repository
        locs = self.list_locations()
        locs = [l for l in locs if l.location_id != location_id]
        self.repository.save({"locations": [l.to_dict() for l in locs]})

        # Remove from SQLite and cleanup assignments
        with self._connect() as conn:
            conn.execute("UPDATE coordinator_assignments SET status = 'Inactive' WHERE location_id = ?", (location_id,))
            conn.execute("DELETE FROM location_departments WHERE location_id = ?", (location_id,))
            conn.execute("DELETE FROM locations WHERE location_id = ?", (location_id,))
            conn.commit()

        # Clear location_id and assigned_locations from any users assigned to this location
        for user in self.list_users():
            changed = False
            if getattr(user, "location_id", None) == location_id:
                user.location_id = None
                changed = True
            if location_id in (getattr(user, "assigned_locations", None) or []):
                user.assigned_locations = [l for l in user.assigned_locations if l != location_id]
                changed = True
            if changed:
                self.save_user(user)

    def create_department(self, name, sla_days=1, complaint_types=None, location_id=None, description=None):
        from models.department import Department
        dept = Department(name, sla_days=sla_days, complaint_types=complaint_types or [], location_id=location_id, description=description)
        self.save_department(dept)
        return dept

    def save_department(self, department):
        depts = self.list_departments()
        for idx, item in enumerate(depts):
            if item.department_id == department.department_id:
                depts[idx] = department
                break
        else:
            depts.append(department)

        self.repository.save({"departments": [d.to_dict() for d in depts]})

    def delete_department_data(self, department_id):
        """Remove a department from JSON storage and clear department_id from assigned users."""
        depts = self.list_departments()
        depts = [d for d in depts if d.department_id != department_id]
        self.repository.save({"departments": [d.to_dict() for d in depts]})

        with self._connect() as conn:
            conn.execute("DELETE FROM location_departments WHERE department_id = ?", (department_id,))
            conn.commit()

        # Clear department_id from any users assigned to this department
        for user in self.list_users():
            if getattr(user, "department_id", None) == department_id:
                user.department_id = None
                self.save_user(user)

    # =========================================================================
    # COORDINATOR ASSIGNMENT MANAGEMENT
    # =========================================================================
    def list_coordinator_assignments(self, coordinator_id=None, location_id=None, department_id=None):
        search_ids = []
        if coordinator_id:
            search_ids.append(coordinator_id)
            resolved = self.get_user(coordinator_id)
            if resolved and resolved.user_id not in search_ids:
                search_ids.append(resolved.user_id)
        with self._connect() as conn:
            query = "SELECT * FROM coordinator_assignments WHERE (status IS NULL OR status = 'Active')"
            params = []
            if search_ids:
                placeholders = ",".join("?" for _ in search_ids)
                query += f" AND coordinator_id IN ({placeholders})"
                params.extend(search_ids)
            if location_id:
                query += " AND (location_id = ? OR location_id IN (SELECT location_id FROM locations WHERE location_type = ?))"
                params.extend([location_id, location_id])
            if department_id:
                query += " AND (department_id = ? OR department_id IN (SELECT department_id FROM departments WHERE name = ?))"
                params.extend([department_id, department_id])

            rows = conn.execute(query, params).fetchall()
            results = [dict(r) for r in rows]

        # Check fallback user single department/location fields for legacy compatibility
        if coordinator_id and not results:
            user = self.get_user(coordinator_id)
            if user and (user.role or "").lower() == "coordinator":
                u_dept = getattr(user, "department_id", None)
                u_loc = getattr(user, "location_id", None)
                if u_dept and u_loc:
                    results.append({
                        "assignment_id": f"LEGACY_{user.user_id}",
                        "coordinator_id": user.user_id,
                        "department_id": u_dept,
                        "location_id": u_loc,
                        "assigned_at": getattr(user, "created_at", now_string()),
                        "assigned_by": "legacy",
                        "status": "Active"
                    })
        return results

    def assign_coordinator(self, coordinator_id, location_id=None, department_id=None, assigned_by="system", confirm_replacement=False):
        user = self.get_user(coordinator_id)
        if not user:
            raise ValueError("Coordinator user not found.")
        if (user.role or "").lower() not in ("coordinator", "employee"):
            raise ValueError("User must have coordinator or employee role.")

        loc_target = location_id if (location_id and location_id.strip() and location_id != "unassigned") else "ALL"
        loc = self.get_location(loc_target) if loc_target != "ALL" else None
        loc_name = loc.name if loc else loc_target

        dept = self.get_department(department_id) if department_id else None
        dept_name = dept.name if dept else (department_id or "General")

        # Rule 3: One Coordinator per Location + Department (Enforce uniqueness)
        existing = self.list_coordinator_assignments(location_id=loc_target, department_id=department_id)
        for ex in existing:
            if ex["coordinator_id"] != coordinator_id:
                if confirm_replacement:
                    with self._connect() as conn:
                        conn.execute("UPDATE coordinator_assignments SET status = 'Inactive' WHERE assignment_id = ? OR (location_id = ? AND department_id = ?)", (ex.get("assignment_id"), loc_target, department_id))
                        conn.commit()
                else:
                    other_user = self.get_user(ex["coordinator_id"])
                    other_name = other_user.name if other_user else ex["coordinator_id"]
                    raise ValueError(
                        f"The combination '{loc_name} -> {dept_name}' is already assigned to {other_name}. "
                        "Unassign or replace the existing assignment first."
                    )
            elif ex["coordinator_id"] == coordinator_id:
                return ex

        asgn_id = generate_id("ASGN")
        now_str = now_string()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO coordinator_assignments (assignment_id, coordinator_id, department_id, location_id, assigned_at, assigned_by, status)
                VALUES (?, ?, ?, ?, ?, ?, 'Active')
                """,
                (asgn_id, coordinator_id, department_id, loc_target, now_str, assigned_by)
            )

        if dept:
            dept.coordinator_id = coordinator_id
            self.save_department(dept)

        return {
            "assignment_id": asgn_id,
            "coordinator_id": coordinator_id,
            "department_id": department_id,
            "location_id": loc_target,
            "assigned_at": now_str,
            "assigned_by": assigned_by,
            "status": "Active"
        }

    def remove_coordinator_assignment(self, assignment_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM coordinator_assignments WHERE assignment_id = ?", (assignment_id,))
        return True

    def set_coordinator_assignments(self, coordinator_id, assignments, assigned_by="system"):
        user = self.get_user(coordinator_id)
        if not user:
            raise ValueError("Coordinator user not found.")
        if (user.role or "").lower() not in ("coordinator", "employee"):
            raise ValueError("User must have coordinator or employee role.")

        now_str = now_string()
        with self._connect() as conn:
            conn.execute("UPDATE coordinator_assignments SET status = 'Inactive' WHERE coordinator_id = ?", (coordinator_id,))
            inserted = []
            for item in assignments:
                loc_id = item.get("location_id") or "ALL"
                dept_id = item.get("department_id")
                if not dept_id:
                    continue
                asgn_id = generate_id("ASGN")
                conn.execute(
                    """
                    INSERT INTO coordinator_assignments (assignment_id, coordinator_id, department_id, location_id, assigned_at, assigned_by, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'Active')
                    ON CONFLICT(coordinator_id, location_id, department_id) DO UPDATE SET
                        status = 'Active',
                        assigned_at = excluded.assigned_at,
                        assigned_by = excluded.assigned_by
                    """,
                    (asgn_id, coordinator_id, dept_id, loc_id, now_str, assigned_by)
                )
                inserted.append({
                    "assignment_id": asgn_id,
                    "coordinator_id": coordinator_id,
                    "department_id": dept_id,
                    "location_id": loc_id,
                    "assigned_at": now_str,
                    "assigned_by": assigned_by,
                    "status": "Active"
                })
            conn.commit()
            return inserted

    def get_coverage_gaps(self):
        all_locs = [l for l in self.list_locations() if getattr(l, "active", True) and not getattr(l, "archived", False)]
        all_depts = [d for d in self.list_departments() if getattr(d, "active", True) and not getattr(d, "archived", False)]

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT ca.location_id, ca.department_id
                FROM coordinator_assignments ca
                JOIN users u ON ca.coordinator_id = u.user_id
                WHERE (ca.status IS NULL OR ca.status = 'Active')
                  AND u.active = 1 AND (u.is_deleted IS NULL OR u.is_deleted = 0)
                  AND (u.status IS NULL OR u.status = 'Active')
                """
            ).fetchall()
            all_loc_depts = set()
            for r in rows:
                loc_id = r["location_id"]
                dept_id = r["department_id"]
                all_loc_depts.add(dept_id)

            # Also check direct coordinator_id on departments
            dept_rows = conn.execute(
                """
                SELECT d.department_id FROM departments d
                JOIN users u ON d.coordinator_id = u.user_id
                WHERE d.active = 1 AND u.active = 1 AND (u.is_deleted IS NULL OR u.is_deleted = 0)
                """
            ).fetchall()
            for dr in dept_rows:
                all_loc_depts.add(dr["department_id"])

            # Also check teams
            team_rows = conn.execute(
                """
                SELECT DISTINCT t.department_id FROM teams t
                JOIN users u ON t.coordinator_id = u.user_id
                WHERE t.active = 1 AND u.active = 1 AND (u.is_deleted IS NULL OR u.is_deleted = 0)
                """
            ).fetchall()
            for tr in team_rows:
                all_loc_depts.add(tr["department_id"])

        unassigned_departments = []
        for dept in all_depts:
            if dept.department_id not in all_loc_depts:
                unassigned_departments.append({
                    "department_id": dept.department_id,
                    "department_name": dept.name,
                    "location_id": "ALL",
                    "location_name": "Campus-wide",
                })

        unassigned_warden_locations = []
        for loc in all_locs:
            warden_id = getattr(loc, "in_charge_id", None)
            warden_user = self.get_user(warden_id) if warden_id else None
            if not warden_user or not warden_user.active or getattr(warden_user, "is_deleted", False) or getattr(warden_user, "status", "Active") != "Active":
                unassigned_warden_locations.append({
                    "location_id": loc.location_id,
                    "location_name": loc.name,
                    "in_charge_id": warden_id,
                })

        return {
            "unassigned_departments": unassigned_departments,
            "unassigned_pairs": unassigned_departments,
            "unassigned_warden_locations": unassigned_warden_locations,
        }

    def is_coordinator_assigned(self, coordinator_id, location_id, department_id):
        user = self.get_user(coordinator_id)
        if not user or (user.role or "").lower() not in ("coordinator", "employee"):
            return False

        effective_ids = {coordinator_id, user.user_id}
        dept_obj = self.get_department(department_id)
        if dept_obj and (
            getattr(dept_obj, "coordinator_id", None) in effective_ids
            or getattr(dept_obj, "coordinator_2_id", None) in effective_ids
        ):
            return True
        for cid in effective_ids:
            if self.is_coordinator_assigned_legacy(cid, location_id, department_id):
                return True
        return False

    def get_active_coordinator_for_department(self, department_id: str):
        dept = self.get_department(department_id)
        if not dept:
            return None
        team_svc = getattr(self, "team_service", None)
        if not team_svc:
            try:
                from services.team_service import TeamService
                team_svc = TeamService(db_path=str(self.db_path) if hasattr(self, "db_path") else "storage/campus_pulse.db")
            except Exception:
                team_svc = None

        from datetime import datetime
        today_str = datetime.now().strftime("%Y-%m-%d")

        def _is_on_leave(uid):
            if team_svc:
                try:
                    return team_svc.is_user_on_leave(uid, department_id=department_id)
                except Exception:
                    pass
            with self._connect() as conn:
                row = conn.execute(
                    """
                    SELECT 1 FROM user_leaves
                    WHERE user_id = ?
                      AND date(from_date) <= date(?)
                      AND date(?) <= date(to_date)
                      AND (department_id IS NULL OR department_id = '' OR department_id = 'ALL' OR department_id = ?)
                    LIMIT 1
                    """,
                    (uid, today_str, today_str, department_id),
                ).fetchone()
                return bool(row)

        c1_id = getattr(dept, "coordinator_id", None)
        if c1_id:
            if not _is_on_leave(c1_id):
                u1 = self.get_user(c1_id)
                if u1 and getattr(u1, "active", True) and not getattr(u1, "is_deleted", False):
                    return u1
        c2_id = getattr(dept, "coordinator_2_id", None)
        if c2_id:
            if not _is_on_leave(c2_id):
                u2 = self.get_user(c2_id)
                if u2 and getattr(u2, "active", True) and not getattr(u2, "is_deleted", False):
                    return u2
        return None

    def is_coordinator_assigned_legacy(self, coordinator_id, location_id, department_id):

        assignments = self.list_coordinator_assignments(coordinator_id=coordinator_id)
        if not assignments:
            return False

        loc_obj = self.get_location(location_id)
        loc_id = loc_obj.location_id if loc_obj else location_id
        loc_type = (getattr(loc_obj, "location_type", None) or (loc_obj.infer_location_type(loc_obj.name) if loc_obj else location_id))

        dept_obj = self.get_department(department_id)
        dept_id = dept_obj.department_id if dept_obj else department_id
        dept_name = dept_obj.name if dept_obj else department_id

        for asgn in assignments:
            a_loc = asgn.get("location_id")
            a_dept = asgn.get("department_id")

            loc_match = (
                a_loc in ("ALL", None)
                or a_loc == loc_id
                or a_loc == loc_type
                or (loc_obj and a_loc.lower() == loc_obj.name.lower())
            )
            dept_match = (
                a_dept in ("ALL", None)
                or a_dept == dept_id
                or a_dept.lower() == dept_name.lower()
            )

            if loc_match and dept_match:
                return True

        return False

    def get_unassigned_location_departments(self):
        locations = [l for l in self.list_locations() if not getattr(l, "archived", False) and getattr(l, "active", True)]
        departments = [d for d in self.list_departments() if not getattr(d, "archived", False) and getattr(d, "active", True)]
        all_assignments = self.list_coordinator_assignments()

        unassigned = []
        for loc in locations:
            loc_type = getattr(loc, "location_type", None) or loc.infer_location_type(loc.name)
            type_to_template_id = {
                "Hostel": "LOC_HOSTEL_A",
                "Academic Block": "LOC_ACADEMIC",
                "Mess": "LOC_MESS",
                "Student Activity Center": "LOC_SAC",
                "Sports Complex": "LOC_SPORTS",
                "Other / Not Sure": "LOC_OTHER",
            }
            template_id = type_to_template_id.get(loc_type)

            loc_depts = [
                d for d in departments
                if d.location_id == loc.location_id or d.location_id == loc_type or (template_id and d.location_id == template_id)
            ]

            for d in loc_depts:
                is_assigned = False
                assigned_coord_id = None
                for asgn in all_assignments:
                    a_loc = asgn.get("location_id")
                    a_dept = asgn.get("department_id")
                    l_match = (a_loc == loc.location_id or a_loc == loc_type or (loc.name and a_loc and a_loc.lower() == loc.name.lower()))
                    d_match = (a_dept == d.department_id or (d.name and a_dept and a_dept.lower() == d.name.lower()))
                    if l_match and d_match:
                        is_assigned = True
                        assigned_coord_id = asgn.get("coordinator_id")
                        break

                if not is_assigned:
                    unassigned.append({
                        "location_id": loc.location_id,
                        "location_name": loc.name,
                        "location_type": loc_type,
                        "department_id": d.department_id,
                        "department_name": d.name,
                        "status": "Unassigned"
                    })

        return unassigned

    # =========================================================================
    # LOCATION IN-CHARGE / WARDEN ASSIGNMENT MANAGEMENT
    # =========================================================================
    def is_warden_assigned(self, warden_id, location_id):
        user = self.get_user(warden_id)
        if not user or (user.role or "").lower() != "location_in_charge":
            return False

        loc = self.get_location(location_id)
        target_loc_id = loc.location_id if loc else location_id
        target_loc_name = loc.name if loc else location_id

        if loc and loc.in_charge_id == warden_id:
            return True

        assigned = getattr(user, "assigned_locations", None) or []
        for a in assigned:
            if a == target_loc_id or (target_loc_name and a.lower() == target_loc_name.lower()):
                return True

        if getattr(user, "location_id", None):
            u_loc = user.location_id
            if u_loc == target_loc_id or (target_loc_name and u_loc.lower() == target_loc_name.lower()):
                return True

        return False

    def get_location_in_charge_assignments(self):
        locations = [l for l in self.list_locations() if not getattr(l, "archived", False) and getattr(l, "active", True)]
        assignments = []
        for loc in locations:
            in_charge_user = self.get_user(loc.in_charge_id) if loc.in_charge_id else None
            assignments.append({
                "location_id": loc.location_id,
                "location_name": loc.name,
                "location_type": getattr(loc, "location_type", None) or loc.infer_location_type(loc.name),
                "in_charge_id": loc.in_charge_id,
                "in_charge_name": in_charge_user.name if in_charge_user else None,
                "status": "Assigned" if (loc.in_charge_id and in_charge_user) else "Unassigned"
            })
        return assignments

    def unassign_location_in_charge(self, location_id):
        loc = self.get_location(location_id)
        if not loc:
            raise ValueError("Location not found.")
        old_in_charge = loc.in_charge_id
        loc.in_charge_id = None
        self.save_location(loc)

        if old_in_charge:
            user = self.get_user(old_in_charge)
            if user:
                assigned = [l for l in (getattr(user, "assigned_locations", None) or []) if l != location_id and l != loc.name]
                user.assigned_locations = assigned
                if user.location_id == location_id:
                    user.location_id = assigned[0] if assigned else None
                self.save_user(user)

        return True

    def get_location_coordinator_assignments(self):
        locations = [l for l in self.list_locations() if not getattr(l, "archived", False) and getattr(l, "active", True)]
        assignments = []
        for loc in locations:
            coord_user = self.get_user(loc.coordinator_id) if loc.coordinator_id else None
            assignments.append({
                "location_id": loc.location_id,
                "location_name": loc.name,
                "location_type": getattr(loc, "location_type", None) or loc.infer_location_type(loc.name),
                "coordinator_id": loc.coordinator_id,
                "coordinator_name": coord_user.name if coord_user else None,
                "status": "Assigned" if (loc.coordinator_id and coord_user) else "Unassigned"
            })
        return assignments

    def assign_location_coordinator(self, location_id, coordinator_id):
        loc = self.get_location(location_id)
        if not loc:
            raise ValueError("Location not found.")

        # Verify that only a valid active Coordinator user can be assigned.
        user = self.get_user(coordinator_id)
        if not user:
            raise ValueError("User not found.")
        if (user.role or "").lower() not in ("coordinator", "employee"):
            raise ValueError("Only users with role 'coordinator' or 'employee' can be assigned as location coordinators.")
        if not user.active:
            raise ValueError("Only active users can be assigned.")

        loc.coordinator_id = coordinator_id
        self.save_location(loc)
        return True

    def unassign_location_coordinator(self, location_id):
        loc = self.get_location(location_id)
        if not loc:
            raise ValueError("Location not found.")
        loc.coordinator_id = None
        self.save_location(loc)
        return True

    # =========================================================================
    # APP MANAGER ASSIGNMENT MANAGEMENT & SCOPE
    # =========================================================================
    def is_app_manager_assigned(self, app_manager_id, location_id):
        user = self.get_user(app_manager_id)
        if not user or (user.role or "").lower() != "app_manager":
            return False

        loc = self.get_location(location_id)
        if loc and getattr(loc, "app_manager_id", None) == app_manager_id:
            return True

        target_loc_id = loc.location_id if loc else location_id
        target_loc_name = loc.name if loc else location_id
        return self._manager_covers_location(user, target_loc_id, target_loc_name)

    def _manager_covers_location(self, user, target_loc_id, target_loc_name):
        loc = self.get_location(target_loc_id)
        if loc and getattr(loc, "app_manager_id", None) == user.user_id:
            return True

        # Check assigned_locations list
        assigned = getattr(user, "assigned_locations", None) or []
        for a in assigned:
            if a == target_loc_id or (target_loc_name and a.lower() == target_loc_name.lower()):
                return True

        # Check single location_id field
        if getattr(user, "location_id", None):
            u_loc = user.location_id
            if u_loc == target_loc_id or (target_loc_name and u_loc.lower() == target_loc_name.lower()):
                return True

        return False

    def get_app_manager_locations(self, manager_id):
        user = self.get_user(manager_id)
        assigned_ids = set()
        if user:
            for l_val in (getattr(user, "assigned_locations", None) or []):
                assigned_ids.add(l_val)
            if getattr(user, "location_id", None):
                assigned_ids.add(user.location_id)

        all_locs = self.list_locations()
        results = []
        seen = set()
        for loc in all_locs:
            if getattr(loc, "archived", False) or not getattr(loc, "active", True):
                continue
            if getattr(loc, "app_manager_id", None) == manager_id or loc.location_id in assigned_ids or (loc.name and loc.name in assigned_ids):
                if loc.location_id not in seen:
                    results.append(loc)
                    seen.add(loc.location_id)
        return results

    def get_warden_locations(self, warden_id):
        user = self.get_user(warden_id)
        assigned_ids = set()
        if user:
            for l_val in (getattr(user, "assigned_locations", None) or []):
                assigned_ids.add(l_val)
            if getattr(user, "location_id", None):
                assigned_ids.add(user.location_id)

        all_locs = self.list_locations()
        results = []
        seen = set()
        for loc in all_locs:
            if getattr(loc, "archived", False) or not getattr(loc, "active", True):
                continue
            if getattr(loc, "in_charge_id", None) == warden_id or loc.location_id in assigned_ids or (loc.name and loc.name in assigned_ids):
                if loc.location_id not in seen:
                    results.append(loc)
                    seen.add(loc.location_id)
        return results

    def assign_user_locations(self, user_id, location_ids):
        user = self.get_user(user_id)
        if not user:
            raise ValueError("User not found.")
        role = (user.role or "").lower()
        if role not in ("app_manager", "location_in_charge", "warden", "employee", "coordinator"):
            raise ValueError("User must have 'app_manager', 'location_in_charge', 'employee', or 'coordinator' role.")

        user.assigned_locations = list(set(location_ids or []))
        if user.assigned_locations and not user.location_id:
            user.location_id = user.assigned_locations[0]
        self.save_user(user)

        with self._connect() as conn:
            conn.execute(
                "UPDATE staff_profiles SET assigned_locations = ? WHERE user_id = ?",
                (json.dumps(user.assigned_locations), user_id)
            )
            conn.commit()

        # Update locations table app_manager_id or in_charge_id for each location
        if role == "app_manager":
            other_mgrs = [
                u for u in self.list_users(role="app_manager")
                if u.user_id != user_id
            ]
            for loc in self.list_locations():
                if loc.location_id in user.assigned_locations:
                    loc.app_manager_id = user_id
                    self.save_location(loc)
                    # If this location was assigned to another App Manager, strip it from their profile
                    for other in other_mgrs:
                        other_locs = getattr(other, "assigned_locations", None) or []
                        if loc.location_id in other_locs or loc.name in other_locs:
                            other.assigned_locations = [
                                lid for lid in other_locs
                                if lid != loc.location_id and lid != loc.name
                            ]
                            if other.location_id == loc.location_id:
                                other.location_id = other.assigned_locations[0] if other.assigned_locations else None
                            self.save_user(other)
                            with self._connect() as conn:
                                conn.execute(
                                    "UPDATE staff_profiles SET assigned_locations = ? WHERE user_id = ?",
                                    (json.dumps(other.assigned_locations), other.user_id)
                                )
                                conn.commit()
                elif getattr(loc, "app_manager_id", None) == user_id:
                    loc.app_manager_id = None
                    self.save_location(loc)
        elif role in ("location_in_charge", "warden"):
            other_wardens = [
                u for u in self.list_users()
                if (u.role or "").lower() in ("location_in_charge", "warden") and u.user_id != user_id
            ]
            for loc in self.list_locations():
                if loc.location_id in user.assigned_locations:
                    loc.in_charge_id = user_id
                    self.save_location(loc)
                    # If this location was assigned to another Warden, strip it from their profile
                    for other in other_wardens:
                        other_locs = getattr(other, "assigned_locations", None) or []
                        if loc.location_id in other_locs or loc.name in other_locs:
                            other.assigned_locations = [
                                lid for lid in other_locs
                                if lid != loc.location_id and lid != loc.name
                            ]
                            if other.location_id == loc.location_id:
                                other.location_id = other.assigned_locations[0] if other.assigned_locations else None
                            self.save_user(other)
                            with self._connect() as conn:
                                conn.execute(
                                    "UPDATE staff_profiles SET assigned_locations = ? WHERE user_id = ?",
                                    (json.dumps(other.assigned_locations), other.user_id)
                                )
                                conn.commit()
                elif getattr(loc, "in_charge_id", None) == user_id:
                    loc.in_charge_id = None
                    self.save_location(loc)
        elif role in ("employee", "coordinator"):
            import uuid
            from datetime import datetime

            user.assigned_locations = list(set(location_ids or []))
            if user.assigned_locations and not user.location_id:
                user.location_id = user.assigned_locations[0]
            elif not user.assigned_locations:
                user.location_id = None
            self.save_user(user)

            with self._connect() as conn:
                conn.execute(
                    "UPDATE users SET location_id = ? WHERE user_id = ?",
                    (user.location_id, user_id)
                )
                conn.execute(
                    "UPDATE staff_profiles SET assigned_locations = ? WHERE user_id = ?",
                    (json.dumps(user.assigned_locations), user_id)
                )

                # Synchronize employee_work_memberships with authorized locations
                dept_rows = conn.execute(
                    "SELECT DISTINCT department_id FROM employee_work_memberships WHERE user_id = ?",
                    (user_id,)
                ).fetchall()
                user_depts = [r[0] for r in dept_rows]
                if user.department_id and user.department_id not in user_depts:
                    user_depts.append(user.department_id)

                if user.assigned_locations:
                    loc_placeholders = ",".join("?" for _ in user.assigned_locations)
                    conn.execute(
                        f"DELETE FROM employee_work_memberships WHERE user_id = ? AND location_id NOT IN ({loc_placeholders})",
                        (user_id, *user.assigned_locations)
                    )
                else:
                    conn.execute("DELETE FROM employee_work_memberships WHERE user_id = ?", (user_id,))

                now_str = datetime.now().isoformat()
                for did in user_depts:
                    for lid in user.assigned_locations:
                        exists = conn.execute(
                            "SELECT 1 FROM employee_work_memberships WHERE user_id = ? AND department_id = ? AND location_id = ?",
                            (user_id, did, lid)
                        ).fetchone()
                        if not exists:
                            m_id = f"EWM_{uuid.uuid4().hex[:12]}"
                            conn.execute(
                                "INSERT INTO employee_work_memberships (membership_id, user_id, department_id, location_id, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?)",
                                (m_id, user_id, did, lid, now_str, "admin")
                            )
                conn.commit()

        return user

    def assign_app_manager_locations(self, app_manager_id, location_ids):
        return self.assign_user_locations(app_manager_id, location_ids)

    def assign_user_departments(self, user_id, department_ids, caller_user=None):
        import uuid
        from datetime import datetime

        user = self.get_user(user_id)
        if not user:
            raise ValueError("User not found.")
        role = (user.role or "").lower()
        if role not in ("employee", "coordinator"):
            raise ValueError("Department eligibility can only be assigned to Coordinators.")

        # App manager location scoping check: verify employee shares authorized location
        if caller_user and (caller_user.role or "").lower() == "app_manager":
            mgr_locs = {loc.location_id for loc in self.get_app_manager_locations(caller_user.user_id)}
            user_locs = set(getattr(user, "assigned_locations", None) or [])
            if getattr(user, "location_id", None):
                user_locs.add(user.location_id)
            if not user_locs.intersection(mgr_locs):
                raise PermissionError("App Managers can only manage employees within their assigned locations.")

        all_depts = {d.department_id: d for d in self.list_departments()}
        for did in department_ids:
            if did not in all_depts:
                raise ValueError(f"Invalid department ID: {did}")

        # Protect coordinator positions from accidental removal
        with self._connect() as conn:
            coord_rows = conn.execute(
                "SELECT department_id, name, 'Coordinator 1' as pos FROM departments WHERE coordinator_id = ? "
                "UNION ALL "
                "SELECT department_id, name, 'Coordinator 2' as pos FROM departments WHERE coordinator_2_id = ?",
                (user_id, user_id),
            ).fetchall()
            for cr in coord_rows:
                if cr["department_id"] not in department_ids:
                    raise ValueError(
                        f"Cannot remove '{cr['name']}' because {user.name} is currently assigned as {cr['pos']} for this department. Please reassign the coordinator position first."
                    )

        # Update primary department
        new_primary = department_ids[0] if department_ids else None
        user.department_id = new_primary
        self.save_user(user)

        with self._connect() as conn:
            primary_name = all_depts[new_primary].name if new_primary and new_primary in all_depts else None
            conn.execute(
                "UPDATE users SET department_id = ? WHERE user_id = ?",
                (new_primary, user_id),
            )
            conn.execute(
                "UPDATE staff_profiles SET department = ? WHERE user_id = ?",
                (primary_name, user_id),
            )

            # Every employee is eligible across all locations on campus
            all_loc_ids = [l.location_id for l in self.list_locations() if not getattr(l, "archived", False)]
            user_locs = all_loc_ids
            user.assigned_locations = all_loc_ids
            conn.execute(
                "UPDATE staff_profiles SET assigned_locations = ? WHERE user_id = ?",
                (json.dumps(all_loc_ids), user_id),
            )

            # Remove memberships for departments no longer eligible
            if department_ids:
                placeholders = ",".join("?" for _ in department_ids)
                conn.execute(
                    f"DELETE FROM employee_work_memberships WHERE user_id = ? AND department_id NOT IN ({placeholders})",
                    (user_id, *department_ids),
                )
            else:
                conn.execute(
                    "DELETE FROM employee_work_memberships WHERE user_id = ?",
                    (user_id,),
                )

            # Add memberships for newly eligible departments
            now_str = datetime.now().isoformat()
            creator_id = getattr(caller_user, "user_id", "admin")
            for did in department_ids:
                for lid in user_locs:
                    exists = conn.execute(
                        "SELECT 1 FROM employee_work_memberships WHERE user_id = ? AND department_id = ? AND location_id = ?",
                        (user_id, did, lid),
                    ).fetchone()
                    if not exists:
                        m_id = f"EWM_{uuid.uuid4().hex[:12]}"
                        conn.execute(
                            "INSERT INTO employee_work_memberships (membership_id, user_id, department_id, location_id, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?)",
                            (m_id, user_id, did, lid, now_str, creator_id),
                        )
            conn.commit()

        return user

    def assign_employee_work_assignments(self, user_id, department_ids, location_ids, caller_user=None):
        import uuid
        from datetime import datetime

        user = self.get_user(user_id)
        if not user:
            raise ValueError("User not found.")
        role = (user.role or "").lower()
        if role not in ("employee", "coordinator"):
            raise ValueError("Work assignments can only be configured for Coordinators.")

        # App manager location scoping check: verify employee shares authorized location
        if caller_user and (caller_user.role or "").lower() == "app_manager":
            mgr_locs = {loc.location_id for loc in self.get_app_manager_locations(caller_user.user_id)}
            user_locs = set(getattr(user, "assigned_locations", None) or [])
            if getattr(user, "location_id", None):
                user_locs.add(user.location_id)
            if not user_locs.intersection(mgr_locs):
                raise PermissionError("App Managers can only manage employees within their assigned locations.")

        all_depts = {d.department_id: d for d in self.list_departments()}
        for did in department_ids:
            if did not in all_depts:
                raise ValueError(f"Invalid department ID: {did}")

        all_locs = {l.location_id: l for l in self.list_locations()}
        for lid in location_ids:
            if lid not in all_locs:
                raise ValueError(f"Invalid location ID: {lid}")

        # Protect coordinator positions from accidental removal
        with self._connect() as conn:
            coord_rows = conn.execute(
                "SELECT department_id, name, 'Coordinator 1' as pos FROM departments WHERE coordinator_id = ? "
                "UNION ALL "
                "SELECT department_id, name, 'Coordinator 2' as pos FROM departments WHERE coordinator_2_id = ?",
                (user_id, user_id),
            ).fetchall()
            for cr in coord_rows:
                if cr["department_id"] not in department_ids:
                    raise ValueError(
                        f"Cannot remove '{cr['name']}' because {user.name} is currently assigned as {cr['pos']} for this department. Please reassign the coordinator position first."
                    )

        # Clean duplicates preserving order
        clean_dept_ids = list(dict.fromkeys(department_ids or []))
        clean_loc_ids = list(dict.fromkeys(location_ids or []))

        user.department_id = clean_dept_ids[0] if clean_dept_ids else None
        user.assigned_departments = clean_dept_ids
        user.assigned_locations = clean_loc_ids
        if clean_loc_ids and (not user.location_id or user.location_id not in clean_loc_ids):
            user.location_id = clean_loc_ids[0]
        elif not clean_loc_ids:
            user.location_id = None
        self.save_user(user)

        with self._connect() as conn:
            primary_dept_name = all_depts[user.department_id].name if user.department_id and user.department_id in all_depts else None
            conn.execute(
                "UPDATE users SET department_id = ?, location_id = ? WHERE user_id = ?",
                (user.department_id, user.location_id, user_id),
            )
            conn.execute(
                "UPDATE staff_profiles SET department = ?, assigned_locations = ? WHERE user_id = ?",
                (primary_dept_name, json.dumps(clean_loc_ids), user_id),
            )

            # Synchronize employee_work_memberships
            if not clean_dept_ids or not clean_loc_ids:
                conn.execute("DELETE FROM employee_work_memberships WHERE user_id = ?", (user_id,))
            else:
                dept_placeholders = ",".join("?" for _ in clean_dept_ids)
                loc_placeholders = ",".join("?" for _ in clean_loc_ids)
                conn.execute(
                    f"DELETE FROM employee_work_memberships WHERE user_id = ? AND (department_id NOT IN ({dept_placeholders}) OR location_id NOT IN ({loc_placeholders}))",
                    (user_id, *clean_dept_ids, *clean_loc_ids),
                )

                now_str = datetime.now().isoformat()
                creator_id = getattr(caller_user, "user_id", "admin")
                for did in clean_dept_ids:
                    for lid in clean_loc_ids:
                        exists = conn.execute(
                            "SELECT 1 FROM employee_work_memberships WHERE user_id = ? AND department_id = ? AND location_id = ?",
                            (user_id, did, lid),
                        ).fetchone()
                        if not exists:
                            m_id = f"EWM_{uuid.uuid4().hex[:12]}"
                            conn.execute(
                                "INSERT INTO employee_work_memberships (membership_id, user_id, department_id, location_id, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?)",
                                (m_id, user_id, did, lid, now_str, creator_id),
                            )
            conn.commit()

        return user

    def get_app_manager_assignments(self):
        app_managers = [u for u in self.list_users(role="app_manager") if getattr(u, "active", True)]
        locations = [l for l in self.list_locations() if not getattr(l, "archived", False) and getattr(l, "active", True)]

        manager_list = []
        assigned_location_ids = set()

        for mgr in app_managers:
            mgr_locs = self.get_app_manager_locations(mgr.user_id)
            loc_objs = []
            for loc in mgr_locs:
                loc_objs.append({"location_id": loc.location_id, "location_name": loc.name})
                assigned_location_ids.add(loc.location_id)

            manager_list.append({
                "user_id": mgr.user_id,
                "name": mgr.name,
                "email": mgr.email,
                "assigned_locations": loc_objs,
                "status": "Assigned" if loc_objs else "No locations assigned"
            })

        unassigned_locations = [
            {
                "location_id": loc.location_id,
                "location_name": loc.name,
                "location_type": getattr(loc, "location_type", None) or loc.infer_location_type(loc.name),
                "status": "Unassigned"
            }
            for loc in locations if loc.location_id not in assigned_location_ids and loc.name not in assigned_location_ids
        ]

        return {
            "app_managers": manager_list,
            "unassigned_locations": unassigned_locations
        }

    def get_location_app_manager_id(self, location_id):
        loc = self.get_location(location_id)
        if loc and getattr(loc, "app_manager_id", None):
            return loc.app_manager_id
        target_loc_id = loc.location_id if loc else location_id
        target_loc_name = loc.name if loc else location_id

        for mgr in self.list_users(role="app_manager"):
            if self._manager_covers_location(mgr, target_loc_id, target_loc_name):
                return mgr.user_id
        return None

    def assign_location_app_manager(self, location_id, app_manager_id):
        user = self.get_user(app_manager_id)
        if not user:
            raise ValueError("App Manager user not found.")
        if (user.role or "").lower() != "app_manager":
            raise ValueError("User must have 'app_manager' role.")

        loc = self.get_location(location_id)
        if not loc:
            raise ValueError("Location not found.")
        target_loc_id = loc.location_id
        target_loc_name = loc.name

        self.unassign_location_app_manager(target_loc_id)

        loc.app_manager_id = app_manager_id
        self.save_location(loc)

        assigned = getattr(user, "assigned_locations", None) or []
        if target_loc_id not in assigned:
            assigned.append(target_loc_id)
        user.assigned_locations = list(set(assigned))
        if not getattr(user, "location_id", None):
            user.location_id = target_loc_id
        self.save_user(user)

        with self._connect() as conn:
            conn.execute(
                "UPDATE staff_profiles SET assigned_locations = ? WHERE user_id = ?",
                (json.dumps(user.assigned_locations), app_manager_id)
            )
            conn.commit()

        return user

    def unassign_location_app_manager(self, location_id):
        loc = self.get_location(location_id)
        target_loc_id = loc.location_id if loc else location_id
        target_loc_name = loc.name if loc else location_id

        if loc and loc.app_manager_id:
            loc.app_manager_id = None
            self.save_location(loc)

        for mgr in self.list_users(role="app_manager"):
            assigned = getattr(mgr, "assigned_locations", None) or []
            new_assigned = [
                l for l in assigned
                if l != target_loc_id and (not target_loc_name or l.lower() != target_loc_name.lower())
            ]
            if len(new_assigned) != len(assigned):
                mgr.assigned_locations = new_assigned
                if mgr.location_id in (target_loc_id, target_loc_name):
                    mgr.location_id = new_assigned[0] if new_assigned else None
                self.save_user(mgr)
                with self._connect() as conn:
                    conn.execute(
                        "UPDATE staff_profiles SET assigned_locations = ? WHERE user_id = ?",
                        (json.dumps(mgr.assigned_locations), mgr.user_id)
                    )
                    conn.commit()

    def generate_activation_token(self, user_id, email):
        import secrets, time
        token = secrets.token_urlsafe(32)
        token_id = generate_id("ACT")
        now_ts = now_string()
        exp_ts = time.time() + (7 * 24 * 3600)  # 7 days expiry
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS activation_tokens (
                    token_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    token TEXT NOT NULL UNIQUE,
                    expires_at TEXT NOT NULL,
                    used INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            # Stored hashed, like session tokens and password-reset codes, so a
            # database/backup leak cannot be used to activate a pending account.
            conn.execute(
                "INSERT INTO activation_tokens (token_id, user_id, email, token, expires_at, used, created_at) VALUES (?, ?, ?, ?, ?, 0, ?)",
                (token_id, user_id, email.strip().lower(), self._hash_activation_token(token), str(exp_ts), now_ts),
            )
        return token

    def _hash_activation_token(self, token):
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def verify_activation_token(self, token):
        import time
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS activation_tokens (
                    token_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    email TEXT NOT NULL,
                    token TEXT NOT NULL UNIQUE,
                    expires_at TEXT NOT NULL,
                    used INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            row = conn.execute(
                "SELECT * FROM activation_tokens WHERE token = ? AND used = 0",
                (self._hash_activation_token(token),),
            ).fetchone()
            if not row:
                raise ValueError("Invalid or expired activation link.")
            rec = dict(row)
            if time.time() > float(rec["expires_at"]):
                raise ValueError("Activation link has expired.")
            user = self.get_user(rec["user_id"])
            if not user:
                raise ValueError("Associated user account not found.")
            return {"user_id": user.user_id, "name": user.name, "email": user.email, "role": user.role, "valid": True}

    def complete_activation(self, token, new_password):
        from utils.passwords import validate_password_complexity, hash_password
        data = self.verify_activation_token(token)
        if not validate_password_complexity(new_password):
            raise ValueError("Password does not meet complexity requirements (min 8 chars, mixed case, number, symbol).")

        user = self.get_user(data["user_id"])
        user.password = hash_password(new_password)
        user.first_login = False
        user.status = User.STATUS_ACTIVE
        user.active = True
        user.updated_at = now_string()
        self.save_user(user)
        self._clear_login_failures(user.email.strip().lower())

        with self._connect() as conn:
            conn.execute("UPDATE activation_tokens SET used = 1 WHERE token = ?", (self._hash_activation_token(token),))
        return user

