"""
Selfie -> face analysis -> persisted profile pipeline.

Uses a real photograph of a face (scikit-image's bundled astronaut portrait) so that
MediaPipe Face Mesh actually runs, and a face-free photo for the failure path.
Requires a running MongoDB (database `stylex_test`).
"""
import base64
import io
import uuid

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from PIL import Image
from pymongo import MongoClient
from skimage import data

from app.config import settings
from app.main import app

PASSWORD = "Sup3rSecret99"


def _b64(arr) -> str:
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@pytest.fixture(scope="module")
def face_b64():
    return _b64(data.astronaut())


@pytest.fixture(scope="module")
def no_face_b64():
    return _b64(data.coffee())


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db():
    mc = MongoClient(settings.DATABASE_URL)
    yield mc["stylex_test"]
    mc.close()


def _new_user(client):
    email = f"selfie_{uuid.uuid4().hex[:10]}@example.com"
    client.post("/api/auth/register", json={"email": email, "password": PASSWORD, "name": "Selfie Tester"})
    tokens = client.post("/api/auth/login", json={"email": email, "password": PASSWORD}).json()
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}).json()
    return me["user"]["user_id"], {"Authorization": f"Bearer {tokens['access_token']}"}


def test_analysis_requires_authentication(client, face_b64):
    r = client.post("/api/face-analysis/analyze", json={"image_base64": face_b64})
    assert r.status_code == 401


def test_face_photo_is_analysed_and_persisted(client, db, face_b64):
    user_id, headers = _new_user(client)
    r = client.post("/api/face-analysis/analyze", json={"image_base64": face_b64}, headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    sf = body["skin_features"]
    assert sf["undertone"] in ("warm", "cool", "neutral")
    assert sf["skin_depth"] in ("fair", "light", "medium", "tan", "deep")
    assert sf["seasonal_type"] in ("spring", "summer", "autumn", "winter")
    assert 0 <= sf["lab_l"] <= 100
    assert len(sf["skin_rgb"]) == 3 and all(0 <= c <= 255 for c in sf["skin_rgb"])
    assert 0 < sf["confidence"] <= 1
    assert body["color_recommendations"]["best_colors"]

    # Persisted on the profile (derived data only - no image)
    profile = db["user_profiles"].find_one({"user_id": ObjectId(user_id)})
    assert profile["skin_features"]["undertone"] == sf["undertone"]
    assert profile["skin_features"]["season"] == sf["seasonal_type"]
    assert profile["style_preferences"]["recommended_colors"] == body["color_recommendations"]["best_colors"]
    assert profile["selfie_image_url"] is None  # the photo itself is never stored

    record = db["analysis_results"].find_one({"user_id": ObjectId(user_id), "analysis_type": "face"})
    assert record is not None


def test_photo_without_a_face_is_rejected_and_not_persisted(client, db, no_face_b64):
    user_id, headers = _new_user(client)
    r = client.post("/api/face-analysis/analyze", json={"image_base64": no_face_b64}, headers=headers)
    assert r.status_code == 422
    assert r.json()["details"]["error_code"] == "no_face_detected"

    profile = db["user_profiles"].find_one({"user_id": ObjectId(user_id)})
    assert not profile.get("skin_features")
    assert db["analysis_results"].count_documents({"user_id": ObjectId(user_id)}) == 0


def test_garbage_image_is_rejected(client):
    _, headers = _new_user(client)
    r = client.post("/api/face-analysis/analyze", json={"image_base64": "bm90IGFuIGltYWdl"}, headers=headers)
    assert r.status_code == 422
    assert r.json()["details"]["error_code"] == "invalid_image"


@pytest.mark.parametrize("url", ["http://127.0.0.1/x.png", "http://localhost:8000/x.png", "file:///etc/passwd"])
def test_private_urls_are_blocked(client, url):
    _, headers = _new_user(client)
    r = client.post("/api/face-analysis/analyze", json={"image_url": url}, headers=headers)
    assert r.status_code == 422


def test_onboarding_selfie_endpoint_uses_real_analysis(client, db, face_b64, no_face_b64):
    user_id, headers = _new_user(client)
    ok = client.post("/api/onboarding/analyze-selfie", json={"image_base64": face_b64}, headers=headers)
    assert ok.status_code == 200, ok.text
    assert ok.json()["face_detected"] is True
    assert db["user_profiles"].find_one({"user_id": ObjectId(user_id)})["skin_features"]

    bad = client.post("/api/onboarding/analyze-selfie", json={"image_base64": no_face_b64}, headers=headers)
    assert bad.status_code == 422


def test_onboarding_is_private_to_its_owner(client):
    owner_id, owner_headers = _new_user(client)
    _, other_headers = _new_user(client)
    assert client.get(f"/api/onboarding/progress/{owner_id}", headers=owner_headers).status_code == 200
    assert client.get(f"/api/onboarding/progress/{owner_id}", headers=other_headers).status_code == 403
    assert client.get(f"/api/onboarding/progress/{owner_id}").status_code == 401


def test_selfie_step_never_stores_the_raw_image(client, db, face_b64):
    user_id, headers = _new_user(client)
    r = client.post(
        f"/api/onboarding/step/selfie/{user_id}",
        json={"image_base64": face_b64, "face_shape": "oval"},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    doc = db["onboarding_progress"].find_one({"user_id": ObjectId(user_id)})
    assert "image_base64" not in doc["step_data"]["selfie"]
    assert doc["step_data"]["selfie"]["face_shape"] == "oval"
