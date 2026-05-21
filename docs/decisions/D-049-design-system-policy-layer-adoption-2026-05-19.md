# D-049 — SCP-side adoption of estate design-system policy layer

**Status:** DRAFT (operator-review surface; not signed)
**Date filed:** 2026-05-19
**Decision date:** TBD (operator signature on merge)
**Operator:** @jrnb2024
**Closes:** open follow-up filed in `STATUS.md` 2026-05-09 chain entry — "D-048 DPBM — file SCP-side adoption decision" (the SCP-side counterpart to CT D-048 + ACC ADR-016 ratified estate-side 2026-04-27).

---

## Context

DPBM — Design Parity Build Method — was adopted estate-side on 2026-04-27 as a layered amendment to the four-tier dispatch pattern for any work that produces designed visual output. The doctrine is documented in two artefacts:

- `/Users/amplience/Projects/acc/docs/decisions/ADR-016-design-parity-build-method.md` — the method itself: Phase 0 Design Lock (DESIGN_SPEC / FLOW_SPEC / TOKENS / pinned screenshots), Phase 1 three-layer test contract (component / flow / visual + a new `harness_coverage` lens), Phase 2 per-view `design_parity` micro-check via Sonnet + Chrome DevTools MCP, Phase 3 holistic UAT producing `UAT_REPORT_*.md` as release sign-off.
- `/Users/amplience/Projects/control-tower/docs/decisions/D-048-design-parity-build-method-adoption.md` — CT-side adoption.

The estate has converged on the *method* but has not yet wired the *policy layer*. Today there is no merge gate that asserts a frontend PR honoured DPBM. ACC's `design_parity` micro-check runs inside the build loop (advisory to that loop) and the `UAT_REPORT_*.md` is produced at release sign-off, but neither artefact gates a PR. An adopter could open a frontend PR with no `DESIGN_SPEC.md`, no `TOKENS.md`, no co-touched visual test, and merge — DPBM ignored — and the merge gate would not notice.

Returns Intelligence (`/Users/amplience/Projects/mapp-returns-intelligence`) is the gold-standard implementation of DPBM Phase 0 artefacts: `docs/design/DESIGN_SPEC.md`, `docs/design/FLOW_SPEC.md`, `docs/design/TOKENS.md`, `docs/design/screenshots/`, `docs/design/uat-screenshots/` are all present and Phase-0-locked. RI is **not** a WP-SCP-024 cohort adopter; it is the oracle the cohort converges toward.

The five cohort adopters (PIM, control-tower, mapp-doc-agent, recommender, shopify-app) vary widely in frontend maturity. PIM has Playwright UAT but no DPBM artefacts. Control-tower has matrix-UI work in flight (D-035 wildcard worktrees). Recommender has the strongest existing frontend stack (Next.js + Storybook references) and is the natural first deny-gate target. Mapp-doc-agent and shopify-app are minimal-frontend and may pass design-system rules vacuously.

The question this decision answers: **what role does SCP play in enforcing DPBM compliance across the estate?**

## Decision

SCP adopts a **three-element policy-layer role** for estate-wide design-system compliance, deliberately bounded so the policy layer does not absorb runtime, dispatch, or platform responsibilities that belong to ACC or to adopter repos.

### Element 1 — Phase-0 artefact-presence gating (OPA Rego rules)

SCP enforces, via the existing federation primitive (`.github/workflows/policy-check.yml`), that DPBM Phase-0 artefacts are present on adopters that have declared themselves DPBM-scoped via `.scp/rule-config.yaml`. The first such rule, SCP-R-005, is specified in `docs/reviews/rule-proposals/RULE-002-dpbm-artefact-presence.md` and ships at `warn` baseline per `policies/VERSIONING.md` (D-036). Subsequent design-system rules (token-reference linkage, visual-test co-touch on frontend PRs, view-coverage in `DESIGN_SPEC.md`, UAT-report presence) follow the rule-RFC process (D-036) on the same warn-baseline → deny-promotion path; they are not bundled with SCP-R-005 and do not pre-commit to a fixed total set.

SCP rules evaluate **static repo state only**: file presence, file path matching, content substring on tracked artefacts, changed-files set arithmetic. Rules do not load running views, do not run browsers, do not compare pixels, do not parse CSS values for token equivalence. The federation primitive's invariant is OPA Rego against the checked-out tree; design-system rules respect that invariant.

