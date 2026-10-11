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
        user = auth_service.authenticate(identity, password)
        access_token = create_session(user)
        response.set_cookie(
            key="session_token",
            value=access_token,
            httponly=True,
            samesite="lax",
            max_age=604800,  # 7 days
            path="/",
        )
        client_ip = request.client.host if request.client else "unknown"
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
        client_ip = request.client.host if request.client else "unknown"
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
        client_ip = request.client.host if request.client else "unknown"
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
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
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
    return conn


@router.post("/password-reset/request", response_model=PasswordResetStartResponse)
def request_password_reset(
    payload: PasswordResetStartRequest, auth_service=Depends(get_auth_service)
):
    clean_email = (payload.email or "").strip().lower()
    now_ts = time.time()
    reset_id = token_urlsafe(16)
    otp = str(100000 + randbelow(900000))
    exp_ts = now_ts + (15 * 60)

    # Check total attempts for this email across active requests in last 15 minutes (Account Brute-Force Protection)
    with _get_db() as conn:
        row = conn.execute(
            "SELECT SUM(attempts) as total_attempts FROM password_resets WHERE email = ? AND expires_at > ?",
            (clean_email, now_ts),
        ).fetchone()
        tot_att = (row["total_attempts"] or 0) if row else 0
        recent_requests = conn.execute(
            "SELECT COUNT(*) FROM password_resets WHERE email = ? AND otp != 'VERIFIED' AND expires_at > ?",
            (clean_email, now_ts),
        ).fetchone()[0]
        if tot_att >= 5 or recent_requests >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many password reset attempts for this account. Please try again later.",
            )

    user = auth_service.get_user_by_email(clean_email)

    with _get_db() as conn:
        conn.execute(
            """
            INSERT INTO password_resets (reset_id, user_id, email, otp, attempts, expires_at, used, created_at)
            VALUES (?, ?, ?, ?, 0, ?, 0, ?)
            """,
            (reset_id, user.user_id if user else None, clean_email, hash_token(otp), exp_ts, now_ts),
        )
        conn.commit()

    # Account Enumeration Protection: send email if user exists, but always return identical generic success
    if user:
        from utils.email import send_otp_email
        send_otp_email(clean_email, otp)

    return {
        "reset_id": reset_id,
        "message": "If the account exists, reset instructions have been sent to your email.",
    }


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

        # Check total cumulative attempts for account
        tot_row = conn.execute(
            "SELECT SUM(attempts) as total_attempts FROM password_resets WHERE email = ? AND expires_at > ?",
            (clean_email, now_ts),
        ).fetchone()
        tot_att = (tot_row["total_attempts"] or 0) if tot_row else 0

        if rec["used"] == 1 or now_ts > rec["expires_at"] or tot_att >= 5 or rec["attempts"] >= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OTP token.",
            )

        if rec["otp"] != hash_token(payload.otp.strip()):
            conn.execute(
                "UPDATE password_resets SET attempts = attempts + 1 WHERE email = ? AND expires_at > ?",
                (clean_email, now_ts),
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
    if payload.confirm_password and payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match.",
        )
    try:
        user = auth_service.complete_activation(
            payload.activation_token, payload.password
        )
        from api.security import invalidate_user_sessions
        invalidate_user_sessions(user.user_id)
        return {
            "message": "Account activated successfully. You can now log in.",
            "user_id": user.user_id,
        }
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

