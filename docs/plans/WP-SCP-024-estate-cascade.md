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
2. Defines a **per-adopter onboarding contract** that each cascade slice satisfies: (a) caller wrapper PR'd into the adopter repo with SCP federation primitive SHA-pinned per VERSIONING.md (D-036); (b) `scripts/enable-required-check.sh` invocation per D-035 with invocation-log entry under `docs/reviews/WP-SCP-024/branch-protection-log.md`; (c) post-bake observation window of ≥1 calendar week before cascade declares the adopter onboarded; (d) opt-in scorecard-emit added as a follow-up sub-slice once TF-023E-002 closes AND the adopter's repo visibility allows OIDC artefact attestation per TF-023E-001.
3. Defines a **canary-first sequencing** that minimises blast radius: smallest cooperative adopter first (PIM target), control-tower (high-traffic flagship) second, then mapp-doc-agent + recommender as a paired slice, then shopify-app last. The sequencing is reversible per slice — any adopter can be removed via PR to the adopter wrapper file + a parallel `enable-required-check.sh --restore` invocation (added at slice 024B).
4. Defines a **scaffolder helper** (`scripts/scaffold-downstream.sh` = `SCP-073-scaffolder` per WP-SCP-020 §11 follow-up + WP-SCP-021 follow-up `SCP-075-scaffolder-compose`) that emits the adopter-side artefacts (wrapper + CODEOWNERS template + ADOPT-001 reference) from a versioned template, so each cascade slice's adopter PR is mechanically consistent.
5. Defines a **Threshold A criterion** for WP-SCP-024: ≥3 of the 5 cohort adopters have `policy-check / scp/policy-check` required-check live + ≥1 SCP version-bump cycle (e.g. v1.2.0 → v1.3.0 minor) propagated cleanly through Renovate to those adopters.

This is **WP-SCP-024 ("estate rollout" per WP-SCP-020 §3 / "estate cascade" per WP-SCP-022 §12)** — the natural successor beyond the 5-move MVCP. WP-SCP-020 made SCP authoritative per-PR on opt-in repos; WP-SCP-021 made SCP consultable pre-code; WP-SCP-023 made SCP observable estate-wide; WP-SCP-024 **drives down the un-onboarded surface** in the named adopter cohort, turning observation into action.

This plan is a **process artefact + spec artefact** — it does not ship code in this slice. Implementation lands in 024B (scaffolder helper) → 024C..024F (per-adopter onboarding) → 024G (Threshold A telemetry + USER-GATE-E).

## 2. Invariants and what this is NOT

### Invariants

