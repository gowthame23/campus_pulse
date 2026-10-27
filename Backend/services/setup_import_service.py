import csv
import io
import re
import secrets
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from core.constants import (
    ROLE_ADMINISTRATOR,
    ROLE_APP_MANAGER,
    ROLE_COORDINATOR,
    ROLE_EMPLOYEE,
    ROLE_LOCATION_IN_CHARGE,
    ROLE_STUDENT,
    ROLE_SUPER_ADMIN,
    ROLE_DISPLAY_NAMES,
)
from utils.logger import get_logger
from utils.passwords import hash_password

logger = get_logger(__name__)


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """Normalize phone numbers consistently across CampusPulse.
    Strips spaces, hyphens, parentheses, dots and +91/91 country prefix.
    Stores 10-15 digits.
    """
    if not phone:
        return None
    raw = str(phone).strip()
    # Strip spaces, hyphens, brackets, dots
    cleaned = re.sub(r"[\s\-\(\)\.]", "", raw)
    if cleaned.startswith("+91") and len(cleaned) == 13:
        cleaned = cleaned[3:]
    elif cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    elif cleaned.startswith("+"):
        cleaned = cleaned[1:]
    return cleaned if cleaned else None


def generate_worker_temp_password() -> str:
    """Generate temporary password in format CP-<4 digits> (e.g. CP-4821)"""
    return f"CP-{secrets.randbelow(9000) + 1000}"


