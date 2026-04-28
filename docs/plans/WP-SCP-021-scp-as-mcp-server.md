# ProgrammePlan — WP-SCP-021 SCP as MCP Server

**Work Package:** `WP-SCP-021`
**Version:** 0.3 (FIXPOINT REACHED at round 3)
**Status:** Draft — ready for plan-PR review
**Date:** 2026-04-21
**Branch:** `feature/wp-scp-021-mcp-server-plan`
**Programme Ref:** SCP-075 (MCP server backlog row, added in slice 021A — Phase 10)
**Decisions introduced:** D-024 (MCP adoption + transport + auth + asymmetric signing), D-025 (scoped pre-code consult + Ed25519-signed receipts)

## 1. Purpose

Expose SCP's policy surface — rules, decision records, open findings, active
waivers, audit capability — to AI coding agents via the **Model Context
Protocol (MCP)**, so that agents working in downstream repos can ask SCP
structured questions *before* they code, not after.

This is **move #3** of the 5-move MVCP. WP-SCP-020 gave SCP a server-side
pre-merge gate. This WP gives agents a client-side consult surface, so
enforcement is belt + braces:

- Client-side (this WP): agents call `scp.consult_rules` via MCP before
  authoring code in a governed domain; Claude Code hooks refuse commit
  without a valid scope-bound Ed25519-signed consult receipt.
- Server-side (WP-SCP-020): reusable workflow + OPA runs the gate regardless
  of whether the agent consulted.

## 2. Invariants and what this is NOT

### Invariants

- **Rego gate is authoritative; MCP consult is advisory.** A consult
  receipt is *never* a gate bypass. If MCP says "allow" at author time
  and Rego says "deny" at gate time, Rego wins. (Elevated to §9
  acceptance criterion.)
- **MCP reflects committed state only.** Working-copy edits are NOT
  visible to MCP until commit + push. Adopter hooks + CI respect this.
- **Propose() writes only to branches, never to main.** `propose()`
  side-effect is a branch + proposal file; merge is human-adjudicated
  (WP-SCP-022).
- **Consult-receipt verification is client-side-hook-only.** The federation
  gate (WP-SCP-020) is independent and does *not* consume receipts.
  Belt = client-side pre-commit hook verifies the Ed25519-signed receipt;
  braces = server-side required status check runs Rego regardless of
  whether a receipt exists. Receipts live at `.scp/consult-receipts/*.json`
  (gitignored per 021A); CI never sees them, by design.

### What this is NOT

- Not a proposal-queue adjudication workflow (WP-SCP-022).
- Not an ACC implementation (ACC-side work in `~/Projects/acc`).
- Not a cross-repo decision-record aggregator (`SCP-075-crossrepo`).
- Not an OAuth service (`SCP-075-oauth`).
- Not a replacement for the Python CLI.

## 3. Programme protocol position

Follows `PROG-SCP-001`: one branch, one PR per WP.

### Slice ordering

```
021A  plan + review pack + D-024 + D-025 + BACKLOG SCP-075 + STATUS stub
  ↓
021B  MCP server scaffold + Ed25519 signing key provisioned + PyPI distribution channel
  ↓
021C  tool implementations + SCP-MCP-E0NN error taxonomy
  ↓
021D  resource implementations + scp://rules/domain-map + scp://security/signing-keys
  ↓
021E  propose() tool stub with anti-spam + silent-rot banner
  ↓
021F  ADOPT-001 §13 appendix: adopter config + scope rule + receipt envelope schema + hook verification + break-glass composition with WP-SCP-020
  ↓
021G  ACC integration stub (interface contract only; ACC-side impl follows)
  ↓
021H  streamable HTTP transport (opt-in) with size + concurrency limits
  ↓
021I  auth model — bearer-token + rotation overlap + overrides/OVERRIDE-NNN break-glass mechanism
  ↓
021J  observability — per-line hash-chained tool-invocation log
  ↓
021K  SCP self-consumes MCP (post-020C SCP PR authoring rule SCP-R-002 or waiver-schema amendment)
```

## 4. Scope

