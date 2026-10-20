from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import PlainTextResponse

from api.dependencies import (
    get_audit_service,
    get_auth_service,
    get_complaint_service,
    get_department_service,
    get_notification_service,
)
from api.schemas import (
    AdminPasswordResetRequest,
    AssignLocationsRequest,
    AssignDepartmentsRequest,
    EmployeeWorkAssignmentsRequest,
    CoordinatorTransferRequest,
    ExcelImportReportResponse,
    UserActivityResponse,
    UserCreateRequest,
    UserResponse,
    UserResponsibilityUpdateRequest,
    UserStatusUpdateRequest,
    UserUpdateRequest,
    LanguageUpdateRequest,
    user_to_response,
)
from api.security import get_current_user, invalidate_user_sessions, require_roles
from models.administrator import Administrator
from models.app_manager import AppManager
from utils.helper import csv_safe

router = APIRouter(prefix="/users", tags=["users"])


def _hide_super_admin(target_user, current_user):
    """The platform Super Admin is invisible to institution roles."""
    if target_user and target_user.role == "super_admin" and current_user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )


def _enrich_user_response(user, auth_service, all_locs, all_depts):
    d = user_to_response(user)
    if d.get("location_id") and d["location_id"] in all_locs:
        d["location_name"] = all_locs[d["location_id"]]
    if d.get("department_id") and d["department_id"] in all_depts:
        d["department_name"] = all_depts[d["department_id"]]

    u_role = (user.role or "").lower()
    if u_role == "app_manager":
        mgr_locs = auth_service.get_app_manager_locations(user.user_id)
        d["assigned_locations"] = [l.location_id for l in mgr_locs]
        d["assigned_location_names"] = [l.name for l in mgr_locs]
    elif u_role == "location_in_charge":
        warden_locs = auth_service.get_warden_locations(user.user_id)
        d["assigned_locations"] = [l.location_id for l in warden_locs]
        d["assigned_location_names"] = [l.name for l in warden_locs]
    elif u_role in ("coordinator", "employee"):
        coord_asgns = auth_service.list_coordinator_assignments(coordinator_id=user.user_id) or []
        assigned_dept_ids = []
        assigned_dept_names = []
        for a in coord_asgns:
            did = a["department_id"]
            if did not in assigned_dept_ids:
                assigned_dept_ids.append(did)
                assigned_dept_names.append(all_depts.get(did, did))

        if getattr(user, "department_id", None) and user.department_id not in assigned_dept_ids:
            assigned_dept_ids.append(user.department_id)
            assigned_dept_names.append(all_depts.get(user.department_id, user.department_id))

        d["assigned_departments"] = assigned_dept_ids
        d["assigned_department_names"] = assigned_dept_names

        with auth_service._connect() as conn:
            coord_row = conn.execute(
                "SELECT department_id, name, 'Coordinator 1' as pos, 1 as slot FROM departments WHERE coordinator_id = ? "
                "UNION ALL "
                "SELECT department_id, name, 'Coordinator 2' as pos, 2 as slot FROM departments WHERE coordinator_2_id = ?",
                (user.user_id, user.user_id),
            ).fetchone()
            if coord_row:
                d["coordinator_position"] = f"{coord_row['pos']} ({coord_row['name']})"
                d["coordinator_department_id"] = coord_row["department_id"]
                d["coordinator_department_name"] = coord_row["name"]
                d["coordinator_slot"] = coord_row["slot"]
            m_cnt = conn.execute(
                "SELECT COUNT(*) FROM employee_work_memberships WHERE user_id = ?",
                (user.user_id,),
            ).fetchone()[0]
            d["work_memberships_count"] = m_cnt

            dept_rows = conn.execute(
                "SELECT DISTINCT d.department_id, d.name "
                "FROM employee_work_memberships ewm "
                "JOIN departments d ON ewm.department_id = d.department_id "
                "WHERE ewm.user_id = ?",
                (user.user_id,),
            ).fetchall()
            for dr in dept_rows:
                if dr["department_id"] not in d["assigned_departments"]:
                    d["assigned_departments"].append(dr["department_id"])
                    d["assigned_department_names"].append(dr["name"])
    return d