### Element 2 — MCP consult surface for design

SCP exposes design rules through the existing MCP server with the new domain key `design`. Agents authoring frontend code call `scp.consult_rules(domain="design")` before authoring, the same way they call `domain="auth"` today (per D-024 + D-025). The response is the matched rule set plus an Ed25519-signed receipt scoped to `base_sha + head_sha + changed_files_hash` with TTL ≤ 2h. Adopter `PreCommit` hooks validate the receipt; commits without a valid receipt for frontend changes get refused, same lifecycle as `auth` consult today.

The view-scoped variant — `scp.consult_rules(domain="design", view=<view_id>)` — is in scope for a later slice once `DESIGN_SPEC.md` provides machine-readable per-view structure across multiple adopters. RI's `DESIGN_SPEC.md` already does this (`view-interventions`, `view-overview`); cohort adopters are unlikely to until DPBM-scoped frontend work begins on them.

### Element 3 — Canonical token-package distribution via the existing Renovate cascade

SCP reuses the Renovate-driven cascade mechanism that today propagates `policy-check.yml` SHA pins, to additionally distribute a canonical design-token package to all onboarded adopters. The tokens themselves are authored and locked in RI's `docs/design/TOKENS.md`; SCP packages a versioned, importable artefact (CSS custom-properties file + Tailwind `@theme` block); adopters consume the package via SHA-pinned import; Renovate auto-PRs each adopter when SCP cuts a new token-package version.

This is a deliberate scope expansion of the cascade — not just rules, but design-system primitives flowing through the same trust-rooted, SHA-pinned, tag-protected pipeline that ships `policy-check.yml`. The cost is one new package-build step in the SCP release flow; the value is single-source-of-truth distribution without forking RI's tokens into every adopter's repo.

The token package's release cadence and Renovate-cascade specifics are deferred to a separate slice (provisionally WP-SCP-025 slice 025B per the sequencing in this decision's "Cross-references" §). **The token package itself ships no earlier than v1.4.0; v1.3.0 carries SCP-R-005 (warn) and the SCP self-dogfood only — no token-package release at v1.3.0.** Cadence beyond v1.4.0 is design-team-paced — the token-package version follows RI's `docs/design/TOKENS.md` authoring cadence, not SCP's federation-primitive release cadence. The decision here remains that the token-package distribution is in scope for SCP's policy layer; D-049 commits to **v1.4.0+** as the floor, deliberately decoupled from v1.3.0 so the rule-RFC path (SCP-R-005) and the platform-distribution path (token package) progress on independent clocks.

### What this decision explicitly does NOT adopt

These items belong to ACC's orchestration layer or to adopter repos' test harnesses, and SCP rejects pulling them into the policy layer:

- **Pixel-level visual diff at the merge gate.** Brittle on font rendering variation, breaks on Playwright engine updates, trains developers to distrust CI. ACC's `design_parity` micro-check (DPBM Phase 2) is the right home — Chrome DevTools MCP + structural diff, with pixel as advisory signal only. SCP rules never load a running view.
- **Token-value equivalence checking.** Verifying that `--ri-brand-600` in CSS matches the value declared in `TOKENS.md` requires parsing CSS-in-JS or CSS custom properties at the AST level. This is an ESLint / Stylelint plugin's job, shipped alongside the token package per Element 3, not an OPA Rego rule.
- **UAT-content evaluation.** Whether the `UAT_REPORT_*.md` *passes* — all flows complete, all parity scores meet threshold — is ACC's determination per ADR-016 Phase 3. SCP rules (if they ever cover UAT) assert only that the artefact exists, never that it passes.
- **Storybook-as-compliance.** Storybook without a wired token contract is documentation theatre, not enforcement. SCP does not mandate Storybook adoption and does not gate on Storybook story presence.

The two hills the orchestrating-skeptic perspective on this decision will not cede: SCP does not load a browser, and SCP does not store design-token *values* in its rules. Both would invert the SCP → ACC dependency or duplicate ACC's runtime capability. Phase 0 artefact discipline plus token-package distribution is the policy-layer slice; everything past it belongs elsewhere.

## Rationale

