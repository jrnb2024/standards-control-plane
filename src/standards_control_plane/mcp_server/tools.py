"""MCP tool implementations for the Standards Control Plane."""

from __future__ import annotations

import fcntl
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
import unicodedata
from collections import OrderedDict
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from standards_control_plane.consult import build_consult_response
from standards_control_plane.registry import SUPPORTED_DOMAINS, RegistrySnapshot, load_registry
from standards_control_plane.resources import output_dir, project_root

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

SCHEMA_VERSION = "1.0.0"
DEFAULT_AUDIT_TIMEOUT_SECONDS = 120
DEFAULT_AUDIT_CACHE_TTL_SECONDS = 3600
DEFAULT_AUDIT_CACHE_MAX_ENTRIES = 256
DEFAULT_AUDIT_DIFF_CAP = 500
DEFAULT_BASE_REF = "HEAD~1"
DEFAULT_HEAD_REF = "HEAD"
DEFAULT_GIT_OPERATION_TIMEOUT_SECONDS = 30
ERROR_CATALOG_PATH = "docs/integrations/mcp-error-codes.md"
DEFAULT_DECISIONS_PATH = project_root() / "docs" / "DECISIONS.md"
DEFAULT_WAIVERS_PATH = output_dir() / "findings" / "waivers.json"
DEFAULT_FINDINGS_DIR = output_dir() / "findings"
DEFAULT_PROPOSALS_ROOT = project_root() / "docs" / "reviews" / "proposals"
TOOL_LOGGER = logging.getLogger("standards_control_plane.mcp.tools")

_PROPOSAL_ID_PATTERN = re.compile(r"^PROP-(\d{3,})\.md$")
_PROPOSAL_METADATA_PATTERN = re.compile(r"<!--\s*proposal_metadata:\s*(\{.*?\})\s*-->", re.DOTALL)
_PROPOSAL_FRONT_MATTER_PATTERN = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
_SIGNING_KEY_LINE_PATTERN = re.compile(
    r"^ssh-ed25519\s+\S+(?P<metadata>.*?)(?:\s+#.*)?$",
)
_MARKDOWN_LINK_PATTERN = re.compile(r"!\[([^\]]*)\]\([^)]+\)|\[([^\]]+)\]\([^)]+\)")
_MARKDOWN_AUTOLINK_PATTERN = re.compile(r"<([^>\s]+)>")
_MARKDOWN_LINE_MARKER_PATTERN = re.compile(r"(?m)^\s{0,3}(?:#{1,6}|>+|[*+-]|\d+[.)])\s*")
_MARKDOWN_EMPHASIS_PATTERN = re.compile(r"[*_~`]+")
_MARKDOWN_TABLE_RULE_PATTERN = re.compile(r"(?m)^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*$")
_AUDIT_CHANGED_CACHE: OrderedDict[str, tuple[float, "AuditChangedResponse"]] = OrderedDict()
_AUDIT_CHANGED_CACHE_LOCK = threading.Lock()
_PROPOSAL_LOCK = threading.Lock()
_PROPOSAL_RATE_LIMIT = 10
_PROPOSAL_RATE_LIMIT_WINDOW = timedelta(hours=1)
_PROPOSAL_DEDUPE_WINDOW = timedelta(hours=24)
_PROPOSAL_HASH_LRU_LIMIT = 1024
_PROPOSAL_SCAN_LIMIT = 2048
_PROPOSAL_TITLE_MAX_LENGTH = 500
_PROPOSAL_BODY_MAX_LENGTH = 65536


class ToolModel(BaseModel):
    """Shared Pydantic configuration for MCP tool models."""

    model_config = ConfigDict(extra="forbid")


class SchemaVersionedResponse(ToolModel):
    """Base response model for MCP tool outputs."""

    schema_version: Literal["1.0.0"] = SCHEMA_VERSION


class ErrorResponse(SchemaVersionedResponse):
    """Structured MCP error response."""

    error_code: str
    message: str
    remediation_url: str


class ConsultApprovedPattern(ToolModel):
    pattern_id: str
    reason: str


class ConsultFindingSummary(ToolModel):
    finding_id: str
    severity: str
    summary: str
    confidence_class: str


class HistoricalReviewSummary(ToolModel):
    review_id: str
    path: str
    summary: str


class ApplicableRuleSummary(ToolModel):
    rule_id: str
    reason: str


class ConsultRulesRequest(ToolModel):
    domain: str = Field(min_length=1)
    subsystem: str | None = None
    area_id: str | None = None


class ConsultRulesResponse(SchemaVersionedResponse):
    request_id: str
    domains: list[str]
    approved_patterns: list[ConsultApprovedPattern]
    open_findings: list[ConsultFindingSummary]
    historical_reviews: list[HistoricalReviewSummary]
    applicable_rules: list[ApplicableRuleSummary]
    guidance: list[str]
    risks: list[str]
    confidence: float
    confidence_class: str


class CheckWaiverRequest(ToolModel):
    rule_id: str = Field(min_length=1)
    scope: str | None = None


class WaiverMatch(ToolModel):
    waiver_id: str
    finding_id: str
    rule_id: str
    scope: str | None = None
    reason: str
    approved_by: str
    expires_at: str
    created_at: str | None = None


class CheckWaiverResponse(SchemaVersionedResponse):
    rule_id: str
    scope: str | None = None
    active_waivers: list[WaiverMatch]


class ListOpenDecisionsRequest(ToolModel):
    since: str | None = None


class DecisionRecord(ToolModel):
    decision_id: str
    date: str
    decision: str
    status: str
    rationale: str


class ListOpenDecisionsResponse(SchemaVersionedResponse):
    decisions: list[DecisionRecord]


class CheckFindingRequest(ToolModel):
    finding_id: str = Field(min_length=1)


class CheckFindingResponse(SchemaVersionedResponse):
    finding: dict[str, Any]


class AuditChangedRequest(ToolModel):
    base_ref: str | None = None
    head_ref: str | None = None


class AuditChangedResponse(SchemaVersionedResponse):
    base_ref: str
    head_ref: str
    changed_paths: list[str]
    audit_result: dict[str, Any]


class ResolveDomainRequest(ToolModel):
    changed_files: list[str]


