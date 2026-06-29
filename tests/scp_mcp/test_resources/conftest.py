from __future__ import annotations

import asyncio
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from standards_control_plane.mcp_server.resources import ScpCommittedResourceCatalog, register_resources
from standards_control_plane.mcp_server.server import _load_fastmcp


def _git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        capture_output=True,
        check=False,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr or completed.stdout or f"git {' '.join(args)} failed")
    return completed.stdout


def _write_files(repo_root: Path, files: dict[str, str]) -> None:
    for relative_path, content in files.items():
        destination = repo_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")


def _initial_fixture_files() -> dict[str, str]:
    return {
        "standards/standards-index.json": json.dumps(
            {
                "name": "standards-control-plane",
                "version": "2026-04-28",
                "status": "active",
                "domains": {
                    "governance": "governance/index.json",
                    "architecture": "architecture/index.json",
                    "service-lifecycle": "service-lifecycle/index.json",
                },
            },
            indent=2,
        )
        + "\n",
        "standards/governance/index.json": json.dumps(
            {
                "domain": "governance",
                "version": "1.0.0",
                "status": "active",
                "rules": [
                    {
                        "rule_id": "GOV-001",
                        "domain": "governance",
                        "title": "Governance rule",
                        "summary": "Governance summary",
                        "path": "rules/GOV-001.md",
                        "severity_default": "high",
                        "scope": ["all"],
                        "signals": ["missing review evidence"],
                        "exceptions": [],
                        "related_patterns": [],
                        "version": "1.0.0",
                        "status": "active",
                        "applies_to": ["docs/**/*.md", "docs/DECISIONS.md"],
                    }
                ],
                "patterns": [],
            },
            indent=2,
        )
        + "\n",
        "standards/architecture/index.json": json.dumps(
            {
                "domain": "architecture",
                "version": "1.0.0",
                "status": "active",
                "rules": [
                    {
                        "rule_id": "ARCH-001",
                        "domain": "architecture",
                        "title": "Architecture rule",
                        "summary": "Architecture summary",
                        "path": "rules/ARCH-001.md",
                        "severity_default": "medium",
                        "scope": ["backend"],
                        "signals": ["direct backend coupling"],
                        "exceptions": [],
                        "related_patterns": [],
                        "version": "1.0.0",
                        "status": "active",
                        "applies_to": ["src/**/*.py"],
                    }
                ],
                "patterns": [],
            },
            indent=2,
        )
        + "\n",
        "standards/service-lifecycle/index.json": json.dumps(
            {
                "domain": "service-lifecycle",
                "version": "1.0.0",
                "status": "active",
                "rules": [
                    {
                        "rule_id": "SVC-001",
                        "domain": "service-lifecycle",
                        "title": "Service contract rule",
                        "summary": "Service summary",
                        "path": "rules/SVC-001.md",
                        "severity_default": "high",
                        "scope": ["all"],
                        "signals": ["services.yml missing contract"],
                        "exceptions": [],
                        "related_patterns": [],
                        "version": "1.0.0",
                        "status": "active",
                    },
                    {
                        # No applies_to → inherits the deploy-script globs from
                        # _FALLBACK_APPLIES_TO_BY_RULE_ID["SVC-004"] (added #222).
                        "rule_id": "SVC-004",
                        "domain": "service-lifecycle",
                        "title": "Deploy recipe rule",
                        "summary": "Deploy summary",
                        "path": "rules/SVC-004.md",
                        "severity_default": "high",
                        "scope": ["all"],
                        "signals": ["non-canonical deploy script"],
                        "exceptions": [],
                        "related_patterns": [],
                        "version": "1.0.0",
                        "status": "active",
                    },
                ],
                "patterns": [],
            },
            indent=2,
        )
        + "\n",
        "standards/governance/rules/GOV-001.md": "# GOV-001\n\nCommitted governance rule.\n",
        "standards/architecture/rules/ARCH-001.md": "# ARCH-001\n\nCommitted architecture rule.\n",
        "standards/service-lifecycle/rules/SVC-001.md": "# SVC-001\n\nCommitted service rule.\n",
        "standards/service-lifecycle/rules/SVC-004.md": "# SVC-004\n\nCommitted deploy rule.\n",
        "docs/DECISIONS.md": "\n".join(
            [
                "# Decisions",
                "",
                "| ID | Date | Decision | Status | Rationale |",
                "|----|------|----------|--------|-----------|",
                "| D-024 | 2026-04-21 | Use MCP | ACCEPTED | Native protocol |",
                "| D-028 | 2026-04-28 | Use DPBM | ACCEPTED | Design parity |",
                "| D-1000 | 2026-04-28 | Long-running numbering | ACCEPTED | Future-proof parsing |",
                "| not-a-row | ignore | me | please | thanks |",
                "",
            ]
        ),
        "docs/STATUS.md": "\n".join(
            [
                "# Status",
                "",
                "**Last Updated:** 2026-04-28",
                "**Current Branch:** `main`",
                "**Current Work Package:** `WP-SCP-022`",
                "**Current State:** Resource slice active",
                "",
                "## Summary",
                "",
                "- resource registry committed",
                "- tests active",
                "",
            ]
        ),
        "docs/security/mcp-signing-keys.pub": "\n".join(
            [
                "# key ring",
                "ssh-ed25519 AAAAOLD key_id=scp-mcp-2026-01 current=false retain_until=2026-07-01",
                "ssh-ed25519 AAAANEW key_id=scp-mcp-2026-04 current=true retain_until=2026-10-01",
                "",
            ]
        ),
        "output/findings/open-findings.json": json.dumps(
            {
                "findings": [
                    {
                        "finding_id": "F-OPEN-001",
                        "domain": "governance",
                        "severity": "medium",
                        "summary": "Open and unwaived",
                        "status": "open",
                        "rule_id": "GOV-001",
                    },
                    {
                        "finding_id": "F-OPEN-002",
                        "domain": "architecture",
                        "severity": "high",
                        "summary": "Open but waived",
                        "status": "open",
                        "rule_id": "ARCH-001",
                    },
                ]
            },
            indent=2,
        )
        + "\n",
        "output/findings/findings-history.json": json.dumps(
            {
                "findings": [
                    {
                        "finding_id": "F-OPEN-003",
                        "domain": "service-lifecycle",
                        "severity": "high",
                        "summary": "Open with expired waiver",
                        "status": "open",
                        "rule_id": "SVC-001",
                    },
                    {
                        "finding_id": "F-RESOLVED-001",
                        "domain": "governance",
                        "severity": "low",
                        "summary": "Resolved finding",
                        "status": "resolved",
                        "rule_id": "GOV-001",
                    },
                ]
            },
            indent=2,
        )
        + "\n",
        "output/findings/waivers.json": json.dumps(
            [
                {
                    "waiver_id": "W-001",
                    "finding_id": "F-OPEN-002",
                    "rule_id": "ARCH-001",
                    "reason": "Temporary exception",
                    "approved_by": "@owner",
                    "expires_at": "2026-05-10T00:00:00Z",
                },
                {
                    "waiver_id": "W-002",
                    "finding_id": "F-OPEN-003",
                    "rule_id": "SVC-001",
                    "reason": "Expired exception",
                    "approved_by": "@owner",
                    "expires_at": "2026-04-01T00:00:00Z",
                },
            ],
            indent=2,
        )
        + "\n",
    }


