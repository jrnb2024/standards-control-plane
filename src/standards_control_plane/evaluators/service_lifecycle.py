"""Service-lifecycle evaluator (SVC-001, SVC-002, SVC-003)."""

from __future__ import annotations

import re
from datetime import date
from pathlib import PurePosixPath
from typing import Any

import yaml

from ..confidence import classify_confidence
from ..registry import RegistrySnapshot, RuleRecord, load_registry
from ..resources import output_dir, project_root
from ..schema_tools import validate_with_schema
from ..scoring import score_findings
from ..waivers import load_waivers

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

APPROVED_MODES = (
    "mode.user_oidc",
    "mode.service_rs256",
    "mode.api_key",
    "mode.bearer_legacy",
)

MODE_METADATA_REQUIRED = {
    "mode.user_oidc": ("audience", "jwks_url"),
    "mode.service_rs256": ("audience", "jwks_url"),
    "mode.api_key": ("issuer",),
    "mode.bearer_legacy": ("deprecation_close_date", "waiver_ref"),
}

MODE_CODE_MARKERS = {
    "mode.user_oidc": (
        "ControlTowerAuth",
        "ct_auth.",
        "create_bff_routes",
        "CT_JWKS_URL",
    ),
    "mode.service_rs256": (
        'algorithms=["RS256"]',
        "algorithms=['RS256']",
        'algorithm="RS256"',
        "algorithm='RS256'",
    ),
    "mode.api_key": (
        "X-API-Key",
        "x-api-key",
    ),
    "mode.bearer_legacy": (
        "secrets.compare_digest",
    ),
}

REQUIRED_RUNTIME_CONTRACT_FIELDS = (
    "start_command",
    "working_dir",
    "interpreter",
    "required_infra",
    "group",
)

SERVICE_MANIFEST_FILENAMES = {"services.yml", "services.yaml"}

AUDIENCE_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
JWKS_URL_PATTERN = re.compile(r"^https?://[^\s]+$")

CODE_EXTENSIONS = (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".java", ".rs", ".rb")

# Paths that host the marker strings themselves as literal source data, not as
# real implementation. Skipping them avoids self-poisoning when SCP dogfoods
# the evaluator against its own repo. These suffixes are matched against
# forward-slashed path strings.
EVALUATOR_SELF_EXCLUSIONS = (
    "evaluators/service_lifecycle.py",
)

ALLOWED_BASE_ENTRY_FIELDS = frozenset({"mode", "notes"})

ADDITIONAL_ENTRY_FIELDS_BY_MODE: dict[str, frozenset[str]] = {
    "mode.user_oidc": frozenset({"audience", "jwks_url"}),
    "mode.service_rs256": frozenset({"audience", "jwks_url"}),
    "mode.api_key": frozenset({"issuer", "key_id_prefix"}),
    "mode.bearer_legacy": frozenset({"deprecation_close_date", "waiver_ref"}),
}


def _validate_standards_version(standards_version: str) -> date:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", standards_version):
        raise ValueError("standards_version must use YYYY-MM-DD format in phase 1")
    return date.fromisoformat(standards_version)


def _deterministic_timestamp(standards_version: str) -> str:
    _validate_standards_version(standards_version)
    return f"{standards_version}T00:00:00Z"


def _read_repo_file(path_value: str) -> str:
    root = project_root().resolve()
    resolved_path = (root / path_value).resolve()
    if not resolved_path.is_relative_to(root):
        return ""
    if not resolved_path.exists() or not resolved_path.is_file():
        return ""
    return resolved_path.read_text(encoding="utf-8")


def _directory_exists(path_value: str) -> bool:
    root = project_root().resolve()
    resolved_path = (root / path_value).resolve()
    if not resolved_path.is_relative_to(root):
        return False
    return resolved_path.exists() and resolved_path.is_dir()


def _service_lifecycle_rules(
    registry_snapshot: RegistrySnapshot | None = None,
) -> dict[str, RuleRecord]:
    registry = registry_snapshot or load_registry()
    return {
        rule.rule_id: rule
        for rule in registry.active_rules_for(["service-lifecycle"])
    }


def _find_services_manifest(project_area: dict[str, Any]) -> str | None:
    for path_value in project_area["artefacts"]["configs"]:
        name = PurePosixPath(str(path_value).replace("\\", "/")).name.lower()
        if name in SERVICE_MANIFEST_FILENAMES:
            return str(path_value)
    return None


