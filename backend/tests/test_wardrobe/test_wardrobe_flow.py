"""
Wardrobe integration tests (real MongoDB `stylex_test`, real recommendation engine).

The clothing *classifier* is replaced by a deterministic fake so these tests check our
pipeline (storage, ownership, ranking, outfits, saved outfits) rather than model accuracy.
"""
import io
import uuid

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from PIL import Image
from pymongo import MongoClient

from app.cloth_analysis import schemas as cs
from app.config import settings
from app.main import app
from app.wardrobe import service as wardrobe_service

PASSWORD = "Sup3rSecret99"


def _png(color=(30, 60, 140), size=(120, 160)) -> bytes:
    img = Image.new("RGB", (200, 240), (255, 255, 255))  # white studio background
    img.paste(Image.new("RGB", size, color), (40, 40))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def _fake_analysis(category="shirt", cat_conf=0.9, style="casual", style_conf=0.8, rgb=(30, 60, 140)):
    hexcode = "#{:02x}{:02x}{:02x}".format(*rgb)

    async def fake(input_data, use_clip=True):
        return cs.ClothAnalysisResponse(
            success=True,
            features=cs.ClothFeatures(
                dominant_colors=[
                    cs.ColorInfo(name="white", hex_code="#ffffff", rgb=[255, 255, 255], percentage=61.0),
                    cs.ColorInfo(name="blue", hex_code=hexcode, rgb=list(rgb), percentage=39.0),
                ],
                category=cs.ClothingCategory(category), category_confidence=cat_conf,
                style=cs.StyleType(style), style_confidence=style_conf,
                formality_level=2, overall_confidence=0.7,
            ),
        )
    return fake


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def db():
    mc = MongoClient(settings.DATABASE_URL)
    yield mc["stylex_test"]
    mc.close()


@pytest.fixture
def fake_analyzer(monkeypatch):
    def install(**kw):
        monkeypatch.setattr(wardrobe_service, "analyze_clothing", _fake_analysis(**kw))
    install()
    return install


