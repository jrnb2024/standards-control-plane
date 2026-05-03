# 023E — fix-round-3 audit (CI environmental constraint)

**Date:** 2026-05-03
**Branch:** `feature/wp-scp-023-023e-threshold`
**Pre-fix-round-3 HEAD:** `e8541bc`

## Trigger

R2 fixpoint was reached at `74b32b0` (R1 inline-fixes + R2 verification).
PR #101 was opened against main expecting clean CI. Three runs hit
`startup_failure` with **zero check-runs created**:

- `25285463500` — head `74b32b0` — startup_failure
- `25285507139` — head `3caef56` (empty re-run trigger commit) — startup_failure
- (rerun via `gh run rerun` had no effect)

The empty `latest_check_runs_count: 0` and absence of any logs/jobs
distinguished this from a normal in-job failure — GitHub Actions was
rejecting the workflow at startup-validation time.

## Fix-round-3 root-cause analysis

**Symptom 1 — startup_failure with no logs.** The wrapper's
caller-side `permissions:` ceiling was `contents: read` + `statuses:
write` only. The called `policy-check.yml@5ff2acd7` declares a
JOB-SCOPED `attest-scorecard` job with `attestations: write` + `id-token:
write`. When the wrapper sets `scorecard-emit: true`, GitHub schedules
that job and validates its permissions against the caller's ceiling.
**Reusable workflows cannot escalate above the caller's ceiling**, so
the workflow is rejected at startup.

This was masked on PRs #98/99/100 (023B/C/D) because none of those
wrappers set `scorecard-emit: true` — `attest-scorecard` was always
skipped by its `if: inputs.scorecard-emit` guard, and GitHub apparently
does not validate permissions for jobs whose `if:` short-circuits at
startup. PR #101 was the first run with `scorecard-emit: true` actually
set, exposing the gap.

**First fix attempt (commit `e8541bc`).** Added `attestations: write` +
`id-token: write` to the wrapper. The startup_failure cleared — the
new run reached the actual job execution path.

**Symptom 2 — attestation step fails at runtime with explicit error.**
The `actions/attest-build-provenance@v4.1.0` step fails:

> `Failed to persist attestation: Feature not available for user-owned
> private repositories. To enable this feature, please make this
> repository public.`
> https://docs.github.com/rest/repos/attestations#create-an-attestation

This is a hard GitHub product constraint. `standards-control-plane-`
is owned by user `jrnb2024` (not by an organisation) AND is private —
the exact intersection that blocks artifact attestations.

## Why R1/R2 missed it

R1 + R2 reviewed the architectural design:

- 023B R1 MAJ-SAFE-001 caught the workflow-level OIDC threat surface
  → JOB-SCOPED `attestations: write` + `id-token: write` on
  `attest-scorecard`. Correct fix.
- R1 + R2 verified CODEOWNERS coverage, schema validation, OIDC
  verification logic, MCP method shape, etc.

But R1 + R2 did NOT simulate the SCP-self-as-first-adopter caller
boot-path. Specifically:

1. They did not exercise "what is the effective permission set when
   `scorecard-emit: true` is set on the SCP-self wrapper?"
2. They did not check the GitHub product matrix for
   `actions/attest-build-provenance` on user-owned private repos.

Both are environmental rather than code-level concerns — visible only
when the workflow actually runs in this repo's specific
visibility/ownership context. **Lesson:** when adversarial review
covers OIDC + attestation + reusable-workflow permissions, the
reviewer must also consult the runtime product constraints (GitHub
docs page on attestation availability) — not just the code shape.

## Second iteration of fix-round-3

After reverting `with: scorecard-emit: true` + the extra wrapper
permissions (commit `4b52224`), CI **still hit startup_failure** on
the new run `25285748233`. Investigation: canary PRs #59/#67/#81 with
their old wrapper pin at `@41a5299` (v1.0.0) all show `SUCCESS` on
their last CI runs — confirming v1.0.0 of the called workflow is fine.
The regression is the SHA bump itself, not the `scorecard-emit` input.

**Diagnosis refined:** GitHub Actions validates declared permissions
on **all** jobs in a called reusable workflow at workflow-resolution
/ startup time, BEFORE evaluating any job-level `if:` conditions. The
`attest-scorecard` job in `policy-check.yml@5ff2acd` declares
`attestations: write` + `id-token: write`, which is above the
wrapper's `contents: read` + `statuses: write` ceiling. Even with
`scorecard-emit: false` (the default) — which would skip the job at
runtime — the static permission validation fires and rejects the
workflow with `startup_failure`. PRs #98/#99/#100 didn't trip this
because their wrapper still pinned at `@41a5299` (pre-attest-
scorecard).

**Second revert:** wrapper SHA pin rolled back to `@41a5299`
(v1.0.0). The bump is forward-filed as TF-023E-002.

