# D-054 — WP-SCP-026 Shape C ratification (one-canary-fast + narrative-retract + named-successor for receipt build)

**Status:** DRAFT (operator-review surface; flips to ACCEPTED on PR merge per the post-merge ADR ceremony established by D-047/D-048/D-049/D-050).
**Date filed:** 2026-05-25
**Decision date:** TBD (operator signature on merge)
**Operator:** @jrnb2024
**Plan-doc anchor:** `docs/plans/WP-SCP-026-mcp-consumer-integration-v1.md` v1.0 §4.3 (Shape C) + §6 (D-054 reservation).
**Closes:** the §4 Shape choice (A / B / C) reserved at WP-SCP-026 plan-doc §6.
**Predecessors:** D-024 (MCP protocol adoption); D-031 (SCP single-operator key custody); D-040 (single-operator mode); WP-SCP-021 (MCP server build); WP-SCP-023 USER-GATE-D ("one real opt-in before threshold sign-off" precedent); WP-SCP-024 USER-GATE-E (operator-attended cohort cascade precedent).
**Successor reservations (do NOT consume):** D-055 (narrative-retraction contract; reserved for WP-SCP-026 slice 026D); D-056 (Threshold + USER-GATE-G observation contract; reserved for WP-SCP-026 slice 026F).

---

## Context

SCP's MCP server (`src/standards_control_plane/mcp_server/`) is structurally complete — 8 registered tools (`consult_rules`, `audit_changed`, `consult_scorecard`, `check_waiver`, `list_open_decisions`, `check_finding`, `resolve_domain`, `propose`), 11 resource URIs, stdio transport, Ed25519 keygen CLI, signed `propose()` proposals — but **has zero consumers across the estate** as of 2026-05-25. No adopter `.mcp.json` references SCP. No estate PreCommit hook validates SCP MCP receipts. ACC's PLAN-EST-P v3 explicitly proxies `scp.consult_rules` via a `scp-cli consult ...` subprocess shim that doesn't exist (SB-R1-020 leaves the door open to dropping the tool entirely from ACC v1).

Compounding the zero-consumer gap, the published narrative runs ahead of the code on three load-bearing points:

1. `docs/OVERVIEW.md` §1.4 + §2.2 + §3.4 + §5.1 reference "Ed25519-signed receipts on every `consult_rules` / `audit_changed` / `consult_scorecard` response" + "stdio + HTTP transports" + "`acc.brokapps.ai` hosting". **None implemented.**
2. `docs/adoption/mcp-adopter-contract.md` ships a PyNaCl verification snippet expecting `response["receipt"]["signature"]` + `response["receipt"]["payload"]`. **These fields do not exist** in any Pydantic response model (`ConsultRulesResponse` etc. at `src/standards_control_plane/mcp_server/tools.py:118-128` carry `schema_version` only).
3. Same doc §"Token rotation (HTTP transport)" documents `SCP_MCP_TOKEN` bearer-token rotation. **HTTP transport does not exist** (`grep` for `streamable_http`, `httpx`, `FastAPI`, `uvicorn` is empty inside the MCP server tree).

The doc-vs-code divergence is itself a SCP credibility risk: an adopter or agent author who reads the doc and writes consumer code following the documented receipt-verification API hits runtime errors because the documented fields aren't there. This isn't a future-state risk; it's already a live credibility hit for any adopter who starts the integration literally from the docs.

The question this decision answers: **for WP-SCP-026, which structural choice does SCP make between (A) ship one ACC-side canary fast and leave the divergence in place, (B) build the full receipt-signing + HTTP narrative as part of WP-SCP-026, or (C) hybrid — ship one canary fast + retract the overstated narrative + defer the receipt-signing build to a named successor with an explicit operator-attended trigger?**

## Decision

**SCP adopts Shape C — hybrid: one-canary-fast + narrative-retract + named-successor (WP-SCP-027) for the deferred receipt-signing build.**

Concretely, WP-SCP-026 carries six slices per the plan-doc §5 slice plan:

