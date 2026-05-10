"""Lightweight PII redaction for clinical request payloads.

For production healthcare deployments, this should be replaced with
Microsoft Presidio (https://microsoft.github.io/presidio/) which combines
regex + NLP for higher recall on names, locations, and clinical IDs.
"""
import re
from typing import Any

# Order matters — more specific patterns first
PATTERNS: list[tuple[str, re.Pattern]] = [
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("EMAIL", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")),
    ("PHONE", re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    ("MRN", re.compile(r"\b(?:MRN|Medical Record(?:\s+Number)?)[:\s#]*([A-Z0-9-]{4,})\b", re.IGNORECASE)),
    ("DOB", re.compile(r"\b(?:DOB|Date of Birth)[:\s]*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE)),
    ("DATE", re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")),
    # Credit cards (just in case)
    ("CREDIT_CARD", re.compile(r"\b(?:\d[ -]*?){13,16}\b")),
]


def redact_text(text: str) -> tuple[str, dict[str, int]]:
    """Redact PII from a string. Returns (redacted_text, counts_per_type)."""
    counts: dict[str, int] = {}
    redacted = text
    for label, pattern in PATTERNS:
        matches = pattern.findall(redacted)
        if matches:
            counts[label] = len(matches)
            redacted = pattern.sub(f"[{label}_REDACTED]", redacted)
    return redacted, counts


def redact_payload(obj: Any) -> tuple[Any, dict[str, int]]:
    """Recursively redact PII from nested dict/list/str structures."""
    total_counts: dict[str, int] = {}

    def _walk(node):
        if isinstance(node, str):
            redacted, counts = redact_text(node)
            for k, v in counts.items():
                total_counts[k] = total_counts.get(k, 0) + v
            return redacted
        if isinstance(node, dict):
            return {k: _walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [_walk(item) for item in node]
        return node

    return _walk(obj), total_counts