1. **Cascade is opt-in per-adopter.** Each adopter onboarded via a PR _to that adopter's repo_, reviewed by an adopter-side maintainer (or, in single-operator mode, by @jrnb2024 self-merging after the SCP-side cascade slice's plan-doc R2 fixpoint). No silent enable. No estate-wide branch-protection mass-mutation. The adopter wrapper PR is the consent surface.
2. **Required-check enablement is operator-run + invocation-logged.** `scripts/enable-required-check.sh` per D-035 runs from the operator's local environment (the script refuses CI=true / GITHUB_ACTIONS=true per D-035), with an invocation log entry under `docs/reviews/WP-SCP-024/branch-protection-log.md` that captures operator, timestamp, script SHA256, target repo+branch, before/after API JSON. An apply without the log entry is unrecorded. Cascade slices that fail to commit the invocation log are blocked from declaring the adopter onboarded.
3. **Cascade does NOT touch existing adopter content.** The wrapper is added; CODEOWNERS may gain a `.github/workflows/policy-check-wrapper.yml` line if the adopter has a CODEOWNERS file; nothing else in the adopter repo is modified by the cascade slice. Specifically: NOT the adopter's `README.md`, NOT `.github/workflows/*` other than the wrapper itself, NOT `package.json` / `pyproject.toml` / build config, NOT `.scp/rule-config.yaml` (the adopter writes that themselves once they need rule-level config).
4. **FLA-independent.** WP-SCP-020.1 (FLA pilot) runs on its own track. WP-SCP-024 cascade slices MUST NOT block on FLA pilot reaching a "stable" state, MUST NOT consume FLA-derived templates (FLA is "still maturing, don't freeze template yet" per `reference_fla_gold_standard.md` 2026-05-03), and MUST NOT cite FLA outcomes as gate-criteria for non-FLA cascade slices. If FLA pilot reaches a milestone during WP-SCP-024 work, cascade slices may opportunistically reference FLA learnings but MUST NOT add any FLA precondition.
5. **Required-check cascade is the primary deliverable; scorecard-emit opt-in is secondary.** Each cascade slice must deliver a working required-check before declaring the adopter onboarded. Scorecard-emit opt-in is a follow-up sub-slice gated on TF-023E-002 closure (+ adopter visibility/ownership per TF-023E-001). An adopter that has the required-check live but no scorecard-emit yet is fully onboarded for cascade purposes.
6. **No cross-repo write surface from automation.** All adopter-repo writes are operator-driven PRs. No cron, no GitHub Action, no MCP method writes to an adopter repo at any point during cascade. The aggregator (WP-SCP-023 023C) reads from adopter repos but never writes; same posture extends here.
7. **Per-adopter rollback is single-operator-doable.** Each cascade slice ships a rollback procedure: `enable-required-check.sh --restore <pre-state>.json` reverts branch protection to the captured before-state, and the adopter wrapper PR can be reverted via standard `git revert`. Rollback time SLO: <30 minutes from operator decision to merge-restored state. Documented per cascade slice.
8. **SCP version-skew tolerance is the cascade timing primitive.** Adopters cascade in onto a current SCP version (v1.2.0 as of 2026-05-03). The post-bake observation window (≥1 week per slice) is intentionally long enough that the next SCP minor version-bump (Renovate-driven SHA pin update) surfaces during the bake — proving version-skew tolerance against a real upgrade cycle, not just a single point-in-time onboard. A cascade slice that completes onboarding without a version-bump occurring during bake MUST extend bake until at least one Renovate-issued SHA pin bump has been merged + observed clean.
9. **Bus-factor-1 acknowledged.** Single-operator mode (D-031). The cascade operator is the same identity across SCP-self, FLA, and the 5-cohort adopters. The 2026-07-21 quarterly review (per WP-SCP-020 §8 + STATUS.md) covers exposure for the full estate post-cascade. Cascade slices MUST surface this in each adopter PR's body (so adopter-side maintainers see the same exposure framing).
10. **No backwards-incompatible adopter-side work in cascade slices.** Each adopter's onboarding PR is purely additive (a new wrapper file + optional CODEOWNERS lines). Renames, deletions, or modifications to existing adopter-side files are out of scope; if discovered necessary during cascade (e.g. adopter has a stale `policy-check.yml` from a prior unrelated experiment), that's filed as a forward TF and unblocks the cascade slice via documenting the conflict, not via fixing it.

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
- **Implementation slices (024B–024G)**: Opus orchestrator + Codex executor per WP-SCP-022 dispatch contract. Each adopter cascade slice is a single PR _on the SCP repo_ shipping (a) the cascade slice's DISPATCH-NOTE, (b) the invocation-log entry under `docs/reviews/WP-SCP-024/branch-protection-log.md`, (c) any SCP-side ADOPT-001 / scaffolder amendments. The adopter-side wrapper PR is a separate PR _on the adopter repo_, opened in parallel; the SCP-side cascade slice references the adopter PR URL.
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
| **T-024-10** | Cascade slice surfaces an adopter-side existing-rule conflict (e.g. adopter has its own `policy-check.yml` workflow that conflicts with the SCP wrapper's name `policy-check`). | Adopter-side workflow file collision. | The wrapper's workflow `name:` is `policy-check`; the rendered job context is `policy-check / scp/policy-check`. The 020D2 required-status-check context per D-033 is `policy-check / scp/policy-check`. If the adopter has a pre-existing `policy-check` workflow, the cascade slice DEFERS until the adopter's existing workflow is renamed (per invariant 10: forward-filed TF, not blocked by cascade). |

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
   - `docs/reviews/WP-SCP-024/<slice-id>/DISPATCH-NOTE.md` (per WP-SCP-022 dispatch contract).
   - `docs/reviews/WP-SCP-024/branch-protection-log.md` invocation log entry (D-035).
   - STATUS.md row update (cascade-slice progress).
   - ADOPT-001 §<TBD by 024B> reference update, if the scaffolder template gained a clarifying sentence during this slice.
   - 3-lens R1+R2 review JSON files under `docs/reviews/WP-SCP-024/<slice-id>/`.
3. **`enable-required-check.sh` invocation** — operator-run from local machine after both PRs merge + post-bake clean. Invocation captured in the branch-protection log per (2).
4. **Post-bake observation entry** — appended to STATUS.md once the bake-clean condition (invariant 8) is satisfied: Renovate PR # merged + clean-observation date.

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

### 5.5 Threshold A telemetry (slice 024G)

Threshold A criteria (D-046 ratifies):
- ≥3 of the 5 cohort adopters have `policy-check / scp/policy-check` required-check live + invocation log entries committed.
- ≥1 SCP minor version-bump cycle (e.g. v1.2.0 → v1.3.0) has propagated cleanly to those adopters via Renovate (proving version-skew tolerance per invariant 8 + T-024-04).
- `docs/reviews/WP-SCP-024/branch-protection-log.md` is current (one entry per onboarded adopter).
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
| 024B | `scripts/scaffold-downstream.sh` + `templates/adopter-wrapper.yml.tmpl` + `enable-required-check.sh --restore` mode + scaffolder unit tests | Scaffolder emits a known-fixture wrapper that schema-validates against the canonical wrapper shape from ADOPT-001 §12; `--restore` round-trip via captured before-state restores branch-protection state byte-for-byte; D-044 filed | Codex executor | Per WP-SCP-022 dispatch contract |
| 024C | PIM cascade — adopter PR + SCP-side cascade slice + invocation log + post-bake observation | PIM `policy-check / scp/policy-check` required-check live; ≥1 Renovate-bump-propagation cycle merged clean; D-045 filed | Codex executor + adopter PR | Per WP-SCP-022 dispatch contract |
| 024D | control-tower cascade — adopter PR + SCP-side cascade slice + invocation log + post-bake observation | control-tower `policy-check / scp/policy-check` required-check live; ≥1 Renovate-bump-propagation cycle merged clean | Codex executor + adopter PR | Per WP-SCP-022 dispatch contract |
| 024E | mapp-doc-agent + recommender paired cascade — both adopter PRs + SCP-side cascade slice + 2 invocation log entries + post-bake observations on both | Both adopters' required-checks live; ≥1 Renovate-bump-propagation cycle merged clean on each | Codex executor + 2 adopter PRs | Per WP-SCP-022 dispatch contract |
| 024F | shopify-app cascade — adopter PR + SCP-side cascade slice + invocation log + post-bake observation | shopify-app `policy-check / scp/policy-check` required-check live; ≥1 Renovate-bump-propagation cycle merged clean | Codex executor + adopter PR | Per WP-SCP-022 dispatch contract |
| 024G | Threshold A telemetry + USER-GATE-E + (optional) `scp.consult_estate_status` MCP method | ≥3 cohort adopters onboarded + bake-clean + USER-GATE-E signed; D-046 filed | orchestrator + USER-GATE | Per WP-SCP-022 USER-GATE pattern |

**Slice ordering note.** 024C → 024D → 024E → 024F is sequential by design (canary-first per §5.1). 024B is a hard predecessor for 024C–024F (the scaffolder must exist before any cascade slice can use it). 024G is the closing slice. The sequence is **NOT parallelisable across cascade slices** — each adopter's bake-clean must complete before the next adopter's cascade slice opens, so a federation-primitive bug surfaced by adopter N can be addressed before adopter N+1 onboards. This is intentional; parallelising the cohort would defeat the purpose of canary sequencing.

## 7. Risk surface

| ID | Risk | Mitigation | Owner |
|---|---|---|---|
| **R-024-01** | Adopter-side maintainer rejects the wrapper PR. | Cascade slice does not declare onboarded until adopter PR merges. Invariant 1 (consent surface). T-024-03 mitigation. | 024C–024F |
| **R-024-02** | Federation-primitive bug surfaces only at scale (e.g. only when 3+ adopters run concurrently). | Sequential cascade per §5.1 + post-bake observation per invariant 8 + each slice's bake captures one Renovate cycle. The aggregate of 5 sequential bakes covers ~5+ weeks of estate observation. | All cascade slices |
| **R-024-03** | Cascade slice onboards an adopter whose internal review shape differs from SCP's (e.g. requires 2 reviewers). | The adopter's existing `required_pull_request_reviews` is preserved by `enable-required-check.sh` per D-035 ("preserves any pre-existing `required_pull_request_reviews` shape rather than nulling it"). No cascade-side override. | 024B + each cascade slice |
| **R-024-04** | Operator runs `enable-required-check.sh` against the wrong adopter. | T-024-01 mitigation: invocation log + script `--i-understand-this-bypasses-the-gate` + script's CI-refusal. Cascade slice's R1 correctness lens verifies log target matches DISPATCH-NOTE target. | 024B + each cascade slice |
| **R-024-05** | Adopter-side CI cost spike unacceptable. | T-024-09 mitigation: cost estimate in adopter PR body. If cost is unacceptable, adopter remains opt-out; cascade slice records "adopter declined" + closes. | Each cascade slice |
| **R-024-06** | A cohort adopter has a pre-existing `policy-check` workflow conflict. | T-024-10 mitigation: cascade defers; forward-files TF; does not modify adopter content per invariant 10. | Each cascade slice |
| **R-024-07** | Renovate misses a cohort adopter (e.g. adopter has Renovate disabled). | The cascade slice surfaces this in DISPATCH-NOTE; without Renovate, the post-bake window is satisfied by an operator-driven SHA pin bump PR instead. T-024-04 mitigation still applies. | Each cascade slice |
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
- Each onboarded adopter has a corresponding entry in `docs/reviews/WP-SCP-024/branch-protection-log.md` with operator + timestamp + before/after API JSON + script SHA256 + git SHA.
- Each onboarded adopter has survived ≥1 Renovate-issued SHA pin bump cycle merged + observed clean on default branch.
- USER-GATE-E artefact (`docs/gates/USER-GATE-E.md`) signed by @jrnb2024.
- (Optional, D-046 to confirm) `scp.consult_estate_status` MCP method live OR existing `scp.consult_scorecard` extended to surface cascade status.

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

These are explicitly OPEN at v0.1 and will be revisited at each implementation slice:

1. **Adopter cohort completeness** — `{pim, recommender, shopify-app, mapp-doc-agent, control-tower}` is the D-035 enumeration. Are there additional in-flight estate repos that should be cohort members at 024A→024G time? Resolved at plan-doc level: **stick to the D-035 enumeration**; non-cohort opportunistic onboarding is post-Threshold-A maintenance per D-046.
2. **FLA pilot interaction** — explicitly FLA-independent per operator direction. Resolved at plan-doc level: **invariant 4**. If FLA pilot reaches a milestone during cascade work, it does not block or accelerate any cascade slice.
3. **Scorecard-emit opt-in coupling** — TF-023E-002 must close before any cascade slice can include scorecard-emit opt-in. Resolved at plan-doc level: **invariant 5** — required-check is primary deliverable, scorecard-emit is secondary follow-up. Cascade slices that complete without scorecard-emit are fully Threshold-A-counting.
4. **Renovate preset coverage** — does Renovate's auto-PR cover all 5 cohort adopters? Open at 024B; cascade slice DISPATCH-NOTEs surface per-adopter Renovate state (R-024-07).
5. **Scaffolder template extensibility** — should the template support adopter-specific overlays (e.g. organisation-specific `permissions:` blocks)? Resolved at plan-doc level: **no overlays in v1**. Adopters may amend the rendered wrapper on their side after cascade; the scaffolder template is the canonical baseline. Revisit at 024B if scaffolder design forces this.
6. **Post-Threshold-A maintenance posture** — recurring drift remediation + version-bump coordination + adopter-departure procedure. Resolved at plan-doc level: **deferred to D-046 at 024G**. Cascade itself ships with the rollback procedure (invariant 7); maintenance posture is a separate decision.
7. **WP-SCP-025 successor** — once cascade is at Threshold A, what's next? Likely candidates: `WP-SCP-025` policy proposal queue (the deferred move #4 of the original MVCP per WP-SCP-022 §12), OR a `WP-SCP-XXX` covering second-cohort adopters (acc / fashion-labelling-agent / non-Mapp repos). Open question; not pre-committed in this plan-doc.
8. **Adopter-side CODEOWNERS bus-factor-1 escalation** — D-031 escalation path triggers at 2026-07-21 quarterly review. If estate cascade onboarding spans that date, do cascade slices that close after 2026-07-21 require 2-of-N quorum on adopter PRs? Resolved at plan-doc level: **adopter-side review shape is per the adopter's repo policy**; SCP-side cascade slice still follows D-031 single-operator + 2026-07-21 escalation timeline.
9. **`enable-required-check.sh --restore` test surface** — the rollback mode lands at 024B. How is it tested without actually mutating an estate repo? Open at 024B; likely a fixture-based dry-run mode that exercises the GitHub API call shape against a local mock + a real-repo round-trip on a throw-away test repo before any cohort adopter cascade.
10. **Cascade slice CI cost** — each cascade slice's PR adds invocation-log + DISPATCH-NOTE + reviews JSON. The SCP-side CI burden is small (mostly docs). Not an open question — surfaced for transparency.

---

**Status:** Draft v0.1 — awaiting plan-PR R1+R2 fixpoint + merge.
