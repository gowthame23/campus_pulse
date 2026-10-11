import hashlib
import sqlite3
import time
from secrets import token_urlsafe
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.dependencies import get_auth_service, get_db_path
from utils.helper import now_string
from utils.logger import get_logger

logger = get_logger(__name__)
bearer_scheme = HTTPBearer(auto_error=False)


def hash_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _get_db_conn():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            device_name TEXT,
            device_type TEXT,
            browser TEXT,
            operating_system TEXT,
            ip_address TEXT,
            country TEXT,
            city TEXT,
            login_time TEXT NOT NULL,
            last_activity TEXT NOT NULL,
            expires_at TEXT,
            refresh_token_hash TEXT,
            status TEXT NOT NULL DEFAULT 'Active',
            created_at TEXT NOT NULL
        )
        """
    )
    return conn


SESSION_LIFETIME = 604800  # 7 days (604,800 seconds)


def create_session(user):
    token = token_urlsafe(32)
    created_ts = time.time()
    expires_ts = created_ts + SESSION_LIFETIME

    conn = _get_db_conn()
    try:
        with conn:
            conn.execute(
                "DELETE FROM user_sessions WHERE status != 'Active' OR CAST(expires_at AS REAL) < ?",
                (created_ts,),
            )
            conn.execute(
                """
                INSERT OR REPLACE INTO user_sessions
                (session_id, user_id, device_name, device_type, browser, operating_system, ip_address, country, city, login_time, last_activity, expires_at, status, created_at)
                VALUES (?, ?, 'Web Browser', 'Desktop', 'Chrome', 'Windows', '127.0.0.1', 'India', 'Campus City', ?, ?, ?, 'Active', ?)
                """,
                (
                    hash_token(token),
                    user.user_id,
                    now_string(),
                    now_string(),
                    str(expires_ts),
                    now_string(),
                ),
            )
            conn.commit()
    except Exception as err:
        logger.warning(f"Failed to persist session token to DB: {err}")
    finally:
        conn.close()

    return token


def delete_session(token):
    if not token:
        return
    conn = _get_db_conn()
    try:
        with conn:
            conn.execute("UPDATE user_sessions SET status = 'Revoked' WHERE session_id = ?", (hash_token(token),))
            conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def invalidate_user_sessions(user_id: str):
    conn = _get_db_conn()
    try:
        with conn:
            conn.execute("UPDATE user_sessions SET status = 'Revoked' WHERE user_id = ?", (user_id,))
            conn.commit()
    except Exception:
        pass
    finally:
        conn.close()


def _lookup_session(token: str):
    if not token:
        return None

    conn = _get_db_conn()
    try:
        row = conn.execute(
            "SELECT user_id, expires_at, status FROM user_sessions WHERE session_id = ? AND status = 'Active'",
            (hash_token(token),),
        ).fetchone()
        if row:
            r_dict = dict(row)
            try:
                exp_time = float(r_dict["expires_at"])
            except (ValueError, TypeError):
                exp_time = time.time() + SESSION_LIFETIME

            now_ts = time.time()
            if now_ts < exp_time:
                # Sliding session extension: if less than 3 days remaining, extend by full SESSION_LIFETIME
                if (exp_time - now_ts) < (3 * 86400):
                    new_exp = now_ts + SESSION_LIFETIME
                    try:
                        conn.execute(
                            "UPDATE user_sessions SET expires_at = ?, last_activity = ? WHERE session_id = ?",
                            (str(new_exp), now_string(), hash_token(token)),
                        )
                        conn.commit()
                        exp_time = new_exp
                    except Exception:
                        pass
                created_ts = exp_time - SESSION_LIFETIME
                return {"user_id": r_dict["user_id"], "created_at": created_ts, "expires_at": exp_time}
    except Exception as err:
        logger.warning(f"DB session lookup failed: {err}")
    finally:
        conn.close()

    return None


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    auth_service=Depends(get_auth_service),
):
    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif request.cookies.get("session_token"):
        token = request.cookies.get("session_token")

    if not token:
        logger.warning(
            f"Authentication Failed - Token missing. Path: {request.url.path} | Method: {request.method} | IP: {request.client.host if request.client else 'unknown'}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token."
        )

    session = _lookup_session(token)
    if not session:
        logger.warning(
            f"Authentication Failed - Token invalid/revoked. Path: {request.url.path} | Method: {request.method}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token."
        )

    if time.time() - session["created_at"] > SESSION_LIFETIME:
        delete_session(token)
        logger.warning(
            f"Authentication Failed - Session expired. User ID: {session['user_id']} | Path: {request.url.path}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session has expired. Please login again.",
        )

    user = auth_service.get_user(session["user_id"])
    if not user or user.is_deleted:
        logger.warning(
            f"Authentication Failed - User not found: ID={session['user_id']} | Path: {request.url.path}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials."
        )

    if user.status in ("Inactive", "Suspended", "Archived") or not user.active:
        logger.warning(
            f"Authentication Failed - User account deactivated: ID={session['user_id']} | Status={user.status} | Path: {request.url.path}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Your account has been deactivated."
        )

    if user.first_login and request.url.path not in (
        "/auth/change-password",
        "/auth/logout",
        "/auth/me",
    ):
        logger.warning(
            f"Authorization Failed - Rejected by first-login policy. User ID: {user.user_id} | Path: {request.url.path}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Temporary password detected. You must change your password to continue.",
        )

    return user


def require_roles(*roles):
    def dependency(request: Request, current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            logger.warning(
                f"403 Forbidden - Reason: Role '{current_user.role}' attempted '{request.method} {request.url.path}', "
                f"Required: {roles} | User ID: {current_user.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )
        return current_user

    return dependency


def require_super_admin():
    return require_roles("super_admin")


def block_super_admin(current_user=Depends(get_current_user)):
    if (current_user.role or "").lower() == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin cannot access institutional operational data.",
        )
    return current_user


def get_ws_user(token):
    session = _lookup_session(token)
    user = get_auth_service().get_user(session["user_id"]) if session else None
    if (
        not user
        or user.is_deleted
        or not user.active
        or user.status in ("Inactive", "Suspended", "Archived")
    ):
        return None
    return user
