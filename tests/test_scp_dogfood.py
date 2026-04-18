"""SCP dogfood — run SVC-001/002/003 against SCP's own service manifest.

This is the 019D slice of WP-SCP-019. If any of these assertions start
failing, either SCP's implementation has drifted from its declared
auth_contract, or the evaluator has acquired a new signal that the
declaration doesn't yet satisfy. In both cases, triage before ignoring.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

from standards_control_plane.audit import build_audit_result
from standards_control_plane.schema_tools import load_json_file, validate_with_schema


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    return subprocess.run(
        [sys.executable, "-m", "standards_control_plane.cli", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_scp_services_yml_exists_at_repo_root() -> None:
    assert (REPO_ROOT / "services.yml").exists(), (
        "SCP's services.yml must exist at repo root for the SVC-* rules to "
        "audit the real service (019D dogfood)"
    )


def test_scp_dogfood_audit_request_validates_against_schema() -> None:
    payload = load_json_file(REPO_ROOT / "examples" / "audit-request-scp-dogfood.json")
    validate_with_schema(payload, "audit-request.schema.json")
    assert payload["domains"] == ["service-lifecycle"]


def _scp_declared_close_date() -> date:
    """Read the authoritative close date from services.yml so the canary
    tracks the declaration rather than a hardcoded copy. If governance
    ever amends D-019's close date, the declaration updates here first."""
    manifest = yaml.safe_load((REPO_ROOT / "services.yml").read_text())
    for entry in manifest["services"]["scp"]["local"]["runtime_contract"][
        "auth_contract"
    ]["accepted_modes"]:
        if entry["mode"] == "mode.bearer_legacy":
            return date.fromisoformat(entry["deprecation_close_date"])
    raise RuntimeError("SCP services.yml has no mode.bearer_legacy entry")


def test_scp_dogfood_audit_is_clean_against_scoped_paths() -> None:
    request = load_json_file(REPO_ROOT / "examples" / "audit-request-scp-dogfood.json")
    result = build_audit_result(request)
    # Use a subset check so legitimate future additions to domain_status
    # shape (e.g. a rules_evaluated counter) don't break the assertion.
    assert result["domain_status"].get("service-lifecycle") == {"status": "evaluated"}
    assert result["scores"]["service-lifecycle"] == 100
    assert result["summary"]["high_severity_count"] == 0
    assert result["summary"]["medium_severity_count"] == 0
    assert result["summary"]["low_severity_count"] == 0
    assert result["findings"] == [], (
        "SCP dogfood must produce zero findings. Got: "
        + ", ".join(
            f"{f['finding_id']} ({f['title']})"
            for f in result["findings"]
        )
    )


def test_scp_dogfood_audit_is_clean_over_full_service_source_tree() -> None:
    # Broader scope includes the evaluator's own module; proves the
    # EVALUATOR_SELF_EXCLUSIONS list keeps the marker constants from
    # self-poisoning the impl-undeclared scan.
    request = {
        "mode": "audit",
        "domains": ["service-lifecycle"],
        "scope": {
            "paths": ["services.yml", "src/standards_control_plane/"],
            "subsystem": "platform",
            "area_id": "scp-service",
        },
        "standards_version": "2026-04-18",
    }
    result = build_audit_result(request)
    assert result["findings"] == [], (
        "SCP dogfood over the full service source tree must be clean. "
        "If impl-undeclared fires for mode.service_rs256 or mode.api_key, "
        "check that evaluators/service_lifecycle.py is still in "
        "EVALUATOR_SELF_EXCLUSIONS. Got: "
        + ", ".join(
            f"{f['finding_id']} ({f['title']})"
            for f in result["findings"]
        )
    )


def test_scp_dogfood_audit_fires_bearer_legacy_after_close_date() -> None:
    # Calendar canary: read the close_date from services.yml itself, run the
    # audit one day later, and assert the bearer-legacy-close-date-passed
    # finding fires. Coupling the test to the declared date means a
    # governance-approved extension (bumping D-019 and services.yml
    # together) keeps the canary coherent.
    close_date = _scp_declared_close_date()
    after_close = (close_date + timedelta(days=1)).isoformat()
    request = load_json_file(REPO_ROOT / "examples" / "audit-request-scp-dogfood.json")
    request["standards_version"] = after_close
    result = build_audit_result(request)
    svc003_findings = [
        f for f in result["findings"] if f["rule_id"] == "SVC-003"
    ]
    assert any(
        "bearer-legacy-close-date-passed" in f["finding_id"]
        for f in svc003_findings
    ), (
        f"After the declared close date ({close_date.isoformat()}), SCP's "
        "bearer_legacy declaration must fire the close-date-passed finding "
        "as a migration canary. Got: "
        + ", ".join(f["finding_id"] for f in svc003_findings)
    )


