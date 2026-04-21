# WP-SCP-021 — Plan fixpoint log

## v0.1 → v0.2 (post round-1 review, 2026-04-21)

### 5 BLOCKING findings folded in

| # | Finding | Resolution in v0.2 |
|---|---|---|
| 1 | HMAC symmetric-key forgery (A B-1) | D-024 + D-025 switched to **Ed25519 asymmetric signing**. SCP holds `SCP_MCP_PRIVATE_KEY`; public key distributed at `scp://security/signing-keys` + committed `docs/security/mcp-signing-keys.pub` with key-id + 90-day rotation overlap. 021B `scp-mcp-server keygen` subcommand. 021F hook verifies with public key — adopters cannot forge. |
| 2 | Break-glass fail-OPEN (A B-2) | 021F(v) + 021I: `SCP_MCP_ALLOW_OFFLINE=true` requires committed sibling `docs/overrides/OVERRIDE-NNN.md` with expiry ≤ 2 weeks; SCP-MCP-E010 is a tracked finding at `scp://findings/open` (not an idle log line); re-enablement requires a new OVERRIDE. Composition with WP-SCP-020 `scp_bypass` documented — transport-offline vs policy-deny are independent levers; audit markers compose. |
| 3 | Rego-authoritative invariant (A B-3) | §2 invariants list: "Rego gate is authoritative; MCP consult is advisory. A consult receipt is *never* a gate bypass." §9 acceptance #13 adds invariant canary. |
| 4 | D-025 scope rule undefined (B B1) | 021F(ii): scope rule via `resolve_domain(changed_files)` tool + `scp://rules/domain-map` resource; default-skip glob list for docs-only changes; receipt required only when resolved domain set is non-empty. |
| 5 | Receipt validity triple-undefined (B B2; overlaps A M-9) | 021F(iii) envelope schema: `{schema_version, key_id, repo, head_sha, base_sha, changed_files_hash, domains_covered, issued_at, expires_at ≤ 2h}`; 021F(iv) hook validates every field; §9 acceptance #11 adds binding canary (PR-A receipt in PR-B fails, 3h old fails, wrong domain fails). |

### MAJORs folded in

- **M-4** cache coherence → §2 invariant "MCP reflects committed state only"; 021D explicit.
- **M-5** self-consume ordering → 021K targets post-020C PR.
- **M-6** tool-vs-resource rule → 021C explicit contract.
- **M-7** stdio caller identity → §8 risk acknowledges advisory-only; real defence is branch-not-main.
- **M-8** log integrity → 021J per-line SHA256 hash chain + CI-verified `verify-mcp-log-chain.sh` + manifest belt-and-braces.
- **M-9** receipt replay → 021F envelope binds head_sha + changed_files_hash + repo.
- **M-10** audit_changed circuit-breaker → 120s wall-clock + 500-file diff cap + SCP-MCP-E011 + 1h result cache.
- **M-11** HTTP size/DoS → 021H limits 1 MB body / 8 MB response / 32 concurrency / 120s per-conn.
- **M-12** token rotation → 021I `SCP_MCP_TOKEN_PREV` 30-day overlap, 3-step rotation procedure, revocation list.
- **M1** domain-map mapping → `scp://rules/domain-map` resource + `resolve_domain` tool in 021C/021D.
- **M2** break-glass composition → 021F(v) explicit composition with WP-SCP-020 `scp_bypass`.
- **M3** offline-posture contradiction → 021F(v) clarified: stdio + HTTP both can fail; both fail-closed; sole escape is `SCP_MCP_ALLOW_OFFLINE + OVERRIDE`.
- **M4** proposal silent-rot → 021E auto-banner in proposal body + `adjudication_status: queued_no_adjudicator` in response.
- **M5** receipt churn → `.gitignore` entry in 021A; regenerated per commit.
- **M6** distribution → 021B PyPI as `standards-control-plane[mcp]` extra; `pipx install` documented.
- **M7** non-Claude clients → 021F feature matrix for Cursor + Codex; re-polling fallback.
- **M9** tool response schema versioning → 021C every tool output has `schema_version`.

### Follow-ups opened

- **SCP-075-errors** — expanded SCP-MCP-E0NN error UX patterns (M-8 ≡ DevEx M8).
- **SCP-075-scaffolder-compose** — SCP-073-scaffolder emits MCP adopter bits (m-4 DevEx).

### MINORs folded

- **m1** `--stdio-test` semantics → 021B one-shot handshake+list+exit.
- **m-13** per-ID URIs → `scp://waiver/<id>`, `scp://finding/<id>`, `scp://decision/<D-NNN>` in 021D.
- **m-14** receipt GC → `.gitignore` owns it (021A).
- **m-15** normalised-hash anti-dup → 021E strips markdown + collapses whitespace + case-folds.
- **m-17** D-025 wording mismatch → rewritten with "Ed25519" explicit.
- **m2** `propose()` response fields → 021E returns `{proposal_id, branch, path, pr_url_if_pushed, adjudication_status, expected_review_date}`.
- **m3** worked example → 021F(vi).

## v0.2 → v0.3 (post round-2 fixpoint check, 2026-04-21)

Round-2 single combined reviewer: 5/5 round-1 BLOCKINGs **FIXED**, 17/17 MAJORs folded (M5 PARTIAL → N-1). 3 new findings surfaced, all word-level:

| # | Finding | Resolution in v0.3 |
|---|---|---|
| N-1 | Receipt visibility ambiguity — gitignored receipts aren't visible in CI, but §2 never says federation gate doesn't consume them. Would confuse future reviewer. | §2 invariants list: "Consult-receipt verification is client-side-hook-only. Federation gate is independent and does not consume receipts. Belt = client-hook; braces = server-gate." |
| N-2 | `docs/overrides/OVERRIDE-NNN.md` schema promised for 021I but not specified inline; "verify unexpired" has nothing to check against. | 021F(v) OVERRIDE schema enumerated: YAML front-matter `{override_id, issued_by, issued_at, expires_at ≤ +14d, reason (≥40 char), scope: mcp_offline\|policy_deny, linked_finding_id}`; JSON Schema at `schemas/override.schema.json`; hook validates schema + expiry + scope; SCP-MCP-E023 on mismatch. |
| N-3 | `resolve_domain` / domain-map failure mode unspecified. Empty registry or resolver error leaves hook behaviour ambiguous. | 021F(ii): (a) resolver error → SCP-MCP-E022 fail-closed; (b) empty/unreachable domain-map → treat as "all domains require consult" (fail-closed). |

Non-blocking also folded:
- **Receipt disk GC.** 021A adds `scripts/scp-prune-receipts.sh` — deletes receipts older than 7 days (prevents unbounded `.scp/consult-receipts/` growth over repo lifetime).

## v0.3 → FIXPOINT REACHED (round 3, 2026-04-21)

Round-3 single verification reviewer confirmed all 4 v0.3 deltas landed clean; no new breakage; slice dependency chain intact. v0.3 ships as the plan-PR version.

## Review-round summary

| Round | Reviewers | Outcome | BLOCKINGs |
|-------|-----------|---------|-----------|
| 1 | 2 parallel | → v0.2 | 5 unique |
| 2 | 1 combined | → v0.3 | 0 (3 word-level findings) |
| 3 | 1 verification | **FIXPOINT** | 0 |

Total distinct BLOCKING findings surfaced + closed: 5.
