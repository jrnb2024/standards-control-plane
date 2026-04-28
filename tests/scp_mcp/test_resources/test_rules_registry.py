from __future__ import annotations

import json
from pathlib import Path

from .conftest import commit_file


def test_rules_registry_reads_committed_registry(resource_catalog) -> None:
    payload = resource_catalog.read_static("scp://rules/registry")

    assert payload["schema_version"] == "1.0.0"
    assert payload["key_id"] == "scp-mcp-2026-04"
    rules = payload["registry"]["domains"]["governance"]["rules"]
    assert rules[0]["rule_id"] == "GOV-001"
    assert rules[0]["applies_to"] == ["docs/**/*.md", "docs/DECISIONS.md"]

    service_rule = payload["registry"]["domains"]["service-lifecycle"]["rules"][0]
    assert service_rule["rule_id"] == "SVC-001"
    assert service_rule["applies_to"] == ["services.yml", "**/services.yml"]


def test_rules_registry_cache_invalidates_on_new_commit(resource_repo: Path, fixed_now) -> None:
    from standards_control_plane.mcp_server.resources import ScpCommittedResourceCatalog

    catalog = ScpCommittedResourceCatalog(repo_root=resource_repo, now_func=lambda: fixed_now)
    first = catalog.read_static("scp://rules/registry")
    first_key = catalog.cache_key()

    updated_index = {
        "domain": "governance",
        "version": "1.1.0",
        "status": "active",
        "rules": [
            {
                "rule_id": "GOV-001",
                "domain": "governance",
                "title": "Governance rule updated",
                "summary": "Governance summary",
                "path": "rules/GOV-001.md",
                "severity_default": "high",
                "scope": ["all"],
                "signals": ["missing review evidence"],
                "exceptions": [],
                "related_patterns": [],
                "version": "1.1.0",
                "status": "active",
                "applies_to": ["docs/**/*.md", "docs/DECISIONS.md"],
            }
        ],
        "patterns": [],
    }
    commit_file(
        resource_repo,
        "standards/governance/index.json",
        json.dumps(updated_index, indent=2) + "\n",
        "Update governance rule title",
    )

    second = catalog.read_static("scp://rules/registry")
    second_key = catalog.cache_key()

    assert first["registry"]["domains"]["governance"]["rules"][0]["title"] == "Governance rule"
    assert second["registry"]["domains"]["governance"]["rules"][0]["title"] == "Governance rule updated"
    assert first_key != second_key