@router.get("", response_model=list[UserResponse])
def list_users(
    role: str | None = None,
    q: str | None = None,
    status_filter: str | None = None,
    department: str | None = None,
    location: str | None = None,
    location_id: str | None = None,
    program: str | None = None,
    hostel: str | None = None,
    block: str | None = None,
    year: str | None = None,
    section: str | None = None,
    designation: str | None = None,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
):
    filters = {
        "status": status_filter,
        "department": department,
        "location": location or location_id,
        "program": program,
        "hostel": hostel,
        "block": block,
        "year": year,
        "section": section,
        "designation": designation,
    }
    users = auth_service.list_users(role=role, search=q, filters=filters)

    all_locs = {l.location_id: l.name for l in auth_service.list_locations()}
    all_depts = {d.department_id: d.name for d in auth_service.list_departments()}

    return [_enrich_user_response(user, auth_service, all_locs, all_depts) for user in users]


@router.get("/paginated")
def list_users_paginated(
    role: str | None = None,
    q: str | None = None,
    status_filter: str | None = None,
    department: str | None = None,
    location: str | None = None,
    location_id: str | None = None,
    program: str | None = None,
    hostel: str | None = None,
    block: str | None = None,
    year: str | None = None,
    section: str | None = None,
    designation: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
):
    from utils.pagination import paginate

    filters = {
        "status": status_filter,
        "department": department,
        "location": location or location_id,
        "program": program,
        "hostel": hostel,
        "block": block,
        "year": year,
        "section": section,
        "designation": designation,
    }
    users = auth_service.list_users(role=role, search=q, filters=filters)
    all_locs = {l.location_id: l.name for l in auth_service.list_locations()}
    all_depts = {d.department_id: d.name for d in auth_service.list_departments()}
    formatted = [_enrich_user_response(u, auth_service, all_locs, all_depts) for u in users]
    return paginate(formatted, page=page, limit=limit)


@router.get("/programs", response_model=list[str])
def get_academic_programs(
    current_user=Depends(get_current_user),
    auth_service=Depends(get_auth_service),
):
    return auth_service.list_academic_programs()


@router.get("/recycle-bin", response_model=list[UserResponse])
def get_recycle_bin_users(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
):
    users = auth_service.list_recycle_bin_users()
    all_locs = {l.location_id: l.name for l in auth_service.list_locations()}
    all_depts = {d.department_id: d.name for d in auth_service.list_departments()}

    res = []
    for user in users:
        d = user_to_response(user)
        if d.get("location_id") and d["location_id"] in all_locs:
            d["location_name"] = all_locs[d["location_id"]]
        if d.get("department_id") and d["department_id"] in all_depts:
            d["department_name"] = all_depts[d["department_id"]]
        res.append(d)
    return res


@router.post("/{user_id}/restore", response_model=UserResponse)
def restore_user(
    user_id: str,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
    audit_service=Depends(get_audit_service),
):
    try:
        restored = auth_service.restore_user_account(user_id, current_user)
        audit_service.log(
            current_user.user_id,
            "Restore User Account",
            user_id,
            old_value={"is_deleted": True},
            new_value={"is_deleted": False, "status": restored.status},
        )
        return user_to_response(restored)
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as v_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(v_err))


