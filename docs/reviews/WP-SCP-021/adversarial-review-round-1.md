# WP-SCP-021 — Adversarial review round 1

**Date:** 2026-04-21
**Plan version reviewed:** v0.1
**Reviewers (parallel):** Reviewer A (architect + security), Reviewer B (governance-realist + devex)
**Outcome:** Return to v0.2. 5 unique BLOCKING findings; ~18 MAJORs; multiple MINORs.

---

## Reviewer A (architect + security)

### BLOCKING

- **B-1 [in-scope]** HMAC symmetric-key forgery. `SCP_MCP_SIGNING_KEY` is named; HMAC is symmetric, so adopter hooks that verify receipts would have to hold the same key that signs — any adopter can forge receipts for any other adopter. Collapses D-025 to "trust every repo with the key." Fix: switch to Ed25519 asymmetric signing; SCP holds private key; adopters pull rotating public key from `scp://security/signing-keys` (or `docs/security/mcp-signing-keys.pub` with prior-key retention window). 021F documents rotation with overlap window + key-id in envelope.

- **B-2 [in-scope]** Break-glass `SCP_MCP_ALLOW_OFFLINE=true` is fail-OPEN, not fail-closed. Risk row says hook "fails closed" but the env var "allows commit" — fail-open dressed as break-glass. Fix: require sibling-commit artefact (mirror WP-SCP-020 `scp_bypass` three-gate): offline break-glass must land committed `docs/overrides/OVERRIDE-NNN.md` + matching expiry; SCP-MCP-E010 is tracked finding on `scp://findings/open`, not idle log.

- **B-3 [in-scope]** Source-of-truth ambiguity between MCP `consult_rules` and Rego gate. Plan never states precedence. Fix: elevate to plan invariant — "Rego gate is authoritative; MCP consult is advisory. A consult receipt is never a gate bypass." Add to §2 and Acceptance §9.

### MAJOR

- **M-4** Cache coherence on working-copy edits — MCP cache is git-sha-keyed; uncommitted `waivers.json` edits aren't reflected. Document as "MCP reflects committed state only."
- **M-5** 021K self-consume ordering paradox — 020C ships before 021 merges. 021K must target a post-020C SCP PR.
- **M-6** Tool-vs-resource duplication contract — `check_waiver` (tool) vs `scp://waivers` (resource). Name the rule: tools = parameterised + logged; resources = bulk + subscription.
- **M-7** stdio caller-identity unforgeable-only-by-convention — PID+path is spoofable. Acknowledge rate-limit is advisory; stronger defence is "propose writes to a branch not main."
- **M-8** Log integrity — "hourly manifest hash" gives a 60-min tamper window. Need per-line hash chain or append-only sink.
- **M-9** Consult-receipt replay across PRs — receipt must bind `{repo, head_sha, changed_files_hash}` and sign over them; hook rejects mismatch.
- **M-10** `audit_changed` no circuit-breaker — add 120s wall-clock timeout, diff-size cap, SCP-MCP-E011 error.
- **M-11** HTTP size + DoS — FastAPI max-body, max-response, concurrency ceiling.
- **M-12** Bearer-token rotation mechanism absent — add `SCP_MCP_TOKEN_PREV` fallback for overlap window.

### MINOR

- **m-13** Missing per-ID resource URIs — add `scp://waiver/<id>`, `scp://finding/<id>`, `scp://decision/<D-NNN>`.
- **m-14** Receipt GC unowned — specify `.gitignore` + regenerate per commit.
- **m-15** Identical-body proposal spam trivially evaded (one whitespace char) — use normalised-text hash.
- **m-16** Read-tool rate-limit deferred as follow-up (SCP-075-ratelimit) — accepted.
- **m-17** D-025 wording reinforces B-1 ("server-signed" is misleading under HMAC).

---

## Reviewer B (governance-realist + devex)

### BLOCKING

- **B1 [in-scope]** D-025 scope rule undefined. "Hook refuses commit without consult receipt" but doesn't say *which commits*. Typo fix in README? Version bump? STATUS refresh? Either friction explodes or rule is vacuous. Fix: hook matches changed-file paths against domain-map published at `scp://rules/domain-map`; skips consult for `{docs/**/*.md except DECISIONS.md, STATUS.md, *.txt, .gitignore}` by default.

