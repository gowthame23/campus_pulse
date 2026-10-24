from pathlib import Path
import concurrent.futures
import json
import os
import smtplib
import socket
import ssl
import urllib.error
import urllib.request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid

try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / '.env'
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path)
    else:
        load_dotenv()
except ImportError:
    pass

from utils.logger import get_logger

logger = get_logger(__name__)

_last_email_error = None


def get_last_email_error() -> str:
    global _last_email_error
    return _last_email_error or "Unknown email delivery error"


# Background worker pool for non-blocking email delivery
_email_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=3, thread_name_prefix="email-dispatcher"
)


class IPv4SMTP(smtplib.SMTP):
    """SMTP client that strictly resolves IPv4 (AF_INET) to prevent [Errno 101] Network is unreachable."""
    def _get_socket(self, host, port, timeout):
        err = None
        for res in socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            sock = None
            try:
                sock = socket.socket(af, socktype, proto)
                if timeout is not None:
                    sock.settimeout(timeout)
                sock.connect(sa)
                return sock
            except OSError as e:
                err = e
                if sock is not None:
                    sock.close()
        if err is not None:
            raise err
        raise OSError(f"Failed to resolve IPv4 address for {host}")


class IPv4SMTP_SSL(smtplib.SMTP_SSL):
    """SMTP_SSL client that strictly resolves IPv4 (AF_INET) to prevent [Errno 101] Network is unreachable."""
    def _get_socket(self, host, port, timeout):
        err = None
        for res in socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM):
            af, socktype, proto, canonname, sa = res
            sock = None
            try:
                sock = socket.socket(af, socktype, proto)
                if timeout is not None:
                    sock.settimeout(timeout)
                sock.connect(sa)
                ctx = self.context if self.context else ssl.create_default_context()
                return ctx.wrap_socket(sock, server_hostname=host)
            except OSError as e:
                err = e
                if sock is not None:
                    sock.close()
        if err is not None:
            raise err
        raise OSError(f"Failed to resolve IPv4 address for {host}")


def _is_sync_mode() -> bool:
    return (
        bool(os.environ.get("PYTEST_CURRENT_TEST"))
        or os.environ.get("TESTING") == "1"
        or os.environ.get("EMAIL_SYNC") == "true"
    )


def _smtp_configured() -> bool:
    if (os.environ.get("BREVO_API_KEY") or "").strip():
        return True
    if (os.environ.get("RESEND_API_KEY") or "").strip():
        return True
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    return bool(smtp_server and smtp_username and smtp_password)


def _send_via_brevo(to_email: str, subject: str, html_content: str, plain_text: str = "") -> bool:
    """Dispatches email via Brevo HTTPS REST API (port 443) to bypass cloud SMTP port blocks."""
    global _last_email_error
    api_key = (os.environ.get("BREVO_API_KEY") or "").strip()
    if not api_key:
        return False

    sender_email = (
        os.environ.get("BREVO_SENDER_EMAIL")
        or os.environ.get("SMTP_FROM")
        or os.environ.get("SMTP_USERNAME")
        or "gowthamejjurothu1@gmail.com"
    ).strip()
    sender_name = (os.environ.get("SMTP_FROM_NAME") or "Campus Pulse").strip()

    payload = {
        "sender": {"name": sender_name, "email": sender_email},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
    }
    if plain_text:
        payload["textContent"] = plain_text

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=data,
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CampusPulse/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            if 200 <= resp.status < 300:
                _last_email_error = None
                logger.info(f"Email successfully delivered to {to_email} via Brevo HTTPS API")
                return True
            _last_email_error = f"Brevo API error: HTTP {resp.status}"
            return False
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        _last_email_error = f"Brevo HTTP {e.code}: {body}"
        logger.exception(_last_email_error)
        return False
    except Exception as e:
        _last_email_error = f"Brevo API error ({type(e).__name__}: {str(e)})"
        logger.exception(_last_email_error)
        return False


def _send_via_resend(to_email: str, subject: str, html_content: str, plain_text: str = "") -> bool:
    """Dispatches email via Resend HTTPS REST API (port 443) to bypass cloud SMTP port blocks."""
    global _last_email_error
    api_key = (os.environ.get("RESEND_API_KEY") or "").strip()
    if not api_key:
        return False

    sender = (
        os.environ.get("RESEND_FROM")
        or os.environ.get("SMTP_FROM")
        or "Campus Pulse <onboarding@resend.dev>"
    ).strip()

    payload = {
        "from": sender,
        "to": [to_email],
        "subject": subject,
        "html": html_content,
    }
    if plain_text:
        payload["text"] = plain_text

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "CampusPulse/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            if 200 <= resp.status < 300:
                _last_email_error = None
                logger.info(f"Email successfully delivered to {to_email} via Resend HTTPS API")
                return True
            _last_email_error = f"Resend API error: HTTP {resp.status}"
            return False
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        _last_email_error = f"Resend HTTP {e.code}: {body}"
        logger.exception(_last_email_error)
        return False
    except Exception as e:
        _last_email_error = f"Resend API error ({type(e).__name__}: {str(e)})"
        logger.exception(_last_email_error)
        return False


