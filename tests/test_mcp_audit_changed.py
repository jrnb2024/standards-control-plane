"""End-to-end tests for the MCP audit_changed tool's adopter-repo surface.

WP-SCP-038 defect 2: the audit_changed MCP tool exposed only base_ref/head_ref,
so a scope whose area could not be inferred died with an unrecoverable
SCP-MCP-E021. These tests exercise the new repo_root / subsystem / area_hint
fields against a real second git repo and assert the error is now recoverable.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from standards_control_plane.mcp_server import tools


@pytest.fixture(autouse=True)
def _isolated_audit_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """The MCP audit path shells out to ``python -m standards_control_plane.cli``
    via ``sys.executable``. Under pytest the package is importable in-process
    (injected sys.path) but that interpreter's site-packages may not carry it,
    so make the child importable by putting the ``src`` dir on PYTHONPATH.
    Also isolate the module-level audit cache between tests."""
    src_dir = str(Path(tools.__file__).resolve().parents[2])
    existing = os.environ.get("PYTHONPATH", "")
    monkeypatch.setenv("PYTHONPATH", src_dir + (os.pathsep + existing if existing else ""))
    tools._AUDIT_CHANGED_CACHE.clear()
    yield
    tools._AUDIT_CHANGED_CACHE.clear()


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


def _init_non_inferable_repo(repo: Path) -> None:
    """Temp git repo whose head commit changes a plain python file — no ENH
    spec and no frontend route, so area_id CANNOT be inferred from the diff."""
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init")
    _git(repo, "config", "user.name", "Adopter")
    _git(repo, "config", "user.email", "adopter@example.com")
    (repo / "README.md").write_text("base\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "base")

    lib_dir = repo / "lib"
    lib_dir.mkdir()
    (lib_dir / "thing.py").write_text("VALUE = 1\n", encoding="utf-8")
    _git(repo, "add", "lib/thing.py")
    _git(repo, "commit", "-m", "add thing")


def test_audit_changed_area_inference_miss_is_e021(tmp_path: Path) -> None:
    repo = tmp_path / "adopter"
    _init_non_inferable_repo(repo)

    response = tools.audit_changed_impl(
        tools.AuditChangedRequest(
            base_ref="HEAD~1",
            head_ref="HEAD",
            repo_root=str(repo),
            subsystem="pim",
        )
    )

    assert isinstance(response, tools.ErrorResponse)
    assert response.error_code == "SCP-MCP-E021"
    # Assert the failure is genuinely area inference — not a subprocess/import
    # break that would collapse to the same E021 and make this test vacuous.
    assert (
        "AreaIdInferenceError" in response.message
        or "area_id" in response.message.lower()
    ), response.message


def test_audit_changed_recovers_e021_with_area_hint(tmp_path: Path) -> None:
    """The same non-inferable scope succeeds once area_hint is supplied, and the
    result targets the adopter repo (changed_paths from THAT repo), not SCP."""
    repo = tmp_path / "adopter"
    _init_non_inferable_repo(repo)

    response = tools.audit_changed_impl(
        tools.AuditChangedRequest(
            base_ref="HEAD~1",
            head_ref="HEAD",
            repo_root=str(repo),
            subsystem="pim",
            area_hint="pim-enrichment",
        )
    )

    assert isinstance(response, tools.AuditChangedResponse)
    assert response.changed_paths == ["lib/thing.py"]
    assert response.audit_result["scope"]["area_id"] == "pim-enrichment"
