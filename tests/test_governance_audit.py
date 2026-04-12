from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

from standards_control_plane.audit import build_audit_result
from standards_control_plane.evaluators import evaluate_governance
from standards_control_plane.extractor import extract_scope
from standards_control_plane.normaliser import normalise_project_area
from standards_control_plane.resources import examples_dir
from standards_control_plane.schema_tools import load_json_file, validate_with_schema


def _seeded_project_area() -> dict[str, object]:
    return normalise_project_area(extract_scope(["fixtures/returns-pilot"]), subsystem="returns")


def _run_cli(*args: str) -> dict[str, object]:
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "src")
    completed = subprocess.run(
        [sys.executable, "-m", "standards_control_plane.cli", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    payload = json.loads(completed.stdout)
    assert isinstance(payload, dict)
    return payload


def test_governance_evaluator_returns_clean_score_for_seeded_area() -> None:
    project_area = _seeded_project_area()
    first = evaluate_governance(project_area, standards_version="2026-04-11")
    second = evaluate_governance(project_area, standards_version="2026-04-11")
    assert first == second
    assert first["score"] == 100
    assert first["findings"] == []
    assert first["recommended_actions"] == []


def test_governance_evaluator_flags_missing_enhancement_spec() -> None:
    project_area = copy.deepcopy(_seeded_project_area())
    project_area["artefacts"]["enhancement_specs"] = []
    result = evaluate_governance(project_area, standards_version="2026-04-11")
    assert [finding["rule_id"] for finding in result["findings"]] == ["GOV-002"]
    assert result["score"] == 70


def test_governance_evaluator_flags_missing_review_evidence() -> None:
    project_area = copy.deepcopy(_seeded_project_area())
    project_area["artefacts"]["review_evidence"] = []
    result = evaluate_governance(project_area, standards_version="2026-04-11")
    assert [finding["rule_id"] for finding in result["findings"]] == ["GOV-003"]
    assert result["score"] == 85


def test_governance_evaluator_rejects_legacy_unstructured_review_evidence() -> None:
    project_area = copy.deepcopy(_seeded_project_area())
    project_area["artefacts"]["review_evidence"] = [
        "fixtures/review-evidence-legacy/docs/reviews/WP-LEG-001/review_findings.md"
    ]
    result = evaluate_governance(project_area, standards_version="2026-04-11")
    assert [finding["rule_id"] for finding in result["findings"]] == ["GOV-003"]
    assert result["score"] == 85


def test_governance_evaluator_flags_boundary_mismatch() -> None:
    project_area = copy.deepcopy(_seeded_project_area())
    project_area["area_id"] = "labeller-exceptions"
    result = evaluate_governance(project_area, standards_version="2026-04-11")
    assert [finding["rule_id"] for finding in result["findings"]] == ["GOV-001"]
    assert result["score"] == 70


def test_governance_evaluator_orders_multiple_findings_by_severity_then_rule() -> None:
    project_area = copy.deepcopy(_seeded_project_area())
    project_area["area_id"] = "labeller-dashboard"
    project_area["artefacts"]["enhancement_specs"] = []
    result = evaluate_governance(project_area, standards_version="2026-04-11")
    assert [finding["rule_id"] for finding in result["findings"]] == [
        "GOV-001",
        "GOV-002",
        "GOV-003",
    ]
    assert result["score"] == 25


def test_audit_builder_returns_live_governance_result_with_domain_status() -> None:
    request = load_json_file(examples_dir() / "audit-request.json")
    result = build_audit_result(request)
    validate_with_schema(result, "audit-result.schema.json")
    assert result["domain_status"] == {
        "governance": {"status": "evaluated"},
        "architecture": {"status": "evaluated"},
    }
    assert result["scores"] == {"architecture": 25, "governance": 100}
    assert result["waivers_applied"] == []


def test_audit_example_matches_live_builder_output() -> None:
    request = load_json_file(examples_dir() / "audit-request.json")
    expected = load_json_file(examples_dir() / "audit-result.json")
    assert build_audit_result(request) == expected


def test_audit_cli_returns_live_governance_result() -> None:
    expected = load_json_file(examples_dir() / "audit-result.json")
    response = _run_cli("audit", "--request", "examples/audit-request.json")
    assert response == expected


def test_audit_rejects_mismatched_scope_area_id() -> None:
    request = load_json_file(examples_dir() / "audit-request.json")
    request["scope"]["area_id"] = "labeller-exceptions"
    try:
        build_audit_result(request)
    except ValueError as error:
        assert "scope.area_id" in str(error)
    else:
        raise AssertionError("Expected mismatched scope.area_id to fail")
