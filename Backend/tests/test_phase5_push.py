import json
import os
import sys
import pytest
from unittest.mock import patch, MagicMock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from services.push_service import (
    get_vapid_public_key,
    is_push_enabled,
    save_subscription,
    remove_subscription,
    get_subscriptions_for_user,
    get_all_subscriptions,
    send_web_push,
    send_web_push_for_notification,
)

client = TestClient(app)


def _get_student_headers():
    login_res = client.post(
        "/auth/login",
        json={"username": "student@example.com", "password": "Student@123"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestPushNotifications:
    def test_get_vapid_public_key_endpoint(self):
        """GET /push/vapid-public-key should return json with public_key."""
        response = client.get("/push/vapid-public-key")
        assert response.status_code == 200
        data = response.json()
        assert "public_key" in data

    def test_push_subscribe_requires_auth(self):
        """POST /push/subscribe must reject unauthenticated requests."""
        payload = {
            "endpoint": "https://fcm.googleapis.com/fcm/send/fake-endpoint-1",
            "p256dh": "dummy-p256dh-key",
            "auth": "dummy-auth-secret",
        }
        res = client.post("/push/subscribe", json=payload)
        assert res.status_code in (401, 403)

    def test_push_subscribe_validation(self):
        """POST /push/subscribe should return 400 if keys or endpoint are missing."""
        headers = _get_student_headers()
        res = client.post("/push/subscribe", json={"endpoint": ""}, headers=headers)
        assert res.status_code == 400

    def test_push_subscribe_and_unsubscribe_flow(self):
        """Authenticated student can subscribe, verify persistence, and unsubscribe."""
        headers = _get_student_headers()
        endpoint = "https://fcm.googleapis.com/fcm/send/test-endpoint-unique-123"
        payload = {
            "endpoint": endpoint,
            "keys": {
                "p256dh": "BD_test_p256dh_key_content_base64",
                "auth": "test_auth_secret_token",
            },
        }

        # Subscribe
        sub_res = client.post("/push/subscribe", json=payload, headers=headers)
        assert sub_res.status_code == 200
        assert sub_res.json()["status"] == "subscribed"

        # Verify DB entry
        user_id = sub_res.json()["user_id"]
        subs = get_subscriptions_for_user(user_id)
        matching = [s for s in subs if s["endpoint"] == endpoint]
        assert len(matching) == 1
        assert matching[0]["p256dh"] == "BD_test_p256dh_key_content_base64"
        assert matching[0]["auth"] == "test_auth_secret_token"

        # Unsubscribe
        unsub_res = client.post(
            "/push/unsubscribe",
            json={"endpoint": endpoint},
            headers=headers,
        )
        assert unsub_res.status_code == 200
        assert unsub_res.json()["status"] == "unsubscribed"

        # Verify DB entry removed
        subs_after = get_subscriptions_for_user(user_id)
        assert not any(s["endpoint"] == endpoint for s in subs_after)

    def test_subscription_service_crud(self):
        """Direct test of push_service database CRUD functions."""
        user_id = "test-user-uuid"
        endpoint = "https://example.com/push/test-endpoint-direct"
        p256dh = "test-p256dh"
        auth = "test-auth"

        try:
            save_subscription(user_id, endpoint, p256dh, auth)
            user_subs = get_subscriptions_for_user(user_id)
            assert any(s["endpoint"] == endpoint for s in user_subs)

            all_subs = get_all_subscriptions()
            assert any(s["endpoint"] == endpoint for s in all_subs)

            # Test idempotent update
            save_subscription(user_id, endpoint, "updated-p256dh", "updated-auth")
            updated_subs = get_subscriptions_for_user(user_id)
            updated_sub = next(s for s in updated_subs if s["endpoint"] == endpoint)
            assert updated_sub["p256dh"] == "updated-p256dh"
            assert updated_sub["auth"] == "updated-auth"
        finally:
            remove_subscription(endpoint)
            remaining = get_subscriptions_for_user(user_id)
            assert not any(s["endpoint"] == endpoint for s in remaining)

    def test_dead_subscription_cleanup_on_410(self):
        """send_web_push should automatically prune subscription on HTTP 410 Gone."""
        endpoint = "https://example.com/push/dead-subscription-410"
        save_subscription("user-dead-test", endpoint, "key", "auth")

        sub = {
            "endpoint": endpoint,
            "p256dh": "key",
            "auth": "auth",
        }

        # Mock pywebpush to raise WebPushException with HTTP 410
        with patch("services.push_service.is_push_enabled", return_value=True):
            try:
                from pywebpush import WebPushException
            except ImportError:
                class WebPushException(Exception):
                    pass

            mock_response = MagicMock()
            mock_response.status_code = 410
            exc = WebPushException("Gone")
            exc.response = mock_response

            with patch("pywebpush.webpush", side_effect=exc):
                delivered = send_web_push(sub, {"title": "Test", "body": "Msg"})
                assert delivered is False

        # Verify subscription was purged
        all_subs = get_all_subscriptions()
        assert not any(s["endpoint"] == endpoint for s in all_subs)

    def test_send_web_push_for_notification_graceful_when_disabled(self):
        """When push is not enabled, dispatch completes safely without exception."""
        with patch("services.push_service.is_push_enabled", return_value=False):
            # Should return immediately without starting background work
            send_web_push_for_notification(
                "user-1",
                {"title": "Notice", "message": "Test push dispatch"},
            )
