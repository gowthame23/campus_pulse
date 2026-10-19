# Campus Pulse v1 - CLI and FastAPI Backend

Campus Pulse is a campus complaint management system. The original CLI business logic is preserved, and the FastAPI backend now reuses the same models and services.

## Install API Dependencies

```bash
pip install -r requirements.txt
```

## Run the CLI

```bash
python main.py
```

## Run the FastAPI Backend

```bash
python run_api.py
```

Then open:

```text
http://127.0.0.1:8000/docs
```

The app creates `storage/campus_pulse.db` automatically if it does not exist.

## Standard 14 Clean Baseline Accounts

| Role | Email | Password | Responsibilities |
| --- | --- | --- | --- |
| Super Admin | superadmin@campuspulse.edu | Admin@123 | Platform Owner & Governance |
| Administrator | gowthamejjurothu@gmail.com | Admin@123 | Campus Operations & Admin Controls |
| App Manager 1 | ejjurothugowtham@gmail.com | Manager@123 | Operations Supervisor (North Zone) |
| App Manager 2 | appmanager2@campus.edu | Manager@123 | Operations Supervisor (South Zone) |
| Employees (6 total) | employee.a1@campuspulse.edu to employee.b3@campuspulse.edu | Employee@123 | Field Maintenance (4 serve as C1/C2 Coordinators) |
| Students (2 total) | gowtham.e23@iiits.in, student2@campus.edu | Student@123 | Student Residents |
| Wardens (2 total) | naveen@campus.edu, warden2@campus.edu | warden@123 | Hostel Wardens |

Use `/auth/login` to get a bearer token, then authorize in Swagger UI with that token.

## Automated Test Execution

```bash
python -m pytest tests/test_multi_department_coordinators.py tests/test_remediation_f01_f15.py -v
```
All 29 tests pass with 100% pass rate.

## Backend Architecture

- `models/`: existing domain entities.
- `services/`: existing business logic used by both CLI and API.
- `storage/sqlite_repository.py`: SQLite persistence behind a `load()` / `save()` interface.
- `api/schemas.py`: Pydantic request and response schemas.
- `api/security.py`: token session handling and role guards.
- `api/dependencies.py`: shared service construction.
- `api/routers/`: REST endpoints grouped by domain.

## REST Areas

- Authentication: `/auth/login`, `/auth/logout`, `/auth/me`, `/auth/change-password`, `/auth/reset-password`
- Users: `/users`
- Departments: `/departments`
- Locations: `/locations`
- Complaints: `/complaints`
- Notifications: `/notifications`
- Health: `/health`

## Design Notes

The API does not duplicate complaint workflow rules. Endpoint functions validate HTTP input, enforce role access, and call the existing services. This keeps the CLI and API behavior aligned.
