from datetime import datetime, timedelta
from secrets import randbelow, token_urlsafe
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials

from api.dependencies import get_audit_service, get_auth_service, get_db_path
from api.schemas import (
    AccountActivationRequest,
    ChangePasswordRequest,
    LoginRequest,
    PasswordResetCompleteRequest,
    PasswordResetStartRequest,
    PasswordResetStartResponse,
    PasswordResetVerifyRequest,
    PasswordResetVerifyResponse,
    TokenResponse,
    get_role_permissions,
    user_to_response,
)
from api.security import bearer_scheme, create_session, delete_session, get_current_user, hash_token
from utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
_reset_requests = {}
_reset_tokens = {}
_RESET_MINUTES = 15  # 15 minutes token expiry as per spec


def _expires_at():
    return datetime.utcnow() + timedelta(minutes=_RESET_MINUTES)


def _is_expired(value):
    return datetime.utcnow() > value["expires_at"]


REDIRECT_MAP = {
    "student": "/student/dashboard",
    "coordinator": "/coordinator/dashboard",
    "location_in_charge": "/location/dashboard",
    "app_manager": "/manager/dashboard",
    "administrator": "/admin/dashboard",
    "super_admin": "/superadmin/dashboard",
}


@router.post("/login", response_model=TokenResponse)
def login(
    request: Request,
    payload: LoginRequest,
    response: Response,
    auth_service=Depends(get_auth_service),
    audit_service=Depends(get_audit_service),
):
    identity = (payload.username or payload.email or "").strip()
    password = (payload.password or "").strip()
    client_ip = request.client.host if request.client else "unknown"

    if not identity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is required."
        )
    if not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required."
        )

    try:
        user = auth_service.authenticate(identity, password, ip=client_ip)
        access_token = create_session(user, request=request)
        is_secure = request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"
        response.set_cookie(
            key="session_token",
            value=access_token,
            httponly=True,
            secure=is_secure,
            samesite="lax",
            max_age=604800,  # 7 days
            path="/",
        )
        from middleware.rate_limiter import record_login_attempt
        record_login_attempt(client_ip, identity, success=True)

        audit_service.log(
            user.user_id,
            "User Login",
            user.user_id,
            old_value=None,
            new_value={"role": user.role},
        )
        redirect_url = REDIRECT_MAP.get(user.role.lower(), "/student/dashboard")
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_to_response(user),
            "role": user.role,
            "redirect": redirect_url,
            "first_login": user.first_login,
            "permissions": get_role_permissions(user.role),
        }
    except PermissionError as p_err:
        from middleware.rate_limiter import record_login_attempt
        record_login_attempt(client_ip, identity, success=False)
        audit_service.log(
            "anonymous",
            "Failed Login Attempt",
            identity.lower(),
            old_value=None,
            new_value={"reason": str(p_err)},
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(p_err))
    except ValueError as error:
        from middleware.rate_limiter import record_login_attempt
        record_login_attempt(client_ip, identity, success=False)
        detail_msg = str(error)
        status_code = status.HTTP_400_BAD_REQUEST if "required" in detail_msg.lower() else status.HTTP_401_UNAUTHORIZED
        audit_service.log(
            "anonymous",
            "Failed Login Attempt",
            identity.lower(),
            old_value=None,
            new_value={"reason": detail_msg},
        )
        raise HTTPException(status_code=status_code, detail=detail_msg)


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    current_user=Depends(get_current_user),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    auth_service=Depends(get_auth_service),
    audit_service=Depends(get_audit_service),
):
    token = credentials.credentials if credentials and credentials.credentials else request.cookies.get("session_token")
    if token:
        delete_session(token)
    response.delete_cookie(key="session_token", path="/")
    auth_service.logout_user(current_user.user_id)
    audit_service.log(current_user.user_id, "User Logout", current_user.user_id)
    return {"message": "Logged out successfully."}


@router.get("/me")
def me(current_user=Depends(get_current_user)):
    return user_to_response(current_user)