class ResolveDomainResponse(SchemaVersionedResponse):
    domains: list[str]
    confidence: float


class ProposeRequest(ToolModel):
    title: str = Field(min_length=1, max_length=_PROPOSAL_TITLE_MAX_LENGTH)
    body: str = Field(min_length=1, max_length=_PROPOSAL_BODY_MAX_LENGTH)
    affected_repos: list[str]
    rule_id: str | None = None


class ProposeResponse(SchemaVersionedResponse):
    proposal_id: str
    branch: str
    path: str
    pr_url_if_pushed: str | None = None
    adjudication_status: Literal["queued_no_adjudicator"]
    expected_review_date: None = None


# WP-SCP-023 023D / D-043: scp.consult_scorecard MCP method.
# Read-only consult method returning aggregated metrics from
# `output/scorecards/index.json`. NEVER returns waiver content
# (`reason` / `approved_by` / `waiver_id` strings) — invariant 2 of
# WP-SCP-023 plan-doc; enforced by Pydantic models below
# (extra='forbid' via ToolModel + explicit field whitelist).
class ConsultScorecardRequest(ToolModel):
    repo_filter: str | None = Field(
        default=None,
        pattern=r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$",
        description="Optional repo filter (owner/name). Omit for all adopters.",
    )
    since_emitted_at: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2}))?$",
        description="ISO-8601 date or RFC3339 datetime; only verified rows with last_emit_emitted_at >= this value are returned.",
    )


class ConsultScorecardRuleCount(ToolModel):
    rule_id: str = Field(pattern=r"^SCP-R-[0-9]+$")
    raw_findings: int = Field(ge=0)
    denies: int = Field(ge=0)
    waived: int = Field(ge=0)
    rule_config_disabled: bool


class ConsultScorecardWaiversAggregate(ToolModel):
    """Aggregated waivers — counts only; NEVER carries waiver content."""

    active_count: int = Field(ge=0)
    by_rule_id: dict[str, int]
    expiring_within_30d: int = Field(ge=0)


class ConsultScorecardRuleConfigAggregate(ToolModel):
    """Aggregated rule-config disable state — rule_ids only; NEVER justification text."""

    disabled_rules: list[str]
    expiring_within_30d: int = Field(ge=0)


class ConsultScorecardAdopterRow(ToolModel):
    """Per-adopter row in the consult_scorecard response.

    Mirrors the index schema's per-adopter shape but limited to
    fields that are safe to expose via MCP. NEVER includes
    `reason`/`approved_by`/`waiver_id` (none of those exist in the
    index either; this is defence-in-depth at the MCP boundary).
    """

    repo: str
    status: Literal["verified", "verification_failure", "unreachable", "no_emit"]
    verdict: Literal["allow", "deny", "warn"] | None = None
    scp_version: str | None = None
    last_emit_emitted_at: str | None = None
    last_emit_run_id: int | None = None
    last_emit_commit: str | None = None
    ref: str | None = None
    rule_counts: list[ConsultScorecardRuleCount] = Field(default_factory=list)
    waivers_aggregate: ConsultScorecardWaiversAggregate | None = None
    rule_config_aggregate: ConsultScorecardRuleConfigAggregate | None = None
    error: str | None = None


class ConsultScorecardResponse(SchemaVersionedResponse):
    aggregated_at: str
    aggregator_run_id: int = Field(ge=0)
    adopters: list[ConsultScorecardAdopterRow]
    request_filters_applied: dict[str, str | None]


def _scorecard_index_path() -> Path:
    """Resolve the live scorecard index path inside the SCP repo."""

    return project_root() / "output" / "scorecards" / "index.json"


def _consult_scorecard_filter_since(emit_at: str | None, since: str | None) -> bool:
    if since is None or emit_at is None:
        return True
    try:
        since_dt = _normalise_iso8601(since)
        emit_dt = _normalise_iso8601(emit_at)
    except (ValueError, TypeError):
        # Malformed timestamp — keep the row (don't silently drop). The
        # caller-side filter is best-effort.
        return True
    return emit_dt >= since_dt


