import re

# Order matters: more specific patterns run first. Best-effort, not perfect.
_OTP = re.compile(r"(?i)(\b(?:otp|code|pin|passcode|cvv)\b\D{0,20})(\d{4,8})\b")
_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")
_PHONE = re.compile(
    r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)|(?<!\d)\+\d{1,3}[\s-]?\d{6,12}(?!\d)"
)
_ACCOUNT = re.compile(r"(?<!\d)\d{9,18}(?!\d)")


def redact(text: str) -> str:
    text = _OTP.sub(r"\1[OTP]", text)
    text = _CARD.sub("[CARD]", text)
    text = _PHONE.sub("[PHONE]", text)
    text = _ACCOUNT.sub("[ACCOUNT]", text)
    return text