# DISPATCH-NOTE — WP-SCP-024 slice 024B-extras-2 (depth-defense surface) — SKELETON

**Date:** 2026-05-12
**Branch:** `feature/wp-scp-024-024b-extras-2-v2` (off origin/main at `d7b16d0`, branched fresh post-extras-1-merge). The original `feature/wp-scp-024-024b-extras-2` branch at fd62641 preserves pre-carve R7-R16 work as audit-trail reference.
**Predecessor:** WP-SCP-024 024B-extras-1 merged at `d7b16d0` on 2026-05-12 (PR #113).
**Decision filed:** D-048 (depth-defense surface ratification).

`cascade-status: not applicable` — this slice ships depth-defense additions; not a cohort cascade slice.
`slice-type: tooling`

## Backstory

WP-SCP-024 024B-extras was operator-decided split on 2026-05-11 (`docs/reviews/WP-SCP-024/024B-extras/SCOPE-CORRECTION-2-2026-05-11.md`) after 16 R-cycles + 38 hours of session wall-time without reaching criterion (b) fixpoint. The R-trajectory plateaued at ~5 MAJ per round (R12 4 / R13 4 / R14 3 / R15 8 / R16 6) with most findings being latent depth-defects in the depth-defense surface, not just-added-code regressions.

The depth-defense surface was extracted into this slice (024B-extras-2). The core --restore + ADOPT-001 §12.8 (manual Gate 3) + workflow CI gate shipped in 024B-extras-1 — that's what 024C cascade needs. This slice adds the automated Gate 3 verification + canonical-context guard + set-equality verify phase + transform inclusion-list defense + annotated-tag dereferencing.

This branch (`feature/wp-scp-024-024b-extras-2`) was created at the 024B-extras carve point (fd62641, post-fix-round-16) so all R7-R16 work is preserved. Re-applying it on top of merged 024B-extras-1 needs a rebase or cherry-pick of the depth-defense diff.

## Why

The depth-defense surface is real defensive value:
1. **Gate 3 wrapper-pin verification** prevents an operator from re-enabling required-check after a break-glass cycle when the adopter wrapper file is still pinned to a broken SHA. Manual procedure (in 024B-extras-1 §12.8) is human-error-prone; automating it adds a real safety property.
2. **Canonical-context guard** (`--i-understand-restore-replaces-required-check-context`) prevents an attacker-modified pre-state JSON from silently replacing the policy gate with attacker-controlled context. Real safety property.
3. **Set-equality verify phase** prevents spurious FAIL=1 + exit 1 on legitimate restore when GitHub returns contexts in a different order than the pre-state JSON. Real reliability property.
4. **Transform inclusion list** prevents unknown nested fields from passing through to PUT body. Defense-in-depth.
5. **Annotated-tag dereferencing** enables Gate 3 SHA validation regardless of whether SCP-self uses lightweight or annotated tags.

These are all valuable. They just don't gate 024C cascade onboarding — invariant 7's <30-min rollback SLO is satisfied by the core --restore mode in 024B-extras-1.

## Scope (in)

| Deliverable | Path | Notes |
|---|---|---|
| `--expected-wrapper-sha SHA` flag + `validate_expected_wrapper_sha_against_tags()` | `scripts/enable-required-check.sh` | Re-add the function with annotated-tag dereferencing (gh api git/refs/tags/* via --paginate + per-annotated-tag git/tags/<sha> dereference). Validates supplied SHA against release-tag SHAs. |
| `--i-understand-no-gate-2-verification` flag + conditional CAUTION/sleep | `scripts/enable-required-check.sh` | Re-add ACK_NO_GATE2_VERIFICATION + GATE2_CAUTION_LINE. CAUTION + 5s sleep fires ONLY when prior_restore_evidence_present (R16-CORR-002 closure). |
| `--i-understand-wrapper-inaccessible` flag + wrapper-pin verification | `scripts/enable-required-check.sh` | Re-add ACK_WRAPPER_INACCESSIBLE + WRAPPER_INACCESSIBLE_CAUTION_LINE + gh api contents grep-anchored uses: match. |
| `--i-understand-restore-replaces-required-check-context` flag + canonical-context guard | `scripts/enable-required-check.sh` | Re-add ACK_RESTORE_REPLACES_REQUIRED_CHECK_CONTEXT + jq element-wise canonical-context check. |
| Set-equality verify phase | `scripts/enable-required-check.sh` | Replace comma-substring grep -F with jq `--argjson expected_contexts ... sort == sort` comparison. |
| Transform inclusion list | `scripts/enable-required-check.sh` | Add ALLOWED_REQUIRED_STATUS_CHECKS_KEYS / ALLOWED_REQUIRED_PR_REVIEWS_KEYS / ALLOWED_RESTRICTIONS_KEYS to transform(). |
| ADOPT-001 §12.8 Gate 3 update | `docs/adoption/ADOPT-001-project-onboarding.md` | Replace the manual Gate 3 from 024B-extras-1 with automated --expected-wrapper-sha procedure. Re-add Post-break-glass permanence callout. |
| D-048 row | `docs/DECISIONS.md` | Ratify depth-defense surface. Includes trust-model: Gate 3 SHA-pin is mandatory + permanence applies post-break-glass. |
| All extracted tests | `tests/check_invocation_log/test_check_invocation_log_entry.sh` | Re-add tests for: tag validation, wrapper-pin verification, canonical-context guard, set-equality verify, transform inclusion list, mutex tests, annotated-tag dereference. |
| Mutex checks | `scripts/enable-required-check.sh` | --restore + --expected-wrapper-sha + --i-understand-no-gate-2-verification + --i-understand-wrapper-inaccessible incompatibilities. |
| 6th posture-degradation flag in VERSIONING.md + branch-protection helper list | `policies/VERSIONING.md` | Re-add --i-understand-restore-replaces-required-check-context + other 3 flags. |

## Scope (out)

- 024C PIM cascade onboarding (unblocked when 024B-extras-1 merges).
- TF-023E-002 closure.
- D-021 May-31 atomic-workday filing.

## Recovery path — Rebase or cherry-pick from fd62641

After 024B-extras-1 merges, this branch contains the full pre-carve state. Choose one:

### Option A — Rebase 024B-extras-2 onto merged 024B-extras-1
```bash
git fetch origin
git checkout feature/wp-scp-024-024b-extras-2
git rebase origin/main  # may have conflicts; resolve preferring 024B-extras-2's depth-defense additions
```
This preserves the full R-cycle history but rebuilds the commit chain over the merged 024B-extras-1.

### Option B — Cherry-pick depth-defense diff onto a fresh branch
```bash
git fetch origin
git checkout -b feature/wp-scp-024-024b-extras-2-v2 origin/main
# Manually re-apply the depth-defense additions from feature/wp-scp-024-024b-extras-2 vs 024B-extras-1-merge-point
git diff <024B-extras-1-merge-SHA> feature/wp-scp-024-024b-extras-2 -- scripts/ tests/ docs/adoption/ docs/DECISIONS.md docs/reviews/WP-SCP-024/024B-extras-2/ policies/ > /tmp/depth-defense.diff
git apply /tmp/depth-defense.diff
# Stage + commit as one clean "024B-extras-2 depth-defense surface" commit
```
This produces a clean single-commit slice without 16 rounds of fix-round commit churn.

**Recommendation: Option B.** The R-cycle commit history is preserved in the `feature/wp-scp-024-024b-extras-2` branch tip; the rebase-vs-cherry-pick choice is about what gets reviewed in the PR. A single-commit slice is cleaner for the new R-cycle.

## Acceptance criteria

- [ ] All extracted features re-implemented and tests passing
- [ ] D-048 filed
- [ ] ADOPT-001 §12.8 Gate 3 automated procedure
- [ ] STATUS.md chain entry
- [ ] 3-lens R1+R2 fixpoint (≤2 MAJ + 0 CRIT per criterion (b))
- [ ] CI green
- [ ] Self-merge per D-040

## Sequencing

| Phase | Work | Mode | Wall |
|---|---|---|---|
| 0 | Pre-flight: 024B-extras-1 merged + this branch rebased/cherry-picked | Operator | ~30 min |
| 1 | Single Codex pass to re-apply the depth-defense diff (already authored) | Codex T3 | ~15 min |
| 2 | 3× sequential Sonnet R1 review | Sonnet | ~30 min |
| 3 | Fix-rounds (expected 1-2 given smaller surface + carried-forward R16 fixes) | Codex + Sonnet | ~1-2 hrs |
| 4 | Final R-fixpoint + self-merge | Opus | ~10 min |

Target: 024B-extras-2 merged within ~4-5 hours wall-clock (smaller surface; R16's depth-finds already addressed).

## Reservation guard

D-048 reserved for this slice. Codex must NOT assign D-048 to anything else.

---

**Status:** ACTIVE — opened 2026-05-12 post-extras-1-merge. 10 carry-forward TFs from extras-1 to absorb:

| TF | Source | Class |
|---|---|---|
| TF-024B-EXTRAS-2-SET-EQ-001 | extras-1 SCOPE-CORRECTION-2 carve + R20/R22/R25/R27/R29/R30 cross-lens | restore-mode set-equality verify |
| TF-024B-EXTRAS-2-RESTORE-PATH-CONTAINMENT-001 | extras-1 fix-round-20 | `--restore` path containment guard |
| TF-024B-EXTRAS-2-COHORT-REGEX-MULTICHAR-001 | extras-1 fix-round-20 | cohort regex multi-char support |
| TF-024B-STEP7-FIXTURE-SEQ-001 | extras-1 fix-round-20 | step-7 fixture alignment polish |
| TF-024B-EXTRAS-2-STAGED-RESTORE-TEST-001 | extras-1 fix-round-20 | staged-but-uncommitted prior-restore test |
| TF-024B-EXTRAS-2-RESTORE-FILE-TOCTOU-001 | extras-1 fix-round-21 | RESTORE_PRE_STATE TOCTOU hardening |
| TF-024B-EXTRAS-2-WORKFLOW-PIN-BASE-BRANCH-001 | extras-1 fix-round-21 | CI workflow pin to base-branch script |
| TF-024B-EXTRAS-2-POLICY-CHECK-TARGET-FILTER-TESTS-001 | extras-1 fix-round-24 | per-test coverage for path-based excludes |
| TF-024B-EXTRAS-2-PUT-BODY-SHAPE-ASSERTIONS-001 | extras-1 fix-round-25 | extend PUT-body shape assertions across all restore tests |
| TF-024B-EXTRAS-2-TRANSFORM-INCLUSION-LIST-001 | extras-1 fix-round-31 (R30 SAFE-MAJ-001) | transform inclusion-list (replaces exclusion-list); covers lock_branch / required_linear_history / block_creations posture gap |

## Slice opening checklist

- [x] DISPATCH-NOTE drafted (this file)
- [x] Branch `feature/wp-scp-024-024b-extras-2-v2` opened off main `d7b16d0`
- [ ] Codex dispatch to apply depth-defense diff (extracted from preserved branch `feature/wp-scp-024-024b-extras-2` at fd62641 OR re-implemented from this DISPATCH-NOTE)
- [ ] 3-lens R1 review on initial implementation
- [ ] Fix-rounds to fixpoint
- [ ] PR + self-merge per D-040

This slice does NOT gate 024C. The cohort cascade can open in parallel once FUP-ACC-INSTALL-TARGET-REPO-001 closes (ACC-side).
