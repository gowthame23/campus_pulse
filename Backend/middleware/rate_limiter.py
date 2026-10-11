import json
import os
import sqlite3
import time
from collections import defaultdict

from fastapi import Request, status

from utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter using sliding window log with configurable thresholds."""

    def __init__(
        self,
        max_requests: int = None,
        window_seconds: int = None,
        lockout_seconds: int = None,
    ):
        self.max_requests = (
            max_requests
            if max_requests is not None
            else int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "30"))
        )
        self.window_seconds = (
            window_seconds
            if window_seconds is not None
            else int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
        )
        self.lockout_seconds = (
            lockout_seconds
            if lockout_seconds is not None
            else int(os.getenv("RATE_LIMIT_LOCKOUT_SECONDS", "900"))
        )
        self._requests = defaultdict(list)  # ip -> [timestamps]
        self._lockouts = {}  # ip -> lockout_until timestamp

    def _cleanup(self, ip: str):
        """Remove expired timestamps."""
        now = time.time()
        cutoff = now - self.window_seconds
        self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]

    def is_locked(self, ip: str) -> bool:
        lockout_until = self._lockouts.get(ip)
        if lockout_until and time.time() < lockout_until:
            return True
        elif lockout_until:
            del self._lockouts[ip]
        return False

    def check(self, ip: str) -> bool:
        """Returns True if request is allowed, False if rate limited."""
        if self.is_locked(ip):
            return False

        self._cleanup(ip)
        now = time.time()

        if len(self._requests[ip]) >= self.max_requests:
            # Lock out the IP
            self._lockouts[ip] = now + self.lockout_seconds
            logger.warning(
                f"Rate limit exceeded for IP {ip}. Locked out for {self.lockout_seconds}s."
            )
            return False

        self._requests[ip].append(now)
        return True


# General per-IP auth limiter instance
auth_limiter = RateLimiter(
    max_requests=int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "30")),
    window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
    lockout_seconds=int(os.getenv("RATE_LIMIT_LOCKOUT_SECONDS", "60")),
)

# Protected paths that should be rate-limited
RATE_LIMITED_PATHS = {
    "/auth/login",
    "/auth/reset-password",
    "/auth/password-reset/request",
    "/auth/password-reset/verify",
    "/auth/password-reset/complete",
    "/auth/change-password",
}


def _get_db_path(db_path: str = None) -> str:
    if db_path is not None:
        return db_path
    return os.environ.get("DATABASE_PATH", "storage/campus_pulse.db")


def check_login_lockout(ip: str, email: str, db_path: str = None) -> tuple[bool, int]:
    """
    Checks SQLite-backed login attempts:
    5 failed attempts per email+IP within 15 minutes -> 429 for 15 minutes.
    Returns (is_locked, remaining_seconds).
    """
    email_clean = (email or "").strip().lower()
    if not email_clean:
        return False, 0

    path = _get_db_path(db_path)
    now_ts = time.time()
    cutoff = now_ts - 900  # 15 minutes window

    try:
        with sqlite3.connect(path, timeout=5.0) as conn:
            cursor = conn.execute(
                """
                SELECT attempted_at FROM login_rate_limits
                WHERE email = ? AND ip = ? AND attempted_at >= ?
                ORDER BY attempted_at DESC
                """,
                (email_clean, ip, cutoff),
            )
            rows = cursor.fetchall()
            if len(rows) >= 5:
                latest_ts = rows[0][0]
                lockout_until = latest_ts + 900
                if now_ts < lockout_until:
                    remaining = max(1, int(lockout_until - now_ts))
                    return True, remaining
    except Exception as e:
        logger.warning(f"Error checking login lockout in SQLite: {e}")

    return False, 0


def record_login_attempt(ip: str, email: str, success: bool = False, db_path: str = None):
    """Record login failure or clear attempts on success across worker processes."""
    email_clean = (email or "").strip().lower()
    if not email_clean:
        return

    path = _get_db_path(db_path)
    now_ts = time.time()

    try:
        with sqlite3.connect(path, timeout=5.0) as conn:
            if success:
                conn.execute("DELETE FROM login_rate_limits WHERE email = ?", (email_clean,))
                conn.commit()
            else:
                conn.execute(
                    "INSERT INTO login_rate_limits (ip, email, attempted_at) VALUES (?, ?, ?)",
                    (ip, email_clean, now_ts),
                )
                conn.commit()
    except Exception as e:
        logger.warning(f"Error recording login attempt in SQLite: {e}")


def prune_login_rate_limits(db_path: str = None):
    """Periodic pruning of old login attempt records (older than 15 minutes)."""
    path = _get_db_path(db_path)
    cutoff = time.time() - 900
    try:
        with sqlite3.connect(path, timeout=5.0) as conn:
            conn.execute("DELETE FROM login_rate_limits WHERE attempted_at < ?", (cutoff,))
            conn.commit()
    except Exception as e:
        logger.warning(f"Error pruning login rate limits in SQLite: {e}")


async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting sensitive auth endpoints across workers."""
    path = request.url.path

    if request.method == "POST" and path in RATE_LIMITED_PATHS:
        client_ip = request.client.host if request.client else "unknown"

        # Check per-email+IP SQLite-backed login rate limiter for /auth/login
        if path == "/auth/login" and client_ip != "testclient" and os.environ.get("TESTING") != "1":
            try:
                body_bytes = await request.body()
                if body_bytes:
                    payload = json.loads(body_bytes.decode("utf-8"))
                    username = payload.get("username") or payload.get("email") or ""
                    if username:
                        is_locked, remaining = check_login_lockout(client_ip, username)
                        if is_locked:
                            logger.warning(
                                f"LOGIN RATE LIMITED | IP: {client_ip} | Account: {username} | "
                                f"Lockout remaining: {remaining}s"
                            )
                            from fastapi.responses import JSONResponse

                            return JSONResponse(
                                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                                content={
                                    "detail": f"Too many failed login attempts. Account temporarily locked. Try again in {max(1, remaining // 60)} minute(s).",
                                    "retry_after": remaining,
                                },
                                headers={"Retry-After": str(remaining)},
                            )
            except Exception:
                pass

        if client_ip == "testclient" or os.environ.get("TESTING") == "1":
            return await call_next(request)

        # General per-IP rate limiter
        if not auth_limiter.check(client_ip):
            remaining_lockout = 0
            lockout_until = auth_limiter._lockouts.get(client_ip)
            if lockout_until:
                remaining_lockout = max(1, int(lockout_until - time.time()))

            logger.warning(
                f"RATE LIMITED | IP: {client_ip} | Path: {path} | "
                f"Lockout remaining: {remaining_lockout}s"
            )

            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": f"Too many requests. Temporary lockout active. Try again in {max(1, remaining_lockout // 60)} minute(s).",
                    "retry_after": remaining_lockout,
                },
                headers={"Retry-After": str(remaining_lockout)},
            )

    response = await call_next(request)
    return response
