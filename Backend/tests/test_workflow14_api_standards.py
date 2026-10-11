import pytest
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from utils.response import api_response
from middleware.rate_limiter import auth_limiter

client = TestClient(app)

def _reset_limiter():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()

def test_workflow_14_response_wrapper():
    resp = api_response(success=True, message="Success", data={"id": "CMP-123"})
    json_data = resp.body.decode("utf-8")
    assert "success" in json_data
    assert "CMP-123" in json_data
    assert "timestamp" in json_data

def test_workflow_14_http_status_codes():
    # 200 OK root index
    r_root = client.get("/")
    assert r_root.status_code == 200

    # 401 Unauthorized
    r_unauth = client.get("/complaints")
    assert r_unauth.status_code in (401, 403)

    # 404 Not Found
    r_notfound = client.get("/non-existent-route-xyz")
    assert r_notfound.status_code == 404