def _parse_services(
    manifest_path: str,
) -> tuple[dict[str, Any] | None, str | None]:
    """Return (services-by-name, parse_error_reason).

    Requires a top-level ``services:`` mapping. A bare map (no ``services`` key)
    is rejected to prevent non-service top-level keys like ``infrastructure``
    from being treated as services.
    """
    content = _read_repo_file(manifest_path)
    if not content:
        return None, None
    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        return None, f"yaml parse error: {exc.__class__.__name__}"
    if not isinstance(parsed, dict):
        return None, "top-level document is not a mapping"
    if "services" not in parsed:
        return None, "top-level 'services' key is missing"
    services_block = parsed["services"]
    if not isinstance(services_block, dict):
        return None, "'services' value is not a mapping"
    services: dict[str, Any] = {}
    for name, config in services_block.items():
        if isinstance(name, str) and isinstance(config, dict):
            services[name] = config
    return services, None


def _service_is_planned(service_config: dict[str, Any]) -> bool:
    local = service_config.get("local")
    if not isinstance(local, dict):
        return False
    return str(local.get("status", "")).lower() == "planned"


def _runtime_contract(service_config: dict[str, Any]) -> dict[str, Any] | None:
    local = service_config.get("local")
    if not isinstance(local, dict):
        return None
    rc = local.get("runtime_contract")
    return rc if isinstance(rc, dict) else None


def _parse_close_date(value: Any) -> tuple[date | None, bool]:
    """Return (parsed_date, was_string_but_malformed)."""
    if value is None:
        return None, False
    if not isinstance(value, str):
        return None, True
    try:
        return date.fromisoformat(value), False
    except ValueError:
        return None, True


def _build_finding(
    *,
    rule: RuleRecord,
    area_id: str,
    service_name: str | None,
    signal_key: str,
    title: str,
    summary: str,
    evidence: list[dict[str, str]],
    suggested_remediation: list[str],
    confidence: float,
    standards_version: str,
    evaluated_at: str,
) -> dict[str, Any]:
    scope_suffix = f"-{service_name}" if service_name else ""
    finding = {
        "finding_id": f"F-{rule.rule_id}-{area_id}{scope_suffix}-{signal_key}",
        "domain": "service-lifecycle",
        "rule_id": rule.rule_id,
        "severity": rule.severity_default,
        "status": "open",
        "title": title,
        "summary": summary,
        "evidence": evidence,
        "area_id": area_id,
        "suggested_remediation": suggested_remediation,
        "confidence": confidence,
        "confidence_class": classify_confidence(confidence),
        "detected_by": "service-lifecycle-evaluator",
        "standards_version": standards_version,
        "created_at": evaluated_at,
        "updated_at": evaluated_at,
    }
    validate_with_schema(finding, "finding.schema.json")
    return finding


