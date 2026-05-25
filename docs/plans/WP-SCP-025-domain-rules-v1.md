# ProgrammePlan — WP-SCP-025 Domain Rules v1

**Work Package:** `WP-SCP-025`
**Version:** 1.0 (active — Phase 1 in flight)
**Status:** ACTIVE — Phase 1 (2 rules) authoring 2026-05-25.
**Date kicked off:** 2026-05-25 (operator-authorised early kickoff per 2026-05-25 directive; original parking precondition softened — see §3.1 below)
**Predecessors:**
- WP-SCP-021 (MCP Server) — landed; receipts + `scp.consult_rules` available.
- WP-SCP-024 024B-core/extras-1/2/3 (cascade infrastructure) — landed.
- WP-SCP-024 024C (PIM cohort adopter #1) — **LIVE since 2026-05-24** (CLOSED via PR #147).

**Predecessor softened:** the original v0.1 PARKED predecessor was "WP-SCP-024 at Threshold A (≥3 cohort adopters)". Operator directive 2026-05-25 unpark this to "≥1 cohort adopter live + cascade plumbing proven end-to-end" — see §3.1.

## 1. Purpose

WP-SCP-020 + WP-SCP-021 + WP-SCP-023 + WP-SCP-024 give SCP per-PR authority + pre-code consultability + estate-wide observability + cohort-cascaded enforcement (now with PIM as adopter #1 LIVE). **They do not, on their own, justify SCP as a project.** SCP's near-term credibility depends on shipping real domain rules that catch things human review misses, used by adopters who'd otherwise be in trouble.

WP-SCP-025 is the first batch of post-infrastructure domain rules. It exists to test the proposition that SCP's policy authority is load-bearing — not just that its CI plumbing works.

## 2. Goal + success criterion

**Goal (Phase 1, locked 2026-05-25):** ship **2** high-value domain rules — **SCP-R-007** (waiver expiry within window) + **SCP-R-008** (secrets not in committed env files) — that catch specific failure patterns adopters cannot reliably catch with review alone. SCP-R-005 + SCP-R-006 are RESERVED for D-049 (RULE-002 design-system) + D-036 (RULE-003 ACC-as-cross-repo-caller) per their respective in-flight slices and intentionally skipped in the WP-SCP-025 numbering.

**Success criterion (≥4-week observation window from rule ratification):**
- ≥1 cohort adopter (PIM at minimum) running both SCP-R-007 + SCP-R-008.
- Green pass rate ≥80% across all PIM PRs (rule produces signal, not noise).
- ≥1 rule-driven PR rejection or waiver-filing event captured a real bug or unsafe pattern that would otherwise have shipped.

**Anti-criterion (treat as failed and re-scope if any of these hold at the 4-week mark):**
- Zero `scp.consult_rules` MCP calls from any consumer (still 0 as of 2026-05-25; tracked in §8).
- Zero rule waivers filed across the cohort AND zero rule-driven PR rejections (suggests the rules don't fire on real adopter traffic — they're testing for nothing real).
- Adopter (PIM) files a TF asking for either rule to be reverted or watered down.

## 3. Phase 1 rule selection (locked 2026-05-25)

### 3.1 Why early kickoff (operator-attended decision)

The original v0.1 parked precondition was "WP-SCP-024 at Threshold A (≥3 cohort adopters)". With only PIM live as of 2026-05-24, that precondition is not satisfied. The 2026-05-25 operator decision relaxes the precondition to "≥1 cohort adopter live + cascade plumbing proven end-to-end" on these grounds:

1. **Plumbing is the de-risked half.** TF-PIM-001 closure proves the federation-primitive scales to cross-org cross-repo via the GitHub App credential surface. The remaining cascade work (024D-024G) is operator-paced bake observation, not engineering.
2. **Substance is the under-de-risked half.** Of the 4 rules currently live (SCP-R-001..004), three are narrowly scoped (services.yml / waivers / dep manifest) and one is warn-only (R-004). On a representative PIM PR none of them fires. The gate is GREEN-by-default. That makes SCP's value-prop "the plumbing works" rather than "the gate catches things humans miss".
3. **PIM as v1 adopter is sufficient signal.** A single adopter running 2 deny-baseline rules across 4 weeks gives enough signal to decide whether the rules are load-bearing. Estate-broad consumption (Threshold A) is the v2 question, not v1.

### 3.2 Selected rules

| # | Rule ID | Title | Initial threshold | Why this one |
|---|---|---|---|---|
| 1 | `SCP-R-007` | `waiver_expiry_within_window` — waivers must have `expires_at` ≤ 90 days from `created_at` AND must not already be expired | **deny** (LOW false-positive risk; date arithmetic on JSON schema field) | Extends SCP-R-002 (schema) + SCP-R-004 (URL citation) with semantics: waivers must be bounded + non-stale. Closes the auth-bypass-by-stale-waiver pattern. Date arithmetic is crisp; FP rate estimated ≤0.5% (only legitimate-but-long-running waivers trigger; those should be flagged anyway). |
| 2 | `SCP-R-008` | `secrets_not_in_committed_env_files` — `.env*` files (other than `.env.example`/`.env.template`/`.env.dist`) must not contain credential-pattern values | **warn** (MEDIUM false-positive risk; entropy + key-shape heuristics) | Standard secret-leakage pattern; multiple near-misses across estate. Universal applicability (every repo can have `.env` files). Warn-first per VERSIONING.md ramp; promotion to deny after ≥4 weeks of low-FP observation. |

### 3.3 Rules DEFERRED from §3 candidate list (parked-plan §3)

| Candidate | Reason for deferral |
|---|---|
| `protected_tables_updated_with_migration` | Narrow applicability (only apps with Alembic migrations + CT-style PROTECTED_TABLES constant); requires cross-repo CT-side state read. Defer to Phase 2. |
| `r1_evidence_linked_in_pr_body` | Already implemented as `.github/workflows/r1-evidence-check.yml`. Duplicating into Rego adds no value (the workflow IS the enforcement, not the rule library). DROP from candidate list. |
| `permission_schema_registered_within_wave_window` | HIGH complexity (cross-repo CT-side state read for live `permission_schemas` table); auth-adjacent (per `feedback_orchestrator_auth_surface_plan_review_default` triggers mandatory 3-agent plan-stage review). Defer to Phase 2 with proper cross-repo coordination. |

## 4. Anti-scope (what WP-SCP-025 Phase 1 is NOT)

- NOT a re-litigation of the 6 retired rules (sdk_version_pin / ct_sdk_conformance / sdk_migration_waiver / sdk_adoption_schedule / bff_refresh_hardening / ct_auth_provider_memoization). Those are off the table for v1.
- NOT a rule-for-the-sake-of-rules exercise. Each Phase 1 rule names the specific failure pattern it catches.
- NOT estate-wide enforcement on all 5+ cohort adopters from day 1. PIM is the only live consumer; the rules ship + bake on PIM. Cohort cascade is Phase 2.

## 5. Process protocol

WP-SCP-025 follows the four-tier dispatch protocol per `feedback_four_tier_dispatch.md`:

- **Plan-doc kickoff slice (025A — this v1.0):** Opus orchestrator drafts; 3× parallel Sonnet R1 review of the plan-doc + bundled artefacts; R2 fixpoint required before merge.
- **Per-rule implementation slice (025B+025C bundled):** RFC proposal at `docs/reviews/rule-proposals/RULE-004.md` + `RULE-005.md` per D-036 (48h wall-clock; quorum=1 in single-operator mode per D-040 CEILING-not-FLOOR). Rego authoring at `policies/SCP-R-007.rego` + `policies/SCP-R-008.rego`. Per-rule OPA coverage ≥90%. Conftest test fixtures matching SCP-R-004 pattern. 3-lens parallel Sonnet R1 review on the implementation bundle. Codex executor NOT required — Rego authoring is non-kernel-dangerous (adds files; the `WARN_BASELINE_RULES` 1-line edit is minor + reviewable).
- **PIM cohort extension slice (025D):** PIM already auto-consumes via Renovate-driven SHA bump cycle. No SCP-side action needed beyond cutting v1.3.0; Renovate bumps PIM wrapper next cycle.
- **Threshold + closure slice (025E):** observation window measurement + USER-GATE-F if success criteria met OR re-scope if anti-criteria fire.

## 6. Slice plan (locked 2026-05-25)

| Slice | Deliverable | Decision filed | PR # |
|---|---|---|---|
| 025A (this) | Plan-doc v1.0 + RULE-004 + RULE-005 proposals + SCP-R-007.rego + SCP-R-008.rego + tests + `WARN_BASELINE_RULES` add R-008 + v1.3.0 cut | D-052 | TBD |
| 025D | PIM cohort extension (Renovate-driven; passive) | (inherits D-045) | (Renovate auto-PR on PIM) |
| 025E | Threshold observation + USER-GATE-F | D-053 | TBD |

## 7. Decisions reserved

- **~~D-050~~** — REASSIGNED to TF-PIM-001 ADR (Path C App credential surface) per 2026-05-21 status; the parked-plan §7 reservation of D-050 for WP-SCP-025 is OBSOLETE.
- **D-052** — Phase 1 rule operational contract: SCP-R-007 ships at deny baseline (LOW FP risk); SCP-R-008 ships at warn baseline (MEDIUM FP risk) with promotion to deny gated on ≥4 weeks of low-FP observation per VERSIONING.md ramp.
- **D-053** — WP-SCP-025 Phase 1 Threshold criteria + decision on whether to proceed to Phase 2 (3 more rules from §3.3 candidate list).

## 8. Forward-looking

- **MCP consumption signal:** 0 `scp.consult_rules` calls as of 2026-05-25 (the MCP server is unconsumed). If Phase 1 ships + still zero calls 4 weeks later, that's strong evidence the MCP surface needs investment (e.g. WP-SCP-026 ACC-MCP-integration spike) or removal.
- **6 retired rules:** if any prove necessary later (e.g. CT WP-D-WAVE-3 needs `bff_refresh_hardening` enforced), file as scope-additions to a future WP-SCP-NNN; do not silently revive them under WP-SCP-025.
- **PR #148 (D-036 RULE-003 / SCP-R-006) interaction:** orthogonal — PR #148 ships a rule-RFC + ADR pair targeting v1.4.0; this slice ships v1.3.0. Numbering reserves R-006 for PR #148. No coupling.

## 9. Risks

1. **`SCP-R-008` entropy heuristics produce noise.** Mitigation: warn baseline + explicit allow-list of conventional non-secret filenames (`.env.example` / `.env.template` / `.env.dist`); §3.1 of RULE-005 spec details the regex anchors. FP-rate hard cap before promotion to deny: ≤2% on adopter PRs.
2. **`SCP-R-007` 90-day window is over-permissive for some auth waivers.** Mitigation: the cap is per-adopter `.scp/rule-config.yaml` overridable (e.g. CT could tighten to 30 days); operator-paced adjustment.
3. **WARN_BASELINE_RULES set grows unbounded.** Mitigation: TF-020P-001 still applies (data-driven `policies/rule-baselines.yaml`); we add R-008 as 1-line edit now, file TF-020P-001 as the proper closure path when a 3rd warn-baseline rule lands.

## 10. Acceptance criteria

1. WP-SCP-025 plan-doc v1.0 merged + D-052 ACCEPTED.
2. RULE-004 + RULE-005 proposal docs landed.
3. `policies/SCP-R-007.rego` + `policies/SCP-R-008.rego` landed with ≥90% per-rule OPA coverage.
4. `WARN_BASELINE_RULES` set extended to `{"SCP-R-004", "SCP-R-008"}`.
5. SCP cuts **v1.3.0** (MINOR per VERSIONING.md — additive opt-in scorecard-emit pattern continues; new rules are additive even at deny baseline because adopters can `.scp/rule-config.yaml disable: true` per D-036 deprecation contract).
6. PIM-side Renovate auto-PR opens within ~24h of v1.3.0 cut + merges clean (no FP storm).

---

**Status:** ACTIVE v1.0 — 025A in flight 2026-05-25.