def create_resource_repo(tmp_path: Path, extra_files: dict[str, str] | None = None) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _git(repo_root, "init", "-b", "main")
    _git(repo_root, "config", "user.name", "Codex")
    _git(repo_root, "config", "user.email", "codex@example.com")
    files = _initial_fixture_files()
    if extra_files:
        files.update(extra_files)
    _write_files(repo_root, files)
    _git(repo_root, "add", ".")
    _git(repo_root, "commit", "-m", "Initial committed state")
    return repo_root


def commit_file(repo_root: Path, relative_path: str, content: str, message: str) -> None:
    _write_files(repo_root, {relative_path: content})
    _git(repo_root, "add", relative_path)
    _git(repo_root, "commit", "-m", message)


def read_server_resource(server: Any, uri: str) -> dict[str, Any]:
    contents = asyncio.run(server.read_resource(uri))
    return json.loads(contents[0].content)


def list_server_resources(server: Any) -> list[str]:
    resources = asyncio.run(server.list_resources())
    return sorted(resource.uri for resource in resources)


def list_server_resource_templates(server: Any) -> list[str]:
    templates = asyncio.run(server.list_resource_templates())
    return sorted(template.uriTemplate for template in templates)


@pytest.fixture
def fixed_now() -> datetime:
    return datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def resource_repo(tmp_path: Path) -> Path:
    return create_resource_repo(tmp_path)


@pytest.fixture
def resource_catalog(resource_repo: Path, fixed_now: datetime) -> ScpCommittedResourceCatalog:
    return ScpCommittedResourceCatalog(repo_root=resource_repo, now_func=lambda: fixed_now)


@pytest.fixture
def resource_server(resource_repo: Path, fixed_now: datetime) -> Any:
    fast_mcp = _load_fastmcp()
    server = fast_mcp(name="test-scp-resources")
    register_resources(server, repo_root=resource_repo, now_func=lambda: fixed_now)
    return server