**TF-023E-002:** restructure `policy-check.yml` so `attest-scorecard`
lives in a separate top-level workflow file (called workflows can't
declare per-job permissions above caller ceiling, period — the `if:`
short-circuit doesn't help). Once that ships, wrappers can bump
without granting OIDC permissions. Until then, the SCP-self wrapper
stays at v1.0.0.

## Fix-round-3 disposition

**Decision: defer the SCP-self opt-in. Do NOT weaken the trust model
with a self-exemption.** D-042 requires every emit to carry an OIDC
attestation verifiable via `gh attestation verify --signer-workflow`.
A self-exemption would create an asymmetry where the SCP repo's row is
trusted by convention while every adopter's row is trusted by
cryptographic proof. The aggregator already handles
`verification_failure` correctly; SCP-self perpetually as
`verification_failure` was rejected on the same trust-asymmetry
grounds.

### Reverted at fix-round-3

1. `policy-check-wrapper.yml`: removed `with: scorecard-emit: true` +
   the `attestations: write` + `id-token: write` permissions (least-
   privilege restored). Then ALSO rolled the SHA pin back to
   `@41a5299` (v1.0.0) after the second startup_failure proved the
   bump alone is the regression.
2. `docs/scorecards/opt-in-registry.yaml`: removed the SCP-self
   adopter entry; `adopters: []` for now.
3. STATUS.md row 5: rewritten to reflect the deferral.
4. USER-GATE-D criterion (i): SCP-self carve-out — satisfied set is
   now `FLA + ≥2 of {PIM / recommender / mapp-doc-agent / control-tower}`
   (was `SCP-self + FLA + ≥1 of {PIM / recommender / mapp-doc-agent /
   control-tower}`).

### Forward-filed

**TF-023E-001** (medium priority): SCP-self scorecard-emit opt-in is
deferred until `standards-control-plane-` becomes public OR transfers
to an org. Closure path: (a) make repo public, OR (b) transfer to an
org. Filed in STATUS.md "Tracked-forward items from 023D / 023E".

**TF-023E-002** (medium priority): wrapper SHA pin stuck at v1.0.0
(`@41a5299`) because GitHub validates over-scoped called-workflow job
permissions at startup time regardless of `if:`. Closure path: (a)
restructure `policy-check.yml` so `attest-scorecard` is a separate
top-level workflow, OR (b) close TF-023E-001 first then universally
grant the OIDC permissions at the wrapper level. (a) preserves least-
privilege for opt-out adopters and is recommended.

### Documentation propagation

- `docs/adoption/ADOPT-001-project-onboarding.md` §12.7.15 step 2
  callout: explicit "repo visibility / ownership prerequisite"
  paragraph naming TF-023E-001 + the GitHub error string.
- `docs/gates/USER-GATE-D.md` criteria (i) + (viii): TF-023E-001
  named.

## What remains intact at fix-round-3

The slice still delivers:

1. USER-GATE-D scaffolding (8-criterion checklist, status:
   `not-yet-signed`).
2. TF-023D-003 closure (`_resolve_audit_key_id` helper + key-ring
   fallback).
3. TF-023A-002 closure (cross-repo notification at
   `~/Projects/control-tower/governance/docs/notifications/SCP-SCORECARD-SURFACE-LIVE-2026-05-03.md`).
4. CODEOWNERS expansion (`docs/gates/**` + `docs/reviews/**` per 023E
   R1 MAJ-SAFE-001).
5. Wrapper SHA pin **stays** at `@41a5299` (v1.0.0) — the bump to
   `5ff2acd...` was reverted (TF-023E-002). SCP self-tests track v1.0.0
   of the federation primitive; the v1.2.0 dogfood is blocked on
   TF-023E-002 closing.
6. ADOPT-001 §12.7.15 — adopter onboarding workflow (with the new
   visibility/ownership prerequisite).

## Lessons added to corpus

1. **Adversarial review must cover environmental constraints.** When
   the design touches OIDC, artifact attestation, or reusable-workflow
   permissions, R1 reviewers should explicitly check GitHub's product
   matrix (private vs public, user-owned vs org-owned). This is now a
   recommended add to the safety_bypass lens prompt.

2. **`startup_failure` with no logs almost always means caller-vs-
   called permission ceiling violation.** Documented for future
   debugging.

3. **Deferring self-dogfood is preferable to weakening the trust
   model.** When environmental constraints prevent the canonical-
   adopter pattern from applying to SCP-self, defer; do not exempt.

## R3 verdict

**Slice 023E ships as scaffolding-only.** Threshold A criteria are
in place + first real adopter wires up via the same opt-in path
(now documented with the visibility/ownership prerequisite). The 1-
adopter test corpus role originally assigned to SCP-self transfers to
the first public/org-owned adopter (likely FLA per the FLA-mandatory
criterion).

CI is expected green after the second iteration of fix-round-3
(wrapper SHA pin rolled back to `@41a5299` v1.0.0). The wrapper is
now at the same shape as the canary PRs #59/#67/#81 which all show
`SUCCESS` on their last CI runs, providing strong baseline that this
shape works.
