from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from standards_control_plane.consult import build_consult_response
from standards_control_plane.findings import load_findings_store, select_consult_findings
from standards_control_plane.resources import examples_dir, output_dir
from standards_control_plane.schema_tools import load_json_file, validate_with_schema
from standards_control_plane.registry import load_registry


def test_load_registry_returns_structured_rules_and_patterns() -> None:
    registry = load_registry()
    assert registry.name == "standards-control-plane"
    assert set(registry.domains) == {"architecture", "design", "governance", "ux"}
    assert len(registry.domains["governance"].rules) == 3
    assert len(registry.domains["architecture"].patterns) == 2
    assert len(registry.domains["ux"].rules) == 3
    assert len(registry.domains["ux"].patterns) == 2
    assert len(registry.domains["design"].rules) == 3
    assert len(registry.domains["design"].patterns) == 2


def test_broken_registry_reference_fails_explicitly(tmp_path: Path) -> None:
    root = tmp_path / "standards"
    architecture = root / "architecture"
    architecture.mkdir(parents=True)
    (root / "standards-index.json").write_text(
        json.dumps(
            {
                "name": "test-registry",
                "version": "0.0.1",
                "status": "draft",
                "domains": {"architecture": "architecture/index.json"},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (architecture / "index.json").write_text(
        json.dumps(
            {
                "domain": "architecture",
                "version": "1.0.0",
                "status": "active",
                "rules": [
                    {
                        "rule_id": "ARCH-999",
                        "domain": "architecture",
                        "title": "Broken reference",
                        "summary": "This points at a missing file.",
                        "path": "rules/missing.md",
                        "severity_default": "high",
                        "scope": ["frontend"],
                        "signals": ["missing target file"],
                        "exceptions": [],
                        "related_patterns": [],
                        "version": "1.0.0",
                        "status": "active",
                    }
                ],
                "patterns": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError, match="rules/missing.md"):
        load_registry(root / "standards-index.json")


def test_registry_reference_cannot_escape_boundary(tmp_path: Path) -> None:
    root = tmp_path / "standards"
    architecture = root / "architecture"
    architecture.mkdir(parents=True)
    outside = tmp_path / "outside.md"
    outside.write_text("# outside\n", encoding="utf-8")
    (root / "standards-index.json").write_text(
        json.dumps(
            {
                "name": "test-registry",
                "version": "0.0.1",
                "status": "draft",
                "domains": {"architecture": "architecture/index.json"},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (architecture / "index.json").write_text(
        json.dumps(
            {
                "domain": "architecture",
                "version": "1.0.0",
                "status": "active",
                "rules": [
                    {
                        "rule_id": "ARCH-999",
                        "domain": "architecture",
                        "title": "Boundary escape",
                        "summary": "This tries to escape the registry boundary.",
                        "path": "../../outside.md",
                        "severity_default": "high",
                        "scope": ["frontend"],
                        "signals": ["registry escape"],
                        "exceptions": [],
                        "related_patterns": [],
                        "version": "1.0.0",
                        "status": "active",
                    }
                ],
                "patterns": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="escapes boundary"):
        load_registry(root / "standards-index.json")


def test_findings_store_validates_and_supports_domain_first_matching() -> None:
    store = load_findings_store(output_dir() / "findings" / "open-findings.json")
    selected = select_consult_findings(
        store,
        requested_domains=["architecture", "governance"],
        area_id="returns-exceptions",
        request_paths=["fixtures/returns-pilot/frontend/app/exceptions/page.tsx"],
    )
    assert [finding.finding_id for finding in selected] == [
        "F-ARCH-001-returns-exceptions",
        "F-ARCH-002-returns-exceptions",
        "F-ARCH-003-returns-exceptions",
        "F-2026-00032",
    ]


def test_area_specific_findings_can_surface_outside_requested_domains() -> None:
    store = load_findings_store(output_dir() / "findings" / "open-findings.json")
    selected = select_consult_findings(
        store,
        requested_domains=["architecture"],
        area_id="returns-exceptions",
        request_paths=["fixtures/returns-pilot/frontend/app/exceptions/page.tsx"],
    )
    assert [finding.finding_id for finding in selected] == [
        "F-ARCH-001-returns-exceptions",
        "F-ARCH-002-returns-exceptions",
        "F-ARCH-003-returns-exceptions",
        "F-2026-00032",
    ]


def test_consult_response_is_schema_valid_and_deterministic() -> None:
    request = load_json_file(examples_dir() / "consult-request.json")
    first = build_consult_response(request)
    second = build_consult_response(request)
    validate_with_schema(first, "consult-response.schema.json")
    assert first == second
    assert first["applicable_rules"]
    assert first["approved_patterns"]
    assert first["open_findings"]
    assert [review["review_id"] for review in first["historical_reviews"][:3]] == [
        "WP-RET-014",
        "WP-SCP-004",
        "WP-OVR-001",
    ]
    assert first["guidance"]
    assert (
        "Use when UI actions trigger meaningful business workflow"
        in first["guidance"][1]
    )


def test_consult_response_returns_empty_historical_reviews_when_no_match_exists() -> None:
    request = {
        "mode": "consult",
        "question": "How should I inspect the signals API drift page?",
        "domains": ["architecture"],
        "area_id": "signals-api-drift",
        "paths": ["fixtures/architecture-api-drift/frontend/app/orders/page.tsx"],
        "task_context": {
            "feature_summary": "Review the signals API drift route.",
            "subsystem": "signals",
        },
    }
    response = build_consult_response(request)
    assert response["historical_reviews"] == []


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


def test_consult_cli_returns_live_registry_data() -> None:
    response = _run_cli("consult", "--request", "examples/consult-request.json")
    assert response["applicable_rules"]
    assert response["guidance"]
    assert response["approved_patterns"]


def test_show_registry_cli_returns_loaded_registry() -> None:
    response = _run_cli("show-registry")
    domains = response["domains"]
    assert isinstance(domains, dict)
    assert "governance" in domains
    assert "architecture" in domains
    assert "ux" in domains
    assert "design" in domains
