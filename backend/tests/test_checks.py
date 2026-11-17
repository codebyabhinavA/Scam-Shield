import uuid

import pytest
from fastapi.testclient import TestClient
from ai_service import AIOutputError, AIServiceError
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
def _raiser(exc):
    def f(text):
        raise exc
    return f


def test_ai_service_error_returns_503_and_saves_nothing(two_users, monkeypatch):
    a, _ = two_users
    monkeypatch.setattr("routers.checks.get_verdict", _raiser(AIServiceError()))
    assert client.post("/checks", json=MSG, headers=a).status_code == 503
    assert client.get("/checks", headers=a).json() == []


def test_ai_bad_output_returns_502(two_users, monkeypatch):
    a, _ = two_users
    monkeypatch.setattr("routers.checks.get_verdict", _raiser(AIOutputError()))
    assert client.post("/checks", json=MSG, headers=a).status_code == 502


def test_stored_message_is_redacted(two_users):
    a, _ = two_users
    r = client.post(
        "/checks",
        json={"message_text": "Your OTP is 482913, call 9876543210"},
        headers=a,
    )
    text = r.json()["message_text"]
    assert "482913" not in text and "9876543210" not in text
def test_feedback_roundtrip_and_validation(two_users):
    a, b = two_users
    cid = client.post("/checks", json=MSG, headers=a).json()["id"]
    url = f"/checks/{cid}/feedback"

    r = client.patch(url, json={"feedback": "scam"}, headers=a)
    assert r.status_code == 200 and r.json()["feedback"] == "scam"
    assert client.patch(url, json={"feedback": "banana"}, headers=a).status_code == 422
    assert client.patch(url, json={"feedback": "legit"}, headers=b).status_code == 404
    assert client.patch(url, json={"feedback": None}, headers=a).json()["feedback"] is None


def test_rate_limit_blocks_and_deleting_does_not_reset(two_users, monkeypatch):
    a, b = two_users
    monkeypatch.setattr("rate_limit.MAX_CHECKS_PER_HOUR", 2)
    ids = [client.post("/checks", json=MSG, headers=a).json()["id"] for _ in range(2)]
    for cid in ids:
        client.delete(f"/checks/{cid}", headers=a)

    r = client.post("/checks", json=MSG, headers=a)
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) > 0
    assert client.post("/checks", json=MSG, headers=b).status_code == 201