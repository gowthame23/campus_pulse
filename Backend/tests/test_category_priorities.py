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


def test_complaint_creation_uses_configured_category_priority(monkeypatch):
    monkeypatch.setenv("CATEGORY_PRIORITY_ENABLED", "true")
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


def test_category_priorities_api(monkeypatch):
    monkeypatch.setenv("CATEGORY_PRIORITY_ENABLED", "true")
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

        # Forbidden for unassigned location (must be a valid location the manager is not assigned to)
        all_locs = auth_svc.list_locations()
        unassigned_loc = next((l.location_id for l in all_locs if not auth_svc.is_app_manager_assigned("USR_MANAGER", l.location_id)), None)
        if unassigned_loc:
            denied_res = client.put(
                f"/departments/{first_dept['department_id']}/category-priorities",
                json={"category_name": "A/C", "priority": "Low", "location_id": unassigned_loc},
                headers=mgr_headers,
            )
            assert denied_res.status_code == 403


def test_complaint_creation_location_override_wins(monkeypatch):
    monkeypatch.setenv("CATEGORY_PRIORITY_ENABLED", "true")
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
    monkeypatch.setenv("CATEGORY_PRIORITY_ENABLED", "true")
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


def test_feature_flag_disabled_behavior(monkeypatch):
    """When CATEGORY_PRIORITY_ENABLED is false (or unset):
    - Complaint creation ignores custom priorities and uses standard default.
    - GET /departments/category-priorities/status returns enabled: False.
    - GET /departments/{id}/category-priorities returns empty priorities and enabled: False.
    - PUT /departments/{id}/category-priorities returns HTTP 403 Forbidden.
    - Department listing enrich_department_dict returns empty category_priorities dict.
    """
    monkeypatch.setenv("CATEGORY_PRIORITY_ENABLED", "false")
    from fastapi.testclient import TestClient
    from api.main import app
    from middleware.rate_limiter import auth_limiter

    auth_service = get_auth_service()
    department_service = get_department_service()
    complaint_service = get_complaint_service()

    # Pre-configure a priority in the table directly
    department_service.set_category_priority(
        department_id="DEPT_FLAG_TEST",
        category_name="Plumbing",
        priority="Critical",
        location_id="ALL",
        actor_id="admin1",
    )

    # 1. Complaint creation ignores the priority table and falls back to standard default
    student = auth_service.get_user("USR_STUDENT")
    if not student:
        student = Student("USR_STUDENT", "Student User", "student@campus.edu", "pass")

    complaint = complaint_service.create_complaint(
        user=student,
        location_id="LOC_HOSTEL_1",
        department_id="DEPT_FLAG_TEST",
        complaint_type="Plumbing",
        description="Disabled flag test",
        category="Plumbing",
    )
    # Even though DB table has Critical, flag is disabled so it should NOT use it!
    # In CATEGORY_PRIORITY_MAP "plumbing" maps to "High" or fallback "Medium"
    # The key test is it does NOT get "Critical" from the location_category_priorities table!
    assert complaint.priority != "Critical"

    # 2. Test Client API checks
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()
    client = TestClient(app)

    admin_res = client.post("/auth/login", json={"username": "admin@example.com", "password": "Admin@123"})
    assert admin_res.status_code == 200
    headers = {"Authorization": f"Bearer {admin_res.json()['access_token']}"}

    # Status endpoint
    status_res = client.get("/departments/category-priorities/status")
    assert status_res.status_code == 200
    assert status_res.json()["enabled"] is False

    # GET category-priorities returns empty priorities
    get_res = client.get("/departments/DEPT_FLAG_TEST/category-priorities", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["enabled"] is False
    assert get_res.json()["priorities"] == {}

    # PUT category-priorities returns 403 Forbidden
    put_res = client.put(
        "/departments/DEPT_FLAG_TEST/category-priorities",
        json={"category_name": "Plumbing", "priority": "Low", "location_id": "ALL"},
        headers=headers,
    )
    assert put_res.status_code == 403
    assert "disabled" in put_res.json()["detail"].lower()

    # Department listing enrichment returns empty dict for category_priorities
    list_res = client.get("/departments", headers=headers)
    assert list_res.status_code == 200
    depts = list_res.json()
    flag_dept = next((d for d in depts if d["department_id"] == "DEPT_FLAG_TEST"), None)
    if flag_dept:
        assert flag_dept.get("category_priorities") == {}


def test_feature_flag_enabled_behavior(monkeypatch):
    """When CATEGORY_PRIORITY_ENABLED is true:
    - GET /departments/category-priorities/status returns enabled: True.
    - PUT /departments/{id}/category-priorities allows configuring priority.
    - GET /departments/{id}/category-priorities returns configured priorities and enabled: True.
    - Complaint creation resolves configured priority.
    """
    monkeypatch.setenv("CATEGORY_PRIORITY_ENABLED", "true")
    from fastapi.testclient import TestClient
    from api.main import app
    from middleware.rate_limiter import auth_limiter

    auth_service = get_auth_service()
    complaint_service = get_complaint_service()

    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()
    client = TestClient(app)

    admin_res = client.post("/auth/login", json={"username": "admin@example.com", "password": "Admin@123"})
    assert admin_res.status_code == 200
    headers = {"Authorization": f"Bearer {admin_res.json()['access_token']}"}

    # Status endpoint
    status_res = client.get("/departments/category-priorities/status")
    assert status_res.status_code == 200
    assert status_res.json()["enabled"] is True

    # PUT updates successfully
    put_res = client.put(
        "/departments/DEPT_FLAG_TEST/category-priorities",
        json={"category_name": "CustomFlagCat", "priority": "Critical", "location_id": "ALL"},
        headers=headers,
    )
    assert put_res.status_code == 200
    assert put_res.json()["priority"] == "Critical"

    # GET returns configured priorities
    get_res = client.get("/departments/DEPT_FLAG_TEST/category-priorities", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["enabled"] is True
    assert get_res.json()["priorities"].get("CustomFlagCat") == "Critical"

    # Complaint creation gets Critical
    student = auth_service.get_user("USR_STUDENT")
    if not student:
        student = Student("USR_STUDENT", "Student User", "student@campus.edu", "pass")

    complaint = complaint_service.create_complaint(
        user=student,
        location_id="LOC_HOSTEL_1",
        department_id="DEPT_FLAG_TEST",
        complaint_type="CustomFlagCat",
        description="Flag enabled test",
        category="CustomFlagCat",
    )
    assert complaint.priority == "Critical"


def test_history_row_written_on_change_and_none_on_noop():
    department_service = get_department_service()
    dept_id = "DEPT_HIST_TEST"
    cat_name = "Water Cooler"

    # Initial set: old_priority is None, new_priority is High
    department_service.set_category_priority(
        department_id=dept_id,
        category_name=cat_name,
        priority="High",
        location_id="ALL",
        actor_id="admin_hist",
    )
    hist = department_service.get_category_priority_history(dept_id, category_name=cat_name)
    assert len(hist) == 1
    assert hist[0]["old_priority"] is None
    assert hist[0]["new_priority"] == "High"
    assert hist[0]["changed_by"] == "admin_hist"

    # Changed priority: High -> Critical
    department_service.set_category_priority(
        department_id=dept_id,
        category_name=cat_name,
        priority="Critical",
        location_id="ALL",
        actor_id="admin_hist_2",
    )
    hist2 = department_service.get_category_priority_history(dept_id, category_name=cat_name)
    assert len(hist2) == 2
    assert hist2[1]["old_priority"] == "High"
    assert hist2[1]["new_priority"] == "Critical"
    assert hist2[1]["changed_by"] == "admin_hist_2"

    # No-op: priority is still Critical
    department_service.set_category_priority(
        department_id=dept_id,
        category_name=cat_name,
        priority="Critical",
        location_id="ALL",
        actor_id="admin_hist_3",
    )
    hist3 = department_service.get_category_priority_history(dept_id, category_name=cat_name)
    assert len(hist3) == 2  # No new row written for no-op!


def test_invalid_location_returns_400(monkeypatch):
    monkeypatch.setenv("CATEGORY_PRIORITY_ENABLED", "true")
    from fastapi.testclient import TestClient
    from api.main import app
    from middleware.rate_limiter import auth_limiter

    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()
    client = TestClient(app)

    admin_res = client.post("/auth/login", json={"username": "admin@example.com", "password": "Admin@123"})
    assert admin_res.status_code == 200
    headers = {"Authorization": f"Bearer {admin_res.json()['access_token']}"}

    # Invalid location
    res = client.put(
        "/departments/DEPT_MAINT/category-priorities",
        json={"category_name": "AC", "priority": "High", "location_id": "LOC_DOES_NOT_EXIST_XYZ"},
        headers=headers,
    )
    assert res.status_code == 400
    assert "does not exist" in res.json()["detail"]


def test_long_categories_with_same_60_char_prefix_do_not_collide():
    department_service = get_department_service()
    dept_id = "DEPT_COLLISION_TEST"
    prefix = "VeryLongCategoryNameWithIdenticalInitialPrefixCharacterSeq_" * 2  # >60 chars
    cat_a = prefix + "_SUFFIX_AAA"
    cat_b = prefix + "_SUFFIX_BBB"

    department_service.set_category_priority(
        department_id=dept_id,
        category_name=cat_a,
        priority="Low",
        location_id="ALL",
        actor_id="admin1",
    )
    department_service.set_category_priority(
        department_id=dept_id,
        category_name=cat_b,
        priority="Critical",
        location_id="ALL",
        actor_id="admin1",
    )

    priorities = department_service.get_category_priorities(dept_id)
    assert priorities.get(cat_a) == "Low"
    assert priorities.get(cat_b) == "Critical"


def test_app_manager_scoping_rules(monkeypatch):
    monkeypatch.setenv("CATEGORY_PRIORITY_ENABLED", "true")
    from fastapi.testclient import TestClient
    from api.main import app
    from middleware.rate_limiter import auth_limiter

    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()
    client = TestClient(app)

    mgr_res = client.post("/auth/login", json={"username": "manager@example.com", "password": "Manager@123"})
    assert mgr_res.status_code == 200
    mgr_headers = {"Authorization": f"Bearer {mgr_res.json()['access_token']}"}

    auth_svc = get_auth_service()
    mgr_locs = auth_svc.get_app_manager_locations("USR_MANAGER")
    assert len(mgr_locs) > 0
    assigned_loc_id = mgr_locs[0].location_id

    all_locs = auth_svc.list_locations()
    unassigned_loc = next((l for l in all_locs if not auth_svc.is_app_manager_assigned("USR_MANAGER", l.location_id)), None)
    assert unassigned_loc is not None, "Need at least one unassigned location for test"

    # App Manager cannot change a location they are not assigned to (403)
    denied = client.put(
        "/departments/DEPT_MAINT/category-priorities",
        json={"category_name": "Projector", "priority": "High", "location_id": unassigned_loc.location_id},
        headers=mgr_headers,
    )
    assert denied.status_code == 403
    assert "not assigned" in denied.json()["detail"].lower()

    # App Manager with 'ALL' only affects their own assigned locations
    all_res = client.put(
        "/departments/DEPT_MAINT/category-priorities",
        json={"category_name": "Projector", "priority": "Critical", "location_id": "ALL"},
        headers=mgr_headers,
    )
    assert all_res.status_code == 200
    updated_loc_ids = [u["location_id"] for u in all_res.json()["updated_locations"]]
    mgr_loc_ids = [l.location_id for l in mgr_locs]
    assert set(updated_loc_ids) == set(mgr_loc_ids)
    assert unassigned_loc.location_id not in updated_loc_ids