def _user(client):
    email = f"ward_{uuid.uuid4().hex[:10]}@example.com"
    client.post("/api/auth/register", json={"email": email, "password": PASSWORD, "name": "Ward Tester"})
    tok = client.post("/api/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    uid = client.get("/api/auth/me", headers=h).json()["user"]["user_id"]
    return uid, h


def _give_skin_profile(db, uid):
    db["user_profiles"].update_one(
        {"user_id": ObjectId(uid)},
        {"$set": {"skin_features": {
            "undertone": "warm", "depth": "medium", "skin_depth": "medium",
            "season": "autumn", "seasonal_type": "autumn",
            "lab_l": 60.0, "lab_a": 12.0, "lab_b": 20.0,
            "skin_rgb": [190, 150, 120], "dominant_colors": [], "confidence_score": 0.8,
        }}},
        upsert=True,
    )


def _upload(client, h, name=None, **kw):
    return client.post(
        "/api/wardrobe/items", headers=h,
        files={"file": ("shirt.png", _png(), "image/png")},
        data={"name": name} if name else {},
    )


def test_wardrobe_requires_auth(client):
    assert client.get("/api/wardrobe/items").status_code == 401
    assert client.post("/api/wardrobe/items", files={"file": ("a.png", _png(), "image/png")}).status_code == 401


def test_upload_persists_item_and_picks_garment_color_over_background(client, db, fake_analyzer):
    uid, h = _user(client)
    r = _upload(client, h, name="Navy shirt")
    assert r.status_code == 201, r.text
    item = r.json()
    assert item["name"] == "Navy shirt"
    assert item["category"] == "top" and item["subcategory"] == "shirt"
    assert item["primary_color"]["name"] == "blue"          # not the white background
    assert item["formality_level"] == 4                       # analyzer 1-5 scale doubled to 1-10
    assert item["needs_review"] is False

    stored = db["clothing_items"].find_one({"_id": ObjectId(item["id"])})
    assert str(stored["user_id"]) == uid
    assert stored["features"]["dominant_colors"][0]["name"] == "blue"

    # the photo is served to its owner
    img = client.get(item["image_url"], headers=h)
    assert img.status_code == 200 and img.headers["content-type"] == "image/jpeg"


def test_low_confidence_or_unknown_items_are_flagged(client, fake_analyzer):
    _, h = _user(client)
    fake_analyzer(category="shirt", cat_conf=0.1)
    assert _upload(client, h).json()["needs_review"] is True
    fake_analyzer(category="unknown", cat_conf=0.9)
    unknown = _upload(client, h).json()
    assert unknown["category"] == "unknown" and unknown["needs_review"] is True


def test_non_image_upload_is_rejected(client, fake_analyzer):
    _, h = _user(client)
    r = client.post("/api/wardrobe/items", headers=h, files={"file": ("a.txt", b"hello", "text/plain")})
    assert r.status_code == 400
    r = client.post("/api/wardrobe/items", headers=h, files={"file": ("a.png", b"not really png", "image/png")})
    assert r.status_code == 422


def test_items_are_private_to_their_owner(client, fake_analyzer):
    _, owner = _user(client)
    _, other = _user(client)
    item = _upload(client, owner).json()
    assert client.get(f"/api/wardrobe/items/{item['id']}", headers=other).status_code == 404
    assert client.get(item["image_url"], headers=other).status_code == 404
    assert client.delete(f"/api/wardrobe/items/{item['id']}", headers=other).status_code == 404
    assert client.patch(f"/api/wardrobe/items/{item['id']}", json={"name": "x"}, headers=other).status_code == 404
    assert client.get("/api/wardrobe/items", headers=other).json()["total"] == 0
    assert client.get("/api/wardrobe/items", headers=owner).json()["total"] == 1


def test_favorite_correct_and_delete(client, db, fake_analyzer):
    _, h = _user(client)
    fake_analyzer(category="shirt", cat_conf=0.1)
    item = _upload(client, h).json()
    assert item["needs_review"] is True

    fav = client.post(f"/api/wardrobe/items/{item['id']}/favorite", headers=h).json()
    assert fav["is_favorite"] is True
    assert client.get("/api/wardrobe/items?favorite=true", headers=h).json()["total"] == 1
    assert client.post(f"/api/wardrobe/items/{item['id']}/favorite", headers=h).json()["is_favorite"] is False

    fixed = client.patch(f"/api/wardrobe/items/{item['id']}",
                         json={"category": "bottom", "style": "business", "primary_color_hex": "#112233"},
                         headers=h).json()
    assert fixed["category"] == "bottom" and fixed["style"] == "business"
    assert fixed["needs_review"] is False and fixed["user_corrected"] is True
    assert fixed["primary_color"]["hex_code"] == "#112233" and fixed["primary_color"]["rgb"] == [17, 34, 51]
    assert client.patch(f"/api/wardrobe/items/{item['id']}", json={"category": "spaceship"}, headers=h).status_code == 422

    assert client.delete(f"/api/wardrobe/items/{item['id']}", headers=h).status_code == 204
    assert client.get(f"/api/wardrobe/items/{item['id']}", headers=h).status_code == 404
    assert db["clothing_items"].count_documents({"_id": ObjectId(item["id"])}) == 0


def test_recommendations_need_a_selfie_analysis_first(client, fake_analyzer):
    _, h = _user(client)
    _upload(client, h)
    r = client.get("/api/wardrobe/recommendations", headers=h)
    assert r.status_code == 409
    assert r.json()["details"]["error_code"] == "profile_incomplete"


def test_empty_wardrobe_reports_why(client, db):
    uid, h = _user(client)
    _give_skin_profile(db, uid)
    body = client.get("/api/wardrobe/recommendations", headers=h).json()
    assert body["recommendations"] == [] and body["reason"] == "empty_wardrobe"


def test_ranking_uses_real_wardrobe_and_season_colours(client, db, fake_analyzer):
    uid, h = _user(client)
    _give_skin_profile(db, uid)                       # warm autumn
    fake_analyzer(category="shirt", rgb=(204, 85, 0))  # burnt orange: an autumn colour
    good = _upload(client, h, name="Burnt orange shirt").json()
    fake_analyzer(category="jeans", rgb=(0, 120, 255))  # saturated cool blue
    other = _upload(client, h, name="Cool blue jeans").json()
    fake_analyzer(category="unknown", cat_conf=0.9)
    _upload(client, h, name="Mystery")                 # unknown category: never ranked

    body = client.get("/api/wardrobe/recommendations", headers=h).json()
    assert body["detected_season"] == "autumn" and body["undertone"] == "warm"
    ids = [r["item"]["id"] for r in body["recommendations"]]
    assert set(ids) == {good["id"], other["id"]}
    assert body["excluded_needs_review"] == 1
    assert [r["rank"] for r in body["recommendations"]] == [1, 2]
    scores = {r["item"]["id"]: r["color_score"] for r in body["recommendations"]}
    assert scores[good["id"]] > scores[other["id"]]    # warm colour beats cool blue for a warm autumn
    for r in body["recommendations"]:
        assert 0 <= r["overall_score"] <= 1 and r["reasoning"]


def test_outfits_and_saved_outfits(client, db, fake_analyzer):
    uid, h = _user(client)
    _give_skin_profile(db, uid)

    assert client.get("/api/wardrobe/outfits", headers=h).json()["outfits"] == []  # nothing yet

    fake_analyzer(category="shirt", rgb=(204, 85, 0))
    top = _upload(client, h).json()
    only_top = client.get("/api/wardrobe/outfits", headers=h).json()
    assert only_top["outfits"] == [] and only_top["reason"]

    fake_analyzer(category="pants", rgb=(90, 70, 50))
    bottom = _upload(client, h).json()
    outfits = client.get("/api/wardrobe/outfits", headers=h).json()["outfits"]
    assert outfits, "a top + bottom should produce an outfit"
    assert {i["item"]["id"] for i in outfits[0]["items"]} == {top["id"], bottom["id"]}

    # save (idempotent), list, delete
    payload = {"name": "Work look", "item_ids": [top["id"], bottom["id"]], "score": outfits[0]["outfit_score"]}
    first = client.post("/api/wardrobe/outfits/saved", json=payload, headers=h)
    again = client.post("/api/wardrobe/outfits/saved", json=payload, headers=h)
    assert first.status_code == 201 and again.json()["id"] == first.json()["id"]
    saved = client.get("/api/wardrobe/outfits/saved", headers=h).json()["outfits"]
    assert len(saved) == 1 and saved[0]["name"] == "Work look" and len(saved[0]["items"]) == 2

    # deleting an item hides outfits that no longer have two items
    client.delete(f"/api/wardrobe/items/{bottom['id']}", headers=h)
    assert client.get("/api/wardrobe/outfits/saved", headers=h).json()["outfits"] == []

    assert client.delete(f"/api/wardrobe/outfits/saved/{first.json()['id']}", headers=h).status_code == 204
    assert client.delete(f"/api/wardrobe/outfits/saved/{first.json()['id']}", headers=h).status_code == 404


def test_cannot_save_outfit_with_someone_elses_items(client, fake_analyzer):
    _, owner = _user(client)
    _, thief = _user(client)
    a = _upload(client, owner).json()
    b = _upload(client, owner).json()
    r = client.post("/api/wardrobe/outfits/saved", json={"item_ids": [a["id"], b["id"]]}, headers=thief)
    assert r.status_code == 404
