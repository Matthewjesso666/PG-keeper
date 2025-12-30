"""Safety filters for PII redaction and policy enforcement."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List


class SafetyPolicyError(ValueError):
    """Raised when a draft violates the active safety policy."""


@dataclass
class Policy:
    """Represents safety settings for outbound drafts."""

    allow_pii: bool = False
    redact_before_send: bool = True
    require_policy_check: bool = True

    @classmethod
    def from_settings(cls, settings: Dict[str, Any]) -> "Policy":
        return cls(
            allow_pii=bool(settings.get("allow_pii", False)),
            redact_before_send=bool(settings.get("redact_before_send", True)),
            require_policy_check=bool(settings.get("require_policy_check", True)),
        )


# Simple PII patterns that are easy to reason about for tests.
PII_PATTERNS: Dict[str, re.Pattern[str]] = {
    "email": re.compile(r"[\w.%-]+@[\w.-]+\.[A-Za-z]{2,}", re.IGNORECASE),
    "phone": re.compile(r"\b\+?\d{1,3}[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
}


def find_pii_segments(text: str) -> List[str]:
    """Return a list of substrings that match known PII patterns."""

    matches: List[str] = []
    for pattern in PII_PATTERNS.values():
        matches.extend(pattern.findall(text))
    return matches


def contains_pii(text: str) -> bool:
    """Check if text contains any PII markers."""

    return bool(find_pii_segments(text))


def _redaction_replacements() -> Iterable[tuple[re.Pattern[str], str]]:
    return (
        (PII_PATTERNS["email"], "[REDACTED EMAIL]"),
        (PII_PATTERNS["phone"], "[REDACTED PHONE]"),
        (PII_PATTERNS["ssn"], "[REDACTED SSN]"),
    )


def redact_pii(text: str) -> str:
    """Redact common PII markers from text using simple substitutions."""

    redacted = text
    for pattern, replacement in _redaction_replacements():
        redacted = pattern.sub(replacement, redacted)
    return redacted


def evaluate_policy_and_redact(
    draft: str, settings: Dict[str, Any], redaction_override: bool | None = None
) -> str:
    """
    Apply redaction toggles and safety checks before sending drafts.

    The policy is derived from the provided settings. Redaction can be forced on/off
    with ``redaction_override``; otherwise the policy toggle is used.
    """

    policy = Policy.from_settings(settings)
    redaction_enabled = policy.redact_before_send if redaction_override is None else bool(redaction_override)

    sanitized = redact_pii(draft) if redaction_enabled else draft

    if policy.require_policy_check and not policy.allow_pii and contains_pii(sanitized):
        raise SafetyPolicyError("Draft contains PII and policy forbids sending it without redaction.")

    return sanitized
