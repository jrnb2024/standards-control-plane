from __future__ import annotations

from typing import Any

from standards_control_plane.audit import build_audit_result
from standards_control_plane.evaluators import evaluate_service_lifecycle
from standards_control_plane.extractor import extract_scope
from standards_control_plane.normaliser import normalise_project_area


def _area(scope_path: str, *, area_hint: str, subsystem: str = "service-lifecycle") -> dict[str, Any]:
    extracted = extract_scope([scope_path])
    return normalise_project_area(extracted, subsystem=subsystem, area_hint=area_hint)


def _signals(findings: list[dict[str, Any]]) -> list[tuple[str, str]]:
    signals: list[tuple[str, str]] = []
    for finding in findings:
        finding_id = str(finding["finding_id"])
        rule_id = str(finding["rule_id"])
        # Signal key is the suffix after the area_id segment, following the
        # F-<RULE>-<area>-<service>-<signal> convention.
        prefix = f"F-{rule_id}-"
        if finding_id.startswith(prefix):
            remainder = finding_id[len(prefix):]
        else:
            remainder = finding_id
        signals.append((rule_id, remainder))
    return signals


def test_conformant_fixture_produces_no_findings() -> None:
    project_area = _area("fixtures/svc-conformant", area_hint="svc-widget")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    assert result["findings"] == []
    assert result["score"] == 100


def test_missing_runtime_contract_fires_svc001_only() -> None:
    project_area = _area("fixtures/svc-missing-runtime-contract", area_hint="svc-broken")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-001"]
    assert "missing-runtime-contract" in result["findings"][0]["finding_id"]


def test_incomplete_runtime_contract_fires_svc001_and_svc003_missing_auth() -> None:
    project_area = _area("fixtures/svc-incomplete-runtime-contract", area_hint="svc-halfbaked")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = sorted({finding["rule_id"] for finding in result["findings"]})
    assert rule_ids == ["SVC-001", "SVC-003"]
    assert any("missing-required-fields" in f["finding_id"] for f in result["findings"])
    assert any("missing-auth-contract" in f["finding_id"] for f in result["findings"])


def test_python_venv_missing_venv_path_fires_svc001() -> None:
    project_area = _area(
        "fixtures/svc-python-venv-missing-venv-path", area_hint="svc-venv"
    )
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-001"]
    assert "python-venv-missing-venv-path" in result["findings"][0]["finding_id"]


def test_missing_health_handler_fires_svc002() -> None:
    project_area = _area("fixtures/svc-missing-health-handler", area_hint="svc-ghost")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-002"]
    assert "missing-health-handler" in result["findings"][0]["finding_id"]


def test_missing_auth_contract_fires_svc003() -> None:
    project_area = _area("fixtures/svc-missing-auth-contract", area_hint="svc-no-auth")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "missing-auth-contract" in result["findings"][0]["finding_id"]


def test_empty_accepted_modes_fires_svc003() -> None:
    project_area = _area("fixtures/svc-empty-accepted-modes", area_hint="svc-empty-modes")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "empty-accepted-modes" in result["findings"][0]["finding_id"]


def test_unknown_mode_fires_svc003() -> None:
    project_area = _area("fixtures/svc-unknown-mode", area_hint="svc-custom")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "unknown-mode-0" in result["findings"][0]["finding_id"]


def test_oidc_missing_audience_fires_svc003_metadata() -> None:
    project_area = _area("fixtures/svc-oidc-missing-audience", area_hint="svc-half-oidc")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "missing-metadata-user_oidc-0" in result["findings"][0]["finding_id"]


def test_bearer_legacy_missing_waiver_fires_svc003_metadata() -> None:
    project_area = _area(
        "fixtures/svc-bearer-legacy-missing-waiver", area_hint="svc-legacy"
    )
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "missing-metadata-bearer_legacy-0" in result["findings"][0]["finding_id"]


