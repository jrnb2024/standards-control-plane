# 021D Fix Round 1 Closure Notes

## Unknown closures recorded for 021D

- `U-21-b` is closed for slice 021D by the server-side resource update implementation and test coverage added in this round. `register_resources()` now registers MCP subscribe/unsubscribe handlers, advertises `resources.subscribe=true` and `resources.listChanged=true`, and `test_resource_notifications.py` exercises a subscribed `scp://rules/registry` update after a committed HEAD advance. Client-specific adoption guidance remains a 021F deliverable; clients that do not consume resource updates continue to rely on re-read/polling fallback.
- `U-21-e` is closed as: direct exposure of `scp://rules/registry` is accepted for v1.0.0. The published schema now lives under `schemas/scp_mcp/rules-registry.schema.json`; a facade layer is deferred unless a future schema-version change requires compatibility indirection.
- `U-21-h` is closed as: `scp://rules/domain-map` is derived from the committed rules registry `applies_to` fields. Separate authored domain-map files were rejected for 021D because they would create a second source of truth.

## Resource schema publication

- Slice 021D now publishes machine-validatable schemas for all resource URI payloads under `schemas/scp_mcp/`.
- `test_resource_schemas.py` validates live resource payloads against the published schemas.

## Signing-key trust note

- `scp://security/signing-keys` now publishes `current_key_sha256`, per-key `public_key_sha256`, and an explicit `trust_model` block that requires adopters to cross-check the MCP-delivered key against either the committed `docs/security/mcp-signing-keys.pub` file or a pinned SHA-256 digest before trusting consult-receipt verification.
- The key parser now fails closed when no key is marked current or when multiple keys are marked current.
