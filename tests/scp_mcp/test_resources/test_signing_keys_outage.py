from __future__ import annotations

import logging

from standards_control_plane.mcp_server.resources import STATIC_RESOURCE_URIS, ScpCommittedResourceCatalog

from .conftest import commit_file, create_resource_repo


def test_snapshot_degrades_when_committed_signing_keys_are_malformed(
    tmp_path,
    fixed_now,
    caplog,
) -> None:
    resource_repo = create_resource_repo(tmp_path)
    commit_file(
        resource_repo,
        "docs/security/mcp-signing-keys.pub",
        "\n".join(
            [
                "# malformed key ring",
                "ssh-ed25519 AAAAOLD key_id=scp-mcp-2026-01 current=true retain_until=2026-07-01",
                "ssh-ed25519 AAAANEW key_id=scp-mcp-2026-04 current=true retain_until=2026-10-01",
                "",
            ]
        ),
        "Commit malformed signing keys fixture",
    )
    catalog = ScpCommittedResourceCatalog(repo_root=resource_repo, now_func=lambda: fixed_now)

    with caplog.at_level(logging.ERROR, logger="standards_control_plane.mcp.resources"):
        snapshot = catalog.snapshot()

    assert snapshot.key_id is None
    signing_keys = catalog.read_static("scp://security/signing-keys")
    assert signing_keys["key_id"] is None
    assert "multiple current signing keys declared" in signing_keys["error"]
    assert signing_keys["current_key"] is None
    assert signing_keys["current_key_sha256"] is None

    for uri in STATIC_RESOURCE_URIS:
        payload = catalog.read_static(uri)
        assert payload["key_id"] is None
    assert catalog.read_rule("GOV-001")["key_id"] is None
    assert catalog.read_waiver("W-001")["key_id"] is None
    assert catalog.read_finding("F-OPEN-001")["key_id"] is None
    assert catalog.read_decision("D-024")["key_id"] is None
    assert "degrading MCP resource snapshot: signing-keys unavailable" in caplog.text


def test_snapshot_logs_and_degrades_for_empty_committed_signing_keyring(
    tmp_path,
    fixed_now,
    caplog,
) -> None:
    resource_repo = create_resource_repo(tmp_path)
    commit_file(
        resource_repo,
        "docs/security/mcp-signing-keys.pub",
        "# empty key ring\n",
        "Commit empty signing keys fixture",
    )
    catalog = ScpCommittedResourceCatalog(repo_root=resource_repo, now_func=lambda: fixed_now)

    with caplog.at_level(logging.ERROR, logger="standards_control_plane.mcp.resources"):
        payload = catalog.read_static("scp://security/signing-keys")

    assert payload["key_id"] is None
    assert payload["current_key"] is None
    assert payload["current_key_sha256"] is None
    assert payload["keys"] == []
    assert "contains no ssh-ed25519 key entries" in payload["error"]
    assert "contains no ssh-ed25519 key entries" in caplog.text