| Slice | Deliverable |
|-------|-------------|
| 021A | Plan doc (this), adversarial review evidence pack, fixpoint log, BACKLOG row SCP-075 in Phase 10, D-024, D-025, STATUS.md stub, MCP contributor README stub, `.gitignore` entry for `.scp/consult-receipts/` (receipts gitignored; regenerated per commit — closure M-5); adopter-side `scripts/scp-prune-receipts.sh` that deletes local receipts older than 7 days (prevents unbounded disk growth). |
| 021B | **MCP server scaffold.** Python `mcp` SDK as runtime dep (pinned version + sdist SHA256); `src/standards_control_plane/mcp_server/` module; `scp-mcp-server` CLI entry point invoking `mcp.server.stdio`. **Distribution** (closure M-6): published to **PyPI as `standards-control-plane[mcp]` extra** alongside existing SCP package; adopters install via `pipx install 'standards-control-plane[mcp]'` or `uv tool install standards-control-plane --with standards-control-plane[mcp]`; version pin documented in ADOPT-001 §13. **Ed25519 signing** (closure B-1): `scp-mcp-server keygen` subcommand generates keypair; SCP holds `SCP_MCP_PRIVATE_KEY` in secrets; public key committed to `docs/security/mcp-signing-keys.pub` with key-id; rotation keeps prior key for 90-day overlap window. Handshake test (`mcp` client connects, lists tools + resources); `--stdio-test` one-shot handshake that lists + exits 0 (m1). |
| 021C | **Tool implementations** (re-use existing Python internals): <br/>— `consult_rules(domain, subsystem?, area_id?)` — mirrors `consult` CLI; response includes `schema_version` (closure M9). <br/>— `check_waiver(rule_id, scope?)` — reads `waivers.json`; applies `expires_at`. <br/>— `list_open_decisions(since?)` — parses `DECISIONS.md` table. <br/>— `check_finding(finding_id)` — reads `output/findings/*.json`. <br/>— `audit_changed(base_ref?, head_ref?)` — invokes existing `audit-changed`; **circuit-breaker** (closure M-10): wall-clock ceiling 120s, diff-size cap 500 changed files, SCP-MCP-E011 on timeout, per-`(base, head)` tuple result cache for 1h. <br/>— `resolve_domain(changed_files: [str]) → {domains: [str], confidence: float}` (closure B1 + M1) — maps changed-file paths to domain set using registry's path-to-domain mapping. <br/>**Tool-vs-resource contract** (closure M-6): tools for parameterised lookup + side-effect logging; resources for bulk enumeration + subscription. Every tool emits an invocation log line (021J). <br/>**Error taxonomy** (closure M8 → in-scope): SCP-MCP-E001..E099 scheme; every error returns `{error_code, message, remediation_url}`; catalogue in `docs/integrations/mcp-error-codes.md`. |
| 021D | **Resource implementations.** Read-only URIs: <br/>— `scp://rules/registry` — full registry (JSON). <br/>— `scp://rules/domain-map` (closure B1 + M1) — changed-file glob → domain map; used by `resolve_domain` tool and adopter hook. <br/>— `scp://decisions` — DECISIONS.md table parsed to JSON. <br/>— `scp://findings/open` — unwaived findings. <br/>— `scp://waivers` — active waivers filtered by `expires_at > now`. <br/>— `scp://status` — STATUS.md summary + recent WP merges. <br/>— `scp://rule/<RULE-ID>` — individual rule card. <br/>— `scp://waiver/<id>`, `scp://finding/<id>`, `scp://decision/<D-NNN>` (closure m-13) — per-ID direct URIs. <br/>— `scp://security/signing-keys` (closure B-1) — current public key + prior keys with retention dates + key-ids. <br/>**Caching** (closure M-4): resources are served from committed state only. git-sha-keyed cache invalidates on new commit; working-copy edits NOT visible until commit+push. Plan documents "MCP reflects committed state" as an invariant (§2). Resource-update notifications emit `schema_version` + key-id. |
| 021E | **`propose()` tool stub.** `propose(title, body, affected_repos, rule_id?) → {proposal_id, branch, path, pr_url_if_pushed, adjudication_status, expected_review_date}`. Writes `docs/reviews/proposals/PROP-NNN.md` on branch `proposals/PROP-NNN`; does NOT merge. **Anti-spam**: rate-limit 10/caller/hour; normalised-text-hash identical-body refusal within 24h (closure m-15 — strips markdown, collapses whitespace, case-folds). **Silent-rot banner** (closure M4): proposal body front-matter auto-injects `adjudication_status: queued_no_adjudicator` + `expected_review_date: null` + `> NOTE: WP-SCP-022 adjudication workflow not yet live; proposals queue until adjudication ships. Status updates via GitHub issue on this branch.` **Schema coordinated with WP-SCP-022**. Proposals carry `mcp_origin: true` + `caller_id` + `signing_key_id`. |
| 021F | **ADOPT-001 §13 "MCP integration — adopter guide"**: <br/>(i) `.mcp.json` + `.claude/mcp.json` snippets with exact server invocation + `pipx` install line. <br/>(ii) **Scope rule for pre-code consult** (closure B1): hook invokes `resolve_domain(changed_files)` against PR's diff; if result is non-empty, consult receipt required; default-skip glob list `{docs/**/*.md except DECISIONS.md/STATUS.md, *.txt, .gitignore, LICENSE, .github/ISSUE_TEMPLATE/**}` — receipts not required for these. **Failure modes (closure N-3):** (a) `resolve_domain` tool error → hook fails closed with SCP-MCP-E022 `domain-resolver-failed` (commit refused; operator fixes resolver OR fires break-glass); (b) `scp://rules/domain-map` resource empty or unreachable → hook treats as "all domains require consult" (fail-closed to the consult requirement; operator populates domain-map or fires break-glass). <br/>(iii) **Receipt envelope schema** (closure B2 + M-9): JSON `{schema_version, key_id, repo, head_sha, base_sha, changed_files_hash (sha256 of sorted changed-file-paths), domains_covered: [str], issued_at, expires_at}` — signed with Ed25519; `expires_at` ≤ `issued_at + 2h`. Receipts at `.scp/consult-receipts/<head_sha>.json` (gitignored; regenerated per commit — M-5). <br/>(iv) **Hook verification** (closure B-1): PreCommit hook fetches current public key from `scp://security/signing-keys` (or local cached copy with 1h TTL); verifies Ed25519 signature; validates every envelope field — `repo == this-repo`, `head_sha == HEAD`, `changed_files_hash == current diff hash`, `domains_covered ⊇ resolve_domain(changed_files)`, `expires_at > now`; refuses commit on any failure with SCP-MCP-E020. <br/>(v) **Break-glass composition with WP-SCP-020** (closure B-2 + M2 + M3): <br/> • **MCP transport outage** (stdio binary missing, crash, HTTP network) → set `SCP_MCP_ALLOW_OFFLINE=true` AND commit sibling `docs/overrides/OVERRIDE-NNN.md` with the schema below; hook verifies the OVERRIDE file exists + passes schema + is unexpired; emits SCP-MCP-E010 as a **tracked finding** at `scp://findings/open` (not an idle log line); expires automatically — re-enablement requires a new OVERRIDE. **OVERRIDE-NNN.md schema (closure N-2):** YAML front-matter with required keys `{override_id: "OVERRIDE-NNN", issued_by: "<@github-handle>", issued_at: "YYYY-MM-DDTHH:MM:SSZ", expires_at: "YYYY-MM-DDTHH:MM:SSZ" (must be ≤ issued_at + 14d), reason: str (min 40 chars, human-readable context), scope: "mcp_offline" | "policy_deny", linked_finding_id: "SCP-MCP-E010-<n>" | null}`. JSON Schema at `schemas/override.schema.json`. Hook validates schema + expiry + scope matches the attempted bypass type; rejects with SCP-MCP-E023 `override-invalid` on any mismatch. <br/> • **Policy-deny bypass** (WP-SCP-020 `scp_bypass: true`) remains unchanged — SCP-E004 three-gate mechanism. <br/> • The two levers are independent: an agent facing both "MCP down AND policy deny" must fire both, which is rare and intentionally high-friction. Audit markers compose (both SCP-E004 and SCP-MCP-E010 appear in JSON summary when both fire). <br/>(vi) Agent feedback-loop worked example (m3): 10-line flow showing `consult_rules → receipt → code → commit → hook verifies → PR → federation gate`. <br/>(vii) Non-Claude-client feature matrix (M7): tools/list + resources/list + progress notifications + resource-update notifications coverage for Claude Code, Claude Desktop, Cursor, Codex; re-polling fallback for clients without resource-update support. <br/>(viii) Pairing note: "Consult receipt does not bypass the federation gate. Both must pass." (Rego-authoritative invariant restated.) |
| 021G | **ACC integration stub.** `docs/integrations/acc-mcp-integration.md` documents: <br/>(i) broker/dispatcher.py recommended hook invoking `scp.consult_rules` at plan-decompose; <br/>(ii) lifecycle gate invoking `audit_changed` at post-implementation checkpoint; <br/>(iii) ACC-side auth: `SCP_MCP_TOKEN` env var for HTTP; <br/>(iv) ACC error posture; <br/>(v) worked JSON request/response pairs. ACC-side PR opens in `~/Projects/acc`. |
| 021H | **Streamable HTTP transport (opt-in).** `scp-mcp-server --http --port 8422` starts `uvicorn` + `fastapi`. Health `GET /healthz`; MCP `POST /mcp`. **Size + concurrency limits** (closure M-11): max request body 1 MB; max response 8 MB (streamed for larger via MCP resource pagination); max concurrent connections 32; per-connection request timeout 120s. Dockerfile target `mcp-http` for deployment. |
| 021I | **Auth model.** <br/>— stdio: trust-the-local-process; acknowledge in §8 that PID+path rate-limit keying is advisory, not security (closure M-7); strong defence is "propose writes to branch only." <br/>— HTTP: bearer-token via `SCP_MCP_TOKEN`; **rotation with overlap** (closure M-12): `SCP_MCP_TOKEN_PREV` supported for 30-day overlap window; `gh` secret rotation documented as 3-step procedure (set PREV = current, set TOKEN = new, update adopters, wait 30d, clear PREV); rate-limit per token; revocation list at `docs/security/mcp-revoked-tokens.txt` (key hashes only). <br/>— No OAuth in v1.0; deferred to `SCP-075-oauth`. <br/>— `docs/overrides/OVERRIDE-NNN.md` schema + lifecycle authored here; OVERRIDE records are first-class findings in `scp://findings/open`. |
| 021J | **Observability.** Tool-invocation log at `output/findings/mcp-invocations.jsonl` — one line per invocation: `{timestamp, tool, caller_id, inputs_hash, outcome, duration_ms, error_code, prev_hash}`. **Per-line hash chain** (closure M-8): each entry's `prev_hash` = SHA256 of prior line; genesis entry `prev_hash = "genesis:<signing-key-id>"`; chain-verification script `scripts/verify-mcp-log-chain.sh` exercised in CI. Rotation: daily; retained 30 days; archives at `output/findings/mcp-invocations-archive/<YYYY-MM>.jsonl.gz` with chain continuity across rotation. Schema at `schemas/mcp-invocation.schema.json`. Committed hourly manifest supplements the per-line chain (belt + braces). |
| 021K | **SCP self-consumes MCP.** Target a **post-020C SCP PR** (closure M-5): rule SCP-R-002 authoring PR, or `waivers.json` schema amendment PR, whichever merges first post-020C. Agent running on SCP calls `scp.consult_rules(domain="service-lifecycle")` before writing; consult receipt checked into PR; evidence at `docs/reviews/WP-SCP-021/self-consume-evidence.md`. |

