# D-050 — TF-PIM-001 App-credential surface (Path C ratification)

**Status:** DRAFT (operator-attended merge mandatory per Wave B Tier; D-049 precedent for ADR-class merge ceremony)
**Date filed:** 2026-05-21
**Decision date:** TBD (operator signature on merge)
**Operator:** @jrnb2024
**Closes:** TF-PIM-001 plan-doc §7 acceptance criterion 4 ("Ratifying D-NNN ADR filed") + impl WP plan-doc Wave B outcome + TF-PIM-001-ARCH-005 (sec + arch-skeptic lens R1 inherited TF item).

---

## Context

WP-SCP-024 024C (PIM canary cascade) ceremonied closed 2026-05-17. PIM PR #236 (WP-300 Workbench Assembly) opened 2026-05-19 surfaced **TF-PIM-001**: the SCP `policy-check.yml` reusable workflow's cross-repo `actions/checkout` steps cannot clone the private SCP repository from an adopter context because the default `GITHUB_TOKEN` is caller-repo-scoped only. PIM `main`'s `policy-check / scp/policy-check` required-check has been relaxed operator-attended since then.

A plan-doc (`docs/plans/TF-PIM-001-cross-repo-checkout-auth.md`) enumerated six fix paths. The operator-confirmed A/C/D primary shortlist was reviewed by a three-lens orchestrator-attended review (sec / arch-skeptic / pragmatist; Plan agents read-only with DO-NOT-EDIT mandate per `feedback_subagent_review_only_scope_must_be_enforced`). The review returned non-convergent (sec=Strong C, arch-skeptic=Strong C, pragmatist=Strong A). Operator-attended convergence 2026-05-21 ratified **Path C** on irreversibility-asymmetry grounds: Path A's "effectively irreversible" repo-public flip permanently exposes governance content + creates permanent two-repo-split + bus-factor-1 friction; Path C's risks are all recoverable.

An implementation WP plan-doc (`docs/plans/TF-PIM-001-impl-path-c-app-credential.md`) authored 2026-05-21 reached R-fixpoint MET via Option A R4 mechanical override at R2 DIMINISHING-RETURNS signal (12 R1 findings + 1 R2 finding all closed; 2/3 lenses at R-FIXPOINT-MET; remaining MIN finding folded in v0.4 as documentation precision in rollback hot-path).

This ADR ratifies the architectural commitment that the impl WP operationalises.

## Decision

SCP adopts a **GitHub App credential surface** for cross-repo `actions/checkout` authentication in the federation primitive's reusable workflow. The decision has four load-bearing properties, each captured in the ADR justification:

### 1. App identity + scope

A GitHub App named `scp-federation-primitive` is registered in the `@jrnb2024` account namespace with `repository_permissions: { contents: read }` scoped to `jrnb2024/standards-control-plane-` only. Installation scope is "Only on this account" (restricts installs to repos under `@jrnb2024`). The App carries no webhook, no other repository permissions, no organization permissions, no user permissions. Minimal surface by design.

### 2. Token acquisition flow

The reusable workflow `.github/workflows/policy-check.yml` obtains an App installation token inside SCP-controlled workflow code via a pinned third-party action (`actions/create-github-app-token@<SHA>` PRIMARY; `tibdex/github-app-token@<SHA>` FALLBACK with documented blocker). The token-exchange step reads `${{ secrets.SCP_FEDERATION_APP_ID }}` + `${{ secrets.SCP_FEDERATION_APP_PRIVATE_KEY }}` — both stored as SCP-repo-scoped Actions secrets (not org-level; not visible in repo settings UI except as `********`).

The obtained installation token is passed as the `token:` parameter on the two cross-repo `actions/checkout` steps that target the SCP repo (lines 107 + 1149-1154 of `policy-check.yml`). `persist-credentials: false` is preserved on all checkout steps. The same-repo "Checkout caller repository" step (line 92) continues to use the default `GITHUB_TOKEN` — no change.

The token-exchange step is gated by `if: github.action_ref != ''` — when the workflow is invoked LOCALLY (SCP-self dogfood; `github.action_ref` is empty), the token-exchange step skips and the existing self-call fallback (symlink `.scp-runtime` to caller working directory) engages. SCP-self dogfood path remains unchanged.

### 3. §12.7.10 invariant preservation