- **026A (kickoff)** — plan-doc v1.0 lock + Shape ratification (this ADR is the artefact).
- **026B** — `scp-cli` shim binary. Default option (i) per plan-doc §8 risk 1 + §10 Q2 default — thin wrapper subprocessing `scp-mcp-server stdio` and translating to/from MCP JSON-RPC. Preserves the MCP-as-protocol narrative. Option (ii) (direct Python entry-point importing `consult_rules_impl`) is the cheaper fallback if option (i) hits unforeseen blockers, but defaults to option (i) to keep the "MCP server is the consult surface" story load-bearing.
- **026C** — ACC-side RI canary wiring. Verify `tool_scp_consult_rules` in `~/Projects/ri-est-p-ws-2/.acc/mcp_server.py` returns useful output when calling `scp-cli consult --domain X`. ACC-side PR — no SCP-side decision (SCP-side decision is bounded to 026A/B/D/E/F).
- **026D** — narrative reconciliation. OVERVIEW.md §1.4 + §3.4 + mcp-adopter-contract.md amended so every claim reflects actually-shipped capabilities. Retracted claims (HTTP transport; Ed25519-signed-consult-response envelopes; `acc.brokapps.ai` MCP hosting) move to OVERVIEW.md §6.3 future-scope with a named forward link to WP-SCP-027. Decision filed inline as **D-055** at 026D merge.
- **026E** — ADOPT-001 MCP integration runbook. New §13 (or §12.7.17) covering `.mcp.json` registration shape, canonical first-consumer pattern, no receipt-validation step (Shape C defers; ADOPT-001 must reflect that, not the published-but-unimplemented PyNaCl snippet).
- **026F** — Threshold + USER-GATE-G observation slice. 4-week window from 026C ship. Criteria: ≥1 real `consult_rules` call in a real session; ≥1 agent-authored output references a returned rule. Decision filed inline as **D-056** at 026F close-out: either (a) advance to WP-SCP-027 (receipt-signing build) on operator-attended demand signal, or (b) hold WP-SCP-027 indefinitely.

The named successor is **WP-SCP-027 (HTTP transport + signed receipts)** — multi-week build, triggered by an operator-attended demand signal (an adopter or ACC team explicitly asks for receipt verification or HTTP-served consult). This satisfies the WP-SCP-021/023/024 precedent for "ship one real consumer fast + defer the unproven build to a named successor with explicit operator-attended trigger" rather than sequencing a multi-week build before the first consumer ships.

### What Shape C is and is not

**Is:**
- A scope-bounded commitment to ship one real consumer (ACC-RI canary) within ~1 week and make the docs honest about today's capabilities.
- A deferral — not a deletion — of the receipt-signing + HTTP narrative. The narrative moves to OVERVIEW.md §6.3 with a forward link, not into the bin.
- A named-successor commitment to WP-SCP-027 with a clear operator-attended trigger (demand signal from a named adopter or ACC team).

**Is not:**
- A re-implementation of the MCP server. Existing 8 tools + 11 resources + stdio transport are preserved as-is.
- A rewrite of ACC's PLAN-EST-P. WP-SCP-026 lives inside ACC's existing per-repo-MCP-server design.
- A commitment to ever ship receipt signing. WP-SCP-027 fires only on an explicit operator-attended demand signal; the absence of such a signal at 026F's 4-week mark is itself a valid outcome (hold indefinitely).
- A security-hardening exercise. The receipt-signing decision IS the security-hardening question; Shape C explicitly defers it.

### Anti-criterion (treat as failed and re-scope if any of these hold at the 026F 4-week mark)