def test_bearer_legacy_past_close_date_fires_svc003() -> None:
    project_area = _area(
        "fixtures/svc-bearer-legacy-past-close-date", area_hint="svc-overdue"
    )
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "bearer-legacy-close-date-passed-0" in result["findings"][0]["finding_id"]


def test_duplicate_mode_fires_svc003() -> None:
    project_area = _area("fixtures/svc-duplicate-mode", area_hint="svc-dup")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "duplicate-mode-bearer_legacy" in result["findings"][0]["finding_id"]


def test_impl_missing_handler_fires_svc003() -> None:
    project_area = _area("fixtures/svc-impl-missing-handler", area_hint="svc-orphaned")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "impl-missing-user_oidc" in result["findings"][0]["finding_id"]


def test_impl_undeclared_mode_fires_svc003() -> None:
    project_area = _area("fixtures/svc-impl-undeclared-mode", area_hint="svc-drift")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "impl-undeclared-user_oidc" in result["findings"][0]["finding_id"]


def test_planned_service_exempt_produces_no_findings() -> None:
    project_area = _area(
        "fixtures/svc-planned-service-exempt", area_hint="svc-future"
    )
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    assert result["findings"] == []


def test_malformed_yaml_fires_svc001_parse_error() -> None:
    project_area = _area("fixtures/svc-malformed-yaml", area_hint="svc-malformed")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-001"]
    assert "services-yml-malformed" in result["findings"][0]["finding_id"]


def test_no_services_manifest_produces_no_findings() -> None:
    # architecture-api-drift has no services.yml → evaluator returns empty gracefully
    project_area = normalise_project_area(
        extract_scope(["fixtures/architecture-api-drift"]), subsystem="signals"
    )
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    assert result["findings"] == []
    assert result["score"] == 100


def test_evaluation_is_deterministic() -> None:
    project_area = _area("fixtures/svc-duplicate-mode", area_hint="svc-dup")
    first = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    second = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    assert first == second


def test_audit_builder_routes_service_lifecycle_domain() -> None:
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
    result = build_audit_result(request)
    assert result["domain_status"] == {"service-lifecycle": {"status": "evaluated"}}
    assert len(result["findings"]) == 1
    finding = result["findings"][0]
    assert finding["rule_id"] == "SVC-003"
    assert "unknown-mode-0" in finding["finding_id"]


def test_audit_builder_emits_svc003_for_past_close_date_fixture() -> None:
    request = {
        "mode": "audit",
        "domains": ["service-lifecycle"],
        "scope": {
            "paths": ["fixtures/svc-bearer-legacy-past-close-date"],
            "subsystem": "service-lifecycle",
            "area_id": "svc-overdue",
        },
        "standards_version": "2026-04-18",
    }
    result = build_audit_result(request)
    assert result["scores"]["service-lifecycle"] < 100
    assert any(
        "bearer-legacy-close-date-passed" in str(finding["finding_id"])
        for finding in result["findings"]
    )


def test_conformant_all_modes_fixture_produces_no_findings() -> None:
    project_area = _area("fixtures/svc-conformant-all-modes", area_hint="svc-omni")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    assert result["findings"] == []
    assert result["score"] == 100


def test_rs256_conformant_produces_no_findings() -> None:
    project_area = _area("fixtures/svc-rs256-conformant", area_hint="svc-rs256-ok")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    assert result["findings"] == []


def test_rs256_impl_undeclared_fires_svc003() -> None:
    project_area = _area(
        "fixtures/svc-rs256-impl-undeclared", area_hint="svc-rs256-drift"
    )
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "impl-undeclared-service_rs256" in result["findings"][0]["finding_id"]


def test_rs256_missing_handler_fires_svc003() -> None:
    project_area = _area(
        "fixtures/svc-rs256-missing-handler", area_hint="svc-rs256-unhandled"
    )
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "impl-missing-service_rs256" in result["findings"][0]["finding_id"]