ADOPT-001 §12.7.10 ("NEVER use `secrets: inherit`") is **reaffirmed**, NOT inverted. The App private key is held in **SCP-repo secrets** (the workflow's own context); it is never passed in from the caller via `secrets: inherit`. The reusable workflow continues to declare no named `secrets:` block, and adopter wrappers MUST continue to invoke without `secrets: inherit`. The forward-compatibility caveat in §12.7.10 (a future SCP version that adds named secrets would retroactively pass every caller secret) never materialises under Path C.

This is the load-bearing safety property that the three-lens path-ratification review settled on as the load-bearing distinction between Path C (preserved) and Path B (inverts §12.7.10 — DROPPED-REQUIRES-OPERATOR-AUTHORISATION).

### 4. Key-custody posture under D-031

Under D-031 single-operator-mode, the App private key is held exclusively by `@jrnb2024` as the `SCP_FEDERATION_APP_PRIVATE_KEY` repo secret. Custody is bus-factor-1 — the same risk shape as every other SCP-side governance artefact, and consistent with the D-031-acknowledged posture.

Mitigations:

- **Rotation SOP at `docs/security/app-key-rotation-sop.md`** (committed in Wave A step 10 per impl WP §4). 90-day rotation cadence + event-triggered rotation (suspected compromise; account access change; D-031 quarterly review).
- **2026-07-21 quarterly D-031 review extension** (TF-PIM-001-SEC-005) — App-key custody audit added to the quarterly bus-factor-1 review agenda.
- **App installation tokens auto-rotate every 1 hour** — compromise window is bounded by token TTL not key TTL.
- **Recovery is recoverable** — if the App key is compromised, delete the App; recreate; redistribute. The blast radius is `contents: read` on one repo (recoverable). This is the canonical distinction from Path A's permanent strategic-information exposure.

### Reversal mechanism

If Path C turns out wrong in 6 months, reversal cost is bounded:

1. Delete the GitHub App (or revoke per-adopter installations)
2. Revert the "Obtain App installation token" step from `policy-check.yml` (one workflow PR)
3. SCP-self workflow returns to working state (same-repo `GITHUB_TOKEN` self-call fallback)
4. External adopters return to the pre-WP failure mode (cross-repo checkout fails; same state as 2026-05-19 PIM degradation)

Reversal is workflow-level + bounded; no adopter wrapper changes needed; estimated <1 day.

## Rationale

Three lenses independently recommended Path C over Path A:

- **sec lens (Strong C):** Path A's permanent strategic-info exposure is irreversible; Path C's risks are all recoverable. App-key custody is a well-understood operational analogue.
- **arch-skeptic lens (Strong C):** Path C is the only option that removes the failure without architecturally worse substitution. Path A trades one runtime failure for permanent strategic exposure. Path C's new failure surface (key compromise; recoverable) is smaller than the failure it removes (permanent public exposure of estate trust map).
- **pragmatist lens (Strong A):** Acknowledged but not overriding. Path A's calendar-saving and zero-per-adopter-cost case is real but does not outweigh the irreversibility-asymmetry.

The operator-attended convergence 2026-05-21 weighted sec + arch-skeptic concordance on irreversibility asymmetry as carrying the decision. The 1-2 week PIM degraded-state persistence under Path C is within the "time-limited + operator-attended + recoverable" framing operator explicitly accepted at convergence. v1.3.0 ships independently per D-049 §Sequencing item 1 (self-dogfood-only; TF-PIM-001 is the artefact-gate on adopter-side consumption, not on v1.3.0 itself).

The full 6-path enumeration + per-path Pareto-frontier analysis + 3-lens evidence files are preserved at `docs/plans/TF-PIM-001-cross-repo-checkout-auth.md` §5 + `docs/reviews/TF-PIM-001/shortlist-A-C-D/`.

## Justification

Five load-bearing properties hold under this decision:

1. **The §12.7.10 invariant is preserved.** No `secrets: inherit` is introduced anywhere. Adopter named secrets remain opaque to SCP code regardless of any future SCP version's added named-secrets declarations. The forward-compatibility caveat never materialises.

2. **The federation primitive's invariants 1-5** (per WP-SCP-020 §3 + TF-PIM-001 plan-doc §4) are preserved or relaxed-with-compensation:
   - Invariant 1 (Adopter token does not leave adopter context) — preserved (no caller token forwarded)
   - Invariant 2 (SCP-controlled workflow code never sees adopter named secrets) — **preserved** (this is the primary Path C claim over Path B)
   - Invariant 3 (Trust roots in tag-protected SHA pins) — preserved with one nuance (App's GitHub-side scope config is out-of-band; compensated by limited scope + adopter-visible install)
   - Invariant 4 (Policy bundle integrity verifiable) — preserved (lockfile + SHA256 unchanged)
   - Invariant 5 (Annotation surface fixed) — preserved (no new SCP-EXXX codes)

3. **The reversal mechanism is bounded + documented.** Delete App + revert workflow PR; <1 day operator-attended; no adopter wrapper changes; SCP-self continues green during reversal.

4. **The custody risk is acknowledged + mitigated.** D-031 single-operator-mode bus-factor-1; rotation SOP authored; 2026-07-21 quarterly review extension; App-installation tokens auto-rotate every 1 hour.

5. **The cohort-of-5 onboarding ceremony is documented + replicable.** ADOPT-001 §12.7.16 (NEW; Wave C) documents the per-adopter App-install ceremony; all 5 current cohort adopters are in `@jrnb2024` namespace where operator self-installs; future multi-org adopter coordination tracked-forward as TF-PIM-001-ARCH-004.

## Cross-references

- `docs/plans/TF-PIM-001-cross-repo-checkout-auth.md` — parent plan-doc (CLOSED-WITH-RATIFIED-PATH 2026-05-21 at PR #133 merge)
- `docs/plans/TF-PIM-001-impl-path-c-app-credential.md` — impl WP plan-doc (R-FIXPOINT MET at v0.4; PR #134 merged at `89e645c`)
- `docs/reviews/TF-PIM-001/shortlist-A-C-D/` — path-ratification 3-lens evidence + synthesis
- `docs/reviews/TF-PIM-001/impl-WP-R-cycle/{R1,R2}/` — impl WP R-cycle evidence + R-fixpoint synthesis
- `docs/adoption/ADOPT-001-project-onboarding.md` §12.7 (federation primitive adopter integration; §12.7.10 NEVER use `secrets: inherit`; §12.7.16 NEW App-install ceremony per Wave C; §12.7.5 amend per Wave C; §12.7.13 amend per Wave C)
- `.github/workflows/policy-check.yml` — modified at Wave D (token-exchange step + `token:` parameter on cross-repo checkouts)
- `docs/security/app-key-rotation-sop.md` — Wave A step 10 deliverable; rotation SOP per TF-PIM-001-SEC-001 + ARCH-001
- `docs/DECISIONS.md` rows D-030 (tag-protection), D-031 (single-operator-mode), D-049 (DPBM design-system role + §Sequencing item 2 artefact-gate)

## Tracked-forward items (inherited from impl WP §3.3)

5 items in-scope across Waves A-G:

- TF-PIM-001-SEC-001 — App-credential rotation SOP (Wave A step 10 + Wave C)
- TF-PIM-001-SEC-002 — ADOPT-001 §12.7.5 de-adoption update (Wave C)
- TF-PIM-001-SEC-003 — `generate-app-token` action SHA-pin + supply-chain registration (Wave D + Wave C §12.7.13)
- TF-PIM-001-SEC-004 — Per-adopter App-install access verification (Wave G — PIM canary scope)
- TF-PIM-001-ARCH-002 — Selftest harness coverage for App token-exchange failure (Wave E; mock-based for v0.1)
- TF-PIM-001-ARCH-003 — ADOPT-001 §12.7 App-install ceremony documentation (Wave C)

2 items TF-carried (out-of-scope this WP):

- TF-PIM-001-SEC-005 — 2026-07-21 quarterly D-031 review extension (calendar gate)
- TF-PIM-001-ARCH-004 — Multi-org adopter App-install coordination (first non-@jrnb2024 adopter)

## Sequencing

D-050 ratifies the architectural commitment. The implementation sequence is the 8-wave structure documented in `docs/plans/TF-PIM-001-impl-path-c-app-credential.md` §4:

1. **Wave A** — GitHub App authoring (operator-attended GitHub UI ceremony + 4-step `.pem` discipline + rotation SOP authoring)
2. **Wave B** — This ADR drafting + operator-attended merge
3. **Wave C** — ADOPT-001 §12.7 updates (this PR's same commit as Wave B authoring)
4. **Wave D** — Reusable workflow change (Tier 2 Codex dispatch; operator-attended fire)
5. **Wave E** — Workflow-selftest harness coverage (same-PR-coupled with Wave D)
6. **Wave F** — SCP-self dogfood verification
7. **Wave G** — External-adopter cross-repo verification (PIM canary)
8. **Wave H** — PIM main required-check restoration + TF-PIM-001 closure

D-050 ratification gates Waves D onward (the workflow change implements what D-050 architecturally commits). Wave A operator-attended ceremony is independent of D-050 (App authoring can happen before or after ratification; per impl WP §8.1 recommended batching, Wave A + Wave B run in the same operator session if ADR is pre-drafted — this PR delivers the pre-draft).

## Status flip ceremony

Per established estate pattern (D-047, D-048, D-049): file lands as DRAFT; flips to ACCEPTED at the next status-bookkeeping commit AFTER operator-attended merge. Operator-attended merge means explicit `gh pr merge` by operator OR explicit paste-back authorisation to orchestrator. Mechanical auto-merge NOT authorised for this PR.
