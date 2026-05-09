# ProgrammePlan — WP-SCP-024 Estate Cascade

**Work Package:** `WP-SCP-024`
**Version:** 0.1
**Status:** Draft — ready for plan-PR review
**Date:** 2026-05-03
**Branch:** `feature/wp-scp-024-estate-cascade-plan`
**Programme Ref:** to be filed at slice 024A close-out (proposed `SCP-110` estate cascade backlog row)
**Decisions reserved (do not assign in any slice before the named target slice — see `docs/DECISIONS.md` header reservation note):**
- **D-044** — reserved for slice 024B: `scripts/scaffold-downstream.sh` (`SCP-073-scaffolder`) operational contract + adopter-template versioning + invocation-log convention extension.
- **D-045** — reserved for slice 024C: estate cascade ordering + per-adopter onboarding contract (PR shape, branch-protection invocation log, post-bake observation window) + canary-first sequencing.
- **D-046** — reserved for slice 024G: estate-cascade Threshold A criteria + post-Threshold-A maintenance posture (recurring drift remediation, version-ramp coordination, departing-adopter procedure).

**Predecessors:**
- `WP-SCP-019` (Service Auth Contract) — closed 2026-04-20.
- `WP-SCP-020` (Policy Federation Primitive) — closed 2026-04-30 at v1.0.0; v1.1.0 cut 2026-05-02; v1.2.0 cut 2026-05-03 (WP-SCP-023 023B emitter).
- `WP-SCP-020.1` (FLA pilot) — **separate track**, not a predecessor for this WP. WP-SCP-024 is explicitly **FLA-independent** per operator direction (2026-05-03): FLA's pilot stability is on its own canary timeline; the non-FLA cohort proceeds in parallel.
- `WP-SCP-021` (MCP Server) — landed 2026-04-29 (USER-GATE-C signed).
- `WP-SCP-022` (Implementation Programme) — closed 2026-04-30 at Threshold A; post-Threshold-A backlog cleared 2026-05-02 / 03.
- `WP-SCP-023` (Cross-repo Scorecards) — closed 2026-05-03 at slice 023E (USER-GATE-D scaffolded; aggregator surface live; awaiting first three real adopters before USER-GATE-D signs).
- **TF-023E-001 + TF-023E-002 carry forward**: scorecard-emit opt-in is BLOCKED on adopter repo being public OR org-owned (GitHub `actions/attest-build-provenance` constraint on user-owned private repos) AND on `policy-check.yml` `attest-scorecard` job restructure (called-workflow per-job permission ceiling validation at startup). WP-SCP-024 designs around both: required-check cascade is mandatory + does NOT depend on attestation; scorecard-emit opt-in is a secondary artefact gated on TF-023E-002 closure.

## 1. Purpose

WP-SCP-020 + WP-SCP-021 + WP-SCP-023 give SCP per-PR authority + pre-code consultability + estate-wide observability — but only on repos that have already opted in. SCP-self (the dogfood instance) and FLA (canary pilot via WP-SCP-020.1) are the only currently-onboarded repos as of 2026-05-03.

`WP-SCP-024` ratifies the **estate cascade** — the coordinated procedure for onboarding the rest of the named adopter cohort onto the federation primitive's required check, with optional scorecard-emit opt-in as a secondary artefact. It:

1. Defines the **adopter cohort** for cascade: `{pim, recommender, shopify-app, mapp-doc-agent, control-tower}` per D-035 (= the 5 estate repos enumerated when D-035 ratified `scripts/enable-required-check.sh` as canonical onboarding mechanism). FLA is explicitly a separate track per operator direction (2026-05-03 — "FLA-independent implementation slices") + the WP-SCP-020.1 canary continues on its own cadence.
2. Defines a **per-adopter onboarding contract** that each cascade slice satisfies: (a) caller wrapper PR'd into the adopter repo with SCP federation primitive SHA-pinned per VERSIONING.md (D-036); (b) `scripts/enable-required-check.sh` invocation per D-035 with invocation-log entry under `docs/reviews/WP-SCP-020/branch-protection-log.md` — **conditional on the slice's `cascade-status:` declaration per §5.2 + invariant 2** (only `onboarded` and `onboarded-operator-bump` slices add a log entry; `blocked-on-adopter-conflict` slices MUST NOT modify the log file); (c) post-bake observation window of ≥1 calendar week before cascade declares the adopter onboarded; (d) opt-in scorecard-emit added as a follow-up sub-slice once TF-023E-002 closes AND the adopter's repo visibility allows OIDC artefact attestation per TF-023E-001.
3. Defines a **canary-first sequencing** that minimises blast radius: smallest cooperative adopter first (PIM target), control-tower (high-traffic flagship) second, then mapp-doc-agent + recommender as a paired slice, then shopify-app last. The sequencing is reversible per slice — any adopter can be removed via PR to the adopter wrapper file + a parallel `enable-required-check.sh --restore` invocation (added at slice 024B).
4. Defines a **scaffolder helper** (`scripts/scaffold-downstream.sh` = `SCP-073-scaffolder` per WP-SCP-020 §11 follow-up + WP-SCP-021 follow-up `SCP-075-scaffolder-compose`) that emits the adopter-side artefacts (wrapper + CODEOWNERS template + ADOPT-001 reference) from a versioned template, so each cascade slice's adopter PR is mechanically consistent.
5. Defines a **Threshold A criterion** for WP-SCP-024: ≥3 of the 5 cohort adopters have `policy-check / scp/policy-check` required-check live + ≥1 SCP minor version-bump cycle (e.g. v1.2.0 → v1.3.0) propagated cleanly **via Renovate** to those adopters (operator-driven bumps under R-024-07 do NOT count toward Threshold A on their own).

This is **WP-SCP-024 ("estate rollout" per WP-SCP-020 §3 / "estate cascade" per WP-SCP-022 §12)** — the natural successor beyond the 5-move MVCP. WP-SCP-020 made SCP authoritative per-PR on opt-in repos; WP-SCP-021 made SCP consultable pre-code; WP-SCP-023 made SCP observable estate-wide; WP-SCP-024 **drives down the un-onboarded surface** in the named adopter cohort, turning observation into action.

This plan is a **process artefact + spec artefact** — it does not ship code in this slice. Implementation lands in 024B (scaffolder helper) → 024C..024F (per-adopter onboarding) → 024G (Threshold A telemetry + USER-GATE-E).

## 2. Invariants and what this is NOT

### Invariants

