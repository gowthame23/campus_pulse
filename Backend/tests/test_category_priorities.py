import pytest
from api.dependencies import get_auth_service, get_department_service, get_complaint_service
from models.student import Student


def test_category_priorities_service():
    auth_service = get_auth_service()
    department_service = get_department_service()

    # Set default campus-wide category priority
    p = department_service.set_category_priority(
        department_id="DEPT_MAINT",
        category_name="A/C",
        priority="Critical",
        location_id="ALL",
        actor_id="admin1",
    )
    assert p == "Critical"

    # Default lookup for ALL
    priorities = department_service.get_category_priorities("DEPT_MAINT")
    assert priorities.get("A/C") == "Critical"
    assert department_service.get_effective_category_priority("DEPT_MAINT", "A/C") == "Critical"

    # Set location-specific override
    department_service.set_category_priority(
        department_id="DEPT_MAINT",
        category_name="A/C",
        priority="Low",
        location_id="LOC_HOSTEL_1",
        actor_id="mgr1",
    )

    # When querying for LOC_HOSTEL_1, override takes effect
    loc_priorities = department_service.get_category_priorities("DEPT_MAINT", location_id="LOC_HOSTEL_1")
    assert loc_priorities.get("A/C") == "Low"
    assert department_service.get_effective_category_priority("DEPT_MAINT", "A/C", location_id="LOC_HOSTEL_1") == "Low"

    # Other locations still see ALL default
    other_priorities = department_service.get_category_priorities("DEPT_MAINT", location_id="LOC_ACADEMIC_1")
    assert other_priorities.get("A/C") == "Critical"
    assert department_service.get_effective_category_priority("DEPT_MAINT", "A/C", location_id="LOC_ACADEMIC_1") == "Critical"


def test_complaint_creation_uses_configured_category_priority():
    auth_service = get_auth_service()
    department_service = get_department_service()
    complaint_service = get_complaint_service()

    # Ensure department has custom category priority
    department_service.set_category_priority(
        department_id="DEPT_MAINT",
        category_name="Hygiene",
        priority="Critical",
        location_id="LOC_HOSTEL_1",
        actor_id="admin1",
    )

    student = auth_service.get_user("USR_STUDENT")
    if not student:
        student = Student("USR_STUDENT", "Student User", "student@campus.edu", "pass")

    complaint = complaint_service.create_complaint(
        user=student,
        location_id="LOC_HOSTEL_1",
        department_id="DEPT_MAINT",
        complaint_type="Hygiene",
        description="Cleanliness issue in hostel wing 1",
        category="Hygiene",
    )

    # Should have Critical priority instead of default Medium
    assert complaint.priority == "Critical"


def test_category_priorities_api():
    from fastapi.testclient import TestClient
    from api.main import app
    from middleware.rate_limiter import auth_limiter

    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()

    client = TestClient(app)
    # Admin login
    admin_res = client.post("/auth/login", json={"username": "admin@example.com", "password": "Admin@123"})
    assert admin_res.status_code == 200
    admin_token = admin_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Update priority via admin
    put_res = client.put(
        "/departments/DEPT_MAINT/category-priorities",
        json={"category_name": "Sensor Fault", "priority": "High", "location_id": "ALL"},
        headers=admin_headers,
    )
    assert put_res.status_code == 200, put_res.text
    assert put_res.json()["priority"] == "High"

    # 2. Get priorities
    get_res = client.get("/departments/DEPT_MAINT/category-priorities", headers=admin_headers)
    assert get_res.status_code == 200
    assert get_res.json()["priorities"].get("Sensor Fault") == "High"

    # 3. Department listing contains category_priorities dict
    list_res = client.get("/departments", headers=admin_headers)
    assert list_res.status_code == 200
    depts = list_res.json()
    first_dept = depts[0]
    assert "category_priorities" in first_dept

    # 4. App Manager scoping
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()
    mgr_res = client.post("/auth/login", json={"username": "manager@example.com", "password": "Manager@123"})
    assert mgr_res.status_code == 200
    mgr_headers = {"Authorization": f"Bearer {mgr_res.json()['access_token']}"}

    auth_svc = get_auth_service()
    mgr_locs = auth_svc.get_app_manager_locations("USR_MANAGER")
    if mgr_locs:
        assigned_loc = mgr_locs[0].location_id
        # Allowed for assigned location
        ok_res = client.put(
            f"/departments/{first_dept['department_id']}/category-priorities",
            json={"category_name": "A/C", "priority": "Critical", "location_id": assigned_loc},
            headers=mgr_headers,
        )
        assert ok_res.status_code == 200, ok_res.text

        # Forbidden for unassigned location
        unassigned_loc = "LOC_NON_EXISTENT_OR_UNASSIGNED"
        denied_res = client.put(
            f"/departments/{first_dept['department_id']}/category-priorities",
            json={"category_name": "A/C", "priority": "Low", "location_id": unassigned_loc},
            headers=mgr_headers,
        )
        assert denied_res.status_code == 403


