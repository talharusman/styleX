"""
Onboarding completion: the exact flow the frontend performs at the last step.
Regression tests for "complete onboarding returned 422 and bounced me back".
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


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db():
    mc = MongoClient(settings.DATABASE_URL)
    yield mc["stylex_test"]
    mc.close()


@pytest.fixture(scope="module")
def face_b64():
    buf = io.BytesIO()
    Image.fromarray(data.astronaut()).save(buf, "PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _user(client):
    email = f"onb_{uuid.uuid4().hex[:10]}@example.com"
    client.post("/api/auth/register", json={"email": email, "password": PASSWORD, "name": "Onb Tester"})
    tok = client.post("/api/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    return client.get("/api/auth/me", headers=h).json()["user"]["user_id"], h


def _me(client, h):
    return client.get("/api/auth/me", headers=h).json()["user"]


def test_complete_requires_a_selfie_analysis(client):
    uid, h = _user(client)
    r = client.post(f"/api/onboarding/step/complete/{uid}", json={}, headers=h)
    assert r.status_code == 409
    assert r.json()["details"]["error_code"] == "profile_incomplete"
    assert _me(client, h)["onboarding_completed"] is False


def test_full_onboarding_flow_completes_and_syncs_profile(client, db, face_b64):
    uid, h = _user(client)
    assert client.post("/api/face-analysis/analyze", json={"image_base64": face_b64}, headers=h).status_code == 200

    skin = client.post(f"/api/onboarding/step/skin-tone/{uid}",
                       json={"skin_tone": "tan", "undertone": "warm", "confirmed_by_user": True}, headers=h)
    body = client.post(f"/api/onboarding/step/body-type/{uid}", json={"body_type": "athletic", "height": 178}, headers=h)
    style = client.post(f"/api/onboarding/step/style/{uid}",
                        json={"primary_style": "business_casual", "secondary_styles": ["minimalist", "classic"],
                              "favorite_colors": ["neutrals"], "avoid_colors": []}, headers=h)
    assert (skin.status_code, body.status_code, style.status_code) == (200, 200, 200), (skin.text, body.text, style.text)

    # The frontend posts no body for the final step
    done = client.post(f"/api/onboarding/step/complete/{uid}", headers=h)
    assert done.status_code == 200, done.text
    assert _me(client, h)["onboarding_completed"] is True

    profile = db["user_profiles"].find_one({"user_id": ObjectId(uid)})
    assert profile["body_measurements"]["body_type"] == "athletic"
    assert profile["body_measurements"]["height_cm"] == 178
    assert profile["style_preferences"]["primary_style"] == "business"        # business_casual -> profile vocabulary
    assert profile["style_preferences"]["secondary_styles"] == ["minimalist", "formal"]
    # selfie-derived palette written earlier must survive the sync
    assert profile["style_preferences"]["recommended_colors"]
    assert profile["skin_features"]["undertone"]


@pytest.mark.parametrize("ui_value", ["lean", "smart-casual", "bulky"])
def test_unmapped_ui_values_are_rejected_not_silently_dropped(client, ui_value):
    """The frontend must translate its ids (see store/onboardingMapping.js); raw ids are invalid."""
    uid, h = _user(client)
    path, payload = (
        ("body-type", {"body_type": ui_value}) if ui_value in ("lean", "bulky")
        else ("style", {"primary_style": ui_value})
    )
    assert client.post(f"/api/onboarding/step/{path}/{uid}", json=payload, headers=h).status_code == 422
