import csv
import io
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


def _parse_csv_rows(file_contents):
    text = file_contents.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    return [(idx, row) for idx, row in enumerate(reader, start=2)]  # Row 1 is header


def parse_user_import_file(
    file_contents: bytes,
    filename: str,
    auth_service,
    creator,
    default_program: Optional[str] = None,
    default_academic_year: Optional[str] = None,
    default_year: Optional[str] = None,
    default_location_id: Optional[str] = None,
    update_existing: bool = False,
) -> Dict[str, Any]:
    report_rows = []
    success_count = 0
    failed_count = 0

    rows_data = []

    # Parse CSV or Excel
    if filename.endswith(".csv"):
        rows_data = _parse_csv_rows(file_contents)
    elif filename.endswith(".xlsx") or filename.endswith(".xls"):
        try:
            import openpyxl
            wb = openpyxl.load_workbook(filename=io.BytesIO(file_contents), data_only=True)
            sheet = wb.active
            headers = [str(cell.value or "").strip().lower() for cell in sheet[1]]
            for idx, row in enumerate(sheet.iter_rows(min_row=2, values_only=True), start=2):
                row_dict = {}
                for h, val in zip(headers, row):
                    if h:
                        row_dict[h] = str(val).strip() if val is not None else ""
                rows_data.append((idx, row_dict))
        except Exception:
            rows_data = _parse_csv_rows(file_contents)
    else:
        rows_data = _parse_csv_rows(file_contents)

    # Pre-fetch locations and departments for human-readable resolution
    all_locations = auth_service.list_locations() or []
    all_departments = auth_service.list_departments() or []

    loc_map = {}
    for l in all_locations:
        loc_map[l.location_id.lower()] = l.location_id
        if getattr(l, "name", None):
            loc_map[l.name.lower()] = l.location_id

    dept_map = {}
    for d in all_departments:
        dept_map[d.department_id.lower()] = d.department_id
        if getattr(d, "name", None):
            dept_map[d.name.lower()] = d.department_id

    for row_idx, row in rows_data:
        norm = {k.strip().lower(): str(v).strip() for k, v in row.items() if k}
        role = norm.get("role", "student").strip()
        name = norm.get("name", "") or norm.get("full_name", "")
        email = norm.get("email", "")
        roll_number = norm.get("roll_number", "") or norm.get("roll_no", "")
        employee_id = norm.get("employee_id", "") or norm.get("emp_id", "")
        raw_dept = norm.get("department_id", "") or norm.get("department", "")
        raw_loc = norm.get("location_id", "") or norm.get("location", "") or norm.get("current_location", "") or default_location_id
        phone_number = norm.get("phone_number", "") or norm.get("phone", "")
        program = norm.get("program") or default_program
        year = norm.get("year") or default_year

        identifier = roll_number or employee_id or email or f"Row {row_idx}"

        if not name or not email:
            report_rows.append({
                "row_index": row_idx,
                "identifier": identifier,
                "name": name or "Unknown",
                "role": role,
                "status": "Failed",
                "reason": "Name and Email are required."
            })
            failed_count += 1
            continue

        # Resolve human-readable location or direct ID
        location_id = None
        if raw_loc:
            resolved = loc_map.get(raw_loc.strip().lower())
            if not resolved:
                loc_obj = auth_service.get_location(raw_loc.strip())
                if loc_obj:
                    resolved = loc_obj.location_id
            if resolved:
                location_id = resolved
            else:
                location_id = raw_loc.strip()

        # Resolve human-readable department or direct ID
        department_id = None
        if raw_dept:
            resolved = dept_map.get(raw_dept.strip().lower())
            if not resolved:
                dept_obj = auth_service.get_department(raw_dept.strip())
                if dept_obj:
                    resolved = dept_obj.department_id
            if resolved:
                department_id = resolved
            else:
                department_id = raw_dept.strip()

        # Handle updating existing students (Section 7, 8, 9 Student Movement)
        if update_existing:
            existing_user = None
            if email:
                existing_user = auth_service.get_user_by_email(email)
            if not existing_user and roll_number:
                existing_user = auth_service.get_user_by_roll_number(roll_number)

            if existing_user and (existing_user.role or "").lower() == "student":
                try:
                    updates = {
                        "name": name or existing_user.name,
                        "location_id": location_id or existing_user.location_id,
                        "program": program or getattr(existing_user, "program", None),
                        "year": year or getattr(existing_user, "year", None),
                        "section": norm.get("section") or getattr(existing_user, "section", None),
                        "hostel": norm.get("hostel") or getattr(existing_user, "hostel", None),
                        "block": norm.get("block") or getattr(existing_user, "block", None),
                        "room_number": norm.get("room_number") or getattr(existing_user, "room_number", None),
                        "department_id": department_id or existing_user.department_id,
                        "phone_number": phone_number or getattr(existing_user, "phone_number", None),
                    }
                    auth_service.update_user_profile(existing_user.user_id, updates, creator)
                    report_rows.append({
                        "row_index": row_idx,
                        "identifier": identifier,
                        "name": updates["name"],
                        "email": existing_user.email,
                        "role": existing_user.role,
                        "action": "updated",
                        "temporary_password": None,
                        "status": "Success",
                        "reason": "Updated existing student record (movement / progression)."
                    })
                    success_count += 1
                    continue
                except Exception as err:
                    report_rows.append({
                        "row_index": row_idx,
                        "identifier": identifier,
                        "name": name,
                        "email": email,
                        "role": role,
                        "action": "updated",
                        "temporary_password": None,
                        "status": "Failed",
                        "reason": f"Update failed: {str(err)}"
                    })
                    failed_count += 1
                    continue

        try:
            created_user = auth_service.create_user(
                name=name,
                email=email,
                password=norm.get("password", "").strip(),
                role=role,
                department_id=department_id if department_id else None,
                location_id=location_id if location_id else None,
                creator=creator,
                roll_number=roll_number if roll_number else None,
                employee_id=employee_id if employee_id else None,
                phone_number=phone_number if phone_number else None,
                program=program,
                year=year,
                section=norm.get("section"),
                hostel=norm.get("hostel"),
                designation=norm.get("designation")
            )
            act_token = auth_service.generate_activation_token(created_user.user_id, created_user.email)
            act_link = f"/activate?token={act_token}"

            # Automatically dispatch activation email if account was created
            try:
                from utils.email import send_activation_email
                send_activation_email(created_user.email, act_link, created_user.name)
            except Exception as mail_err:
                logger.warning(
                    f"Failed to dispatch activation email for {created_user.email}: {mail_err}"
                )

            report_rows.append({
                "row_index": row_idx,
                "identifier": identifier,
                "name": created_user.name,
                "email": created_user.email,
                "role": created_user.role,
                "action": "created",
                "temporary_password": created_user.temporary_password,
                "activation_token": act_token,
                "activation_link": act_link,
                "status": "Success",
                "reason": None
            })
            success_count += 1
        except Exception as err:
            report_rows.append({
                "row_index": row_idx,
                "identifier": identifier,
                "name": name,
                "email": email,
                "role": role,
                "temporary_password": None,
                "status": "Failed",
                "reason": str(err)
            })
            failed_count += 1

    return {
        "total_rows": len(rows_data),
        "success_count": success_count,
        "failed_count": failed_count,
        "report": report_rows
    }
