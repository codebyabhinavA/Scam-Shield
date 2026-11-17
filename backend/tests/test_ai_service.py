import pytest

from ai_service import AIOutputError, AIServiceError, get_verdict

GOOD = {"risk_level": "low", "summary": "ok", "red_flags": [], "next_steps": "none"}


def test_valid_output_passes(monkeypatch):
    monkeypatch.setattr("ai_service.analyze_message", lambda t: GOOD)
    assert get_verdict("hello there").risk_level == "low"


def test_bad_output_retries_then_fails(monkeypatch):
    calls = []

    def bad(t):
        calls.append(1)
        return {"risk_level": "banana"}

    monkeypatch.setattr("ai_service.analyze_message", bad)
    with pytest.raises(AIOutputError):
        get_verdict("hello there")
    assert len(calls) == 2


def test_bad_then_good_recovers(monkeypatch):
    answers = iter([{"nonsense": 1}, GOOD])
    monkeypatch.setattr("ai_service.analyze_message", lambda t: next(answers))
    assert get_verdict("hello there").risk_level == "low"


def test_provider_failure_becomes_service_error(monkeypatch):
    def boom(t):
        raise ConnectionError("network down")

    monkeypatch.setattr("ai_service.analyze_message", boom)
    with pytest.raises(AIServiceError):
        get_verdict("hello there")