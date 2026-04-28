#!/usr/bin/env python3
"""Sanitize a SonnetReviewResult finding's free-text fields before they reach
a Codex fix-round prompt.

Per WP-SCP-022 §4.3 invariant 9: reviewer findings entering Codex prompts
must be stripped of control characters, length-capped, and JSON-string-
encoded so they cannot carry prompt-injection payloads through to the
resumed Codex session.

Closes WP-SCP-022 R1 CRIT-BYPASS-004.

Usage:
    cat finding.json | scripts/sanitize_review_finding.py > clean.json
    scripts/sanitize_review_finding.py < findings-list.json > clean-list.json

Input shape: either a single finding object or a JSON array of finding
objects. Each finding object has at minimum the SonnetReviewResult
finding properties: id, severity, claim, evidence, impact, mitigation.
"""

from __future__ import annotations

import json
import sys

_ASCII_CONTROLS = list(range(0x00, 0x20)) + [0x7F]
# Closes WP-SCP-022 R2 BYPASS-003: Unicode line/paragraph separators that
# act as newlines in many parsers but bypass an ASCII-only control filter.
_UNICODE_SEPARATORS = [0x0085, 0x2028, 0x2029]
CONTROL_CHARS = "".join(chr(c) for c in _ASCII_CONTROLS + _UNICODE_SEPARATORS)
CONTROL_TRANS = str.maketrans({c: None for c in CONTROL_CHARS})

FIELD_CAP_CHARS = 2000
TRUNC_MARKER = " ...[TRUNCATED]"

# Closes WP-SCP-022 R2 BYPASS-002: `id` is free-text per the
# SonnetReviewResult schema and reaches the Codex prompt, so it must be
# sanitized too. `severity` is a closed enum (CRIT / MAJ / MIN / nit) and
# is validated separately at consolidation time, so we don't need to
# sanitize it — a non-conforming severity fails consolidation outright.
SANITIZE_FIELDS = ("id", "claim", "evidence", "impact", "mitigation")


def sanitize_text(value: str) -> str:
    """Strip controls, escape backticks, length-cap, return safe string."""
    if not isinstance(value, str):
        return str(value)
    cleaned = value.translate(CONTROL_TRANS)
    cleaned = cleaned.replace("`", "\\`")
    if len(cleaned) > FIELD_CAP_CHARS:
        cleaned = cleaned[: FIELD_CAP_CHARS - len(TRUNC_MARKER)] + TRUNC_MARKER
    return cleaned


def sanitize_finding(finding: dict) -> dict:
    out = dict(finding)
    for field in SANITIZE_FIELDS:
        if field in out:
            out[field] = sanitize_text(out[field])
    return out


def sanitize_review_result(result: dict) -> dict:
    """Sanitize a top-level SonnetReviewResult.

    Handles the schema's top-level free-text fields (`summary`,
    `self_reported_concerns`) AND each finding inside `findings[]`.
    Closes R3 BYPASS-003: top-level `self_reported_concerns` array was
    previously not covered by the per-finding sanitizer.
    """
    out = dict(result)
    if "summary" in out and isinstance(out["summary"], str):
        out["summary"] = sanitize_text(out["summary"])
    if "self_reported_concerns" in out and isinstance(out["self_reported_concerns"], list):
        out["self_reported_concerns"] = [
            sanitize_text(c) if isinstance(c, str) else c
            for c in out["self_reported_concerns"]
        ]
    if "findings" in out and isinstance(out["findings"], list):
        out["findings"] = [
            sanitize_finding(f) if isinstance(f, dict) else f
            for f in out["findings"]
        ]
    return out


def _looks_like_review_result(d: dict) -> bool:
    """Heuristic: top-level review-result object has 'verdict' + 'findings'."""
    return "verdict" in d and ("findings" in d or "self_reported_concerns" in d)


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        sys.stderr.write("sanitize_review_finding: empty input\n")
        return 2
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"sanitize_review_finding: invalid JSON: {exc}\n")
        return 2

    if isinstance(parsed, list):
        cleaned = [sanitize_finding(f) for f in parsed]
    elif isinstance(parsed, dict):
        if _looks_like_review_result(parsed):
            cleaned = sanitize_review_result(parsed)
        else:
            cleaned = sanitize_finding(parsed)
    else:
        sys.stderr.write("sanitize_review_finding: input must be object or array\n")
        return 2

    json.dump(cleaned, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
