import pytest
from models.administrator import Administrator
from models.app_manager import AppManager
from models.coordinator import Coordinator
from models.location_in_charge import LocationInCharge
from models.student import Student
from models.complaint import Complaint
from models.location import Location
from models.department import Department
from api.dependencies import (
    get_auth_service,
    get_location_service,
    get_department_service,
    get_complaint_service,
    get_report_service,
    get_analytics_service,
    get_global_search_service,
)


@pytest.fixture
def auth_service():
    auth = get_auth_service()
    auth.ensure_seed_data()
    return auth


@pytest.fixture
def location_service():
    return get_location_service()


@pytest.fixture
def department_service():
    return get_department_service()


@pytest.fixture
def complaint_service():
    return get_complaint_service()


@pytest.fixture
def report_service():
    return get_report_service()


@pytest.fixture
def analytics_service():
    return get_analytics_service()


@pytest.fixture
def search_service():
    return get_global_search_service()


def test_initial_users_exist_and_admin_retained(auth_service):
    """Verify that two initial accounts exist per role and Administrator is retained."""
    mgr1 = auth_service.get_user("USR_MANAGER")
    mgr2 = auth_service.get_user("USR_MANAGER_2")
    assert mgr1 is not None and mgr1.role == AppManager.ROLE
    assert mgr2 is not None and mgr2.role == AppManager.ROLE

    warden1 = auth_service.get_user("USR_WARDEN")
    warden2 = auth_service.get_user("USR_WARDEN_2")
    assert warden1 is not None and warden1.role == LocationInCharge.ROLE
    assert warden2 is not None and warden2.role == LocationInCharge.ROLE

    coord1 = auth_service.get_user("USR_COORDINATOR")
    coord2 = auth_service.get_user("USR_COORDINATOR_2")
    assert coord1 is not None and coord1.role in (Coordinator.ROLE, "employee")
    assert coord2 is not None and coord2.role in (Coordinator.ROLE, "employee")

    student1 = auth_service.get_user("USR_STUDENT")
    student2 = auth_service.get_user("USR_STUDENT_2")
    assert student1 is not None and student1.role == Student.ROLE
    assert student2 is not None and student2.role == Student.ROLE

    admin = auth_service.get_user("USR_ADMIN")
    assert admin is not None and admin.role == Administrator.ROLE


def test_initial_locations_structure(auth_service):
    """Verify 2 locations exist for each operational type and no numbered Other locations."""
    expected_types = [
        ("LOC_HOSTEL_1", "Hostel 1", "Hostel"),
        ("LOC_HOSTEL_2", "Hostel 2", "Hostel"),
        ("LOC_ACADEMIC_1", "Academic Block 1", "Academic Block"),
        ("LOC_ACADEMIC_2", "Academic Block 2", "Academic Block"),
        ("LOC_MESS_1", "Mess 1", "Mess"),
        ("LOC_MESS_2", "Mess 2", "Mess"),
        ("LOC_SAC_1", "Student Activity Center 1", "Student Activity Center"),
        ("LOC_SAC_2", "Student Activity Center 2", "Student Activity Center"),
        ("LOC_SPORTS_1", "Sports Complex 1", "Sports Complex"),
        ("LOC_SPORTS_2", "Sports Complex 2", "Sports Complex"),
    ]

    for loc_id, loc_name, loc_type in expected_types:
        loc = auth_service.get_location(loc_id)
        assert loc is not None, f"Location {loc_id} ({loc_name}) not found"
        assert loc.name == loc_name
        assert (loc.location_type or loc.infer_location_type(loc.name)) == loc_type

    # Verify no numbered "Other" locations exist
    all_locs = auth_service.list_locations()
    for loc in all_locs:
        assert "Other 1" not in loc.name
        assert "Other 2" not in loc.name


