# ProgrammePlan — WP-SCP-025 Domain Rules v1

**Work Package:** `WP-SCP-025`
**Version:** 0.1 (PARKED)
**Status:** PARKED — ready to start after WP-SCP-024 reaches Threshold A. Not in flight.
**Date parked:** 2026-05-09
**Owner:** TBD (named at kickoff; likely SCP team member; co-ownership with a CT engineer is acceptable given auth-domain overlap)
**Predecessors:**
- WP-SCP-024 (Estate Cascade) at Threshold A — required (≥3 cohort adopters onboarded + ≥1 Renovate cycle clean per adopter + USER-GATE-E signed).
- WP-SCP-021 (MCP Server) — landed; receipts + `scp.consult_rules` available.

## 1. Purpose

WP-SCP-020 + WP-SCP-021 + WP-SCP-023 + WP-SCP-024 give SCP per-PR authority + pre-code consultability + estate-wide observability + cohort-cascaded enforcement. **They do not, on their own, justify SCP as a project.** SCP's near-term credibility depends on shipping real domain rules that catch things human review misses, used by adopters who'd otherwise be in trouble.

WP-SCP-025 is the first batch of post-infrastructure domain rules. It exists to test the proposition that SCP's policy authority is load-bearing — not just that its CI plumbing works.

## 2. Goal + success criterion

**Goal:** ship 2-3 high-value domain rules (SCP-R-005..007) that catch specific failure patterns adopters cannot reliably catch with review alone, adopted by ≥3 cohort repos under the WP-SCP-024 federation primitive.

**Success criterion (≥4-week observation window from rule ratification):**
- ≥3 cohort adopters running ≥2 SCP-R-005+ rules.
- Green pass rate ≥80% across all adopter PRs (rule produces signal, not noise).
- ≥1 rule-driven PR rejection or waiver-filing event captured a real bug or unsafe pattern that would otherwise have shipped.

**Anti-criterion (treat as failed and re-scope if any of these hold at the 4-week mark):**
- Zero `scp.consult_rules` MCP calls from ACC's planning phase (per WP-SCP-026 ACC-MCP integration).
- Zero rule waivers filed across the cohort (suggests the rules don't fire, i.e. they're testing for nothing real).
- Zero rule-driven PR rejections (suggests the rules are advisory-only in practice, not load-bearing).
- Adopters file a TF asking for the rules to be reverted or watered down.

## 3. Candidate rules (operator selects 2-3 at WP-SCP-025 kickoff)

This is a **starting list, not a commitment.** Each candidate would catch a specific failure pattern that has actually happened (or has high probability of happening) across the estate. The operator picks 2-3 at scoping time, or proposes alternatives.

