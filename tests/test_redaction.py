from app.redaction import redact_payload, redact_text


def test_redact_email_and_phone():
    text = "Patient john.doe@example.com or call 555-123-4567 for follow-up"
    redacted, counts = redact_text(text)
    assert "[EMAIL_REDACTED]" in redacted
    assert "[PHONE_REDACTED]" in redacted
    assert counts["EMAIL"] == 1
    assert counts["PHONE"] == 1


def test_redact_mrn_and_dob():
    text = "MRN: A1234567, DOB: 03/15/1962, presenting with chest pain"
    redacted, counts = redact_text(text)
    assert "[MRN_REDACTED]" in redacted
    assert "[DOB_REDACTED]" in redacted


def test_redact_nested_payload():
    payload = {
        "question": "Patient SSN 123-45-6789 has HFpEF",
        "max_per_source": 5,
    }
    redacted, counts = redact_payload(payload)
    assert "[SSN_REDACTED]" in redacted["question"]
    assert "123-45-6789" not in redacted["question"]
    assert redacted["max_per_source"] == 5  # numbers pass through
    assert counts["SSN"] == 1


def test_clean_text_unchanged():
    text = "Are SGLT2 inhibitors effective for HFpEF?"
    redacted, counts = redact_text(text)
    assert redacted == text
    assert counts == {}