### 4.1 Deferred to follow-up WP

| Slice / WP | Deliverable | Blocker |
|---|---|---|
| → `WP-SCP-022` | Structured proposal queue adjudication workflow. Adjudication quorum, promotion-to-D-NNN, rejection semantics. | Depends on 021 ship. |
| → `WP-SCP-023` | Estate scorecards with MCP invocation aggregation. | Depends on 021J logs flowing. |
| Follow-up `SCP-075-oauth` | OAuth 2.0 for HTTP transport. | Opens now. |
| Follow-up `SCP-075-crossrepo` | Cross-repo decision-record indexing under `scp://external/ct/*`. | Opens now. |
| Follow-up `SCP-075-ratelimit` | Per-caller rate-limit on read tools. | Opens now. |
| Follow-up `SCP-075-errors` | Expanded SCP-MCP-E0NN error-UX patterns + remediation links for every code. | Opens now. |
| Follow-up `SCP-075-scaffolder-compose` | SCP-073-scaffolder emits MCP adopter bits (`.mcp.json`, CLAUDE.md snippet, hook) alongside federation wrapper. | Opens now; ready before WP-SCP-024. |

## 5. Out of scope

- Proposal adjudication (WP-SCP-022).
- Cross-repo decision aggregation (`SCP-075-crossrepo`).
- OAuth (`SCP-075-oauth`).
- Scorecards dashboard (WP-SCP-023).
- ACC-side implementation.
- Writing to repo state other than `docs/reviews/proposals/` on a branch.

