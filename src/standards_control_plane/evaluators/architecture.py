"""Architecture evaluator."""

from __future__ import annotations

import re
from typing import Any

from ..registry import RuleRecord, load_registry
from ..resources import project_root
from ..schema_tools import validate_with_schema
from ..scoring import score_findings

SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}
REMOTE_ACCESS_MARKERS = ("fetch(", "axios.", "requests.", "httpx.")
ASYNC_EVENT_MARKERS = ("asyncio.create_task(", "threading.Thread(", "publish_event(", "emit_event(")
APPROVED_WRAPPER_MARKERS = ("workflow_runner", "task_queue", "event_bus")
WORKFLOW_ACTION_MARKERS = ("resolve", "approve", "reject", "dispatch", "submit")


def _deterministic_timestamp(standards_version: str) -> str:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", standards_version):
        raise ValueError("standards_version must use YYYY-MM-DD format in phase 1")
    return f"{standards_version}T00:00:00Z"


def _architecture_rules() -> dict[str, RuleRecord]:
    registry = load_registry()
    return {
        rule.rule_id: rule
        for rule in registry.active_rules_for(["architecture"])
    }


def _read_repo_file(path_value: str) -> str:
    root = project_root().resolve()
    resolved_path = (root / path_value).resolve()
    if not resolved_path.is_relative_to(root):
        return ""
    if not resolved_path.exists() or not resolved_path.is_file():
        return ""
    return resolved_path.read_text(encoding="utf-8")


def _strip_comments(source: str) -> str:
    without_block_comments = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
    without_js_comments = re.sub(r"//.*", "", without_block_comments)
    without_hash_comments = re.sub(r"(?m)^\s*#.*$", "", without_js_comments)
    return without_hash_comments


def _import_lines(source: str) -> list[str]:
    lines: list[str] = []
    for line in _strip_comments(source).splitlines():
        stripped = line.strip()
        if stripped.startswith(("import ", "from ", "export ")):
            lines.append(stripped)
    return lines


def _path_root(path_value: str) -> str:
    normalised = path_value.replace("\\", "/")
    if "/frontend/" in normalised:
        return "frontend"
    if "/backend/" in normalised:
        return "backend"
    return "other"


def _is_service_path(path_value: str) -> bool:
    return "/backend/services/" in path_value.replace("\\", "/")


def _is_test_path(path_value: str) -> bool:
    normalised = path_value.replace("\\", "/").lower()
    return "/tests/" in normalised or normalised.endswith("_test.py") or "/__tests__/" in normalised


def _build_finding(
    *,
    rule: RuleRecord,
    area_id: str,
    standards_version: str,
    evaluated_at: str,
    title: str,
    summary: str,
    evidence: list[dict[str, str]],
    suggested_remediation: list[str],
    confidence: float,
) -> dict[str, Any]:
    finding = {
        "finding_id": f"F-{rule.rule_id}-{area_id}",
        "domain": "architecture",
        "rule_id": rule.rule_id,
        "severity": rule.severity_default,
        "status": "open",
        "title": title,
        "summary": summary,
        "evidence": evidence,
        "area_id": area_id,
        "suggested_remediation": suggested_remediation,
        "confidence": confidence,
        "detected_by": "architecture-evaluator",
        "standards_version": standards_version,
        "created_at": evaluated_at,
        "updated_at": evaluated_at,
    }
    validate_with_schema(finding, "finding.schema.json")
    return finding


def _boundary_leak_finding(
    project_area: dict[str, Any],
    *,
    rule: RuleRecord,
    standards_version: str,
    evaluated_at: str,
) -> dict[str, Any] | None:
    violations: list[str] = []
    evidence: list[dict[str, str]] = []
    for path_value in project_area["artefacts"]["code_paths"]:
        content = _read_repo_file(str(path_value))
        import_lines = _import_lines(content)
        root = _path_root(str(path_value))
        if root == "frontend" and any(marker in line for line in import_lines for marker in ("backend/services", "/backend/", "backend.")):
            violations.append(str(path_value))
            evidence.append({"path": str(path_value), "locator": "cross-boundary import marker"})
        elif root == "backend" and any(marker in line for line in import_lines for marker in ("/frontend/", "frontend/", "from frontend.", "import frontend.", "frontend.")):
            violations.append(str(path_value))
            evidence.append({"path": str(path_value), "locator": "cross-boundary import marker"})
    if not violations:
        return None
    return _build_finding(
        rule=rule,
        area_id=str(project_area["area_id"]),
        standards_version=standards_version,
        evaluated_at=evaluated_at,
        title="Code crosses bounded service roots",
        summary=(
            f"{len(violations)} file(s) reach directly across frontend/backend boundaries: "
            + ", ".join(sorted(violations))
        ),
        evidence=evidence,
        suggested_remediation=[
            "Route cross-boundary work through the approved integration seam instead of importing bounded implementation modules directly.",
        ],
        confidence=0.95,
    )