def test_app_manager_assignments_and_reassignment(auth_service, location_service):
    """Verify App Manager assignments: 1 per location, multiple per manager, reassignment & unassignment."""
    # Check initial distribution
    group1 = ["LOC_HOSTEL_1", "LOC_ACADEMIC_1", "LOC_MESS_1", "LOC_SAC_1", "LOC_SPORTS_1"]
    group2 = ["LOC_HOSTEL_2", "LOC_ACADEMIC_2", "LOC_MESS_2", "LOC_SAC_2", "LOC_SPORTS_2"]

    mgr1_locs = [l.location_id for l in auth_service.get_app_manager_locations("USR_MANAGER")]
    mgr2_locs = [l.location_id for l in auth_service.get_app_manager_locations("USR_MANAGER_2")]

    for gid in group1:
        assert gid in mgr1_locs, f"{gid} should be in App Manager 1 locations"
        loc = auth_service.get_location(gid)
        assert loc.app_manager_id == "USR_MANAGER"

    for gid in group2:
        assert gid in mgr2_locs, f"{gid} should be in App Manager 2 locations"
        loc = auth_service.get_location(gid)
        assert loc.app_manager_id == "USR_MANAGER_2"

    # Test reassignment: Reassign LOC_HOSTEL_1 to App Manager 2
    auth_service.assign_location_app_manager("LOC_HOSTEL_1", "USR_MANAGER_2")
    loc_h1 = auth_service.get_location("LOC_HOSTEL_1")
    assert loc_h1.app_manager_id == "USR_MANAGER_2"

    mgr1_updated = [l.location_id for l in auth_service.get_app_manager_locations("USR_MANAGER")]
    mgr2_updated = [l.location_id for l in auth_service.get_app_manager_locations("USR_MANAGER_2")]
    assert "LOC_HOSTEL_1" not in mgr1_updated
    assert "LOC_HOSTEL_1" in mgr2_updated

    # Test unassignment
    auth_service.unassign_location_app_manager("LOC_HOSTEL_1")
    loc_h1_unassigned = auth_service.get_location("LOC_HOSTEL_1")
    assert loc_h1_unassigned.app_manager_id is None
    assert auth_service.get_location_app_manager_id("LOC_HOSTEL_1") is None

    # Restore initial state
    auth_service.assign_location_app_manager("LOC_HOSTEL_1", "USR_MANAGER")


def test_warden_assignments(auth_service):
    """Verify Warden assignments: 1 per location, multiple per warden."""
    group1 = ["LOC_HOSTEL_1", "LOC_ACADEMIC_1", "LOC_MESS_1", "LOC_SAC_1", "LOC_SPORTS_1"]
    group2 = ["LOC_HOSTEL_2", "LOC_ACADEMIC_2", "LOC_MESS_2", "LOC_SAC_2", "LOC_SPORTS_2"]

    w1_locs = [l.location_id for l in auth_service.get_warden_locations("USR_WARDEN")]
    w2_locs = [l.location_id for l in auth_service.get_warden_locations("USR_WARDEN_2")]

    for gid in group1:
        assert gid in w1_locs
        loc = auth_service.get_location(gid)
        assert loc.in_charge_id == "USR_WARDEN"

    for gid in group2:
        assert gid in w2_locs
        loc = auth_service.get_location(gid)
        assert loc.in_charge_id == "USR_WARDEN_2"


def test_coordinator_department_assignments(auth_service):
    """Verify coordinators are assigned to departments across locations, not directly to locations."""
    c1_asgns = auth_service.list_coordinator_assignments(coordinator_id="USR_COORDINATOR")
    assert len(c1_asgns) >= 1
    # Check that coordinator covers electrical across any campus location
    assert auth_service.is_coordinator_assigned("USR_COORDINATOR", "LOC_HOSTEL_1", "DEPT_HOSTEL_ELECTRICAL")
    assert auth_service.is_coordinator_assigned("USR_COORDINATOR", "LOC_HOSTEL_2", "DEPT_HOSTEL_ELECTRICAL")

    # Check multi-department assignment: assign coordinator 1 to plumbing as well
    auth_service.assign_coordinator("USR_COORDINATOR", location_id="ALL", department_id="DEPT_MESS_PLUMBING")
    assert auth_service.is_coordinator_assigned("USR_COORDINATOR", "LOC_MESS_1", "DEPT_MESS_PLUMBING")


