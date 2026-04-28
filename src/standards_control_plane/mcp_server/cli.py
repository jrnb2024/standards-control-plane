"""CLI entry points for the Standards Control Plane MCP server scaffold."""

from __future__ import annotations

import argparse
import asyncio
import errno
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Sequence

from .server import MissingMcpDependencyError, ScpMcpServer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Standards Control Plane MCP server")
    parser.add_argument(
        "--stdio-test",
        action="store_true",
        help="Run a one-shot handshake and print the empty tool/resource listings",
    )

    subparsers = parser.add_subparsers(dest="command")

    serve_parser = subparsers.add_parser(
        "serve",
        help="Start the Standards Control Plane MCP server on stdio",
    )
    serve_parser.set_defaults(func=cmd_serve)

    keygen_parser = subparsers.add_parser(
        "keygen",
        help="Generate an Ed25519 signing keypair for MCP receipt signing",
    )
    keygen_parser.add_argument("--out", required=True, help="Path to the private key file to write")
    keygen_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the target private and public key files if they already exist",
    )
    keygen_parser.set_defaults(func=cmd_keygen)

    return parser


def _write_bytes(path: Path, payload: bytes, mode: int, *, overwrite: bool) -> None:
    flags = os.O_WRONLY | os.O_CREAT
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= os.O_TRUNC if overwrite else os.O_EXCL
    try:
        fd = os.open(path, flags, 0o000)
    except OSError as error:
        if error.errno == errno.ELOOP:
            raise FileExistsError(f"Refusing to write through symlink target: {path}") from error
        raise
    try:
        os.fchmod(fd, mode)
        handle = os.fdopen(fd, "wb")
        fd = -1
        with handle:
            handle.write(payload)
    except Exception:
        if fd != -1:
            os.close(fd)
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


def _key_id_from_public_key_bytes(raw_public_key: bytes) -> str:
    return hashlib.sha256(raw_public_key).hexdigest()[:16]


def _restore_previous_bytes(path: Path, previous_payload: bytes | None, mode: int) -> None:
    if previous_payload is None:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        return
    _write_bytes(path, previous_payload, mode, overwrite=True)


def _refuse_symlink_target(path: Path) -> None:
    if path.is_symlink():
        raise FileExistsError(f"Refusing to write through symlink target: {path}")


def _generate_keypair(out_path: Path, *, force: bool) -> str:
    try:
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519
    except ImportError as error:  # pragma: no cover - exercised without extras only
        raise RuntimeError(
            "The key generator requires the optional 'mcp' extra. "
            "Install standards-control-plane[mcp]."
        ) from error

    public_path = Path(f"{out_path}.pub")
    _refuse_symlink_target(out_path)
    _refuse_symlink_target(public_path)
    existing_targets = [path for path in (out_path, public_path) if path.exists()]
    if existing_targets and not force:
        raise FileExistsError(
            "Refusing to overwrite existing key material: "
            + ", ".join(str(path) for path in existing_targets)
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    previous_private_payload = out_path.read_bytes() if force and out_path.exists() else None
    previous_public_payload = public_path.read_bytes() if force and public_path.exists() else None
    private_key = ed25519.Ed25519PrivateKey.generate()
    private_payload = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    # The key-id must track the canonical Ed25519 public key bytes, not the
    # OpenSSH file encoding used for serialisation.
    raw_public_key = private_key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    public_payload = private_key.public_key().public_bytes(
        serialization.Encoding.OpenSSH,
        serialization.PublicFormat.OpenSSH,
    )
    public_file_payload = public_payload + b"\n"

    private_written = False
    try:
        _write_bytes(out_path, private_payload, 0o600, overwrite=force)
        private_written = True
        _write_bytes(public_path, public_file_payload, 0o644, overwrite=force)
    except Exception as error:
        if private_written:
            try:
                _restore_previous_bytes(out_path, previous_private_payload, 0o600)
                _restore_previous_bytes(public_path, previous_public_payload, 0o644)
            except Exception as restore_error:
                raise RuntimeError(
                    "Key generation failed and previous key material could not be restored."
                ) from restore_error
        raise
    return _key_id_from_public_key_bytes(raw_public_key)


def cmd_serve(_args: argparse.Namespace) -> int:
    try:
        ScpMcpServer().run_stdio()
    except MissingMcpDependencyError as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


def cmd_keygen(args: argparse.Namespace) -> int:
    if sys.platform == "win32" or sys.platform == "cygwin":
        raise SystemExit(
            "scp-mcp-server keygen is not supported on Windows; use a POSIX system"
        )
    try:
        key_id = _generate_keypair(Path(args.out).expanduser(), force=bool(args.force))
    except (OSError, RuntimeError) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(key_id)
    return 0


def cmd_stdio_test() -> int:
    try:
        payload = asyncio.run(ScpMcpServer().handshake_payload())
    except MissingMcpDependencyError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(payload, sort_keys=True))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    if args.stdio_test:
        if getattr(args, "command", None) is not None:
            parser.error("--stdio-test cannot be combined with a subcommand")
        return cmd_stdio_test()
    if getattr(args, "func", None) is None:
        parser.print_help(sys.stderr)
        return 1
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