## 6. External dependencies

| Dependency | Owner | Notes |
|------------|-------|-------|
| Python `mcp` SDK | Anthropic | Pinned by version + sdist SHA256; post-1.0 breaking changes tracked. |
| `cryptography` (Ed25519) | PyCA | For asymmetric signing (closure B-1). |
| `pydantic >= 2` | Pydantic | Already in SCP. |
| `uvicorn` + `fastapi` | Community | Already present. |
| Claude Code / Cursor / Codex MCP config schemas | Various | Feature matrix in 021F. |

## 7. Rollout prerequisites

Adoption across downstream repos is part of WP-SCP-024 — same gate as
federation-primitive rollout (FLA economical + Go SDK + CT lessons).

## 8. Risks

- **MCP SDK churn.** Pin + SHA256; SDK bumps behind regression tests.
- **Schema exposure cascades.** Per-resource `schema_version`; per-tool `schema_version`; deprecation = one-release dual-publish window.
- **Proposal spam.** Rate-limit + normalised-hash anti-dup + branch-not-main invariant.
- **stdio process lifecycle.** Stateless server; reconnect-tolerant.
- **Caching coherence.** MCP reflects committed state only (§2 invariant).
- **Auth gap on HTTP.** Bearer + rotation overlap; OAuth as follow-up.
- **Consult-receipt forgery.** Ed25519 asymmetric signing (SCP private, adopters verify with public key from `scp://security/signing-keys` or committed keyring); adopters cannot forge. Key rotation with 90-day overlap.
- **Consult-receipt replay across PRs.** Receipt binds `{repo, head_sha, changed_files_hash}`; hook rejects mismatch (closure M-9).
- **Consult-receipt scope bypass.** Receipt binds `domains_covered`; hook checks ⊇ `resolve_domain(diff)`.
- **Consult-receipt TTL abuse.** `expires_at ≤ issued_at + 2h`; hook rejects stale.
- **SCP MCP outage.** stdio primary + local; HTTP break-glass via `SCP_MCP_ALLOW_OFFLINE=true` + committed `OVERRIDE-NNN.md` + SCP-MCP-E010 tracked finding.
- **stdio caller-identity spoofing.** Advisory only; real defence is "propose writes to branch, not main."
- **Log tampering.** Per-line SHA256 hash chain (`prev_hash`); CI-verified; rotation preserves chain.
- **`audit_changed` cost / DoS.** 120s wall-clock; 500-file diff cap; per-tuple 1h cache.
- **HTTP DoS.** Request 1 MB / response 8 MB / concurrency 32 / per-conn 120s.
- **Client compatibility.** 021F feature matrix + re-poll fallback.
- **Offline posture composition with 020.** Transport-offline vs policy-deny are different break-glass paths; both may fire; audit markers compose; both levers require committed sibling artefacts.
- **Bus-factor-1** (inherited from WP-SCP-020 §8). Quarterly review 2026-07-21.

