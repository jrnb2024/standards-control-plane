# SCOPE CORRECTION 2 — operator-decided split of 024B-extras into 024B-extras-1 + 024B-extras-2

**Date:** 2026-05-11
**Decided by:** @jrnb2024 (operator)
**Trigger:** R-cycle convergence trajectory plateaued at ~5 MAJ for 5 consecutive rounds (R12 4 / R13 4 / R14 3 / R15 8 / R16 6) without hitting criterion (b) (≤2 MAJ + 0 CRIT + >50% polish-class). 16 R-rounds + 16 fix-rounds + 38 hours of session wall-time. Each round closing 4-7 MAJ; next round finding 4-8 latent depth defects in the existing code (mostly NOT just-added-code regressions).

## Precedent

This is the second operator-decided split of WP-SCP-024 slice 024B. The first split (2026-05-09) carved 024B into 024B-core (scaffolder + template + CI script CLI + tests; merged at 249aa9f) + 024B-extras (this slice; --restore + ADOPT-001 §12.8 + workflow + extras tests). The first SCOPE CORRECTION is recorded at `docs/reviews/WP-SCP-024/024B-core/SCOPE-CORRECTION-2026-05-09.md`.

## Empirical justification

Reviewing the R-trajectory and findings:

| Round | CRIT | MAJ unique | Composition |
|---|---|---|---|
| R7 | 0 | 4 | initial signal |
| R8 | 0 | 4 | converging |
| R9 | 1 | 3 | mock-masked URL singular→plural CRIT |
| R10 | 1 | 7 | mock-masked workflow `pull-requests:` CRIT + 6 MAJ (advisory-only since fix-round-1) |
| R11 | 0 | 7 | 2 fix-round-10 regressions + 2 latents + 1 conflict + 2 completeness gaps |
| R12 | 0 | 4 | drop — convergence resumed (1 fix-round-10 surface) |
| R13 | 0 | 4 | autonomous-agent dispatch (enforce_admins string-only + dead RESTORE_CAUTION_LINES + put_fail test + wrapper base64) |
| R14 | 0 | 3 | small fix-round-14 surface gaps + 1 fix-11 regression |
| R15 | 0 | 8 | 3 latent depth-finds (required_signatures validator, transform exclusion, mutex test) + 4 fix-round-14 surface |
| R16 | 0 | 6 | 5 latent depth-finds (verify-phase order, ACK_NO_GATE2 unconditional, validator gaps, verify GET, working-tree test) + 1 fix-round-14 surface |

**Pattern:** the slice has functional convergence (0 CRIT for 7 consecutive rounds; governance lens APPROVED_WITH_FINDINGS for 4 consecutive rounds) but the R-cycle keeps surfacing latent defects in the **depth-defense surface** added across fix-rounds 10-14:

1. **Gate 3 wrapper-pin verification surface** (fix-round-10 SAFE-MAJ-003, fix-round-11 SB-004, fix-round-14 CORR-001, fix-round-16 R16-CORR-002): `--expected-wrapper-sha` + tag-validation + wrapper-pin verification + `--i-understand-no-gate-2-verification` + `--i-understand-wrapper-inaccessible` + conditional CAUTION/sleep + annotated-tag dereferencing
2. **Canonical-context guard** (fix-round-14 SB-001, fix-round-15 SB-002): `--i-understand-restore-replaces-required-check-context` + jq element-wise canonical-context check
3. **Set-equality verify phase** (fix-round-16 R16-CORR-001): replace comma-substring with jq sorted-set comparison
4. **Transform inclusion list** (fix-round-15 SB-003): allowed-keys for nested fields under required_status_checks / required_pull_request_reviews / restrictions

These surfaces interact: each fix-round on one surface tends to surface latent edge-cases in another. R15 saw a regression from fix-round-14 (SB-002 comma-substring); R16 saw a regression from fix-round-14 (R16-CORR-002 unconditional CAUTION); each fix introduced 1-2 new test gaps in just-added code.

**Diagnosis:** the depth-defense surface is structurally separable from the core --restore + break-glass + workflow contract. Carving it off into a sibling slice unblocks 024C cascade onboarding (which only needs the core contract).

## Split contract

### 024B-extras-1 (this slice, post-split — what merges before 024C)

Stays:
- `scripts/enable-required-check.sh --restore` core mode: GET→PUT transform, APPLY_FAIL wrap, required_signatures sub-resource handling, pre-restore state capture
- 5 of 6 posture-degradation acknowledgement flags: `--i-understand-restore-removes-admin-enforcement`, `--i-understand-restore-removes-required-checks`, `--i-understand-restore-disables-required-signatures`, `--i-understand-restore-re-enables-force-pushes`, `--i-understand-restore-re-enables-deletions`
- Forward-mode safety check: path-pinned workflow lookup (`.github/workflows/policy-check-wrapper.yml`), no `&branch=` filter on workflow-runs API, URL-encoded date filter (`?created=%3E%3D`), `--paginate` for tag list, `--i-understand-this-repo-has-no-prior-green-ci` for cold-start adopters
- `docs/adoption/ADOPT-001-project-onboarding.md` §12.8 break-glass procedure (3-gate playbook with manual Gate 3 verification — operator manually confirms wrapper pins to release-tag SHA; no script-side verification)
- `.github/workflows/check-invocation-log-entry.yml` (CI workflow with `pull-requests: read` permission + cohort-precedence short-circuit + tooling-slice + log-modified guard)
- D-047 ratification of the core contract
- `STATUS.md` chain entry + `TF-024B-STEP7-DEMO-001` (operator-interactive demo, merge-blocking AC)
- `TF-024B-REQCHECK-ENABLE-001` (closure procedure: STATUS.md chain entry only; no branch-protection-log.md modification per fix-round-11 procedure)
- Core tests for the above