Four perspectives were sourced via multi-agent adversarial dispatch before this decision was drafted (2026-05-19; archives in the PR opening this ADR). They converged on the three-element shape above:

- **Domain-boundary skeptic.** Argued for a *single* presence-gate rule and nothing more, on the grounds that DPBM is fundamentally a dispatch-method amendment owned by ACC. The hill-to-die-on (no browser inside SCP) is preserved in the decision. The pure-skeptic position (SCP carries one rule and nothing else) was softened by the adopter-advocate perspective (Element 3 — token distribution — is too valuable to forgo, and reuses existing infrastructure).
- **Estate architect.** Proposed five rules (artefact-presence, token-reference, visual-test co-touch, view-coverage, UAT-report) in a single bundled adoption. Softened in this decision to one rule now (SCP-R-005) with the remaining four open to the rule-RFC process individually. The architect's MCP consult surface design is adopted in Element 2.
- **Adopter-experience advocate.** Surfaced the strongest single insight: SCP's current failure surface teaches bypass, not compliance. Two preconditions for any deny-gate ship — failure-output remediation (a token-reference URL + corrective example in the annotation) and a `hotfix: design-gate-advisory` PR label that downgrades blocking rules to advisory for that PR with audit-trail capture. Both are tracked-forward items, not blockers on this decision; see "Cross-references" §.
- **Roadmap pragmatist.** Held the line on cascade sequencing: hold WP-SCP-025 in authoring mode until WP-SCP-024 Threshold A (024G + USER-GATE-E + D-046) signs. Premature design-system cascade is what retired the D-035-aligned rules in early May 2026 (STATUS.md 2026-05-09 chain). This decision preserves the sequencing: SCP-R-005 ships at warn (zero-cost trust-earning) but WP-SCP-025 does not open as an active build work-package until 024G signs.

The three-element shape adopted here is the convergence point all four perspectives reached when forced to specify what they would *not* concede. The skeptic conceded Element 3; the architect conceded the rule-count compression to one-then-RFC-the-next; the advocate conceded that the remediation-surface and hotfix-label work can be tracked-forward rather than blocking; the pragmatist conceded that authoring D-049 + SCP-R-005 at warn does not interfere with 024 cascade execution.

The decision deliberately defers the harder questions — when SCP-R-005 promotes to deny, which adopters opt in via `.scp/rule-config.yaml` `dpbm-scoped: true`, whether the token-package shape converges to plain CSS or to a JS module — to the WP-SCP-025 slice plan, which is gated on 024 cascade completion. The decision does not pre-commit to those answers; it commits to the *shape* of the SCP policy-layer role in design-system enforcement.

**Explicit opt-in confirmation (folded 2026-05-20):** `.scp/rule-config.yaml` `dpbm-scoped: true` is **confirmed** as the canonical opt-in mechanism. The alternative considered in §"Decision points" item 4 (a global rule that applies to any repo with `docs/design/` populated) is rejected — the WP-SCP-024 cascade pattern is per-adopter-declared (`cascade-status: onboarded` is set by adopter PR, not auto-detected), and design-system enforcement inherits that same opt-in shape per `cardinal-rule-1` (deterministic, adopter-declared state at the policy layer). Auto-detection on `docs/design/` directory presence would surface enforcement on adopters that authored DPBM artefacts as documentation without intending to enter the deny-ramp lane — false positive at the worst possible time. The two-tier opt-in (`dpbm-scoped: true` boolean + `threshold-overrides` per-rule map) is the explicit shape; both keys are bypass-surface elements per RULE-002 §5.

## Justification

Three load-bearing properties hold under this decision:

1. **The boundary cut is principled, not arbitrary.** SCP's federation primitive evaluates OPA Rego against a static checked-out repo tree. Every rule SCP carries (SCP-R-001 through SCP-R-004) respects this invariant. Element 1's design-system rules respect it. Element 3's token-package distribution respects it (the package is a build artefact, distributed via Renovate, consumed by adopters — SCP doesn't enforce the package's *contents* at the gate). Element 2's MCP consult is the existing receipt-signed surface, extended to a new domain key. No element pulls a browser, a runtime preview, or a CSS parser into SCP. The invariant the federation primitive depends on is preserved.

