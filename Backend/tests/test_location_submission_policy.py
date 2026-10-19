import os
import sys
import uuid
import unittest
from pathlib import Path

# Add Backend root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_db_path, _get_services_for_db
from models.location import Location
from models.user import User


class TestLocationSubmissionPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = get_db_path()
        svcs = _get_services_for_db(cls.db_path)
        cls.auth_service = svcs["auth"]
        cls.location_service = svcs["location"]
        cls.department_service = svcs["department"]
        cls.team_service = svcs["team"]
        cls.notification_service = svcs["notification"]
        cls.complaint_service = svcs["complaint"]
        cls.audit_service = svcs["audit"]
        cls.client = TestClient(app)

    def _unique_id(self):
        return uuid.uuid4().hex[:8]

    def test_01_location_model_defaults_and_sync(self):
        """Verify Location model defaults and dual-property synchronization."""
        # Hostel defaults to location_only
        loc_hostel = Location("Hostel Test", "Hostel")
        self.assertEqual(loc_hostel.complaint_submission_policy, "location_only")
        self.assertEqual(loc_hostel.public_complaint_access, "location_only")

        # Academic block defaults to everyone
        loc_acad = Location("Engineering Block", "Academic Block")
        self.assertEqual(loc_acad.complaint_submission_policy, "everyone")
        self.assertEqual(loc_acad.public_complaint_access, "everyone")

        # Explicit complaint_submission_policy
        loc_custom = Location("Special Lab", "Facility", complaint_submission_policy="location_only")
        self.assertEqual(loc_custom.complaint_submission_policy, "location_only")
        self.assertEqual(loc_custom.public_complaint_access, "location_only")

        # Backward-compat: explicit public_complaint_access
        loc_compat = Location("Auditorium", "Hall", public_complaint_access="location_only")
        self.assertEqual(loc_compat.complaint_submission_policy, "location_only")
        self.assertEqual(loc_compat.public_complaint_access, "location_only")

        # Serialization to dict
        d = loc_custom.to_dict()
        self.assertIn("complaint_submission_policy", d)
        self.assertIn("public_complaint_access", d)
        self.assertEqual(d["complaint_submission_policy"], "location_only")

    def test_02_location_service_crud_and_persistence(self):
        """Verify service layer creation, update, and database roundtrip."""
        uid = self._unique_id()
        loc = self.location_service.create_location(
            name=f"Library Wing {uid}",
            location_type="Library",
            complaint_submission_policy="location_only",
        )
        self.assertIsNotNone(loc)
        self.assertEqual(loc.complaint_submission_policy, "location_only")

        # Fetch fresh from repository
        fetched = self.location_service.get_location(loc.location_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.complaint_submission_policy, "location_only")
        self.assertEqual(fetched.public_complaint_access, "location_only")

        # Update policy to everyone
        updated = self.location_service.update_location(
            loc.location_id,
            complaint_submission_policy="everyone",
        )
        self.assertEqual(updated.complaint_submission_policy, "everyone")
        self.assertEqual(updated.public_complaint_access, "everyone")

        # Fetch fresh again
        fetched_after = self.location_service.get_location(loc.location_id)
        self.assertEqual(fetched_after.complaint_submission_policy, "everyone")

        # Invalid policy value validation
        with self.assertRaises(ValueError):
            self.location_service.create_location(
                name=f"Invalid Loc {uid}",
                complaint_submission_policy="invalid_option",
            )

        with self.assertRaises(ValueError):
            self.location_service.update_location(
                loc.location_id,
                complaint_submission_policy="disallowed_value",
            )

    def test_03_enforcement_option_a_allow_everyone(self):
        """Option A (everyone): Residents, non-residents, and unassigned students can all submit."""
        uid = self._unique_id()
        loc_open = self.location_service.create_location(
            name=f"Open Cafeteria {uid}",
            location_type="Cafeteria",
            complaint_submission_policy="everyone",
        )
        dept = self.department_service.create_department(
            name=f"Cafeteria Services {uid}",
            sla_days=2,
            complaint_types=["Hygiene", "General"],
            location_id=loc_open.location_id,
        )

        # Student 1: Assigned to Open Cafeteria
        student_resident = self.auth_service.create_user(
            name=f"Resident {uid}",
            email=f"res_{uid}@test.edu",
            password="Password123!",
            role="student",
            location_id=loc_open.location_id,
        )

        # Student 2: Assigned elsewhere
        student_outsider = self.auth_service.create_user(
            name=f"Outsider {uid}",
            email=f"out_{uid}@test.edu",
            password="Password123!",
            role="student",
            location_id="OTHER_LOCATION_ID",
            hostel="Other Hostel",
        )

        # Student 3: No location assigned
        student_unassigned = self.auth_service.create_user(
            name=f"Unassigned {uid}",
            email=f"unassigned_{uid}@test.edu",
            password="Password123!",
            role="student",
            location_id=None,
        )

        # 1. Resident submits -> SUCCESS
        c1 = self.complaint_service.create_complaint(
            user=student_resident,
            location_id=loc_open.location_id,
            department_id=dept.department_id,
            complaint_type="Hygiene",
            description="Resident issue report",
            visibility_type="Community",
        )
        self.assertIsNotNone(c1)

        # 2. Outsider submits -> SUCCESS
        c2 = self.complaint_service.create_complaint(
            user=student_outsider,
            location_id=loc_open.location_id,
            department_id=dept.department_id,
            complaint_type="Hygiene",
            description="Outsider issue report",
            visibility_type="Community",
        )
        self.assertIsNotNone(c2)

        # 3. Unassigned submits -> SUCCESS
        c3 = self.complaint_service.create_complaint(
            user=student_unassigned,
            location_id=loc_open.location_id,
            department_id=dept.department_id,
            complaint_type="General",
            description="Unassigned student issue report",
            visibility_type="Private",
        )
        self.assertIsNotNone(c3)

    def test_04_enforcement_option_b_allow_location_only(self):
        """Option B (location_only): Only students belonging to location can submit."""
        uid = self._unique_id()
        loc_restricted = self.location_service.create_location(
            name=f"Restricted Research Lab {uid}",
            location_type="Research Lab",
            complaint_submission_policy="location_only",
        )
        dept = self.department_service.create_department(
            name=f"Lab Equipment {uid}",
            sla_days=1,
            complaint_types=["Hardware", "Safety"],
            location_id=loc_restricted.location_id,
        )

        # Student assigned to this lab
        student_member = self.auth_service.create_user(
            name=f"Lab Member {uid}",
            email=f"member_{uid}@test.edu",
            password="Password123!",
            role="student",
            location_id=loc_restricted.location_id,
        )

        # Student assigned elsewhere
        student_non_member = self.auth_service.create_user(
            name=f"Non Member {uid}",
            email=f"nonmember_{uid}@test.edu",
            password="Password123!",
            role="student",
            location_id="DIFFERENT_LOC_ID",
            hostel="Different Hostel",
        )

        # Student with no location
        student_unassigned = self.auth_service.create_user(
            name=f"No Loc {uid}",
            email=f"noloc_{uid}@test.edu",
            password="Password123!",
            role="student",
            location_id=None,
        )

        # 1. Member can submit
        c_ok = self.complaint_service.create_complaint(
            user=student_member,
            location_id=loc_restricted.location_id,
            department_id=dept.department_id,
            complaint_type="Hardware",
            description="Lab member report",
            visibility_type="Community",
        )
        self.assertIsNotNone(c_ok)

        # 2. Non-member rejected with PermissionError
        with self.assertRaises(PermissionError) as ctx1:
            self.complaint_service.create_complaint(
                user=student_non_member,
                location_id=loc_restricted.location_id,
                department_id=dept.department_id,
                complaint_type="Hardware",
                description="Non member unauthorized submission",
                visibility_type="Community",
            )
        self.assertIn("only accepts complaints from residents or assigned students", str(ctx1.exception))

        # 3. Unassigned student rejected with PermissionError
        with self.assertRaises(PermissionError) as ctx2:
            self.complaint_service.create_complaint(
                user=student_unassigned,
                location_id=loc_restricted.location_id,
                department_id=dept.department_id,
                complaint_type="Safety",
                description="Unassigned student unauthorized submission",
                visibility_type="Private",
            )
        self.assertIn("only accepts complaints from residents or assigned students", str(ctx2.exception))

    def test_05_hostel_configured_with_option_a_allows_all(self):
        """If an admin explicitly sets a Hostel's policy to 'everyone', non-residents must be allowed."""
        uid = self._unique_id()
        hostel_open = self.location_service.create_location(
            name=f"Open Hostel Gamma {uid}",
            location_type="Hostel",
            complaint_submission_policy="everyone",
        )
        dept = self.department_service.create_department(
            name=f"Hostel Repairs {uid}",
            sla_days=2,
            complaint_types=["Plumbing"],
            location_id=hostel_open.location_id,
        )

        student_outsider = self.auth_service.create_user(
            name=f"Hostel Outsider {uid}",
            email=f"hostel_out_{uid}@test.edu",
            password="Password123!",
            role="student",
            location_id="OTHER_HOSTEL_ID",
            hostel="Other Hostel Delta",
        )

        # Submitting to open hostel must succeed for non-resident
        c_open = self.complaint_service.create_complaint(
            user=student_outsider,
            location_id=hostel_open.location_id,
            department_id=dept.department_id,
            complaint_type="Plumbing",
            description="Non resident reporting common water tank issue in Gamma",
            visibility_type="Community",
        )
        self.assertIsNotNone(c_open)
        self.assertEqual(c_open.location_id, hostel_open.location_id)

    def test_06_non_student_roles_not_blocked_by_student_policy(self):
        """Staff roles (warden / location in charge) can report issues at restricted locations."""
        uid = self._unique_id()
        loc_res = self.location_service.create_location(
            name=f"Restricted Facility {uid}",
            location_type="Facility",
            complaint_submission_policy="location_only",
        )
        dept = self.department_service.create_department(
            name=f"Facility Ops {uid}",
            sla_days=1,
            complaint_types=["Repair"],
            location_id=loc_res.location_id,
        )

        warden = self.auth_service.create_user(
            name=f"Warden Staff {uid}",
            email=f"warden_{uid}@test.edu",
            password="Password123!",
            role="location_in_charge",
            location_id="ANOTHER_FACILITY",
        )

        c_staff = self.complaint_service.create_complaint(
            user=warden,
            location_id=loc_res.location_id,
            department_id=dept.department_id,
            complaint_type="Repair",
            description="Staff inspection issue",
        )
        self.assertIsNotNone(c_staff)

    def test_07_api_router_enforces_http_403(self):
        """Test FastAPI router directly: non-resident receives HTTP 403 Forbidden on location_only."""
        uid = self._unique_id()
        loc_restricted = self.location_service.create_location(
            name=f"API Restricted Zone {uid}",
            location_type="Hostel",
            complaint_submission_policy="location_only",
        )
        dept = self.department_service.create_department(
            name=f"Zone Maintenance {uid}",
            sla_days=2,
            complaint_types=["Electrical"],
            location_id=loc_restricted.location_id,
        )

        # Create non-resident student and generate auth token
        pwd = "Password123!"
        student = self.auth_service.create_user(
            name=f"API Student {uid}",
            email=f"api_stu_{uid}@test.edu",
            password=pwd,
            role="student",
            location_id="DIFFERENT_ZONE",
        )
        student.first_login = False
        student.must_change_password = False
        self.auth_service.save_user(student)
        login_res = self.client.post(
            "/auth/login",
            json={"username": student.email, "password": pwd},
        )
        self.assertEqual(login_res.status_code, 200)
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Post to restricted location -> Expect 403
        payload_fail = {
            "title": "Broken light",
            "description": "Corridor light flickering continuously",
            "department_id": dept.department_id,
            "location_id": loc_restricted.location_id,
            "complaint_type": "Electrical",
            "visibility_type": "Community",
        }
        res_fail = self.client.post("/complaints", json=payload_fail, headers=headers)
        self.assertEqual(res_fail.status_code, 403)
        self.assertIn("only accepts complaints from residents or assigned students", res_fail.json()["detail"])

        # 2. Update location to 'everyone' -> Now same student's request must succeed with 201
        self.location_service.update_location(
            loc_restricted.location_id,
            complaint_submission_policy="everyone",
        )
        res_ok = self.client.post("/complaints", json=payload_fail, headers=headers)
        self.assertEqual(res_ok.status_code, 201)
        self.assertEqual(res_ok.json()["location_id"], loc_restricted.location_id)

    def test_08_separation_of_concerns_and_workflows(self):
        """Separation of concerns: submission policy does not interfere with visibility or endorsement."""
        uid = self._unique_id()
        loc = self.location_service.create_location(
            name=f"Separation Test Arena {uid}",
            location_type="Facility",
            complaint_submission_policy="everyone",
        )
        dept = self.department_service.create_department(
            name=f"Arena Ops {uid}",
            sla_days=2,
            complaint_types=["A/C"],
            location_id=loc.location_id,
        )

        student_author = self.auth_service.create_user(
            name=f"Author {uid}",
            email=f"author_{uid}@test.edu",
            password="Password123!",
            role="student",
            location_id="ANOTHER_LOC",
        )
        student_author.first_login = False
        self.auth_service.save_user(student_author)

        # 1. Author submits a Community complaint at everyone location
        c_pub = self.complaint_service.create_complaint(
            user=student_author,
            location_id=loc.location_id,
            department_id=dept.department_id,
            complaint_type="A/C",
            description="Arena AC not cooling",
            visibility_type="Community",
        )
        self.assertEqual(c_pub.visibility_type, "Community")

        # 2. Endorsement works independently of submission policy
        student_other = self.auth_service.create_user(
            name=f"Endorser {uid}",
            email=f"endorser_{uid}@test.edu",
            password="Password123!",
            role="student",
            location_id="THIRD_LOC",
        )
        self.complaint_service.add_affected_student(c_pub.complaint_id, student_other.user_id, "Also feeling heat")
        affected_count = self.complaint_service.get_affected_count(c_pub.complaint_id)
        self.assertEqual(affected_count, 1)

        # 3. Private complaint retains private visibility
        c_priv = self.complaint_service.create_complaint(
            user=student_author,
            location_id=loc.location_id,
            department_id=dept.department_id,
            complaint_type="A/C",
            description="Private Arena issue",
            visibility_type="Private",
        )
        self.assertEqual(c_priv.visibility_type, "Private")


if __name__ == "__main__":
    unittest.main()