class SetupImportService:
    def __init__(self, auth_service, team_service, emergency_service, complaint_service):
        self.auth_service = auth_service
        self.team_service = team_service
        self.emergency_service = emergency_service
        self.complaint_service = complaint_service

    # -------------------------------------------------------------------------
    # 1. TEMPLATES (CSV & Excel)
    # -------------------------------------------------------------------------
    def get_template(self, import_type: str, format_type: str = "csv") -> Tuple[bytes, str, str]:
        import_type = (import_type or "").lower().strip()
        format_type = (format_type or "csv").lower().strip()

        templates = {
            "locations": {
                "headers": ["name", "parent", "type", "warden_email_or_phone"],
                "sample": ["Block A - Floor 2", "Hostel Block A", "hostel", "warden.blocka@campus.edu"],
                "filename_base": "locations_import_template",
            },
            "staff": {
                "headers": ["name", "role", "email", "phone", "teams"],
                "sample": ["Ramesh Kumar", "Employee", "", "9876543210", "Electrical Team, Plumbing Team"],
                "filename_base": "staff_import_template",
            },
            "teams": {
                "headers": ["team name", "department", "places", "coordinator", "backup", "members"],
                "sample": ["Block A Electrical", "Electrical", "Hostel Block A, Block B", "coord.elec@campus.edu", "backup.elec@campus.edu", "9876543210, 9876543211"],
                "filename_base": "teams_import_template",
            },
            "emergency_contacts": {
                "headers": ["department", "location", "name", "phone", "order", "day_only", "night_only"],
                "sample": ["Electrical", "Hostel Block A", "Duty Electrician", "9876543210", "1", "no", "yes"],
                "filename_base": "emergency_contacts_import_template",
            },
        }

        tpl = templates.get(import_type)
        if not tpl:
            raise ValueError(f"Unknown import type: {import_type}. Supported: {list(templates.keys())}")

        headers = tpl["headers"]
        sample = tpl["sample"]

        if format_type in ("xlsx", "excel"):
            try:
                import openpyxl
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = f"{import_type.title()} Template"
                ws.append(headers)
                ws.append(sample)
                output = io.BytesIO()
                wb.save(output)
                output.seek(0)
                return (
                    output.getvalue(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    f"{tpl['filename_base']}.xlsx",
                )
            except Exception as e:
                logger.warning(f"openpyxl failed, falling back to CSV: {e}")

        # Default CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerow(sample)
        return (
            output.getvalue().encode("utf-8"),
            "text/csv",
            f"{tpl['filename_base']}.csv",
        )

    # -------------------------------------------------------------------------
    # 2. FILE PARSER HELPER
    # -------------------------------------------------------------------------
    def _parse_file_rows(self, file_contents: bytes, filename: str) -> List[Tuple[int, Dict[str, str]]]:
        filename_lower = (filename or "").lower()
        rows_data = []

        if filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls"):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(filename=io.BytesIO(file_contents), data_only=True)
                sheet = wb.active
                headers = [str(cell.value or "").strip().lower() for cell in sheet[1]]
                for idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                    row_dict = {}
                    has_content = False
                    for h, val in zip(headers, row):
                        if h:
                            str_val = str(val).strip() if val is not None else ""
                            row_dict[h] = str_val
                            if str_val:
                                has_content = True
                    if has_content:
                        rows_data.append((idx, row_dict))
                return rows_data
            except Exception as e:
                logger.warning(f"Excel parsing fallback to CSV: {e}")

        # Fallback / standard CSV parsing
        text = file_contents.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        for idx, row in enumerate(reader, start=2):
            norm_row = {str(k or "").strip().lower(): str(v or "").strip() for k, v in row.items()}
            if any(norm_row.values()):
                rows_data.append((idx, norm_row))
        return rows_data

    # -------------------------------------------------------------------------
    # 3. PREVIEW IMPORT (Row-by-Row Validation)
    # -------------------------------------------------------------------------
    def preview_import(self, import_type: str, file_contents: bytes, filename: str) -> Dict[str, Any]:
        rows_data = self._parse_file_rows(file_contents, filename)
        import_type = (import_type or "").lower().strip()

        if import_type == "locations":
            validated_rows = self._validate_location_rows(rows_data)
        elif import_type == "staff":
            validated_rows = self._validate_staff_rows(rows_data)
        elif import_type == "teams":
            validated_rows = self._validate_team_rows(rows_data)
        elif import_type == "emergency_contacts":
            validated_rows = self._validate_emergency_contact_rows(rows_data)
        else:
            raise ValueError(f"Unknown import type: {import_type}")

        valid_count = sum(1 for r in validated_rows if r["is_valid"])
        invalid_count = len(validated_rows) - valid_count

        return {
            "import_type": import_type,
            "total_rows": len(validated_rows),
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "rows": validated_rows,
        }

    # -------------------------------------------------------------------------
    # 4. EXECUTE IMPORT
    # -------------------------------------------------------------------------
    def execute_import(self, import_type: str, file_contents: bytes, filename: str, creator) -> Dict[str, Any]:
        preview = self.preview_import(import_type, file_contents, filename)
        valid_rows = [r for r in preview["rows"] if r["is_valid"]]
        invalid_rows = [r for r in preview["rows"] if not r["is_valid"]]

        if import_type == "locations":
            result = self._execute_location_import(valid_rows, invalid_rows, creator)
        elif import_type == "staff":
            result = self._execute_staff_import(valid_rows, invalid_rows, creator)
        elif import_type == "teams":
            result = self._execute_team_import(valid_rows, invalid_rows, creator)
        elif import_type == "emergency_contacts":
            result = self._execute_emergency_contacts_import(valid_rows, invalid_rows, creator)
        else:
            raise ValueError(f"Unknown import type: {import_type}")

        return result

    # -------------------------------------------------------------------------
    # VALIDATION LOGIC FOR EACH SPEC
    # -------------------------------------------------------------------------
    def _validate_location_rows(self, rows_data: List[Tuple[int, Dict[str, str]]]) -> List[Dict[str, Any]]:
        existing_locs = self.auth_service.list_locations() or []
        loc_by_name = {l.name.lower(): l for l in existing_locs}
        file_loc_names = {r.get("name", "").strip().lower() for _, r in rows_data if r.get("name")}

        valid_types = {"hostel", "academic", "common", "mess", "other"}

        results = []
        for row_idx, row in rows_data:
            name = row.get("name", "").strip()
            parent = row.get("parent", "").strip()
            raw_type = row.get("type", "").strip().lower()
            warden_val = row.get("warden_email_or_phone", "").strip()

            errors = []
            if not name:
                errors.append("Location name is required.")

            parent_id = None
            if parent:
                parent_loc = loc_by_name.get(parent.lower())
                if parent_loc:
                    parent_id = parent_loc.location_id
                elif parent.lower() in file_loc_names:
                    # Valid: parent location is defined in this same import batch
                    parent_id = None
                else:
                    errors.append(f"Parent location '{parent}' not found.")

            if raw_type and raw_type not in valid_types:
                errors.append(f"Invalid type '{raw_type}'. Must be one of: hostel, academic, common, mess, other.")

            warden_id = None
            if warden_val:
                warden_user = self.auth_service.get_user_by_email(warden_val.lower())
                if not warden_user:
                    clean_phone = normalize_phone(warden_val)
                    if clean_phone:
                        warden_user = self.auth_service.get_user_by_phone(clean_phone)
                if warden_user:
                    warden_id = warden_user.user_id
                else:
                    errors.append(f"Warden '{warden_val}' not found by email or phone.")

            results.append({
                "row_index": row_idx,
                "raw_data": row,
                "is_valid": len(errors) == 0,
                "errors": errors,
                "parsed_data": {
                    "name": name,
                    "parent_name": parent,
                    "parent_id": parent_id,
                    "location_type": self._map_location_type(raw_type or "other"),
                    "in_charge_id": warden_id,
                },
            })
        return results

    def _map_location_type(self, raw: str) -> str:
        mapping = {
            "hostel": "Hostel",
            "academic": "Academic Block",
            "common": "Student Activity Center",
            "mess": "Mess",
            "other": "Other / Not Sure",
        }
        return mapping.get(raw.lower(), "Other / Not Sure")

    def _validate_staff_rows(self, rows_data: List[Tuple[int, Dict[str, str]]]) -> List[Dict[str, Any]]:
        # STAFF: name, role ('Employee'|'Coordinator'|'Warden'|'App Manager'),
        # email (optional for Employees), phone (REQUIRED for Employee, Coordinator, Warden; optional for App Manager),
        # teams (optional, comma-separated)
        existing_teams = self.team_service.list_teams() or []
        team_by_name = {
            (t.get("name") if isinstance(t, dict) else getattr(t, "name", "")).lower(): t
            for t in existing_teams
        }

        role_map = {
            "employee": ROLE_EMPLOYEE,
            "coordinator": ROLE_COORDINATOR,
            "warden": ROLE_LOCATION_IN_CHARGE,
            "location in-charge": ROLE_LOCATION_IN_CHARGE,
            "location_in_charge": ROLE_LOCATION_IN_CHARGE,
            "app manager": ROLE_APP_MANAGER,
            "app_manager": ROLE_APP_MANAGER,
        }

        seen_phones = set()
        seen_emails = set()

        results = []
        for row_idx, row in rows_data:
            name = row.get("name", "").strip()
            raw_role = row.get("role", "").strip().lower()
            email = row.get("email", "").strip().lower()
            raw_phone = row.get("phone", "").strip()
            teams_str = row.get("teams", "").strip()

            errors = []
            if not name:
                errors.append("Name is required.")

            canonical_role = role_map.get(raw_role)
            if not canonical_role:
                errors.append(f"Invalid role '{row.get('role')}'. Allowed: Employee, Coordinator, Warden, App Manager.")

            phone = normalize_phone(raw_phone)
            if canonical_role in (ROLE_EMPLOYEE, ROLE_COORDINATOR, ROLE_LOCATION_IN_CHARGE):
                if not phone:
                    errors.append(f"Phone number is required for {ROLE_DISPLAY_NAMES.get(canonical_role, 'Staff')}.")
                elif not (10 <= len(phone) <= 15):
                    errors.append(f"Phone number '{raw_phone}' must be 10 to 15 digits.")
            elif raw_phone and not phone:
                errors.append(f"Invalid phone number format: '{raw_phone}'.")

            is_update = False
            matched_user_id = None
            if canonical_role in (ROLE_COORDINATOR, ROLE_LOCATION_IN_CHARGE, ROLE_APP_MANAGER) and not email:
                errors.append(f"Email is required for {ROLE_DISPLAY_NAMES.get(canonical_role, 'Staff')}.")
            elif email:
                if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                    errors.append(f"Invalid email format: '{email}'.")
                elif email in seen_emails:
                    errors.append(f"Duplicate email '{email}' within file.")
                else:
                    existing_user = self.auth_service.get_user_by_email(email)
                    if existing_user:
                        is_update = True
                        matched_user_id = getattr(existing_user, "user_id", None) or (existing_user.get("user_id") if isinstance(existing_user, dict) else None)
                seen_emails.add(email)

            if phone:
                if phone in seen_phones:
                    errors.append(f"Duplicate phone '{phone}' within file.")
                else:
                    existing_user = self.auth_service.get_user_by_phone(phone)
                    if existing_user:
                        is_update = True
                        matched_user_id = getattr(existing_user, "user_id", None) or (existing_user.get("user_id") if isinstance(existing_user, dict) else None)
                seen_phones.add(phone)

            team_names = [t.strip() for t in teams_str.split(",") if t.strip()] if teams_str else []

            results.append({
                "row_index": row_idx,
                "raw_data": row,
                "is_valid": len(errors) == 0,
                "errors": errors,
                "parsed_data": {
                    "name": name,
                    "role": canonical_role,
                    "email": email,
                    "phone": phone,
                    "team_names": team_names,
                    "is_update": is_update,
                    "matched_user_id": matched_user_id,
                },
            })
        return results

    def _validate_team_rows(self, rows_data: List[Tuple[int, Dict[str, str]]]) -> List[Dict[str, Any]]:
        # TEAMS: team name, department, places (comma-separated), coordinator (email/phone),
        # backup (optional, email/phone), members (comma-separated emails/phones)
        # Rule: one team per (place, department). If a row tries to overlap, show row error.
        all_depts = self.auth_service.list_departments() or []
        dept_by_name = {d.name.lower(): d for d in all_depts}
        for d in all_depts:
            dept_by_name[d.department_id.lower()] = d

        all_locs = self.auth_service.list_locations() or []
        loc_by_name = {l.name.lower(): l for l in all_locs}
        for l in all_locs:
            loc_by_name[l.location_id.lower()] = l

        existing_teams = self.team_service.list_teams() or []

        # Build coverage map of existing teams: (location_id, dept_id) -> team_name
        covered_pairs = {}
        for t in existing_teams:
            is_active = t.get("active", True) if isinstance(t, dict) else getattr(t, "active", True)
            if is_active:
                d_id = t.get("department_id") if isinstance(t, dict) else getattr(t, "department_id", None)
                l_ids = t.get("location_ids", []) if isinstance(t, dict) else (getattr(t, "location_ids", []) or [])
                t_name = t.get("name") if isinstance(t, dict) else getattr(t, "name", "")
                for l_id in (l_ids or []):
                    covered_pairs[(l_id, d_id)] = t_name

        file_covered_pairs = {}
        results = []

        for row_idx, row in rows_data:
            team_name = row.get("team name", "").strip() or row.get("team_name", "").strip() or row.get("name", "").strip()
            dept_val = row.get("department", "").strip()
            places_val = row.get("places", "").strip() or row.get("locations", "").strip()
            coord_val = row.get("coordinator", "").strip()
            backup_val = row.get("backup", "").strip()
            members_val = row.get("members", "").strip()

            errors = []
            if not team_name:
                errors.append("Team name is required.")

            dept_obj = dept_by_name.get(dept_val.lower())
            if not dept_obj:
                errors.append(f"Department '{dept_val}' not found.")

            place_objs = []
            if not places_val:
                errors.append("Places (assigned locations) are required.")
            else:
                for p_name in [p.strip() for p in places_val.split(",") if p.strip()]:
                    loc_obj = loc_by_name.get(p_name.lower())
                    if loc_obj:
                        place_objs.append(loc_obj)
                    else:
                        errors.append(f"Location '{p_name}' not found.")

            # Coordinator lookup
            coord_user = None
            if not coord_val:
                errors.append("Coordinator is required.")
            else:
                coord_user = self._resolve_user(coord_val)
                if not coord_user:
                    errors.append(f"Coordinator '{coord_val}' not found by email or phone.")

            # Backup coordinator lookup
            backup_user = None
            if backup_val:
                backup_user = self._resolve_user(backup_val)
                if not backup_user:
                    errors.append(f"Backup coordinator '{backup_val}' not found by email or phone.")

            # Members lookup
            member_users = []
            if members_val:
                for m_val in [m.strip() for m in members_val.split(",") if m.strip()]:
                    u = self._resolve_user(m_val)
                    if u:
                        member_users.append(u)
                    else:
                        errors.append(f"Member '{m_val}' not found by email or phone.")

            # Check coverage overlap rule: one team per (place, department)
            if dept_obj and place_objs:
                for p in place_objs:
                    pair = (p.location_id, dept_obj.department_id)
                    if pair in covered_pairs:
                        errors.append(
                            f"Coverage overlap: {p.name} + {dept_obj.name} is already assigned to team '{covered_pairs[pair]}'."
                        )
                    elif pair in file_covered_pairs:
                        errors.append(
                            f"Coverage overlap: {p.name} + {dept_obj.name} is already assigned to team '{file_covered_pairs[pair]}' earlier in this file."
                        )
                    else:
                        file_covered_pairs[pair] = team_name

            results.append({
                "row_index": row_idx,
                "raw_data": row,
                "is_valid": len(errors) == 0,
                "errors": errors,
                "parsed_data": {
                    "name": team_name,
                    "department_id": dept_obj.department_id if dept_obj else None,
                    "location_ids": [p.location_id for p in place_objs],
                    "coordinator_id": coord_user.user_id if coord_user else None,
                    "backup_coordinator_id": backup_user.user_id if backup_user else None,
                    "member_ids": [m.user_id for m in member_users],
                },
            })
        return results

    def _validate_emergency_contact_rows(self, rows_data: List[Tuple[int, Dict[str, str]]]) -> List[Dict[str, Any]]:
        # EMERGENCY CONTACTS: department, location (optional), name, phone, order (1, 2, 3...), day_only (yes/no), night_only (yes/no)
        all_depts = self.auth_service.list_departments() or []
        dept_by_name = {d.name.lower(): d for d in all_depts}
        for d in all_depts:
            dept_by_name[d.department_id.lower()] = d

        all_locs = self.auth_service.list_locations() or []
        loc_by_name = {l.name.lower(): l for l in all_locs}
        for l in all_locs:
            loc_by_name[l.location_id.lower()] = l

        results = []
        for row_idx, row in rows_data:
            dept_val = row.get("department", "").strip()
            loc_val = row.get("location", "").strip()
            name = row.get("name", "").strip()
            raw_phone = row.get("phone", "").strip()
            order_val = row.get("order", "1").strip()
            day_only_val = row.get("day_only", "no").strip().lower()
            night_only_val = row.get("night_only", "no").strip().lower()

            errors = []
            if not name:
                errors.append("Contact name is required.")

            dept_obj = dept_by_name.get(dept_val.lower())
            if not dept_obj:
                errors.append(f"Department '{dept_val}' not found.")

            loc_obj = None
            if loc_val:
                loc_obj = loc_by_name.get(loc_val.lower())
                if not loc_obj:
                    errors.append(f"Location '{loc_val}' not found.")

            phone = normalize_phone(raw_phone)
            if not phone:
                errors.append("Phone number is required.")
            elif not (10 <= len(phone) <= 15):
                errors.append(f"Phone number '{raw_phone}' must be 10 to 15 digits.")

            sort_order = 1
            try:
                sort_order = int(order_val)
            except ValueError:
                errors.append(f"Order '{order_val}' must be an integer.")

            day_only = 1 if day_only_val in ("yes", "1", "true") else 0
            night_only = 1 if night_only_val in ("yes", "1", "true") else 0

            results.append({
                "row_index": row_idx,
                "raw_data": row,
                "is_valid": len(errors) == 0,
                "errors": errors,
                "parsed_data": {
                    "name": name,
                    "phone": phone,
                    "department_id": dept_obj.department_id if dept_obj else None,
                    "location_id": loc_obj.location_id if loc_obj else None,
                    "sort_order": sort_order,
                    "day_only": day_only,
                    "night_only": night_only,
                },
            })
        return results

    def _resolve_user(self, identifier: str):
        if not identifier:
            return None
        clean = identifier.strip()
        # 1. By email
        user = self.auth_service.get_user_by_email(clean.lower())
        if user:
            return user
        # 2. By phone
        clean_phone = normalize_phone(clean)
        if clean_phone:
            user = self.auth_service.get_user_by_phone(clean_phone)
            if user:
                return user
        # 3. By user_id
        user = self.auth_service.get_user(clean)
        return user

    # -------------------------------------------------------------------------
    # EXECUTION HANDLERS
    # -------------------------------------------------------------------------
    def _execute_location_import(self, valid_rows: List[Dict[str, Any]], invalid_rows: List[Dict[str, Any]], creator) -> Dict[str, Any]:
        from models.location import Location

        report = []
        imported_count = 0
        updated_count = 0

        # Existing locations
        existing_locs = {l.name.lower(): l for l in self.auth_service.list_locations() or []}

        for r in valid_rows:
            pdata = r["parsed_data"]
            loc_name = pdata["name"]
            existing = existing_locs.get(loc_name.lower())

            # Resolve parent_id if parent was created in this same batch
            resolved_parent_id = pdata.get("parent_id")
            if not resolved_parent_id and pdata.get("parent_name"):
                parent_entry = existing_locs.get(pdata["parent_name"].lower())
                if parent_entry:
                    resolved_parent_id = parent_entry.location_id

            try:
                if existing:
                    existing.location_type = pdata["location_type"]
                    if pdata.get("in_charge_id"):
                        existing.in_charge_id = pdata["in_charge_id"]
                    if resolved_parent_id:
                        existing.parent_id = resolved_parent_id
                    self.auth_service.save_location(existing)
                    updated_count += 1
                    report.append({
                        "row_index": r["row_index"],
                        "name": loc_name,
                        "status": "Success",
                        "action": "Updated",
                        "reason": "Updated existing location details.",
                    })
                else:
                    new_loc = Location(
                        name=loc_name,
                        location_type=pdata["location_type"],
                        in_charge_id=pdata.get("in_charge_id"),
                        parent_id=resolved_parent_id,
                    )
                    self.auth_service.save_location(new_loc)
                    existing_locs[loc_name.lower()] = new_loc
                    imported_count += 1
                    report.append({
                        "row_index": r["row_index"],
                        "name": loc_name,
                        "status": "Success",
                        "action": "Imported",
                        "reason": "Created new location.",
                    })
            except Exception as e:
                report.append({
                    "row_index": r["row_index"],
                    "name": loc_name,
                    "status": "Failed",
                    "action": "Skipped",
                    "reason": str(e),
                })

        for r in invalid_rows:
            report.append({
                "row_index": r["row_index"],
                "name": r["raw_data"].get("name", "Unknown"),
                "status": "Failed",
                "action": "Skipped",
                "reason": "; ".join(r["errors"]),
            })

        return {
            "import_type": "locations",
            "total_rows": len(valid_rows) + len(invalid_rows),
            "success_count": imported_count + updated_count,
            "imported_count": imported_count,
            "updated_count": updated_count,
            "failed_count": len(invalid_rows) + (len(valid_rows) - imported_count - updated_count),
            "skipped_count": len(invalid_rows) + (len(valid_rows) - imported_count - updated_count),
            "report": report,
            "credentials_slips": [],
        }

    def _execute_staff_import(self, valid_rows: List[Dict[str, Any]], invalid_rows: List[Dict[str, Any]], creator) -> Dict[str, Any]:
        report = []
        slips = []
        imported_count = 0
        updated_count = 0

        for r in valid_rows:
            pdata = r["parsed_data"]
            name = pdata["name"]
            role = pdata["role"]
            email = pdata.get("email")
            phone = pdata.get("phone")
            team_names = pdata.get("team_names", [])

            # For worker without email: generate worker temp password
            is_worker_without_email = (role == ROLE_EMPLOYEE and not email)
            temp_password = generate_worker_temp_password() if is_worker_without_email else None

            try:
                user_to_link = None
                action_type = "Imported"
                action_reason = "Created user account."

                if pdata.get("matched_user_id"):
                    existing_user = self.auth_service.get_user(pdata["matched_user_id"])
                    if existing_user:
                        creator_role = (getattr(creator, "role", "") or "").lower()
                        # Privilege Escalation Guard: App Managers cannot overwrite roles to/from Administrator or App Manager
                        if creator_role == "app_manager":
                            if existing_user.role in ("administrator", "super_admin", "app_manager") or role in (ROLE_APP_MANAGER, "administrator", "super_admin"):
                                raise PermissionError(f"App Managers cannot modify administrative or App Manager accounts.")

                        existing_user.name = name
                        existing_user.role = role
                        if phone:
                            existing_user.phone_number = phone
                        self.auth_service.save_user(existing_user)
                        user_to_link = existing_user
                        updated_count += 1
                        action_type = "Updated"
                        action_reason = f"Updated existing user '{name}' ({role})."

                if not user_to_link:
                    created_user = self.auth_service.create_user(
                        name=name,
                        email=email if email else None,
                        password=temp_password,
                        role=role,
                        creator=creator,
                        phone_number=phone,
                    )
                    user_to_link = created_user
                    imported_count += 1

                u_name = getattr(user_to_link, "name", None) or (user_to_link.get("name") if isinstance(user_to_link, dict) else name)
                u_role = getattr(user_to_link, "role", None) or (user_to_link.get("role") if isinstance(user_to_link, dict) else role)
                u_id = getattr(user_to_link, "user_id", None) or (user_to_link.get("user_id") if isinstance(user_to_link, dict) else "")

                if is_worker_without_email:
                    slips.append({
                        "name": u_name,
                        "role": ROLE_DISPLAY_NAMES.get(u_role, "Employee"),
                        "phone": phone,
                        "temporary_password": temp_password,
                    })

                # Attach user to requested teams if they exist
                for tname in team_names:
                    team = self.team_service.get_team_by_name(tname)
                    if team:
                        t_id = team["team_id"] if isinstance(team, dict) else team.team_id
                        mem_list = team.get("member_ids") if isinstance(team, dict) else getattr(team, "member_ids", [])
                        members = set(mem_list or [])
                        members.add(u_id)
                        payload = team.copy() if isinstance(team, dict) else team.to_dict()
                        payload["member_ids"] = list(members)
                        self.team_service.update_team(t_id, payload)

                report.append({
                    "row_index": r["row_index"],
                    "name": name,
                    "role": ROLE_DISPLAY_NAMES.get(role, role),
                    "phone": phone,
                    "email": email or "",
                    "temporary_password": temp_password,
                    "status": "Success",
                    "action": action_type,
                    "reason": action_reason,
                })
            except Exception as e:
                report.append({
                    "row_index": r["row_index"],
                    "name": name,
                    "role": ROLE_DISPLAY_NAMES.get(role, role),
                    "phone": phone,
                    "email": email or "",
                    "status": "Failed",
                    "action": "Skipped",
                    "reason": str(e),
                })

        for r in invalid_rows:
            report.append({
                "row_index": r["row_index"],
                "name": r["raw_data"].get("name", "Unknown"),
                "status": "Failed",
                "action": "Skipped",
                "reason": "; ".join(r["errors"]),
            })

        return {
            "import_type": "staff",
            "total_rows": len(valid_rows) + len(invalid_rows),
            "success_count": imported_count + updated_count,
            "imported_count": imported_count,
            "updated_count": updated_count,
            "failed_count": len(invalid_rows) + (len(valid_rows) - imported_count - updated_count),
            "skipped_count": len(invalid_rows) + (len(valid_rows) - imported_count - updated_count),
            "report": report,
            "credentials_slips": slips,
        }

    def _execute_team_import(self, valid_rows: List[Dict[str, Any]], invalid_rows: List[Dict[str, Any]], creator) -> Dict[str, Any]:
        report = []
        imported_count = 0

        for r in valid_rows:
            pdata = r["parsed_data"]
            try:
                created_team = self.team_service.create_team(
                    name=pdata["name"],
                    department_id=pdata["department_id"],
                    location_ids=pdata["location_ids"],
                    coordinator_id=pdata["coordinator_id"],
                    backup_coordinator_id=pdata.get("backup_coordinator_id"),
                    member_ids=pdata.get("member_ids", []),
                )
                imported_count += 1
                report.append({
                    "row_index": r["row_index"],
                    "name": pdata["name"],
                    "status": "Success",
                    "action": "Imported",
                    "reason": f"Created team {pdata['name']}.",
                })
            except Exception as e:
                report.append({
                    "row_index": r["row_index"],
                    "name": pdata["name"],
                    "status": "Failed",
                    "action": "Skipped",
                    "reason": str(e),
                })

        for r in invalid_rows:
            report.append({
                "row_index": r["row_index"],
                "name": r["raw_data"].get("team name", r["raw_data"].get("name", "Unknown")),
                "status": "Failed",
                "action": "Skipped",
                "reason": "; ".join(r["errors"]),
            })

        return {
            "import_type": "teams",
            "total_rows": len(valid_rows) + len(invalid_rows),
            "success_count": imported_count,
            "imported_count": imported_count,
            "updated_count": 0,
            "failed_count": len(invalid_rows) + (len(valid_rows) - imported_count),
            "skipped_count": len(invalid_rows) + (len(valid_rows) - imported_count),
            "report": report,
            "credentials_slips": [],
        }

    def _execute_emergency_contacts_import(self, valid_rows: List[Dict[str, Any]], invalid_rows: List[Dict[str, Any]], creator) -> Dict[str, Any]:
        report = []
        imported_count = 0

        for r in valid_rows:
            pdata = r["parsed_data"]
            try:
                contact = self.emergency_service.create_contact(
                    department_id=pdata["department_id"],
                    name=pdata["name"],
                    phone=pdata["phone"],
                    location_id=pdata.get("location_id"),
                    sort_order=pdata.get("sort_order", 1),
                    day_only=pdata.get("day_only", 0),
                    night_only=pdata.get("night_only", 0),
                )
                imported_count += 1
                report.append({
                    "row_index": r["row_index"],
                    "name": pdata["name"],
                    "phone": pdata["phone"],
                    "status": "Success",
                    "action": "Imported",
                    "reason": f"Created emergency contact.",
                })
            except Exception as e:
                report.append({
                    "row_index": r["row_index"],
                    "name": pdata["name"],
                    "phone": pdata["phone"],
                    "status": "Failed",
                    "action": "Skipped",
                    "reason": str(e),
                })

        for r in invalid_rows:
            report.append({
                "row_index": r["row_index"],
                "name": r["raw_data"].get("name", "Unknown"),
                "status": "Failed",
                "action": "Skipped",
                "reason": "; ".join(r["errors"]),
            })

        return {
            "import_type": "emergency_contacts",
            "total_rows": len(valid_rows) + len(invalid_rows),
            "success_count": imported_count,
            "imported_count": imported_count,
            "updated_count": 0,
            "failed_count": len(invalid_rows) + (len(valid_rows) - imported_count),
            "skipped_count": len(invalid_rows) + (len(valid_rows) - imported_count),
            "report": report,
            "credentials_slips": [],
        }

    # -------------------------------------------------------------------------
    # 5. SETUP CHECKLIST WIDGET DATA
    # -------------------------------------------------------------------------
    def get_setup_checklist(self) -> Dict[str, Any]:
        """Provides live counts and checks for the College Setup Checklist:
        - Students imported (count)
        - Locations added (count)
        - Departments / places with no team (list count, link to Teams)
        - Teams with no backup (list count, link to Teams)
        - Locations with no Warden (list count, link to Locations)
        - Coordinators / Wardens without phone number (list count, link to Users)
        - Departments with < 2 emergency contacts (list count, link to Emergency setup)
        """
        # 1. Students count
        students = self.auth_service.list_users(role=ROLE_STUDENT) or []
        students_count = len([s for s in students if getattr(s, "active", True)])

        # 2. Locations count
        locations = self.auth_service.list_locations() or []
        active_locations = [l for l in locations if getattr(l, "active", True) and not getattr(l, "archived", False)]
        locations_count = len(active_locations)

        # 3. Coverage gaps: departments with no coordinator or team
        gaps_data = self.team_service.get_coverage_gaps() if hasattr(self.team_service, "get_coverage_gaps") else {}
        coverage_gaps = (
            gaps_data.get("uncovered_departments")
            or gaps_data.get("uncovered_pairs", [])
            if isinstance(gaps_data, dict)
            else (gaps_data or [])
        )
        uncovered_count = len(coverage_gaps)

        # 4. Teams with no backup
        teams = self.team_service.list_teams() or []
        teams_no_backup = [
            {
                "team_id": t.get("team_id") if isinstance(t, dict) else t.team_id,
                "name": t.get("name") if isinstance(t, dict) else t.name,
            }
            for t in teams
            if (t.get("active", True) if isinstance(t, dict) else getattr(t, "active", True))
            and not (t.get("backup_coordinator_id") if isinstance(t, dict) else getattr(t, "backup_coordinator_id", None))
        ]

        # 5. Locations with no Warden (Hostels and physical locations lacking in_charge_id; excluding system-level Admin-managed locations like LOC_OTHER)
        locations_no_warden = [
            {"location_id": l.location_id, "name": l.name, "type": getattr(l, "location_type", "")}
            for l in active_locations
            if not getattr(l, "in_charge_id", None) and l.location_id != "LOC_OTHER" and not (getattr(l, "name", "") or "").strip().lower().startswith("other")
        ]

        # 6. Coordinators / Wardens without phone number
        all_staff = (self.auth_service.list_users(role=ROLE_COORDINATOR) or []) + \
                    (self.auth_service.list_users(role=ROLE_LOCATION_IN_CHARGE) or [])
        staff_no_phone = [
            {
                "user_id": u.user_id,
                "name": u.name,
                "role": ROLE_DISPLAY_NAMES.get(u.role, u.role),
            }
            for u in all_staff
            if getattr(u, "active", True) and not normalize_phone(getattr(u, "phone_number", None))
        ]

        # 7. Departments with < 2 emergency contacts
        active_depts = [d for d in (self.auth_service.list_departments() or []) if getattr(d, "active", True)]
        dept_contacts = self.emergency_service.list_contacts() if hasattr(self.emergency_service, "list_contacts") else []
        depts_few_contacts = []
        for d in active_depts:
            cnt = sum(1 for c in dept_contacts if c.get("department_id") == d.department_id and c.get("active"))
            if cnt < 2:
                depts_few_contacts.append({
                    "department_id": d.department_id,
                    "name": d.name,
                    "contacts_count": cnt,
                })

        is_complete = (
            students_count > 0 and
            locations_count > 0 and
            uncovered_count == 0 and
            len(teams_no_backup) == 0 and
            len(locations_no_warden) == 0 and
            len(staff_no_phone) == 0 and
            len(depts_few_contacts) == 0
        )

        return {
            "is_complete": is_complete,
            "students": {
                "count": students_count,
                "is_ready": students_count > 0,
                "link": "/admin/users",
            },
            "locations": {
                "count": locations_count,
                "is_ready": locations_count > 0,
                "link": "/admin/locations",
            },
            "uncovered_places": {
                "count": uncovered_count,
                "items": coverage_gaps,
                "is_ready": uncovered_count == 0,
                "link": "/admin/departments",
            },
            "teams_no_backup": {
                "count": len(teams_no_backup),
                "items": teams_no_backup,
                "is_ready": len(teams_no_backup) == 0,
                "link": "/admin/teams",
            },
            "locations_no_warden": {
                "count": len(locations_no_warden),
                "items": locations_no_warden,
                "is_ready": len(locations_no_warden) == 0,
                "link": "/admin/locations",
            },
            "staff_no_phone": {
                "count": len(staff_no_phone),
                "items": staff_no_phone,
                "is_ready": len(staff_no_phone) == 0,
                "link": "/admin/users",
            },
            "departments_few_emergency_contacts": {
                "count": len(depts_few_contacts),
                "items": depts_few_contacts,
                "is_ready": len(depts_few_contacts) == 0,
                "link": "/admin/emergency",
            },
        }

    # -------------------------------------------------------------------------
    # 6. RESET WORKER PASSWORD SLIP
    # -------------------------------------------------------------------------
    def reset_worker_password(self, target_user_id: str, actor_user) -> Dict[str, Any]:
        target_user = self.auth_service.get_user(target_user_id)
        if not target_user:
            raise ValueError("User not found.")

        actor_role = getattr(actor_user, "role", "").lower()
        actor_id = getattr(actor_user, "user_id", "")

        # If coordinator, ensure target user belongs to a team controlled by this coordinator
        if actor_role == ROLE_COORDINATOR:
            teams = self.team_service.list_teams() or []
            controlled_teams = []
            for t in teams:
                c_id = t.get("coordinator_id") if isinstance(t, dict) else getattr(t, "coordinator_id", None)
                b_id = t.get("backup_coordinator_id") if isinstance(t, dict) else getattr(t, "backup_coordinator_id", None)
                if c_id == actor_id or b_id == actor_id:
                    controlled_teams.append(t)

            worker_in_team = False
            for t in controlled_teams:
                m_ids = (t.get("member_ids") if isinstance(t, dict) else getattr(t, "member_ids", None)) or []
                if target_user_id in m_ids:
                    worker_in_team = True
                    break
            if not worker_in_team:
                raise PermissionError("Coordinators can only reset passwords for members of their own team.")
        elif actor_role not in (ROLE_ADMINISTRATOR, ROLE_APP_MANAGER):
            raise PermissionError("Unauthorized to reset worker password.")

        new_temp_pwd = generate_worker_temp_password()
        target_user.password = hash_password(new_temp_pwd)
        target_user.first_login = True
        self.auth_service.save_user(target_user)

        # Invalidate existing user sessions
        from api.security import invalidate_user_sessions
        invalidate_user_sessions(target_user.user_id)

        clean_phone = normalize_phone(getattr(target_user, "phone_number", ""))
        return {
            "user_id": target_user.user_id,
            "name": target_user.name,
            "role": ROLE_DISPLAY_NAMES.get(target_user.role, target_user.role),
            "phone": clean_phone or getattr(target_user, "phone_number", ""),
            "temporary_password": new_temp_pwd,
            "temp_password": new_temp_pwd,
        }
