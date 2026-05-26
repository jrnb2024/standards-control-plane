# D-055 — WP-SCP-026 026D narrative reconciliation: retract HTTP MCP transport + Ed25519-signed-consult-receipts + `acc.brokapps.ai` MCP hosting

**Status:** DRAFT (operator-review surface; flips to ACCEPTED on PR merge per the post-merge ADR ceremony established by D-047 / D-048 / D-049 / D-050 / D-054).
**Date filed:** 2026-05-26
**Decision date:** TBD (operator signature on merge)
**Operator:** @jrnb2024
**Plan-doc anchor:** `docs/plans/WP-SCP-026-mcp-consumer-integration-v1.md` v1.0 §5 (slice 026D) + §6 (D-055 reservation).
**Closes:** D-054 §"Decision" → slice 026D row ("Narrative reconciliation. OVERVIEW.md §1.4 + §3.4 + mcp-adopter-contract.md amended so every claim reflects actually-shipped capabilities. Retracted claims … move to OVERVIEW.md §6.3 future-scope with a named forward link to WP-SCP-027. Decision filed inline as D-055 at 026D merge.").
**Predecessor:** D-054 (Shape C ratification, 2026-05-25).
**Successor reservation (do NOT consume):** D-056 (WP-SCP-026 026F Threshold + USER-GATE-G observation contract; reserved at D-054 §"Successor reservations").

---

## Context

D-054 ratified Shape C for WP-SCP-026 — one-canary-fast + narrative-retract + named-successor (WP-SCP-027) for the deferred receipt-signing + HTTP-transport build. Three load-bearing claims in the SCP narrative reference capabilities that the code does not implement:

1. **`docs/OVERVIEW.md` §1.4 + §3.4 + §5.1.** "scp.consult_rules(domain) — agent asks 'what rules apply if I'm changing files under X?' before authoring; returns matched rules + Ed25519-signed receipt." Plus a multi-step flow in §3.4 describing receipt envelopes (key_id + repo + head_sha + base_sha + changed_files_hash + domains_covered + issued_at + expires_at ≤ 2h), signing with the private Ed25519 key, and adopter PreCommit-hook validation against `docs/security/mcp-signing-keys.pub`. Plus a WP-SCP-021 row in §5.1 framed as "Ed25519-signed receipts + scoped pre-code consult; stdio + HTTP transports". None implemented.

2. **`docs/adoption/mcp-adopter-contract.md` §"Receipt verification (Ed25519-signed responses)"** ships a PyNaCl verification snippet expecting `response["receipt"]["signature"]` + `response["receipt"]["payload"]`. These fields do not exist in any Pydantic response model — `ConsultRulesResponse` at `src/standards_control_plane/mcp_server/tools.py:118-128` carries `schema_version` only. An adopter writing consumer code following the snippet literally hits `KeyError` on the first call.

3. **`docs/adoption/mcp-adopter-contract.md` §"Token rotation (HTTP transport)"** documents `SCP_MCP_TOKEN` bearer-token rotation with a 30-day overlap cadence. HTTP transport does not exist — `grep` for `streamable_http` / `httpx` / `FastAPI` / `uvicorn` inside `src/standards_control_plane/mcp_server/` returns empty. Server transport is stdio-only (`server.py:87`).

Auxiliary: `docs/OVERVIEW.md` §2.2 previously referenced `acc.brokapps.ai` as a deployment target for SCP MCP. `acc.brokapps.ai` exists, but it is ACC's orchestrator UI — not SCP's MCP server. The `Live Watch UI (acc.brokapps.ai)` mention in §2.1 is correctly scoped to ACC's UI; the prior MCP-hosting framing was inaccurate and has been removed (corrected in STATUS PR #173 already; verified clean post-merge).

The doc-vs-code divergence is itself a SCP credibility risk: an adopter following the docs literally writes broken consumer code. D-054 chose Shape C explicitly to close this gap.

## Decision

