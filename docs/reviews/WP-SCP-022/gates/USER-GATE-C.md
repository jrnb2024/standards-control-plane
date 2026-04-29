# USER-GATE-C — Track 2 (MCP server) close-out review

**Slice:** WP-SCP-022 / WP-SCP-021 §3 USER-GATE-C
**Status:** Awaiting operator signature
**Drafted by:** orchestrator (Opus) on 2026-04-29
**Operator signs by:** committing this file to `main` with the `Signed:` line populated and operator's git author email matching the `SCP_OPERATOR_EMAILS` allowlist (default `jrnb2024:james@brokai.net`).

## What this gate confirms

Track 2 of WP-SCP-022 reaches the autonomous-run-scope ceiling: the MCP server scaffold + tools + resources + propose() stub are on `main`. From here, the operator has reviewed the chain and authorises advancing to the post-pause continuation WP (WP-SCP-022.1 — slices 021F through 021K).

## Track 2 PR roll

| PR | Slice | Subject | Fixpoint round |
|----|-------|---------|----------------|
| #37 | 021B | MCP server scaffold + Ed25519 keygen + PyPI extras | R3 |
| #40 | 021C | MCP tools (7) + SCP-MCP-E0NN error taxonomy | R3 |
| #45 | 021D | MCP resources (11 URI types) + domain-map + signing-keys | R5 |
| #48 | 021E | propose() stub hardening (anti-spam + silent-rot banner) | R2 |

All four merged on `main` between 2026-04-28 and 2026-04-29. Adversarial review caught and closed (across all rounds): HMAC→Ed25519 forgery surface, race-unsafe propose() ID allocator, audit_changed cache key on literal `HEAD`, signing-keys parse-failure outage, MITM-bypassable trust-model wording, U-21-* unknowns, server.py instructions stale, caller_id PID DoS reset, sentinel signing-key leak, banner text drift.

## Installable evidence

- `pip install -e '.[mcp]'` resolves locally via `pyproject.toml [project.optional-dependencies.mcp]` (mcp + cryptography).
- Console script `scp-mcp-server` registered in `[project.scripts]`.
- 66 pytest tests pass under `tests/scp_mcp/`.
- PyPI publish step is operator-side once `scp-mcp-server keygen` populates the operational keypair (next operational action — see below).

## Public verification key path

- `docs/security/mcp-signing-keys.pub` (placeholder; populated post-merge by `scp-mcp-server keygen --out ~/.config/scp/mcp-signing-key`).
- Resource `scp://security/signing-keys` serves the published public key with key-id + retention dates per the trust model in `src/standards_control_plane/mcp_server/resources.py`.
- Trust-model adopter requirement (post-fr3 wording): out-of-band verification only — adopters MUST cross-check `current_key.public_key` against the committed `docs/security/mcp-signing-keys.pub` at a known git SHA OR an operator-distributed public key hash. Resource-only cross-check explicitly insufficient.

## Post-pause Track 2 continuation (out of WP-SCP-022 scope)

The autonomous-run scope stops here. The post-pause WP (`WP-SCP-022.1` per the WP-SCP-022 plan §12) covers:

- 021F — ADOPT-001 §13 adopter guide for MCP client-side hook.
- 021G — ACC integration stub (hooks SCP MCP into ACC dispatcher's plan-decompose step).
- 021H — streamable HTTP transport (opt-in).
- 021I — auth model (bearer-token + rotation overlap + `OVERRIDE-NNN` break-glass).
- 021J — observability (per-line hash-chained tool-invocation log).
- 021K — SCP self-consumes MCP on a post-020C PR (the canonical first real-world test of the consult+gate compose).

Operator next operational actions (out-of-band):
1. Run `scp-mcp-server keygen --out <path>` once to generate the operational Ed25519 keypair.
2. Commit the public key to `docs/security/mcp-signing-keys.pub`.
3. Publish to PyPI as `standards-control-plane[mcp]` extra (or schedule for first release tag alongside Track 1's v1.0.0).

## Operator signature

By committing this file with the `Signed:` line below populated, the operator confirms (a) the Track 2 PR roll is correct, (b) installable evidence is acceptable, and (c) the chain may advance.

_The gate-helper greps for `^(Signed|Signer):\s+\S+` on this file. Keep the line format below — no markdown bold — replace the placeholder, then commit. Defence-in-depth: helper also checks `git log -1 --format=%ae` matches `SCP_OPERATOR_EMAILS` (override via env if your git email isn't in the default allowlist)._

Signed: James Brooke <james.brooke@mapp.com>
Signed-At: 2026-04-29T15:35:00Z
Signing-Method: plain commit (cryptographic git-signing not yet enforced); attested verbally in operator session 2026-04-29.
