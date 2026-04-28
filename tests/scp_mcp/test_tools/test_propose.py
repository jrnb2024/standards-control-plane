from __future__ import annotations

import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

from standards_control_plane.mcp_server import tools


def _init_git_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.email", "scp@example.com"], cwd=repo_root, check=True)
    subprocess.run(["git", "config", "user.name", "SCP MCP Tests"], cwd=repo_root, check=True)
    (repo_root / "README.md").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo_root, check=True)
    subprocess.run(["git", "commit", "-m", "seed"], cwd=repo_root, check=True, capture_output=True, text=True)
    return repo_root


def test_propose_creates_branch_and_stub_file(tmp_path: Path) -> None:
    repo_root = _init_git_repo(tmp_path)
    proposals_root = repo_root / "docs" / "reviews" / "proposals"

    response = tools.propose_impl(
        tools.ProposeRequest(title="Add MCP policy", body="Queue this for later adjudication."),
        proposals_root=proposals_root,
        repo_root=repo_root,
        now=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
    )

    current_branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    assert isinstance(response, tools.ProposeResponse)
    assert response.proposal_id == "PROP-001"
    assert current_branch == response.branch_name
    assert (proposals_root / "PROP-001.md").exists()


def test_propose_does_not_write_file_when_branch_creation_fails(tmp_path: Path, monkeypatch) -> None:
    proposals_root = tmp_path / "docs" / "reviews" / "proposals"
    monkeypatch.setattr(
        tools,
        "_create_proposal_branch",
        lambda *, repo_root, branch_name: (_ for _ in ()).throw(RuntimeError("branch create failed")),
    )

    response = tools.propose_impl(
        tools.ProposeRequest(title="Add MCP policy", body="Queue this for later adjudication."),
        proposals_root=proposals_root,
        repo_root=tmp_path,
        now=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
    )

    assert isinstance(response, tools.ErrorResponse)
    assert response.error_code == "SCP-MCP-E021"
    assert not list(proposals_root.glob("PROP-*.md"))


def test_propose_rejects_duplicate_normalised_content(tmp_path: Path) -> None:
    repo_root = _init_git_repo(tmp_path)
    proposals_root = repo_root / "docs" / "reviews" / "proposals"

    first = tools.propose_impl(
        tools.ProposeRequest(title="Add MCP policy", body="Queue this for later adjudication."),
        proposals_root=proposals_root,
        repo_root=repo_root,
        now=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
    )
    assert isinstance(first, tools.ProposeResponse)

    duplicate = tools.propose_impl(
        tools.ProposeRequest(
            title="Add   MCP   policy",
            body="Queue this   for later adjudication.",
        ),
        proposals_root=proposals_root,
        repo_root=repo_root,
        now=datetime(2026, 4, 28, 12, 5, tzinfo=timezone.utc),
    )

    assert isinstance(duplicate, tools.ErrorResponse)
    assert duplicate.error_code == "SCP-MCP-E020"


def test_propose_rejects_duplicate_with_invisible_unicode(tmp_path: Path) -> None:
    repo_root = _init_git_repo(tmp_path)
    proposals_root = repo_root / "docs" / "reviews" / "proposals"

    first = tools.propose_impl(
        tools.ProposeRequest(title="Add MCP policy", body="Queue this for later adjudication."),
        proposals_root=proposals_root,
        repo_root=repo_root,
        now=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
    )
    assert isinstance(first, tools.ProposeResponse)

    duplicate = tools.propose_impl(
        tools.ProposeRequest(
            title="Add\u2028MCP policy",
            body="Queue this for later\u200eadjudication.",
        ),
        proposals_root=proposals_root,
        repo_root=repo_root,
        now=datetime(2026, 4, 28, 12, 5, tzinfo=timezone.utc),
    )

    assert isinstance(duplicate, tools.ErrorResponse)
    assert duplicate.error_code == "SCP-MCP-E020"


def test_propose_rejects_nul_bytes(tmp_path: Path) -> None:
    proposals_root = tmp_path / "docs" / "reviews" / "proposals"

    response = tools.propose_impl(
        tools.ProposeRequest(title="Add MCP policy", body="Queue\x00this for later adjudication."),
        proposals_root=proposals_root,
        repo_root=tmp_path,
        now=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
    )

    assert isinstance(response, tools.ErrorResponse)
    assert response.error_code == "SCP-MCP-E021"
    assert not list(proposals_root.glob("PROP-*.md"))


def test_propose_serialises_distinct_concurrent_submissions(tmp_path: Path, monkeypatch) -> None:
    proposals_root = tmp_path / "docs" / "reviews" / "proposals"
    barrier = threading.Barrier(3)
    responses: list[tools.ProposeResponse | tools.ErrorResponse] = []

    monkeypatch.setattr(tools, "_create_proposal_branch", lambda *, repo_root, branch_name: None)

    def _worker(title: str, body: str) -> None:
        barrier.wait()
        response = tools.propose_impl(
            tools.ProposeRequest(title=title, body=body),
            proposals_root=proposals_root,
            repo_root=tmp_path,
            now=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        )
        responses.append(response)

    threads = [
        threading.Thread(target=_worker, args=("Proposal one", "First body"), daemon=True),
        threading.Thread(target=_worker, args=("Proposal two", "Second body"), daemon=True),
    ]
    for thread in threads:
        thread.start()
    barrier.wait()
    for thread in threads:
        thread.join()

    successes = [response for response in responses if isinstance(response, tools.ProposeResponse)]
    assert len(successes) == 2
    assert {response.proposal_id for response in successes} == {"PROP-001", "PROP-002"}
    assert sorted(path.name for path in proposals_root.glob("PROP-*.md")) == ["PROP-001.md", "PROP-002.md"]


def test_propose_rejects_identical_concurrent_submissions(tmp_path: Path, monkeypatch) -> None:
    proposals_root = tmp_path / "docs" / "reviews" / "proposals"
    barrier = threading.Barrier(3)
    responses: list[tools.ProposeResponse | tools.ErrorResponse] = []

    monkeypatch.setattr(tools, "_create_proposal_branch", lambda *, repo_root, branch_name: None)

    def _worker() -> None:
        barrier.wait()
        response = tools.propose_impl(
            tools.ProposeRequest(title="Duplicate proposal", body="Same body"),
            proposals_root=proposals_root,
            repo_root=tmp_path,
            now=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        )
        responses.append(response)

    threads = [threading.Thread(target=_worker, daemon=True) for _ in range(2)]
    for thread in threads:
        thread.start()
    barrier.wait()
    for thread in threads:
        thread.join()

    successes = [response for response in responses if isinstance(response, tools.ProposeResponse)]
    failures = [response for response in responses if isinstance(response, tools.ErrorResponse)]
    assert len(successes) == 1
    assert len(failures) == 1
    assert failures[0].error_code == "SCP-MCP-E020"
    assert sorted(path.name for path in proposals_root.glob("PROP-*.md")) == ["PROP-001.md"]