## 9. Acceptance criteria

WP-SCP-021 PR merges when all of:

1. Slices 021A–021K complete on-branch.
2. `scp-mcp-server --stdio` clean start; client handshake tests pass; all
   tools + resources listed.
3. Every tool has Pydantic input + output schema with `schema_version`; unit
   tests ≥ 90% coverage; round-trip tests via real `mcp` client.
4. Every resource has a JSON Schema + `schema_version`; update notifications
   tested.
5. `propose()` rate-limit + normalised-hash anti-dup exercised; silent-rot
   banner appears in proposal body.
6. HTTP transport starts; bearer-token rejection exercised (no/wrong/rotated
   prev/revoked); size + concurrency limits exercised.
7. Observability log hash chain verifies end-to-end via `scripts/verify-mcp-log-chain.sh`.
8. ADOPT-001 §13 published with all adopter content per 021F.
9. `docs/integrations/acc-mcp-integration.md` + `docs/integrations/mcp-error-codes.md` published.
10. **Ed25519 signing live**: `SCP_MCP_PRIVATE_KEY` in secrets; public key in
    `docs/security/mcp-signing-keys.pub` with key-id + rotation record;
    hook verification exercised in canary.
11. **Consult-receipt binding canary**: receipt from PR-A copy-pasted into
    PR-B fails hook (proof of head_sha + changed_files_hash binding).
    Receipt 3h old fails hook (proof of TTL). Receipt with wrong
    `domains_covered` fails hook (proof of scope binding).
