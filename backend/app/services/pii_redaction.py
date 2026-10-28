from __future__ import annotations

import re


_PATTERNS = (
    (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE), "[EMAIL_REDACTED]"),
    (re.compile(r"\b(?:\+?\d[\d\s().-]{8,}\d)\b"), "[PHONE_REDACTED]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN_REDACTED]"),
    (re.compile(r"(?i)\b(password|passcode|otp|api[_ -]?key|secret)\s*[:=]\s*\S+"), r"\1=[SECRET_REDACTED]"),
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[IP_REDACTED]"),
)


def redact_pii(text: str) -> str:
    redacted = text
    for pattern, replacement in _PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted
