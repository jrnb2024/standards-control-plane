from __future__ import annotations

from standards_control_plane.audit import build_audit_result
from standards_control_plane.evaluators import evaluate_ux
from standards_control_plane.extractor import extract_scope
from standards_control_plane.normaliser import normalise_project_area


def _returns_area() -> dict[str, object]:
    return normalise_project_area(extract_scope(["fixtures/returns-pilot"]), subsystem="returns")


def _stable_workspace_area() -> dict[str, object]:
    return normalise_project_area(
        extract_scope(["fixtures/ux-stable-workspace"]),
        subsystem="returns",
    )


def test_ux_evaluator_returns_bounded_findings_for_seeded_returns_pilot() -> None:
    result = evaluate_ux(_returns_area(), standards_version="2026-04-11")
    assert [finding["rule_id"] for finding in result["findings"]] == [
        "UX-001",
        "UX-002",
        "UX-003",
    ]
    assert {finding["confidence_class"] for finding in result["findings"]} == {"medium"}
    assert result["score"] == 65


def test_ux_evaluator_returns_clean_score_for_stable_workspace_fixture() -> None:
    result = evaluate_ux(_stable_workspace_area(), standards_version="2026-04-11")
    assert result["findings"] == []
    assert result["recommended_actions"] == []
    assert result["score"] == 100


def test_audit_builder_evaluates_ux_domain() -> None:
    request = {
        "mode": "audit",
        "domains": ["ux"],
        "scope": {
            "paths": ["fixtures/returns-pilot"],
            "subsystem": "returns",
        },
        "standards_version": "2026-04-11",
    }
    result = build_audit_result(request)
    assert result["domain_status"] == {"ux": {"status": "evaluated"}}
    assert [finding["rule_id"] for finding in result["findings"]] == [
        "UX-001",
        "UX-002",
        "UX-003",
    ]