Retract from `docs/OVERVIEW.md`, `docs/adoption/mcp-adopter-contract.md`, `docs/adoption/ADOPT-001-project-onboarding.md`, `docs/home/HOME.md`, `docs/ESTATE-CONVERGENCE.md`, and `docs/gates/USER-GATE-D.md` every claim that describes the unimplemented receipt-signing + HTTP-transport + `acc.brokapps.ai` MCP-hosting capabilities as if they were shipped. Move the descriptions to `docs/OVERVIEW.md` §6.3 future-scope (the "Tighter agent integration" section) under a single forward-linked entry for **WP-SCP-027 — Ed25519-signed consult receipts + HTTP MCP transport + adopter PreCommit-receipt-validator**.

**Scope expansion note (2026-05-26):** the WP-SCP-026 autonomous-run prompt pre-cited 18 lines across 3 files; the run-time `grep` per `feedback_grep_production_before_planning.md` discipline surfaced 7 additional current-state lines across 3 further files (HOME.md / ESTATE-CONVERGENCE.md / USER-GATE-D.md) that contained the same class of retracted claim. Per operator decision 2026-05-26 (Option 2 in the scope-expansion question), this PR extends to 25 lines across 6 files. Historical artefacts (`docs/plans/WP-SCP-021-*` / `docs/plans/WP-SCP-023-*` / `docs/releases/v1.0.0-rc.1.md` / `docs/decisions/D-049-*` / `docs/BACKLOG.md` L121 SCP-075 / `docs/DECISIONS.md` D-024 + D-025 rows) are deliberately LEFT AS-IS — they describe state at the time of authoring and shouldn't be rewritten; supersede-marker addition is filed forward as `FUP-WP-SCP-026-026D-HISTORICAL-SUPERSEDE-MARKERS-001` (P3) in BACKLOG.md.

Concretely, this PR mutates:

1. **`docs/OVERVIEW.md`** —
   - §1.4: drop "+ Ed25519-signed receipt" clause from the `consult_rules` description; replace the receipt-signed/PreCommit narrative paragraph with an explicit retraction note ("Per D-054 + D-055, consult responses are unsigned JSON today. Adopters do NOT validate receipts in v1.").
   - §3.4: replace the 7-step signed-receipt flow (steps 2-6 of the prior numbered list) with a 5-step plain-JSON flow that names `scp-cli consult` as the WP-SCP-026 026B caller entry-point + states explicitly that receipt-signing + PreCommit-hook validation are retracted to §6.3.
   - §5.1: amend the WP-SCP-021 row to reflect what shipped (stdio MCP scaffolding only; signed-receipt + HTTP narrative parked under WP-SCP-027).
   - §6.3: extend the "Tighter agent integration" list with the **WP-SCP-027** entry enumerating signed-response envelope shape + HTTP transport with `SCP_MCP_TOKEN` rotation + adopter PreCommit-receipt-validator + extension to PrePush / PrePR / PreDeploy hooks.
   - §6.5: amend the "Compliance attestation" bullet to make clear that compliance attestation is performed at merge-time by the federation primitive's required check, not by pre-commit receipts.

2. **`docs/adoption/mcp-adopter-contract.md`** —
   - drop the HTTP-transport clause from the §"Pre-code consult — scp.consult_rules" latency budget line.
   - delete the entire §"Receipt verification (Ed25519-signed responses)" section, including the PyNaCl `verify_receipt(...)` snippet that referenced `response["receipt"]["signature"]` + `response["receipt"]["payload"]`.
   - delete the entire §"Token rotation (HTTP transport)" section.
   - replace both deleted sections with a single retraction note pointing to `docs/OVERVIEW.md` §6.3 + WP-SCP-027.
   - drop the "Receipt signature verification fail" + "401 UNAUTHORIZED (HTTP)" rows from the §"Failure modes adopters MUST handle" table.
   - add a changelog entry documenting the retraction.

3. **`docs/adoption/ADOPT-001-project-onboarding.md`** —
   - §7.3 §"Add thin wrapper scripts" — replace the `scripts/scp-consult` recommendation with `scp-cli consult` (the binary delivered by WP-SCP-026 026B). Cross-reference §13 (delivered by WP-SCP-026 026E).

