"""CLI-level integration tests for the service-lifecycle domain (019C)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from standards_control_plane.audit import build_audit_result
from standards_control_plane.changed_audit import build_changed_file_audit_result
from standards_control_plane.ci_outputs import load_ci_output
from standards_control_plane.consult import build_consult_response
from standards_control_plane.control_tower import load_estate_dashboard
from standards_control_plane.registry import load_registry
from standards_control_plane.resources import examples_dir, output_dir
from standards_control_plane.schema_tools import load_json_file, validate_with_schema


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    root = Path(__file__).resolve().parents[1]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root / "src")
    return subprocess.run(
        [sys.executable, "-m", "standards_control_plane.cli", *args],
        cwd=root,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


# ---------------------------------------------------------------------------
# CLI examples and conformant end-to-end
# ---------------------------------------------------------------------------


def test_example_audit_request_for_service_lifecycle_validates_against_schema() -> None:
    payload = load_json_file(examples_dir() / "audit-request-service-lifecycle.json")
    validate_with_schema(payload, "audit-request.schema.json")
    assert payload["domains"] == ["service-lifecycle"]


def test_example_consult_request_for_service_lifecycle_validates_against_schema() -> None:
    payload = load_json_file(examples_dir() / "consult-request-service-lifecycle.json")
    validate_with_schema(payload, "consult-request.schema.json")
    assert payload["domains"] == ["service-lifecycle"]


def test_show_registry_cli_surfaces_service_lifecycle_rules() -> None:
    result = _run_cli("show-registry")
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert "service-lifecycle" in payload["domains"]
    svc_domain = payload["domains"]["service-lifecycle"]
    rule_ids = {rule["rule_id"] for rule in svc_domain["rules"]}
    assert {"SVC-001", "SVC-002", "SVC-003"}.issubset(rule_ids)


def test_audit_cli_accepts_service_lifecycle_domain_on_conformant_fixture() -> None:
    result = _run_cli(
        "audit", "--request", "examples/audit-request-service-lifecycle.json"
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["domain_status"] == {"service-lifecycle": {"status": "evaluated"}}
    assert payload["findings"] == []
    assert payload["scores"]["service-lifecycle"] == 100


# ---------------------------------------------------------------------------
# --write-output flow end-to-end (subprocess) — proves the audit-writer stack
# (findings persistence, report writer, CI writer, Control Tower writer)
# does not choke on a service-lifecycle-only audit result.
# ---------------------------------------------------------------------------


def _preserve(path: Path) -> str | None:
    return path.read_text(encoding="utf-8") if path.exists() else None


def _restore(path: Path, original: str | None) -> None:
    if original is None:
        path.unlink(missing_ok=True)
        return
    path.write_text(original, encoding="utf-8")


def test_audit_write_output_flow_for_service_lifecycle_emits_all_artifacts(
    tmp_path: Path,
) -> None:
    request_path = tmp_path / "svc-request.json"
    request_path.write_text(
        json.dumps(
            {
                "mode": "audit",
                "domains": ["service-lifecycle"],
                "scope": {
                    "paths": ["fixtures/svc-unknown-mode"],
                    "subsystem": "service-lifecycle",
                    "area_id": "svc-custom",
                },
                "standards_version": "2026-04-18",
            }
        ),
        encoding="utf-8",
    )

    ci_json = output_dir() / "ci" / "latest-ci.json"
    ci_md = output_dir() / "ci" / "latest-ci.md"
    report_md = output_dir() / "reports" / "latest-review.md"
    ct_dashboard = output_dir() / "control-tower" / "estate-dashboard.json"
    ct_surface = output_dir() / "control-tower" / "surface.json"
    open_findings = output_dir() / "findings" / "open-findings.json"
    history = output_dir() / "findings" / "findings-history.json"
    fp_summary = output_dir() / "findings" / "false-positive-summary.json"

    snapshots = {
        path: _preserve(path)
        for path in (ci_json, ci_md, report_md, ct_dashboard, ct_surface, open_findings, history, fp_summary)
    }

    try:
        run = _run_cli("audit", "--request", str(request_path), "--write-output")
        assert run.returncode == 0, run.stderr

        assert ci_json.exists()
        assert ci_md.exists()
        assert report_md.exists()
        assert ct_dashboard.exists()
        assert ct_surface.exists()

        ci_output = load_ci_output(ci_json)
        assert "service-lifecycle" in ci_output["domain_status"]
        assert ci_output["scores"]["service-lifecycle"] < 100
        assert any(
            "SVC-003" in warning["finding_id"]
            for warning in ci_output.get("warnings", [])
        )

        dashboard = load_estate_dashboard(ct_dashboard)
        svc_entries = [
            entry
            for entry in dashboard["subsystems"]
            if entry["subsystem"] == "service-lifecycle"
        ]
        assert svc_entries, "service-lifecycle subsystem should be in the estate dashboard"
        svc_subsystem = svc_entries[0]
        assert "service-lifecycle" in svc_subsystem["domains_evaluated"]
        assert "service-lifecycle" in svc_subsystem["scores"]

        assert "SVC-003" in report_md.read_text(encoding="utf-8")

        # Read-back CLI subcommands must also render the service-lifecycle
        # artifacts now that they're on disk. Run them inside the same
        # snapshot window to avoid an extra audit round-trip.
        findings_run = _run_cli("findings")
        assert findings_run.returncode == 0, findings_run.stderr
        findings_payload = json.loads(findings_run.stdout)
        assert any(
            str(finding.get("rule_id")) == "SVC-003"
            for finding in findings_payload.get("findings", [])
        )

        report_run = _run_cli("report")
        assert report_run.returncode == 0, report_run.stderr
        assert "SVC-003" in report_run.stdout

        ci_json_run = _run_cli("ci", "--format", "json")
        assert ci_json_run.returncode == 0, ci_json_run.stderr
        ci_payload = json.loads(ci_json_run.stdout)
        assert ci_payload["scores"]["service-lifecycle"] < 100

        ci_md_run = _run_cli("ci")
        assert ci_md_run.returncode == 0, ci_md_run.stderr
        assert "service-lifecycle" in ci_md_run.stdout

        ct_dashboard_run = _run_cli("control-tower")
        assert ct_dashboard_run.returncode == 0, ct_dashboard_run.stderr
        ct_dashboard_payload = json.loads(ct_dashboard_run.stdout)
        assert any(
            entry["subsystem"] == "service-lifecycle"
            for entry in ct_dashboard_payload["subsystems"]
        )

        ct_surface_run = _run_cli("control-tower", "--format", "surface")
        assert ct_surface_run.returncode == 0, ct_surface_run.stderr
    finally:
        for path, original in snapshots.items():
            _restore(path, original)
        # The audit writes a new per-subsystem record keyed by the subsystem
        # name (service-lifecycle), plus a per-subsystem report with the same
        # key. Neither is a pre-existing repo artifact, so remove both
        # unconditionally to keep the working tree clean.
        for path in (
            output_dir() / "findings" / "area-summaries" / "service-lifecycle.json",
            output_dir() / "control-tower" / "subsystems" / "service-lifecycle.json",
            output_dir() / "reports" / "subsystems" / "service-lifecycle-review.md",
        ):
            path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Changed-file audit routing (direct call — no git churn required)
# ---------------------------------------------------------------------------


def test_changed_file_audit_routes_service_lifecycle_domain_via_explicit_paths() -> None:
    result = build_changed_file_audit_result(
        base_ref="HEAD~1",
        head_ref="HEAD",
        domains=["service-lifecycle"],
        subsystem="service-lifecycle",
        standards_version="2026-04-18",
        area_id="svc-overdue",
        changed_paths=[
            "fixtures/svc-bearer-legacy-past-close-date/services.yml",
            "fixtures/svc-bearer-legacy-past-close-date/docs/enhancements/ENH-920-svc-overdue.md",
        ],
    )
    audit = result["audit_result"]
    assert audit["domain_status"] == {"service-lifecycle": {"status": "evaluated"}}
    assert any(
        "bearer-legacy-close-date-passed" in str(finding["finding_id"])
        for finding in audit["findings"]
    )


# ---------------------------------------------------------------------------
# Consult routing for service-lifecycle
# ---------------------------------------------------------------------------


def test_consult_returns_service_lifecycle_rules_when_domain_requested() -> None:
    request = {
        "mode": "consult",
        "question": (
            "Stand up a shared service that accepts Control Tower OIDC for "
            "browsers and an API key for machine callers."
        ),
        "domains": ["service-lifecycle"],
        "area_id": "svc-platform",
        "paths": ["fixtures/svc-conformant-all-modes"],
    }
    response = build_consult_response(request)
    rule_ids = {rule["rule_id"] for rule in response["applicable_rules"]}
    assert {"SVC-001", "SVC-002", "SVC-003"}.issubset(rule_ids)
    assert response["domains"] == ["service-lifecycle"]


# ---------------------------------------------------------------------------
# Overlay extension of the service-lifecycle domain
# ---------------------------------------------------------------------------


def _write_service_lifecycle_overlay(root: Path) -> Path:
    overlay_root = root / "overlay"
    overlay_root.mkdir(parents=True, exist_ok=True)
    (overlay_root / "standards-index.json").write_text(
        json.dumps(
            {
                "name": "overlay-registry",
                "version": "2026-04-18-overlay",
                "status": "draft",
                "domains": {
                    "service-lifecycle": "service-lifecycle/index.json",
                },
            }
        ),
        encoding="utf-8",
    )
    domain_dir = overlay_root / "service-lifecycle"
    rules_dir = domain_dir / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    (rules_dir / "SVC-003-overlay.md").write_text(
        "# SVC-003 overlay — raises severity to critical\n", encoding="utf-8"
    )
    (domain_dir / "index.json").write_text(
        json.dumps(
            {
                "domain": "service-lifecycle",
                "version": "1.0.1",
                "status": "active",
                "rules": [
                    {
                        "rule_id": "SVC-003",
                        "domain": "service-lifecycle",
                        "title": "Service Must Declare Auth Contract (overlay)",
                        "summary": (
                            "Overlay replacing SVC-003 with critical severity "
                            "for this repo."
                        ),
                        "path": "rules/SVC-003-overlay.md",
                        "severity_default": "critical",
                        "scope": ["all"],
                        "signals": ["overlay-placeholder"],
                        "exceptions": [],
                        "related_patterns": [],
                        "version": "1.0.1",
                        "status": "active",
                    }
                ],
                "patterns": [],
            }
        ),
        encoding="utf-8",
    )
    return overlay_root


def test_overlay_can_replace_svc003_and_raise_severity(tmp_path: Path) -> None:
    overlay_root = _write_service_lifecycle_overlay(tmp_path)
    registry = load_registry(overlay_paths=[overlay_root])
    rules = {rule.rule_id: rule for rule in registry.active_rules_for(["service-lifecycle"])}
    # Base SVC-001 and SVC-002 must survive the overlay (overlay only replaces
    # SVC-003 by id); the overlay must have raised SVC-003's severity.
    assert {"SVC-001", "SVC-002", "SVC-003"}.issubset(rules.keys())
    assert rules["SVC-001"].severity_default == "high"
    assert rules["SVC-002"].severity_default == "high"
    assert rules["SVC-003"].severity_default == "critical"
    assert rules["SVC-003"].title.endswith("(overlay)")


def test_audit_with_overlay_propagates_overlay_severity_to_findings(
    tmp_path: Path,
) -> None:
    overlay_root = _write_service_lifecycle_overlay(tmp_path)
    registry = load_registry(overlay_paths=[overlay_root])
    request = {
        "mode": "audit",
        "domains": ["service-lifecycle"],
        "scope": {
            "paths": ["fixtures/svc-unknown-mode"],
            "subsystem": "service-lifecycle",
            "area_id": "svc-custom",
        },
        "standards_version": "2026-04-18",
    }
    result = build_audit_result(request, registry_snapshot=registry)
    svc003_findings = [
        finding for finding in result["findings"] if finding["rule_id"] == "SVC-003"
    ]
    assert svc003_findings, "expected at least one SVC-003 finding from overlay"
    assert all(finding["severity"] == "critical" for finding in svc003_findings)


# ---------------------------------------------------------------------------
# Mixed-domain audit: service-lifecycle alongside other domains
# ---------------------------------------------------------------------------


def test_mixed_domain_audit_evaluates_service_lifecycle_and_governance_together() -> None:
    request = {
        "mode": "audit",
        "domains": ["governance", "service-lifecycle"],
        "scope": {
            "paths": ["fixtures/svc-unknown-mode"],
            "subsystem": "service-lifecycle",
            "area_id": "svc-custom",
        },
        "standards_version": "2026-04-18",
    }
    result = build_audit_result(request)
    assert result["domain_status"] == {
        "governance": {"status": "evaluated"},
        "service-lifecycle": {"status": "evaluated"},
    }
    domains_in_findings = {str(finding["domain"]) for finding in result["findings"]}
    # Both domains must emit findings against this fixture. Governance
    # reports the missing review-evidence (GOV-003) and service-lifecycle
    # the unknown mode (SVC-003).
    assert "governance" in domains_in_findings
    assert "service-lifecycle" in domains_in_findings
    rule_ids = {str(finding["rule_id"]) for finding in result["findings"]}
    assert "GOV-003" in rule_ids
    assert "SVC-003" in rule_ids
    # Findings must be stable-sorted across domains on repeated runs.
    second = build_audit_result(request)["findings"]
    assert result["findings"] == second
    # Audit sort key is (severity, finding_id). All high-severity findings
    # across both domains must therefore appear in ascending finding_id
    # order, which pins governance before service-lifecycle alphabetically.
    high_severity_ids = [
        str(finding["finding_id"])
        for finding in result["findings"]
        if finding["severity"] == "high"
    ]
    assert high_severity_ids == sorted(high_severity_ids)