@router.get("/export")
def export_filtered_users(
    export_format: str = Query("csv", alias="format"),
    role: str | None = None,
    q: str | None = None,
    status_filter: str | None = None,
    department: str | None = None,
    location: str | None = None,
    location_id: str | None = None,
    program: str | None = None,
    year: str | None = None,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
    audit_service=Depends(get_audit_service),
):
    from fastapi.responses import Response
    import csv
    import io

    filters = {
        "status": status_filter,
        "department": department,
        "location": location or location_id,
        "program": program,
        "year": year,
    }
    users = auth_service.list_users(role=role, search=q, filters=filters)
    all_locs = {l.location_id: l.name for l in auth_service.list_locations()}
    all_depts = {d.department_id: d.name for d in auth_service.list_departments()}

    export_rows = []
    for u in users:
        d = user_to_response(u)
        loc_name = all_locs.get(d.get("location_id"), d.get("location_id") or "")
        dept_name = all_depts.get(d.get("department_id"), d.get("department_id") or "")
        export_rows.append({
            "User ID": csv_safe(d.get("user_id", "")),
            "Name": csv_safe(d.get("name", "")),
            "Email": csv_safe(d.get("email", "")),
            "Role": csv_safe(d.get("role", "")),
            "Status": csv_safe(d.get("status", "")),
            "Phone": csv_safe(d.get("phone_number", "")),
            "Roll Number": csv_safe(d.get("roll_number", "")),
            "Employee ID": csv_safe(d.get("employee_id", "")),
            "Program": csv_safe(d.get("program", "")),
            "Year": csv_safe(d.get("year", "")),
            "Department": csv_safe(dept_name),
            "Current Location": csv_safe(loc_name),
            "Hostel": csv_safe(d.get("hostel", "")),
            "Block": csv_safe(d.get("block", "")),
            "Room Number": csv_safe(d.get("room_number", "")),
        })

    audit_service.log(
        current_user.user_id,
        "Export Users",
        f"Exported {len(export_rows)} users in {export_format.upper()} format",
        old_value=None,
        new_value={"count": len(export_rows), "format": export_format},
    )

    if export_format.lower() == "xlsx":
        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Users Export"
            if export_rows:
                headers = list(export_rows[0].keys())
                ws.append(headers)
                for r in export_rows:
                    ws.append([csv_safe(r[h]) for h in headers])
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            return Response(
                content=output.getvalue(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=campus_pulse_users_export.xlsx"},
            )
        except Exception:
            pass

    output = io.StringIO()
    if export_rows:
        writer = csv.DictWriter(output, fieldnames=list(export_rows[0].keys()))
        writer.writeheader()
        writer.writerows(export_rows)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=campus_pulse_users_export.csv"},
    )


@router.get("/activities/all", response_model=list[UserActivityResponse])
def get_all_activities(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
):
    return auth_service.get_user_activities()