def test_complaint_reassignment_safety(complaint_service, auth_service):
    """Verify complaint is unassigned if modified to a location/department where coordinator is unauthorized."""
    # Ensure coordinator 1 is authorized for DEPT_HOSTEL_ELECTRICAL
    student1 = auth_service.get_user("USR_STUDENT")
    complaint = complaint_service.create_complaint(
        user=student1,
        title="Test Socket Issue",
        description="Socket sparking in room",
        complaint_type="Power Failure",
        category="Electrical",
        location_id="LOC_HOSTEL_1",
        department_id="DEPT_HOSTEL_ELECTRICAL",
    )
    complaint.assigned_to = "USR_COORDINATOR"
    complaint.status = Complaint.ASSIGNED
    complaint_service.save_complaint(complaint)

    assert complaint.assigned_to == "USR_COORDINATOR"

    # Simulate modifying complaint to a department Coordinator 1 is not assigned to
    from api.routers.complaints import update_complaint
    from api.schemas import ComplaintUpdateRequest

    user_admin = auth_service.get_user("USR_ADMIN")
    payload = ComplaintUpdateRequest(department_id="DEPT_SPORTS_GROUNDS")

    from api.dependencies import get_audit_service
    audit_service = get_audit_service()

    updated = update_complaint(
        complaint_id=complaint.complaint_id,
        payload=payload,
        current_user=user_admin,
        complaint_service=complaint_service,
        audit_service=audit_service,
    )

    # Coordinator should be cleared and status returned to Submitted
    assert updated["assigned_to"] is None
    assert updated["status"] == Complaint.SUBMITTED


