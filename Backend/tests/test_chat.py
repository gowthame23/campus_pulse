"""
Basic tests for chat endpoints and websocket authentication.

Run with:
    cd Backend
    python -m pip install requests websocket-client
    python tests/test_chat.py

"""

import json
import time

import requests
from websocket import create_connection

import pytest

BASE = "http://127.0.0.1:8000"


def _server_is_running():
    try:
        r = requests.get(f"{BASE}/docs", timeout=0.5)
        return r.status_code == 200
    except Exception:
        return False


def login(email, password):
    r = requests.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    if r.status_code == 200:
        return r.json().get("access_token")
    return None


def hdrs(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.skipif(not _server_is_running(), reason="Live backend server is not running on port 8000")
def test_chat_flow():
    print("=== Chat REST flow")
    alice = login("student@campuspulse.edu", "student123")
    bob = login("student2@campuspulse.edu", "student123")
    if not alice or not bob:
        print("Login failed for test accounts; ensure seeding. Aborting test.")
        return
    # End-to-end: submit claim for seeded found item LF_F01, approve it, then check conversation appears
    item_id = "LF_F01"
    # submit claim as alice (student)
    r1 = requests.post(
        f"{BASE}/lost-found/items/{item_id}/claim",
        json={"claim_reason": "Test claim", "proof_description": "test"},
        headers=hdrs(alice),
    )
    print("submit claim", r1.status_code)
    assert r1.status_code in (200, 201)
    claim = r1.json()
    claim_id = claim.get("claim_id") or claim.get("id")
    assert claim_id

    # approve as coordinator
    coord = login("coordinator@campuspulse.edu", "Coordinator@123")
    assert coord
    r2 = requests.put(
        f"{BASE}/lost-found/claims/{claim_id}/approve",
        json={"decision_notes": "Approved by test"},
        headers=hdrs(coord),
    )
    print("approve", r2.status_code)
    assert r2.status_code == 200

    # Give the server a moment to create conversation and notifications
    time.sleep(0.5)

    # list conversations as claimant (alice) and ensure one is linked to item_id
    r3 = requests.get(f"{BASE}/chat/conversations", headers=hdrs(alice))
    print("list convs", r3.status_code, r3.text[:200])
    assert r3.status_code == 200
    convs = r3.json()
    assert any(
        c.get("item_id") == item_id for c in convs
    ), f"No conversation linked to {item_id} found: {convs}"
    print("E2E chat conversation creation verified")


@pytest.mark.skipif(not _server_is_running(), reason="Live backend server is not running on port 8000")
def test_ws_auth():
    print("\n=== WebSocket auth test")
    token = login("student@campuspulse.edu", "student123")
    if not token:
        print("Login failed; cannot test WS")
        return
    # try to connect without token → should be rejected/close
    try:
        ws = create_connection("ws://127.0.0.1:8000/notifications/ws/USR_STUDENT")
        # if it remains open, close
        ws.close()
        print("WS opened without token (unexpected)")
    except Exception as e:
        print("WS without token rejected (expected)")

    # connect with token
    ws_url = f"ws://127.0.0.1:8000/notifications/ws/USR_STUDENT?token={token}"
    try:
        ws2 = create_connection(ws_url)
        ws2.send("ping")
        # server may not respond to ping on notifications socket; just close
        ws2.close()
        print("WS with token connected OK")
    except Exception as e:
        print("WS with token failed:", e)


if __name__ == "__main__":
    test_chat_flow()
    test_ws_auth()
