from pathlib import Path

try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / '.env'
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path)
    else:
        load_dotenv()
except ImportError:
    pass

import concurrent.futures
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid

from utils.logger import get_logger

logger = get_logger(__name__)

_last_email_error = None

def get_last_email_error() -> str:
    global _last_email_error
    return _last_email_error or "Unknown SMTP error"


# Small background worker pool so SMTP network latency never blocks the event loop
_email_executor = concurrent.futures.ThreadPoolExecutor(max_workers=3, thread_name_prefix="email-dispatcher")


def _is_sync_mode() -> bool:
    return (
        bool(os.environ.get("PYTEST_CURRENT_TEST"))
        or os.environ.get("TESTING") == "1"
        or os.environ.get("EMAIL_SYNC") == "true"
    )


def _smtp_configured() -> bool:
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    return bool(smtp_server and smtp_username and smtp_password)


def _send_notification_email_sync(to_email, title, message) -> bool:
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_from = os.environ.get("SMTP_FROM", smtp_username)
    if not smtp_server or not smtp_username or not smtp_password:
        logger.warning("Notification email not sent: SMTP is not configured")
        return False
    msg = MIMEText(message)
    msg["Subject"] = f"Campus Pulse - {title}"
    msg["From"] = smtp_from if smtp_from else "noreply@campus.edu"
    msg["To"] = to_email
    try:
        with smtplib.SMTP(smtp_server, int(smtp_port) if smtp_port else 587) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(msg["From"], [to_email], msg.as_string())
        logger.info("Notification email sent", extra={"recipient": to_email})
        return True
    except Exception:
        logger.exception("Notification email delivery failed", extra={"recipient": to_email})
        return False


def send_notification_email(to_email, title, message) -> bool:
    """Non-blocking email delivery. Dispatches to worker thread pool unless in test sync mode."""
    if not _smtp_configured():
        return False
    if _is_sync_mode():
        return _send_notification_email_sync(to_email, title, message)
    try:
        _email_executor.submit(_send_notification_email_sync, to_email, title, message)
        return True
    except Exception as e:
        logger.exception(f"Failed to submit notification email to thread pool: {e}")
        return False


