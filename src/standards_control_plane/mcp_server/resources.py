"""Committed-state MCP resources for the Standards Control Plane."""

from __future__ import annotations

import copy
import asyncio
import hashlib
import json
import logging
import re
import subprocess
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Callable

from standards_control_plane.resources import project_root

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP

SCHEMA_VERSION = "1.0.0"
_RESOURCE_GIT_TIMEOUT_SECONDS = 30
_DECISION_ID_PATTERN = re.compile(r"^D-\d{3,}$")
_KEY_VALUE_PATTERN = re.compile(r"(?P<key>[A-Za-z_][A-Za-z0-9_-]*)=(?P<value>[^\s]+)")

STATIC_RESOURCE_URIS = (
    "scp://rules/registry",
    "scp://rules/domain-map",
    "scp://decisions",
    "scp://findings/open",
    "scp://waivers",
    "scp://status",
    "scp://security/signing-keys",
)

TEMPLATE_RESOURCE_URIS = (
    "scp://rule/{rule_id}",
    "scp://waiver/{waiver_id}",
    "scp://finding/{finding_id}",
    "scp://decision/{decision_id}",
)

_FALLBACK_APPLIES_TO_BY_RULE_ID: dict[str, tuple[str, ...]] = {
    "SVC-001": ("services.yml", "**/services.yml"),
    "SVC-002": ("services.yml", "**/services.yml"),
    "SVC-003": ("services.yml", "**/services.yml"),
    # ARCH-006 ontology-canonical-consumption (enforced via SCP-R-013). Relevance
    # covers the ontology_contract declaration surface (services.yml) plus the
    # divergent-copy markers the rule guards: embedded canonical ontology data
    # files and the source languages where a local Ontology/Canonicalizer class
    # would live. A rule-specific entry REPLACES (does not merge) the architecture
    # domain fallback, so services.yml is listed explicitly here.
    "ARCH-006": (
        "services.yml",
        "**/services.yml",
        "**/ontology_complete.yaml",
        "**/value_mappings.json",
        "**/ontology.py",
        "src/**/*.py",
        "backend/**/*.py",
        "src/**/*.ts",
        "src/**/*.go",
    ),
    "SVC-004": (
        "scripts/deploy-dev.sh",
        "scripts/deploy-staging.sh",
        "scripts/deploy-*.sh",
        "docker-compose*.yml",
        "infra/**/deploy*.sh",
        "Dockerfile",
        "services.yml",
        "**/services.yml",
    ),
}

_FALLBACK_APPLIES_TO_BY_DOMAIN: dict[str, tuple[str, ...]] = {
    "governance": (
        "docs/**/*.md",
        "docs/DECISIONS.md",
        "docs/STATUS.md",
    ),
    "architecture": (
        "src/**/*.py",
        "src/**/*.ts",
        "src/**/*.tsx",
        "frontend/**/*.ts",
        "frontend/**/*.tsx",
        "backend/**/*.py",
        # R3.0: surface architecture rules on Go (control-tower + mapp-pim are
        # heavily Go). Advisory consult only — no Rego enforcement fires on Go
        # yet (REACH-3.1). Scoped to src/ + packages/ (NOT blanket **/*.go) so
        # vendored/example Go is not flagged.
        "src/**/*.go",
        "packages/**/*.go",
    ),
    "ux": (
        "frontend/**/*.tsx",
        "frontend/**/*.jsx",
        "app/**/*.tsx",
        "app/**/*.jsx",
        "**/*.css",
        "**/*.scss",
    ),
    "design": (
        "frontend/**/*.tsx",
        "frontend/**/*.jsx",
        "app/**/*.tsx",
        "app/**/*.jsx",
        "design-system/**",
        "**/*.css",
        "**/*.scss",
    ),
    "product": (
        "docs/plans/**/*.md",
        "docs/reviews/**/*.md",
        "frontend/**/*.tsx",
        "app/**/*.tsx",
    ),
    "service-lifecycle": (
        "services.yml",
        "**/services.yml",
    ),
}

RESOURCE_LOGGER = logging.getLogger("standards_control_plane.mcp.resources")