4. **`docs/home/HOME.md`** (current-state landing page; deployed at `/` route on `scp.brokapps.ai`) —
   - §"What SCP is" item 3 — `scp.consult_rules` return shape swapped from "signed receipt + adopter-side pre-commit hook validates" to plain `ConsultRulesResponse` JSON; retraction note pointing to §6.3 + WP-SCP-027.
   - §"The MCP consult flow" (§5.4) — 7-step receipt-signed agent flow rewritten 5-step naming `scp-cli consult` (WP-SCP-026 026B) as the entry-point; retraction paragraph documenting deferred capability + named successor WP-SCP-027.
   - 3-layer-stack diagram caption + service-endpoints table row for `MCP server` — `acc.brokapps.ai (ACC-hosted; stdio + HTTP transports per D-024)` corrected to `scp-mcp-server` CLI; stdio only; zero adopter consumers; `acc.brokapps.ai` is ACC's orchestrator UI not SCP's MCP.
   - `/consult` + `/audit` service-endpoint rows — disambiguated "HTTP transport" to clarify FastAPI HTTP service (distinct from MCP, which is stdio-only).
   - "Compliance attestation" bullet (§"The bigger ambition") — rewritten to credit merge-gate enforcement, parallel to OVERVIEW.md §6.5 amendment.
   - ACC layer text — receipt-validation claim dropped from PreToolUse description.

5. **`docs/ESTATE-CONVERGENCE.md`** —
   - §"Where SCP fits" — `MCP server at acc.brokapps.ai` claim retracted; clarified that MCP is stdio-only (zero consumers; HTTP + acc.brokapps.ai-hosting deferred to WP-SCP-027); `scp.brokapps.ai` is the deployed FastAPI HTTP service (not MCP).
   - §"Cross-estate aggregator" — `Ed25519-signed receipts` qualifier dropped from MCP server description; retraction note added with WP-SCP-027 forward link.

6. **`docs/gates/USER-GATE-D.md`** —
   - criterion (iv) — `Verified by querying the deployed MCP server at acc.brokapps.ai` retracted; reworded to require reachability of `scp.consult_scorecard` via any working consumer path (stdio MCP via `scp-cli` post-026B or via a per-repo MCP server that proxies the tool); explicit note documenting that `acc.brokapps.ai` is ACC's orchestrator UI, not SCP's MCP, so the prior criterion's predicate (`TF-023D-005 — MCP server redeploy on acc.brokapps.ai`) is non-applicable as written; reframed under WP-SCP-026 first-consumer canary (026F observation) or under WP-SCP-027 if HTTP transport ever ships.

7. **`docs/DECISIONS.md`** —
   - append a row for D-055 after D-054 with the full retraction summary + rationale.
   - bump `**Last Updated:**` header.

9. **`STATUS.md`** —
   - chain row documenting the retraction PR (path-trigger for `check-invocation-log-entry`).

## Rationale

**1. Credibility cost of doc-vs-code divergence is already accruing.** An adopter who reads `mcp-adopter-contract.md` and writes consumer code following the documented PyNaCl snippet literally hits runtime errors on the first call — `response["receipt"]["signature"]` does not exist in the response shape. This isn't a future-state risk; it's a current credibility hit for any adopter who starts integration literally from the docs. WP-SCP-026 Shape C explicitly chose to close this gap; D-055 is the artefact that closes it.

