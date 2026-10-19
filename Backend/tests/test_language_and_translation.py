import os
import sys
import pytest
from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from api.main import app
from api.dependencies import db_path
from middleware.rate_limiter import auth_limiter
from services.translation_service import TranslationService, detect_language

client = TestClient(app)


def _reset_limiter():
    auth_limiter._requests.clear()
    auth_limiter._lockouts.clear()
    client.cookies.clear()


def _login(username="gowtham.e23@iiits.in", password="Student@123"):
    _reset_limiter()
    resp = client.post("/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_language_detection_unicode():
    """Test fast script detection across English, Telugu, and Hindi."""
    assert detect_language("Ceiling fan not working in room 302") == "en"
    assert detect_language("గది 302 లో ఫ్యాన్ తిరగడం లేదు") == "te"
    assert detect_language("कमरा 302 में पंखा काम नहीं कर रहा है") == "hi"
    assert detect_language("Room 302 గది") == "te"  # Mixed script with Telugu chars


def test_user_language_persistence():
    """Test user updating their language preference via PUT /users/me/language."""
    headers = _login()

    # Set to Telugu
    resp = client.put("/users/me/language", json={"language": "te"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["language"] == "te"

    # Verify GET /auth/me reflects 'te'
    me_resp = client.get("/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["language"] == "te"

    # Set to Hindi
    resp = client.put("/users/me/language", json={"language": "hi"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["language"] == "hi"

    # Reset back to English
    resp = client.put("/users/me/language", json={"language": "en"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["language"] == "en"

    # Invalid language code rejected
    resp = client.put("/users/me/language", json={"language": "fr"}, headers=headers)
    assert resp.status_code in (400, 422)


def test_same_language_bypass():
    """Translating English complaint to English should bypass AI and return immediately."""
    translation_svc = TranslationService(db_path)
    complaint_data = {
        "complaint_id": "CMP_TEST_BYPASS",
        "title": "Water leak in lab",
        "description": "The pipe under the second washbasin is leaking water continuously.",
    }

    result = translation_svc.translate_complaint_description(complaint_data, target_language="en")
    assert result["translated_text"] == complaint_data["description"]
    assert result["source_language"] == "en"
    assert result["target_language"] == "en"
    assert result["provider"] == "bypass"
    assert result["cached"] is True


def test_translation_telugu_and_hindi_local_engine():
    """Test campus facility translation engine for Telugu and Hindi."""
    translation_svc = TranslationService(db_path)
    complaint_data = {
        "complaint_id": "CMP_TEST_TRANSLATE_1",
        "title": "Broken fan",
        "description": "Fan is not working in the study room.",
    }

    # Translate to Telugu
    te_result = translation_svc.translate_complaint_description(complaint_data, target_language="te")
    assert te_result["target_language"] == "te"
    assert te_result["source_language"] == "en"
    assert len(te_result["translated_text"]) > 0

    # Translate to Hindi
    hi_result = translation_svc.translate_complaint_description(complaint_data, target_language="hi")
    assert hi_result["target_language"] == "hi"
    assert hi_result["source_language"] == "en"
    assert len(hi_result["translated_text"]) > 0


def test_translation_caching_and_invalidation():
    """Test persistent caching in complaint_translations and cache invalidation on description update."""
    translation_svc = TranslationService(db_path)
    test_id = "CMP_CACHE_VERIFY_99"
    complaint_data = {
        "complaint_id": test_id,
        "title": "Leaking tap",
        "description": "Water tap in bathroom 101 is leaking badly.",
    }

    # First call: fresh translation (cached = False)
    res1 = translation_svc.translate_complaint_description(complaint_data, target_language="te")
    assert res1["cached"] is False

    # Second call: cache hit (cached = True)
    res2 = translation_svc.translate_complaint_description(complaint_data, target_language="te")
    assert res2["cached"] is True
    assert res2["translated_text"] == res1["translated_text"]

    # Invalidate cache for this complaint
    translation_svc.invalidate_complaint_translations(test_id)

    # Third call: cache was purged, fresh translation occurs
    res3 = translation_svc.translate_complaint_description(complaint_data, target_language="te")
    assert res3["cached"] is False


def test_api_translate_complaint_rbac_and_flow():
    """Test POST /complaints/{id}/translate with authentication and RBAC checks."""
    student_headers = _login()

    loc_resp = client.get("/locations", headers=student_headers)
    assert loc_resp.status_code == 200
    locations = loc_resp.json()
    assert len(locations) > 0
    loc_id = locations[0]["location_id"]

    dept_resp = client.get(f"/departments?location_id={loc_id}", headers=student_headers)
    assert dept_resp.status_code == 200
    departments = dept_resp.json()
    assert len(departments) > 0
    dept_id = departments[0]["department_id"]

    # Create a fresh complaint to ensure clean ownership
    create_payload = {
        "title": "Power outlet broken",
        "description": "The wall socket next to bed 2 is sparking and not working.",
        "location_id": loc_id,
        "department_id": dept_id,
        "priority": "Medium",
        "visibility_type": "Private",
    }
    create_resp = client.post("/complaints", json=create_payload, headers=student_headers)
    assert create_resp.status_code == 201
    cid = create_resp.json()["complaint_id"]

    # Request translation to Telugu
    tr_resp = client.post(
        f"/complaints/{cid}/translate",
        json={"target_language": "te"},
        headers=student_headers,
    )
    assert tr_resp.status_code == 200
    data = tr_resp.json()
    assert data["complaint_id"] == cid
    assert data["target_language"] == "te"
    assert "translated_text" in data
    assert "source_language" in data

    # Request translation without body -> defaults to user's language
    tr_default = client.post(
        f"/complaints/{cid}/translate",
        headers=student_headers,
    )
    assert tr_default.status_code == 200

    # Test cache hit on repeated call
    tr_cached = client.post(
        f"/complaints/{cid}/translate",
        json={"target_language": "te"},
        headers=student_headers,
    )
    assert tr_cached.status_code == 200
    assert tr_cached.json()["cached"] is True


def test_translate_unauthorized_user():
    """Unauthenticated users must be rejected with 401."""
    _reset_limiter()
    # Explicitly empty auth headers and cookies
    unauth_client = TestClient(app)
    resp = unauth_client.post("/complaints/CMP-12345/translate", json={"target_language": "te"})
    assert resp.status_code == 401