@router.get("/template", response_class=PlainTextResponse)
@router.get("/import/template", response_class=PlainTextResponse)
@router.get("/import/sample-template")
def get_csv_template(format: str = Query("csv")):
    headers = ["Name", "Email", "Roll Number", "Role", "Phone Number", "Department", "Program", "Year", "Current Location", "Hostel", "Block", "Room Number"]
    sample_row = ["Rahul Kumar", "rahul.kumar@campus.edu", "S2026101", "student", "9876543210", "Computer Science", "B.Tech", "3", "Hostel Block A", "Hostel Block A", "Block B", "204"]
    
    if format.lower() == "xlsx":
        try:
            import openpyxl
            import io
            from fastapi.responses import Response
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Student Import Template"
            ws.append(headers)
            ws.append(sample_row)
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            return Response(
                content=output.getvalue(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=student_import_sample_template.xlsx"},
            )
        except Exception:
            pass

    return "Name,Email,Roll Number,Role,Phone Number,Department,Program,Year,Current Location,Hostel,Block,Room Number\nRahul Kumar,rahul.kumar@campus.edu,S2026101,student,9876543210,Computer Science,B.Tech,3,Hostel Block A,Hostel Block A,Block B,204\n"


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: str,
    current_user=Depends(get_current_user),
    auth_service=Depends(get_auth_service),
):
    if (
        current_user.role not in (Administrator.ROLE, AppManager.ROLE)
        and current_user.user_id != user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view this user profile.",
        )
    if current_user.role == AppManager.ROLE and current_user.user_id != user_id:
        # ensure target user is within assigned locations
        assigned = getattr(current_user, "assigned_locations", []) or []
        if assigned:
            target = auth_service.get_user(user_id)
            if target:
                loc = getattr(target, "location_id", None)
                a_locs = getattr(target, "assigned_locations", []) or []
                if not (loc in assigned or any(al in assigned for al in a_locs)):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions to view this user profile.",
                    )
    user = auth_service.get_user(user_id)
    _hide_super_admin(user, current_user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    return user_to_response(user)


@router.get("/{user_id}/activities", response_model=list[UserActivityResponse])
def get_user_activities(
    user_id: str,
    current_user=Depends(get_current_user),
    auth_service=Depends(get_auth_service),
):
    if (
        current_user.role not in (Administrator.ROLE, AppManager.ROLE)
        and current_user.user_id != user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions."
        )
    _hide_super_admin(auth_service.get_user(user_id), current_user)
    return auth_service.get_user_activities(user_id=user_id)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
    audit_service=Depends(get_audit_service),
):
    if payload.confirm_password is not None and payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match."
        )

    try:
        user = auth_service.create_user(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            role=payload.role,
            department_id=payload.department_id,
            location_id=payload.location_id,
            creator=current_user,
            roll_number=payload.roll_number,
            program=payload.program,
            year=payload.year,
            section=payload.section,
            hostel=payload.hostel,
            block=payload.block,
            room_number=payload.room_number,
            employee_id=payload.employee_id,
            designation=payload.designation,
            phone_number=payload.phone_number,
        )

        audit_service.log(
            current_user.user_id,
            "Create User",
            user.user_id,
            old_value=None,
            new_value={"name": user.name, "email": user.email, "role": user.role},
        )

        # Generate activation token & link, and dispatch welcome/activation email
        act_token = None
        act_link = None
        if user.email and not str(user.email).endswith("@worker.campuspulse"):
            try:
                act_token = auth_service.generate_activation_token(user.user_id, user.email)
                act_link = f"/activate?token={act_token}"
                from utils.email import send_activation_email
                send_activation_email(user.email, act_link, user.name)
            except Exception as mail_err:
                pass

        resp_data = user_to_response(user)
        if act_token:
            resp_data["activation_token"] = act_token
            resp_data["activation_link"] = act_link
        return resp_data
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.put("/{user_id}", response_model=UserResponse)
@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    current_user=Depends(get_current_user),
    auth_service=Depends(get_auth_service),
    audit_service=Depends(get_audit_service),
):
    target_user = auth_service.get_user(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    _hide_super_admin(target_user, current_user)

    old_data = user_to_response(target_user)
    updates = payload.dict(exclude_unset=True)

    try:
        updated_user = auth_service.update_user_profile(user_id, updates, current_user)
        new_data = user_to_response(updated_user)
        audit_service.log(
            current_user.user_id,
            "Update Profile",
            user_id,
            old_value=old_data,
            new_value=new_data,
        )
        return new_data
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.put("/{user_id}/responsibility-and-role", response_model=UserResponse)
def update_user_responsibility_and_role(
    user_id: str,
    payload: UserResponsibilityUpdateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
    department_service=Depends(get_department_service),
    audit_service=Depends(get_audit_service),
):
    target_user = auth_service.get_user(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    _hide_super_admin(target_user, current_user)

    if (current_user.role or "").lower() == "app_manager" and target_user.role in ("administrator", "app_manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="App Managers are not authorized to manage Admin or App Manager accounts.",
        )

    old_data = user_to_response(target_user)

    # 1. Update Name if provided
    if payload.name is not None and payload.name.strip():
        target_user.name = payload.name.strip()

    # 2. Update Role if provided
    new_role = (payload.role or "").strip().lower() if payload.role else None
    if new_role and new_role != (target_user.role or "").lower():
        if target_user.role in ("administrator", "super_admin"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot alter administrator system role.",
            )
        valid_roles = ("coordinator", "location_in_charge", "app_manager", "student", "administrator")
        if new_role not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid target role: {new_role}",
            )
        target_user.role = new_role

        # If role changed away from coordinator or employee, deactivate any coordinator roles
        if new_role not in ("employee", "coordinator"):
            all_depts = auth_service.list_departments()
            for d in all_depts:
                changed = False
                if d.coordinator_id == user_id:
                    d.coordinator_id = None
                    changed = True
                if getattr(d, "coordinator_2_id", None) == user_id:
                    d.coordinator_2_id = None
                    changed = True
                if changed:
                    auth_service.save_department(d)
            with auth_service._connect() as conn:
                conn.execute(
                    "UPDATE coordinator_assignments SET status = 'Inactive' WHERE coordinator_id = ?",
                    (user_id,),
                )
                conn.commit()

    # 3. Update Coordinator Responsibility if provided
    coord_type = (payload.coordinator_type or "").strip().lower() if payload.coordinator_type else None
    if coord_type:
        all_depts = auth_service.list_departments()

        if coord_type == "none":
            # Demote/clear to standard operational staff - remove from all coordinator slots
            for d in all_depts:
                changed = False
                if d.coordinator_id == user_id:
                    d.coordinator_id = None
                    changed = True
                if getattr(d, "coordinator_2_id", None) == user_id:
                    d.coordinator_2_id = None
                    changed = True
                if changed:
                    auth_service.save_department(d)
            with auth_service._connect() as conn:
                conn.execute(
                    "UPDATE coordinator_assignments SET status = 'Inactive' WHERE coordinator_id = ?",
                    (user_id,),
                )
                conn.commit()

        elif coord_type in ("coordinator_1", "coordinator_2"):
            if not payload.department_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Department is required for coordinator assignment.",
                )
            target_dept = department_service.get_department(payload.department_id)
            if not target_dept:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Target department not found.",
                )

            # Clear user from any other departments
            for d in all_depts:
                if d.department_id != payload.department_id:
                    changed = False
                    if d.coordinator_id == user_id:
                        d.coordinator_id = None
                        changed = True
                    if getattr(d, "coordinator_2_id", None) == user_id:
                        d.coordinator_2_id = None
                        changed = True
                    if changed:
                        auth_service.save_department(d)

            # Assign to target department slot
            if coord_type == "coordinator_1":
                if getattr(target_dept, "coordinator_2_id", None) == user_id:
                    target_dept.coordinator_2_id = None
                target_dept.coordinator_id = user_id
            else:
                if target_dept.coordinator_id == user_id:
                    target_dept.coordinator_id = None
                target_dept.coordinator_2_id = user_id
            auth_service.save_department(target_dept)

            # Ensure user is eligible for this department so they can service it
            assigned_depts = list(target_user.assigned_departments or [])
            if target_dept.department_id not in assigned_depts:
                assigned_depts.append(target_dept.department_id)
                auth_service.assign_user_departments(user_id, assigned_depts)

    auth_service.save_user(target_user)
    new_data = user_to_response(target_user)
    audit_service.log(
        current_user.user_id,
        "Update Responsibility and Role",
        user_id,
        old_value=old_data,
        new_value=new_data,
    )
    return new_data


