# ProgrammePlan — WP-SCP-026 MCP Consumer Integration v1

**Work Package:** `WP-SCP-026`
**Version:** 1.0 (ACTIVE — Shape C ratified 2026-05-25)
**Status:** ACTIVE — Phase 1 (Shape C; see §4.3) authoring authorisation in place; implementation kicks off post-merge
**Date kicked off:** 2026-05-25 (operator-delegated strategic choice; orchestrator selected Shape C per the research recommendation + WP-SCP-021/023/024 precedent for "ship one real consumer fast + defer the unproven build to a named successor" discipline)
**Owner:** TBD (named at first implementation slice)
**Predecessors:**
- WP-SCP-021 (MCP Server) — landed; `consult_rules`, `audit_changed`, `consult_scorecard`, `propose`, etc. exposed via stdio MCP
- WP-SCP-024 024C (PIM cohort adopter #1) — LIVE since 2026-05-24

**Companion ratification artefacts:** D-054 reservation per §6 (Shape choice ratification + narrative reconciliation contract). Files inline on first implementation slice merge per the established post-merge ADR ceremony pattern (cf. D-049 + D-050).

**Why Shape C (this version's strategic decision):**

The doc-vs-code divergence is itself a SCP credibility risk — an adopter who reads `docs/adoption/mcp-adopter-contract.md` and writes consumer code following the documented receipt-verification API will hit runtime errors because the documented `response["receipt"]["signature"]` + `response["receipt"]["payload"]` fields do not exist in the Pydantic response models. This isn't a future risk; it's already a credibility hit for any adopter who starts the integration following the docs literally. Shape A (ACC-side canary only) leaves the divergence in place — credibility hit persists. Shape B (full receipt-signing + HTTP build) sequences a multi-week kernel build before any consumer ships, which is exactly the trap WP-SCP-021 fell into (the MCP server's receipt-signing narrative was published before being implemented; the implementation gap is what created this WP). Shape C threads the needle: ship one real consumer fast (closes the headline "zero consumers" gap; matches WP-SCP-023 USER-GATE-D pattern of "one real opt-in before threshold sign-off"), retract the overstated narrative (closes the credibility-hit risk), defer the actual receipt-signing build to a named WP-SCP-027 with a clear operator-attended trigger ("demand signal from an adopter or ACC team explicitly asks for receipt verification"). This matches the established SCP discipline of operator-attended USER-GATE checkpoints (WP-SCP-023 USER-GATE-D, WP-SCP-024 USER-GATE-E).

---

## 1. Purpose

SCP's MCP server (`src/standards_control_plane/mcp_server/`) is structurally complete — 8 registered tools, 11 resource URIs, Ed25519 keygen CLI, stdio transport, signed `propose()` proposals — but **has zero consumers across the estate**. No adopter has `.mcp.json` SCP entries. No PreCommit hook anywhere in the estate validates SCP MCP receipts (the only PreCommit hook in the cohort, FLA's, runs orchestrator-sprawl checks; ADOPT-001 §12.7.9's PreCommit hook is local OPA evaluation, not MCP). ACC's PLAN-EST-P v3 explicitly *avoids* calling SCP's MCP server: per-repo MCP servers proxy `scp.consult_rules` by `subprocess.run(["scp-cli", "consult", ...])` (a CLI that doesn't exist; SB-R1-020 leaves the door open to dropping the tool from v1 MVP).

WP-SCP-026 is the first batch of MCP-consumer-integration work. It exists to test the proposition that SCP's pre-code consult surface (the part that's supposed to *prevent* defects rather than catch them at the merge gate) is load-bearing — not just that the code compiles.

Companion concern: the OVERVIEW.md / mcp-adopter-contract.md / ADOPT-001 narrative describes capabilities the code does not implement (Ed25519-signed receipts on `consult_rules` / `audit_changed` / `consult_scorecard` responses; HTTP transport; `acc.brokapps.ai` hosting). Either the docs lead the code (build the capabilities) or the docs lag the code (retract the claims). The choice between those forks is the load-bearing decision in this WP.

## 2. Goal + success criterion

**Goal:** ship at least one end-to-end working consumer of SCP's MCP `consult_rules` tool (an agent that calls it, gets back useful guidance, and uses the response in an authored output). Make the OVERVIEW.md / mcp-adopter-contract.md / ADOPT-001 narrative honest about what's there today.

**Success criterion (4-week observation window from first-consumer ship):**
- ≥1 agent calls `scp.consult_rules` from a real session (not a unit test); the call returns a non-empty `applicable_rules` list; the agent's authored output references at least one returned rule.
- OVERVIEW.md §1.4 + §3.4 + mcp-adopter-contract.md + ADOPT-001 §12 reflect actually-implemented capabilities (no claims of HTTP transport / signed-receipt envelopes / `acc.brokapps.ai` hosting unless those have shipped).
- Either: (a) signed-receipt envelopes ship on `consult_rules` / `audit_changed` / `consult_scorecard` responses + adopter PreCommit hook validates them, OR (b) the receipt-signing narrative is retracted to §6.3 "Tighter agent integration" future-scope.

**Anti-criterion (treat as failed and re-scope if any of these hold at the 4-week mark):**
- Zero real `consult_rules` invocations 4 weeks after ship (the canary doesn't get used).
- The doc-vs-code divergence persists or grows (new aspirational claims land in OVERVIEW.md without supporting code).
- Adopter onboarding fails because the documented MCP integration path doesn't actually work (operator hits the "consumer-side code following mcp-adopter-contract.md literally fails" trap).

## 3. Findings driving this WP (research input)

Research conducted 2026-05-25 via parallel sub-agent (general-purpose; read-only). Full report at `~/.claude/projects/-Users-amplience-Projects/memory/` if persisted; key findings reproduced here for plan-doc context.

### 3.1 What SCP's MCP server actually exposes

**Tools (8, registered at `tools.py:1483-1490`):**
- `consult_rules(domain, subsystem?, area_id?)` — returns ConsultRulesResponse with `domains`, `approved_patterns`, `open_findings`, `historical_reviews`, `applicable_rules`, `guidance`, `risks`, `confidence`, `confidence_class`. **No receipt field on the response model.**
- `check_waiver(rule_id, scope?)` — returns active WaiverMatch list.
- `list_open_decisions(since?)` — parses `docs/DECISIONS.md`; returns D-NNN rows.
- `check_finding(finding_id)` — returns raw finding dict.
- `audit_changed(base_ref?, head_ref?)` — git diff + subprocess invoke of `standards_control_plane.cli audit-changed`; 1h LRU cache; 500-file diff cap; 120s timeout.
- `resolve_domain(changed_files)` — exact-path registry map + fuzzy heuristic → domain set + confidence float.
- `propose(title, body, affected_repos, rule_id?)` — only write tool; embeds `signing_key_id`; rate-limited 10/hr; 24h dedupe.
- `consult_scorecard(repo_filter?, since_emitted_at?)` — aggregated counts only (NEVER waiver content per WP-SCP-023 invariant 2).

**Resources (11 URI types):** 7 static (`scp://rules/registry`, `scp://rules/domain-map`, `scp://decisions`, `scp://findings/open`, `scp://waivers`, `scp://status`, `scp://security/signing-keys`) + 4 templated (`scp://rule/{id}`, `scp://waiver/{id}`, `scp://finding/{id}`, `scp://decision/{D-NNN}`). All resources reflect committed git state (`git show HEAD:path`); per-HEAD-SHA snapshot cache; resource-update notifications wired via FastMCP `subscribe()`. Resource payloads wrap responses with `_resource_envelope(payload, key_id=...)` — `key_id` is informational; no signature is computed.

**Transport:** stdio only (`server.py:87`). **No HTTP transport implemented** (`grep` for `streamable_http`, `httpx`, `FastAPI`, `uvicorn` is empty in `src/standards_control_plane/mcp_server/`).

### 3.2 Doc-vs-code divergences (load-bearing)

1. `docs/OVERVIEW.md` §1.4 + §2.2 + §3.4 + §5.1 reference "stdio + HTTP transports" / "Ed25519-signed receipts on every consult_rules / audit_changed / consult_scorecard response" / "acc.brokapps.ai hosting". **None implemented.**
2. `docs/adoption/mcp-adopter-contract.md` provides a PyNaCl verification snippet expecting `response["receipt"]["signature"]` + `response["receipt"]["payload"]`. **These fields do not exist in any of the response Pydantic models** (`ConsultRulesResponse` etc. at `tools.py:118-128` carry `schema_version` only).
3. Same doc §"Token rotation (HTTP transport)" documents `SCP_MCP_TOKEN` bearer-token rotation. **HTTP transport does not exist.**
4. ADOPT-001 has no §12.x covering MCP onboarding (`.mcp.json` registration, `scp-mcp-server serve` invocation, receipt-validation hook installation, token configuration). §7.3 mentions a `scripts/scp-consult` wrapper script but doesn't specify the integration shape. §5.3 gestures at "optional shared consult service" non-prescriptively.

### 3.3 ACC's intended integration shape

PLAN-EST-P v3 §3.3 defines the canonical envisioning:
- The intended consumer is **per-repo MCP servers** spawned as subprocesses inside each target repo by ACC's `per_repo_mcp_server_builder.py`. ACC dispatches via `subprocess.Popen([sys.executable, str(workspace_path / '.acc/mcp_server.py')], ...)` then talks JSON-RPC over stdio to that per-repo server.
- The per-repo server's `scp.consult_rules` proxies a CLI (per RI canary at `~/Projects/ri-est-p-ws-2/.acc/mcp_server.py:298-338`): `subprocess.run(["scp-cli", "consult", "--domain", domain], ...)`. SCP exposes `scp-mcp-server serve` and a Python module CLI but **no `scp-cli` binary**.
- ACC orchestrators do NOT call SCP MCP directly. PreToolUse hook (Go `acc-hook` Phase X) enforces scope-boundary from `.acc/active-dispatch.json`; does not consult SCP.

### 3.4 Cohort adopter state

`find -name ".mcp.json"` across 8 adopters (PIM, CT, mapp-doc-agent, Recommender, FLA, RI, SA, VS): **zero hits**. `find -name ".pre-commit-config.yaml"`: only FLA has one (runs orchestrator-internal CLI; not SCP). **0 of 8 adopters has any SCP MCP wiring.**

## 4. Three possible scoping shapes — operator-attended choice required

Three structural choices for WP-SCP-026's scope. The operator picks one at WP-SCP-026 kickoff (or proposes a fourth). Each choice has different effort/risk/load-bearing-ness trade-offs.

### 4.1 Shape A — ACC-side integration only (one canary path)

**Scope:** wire ACC's per-repo MCP server builder (or ACC orchestrator directly) to actually call SCP's MCP server. Concretely: drop a real `scp-cli` shim into SCP that talks MCP stdio to the local server, so the RI canary's `tool_scp_consult_rules` returns useful output. Verify one end-to-end ACC dispatch from a programme on RI uses real SCP rules. Doesn't touch receipt narrative, HTTP narrative, or adopter cohort.

**Effort:** ~3-4 days (matches ACC's original 2026-05-09 estimate; PLAN-EST-P §"Where to ask for help" cites a ~3-day spike envelope).

**Risk:** low. No kernel-dangerous touches. No multi-week receipt-signing build. Defers all doc-reconciliation work.

**Load-bearing-ness:** high — closes the headline "zero consumers" gap with one consumer. ACC EST-P unblocks at the SCP-MCP integration level (independent of the WP-SCP-024 cohort cascade).

### 4.2 Shape B — SCP-side narrative reconciliation + ADOPT-001 §12.x.MCP + cohort onboarding (parallel to WP-SCP-024 cascade)

**Scope:** decide whether the receipt-signing + HTTP narrative becomes real or gets retracted.
- **If real:** implement signed-receipt envelopes on `consult_rules`/`audit_changed`/`consult_scorecard`; implement HTTP transport in `server.py`; ship `SCP_MCP_TOKEN` rotation contract.
- **If retracted:** amend OVERVIEW.md §1.4 + §3.4 + mcp-adopter-contract.md to drop receipt-verification + HTTP claims; mark the narrative as future-scope (§6.3).

Either way: add ADOPT-001 §12.7.17 (or new §13) covering `.mcp.json` registration, receipt-validation hook (if real), token configuration (if HTTP); push to 5 cohort adopters' `.claude/` + `.mcp.json` as cascade slices alongside their wrapper installation.

**Effort:** 2-4 weeks depending on which fork (real vs retracted); the receipt-signing fork is multi-week (key rotation, signature scheme, replay-defence on consult headers, expires_at semantics, break-glass override; mirrors WP-SCP-021's original scope per OVERVIEW.md §5.1).

**Risk:** medium-high. Multi-week build before the first consumer ships. Risks WP-SCP-026 itself becoming shelfware (the same trap WP-SCP-021 fell into).

**Load-bearing-ness:** highest — closes the doc-vs-code divergence + sets up the federation primitive's pre-code consult surface across the estate.

### 4.3 Shape C — hybrid (RECOMMENDED)

**Scope:** First half: Shape A end-to-end (single ACC canary path, stdio, no receipt change). Second half: explicit narrative-retraction PR on OVERVIEW.md + mcp-adopter-contract.md, deferring receipt signing + HTTP to a named future WP-SCP-027 (or making them §6.3 "tighter agent integration" items). Defers the cohort onboarding to a follow-up wave but unblocks ACC and gets at least one real consumer into the estate while the receipt question is operator-decided.

**Effort:** ~1 week (Shape A's 3-4 days + 2-3 days of doc-reconciliation review with operator-attended decisions).

**Risk:** low-medium. Ships one real consumer fast; makes the docs honest; defers the receipt-signing decision to a named operator-attended fork point.

**Load-bearing-ness:** medium-high — closes the headline gap + de-risks the doc-vs-code divergence without committing to the larger receipt-signing build.

**Why this one (researcher's recommendation):** the credibility cost of the OVERVIEW.md / mcp-adopter-contract.md narrative running ahead of the code is itself a SCP credibility hit — an adopter who follows the doc literally writes broken consumer code. Shape A alone leaves the divergence in place; Shape B sequences a multi-week receipt-signing build before the first consumer ships (high-risk; risks WP-SCP-026 itself becoming shelfware). Shape C ships one real consumer fast, makes the docs honest about what's there today, and explicitly defers the receipt-signing decision to a named operator-attended fork point — which matches the SCP project's existing patterns (cf. WP-SCP-023's threshold/operator-gate discipline).

## 5. Slice plan (preliminary — finalised at kickoff after §4 Shape choice)

**Conditional on Shape C selection** (replaces with appropriate slices if A or B chosen):

| Slice | Deliverable | Decision |
|---|---|---|
| 026A (kickoff) | Plan-doc v1.0 lock + Shape ratification | D-054 (or inline under D-036) |
| 026B | `scp-cli` shim binary (thin wrapper over `scp-mcp-server stdio` OR direct Python entry-point importing `consult_rules_impl`) | (inherits D-054 pattern) |
| 026C | ACC-side RI canary wiring: verify `tool_scp_consult_rules` returns useful output from `scp-cli consult --domain X` | ACC-side PR (no SCP-side decision) |
| 026D | Narrative reconciliation: OVERVIEW.md §1.4 + §3.4 + mcp-adopter-contract.md amended to reflect actually-shipped capabilities. Retracted claims move to §6.3 future-scope with a named WP-SCP-027 forward link | D-055 (narrative-retraction contract) |
| 026E | ADOPT-001 §12.7.17 (or new §13) MCP integration runbook — adopter `.mcp.json` registration shape; canonical first-consumer pattern; no receipt-validation if Shape C (deferred) | (inherits D-054 pattern) |
| 026F | Threshold + USER-GATE-G observation: ≥1 real `consult_rules` call in a real session; ≥1 agent-authored output references a returned rule | D-056 (Threshold criteria) |

## 6. Decisions reserved

- **D-054** — WP-SCP-026 Shape choice (A / B / C) + ratification contract. Filed inline with this plan-doc on kickoff (post-operator-ratification).
- **D-055** — Narrative retraction contract (Shape C path only). Specifies which OVERVIEW.md / mcp-adopter-contract.md / ADOPT-001 sections are factually-current-true vs aspirational/deferred. Mandates a forward link to WP-SCP-027 (the named successor for HTTP transport + signed receipts).
- **D-056** — WP-SCP-026 Threshold criteria + decision on whether to advance to WP-SCP-027 (receipt signing + HTTP transport) or hold indefinitely.

## 7. Forward-looking — what becomes WP-SCP-027+

If Shape C ratified + receipt-signing narrative deferred:
- **WP-SCP-027 (HTTP transport + signed receipts):** the deferred capability. Multi-week build. Triggered by an operator-attended demand signal — adopter or ACC team explicitly asks for receipt verification or HTTP-served consult.
- **WP-SCP-028 (cohort MCP cascade):** push `.mcp.json` registration to 5 cohort adopters alongside their wrapper installation. Same shape as WP-SCP-024 024D/E/F/G cascade slices.
- **WP-SCP-029 (PreCommit-receipt-validator):** adopter-side hook validating receipt signature + expires_at + head_sha + changed_files_hash. Requires WP-SCP-027 to ship first.

If Shape B ratified (build the narrative): WP-SCP-027/028/029 collapse into WP-SCP-026's scope.

## 8. Risks

1. **`scp-cli` shape decision (Shape A/C kickoff dependency).** Three options per the research:
   - (i) Implement `scp-cli` as a thin wrapper subprocessing `scp-mcp-server` and translating to/from MCP JSON-RPC. Preserves MCP transport.
   - (ii) Implement `scp-cli` as a Python entry-point that imports `consult_rules_impl` directly. Bypasses MCP layer entirely (fastest; undermines "MCP server is the consult surface" narrative).
   - (iii) Re-spec PLAN-EST-P so per-repo MCP servers talk MCP-to-MCP to SCP. Closest to the OVERVIEW.md ideal but requires PLAN-EST-P amendment.
   Decision: at kickoff via §10 Q2.
2. **The first consumer might not stick.** Even with a working scp-cli, the RI canary may not be a real-usage path — ACC EST-P is in flight (WS-EST-P-2 not yet shipped). Risk that we ship a `scp-cli` that nobody calls in production. Mitigation: Shape C anti-criterion explicitly catches this.
3. **Narrative retraction has political cost.** Walking back published docs that describe receipt-signing as a capability looks like a step backwards. Mitigation: D-055 frames it as "rescheduling, not deletion" — the capability moves to WP-SCP-027 with a clear trigger (operator-attended demand signal).
4. **Doc-vs-code drift continues post-WP-SCP-026.** If we land Shape C and the docs are accurate today, but new features ship without doc updates, the divergence re-opens. Mitigation: add a §6.x doc-discipline-maintenance entry to WP-SCP-026 closure that names a quarterly review checkpoint.

## 9. Anti-scope (what WP-SCP-026 is NOT)

- NOT a re-implementation of the MCP server from scratch. The existing 8 tools + 11 resources + stdio transport are kept.
- NOT a rewrite of ACC's PLAN-EST-P. WP-SCP-026 lives within ACC's existing per-repo-MCP-server design (Shape A/C path) or escalates to PLAN-EST-P amendment (Shape A option iii) only with operator-attended ratification.
- NOT a security-hardening exercise (Shape A/C path). The receipt-signing decision IS the security-hardening question; this WP picks the answer or defers it.

## 10. Open questions for the operator at WP-SCP-026 kickoff

1. **Is the receipt-signed-consult narrative load-bearing or aspirational?** OVERVIEW.md §3.4 + mcp-adopter-contract.md §"Receipt verification" describe a working pipeline that doesn't exist in code. Answers:
   - (a) "Build it as part of WP-SCP-026" (Shape B path)
   - (b) "Retract from docs; reschedule to WP-SCP-027+" (Shape C path)
   - (c) "Narrative was always future-scope; clarify in OVERVIEW.md §6.3" (Shape C narrower path)
2. **`scp-cli` shape — ship it or pivot?** Three options per §8 risk 1. Default: (i) thin wrapper preserves MCP narrative.
3. **First consumer: SCP-self, FLA, ACC, or PIM?**
   - SCP-self: lowest-risk (no cross-repo auth). The operator's own Claude Code session calls `consult_rules` while authoring a rule.
   - FLA: already has a pre-commit framework; shortest path to receipt-validator if Shape B ratified.
   - ACC: the load-bearing "credibility signal" per WP-SCP-025 plan-doc §8. Default for Shape A/C.
   - PIM: only LIVE cohort adopter (cascade slice 024C closed 2026-05-24); piggy-backs on existing wrapper-installation discipline.
4. **HTTP transport — needed in v1?** No current consumer pathway requires HTTP. Is HTTP a doc-retraction item or a v1 deliverable? If retracted, the `acc.brokapps.ai` hosting story (OVERVIEW.md §2.2) needs amendment too.
5. **Adopter PreCommit-receipt-validator: required for first consumer, or deferred?** Bounded by Q1's answer.

---

**Status:** ACTIVE v1.0 — Shape C ratified 2026-05-25. Slice plan §5 LOCKED. Next action: 026A kickoff slice opens for D-054 ADR authoring; subsequent slices 026B (scp-cli shim) + 026C (RI canary wiring) + 026D (narrative reconciliation) + 026E (ADOPT-001 §12.7.17) + 026F (Threshold + USER-GATE-G observation) sequence per §5 dependencies.