def _normalise_iso8601(value: str) -> datetime:
    normalised = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", normalised):
        return datetime.fromisoformat(f"{normalised}T00:00:00+00:00")
    return datetime.fromisoformat(normalised.replace("Z", "+00:00"))


def _git_stdout(repo_root: Path, args: list[str]) -> str:
    completed = subprocess.run(
        args,
        cwd=repo_root,
        capture_output=True,
        check=False,
        text=True,
        timeout=_RESOURCE_GIT_TIMEOUT_SECONDS,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        stdout = completed.stdout.strip()
        raise RuntimeError(stderr or stdout or f"{' '.join(args)} failed without output")
    return completed.stdout


def _head_commit(repo_root: Path) -> str:
    return _git_stdout(repo_root, ["git", "rev-parse", "--verify", "HEAD^{commit}"]).strip()


def _cache_key_for_commit(commit_sha: str) -> str:
    return hashlib.sha256(commit_sha.encode("utf-8")).hexdigest()


def _read_committed_text(repo_root: Path, ref: str, relative_path: str) -> str:
    return _git_stdout(repo_root, ["git", "show", f"{ref}:{relative_path}"])


def _read_committed_json(repo_root: Path, ref: str, relative_path: str) -> Any:
    return json.loads(_read_committed_text(repo_root, ref, relative_path))


def _list_committed_paths(repo_root: Path, ref: str, prefix: str) -> list[str]:
    output = _git_stdout(
        repo_root,
        ["git", "ls-tree", "-r", "--name-only", ref, "--", prefix],
    )
    return [line.strip() for line in output.splitlines() if line.strip()]


def _resource_envelope(payload: dict[str, Any], *, key_id: str | None) -> dict[str, Any]:
    if "schema_version" in payload or "key_id" in payload:
        raise ValueError("resource payloads must not override envelope keys")
    return {
        "schema_version": SCHEMA_VERSION,
        "key_id": key_id,
        **payload,
    }


def _signing_keys_trust_model() -> dict[str, Any]:
    return {
        "transport_trust_required": True,
        "verification_roots": [
            "docs/security/mcp-signing-keys.pub at a known git SHA",
            "operator-distributed public key hash",
        ],
        "adopter_requirement": (
            "Adopters MUST verify current_key.public_key against an out-of-band "
            "trust anchor such as the committed docs/security/mcp-signing-keys.pub "
            "file at a known git SHA or an operator-distributed public key hash. "
            "Resource-only cross-checks are insufficient; current_key_sha256 is "
            "informational, not authoritative."
        ),
    }


def _degraded_signing_keys_payload(reason: str) -> dict[str, Any]:
    return {
        "current_key": None,
        "current_key_sha256": None,
        "prior_keys": [],
        "keys": [],
        "error": reason,
        "trust_model": _signing_keys_trust_model(),
    }


def _extract_finding_objects(
    payload: Any,
    *,
    seen_finding_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    seen = seen_finding_ids if seen_finding_ids is not None else set()
    findings: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        if {"finding_id", "domain", "severity", "summary"}.issubset(payload):
            finding_id = payload.get("finding_id")
            if isinstance(finding_id, str) and finding_id not in seen:
                seen.add(finding_id)
                findings.append(payload)
        nested = payload.get("findings")
        if isinstance(nested, list):
            for item in nested:
                findings.extend(_extract_finding_objects(item, seen_finding_ids=seen))
    elif isinstance(payload, list):
        for item in payload:
            findings.extend(_extract_finding_objects(item, seen_finding_ids=seen))
    return findings


def _parse_decisions_table(markdown: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if len(cells) != 5:
            continue
        if cells[0] in {"ID", "----"} or set(cells[0]) == {"-"}:
            continue
        if not _DECISION_ID_PATTERN.fullmatch(cells[0]):
            continue
        rows.append(
            {
                "decision_id": cells[0],
                "date": cells[1],
                "decision": cells[2],
                "status": cells[3],
                "rationale": cells[4],
            }
        )
    return rows


def _parse_status_markdown(markdown: str) -> dict[str, Any]:
    metadata: dict[str, str] = {}
    summary: list[str] = []
    section: str | None = None

    for line in markdown.splitlines():
        stripped = line.strip()
        metadata_match = re.match(r"^\*\*(.+?):\*\*\s*(.+)$", stripped)
        if metadata_match and section is None:
            key = metadata_match.group(1).strip().lower().replace(" ", "_")
            metadata[key] = metadata_match.group(2).strip()
            continue
        if stripped.startswith("## "):
            section = stripped[3:].strip().lower()
            continue
        if section == "summary" and stripped.startswith("- "):
            summary.append(stripped[2:].strip())

    return {
        "last_updated": metadata.get("last_updated"),
        "current_branch": metadata.get("current_branch"),
        "current_work_package": metadata.get("current_work_package"),
        "current_state": metadata.get("current_state"),
        "summary": summary,
    }


def _parse_signing_keys(text: str) -> dict[str, Any]:
    keys: list[dict[str, Any]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 2 or parts[0] != "ssh-ed25519":
            continue
        metadata = {
            match.group("key"): match.group("value").strip()
            for match in _KEY_VALUE_PATTERN.finditer(" ".join(parts[2:]))
        }
        entry = {
            "algorithm": parts[0],
            "public_key": parts[1],
            "key_id": metadata.get("key_id") or metadata.get("key-id"),
            "current": metadata.get("current", "").lower() in {"1", "true", "yes"},
            "retain_until": metadata.get("retain_until")
            or metadata.get("retain-until")
            or metadata.get("retention_until")
            or metadata.get("retention-date"),
            "public_key_sha256": hashlib.sha256(parts[1].encode("utf-8")).hexdigest(),
        }
        keys.append(entry)

    current_entries = [entry for entry in keys if entry["current"]]
    if len(current_entries) > 1:
        key_ids = [entry.get("key_id") for entry in current_entries]
        raise RuntimeError(f"multiple current signing keys declared: {key_ids}")
    if not current_entries and keys:
        key_ids = [entry.get("key_id") for entry in keys]
        raise RuntimeError(
            "no current signing key declared in docs/security/mcp-signing-keys.pub; "
            f"available key_ids={key_ids}"
        )
    current_key = current_entries[0] if current_entries else None

    current_key_id = current_key.get("key_id") if current_key else None
    previous_keys = [entry for entry in keys if entry.get("key_id") != current_key_id]
    return {
        "current_key": current_key,
        "current_key_sha256": current_key.get("public_key_sha256") if current_key else None,
        "prior_keys": previous_keys,
        "keys": keys,
        "error": None,
        "trust_model": _signing_keys_trust_model(),
    }


def _recent_wp_merges(repo_root: Path, ref: str, *, limit: int = 10) -> list[dict[str, str]]:
    output = _git_stdout(
        repo_root,
        [
            "git",
            "log",
            "--first-parent",
            f"--max-count={limit * 5}",
            "--pretty=format:%H%x1f%s%x1f%aI",
            ref,
        ],
    )
    merges: list[dict[str, str]] = []
    for line in output.splitlines():
        parts = line.split("\x1f")
        if len(parts) != 3:
            continue
        commit_sha, subject, committed_at = parts
        if "WP-SCP-" not in subject:
            continue
        merges.append(
            {
                "commit": commit_sha,
                "subject": subject,
                "committed_at": committed_at,
            }
        )
        if len(merges) >= limit:
            break
    return merges


def _applies_to_for_rule(rule_entry: dict[str, Any]) -> list[str]:
    applies_to = rule_entry.get("applies_to")
    if isinstance(applies_to, list) and all(isinstance(item, str) for item in applies_to):
        return list(dict.fromkeys(applies_to))

    rule_id = str(rule_entry.get("rule_id", ""))
    domain = str(rule_entry.get("domain", ""))
    fallback = _FALLBACK_APPLIES_TO_BY_RULE_ID.get(rule_id)
    if fallback is None:
        fallback = _FALLBACK_APPLIES_TO_BY_DOMAIN.get(domain, ())
    return list(fallback)


def _normalise_repo_relative_path(path: PurePosixPath) -> PurePosixPath:
    parts: list[str] = []
    for part in path.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                raise ValueError(f"path traversal escapes repository root: {path.as_posix()}")
            parts.pop()
            continue
        parts.append(part)
    return PurePosixPath(*parts)


def _resolve_repo_relative_path(
    *,
    base_dir: PurePosixPath,
    relative_path: str,
    container_dir: PurePosixPath,
) -> str:
    candidate = PurePosixPath(relative_path)
    if candidate.is_absolute():
        raise ValueError(f"absolute repository path is not allowed: {relative_path}")

    resolved = _normalise_repo_relative_path(base_dir / candidate)
    if resolved == container_dir or resolved.is_relative_to(container_dir):
        return resolved.as_posix()
    raise ValueError(
        f"path traversal escapes committed resource container: {relative_path} -> {resolved.as_posix()}"
    )


def _classify_waivers(
    waivers_payload: Any,
    *,
    current_time: datetime,
    key_id: str | None,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]], set[str]]:
    entries = waivers_payload if isinstance(waivers_payload, list) else []
    active_waivers: list[dict[str, Any]] = []
    waivers_by_id: dict[str, dict[str, Any]] = {}
    active_waiver_ids: set[str] = set()

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        waiver_id = entry.get("waiver_id")
        if not isinstance(waiver_id, str):
            continue

        expires_at = entry.get("expires_at")
        finding_id = entry.get("finding_id")
        is_active = False
        if isinstance(expires_at, str):
            try:
                is_active = _normalise_iso8601(expires_at) > current_time
            except ValueError:
                is_active = False

        waiver_resource = {
            **entry,
            "active": is_active,
        }
        waivers_by_id[waiver_id] = _resource_envelope({"waiver": waiver_resource}, key_id=key_id)

        if not is_active:
            continue
        active_waivers.append(waiver_resource)
        if isinstance(finding_id, str):
            active_waiver_ids.add(finding_id)

    active_waivers.sort(key=lambda entry: (str(entry.get("finding_id", "")), str(entry.get("waiver_id", ""))))
    return active_waivers, waivers_by_id, active_waiver_ids


@dataclass(slots=True)
class CommittedResourceSnapshot:
    head_commit: str
    cache_key: str
    static_resources: dict[str, dict[str, Any]]
    rules_by_id: dict[str, dict[str, Any]]
    findings_by_id: dict[str, dict[str, Any]]
    waivers_by_id: dict[str, dict[str, Any]]
    decisions_by_id: dict[str, dict[str, Any]]
    key_id: str | None


class ScpCommittedResourceCatalog:
    """Read MCP resources from committed git state only."""

    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        now_func: Callable[[], datetime] | None = None,
    ) -> None:
        self._repo_root = (repo_root or project_root()).resolve()
        self._now_func = now_func or (lambda: datetime.now(timezone.utc))
        self._snapshot: CommittedResourceSnapshot | None = None
        self._snapshot_lock = threading.Lock()
        self._subscribers: dict[str, set[Any]] = {}

    @property
    def repo_root(self) -> Path:
        return self._repo_root

    def cache_key(self) -> str:
        return self.snapshot().cache_key

    def snapshot(self) -> CommittedResourceSnapshot:
        head_commit = _head_commit(self._repo_root)
        cache_key = _cache_key_for_commit(head_commit)
        snapshot = self._snapshot
        if snapshot is not None and snapshot.cache_key == cache_key:
            return snapshot

        with self._snapshot_lock:
            snapshot = self._snapshot
            if snapshot is not None and snapshot.cache_key == cache_key:
                return snapshot
            previous_snapshot = snapshot
            snapshot = self._build_snapshot(head_commit=head_commit, cache_key=cache_key)
            self._snapshot = snapshot

        self._schedule_resource_update_notifications(previous_snapshot, snapshot)
        return snapshot

    def subscribe(self, uri: str, session: Any) -> None:
        self._subscribers.setdefault(uri, set()).add(session)

    def unsubscribe(self, uri: str, session: Any) -> None:
        subscribers = self._subscribers.get(uri)
        if not subscribers:
            return
        subscribers.discard(session)
        if not subscribers:
            self._subscribers.pop(uri, None)

    def read_static(self, uri: str) -> dict[str, Any]:
        snapshot = self.snapshot()
        if uri not in snapshot.static_resources:
            raise KeyError(f"unknown resource URI: {uri}")
        return copy.deepcopy(snapshot.static_resources[uri])

    def read_rule(self, rule_id: str) -> dict[str, Any]:
        snapshot = self.snapshot()
        payload = snapshot.rules_by_id.get(rule_id)
        if payload is None:
            raise KeyError(f"unknown rule resource: {rule_id}")
        return copy.deepcopy(payload)

    def read_waiver(self, waiver_id: str) -> dict[str, Any]:
        snapshot = self.snapshot()
        payload = snapshot.waivers_by_id.get(waiver_id)
        if payload is None:
            raise KeyError(f"unknown waiver resource: {waiver_id}")
        return copy.deepcopy(payload)

    def read_finding(self, finding_id: str) -> dict[str, Any]:
        snapshot = self.snapshot()
        payload = snapshot.findings_by_id.get(finding_id)
        if payload is None:
            raise KeyError(f"unknown finding resource: {finding_id}")
        return copy.deepcopy(payload)

    def read_decision(self, decision_id: str) -> dict[str, Any]:
        snapshot = self.snapshot()
        payload = snapshot.decisions_by_id.get(decision_id)
        if payload is None:
            raise KeyError(f"unknown decision resource: {decision_id}")
        return copy.deepcopy(payload)

    def _snapshot_payload_for_uri(self, snapshot: CommittedResourceSnapshot, uri: str) -> dict[str, Any] | None:
        if uri in snapshot.static_resources:
            return snapshot.static_resources[uri]
        for prefix, payloads in (
            ("scp://rule/", snapshot.rules_by_id),
            ("scp://waiver/", snapshot.waivers_by_id),
            ("scp://finding/", snapshot.findings_by_id),
            ("scp://decision/", snapshot.decisions_by_id),
        ):
            if uri.startswith(prefix):
                return payloads.get(uri[len(prefix) :])
        return None

    def _schedule_resource_update_notifications(
        self,
        previous_snapshot: CommittedResourceSnapshot | None,
        snapshot: CommittedResourceSnapshot,
    ) -> None:
        if previous_snapshot is None or previous_snapshot.cache_key == snapshot.cache_key:
            return
        if not self._subscribers:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        for uri, sessions in list(self._subscribers.items()):
            if not sessions:
                continue
            if self._snapshot_payload_for_uri(previous_snapshot, uri) == self._snapshot_payload_for_uri(snapshot, uri):
                continue
            for session in list(sessions):
                loop.create_task(session.send_resource_updated(uri))

    def _build_snapshot(self, *, head_commit: str, cache_key: str) -> CommittedResourceSnapshot:
        ref = head_commit
        current_time = self._now_func().astimezone(timezone.utc)
        current_key_id: str | None = None
        try:
            signing_keys_text = _read_committed_text(
                self._repo_root,
                ref,
                "docs/security/mcp-signing-keys.pub",
            )
            signing_keys_body = _parse_signing_keys(signing_keys_text)
            if not signing_keys_body["keys"]:
                raise RuntimeError(
                    "docs/security/mcp-signing-keys.pub contains no ssh-ed25519 key entries"
                )
            current_key = signing_keys_body["current_key"]
            current_key_id = current_key.get("key_id") if isinstance(current_key, dict) else None
            if current_key_id is None:
                raise RuntimeError(
                    "docs/security/mcp-signing-keys.pub does not identify a current signing key"
                )
        except (RuntimeError, subprocess.TimeoutExpired, OSError) as error:
            # RuntimeError: parse failure (no/multiple current marker, malformed entries).
            # subprocess.TimeoutExpired: git show exceeded _RESOURCE_GIT_TIMEOUT_SECONDS.
            # OSError (incl. FileNotFoundError): git binary absent / repo unreadable.
            # All three classes degrade the snapshot rather than re-raising — the
            # invariant "a malformed/unreadable signing-keys file does NOT take
            # all 11 resource URIs offline" holds across the full failure surface.
            RESOURCE_LOGGER.error("degrading MCP resource snapshot: signing-keys unavailable: %s", error)
            signing_keys_body = _degraded_signing_keys_payload(str(error))

        registry_body, rule_cards = self._build_registry(ref=ref, key_id=current_key_id)
        domain_map_body = self._build_domain_map(
            registry_body=registry_body,
            key_id=current_key_id,
        )

        waivers_payload = _read_committed_json(self._repo_root, ref, "output/findings/waivers.json")
        active_waivers, waivers_by_id, active_waiver_ids = _classify_waivers(
            waivers_payload,
            current_time=current_time,
            key_id=current_key_id,
        )
        decisions_body = self._build_decisions(ref=ref, key_id=current_key_id)
        findings_open_body, findings_by_id = self._build_findings(
            ref=ref,
            key_id=current_key_id,
            active_waiver_ids=active_waiver_ids,
        )
        waivers_body = self._build_waivers(active_waivers=active_waivers, key_id=current_key_id)
        status_body = self._build_status(ref=ref, key_id=current_key_id)
        signing_keys_resource = _resource_envelope(signing_keys_body, key_id=current_key_id)

        static_resources = {
            "scp://rules/registry": registry_body,
            "scp://rules/domain-map": domain_map_body,
            "scp://decisions": decisions_body["resource"],
            "scp://findings/open": findings_open_body,
            "scp://waivers": waivers_body,
            "scp://status": status_body,
            "scp://security/signing-keys": signing_keys_resource,
        }
        return CommittedResourceSnapshot(
            head_commit=head_commit,
            cache_key=cache_key,
            static_resources=static_resources,
            rules_by_id=rule_cards,
            findings_by_id=findings_by_id,
            waivers_by_id=waivers_by_id,
            decisions_by_id=decisions_body["by_id"],
            key_id=current_key_id,
        )

    def _build_registry(
        self,
        *,
        ref: str,
        key_id: str | None,
    ) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
        root_index = _read_committed_json(self._repo_root, ref, "standards/standards-index.json")
        domains_payload = root_index.get("domains", {})
        if not isinstance(domains_payload, dict):
            raise ValueError("standards/standards-index.json must define a domains object")

        registry_domains: dict[str, Any] = {}
        rule_cards: dict[str, dict[str, Any]] = {}
        standards_root = Path("standards")

        for domain_name, index_relative_path in sorted(domains_payload.items()):
            if not isinstance(index_relative_path, str):
                raise TypeError(f"Registry index path for {domain_name} must be a string")
            index_path = _resolve_repo_relative_path(
                base_dir=standards_root,
                relative_path=index_relative_path,
                container_dir=standards_root,
            )
            domain_index = _read_committed_json(self._repo_root, ref, index_path)
            rules: list[dict[str, Any]] = []
            for entry in domain_index.get("rules", []):
                if not isinstance(entry, dict):
                    continue
                applies_to = _applies_to_for_rule(entry)
                rule_path = entry.get("path")
                if not isinstance(rule_path, str):
                    raise TypeError(f"Rule path for domain {domain_name} must be a string")
                rule_resource_path = _resolve_repo_relative_path(
                    base_dir=PurePosixPath(index_path).parent,
                    relative_path=rule_path,
                    container_dir=PurePosixPath(index_path).parent,
                )
                rule_body_markdown = _read_committed_text(self._repo_root, ref, rule_resource_path)
                rule_resource = {
                    **entry,
                    "source_path": rule_resource_path,
                    "applies_to": applies_to,
                }
                rules.append(rule_resource)
                rule_id = str(entry["rule_id"])
                rule_cards[rule_id] = _resource_envelope(
                    {
                        "rule": {
                            **rule_resource,
                            "body_markdown": rule_body_markdown,
                        }
                    },
                    key_id=key_id,
                )

            patterns = [
                entry
                for entry in domain_index.get("patterns", [])
                if isinstance(entry, dict)
            ]
            registry_domains[str(domain_name)] = {
                "domain": domain_index.get("domain"),
                "version": domain_index.get("version"),
                "status": domain_index.get("status"),
                "rules": rules,
                "patterns": patterns,
            }

        registry_body = _resource_envelope(
            {
                "registry": {
                    "name": root_index.get("name"),
                    "version": root_index.get("version"),
                    "status": root_index.get("status"),
                    "domains": registry_domains,
                }
            },
            key_id=key_id,
        )
        return registry_body, rule_cards

    def _build_domain_map(
        self,
        *,
        registry_body: dict[str, Any],
        key_id: str | None,
    ) -> dict[str, Any]:
        registry = registry_body["registry"]
        by_rule: dict[str, dict[str, Any]] = {}
        by_glob: dict[str, dict[str, Any]] = {}
        for domain_name, domain_registry in registry["domains"].items():
            for rule in domain_registry.get("rules", []):
                rule_id = str(rule["rule_id"])
                globs = list(dict.fromkeys(rule.get("applies_to", [])))
                by_rule[rule_id] = {
                    "domain": domain_name,
                    "globs": globs,
                }
                for glob in globs:
                    bucket = by_glob.setdefault(glob, {"domains": set(), "rule_ids": set()})
                    bucket["domains"].add(domain_name)
                    bucket["rule_ids"].add(rule_id)

        return _resource_envelope(
            {
                "domain_map": {
                    "by_rule": by_rule,
                    "by_glob": {
                        glob: {
                            "domains": sorted(payload["domains"]),
                            "rule_ids": sorted(payload["rule_ids"]),
                        }
                        for glob, payload in sorted(by_glob.items())
                    },
                }
            },
            key_id=key_id,
        )

    def _build_decisions(self, *, ref: str, key_id: str | None) -> dict[str, Any]:
        decisions_markdown = _read_committed_text(self._repo_root, ref, "docs/DECISIONS.md")
        decisions = _parse_decisions_table(decisions_markdown)
        decisions_by_id = {
            decision["decision_id"]: _resource_envelope({"decision": decision}, key_id=key_id)
            for decision in decisions
        }
        return {
            "resource": _resource_envelope({"decisions": decisions}, key_id=key_id),
            "by_id": decisions_by_id,
        }

    def _build_waivers(self, *, active_waivers: list[dict[str, Any]], key_id: str | None) -> dict[str, Any]:
        return _resource_envelope({"waivers": active_waivers}, key_id=key_id)

    def _build_findings(
        self,
        *,
        ref: str,
        key_id: str | None,
        active_waiver_ids: set[str],
    ) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
        findings_by_id: dict[str, dict[str, Any]] = {}
        open_unwaived: dict[str, dict[str, Any]] = {}
        committed_json_paths = [
            path
            for path in _list_committed_paths(self._repo_root, ref, "output/findings")
            if path.endswith(".json") and Path(path).name != "waivers.json"
        ]
        for relative_path in committed_json_paths:
            payload = _read_committed_json(self._repo_root, ref, relative_path)
            for finding in _extract_finding_objects(payload):
                finding_id = finding.get("finding_id")
                if not isinstance(finding_id, str):
                    continue
                findings_by_id[finding_id] = _resource_envelope({"finding": finding}, key_id=key_id)
                if finding.get("status") != "open":
                    continue
                if finding_id in active_waiver_ids:
                    continue
                open_unwaived[finding_id] = finding

        findings = [open_unwaived[finding_id] for finding_id in sorted(open_unwaived)]
        return (
            _resource_envelope({"findings": findings}, key_id=key_id),
            findings_by_id,
        )

    def _build_status(self, *, ref: str, key_id: str | None) -> dict[str, Any]:
        status_markdown = _read_committed_text(self._repo_root, ref, "docs/STATUS.md")
        status_summary = _parse_status_markdown(status_markdown)
        recent_wp_merges = _recent_wp_merges(self._repo_root, ref)
        return _resource_envelope(
            {
                "status": status_summary,
                "recent_wp_merges": recent_wp_merges,
            },
            key_id=key_id,
        )


def register_resources(
    server: FastMCP,
    *,
    repo_root: Path | None = None,
    now_func: Callable[[], datetime] | None = None,
) -> None:
    """Register committed-state SCP MCP resources on the provided server."""

    catalog = ScpCommittedResourceCatalog(repo_root=repo_root, now_func=now_func)
    lowlevel_server = getattr(server, "_mcp_server", None)
    if lowlevel_server is not None:
        from mcp.server.lowlevel.server import NotificationOptions

        @lowlevel_server.subscribe_resource()
        async def subscribe_resource(uri: Any) -> None:
            catalog.subscribe(str(uri), lowlevel_server.request_context.session)

        @lowlevel_server.unsubscribe_resource()
        async def unsubscribe_resource(uri: Any) -> None:
            catalog.unsubscribe(str(uri), lowlevel_server.request_context.session)

        original_create_initialization_options = lowlevel_server.create_initialization_options

        def create_initialization_options(
            notification_options: Any = None,
            experimental_capabilities: dict[str, dict[str, Any]] | None = None,
        ) -> Any:
            options = original_create_initialization_options(
                notification_options=notification_options or NotificationOptions(resources_changed=True),
                experimental_capabilities=experimental_capabilities,
            )
            if options.capabilities.resources is not None:
                options.capabilities.resources.subscribe = True
                options.capabilities.resources.listChanged = True
            return options

        lowlevel_server.create_initialization_options = create_initialization_options

    @server.resource(
        "scp://rules/registry",
        name="rules-registry",
        description="Committed standards registry with per-rule applies_to mappings.",
        mime_type="application/json",
    )
    def rules_registry() -> dict[str, Any]:
        return catalog.read_static("scp://rules/registry")

    @server.resource(
        "scp://rules/domain-map",
        name="rules-domain-map",
        description="Committed changed-file glob to domain and rule mapping.",
        mime_type="application/json",
    )
    def rules_domain_map() -> dict[str, Any]:
        return catalog.read_static("scp://rules/domain-map")

    @server.resource(
        "scp://decisions",
        name="decisions",
        description="Committed DECISIONS.md table parsed to JSON.",
        mime_type="application/json",
    )
    def decisions() -> dict[str, Any]:
        return catalog.read_static("scp://decisions")

    @server.resource(
        "scp://findings/open",
        name="open-findings",
        description="Committed open findings with active waivers removed.",
        mime_type="application/json",
    )
    def findings_open() -> dict[str, Any]:
        return catalog.read_static("scp://findings/open")

    @server.resource(
        "scp://waivers",
        name="waivers",
        description="Committed active waivers filtered by expires_at.",
        mime_type="application/json",
    )
    def waivers() -> dict[str, Any]:
        return catalog.read_static("scp://waivers")

    @server.resource(
        "scp://status",
        name="status",
        description="Committed STATUS.md summary with recent WP git history.",
        mime_type="application/json",
    )
    def status() -> dict[str, Any]:
        return catalog.read_static("scp://status")

    @server.resource(
        "scp://security/signing-keys",
        name="signing-keys",
        description="Committed public signing-key ring for MCP receipt verification.",
        mime_type="application/json",
    )
    def signing_keys() -> dict[str, Any]:
        return catalog.read_static("scp://security/signing-keys")

    @server.resource(
        "scp://rule/{rule_id}",
        name="rule-card",
        description="Committed individual rule card with markdown body.",
        mime_type="application/json",
    )
    def rule_card(rule_id: str) -> dict[str, Any]:
        return catalog.read_rule(rule_id)

    @server.resource(
        "scp://waiver/{waiver_id}",
        name="waiver",
        description="Committed individual active waiver by waiver_id.",
        mime_type="application/json",
    )
    def waiver(waiver_id: str) -> dict[str, Any]:
        return catalog.read_waiver(waiver_id)

    @server.resource(
        "scp://finding/{finding_id}",
        name="finding",
        description="Committed individual finding by finding_id.",
        mime_type="application/json",
    )
    def finding(finding_id: str) -> dict[str, Any]:
        return catalog.read_finding(finding_id)

    @server.resource(
        "scp://decision/{decision_id}",
        name="decision",
        description="Committed individual decision record by decision_id.",
        mime_type="application/json",
    )
    def decision(decision_id: str) -> dict[str, Any]:
        return catalog.read_decision(decision_id)