def _send_otp_email_sync(to_email, otp) -> bool:
    global _last_email_error
    smtp_server = (os.environ.get("SMTP_SERVER") or "").strip()
    smtp_port = (os.environ.get("SMTP_PORT") or "").strip()
    smtp_username = (os.environ.get("SMTP_USERNAME") or "").strip()
    smtp_password = (os.environ.get("SMTP_PASSWORD") or "").strip().replace(" ", "").strip('"').strip("'")
    smtp_from = (os.environ.get("SMTP_FROM") or smtp_username).strip()

    if not smtp_server or not smtp_username or not smtp_password:
        _last_email_error = "SMTP credentials are not configured on the server."
        logger.warning(f"OTP email not sent: {_last_email_error}")
        return False

    plain_text = f"Your Campus Pulse password reset OTP is: {otp}\r\nThis code will expire in 15 minutes."
    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px;">
  <div style="max-width: 480px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
    <div style="text-align: center; margin-bottom: 24px;">
      <h2 style="color: #0f172a; margin: 0; font-size: 22px;">Campus Pulse</h2>
      <p style="color: #64748b; font-size: 13px; margin-top: 4px;">Password Reset Verification Code</p>
    </div>
    <p style="color: #334155; font-size: 14px; line-height: 1.5;">You requested a password reset for your Campus Pulse account. Use the verification code below to complete the reset:</p>
    <div style="text-align: center; margin: 28px 0;">
      <span style="display: inline-block; font-size: 32px; font-weight: 700; letter-spacing: 6px; color: #0284c7; background: #f0f9ff; border: 1px dashed #0284c7; border-radius: 8px; padding: 12px 24px;">{otp}</span>
    </div>
    <p style="color: #64748b; font-size: 12px; line-height: 1.5; text-align: center;">This code will expire in 15 minutes. If you did not request this code, you can safely ignore this email.</p>
  </div>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Campus Pulse - Password Reset OTP"
    from_header = f"Campus Pulse <{smtp_from}>" if "<" not in smtp_from else smtp_from
    msg["From"] = from_header
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="campuspulse.edu")

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        port = int(smtp_port) if smtp_port else 587
        if port == 465:
            server = smtplib.SMTP_SSL(smtp_server, port, timeout=15)
        else:
            server = smtplib.SMTP(smtp_server, port, timeout=15)
            server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_from, [to_email], msg.as_string())
        server.quit()
        _last_email_error = None
        logger.info(f"Reset OTP email successfully delivered to {to_email}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        _last_email_error = "Google SMTP authentication failed (535): App Password rejected. Check for typos or re-generate 16-character App Password."
        logger.exception(_last_email_error)
        return False
    except Exception as e:
        _last_email_error = f"SMTP error ({type(e).__name__}: {str(e)})"
        logger.exception(_last_email_error)
        return False


def send_otp_email(to_email, otp) -> bool:
    """Non-blocking OTP email delivery. Dispatches to worker thread pool unless in test sync mode."""
    if not _smtp_configured():
        return False
    if _is_sync_mode():
        return _send_otp_email_sync(to_email, otp)
    try:
        _email_executor.submit(_send_otp_email_sync, to_email, otp)
        return True
    except Exception as e:
        logger.exception(f"Failed to submit OTP email to thread pool: {e}")
        return False


def _send_password_changed_email_sync(to_email, user_name) -> bool:
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_from = os.environ.get("SMTP_FROM", smtp_username)

    body = f"Hello {user_name},\r\n\r\nYour Campus Pulse password was successfully updated.\r\nIf you did not perform this change, please contact an Admin immediately."
    msg = MIMEText(body)
    msg["Subject"] = "Campus Pulse - Password Security Notification"
    msg["From"] = smtp_from if smtp_from else "noreply@campus.edu"
    msg["To"] = to_email

    if not smtp_server or not smtp_username or not smtp_password:
        logger.info(f"Password updated notification email simulated to {to_email}")
        return True

    try:
        port = int(smtp_port) if smtp_port else 587
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(msg["From"], [to_email], msg.as_string())
        server.quit()
        logger.info(f"Successfully sent password updated email to {to_email}")
        return True
    except Exception as e:
        logger.exception(f"Password updated notice failed for {to_email}: {e}")
        return False


def send_password_changed_email(to_email, user_name) -> bool:
    """Non-blocking password change email delivery."""
    if _is_sync_mode():
        return _send_password_changed_email_sync(to_email, user_name)
    try:
        _email_executor.submit(_send_password_changed_email_sync, to_email, user_name)
        return True
    except Exception as e:
        logger.exception(f"Failed to submit password updated email to thread pool: {e}")
        return False


def _send_activation_email_sync(to_email, activation_link, user_name="Student") -> bool:
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_from = os.environ.get("SMTP_FROM", smtp_username)
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")

    # Ensure activation_link is formatted with base frontend URL if relative
    if activation_link.startswith("/"):
        full_activation_url = f"{frontend_url}{activation_link}"
    else:
        full_activation_url = activation_link

    if not smtp_server or not smtp_username or not smtp_password:
        logger.warning(
            "Activation email simulated (SMTP not configured)",
            extra={"recipient": to_email},
        )
        return False

    plain_text = (
        f"Hello {user_name},\r\n\r\n"
        f"Welcome to Campus Pulse! An account has been created for you.\r\n\r\n"
        f"Please click the link below to activate your account and choose your password:\r\n"
        f"{full_activation_url}\r\n\r\n"
        f"Security Notice:\r\n"
        f"- This activation link is unique to you and will expire in 7 days.\r\n"
        f"- If you did not request this, please contact your administrator.\r\n\r\n"
        f"Regards,\r\nCampus Pulse Team"
    )

    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px;">
  <div style="max-width: 520px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
    <div style="text-align: center; margin-bottom: 24px;">
      <h2 style="color: #0f172a; margin: 0; font-size: 24px; font-weight: 700;">Campus Pulse</h2>
      <p style="color: #64748b; font-size: 13px; margin-top: 4px;">Campus Complaint & Operations System</p>
    </div>
    <div style="border-top: 1px solid #f1f5f9; padding-top: 20px;">
      <p style="color: #1e293b; font-size: 15px; line-height: 1.5; margin: 0 0 16px 0;">Hello <strong>{user_name}</strong>,</p>
      <p style="color: #334155; font-size: 14px; line-height: 1.6; margin: 0 0 24px 0;">
        Welcome to Campus Pulse! An institutional student account has been created for you. Click the button below to set up your password and activate your account:
      </p>
      <div style="text-align: center; margin: 28px 0;">
        <a href="{full_activation_url}" style="display: inline-block; background-color: #0284c7; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 14px; padding: 12px 32px; border-radius: 8px; box-shadow: 0 2px 4px rgba(2,132,199,0.25);">
          Activate My Account &rarr;
        </a>
      </div>
      <p style="color: #64748b; font-size: 12px; line-height: 1.5; margin: 0 0 8px 0;">
        Or copy and paste this link in your browser:
      </p>
      <p style="word-break: break-all; color: #0284c7; font-size: 12px; background: #f0f9ff; padding: 8px 12px; border-radius: 6px; margin: 0 0 24px 0;">
        {full_activation_url}
      </p>
      <div style="border-top: 1px solid #f1f5f9; padding-top: 16px;">
        <p style="color: #94a3b8; font-size: 11px; line-height: 1.5; margin: 0;">
          &#8226; This link is unique to your account and will expire in 7 days.<br/>
          &#8226; After setting your password, you will be redirected to the Campus Pulse login page.
        </p>
      </div>
    </div>
  </div>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Campus Pulse - Account Activation & Password Setup"
    from_header = f"Campus Pulse <{smtp_from}>" if "<" not in smtp_from else smtp_from
    msg["From"] = from_header
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="campuspulse.edu")

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        port = int(smtp_port) if smtp_port else 587
        server = smtplib.SMTP(smtp_server, port, timeout=15)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_from, [to_email], msg.as_string())
        server.quit()
        logger.info("Activation email sent successfully", extra={"recipient": to_email})
        return True
    except Exception as e:
        logger.exception("Activation email delivery failed", extra={"recipient": to_email})
        return False


def send_activation_email(to_email, activation_link, user_name="Student") -> bool:
    """Non-blocking activation email delivery."""
    if not _smtp_configured():
        return False
    if _is_sync_mode():
        return _send_activation_email_sync(to_email, activation_link, user_name)
    try:
        _email_executor.submit(
            _send_activation_email_sync, to_email, activation_link, user_name
        )
        return True
    except Exception as e:
        logger.exception(f"Failed to submit activation email to thread pool: {e}")
        return False