def _ui_orchestration_finding(
    project_area: dict[str, Any],
    *,
    rule: RuleRecord,
    standards_version: str,
    evaluated_at: str,
) -> dict[str, Any] | None:
    violations: list[str] = []
    evidence: list[dict[str, str]] = []
    for path_value in project_area["artefacts"]["ui_components"]:
        content = _strip_comments(_read_repo_file(str(path_value)))
        await_count = content.count("await ")
        has_branching = any(marker in content for marker in ("if (", "if ", "switch ", "try {"))
        has_backend_import = any(
            marker in line
            for line in _import_lines(content)
            for marker in ("backend/services", "/backend/", "backend.")
        )
        has_workflow_marker = any(marker in content.lower() for marker in WORKFLOW_ACTION_MARKERS)
        if has_backend_import or await_count >= 2 or (await_count >= 1 and has_branching and has_workflow_marker):
            violations.append(str(path_value))
            evidence.append({"path": str(path_value), "locator": "ui orchestration marker"})
    if not violations:
        return None
    return _build_finding(
        rule=rule,
        area_id=str(project_area["area_id"]),
        standards_version=standards_version,
        evaluated_at=evaluated_at,
        title="UI layer contains multi-step workflow orchestration",
        summary=(
            f"{len(violations)} UI file(s) coordinate workflow logic through backend imports or multiple awaited branches: "
            + ", ".join(sorted(violations))
        ),
        evidence=evidence,
        suggested_remediation=[
            "Move workflow orchestration into an action or service layer and keep UI modules focused on state binding.",
        ],
        confidence=0.92,
    )


def _ad_hoc_api_access_finding(
    project_area: dict[str, Any],
    *,
    rule: RuleRecord,
    standards_version: str,
    evaluated_at: str,
) -> dict[str, Any] | None:
    violations: list[str] = []
    evidence: list[dict[str, str]] = []
    for path_value in project_area["artefacts"]["code_paths"]:
        path_string = str(path_value)
        if _is_service_path(path_string) or _is_test_path(path_string):
            continue
        content = _strip_comments(_read_repo_file(path_string))
        matched_marker = next((marker for marker in REMOTE_ACCESS_MARKERS if marker in content), None)
        if matched_marker is None:
            continue
        violations.append(path_string)
        evidence.append({"path": path_string, "locator": matched_marker})
    if not violations:
        return None
    return _build_finding(
        rule=rule,
        area_id=str(project_area["area_id"]),
        standards_version=standards_version,
        evaluated_at=evaluated_at,
        title="Feature code uses ad hoc remote access",
        summary=(
            f"{len(violations)} non-service file(s) use direct remote-access markers outside the approved service path: "
            + ", ".join(sorted(violations))
        ),
        evidence=evidence,
        suggested_remediation=[
            "Move remote-access setup behind the approved service abstraction for the subsystem.",
        ],
        confidence=0.9,
    )


def _async_eventing_finding(
    project_area: dict[str, Any],
    *,
    rule: RuleRecord,
    standards_version: str,
    evaluated_at: str,
) -> dict[str, Any] | None:
    violations: list[str] = []
    evidence: list[dict[str, str]] = []
    for path_value in project_area["artefacts"]["code_paths"]:
        path_string = str(path_value)
        if _path_root(path_string) != "backend" or _is_test_path(path_string):
            continue
        content = _strip_comments(_read_repo_file(path_string))
        hits = [marker for marker in ASYNC_EVENT_MARKERS if marker in content]
        if not hits:
            continue
        if any(wrapper in content for wrapper in APPROVED_WRAPPER_MARKERS):
            continue
        violations.append(path_string)
        evidence.append({"path": path_string, "locator": ", ".join(hits)})
    if not violations:
        return None
    return _build_finding(
        rule=rule,
        area_id=str(project_area["area_id"]),
        standards_version=standards_version,
        evaluated_at=evaluated_at,
        title="Backend workflow mixes async or eventing style without wrapper seam",
        summary=(
            f"{len(violations)} backend service file(s) use explicit async/event markers without approved wrappers: "
            + ", ".join(sorted(violations))
        ),
        evidence=evidence,
        suggested_remediation=[
            "Route background work and event publication through the approved workflow wrapper for the subsystem.",
        ],
        confidence=0.88,
    )


def _sorted_findings(findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        findings,
        key=lambda finding: (
            SEVERITY_ORDER[str(finding["severity"])],
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


def evaluate_architecture(
    project_area: dict[str, Any],
    *,
    standards_version: str,
    evaluated_at: str | None = None,
) -> dict[str, Any]:
    validate_with_schema(project_area, "project-area.schema.json")
    timestamp = evaluated_at or _deterministic_timestamp(standards_version)
    rules = _architecture_rules()
    findings = [
        finding
        for finding in [
            _boundary_leak_finding(
                project_area,
                rule=rules["ARCH-001"],
                standards_version=standards_version,
                evaluated_at=timestamp,
            ),
            _ui_orchestration_finding(
                project_area,
                rule=rules["ARCH-002"],
                standards_version=standards_version,
                evaluated_at=timestamp,
            ),
            _ad_hoc_api_access_finding(
                project_area,
                rule=rules["ARCH-003"],
                standards_version=standards_version,
                evaluated_at=timestamp,
            ),
            _async_eventing_finding(
                project_area,
                rule=rules["ARCH-004"],
                standards_version=standards_version,
                evaluated_at=timestamp,
            ),
        ]
        if finding is not None
    ]
    sorted_findings = _sorted_findings(findings)
    return {
        "score": score_findings(sorted_findings),
        "findings": sorted_findings,
        "recommended_actions": _recommended_actions(sorted_findings),
    }
