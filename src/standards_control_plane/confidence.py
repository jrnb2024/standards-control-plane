"""Shared confidence and evidence taxonomy helpers."""

from __future__ import annotations

from typing import Final

HIGH_CONFIDENCE_MIN: Final[float] = 0.95
MEDIUM_CONFIDENCE_MIN: Final[float] = 0.80

CONFIDENCE_CLASSES: Final[tuple[str, ...]] = ("high", "medium", "low")
EVIDENCE_CLASSES: Final[tuple[str, ...]] = (
    "direct_file",
    "declared_metadata",
    "structured_review",
    "historical_review",
    "derived_heuristic",
)


def classify_confidence(confidence: float) -> str:
    if not 0 <= confidence <= 1:
        raise ValueError("confidence must be between 0 and 1")
    if confidence >= HIGH_CONFIDENCE_MIN:
        return "high"
    if confidence >= MEDIUM_CONFIDENCE_MIN:
        return "medium"
    return "low"
