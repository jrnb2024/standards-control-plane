from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def resolve_scp_mcp_server() -> str:
    executable = str(Path(sys.executable).with_name("scp-mcp-server"))
    if not Path(executable).exists():
        executable = shutil.which("scp-mcp-server") or ""
    if not executable:
        raise AssertionError(
            "scp-mcp-server is not on PATH; install the package with `pip install -e '.[dev,mcp]'`"
        )
    return executable


def run_scp_mcp_server(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    executable = resolve_scp_mcp_server()
    return subprocess.run(
        [executable, *args],
        capture_output=True,
        check=False,
        cwd=cwd or REPO_ROOT,
        text=True,
    )