def test_api_key_missing_issuer_fires_svc003_metadata() -> None:
    project_area = _area(
        "fixtures/svc-api-key-missing-issuer", area_hint="svc-api-no-issuer"
    )
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "missing-metadata-api_key-0" in result["findings"][0]["finding_id"]


def test_audience_invalid_fires_svc003() -> None:
    project_area = _area("fixtures/svc-audience-invalid", area_hint="svc-bad-aud")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "audience-invalid-user_oidc-0" in result["findings"][0]["finding_id"]


def test_jwks_url_invalid_fires_svc003() -> None:
    project_area = _area("fixtures/svc-jwks-url-invalid", area_hint="svc-bad-jwks")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "jwks-url-invalid-user_oidc-0" in result["findings"][0]["finding_id"]


def test_auth_contract_wrong_type_fires_svc003() -> None:
    project_area = _area(
        "fixtures/svc-auth-contract-wrong-type", area_hint="svc-bad-auth-shape"
    )
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "auth-contract-wrong-type" in result["findings"][0]["finding_id"]


def test_accepted_modes_wrong_type_fires_svc003() -> None:
    project_area = _area(
        "fixtures/svc-accepted-modes-wrong-type", area_hint="svc-bad-modes-shape"
    )
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "accepted-modes-wrong-type" in result["findings"][0]["finding_id"]


def test_malformed_entry_fires_svc003() -> None:
    project_area = _area("fixtures/svc-malformed-entry", area_hint="svc-stringy-entry")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "malformed-entry-0" in result["findings"][0]["finding_id"]


def test_bearer_legacy_missing_close_date_fires_svc003() -> None:
    project_area = _area(
        "fixtures/svc-bearer-legacy-missing-close-date",
        area_hint="svc-no-close-date",
    )
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert "missing-metadata-bearer_legacy-0" in result["findings"][0]["finding_id"]
    assert "deprecation_close_date" in result["findings"][0]["summary"]


def test_bearer_legacy_malformed_close_date_fires_svc003() -> None:
    project_area = _area(
        "fixtures/svc-bearer-legacy-malformed-close-date",
        area_hint="svc-garbled-date",
    )
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-003"]
    assert (
        "bearer-legacy-close-date-malformed-0" in result["findings"][0]["finding_id"]
    )


def test_working_dir_missing_fires_svc001() -> None:
    project_area = _area(
        "fixtures/svc-working-dir-missing", area_hint="svc-wandering"
    )
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-001"]
    assert "working-dir-missing" in result["findings"][0]["finding_id"]


def test_multi_service_audits_ready_and_skips_planned() -> None:
    project_area = _area("fixtures/svc-multi-service", area_hint="svc-multi")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    for finding in result["findings"]:
        # Only the non-planned sibling should produce findings.
        assert "active-but-broken" in finding["finding_id"]
        assert "planned-sibling" not in finding["finding_id"]
    rule_ids = sorted({finding["rule_id"] for finding in result["findings"]})
    assert rule_ids == ["SVC-001", "SVC-003"]


def test_bare_map_rejected_as_malformed() -> None:
    project_area = _area("fixtures/svc-bare-map", area_hint="svc-bare")
    result = evaluate_service_lifecycle(project_area, standards_version="2026-04-18")
    rule_ids = [finding["rule_id"] for finding in result["findings"]]
    assert rule_ids == ["SVC-001"]
    assert "services-yml-malformed" in result["findings"][0]["finding_id"]


def test_standards_version_must_be_iso_date() -> None:
    project_area = _area("fixtures/svc-conformant", area_hint="svc-widget")
    try:
        evaluate_service_lifecycle(project_area, standards_version="2026/04/18")
    except ValueError as exc:
        assert "YYYY-MM-DD" in str(exc)
    else:
        raise AssertionError("expected ValueError for malformed standards_version")
