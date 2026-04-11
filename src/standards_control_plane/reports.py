"""Markdown report and area summary generation."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .findings import FindingRecord, FindingsStore
from .resources import output_dir
from .schema_tools import validate_with_schema

LATEST_REVIEW_FILENAME = "latest-review.md"
SUBSYSTEM_REPORTS_DIRNAME = "subsystems"
AREA_SUMMARIES_DIRNAME = "area-summaries"
GENERATED_AT_PREFIX = "**Generated at:** "
OPEN_SIGNATURE_PREFIX = "<!-- open-findings-signature: "
HISTORY_SIGNATURE_PREFIX = "<!-- history-findings-signature: "
COMMENT_SUFFIX = " -->"

SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


def _review_sort_key(finding: FindingRecord) -> tuple[int, str]:
    return (
        SEVERITY_ORDER.get(finding.severity, 99),
        finding.finding_id,
    )


def _reports_dir(base_output_dir: Path | None = None) -> Path:
    root = base_output_dir or output_dir()
    return root / "reports"


def _findings_dir(base_output_dir: Path | None = None) -> Path:
    root = base_output_dir or output_dir()
    return root / "findings"


def _latest_review_path(base_output_dir: Path | None = None) -> Path:
    return _reports_dir(base_output_dir) / LATEST_REVIEW_FILENAME


def _subsystem_review_path(subsystem: str, base_output_dir: Path | None = None) -> Path:
    return _reports_dir(base_output_dir) / SUBSYSTEM_REPORTS_DIRNAME / f"{subsystem}-review.md"


def _area_summary_path(subsystem: str, base_output_dir: Path | None = None) -> Path:
    return _findings_dir(base_output_dir) / AREA_SUMMARIES_DIRNAME / f"{subsystem}.json"


def extract_generated_at(markdown: str) -> str | None:
    for line in markdown.splitlines():
        if line.startswith(GENERATED_AT_PREFIX):
            return line.removeprefix(GENERATED_AT_PREFIX).strip()
    return None


def _extract_comment_value(markdown: str, prefix: str) -> str | None:
    for line in markdown.splitlines():
        if line.startswith(prefix) and line.endswith(COMMENT_SUFFIX):
            return line.removeprefix(prefix).removesuffix(COMMENT_SUFFIX).strip()
    return None


def extract_open_signature(markdown: str) -> str | None:
    return _extract_comment_value(markdown, OPEN_SIGNATURE_PREFIX)


def extract_history_signature(markdown: str) -> str | None:
    return _extract_comment_value(markdown, HISTORY_SIGNATURE_PREFIX)


def _store_signature(store: FindingsStore) -> str:
    payload = json.dumps(store.to_dict(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def report_source_signatures(
    open_store: FindingsStore,
    history_store: FindingsStore,
) -> tuple[str, str]:
    return _store_signature(open_store), _store_signature(history_store)


def _scoped_open_findings(open_store: FindingsStore, area_id: str) -> list[FindingRecord]:
    return [
        finding
        for finding in open_store.findings
        if finding.status == "open" and finding.area_id == area_id
    ]


def _high_severity_findings(open_store: FindingsStore, area_id: str) -> list[FindingRecord]:
    findings = [
        finding
        for finding in _scoped_open_findings(open_store, area_id)
        if finding.severity in {"critical", "high"}
    ]
    return sorted(findings, key=_review_sort_key)


def _notable_improvements(
    history_store: FindingsStore,
    *,
    area_id: str,
    generated_at: str,
) -> list[FindingRecord]:
    findings = [
        finding
        for finding in history_store.findings
        if finding.area_id == area_id
        and finding.status == "resolved"
        and finding.updated_at == generated_at
    ]
    return sorted(findings, key=_review_sort_key)


def _render_findings_block(findings: list[FindingRecord], *, empty_line: str) -> list[str]:
    if not findings:
        return [empty_line]

    rendered: list[str] = []
    for finding in findings:
        evidence_paths = ", ".join(
            sorted({evidence.path for evidence in finding.evidence})
        ) or "none"
        rule_label = finding.rule_id or "no-rule"
        rendered.append(
            f"- `{finding.finding_id}` ({rule_label}) {finding.title}: {finding.summary}"
        )
        rendered.append(f"  - evidence: {evidence_paths}")
    return rendered


def _render_recommendations(actions: list[str]) -> list[str]:
    if not actions:
        return ["- none in this phase"]
    return [f"- {action}" for action in actions]


def _render_scores(audit_result: dict[str, Any]) -> list[str]:
    domain_status = audit_result.get("domain_status", {})
    scores = audit_result.get("scores", {})
    lines: list[str] = []
    if isinstance(domain_status, dict):
        for domain, status in domain_status.items():
            if not isinstance(status, dict):
                continue
            if status.get("status") == "evaluated" and domain in scores:
                lines.append(f"- {domain}: {scores[domain]}")
    return lines or ["- none"]


def render_review_markdown(
    *,
    title: str,
    audit_result: dict[str, Any],
    open_store: FindingsStore,
    history_store: FindingsStore,
) -> str:
    scope = audit_result["scope"]
    subsystem = scope["subsystem"]
    area_id = scope["area_id"]
    generated_at = audit_result["generated_at"]
    standards_version = str(generated_at).split("T", 1)[0]
    open_signature, history_signature = report_source_signatures(open_store, history_store)
    report_lines = [
        title,
        "",
        "**Status:** live audit",
        f"{GENERATED_AT_PREFIX}{generated_at}",
        f"{OPEN_SIGNATURE_PREFIX}{open_signature}{COMMENT_SUFFIX}",
        f"{HISTORY_SIGNATURE_PREFIX}{history_signature}{COMMENT_SUFFIX}",
        f"**Scope:** subsystem `{subsystem}`, area `{area_id}`, paths `{', '.join(scope['paths'])}`",
        f"**Standards version:** {standards_version}",
        "",
        "## Domain Scores",
        *_render_scores(audit_result),
        "",
        "## Top Open High-Severity Issues",
        *_render_findings_block(
            _high_severity_findings(open_store, area_id),
            empty_line="- none",
        ),
        "",
        "## Recommended Next Actions",
        *_render_recommendations(list(audit_result.get("recommended_actions", []))),
        "",
        "## Regressions",
        *(
            [f"- {item}" for item in audit_result.get("regressions", [])]
            if audit_result.get("regressions")
            else ["- none in this phase"]
        ),
        "",
        "## Notable Improvements",
        *_render_findings_block(
            _notable_improvements(
                history_store,
                area_id=area_id,
                generated_at=generated_at,
            ),
            empty_line="- none in this phase",
        ),
        "",
    ]
    return "\n".join(report_lines)


def build_area_summary(
    audit_result: dict[str, Any],
    open_store: FindingsStore,
) -> dict[str, Any]:
    scope = audit_result["scope"]
    summary = {
        "area_id": scope["area_id"],
        "subsystem": scope["subsystem"],
        "scores": audit_result["scores"],
        "open_findings_count": len(_scoped_open_findings(open_store, scope["area_id"])),
        "updated_at": audit_result["generated_at"],
    }
    validate_with_schema(summary, "area-summary.schema.json")
    return summary


def _stage_text(target_path: Path, content: str) -> Path:
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=target_path.parent,
        delete=False,
        prefix=f".{target_path.name}.",
        suffix=".tmp",
    ) as handle:
        handle.write(content)
        return Path(handle.name)


def _stage_json(target_path: Path, payload: dict[str, Any]) -> Path:
    validate_with_schema(payload, "area-summary.schema.json")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=target_path.parent,
        delete=False,
        prefix=f".{target_path.name}.",
        suffix=".tmp",
    ) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
        return Path(handle.name)


def _stage_backup(target_path: Path) -> Path | None:
    if not target_path.exists():
        return None
    with NamedTemporaryFile(
        mode="wb",
        dir=target_path.parent,
        delete=False,
        prefix=f".{target_path.name}.",
        suffix=".bak",
    ) as handle:
        handle.write(target_path.read_bytes())
        return Path(handle.name)


def _cleanup(path: Path | None) -> None:
    if path is not None and path.exists():
        path.unlink()


def _write_artifacts_atomic(targets: list[tuple[Path, str | dict[str, Any]]]) -> None:
    staged: list[tuple[Path, Path]] = []
    backups: list[tuple[Path, Path | None]] = []
    for target_path, payload in targets:
        if isinstance(payload, str):
            staged_path = _stage_text(target_path, payload)
        else:
            staged_path = _stage_json(target_path, payload)
        staged.append((target_path, staged_path))
        backups.append((target_path, _stage_backup(target_path)))

    try:
        for target_path, staged_path in staged:
            os.replace(staged_path, target_path)
    except Exception:
        for target_path, backup_path in backups:
            if backup_path is not None:
                os.replace(backup_path, target_path)
            elif target_path.exists():
                target_path.unlink()
        raise
    finally:
        for _, staged_path in staged:
            _cleanup(staged_path)
        for _, backup_path in backups:
            _cleanup(backup_path)


def write_audit_reports(
    audit_result: dict[str, Any],
    *,
    open_store: FindingsStore,
    history_store: FindingsStore,
    base_output_dir: Path | None = None,
) -> tuple[Path, Path, Path]:
    scope = audit_result["scope"]
    subsystem = scope["subsystem"]
    latest_review = render_review_markdown(
        title="# Standards Control Plane — Latest Review",
        audit_result=audit_result,
        open_store=open_store,
        history_store=history_store,
    )
    subsystem_review = render_review_markdown(
        title=f"# Standards Control Plane — {subsystem.title()} Review",
        audit_result=audit_result,
        open_store=open_store,
        history_store=history_store,
    )
    area_summary = build_area_summary(audit_result, open_store)

    latest_path = _latest_review_path(base_output_dir)
    subsystem_path = _subsystem_review_path(subsystem, base_output_dir)
    area_summary_path = _area_summary_path(subsystem, base_output_dir)
    _write_artifacts_atomic(
        [
            (latest_path, latest_review),
            (subsystem_path, subsystem_review),
            (area_summary_path, area_summary),
        ]
    )
    return latest_path, subsystem_path, area_summary_path
