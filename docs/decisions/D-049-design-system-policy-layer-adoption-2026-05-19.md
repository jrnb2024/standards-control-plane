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

The token package's release cadence and Renovate-cascade specifics are deferred to a separate slice (provisionally WP-SCP-025 slice 025B per the sequencing in this decision's "Cross-references" §). The decision here is that **the token package distribution is in scope for SCP's policy layer**, not whether it ships at v1.3.0 or v1.4.0.

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

## Justification

Three load-bearing properties hold under this decision:

1. **The boundary cut is principled, not arbitrary.** SCP's federation primitive evaluates OPA Rego against a static checked-out repo tree. Every rule SCP carries (SCP-R-001 through SCP-R-004) respects this invariant. Element 1's design-system rules respect it. Element 3's token-package distribution respects it (the package is a build artefact, distributed via Renovate, consumed by adopters — SCP doesn't enforce the package's *contents* at the gate). Element 2's MCP consult is the existing receipt-signed surface, extended to a new domain key. No element pulls a browser, a runtime preview, or a CSS parser into SCP. The invariant the federation primitive depends on is preserved.

2. **The token-package distribution mechanism is a reuse, not a new capability.** SCP already publishes versioned releases that propagate to adopters via Renovate. Element 3 extends the *content* of those releases to include the token package; it does not require new infrastructure. The Renovate preset already exists at `renovate/v*`; tag-protection on `v*` and `renovate/v*` already roots the trust chain (D-030 + D-034). The token-package release is a packaging-step addition, not a platform addition.

3. **The sequencing matches the cohort cascade discipline.** SCP-R-005 ships at warn baseline at SCP v1.3.0 — a zero-cost release because no current adopter has `dpbm-scoped: true` declared. Renovate cascades v1.3.0 to onboarded adopters within ~24h. Adopters see the rule defined but never see it fire. The rule earns trust against zero waivers, zero false-positives, zero adopter friction. When recommender becomes the first frontend-heavy DPBM-scoped adopter (estimated 2026-Q3, post-024G), the per-adopter `rule-config.yaml` `dpbm-scoped: true` declaration activates the gate on that one adopter — a per-adopter flip, not a global rule promotion. The pattern is the same as SCP-R-004's warn-baseline → deny-promotion ramp, applied per-adopter rather than estate-wide.

## Cross-references

- `/Users/amplience/Projects/acc/docs/decisions/ADR-016-design-parity-build-method.md` — DPBM doctrine (ACC-side, 2026-04-27).
- `/Users/amplience/Projects/control-tower/docs/decisions/D-048-design-parity-build-method-adoption.md` — DPBM adoption (CT-side, 2026-04-27).
- `/Users/amplience/Projects/mapp-returns-intelligence/docs/design/` — gold-standard Phase-0 artefacts (DESIGN_SPEC.md, FLOW_SPEC.md, TOKENS.md, screenshots/, uat-screenshots/).
- `docs/reviews/rule-proposals/RULE-002-dpbm-artefact-presence.md` — companion rule-RFC proposing SCP-R-005 at warn baseline (filed alongside this ADR for combined operator review).
- `docs/DECISIONS.md` — appended row for D-049 (single-table record).
- `docs/plans/WP-SCP-024-estate-cascade.md` §6 — 024 slice plan; design-system cascade WP-SCP-025 sequenced after 024G Threshold A.
- `STATUS.md` 2026-05-09 chain — original "D-048 DPBM — file SCP-side adoption decision" follow-up item this decision closes.
- `docs/home/HOME.md` §8.2 "Policy expansion" — names DPBM as one of seven real candidates for the federation primitive to carry; this decision ratifies DPBM as the first such candidate filed.

## Tracked-forward items (not blocking this decision)

These items are surfaced for follow-up but do not block D-049 acceptance. They will fold into the WP-SCP-025 slice plan when that opens after 024G signs:

- **TF-D049-001 — Failure-output remediation surface.** When SCP-R-005 fires on an adopter, the GitHub Actions annotation should include a direct URL to RI's `docs/design/TOKENS.md` plus a 3-line corrective code example. Per adopter-experience advocate insight: the current failure surface teaches bypass; teaching remediation in the annotation is a precondition for any deny gate.
- **TF-D049-002 — Hotfix advisory label.** A PR label (e.g., `hotfix: design-gate-advisory`) that downgrades design-system rules from blocking to advisory for that PR only, with the downgrade automatically recorded to the waiver audit trail. Per adopter-experience advocate: waiver-as-emergency-process is intolerable friction under production incident.
- **TF-D049-003 — Token-package release flow.** Element 3 commits to distributing a canonical token package via Renovate; the concrete release cadence, package format (CSS custom-properties file vs Tailwind `@theme` block vs both), and version-bumping policy are deferred to a WP-SCP-025 implementation slice.
- **TF-D049-004 — Per-adopter `dpbm-scoped: true` declaration mechanism.** Adopters opt into design-system rule enforcement via their `.scp/rule-config.yaml`. The schema extension (`schemas/rule-config.schema.json`) for the new `dpbm-scoped` key is a small implementation detail and folds into RULE-002 review.
- **TF-D049-005 — Coordination with the open 024 cascade.** This decision opens authoring of D-049 + RULE-002 + token-package design concurrent with 024C bake observation and 024D ceremony. WP-SCP-025 does NOT open as an active work-package until 024G Threshold A signs. The TF tracks the coordination signal so design-system authoring does not consume operator attention budget reserved for cascade execution.

## Decision points the operator can edit before signing

This ADR is filed in DRAFT status. Before signing (merging this PR), the operator may amend any of the following without re-drafting the broader decision:

1. **Whether to ship SCP-R-005 immediately at v1.3.0 or hold until 024G signs.** The pragmatist position is "ship at warn now, defer WP-SCP-025 build-package to post-024G"; the alternative is "hold everything until 024G." Either is consistent with D-049's three-element shape.
2. **Whether Element 3 (token-package distribution) is in-scope for v1.3.0 or deferred to v1.4.0 / a later cut.** Element 3 is committed to in this decision; only the *cadence* is open.
3. **Whether the first deny-gate target is recommender, shopify-app, or another adopter.** Recommender is the architect+pragmatist convergence; the decision body says "the first frontend-heavy cohort adopter" without naming. The operator may name (or leave open) before signing.
4. **Whether the `dpbm-scoped` rule-config key is the right opt-in mechanism.** Alternative: a global rule that applies to any repo with `docs/design/` populated. The decision commits to opt-in but is silent on the schema; that schema change folds into RULE-002.