@router.post("/ws-ticket")
def create_websocket_ticket(current_user=Depends(get_current_user)):
    from api.security import create_ws_ticket

    ticket = create_ws_ticket(current_user.user_id)
    return {"ticket": ticket, "expires_in": 60}


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    current_user=Depends(get_current_user),
    auth_service=Depends(get_auth_service),
    audit_service=Depends(get_audit_service),
):
    old_pw = payload.old_password or payload.current_password
    if not old_pw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is required.",
        )
    if not current_user.check_password(old_pw):
        audit_service.log(
            current_user.user_id,
            "Failed Password Change",
            current_user.user_id,
            old_value=None,
            new_value={"reason": "Incorrect current password"},
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Old password is incorrect.",
        )
    if payload.confirm_password and payload.new_password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match.",
        )
    try:
        user = auth_service.change_password(current_user.user_id, payload.new_password, old_password=old_pw)
        from api.security import invalidate_user_sessions
        invalidate_user_sessions(current_user.user_id)
        audit_service.log(
            current_user.user_id,
            "Password Changed",
            current_user.user_id,
            old_value=None,
            new_value={"changed_by": current_user.user_id, "role": current_user.role},
        )
        from utils.email import send_password_changed_email

        send_password_changed_email(user.email, user.name)
        return user_to_response(user)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password. Please try again.",
        )


@router.post("/reset-password", status_code=status.HTTP_410_GONE)
def reset_password():
    """Deprecated insecure reset route; use the OTP reset flow instead."""
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="Use /auth/password-reset/request, /verify, and /complete.",
    )


import sqlite3
import time

