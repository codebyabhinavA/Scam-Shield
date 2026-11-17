import logging

from google.genai import errors

from ai_client import analyze_message
from models import AIVerdict

log = logging.getLogger(__name__)


class AIServiceError(Exception):
    """The AI provider failed or is unavailable (timeout, quota, network)."""


class AIOutputError(Exception):
    """The AI answered, but not in the shape we require."""


def get_verdict(text: str) -> AIVerdict:
    for attempt in (1, 2):
        try:
            raw = analyze_message(text)
            return AIVerdict.model_validate(raw)
        except (ValueError, TypeError):
            # bad JSON, missing fields, or invalid values: try once more
            log.warning("AI output invalid (attempt %s)", attempt)
        except errors.APIError as e:
            log.error("AI provider error, code=%s", getattr(e, "code", None))
            raise AIServiceError() from e
        except Exception as e:
            log.exception("Unexpected AI failure")
            raise AIServiceError() from e
    raise AIOutputError()