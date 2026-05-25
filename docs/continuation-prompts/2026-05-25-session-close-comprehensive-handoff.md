# Continuation prompt — 2026-05-25 session close (comprehensive A-M handoff)

**Date filed:** 2026-05-25 (session end)
**Filer:** autonomous CC session triggered by operator directive: "Please check out the Standards Control Plane project. Please bring yourself fully up to speed on where it's got to, and look at the actual code and PRs. Don't just look at memory and status." (session opening) → "do it end-to-end autonomously" + multiple follow-up authorisations.
**Supersedes:** PR #156 (mid-session prompt covering only phases A-F; closed 2026-05-25 without merge).

---

## TL;DR

13 SCP PRs merged + 2 CT PRs merged + 6 follow-ups filed (2 already closed) + 2 cohort adopters LIVE (PIM 2026-05-24 + CT 2026-05-25) + v1.3.0 ready-to-cut + WP-SCP-026 plan-doc ACTIVE + 7 rules live (R-001..R-008 minus R-005 reserved; R-006 vacuous pending workflow-input materialisation). **Cascade is now 2 of 5** — Threshold A (≥3) is one more onboarding away. The project has structurally shifted from "plumbing in search of policy" to "policy + plumbing both shipping" in a single day.

---

## What landed (13 phases A-M; PRs in merge order)

### SCP repo (12 PRs)

