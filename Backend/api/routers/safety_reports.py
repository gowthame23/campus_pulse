import random
import string
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from api.dependencies import get_audit_service, get_auth_service, get_complaint_service, get_config_service
from api.schemas import (
    SafetyReportCreateRequest,
    SafetyReportDecisionRequest,
    SafetyReportMessageRequest,
    SafetyReportRevealRequest,
)
from api.security import get_current_user, require_roles
from models.administrator import Administrator
from models.student import Student
from utils.helper import generate_id, now_string

router = APIRouter(prefix="/safety-reports", tags=["safety-reports"])


def _generate_case_code() -> str:
    chars = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"SAFE-{chars}"


def _check_safety_enabled(config_service):
    is_enabled = config_service.get_setting("safety_reports_enabled")
    if str(is_enabled).strip().lower() not in ("true", "1", "yes"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Safety reports module is currently disabled by administrator.",
        )


@router.post("", status_code=status.HTTP_201_CREATED)
def create_safety_report(
    payload: SafetyReportCreateRequest,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
    config_service=Depends(get_config_service),
    audit_service=Depends(get_audit_service),
):
    """Student submits an anonymous safety report. Returns confidential case code."""
    _check_safety_enabled(config_service)

    # Check if student is blocked from safety reports
    blocked_until = getattr(current_user, "safety_blocked_until", None)
    if blocked_until:
        try:
            if datetime.fromisoformat(blocked_until.replace("Z", "")) > datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You are currently blocked from submitting safety reports until {blocked_until}.",
                )
        except (ValueError, TypeError):
            pass

    db = complaint_service.repository
    report_id = generate_id("SFR")
    now_ts = now_string()

    # Generate unique case code
    with db.get_connection() as conn:
        for _ in range(10):
            case_code = _generate_case_code()
            exists = conn.execute("SELECT 1 FROM safety_reports WHERE case_code = ?", (case_code,)).fetchone()
            if not exists:
                break
        else:
            case_code = f"SAFE-{generate_id('')[:4]}"

        # Insert anonymous report
        conn.execute("""
            INSERT INTO safety_reports (report_id, case_code, category, description, status, created_at)
            VALUES (?, ?, ?, ?, 'submitted', ?)
        """, (report_id, case_code, payload.category, payload.description, now_ts))

        # Insert sealed identity
        conn.execute("""
            INSERT INTO safety_report_identity (report_id, reporter_user_id, revealed)
            VALUES (?, ?, 0)
        """, (report_id, current_user.user_id))

        # Insert initial description as first message
        msg_id = generate_id("SFM")
        conn.execute("""
            INSERT INTO safety_report_messages (message_id, report_id, sender_type, body, created_at)
            VALUES (?, ?, 'reporter', ?, ?)
        """, (msg_id, report_id, payload.description, now_ts))

        conn.commit()

    audit_service.log(
        "anonymous",
        "CREATE_SAFETY_REPORT",
        report_id,
        new_value={"case_code": case_code, "category": payload.category},
    )

    return {
        "report_id": report_id,
        "case_code": case_code,
        "status": "submitted",
        "message": "Safety report submitted securely. Keep your case code safe to check replies anonymously.",
    }


@router.get("")
def list_safety_reports(
    current_user=Depends(require_roles(Administrator.ROLE)),
    complaint_service=Depends(get_complaint_service),
):
    """Administrator-only: list all submitted safety reports (identity is sealed)."""
    db = complaint_service.repository
    with db.get_connection() as conn:
        rows = conn.execute("""
            SELECT report_id, case_code, category, description, status, outcome, outcome_notes, created_at, closed_at
            FROM safety_reports
            ORDER BY created_at DESC
        """).fetchall()

    return [dict(r) for r in rows]