**2. Retraction is rescheduling, not deletion.** The receipt-signing + HTTP capabilities move to `docs/OVERVIEW.md` §6.3 with an explicit forward link to WP-SCP-027 and a clear operator-attended demand-signal trigger. The narrative authority over future-scope reorganisation is established (cf. D-049 deferral of design-system view-coverage rule + view-scoped consult; D-054 same-pattern deferral for WP-SCP-026's own scope choices). Adopters who want signed receipts have a named successor WP to point at, not a deletion.

**3. Diff-verification grounds the retraction in code, not assertion.** Per `feedback_verbatim_claim_diff_verification.md`, every retracted line is verified via the actual file diff in this PR. Reviewers diff-verify at R1 time via `git show <PR-merge-sha>:docs/OVERVIEW.md` (and the equivalent for the other touched files). No claim about the prior state is asserted without being demonstrable in the same PR.

**4. Operator-attended discipline preserved.** D-055 is an ADR; it does NOT commit SCP to ever shipping WP-SCP-027. WP-SCP-027 fires only on an explicit operator-attended demand signal at 026F close-out per D-054 §"Decision" → 026F row. Absence of such a signal at the 4-week observation mark is itself a valid outcome (hold WP-SCP-027 indefinitely). The deferral does not lock SCP into the WP-SCP-027 build; it only locks the narrative to what's actually shipped.

**5. Bus-factor-1 mitigated by ratification chain.** This decision is operator-authored per D-040 single-operator-mode. The R-cycle on this PR (3-lens R1 doc review) is the discipline anchor. The narrative reconciliation is reversible — if WP-SCP-027 ships later, swapping §6.3 ↔ §1.4 / §3.4 is ≤2 days of doc work per D-054 §"Reversal mechanism". The build itself is the same scope regardless of when it ships, so D-055 delays WP-SCP-027 without making it more expensive.

## Reversal mechanism

If WP-SCP-027 ships, the reversal cost is bounded:

- §6.3 entry → §1.4 / §3.4 main-narrative reinstatement: PR amending the moved text back to its original locations. <1 day, no code change.
- `mcp-adopter-contract.md` retraction note → restored §"Receipt verification" + §"Token rotation" sections + reinstated failure-modes rows: PR amending the file. <1 day, no code change.
- ADOPT-001 §13 retraction notes (added by WP-SCP-026 026E) → updated to reflect shipped receipt validation: PR amending the file. <1 day, no code change.

Total reversal cost ≤2 days of doc work. The WP-SCP-027 build itself is the multi-week shape regardless of when it ships, so D-055 does not increase the cost of WP-SCP-027.

## Boundaries (anti-scope of THIS ADR)

This ADR ratifies the narrative reconciliation only. It does NOT:

- Specify the WP-SCP-027 implementation shape (deferred to WP-SCP-027 plan-doc at fire time).
- Specify the operator-attended demand-signal trigger format (deferred to D-056 + WP-SCP-026 026F close-out).
- Specify ADOPT-001 §13 content (deferred to WP-SCP-026 026E).
- Specify the WP-SCP-026 026B `scp-cli` shim (deferred to 026B implementation slice).
- Commit SCP to ever shipping WP-SCP-027 (per D-054 §"What Shape C is and is not" — operator may choose to hold indefinitely).

## Diff-verification

Per `feedback_verbatim_claim_diff_verification.md`, every retraction in this PR is grounded in the actual file diff. Reviewers verify at R1 time:

```bash
git show <PR-merge-sha>:docs/OVERVIEW.md > /tmp/post.md
git show <PR-merge-sha>^:docs/OVERVIEW.md > /tmp/pre.md
diff /tmp/pre.md /tmp/post.md
# Expected: 8 specific line-class changes per D-055 §"Decision" item 1
```

Same pattern for `docs/adoption/mcp-adopter-contract.md` (2 section deletions + 1 line amendment + 1 row deletion + 1 changelog entry) and `docs/adoption/ADOPT-001-project-onboarding.md` (1 line replacement + 1 cross-reference).

## Status flip ceremony

Per established estate pattern (D-047 / D-048 / D-049 / D-050 / D-054), this ADR's status flips DRAFT → ACCEPTED on the merge of the PR that opens it. Operator merge constitutes the ratification signature. Post-merge, the WP-SCP-026 plan-doc v1.0 §6 D-055 reservation row + the `docs/DECISIONS.md` tabular row reference this filed ADR by path. Successor decision D-056 follows the same DRAFT → ACCEPTED post-merge pattern at WP-SCP-026 026F close-out.

**PR body discipline (pre-merge gate).** The PR opening this ADR MUST include a `## R1 evidence` block with three lens lines matching the `.github/workflows/r1-evidence-check.yml` validator regex `^[ \t]*-[ \t]*(correctness|safety_bypass|completeness_governance):[ \t]*\S`: `- correctness: <evidence>`, `- safety_bypass: <evidence>`, `- completeness_governance: <evidence>`. NO `**bold**` tagging on lens labels — the validator rejects bold. CI fails on PR open without all three lenses populated.

---

**Identified at:** 2026-05-25 WP-SCP-026 plan-doc v1.0 §6 D-055 reservation.

**Filed:** 2026-05-26 (this ADR PR).

**Closes when:** operator merges this PR + `docs/DECISIONS.md` row appended + STATUS chain row landed.
