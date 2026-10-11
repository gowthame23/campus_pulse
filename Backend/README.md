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

## Default Accounts

| Role | Email | Password |
| --- | --- | --- |
| Administrator | gowthamejjurothu@gmail.com | Admin@123 |
| App Manager | ejjurothugowtham@gmail.com | Manager@123 |
| Coordinator | gowthamejjurothu15@gmail.com | Coordinator@123 |
| Student | gowtham.e23@iiits.in | Student@123 |
| Location In-Charge (Warden) | naveen@campus.edu | warden@123 |

Use `/auth/login` to get a bearer token, then authorize in Swagger UI with that token.

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
