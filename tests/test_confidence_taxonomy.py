from __future__ import annotations

import pytest

from standards_control_plane.confidence import classify_confidence
from standards_control_plane.consult import build_consult_response
from standards_control_plane.resources import examples_dir
from standards_control_plane.schema_tools import load_json_file


def test_classify_confidence_uses_documented_thresholds() -> None:
    assert classify_confidence(0.99) == "high"
    assert classify_confidence(0.95) == "high"
    assert classify_confidence(0.94) == "medium"
    assert classify_confidence(0.80) == "medium"
    assert classify_confidence(0.79) == "low"
    assert classify_confidence(0.0) == "low"


def test_classify_confidence_rejects_out_of_range_values() -> None:
    with pytest.raises(ValueError, match="between 0 and 1"):
        classify_confidence(1.1)


def test_consult_response_surfaces_confidence_classes() -> None:
    request = load_json_file(examples_dir() / "consult-request.json")
    response = build_consult_response(request)
    assert response["confidence_class"] == "high"
    assert response["open_findings"]
    assert {finding["confidence_class"] for finding in response["open_findings"]} == {
        "high",
        "medium",
    }
