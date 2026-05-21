# Continuation prompt — 6 D-035 SCP rules retired + WP-SCP-025 parked (2026-05-09)

**Date:** 2026-05-09
**Decision lineage doc.** Filed standalone for in-repo decision lineage so future readers can answer "why was the 6-rules-by-2026-05-15 deadline retired?" from in-repo sources alone.

---

## Operator decision (locked 2026-05-09)

The 6 D-035-aligned SCP rules previously framed as gating CT Wave 1 entry on 2026-05-15 are **RETIRED under that deadline**. This is not a decision to never ship them — it's a decision to not force them through under deadline pressure.

The 6 retired rule names (preserved for traceability):

1. `sdk_version_pin` — was Wave 1 gate
2. `ct_sdk_conformance` — was Wave 1 gate
3. `sdk_migration_waiver` — was Wave 1 gate
4. `sdk_adoption_schedule` — was Wave 1 mid
5. `bff_refresh_hardening` — was Wave 2 gate
6. `ct_auth_provider_memoization` — was Wave 3 gate

## Why retire under deadline

1. **CT D-035 Phase 5 already shipped 2026-05-07 without these rules as preconditions.** Phase 5 (estate adoption) is in flight using CT's own conformance machinery (`.github/workflows/ct-sdk-conformance.yml` + `sdk-pins.json` + `scripts/conformance/abuse-monitor.py`), not SCP rule gates. SCP was not the load-bearing gate.

2. **WP-SCP-024 cascade is operator-decided FLA-INDEPENDENT** per 2026-05-03 (plan-doc §2 invariants row 4). FLA's pilot stability is on its own track; the non-FLA cohort proceeds in parallel and does not depend on the 6 rules.

3. **None of the 6 rules had been drafted with 6 days remaining.** Forcing 6 Rego rules + conftest fixtures + 3-lens R1 review through in 6 days while WP-SCP-024 slice 024B (the actual cascade gate per plan-doc §6) was the immediate work would have diluted both deliverables.

4. **The deadline wasn't load-bearing.** The 2026-05-15 framing came from cross-project coordination expectations that were already moot by Phase 5's 2026-05-07 ship.

## Strategic reframe (load-bearing for the retirement decision)

SCP's near-term credibility depends on shipping 2-3 high-value domain rules that catch things review misses + measurable adopter consumption (≥3 cohort adopters running ≥2 SCP-R-005+ rules with ≥80% pass rate over ≥4-week observation window), not on forcing SDK-discipline rules through under deadline pressure.

The federation primitive + MCP server + cohort cascade are real engineering and have value, but **they do not, on their own, justify SCP as a project.** SCP's credibility depends on shipping real domain rules that catch things review would miss, used by adopters who'd otherwise be in trouble.

## What the retirement is conditional on

The retirement is conditional on a **strategic reframe**: a properly-chosen first batch of 2-3 high-value domain rules under WP-SCP-025 (parked plan-doc filed at `docs/plans/WP-SCP-025-domain-rules-v1.md`).

WP-SCP-025 success criterion (≥4-week observation window from rule ratification):
- ≥3 cohort adopters running ≥2 SCP-R-005+ rules.
- Green pass rate ≥80% across all adopter PRs (rule produces signal, not noise).
- ≥1 rule-driven PR rejection or waiver-filing event captured a real bug or unsafe pattern that would otherwise have shipped.

WP-SCP-025 anti-criterion (treat as failed and re-scope if any of these hold at the 4-week mark):
- Zero `scp.consult_rules` MCP calls from ACC's planning phase.
- Zero rule waivers filed across the cohort.
- Zero rule-driven PR rejections.
- Adopters file a TF asking for rules to be reverted or watered down.

## Candidate domain rules (operator selects 2-3 at WP-SCP-025 kickoff)

Starting list, not a commitment. Each catches a specific failure pattern that has actually happened (or has high probability) across the estate:

