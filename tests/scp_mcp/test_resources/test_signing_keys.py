from __future__ import annotations


def test_signing_keys_resource_serves_current_and_prior_keys(resource_catalog) -> None:
    payload = resource_catalog.read_static("scp://security/signing-keys")

    assert payload["schema_version"] == "1.0.0"
    assert payload["key_id"] == "scp-mcp-2026-04"
    assert payload["current_key"]["key_id"] == "scp-mcp-2026-04"
    assert payload["prior_keys"] == [
        {
            "algorithm": "ssh-ed25519",
            "public_key": "AAAAOLD",
            "key_id": "scp-mcp-2026-01",
            "current": False,
            "retain_until": "2026-07-01",
        }
    ]
