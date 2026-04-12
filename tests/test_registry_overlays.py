from __future__ import annotations

import json
from pathlib import Path

from standards_control_plane.audit import build_audit_result
from standards_control_plane.consult import build_consult_response
from standards_control_plane.registry import load_registry
from standards_control_plane.resources import examples_dir
from standards_control_plane.schema_tools import load_json_file


def _write_overlay(root: Path) -> Path:
    architecture = root / "architecture"
    rules_dir = architecture / "rules"
    patterns_dir = architecture / "patterns"
    rules_dir.mkdir(parents=True)
    patterns_dir.mkdir(parents=True)

    (root / "standards-index.json").write_text(
        json.dumps(
            {
                "name": "overlay-registry",
                "version": "2026-04-12",
                "status": "draft",
                "domains": {"architecture": "architecture/index.json"},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (rules_dir / "ARCH-001-overlay.md").write_text("# ARCH-001 overlay\n", encoding="utf-8")
    (patterns_dir / "overlay-action-service-pattern.md").write_text(
        "# overlay pattern\n",
        encoding="utf-8",
    )
    (architecture / "index.json").write_text(
        json.dumps(
            {
                "domain": "architecture",
                "version": "2026-04-12",
                "status": "active",
                "rules": [
                    {
                        "rule_id": "ARCH-001",
                        "domain": "architecture",
                        "title": "Overlay boundary severity",
                        "summary": "Overlay raises boundary leaks to critical severity.",
                        "path": "rules/ARCH-001-overlay.md",
                        "severity_default": "critical",
                        "scope": ["frontend", "backend"],
                        "signals": ["cross-boundary import marker"],
                        "exceptions": [],
                        "related_patterns": ["overlay-action-service-pattern"],
                        "version": "2026-04-12",
                        "status": "active",
                    }
                ],
                "patterns": [
                    {
                        "pattern_id": "overlay-action-service-pattern",
                        "domain": "architecture",
                        "title": "Overlay action service pattern",
                        "summary": (
                            "Use the overlay action service for cross-boundary "
                            "orchestration."
                        ),
                        "path": "patterns/overlay-action-service-pattern.md",
                        "tags": ["returns", "triage"],
                        "version": "2026-04-12",
                        "status": "active",
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return root


def test_load_registry_merges_overlay_rules_and_patterns(tmp_path: Path) -> None:
    overlay_root = _write_overlay(tmp_path / "overlay")
    registry = load_registry(overlay_paths=[overlay_root])

    architecture_rules = {
        rule.rule_id: rule for rule in registry.active_rules_for(["architecture"])
    }
    architecture_patterns = {
        pattern.pattern_id: pattern for pattern in registry.active_patterns_for(["architecture"])
    }

    assert architecture_rules["ARCH-001"].severity_default == "critical"
    assert "overlay-action-service-pattern" in architecture_patterns


def test_consult_and_audit_honour_overlay_registry(tmp_path: Path) -> None:
    overlay_root = _write_overlay(tmp_path / "overlay")
    registry_snapshot = load_registry(overlay_paths=[overlay_root])

    consult_request = load_json_file(examples_dir() / "consult-request.json")
    consult_response = build_consult_response(
        consult_request,
        registry_snapshot=registry_snapshot,
    )
    assert any(
        item["pattern_id"] == "overlay-action-service-pattern"
        for item in consult_response["approved_patterns"]
    )

    audit_request = load_json_file(examples_dir() / "audit-request.json")
    audit_result = build_audit_result(
        audit_request,
        registry_snapshot=registry_snapshot,
    )
    severity_by_id = {
        finding["finding_id"]: finding["severity"] for finding in audit_result["findings"]
    }
    assert severity_by_id["F-ARCH-001-returns-exceptions"] == "critical"
