from redaction import redact


def test_masks_otp_and_phone():
    out = redact("Your OTP is 482913. Call +91 98765 43210 now")
    assert "482913" not in out and "98765" not in out
    assert "[OTP]" in out and "[PHONE]" in out


def test_masks_card_and_account():
    out = redact("Card 4111 1111 1111 1111 and account 123456789012")
    assert "4111" not in out and "123456789012" not in out


def test_keeps_links_and_plain_text():
    text = "Update KYC at http://bit.ly/abc123 today"
    assert redact(text) == text