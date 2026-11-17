import pytest

from models import AIRedFlag, AIVerdict

FAKE = AIVerdict(
    risk_level="high",
    summary="Fake verdict for tests.",
    red_flags=[AIRedFlag(type="urgency", explanation="Pressures you to act now.")],
    next_steps="Do not click links.",
)


@pytest.fixture(autouse=True)
def mock_ai(monkeypatch):
    monkeypatch.setattr("routers.checks.get_verdict", lambda text: FAKE)