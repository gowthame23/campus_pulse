import os
import smtplib
from email.mime.text import MIMEText

from utils.logger import get_logger

logger = get_logger(__name__)


def send_notification_email(to_email, title, message):
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


def send_otp_email(to_email, otp):
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_from = os.environ.get("SMTP_FROM", smtp_username)

    body = f"Your Campus Pulse password reset OTP is: {otp}\nThis code will expire in 15 minutes."
    msg = MIMEText(body)
    msg["Subject"] = "Campus Pulse - Password Reset OTP"
    msg["From"] = smtp_from if smtp_from else "noreply@campus.edu"
    msg["To"] = to_email

    if not smtp_server or not smtp_username or not smtp_password:
        logger.warning("OTP email not sent: SMTP is not configured")
        return False

    try:
        port = int(smtp_port) if smtp_port else 587
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(msg["From"], [to_email], msg.as_string())
        server.quit()
        logger.info("Reset OTP email sent", extra={"recipient": to_email})
        return True
    except Exception as e:
        logger.exception("Reset OTP email delivery failed", extra={"recipient": to_email})
        return False


def send_password_changed_email(to_email, user_name):
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_username = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_from = os.environ.get("SMTP_FROM", smtp_username)

    body = f"Hello {user_name},\n\nYour Campus Pulse password was successfully updated.\nIf you did not perform this change, please contact an Administrator immediately."
    msg = MIMEText(body)
    msg["Subject"] = "Campus Pulse - Password Security Notification"
    msg["From"] = smtp_from if smtp_from else "noreply@campus.edu"
    msg["To"] = to_email

    if not smtp_server or not smtp_username or not smtp_password:
        print(f"[SIMULATION] Password updated notification email sent to {to_email}")
        return True

    try:
        port = int(smtp_port) if smtp_port else 587
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.sendmail(msg["From"], [to_email], msg.as_string())
        server.quit()
        print(f"Successfully sent password updated email to {to_email}")
        return True
    except Exception as e:
        print(f"[SIMULATION FALLBACK] Password updated notice to {to_email}: {e}")
        return False


def send_activation_email(to_email, activation_link, user_name="Student"):
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

    msg_body = (
        f"Hello {user_name},\n\n"
        f"Welcome to Campus Pulse! An account has been created for you.\n\n"
        f"Please click the following link to activate your account and set your permanent password:\n"
        f"{full_activation_url}\n\n"
        f"Security Notice:\n"
        f"- This activation link is unique to you and will expire in 7 days.\n"
        f"- Do not share this link with anyone.\n"
        f"- If you did not request this account, please contact your Campus Administrator immediately.\n\n"
        f"Regards,\n"
        f"Campus Pulse Team"
    )

    msg = MIMEText(msg_body)
    msg["Subject"] = "Campus Pulse - Account Activation & Password Setup"
    msg["From"] = smtp_from if smtp_from else "noreply@campus.edu"
    msg["To"] = to_email

    if not smtp_server or not smtp_username or not smtp_password:
        logger.warning(
            "Activation email simulated (SMTP not configured)",
            extra={"recipient": to_email}
        )
        return False

    try:
        port = int(smtp_port) if smtp_port else 587
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(msg["From"], [to_email], msg.as_string())
        logger.info("Activation email sent successfully", extra={"recipient": to_email})
        return True
    except Exception as e:
        logger.exception("Activation email delivery failed", extra={"recipient": to_email})
        return False

