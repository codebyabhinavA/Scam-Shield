import uuid

import pytest
from fastapi.testclient import TestClient

from database import get_connection
from main import app

client = TestClient(app)


@pytest.fixture
def new_user():
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    password = "correct-horse-battery"
    yield email, password
    with get_connection() as conn:
        conn.execute("DELETE FROM users WHERE email = %s", (email,))


def test_signup_login_and_me(new_user):
    email, password = new_user
    r = client.post("/auth/signup", json={"email": email, "password": password})
    assert r.status_code == 201
    assert "password_hash" not in r.json()

    r = client.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    token = r.json()["access_token"]

    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == email


def test_login_wrong_password(new_user):
    email, password = new_user
    client.post("/auth/signup", json={"email": email, "password": password})
    r = client.post("/auth/login", json={"email": email, "password": "wrong-password"})
    assert r.status_code == 401


def test_protected_route_rejects_missing_or_bad_token():
    assert client.get("/auth/me").status_code == 401
    bad = {"Authorization": "Bearer not-a-real-token"}
    assert client.get("/auth/me", headers=bad).status_code == 401