import uuid

import pytest
from fastapi.testclient import TestClient

from database import get_connection
from main import app

client = TestClient(app)
MSG = {"message_text": "Your account will be blocked. Update KYC now"}


def make_user():
    email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    password = "correct-horse-battery"
    client.post("/auth/signup", json={"email": email, "password": password})
    r = client.post("/auth/login", json={"email": email, "password": password})
    return email, {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def two_users():
    email_a, a = make_user()
    email_b, b = make_user()
    yield a, b
    with get_connection() as conn:
        conn.execute("DELETE FROM users WHERE email = ANY(%s)", ([email_a, email_b],))


def test_checks_require_login():
    assert client.post("/checks", json=MSG).status_code == 401
    assert client.get("/checks").status_code == 401


def test_create_and_list(two_users):
    a, _ = two_users
    r = client.post("/checks", json=MSG, headers=a)
    assert r.status_code == 201
    assert len(r.json()["red_flags"]) >= 1
    assert len(client.get("/checks", headers=a).json()) == 1


def test_user_cannot_access_others_check(two_users):
    a, b = two_users
    check_id = client.post("/checks", json=MSG, headers=a).json()["id"]
    assert client.get(f"/checks/{check_id}", headers=b).status_code == 404
    assert client.delete(f"/checks/{check_id}", headers=b).status_code == 404
    assert client.get("/checks", headers=b).json() == []
    assert client.get(f"/checks/{check_id}", headers=a).status_code == 200


def test_validation_and_delete(two_users):
    a, _ = two_users
    assert client.post("/checks", json={"message_text": "  "}, headers=a).status_code == 422
    check_id = client.post("/checks", json=MSG, headers=a).json()["id"]
    assert client.delete(f"/checks/{check_id}", headers=a).status_code == 204
    assert client.get(f"/checks/{check_id}", headers=a).status_code == 404