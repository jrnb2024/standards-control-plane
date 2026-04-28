from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from standards_control_plane.mcp_server import tools

_METADATA_PATTERN = re.compile(r"<!--\s*proposal_metadata:\s*(\{.*?\})\s*-->", re.DOTALL)


def _init_git_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "scp@example.com"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "SCP MCP Hardening Tests"], cwd=repo_root, check=True)
    (repo_root / "README.md").write_text("seed\n", encoding="utf-8")
    signing_keys_path = repo_root / "docs" / "security" / "mcp-signing-keys.pub"
    signing_keys_path.parent.mkdir(parents=True, exist_ok=True)
    signing_keys_path.write_text(
        "\n".join(
            [
                "# key ring",
                "ssh-ed25519 AAAAHARDEN key_id=scp-mcp-hardening-key current=true retain_until=2026-10-01",
                "",
            ]
        ),
        encoding="utf-8",
    )
    subprocess.run(["git", "add", "README.md", "docs/security/mcp-signing-keys.pub"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-m", "seed"], cwd=repo_root, check=True, capture_output=True, text=True)
    return repo_root


def _proposal_request(
    title: str,
    body: str,
    *,
    affected_repos: list[str] | None = None,
    rule_id: str | None = None,
) -> tools.ProposeRequest:
    return tools.ProposeRequest(
        title=title,
        body=body,
        affected_repos=affected_repos or ["standards-control-plane"],
        rule_id=rule_id,
    )


def _proposal_metadata(proposal_path: Path) -> dict[str, object]:
    match = _METADATA_PATTERN.search(proposal_path.read_text(encoding="utf-8"))
    assert match is not None
    return json.loads(match.group(1))


def test_propose_rate_limits_the_eleventh_call(tmp_path: Path) -> None:
    repo_root = _init_git_repo(tmp_path)
    proposals_root = repo_root / "docs" / "reviews" / "proposals"
    caller_id = "stdio:123:/tmp/scp-mcp-server"
    start = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)

    for index in range(10):
        response = tools.propose_impl(
            _proposal_request(
                title=f"Proposal {index + 1}",
                body=f"Body {index + 1}",
            ),
            proposals_root=proposals_root,
            repo_root=repo_root,
            now=start + timedelta(minutes=index),
            caller_id=caller_id,
            signing_key_id="scp-mcp-hardening-key",
        )
        assert isinstance(response, tools.ProposeResponse)

    eleventh = tools.propose_impl(
        _proposal_request(title="Proposal 11", body="Body 11"),
        proposals_root=proposals_root,
        repo_root=repo_root,
        now=start + timedelta(minutes=59),
        caller_id=caller_id,
        signing_key_id="scp-mcp-hardening-key",
    )

    assert isinstance(eleventh, tools.ErrorResponse)
    assert eleventh.error_code == "SCP-MCP-E020"


def test_propose_rejects_markdown_normalised_duplicate_within_24_hours(tmp_path: Path) -> None:
    repo_root = _init_git_repo(tmp_path)
    proposals_root = repo_root / "docs" / "reviews" / "proposals"
    start = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)

    first = tools.propose_impl(
        _proposal_request(
            title="Markdown proposal",
            body="## Queue\n\n- Ship the **policy** after review.",
        ),
        proposals_root=proposals_root,
        repo_root=repo_root,
        now=start,
        caller_id="stdio:111:/tmp/scp-mcp-server",
        signing_key_id="scp-mcp-hardening-key",
    )
    assert isinstance(first, tools.ProposeResponse)

    duplicate = tools.propose_impl(
        _proposal_request(
            title="Different title",
            body="queue ship the policy after review.",
        ),
        proposals_root=proposals_root,
        repo_root=repo_root,
        now=start + timedelta(hours=23, minutes=59),
        caller_id="stdio:222:/tmp/scp-mcp-server",
        signing_key_id="scp-mcp-hardening-key",
    )

    assert isinstance(duplicate, tools.ErrorResponse)
    assert duplicate.error_code == "SCP-MCP-E020"


def test_propose_injects_the_silent_rot_banner_front_matter(tmp_path: Path) -> None:
    repo_root = _init_git_repo(tmp_path)
    proposals_root = repo_root / "docs" / "reviews" / "proposals"
    timestamp = datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc)

    response = tools.propose_impl(
        _proposal_request(title="Banner proposal", body="Queue this until adjudication ships."),
        proposals_root=proposals_root,
        repo_root=repo_root,
        now=timestamp,
        caller_id="stdio:333:/tmp/scp-mcp-server",
        signing_key_id="scp-mcp-hardening-key",
    )

    assert isinstance(response, tools.ProposeResponse)
    proposal_text = (proposals_root / "PROP-001.md").read_text(encoding="utf-8")
    assert proposal_text.startswith(
        "\n".join(
            [
                "---",
                "adjudication_status: queued_no_adjudicator",
                "expected_review_date: null",
                "queued_at: 2026-04-28T12:00:00Z",
                "---",
                "> NOTE: WP-SCP-022-proposal-queue adjudication workflow is not yet live;",
                "> proposals queue until adjudication ships. Status updates land via",
                "> GitHub issue on this branch (proposals/PROP-001). See",
                "> docs/plans/WP-SCP-022-implementation-programme-plan.md §12.",
            ]
        )
    )


def test_propose_records_envelope_fields_with_stdio_identity(tmp_path: Path) -> None:
    repo_root = _init_git_repo(tmp_path)
    proposals_root = repo_root / "docs" / "reviews" / "proposals"

    response = tools.propose_impl(
        _proposal_request(
            title="Envelope proposal",
            body="Record the MCP origin envelope.",
            affected_repos=["standards-control-plane", "acc"],
            rule_id="ARCH-001",
        ),
        proposals_root=proposals_root,
        repo_root=repo_root,
        now=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
    )

    assert isinstance(response, tools.ProposeResponse)
    metadata = _proposal_metadata(proposals_root / "PROP-001.md")
    assert metadata["mcp_origin"] is True
    assert metadata["caller_id"].startswith(f"stdio:{os.getpid()}:")
    assert metadata["signing_key_id"] == "scp-mcp-hardening-key"