@router.put("/{user_id}/status", response_model=UserResponse)
@router.patch("/{user_id}/status", response_model=UserResponse)
def patch_user_status(
    user_id: str,
    payload: UserStatusUpdateRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
    audit_service=Depends(get_audit_service),
    complaint_service=Depends(get_complaint_service),
):
    target_user = auth_service.get_user(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    _hide_super_admin(target_user, current_user)

    if (current_user.role or "").lower() == "app_manager" and target_user.role in ("administrator", "app_manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="App Managers are not authorized to manage Admin or App Manager accounts."
        )

    if current_user.user_id == user_id and payload.status != "Active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate or suspend your own account.",
        )

    if payload.status != "Active" and target_user.role == "coordinator":
        pending = [
            c
            for c in complaint_service.list_all()
            if c.assigned_to == user_id
            and c.status not in ("Closed", "Closed (Auto Closed)")
        ]
        if len(pending) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change Coordinator status. Coordinator has {len(pending)} active complaints. Transfer complaints first.",
            )

    if payload.status != "Active" and target_user.role == "administrator":
        active_admins = [
            u for u in auth_service.list_users("administrator") if u.status == "Active"
        ]
        if len(active_admins) <= 1 and target_user.user_id in [
            u.user_id for u in active_admins
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="System must always contain at least one active Admin.",
            )

    try:
        old_status = target_user.status
        updated_user = auth_service.update_user_status(
            user_id, payload.status, current_user, remarks=payload.remarks
        )
        audit_service.log(
            current_user.user_id,
            "Update User Status",
            user_id,
            old_value={"status": old_status},
            new_value={"status": payload.status, "remarks": payload.remarks},
        )
        return user_to_response(updated_user)
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/{user_id}/deletion-impact")
def get_user_deletion_impact(
    user_id: str,
    current_user=Depends(require_roles(Administrator.ROLE)),
    auth_service=Depends(get_auth_service),
):
    """Reports every existing reference to this user across the schema, so
    the Force Delete confirmation can show what will be preserved before the
    Administrator confirms. Read-only — performs no deletion."""
    target_user = auth_service.get_user(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    _hide_super_admin(target_user, current_user)
    return auth_service.check_user_dependencies(user_id)


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: str,
    current_user=Depends(require_roles(Administrator.ROLE)),
    auth_service=Depends(get_auth_service),
    audit_service=Depends(get_audit_service),
):
    _hide_super_admin(auth_service.get_user(user_id), current_user)
    try:
        # Force Delete is always resolved to the safe soft-delete path below:
        # this app's schema has no ON DELETE CASCADE, so a physical DELETE
        # from `users` would silently orphan every complaint/notification/
        # audit_log/etc. that references this user_id. Checked and logged
        # here (never blind-deleted) so the audit trail shows what was
        # preserved, matching the FK-safety requirement.
        dependencies = auth_service.check_user_dependencies(user_id)

        deleted_user = auth_service.delete_user_account(user_id, current_user)
        audit_service.log(
            current_user.user_id,
            "Force Delete User (soft-delete, history preserved)",
            user_id,
            old_value=user_to_response(deleted_user),
            new_value={"preserved_references": dependencies["by_source"]},
        )
        return {
            "message": "User deleted. Historical records referencing this user were preserved.",
            "preserved_references": dependencies["by_source"],
        }
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as v_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(v_err))