def _code_paths_to_scan(project_area: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for bucket in ("code_paths", "services"):
        for path_value in project_area["artefacts"].get(bucket, []):
            path_string = str(path_value)
            if not path_string.endswith(CODE_EXTENSIONS):
                continue
            normalised = path_string.replace("\\", "/")
            if any(
                normalised == excl or normalised.endswith("/" + excl)
                for excl in EVALUATOR_SELF_EXCLUSIONS
            ):
                continue
            if path_string in seen:
                continue
            seen.add(path_string)
            paths.append(path_string)
    return sorted(paths)


def _known_waiver_ids() -> set[str] | None:
    """Return the set of known waiver_ids, or None if no waivers file is loaded.

    Returns None when ``output/findings/waivers.json`` is absent or contains no
    entries, so fixtures and adopters in an empty-waiver state are not forced
    to maintain a populated file before the auto-check activates.
    """
    waivers_path = output_dir() / "findings" / "waivers.json"
    if not waivers_path.exists():
        return None
    try:
        waivers = load_waivers(waivers_path)
    except Exception:
        return None
    if not waivers:
        return None
    return {waiver.waiver_id for waiver in waivers}


def _mode_marker_hits(
    code_paths: list[str],
) -> dict[str, list[tuple[str, str]]]:
    """For each approved mode, list (path, marker) tuples where a marker is found."""
    hits: dict[str, list[tuple[str, str]]] = {mode: [] for mode in APPROVED_MODES}
    for path_value in code_paths:
        content = _read_repo_file(path_value)
        if not content:
            continue
        for mode, markers in MODE_CODE_MARKERS.items():
            for marker in markers:
                if marker in content:
                    hits[mode].append((path_value, marker))
                    break
    return hits


def _svc001_findings(
    services: dict[str, Any],
    *,
    manifest_path: str,
    area_id: str,
    rule: RuleRecord,
    standards_version: str,
    evaluated_at: str,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for service_name in sorted(services.keys()):
        service_config = services[service_name]
        if _service_is_planned(service_config):
            continue
        runtime_contract = _runtime_contract(service_config)
        if runtime_contract is None:
            findings.append(
                _build_finding(
                    rule=rule,
                    area_id=area_id,
                    service_name=service_name,
                    signal_key="missing-runtime-contract",
                    title="Service missing runtime_contract block",
                    summary=(
                        f"Service '{service_name}' has no runtime_contract under its "
                        f"local environment in {manifest_path}."
                    ),
                    evidence=[
                        {
                            "path": manifest_path,
                            "evidence_class": "declared_metadata",
                            "locator": f"{service_name}.local.runtime_contract",
                        }
                    ],
                    suggested_remediation=[
                        "Add a runtime_contract block under local declaring start_command, working_dir, interpreter, required_infra, and group.",
                    ],
                    confidence=0.95,
                    standards_version=standards_version,
                    evaluated_at=evaluated_at,
                )
            )
            continue
        missing_fields = [
            field
            for field in REQUIRED_RUNTIME_CONTRACT_FIELDS
            if field not in runtime_contract
        ]
        if missing_fields:
            findings.append(
                _build_finding(
                    rule=rule,
                    area_id=area_id,
                    service_name=service_name,
                    signal_key="missing-required-fields",
                    title="Runtime contract missing required fields",
                    summary=(
                        f"Service '{service_name}' runtime_contract is missing: "
                        + ", ".join(missing_fields)
                    ),
                    evidence=[
                        {
                            "path": manifest_path,
                            "evidence_class": "declared_metadata",
                            "locator": f"{service_name}.local.runtime_contract",
                        }
                    ],
                    suggested_remediation=[
                        f"Declare {', '.join(missing_fields)} under the runtime_contract block.",
                    ],
                    confidence=0.95,
                    standards_version=standards_version,
                    evaluated_at=evaluated_at,
                )
            )
        if (
            runtime_contract.get("interpreter") == "python-venv"
            and "venv_path" not in runtime_contract
        ):
            findings.append(
                _build_finding(
                    rule=rule,
                    area_id=area_id,
                    service_name=service_name,
                    signal_key="python-venv-missing-venv-path",
                    title="python-venv interpreter requires venv_path",
                    summary=(
                        f"Service '{service_name}' uses interpreter 'python-venv' but does not "
                        "declare venv_path in its runtime_contract."
                    ),
                    evidence=[
                        {
                            "path": manifest_path,
                            "evidence_class": "declared_metadata",
                            "locator": f"{service_name}.local.runtime_contract.interpreter",
                        }
                    ],
                    suggested_remediation=[
                        "Declare venv_path as a relative path from working_dir to the service's Python venv.",
                    ],
                    confidence=0.95,
                    standards_version=standards_version,
                    evaluated_at=evaluated_at,
                )
            )
        working_dir = runtime_contract.get("working_dir")
        if isinstance(working_dir, str) and working_dir:
            if not _directory_exists(working_dir):
                findings.append(
                    _build_finding(
                        rule=rule,
                        area_id=area_id,
                        service_name=service_name,
                        signal_key="working-dir-missing",
                        title="Runtime contract working_dir does not exist",
                        summary=(
                            f"Service '{service_name}' declares working_dir '{working_dir}' but "
                            "no directory exists at that path relative to the repo root."
                        ),
                        evidence=[
                            {
                                "path": manifest_path,
                                "evidence_class": "declared_metadata",
                                "locator": f"{service_name}.local.runtime_contract.working_dir",
                            }
                        ],
                        suggested_remediation=[
                            "Update working_dir to point at the service's real directory, or create the directory.",
                        ],
                        confidence=0.97,
                        standards_version=standards_version,
                        evaluated_at=evaluated_at,
                    )
                )
    return findings


def _svc002_findings(
    services: dict[str, Any],
    *,
    manifest_path: str,
    project_area: dict[str, Any],
    area_id: str,
    rule: RuleRecord,
    standards_version: str,
    evaluated_at: str,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    code_paths = _code_paths_to_scan(project_area)
    for service_name in sorted(services.keys()):
        service_config = services[service_name]
        if _service_is_planned(service_config):
            continue
        healthcheck = service_config.get("healthcheck")
        if not isinstance(healthcheck, str) or not healthcheck:
            continue
        handler_found = False
        for path_value in code_paths:
            content = _read_repo_file(path_value)
            if not content:
                continue
            if healthcheck in content:
                handler_found = True
                break
        if handler_found:
            continue
        findings.append(
            _build_finding(
                rule=rule,
                area_id=area_id,
                service_name=service_name,
                signal_key="missing-health-handler",
                title="Declared healthcheck path has no handler in scanned source",
                summary=(
                    f"Service '{service_name}' declares healthcheck '{healthcheck}' in "
                    f"{manifest_path}, but the exact path was not found in any scanned code "
                    "file. Runtime response-shape checks are out of scope for the static "
                    "evaluator."
                ),
                evidence=[
                    {
                        "path": manifest_path,
                        "evidence_class": "declared_metadata",
                        "locator": f"{service_name}.healthcheck",
                    }
                ],
                suggested_remediation=[
                    (
                        "Implement a handler for the declared healthcheck path that returns the "
                        "platform schema (status, version, checks), or update the services.yml "
                        "declaration to match the real route."
                    ),
                ],
                confidence=0.85,
                standards_version=standards_version,
                evaluated_at=evaluated_at,
            )
        )
    return findings


def _svc003_findings(
    services: dict[str, Any],
    *,
    manifest_path: str,
    project_area: dict[str, Any],
    area_id: str,
    rule: RuleRecord,
    audit_date: date,
    standards_version: str,
    evaluated_at: str,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    code_paths = _code_paths_to_scan(project_area)
    marker_hits = _mode_marker_hits(code_paths)
    known_waiver_ids = _known_waiver_ids()
    for service_name in sorted(services.keys()):
        service_config = services[service_name]
        if _service_is_planned(service_config):
            continue
        runtime_contract = _runtime_contract(service_config)
        if runtime_contract is None:
            continue
        auth_contract = runtime_contract.get("auth_contract")
        if auth_contract is None:
            findings.append(
                _build_finding(
                    rule=rule,
                    area_id=area_id,
                    service_name=service_name,
                    signal_key="missing-auth-contract",
                    title="Service missing auth_contract block",
                    summary=(
                        f"Service '{service_name}' has no auth_contract under runtime_contract "
                        f"in {manifest_path}."
                    ),
                    evidence=[
                        {
                            "path": manifest_path,
                            "evidence_class": "declared_metadata",
                            "locator": f"{service_name}.local.runtime_contract.auth_contract",
                        }
                    ],
                    suggested_remediation=[
                        "Declare auth_contract.accepted_modes listing one or more approved auth modes.",
                    ],
                    confidence=0.95,
                    standards_version=standards_version,
                    evaluated_at=evaluated_at,
                )
            )
            continue
        if not isinstance(auth_contract, dict):
            findings.append(
                _build_finding(
                    rule=rule,
                    area_id=area_id,
                    service_name=service_name,
                    signal_key="auth-contract-wrong-type",
                    title="auth_contract block is not a mapping",
                    summary=(
                        f"Service '{service_name}' has an auth_contract value that is not a "
                        f"mapping (got {type(auth_contract).__name__})."
                    ),
                    evidence=[
                        {
                            "path": manifest_path,
                            "evidence_class": "declared_metadata",
                            "locator": f"{service_name}.local.runtime_contract.auth_contract",
                        }
                    ],
                    suggested_remediation=[
                        "Rewrite auth_contract as a mapping containing an accepted_modes array.",
                    ],
                    confidence=0.97,
                    standards_version=standards_version,
                    evaluated_at=evaluated_at,
                )
            )
            continue
        accepted_modes = auth_contract.get("accepted_modes")
        if accepted_modes is None or (
            isinstance(accepted_modes, list) and not accepted_modes
        ):
            findings.append(
                _build_finding(
                    rule=rule,
                    area_id=area_id,
                    service_name=service_name,
                    signal_key="empty-accepted-modes",
                    title="auth_contract.accepted_modes is empty",
                    summary=(
                        f"Service '{service_name}' declares an auth_contract block but no "
                        "accepted_modes entries."
                    ),
                    evidence=[
                        {
                            "path": manifest_path,
                            "evidence_class": "declared_metadata",
                            "locator": f"{service_name}.local.runtime_contract.auth_contract.accepted_modes",
                        }
                    ],
                    suggested_remediation=[
                        "Declare at least one approved mode in accepted_modes.",
                    ],
                    confidence=0.95,
                    standards_version=standards_version,
                    evaluated_at=evaluated_at,
                )
            )
            continue
        if not isinstance(accepted_modes, list):
            findings.append(
                _build_finding(
                    rule=rule,
                    area_id=area_id,
                    service_name=service_name,
                    signal_key="accepted-modes-wrong-type",
                    title="accepted_modes is not a list",
                    summary=(
                        f"Service '{service_name}' accepted_modes value is not a list (got "
                        f"{type(accepted_modes).__name__})."
                    ),
                    evidence=[
                        {
                            "path": manifest_path,
                            "evidence_class": "declared_metadata",
                            "locator": f"{service_name}.local.runtime_contract.auth_contract.accepted_modes",
                        }
                    ],
                    suggested_remediation=[
                        "Rewrite accepted_modes as a non-empty list of mode entries.",
                    ],
                    confidence=0.97,
                    standards_version=standards_version,
                    evaluated_at=evaluated_at,
                )
            )
            continue
        declared_modes: list[str] = []
        seen_modes: set[str] = set()
        duplicates: set[str] = set()
        for index, entry in enumerate(accepted_modes):
            if not isinstance(entry, dict):
                findings.append(
                    _build_finding(
                        rule=rule,
                        area_id=area_id,
                        service_name=service_name,
                        signal_key=f"malformed-entry-{index}",
                        title="accepted_modes entry is not a mapping",
                        summary=(
                            f"Service '{service_name}' accepted_modes[{index}] is not a mapping "
                            f"(got {type(entry).__name__})."
                        ),
                        evidence=[
                            {
                                "path": manifest_path,
                                "evidence_class": "declared_metadata",
                                "locator": f"{service_name}.local.runtime_contract.auth_contract.accepted_modes[{index}]",
                            }
                        ],
                        suggested_remediation=[
                            "Rewrite the entry as a mapping with a 'mode' key and the required per-mode metadata.",
                        ],
                        confidence=0.97,
                        standards_version=standards_version,
                        evaluated_at=evaluated_at,
                    )
                )
                continue
            mode_value = entry.get("mode")
            if not isinstance(mode_value, str):
                findings.append(
                    _build_finding(
                        rule=rule,
                        area_id=area_id,
                        service_name=service_name,
                        signal_key=f"malformed-mode-{index}",
                        title="accepted_modes entry has non-string mode",
                        summary=(
                            f"Service '{service_name}' accepted_modes[{index}].mode is not a "
                            f"string (got {type(mode_value).__name__})."
                        ),
                        evidence=[
                            {
                                "path": manifest_path,
                                "evidence_class": "declared_metadata",
                                "locator": f"{service_name}.local.runtime_contract.auth_contract.accepted_modes[{index}].mode",
                            }
                        ],
                        suggested_remediation=[
                            "Set 'mode' to one of the four approved mode strings.",
                        ],
                        confidence=0.97,
                        standards_version=standards_version,
                        evaluated_at=evaluated_at,
                    )
                )
                continue
            if mode_value in seen_modes:
                duplicates.add(mode_value)
            else:
                seen_modes.add(mode_value)
                declared_modes.append(mode_value)
            if mode_value not in APPROVED_MODES:
                findings.append(
                    _build_finding(
                        rule=rule,
                        area_id=area_id,
                        service_name=service_name,
                        signal_key=f"unknown-mode-{index}",
                        title="Declared auth mode is not in the approved set",
                        summary=(
                            f"Service '{service_name}' declares mode '{mode_value}', which is "
                            "not one of mode.user_oidc, mode.service_rs256, mode.api_key, "
                            "mode.bearer_legacy."
                        ),
                        evidence=[
                            {
                                "path": manifest_path,
                                "evidence_class": "declared_metadata",
                                "locator": f"{service_name}.local.runtime_contract.auth_contract.accepted_modes[{index}].mode",
                            }
                        ],
                        suggested_remediation=[
                            "Replace the mode value with one of the four approved modes, or raise a standards change.",
                        ],
                        confidence=0.97,
                        standards_version=standards_version,
                        evaluated_at=evaluated_at,
                    )
                )
                continue
            allowed_fields = (
                ALLOWED_BASE_ENTRY_FIELDS
                | ADDITIONAL_ENTRY_FIELDS_BY_MODE[mode_value]
            )
            unknown_fields = sorted(
                field for field in entry.keys() if field not in allowed_fields
            )
            if unknown_fields:
                findings.append(
                    _build_finding(
                        rule=rule,
                        area_id=area_id,
                        service_name=service_name,
                        signal_key=f"unknown-field-{mode_value.split('.', 1)[-1]}-{index}",
                        title=f"{mode_value} entry carries unknown fields",
                        summary=(
                            f"Service '{service_name}' {mode_value} entry has unknown field(s): "
                            + ", ".join(unknown_fields)
                            + ". The auth-contract schema does not allow extra fields. "
                            "Typos in required-field names surface here."
                        ),
                        evidence=[
                            {
                                "path": manifest_path,
                                "evidence_class": "declared_metadata",
                                "locator": f"{service_name}.local.runtime_contract.auth_contract.accepted_modes[{index}]",
                            }
                        ],
                        suggested_remediation=[
                            f"Remove or correct {', '.join(unknown_fields)} in the {mode_value} entry.",
                        ],
                        confidence=0.97,
                        standards_version=standards_version,
                        evaluated_at=evaluated_at,
                    )
                )
            required_fields = MODE_METADATA_REQUIRED[mode_value]
            missing = [field for field in required_fields if field not in entry]
            if missing:
                findings.append(
                    _build_finding(
                        rule=rule,
                        area_id=area_id,
                        service_name=service_name,
                        signal_key=f"missing-metadata-{mode_value.split('.', 1)[-1]}-{index}",
                        title=f"{mode_value} entry missing required metadata",
                        summary=(
                            f"Service '{service_name}' declares {mode_value} but the entry is "
                            "missing: " + ", ".join(missing)
                        ),
                        evidence=[
                            {
                                "path": manifest_path,
                                "evidence_class": "declared_metadata",
                                "locator": f"{service_name}.local.runtime_contract.auth_contract.accepted_modes[{index}]",
                            }
                        ],
                        suggested_remediation=[
                            f"Add {', '.join(missing)} to the {mode_value} entry.",
                        ],
                        confidence=0.95,
                        standards_version=standards_version,
                        evaluated_at=evaluated_at,
                    )
                )
                continue
            if mode_value in ("mode.user_oidc", "mode.service_rs256"):
                audience_value = entry.get("audience")
                if isinstance(audience_value, str) and not AUDIENCE_PATTERN.fullmatch(
                    audience_value
                ):
                    findings.append(
                        _build_finding(
                            rule=rule,
                            area_id=area_id,
                            service_name=service_name,
                            signal_key=f"audience-invalid-{mode_value.split('.', 1)[-1]}-{index}",
                            title=f"{mode_value} audience is not a bare app-id",
                            summary=(
                                f"Service '{service_name}' {mode_value} audience "
                                f"'{audience_value}' does not match the bare app-id pattern "
                                f"'^[a-z][a-z0-9-]*$'. The audience must be the service's "
                                f"services.yml key, not a URI."
                            ),
                            evidence=[
                                {
                                    "path": manifest_path,
                                    "evidence_class": "declared_metadata",
                                    "locator": f"{service_name}.local.runtime_contract.auth_contract.accepted_modes[{index}].audience",
                                }
                            ],
                            suggested_remediation=[
                                "Set audience to the service's services.yml key (e.g. 'widget', 'scp-dev').",
                            ],
                            confidence=0.97,
                            standards_version=standards_version,
                            evaluated_at=evaluated_at,
                        )
                    )
                jwks_value = entry.get("jwks_url")
                if isinstance(jwks_value, str) and not JWKS_URL_PATTERN.fullmatch(
                    jwks_value
                ):
                    findings.append(
                        _build_finding(
                            rule=rule,
                            area_id=area_id,
                            service_name=service_name,
                            signal_key=f"jwks-url-invalid-{mode_value.split('.', 1)[-1]}-{index}",
                            title=f"{mode_value} jwks_url is not a valid http(s) URL",
                            summary=(
                                f"Service '{service_name}' {mode_value} jwks_url "
                                f"'{jwks_value}' is not a valid http(s) URL."
                            ),
                            evidence=[
                                {
                                    "path": manifest_path,
                                    "evidence_class": "declared_metadata",
                                    "locator": f"{service_name}.local.runtime_contract.auth_contract.accepted_modes[{index}].jwks_url",
                                }
                            ],
                            suggested_remediation=[
                                "Set jwks_url to the authoritative JWKS endpoint URL the service verifies against.",
                            ],
                            confidence=0.95,
                            standards_version=standards_version,
                            evaluated_at=evaluated_at,
                        )
                    )
            if mode_value == "mode.bearer_legacy":
                waiver_ref_value = entry.get("waiver_ref")
                if (
                    known_waiver_ids is not None
                    and isinstance(waiver_ref_value, str)
                    and waiver_ref_value
                    and waiver_ref_value not in known_waiver_ids
                ):
                    findings.append(
                        _build_finding(
                            rule=rule,
                            area_id=area_id,
                            service_name=service_name,
                            signal_key=f"bearer-legacy-waiver-not-found-{index}",
                            title="mode.bearer_legacy waiver_ref is not registered",
                            summary=(
                                f"Service '{service_name}' mode.bearer_legacy waiver_ref "
                                f"'{waiver_ref_value}' is not found in the waivers registered "
                                "in output/findings/waivers.json."
                            ),
                            evidence=[
                                {
                                    "path": manifest_path,
                                    "evidence_class": "declared_metadata",
                                    "locator": f"{service_name}.local.runtime_contract.auth_contract.accepted_modes[{index}].waiver_ref",
                                }
                            ],
                            suggested_remediation=[
                                "Register the migration waiver in output/findings/waivers.json, or update the waiver_ref to match an existing waiver_id.",
                            ],
                            confidence=0.95,
                            standards_version=standards_version,
                            evaluated_at=evaluated_at,
                        )
                    )
                close_date, close_date_malformed = _parse_close_date(
                    entry.get("deprecation_close_date")
                )
                if close_date_malformed:
                    findings.append(
                        _build_finding(
                            rule=rule,
                            area_id=area_id,
                            service_name=service_name,
                            signal_key=f"bearer-legacy-close-date-malformed-{index}",
                            title="mode.bearer_legacy deprecation_close_date is not a valid ISO date",
                            summary=(
                                f"Service '{service_name}' mode.bearer_legacy "
                                f"deprecation_close_date "
                                f"'{entry.get('deprecation_close_date')!r}' is not a parseable "
                                "YYYY-MM-DD date."
                            ),
                            evidence=[
                                {
                                    "path": manifest_path,
                                    "evidence_class": "declared_metadata",
                                    "locator": f"{service_name}.local.runtime_contract.auth_contract.accepted_modes[{index}].deprecation_close_date",
                                }
                            ],
                            suggested_remediation=[
                                "Set deprecation_close_date to a YYYY-MM-DD date.",
                            ],
                            confidence=0.97,
                            standards_version=standards_version,
                            evaluated_at=evaluated_at,
                        )
                    )
                elif close_date is not None and close_date <= audit_date:
                    findings.append(
                        _build_finding(
                            rule=rule,
                            area_id=area_id,
                            service_name=service_name,
                            signal_key=f"bearer-legacy-close-date-passed-{index}",
                            title="mode.bearer_legacy deprecation_close_date has passed",
                            summary=(
                                f"Service '{service_name}' mode.bearer_legacy "
                                f"deprecation_close_date is {close_date.isoformat()}, on or "
                                f"before audit date {audit_date.isoformat()}."
                            ),
                            evidence=[
                                {
                                    "path": manifest_path,
                                    "evidence_class": "declared_metadata",
                                    "locator": f"{service_name}.local.runtime_contract.auth_contract.accepted_modes[{index}].deprecation_close_date",
                                }
                            ],
                            suggested_remediation=[
                                "Complete the migration to mode.api_key or another approved mode and remove the bearer_legacy entry, or renew the waiver with an updated close date after governance review.",
                            ],
                            confidence=0.97,
                            standards_version=standards_version,
                            evaluated_at=evaluated_at,
                        )
                    )
        for duplicate_mode in sorted(duplicates):
            findings.append(
                _build_finding(
                    rule=rule,
                    area_id=area_id,
                    service_name=service_name,
                    signal_key=f"duplicate-mode-{duplicate_mode.split('.', 1)[-1]}",
                    title="Mode declared more than once",
                    summary=(
                        f"Service '{service_name}' declares {duplicate_mode} more than once in "
                        "accepted_modes. Each approved mode may appear at most once."
                    ),
                    evidence=[
                        {
                            "path": manifest_path,
                            "evidence_class": "declared_metadata",
                            "locator": f"{service_name}.local.runtime_contract.auth_contract.accepted_modes",
                        }
                    ],
                    suggested_remediation=[
                        f"Collapse the duplicate {duplicate_mode} entries into a single entry with the authoritative metadata.",
                    ],
                    confidence=0.95,
                    standards_version=standards_version,
                    evaluated_at=evaluated_at,
                )
            )
        if not code_paths:
            continue
        for declared_mode in declared_modes:
            if declared_mode not in APPROVED_MODES:
                continue
            if not marker_hits[declared_mode]:
                findings.append(
                    _build_finding(
                        rule=rule,
                        area_id=area_id,
                        service_name=service_name,
                        signal_key=f"impl-missing-{declared_mode.split('.', 1)[-1]}",
                        title=f"Declared {declared_mode} has no matching implementation markers",
                        summary=(
                            f"Service '{service_name}' declares {declared_mode} but no "
                            "implementation markers for that mode were found in scanned source. "
                            "The code-pattern scan looked for: "
                            + ", ".join(MODE_CODE_MARKERS[declared_mode])
                        ),
                        evidence=[
                            {
                                "path": manifest_path,
                                "evidence_class": "declared_metadata",
                                "locator": f"{service_name}.local.runtime_contract.auth_contract.accepted_modes",
                            }
                        ],
                        suggested_remediation=[
                            f"Implement handler code for {declared_mode} in the service, or drop the mode from accepted_modes if it is not actually used.",
                        ],
                        confidence=0.85,
                        standards_version=standards_version,
                        evaluated_at=evaluated_at,
                    )
                )
        for mode in APPROVED_MODES:
            if mode in declared_modes:
                continue
            if not marker_hits[mode]:
                continue
            first_hit_path, first_marker = marker_hits[mode][0]
            findings.append(
                _build_finding(
                    rule=rule,
                    area_id=area_id,
                    service_name=service_name,
                    signal_key=f"impl-undeclared-{mode.split('.', 1)[-1]}",
                    title=f"Implementation markers present for undeclared {mode}",
                    summary=(
                        f"Service '{service_name}' does not declare {mode} in accepted_modes, "
                        f"but a marker for that mode was found in {first_hit_path} "
                        f"(locator: '{first_marker}')."
                    ),
                    evidence=[
                        {
                            "path": first_hit_path,
                            "evidence_class": "direct_file",
                            "locator": first_marker,
                        },
                        {
                            "path": manifest_path,
                            "evidence_class": "declared_metadata",
                            "locator": f"{service_name}.local.runtime_contract.auth_contract.accepted_modes",
                        },
                    ],
                    suggested_remediation=[
                        f"Declare {mode} in accepted_modes, or remove the implementation path that handles it.",
                    ],
                    confidence=0.85,
                    standards_version=standards_version,
                    evaluated_at=evaluated_at,
                )
            )
    return findings


def _sorted_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        findings,
        key=lambda finding: (
            SEVERITY_ORDER.get(str(finding["severity"]), 99),
            str(finding["finding_id"]),
        ),
    )


def _recommended_actions(findings: list[dict[str, Any]]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for finding in findings:
        for action in finding.get("suggested_remediation", []):
            action_value = str(action)
            if action_value not in seen:
                ordered.append(action_value)
                seen.add(action_value)
    return ordered


def evaluate_service_lifecycle(
    project_area: dict[str, Any],
    *,
    standards_version: str,
    evaluated_at: str | None = None,
    registry_snapshot: RegistrySnapshot | None = None,
) -> dict[str, Any]:
    validate_with_schema(project_area, "project-area.schema.json")
    audit_date = _validate_standards_version(standards_version)
    timestamp = evaluated_at or f"{standards_version}T00:00:00Z"
    manifest_path = _find_services_manifest(project_area)
    if manifest_path is None:
        return {"score": 100, "findings": [], "recommended_actions": []}
    rules = _service_lifecycle_rules(registry_snapshot)
    services, parse_error = _parse_services(manifest_path)
    if parse_error is not None:
        malformed_finding = _build_finding(
            rule=rules["SVC-001"],
            area_id=str(project_area["area_id"]),
            service_name=None,
            signal_key="services-yml-malformed",
            title="services.yml could not be parsed",
            summary=f"{manifest_path} is not a valid services manifest: {parse_error}.",
            evidence=[
                {
                    "path": manifest_path,
                    "evidence_class": "declared_metadata",
                    "locator": "root",
                }
            ],
            suggested_remediation=[
                "Repair the YAML so the file parses and declares a top-level 'services' mapping of service names to service configuration.",
            ],
            confidence=0.99,
            standards_version=standards_version,
            evaluated_at=timestamp,
        )
        sorted_findings = [malformed_finding]
        return {
            "score": score_findings(sorted_findings),
            "findings": sorted_findings,
            "recommended_actions": _recommended_actions(sorted_findings),
        }
    if not services:
        return {"score": 100, "findings": [], "recommended_actions": []}
    area_id = str(project_area["area_id"])
    findings: list[dict[str, Any]] = []
    findings.extend(
        _svc001_findings(
            services,
            manifest_path=manifest_path,
            area_id=area_id,
            rule=rules["SVC-001"],
            standards_version=standards_version,
            evaluated_at=timestamp,
        )
    )
    findings.extend(
        _svc002_findings(
            services,
            manifest_path=manifest_path,
            project_area=project_area,
            area_id=area_id,
            rule=rules["SVC-002"],
            standards_version=standards_version,
            evaluated_at=timestamp,
        )
    )
    findings.extend(
        _svc003_findings(
            services,
            manifest_path=manifest_path,
            project_area=project_area,
            area_id=area_id,
            rule=rules["SVC-003"],
            audit_date=audit_date,
            standards_version=standards_version,
            evaluated_at=timestamp,
        )
    )
    sorted_findings = _sorted_findings(findings)
    return {
        "score": score_findings(sorted_findings),
        "findings": sorted_findings,
        "recommended_actions": _recommended_actions(sorted_findings),
    }
