# WP-ESC-007 review closure — SCP Estate read facade (PR #257)

**Programme:** PLAN-CT-ESTATE-CONTEXT-001 · **Repository:** standards-control-plane · **PR:** [#257](https://github.com/jrnb2024/standards-control-plane/pull/257)
**Base:** `500ec52caa02ebec24f9befcc0c7a313a3cb6fd5` (== origin/main) · **R1 reviewed head:** `7a3830f5cb385c82dcbdde5b78c7b99d9ffd4792` (tree `8be96475`)

## Round 1 — final-head three-lens R1 (2026-07-25)

| Lens | Evidence | Verdict |
|---|---|---|
| correctness | [final-head-R1/correctness.json](final-head-R1/correctness.json) | APPROVED (2 LOW) |
| safety_bypass | [final-head-R1/safety_bypass.json](final-head-R1/safety_bypass.json) | APPROVED (2 LOW, 2 NIT) |
| completeness_governance | [final-head-R1/completeness_governance.json](final-head-R1/completeness_governance.json) | APPROVED (1 LOW, 1 NIT) |

The Estate REST facade is opt-in (`SCP_ESTATE_READ_ONLY_ENABLED=false` default), authenticated (exact CT
principal/scope/binding), and read-only; the Estate MCP profile is a genuine **positive** allowlist of six read tools
with `propose`/`audit_changed` structurally undispatchable; health is truthful (C-ESC-006, no signature over-claim).
The safety lens ran the full attack matrix (tool-allowlist bypass, flag-off reachability, cross-tenant, wrong-scope,
health over-claim, secret exposure, path-traversal) — all fail-closed.

## Fix round — all findings dispositioned (none descoped)

| Finding | Class | Disposition |
|---|---|---|
| SB-R1-002 | NIT | FIXED — call-level negative: invoking `propose`/`audit_changed` through the estate profile raises `ToolError('Unknown tool')`; anti-vacuity counterpart proves they ARE reachable under the legacy profile. |
| SB-R1-003 | NIT | FIXED — unauthenticated request (no token) to an estate REST endpoint → 401. |
| CORR-R1-001 | LOW | NOT_APPLICABLE — CLI vs service flag-parse divergence; both directions fail-closed (facade stays off). Tracked diagnostic-consistency follow-up. |
| CORR-R1-002 / CG-R1-002 | LOW/NIT | NOT_APPLICABLE — config-derived health is as-designed (invalid config fails startup); C-ESC-006 satisfied. |
| SB-R1-001 | LOW | NOT_APPLICABLE — the OIDC issuer on `/status` is a public identifier, not a secret. Tracked consistency hardening. |
| SB-R1-004 | LOW | NOT_APPLICABLE — binding IDs are echo-only (no filesystem sink); the `scopes` (plural) claim name is confirmed consistent with CT issuance (`control-tower/auth/tokens.py` emits `scopes`). Path-separator tightening tracked as defense-in-depth. |
| CG-R1-001 | LOW | FIXED — this final-head R1 evidence landed on `7a3830f`; PR body + changeset `governance_review` updated to the reviewed head; no placeholder evidence. |

## Test evidence at the reviewed head + fix round

- Focused REST/MCP/CLI: 32 passed. Broad MCP regression: 106 passed, 1 deselected. New negatives added and load-bearing.
- Full repository: `417 passed, 6` documented pre-existing failures outside this change set — including
  `test_no_private_keys_committed`, which flags two files (`docs/reviews/rule-proposals/RULE-005-...md`,
  `policies/tests/scp_r_008_test.rego`) that are **byte-identical to the pinned base** and not in this change set.
  Verified not attributable to this PR and not broadened.

## Authority boundary

Authenticated, opt-in, read-only; `SCP_ESTATE_READ_ONLY_ENABLED=false`. Mutation/`propose`/`audit_changed` tools
excluded from the Estate profile. No deployment or feature activation. Rollback: disable the flag; the legacy profile
is unaffected.

## Exit state

Zero unresolved CRITICAL/HIGH/MEDIUM findings. Review-converged. Merge gate remains with the operator.