12. **Break-glass composition canary**: `SCP_MCP_ALLOW_OFFLINE=true` without
    sibling `OVERRIDE-NNN.md` fails hook. With OVERRIDE-NNN.md unexpired:
    hook passes; SCP-MCP-E010 recorded as tracked finding.
13. **Rego-authoritative invariant canary**: consult receipt present +
    valid; Rego rule emits deny; PR is merge-blocked (receipt did NOT
    bypass the gate).
14. SCP self-consume evidence at `docs/reviews/WP-SCP-021/self-consume-evidence.md`
    (post-020C SCP PR).
15. Adversarial review rounds on-file; fixpoint declared.
16. `docs/BACKLOG.md` Phase 10 row SCP-075 + follow-ups open.
17. `STATUS.md` refreshed.

## 10. Decisions introduced

- **D-024** (2026-04-21): Adopt MCP as the estate's agent-to-SCP tool
  protocol. stdio primary (local, trust-the-process); streamable HTTP
  opt-in with bearer-token auth + 30-day rotation overlap. **Ed25519
  asymmetric signing** for consult receipts: SCP holds private key;
  adopters verify with public key distributed at `scp://security/signing-keys`
  + committed `docs/security/mcp-signing-keys.pub`. Python `mcp` SDK
  pinned by version + SHA256; distributed via PyPI as
  `standards-control-plane[mcp]` extra. OAuth deferred to `SCP-075-oauth`.
  *Rationale:* MCP is the dominant vertical agent-to-tool protocol post
  Linux Foundation Agentic AI Foundation (Dec 2025); Anthropic is origin;
  Claude Code/Desktop + ACC speak MCP natively. Asymmetric signing
  prevents adopter-held-key forgery (HMAC symmetric rejected in round 1).
  Alternatives rejected: raw REST (no client ecosystem); custom JSON-RPC
  (reinvents MCP); gRPC (no agent support); HMAC symmetric (any adopter
  can forge).
- **D-025** (2026-04-21): Scoped pre-code consult requirement with
  Ed25519-signed receipts. Downstream `CLAUDE.md` mandates
  `scp.consult_rules` before code authoring in governed domains;
  Claude Code `PreCommit` hook refuses commit without valid receipt.
  **Scope rule**: hook consults `scp://rules/domain-map` via
  `resolve_domain(changed_files)`; non-empty result → receipt required;
  default-skip globs for docs-only changes. **Receipt envelope**:
  `{schema_version, key_id, repo, head_sha, base_sha,
  changed_files_hash, domains_covered, issued_at, expires_at ≤ 2h}`
  signed Ed25519. Hook validates every field; rejects on any mismatch.
  Break-glass `SCP_MCP_ALLOW_OFFLINE=true` requires committed
  `docs/overrides/OVERRIDE-NNN.md` with expiry ≤ 2 weeks; emits
  tracked finding SCP-MCP-E010. *Rationale:* client-side enforcement
  pairs with server-side gate as belt + braces; scoped + TTL + PR-bound
  receipts prevent replay/forgery; break-glass requires sibling artefact
  so fail-closed posture is maintained; Rego gate is authoritative
  (MCP consult never bypasses).

## 11. Review evidence

