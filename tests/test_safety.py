import pytest

from pg_keeper.safety.filters import SafetyPolicyError, contains_pii, evaluate_policy_and_redact, redact_pii


BASE_SETTINGS = {
    "allow_pii": False,
    "redact_before_send": True,
    "require_policy_check": True,
}


def test_redaction_applied_when_enabled():
    draft = "Contact me at worker@example.com or +1-202-555-0100."
    sanitized = evaluate_policy_and_redact(draft, BASE_SETTINGS)
    assert "[REDACTED EMAIL]" in sanitized
    assert "[REDACTED PHONE]" in sanitized
    assert not contains_pii(sanitized)


def test_policy_blocks_pii_without_redaction():
    draft = "SSN: 123-45-6789"
    settings = {**BASE_SETTINGS, "redact_before_send": False}
    with pytest.raises(SafetyPolicyError):
        evaluate_policy_and_redact(draft, settings)


def test_redaction_override_allows_safe_send():
    draft = "Email me at case.agent@example.com"
    settings = {**BASE_SETTINGS, "redact_before_send": False}
    sanitized = evaluate_policy_and_redact(draft, settings, redaction_override=True)
    assert "[REDACTED EMAIL]" in sanitized
    assert not contains_pii(sanitized)


def test_allows_pii_when_policy_permits():
    draft = "Email me at case.agent@example.com"
    settings = {**BASE_SETTINGS, "allow_pii": True, "redact_before_send": False}
    sanitized = evaluate_policy_and_redact(draft, settings)
    assert sanitized == draft
    assert contains_pii(sanitized)
