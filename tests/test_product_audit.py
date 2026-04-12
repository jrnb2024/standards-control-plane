from __future__ import annotations

from standards_control_plane.audit import build_audit_result
from standards_control_plane.evaluators import evaluate_product
from standards_control_plane.extractor import extract_scope
from standards_control_plane.normaliser import normalise_project_area


def _product_drift_area() -> dict[str, object]:
    return normalise_project_area(
        extract_scope(["fixtures/product-drift-console"]),
        subsystem="ops",
    )


def _product_stable_area() -> dict[str, object]:
    return normalise_project_area(
        extract_scope(["fixtures/product-stable-review"]),
        subsystem="returns",
    )


def test_product_evaluator_returns_bounded_advisory_findings_for_drift_fixture() -> None:
    result = evaluate_product(_product_drift_area(), standards_version="2026-04-11")
    assert [finding["rule_id"] for finding in result["findings"]] == [
        "PROD-001",
        "PROD-002",
        "PROD-003",
    ]
    assert {finding["confidence_class"] for finding in result["findings"]} == {"low", "medium"}
    assert result["score"] == 65


def test_product_evaluator_returns_clean_score_for_stable_product_fixture() -> None:
    result = evaluate_product(_product_stable_area(), standards_version="2026-04-11")
    assert result["findings"] == []
    assert result["recommended_actions"] == []
    assert result["score"] == 100


def test_audit_builder_evaluates_product_domain() -> None:
    request = {
        "mode": "audit",
        "domains": ["product"],
        "scope": {
            "paths": ["fixtures/product-drift-console"],
            "subsystem": "ops",
        },
        "standards_version": "2026-04-11",
    }
    result = build_audit_result(request)
    assert result["domain_status"] == {"product": {"status": "evaluated"}}
    assert [finding["rule_id"] for finding in result["findings"]] == [
        "PROD-001",
        "PROD-002",
        "PROD-003",
    ]
