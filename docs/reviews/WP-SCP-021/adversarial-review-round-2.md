# WP-SCP-021 — Adversarial review round 2

**Date:** 2026-04-21
**Plan version reviewed:** v0.2
**Reviewer:** combined architect + security + governance + devex (round-1 findings converged tightly; single-reviewer fixpoint check is proportionate — parallel round reopens if a new BLOCKING surfaces)
**Outcome:** RETURN TO v0.3. All 5 round-1 BLOCKINGs **FIXED**; all round-1 MAJORs folded (M5 receipt-churn graded PARTIAL, resolved by N-1); 3 new findings surfaced, all word-level.

## Round-1 BLOCKING verification

| # | Finding | Grade | Evidence |
|---|---|---|---|
| B-1 | HMAC → Ed25519 asymmetric | **FIXED** | D-024/D-025 rewritten; SCP holds `SCP_MCP_PRIVATE_KEY`; public key dual-published; 90-day overlap; `key_id` in envelope; §9 #10. |
| B-2 | Break-glass fail-closed + sibling | **FIXED** | 021F(v): `SCP_MCP_ALLOW_OFFLINE=true` AND committed `docs/overrides/OVERRIDE-NNN.md`; SCP-MCP-E010 tracked finding; §9 #12 canary. (OVERRIDE schema inline is N-2 follow-up.) |
| B-3 | Rego-authoritative invariant | **FIXED** | §2 invariant + §9 #13 canary "receipt valid + Rego deny → merge-blocked." |
| B1 | D-025 scope rule | **FIXED** | 021F(ii): `resolve_domain` + `scp://rules/domain-map` + default-skip globs enumerated. |
| B2 | Receipt validity bindings | **FIXED** | 021F(iii) envelope: schema_version + key_id + repo + head_sha + base_sha + changed_files_hash + domains_covered + issued_at + expires_at ≤ 2h; §9 #11 three-way canary. |

## Round-1 MAJOR sweep

All FIXED except:
- **M5 receipt-churn** → PARTIAL; N-1 (receipt-visibility invariant) closes the residual confusion.

## v0.2-introduced complexity scrutiny

**Ed25519 chain.** Coherent end-to-end. Minor loose thread: hook behaviour when `scp://security/signing-keys` unreachable AND local cache stale — should fail-closed with SCP-MCP-E021. Not blocking; can be handled in 021F implementation.

**Domain-map empty / resolver error.** *NEW MAJOR → folded into v0.3 (N-3)*. Ambiguous fail-open vs fail-closed. Resolved: resolver error → SCP-MCP-E022 fail-closed; empty domain-map → treat as "all domains require consult" (fail-closed). Operator populates domain-map or fires break-glass.

**Break-glass composition gaming.** Orthogonal and sound. Policy-deny (SCP-E004) and transport-offline (SCP-MCP-E010) cannot substitute for each other. Rego runs server-side independently; hook runs client-side pre-commit. Sound.

**`.gitignore` receipts in CI.** *NEW BLOCKER-risk → folded into v0.3 (N-1)*. Under v0.2, receipts are gitignored — CI never sees them. §2 v0.2 didn't explicitly state federation gate doesn't need them. Would confuse a future reviewer into reopening. Resolved in v0.3 §2: "Consult-receipt verification is client-side-hook-only; federation gate is independent and does not consume receipts. Belt = client-hook; braces = server-gate."

**OVERRIDE-NNN.md schema.** *NEW MAJOR → folded into v0.3 (N-2)*. 021I promised schema but v0.2 hadn't specified it. Hook "verify unexpired" had no schema contract. Resolved: 021F(v) inline schema `{override_id, issued_by, issued_at, expires_at ≤ +14d, reason (≥40 char), scope: mcp_offline|policy_deny, linked_finding_id}`; JSON Schema at `schemas/override.schema.json`; SCP-MCP-E023 on mismatch.

**§9 #13 Rego-authoritative canary runnability.** Depends on WP-SCP-020 slices 020C/020C.1/020D2 being live on SCP self. WP-SCP-020 has merged; slices land in planned sequence. 021K already targets post-020C PR. FIXED.

## Fixpoint declaration

**RETURN TO v0.3** — three word-level edits folded:

1. **N-1** §2 invariant on client-side-only receipt verification.
2. **N-2** OVERRIDE-NNN schema inline at 021F(v).
3. **N-3** `resolve_domain` / domain-map failure-mode specification at 021F(ii).

Plus one non-blocking: `scripts/scp-prune-receipts.sh` in 021A for 7-day receipt GC.

None require new slices, touch the signing chain, or re-architect. Round 3 (1 reviewer) expected to confirm FIXPOINT.
