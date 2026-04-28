from __future__ import annotations

import pytest

from standards_control_plane.mcp_server.resources import _parse_signing_keys


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
    assert payload["error"] is None
    assert payload["trust_model"]["transport_trust_required"] is True
    assert "operator-distributed public key hash" in payload["trust_model"]["verification_roots"][1]
    assert "out-of-band trust anchor" in payload["trust_model"]["adopter_requirement"]
    assert "or a pinned sha256" not in payload["trust_model"]["adopter_requirement"]
    assert "raw_text" not in payload


def test_parse_signing_keys_requires_exactly_one_current_marker() -> None:
    with pytest.raises(RuntimeError, match="no current signing key declared"):
        _parse_signing_keys(
            "\n".join(
                [
                    "# key ring",
                    "ssh-ed25519 AAAAOLD key_id=scp-mcp-2026-01 current=false retain_until=2026-07-01",
                    "ssh-ed25519 AAAANEW key_id=scp-mcp-2026-04 retain_until=2026-10-01",
                    "",
                ]
            )
        )


def test_parse_signing_keys_rejects_multiple_current_markers() -> None:
    with pytest.raises(RuntimeError, match="multiple current signing keys declared"):
        _parse_signing_keys(
            "\n".join(
                [
                    "# key ring",
                    "ssh-ed25519 AAAAOLD key_id=scp-mcp-2026-01 current=true retain_until=2026-07-01",
                    "ssh-ed25519 AAAANEW key_id=scp-mcp-2026-04 current=true retain_until=2026-10-01",
                    "",
                ]
            )
        )
