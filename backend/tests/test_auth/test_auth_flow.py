"""
Auth integration tests. Require a running MongoDB (uses the `stylex_test` database,
forced in conftest.py). They exercise real behaviour: registration, login, JWT
validation, refresh-token rotation + reuse detection, logout and protected routes.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app

PASSWORD = "Sup3rSecret99"


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _register(client, email=None, password=PASSWORD, name="Test User"):
    email = email or f"user_{uuid.uuid4().hex[:10]}@example.com"
    r = client.post("/api/auth/register", json={"email": email, "password": password, "name": name})
    return email, r


def _login(client, email, password=PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_register_creates_user(client):
    email, r = _register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["email"] == email
    assert "password" not in str(body).lower().replace("message", "")


def test_register_duplicate_email_conflicts(client):
    email, _ = _register(client)
    _, r = _register(client, email=email)
    assert r.status_code == 409


@pytest.mark.parametrize("password", ["short1", "allletters", "12345678"])
def test_register_rejects_weak_password(client, password):
    _, r = _register(client, password=password)
    assert r.status_code == 422


def test_login_wrong_password_is_401(client):
    email, _ = _register(client)
    assert _login(client, email, "WrongPass123").status_code == 401


def test_login_unknown_user_is_401(client):
    assert _login(client, "nobody@example.com").status_code == 401


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers=_auth("garbage")).status_code == 401


def test_login_then_me(client):
    email, _ = _register(client)
    r = _login(client, email)
    assert r.status_code == 200
    me = client.get("/api/auth/me", headers=_auth(r.json()["access_token"]))
    assert me.status_code == 200
    assert me.json()["user"]["email"] == email


def test_refresh_token_cannot_be_used_as_access_token(client):
    email, _ = _register(client)
    tokens = _login(client, email).json()
    r = client.get("/api/auth/me", headers=_auth(tokens["refresh_token"]))
    assert r.status_code == 401


def test_refresh_rotates_tokens(client):
    email, _ = _register(client)
    first = _login(client, email).json()
    r = client.post("/api/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert r.status_code == 200
    second = r.json()
    assert second["refresh_token"] != first["refresh_token"]
    assert second["access_token"] != first["access_token"]
    # New access token works
    assert client.get("/api/auth/me", headers=_auth(second["access_token"])).status_code == 200


def test_reusing_rotated_refresh_token_revokes_all_sessions(client):
    email, _ = _register(client)
    first = _login(client, email).json()
    second = client.post("/api/auth/refresh", json={"refresh_token": first["refresh_token"]}).json()
    # Replay the old token: rejected...
    replay = client.post("/api/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert replay.status_code == 401
    # ...and the legitimate newer token is revoked too (reuse detection)
    again = client.post("/api/auth/refresh", json={"refresh_token": second["refresh_token"]})
    assert again.status_code == 401


def test_access_token_is_not_accepted_for_refresh(client):
    email, _ = _register(client)
    tokens = _login(client, email).json()
    r = client.post("/api/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert r.status_code == 401


def test_logout_revokes_refresh_tokens(client):
    email, _ = _register(client)
    tokens = _login(client, email).json()
    out = client.post("/api/auth/logout", headers=_auth(tokens["access_token"]))
    assert out.status_code == 200
    r = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert r.status_code == 401


def test_protected_profile_route_requires_auth(client):
    # Any protected route must reject anonymous callers
    assert client.post("/api/auth/logout").status_code == 401
