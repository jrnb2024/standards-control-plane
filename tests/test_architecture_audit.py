from __future__ import annotations

import copy

from standards_control_plane.audit import build_audit_result
from standards_control_plane.evaluators import evaluate_architecture
from standards_control_plane.extractor import extract_scope
from standards_control_plane.normaliser import normalise_project_area


def _returns_area() -> dict[str, object]:
    return normalise_project_area(extract_scope(["fixtures/returns-pilot"]), subsystem="returns")


def _api_drift_area() -> dict[str, object]:
    return normalise_project_area(extract_scope(["fixtures/architecture-api-drift"]), subsystem="signals")


def _async_drift_area() -> dict[str, object]:
    return normalise_project_area(extract_scope(["fixtures/architecture-async-drift"]), subsystem="signals")


def test_architecture_evaluator_returns_seeded_returns_findings() -> None:
    project_area = _returns_area()
    first = evaluate_architecture(project_area, standards_version="2026-04-11")
    second = evaluate_architecture(project_area, standards_version="2026-04-11")
    assert first == second
    assert [finding["rule_id"] for finding in first["findings"]] == [
        "ARCH-001",
        "ARCH-002",
        "ARCH-003",
    ]
    assert first["score"] == 25


def test_architecture_evaluator_flags_arch_003_from_repo_backed_fixture() -> None:
    project_area = _api_drift_area()
    result = evaluate_architecture(project_area, standards_version="2026-04-11")
    assert [finding["rule_id"] for finding in result["findings"]] == ["ARCH-003"]
    assert result["score"] == 85


def test_architecture_evaluator_flags_arch_004_from_repo_backed_fixture() -> None:
    project_area = _async_drift_area()
    result = evaluate_architecture(project_area, standards_version="2026-04-11")
    assert [finding["rule_id"] for finding in result["findings"]] == ["ARCH-004"]
    assert result["score"] == 85


def test_architecture_evaluator_preserves_findings_order() -> None:
    project_area = copy.deepcopy(_returns_area())
    result = evaluate_architecture(project_area, standards_version="2026-04-11")
    assert [finding["finding_id"] for finding in result["findings"]] == [
        "F-ARCH-001-returns-exceptions",
        "F-ARCH-002-returns-exceptions",
        "F-ARCH-003-returns-exceptions",
    ]


def test_audit_builder_preserves_merged_findings_order_and_unsupported_domains() -> None:
    request = {
        "mode": "audit",
        "domains": ["governance", "architecture", "ux"],
        "scope": {
            "paths": ["fixtures/architecture-api-drift"],
            "subsystem": "signals",
        },
        "standards_version": "2026-04-11",
    }
    result = build_audit_result(request)
    assert result["domain_status"] == {
        "governance": {"status": "evaluated"},
        "architecture": {"status": "evaluated"},
        "ux": {
            "status": "not_evaluated",
            "reason": "Ux evaluator is not implemented in this phase.",
        },
    }
    assert [finding["rule_id"] for finding in result["findings"]] == [
        "ARCH-003",
        "GOV-003",
    ]
