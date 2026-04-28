from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import create_resource_repo


def test_signing_keys_resource_serves_current_and_prior_keys(resource_catalog) -> None:
    payload = resource_catalog.read_static("scp://security/signing-keys")

    assert payload["schema_version"] == "1.0.0"
    assert payload["key_id"] == "scp-mcp-2026-04"
    assert payload["current_key"]["key_id"] == "scp-mcp-2026-04"
    assert payload["current_key"]["public_key_sha256"] == payload["current_key_sha256"]
    assert payload["prior_keys"] == [
        {
            "algorithm": "ssh-ed25519",
            "public_key": "AAAAOLD",
            "key_id": "scp-mcp-2026-01",
            "current": False,
            "retain_until": "2026-07-01",
            "public_key_sha256": "297883e9bb8024a2c0ee2298f420e26b8549800fee2640816544b9abf45fecfb",
        }
    ]
    assert payload["trust_model"]["transport_trust_required"] is True
    assert "pinned sha256" in payload["trust_model"]["verification_roots"][1]
    assert "raw_text" not in payload


def test_signing_keys_require_exactly_one_current_marker(tmp_path: Path, fixed_now) -> None:
    from standards_control_plane.mcp_server.resources import ScpCommittedResourceCatalog

    resource_repo = create_resource_repo(
        tmp_path,
        extra_files={
            "docs/security/mcp-signing-keys.pub": "\n".join(
                [
                    "# key ring",
                    "ssh-ed25519 AAAAOLD key_id=scp-mcp-2026-01 current=false retain_until=2026-07-01",
                    "ssh-ed25519 AAAANEW key_id=scp-mcp-2026-04 retain_until=2026-10-01",
                    "",
                ]
            )
        },
    )
    catalog = ScpCommittedResourceCatalog(repo_root=resource_repo, now_func=lambda: fixed_now)

    with pytest.raises(RuntimeError, match="no current signing key declared"):
        catalog.read_static("scp://security/signing-keys")