@router.get("/status")
def get_safety_status(
    config_service=Depends(get_config_service),
):
    """Check if safety reports module is enabled and get emergency contact numbers."""
    enabled = str(config_service.get_setting("safety_reports_enabled")).strip().lower() in ("true", "1", "yes")
    emergency = config_service.get_setting("safety_emergency_numbers") or "112"
    return {"enabled": enabled, "emergency_numbers": emergency}


@router.get("/{case_code}")
def get_safety_report_by_case_code(
    case_code: str,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
    auth_service=Depends(get_auth_service),
):
    """Look up a safety report and its anonymous message thread."""
    is_admin = (current_user.role or "").lower() == Administrator.ROLE.lower()

    # Block staff members other than administrator
    user_role = (current_user.role or "").lower()
    if user_role in ("coordinator", "location_in_charge", "warden", "app_manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff members other than Admin are not permitted to view safety reports.",
        )

    db = complaint_service.repository
    with db.get_connection() as conn:
        report = conn.execute("""
            SELECT report_id, case_code, category, description, status, outcome, outcome_notes, created_at, closed_at
            FROM safety_reports
            WHERE case_code = ? OR report_id = ?
        """, (case_code, case_code)).fetchone()

        if not report:
            raise HTTPException(status_code=404, detail="Safety report not found.")

        report_dict = dict(report)
        rep_id = report_dict["report_id"]

        # Fetch messages
        messages = conn.execute("""
            SELECT message_id, sender_type, body, created_at
            FROM safety_report_messages
            WHERE report_id = ?
            ORDER BY created_at ASC
        """, (rep_id,)).fetchall()
        report_dict["messages"] = [dict(m) for m in messages]

        # Check identity status
        identity_row = conn.execute("""
            SELECT reporter_user_id, revealed, revealed_at, revealed_by, reveal_reason
            FROM safety_report_identity
            WHERE report_id = ?
        """, (rep_id,)).fetchone()

        report_dict["is_revealed"] = bool(identity_row and identity_row["revealed"])
        if is_admin and identity_row and identity_row["revealed"]:
            reporter_user = auth_service.get_user(identity_row["reporter_user_id"])
            report_dict["revealed_reporter"] = {
                "user_id": reporter_user.user_id if reporter_user else identity_row["reporter_user_id"],
                "name": reporter_user.name if reporter_user else "Unknown",
                "email": reporter_user.email if reporter_user else "",
                "reveal_reason": identity_row["reveal_reason"],
                "revealed_at": identity_row["revealed_at"],
            }

    return report_dict