def consult_scorecard_impl(request: ConsultScorecardRequest) -> ConsultScorecardResponse | ErrorResponse:
    index_path = _scorecard_index_path()
    if not index_path.is_file():
        return _error(
            "SCP-MCP-SCORECARD-001",
            f"scorecard index not found at {index_path} — has the WP-SCP-023 023C aggregator workflow run yet?",
        )
    try:
        index = json.loads(index_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        return _error(
            "SCP-MCP-SCORECARD-002",
            f"could not read/parse scorecard index: {type(exc).__name__}: {str(exc)[:300]}",
        )

    # Closes 023D R1 COR-MAJ-001: drop indexes with unknown
    # schema_version per the index schema's documented consumer
    # contract. Future schema bumps require updating the supported
    # set; until then, an unknown version is an error rather than a
    # silent drift.
    _SUPPORTED_INDEX_SCHEMA_VERSIONS = {"0.1"}
    index_schema_version = index.get("schema_version")
    if index_schema_version not in _SUPPORTED_INDEX_SCHEMA_VERSIONS:
        return _error(
            "SCP-MCP-SCORECARD-004",
            f"unsupported scorecard-index schema_version "
            f"{index_schema_version!r}; supported: "
            f"{sorted(_SUPPORTED_INDEX_SCHEMA_VERSIONS)}",
        )

    raw_adopters = index.get("adopters", [])
    if not isinstance(raw_adopters, list):
        return _error(
            "SCP-MCP-SCORECARD-003",
            "scorecard index `adopters` is not a list — index is malformed",
        )

    rows: list[ConsultScorecardAdopterRow] = []
    for raw in raw_adopters:
        if not isinstance(raw, dict):
            continue
        if request.repo_filter is not None and raw.get("repo") != request.repo_filter:
            continue
        if not _consult_scorecard_filter_since(raw.get("last_emit_emitted_at"), request.since_emitted_at):
            continue
        # Build rule_counts list from the dict shape in the index.
        rc_list: list[ConsultScorecardRuleCount] = []
        rc_dict = raw.get("rule_counts", {}) or {}
        for rule_id in sorted(rc_dict.keys()):
            entry = rc_dict[rule_id]
            if not isinstance(entry, dict):
                continue
            try:
                rc_list.append(
                    ConsultScorecardRuleCount(
                        rule_id=rule_id,
                        raw_findings=int(entry.get("raw_findings", 0)),
                        denies=int(entry.get("denies", 0)),
                        waived=int(entry.get("waived", 0)),
                        rule_config_disabled=bool(entry.get("rule_config_disabled", False)),
                    )
                )
            except (ValidationError, ValueError, TypeError):
                continue

        waivers_agg = None
        wa = raw.get("waivers_aggregate")
        if isinstance(wa, dict):
            try:
                waivers_agg = ConsultScorecardWaiversAggregate(
                    active_count=int(wa.get("active_count", 0)),
                    by_rule_id={k: int(v) for k, v in (wa.get("by_rule_id", {}) or {}).items()},
                    expiring_within_30d=int(wa.get("expiring_within_30d", 0)),
                )
            except (ValidationError, ValueError, TypeError):
                waivers_agg = None

        rc_agg = None
        ra = raw.get("rule_config_aggregate")
        if isinstance(ra, dict):
            try:
                rc_agg = ConsultScorecardRuleConfigAggregate(
                    disabled_rules=list(ra.get("disabled_rules", []) or []),
                    expiring_within_30d=int(ra.get("expiring_within_30d", 0)),
                )
            except (ValidationError, ValueError, TypeError):
                rc_agg = None

        try:
            row = ConsultScorecardAdopterRow(
                repo=str(raw.get("repo", "")),
                status=raw.get("status", "no_emit"),
                verdict=raw.get("verdict"),
                scp_version=raw.get("scp_version"),
                last_emit_emitted_at=raw.get("last_emit_emitted_at"),
                last_emit_run_id=raw.get("last_emit_run_id"),
                last_emit_commit=raw.get("last_emit_commit"),
                ref=raw.get("ref"),
                rule_counts=rc_list,
                waivers_aggregate=waivers_agg,
                rule_config_aggregate=rc_agg,
                error=raw.get("error"),
            )
        except ValidationError:
            continue
        rows.append(row)

    return ConsultScorecardResponse(
        aggregated_at=str(index.get("aggregated_at", "")),
        aggregator_run_id=int(index.get("aggregator_run_id", 0)),
        adopters=rows,
        request_filters_applied={
            "repo_filter": request.repo_filter,
            "since_emitted_at": request.since_emitted_at,
        },
    )


def consult_scorecard(request: ConsultScorecardRequest) -> ConsultScorecardResponse | ErrorResponse:
    _log_tool_invocation("consult_scorecard", request)
    return consult_scorecard_impl(request)


def _tool_params_hash(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _log_tool_invocation(tool_name: str, request: ToolModel) -> None:
    TOOL_LOGGER.info(
        "tool_name=%s params_hash=%s key_id=%s",
        tool_name,
        _tool_params_hash(request.model_dump(mode="json")),
        "pending_021J",
    )


def _error(code: str, message: str) -> ErrorResponse:
    return ErrorResponse(
        error_code=code,
        message=message,
        remediation_url=f"{ERROR_CATALOG_PATH}#{code.lower()}",
    )


def _normalise_iso8601(value: str) -> datetime:
    normalised = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", normalised):
        return datetime.fromisoformat(f"{normalised}T00:00:00+00:00")
    return datetime.fromisoformat(normalised.replace("Z", "+00:00"))


def _timeout_error(timeout_seconds: int) -> ErrorResponse:
    return _error(
        "SCP-MCP-E011",
        f"audit-changed exceeded the {timeout_seconds}-second wall-clock timeout",
    )


def _remaining_timeout_seconds(start_time: float, timeout_seconds: int) -> float:
    remaining = timeout_seconds - (time.monotonic() - start_time)
    if remaining <= 0:
        raise subprocess.TimeoutExpired(cmd=["audit-changed"], timeout=timeout_seconds)
    return remaining


def _run_git_command(
    command: list[str],
    *,
    repo_root: Path,
    timeout_seconds: float,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        check=False,
        text=True,
        timeout=timeout_seconds,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        stdout = completed.stdout.strip()
        raise RuntimeError(stderr or stdout or f"{' '.join(command)} failed without output")
    return completed


def _ensure_supported_domain(domain: str) -> str | ErrorResponse:
    candidate = domain.strip()
    if not candidate:
        return _error("SCP-MCP-E021", "domain must be a non-empty supported domain")
    if candidate not in SUPPORTED_DOMAINS:
        return _error(
            "SCP-MCP-E021",
            f"unsupported domain '{candidate}'; expected one of {', '.join(SUPPORTED_DOMAINS)}",
        )
    return candidate


def _ensure_valid_subsystem(subsystem: str | None) -> str | None | ErrorResponse:
    if subsystem is None:
        return None
    candidate = subsystem.strip()
    if not candidate:
        return None
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", candidate):
        return _error(
            "SCP-MCP-E021",
            "subsystem must match ^[a-z0-9][a-z0-9-]*$ when provided",
        )
    return candidate


def _decision_since_filter(value: str | None) -> date | ErrorResponse | None:
    if value is None:
        return None
    try:
        return _normalise_iso8601(value).date()
    except ValueError:
        return _error("SCP-MCP-E021", f"since must be valid ISO-8601, got '{value}'")


def _findings_json_paths(findings_dir: Path) -> list[Path]:
    if not findings_dir.exists():
        return []
    return sorted(path for path in findings_dir.rglob("*.json") if path.is_file())


def _iter_finding_payloads(findings_dir: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in _findings_json_paths(findings_dir):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        findings.extend(_extract_finding_objects(payload))
    return findings


def _extract_finding_objects(payload: Any) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        if {"finding_id", "domain", "severity", "summary"}.issubset(payload):
            findings.append(payload)
        nested = payload.get("findings")
        if isinstance(nested, list):
            for item in nested:
                findings.extend(_extract_finding_objects(item))
    elif isinstance(payload, list):
        for item in payload:
            findings.extend(_extract_finding_objects(item))
    return findings


def _finding_index(findings_dir: Path) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for finding in _iter_finding_payloads(findings_dir):
        finding_id = finding.get("finding_id")
        if isinstance(finding_id, str) and finding_id not in index:
            index[finding_id] = finding
    return index


def _load_waiver_entries(waivers_path: Path) -> list[dict[str, Any]]:
    if not waivers_path.exists():
        return []
    payload = json.loads(waivers_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("waivers.json must contain a JSON list")
    return [entry for entry in payload if isinstance(entry, dict)]


def _parse_decisions_table(decisions_path: Path) -> list[DecisionRecord]:
    rows: list[DecisionRecord] = []
    for line in decisions_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 5:
            continue
        if cells[0] in {"ID", "----"} or set(cells[0]) == {"-"}:
            continue
        if not re.fullmatch(r"D-\d{3}", cells[0]):
            continue
        rows.append(
            DecisionRecord(
                decision_id=cells[0],
                date=cells[1],
                decision=cells[2],
                status=cells[3],
                rationale=cells[4],
            )
        )
    return rows


def _registry_exact_path_map(registry_snapshot: RegistrySnapshot) -> dict[str, set[str]]:
    root = project_root().resolve()
    exact: dict[str, set[str]] = {}
    for domain_name, domain_registry in registry_snapshot.domains.items():
        for record in [*domain_registry.rules, *domain_registry.patterns]:
            relative = str(record.source_path.resolve().relative_to(root)).replace("\\", "/")
            exact.setdefault(relative, set()).add(domain_name)
    return exact


def _fuzzy_domains_for_path(path_value: str) -> set[str]:
    path = path_value.replace("\\", "/").lower().strip("/")
    domains: set[str] = set()
    suffixes = (".tsx", ".jsx", ".ts", ".js", ".css", ".scss", ".html")

    if path.startswith("docs/") or path.endswith((".md", ".rst", ".txt")):
        domains.add("governance")
    if path.endswith(suffixes) or "/frontend/" in path or path.startswith("frontend/") or "/app/" in path:
        domains.update({"architecture", "ux", "design", "product"})
    if path.endswith(("services.yml", "service.yml")) or "/health" in path or "auth" in path:
        domains.add("service-lifecycle")
    if any(token in path for token in ("/backend/", "/api/", "/service/", "/worker/")):
        domains.add("architecture")
    return domains


def _audit_cache_key(base_ref: str, head_ref: str) -> str:
    return hashlib.sha256(f"{base_ref}\0{head_ref}".encode("utf-8")).hexdigest()


def _resolve_git_commit(
    ref: str,
    *,
    repo_root: Path,
    timeout_seconds: float,
) -> str:
    completed = _run_git_command(
        ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
        repo_root=repo_root,
        timeout_seconds=timeout_seconds,
    )
    commit_sha = completed.stdout.strip()
    if not commit_sha:
        raise ValueError(f"git rev-parse returned an empty commit SHA for '{ref}'")
    return commit_sha


def _list_changed_files_with_timeout(
    *,
    base_ref: str,
    head_ref: str,
    repo_root: Path,
    timeout_seconds: float,
) -> list[str]:
    completed = _run_git_command(
        [
            "git",
            "diff",
            "--name-only",
            "--diff-filter=ACMR",
            base_ref,
            head_ref,
        ],
        repo_root=repo_root,
        timeout_seconds=timeout_seconds,
    )
    changed_paths: list[str] = []
    seen: set[str] = set()
    for line in completed.stdout.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        resolved = (repo_root / candidate).resolve()
        if not resolved.is_relative_to(repo_root):
            raise ValueError(f"Changed path escapes repo boundary: {candidate}")
        if not resolved.exists():
            continue
        relative = str(resolved.relative_to(repo_root)).replace("\\", "/")
        if relative not in seen:
            seen.add(relative)
            changed_paths.append(relative)
    return sorted(changed_paths)


def _prune_audit_changed_cache(
    *,
    current_time: float,
    max_entries: int,
) -> None:
    expired_keys = [key for key, (expires_at, _) in _AUDIT_CHANGED_CACHE.items() if expires_at <= current_time]
    for key in expired_keys:
        _AUDIT_CHANGED_CACHE.pop(key, None)
    while len(_AUDIT_CHANGED_CACHE) > max_entries:
        _AUDIT_CHANGED_CACHE.popitem(last=False)


def _run_audit_changed_cli(
    *,
    base_ref: str,
    head_ref: str,
    domains: list[str],
    timeout_seconds: float,
) -> dict[str, Any]:
    command = [
        sys.executable,
        "-m",
        "standards_control_plane.cli",
        "audit-changed",
        "--base-ref",
        base_ref,
        "--head-ref",
        head_ref,
        "--domains",
        ",".join(domains),
        "--subsystem",
        project_root().name,
        "--standards-version",
        load_registry().version,
    ]
    completed = subprocess.run(
        command,
        cwd=project_root(),
        capture_output=True,
        check=False,
        text=True,
        timeout=timeout_seconds,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        stdout = completed.stdout.strip()
        raise RuntimeError(stderr or stdout or "audit-changed CLI failed without output")
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise ValueError("audit-changed CLI returned a non-object JSON payload")
    return payload


def _strip_markdown_markers(text: str) -> str:
    without_links = _MARKDOWN_LINK_PATTERN.sub(lambda match: match.group(1) or match.group(2) or " ", text)
    without_autolinks = _MARKDOWN_AUTOLINK_PATTERN.sub(r"\1", without_links)
    without_line_markers = _MARKDOWN_LINE_MARKER_PATTERN.sub("", without_autolinks)
    without_table_rules = _MARKDOWN_TABLE_RULE_PATTERN.sub(" ", without_line_markers)
    without_emphasis = _MARKDOWN_EMPHASIS_PATTERN.sub(" ", without_table_rules)
    return without_emphasis.translate(str.maketrans({"[": " ", "]": " ", "(": " ", ")": " ", "|": " "}))


def _normalise_proposal_body(body: str) -> str:
    if "\x00" in body:
        raise ValueError("proposal content must not contain NUL bytes")
    normalised = unicodedata.normalize("NFKC", _strip_markdown_markers(body)).casefold()
    collapsed = "".join(
        " "
        if character.isspace() or unicodedata.category(character) in {"Cc", "Cf", "Cs"}
        else character
        for character in normalised
    )
    return " ".join(collapsed.split())


def _proposal_hash(body: str) -> str:
    return hashlib.sha256(_normalise_proposal_body(body).encode("utf-8")).hexdigest()


def _next_proposal_id(proposals_root: Path) -> str:
    highest = 0
    for path in proposals_root.glob("PROP-*.md"):
        match = _PROPOSAL_ID_PATTERN.match(path.name)
        if match is None:
            continue
        highest = max(highest, int(match.group(1)))
    return f"PROP-{highest + 1:03d}"


def _parse_proposal_front_matter(text: str) -> dict[str, str]:
    match = _PROPOSAL_FRONT_MATTER_PATTERN.match(text)
    if match is None:
        return {}
    payload: dict[str, str] = {}
    for line in match.group("body").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        payload[key.strip()] = value.strip()
    return payload


def _parse_proposal_metadata(text: str) -> dict[str, Any]:
    match = _PROPOSAL_METADATA_PATTERN.search(text)
    if match is None:
        return {}
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _iter_existing_proposals(
    proposals_root: Path,
    *,
    max_records: int = _PROPOSAL_SCAN_LIMIT,
) -> list[dict[str, Any]]:
    candidate_paths: list[tuple[int, Path]] = []
    for path in proposals_root.glob("PROP-*.md"):
        match = _PROPOSAL_ID_PATTERN.match(path.name)
        if match is None:
            continue
        candidate_paths.append((int(match.group(1)), path))

    records: list[dict[str, Any]] = []
    for _, path in sorted(candidate_paths, reverse=True)[:max_records]:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        front_matter = _parse_proposal_front_matter(text)
        metadata = _parse_proposal_metadata(text)
        queued_at_raw = front_matter.get("queued_at")
        try:
            queued_at = _normalise_iso8601(queued_at_raw) if queued_at_raw else None
        except ValueError:
            queued_at = None
        records.append(
            {
                "proposal_id": path.stem,
                "path": path,
                "branch_name": f"proposals/{path.stem}",
                "queued_at": queued_at,
                "caller_id": metadata.get("caller_id"),
                "proposal_hash": metadata.get("proposal_hash"),
            }
        )
    records.sort(
        key=lambda record: record["queued_at"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )
    return records


def _recent_proposal_hashes(proposals_root: Path) -> OrderedDict[str, datetime]:
    recent_hashes: OrderedDict[str, datetime] = OrderedDict()
    for record in _iter_existing_proposals(proposals_root):
        proposal_hash = record.get("proposal_hash")
        queued_at = record.get("queued_at")
        if not isinstance(proposal_hash, str) or not isinstance(queued_at, datetime):
            continue
        if proposal_hash in recent_hashes:
            continue
        recent_hashes[proposal_hash] = queued_at
        if len(recent_hashes) >= _PROPOSAL_HASH_LRU_LIMIT:
            break
    return recent_hashes


def _proposal_rate_limit_exceeded(
    *,
    proposals_root: Path,
    caller_id: str,
    now: datetime,
) -> bool:
    cutoff = now - _PROPOSAL_RATE_LIMIT_WINDOW
    recent_count = 0
    for record in _iter_existing_proposals(proposals_root):
        queued_at = record.get("queued_at")
        if not isinstance(queued_at, datetime) or queued_at < cutoff:
            break
        if record.get("caller_id") != caller_id:
            continue
        recent_count += 1
        if recent_count >= _PROPOSAL_RATE_LIMIT:
            return True
    return False


def _proposal_is_duplicate(
    *,
    proposals_root: Path,
    proposal_hash: str,
    now: datetime,
) -> bool:
    queued_at = _recent_proposal_hashes(proposals_root).get(proposal_hash)
    return isinstance(queued_at, datetime) and queued_at >= now - _PROPOSAL_DEDUPE_WINDOW


def _stdio_caller_id() -> str:
    executable_path = Path(sys.argv[0]).resolve() if sys.argv and sys.argv[0].strip() else Path.cwd().resolve()
    return f"stdio:{os.getpid()}:{executable_path}"


def _current_signing_key_id(repo_root: Path) -> str:
    key_ring_path = repo_root / "docs" / "security" / "mcp-signing-keys.pub"
    if not key_ring_path.exists():
        raise ValueError(
            "signing key ring not configured at docs/security/mcp-signing-keys.pub; "
            "cannot record signing_key_id - provision a key ring before using propose()"
        )
    try:
        text = key_ring_path.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(
            "signing key ring not configured at docs/security/mcp-signing-keys.pub; "
            "cannot record signing_key_id - provision a key ring before using propose()"
        ) from error
    for line in text.splitlines():
        match = _SIGNING_KEY_LINE_PATTERN.match(line.strip())
        if match is None:
            continue
        metadata = {
            token.split("=", 1)[0]: token.split("=", 1)[1]
            for token in match.group("metadata").split()
            if "=" in token
        }
        if metadata.get("current", "").lower() not in {"1", "true", "yes"}:
            continue
        key_id = metadata.get("key_id") or metadata.get("key-id")
        if key_id:
            return key_id
    raise ValueError(
        "signing key ring not configured at docs/security/mcp-signing-keys.pub; "
        "cannot record signing_key_id - provision a key ring before using propose()"
    )


def _proposal_relative_path(*, proposal_path: Path, repo_root: Path) -> str:
    return str(proposal_path.resolve().relative_to(repo_root.resolve())).replace("\\", "/")


def _proposal_markdown(
    *,
    proposal_id: str,
    branch_name: str,
    proposal_hash: str,
    title: str,
    body: str,
    affected_repos: list[str],
    rule_id: str | None,
    queued_at: str,
    caller_id: str,
    signing_key_id: str,
) -> str:
    metadata_comment = json.dumps(
        {
            "proposal_hash": proposal_hash,
            "mcp_origin": True,
            "caller_id": caller_id,
            "signing_key_id": signing_key_id,
            "affected_repos": affected_repos,
            "rule_id": rule_id,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    rule_block = rule_id or "null"
    affected_repo_lines = affected_repos or ["(none declared)"]
    return "\n".join(
        [
            "---",
            "adjudication_status: queued_no_adjudicator",
            "expected_review_date: null",
            f"queued_at: {queued_at}",
            "---",
            "> NOTE: WP-SCP-022-proposal-queue adjudication workflow is not yet live;",
            "> proposals queue until adjudication ships. Status updates via",
            f"> GitHub issue on this branch ({branch_name}). See",
            "> docs/plans/WP-SCP-022-implementation-programme-plan.md §12.",
            "",
            f"<!-- proposal_metadata: {metadata_comment} -->",
            "",
            f"# {proposal_id}: {title}",
            "",
            "## Proposal Envelope",
            "- mcp_origin: true",
            f"- caller_id: {caller_id}",
            f"- signing_key_id: {signing_key_id}",
            "",
            "## Affected Repositories",
            *[f"- {repo}" for repo in affected_repo_lines],
            "",
            "## Rule Context",
            rule_block,
            "",
            "## Proposal Body",
            body.strip(),
            "",
        ]
    )


def _proposal_branch_exists(
    *,
    repo_root: Path,
    branch_name: str,
) -> bool:
    completed = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"],
        cwd=repo_root,
        capture_output=True,
        check=False,
        text=True,
        timeout=DEFAULT_GIT_OPERATION_TIMEOUT_SECONDS,
    )
    return completed.returncode == 0


def _remove_orphaned_duplicate_proposals(
    *,
    proposals_root: Path,
    repo_root: Path,
    proposal_hash: str,
) -> None:
    for record in _iter_existing_proposals(proposals_root):
        if record.get("proposal_hash") != proposal_hash:
            continue
        proposal_path = record.get("path")
        branch_name = record.get("branch_name")
        if not isinstance(proposal_path, Path) or not isinstance(branch_name, str):
            continue
        if _proposal_branch_exists(repo_root=repo_root, branch_name=branch_name):
            continue
        proposal_path.unlink(missing_ok=True)


@contextmanager
def _proposal_creation_guard(proposals_root: Path) -> Any:
    proposals_root.mkdir(parents=True, exist_ok=True)
    lock_path = proposals_root / ".proposal.lock"
    with _PROPOSAL_LOCK:
        with lock_path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _create_proposal_branch(
    *,
    repo_root: Path,
    branch_name: str,
    base_commit: str,
) -> None:
    _run_git_command(
        ["git", "branch", branch_name, base_commit],
        repo_root=repo_root,
        timeout_seconds=DEFAULT_GIT_OPERATION_TIMEOUT_SECONDS,
    )


def _write_new_proposal_file(proposal_path: Path, proposal_body: str) -> None:
    file_descriptor = os.open(
        proposal_path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o644,
    )
    with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
        handle.write(proposal_body)


def consult_rules_impl(
    request: ConsultRulesRequest,
    *,
    registry_snapshot: RegistrySnapshot | None = None,
) -> ConsultRulesResponse | ErrorResponse:
    domain = _ensure_supported_domain(request.domain)
    if isinstance(domain, ErrorResponse):
        return domain
    subsystem = _ensure_valid_subsystem(request.subsystem)
    if isinstance(subsystem, ErrorResponse):
        return subsystem

    area_id = (request.area_id or subsystem or f"{domain}-consult").strip()
    registry = registry_snapshot or load_registry()
    domain_registry = registry.domains.get(domain)
    representative_paths = [
        str(domain_registry.rules[0].source_path.resolve().relative_to(project_root())).replace("\\", "/")
    ] if domain_registry is not None and domain_registry.rules else []
    payload: dict[str, Any] = {
        "mode": "consult",
        "question": f"Consult rules for domain '{domain}'.",
        "domains": [domain],
        "area_id": area_id,
        "paths": representative_paths,
    }
    if subsystem is not None:
        payload["task_context"] = {
            "subsystem": subsystem,
            "feature_summary": f"MCP consult for subsystem {subsystem}.",
        }
    try:
        response = build_consult_response(
            payload,
            registry_snapshot=registry,
        )
        return ConsultRulesResponse.model_validate({"schema_version": SCHEMA_VERSION, **response})
    except (ValidationError, ValueError, TypeError) as error:
        return _error("SCP-MCP-E021", f"consult response schema mismatch: {error}")
    except Exception as error:
        return _error("SCP-MCP-E021", f"unable to assemble consult response: {error}")


def check_waiver_impl(
    request: CheckWaiverRequest,
    *,
    waivers_path: Path = DEFAULT_WAIVERS_PATH,
    findings_dir: Path = DEFAULT_FINDINGS_DIR,
    now: datetime | None = None,
) -> CheckWaiverResponse | ErrorResponse:
    current_time = now or datetime.now(timezone.utc)
    try:
        waivers = _load_waiver_entries(waivers_path)
    except Exception as error:
        return _error("SCP-MCP-E021", f"unable to read waivers: {error}")

    findings_by_id = _finding_index(findings_dir)
    matches: list[WaiverMatch] = []
    for waiver in waivers:
        finding_id = waiver.get("finding_id")
        expires_at = waiver.get("expires_at")
        if not isinstance(finding_id, str) or not isinstance(expires_at, str):
            continue
        finding = findings_by_id.get(finding_id)
        if finding is None or finding.get("rule_id") != request.rule_id:
            continue
        if request.scope is not None and finding.get("area_id") != request.scope:
            continue
        try:
            if _normalise_iso8601(expires_at) <= current_time.astimezone(timezone.utc):
                continue
        except ValueError:
            continue
        matches.append(
            WaiverMatch(
                waiver_id=str(waiver.get("waiver_id", "")),
                finding_id=finding_id,
                rule_id=request.rule_id,
                scope=str(finding.get("area_id")) if isinstance(finding.get("area_id"), str) else None,
                reason=str(waiver.get("reason", "")),
                approved_by=str(waiver.get("approved_by", "")),
                expires_at=expires_at,
                created_at=str(waiver.get("created_at")) if waiver.get("created_at") is not None else None,
            )
        )
    matches.sort(key=lambda match: (match.finding_id, match.waiver_id))
    return CheckWaiverResponse(rule_id=request.rule_id, scope=request.scope, active_waivers=matches)


def list_open_decisions_impl(
    request: ListOpenDecisionsRequest,
    *,
    decisions_path: Path = DEFAULT_DECISIONS_PATH,
) -> ListOpenDecisionsResponse | ErrorResponse:
    since = _decision_since_filter(request.since)
    if isinstance(since, ErrorResponse):
        return since
    try:
        decisions = _parse_decisions_table(decisions_path)
        if since is not None:
            decisions = [decision for decision in decisions if date.fromisoformat(decision.date) >= since]
    except Exception as error:
        return _error("SCP-MCP-E021", f"unable to parse decision log: {error}")
    return ListOpenDecisionsResponse(decisions=decisions)


def check_finding_impl(
    request: CheckFindingRequest,
    *,
    findings_dir: Path = DEFAULT_FINDINGS_DIR,
) -> CheckFindingResponse | ErrorResponse:
    finding = _finding_index(findings_dir).get(request.finding_id)
    if finding is None:
        return _error(
            "SCP-MCP-E022",
            f"finding '{request.finding_id}' was not found under {findings_dir}",
        )
    return CheckFindingResponse(finding=finding)


def resolve_domain_impl(
    request: ResolveDomainRequest,
    *,
    registry_snapshot: RegistrySnapshot | None = None,
) -> ResolveDomainResponse:
    registry = registry_snapshot or load_registry()
    exact_map = _registry_exact_path_map(registry)
    resolved_domains: set[str] = set()
    saw_exact = False
    saw_fuzzy = False

    for changed_file in request.changed_files:
        normalised = changed_file.replace("\\", "/").strip("/")
        exact_domains = exact_map.get(normalised, set())
        if exact_domains:
            resolved_domains.update(exact_domains)
            saw_exact = True
            continue
        fuzzy_domains = _fuzzy_domains_for_path(normalised)
        if fuzzy_domains:
            resolved_domains.update(fuzzy_domains)
            saw_fuzzy = True

    confidence = 0.0
    if saw_exact and not saw_fuzzy:
        confidence = 1.0
    elif saw_exact and saw_fuzzy:
        confidence = 0.8
    elif saw_fuzzy:
        confidence = 0.55

    return ResolveDomainResponse(domains=sorted(resolved_domains), confidence=confidence)


def audit_changed_impl(
    request: AuditChangedRequest,
    *,
    cache_ttl_seconds: int = DEFAULT_AUDIT_CACHE_TTL_SECONDS,
    cache_max_entries: int = DEFAULT_AUDIT_CACHE_MAX_ENTRIES,
    diff_cap: int = DEFAULT_AUDIT_DIFF_CAP,
    timeout_seconds: int = DEFAULT_AUDIT_TIMEOUT_SECONDS,
) -> AuditChangedResponse | ErrorResponse:
    base_ref = (request.base_ref or DEFAULT_BASE_REF).strip()
    head_ref = (request.head_ref or DEFAULT_HEAD_REF).strip()
    repo_root = project_root()
    start_time = time.monotonic()
    current_time = time.time()
    with _AUDIT_CHANGED_CACHE_LOCK:
        _prune_audit_changed_cache(current_time=current_time, max_entries=cache_max_entries)

    try:
        resolved_base_ref = _resolve_git_commit(
            base_ref,
            repo_root=repo_root,
            timeout_seconds=_remaining_timeout_seconds(start_time, timeout_seconds),
        )
        resolved_head_ref = _resolve_git_commit(
            head_ref,
            repo_root=repo_root,
            timeout_seconds=_remaining_timeout_seconds(start_time, timeout_seconds),
        )
    except subprocess.TimeoutExpired:
        return _timeout_error(timeout_seconds)
    except Exception as error:
        return _error("SCP-MCP-E021", f"unable to resolve audit refs: {error}")

    cache_key = _audit_cache_key(resolved_base_ref, resolved_head_ref)
    with _AUDIT_CHANGED_CACHE_LOCK:
        cached = _AUDIT_CHANGED_CACHE.get(cache_key)
        if cached is not None and cached[0] > current_time:
            try:
                _AUDIT_CHANGED_CACHE.move_to_end(cache_key)
            except KeyError:
                cached = None
            else:
                return cached[1]

    try:
        changed_paths = _list_changed_files_with_timeout(
            base_ref=base_ref,
            head_ref=head_ref,
            repo_root=repo_root,
            timeout_seconds=_remaining_timeout_seconds(start_time, timeout_seconds),
        )
    except subprocess.TimeoutExpired:
        return _timeout_error(timeout_seconds)
    except Exception as error:
        return _error("SCP-MCP-E021", f"unable to resolve changed files: {error}")
    if len(changed_paths) > diff_cap:
        return _error(
            "SCP-MCP-E012",
            f"diff between {base_ref} and {head_ref} contains {len(changed_paths)} files, exceeding the cap of {diff_cap}",
        )

    domains_response = resolve_domain_impl(ResolveDomainRequest(changed_files=changed_paths))
    domains = domains_response.domains or ["governance"]

    try:
        payload = _run_audit_changed_cli(
            base_ref=base_ref,
            head_ref=head_ref,
            domains=domains,
            timeout_seconds=_remaining_timeout_seconds(start_time, timeout_seconds),
        )
    except subprocess.TimeoutExpired:
        return _timeout_error(timeout_seconds)
    except Exception as error:
        return _error("SCP-MCP-E021", f"audit-changed failed: {error}")

    try:
        response = AuditChangedResponse.model_validate({"schema_version": SCHEMA_VERSION, **payload})
    except (ValidationError, ValueError, TypeError) as error:
        return _error("SCP-MCP-E021", f"audit-changed returned an unexpected payload: {error}")

    expiry_time = time.time() + cache_ttl_seconds
    with _AUDIT_CHANGED_CACHE_LOCK:
        _AUDIT_CHANGED_CACHE[cache_key] = (expiry_time, response)
        try:
            _AUDIT_CHANGED_CACHE.move_to_end(cache_key)
        except KeyError:
            pass
        _prune_audit_changed_cache(current_time=time.time(), max_entries=cache_max_entries)
    return response


def propose_impl(
    request: ProposeRequest,
    *,
    proposals_root: Path = DEFAULT_PROPOSALS_ROOT,
    repo_root: Path = project_root(),
    now: datetime | None = None,
    caller_id: str | None = None,
    signing_key_id: str | None = None,
) -> ProposeResponse | ErrorResponse:
    queued_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if "\x00" in request.title or "\x00" in request.body:
        return _error("SCP-MCP-E021", "proposal content must not contain NUL bytes")
    try:
        proposal_hash = _proposal_hash(request.body)
    except ValueError as error:
        return _error("SCP-MCP-E021", str(error))

    with _proposal_creation_guard(proposals_root):
        effective_caller_id = caller_id or _stdio_caller_id()
        try:
            effective_signing_key_id = signing_key_id or _current_signing_key_id(repo_root)
        except ValueError as error:
            return _error("SCP-MCP-E021", str(error))

        try:
            _remove_orphaned_duplicate_proposals(
                proposals_root=proposals_root,
                repo_root=repo_root,
                proposal_hash=proposal_hash,
            )
        except subprocess.TimeoutExpired:
            return _error(
                "SCP-MCP-E021",
                "timed out while checking for orphaned proposal branches during duplicate recovery",
            )
        except OSError as error:
            return _error("SCP-MCP-E021", f"unable to remove orphaned proposal file: {error}")

        if _proposal_rate_limit_exceeded(
            proposals_root=proposals_root,
            caller_id=effective_caller_id,
            now=queued_at,
        ):
            return _error(
                "SCP-MCP-E020",
                "caller exceeded the 10 proposals per rolling hour anti-spam limit",
            )
        if _proposal_is_duplicate(
            proposals_root=proposals_root,
            proposal_hash=proposal_hash,
            now=queued_at,
        ):
            return _error(
                "SCP-MCP-E020",
                "an identical proposal body was already submitted within the last 24 hours",
            )

        try:
            base_commit = _resolve_git_commit(
                "HEAD",
                repo_root=repo_root,
                timeout_seconds=DEFAULT_GIT_OPERATION_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return _error(
                "SCP-MCP-E021",
                "timed out while resolving the current repository HEAD for proposal branch creation",
            )
        except Exception as error:
            return _error("SCP-MCP-E021", f"unable to resolve proposal branch base: {error}")

        next_proposal_number = int(_next_proposal_id(proposals_root).removeprefix("PROP-"))
        while True:
            proposal_id = f"PROP-{next_proposal_number:03d}"
            branch_name = f"proposals/{proposal_id}"
            proposal_path = proposals_root / f"{proposal_id}.md"
            try:
                if not _proposal_branch_exists(repo_root=repo_root, branch_name=branch_name):
                    break
            except subprocess.TimeoutExpired:
                return _error(
                    "SCP-MCP-E021",
                    f"timed out while checking whether proposal branch '{branch_name}' already exists",
                )
            next_proposal_number += 1

        timestamp = queued_at.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        proposal_body = _proposal_markdown(
            proposal_id=proposal_id,
            branch_name=branch_name,
            proposal_hash=proposal_hash,
            title=request.title,
            body=request.body,
            affected_repos=request.affected_repos,
            rule_id=request.rule_id,
            queued_at=timestamp,
            caller_id=effective_caller_id,
            signing_key_id=effective_signing_key_id,
        )
        try:
            _write_new_proposal_file(proposal_path, proposal_body)
        except FileExistsError:
            return _error("SCP-MCP-E021", f"proposal file '{proposal_path.name}' already exists")
        except OSError as error:
            return _error("SCP-MCP-E021", f"unable to write proposal file: {error}")
        try:
            _create_proposal_branch(
                repo_root=repo_root,
                branch_name=branch_name,
                base_commit=base_commit,
            )
        except Exception as error:
            try:
                proposal_path.unlink(missing_ok=True)
            except OSError:
                pass
            return _error("SCP-MCP-E021", f"unable to create proposal branch: {error}")
    return ProposeResponse(
        proposal_id=proposal_id,
        branch=branch_name,
        path=_proposal_relative_path(proposal_path=proposal_path, repo_root=repo_root),
        pr_url_if_pushed=None,
        adjudication_status="queued_no_adjudicator",
        expected_review_date=None,
    )


def consult_rules(request: ConsultRulesRequest) -> ConsultRulesResponse | ErrorResponse:
    _log_tool_invocation("consult_rules", request)
    return consult_rules_impl(request)


def check_waiver(request: CheckWaiverRequest) -> CheckWaiverResponse | ErrorResponse:
    _log_tool_invocation("check_waiver", request)
    return check_waiver_impl(request)


def list_open_decisions(request: ListOpenDecisionsRequest) -> ListOpenDecisionsResponse | ErrorResponse:
    _log_tool_invocation("list_open_decisions", request)
    return list_open_decisions_impl(request)


def check_finding(request: CheckFindingRequest) -> CheckFindingResponse | ErrorResponse:
    _log_tool_invocation("check_finding", request)
    return check_finding_impl(request)


def audit_changed(request: AuditChangedRequest) -> AuditChangedResponse | ErrorResponse:
    _log_tool_invocation("audit_changed", request)
    return audit_changed_impl(request)


def resolve_domain(request: ResolveDomainRequest) -> ResolveDomainResponse:
    _log_tool_invocation("resolve_domain", request)
    return resolve_domain_impl(request)


def propose(request: ProposeRequest) -> ProposeResponse | ErrorResponse:
    _log_tool_invocation("propose", request)
    return propose_impl(request)


def register_tools(server: FastMCP) -> None:
    """Register SCP MCP tools on the provided FastMCP server."""

    server.tool(name="consult_rules", structured_output=True)(consult_rules)
    server.tool(name="check_waiver", structured_output=True)(check_waiver)
    server.tool(name="list_open_decisions", structured_output=True)(list_open_decisions)
    server.tool(name="check_finding", structured_output=True)(check_finding)
    server.tool(name="audit_changed", structured_output=True)(audit_changed)
    server.tool(name="resolve_domain", structured_output=True)(resolve_domain)
    server.tool(name="propose", structured_output=True)(propose)
    server.tool(name="consult_scorecard", structured_output=True)(consult_scorecard)
