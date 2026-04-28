from __future__ import annotations

import re
import stat
from pathlib import Path

from .conftest import run_scp_mcp_server


def test_keygen_creates_keypair_and_honours_force(tmp_path: Path) -> None:
    private_key_path = tmp_path / "mcp-signing-key"
    public_key_path = Path(f"{private_key_path}.pub")

    first = run_scp_mcp_server("keygen", "--out", str(private_key_path))
    assert first.returncode == 0, first.stderr
    assert re.fullmatch(r"[0-9a-f]{16}", first.stdout.strip())

    assert private_key_path.exists()
    assert public_key_path.exists()
    assert stat.S_IMODE(private_key_path.stat().st_mode) == 0o600
    assert stat.S_IMODE(public_key_path.stat().st_mode) == 0o644

    second = run_scp_mcp_server("keygen", "--out", str(private_key_path))
    assert second.returncode != 0
    assert "Refusing to overwrite existing key material" in second.stderr

    third = run_scp_mcp_server("keygen", "--out", str(private_key_path), "--force")
    assert third.returncode == 0, third.stderr
    assert re.fullmatch(r"[0-9a-f]{16}", third.stdout.strip())
