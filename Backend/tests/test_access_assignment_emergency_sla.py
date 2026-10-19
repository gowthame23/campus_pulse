import os
import sys
import unittest
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.dependencies import get_db_path, _get_services_for_db
from models.user import User
from models.student import Student
from models.coordinator import Coordinator
from models.administrator import Administrator
from models.app_manager import AppManager
from models.location_in_charge import LocationInCharge
from models.complaint import Complaint
from api.routers.complaints import _format_complaint, is_complaint_visible, _get_critical_emergency_contacts
from api.schemas import DepartmentSlaConfigUpdateRequest
from api.routers.departments import update_department_sla_config
from fastapi import HTTPException


class TestAccessAssignmentEmergencySLA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = get_db_path()
        svcs = _get_services_for_db(path)
        cls.auth_service = svcs["auth"]
        cls.location_service = svcs["location"]
        cls.department_service = svcs["department"]
        cls.team_service = svcs["team"]
        cls.notification_service = svcs["notification"]
        cls.complaint_service = svcs["complaint"]
        cls.audit_service = svcs["audit"]
        cls.repo = cls.auth_service.repository

    def test_01_location_public_complaint_access(self):
        """Test public complaint access Option A (everyone) vs Option B (location_only)."""
        import uuid
        uid = uuid.uuid4().hex[:6]
        # Create test locations
        loc_a = self.location_service.create_location(
            name=f"Hostel Alpha {uid}",
            location_type="Hostel",
            public_complaint_access="location_only",
        )
        loc_b = self.location_service.create_location(
            name=f"Academic Block {uid}",
            location_type="Academic Block",
            public_complaint_access="everyone",
        )
        dept = self.department_service.create_department(
            name=f"Maintenance {uid}",
            sla_days=2,
            complaint_types=["General"],
        )
        self.department_service.assign_locations_to_department(dept.department_id, [loc_a.location_id, loc_b.location_id])

        # Create students: Student A assigned to Hostel Alpha, Student B assigned to another location
        student_a = self.auth_service.create_user(
            name="Student A",
            email=f"student_a_{uid}@test.edu",
            password="Password123!",
            role="student",
            location_id=loc_a.location_id,
            hostel=f"Hostel Alpha {uid}",
        )
        student_b = self.auth_service.create_user(
            name="Student B",
            email=f"student_b_{uid}@test.edu",
            password="Password123!",
            role="student",
            location_id="OTHER_LOC",
            hostel="Hostel Other",
        )

        # 1. Student A can submit community complaint to Hostel Alpha (their location)
        c1 = self.complaint_service.create_complaint(
            user=student_a,
            location_id=loc_a.location_id,
            department_id=dept.department_id,
            complaint_type="General",
            description="Alpha hostel water issue",
            visibility_type="Community",
        )
        self.assertIsNotNone(c1)

        # 2. Student B submitting community complaint to Hostel Alpha (location_only) must FAIL
        with self.assertRaises(PermissionError) as ctx:
            self.complaint_service.create_complaint(
                user=student_b,
                location_id=loc_a.location_id,
                department_id=dept.department_id,
                complaint_type="General",
                description="Student B trying to report alpha hostel",
                visibility_type="Community",
            )
        self.assertIn("only accepts complaints from residents or assigned students", str(ctx.exception))

        # 3. Student A and Student B can BOTH submit community complaints to Academic Block Beta (everyone)
        c2 = self.complaint_service.create_complaint(
            user=student_b,
            location_id=loc_b.location_id,
            department_id=dept.department_id,
            complaint_type="General",
            description="Beta academic block broken chair",
            visibility_type="Community",
        )
        self.assertIsNotNone(c2)

    def test_02_assigned_employee_visibility_and_formatting(self):
        """Test that unassigned complaints show 'Awaiting assignment' and assigned complaints show employee name."""
        import uuid
        uid = uuid.uuid4().hex[:6]
        with self.auth_service._connect() as conn:
            row = conn.execute("SELECT location_id, department_id FROM location_departments WHERE is_active = 1 LIMIT 1").fetchone()
            loc_id, dept_id = row[0], row[1]
        loc = self.auth_service.get_location(loc_id)
        dept = self.auth_service.get_department(dept_id)
        student = self.auth_service.list_users(role="student")[0]

        # Create a submitted complaint
        c = self.complaint_service.create_complaint(
            user=student,
            location_id=loc.location_id,
            department_id=dept.department_id,
            complaint_type="General",
            description=f"Visibility test complaint {uid}",
            visibility_type="Community",
        )

        # Unassigned check
        formatted = _format_complaint(c, self.complaint_service)
        self.assertEqual(formatted.get("assigned_employee_name"), "Awaiting assignment")
        self.assertEqual(formatted.get("assigned_to_name"), "Awaiting assignment")

        # Assign to coordinator / employee
        emp = self.auth_service.create_user(
            name="John Technician",
            email=f"tech_john_{uid}@test.edu",
            password="Password123!",
            role="employee",
            department_id=dept.department_id,
        )
        c.assigned_to = emp.user_id
        self.complaint_service.save_complaint(c)

        # Formatted check after assignment
        formatted_after = _format_complaint(c, self.complaint_service)
        self.assertEqual(formatted_after.get("assigned_employee_name"), "John Technician")
        self.assertEqual(formatted_after.get("assigned_to_name"), "John Technician")

    def test_03_critical_emergency_contacts(self):
        """Test emergency contacts resolution for Critical complaints vs non-critical."""
        import uuid
        uid = uuid.uuid4().hex[:6]
        with self.auth_service._connect() as conn:
            row = conn.execute("SELECT location_id, department_id FROM location_departments WHERE is_active = 1 LIMIT 1").fetchone()
            loc_id, dept_id = row[0], row[1]
        loc = self.auth_service.get_location(loc_id)
        dept = self.auth_service.get_department(dept_id)
        student = self.auth_service.list_users(role="student")[0]

        import random
        phone_num = f"98{random.randint(10000000, 99999999)}"
        # Assign warden to location with phone
        warden = self.auth_service.create_user(
            name="Chief Warden Smith",
            email=f"warden_smith_{uid}@test.edu",
            password="Password123!",
            role="location_in_charge",
            phone_number=phone_num,
        )
        self.location_service.update_location(loc.location_id, in_charge_id=warden.user_id)

        # Non-critical complaint -> emergency_contacts should be empty
        c_norm = self.complaint_service.create_complaint(
            user=student,
            location_id=loc.location_id,
            department_id=dept.department_id,
            complaint_type="General",
            description=f"Normal complaint test {uid}",
            priority="Normal",
        )
        contacts_norm = _get_critical_emergency_contacts(c_norm, self.complaint_service)
        self.assertEqual(len(contacts_norm), 0)

        # Critical complaint -> emergency_contacts should be populated with direct phone info
        c_crit = self.complaint_service.create_complaint(
            user=student,
            location_id=loc.location_id,
            department_id=dept.department_id,
            complaint_type="General",
            description=f"Critical complaint power line sparks {uid}",
            priority="Critical",
        )
        contacts_crit = _get_critical_emergency_contacts(c_crit, self.complaint_service)
        self.assertGreater(len(contacts_crit), 0)

        warden_contact = next((ct for ct in contacts_crit if "Warden" in ct["role"]), None)
        self.assertIsNotNone(warden_contact)
        self.assertEqual(warden_contact["name"], "Chief Warden Smith")
        self.assertEqual(warden_contact["phone"], phone_num)
        self.assertTrue(warden_contact["phone_available"])

    def test_04_department_sla_config_and_escalation_ordering_rule(self):
        """Test SLA configuration and mandatory escalation ordering rule: App Manager < Admin strictly."""
        import uuid
        uid = uuid.uuid4().hex[:6]
        dept = self.department_service.create_department(
            name=f"SLA Test Dept {uid}",
            sla_days=3,
            complaint_types=["General"],
            location_id=None,
        )

        # Default SLA config
        default_cfg = self.repo.get_department_sla_config(dept.department_id)
        self.assertIsNotNone(default_cfg)
        self.assertEqual(default_cfg["normal_duration_hours"], 72)
        self.assertEqual(default_cfg["critical_duration_hours"], 4)
        self.assertEqual(default_cfg["app_manager_escalation_hours"], 24)
        self.assertEqual(default_cfg["admin_escalation_hours"], 48)

        # Valid update: App Manager (12h) < Admin (24h)
        valid_data = {
            "department_id": dept.department_id,
            "normal_start_time": "08:00",
            "normal_end_time": "18:00",
            "normal_duration_hours": 60,
            "medium_start_time": "08:00",
            "medium_end_time": "18:00",
            "medium_duration_hours": 36,
            "high_start_time": "08:00",
            "high_end_time": "20:00",
            "high_duration_hours": 18,
            "critical_start_time": "00:00",
            "critical_end_time": "23:59",
            "critical_duration_hours": 2,
            "app_manager_escalation_hours": 12,
            "admin_escalation_hours": 24,
            "updated_by": "USR_ADMIN",
        }
        saved = self.repo.save_department_sla_config(valid_data)
        self.assertEqual(saved["app_manager_escalation_hours"], 12)
        self.assertEqual(saved["admin_escalation_hours"], 24)
        self.assertEqual(saved["critical_duration_hours"], 2)

        # Verify router endpoint validation rule via update_department_sla_config
        admin_user = self.auth_service.list_users(role="administrator")[0]

        # Case: app_manager >= admin -> MUST raise HTTPException 400 with exact message
        invalid_payload = DepartmentSlaConfigUpdateRequest(
            app_manager_escalation_hours=36,
            admin_escalation_hours=24,
        )
        with self.assertRaises(HTTPException) as ctx:
            update_department_sla_config(
                department_id=dept.department_id,
                payload=invalid_payload,
                current_user=admin_user,
                department_service=self.department_service,
                audit_service=self.audit_service,
            )
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(
            ctx.exception.detail,
            "App Manager escalation time must be less than Admin escalation time.",
        )

        # Case: App Manager attempts to change admin_escalation_hours -> MUST raise 403 Forbidden
        app_mgr_user = self.auth_service.list_users(role="app_manager")
        if app_mgr_user:
            mgr = app_mgr_user[0]
            tamper_payload = DepartmentSlaConfigUpdateRequest(
                app_manager_escalation_hours=10,
                admin_escalation_hours=99,
            )
            with self.assertRaises(HTTPException) as ctx_tamper:
                update_department_sla_config(
                    department_id=dept.department_id,
                    payload=tamper_payload,
                    current_user=mgr,
                    department_service=self.department_service,
                    audit_service=self.audit_service,
                )
            self.assertEqual(ctx_tamper.exception.status_code, 403)
            self.assertEqual(
                ctx_tamper.exception.detail,
                "App Manager cannot modify Admin escalation threshold.",
            )


if __name__ == "__main__":
    unittest.main()
