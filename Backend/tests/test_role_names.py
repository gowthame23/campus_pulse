import os
import re
import json
import pytest
from core.constants import (
    ROLE_ADMINISTRATOR,
    ROLE_APP_MANAGER,
    ROLE_COORDINATOR,
    ROLE_EMPLOYEE,
    ROLE_WARDEN,
    ROLE_STUDENT,
    ROLE_SUPER_ADMIN,
    ROLE_DISPLAY_NAMES,
    get_role_display_name,
)

def test_internal_roles_unchanged():
    """Rule 1.2: Internal role IDs in the database and code DO NOT change."""
    assert ROLE_ADMINISTRATOR == "administrator"
    assert ROLE_APP_MANAGER == "app_manager"
    assert ROLE_COORDINATOR == "coordinator"
    assert ROLE_EMPLOYEE == "employee"
    assert ROLE_WARDEN == "location_in_charge"
    assert ROLE_STUDENT == "student"
    assert ROLE_SUPER_ADMIN == "super_admin"


def test_canonical_display_names():
    """Rule 1.1: The ONLY role names shown to users anywhere are:
    Admin | App Manager | Coordinator | Employee | Warden | Student (Super Admin platform-level)
    """
    assert get_role_display_name(ROLE_ADMINISTRATOR) == "Admin"
    assert get_role_display_name("admin") == "Admin"
    assert get_role_display_name(ROLE_APP_MANAGER) == "App Manager"
    assert get_role_display_name("manager") == "App Manager"
    assert get_role_display_name(ROLE_COORDINATOR) == "Coordinator"
    assert get_role_display_name(ROLE_EMPLOYEE) == "Employee"
    assert get_role_display_name(ROLE_WARDEN) == "Warden"
    assert get_role_display_name("warden") == "Warden"
    assert get_role_display_name(ROLE_STUDENT) == "Student"
    assert get_role_display_name(ROLE_SUPER_ADMIN) == "Super Admin"


def test_frontend_locales_contain_canonical_roles():
    """Rule 1.3: Locales in en.json, hi.json, te.json contain canonical role display names."""
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Frontend", "src", "locales"))
    for lang in ["en.json", "hi.json", "te.json"]:
        path = os.path.join(frontend_dir, lang)
        assert os.path.exists(path), f"Locale file {path} missing"
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "roles" in data, f"{lang} missing roles section"
        roles = data["roles"]
        if lang == "en.json":
            assert roles["admin"] == "Admin"
            assert roles["app_manager"] == "App Manager"
            assert roles["coordinator"] == "Coordinator"
            assert roles["employee"] == "Employee"
            assert roles["warden"] == "Warden"
            assert roles["student"] == "Student"
        else:
            assert all(k in roles for k in ["admin", "app_manager", "coordinator", "employee", "warden", "student"])