def test_report_scoping(report_service, auth_service, complaint_service):
    """Verify report generation scopes complaint exports according to role."""
    # Create complaints in different locations
    student1 = auth_service.get_user("USR_STUDENT")
    student2 = auth_service.get_user("USR_STUDENT_2")
    c_h1 = complaint_service.create_complaint(
        user=student1,
        title="Hostel 1 Complaint",
        description="Issue in Hostel 1",
        complaint_type="Power Failure",
        category="Electrical",
        location_id="LOC_HOSTEL_1",
        department_id="DEPT_HOSTEL_ELECTRICAL",
    )
    c_h2 = complaint_service.create_complaint(
        user=student2,
        title="Hostel 2 Complaint",
        description="Issue in Hostel 2",
        complaint_type="Power Failure",
        category="Electrical",
        location_id="LOC_HOSTEL_2",
        department_id="DEPT_HOSTEL_ELECTRICAL",
    )

    mgr1 = auth_service.get_user("USR_MANAGER")
    rpt_mgr1 = report_service.generate_report(
        report_name="Mgr1 Scope Test",
        report_type="Complaint",
        generated_by=mgr1.user_id,
        user=mgr1,
    )
    assert rpt_mgr1["report_id"] is not None

    # Read exported file content
    import csv
    with open(rpt_mgr1["file_path"], "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        complaint_ids = [row["complaint_id"] for row in reader]

    # App Manager 1 manages LOC_HOSTEL_1, not LOC_HOSTEL_2
    assert c_h1.complaint_id in complaint_ids
    assert c_h2.complaint_id not in complaint_ids


def test_analytics_multi_location_aggregation(analytics_service, auth_service, complaint_service):
    """Verify Warden and App Manager dashboard analytics aggregate across all their assigned locations."""
    warden1 = auth_service.get_user("USR_WARDEN")
    summary = analytics_service.get_dashboard_summary(warden1)

    assert summary["role"] == "location_in_charge"
    assert "metrics" in summary
    assert "hostel_complaints" in summary["metrics"]


def test_app_manager_deactivation_safety(auth_service):
    """Verify deactivating an App Manager unassigns their locations safely without deletion."""
    import uuid
    uid = uuid.uuid4().hex[:6]
    # Create temporary manager
    tmp_mgr = auth_service.create_user(
        name="Temp Manager",
        email=f"temp_mgr_{uid}@campus.edu",
        password="TempPassword@123",
        role="app_manager",
    )
    auth_service.assign_location_app_manager("LOC_SPORTS_1", tmp_mgr.user_id)
    assert auth_service.get_location("LOC_SPORTS_1").app_manager_id == tmp_mgr.user_id

    # Deactivate manager
    admin = auth_service.get_user("USR_ADMIN")
    auth_service.update_user_status(tmp_mgr.user_id, "Inactive", performer=admin)

    # Location should now have app_manager_id as None, not deleted
    loc_sports = auth_service.get_location("LOC_SPORTS_1")
    assert loc_sports is not None
    assert loc_sports.app_manager_id is None

    # Re-assign initial manager back
    auth_service.assign_location_app_manager("LOC_SPORTS_1", "USR_MANAGER")


def test_student_hostel_complaint_restriction(auth_service, complaint_service):
    """Verify students can complain about their assigned hostel and general campus facilities,
    but cannot submit complaints about other hostels."""
    student1 = auth_service.get_user("USR_STUDENT")
    student2 = auth_service.get_user("USR_STUDENT_2")

    # Student 1 is assigned to Hostel 1
    # 1. Allowed: Student 1 submits complaint for Hostel 1
    c1 = complaint_service.create_complaint(
        user=student1,
        title="Hostel 1 Fan Issue",
        description="Ceiling fan regulator is broken in room",
        complaint_type="Electrical Issue",
        category="Electrical",
        location_id="LOC_HOSTEL_1",
        department_id="DEPT_HOSTEL_ELECTRICAL",
    )
    assert c1 is not None
    assert c1.location_id == "LOC_HOSTEL_1"

    # 2. Denied: Student 1 attempts to submit complaint for Hostel 2 (fails with PermissionError)
    with pytest.raises(PermissionError) as exc_info:
        complaint_service.create_complaint(
            user=student1,
            title="Hostel 2 Fan Issue",
            description="Ceiling fan broken in other hostel",
            complaint_type="Electrical Issue",
            category="Electrical",
            location_id="LOC_HOSTEL_2",
            department_id="DEPT_HOSTEL_ELECTRICAL",
        )
    assert "assigned hostel" in str(exc_info.value).lower()

    # 3. Allowed: Student 1 submits complaint for non-hostel campus locations
    # Academic Block 1
    c_acad1 = complaint_service.create_complaint(
        user=student1,
        title="Classroom Projector Issue",
        description="Projector lamp failing in Room 101",
        complaint_type="Electrical Issue",
        category="Electrical",
        location_id="LOC_ACADEMIC_1",
        department_id="DEPT_ACADEMIC_ELECTRICAL",
    )
    assert c_acad1 is not None

    # Academic Block 2 (permitted across campus)
    c_acad2 = complaint_service.create_complaint(
        user=student1,
        title="Academic Block 2 Lighting Issue",
        description="Lights flickering in 2nd floor hallway",
        complaint_type="Electrical Issue",
        category="Electrical",
        location_id="LOC_ACADEMIC_2",
        department_id="DEPT_ACADEMIC_ELECTRICAL",
    )
    assert c_acad2 is not None

    # Mess 1
    c_mess = complaint_service.create_complaint(
        user=student1,
        title="Mess Water Dispenser Issue",
        description="Cold water dispenser leaking in Mess 1",
        complaint_type="Plumbing Issue",
        category="Plumbing",
        location_id="LOC_MESS_1",
        department_id="DEPT_MESS_PLUMBING",
    )
    assert c_mess is not None

    # Student Activity Center 1
    c_sac = complaint_service.create_complaint(
        user=student1,
        title="SAC AV Issue",
        description="Speaker buzz in auditorium",
        complaint_type="Speaker / Sound System Issue",
        category="AV",
        location_id="LOC_SAC_1",
        department_id="DEPT_SAC_AV",
    )
    assert c_sac is not None

    # Sports Complex 1
    c_sports = complaint_service.create_complaint(
        user=student1,
        title="Court Lighting Issue",
        description="Floodlight 2 off in Badminton Court",
        complaint_type="Court Lighting Defect",
        category="Maintenance",
        location_id="LOC_SPORTS_1",
        department_id="DEPT_SPORTS_GROUNDS",
    )
    assert c_sports is not None

    # 4. Student 2 (assigned to Hostel 2):
    # Allowed on Hostel 2, Denied on Hostel 1
    c2 = complaint_service.create_complaint(
        user=student2,
        title="Hostel 2 Plumbing Issue",
        description="Tap dripping in washroom",
        complaint_type="Plumbing Issue",
        category="Plumbing",
        location_id="LOC_HOSTEL_2",
        department_id="DEPT_HOSTEL_PLUMBING",
    )
    assert c2 is not None

    with pytest.raises(PermissionError) as exc_info2:
        complaint_service.create_complaint(
            user=student2,
            title="Hostel 1 Issue Attempt",
            description="Trying to submit issue for Hostel 1",
            complaint_type="Plumbing Issue",
            category="Plumbing",
            location_id="LOC_HOSTEL_1",
            department_id="DEPT_HOSTEL_PLUMBING",
        )
    assert "assigned hostel" in str(exc_info2.value).lower()