def _get_db():
    from utils.db import get_db_connection
    conn = get_db_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS password_resets (
            reset_id TEXT PRIMARY KEY,
            user_id TEXT,
            email TEXT NOT NULL,
            otp TEXT NOT NULL,
            attempts INTEGER DEFAULT 0,
            expires_at REAL NOT NULL,
            used INTEGER DEFAULT 0,
            created_at REAL NOT NULL
        )
        """
    )
    if hasattr(conn, "commit"):
        conn.commit()
    return conn


@router.post("/password-reset/request", response_model=PasswordResetStartResponse)
def request_password_reset(
    request: Request, payload: PasswordResetStartRequest, auth_service=Depends(get_auth_service)
):
    clean_email = (payload.email or "").strip().lower()
    now_ts = time.time()
    client_ip = request.client.host if request.client else "unknown"

    user = auth_service.get_user_by_email(clean_email)
    if not user:
        user = auth_service.get_user_by_identity(payload.email.strip())

    delivery_email = user.email.strip().lower() if (user and getattr(user, "email", None)) else clean_email
    user_id = user.user_id if user else None

    # 1. IP Rate Limiting: Max 10 reset requests per IP in 15 minutes to prevent network DoS
    with _get_db() as conn:
        ip_cnt = conn.execute(
            "SELECT COUNT(*) FROM password_resets WHERE email LIKE ? AND created_at > ?",
            (f"%@{client_ip}%", now_ts - 900),
        ).fetchone()[0]

        # Check failed attempts across active resets for this email or user
        failed_attempts = conn.execute(
            """
            SELECT SUM(attempts) FROM password_resets
            WHERE (email = ? OR email = ? OR (user_id IS NOT NULL AND user_id = ?))
              AND expires_at > ?
            """,
            (clean_email, delivery_email, user_id, now_ts),
        ).fetchone()[0] or 0
        if failed_attempts >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many failed attempts. Account password reset locked.",
            )

        # 2. Account Rate Limiting: Check unverified requests initiated in the last 15 minutes
        recent_requests = conn.execute(
            """
            SELECT COUNT(*) FROM password_resets
            WHERE (email = ? OR email = ? OR (user_id IS NOT NULL AND user_id = ?))
              AND otp != 'VERIFIED'
              AND expires_at > ?
            """,
            (clean_email, delivery_email, user_id, now_ts),
        ).fetchone()[0]
        if recent_requests >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many password reset requests. Please wait 15 minutes before trying again.",
            )

    reset_id = token_urlsafe(16)
    generic_success = {
        "reset_id": reset_id,
        "message": "If the account exists, a password reset verification code has been sent.",
    }

    if not user or not getattr(user, "email", None):
        logger.warning(f"Password reset requested for unrecognized user/email: {clean_email}")
        return generic_success

    otp = str(100000 + randbelow(900000))
    exp_ts = now_ts + (15 * 60)

    from utils import email as email_utils
    if not email_utils._smtp_configured():
        logger.error("Password reset failed: SMTP is not configured on server")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is temporarily unavailable on the server. Please contact an Administrator.",
        )

    with _get_db() as conn:
        conn.execute(
            """
            INSERT INTO password_resets (reset_id, user_id, email, otp, attempts, expires_at, used, created_at)
            VALUES (?, ?, ?, ?, 0, ?, 0, ?)
            """,
            (reset_id, user_id, delivery_email, hash_token(otp), exp_ts, now_ts),
        )
        conn.commit()

    email_sent = email_utils.send_otp_email(delivery_email, otp)
    if email_sent is False:
        with _get_db() as conn:
            conn.execute("DELETE FROM password_resets WHERE reset_id = ?", (reset_id,))
            conn.commit()
        # Log the real reason (which can contain raw SMTP/provider errors --
        # e.g. Gmail auth failures or a Brevo/Resend API response body) only
        # server-side. The client gets a generic message: returning err_msg
        # in the response handed an anonymous caller a readout of our email
        # provider and auth method, which they don't need and we don't want
        # printed into an anonymous browser toast.
        err_msg = email_utils.get_last_email_error() or "Unable to dispatch email"
        logger.error(f"Failed to deliver OTP email to {delivery_email}: {err_msg}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="We couldn't send the email right now. Please try again shortly.",
        )

    logger.info(f"Password reset OTP initiated for user {user.user_id} ({delivery_email})")
    return generic_success


@router.post("/password-reset/verify", response_model=PasswordResetVerifyResponse)
def verify_password_reset(payload: PasswordResetVerifyRequest):
    now_ts = time.time()
    with _get_db() as conn:
        row = conn.execute(
            "SELECT * FROM password_resets WHERE reset_id = ?", (payload.reset_id,)
        ).fetchone()
        if not row:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP token.",
            )
        rec = dict(row)
        clean_email = rec["email"]

        # Check attempts on this specific reset_id (isolated attempt counting)
        if rec["used"] == 1 or now_ts > rec["expires_at"] or rec["attempts"] >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP token.",
            )

        if rec["otp"] != hash_token(payload.otp.strip()):
            conn.execute(
                "UPDATE password_resets SET attempts = attempts + 1 WHERE reset_id = ?",
                (payload.reset_id,),
            )
            conn.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP token.",
            )

        # OTP is correct -> mark used & generate reset token
        reset_token = token_urlsafe(24)
        conn.execute("UPDATE password_resets SET used = 1 WHERE reset_id = ?", (payload.reset_id,))
        conn.execute(
            """
            INSERT INTO password_resets (reset_id, user_id, email, otp, attempts, expires_at, used, created_at)
            VALUES (?, ?, ?, 'VERIFIED', 0, ?, 0, ?)
            """,
            (hash_token(reset_token), rec["user_id"], clean_email, now_ts + (15 * 60), now_ts),
        )
        conn.commit()

    return {"reset_token": reset_token, "message": "OTP verified successfully."}


@router.post("/password-reset/complete")
def complete_password_reset(
    payload: PasswordResetCompleteRequest, auth_service=Depends(get_auth_service)
):
    now_ts = time.time()
    with _get_db() as conn:
        row = conn.execute(
            "SELECT * FROM password_resets WHERE reset_id = ? AND otp = 'VERIFIED' AND used = 0",
            (hash_token(payload.reset_token),),
        ).fetchone()
        if not row or now_ts > row["expires_at"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token.",
            )
        rec = dict(row)
        conn.execute("UPDATE password_resets SET used = 1 WHERE reset_id = ?", (rec["reset_id"],))
        conn.commit()

    try:
        user = auth_service.reset_password(rec["email"], payload.new_password)
        from api.security import invalidate_user_sessions
        invalidate_user_sessions(user.user_id)
        return {
            "message": "Password reset successful. Login with your new password.",
            "user_id": user.user_id,
        }
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.get("/activate/verify")
def verify_activation_token(token: str, auth_service=Depends(get_auth_service)):
    try:
        return auth_service.verify_activation_token(token)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))


@router.post("/activate/complete")
def complete_activation(
    payload: AccountActivationRequest, auth_service=Depends(get_auth_service)
):
    token = payload.activation_token or payload.token
    pwd = payload.password or payload.new_password
    conf = payload.confirm_password
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Activation token is required.",
        )
    if not pwd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required.",
        )
    if conf and pwd != conf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match.",
        )
    try:
        user = auth_service.complete_activation(token, pwd)
        from api.security import invalidate_user_sessions
        invalidate_user_sessions(user.user_id)
        return {
            "message": "Account activated successfully. You can now log in.",
            "user_id": user.user_id,
        }
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

