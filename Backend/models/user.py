from utils.helper import now_string
from utils.passwords import hash_password, verify_password


class User:
    STATUS_ACTIVE = "Active"
    STATUS_INACTIVE = "Inactive"
    STATUS_SUSPENDED = "Suspended"
    STATUS_ARCHIVED = "Archived"
    STATUS_GRADUATED = "Graduated"
    STATUS_LEFT_COLLEGE = "Left College"
    STATUS_TRANSFERRED = "Transferred"

    def __init__(
        self,
        user_id,
        name,
        email,
        password,
        role,
        phone_number=None,
        status="Active",
        profile_photo=None,
        first_login=True,
        active=True,
        department_id=None,
        location_id=None,
        created_at=None,
        updated_at=None,
        last_login=None,
        last_logout=None,
        created_by="system",
        is_deleted=False,
        deleted_at=None,
        deleted_by=None,
        deactivated_by_user_id=None,
        deactivated_by_role=None,
        deactivated_at=None,
        # Student Profile Fields
        roll_number=None,
        student_department=None,
        program=None,
        year=None,
        section=None,
        hostel=None,
        block=None,
        room_number=None,
        # Staff Profile Fields
        employee_id=None,
        designation=None,
        staff_department=None,
        assigned_locations=None,
        assigned_categories=None,
        photo_skip_streak=0,
        force_next_warden_check=0,
        language="en",
        safety_blocked_until=None,
    ):
        self.user_id = user_id
        self.name = name
        self.full_name = name  # alias
        self.email = email
        self.password = password
        self.role = role
        self.phone_number = phone_number
        self.status = status or self.STATUS_ACTIVE
        self.profile_photo = profile_photo
        self.first_login = bool(first_login)
        self.is_deleted = bool(is_deleted)
        self.active = bool(active and self.status == self.STATUS_ACTIVE and not self.is_deleted)
        self.department_id = department_id
        self.location_id = location_id
        self.created_at = created_at or now_string()
        self.updated_at = updated_at or self.created_at
        self.last_login = last_login
        self.last_logout = last_logout
        self.created_by = created_by or "system"
        self.is_deleted = bool(is_deleted)
        self.deleted_at = deleted_at
        self.deleted_by = deleted_by
        self.deactivated_by_user_id = deactivated_by_user_id
        self.deactivated_by_role = deactivated_by_role
        self.deactivated_at = deactivated_at

        # Student specific
        self.roll_number = roll_number
        self.student_department = student_department
        self.program = program
        self.year = year
        self.section = section
        self.hostel = hostel
        self.block = block
        self.room_number = room_number

        # Staff specific
        self.employee_id = employee_id
        self.designation = designation
        self.staff_department = staff_department
        self.assigned_locations = assigned_locations or []
        self.assigned_categories = assigned_categories or []
        self.photo_skip_streak = int(photo_skip_streak or 0)
        self.force_next_warden_check = int(force_next_warden_check or 0)
        self.language = language or "en"
        self.safety_blocked_until = safety_blocked_until

    def check_password(self, password):
        return verify_password(password, self.password)

    def change_password(self, new_password):
        self.password = hash_password(new_password)
        self.first_login = False
        self.updated_at = now_string()

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "full_name": self.name,
            "email": self.email,
            "password": self.password,
            "role": self.role,
            "phone_number": self.phone_number,
            "phone": self.phone_number,
            "status": self.status,
            "profile_photo": self.profile_photo,
            "first_login": self.first_login,
            "active": self.active,
            "department_id": self.department_id,
            "location_id": self.location_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_login": self.last_login,
            "last_logout": self.last_logout,
            "created_by": self.created_by,
            "is_deleted": self.is_deleted,
            "deleted_at": self.deleted_at,
            "deleted_by": self.deleted_by,
            "deactivated_by_user_id": self.deactivated_by_user_id,
            "deactivated_by_role": self.deactivated_by_role,
            "deactivated_at": self.deactivated_at,
            # Student fields
            "roll_number": self.roll_number,
            "department": self.student_department or self.department_id,
            "program": self.program,
            "year": self.year,
            "section": self.section,
            "hostel": self.hostel,
            "block": self.block,
            "room_number": self.room_number,
            # Staff fields
            "employee_id": self.employee_id,
            "designation": self.designation,
            "staff_department": self.staff_department or self.department_id,
            "assigned_locations": self.assigned_locations,
            "assigned_categories": self.assigned_categories,
            "photo_skip_streak": self.photo_skip_streak,
            "force_next_warden_check": self.force_next_warden_check,
            "language": self.language,
            "safety_blocked_until": self.safety_blocked_until,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["user_id"],
            data.get("name") or data.get("full_name") or "",
            data["email"],
            data["password"],
            data["role"],
            phone_number=data.get("phone_number"),
            status=data.get("status", "Active"),
            profile_photo=data.get("profile_photo"),
            first_login=data.get("first_login", True),
            active=data.get("active", True),
            department_id=data.get("department_id"),
            location_id=data.get("location_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            last_login=data.get("last_login"),
            last_logout=data.get("last_logout"),
            created_by=data.get("created_by", "system"),
            is_deleted=data.get("is_deleted", False),
            deleted_at=data.get("deleted_at"),
            deleted_by=data.get("deleted_by"),
            deactivated_by_user_id=data.get("deactivated_by_user_id"),
            deactivated_by_role=data.get("deactivated_by_role"),
            deactivated_at=data.get("deactivated_at"),
            roll_number=data.get("roll_number"),
            student_department=data.get("department"),
            program=data.get("program"),
            year=data.get("year"),
            section=data.get("section"),
            hostel=data.get("hostel"),
            block=data.get("block"),
            room_number=data.get("room_number"),
            employee_id=data.get("employee_id"),
            designation=data.get("designation"),
            staff_department=data.get("staff_department") or data.get("department"),
            assigned_locations=data.get("assigned_locations", []),
            assigned_categories=data.get("assigned_categories", []),
            photo_skip_streak=int(data.get("photo_skip_streak", 0) or 0),
            force_next_warden_check=int(data.get("force_next_warden_check", 0) or 0),
            language=data.get("language", "en"),
            safety_blocked_until=data.get("safety_blocked_until"),
        )
