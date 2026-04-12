from __future__ import annotations

from standards_control_plane.audit import build_audit_result
from standards_control_plane.evaluators import evaluate_design
from standards_control_plane.extractor import extract_scope
from standards_control_plane.normaliser import normalise_project_area


def _design_drift_area() -> dict[str, object]:
    return normalise_project_area(
        extract_scope(["fixtures/design-drift-dashboard"]),
        subsystem="returns",
    )


def _design_stable_area() -> dict[str, object]:
    return normalise_project_area(
        extract_scope(["fixtures/design-stable-screen"]),
        subsystem="returns",
    )


def test_design_evaluator_returns_bounded_findings_for_design_drift_fixture() -> None:
    result = evaluate_design(_design_drift_area(), standards_version="2026-04-11")
    assert [finding["rule_id"] for finding in result["findings"]] == [
        "DS-001",
        "DS-002",
        "DS-003",
    ]
    assert result["score"] == 65


def test_design_evaluator_returns_clean_score_for_stable_design_fixture() -> None:
    result = evaluate_design(_design_stable_area(), standards_version="2026-04-11")
    assert result["findings"] == []
    assert result["recommended_actions"] == []
    assert result["score"] == 100


def test_audit_builder_evaluates_design_domain() -> None:
    request = {
        "mode": "audit",
        "domains": ["design"],
        "scope": {
            "paths": ["fixtures/design-drift-dashboard"],
            "subsystem": "returns",
        },
        "standards_version": "2026-04-11",
    }
    result = build_audit_result(request)
    assert result["domain_status"] == {"design": {"status": "evaluated"}}
    assert [finding["rule_id"] for finding in result["findings"]] == [
        "DS-001",
        "DS-002",
        "DS-003",
    ]