Moves to 024B-extras-2:
- `--expected-wrapper-sha SHA` flag + `validate_expected_wrapper_sha_against_tags()` function + annotated-tag dereferencing
- `--i-understand-no-gate-2-verification` flag + conditional CAUTION/sleep emission + `GATE2_CAUTION_LINE`
- `--i-understand-wrapper-inaccessible` flag + wrapper content fetch via `gh api contents` + grep-anchored uses: match + `WRAPPER_INACCESSIBLE_CAUTION_LINE`
- 6th posture-degradation flag: `--i-understand-restore-replaces-required-check-context` + canonical-context jq element-wise check + `RESTORE_TARGET_CHECKS_CONTEXTS`-related logic
- Set-equality verify phase comparison (jq sorted comparison for required_status_checks.contexts)
- Transform inclusion list for nested fields (`ALLOWED_REQUIRED_STATUS_CHECKS_KEYS` / `ALLOWED_REQUIRED_PR_REVIEWS_KEYS` / `ALLOWED_RESTRICTIONS_KEYS`)
- `prior_restore_evidence_present()`'s role in gating `--expected-wrapper-sha` (the function stays for working-tree Gate-1 detection; just its Gate 3 enforcement role moves)
- All tests for the above
- D-048 (NEW) ratification of the depth-defense contract

Plus minor:
- ADOPT-001 §12.8 Gate 3 in 024B-extras-1 says "operator manually verifies wrapper pins to release-tag SHA via `gh repo view --json defaultBranchRef` + manual SHA comparison"; in 024B-extras-2 this is replaced with the automated `--expected-wrapper-sha` machinery.

## Why this split is incremental delivery, not descope

Both halves still ship. 024C cascade onboarding does NOT require the depth-defense surface — invariant 7's <30-min rollback SLO is satisfied by the core `--restore` mode (which works correctly per all R-cycles). The depth-defense surface is added safety for the rare break-glass cycle; deferring it by ≤1 sprint does not affect cascade onboarding.

Per `feedback_split_not_descope.md`:
> When recursive adversarial review on a slice keeps finding new MAJ-class issues at the margin — and each fix-round introduces 2-3 new defects in the just-added code — the trajectory is asymptotic, not converging. Diminishing-returns exit fires when net rate approaches *zero*, not when it's slow-but-positive.

Last 5 rounds net rate: closed ~25 MAJ; introduced ~25 in newly-found latents. Net rate ~0. **Asymptotic.**

Splitting the surface (carving the depth-defense layer off) reduces the review surface to a degree where the smaller half should hit criterion (b) within 1-2 R-cycles.

## Branch state at split time

- `feature/wp-scp-024-024b-extras` (this branch): currently at fd62641 (fix-round-16 merged). Will become 024B-extras-1 after surgical extraction of the depth-defense surface.
- `feature/wp-scp-024-024b-extras-2`: branched from fd62641 (preserves all current work including depth-defense). Will be the basis for the sibling slice.

## Plan-doc §6 update

Plan-doc §6 024B split note (already cites 024B-core + 024B-extras) extends to mention 024B-extras-2 as a successor slice that ratifies the depth-defense surface (D-048 reserved). 024C precondition is updated to gate on 024B-extras-1 merging + FUP-ACC-INSTALL-TARGET-REPO-001 closure (no longer gated on 024B-extras-2).

## Lessons captured

- **Mock-masking pattern** (R9 + R10 CRITs): test harness using fake `gh` doesn't enforce GitHub's permission model OR URL contract. Adversarial review caught both by reading API endpoint citations, not by code execution. Recommendation: future federation-primitive slices should add a real-API smoke test step (one read-only call under workflow's own permissions block) so external-API contract drift is detectable mid-cycle. Memory: `feedback_fill_rcycle_wait_windows.md` extension recommended.
- **Asymptotic-trajectory detection threshold**: 5 consecutive rounds without dropping below 4 MAJ, with most new findings being latent depth-finds rather than just-added-code regressions, is a strong split signal. The 50%-regression-rate threshold in `feedback_split_not_descope.md` is a different (earlier) signal; this is an additional signal for slices that survive that threshold but still oscillate.
- **Depth-defense surface separability**: when a slice contains a feature whose verification adds 3+ layers of operator-acknowledgement flags + corresponding CAUTION emission paths + cross-cutting tests, that feature is a candidate for its own sibling slice from inception. Future slices should plan-doc this explicitly rather than discover it via R-cycle.

## References

- Plan-doc `docs/plans/WP-SCP-024-estate-cascade.md` §6 (024B-extras-1 + 024B-extras-2 update)
- Memory `feedback_split_not_descope.md` (split-discipline)
- First split: `docs/reviews/WP-SCP-024/024B-core/SCOPE-CORRECTION-2026-05-09.md`
- DISPATCH-NOTE update: `docs/reviews/WP-SCP-024/024B-extras/DISPATCH-NOTE.md` post-split
- Future DISPATCH-NOTE: `docs/reviews/WP-SCP-024/024B-extras-2/DISPATCH-NOTE.md` (when slice opens)
