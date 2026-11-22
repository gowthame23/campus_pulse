# Campus Pulse - FastAPI Backend

REST and WebSocket backend for the Campus Pulse campus complaint management platform. See the root `README.md` for full setup and deployment notes.

## Install API Dependencies

```bash
pip install -r requirements.txt
```

## Run the FastAPI Backend

```bash
python run_api.py
```

Then open:

```text
http://127.0.0.1:8000/docs
```

Copy `.env.example` to `.env` first. For a local run without PostgreSQL, set `DB_ENGINE=sqlite`; the app then creates `storage/campus_pulse.db` automatically.

## Initial Accounts

Production (`ENVIRONMENT=production`) seeds no demo accounts. The administrator and app manager accounts come from `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `MANAGER_EMAIL` and `MANAGER_PASSWORD`, which must be set before the first start.

For local development on a fresh database, other seeded accounts get a random password that must be changed on first login. Set `ALLOW_DEMO_SEED_PASSWORDS=true` in `.env` to use the well-known demo passwords instead. Never set it in a real deployment.

Use `/auth/login` to get a bearer token, then authorize in Swagger UI with that token.

## Automated Test Execution

```bash
python -m pytest tests -v
```

## Backend Architecture

- `models/`: existing domain entities.
- `services/`: business logic used by the API routers.
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

The API does not duplicate complaint workflow rules. Endpoint functions validate HTTP input, enforce role access, and call the services.
