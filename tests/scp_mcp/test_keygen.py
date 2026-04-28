from __future__ import annotations

import argparse
import hashlib
import re
import stat
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from standards_control_plane.mcp_server import cli

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
    private_key = serialization.load_pem_private_key(private_key_path.read_bytes(), password=None)
    raw_public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    assert first.stdout.strip() == hashlib.sha256(raw_public_key).hexdigest()[:16]

    second = run_scp_mcp_server("keygen", "--out", str(private_key_path))
    assert second.returncode != 0
    assert "Refusing to overwrite existing key material" in second.stderr

    third = run_scp_mcp_server("keygen", "--out", str(private_key_path), "--force")
    assert third.returncode == 0, third.stderr
    assert re.fullmatch(r"[0-9a-f]{16}", third.stdout.strip())


def test_key_id_uses_raw_ed25519_public_key_bytes() -> None:
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(bytes(range(32)))
    raw_public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )

    assert cli._key_id_from_public_key_bytes(raw_public_key) == "56475aa75463474c"


def test_keygen_refuses_symlink_targets(tmp_path: Path) -> None:
    redirect_target = tmp_path / "redirect-target"
    redirect_target.write_text("sentinel", encoding="utf-8")
    private_key_path = tmp_path / "mcp-signing-key"
    private_key_path.symlink_to(redirect_target)

    result = run_scp_mcp_server("keygen", "--out", str(private_key_path), "--force")

    assert result.returncode != 0
    assert "symlink" in result.stderr.lower()
    assert redirect_target.read_text(encoding="utf-8") == "sentinel"
    assert not Path(f"{private_key_path}.pub").exists()


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="Windows runners do not support scp-mcp-server keygen",
)
def test_keygen_rejects_windows_platform(tmp_path: Path) -> None:
    args = argparse.Namespace(out=str(tmp_path / "mcp-signing-key"), force=False)

    with patch("sys.platform", "win32"):
        with pytest.raises(
            SystemExit,
            match="scp-mcp-server keygen is not supported on Windows; use a POSIX system",
        ):
            cli.cmd_keygen(args)


def test_keygen_restores_previous_keypair_when_public_write_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    private_key_path = tmp_path / "mcp-signing-key"
    public_key_path = Path(f"{private_key_path}.pub")
    private_key_path.write_bytes(b"old-private")
    public_key_path.write_bytes(b"old-public\n")

    original_write_bytes = cli._write_bytes
    public_write_failed = False

    def flaky_write(path: Path, payload: bytes, mode: int, *, overwrite: bool) -> None:
        nonlocal public_write_failed
        if path == public_key_path and not public_write_failed:
            public_write_failed = True
            raise PermissionError("simulated public key write failure")
        original_write_bytes(path, payload, mode, overwrite=overwrite)

    monkeypatch.setattr(cli, "_write_bytes", flaky_write)

    with pytest.raises(PermissionError, match="simulated public key write failure"):
        cli._generate_keypair(private_key_path, force=True)

    assert private_key_path.read_bytes() == b"old-private"
    assert public_key_path.read_bytes() == b"old-public\n"