@router.post("/{case_code}/messages")
def send_safety_report_message(
    case_code: str,
    payload: SafetyReportMessageRequest,
    current_user=Depends(get_current_user),
    complaint_service=Depends(get_complaint_service),
):
    """Send an anonymous two-way message on a safety report case."""
    user_role = (current_user.role or "").lower()
    if user_role in ("coordinator", "location_in_charge", "warden", "app_manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff members other than Admin are not permitted to participate in safety reports.",
        )

    is_admin = user_role == Administrator.ROLE.lower()
    sender_type = "admin" if is_admin else "reporter"

    db = complaint_service.repository
    with db.get_connection() as conn:
        report = conn.execute("""
            SELECT report_id, status
            FROM safety_reports
            WHERE case_code = ? OR report_id = ?
        """, (case_code, case_code)).fetchone()

        if not report:
            raise HTTPException(status_code=404, detail="Safety report not found.")

        if report["status"] == "closed":
            raise HTTPException(status_code=400, detail="Cannot send messages on a closed safety report.")

        msg_id = generate_id("SFM")
        now_ts = now_string()
        conn.execute("""
            INSERT INTO safety_report_messages (message_id, report_id, sender_type, body, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (msg_id, report["report_id"], sender_type, payload.body, now_ts))
        conn.commit()

    return {
        "message_id": msg_id,
        "sender_type": sender_type,
        "body": payload.body,
        "created_at": now_ts,
    }


@router.post("/{report_id}/decision")
def decide_safety_report(
    report_id: str,
    payload: SafetyReportDecisionRequest,
    current_user=Depends(require_roles(Administrator.ROLE)),
    complaint_service=Depends(get_complaint_service),
    audit_service=Depends(get_audit_service),
):
    """Administrator closes safety report with an outcome."""
    valid_outcomes = ("action_taken", "could_not_confirm", "not_a_safety_issue", "false_misuse")
    if payload.outcome not in valid_outcomes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid outcome. Must be one of: {', '.join(valid_outcomes)}",
        )

    db = complaint_service.repository
    now_ts = now_string()

    with db.get_connection() as conn:
        report = conn.execute("SELECT report_id FROM safety_reports WHERE report_id = ?", (report_id,)).fetchone()
        if not report:
            raise HTTPException(status_code=404, detail="Safety report not found.")

        conn.execute("""
            UPDATE safety_reports
            SET status = 'closed', outcome = ?, outcome_notes = ?, closed_at = ?
            WHERE report_id = ?
        """, (payload.outcome, payload.notes or "", now_ts, report_id))
        conn.commit()

    audit_service.log(
        current_user.user_id,
        "DECIDE_SAFETY_REPORT",
        report_id,
        new_value={"outcome": payload.outcome, "notes": payload.notes},
    )

    return {
        "message": f"Safety report marked as closed with outcome '{payload.outcome}'.",
        "report_id": report_id,
        "outcome": payload.outcome,
        "closed_at": now_ts,
    }


@router.post("/{report_id}/reveal")
def reveal_safety_report_identity(
    report_id: str,
    payload: SafetyReportRevealRequest,
    current_user=Depends(require_roles(Administrator.ROLE)),
    complaint_service=Depends(get_complaint_service),
    auth_service=Depends(get_auth_service),
    audit_service=Depends(get_audit_service),
):
    """
    Administrator unseals reporter identity ONLY when outcome is 'false_misuse'.
    Imposes a 30-day block penalty on the reporter.
    """
    db = complaint_service.repository
    with db.get_connection() as conn:
        report = conn.execute("""
            SELECT report_id, outcome, status
            FROM safety_reports
            WHERE report_id = ?
        """, (report_id,)).fetchone()

        if not report:
            raise HTTPException(status_code=404, detail="Safety report not found.")

        if report["outcome"] != "false_misuse":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reporter identity can only be unsealed when the outcome is specifically decided as 'false_misuse'.",
            )

        identity = conn.execute("""
            SELECT reporter_user_id, revealed
            FROM safety_report_identity
            WHERE report_id = ?
        """, (report_id,)).fetchone()

        if not identity:
            raise HTTPException(status_code=404, detail="Identity record not found.")

        reporter_id = identity["reporter_user_id"]
        now_ts = now_string()
        block_until = (datetime.now() + timedelta(days=30)).isoformat()

        conn.execute("""
            UPDATE safety_report_identity
            SET revealed = 1, revealed_at = ?, revealed_by = ?, reveal_reason = ?
            WHERE report_id = ?
        """, (now_ts, current_user.user_id, payload.reason, report_id))

        # Impose 30-day block penalty on the user
        conn.execute("""
            UPDATE users
            SET safety_blocked_until = ?
            WHERE user_id = ?
        """, (block_until, reporter_id))

        conn.commit()

    reporter_user = auth_service.get_user(reporter_id)

    audit_service.log(
        current_user.user_id,
        "SAFETY_REPORT_IDENTITY_REVEALED",
        report_id,
        new_value={
            "reporter_user_id": reporter_id,
            "reason": payload.reason,
            "blocked_until": block_until,
        },
    )

    return {
        "message": "Reporter identity unsealed and 30-day safety report block imposed.",
        "reporter": {
            "user_id": reporter_id,
            "name": reporter_user.name if reporter_user else "Unknown",
            "email": reporter_user.email if reporter_user else "",
        },
        "blocked_until": block_until,
    }