| Candidate | Catches | Source/precedent |
|---|---|---|
| `protected_tables_updated_with_migration` | Alembic migrations touching persistent-state tables without updating CT's `PROTECTED_TABLES` | D-022 / WP-SCC-7 silent-data-loss risk |
| `r1_evidence_linked_in_pr_body` | PRs merging without 3-lens R1 evidence link | WP-D035-615 cardinal-rule-2 incident retro 2026-05-02 |
| `waiver_expiry_within_window` | Waivers with `expires_at` more than 30 days out, none, or stale | Auth-bypass-by-stale-waiver pattern |
| `secrets_not_in_committed_env_files` | `.env`/`.env.docker` containing actual creds (not `.env.example`) | Standard secret-leakage; multiple near-misses |
| `permission_schema_registered_within_wave_window` | Apps that adopt CT but never register `permission_schemas` row within N days | Closes dual-gate problem (Recommender J1, PIM auth-foundation, expected VS Phase N) |

**Why these and not the original 6:** all five target safety boundaries humans get wrong with high consequence. The original 6 targeted SDK pin discipline, which CT's own conformance machinery already covers and which has lower failure-cost.

## Cross-project reconciliation

SCP filed `SCP-D035-RULES-RETIRED-2026-05-09.md` to CT governance notifications log requesting CT amendments to:

- `docs/briefings/recommender-shopify-j1-rbac-response-2026-05-09.md` Q6+Q8 — drop the 6-rules / 2026-05-15-deadline framing before the response ships.
- `docs/plans/PLAN-CT-D-rollout.md` §3 WP-D-SCP entry — point at WP-SCP-025 backlog or drop the section.

CT acknowledged the retirement in a sibling notification (commit `<TBD-CT-SHA>`) closing the cross-project loop.

## What this does NOT change

- **WP-SCP-024 cascade plan unchanged.** Slice 024B (later split into 024B-core + 024B-extras per 2026-05-09 split) is the immediate SCP work; PIM canary (024C) follows once both halves merge.
- **MCP integration story unchanged.** ACC remains the first planned `scp.consult_rules` consumer (~3-day spike per ACC's 2026-05-09 continuation prompt).
- **D-021 May-31 atomic-workday commitment unchanged.** Pre-staged at SCP `docs/reviews/WP-SCP-019/d019-may31-checkpoint.md`. Independent of WP-SCP-025.

## Relationship to the 024B split (2026-05-09 PM)

The 6-rules retirement and the 024B split are separate decisions made on the same day:

- **6-rules retirement (AM):** scope re-scoping decision driven by external deadline + strategic reframe.
- **024B split (PM):** scope re-scoping decision driven by adversarial-review trajectory (R6→R7→R8 trajectory: each fix-round +3-4 net MAJ closure but +2-3 new defects in just-added code = surface-area-too-large). Documented at `docs/reviews/WP-SCP-024/024B-core/SCOPE-CORRECTION-2026-05-09.md`.

Both decisions follow the same principle: **incremental delivery, not descope.** The 6 rules ship under WP-SCP-025 (parked, post-024 Threshold A). 024B ships as core + extras. Nothing dropped on the floor.

## Reference

- `docs/plans/WP-SCP-025-domain-rules-v1.md` (parked plan-doc; merged at PR #105 / commit `04135f0`)
- `docs/reviews/WP-SCP-024/024B-core/SCOPE-CORRECTION-2026-05-09.md` (024B split decision)
- `STATUS.md` "Today's chain (2026-05-09)" entry (retirement) + "Today's chain (2026-05-09 PM)" entry (split)
- `~/Projects/control-tower/governance/docs/notifications/SCP-D035-RULES-RETIRED-2026-05-09.md` (outbound notification)
- `~/Projects/control-tower/governance/docs/notifications/<CT-ack-filename>` (inbound ack — filename TBD when CT files)

---

**Status:** continuation-prompt artefact. Files standalone PR. Single-file. Self-merge per D-040.