- **B2 [in-scope]** Receipt validity triple-undefined: **(a) TTL** — no max_age; **(b) Scope-binding** — `consult_rules(domain=governance)` apparently satisfies architecture-touching PR; **(c) PR-binding** — no PR/branch/changed-file-set binding. One consult/session satisfies every subsequent PR. Fix: payload binds `{domains_covered, changed_files_hash, issued_at, expires_at ≤ 2h}`; hook re-verifies all four.

### MAJOR

- **M1** CLAUDE.md `domain → files` mapping missing. Agents guess `domain`; hook punishes wrong guesses. Ship `scp://rules/domain-map` resource + `resolve_domain(changed_files) → [domain]` tool.
- **M2** Break-glass composition with WP-SCP-020 incoherent. Two levers (`scp_bypass` + `SCP_MCP_ALLOW_OFFLINE`), two audit codes (SCP-E004 + SCP-MCP-E010), unclear which applies when. 021F must state: transport-offline vs policy-deny are different break-glass paths; both may fire together; audit markers compose.
- **M3** Offline-posture wording contradictory. Clarify: stdio CAN fail (binary missing, crash, repo not checked out); HTTP can fail (network). Both fail-closed; `SCP_MCP_ALLOW_OFFLINE=true` is sole escape with sibling artefact.
- **M4** Proposal queue silent-rot — 021E ships before WP-SCP-022 adjudication. Auto-stamp banner in proposal front-matter; `propose()` response includes `adjudication_status: "queued_no_adjudicator"`.
- **M5** Receipt artefact churn — `.scp/consult-receipts/<sha>.json` committed to main accumulates forever. Fix: gitignored + regenerated per commit OR feature-branch-only with pre-merge stripping.
- **M6** Distribution story missing — PyPI? vendored wheel? Docker? `uv tool install`? Plan silent. 021B or 021F must name channel + pin + one-liner install.
- **M7** Non-Claude client feature matrix absent. Enumerate for Cursor, Codex, Jules: tools/list, resources/list, progress notifications, resource-update notifications. Document re-polling fallback.
- **M8 [follow-up=SCP-075-errors]** Tool error-response UX undefined — structured `{error_code, message, remediation}` scheme. Mirror 020's `SCP-E00N` with `SCP-MCP-E0NN`.
- **M9** Tool response schema versioning — add `schema_version` on every tool output Pydantic model.

### MINOR

- **m1** `--stdio-test` semantics undefined — one-shot handshake listing tools+resources.
- **m2** `propose()` response must include `{pr_url_if_pushed, adjudication_status, expected_review_date}`.
- **m3** Agent feedback-loop worked example — 10-line flow in 021F.
- **m4 [follow-up=SCP-073-scaffolder composition]** Adopter scaffolding cost — 5 artefacts per repo. Compose with existing SCP-073-scaffolder.

---

## Round-1 consolidation

**5 unique BLOCKINGs → v0.2:**

| # | Finding | v0.2 fix |
|---|---|---|
| 1 | HMAC → Ed25519 asymmetric (A B-1) | D-025 rewritten; new `scp://security/signing-keys` resource; key rotation with overlap + key-id. |
| 2 | Break-glass fail-closed + sibling artefact (A B-2) | 021F/021I: `SCP_MCP_ALLOW_OFFLINE=true` requires committed `docs/overrides/OVERRIDE-NNN.md` + expiry; SCP-MCP-E010 = tracked finding. Composition with 020 documented. |
| 3 | Rego-authoritative invariant (A B-3) | §2 invariant line + §9 acceptance criterion. |
| 4 | D-025 scope rule (B B1) | `scp://rules/domain-map` resource + `resolve_domain` tool + default-skip glob list in 021F. |
| 5 | Receipt validity bindings (B B2, overlaps A M-9) | Receipt envelope binds `{repo, head_sha, changed_files_hash, domains_covered, issued_at, expires_at ≤ 2h}`; hook validates all four. |

**MAJORs folded into v0.2 slice acceptance** (M-4, M-5, M-6, M-7, M-8, M-10, M-11, M-12, M1, M2, M3, M4, M5, M6, M7, M9). **Follow-ups:** M8 → `SCP-075-errors`; m4 → composition with `SCP-073-scaffolder`. **MINORs** folded where cheap.
