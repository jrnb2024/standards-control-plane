"""Standards registry loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .resources import standards_dir
from .schema_tools import load_json_file, validate_with_schema

SUPPORTED_DOMAINS = ("governance", "architecture", "ux", "design", "product", "service-lifecycle")
USABLE_STATUSES = frozenset({"active"})


def _ensure_object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{context} must be an object")
    return value


def _ensure_string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{context} must be a non-empty string")
    return value


def _ensure_string_list(value: Any, context: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise TypeError(f"{context} must be a list of strings")
    return tuple(value)


@dataclass(frozen=True)
class RuleRecord:
    rule_id: str
    domain: str
    title: str
    summary: str
    path: str
    severity_default: str
    scope: tuple[str, ...]
    signals: tuple[str, ...]
    exceptions: tuple[str, ...]
    related_patterns: tuple[str, ...]
    version: str
    status: str
    source_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "domain": self.domain,
            "title": self.title,
            "summary": self.summary,
            "path": self.path,
            "severity_default": self.severity_default,
            "scope": list(self.scope),
            "signals": list(self.signals),
            "exceptions": list(self.exceptions),
            "related_patterns": list(self.related_patterns),
            "version": self.version,
            "status": self.status,
        }


@dataclass(frozen=True)
class PatternRecord:
    pattern_id: str
    domain: str
    title: str
    summary: str
    path: str
    tags: tuple[str, ...]
    version: str
    status: str
    source_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "domain": self.domain,
            "title": self.title,
            "summary": self.summary,
            "path": self.path,
            "tags": list(self.tags),
            "version": self.version,
            "status": self.status,
        }


@dataclass(frozen=True)
class DomainRegistry:
    domain: str
    version: str
    status: str
    rules: tuple[RuleRecord, ...]
    patterns: tuple[PatternRecord, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "version": self.version,
            "status": self.status,
            "rules": [rule.to_dict() for rule in self.rules],
            "patterns": [pattern.to_dict() for pattern in self.patterns],
        }


@dataclass(frozen=True)
class RegistrySnapshot:
    name: str
    version: str
    status: str
    domains: dict[str, DomainRegistry]

    def active_rules_for(self, requested_domains: list[str]) -> list[RuleRecord]:
        selected: list[RuleRecord] = []
        for domain_name in requested_domains:
            domain_registry = self.domains.get(domain_name)
            if domain_registry is None:
                continue
            selected.extend(
                rule
                for rule in domain_registry.rules
                if rule.status in USABLE_STATUSES
            )
        return selected

    def active_patterns_for(self, requested_domains: list[str]) -> list[PatternRecord]:
        selected: list[PatternRecord] = []
        for domain_name in requested_domains:
            domain_registry = self.domains.get(domain_name)
            if domain_registry is None:
                continue
            selected.extend(
                pattern
                for pattern in domain_registry.patterns
                if pattern.status in USABLE_STATUSES
            )
        return selected

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "status": self.status,
            "domains": {
                domain_name: registry.to_dict()
                for domain_name, registry in sorted(self.domains.items())
            },
        }


def _normalise_index_path(path_value: Path | None) -> Path:
    if path_value is None:
        return standards_dir() / "standards-index.json"
    if path_value.is_dir():
        return path_value / "standards-index.json"
    return path_value


def _resolve_existing_path(base_dir: Path, relative_path: str, boundary_root: Path) -> Path:
    resolved = (base_dir / relative_path).resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Registry reference not found: {relative_path}")
    if not resolved.is_relative_to(boundary_root.resolve()):
        raise ValueError(f"Registry reference escapes boundary: {relative_path}")
    return resolved


def _load_rule(entry: Any, domain_name: str, base_dir: Path) -> RuleRecord:
    payload = _ensure_object(entry, f"{domain_name} rule entry")
    validate_with_schema(payload, "standards-rule.schema.json")
    path = _ensure_string(payload["path"], f"{domain_name} rule path")
    source_path = _resolve_existing_path(base_dir, path, boundary_root=base_dir)
    if payload["domain"] != domain_name:
        raise ValueError(
            f"Rule {payload['rule_id']} declares domain {payload['domain']}, expected {domain_name}"
        )
    return RuleRecord(
        rule_id=_ensure_string(payload["rule_id"], "rule_id"),
        domain=_ensure_string(payload["domain"], "domain"),
        title=_ensure_string(payload["title"], "title"),
        summary=_ensure_string(payload["summary"], "summary"),
        path=path,
        severity_default=_ensure_string(payload["severity_default"], "severity_default"),
        scope=_ensure_string_list(payload["scope"], "scope"),
        signals=_ensure_string_list(payload["signals"], "signals"),
        exceptions=_ensure_string_list(payload.get("exceptions", []), "exceptions"),
        related_patterns=_ensure_string_list(
            payload.get("related_patterns", []),
            "related_patterns",
        ),
        version=_ensure_string(payload["version"], "version"),
        status=_ensure_string(payload["status"], "status"),
        source_path=source_path,
    )


def _load_pattern(entry: Any, domain_name: str, base_dir: Path) -> PatternRecord:
    payload = _ensure_object(entry, f"{domain_name} pattern entry")
    validate_with_schema(payload, "standards-pattern.schema.json")
    path = _ensure_string(payload["path"], f"{domain_name} pattern path")
    source_path = _resolve_existing_path(base_dir, path, boundary_root=base_dir)
    if payload["domain"] != domain_name:
        raise ValueError(
            "Pattern "
            f"{payload['pattern_id']} declares domain {payload['domain']}, "
            f"expected {domain_name}"
        )
    return PatternRecord(
        pattern_id=_ensure_string(payload["pattern_id"], "pattern_id"),
        domain=_ensure_string(payload["domain"], "domain"),
        title=_ensure_string(payload["title"], "title"),
        summary=_ensure_string(payload["summary"], "summary"),
        path=path,
        tags=_ensure_string_list(payload.get("tags", []), "tags"),
        version=_ensure_string(payload["version"], "version"),
        status=_ensure_string(payload["status"], "status"),
        source_path=source_path,
    )


def _load_domain_registry(index_path: Path, domain_name: str) -> DomainRegistry:
    payload = _ensure_object(load_json_file(index_path), f"{domain_name} index")
    if payload.get("domain") != domain_name:
        raise ValueError(f"Domain index mismatch for {index_path}: {payload.get('domain')}")
    rules_payload = payload.get("rules", [])
    patterns_payload = payload.get("patterns", [])
    if not isinstance(rules_payload, list):
        raise TypeError(f"{index_path} rules must be a list")
    if not isinstance(patterns_payload, list):
        raise TypeError(f"{index_path} patterns must be a list")
    base_dir = index_path.parent
    return DomainRegistry(
        domain=domain_name,
        version=_ensure_string(payload["version"], f"{domain_name} version"),
        status=_ensure_string(payload["status"], f"{domain_name} status"),
        rules=tuple(_load_rule(entry, domain_name, base_dir) for entry in rules_payload),
        patterns=tuple(_load_pattern(entry, domain_name, base_dir) for entry in patterns_payload),
    )


def _load_registry_snapshot(index_path: Path) -> RegistrySnapshot:
    root_index_path = _normalise_index_path(index_path)
    payload = _ensure_object(load_json_file(root_index_path), "standards registry")
    domains = payload.get("domains")
    if not isinstance(domains, dict):
        raise TypeError("standards registry domains must be an object")

    loaded_domains: dict[str, DomainRegistry] = {}
    for domain_name, relative_index_path in sorted(domains.items()):
        if domain_name not in SUPPORTED_DOMAINS:
            raise ValueError(f"Unsupported domain in registry: {domain_name}")
        relative_path = _ensure_string(relative_index_path, f"{domain_name} index path")
        resolved_index_path = _resolve_existing_path(
            root_index_path.parent,
            relative_path,
            boundary_root=root_index_path.parent,
        )
        loaded_domains[domain_name] = _load_domain_registry(resolved_index_path, domain_name)

    return RegistrySnapshot(
        name=_ensure_string(payload["name"], "registry name"),
        version=_ensure_string(payload["version"], "registry version"),
        status=_ensure_string(payload["status"], "registry status"),
        domains=loaded_domains,
    )


def _merge_domain_registry(base: DomainRegistry, overlay: DomainRegistry) -> DomainRegistry:
    merged_rules = {rule.rule_id: rule for rule in base.rules}
    merged_rules.update({rule.rule_id: rule for rule in overlay.rules})
    merged_patterns = {pattern.pattern_id: pattern for pattern in base.patterns}
    merged_patterns.update({pattern.pattern_id: pattern for pattern in overlay.patterns})
    return DomainRegistry(
        domain=base.domain,
        version=overlay.version,
        status=overlay.status,
        rules=tuple(sorted(merged_rules.values(), key=lambda rule: rule.rule_id)),
        patterns=tuple(sorted(merged_patterns.values(), key=lambda pattern: pattern.pattern_id)),
    )


def _merge_registry_snapshots(
    base: RegistrySnapshot,
    overlay: RegistrySnapshot,
) -> RegistrySnapshot:
    merged_domains = dict(base.domains)
    for domain_name, overlay_domain in overlay.domains.items():
        base_domain = merged_domains.get(domain_name)
        if base_domain is None:
            merged_domains[domain_name] = overlay_domain
            continue
        merged_domains[domain_name] = _merge_domain_registry(base_domain, overlay_domain)
    return RegistrySnapshot(
        name=base.name,
        version=base.version,
        status=base.status,
        domains=merged_domains,
    )


def load_registry(
    index_path: Path | None = None,
    *,
    overlay_paths: list[Path] | None = None,
) -> RegistrySnapshot:
    snapshot = _load_registry_snapshot(_normalise_index_path(index_path))
    for overlay_path in overlay_paths or []:
        overlay_snapshot = _load_registry_snapshot(_normalise_index_path(overlay_path))
        snapshot = _merge_registry_snapshots(snapshot, overlay_snapshot)
    return snapshot