| Candidate | Catches | Source / precedent | Estimated complexity |
|---|---|---|---|
| `protected_tables_updated_with_migration` | Alembic migrations touching persistent-state tables without updating CT's `PROTECTED_TABLES` list | D-022 / WP-SCC-7 — silent data-loss risk; current enforcement is hand-rolled in `scripts/check-migration-safety.py` | MED — needs migration-file parsing + cross-reference into CT-side `PROTECTED_TABLES` constant |
| `r1_evidence_linked_in_pr_body` | PRs merging without 3-lens R1 evidence link in PR body | WP-D035-615 incident retro 2026-05-02 (cardinal-rule-2 violation that drove CT's `.github/workflows/r1-evidence-check.yml`) | LOW — text-search PR body for `R1 evidence:` anchor; mirrors CT's existing CI gate |
| `waiver_expiry_within_window` | Waivers with `expires_at > today + 30d`, or no expiry, or stale (`expires_at < today`) | Auth-bypass-by-stale-waiver pattern; SCP-R-002 already validates schema, this validates semantics | LOW — extends SCP-R-002 with date arithmetic on `expires_at` |
| `secrets_not_in_committed_env_files` | `.env` / `.env.docker` files containing actual credentials (not `.env.example`) | Standard secret-leakage pattern; multiple near-misses across the estate | MED — entropy + key-shape heuristics; risk of false positives |
| `permission_schema_registered_within_wave_window` | Apps that adopt CT but never register their `permission_schemas` row within N days of wave entry | Closes the dual-gate problem (Recommender J1, PIM auth-foundation, expected VS Phase N all hit it) | HIGH — needs CT-side state read (live `permission_schemas` table); cross-repo coupling |

**Why these and not the original 6 D-035-aligned rules:** all five candidates target safety boundaries humans get wrong with high consequence. The original 6 (`sdk_version_pin`, `ct_sdk_conformance`, `sdk_migration_waiver`, `sdk_adoption_schedule`, `bff_refresh_hardening`, `ct_auth_provider_memoization`) targeted SDK pin discipline, which CT's own conformance machinery (`ct-sdk-conformance.yml` + `sdk-pins.json` + `scripts/conformance/abuse-monitor.py` per PLAN-CT-D-rollout §3) already covers and which has lower failure-cost.

## 4. Anti-scope (what WP-SCP-025 is NOT)

- NOT a re-litigation of the 6 retired rules. Those are off the table for v1; if revived, must be re-scoped against the success/anti-criteria above and the cohort consumption signal.
- NOT a vendor-SLA cascade.
- NOT a rule-for-the-sake-of-rules exercise. Each rule must name the specific failure pattern it catches AND the precedent (incident, near-miss, audit finding).
- NOT estate-wide enforcement on all 5+ cohort adopters from day 1. Advisory → warn → required ramp per `policies/VERSIONING.md` D-036 deprecation contract.

## 5. Process protocol

WP-SCP-025 follows the four-tier dispatch protocol per `feedback_four_tier_dispatch.md`:

- **Plan-doc kickoff slice (025A):** Opus orchestrator drafts; 3× parallel Sonnet R1; R2 fixpoint required.
- **Per-rule slices (025B / 025C / 025D — one per rule):** RFC-lite proposal at `docs/reviews/rule-proposals/RULE-NNN.md` per D-036 (48h wall-clock; quorum=1 in single-operator mode); Rego authoring at `policies/SCP-R-NNN.rego`; per-rule OPA coverage ≥90%; conftest test fixtures matching SCP-R-004 pattern (≥21 cases bar). Codex executor for Rego; 3-lens parallel Sonnet R1 review.
- **Cohort adoption slices (025E / 025F / 025G):** one per onboarded adopter; cascade-status declaration + invocation-log + post-bake observation per WP-SCP-024 plan-doc invariant pattern.
- **Closure slice (025H):** USER-GATE-F if Threshold succeeds; re-scope plan-doc if anti-criteria fire.

## 6. Slice plan (placeholder — finalised at kickoff)

| Slice | Deliverable | Decision filed |
|---|---|---|
| 025A (this) | Plan-doc v1.0 | (none — kickoff slice) |
| 025B | First rule (operator-selected from §3) | D-050 |
| 025C | Second rule (operator-selected from §3) | (inherits D-050 pattern) |
| 025D | Third rule (operator-selected from §3, optional) | (inherits D-050 pattern) |
| 025E-G | Per-adopter cascade extensions for the new rules | (inherits D-045 pattern from WP-SCP-024) |
| 025H | Threshold metric + USER-GATE-F | D-051 |

## 7. Decisions reserved

- **D-050** — first-batch rule operational contract (lifecycle: advisory → warn → required ramp per VERSIONING.md; cohort onboarding cadence; waiver shape).
- **D-051** — WP-SCP-025 Threshold criteria + post-Threshold maintenance posture + decision on whether to graduate to a second batch (WP-SCP-026 for ACC-MCP-integration-driven rules; or WP-SCP-027 for cohort-broadening).

## 8. Forward-looking

- **ACC MCP integration (~WP-SCP-026):** the load-bearing credibility signal. ACC is the first planned MCP consumer (~3-day spike per ACC's 2026-05-09 continuation prompt). If ACC consults `scp.consult_rules` and gets back useful, specific guidance, that's evidence SCP works. If it gets back generic meta-rules ("your services.yml is well-formed"), evidence that the value isn't there yet — and WP-SCP-025 should re-scope toward richer consult-time content.
- **D-021 May-31 atomic-workday checkpoint:** independent track. Does not interact with WP-SCP-025.
- **6 retired rules:** if any prove necessary later (e.g. CT WP-D-WAVE-3 needs `bff_refresh_hardening` enforced; or CT WP-D-WAVE-5 needs `ct_auth_provider_memoization`), file as scope-additions to a future WP-SCP-NNN; do not silently revive them under WP-SCP-025.

## 9. Open questions for kickoff

1. **First-batch rule selection** (operator decision at kickoff — soft signal welcome now; locked at slice 025B kick).
2. **Owner identity** — likely SCP team member; co-owned with CT engineer if rule selection skews toward auth surfaces (e.g. `permission_schema_registered_within_wave_window`).
3. **Cohort enrollment cadence** — advisory phase length per rule (≥1 calendar week per WP-SCP-024 invariant 8 pattern, or shorter for low-risk rules).
4. **ACC MCP-integration coupling** — does WP-SCP-026 (ACC integration) depend on a specific WP-SCP-025 rule shipping first, or are they independent?

---

**Status:** PARKED v0.1 — kicks off after WP-SCP-024 Threshold A; restored to active planning at that time.
