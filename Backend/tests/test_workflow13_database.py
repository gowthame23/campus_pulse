import pytest
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from fastapi.testclient import TestClient
from api.main import app
from middleware.rate_limiter import auth_limiter

client = TestClient(app)

def _reset_limiter():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()

def _get_headers(email, password):
    _reset_limiter()
    login_res = client.post("/auth/login", json={"username": email, "password": password})
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_workflow_13_master_references():
    headers = _get_headers("gowtham.e23@iiits.in", "Student@123")

    # 1. Get all master references
    res_all = client.get("/master-references", headers=headers)
    assert res_all.status_code == 200
    refs = res_all.json()
    assert isinstance(refs, list)
    assert len(refs) > 0

    # 2. Get priority category references
    res_prio = client.get("/master-references/PRIORITY", headers=headers)
    assert res_prio.status_code == 200
    prios = res_prio.json()
    codes = [p["code"] for p in prios]
    assert "HIGH" in codes
    assert "MEDIUM" in codes
    assert "LOW" in codes