2. **The token-package distribution mechanism is a reuse, not a new capability.** SCP already publishes versioned releases that propagate to adopters via Renovate. Element 3 extends the *content* of those releases to include the token package; it does not require new infrastructure. The Renovate preset already exists at `renovate/v*`; tag-protection on `v*` and `renovate/v*` already roots the trust chain (D-030 + D-034). The token-package release is a packaging-step addition, not a platform addition.

3. **The sequencing matches the cohort cascade discipline.** SCP-R-005 ships at warn baseline at SCP v1.3.0 — a zero-cost release because no current adopter has `dpbm-scoped: true` declared. Renovate cascades v1.3.0 to onboarded adopters within ~24h. Adopters see the rule defined but never see it fire. The rule earns trust against zero waivers, zero false-positives, zero adopter friction. When recommender becomes the first frontend-heavy DPBM-scoped adopter (estimated 2026-Q3, post-024G), the per-adopter `rule-config.yaml` `dpbm-scoped: true` declaration activates the gate on that one adopter — a per-adopter flip, not a global rule promotion. The pattern is the same as SCP-R-004's warn-baseline → deny-promotion ramp, applied per-adopter rather than estate-wide.

## Sequencing

SCP-R-005 ships at v1.3.0 at `warn` baseline as **self-dogfood-only**. The rule is defined, packaged, and exercised against SCP's own `main` via the existing self-dogfood wrapper (D-049 §3.3 Element 1's federation-primitive surface). No external adopter is gated by this rule at v1.3.0 — adopter cascade consumption is held pending the **TF-PIM-001 fix** (cross-repo `actions/checkout` authentication for SCP federation adopters; filed 2026-05-19 against PIM PR #236 cascade rollout). Until TF-PIM-001 lands, no external adopter can fetch and exercise the SCP federation primitive cross-repo regardless of which rules it carries; SCP-R-005's adopter-side activation timeline is bound by that gate, not by SCP-R-005's own release readiness.

This is an **artefact-gate, not a time-bake** per `feedback_artefact_gates_not_time_bakes.md` — the unblock signal is "TF-PIM-001 closed + at least one external adopter has run the wrapper cross-repo successfully," not "X weeks have passed since v1.3.0." Calendar dates in this ADR ("estimated 2026-Q3", "Week 27") are orientation aids for the WP-SCP-025 plan-doc, not gates; the canonical sequence is:

1. **v1.3.0 ships** with SCP-R-005 at warn, self-dogfood only. (Zero-cost release; no external adopter is `dpbm-scoped: true`.)
2. **TF-PIM-001 closes** — cross-repo checkout auth resolved; first external adopter runs the wrapper cross-repo green.
3. **First DPBM-scoped adopter declares.** Per D3 resolution, this is Recommender (see §"Decision points" item 3 below). Recommender sets `dpbm-scoped: true` + `dpbm-frontend-paths` override in its `.scp/rule-config.yaml`. SCP-R-005 begins firing on Recommender's frontend PRs at warn.
4. **Warn-to-deny promotion on Recommender** via `threshold-overrides: { SCP-R-005: deny }` in Recommender's `.scp/rule-config.yaml`. Per-adopter promotion, not global RFC. Triggered by Recommender's own readiness, not by SCP's release cadence.
5. **Subsequent adopters** repeat steps 3–4 on their own clocks. No bundled cohort flip; each adopter ramps independently.

The v1.4.0 token-package release (Element 3) is on a parallel, decoupled clock — design-team-paced per §Decision Element 3 amendment above. v1.3.0 → v1.4.0 is not a sequential SCP release dependency; v1.4.0 cuts when the token-package authoring is ready, regardless of where the per-adopter SCP-R-005 ramp has reached.

## Cross-references

- `/Users/amplience/Projects/acc/docs/decisions/ADR-016-design-parity-build-method.md` — DPBM doctrine (ACC-side, 2026-04-27).
- `/Users/amplience/Projects/control-tower/docs/decisions/D-048-design-parity-build-method-adoption.md` — DPBM adoption (CT-side, 2026-04-27).
- `/Users/amplience/Projects/mapp-returns-intelligence/docs/design/` — gold-standard Phase-0 artefacts (DESIGN_SPEC.md, FLOW_SPEC.md, TOKENS.md, screenshots/, uat-screenshots/).
- `docs/reviews/rule-proposals/RULE-002-dpbm-artefact-presence.md` — companion rule-RFC proposing SCP-R-005 at warn baseline (filed alongside this ADR for combined operator review).
- `docs/DECISIONS.md` — appended row for D-049 (single-table record).
- `docs/plans/WP-SCP-024-estate-cascade.md` §6 — 024 slice plan; design-system cascade WP-SCP-025 sequenced after 024G Threshold A.
- `STATUS.md` 2026-05-09 chain — original "D-048 DPBM — file SCP-side adoption decision" follow-up item this decision closes.
- `docs/home/HOME.md` §8.2 "Policy expansion" — names DPBM as one of seven real candidates for the federation primitive to carry; this decision ratifies DPBM as the first such candidate filed.
- `docs/BACKLOG.md` Phase 12 → **TF-PIM-001** "Cross-repo checkout authentication for SCP federation adopters" — explicit adopter-consumption-timing dependency for this decision. SCP-R-005 ships at v1.3.0 self-dogfood-only (see §Sequencing); adopter-side activation requires TF-PIM-001 closed first. D-049 does not block on TF-PIM-001 (it ratifies the SCP-side role + ships the rule into the codebase); D-049's *adopter-cascade outcome* does.

## Tracked-forward items (not blocking this decision)

These items are surfaced for follow-up but do not block D-049 acceptance. They will fold into the WP-SCP-025 slice plan when that opens after 024G signs:

- **TF-D049-001 — Failure-output remediation surface.** When SCP-R-005 fires on an adopter, the GitHub Actions annotation should include a direct URL to RI's `docs/design/TOKENS.md` plus a 3-line corrective code example. Per adopter-experience advocate insight: the current failure surface teaches bypass; teaching remediation in the annotation is a precondition for any deny gate.
- **TF-D049-002 — Hotfix advisory label.** A PR label (e.g., `hotfix: design-gate-advisory`) that downgrades design-system rules from blocking to advisory for that PR only, with the downgrade automatically recorded to the waiver audit trail. Per adopter-experience advocate: waiver-as-emergency-process is intolerable friction under production incident.
- **TF-D049-003 — Token-package release flow.** Element 3 commits to distributing a canonical token package via Renovate; the concrete release cadence, package format (CSS custom-properties file vs Tailwind `@theme` block vs both), and version-bumping policy are deferred to a WP-SCP-025 implementation slice.
- **TF-D049-004 — Per-adopter `dpbm-scoped: true` declaration mechanism.** Adopters opt into design-system rule enforcement via their `.scp/rule-config.yaml`. The schema extension (`schemas/rule-config.schema.json`) for the new `dpbm-scoped` key is a small implementation detail and folds into RULE-002 review.
- **TF-D049-005 — Coordination with the open 024 cascade.** This decision opens authoring of D-049 + RULE-002 + token-package design concurrent with 024C bake observation and 024D ceremony. WP-SCP-025 does NOT open as an active work-package until 024G Threshold A signs. The TF tracks the coordination signal so design-system authoring does not consume operator attention budget reserved for cascade execution.

## Decision points (operator-resolved, folded 2026-05-20)

This ADR was filed 2026-05-19 in DRAFT status with four open decision points. Operator returned the resolutions below on 2026-05-20 (pre-restart authorisation); the four points are now closed and the text below captures the operator's choice on each. ADR status remains DRAFT in this file until the PR opening it merges; merge is the ACCEPTED-flip ceremony per established pattern.

1. **Ship SCP-R-005 at v1.3.0 immediately, vs hold until 024G signs.** **RESOLVED: ship at v1.3.0 at warn baseline, self-dogfood only.** Adopter-cascade consumption is held until TF-PIM-001 fix lands (see §Sequencing). The pragmatist position carries — warn-at-v1.3.0 + dogfood is zero-cost and earns trust against zero waivers. WP-SCP-025 (design-system build work-package) remains in authoring mode until 024G Threshold A signs; that gating is unchanged.

2. **Element 3 (token-package distribution) in-scope for v1.3.0, or deferred.** **RESOLVED: deferred to v1.4.0+** (design-team-paced; see §Decision Element 3 amended text). v1.3.0 ships the rule + self-dogfood only — no token-package release at v1.3.0. v1.4.0 floor commits to token-package distribution; the cadence beyond v1.4.0 follows RI's `docs/design/TOKENS.md` authoring tempo, decoupled from SCP federation-primitive release cadence.

3. **First deny-gate target — recommender, shopify-app, or other.** **RESOLVED: Recommender.** Captured rationale (5 bullets):

   - **Architectural rationale.** Recommender aligns with the existing Phase 2 cascade slice 12 timing (Week 27 per CT auth-foundation v7 plan-doc); the first DPBM-deny activation is naturally concurrent with the TF-PIM-001 fix calendar (cross-repo checkout auth resolution + first non-PIM cascade adopter both arrive in the same window). Reflects the architect/pragmatist multi-agent convergence point recorded in §Rationale.
   - **Mid-flight non-conflict.** Recommender's J1-INT work in flight at 2026-05-20 is backend/DB-layer (Prisma `admin_audit` extension + D.1 hardening + DB constraint work). SCP-R-005 fires only on the adopter's `dpbm-frontend-paths` glob set (default `frontend/**`); zero intersection with the current J1-INT changeset. Activating SCP-R-005 against Recommender does not collide with the in-flight admin_audit lane.
   - **ACC alternative — captured, deferred.** ACC was considered as a showcase deny-gate target (it carries the DPBM doctrine source ADR-016 and would be self-referentially demonstrative). Rejected for first-target: it would require a net-new cascade slice ahead-of-schedule and competes with ACC's current Wave 6 + test-debt sweep bandwidth. ACC is captured as a *future* deny-gate adopter for showcase value once Recommender ramp completes.
   - **SA alternative — captured, deferred (added 2026-05-20 PM).** Shopify-app (SA) also captured as a future deny-gate adopter, naturally sequenced as #3 post-Recommender + ACC. SA-011 visual migration closed 2026-05-20 with a clean `v2/**` design substrate + zero SDK pin drift — the substrate is already in the shape SCP-R-005 is meant to verify (Phase-0 oracle present + frontend paths well-isolated). Not selected as first-target because: (1) Recommender's per-adopter glob caveat is a more demanding first concrete example (forces the override pattern out into RULE-002 §3.4 immediately rather than deferring), and (2) Recommender's Phase 2 cascade slice 12 timing is already on-calendar; SA's deny-gate slice would require a net-new cascade slice with no calendar anchor. SA enters first-flight candidacy at the natural #3 position post-Recommender deny-promotion + ACC deny-promotion.
   - **NOT-PIM-first rationale.** PIM is the obvious first-adopter on cascade order (it carries `cascade-status: onboarded` from 024C), but PIM's `policy-check / scp/policy-check` required-check is currently **relaxed** on `main` pending the TF-PIM-001 cross-repo checkout auth fix. Promoting DPBM enforcement against a repo whose underlying required-check is mid-relax would conflate two failure modes (auth-blocker vs DPBM-Phase-0-absence) and degrade signal on both. PIM re-enters first-flight candidacy after TF-PIM-001 closes AND PIM's main re-enables the required check; at that point PIM is a candidate for SCP-R-005 deny activation in its own right (likely sequenced after Recommender on operator clock).
   - **Per-adopter glob caveat.** Recommender's frontend tree exercises both the **default** `frontend/**` glob (top-level `frontend/src/app/`) **and** a path under `shopify-app/app/**` per the 2026-05-20 grep-check the operator surfaced. Recommender therefore sets `dpbm-frontend-paths: ["frontend/**", "shopify-app/app/**"]` in `.scp/rule-config.yaml` — the default plus an explicit override. RULE-002 §3.4 documents the per-adopter override pattern; Recommender is the first concrete example folded back into the rule-RFC.

4. **`dpbm-scoped` rule-config key, vs global rule on any repo with `docs/design/` populated.** **RESOLVED: `dpbm-scoped: true` per-adopter declared opt-in.** See §Rationale "Explicit opt-in confirmation" — auto-detection on directory presence creates a false-positive at the worst possible time (adopters who authored DPBM artefacts as documentation without intending the deny-ramp). Per-adopter declaration mirrors the WP-SCP-024 `cascade-status: onboarded` shape per `cardinal-rule-1` (deterministic, adopter-declared state at the policy layer). The schema extension folds into RULE-002 §5 (`schemas/rule-config.schema.json` adds three keys: `dpbm-scoped`, `dpbm-frontend-paths`, `threshold-overrides`).
