import json
import os
import sqlite3
import threading
from typing import Optional

from utils.logger import get_logger

logger = get_logger(__name__)

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "").strip()
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "").strip()
VAPID_SUBJECT = os.getenv("VAPID_SUBJECT", "mailto:admin@campuspulse.edu").strip()


def _get_db_path(db_path: Optional[str] = None) -> str:
    if db_path:
        return db_path
    return os.environ.get("DATABASE_PATH", "storage/campus_pulse.db")


def get_vapid_public_key() -> str:
    """Return the configured VAPID public key, or empty string if disabled."""
    return os.getenv("VAPID_PUBLIC_KEY", VAPID_PUBLIC_KEY).strip()


def get_vapid_private_key() -> str:
    """Return the configured VAPID private key, or empty string if disabled."""
    return os.getenv("VAPID_PRIVATE_KEY", VAPID_PRIVATE_KEY).strip()


def get_vapid_subject() -> str:
    """Return the configured VAPID subject claim."""
    return os.getenv("VAPID_SUBJECT", VAPID_SUBJECT).strip()


def is_push_enabled() -> bool:
    """Return True if VAPID keys are configured for Web Push."""
    return bool(get_vapid_public_key() and get_vapid_private_key())


def save_subscription(
    user_id: str,
    endpoint: str,
    p256dh: str,
    auth: str,
    db_path: Optional[str] = None,
) -> None:
    """Save or update a user's Web Push subscription."""
    if not endpoint or not p256dh or not auth:
        raise ValueError("endpoint, p256dh and auth are required for push subscription.")

    target_db = _get_db_path(db_path)
    with sqlite3.connect(target_db) as conn:
        conn.execute(
            """
            INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
            ON CONFLICT(endpoint) DO UPDATE SET
                user_id = excluded.user_id,
                p256dh = excluded.p256dh,
                auth = excluded.auth,
                created_at = datetime('now');
            """,
            (user_id, endpoint, p256dh, auth),
        )
        conn.commit()
    logger.info(f"Saved push subscription for user {user_id}.")


def remove_subscription(endpoint: str, db_path: Optional[str] = None) -> None:
    """Remove a Web Push subscription (e.g. on unsubscribe or 404/410)."""
    target_db = _get_db_path(db_path)
    with sqlite3.connect(target_db) as conn:
        conn.execute("DELETE FROM push_subscriptions WHERE endpoint = ?", (endpoint,))
        conn.commit()
    logger.info(f"Removed push subscription for endpoint: {endpoint[:40]}...")


def get_subscriptions_for_user(
    user_id: str, db_path: Optional[str] = None
) -> list[dict]:
    """Retrieve all push subscriptions for a given user."""
    target_db = _get_db_path(db_path)
    with sqlite3.connect(target_db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT user_id, endpoint, p256dh, auth, created_at FROM push_subscriptions WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def get_all_subscriptions(db_path: Optional[str] = None) -> list[dict]:
    """Retrieve all push subscriptions in the system."""
    target_db = _get_db_path(db_path)
    with sqlite3.connect(target_db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT user_id, endpoint, p256dh, auth, created_at FROM push_subscriptions"
        ).fetchall()
        return [dict(r) for r in rows]


def send_web_push(subscription: dict, payload: dict, db_path: Optional[str] = None) -> bool:
    """Send a single Web Push notification. Removes subscription on 404/410."""
    if not is_push_enabled():
        logger.debug("VAPID keys not configured; web push skipped.")
        return False

    try:
        from pywebpush import WebPushException, webpush
    except ImportError:
        logger.warning("pywebpush is not installed; web push skipped.")
        return False

    sub_info = {
        "endpoint": subscription["endpoint"],
        "keys": {
            "p256dh": subscription["p256dh"],
            "auth": subscription["auth"],
        },
    }

    try:
        data_str = json.dumps(payload)
        webpush(
            subscription_info=sub_info,
            data=data_str,
            vapid_private_key=get_vapid_private_key(),
            vapid_claims={"sub": get_vapid_subject()},
        )
        return True
    except WebPushException as ex:
        status_code = getattr(getattr(ex, "response", None), "status_code", None)
        logger.warning(f"WebPushException delivery failed (status {status_code}): {ex}")
        if status_code in (404, 410):
            logger.info(f"Subscription expired or dead (HTTP {status_code}). Removing {subscription['endpoint']}")
            remove_subscription(subscription["endpoint"], db_path=db_path)
        return False
    except Exception as err:
        logger.warning(f"Unexpected error in send_web_push: {err}")
        return False


def send_web_push_for_notification(
    receiver_id: str,
    notification: dict,
    db_path: Optional[str] = None,
) -> None:
    """
    Asynchronously dispatch Web Push notification to the receiver's devices.
    Executes in a background daemon thread so it never blocks HTTP request threads.
    """
    if not is_push_enabled():
        return

    def _worker():
        try:
            ref_type = notification.get("reference_type")
            ref_id = notification.get("reference_id")
            url = f"/complaints/{ref_id}" if ref_type == "Complaint" and ref_id else "/notifications"

            payload = {
                "title": notification.get("title") or "Campus Pulse",
                "body": notification.get("message") or "",
                "data": {
                    "notification_id": notification.get("notification_id"),
                    "reference_type": ref_type,
                    "reference_id": ref_id,
                    "url": url,
                },
            }

            if receiver_id and receiver_id.lower() in ("all", "everyone"):
                subs = get_all_subscriptions(db_path=db_path)
            else:
                subs = get_subscriptions_for_user(receiver_id, db_path=db_path)

            for sub in subs:
                send_web_push(sub, payload, db_path=db_path)
        except Exception as err:
            logger.exception(f"Background web push worker error: {err}")

    threading.Thread(target=_worker, daemon=True).start()