@router.post("/transfer-coordinator")
def transfer_coordinator(
    payload: CoordinatorTransferRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
    complaint_service=Depends(get_complaint_service),
    notification_service=Depends(get_notification_service),
    audit_service=Depends(get_audit_service),
):
    old_coord = auth_service.get_user(payload.old_coordinator_id)
    new_coord = auth_service.get_user(payload.new_coordinator_id)
    if not old_coord or old_coord.role != "coordinator":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old coordinator not found or invalid.",
        )
    if not new_coord or new_coord.role != "coordinator":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New coordinator not found or invalid.",
        )

    assigned_complaints = [
        c
        for c in complaint_service.list_all(include_archived=True)
        if c.assigned_to == payload.old_coordinator_id
    ]

    for complaint in assigned_complaints:
        complaint.assigned_to = payload.new_coordinator_id
        complaint.add_history(
            f"Coordinator changed from {old_coord.name} to {new_coord.name}. Reason: Transferred during account deactivation."
        )
        complaint_service.save_complaint(complaint)

    if len(assigned_complaints) > 0:
        notification_service.notify(
            payload.new_coordinator_id,
            f"You have been assigned {len(assigned_complaints)} complaints from {old_coord.name}.",
        )

    auth_service.update_user_status(
        payload.old_coordinator_id,
        "Inactive",
        current_user,
        remarks="Deactivated after coordinator transfer",
    )

    audit_service.log(
        current_user.user_id,
        "Transfer Coordinator Complaints",
        payload.old_coordinator_id,
        old_value={
            "status": old_coord.status,
            "assigned_count": len(assigned_complaints),
        },
        new_value={"status": "Inactive", "transferred_to": payload.new_coordinator_id},
    )
    return {
        "message": f"Successfully transferred {len(assigned_complaints)} complaints to {new_coord.name} and deactivated {old_coord.name}."
    }