def _send_via_smtp(to_email: str, subject: str, html_content: str, plain_text: str = "") -> bool:
    """Fallback standard SMTP delivery using IPv4 resolution."""
    global _last_email_error
    smtp_server = (os.environ.get("SMTP_SERVER") or "").strip()
    smtp_port = (os.environ.get("SMTP_PORT") or "").strip()
    smtp_username = (os.environ.get("SMTP_USERNAME") or "").strip()
    smtp_password = (os.environ.get("SMTP_PASSWORD") or "").strip().replace(" ", "").strip('"').strip("'")
    smtp_from = (os.environ.get("SMTP_FROM") or smtp_username).strip()

    if not smtp_server or not smtp_username or not smtp_password:
        _last_email_error = "SMTP credentials are not configured on the server."
        logger.warning(f"Email not sent: {_last_email_error}")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    from_header = f"Campus Pulse <{smtp_from}>" if "<" not in smtp_from else smtp_from
    msg["From"] = from_header
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="campuspulse.edu")

    if plain_text:
        msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    if html_content:
        msg.attach(MIMEText(html_content, "html", "utf-8"))

    try:
        port = int(smtp_port) if smtp_port else 587
        if port == 465:
            server = IPv4SMTP_SSL(smtp_server, port, timeout=15)
        else:
            server = IPv4SMTP(smtp_server, port, timeout=15)
            server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(smtp_from, [to_email], msg.as_string())
        server.quit()
        _last_email_error = None
        logger.info(f"Email delivered to {to_email} via SMTP ({smtp_server}:{port})")
        return True
    except smtplib.SMTPAuthenticationError:
        _last_email_error = "Google SMTP authentication failed (535): App Password rejected. Check for typos or re-generate 16-character App Password."
        logger.exception(_last_email_error)
        return False
    except Exception as e:
        _last_email_error = f"SMTP error ({type(e).__name__}: {str(e)})"
        logger.exception(_last_email_error)
        return False


def _dispatch_email(to_email: str, subject: str, html_content: str, plain_text: str = "") -> bool:
    """Dispatches email across available providers: Brevo HTTPS -> Resend HTTPS -> Standard SMTP."""
    global _last_email_error

    # 1. Brevo HTTPS API (Port 443 - zero credit card, 300 free emails/day)
    if (os.environ.get("BREVO_API_KEY") or "").strip():
        if _send_via_brevo(to_email, subject, html_content, plain_text):
            return True
        logger.warning("Brevo delivery failed, attempting secondary fallbacks...")

    # 2. Resend HTTPS API (Port 443 - zero credit card, 3,000 free emails/month)
    if (os.environ.get("RESEND_API_KEY") or "").strip():
        if _send_via_resend(to_email, subject, html_content, plain_text):
            return True
        logger.warning("Resend delivery failed, attempting secondary fallbacks...")

    # 3. Standard SMTP (Port 587/465)
    smtp_server = (os.environ.get("SMTP_SERVER") or "").strip()
    smtp_username = (os.environ.get("SMTP_USERNAME") or "").strip()
    smtp_password = (os.environ.get("SMTP_PASSWORD") or "").strip()
    if smtp_server and smtp_username and smtp_password:
        return _send_via_smtp(to_email, subject, html_content, plain_text)

    if not _last_email_error:
        _last_email_error = "No active email provider configured. Please set BREVO_API_KEY, RESEND_API_KEY, or SMTP credentials."
    return False


def _send_notification_email_sync(to_email, title, message) -> bool:
    subject = f"Campus Pulse - {title}"
    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px;">
  <div style="max-width: 480px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
    <h2 style="color: #0f172a; margin: 0 0 16px 0; font-size: 20px;">{title}</h2>
    <p style="color: #334155; font-size: 14px; line-height: 1.6; margin: 0 0 20px 0;">{message}</p>
    <p style="color: #64748b; font-size: 12px; margin: 0;">Campus Pulse System Notification</p>
  </div>
</body>
</html>"""
    return _dispatch_email(to_email, subject, html_content, message)


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
    subject = "Campus Pulse - Password Reset OTP"
    return _dispatch_email(to_email, subject, html_content, plain_text)


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
    subject = "Campus Pulse - Password Security Notification"
    plain_text = f"Hello {user_name},\r\n\r\nYour Campus Pulse password was successfully updated.\r\nIf you did not perform this change, please contact an Admin immediately."
    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px;">
  <div style="max-width: 480px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
    <h2 style="color: #0f172a; margin: 0 0 16px 0; font-size: 20px;">Campus Pulse</h2>
    <p style="color: #334155; font-size: 14px; line-height: 1.5; margin: 0 0 16px 0;">Hello <strong>{user_name}</strong>,</p>
    <p style="color: #334155; font-size: 14px; line-height: 1.5; margin: 0 0 16px 0;">Your Campus Pulse account password was successfully updated.</p>
    <p style="color: #dc2626; font-size: 13px; line-height: 1.5; margin: 0 0 20px 0;">If you did not perform this action, please contact an administrator immediately.</p>
    <p style="color: #64748b; font-size: 12px; margin: 0;">Campus Pulse Security Team</p>
  </div>
</body>
</html>"""
    return _dispatch_email(to_email, subject, html_content, plain_text)


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
    frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    if activation_link.startswith("/"):
        full_activation_url = f"{frontend_url}{activation_link}"
    else:
        full_activation_url = activation_link

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
    subject = "Campus Pulse - Account Activation & Password Setup"
    return _dispatch_email(to_email, subject, html_content, plain_text)


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
