from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from standards_control_plane.audit import build_audit_result
from standards_control_plane.findings import (
    HISTORY_FINDINGS_FILENAME,
    OPEN_FINDINGS_FILENAME,
    load_findings_store,
    persist_audit_findings,
    reconcile_findings,
)
from standards_control_plane.resources import examples_dir, output_dir
from standards_control_plane.schema_tools import load_json_file, validate_with_schema


def _seed_legacy_findings(findings_dir: Path) -> None:
    findings_dir.mkdir(parents=True, exist_ok=True)
    (findings_dir / OPEN_FINDINGS_FILENAME).write_text(
        json.dumps(
            {
                "store_version": "0.1.0",
                "generated_at": "2026-04-11T00:00:00Z",
                "findings": [
                    {
                        "finding_id": "F-2026-00031",
                        "domain": "architecture",
                        "rule_id": "ARCH-002",
                        "severity": "high",
                        "status": "open",
                        "title": "UI layer contains workflow orchestration",
                        "summary": "The returns exceptions page already mixes workflow branching into the UI layer and should not absorb more orchestration.",
                        "evidence": [
                            {
                                "path": "fixtures/returns-pilot/frontend/app/exceptions/page.tsx",
                                "evidence_class": "direct_file",
                                "locator": "ExceptionsPage",
                            }
                        ],
                        "area_id": "returns-exceptions",
                        "suggested_remediation": [
                            "Move branching workflow into an action or service layer.",
                            "Keep the page focused on state binding and event dispatch.",
                        ],
                        "confidence": 0.89,
                        "confidence_class": "medium",
                        "detected_by": "architecture-evaluator",
                        "standards_version": "2026-04-11",
                        "created_at": "2026-04-11T16:10:00Z",
                        "updated_at": "2026-04-11T16:10:00Z",
                    },
                    {
                        "finding_id": "F-2026-00032",
                        "domain": "architecture",
                        "rule_id": "ARCH-003",
                        "severity": "medium",
                        "status": "open",
                        "title": "Returns filters use duplicated access logic",
                        "summary": "Adjacent returns workflow code already duplicates API access setup instead of using a shared integration seam.",
                        "evidence": [
                            {
                                "path": "fixtures/returns-pilot/frontend/app/shared/filters.ts",
                                "evidence_class": "direct_file",
                                "locator": "buildReturnsFilters",
                            }
                        ],
                        "area_id": "returns-dashboard",
                        "suggested_remediation": [
                            "Route remote access through the agreed abstraction for returns integrations."
                        ],
                        "confidence": 0.82,
                        "confidence_class": "medium",
                        "detected_by": "architecture-evaluator",
                        "standards_version": "2026-04-11",
                        "created_at": "2026-04-11T16:12:00Z",
                        "updated_at": "2026-04-11T16:12:00Z",
                    },
                    {
                        "finding_id": "F-2026-00033",
                        "domain": "governance",
                        "rule_id": "GOV-003",
                        "severity": "medium",
                        "status": "open",
                        "title": "Returns work package evidence is incomplete",
                        "summary": "Recent returns work has missing review evidence files, so new changes in the same area should preserve a clear evidence trail.",
                        "evidence": [
                            {
                                "path": "fixtures/returns-pilot/docs/reviews/WP-RET-014/review_findings.md",
                                "evidence_class": "structured_review"
                            }
                        ],
                        "area_id": "returns-exceptions",
                        "suggested_remediation": [
                            "Add explicit review findings and test evidence for each work package."
                        ],
                        "confidence": 0.78,
                        "confidence_class": "low",
                        "detected_by": "governance-evaluator",
                        "standards_version": "2026-04-11",
                        "created_at": "2026-04-11T16:15:00Z",
                        "updated_at": "2026-04-11T16:15:00Z",
                    },
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (findings_dir / HISTORY_FINDINGS_FILENAME).write_text(
        json.dumps(
            {
                "store_version": "0.1.0",
                "generated_at": "2026-04-11T00:00:00Z",
                "findings": [],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _build_example_audit_result() -> dict[str, object]:
    request = load_json_file(examples_dir() / "audit-request.json")
    return build_audit_result(request)


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


def _repo_findings_paths() -> tuple[Path, Path]:
    findings_dir = output_dir() / "findings"
    return findings_dir / OPEN_FINDINGS_FILENAME, findings_dir / HISTORY_FINDINGS_FILENAME


def test_persist_audit_findings_reconciles_scope_and_preserves_timestamps(tmp_path: Path) -> None:
    findings_dir = tmp_path / "findings"
    _seed_legacy_findings(findings_dir)
    audit_result = _build_example_audit_result()

    open_store, history_store = persist_audit_findings(audit_result, findings_dir=findings_dir)

    assert [finding.finding_id for finding in open_store.findings] == [
        "F-2026-00032",
        "F-ARCH-001-returns-exceptions",
        "F-ARCH-002-returns-exceptions",
        "F-ARCH-003-returns-exceptions",
    ]
    history_by_id = {finding.finding_id: finding for finding in history_store.findings}
    assert history_by_id["F-2026-00031"].status == "resolved"
    assert history_by_id["F-2026-00031"].created_at == "2026-04-11T16:10:00Z"
    assert history_by_id["F-2026-00031"].updated_at == str(audit_result["generated_at"])
    assert history_by_id["F-2026-00032"].status == "open"
    assert history_by_id["F-2026-00032"].updated_at == "2026-04-11T16:12:00Z"
    assert history_by_id["F-2026-00033"].status == "resolved"
    assert history_by_id["F-ARCH-001-returns-exceptions"].created_at == str(
        audit_result["generated_at"]
    )
    assert history_by_id["F-ARCH-001-returns-exceptions"].updated_at == str(
        audit_result["generated_at"]
    )

    validate_with_schema(open_store.to_dict(), "findings-store.schema.json")
    validate_with_schema(history_store.to_dict(), "findings-store.schema.json")


def test_persist_audit_findings_is_idempotent(tmp_path: Path) -> None:
    findings_dir = tmp_path / "findings"
    _seed_legacy_findings(findings_dir)
    audit_result = _build_example_audit_result()

    first_open, first_history = persist_audit_findings(audit_result, findings_dir=findings_dir)
    first_open_text = (findings_dir / OPEN_FINDINGS_FILENAME).read_text(encoding="utf-8")
    first_history_text = (findings_dir / HISTORY_FINDINGS_FILENAME).read_text(encoding="utf-8")

    second_open, second_history = persist_audit_findings(audit_result, findings_dir=findings_dir)

    assert second_open == first_open
    assert second_history == first_history
    assert (findings_dir / OPEN_FINDINGS_FILENAME).read_text(encoding="utf-8") == first_open_text
    assert (findings_dir / HISTORY_FINDINGS_FILENAME).read_text(encoding="utf-8") == first_history_text


def test_reconcile_findings_collapses_identical_duplicates_and_rejects_conflicts() -> None:
    audit_result = _build_example_audit_result()
    duplicate = copy.deepcopy(audit_result["findings"][0])
    audit_result["findings"].append(duplicate)

    open_store, history_store = reconcile_findings(audit_result)
    assert [finding.finding_id for finding in open_store.findings] == [
        "F-ARCH-001-returns-exceptions",
        "F-ARCH-002-returns-exceptions",
        "F-ARCH-003-returns-exceptions",
    ]
    assert open_store == history_store

    conflicting = _build_example_audit_result()
    duplicate_conflict = copy.deepcopy(conflicting["findings"][0])
    duplicate_conflict["area_id"] = "returns-dashboard"
    conflicting["findings"].append(duplicate_conflict)

    with pytest.raises(ValueError, match="duplicate payloads|scope pairs"):
        reconcile_findings(conflicting)


def test_audit_cli_is_read_only_without_write_flag() -> None:
    expected = _build_example_audit_result()
    open_path, history_path = _repo_findings_paths()
    before_open = open_path.read_text(encoding="utf-8")
    before_history = history_path.read_text(encoding="utf-8")

    response = _run_cli("audit", "--request", "examples/audit-request.json")

    assert response == expected
    assert open_path.read_text(encoding="utf-8") == before_open
    assert history_path.read_text(encoding="utf-8") == before_history


def test_audit_cli_write_output_persists_reconciled_stores() -> None:
    expected = _build_example_audit_result()
    open_path, history_path = _repo_findings_paths()
    original_open = open_path.read_text(encoding="utf-8")
    original_history = history_path.read_text(encoding="utf-8")
    try:
        _seed_legacy_findings(output_dir() / "findings")
        response = _run_cli(
            "audit",
            "--request",
            "examples/audit-request.json",
            "--write-output",
        )
        assert response == expected
        open_store = load_findings_store(open_path)
        history_store = load_findings_store(history_path)
        assert [finding.finding_id for finding in open_store.findings] == [
            "F-2026-00032",
            "F-ARCH-001-returns-exceptions",
            "F-ARCH-002-returns-exceptions",
            "F-ARCH-003-returns-exceptions",
        ]
        history_by_id = {finding.finding_id: finding for finding in history_store.findings}
        assert history_by_id["F-2026-00033"].status == "resolved"
    finally:
        open_path.write_text(original_open, encoding="utf-8")
        history_path.write_text(original_history, encoding="utf-8")


def test_findings_cli_returns_current_open_store() -> None:
    expected = load_findings_store(output_dir() / "findings" / OPEN_FINDINGS_FILENAME).to_dict()
    response = _run_cli("findings")
    assert response == expected