@router.put("/{user_id}/reset-password", response_model=UserResponse)
def reset_user_password(
    user_id: str,
    payload: AdminPasswordResetRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
):
    target_user = auth_service.get_user(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    _hide_super_admin(target_user, current_user)

    new_password = payload.new_password
    if not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="new_password is required."
        )

    if (current_user.role or "").lower() == AppManager.ROLE.lower():
        if (target_user.role or "").lower() not in ("coordinator", "location_in_charge", "student", "employee"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="App Managers can only reset passwords for Coordinators, Employees, Wardens, or Students.",
            )
    elif (current_user.role or "").lower() == Administrator.ROLE.lower():
        if (target_user.role or "").lower() == "super_admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Administrators cannot reset Super Admin passwords.",
            )

    from utils.passwords import hash_password, validate_password_complexity

    if not validate_password_complexity(new_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password complexity requirements not met (min 8 chars, 1 uppercase, 1 lowercase, 1 number, 1 special character).",
        )

    target_user.password = hash_password(new_password)
    target_user.first_login = True
    auth_service.save_user(target_user)
    invalidate_user_sessions(user_id)
    return user_to_response(target_user)


@router.post("/{user_id}/resend-activation")
def resend_activation_email(
    user_id: str,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
):
    target_user = auth_service.get_user(user_id)
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    if not target_user.email or str(target_user.email).endswith("@worker.campuspulse"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot send activation link to an account without a valid email address.",
        )
    act_token = auth_service.generate_activation_token(target_user.user_id, target_user.email)
    act_link = f"/activate?token={act_token}"
    try:
        from utils.email import send_activation_email
        send_activation_email(target_user.email, act_link, target_user.name)
    except Exception as mail_err:
        pass
    return {
        "message": f"Activation email dispatched successfully to {target_user.email}.",
        "activation_token": act_token,
        "activation_link": act_link,
    }


@router.post("/import", response_model=ExcelImportReportResponse)
def import_users(
    file: UploadFile = File(...),
    program: str | None = Form(None),
    academic_year: str | None = Form(None),
    year: str | None = Form(None),
    location_id: str | None = Form(None),
    update_existing: bool = Form(False),
    default_program: str | None = Form(None),
    default_academic_year: str | None = Form(None),
    default_year: str | None = Form(None),
    default_location_id: str | None = Form(None),
    q_program: str | None = Query(None, alias="program"),
    q_academic_year: str | None = Query(None, alias="academic_year"),
    q_year: str | None = Query(None, alias="year"),
    q_location_id: str | None = Query(None, alias="location_id"),
    q_default_program: str | None = Query(None, alias="default_program"),
    q_default_academic_year: str | None = Query(None, alias="default_academic_year"),
    q_default_year: str | None = Query(None, alias="default_year"),
    q_default_location_id: str | None = Query(None, alias="default_location_id"),
    q_update_existing: bool | None = Query(None, alias="update_existing"),
    current_user=Depends(require_roles(AppManager.ROLE, Administrator.ROLE)),
    auth_service=Depends(get_auth_service),
    audit_service=Depends(get_audit_service),
):
    from utils.excel_importer import parse_user_import_file

    eff_program = program or default_program or q_program or q_default_program
    eff_academic_year = academic_year or default_academic_year or q_academic_year or q_default_academic_year
    eff_year = year or default_year or q_year or q_default_year
    eff_location_id = location_id or default_location_id or q_location_id or q_default_location_id
    eff_update_existing = bool(update_existing or q_update_existing)

    file_bytes = file.file.read()
    report_data = parse_user_import_file(
        file_contents=file_bytes,
        filename=file.filename or "import.csv",
        auth_service=auth_service,
        creator=current_user,
        default_program=eff_program,
        default_academic_year=eff_academic_year,
        default_year=eff_year,
        default_location_id=eff_location_id,
        update_existing=eff_update_existing,
    )

    audit_service.log(
        current_user.user_id,
        "Excel Import Users",
        f"Total: {report_data['total_rows']}, Success: {report_data['success_count']}, Failed: {report_data['failed_count']}",
        old_value=None,
        new_value={
            **report_data,
            "report": [
                {
                    k: v
                    for k, v in row.items()
                    if k not in ("temporary_password", "activation_token", "activation_link")
                }
                for row in report_data["report"]
            ],
        },
    )

    return report_data


