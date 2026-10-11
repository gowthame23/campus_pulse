import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import get_complaint_service, get_config_service
from middleware.rate_limiter import rate_limit_middleware
from services.scheduler_service import create_scheduler
from utils.logger import get_logger
from utils.websocket_manager import manager as ws_manager

logger = get_logger(__name__)

scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    # Register the running event loop so WebSocket pushes triggered from
    # sync route handlers (which run in a threadpool) can reach it.
    ws_manager.set_loop(asyncio.get_running_loop())
    # Startup: Start background scheduler
    logger.info("Initializing background scheduler...")
    complaint_svc = get_complaint_service()
    config_svc = get_config_service()
    scheduler = create_scheduler(complaint_svc, config_svc)
    scheduler.start()
    yield
    # Shutdown: Stop scheduler gracefully
    if scheduler:
        scheduler.stop()


app = FastAPI(
    title="Campus Pulse API",
    description="REST backend for Campus Pulse complaint management.",
    version="1.0.0",
    lifespan=lifespan,
)

import os

env_type = os.getenv("ENVIRONMENT", "development").lower()
cors_env = os.getenv("CORS_ORIGINS")
if env_type == "production" and not cors_env:
    # Previously this only logged a warning and silently fell back to the
    # localhost dev origins, which means a misconfigured production deploy
    # would boot "successfully" while actually rejecting the real frontend's
    # origin (a startup-time failure is far easier to notice and fix than
    # mysterious CORS errors in the browser console after launch).
    raise RuntimeError(
        "CORS_ORIGINS must be explicitly set when ENVIRONMENT=production. "
        "Refusing to silently fall back to localhost origins in production."
    )

cors_origins = (cors_env or "http://127.0.0.1:5173,http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Cache-Control"] = "no-store"
    # HSTS only makes sense once the connection is actually HTTPS -- forcing
    # it during local HTTP development would make browsers refuse to connect
    # over plain http:// afterward. request.url.scheme reflects Starlette's
    # own view of the connection; x-forwarded-proto covers the common case of
    # running behind a reverse proxy that terminates TLS.
    is_https = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
    if is_https:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Register rate limiter middleware for sensitive auth routes
app.middleware("http")(rate_limit_middleware)


@app.middleware("http")
async def log_request_middleware(request: Request, call_next):
    start_time = time.time()

    # Try to extract user info from token
    user_id = "anonymous"
    user_role = "anonymous"

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        from api.security import _lookup_session

        session = _lookup_session(token)
        if session:
            from api.dependencies import get_auth_service

            auth_svc = get_auth_service()
            user = auth_svc.get_user(session["user_id"])
            if user:
                user_id = user.user_id
                user_role = user.role

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000

    logger.info(
        f"Method: {request.method} | Path: {request.url.path} | "
        f"Status: {response.status_code} | Time: {process_time:.2f}ms | "
        f"User: {user_id} | Role: {user_role} | "
        f"IP: {request.client.host if request.client else 'unknown'}"
    )
    return response





@app.get("/", tags=["root"])
def root_index():
    return {
        "message": "Campus Pulse API is running",
        "docs": "http://127.0.0.1:8000/docs",
        "redoc": "http://127.0.0.1:8000/redoc",
        "health": "http://127.0.0.1:8000/health"
    }


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}


import traceback

from fastapi.responses import JSONResponse


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Skip logging common HTTPExceptions to keep logs clean
    if hasattr(exc, "status_code") and exc.status_code < 500:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": str(exc.detail) if hasattr(exc, "detail") else str(exc)},
        )

    user_id = "unknown"
    if hasattr(request.state, "user"):
        user_id = getattr(request.state.user, "user_id", "unknown")

    logger.error(
        f"Time: - | User: {user_id} | Route: {request.url.path} | Exception: {type(exc).__name__}: {str(exc)}\nStack Trace:\n{''.join(traceback.format_tb(exc.__traceback__))}"
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


from api.routers import (
    analytics,
    announcements,
    attachments,
    audit,
    auth,
    backups,
    chat,
    complaints,
    dashboard,
    departments,
    feedback,
    issues,
    locations,
    lost_found,
    master,
    notifications,
    platform,
    programs,
    public_complaints,
    reports,
    search,
    settings,
    supervisor,
    users,
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(departments.router)
app.include_router(locations.router)
app.include_router(issues.router)
app.include_router(complaints.router)
app.include_router(public_complaints.router)
app.include_router(dashboard.router)
app.include_router(notifications.router)
app.include_router(settings.router)
app.include_router(attachments.router)
app.include_router(analytics.router)
app.include_router(audit.router)
app.include_router(lost_found.router)
app.include_router(announcements.router)
app.include_router(feedback.router)
app.include_router(reports.router)
app.include_router(search.router)
app.include_router(backups.router)
app.include_router(chat.router)
app.include_router(supervisor.router)
app.include_router(master.router)
app.include_router(programs.router)

app.include_router(platform.router)
