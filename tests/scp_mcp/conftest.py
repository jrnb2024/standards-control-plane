from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def resolve_scp_mcp_server() -> list[str]:
    executable = str(Path(sys.executable).with_name("scp-mcp-server"))
    if not Path(executable).exists():
        executable = shutil.which("scp-mcp-server") or ""
    if executable:
        return [executable]
    return [sys.executable, "-m", "standards_control_plane.mcp_server.cli"]


def run_scp_mcp_server(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = resolve_scp_mcp_server()
    env = dict(os.environ)
    pythonpath_parts = [str(REPO_ROOT / "src")]
    if env.get("PYTHONPATH"):
        pythonpath_parts.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    return subprocess.run(
        [*command, *args],
        capture_output=True,
        check=False,
        cwd=cwd or REPO_ROOT,
        env=env,
        text=True,
    )