@router.get("/audit-logs/list")
def list_audit_logs(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    audit_service=Depends(get_audit_service),
):
    return audit_service.list_logs()


@router.get("/audit-logs/paginated")
def list_audit_logs_paginated(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    audit_service=Depends(get_audit_service),
):
    from utils.pagination import paginate

    logs = audit_service.list_logs()
    return paginate(logs, page=page, limit=limit)


@router.get("/app-managers/assignments")
def get_app_manager_assignments(
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
):
    result = auth_service.get_app_manager_assignments()
    if (current_user.role or "").lower() == AppManager.ROLE.lower():
        # App Managers may only see their own assigned-locations entry, plus
        # the genuinely-unassigned list (which belongs to no one) — never
        # another App Manager's assignments.
        result = {
            "app_managers": [
                m for m in result["app_managers"] if m["user_id"] == current_user.user_id
            ],
            "unassigned_locations": result["unassigned_locations"],
        }
    return result


@router.post("/{user_id}/assigned-locations")
@router.put("/{user_id}/assigned-locations")
def assign_app_manager_locations(
    user_id: str,
    payload: AssignLocationsRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
):
    try:
        updated_user = auth_service.assign_app_manager_locations(user_id, payload.location_ids)
        return {
            "message": "Assigned locations updated successfully.",
            "assigned_locations": updated_user.assigned_locations,
        }
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/{user_id}/assigned-departments")
@router.put("/{user_id}/assigned-departments")
def assign_employee_departments(
    user_id: str,
    payload: AssignDepartmentsRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
    audit_service=Depends(get_audit_service),
):
    try:
        updated_user = auth_service.assign_user_departments(
            user_id, payload.department_ids, caller_user=current_user
        )
        all_depts = {d.department_id: d.name for d in auth_service.list_departments()}
        dept_names = [all_depts.get(did, did) for did in payload.department_ids]
        audit_service.log(
            current_user.user_id,
            "Assign Eligible Departments",
            user_id,
            old_value=None,
            new_value={"department_ids": payload.department_ids, "department_names": dept_names},
        )
        return {
            "message": "Eligible departments updated successfully.",
            "assigned_departments": payload.department_ids,
            "assigned_department_names": dept_names,
        }
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))


@router.post("/{user_id}/employee-work-assignments")
@router.put("/{user_id}/employee-work-assignments")
def assign_employee_work_assignments(
    user_id: str,
    payload: EmployeeWorkAssignmentsRequest,
    current_user=Depends(require_roles(Administrator.ROLE, AppManager.ROLE)),
    auth_service=Depends(get_auth_service),
    audit_service=Depends(get_audit_service),
):
    try:
        updated_user = auth_service.assign_employee_work_assignments(
            user_id, payload.department_ids, payload.location_ids, caller_user=current_user
        )
        all_depts = {d.department_id: d.name for d in auth_service.list_departments()}
        dept_names = [all_depts.get(did, did) for did in payload.department_ids]
        audit_service.log(
            current_user.user_id,
            "Assign Employee Work Assignments",
            user_id,
            old_value=None,
            new_value={
                "department_ids": payload.department_ids,
                "department_names": dept_names,
                "location_ids": payload.location_ids,
            },
        )
        return {
            "message": "Employee work assignments updated successfully.",
            "assigned_departments": payload.department_ids,
            "assigned_department_names": dept_names,
            "assigned_locations": payload.location_ids,
        }
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    except PermissionError as p_err:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))


@router.put("/me/language")
def update_my_language(
    payload: LanguageUpdateRequest,
    current_user=Depends(get_current_user),
    auth_service=Depends(get_auth_service),
    audit_service=Depends(get_audit_service),
):
    """Update preferred UI language for current user ('en', 'te', 'hi')."""
    old_lang = getattr(current_user, "language", "en")
    current_user.language = payload.language
    auth_service.save_user(current_user)
    audit_service.log(
        current_user.user_id,
        "Update Language Preference",
        current_user.user_id,
        old_value={"language": old_lang},
        new_value={"language": payload.language},
    )
    return {"message": "Language preference updated successfully.", "language": payload.language}