- Zero real `consult_rules` invocations 4 weeks after 026C ship (the canary doesn't get used).
- The doc-vs-code divergence persists or grows (new aspirational claims land in OVERVIEW.md without supporting code).
- Adopter onboarding fails because the documented MCP integration path doesn't actually work post-026D.

## Rationale

**1. Shape B is the WP-SCP-021 trap.** WP-SCP-021's original receipt-signing narrative was published before being implemented; that implementation gap is what created WP-SCP-026 in the first place. Choosing Shape B would sequence another multi-week receipt-signing build before any consumer ships, repeating the same pattern that produced the current credibility hit. SCP has institutional evidence that "publish the narrative first + build later" produces shelfware; Shape B re-runs that experiment.

**2. Shape A leaves the credibility hit standing.** An ACC-side canary alone closes the headline "zero consumers" gap but leaves OVERVIEW.md and mcp-adopter-contract.md asserting capabilities the code does not implement. Adopters who follow the docs literally continue to hit broken-consumer-code runtime errors. The federation primitive's whole value proposition rests on documented capabilities being load-bearing; allowing a known doc-vs-code divergence to persist contradicts that proposition.

**3. Shape C threads the needle by mirroring established SCP discipline.** The "ship one real opt-in fast + defer the multi-week build to a named successor with operator-attended trigger" pattern has been used twice before in SCP's history:
  - WP-SCP-023 USER-GATE-D ratified the scorecard aggregator only after one opt-in adopter (SCP-self) was producing real emits — not after the full estate was wired.
  - WP-SCP-024 USER-GATE-E ratified the cohort cascade with PIM as adopter #1 (LIVE 2026-05-24), then onboarded CT as adopter #2 (LIVE 2026-05-25), rather than batch-onboarding all 5 adopters before testing any.

  Both patterns produced load-bearing learnings during the single-adopter slice that would have been buried inside a multi-week build. Shape C applies the same discipline to MCP consumer integration.

**4. Narrative retraction reframed as rescheduling.** D-055 (filed inline at 026D merge) will explicitly frame the retraction as "rescheduling, not deletion" — the receipt-signing + HTTP capabilities move to WP-SCP-027 with a clear operator-attended trigger, and OVERVIEW.md §6.3 forward-links to that WP. This avoids the political-cost framing of "walking back" published claims; the operator's narrative authority over future-scope reorganisation is established (cf. D-049 deferral of design-system view-coverage rule + view-scoped consult to "later slice once `DESIGN_SPEC.md` provides machine-readable per-view structure").

**5. Risk asymmetry favours Shape C.**
  - Shape A risk: doc-vs-code divergence persists. Recoverable but compounds over time.
  - Shape B risk: multi-week build that may produce no consumer (the WP-SCP-021 trap). Recoverable but expensive; bus-factor-1 amplifies cost (D-040).
  - Shape C risk: canary may not get used by an actual ACC dispatch (anti-criterion 1 catches this); narrative retraction has political cost (mitigated by D-055 reframing). Both are recoverable inside the 4-week observation window and produce learning regardless of outcome.

  Shape C's failure modes are observable + bounded; Shapes A and B's failure modes either persist (A) or hide inside a long build (B).

**6. Operator-attended discipline is preserved.** Shape C does not commit SCP to ever shipping receipt-signing — WP-SCP-027 fires only on an explicit operator-attended demand signal at 026F close-out. The absence of such a signal is itself a valid outcome (hold WP-SCP-027 indefinitely). This matches the D-040 single-operator-mode + D-031 single-operator-key-custody posture: decisions that commit SCP to multi-week kernel-touching builds require operator-attended ratification, not orchestrator default.

**7. Bus-factor-1 acknowledged + mitigated.** This decision is operator-authored per D-040 single-operator-mode; the plan-doc R-cycle (forthcoming for WP-SCP-026 slices) is the discipline-anchor; operator-attended merge on this ADR is the ratification. 026F's 4-week observation window provides a natural checkpoint for the operator to revisit Shape choice if the canary fails to attract real usage.

## Reversal mechanism

If WP-SCP-026 ships under Shape C and the 4-week 026F observation surfaces that Shape B was the right call all along, the reversal cost is bounded:

- **026D narrative retraction reversed:** PR amending OVERVIEW.md §6.3 to move HTTP transport + signed-receipt items back to §1.4 + §3.4 main narrative. <1 day. No code change.
- **026E ADOPT-001 amendment reversed:** PR amending the new §13 to add the receipt-validation step. <1 day. No code change.
- **Receipt-signing + HTTP build still required:** the WP-SCP-027 build is the same multi-week scope regardless of when it ships. Choosing Shape C now does not increase the cost of the WP-SCP-027 build later.

Total reversal cost: ≤2 days of doc work + the existing WP-SCP-027 build (which would have been required under Shape B anyway). The decision is therefore architecturally non-locking — Shape C delays WP-SCP-027 without making it more expensive.

## Boundaries (anti-scope of THIS ADR)

This ADR ratifies Shape choice + slice plan only. It does NOT:

- Specify the `scp-cli` binary's CLI shape (deferred to 026B).
- Specify the exact OVERVIEW.md / mcp-adopter-contract.md retraction text (deferred to 026D + D-055).
- Specify the ADOPT-001 §13 MCP runbook content (deferred to 026E).
- Specify the 026F Threshold criteria beyond the §"Decision" anti-criterion bullets (deferred to D-056).
- Commit to WP-SCP-027 shipping (deferred to operator-attended D-056 decision).

Each downstream slice carries its own R-cycle + ratification ceremony. D-054 is the parent decision; D-055 + D-056 are reserved children.

## Status flip ceremony

Per established estate pattern (D-047, D-048, D-049, D-050), this ADR's status flips DRAFT → ACCEPTED on the merge of the PR opening it. Operator merge constitutes the ratification signature. Post-merge, the WP-SCP-026 plan-doc v1.0 §6 D-054 reservation row + the DECISIONS.md tabular row reference this filed ADR by path. Successor decisions (D-055, D-056) follow the same DRAFT → ACCEPTED post-merge pattern at their respective slice merges.

---

**Identified at:** 2026-05-25 WP-SCP-026 plan-doc v1.0 §4.3 Shape C ratification (orchestrator selected Shape C per operator-delegated strategic choice on the recommendation in the research output).

**Filed:** 2026-05-25 (this ADR PR).

**Closes when:** operator merges this PR + DECISIONS.md row appended.