def test_complaint_creation_location_override_wins():
    auth_service = get_auth_service()
    department_service = get_department_service()
    complaint_service = get_complaint_service()

    # Campus-wide priority is Low
    department_service.set_category_priority(
        department_id="DEPT_OVERRIDE_TEST",
        category_name="Plumbing",
        priority="Low",
        location_id="ALL",
        actor_id="admin1",
    )
    # Location override is Critical
    department_service.set_category_priority(
        department_id="DEPT_OVERRIDE_TEST",
        category_name="Plumbing",
        priority="Critical",
        location_id="LOC_HOSTEL_1",
        actor_id="admin1",
    )

    student = auth_service.get_user("USR_STUDENT")
    if not student:
        student = Student("USR_STUDENT", "Student User", "student@campus.edu", "pass")

    # Override location gets Critical
    c1 = complaint_service.create_complaint(
        user=student,
        location_id="LOC_HOSTEL_1",
        department_id="DEPT_OVERRIDE_TEST",
        complaint_type="Plumbing",
        description="Leak at hostel",
        category="Plumbing",
    )
    assert c1.priority == "Critical"

    # Other location gets campus-wide default Low
    student.location_id = "LOC_HOSTEL_2"
    c2 = complaint_service.create_complaint(
        user=student,
        location_id="LOC_HOSTEL_2",
        department_id="DEPT_OVERRIDE_TEST",
        complaint_type="Plumbing",
        description="Leak at other location",
        category="Plumbing",
    )
    assert c2.priority == "Low"


def test_complaint_creation_with_none_uses_old_default():
    auth_service = get_auth_service()
    complaint_service = get_complaint_service()

    student = auth_service.get_user("USR_STUDENT")
    if not student:
        student = Student("USR_STUDENT", "Student User", "student@campus.edu", "pass")

    # Unconfigured category and department uses CATEGORY_PRIORITY_MAP
    c = complaint_service.create_complaint(
        user=student,
        location_id="LOC_HOSTEL_1",
        department_id="DEPT_UNCONFIGURED_999",
        complaint_type="Carpentry",
        description="Broken desk",
        category="Carpentry",
    )
    assert c.priority == "Medium"


def test_complaint_creation_fallback_and_logged_on_exception(monkeypatch, caplog):
    import logging
    auth_service = get_auth_service()
    department_service = get_department_service()
    complaint_service = get_complaint_service()

    student = auth_service.get_user("USR_STUDENT")
    if not student:
        student = Student("USR_STUDENT", "Student User", "student@campus.edu", "pass")

    def mock_failing_resolve(*args, **kwargs):
        raise RuntimeError("Simulated DB lookup crash")

    monkeypatch.setattr(department_service, "resolve_category_priority", mock_failing_resolve)

    with caplog.at_level(logging.WARNING):
        c = complaint_service.create_complaint(
            user=student,
            location_id="LOC_HOSTEL_1",
            department_id="DEPT_HOSTEL_ELECTRICAL",
            complaint_type="Electrical",
            description="Flickering bulb",
            category="Electrical",
        )

    # Complaint is still created successfully with the default priority
    assert c is not None
    assert c.priority == "Medium"
    # Exception was logged with error text
    assert any("Simulated DB lookup crash" in record.message for record in caplog.records)