def test_scp_dogfood_via_cli_subprocess_is_clean() -> None:
    run = _run_cli(
        "audit", "--request", "examples/audit-request-scp-dogfood.json"
    )
    assert run.returncode == 0, run.stderr
    payload = json.loads(run.stdout)
    assert payload["findings"] == []
    assert payload["scores"]["service-lifecycle"] == 100


def _write_waiver(path: Path, waiver_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            [
                {
                    "waiver_id": waiver_id,
                    "finding_id": "F-SCP-BEARER-LEGACY",
                    "reason": "SCP bearer-legacy migration window",
                    "approved_by": "governance-owner",
                    "created_at": "2026-04-18T00:00:00Z",
                    "expires_at": "2026-06-30T23:59:59Z",
                }
            ]
        ),
        encoding="utf-8",
    )


def test_scp_waiver_ref_fires_when_an_unrelated_waiver_is_registered(
    tmp_path: Path,
    monkeypatch,
) -> None:
    # Negative half: registry contains a waiver that is NOT SCP's.
    _write_waiver(tmp_path / "findings" / "waivers.json", "unrelated-waiver")
    from standards_control_plane.evaluators import service_lifecycle as module

    monkeypatch.setattr(module, "output_dir", lambda: tmp_path)
    request = load_json_file(REPO_ROOT / "examples" / "audit-request-scp-dogfood.json")
    result = build_audit_result(request)
    assert any(
        f["rule_id"] == "SVC-003"
        and "bearer-legacy-waiver-not-found" in f["finding_id"]
        for f in result["findings"]
    )


def test_audit_accepts_requested_area_id_when_scope_is_uninferrable() -> None:
    # Direct coverage of the D-020 contract: a scope that has no ENH marker
    # and no /frontend/app/<route>/page.tsx pattern must still audit when
    # the request supplies area_id explicitly.
    request = {
        "mode": "audit",
        "domains": ["service-lifecycle"],
        "scope": {
            "paths": ["services.yml"],
            "subsystem": "platform",
            "area_id": "scp-manifest-only",
        },
        "standards_version": "2026-04-18",
    }
    result = build_audit_result(request)
    assert result["scope"]["area_id"] == "scp-manifest-only"
    assert result["domain_status"].get("service-lifecycle") == {"status": "evaluated"}


def test_audit_still_rejects_mismatch_when_inference_succeeds() -> None:
    # D-020 is the narrow uninferrable relaxation — the inferred-mismatch
    # guardrail is still load-bearing. A scope with an ENH spec cannot be
    # audited with a mismatched area_id claim.
    request = {
        "mode": "audit",
        "domains": ["service-lifecycle"],
        "scope": {
            "paths": ["fixtures/svc-unknown-mode"],
            "subsystem": "service-lifecycle",
            "area_id": "svc-claim-does-not-match",
        },
        "standards_version": "2026-04-18",
    }
    try:
        build_audit_result(request)
    except ValueError as exc:
        assert "scope.area_id" in str(exc)
    else:
        raise AssertionError(
            "build_audit_result must still reject mismatched area_id when "
            "inference succeeds"
        )


def test_scp_waiver_ref_clears_when_the_scp_migration_waiver_is_registered(
    tmp_path: Path,
    monkeypatch,
) -> None:
    # Positive half: registry contains SCP's actual migration waiver. The
    # waiver-not-found check must go silent; no other findings should
    # appear either (the audit stays clean end-to-end).
    _write_waiver(
        tmp_path / "findings" / "waivers.json", "scp-bearer-legacy-migration"
    )
    from standards_control_plane.evaluators import service_lifecycle as module

    monkeypatch.setattr(module, "output_dir", lambda: tmp_path)
    request = load_json_file(REPO_ROOT / "examples" / "audit-request-scp-dogfood.json")
    result = build_audit_result(request)
    assert result["findings"] == [], (
        "With the SCP migration waiver registered, the dogfood audit must "
        "stay clean. Got: "
        + ", ".join(f["finding_id"] for f in result["findings"])
    )