1. **Cascade is opt-in per-adopter.** Each adopter onboarded via a PR _to that adopter's repo_, reviewed by an adopter-side maintainer (or, in single-operator mode, by @jrnb2024 self-merging after the SCP-side cascade slice's plan-doc R2 fixpoint). No silent enable. No estate-wide branch-protection mass-mutation. The adopter wrapper PR is the consent surface.
2. **Required-check enablement is operator-run + invocation-logged + CI-enforced.** `scripts/enable-required-check.sh` per D-035 runs from the operator's local environment (the script refuses CI=true / GITHUB_ACTIONS=true per D-035), with an invocation log entry under `docs/reviews/WP-SCP-020/branch-protection-log.md` (the D-035-canonical estate-cascade audit trail; the file's existing comment "Estate cascade rollout = WP-SCP-024" reserves it for this WP) that captures operator, timestamp, script SHA256, target repo+branch, before/after API JSON. An apply without the log entry is unrecorded. **CI enforcement (lands in 024B as `scripts/check-invocation-log-entry.sh`)** parses DISPATCH-NOTE `cascade-status:` field. **Fail-closed default (closes 024A R6 R6-NEW-MAJ-003 safety):** if `cascade-status:` is absent OR contains a value not in the enumerated set `{onboarded, onboarded-operator-bump, blocked-on-adopter-conflict}`, the script exits non-zero (CI fails). Recognised values map to check-paths:
   - **`cascade-status: onboarded` (Renovate path):** PR MUST modify `docs/reviews/WP-SCP-020/branch-protection-log.md` AND the modified entry's target repo string MUST match the DISPATCH-NOTE's target.
   - **`cascade-status: onboarded-operator-bump` (R-024-07 fallback path):** PR MUST modify `docs/reviews/WP-SCP-020/branch-protection-log.md` (target match as above) AND STATUS.md MUST contain a row matching the standardised prefix `TF-024X-renovate-<adopter-slug>` **with meaningful content** (format spec below). A bare-prefix stub row fails CI. (Closes 024A R4 R4-NEW-MAJ-002 (safety) — bare-prefix stub bypass.)
   - **`cascade-status: blocked-on-adopter-conflict` (invariant-10 path):** PR MUST NOT modify `docs/reviews/WP-SCP-020/branch-protection-log.md` (no `enable-required-check.sh` invocation occurred — closing the bypass surface that R3 safety surfaced) AND MUST reference the filed `TF-024X-conflict-<adopter>` TF in DISPATCH-NOTE matching the standardised prefix **with meaningful content** (format spec below; bare-prefix stub fails CI per the same rule above).

   **Meaningful-content format spec (closes 024A R5 R5-NEW-MAJ-002 safety + 024A R6 R6-NEW-MAJ-001 safety/completeness regex prose mismatch + 024A R6 R6-NEW-MAJ-001 completeness regex file-scoping).** TF-024X references — whether they appear in STATUS.md (the `onboarded-operator-bump` row in "Tracked-forward items") or in DISPATCH-NOTE (the `blocked-on-adopter-conflict` reference) — MUST contain a line matching this regex literally:

   ```
   TF-024X-(renovate|conflict)-[a-z0-9]+(?:-[a-z0-9]+)+(?:\*\*)? \((open|pending|in-progress|closed)\): \S.{19,}
   ```

   The regex is **file-agnostic**: it matches the TF reference content, not the surrounding markdown (so the same line passes whether it has a `- **...**` STATUS.md bullet wrapper, lives in a DISPATCH-NOTE prose paragraph, or is otherwise embedded). The `(?:\*\*)?` optional group accepts the trailing `**` closing-bold marker that STATUS.md bullet format produces between the slug and the status parenthetical (closes 024A R7 R7-NEW-CRIT-001 — fix-round-6 dropped this and Example 1 silently failed its own regex). Concretely: `TF-024X-{type}-<adopter-slug>` (type ∈ {`renovate`, `conflict`}; adopter-slug is `<owner>-<repo>` lowercased, hyphens only), optionally followed by `**` (STATUS.md closing-bold), then ` ` (single space), parenthesised status ∈ {`(open)`, `(pending)`, `(in-progress)`, `(closed)`}, `: ` separator, then **≥20 characters starting with a non-whitespace character** (`\S` anchor at start of description prevents all-whitespace bypass per R6 safety; `.{19,}` allows the remaining 19+ chars to be anything). `check-invocation-log-entry.sh` (024B) implements this regex literally + greps for it across STATUS.md (operator-bump path) or DISPATCH-NOTE (conflict-close path) per the `cascade-status:` value.

   Examples:
   - ✅ `- **TF-024X-renovate-jrnb2024-pim** (open): Renovate disabled on PIM; operator-bumped @abc123 at 024C; track until adopter enables Renovate cohort.` (STATUS.md bullet wrapping passes — regex doesn't care about wrapper)
   - ✅ `See TF-024X-conflict-jrnb2024-pim (pending): adopter has prior policy-check workflow; awaiting rename PR.` (DISPATCH-NOTE prose embedding passes — regex doesn't care about wrapper)
   - ❌ `- **TF-024X-renovate-jrnb2024-pim**` (bare-prefix stub — fails: no status field)
   - ❌ `- **TF-024X-renovate-jrnb2024-pim** (open):` (empty description — fails: 0 chars after `: `)
   - ❌ `- **TF-024X-renovate-jrnb2024-pim** (open):                    ` (all-whitespace 20-char description — fails: `\S` anchor demands non-whitespace start)
   - ❌ `- **TF-024X-renovate-jrnb2024-pim** (open): short` (only 5 chars after `: ` — fails: `\S.{19,}` demands ≥20)

   The check is a hard predecessor for slice 024C — 024C does not open until the enforcement script is committed + green AND covers all four CI behaviours (the three named cascade-status check-paths + the fail-closed default for absent/unrecognised values). Closes 024A R1 MAJ-SAFE-001 + 024A R2 NEW-MAJ-001 + 024A R3 R3-NEW-MAJ-001 (correctness — third cascade-status value) + 024A R3 R3-NEW-MAJ-001 (safety — bypass via concurrent invocation + conflict-declaration) + 024A R4 R4-NEW-MAJ-002 (safety — bare-prefix TF-row stub bypass) + 024A R5 R5-NEW-MAJ-002 (safety — meaningful-content format spec) + 024A R6 R6-NEW-MAJ-001 (safety + completeness — regex non-whitespace anchor + file-agnostic scoping) + 024A R6 R6-NEW-MAJ-003 (safety — fail-closed default).
3. **Cascade does NOT touch existing adopter content.** The wrapper is added; CODEOWNERS may gain a `.github/workflows/policy-check-wrapper.yml` line if the adopter has a CODEOWNERS file; nothing else in the adopter repo is modified by the cascade slice. Specifically: NOT the adopter's `README.md`, NOT `.github/workflows/*` other than the wrapper itself, NOT `package.json` / `pyproject.toml` / build config, NOT `.scp/rule-config.yaml` (the adopter writes that themselves once they need rule-level config).
4. **FLA-independent.** WP-SCP-020.1 (FLA pilot) runs on its own track. WP-SCP-024 cascade slices MUST NOT block on FLA pilot reaching a "stable" state, MUST NOT consume FLA-derived templates (FLA is "still maturing, don't freeze template yet" per `reference_fla_gold_standard.md` 2026-05-03), and MUST NOT cite FLA outcomes as gate-criteria for non-FLA cascade slices. If FLA pilot reaches a milestone during WP-SCP-024 work, cascade slices may opportunistically reference FLA learnings but MUST NOT add any FLA precondition.
5. **Required-check cascade is the primary deliverable; scorecard-emit opt-in is secondary.** Each cascade slice must deliver a working required-check before declaring the adopter onboarded. Scorecard-emit opt-in is a follow-up sub-slice gated on TF-023E-002 closure (+ adopter visibility/ownership per TF-023E-001). An adopter that has the required-check live but no scorecard-emit yet is fully onboarded for cascade purposes.
6. **No cross-repo write surface from automation.** All adopter-repo writes are operator-driven PRs. No cron, no GitHub Action, no MCP method writes to an adopter repo at any point during cascade. The aggregator (WP-SCP-023 023C) reads from adopter repos but never writes; same posture extends here.
7. **Per-adopter rollback is single-operator-doable.** Each cascade slice ships a rollback procedure: `enable-required-check.sh --restore <pre-state.json>` reverts branch protection to the captured before-state, and the adopter wrapper PR can be reverted via standard `git revert`. Rollback time SLO: **<30 minutes from operator decision to merge-restored state — claimed only after slice 024B closes with a demonstrated real-repo round-trip on a throw-away test repo (not a dry-run mock).** The SLO is aspirational at 024A merge; 024B's acceptance criterion in §6 makes the round-trip a hard predecessor for 024C. Documented per cascade slice. Closes 024A R1 MAJ-SAFE-003.
8. **SCP version-skew tolerance is the cascade timing primitive.** Adopters cascade in onto a current SCP version (v1.2.0 as of 2026-05-03). The post-bake observation window (≥1 week per slice) is intentionally long enough that the next SCP minor version-bump (Renovate-driven SHA pin update) surfaces during the bake — proving version-skew tolerance against a real upgrade cycle, not just a single point-in-time onboard. A cascade slice that completes onboarding without a version-bump occurring during bake MUST extend bake until at least one Renovate-issued SHA pin bump has been merged + observed clean.
9. **Bus-factor-1 acknowledged.** Single-operator mode (D-031). The cascade operator is the same identity across SCP-self, FLA, and the 5-cohort adopters. The 2026-07-21 quarterly review (per WP-SCP-020 §8 + STATUS.md) covers exposure for the full estate post-cascade. Cascade slices MUST surface this in each adopter PR's body (so adopter-side maintainers see the same exposure framing).
10. **No backwards-incompatible adopter-side work in cascade slices.** Each adopter's onboarding PR is purely additive (a new wrapper file + optional CODEOWNERS lines). Renames, deletions, or modifications to existing adopter-side files are out of scope. **If a conflict is discovered during cascade** (e.g. adopter has a stale `policy-check.yml` from a prior unrelated experiment): (a) the cascade slice CLOSES on the SCP side with status `blocked-on-adopter-conflict` (not deferred indefinitely); (b) a forward TF is filed (`TF-024X-conflict-<adopter>`) owned by the cascade slice author and targeting the adopter-side resolution (typically a rename); (c) when the conflict is resolved, a NEW cascade sub-slice opens for that adopter. This eliminates the open-ended "defer" state. Closes 024A R1 MIN-SAFE-006.

### What this is NOT

- **NOT a forced-march onboarding.** Adopters that aren't ready cascade later or not at all; absence from the index is not a signal of non-compliance.
- **NOT a vendor-SLA cascade.** WP-SCP-024 cascades the SCP federation primitive. Vendor SLAs (Snyk, Dependabot, Renovate-self) are out of scope.
- **NOT an estate-wide config standardisation cascade.** Adopters keep their own `.scp/rule-config.yaml` content. The cascade adds the gate, not the config.
- **NOT an enforcement-cascade for waivers / break-glass.** The federation primitive's `scp_bypass` mechanism is per-PR, not estate-toggled. Cascade does not modify break-glass posture.
- **NOT a replacement for FLA pilot.** FLA pilot is the canary for "is the federation primitive even working?" — that question is closed for WP-SCP-024's purposes. FLA continues independently.
- **NOT a one-shot.** Cascade is multi-slice (one slice per adopter). Each slice is independently mergeable + reversible.

## 3. Programme protocol position

WP-SCP-024 follows the four-tier dispatch protocol per `feedback_four_tier_dispatch.md` + `feedback_protocol_over_shortcuts.md`:

- **Plan-doc slice (this slice, 024A)**: Opus orchestrator drafts; 3× parallel Sonnet R1 (correctness, safety_bypass, completeness); R2 fixpoint required (0 new CRIT + 0 new MAJ); merge to main when fixpoint reached + CI green.
- **Implementation slices (024B–024G)**: Opus orchestrator + Codex executor per WP-SCP-022 dispatch contract. Each adopter cascade slice is a single PR _on the SCP repo_ shipping (a) the cascade slice's DISPATCH-NOTE with a `cascade-status:` field declaring one of three close-states per §5.2 + invariant 2, (b) the invocation-log entry under `docs/reviews/WP-SCP-020/branch-protection-log.md` **only when `cascade-status` is `onboarded` or `onboarded-operator-bump`** (when `cascade-status: blocked-on-adopter-conflict`, no log entry is added — the CI asserts log-file was NOT modified per invariant 2), (c) any SCP-side ADOPT-001 / scaffolder amendments. The adopter-side wrapper PR is a separate PR _on the adopter repo_, opened in parallel; the SCP-side cascade slice references the adopter PR URL. Closes 024A R4 R4-NEW-MAJ-002 (correctness — §3 unconditional invocation-log claim contradicted invariant 2's conditional carve-out).
- **Adversarial review applies twice** for each cascade slice: once on the SCP-side cascade slice (3-lens R1+R2 fixpoint per usual), once on the adopter-side wrapper PR (single-lens correctness sufficient — the wrapper is template-derived from the scaffolder).

WP-SCP-024 inherits D-028 (DPBM) — currently no cascade slice ships visual output, so the DPBM "applies" criteria fail across the cascade. If a future cascade slice introduces a visual artefact (e.g. an estate-status dashboard), it picks up D-028's contract layer.

## 4. Threat model

| ID | Threat | Surface | Mitigation |
|---|---|---|---|
| **T-024-01** | Operator runs `enable-required-check.sh` against the wrong adopter repo, mass-mutating branch protection on a non-target repo. | `enable-required-check.sh` invocation. | D-035 + script's CI=true / GITHUB_ACTIONS=true refusal + script's `--i-understand-this-bypasses-the-gate` confirmation for `--no-enforce-admins`. Cascade slice's invocation log captures target repo+branch BEFORE invocation, surfacing typos for review. |
| **T-024-02** | Compromised operator credentials drive cascade against the cohort + bypass admin-enforce. | Operator GitHub PAT / SSH key. | The script ships from the SCP repo with SHA-pinned invocation log; a credentialed-but-unrecorded mass-mutation is forensically detectable via the absence of invocation log entries. Single-operator mode (D-031); the 2026-07-21 quarterly review covers credential rotation. |
| **T-024-03** | Adopter-side maintainer rejects the wrapper PR after cascade slice merges. | Adopter wrapper PR. | The cascade slice does not declare the adopter onboarded until the adopter wrapper PR merges + the post-bake window has elapsed cleanly. If the adopter PR is rejected, the SCP-side cascade slice is reverted (the cascade slice itself is still mergeable on the SCP repo because it ships only docs + invocation log entries; it just records "adopter rejected" as the closure status). |
| **T-024-04** | A cascade slice merges + the required-check is enabled, but the SCP federation primitive then ships a breaking change that the adopter's pinned SHA can't tolerate, blocking the adopter's merges. | SCP version bump + Renovate-driven SHA pin update. | The post-bake observation window per invariant 8 explicitly tests version-skew tolerance. VERSIONING.md (D-036) requires a one-release deprecation ramp before any breaking change. Renovate preset auto-PRs new SHAs; the adopter has a full PR cycle's warning before any breaking change. The cascade rollback procedure (invariant 7) covers the worst case. |
| **T-024-05** | Cascade slice merges with a stale adopter wrapper SHA pin (e.g. v1.0.0 instead of v1.2.0), causing the adopter to miss safety fixes that landed at v1.1.0+. | Scaffolder template SHA pin. | Scaffolder (024B) generates wrappers pinned to the **current SCP main HEAD SHA**, not a hard-coded literal. Cascade slice's R1 review verifies the generated SHA pin matches the SCP main HEAD at slice-author time. Renovate-issued bumps catch any subsequent drift. |
| **T-024-06** | Cascade onboards an adopter whose default branch isn't `main` (some adopters use `master` or `develop`); the wrapper hard-codes `branches: [main]` in its `pull_request:` trigger. | Wrapper template `pull_request: branches:` field. | Scaffolder accepts a `--default-branch` argument + emits the wrapper accordingly. Cascade slice's DISPATCH-NOTE captures the adopter's actual default branch from `gh repo view`. Lands in 024B. |
| **T-024-07** | Cascade slice declares an adopter onboarded but the post-bake window did not actually surface a Renovate bump (estate happens to be quiet). | Post-bake observation. | Invariant 8: bake EXTENDS until at least one Renovate-issued SHA pin bump has merged + observed clean. The cascade slice's closure criteria explicitly check "Renovate PR # (merged): ___, observed-clean date: ___" and refuse to declare onboarding without both fields populated. |
| **T-024-08** | The cascade aggregates SCP version-bump risk: 5 adopters all on the same SHA, a v1.x → v2.0 break affects all 5 simultaneously. | Estate-wide SHA homogeneity. | This is by design — the federation primitive is the single source of truth. The mitigation lives at the SCP-side: D-036's deprecation-ramp + Renovate's per-adopter PR cadence + adopters retain veto over any individual bump. The cascade does not _create_ this concentration risk; it makes it visible. Documented as an accepted estate-architecture posture. |
| **T-024-09** | Adopter-side CI cost spike from running the SCP federation primitive on every PR. | Adopter CI minutes. | The reusable workflow runs ~2-5 min on `ubuntu-24.04`. For most adopters this is <10% of existing CI cost. The cascade slice's adopter PR body surfaces the cost estimate; opt-out remains at adopter discretion. |
| **T-024-10** | Cascade slice surfaces an adopter-side existing-rule conflict (e.g. adopter has its own `policy-check.yml` workflow that conflicts with the SCP wrapper's name `policy-check`). | Adopter-side workflow file collision. | The wrapper's workflow `name:` is `policy-check`; the rendered job context is `policy-check / scp/policy-check`. The 020D2 required-status-check context per D-033 is `policy-check / scp/policy-check`. If the adopter has a pre-existing `policy-check` workflow, the cascade slice CLOSES on the SCP side with status `blocked-on-adopter-conflict` per invariant 10 (forward-filed TF owned by the slice author; new sub-slice opens on conflict resolution). |

## 5. Architecture

### 5.1 Adopter cohort + sequencing

The 5-cohort cascade (FLA-independent, per operator direction):

1. **PIM** (canary first cascade slice — smallest blast radius among the 5): a content-management-adjacent service. Smaller PR throughput than control-tower; cooperative team (per memory `project_estate_structure.md`). Cascade slice 024C.
2. **control-tower** (flagship): the cross-repo orchestration layer (`~/Projects/control-tower`). Highest PR throughput in the estate. Cascade slice 024D — runs after PIM bake-clean to minimise blast radius if a federation-primitive surprise emerges.
3. **mapp-doc-agent** (paired with recommender): documentation-generation service. Lower throughput. Cascade slice 024E.
4. **recommender** (paired with mapp-doc-agent): recommendation service. Lower throughput. Cascade slice 024E (same slice — paired because both are low-traffic + onboard-shape-symmetric).
5. **shopify-app** (deferred): integration layer. Cascade slice 024F. Last because shopify-app's CI surface historically carries more vendor-driven flakiness; cascading after the other 4 prove clean reduces the ambiguity-cost of any first-week red runs.

Each slice carries the **post-bake observation window** per invariant 8: ≥1 calendar week + at least one Renovate-issued SHA pin bump merged + observed clean before the slice's adopter is declared onboarded.

### 5.2 Per-adopter onboarding contract (each cascade slice satisfies)

Each cascade slice (024C–024F) ships:

1. **Adopter PR (separate repo)** — opened in parallel, contains:
   - `.github/workflows/policy-check-wrapper.yml` rendered by the scaffolder (024B), pinned to current SCP main HEAD SHA at slice-author time.
   - Optional CODEOWNERS line `.github/workflows/policy-check-wrapper.yml @<adopter-CODEOWNERS-account>` if the adopter has a CODEOWNERS file. If not, no CODEOWNERS work in cascade slice.
   - PR body: cost estimate (T-024-09) + bus-factor-1 disclosure (invariant 9) + version-skew tolerance reference (T-024-04 + D-036) + scorecard-emit opt-in note (deferred per TF-023E-002).
2. **SCP-side cascade slice PR** — opened on the SCP repo, contains:
   - `docs/reviews/WP-SCP-024/<slice-id>/DISPATCH-NOTE.md` (per WP-SCP-022 dispatch contract). **MUST declare a `cascade-status:` field** in the DISPATCH-NOTE header taking one of **three** values:
     - **`onboarded`** — success-path via Renovate; an `enable-required-check.sh` invocation occurred + the log entry is in this PR + bake observed a Renovate-issued SHA pin bump cycle clean.
     - **`onboarded-operator-bump`** — R-024-07 fallback path; an `enable-required-check.sh` invocation occurred + the log entry is in this PR + bake satisfied via operator-driven SHA pin bump (NOT Renovate); STATUS.md gains a `TF-024X-renovate-<adopter-slug>` row gating Threshold A credit (per R-024-07).
     - **`blocked-on-adopter-conflict`** — invariant-10 conflict-close path; NO invocation occurred (conflict was discovered before invocation); a `TF-024X-conflict-<adopter>` TF is filed + referenced in DISPATCH-NOTE **with meaningful content per invariant 2's regex spec** (status field ∈ {open, pending, in-progress, closed} + description starting with a non-whitespace character (`\S` anchor) + ≥20 chars total; bare-prefix stub or all-whitespace description fails CI); the PR MUST NOT modify `branch-protection-log.md` (CI script asserts absence of modification per invariant 2). Closes 024A R5 R5-NEW-MAJ-001 (completeness — §5.2 missing meaningful-content qualifier) + 024A R7 R7-NEW-MAJ-001 (correctness) + R7-NEW-MAJ-003 (completeness) — `\S` anchor + ≥20-char propagation to §5.2 paraphrase.

     The `check-invocation-log-entry.sh` CI script (024B) parses this field and applies the appropriate check-path per invariant 2.
   - `docs/reviews/WP-SCP-020/branch-protection-log.md` invocation log entry (D-035) — only when `cascade-status: onboarded` or `onboarded-operator-bump`.
   - STATUS.md row update (cascade-slice progress) — and, when `cascade-status: onboarded-operator-bump`, a `TF-024X-renovate-<adopter-slug>` row in "Tracked-forward items".
   - ADOPT-001 §<TBD by 024B> reference update, if the scaffolder template gained a clarifying sentence during this slice.
   - 3-lens R1+R2 review JSON files under `docs/reviews/WP-SCP-024/<slice-id>/`.
3. **`enable-required-check.sh` invocation** — operator-run from local machine after the adopter wrapper PR merges AND at least one green `policy-check / scp/policy-check` CI run is observed on the adopter repo (satisfying §5.4's safety check), AND BEFORE the post-bake observation window begins. Invocation captured in the branch-protection log per (2). **Steps (3) and (4) are not concurrent — (3) enables the gate that (4) observes.** Closes 024A R1 CMP-nit-001.
4. **Post-bake observation entry** — appended to STATUS.md once the bake-clean condition (invariant 8) is satisfied: Renovate PR # merged + clean-observation date.
5. **FLA pilot safety findings reviewed** — single line in DISPATCH-NOTE (template lands in 024B's D-044): `FLA pilot safety findings reviewed: [none new since <last slice's check date> | <link to finding>]`. This is **not** an FLA precondition (invariant 4 still holds); it is a check that the cascade slice author has looked at the FLA pilot state before opening the slice, so safety discoveries don't silently accumulate between slices. Closes 024A R1 MIN-SAFE-005.

### 5.3 Scaffolder helper (`SCP-073-scaffolder` = `scripts/scaffold-downstream.sh`, lands at 024B)

Generates adopter-side artefacts from a versioned template:

```text
scripts/scaffold-downstream.sh \
  --adopter-repo <owner/name> \
  --default-branch <main|master|develop> \
  --scp-sha <40-char-sha> \
  --scorecard-emit <true|false> \
  --output-dir <local-clone-path>
```

Emits:
- `<output-dir>/.github/workflows/policy-check-wrapper.yml` (the wrapper from `templates/adopter-wrapper.yml.tmpl`, with substitutions for default-branch + scp-sha + scorecard-emit).
- `<output-dir>/.github/CODEOWNERS-snippet.txt` (line for adopter to merge into existing CODEOWNERS, if present).
- `<output-dir>/CASCADE-PR-BODY.md` (PR body template covering cost estimate + bus-factor-1 disclosure + version-skew reference + scorecard-emit opt-in note).

D-044 ratifies this script's operational contract: bootstrap-only (refuses CI=true / GITHUB_ACTIONS=true per D-035 symmetry), validates `--scp-sha` against the SCP main HEAD at invocation time (warns if it's not main HEAD; refuses to emit if it's a non-existent SHA), and emits a manifest file `MANIFEST.json` listing every file emitted + its SHA256 for audit.

The scaffolder template (`templates/adopter-wrapper.yml.tmpl`) is the single source of truth for the canonical adopter wrapper shape per ADOPT-001 §12 — any future change to the wrapper shape lands in the template + propagates to all cascade slices via Renovate-driven SHA pin bumps.

### 5.4 `enable-required-check.sh` — already exists, extended at 024B

Per D-035 the script already exists at `scripts/enable-required-check.sh` from WP-SCP-020 020G. WP-SCP-024 024B adds:
- A `--restore <pre-state.json>` mode that consumes a captured before-state from a prior invocation log entry + reverses the branch-protection mutation (rollback path per invariant 7). Existing forward-mode behaviour unchanged.
- A safety check: refuses to invoke against a target repo whose `policy-check / scp/policy-check` check has not run successfully at least once on a recent PR (proving the wrapper PR landed + the federation primitive is functional in that adopter's environment). This is the "no enable before the wrapper has actually green-CI'd once" check; closes a real foot-gun where an operator could enable required-check on an adopter whose wrapper PR is still pending.

### 5.5 Cross-repo coordination (notifications)

The cascade requires coordination notifications to neighbouring estate repos. Each cascade slice files notifications per the pattern below; implementation slices reference this section for their coordination step.

| When | What | Where | Why |
|---|---|---|---|
| **At 024C kickoff** | Estate cascade start announcement — names the 5-cohort, the canary-first sequencing, the post-bake SLO, the adopter-side rollback path. **Incorporates TF-023A-002** (the deferred WP-SCP-023 v1.2.0 release notification — re-deferred from 023D → 023E and now re-deferred again to here, since adopter participation actually starts with cascade). | `~/Projects/control-tower/governance/docs/notifications/SCP-ESTATE-CASCADE-START-2026-MM-DD.md` per `reference_ct_notifications.md`. | CT governance log is the canonical cross-repo conversation log per memory. |
| **At 024C kickoff (parallel)** | Notification to **ACC** — ACC's MCP dispatcher consults SCP at plan-decompose; estate-wide branch-protection changes affecting the cascade cohort are material to ACC's operating context. | `~/Projects/acc/docs/notifications/` (path established at 024B if not present; otherwise inline reference in the CT notification covers ACC implicitly via the `reference_acc_project.md` shared-cross-repo channel). | ACC must know which adopters now require SCP green-CI before agents propose changes targeting them. |
| **At 024E kickoff** | Notification to **mapp-estate-regression** — mapp-doc-agent + recommender fall within mapp-estate-regression's tracking scope. | `~/Projects/mapp-estate-regression/docs/notifications/` if present; otherwise via the CT log entry's "Affected estates" section. | mapp-estate-regression tracks regressions across the mapp.* sub-estate; cascade-induced CI changes there are in-scope. |
| **At 024G Threshold A signed** | Closure announcement — names which 3+ adopters reached Threshold A, USER-GATE-E sign-off date, and the post-Threshold-A maintenance posture per D-046. | `~/Projects/control-tower/governance/docs/notifications/SCP-ESTATE-CASCADE-THRESHOLD-A-2026-MM-DD.md`. | Estate gets to know cascade is in steady-state maintenance mode. |

Each cascade slice's DISPATCH-NOTE has a "Cross-repo coordination" subsection that points to its specific notification file (or notes "covered by 024C kickoff notification" if not file-creating). This makes the §5.5 pattern testable: a slice whose DISPATCH-NOTE skips the subsection fails the completeness lens. Closes 024A R1 CMP-MAJ-002 + 024A R3 R3-NEW-MAJ-001 (completeness — §5.5 self-reference, was incorrectly §5.6).

### 5.6 Threshold A telemetry (slice 024G)

Threshold A criteria (D-046 ratifies — phrased identically to §8 to avoid drift; closes 024A R6 R6-NEW-MIN-001 completeness):
- ≥3 of {PIM, recommender, mapp-doc-agent, control-tower, shopify-app} have `policy-check / scp/policy-check` as a required status check on default branch (per `cascade-status: onboarded` or `onboarded-operator-bump`; `blocked-on-adopter-conflict` adopters do NOT count until a successor sub-slice onboards them per invariant 10).
- ≥1 SCP minor version-bump cycle (e.g. v1.2.0 → v1.3.0) has propagated cleanly to those adopters via Renovate (proving version-skew tolerance per invariant 8 + T-024-04).
- `docs/reviews/WP-SCP-020/branch-protection-log.md` is current (one entry per adopter that closed with `cascade-status: onboarded` or `cascade-status: onboarded-operator-bump`; conflict-close slices have NO entry per invariant 2's negative assertion).
- `docs/scorecards/opt-in-registry.yaml` may carry adopter rows by Threshold A — but only for those adopters whose repo visibility/ownership allows OIDC artefact attestation per TF-023E-001. Adopters without scorecard-emit opt-in are fully Threshold-A-counting per invariant 5.
- USER-GATE-E artefact (`docs/gates/USER-GATE-E.md`) signed by @jrnb2024.

Slice 024G ships:
- USER-GATE-E artefact scaffolded (status: `not-yet-signed`).
- A new MCP method (or extension of `consult_scorecard`) — `scp.consult_estate_status` — returning per-cohort-adopter onboarding status (cascade-pending / cascade-onboarded / scorecard-emitting / observation-clean). Read-only, signed-output, mirrors WP-SCP-021 + 023D shape. Optional — if the existing `consult_scorecard` method already covers the use-case adequately at 024G time, the new method is dropped + the criterion is met by the existing surface. Decision deferred to 024G's D-046.
- STATUS.md "At-a-glance" row promoting WP-SCP-024 to closed-when-Threshold-A-signed.

## 6. Slice plan

| Slice | Deliverable | Acceptance criteria | Tier | Dispatch contract |
|---|---|---|---|---|
| 024A (this) | `docs/plans/WP-SCP-024-estate-cascade.md` v0.1 | Plan-doc R2 fixpoint reached + merged | orchestrator | DISPATCH-NOTE + 3-lens R1 |
| 024B | 024B-core: `scripts/scaffold-downstream.sh` + `templates/adopter-wrapper.yml.tmpl` + `scripts/check-invocation-log-entry.sh` + scaffolder unit tests | Scaffolder emits a known-fixture wrapper that schema-validates against the canonical wrapper shape from ADOPT-001 §12; `check-invocation-log-entry.sh` parses DISPATCH-NOTE `cascade-status:` field and implements all four CI behaviours per invariant 2 — **fail-closed default** (absent or unrecognised value → exit non-zero); for `onboarded`: requires log entry + target match; for `onboarded-operator-bump`: requires log entry + target match + `TF-024X-renovate-<adopter-slug>` STATUS.md row matching invariant 2's **regex format spec literally** (file-agnostic; `\S` non-whitespace anchor at description start; ≥20 char total); for `blocked-on-adopter-conflict`: requires `TF-024X-conflict-<adopter>` reference (in DISPATCH-NOTE) matching the same regex spec literally AND **asserts log file was NOT modified** (closes the R3 safety bypass + R4 safety stub bypass + R6 safety regex/whitespace + file-scoping bypasses); D-044 filed. **024B-extras is deferred**: `enable-required-check.sh --restore` round-trip, ADOPT-001 §12.8 break-glass, workflow wiring, and step 7 operator demo move to the sibling slice. **024B-core is a hard predecessor for 024C; 024B-extras must also merge before 024C opens per the split decision.** | Codex executor | Per WP-SCP-022 dispatch contract |
| 024C | PIM cascade — adopter PR + SCP-side cascade slice (deliverables conditional on `cascade-status:` per §5.2 + invariant 2 — `onboarded`/`onboarded-operator-bump` paths ship invocation-log entry + post-bake observation; `blocked-on-adopter-conflict` path ships `TF-024X-conflict-<adopter>` reference instead per invariant 10 with NO log entry; closes 024A R6 R6-NEW-MAJ-001 (correctness — §6 024C/D/E/F rows now conditional on cascade-status — closes-marker per 024A R7 R7-NEW-MAJ-001 completeness)) | PIM `policy-check / scp/policy-check` required-check live; ≥1 Renovate-bump-propagation cycle merged clean; D-045 filed. *(`blocked-on-adopter-conflict` close-state acceptance defers to invariant 10's sub-slice procedure; slice still merges with its conflict-TF + DISPATCH-NOTE record.)* | Codex executor + adopter PR | Per WP-SCP-022 dispatch contract |
| 024D | control-tower cascade — adopter PR + SCP-side cascade slice (same conditional-on-`cascade-status:` pattern as 024C) | control-tower `policy-check / scp/policy-check` required-check live; ≥1 Renovate-bump-propagation cycle merged clean. *(No new D-NNN filed — D-045 at 024C ratifies the per-adopter onboarding contract pattern that this slice inherits unchanged.)* | Codex executor + adopter PR | Per WP-SCP-022 dispatch contract |
| 024E | mapp-doc-agent + recommender paired cascade — both adopter PRs + SCP-side cascade slice (each adopter independently per §5.2 cascade-status spec; both `onboarded`/`onboarded-operator-bump` paths ship 2 invocation log entries + post-bake observations on both; conflict-close path on either adopter handled per invariant 10) | Both adopters' required-checks live; ≥1 Renovate-bump-propagation cycle merged clean on each. *(No new D-NNN filed — inherits D-045's pattern.)* | Codex executor + 2 adopter PRs | Per WP-SCP-022 dispatch contract |
| 024F | shopify-app cascade — adopter PR + SCP-side cascade slice (same conditional-on-`cascade-status:` pattern as 024C) | shopify-app `policy-check / scp/policy-check` required-check live; ≥1 Renovate-bump-propagation cycle merged clean. *(No new D-NNN filed — inherits D-045's pattern.)* | Codex executor + adopter PR | Per WP-SCP-022 dispatch contract |
| 024G | Threshold A telemetry + USER-GATE-E + (optional) `scp.consult_estate_status` MCP method | ≥3 cohort adopters onboarded + bake-clean + USER-GATE-E signed; D-046 filed | orchestrator + USER-GATE | Per WP-SCP-022 USER-GATE pattern |

**024B split note.** WP-SCP-024 slice 024B was split into 024B-core + 024B-extras per [`docs/reviews/WP-SCP-024/024B-core/SCOPE-CORRECTION-2026-05-09.md`](../reviews/WP-SCP-024/024B-core/SCOPE-CORRECTION-2026-05-09.md). 024C remains gated on both halves merging, plus FUP-ACC-INSTALL-TARGET-REPO-001 closure, before cohort onboarding opens.

**Slice ordering note.** 024C → 024D → 024E → 024F is sequential by design (canary-first per §5.1). 024B is a hard predecessor for 024C–024F (the scaffolder must exist before any cascade slice can use it). 024G is the closing slice. The sequence is **NOT parallelisable across cascade slices** — each adopter's bake-clean must complete before the next adopter's cascade slice opens, so a federation-primitive bug surfaced by adopter N can be addressed before adopter N+1 onboards. This is intentional; parallelising the cohort would defeat the purpose of canary sequencing.

## 7. Risk surface

| ID | Risk | Mitigation | Owner |
|---|---|---|---|
| **R-024-01** | Adopter-side maintainer rejects the wrapper PR. | Cascade slice does not declare onboarded until adopter PR merges. Invariant 1 (consent surface). T-024-03 mitigation. | 024C–024F |
| **R-024-02** | Federation-primitive bug surfaces only at scale (e.g. only when 3+ adopters run concurrently). | Sequential cascade per §5.1 + post-bake observation per invariant 8 + each slice's bake captures one Renovate cycle. The aggregate of 5 sequential bakes covers ~5+ weeks of estate observation. | All cascade slices |
| **R-024-03** | Cascade slice onboards an adopter whose internal review shape differs from SCP's (e.g. requires 2 reviewers). | The adopter's existing `required_pull_request_reviews` is preserved by `enable-required-check.sh` per D-035 ("preserves any pre-existing `required_pull_request_reviews` shape rather than nulling it"). No cascade-side override. | 024B + each cascade slice |
| **R-024-04** | Operator runs `enable-required-check.sh` against the wrong adopter. | T-024-01 mitigation: invocation log + script `--i-understand-this-bypasses-the-gate` + script's CI-refusal. Cascade slice's R1 correctness lens verifies log target matches DISPATCH-NOTE target. | 024B + each cascade slice |
| **R-024-05** | Adopter-side CI cost spike unacceptable. | T-024-09 mitigation: cost estimate in adopter PR body. If cost is unacceptable, adopter remains opt-out; cascade slice records "adopter declined" + closes. | Each cascade slice |
| **R-024-06** | A cohort adopter has a pre-existing `policy-check` workflow conflict. | T-024-10 mitigation: cascade slice CLOSES with status `blocked-on-adopter-conflict` per invariant 10 (forward TF `TF-024X-conflict-<adopter>` owned by the slice author; new sub-slice opens on conflict resolution). **CI enforcement (invariant 2):** when `cascade-status: blocked-on-adopter-conflict`, `check-invocation-log-entry.sh` (a) verifies the `TF-024X-conflict-<adopter>` reference IS present in DISPATCH-NOTE **matching invariant 2's regex spec literally** (status field ∈ {open, pending, in-progress, closed} + description starting with a non-whitespace character (`\S` anchor) + ≥20 chars total; bare-prefix stubs and all-whitespace descriptions fail CI) AND (b) **actively asserts that `docs/reviews/WP-SCP-020/branch-protection-log.md` was NOT modified in the PR diff** (closes the R3 safety bypass — a slice declaring conflict-close while actually invoking the script must fail CI). All three checks are required; positive evidence + regex-spec format match + negative assertion. Closes 024A R4 R4-NEW-MAJ-001 (R-024-06 stale language flagged by all 3 lenses) + 024A R5 R5-NEW-MAJ-002 (completeness — meaningful-content qualifier) + 024A R7 R7-NEW-MAJ-001 (correctness) + R7-NEW-MAJ-003 (completeness) — `\S` anchor + ≥20-char propagation to R-024-06 paraphrase. | Each cascade slice |
| **R-024-07** | Renovate misses a cohort adopter (e.g. adopter has Renovate disabled). | The cascade slice surfaces this in DISPATCH-NOTE by declaring `cascade-status: onboarded-operator-bump`. Operator-driven SHA pin bump PR is acceptable as a **temporary** unblock, but the cascade slice MUST file a forward TF (`TF-024X-renovate-<adopter-slug>`) **as a STATUS.md "Tracked-forward items" row matching invariant 2's regex spec literally** (status field ∈ {open, pending, in-progress, closed} + description starting with a non-whitespace character (`\S` anchor) + ≥20 chars total — bare-prefix stubs and all-whitespace descriptions fail the CI check per invariant 2; closes 024A R4 R4-NEW-MAJ-002 safety + 024A R7 R7-NEW-MAJ-001 (correctness) + R7-NEW-MAJ-003 (completeness) — pre-R6 paraphrase swept at R-024-07). The `check-invocation-log-entry.sh` CI script verifies STATUS.md contains the matching TF row + regex-spec match when DISPATCH-NOTE declares `cascade-status: onboarded-operator-bump`. The adopter is **not credited toward Threshold A** until that TF closes + a real Renovate cycle has merged + observed clean. This distinguishes adopters that genuinely exercise automated version-skew tolerance from those that satisfy the letter of the criterion via a one-off operator action. Closes 024A R1 MAJ-SAFE-004 + 024A R2 NEW-MIN-002 + 024A R3 R3-NEW-MAJ-001 (correctness — third cascade-status value enumerated) + 024A R4 R4-NEW-MAJ-002 (safety — meaningful-content gate). T-024-04 mitigation still applies. | Each cascade slice |
| **R-024-08** | Estate-wide SHA homogeneity creates concentration risk on SCP version bumps. | T-024-08 — accepted posture. D-036 deprecation-ramp + Renovate per-adopter cadence + per-adopter veto are the existing safeguards. Invariant 7 rollback is the worst-case escape. | All cascade slices + D-036 governance |
| **R-024-09** | Bus-factor-1 exposure compounds across the cascade. | Invariant 9 — acknowledged + each adopter PR body surfaces. 2026-07-21 quarterly review covers exposure. | All cascade slices |
| **R-024-10** | Scaffolder template drift: a cascade slice ships an out-of-date wrapper. | T-024-05 mitigation: scaffolder validates `--scp-sha` against SCP main HEAD at invocation. Cascade slice's R1 review verifies generated SHA pin matches SCP main HEAD. | 024B |
| **R-024-11** | Default-branch heterogeneity (some adopters on `master` or `develop`). | T-024-06 mitigation: scaffolder accepts `--default-branch`. Cascade slice's DISPATCH-NOTE captures actual default branch via `gh repo view`. | 024B + each cascade slice |
| **R-024-12** | Post-bake observation declares clean prematurely (e.g. no Renovate bump occurred during the calendar week). | Invariant 8 + T-024-07 mitigation: bake EXTENDS until ≥1 Renovate-issued bump merged + observed clean. Cascade slice's STATUS.md row captures both fields explicitly. | Each cascade slice |
| **R-024-13** | Plan-doc commits to scaffolder shape before scaffolder is implemented. | Plan-doc is v0.1. Scaffolder's ratifying decision (D-044) lands at 024B with the implementation. Plan-doc shape may be amended at 024B if implementation surfaces a better shape. | 024A → 024B |
| **R-024-14** | Cascade-side scope creep: cascade slice tries to fix adopter-side rule conflicts in-line. | Invariant 10: cascade is purely additive. Conflicts are forward-filed TFs + the cascade slice notes the conflict; it does not fix it. | All cascade slices |
| **R-024-15** | An adopter accepted into the cascade then later wants to opt out. | Invariant 7: per-adopter rollback is single-operator-doable + <30min SLO. The adopter's `enable-required-check.sh --restore` invocation reverts branch-protection; the wrapper PR can be reverted via `git revert`. Documented per cascade slice. | Each cascade slice |

## 8. Acceptance criteria + Threshold A

**Plan-doc (slice 024A) acceptance:**
- v0.1 plan-doc lands with §1–§10 populated.
- 3-lens R1+R2 fixpoint reached (0 CRIT + 0 MAJ on a complete cycle).
- D-044 / D-045 / D-046 reserved (not assigned in this slice).

**Threshold A (slice 024G gate):**
- ≥3 of {PIM, recommender, mapp-doc-agent, control-tower, shopify-app} have `policy-check / scp/policy-check` as a required status check on default branch.
- Each adopter that reached `cascade-status: onboarded` or `cascade-status: onboarded-operator-bump` has a corresponding entry in `docs/reviews/WP-SCP-020/branch-protection-log.md` with operator + timestamp + before/after API JSON + script SHA256 + git SHA. Adopters whose cascade slice closed with `cascade-status: blocked-on-adopter-conflict` have NO log entry (per invariant 2's negative assertion) and do NOT count toward Threshold A's "≥3 of 5" criterion until a successor sub-slice onboards them per invariant 10.
- Each onboarded adopter has survived ≥1 SCP minor version-bump cycle propagated cleanly — **via Renovate** (a Renovate-issued SHA pin bump PR merged + observed clean on default branch). Adopters who satisfied the per-slice bake via an operator-driven bump (R-024-07 fallback) do NOT count toward Threshold A until a real Renovate cycle has also merged + observed clean.
- USER-GATE-E artefact (`docs/gates/USER-GATE-E.md`) signed by @jrnb2024.

**Threshold A is the binary pass/fail gate above (4 mandatory criteria).** D-046 (at 024G) decides separately whether `scp.consult_estate_status` ships as a new MCP method or rolls into existing `scp.consult_scorecard` — that decision is informational at plan-doc time and is **not** part of the Threshold A pass/fail. Closes 024A R1 CMP-MIN-002.

**Closure metric:**
WP-SCP-024 closes when Threshold A is reached. Post-Threshold-A backlog: maintenance posture for ongoing version bumps + occasional adopter-departure procedure (rare; covered by invariant 7 rollback) + opportunistic onboarding of additional non-cohort adopters as they emerge.

## 9. Decisions reserved

| ID | Slice | Topic |
|---|---|---|
| **D-044** | 024B | `scripts/scaffold-downstream.sh` operational contract — bootstrap-only / no-CI guards (D-035 symmetry); `--scp-sha` validation against SCP main HEAD; `--default-branch` flag + template substitution; `MANIFEST.json` audit emission. Adopter-template versioning (template SHA captured in scaffolder output for forensic traceability). Invocation-log convention extension: scaffolder writes a "rendered-template" log entry alongside `enable-required-check.sh`'s branch-protection log. Ratifies invariants 2 + 3 + 10 in code form. |
| **D-045** | 024C | Estate cascade ordering (canary-first §5.1) + per-adopter onboarding contract (§5.2) + post-bake observation window (≥1 calendar week + ≥1 Renovate bump cycle per invariant 8) + cascade-slice rollback procedure (§5.4 + invariant 7). The adopter-onboarding contract becomes the canonical pattern reused by 024D / 024E / 024F. Ratifies invariants 1 + 7 + 8 in slice-procedure form. |
| **D-046** | 024G | Estate-cascade Threshold A criteria + post-Threshold-A maintenance posture: recurring Renovate-driven SHA pin bumps + occasional adopter-departure procedure + non-cohort opportunistic onboarding rules. Decision on whether `scp.consult_estate_status` MCP method ships in 024G or is rolled into existing `consult_scorecard`. Ratifies §8 Threshold A in artefact form. |

**Codex-executor reservation guard.** Per the `docs/DECISIONS.md` header reservation block, Codex executors dispatched for any WP-SCP-024 implementation slice must NOT assign D-044, D-045, or D-046 to any other decision filed during that slice. The reservation pattern mirrors WP-SCP-022's D-021 reservation guard + WP-SCP-023's D-041/D-042/D-043 reservation guard.

## 10. Forward-looking + open questions

These are explicitly OPEN at v0.1 and will be revisited at the named implementation slice. **Note (closes 024A R1 CMP-MAJ-001):** earlier drafts of this section listed 10 entries, 7 of which were resolved at plan-doc level (and thus belonged in §2 invariants, §5 architecture, or §9 reservations — not §10). They have been removed; their resolutions are embodied in the plan-doc body. Below are the only **genuinely open** questions remaining at 024A merge.

1. **Renovate preset coverage** — does Renovate's auto-PR cover all 5 cohort adopters? Open at 024B; cascade slice DISPATCH-NOTEs surface per-adopter Renovate state (R-024-07).
2. **WP-SCP-025 successor** — once cascade is at Threshold A, what's next? Likely candidates: `WP-SCP-025` policy proposal queue (the deferred move #4 of the original MVCP per WP-SCP-022 §12), OR a `WP-SCP-XXX` covering second-cohort adopters (acc / fashion-labelling-agent / non-Mapp repos). Open question; not pre-committed in this plan-doc.
3. **`enable-required-check.sh --restore` test surface** — the rollback mode lands at 024B. How is it tested without actually mutating an estate repo? **Resolution path (closes 024A R1 MAJ-SAFE-003):** Q3 closes only when 024B's acceptance criterion in §6 is met — i.e. a real-repo round-trip on a throw-away test repo (NOT a dry-run mock). Until that demonstration is complete, invariant 7's <30-min rollback SLO is aspirational and 024C MUST NOT open.

---

**Status:** Draft v0.1 — awaiting plan-PR R1+R2 fixpoint + merge.