- `docs/reviews/WP-SCP-021/adversarial-review-round-*.md`
- `docs/reviews/WP-SCP-021/plan-fixpoint-log.md`
- `docs/reviews/WP-SCP-021/self-consume-evidence.md` (populated in 021K)

## 12. Next WP candidates

See §4.1. Primary next: WP-SCP-022 (proposal queue adjudication), WP-SCP-023 (scorecards).

## 13. Open unknowns (must close before specific slice)

| ID | Question | Closes before | Resolution |
|----|----------|---------------|------------|
| U-21-a | Python `mcp` SDK version + sdist SHA256 pinnability | 021B | **CLOSED in 021B (PR #37, 2026-04-28):** `mcp >= 1.0` declared in `pyproject.toml [project.optional-dependencies.mcp]`; sdist SHA256 deferred to live PyPI publish step (out-of-scope until first release tag). |
| U-21-b | MCP client support for progress + resource-update notifications (Claude Code, Desktop, Cursor, Codex) | 021D | **CLOSED in 021D implementation commit `5debbcc` and hardened in `d4d78c6`:** `src/standards_control_plane/mcp_server/resources.py` resolves the server side of the notification-client matrix by emitting `notifications/resources/updated` from `ScpCommittedResourceCatalog._schedule_resource_update_notifications()` whenever the git-SHA-keyed snapshot changes, with `register_resources()` exposing the same schema-versioned URIs to every client. The adopter-facing matrix outcome for Claude Code, Claude Desktop, Cursor, and Codex is therefore: subscribe when the client surfaces MCP resource-update notifications, otherwise re-poll the same resource URIs as the 021F fallback. |
| U-21-c | Key-rotation overlap window (90d proposed; confirm vs adopter upgrade cadence) | 021B | **CLOSED in 021B (PR #37):** 90-day overlap accepted as default per D-024; rotation-time configuration is operator-side and lives in `scp-mcp-server keygen` invocation parameters (no plan amendment required). |
| U-21-d | ACC broker/dispatcher interface — PR-ready or needs harness? | 021G | OPEN — closes in slice 021G (post-pause). |
| U-21-e | `scp://rules/registry` internal shape stability — expose direct or via façade? | 021D | **CLOSED in 021D implementation commit `5debbcc`:** `src/standards_control_plane/mcp_server/resources.py` settles the façade choice in `ScpCommittedResourceCatalog._build_registry()` by publishing `scp://rules/registry` directly from committed `standards/standards-index.json` plus the per-domain index files, wrapped only by the common MCP resource envelope and `schema_version`. 021D did not add a second façade document or translation layer; the direct registry surface is the contract, and later refactors must preserve or version that shape rather than hide it behind a separate adapter. |
| U-21-f | stdio session-identity keying (PID/path/both) | 021E | **CLOSED in 021E (2026-04-28 hardening):** `propose()` derives `caller_id` from the live stdio server process as `stdio:<pid>:<resolved argv[0] path>`. That closes the "PID/path/both" choice in favour of both, with the advisory-security caveat already recorded in §8/021I: PID+path keying is for rate-limit partitioning and proposal attribution, not strong authentication. |
| U-21-g | PyPI package name + version bump cadence for `standards-control-plane[mcp]` extra | 021B | **CLOSED in 021B (PR #37):** package name `standards-control-plane`; extras key `[mcp]`; bump cadence aligned with rule changes (rule additions = minor; rule semantic changes = major) per ADOPT-001 §13 forthcoming guide. |
| U-21-h | `scp://rules/domain-map` source-of-truth — derived from registry or authored separately? | 021D | **CLOSED in 021D implementation commit `5debbcc`:** `src/standards_control_plane/mcp_server/resources.py` derives `scp://rules/domain-map` from the same rule metadata emitted by `ScpCommittedResourceCatalog._build_registry()`, then materialises the inverse glob-to-domain structure in `ScpCommittedResourceCatalog._build_domain_map()`. That closes the unknown in favour of derivation, not separate authoring, so `resolve_domain`, the resource payload, and the adopter hook all consume one source of truth and cannot drift through a second hand-maintained map file. |
| U-21-i | 021K target PR identity (post-020C, specific slice of next rule work) | 021K — closes when 020C merges | OPEN — closes when 020C merges. |