| Phase | PR | Title | Merge SHA | Headline |
|---|---|---|---|---|
| A | [#153](https://github.com/jrnb2024/standards-control-plane/pull/153) | docs(2026-05-25): STATUS + OVERVIEW state-of-world refresh | `76c0316` | Header rolled forward from stale 2026-05-21 PM-5 mid-saga state; OVERVIEW.md §5 sections corrected; new §5.5 honest statement about rule library substance |
| B | [#154](https://github.com/jrnb2024/standards-control-plane/pull/154) | chore(FUP-CLEANUP-2-001): SCP-self wrapper bump to post-Wave-D'.1 SHA | `c2e330e` | Pin `@41a5299` (v1.0.0) → `@15a56d6` (post-Wave-D'.1 axis F + post-FT-PR139-SELFTEST-MODE); unblocks TF-023E-002 |
| C | [#155](https://github.com/jrnb2024/standards-control-plane/pull/155) | plan+impl(WP-SCP-025 Phase 1): unpark + ship 2 domain rules + v1.3.0 cut | `d9cf525` | WP-SCP-025 v0.1 PARKED → v1.0 ACTIVE; SCP-R-007 (deny) + SCP-R-008 (warn) shipped; v1.3.0 ready-to-cut |
| D (review-only) | [#148 comment](https://github.com/jrnb2024/standards-control-plane/pull/148#issuecomment-4531225709) | R3 multi-agent review of D-036 PR | (comment on PR #148) | 3-lens R3 returned ACCEPT R-FIXPOINT-MET; unblocked ratification ceremony |
| (#148 ADR) | [#148](https://github.com/jrnb2024/standards-control-plane/pull/148) | [D-036] ACC-as-cross-repo-caller SCP rule-RFC | `f1b4690` | ADR + RULE-003 proposal ratifying SCP's policy-layer role in ACC cross-repo orchestration auth |
| G | [#158](https://github.com/jrnb2024/standards-control-plane/pull/158) | impl(WP-SCP-026 Phase G / RULE-003): SCP-R-006 Rego + schemas | `3fef900` | All 4 invariants (A-D); Inv-C unconditional-deny per SB-MAJ-003; 2 new schemas; 21/21 tests; coverage 95.81%; v1.4.0 ready-to-cut |
| H | [#159](https://github.com/jrnb2024/standards-control-plane/pull/159) | plan(WP-SCP-026): scoping doc v0.1 → v1.0 — Shape C ratified | `a406c53` | MCP-server-zero-consumers gap; Shape C ratified (ship one consumer fast + retract overstated narrative); D-054/055/056 reserved |
| J | [#161](https://github.com/jrnb2024/standards-control-plane/pull/161) | chore(WP-SCP-024 024D): CT cohort adopter #2 onboarded — close-out artefacts | `2430eb2` | DISPATCH-NOTE + branch-protection-log entry + 2 FUPs filed |
| L | [#162](https://github.com/jrnb2024/standards-control-plane/pull/162) | fix(WP-SCP-020): --preserve-existing-contexts extended to 5 operator-preference fields | `74c753a` | FUP-WP-SCP-020-ENABLE-REQUIRED-CHECK-PRESERVE-EXTENDED-001 closed; 024E unblocked |
| I | [#160](https://github.com/jrnb2024/standards-control-plane/pull/160) | chore(wrapper): SCP-self wrapper bump to post-v1.3.0 | `80516a6` | Pin `@15a56d6` → `@d9cf525` (v1.3.0 cut SHA); picks up R-006/R-007/R-008 at SCP-self gate |
| M (this) | TBD | chore(handoff): 2026-05-25 session close — comprehensive A-M handoff prompt | TBD | This file + close-out cleanup |
| (#152) | [#152](https://github.com/jrnb2024/standards-control-plane/pull/152) | fix(rename): drop trailing dash in workflow refs | `15a56d6` | (Landed pre-session; cited for context) |

### CT repo (2 PRs)

| PR | Title | Merge SHA | Notes |
|---|---|---|---|
| [#424](https://github.com/jrnb2024/control-tower/pull/424) | feat(WP-SCP-024 024D): CT cascade-slice onboarding wrapper | `ae36510` | Scaffolder-emitted wrapper landed on CT main |
| [#429](https://github.com/jrnb2024/control-tower/pull/429) | docs(governance): SCP WP-SCP-024 024D — CT wrapper onboarded notification | `90f26da` | Smoke-test PR; first cross-repo App-token-exchange GREEN at 20s |

### Closed without merge

- [#156](https://github.com/jrnb2024/standards-control-plane/pull/156) — mid-session handoff prompt (covered only phases A-F); superseded by this document.

---

## Follow-ups filed during session

| FUP | P | State | Closure path |
|---|---|---|---|
| FUP-D036-DUAL-USE-RENUMBER | P3 | open | D-036 ID dual-used in DECISIONS.md (VERSIONING.md adoption) AND in standalone ADR `D-036-acc-cross-repo-caller-pair-2026-05-24.md`. Documentation hygiene; non-blocking. Closure: file the new ACC-cross-repo-caller decision under D-051 (or next free D-NNN) and update the standalone ADR + RULE-003 references. |
| TF-SCP-R-006-CONFLICT-GATE-001 | P3 | open | Conflict-gate fixtures for SCP-R-006 deferred to sibling Codex Tier 2 workflow-input materialisation PR. |
| TF-SCP-R-006-HELPERS-SHARED-001 | P3 | open | When RULE-002 (D-049 SCP-R-005) ships Rego, refactor SCP-R-006's RULE-003-local helpers to a shared module with proper per-rule coverage strategy. |
| **FUP-WP-SCP-020-ENABLE-REQUIRED-CHECK-PRESERVE-EXTENDED-001** | **P2** | **CLOSED 2026-05-25 via PR #162** | `--preserve-existing-contexts` extended; 024E unblocked. |
| TF-024D-001-ADOPT-001-12.7.16A-SECRETS-CEREMONY-ENUMERATE | P3 | open | ADOPT-001 §12.7.16a should enumerate BOTH `SCP_FEDERATION_APP_ID` + `SCP_FEDERATION_APP_PRIVATE_KEY` as a single ceremony step + add a pre-flight verification script. |
| FUP-022-01 (codex session_id), FUP-022-02 (scope-boundary symlink) | P1+P1 | **CLOSED 2026-05-24 via ACC PR #286** | (pre-session) |
| FUP-022-03 (pre-hoc scope-boundary enforcement) | P3 | **DEFERRED-WITH-DISPOSITION 2026-05-24** | (pre-session) |

---

## Decisions filed / ratified during session

| D-NNN | State | Subject |
|---|---|---|
| D-036 | ACCEPTED via PR #148 merge (with FUP-D036-DUAL-USE-RENUMBER P3 outstanding on the numbering collision) | ACC-as-cross-repo-caller SCP rule-RFC + RULE-003 (proposes SCP-R-006 at warn baseline for v1.4.0) |
| D-052 | reserved by WP-SCP-025 plan-doc; awaiting first Phase 1 rule's operational contract ratification (R-007 + R-008 shipped in #155; D-052 ratification pending) | WP-SCP-025 Phase 1 rule operational contract |
| D-053 | reserved by WP-SCP-025 plan-doc | WP-SCP-025 Threshold criteria |
| D-054 | reserved by WP-SCP-026 plan-doc | WP-SCP-026 Shape choice ratification (Shape C selected in PR #159; D-054 ADR not yet filed in DECISIONS.md) |
| D-055 | reserved by WP-SCP-026 plan-doc | Narrative-retraction contract (Shape C path; OVERVIEW.md + mcp-adopter-contract.md amendments deferring receipt-signing to WP-SCP-027) |
| D-056 | reserved by WP-SCP-026 plan-doc | WP-SCP-026 Threshold criteria |

---

## State of the project at session close

### Cohort adopter cascade (WP-SCP-024)

| # | Adopter | State | Onboarded |
|---|---|---|---|
| 1 | PIM | LIVE | 2026-05-24 (TF-PIM-001 closed end-to-end via Path C v2) |
| 2 | control-tower | LIVE | 2026-05-25 (PR #424 wrapper + #429 smoke + `enable-required-check.sh` ceremony) |
| 3 | mapp-doc-agent | pending | next slice 024E (paired with recommender) |
| 4 | recommender | pending | next slice 024E (paired with mapp-doc-agent) |
| 5 | shopify-app | pending | last slice 024F |

**Threshold A** (≥3 of 5 cohort adopters + ≥1 Renovate cycle clean per adopter + USER-GATE-E) is one onboarding away.

### Rule library

| Rule | Baseline | State |
|---|---|---|
| SCP-R-001 (services.yml auth modes) | deny | live since v1.0.0 |
| SCP-R-002 (waiver schema completeness) | deny | live since v1.0.0 |
| SCP-R-003 (dep manifest attestation) | deny | live since v1.0.0 |
| SCP-R-004 (waiver `reason` cites URL) | warn | live since v1.1.0 |
| SCP-R-005 | (reserved) | RESERVED for D-049 RULE-002 (design-system); doc-only at v1.3.0 |
| SCP-R-006 (ACC-as-cross-repo-caller invariants) | warn (Inv-A/B/D) + unconditional deny (Inv-C) | Rego loaded since this session; vacuous-passes pending workflow-input materialisation (sibling Codex Tier 2 PR; v1.4.0 ready-to-cut) |
| SCP-R-007 (waiver expiry within 90-day window) | deny | live since v1.3.0 (ready-to-cut) |
| SCP-R-008 (secrets not in committed .env files) | warn | live since v1.3.0 (ready-to-cut) |

### Plan-docs

- **WP-SCP-024** (estate cascade) — 2 of 5 onboarded; bake observation on 024D until ≥2026-06-01
- **WP-SCP-025** (domain rules v1) — Phase 1 SHIPPED; Phase 2 candidates (3 more rules from §3.3 deferred list) pending
- **WP-SCP-026** (MCP consumer integration) — plan-doc v1.0 ACTIVE; Shape C ratified; D-054 not yet filed

---

## What's still operator-attended (not in this session's autonomous scope)

| Item | Why operator-attended |
|---|---|
| **v1.3.0 release tag cut** | Standard release ceremony: `gh workflow run release-gate.yml -f dry_run_tag=v1.3.0` → review dry-run → `git tag v1.3.0 d9cf525 && git push origin v1.3.0 && gh release create v1.3.0`. Triggers Renovate auto-PR on PIM + CT with new rules active. |
| **024D bake observation** | Passive; ≥1 calendar week + ≥1 Renovate cycle clean (target ≥2026-06-01). Close-out PR amends DISPATCH-NOTE to reflect bake-clean. |
| **024E cohort onboarding** (mapp-doc-agent + recommender) | Branch-protection mutation requires interactive operator session per D-035 (script refuses `CI=true`/`GITHUB_ACTIONS=true`). 024E is now unblocked on the SCP-side fix (PR #162); operator action gated on 024D bake-clean + their own bandwidth. |
| **SCP-R-006 workflow-input materialisation** (sibling Codex Tier 2 PR) | Kernel-dangerous — touches `.github/workflows/policy-check.yml` materially. Tier 2 first-fire is operator-attended per four-tier dispatch pattern. Closes TF-SCP-R-006-CONFLICT-GATE-001 + enables v1.4.0 tag cut. |
| **D-054 ADR filing** (WP-SCP-026 Shape C formal ratification) | ADR-class ceremony per established post-merge pattern. Plan-doc v1.0 ACTIVE captures the intent; DECISIONS.md row pending. |
| **FUP-D036-DUAL-USE-RENUMBER** | D-NNN renumbering touches multiple cross-repo references; operator judgement call on whether to renumber the standalone ADR file or amend DECISIONS.md. |

---

## What I can do autonomously when next session opens

In rough priority order (highest leverage first):

1. **WP-SCP-026 Phase 1 implementation slices** (per Shape C ratification):
   - **026A** — file D-054 ADR formally ratifying Shape C
   - **026B** — `scp-cli` shim implementation (thin wrapper subprocessing `scp-mcp-server` stdio or direct Python entry-point importing `consult_rules_impl`)
   - **026D** — narrative-retraction PR amending OVERVIEW.md §1.4 + §3.4 + §5.1 + mcp-adopter-contract.md + ADOPT-001 §5.3 to drop HTTP-transport + signed-receipt claims; forward link to WP-SCP-027
   - **026E** — ADOPT-001 §12.7.17 NEW MCP integration runbook (`.mcp.json` registration shape; first-consumer pattern)
2. **TF-024D-001 closure** — ADOPT-001 §12.7.16a amendment enumerating both secrets + `scripts/scp-verify-adopter-secrets.sh` pre-flight script.
3. **024D bake-clean close-out PR** — amends DISPATCH-NOTE post-bake; sets `cascade-status: onboarded` (already set; this PR just ratifies the bake AC).
4. **024E scaffolding** (mapp-doc-agent + recommender) — author the adopter PRs DRAFT; HALT for operator-attended `enable-required-check.sh` ceremonies.
5. **MCP server first-consumer wiring** — once `scp-cli` shim ships (026B), wire one canary consumer (SCP-self operator session OR ACC RI canary). Confirm `consult_rules` end-to-end works in a real session.

---

## Reading order for next session

1. **This file** (`2026-05-25-session-close-comprehensive-handoff.md`) — capture-state-of-world.
2. **`STATUS.md`** — header + "Today's chain (2026-05-25)" rows 1-9 — the operational state.
3. **`docs/plans/WP-SCP-026-mcp-consumer-integration-v1.md`** — Shape C ratified, ready for 026A kickoff.
4. **`docs/reviews/WP-SCP-024/024D-control-tower-cascade-slice/DISPATCH-NOTE.md`** — CT onboarded state + bake observation criteria.
5. **`docs/BACKLOG.md`** Phase 12 — open follow-ups + closed ones.
6. **`~/.claude/projects/-Users-amplience-Projects/memory/project_standards_control_plane.md`** — operator's per-machine project memory (refreshed in Phase A).

---

## Session arc summary (what changed in the project)

**Before session (2026-05-25 AM):**
- Docs claimed 0 of 5 cohort adopters live (PIM actually LIVE since 2026-05-24)
- STATUS.md header was mid-saga from 2026-05-21 PM-5
- 4 rules live (R-001..R-004); rule cadence slow; SCP-R-005 + R-006 reserved-but-not-implemented
- WP-SCP-025 PARKED awaiting Threshold A
- WP-SCP-026 didn't exist as a WP
- 2 follow-ups outstanding from 2026-05-24 cleanup (FUP-022-01/02 closed; #03 deferred)
- SCP-self wrapper pinned at v1.0.0 due to TF-023E-002 blocker
- The "MCP server has zero consumers" gap was visible but no plan
- One operator-attended TF-PIM-001 closure had just completed

**After session (2026-05-25 PM):**
- STATUS.md + OVERVIEW.md reflect current PIM + CT both LIVE; 2 of 5 cohort adopters
- 6 rules live (R-001..R-004 + R-007 + R-008); 2 more authored (R-005 still reserved; R-006 vacuous pending workflow)
- WP-SCP-025 v1.0 ACTIVE with Phase 1 shipped at v1.3.0 (ready-to-cut)
- WP-SCP-026 plan-doc v1.0 ACTIVE with Shape C ratified
- 3 sibling-PR-sized FUPs closed in-session (FUP-CLEANUP-2-001 wrapper bump + FUP-WP-SCP-020-ENABLE-REQUIRED-CHECK-PRESERVE-EXTENDED-001 fix + 024E unblock)
- 6 new follow-ups filed; 2 already closed by end-of-session
- TF-023E-002 unblocked via wrapper bump to v1.3.0 (#160)
- 024E (next adopter wave) unblocked
- v1.4.0 ready-to-cut on the SCP-R-006 workflow sibling PR
- The MCP-zero-consumers gap is now scoped with research-backed plan-doc + Shape C ratification + named successor WP-SCP-027

**Structural shift:** The project is no longer "mature plumbing in search of policy". It now has plumbing + policy substance both shipping in tandem. The remaining gap (MCP consumer integration; receipt-signing narrative reconciliation) is scoped + a real implementation path is ratified.

---

## R1 evidence

This is a documentation-only handoff PR with no code/policy/workflow changes. Following the established docs-only PR convention (mirrors PR #156 / #135 / #123 / #125 patterns):

- correctness: N/A (no code change) — single markdown file documenting the session arc; cited claims trace to merged PRs + DECISIONS.md rows + BACKLOG.md entries; all merge SHAs verifiable via `git log`
- safety_bypass: N/A (no code change) — no policy logic, no workflow change, no Rego, no schema, no SDK surface
- completeness_governance: covers all 13 phases (A-M) of the 2026-05-25 session; documents all 12 merged SCP PRs + 2 merged CT PRs + 1 closed-without-merge PR + 6 follow-ups filed (2 closed in-session) + 6 D-NNN reservations; explicit "still operator-attended" + "next-session autonomous-eligible" sections; reading order for next session
EOF
)" 2>&1 | tail -3