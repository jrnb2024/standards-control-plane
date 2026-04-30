# WP-SCP-022 slice 020G — fix round 3

**Date:** 2026-04-30 (evening)
**Triggered by:** R3 review × 3 surfaced 1 MAJ + 4 MIN + 3 nit findings.

## R3 verdicts

| Lens | Verdict | NEW findings vs R2 |
|---|---|---|
| correctness | CONDITIONAL | 1 MIN + 1 nit |
| safety_bypass | NEEDS_REVISION | 1 MAJ + 2 MIN |
| completeness_governance | CONDITIONAL | 2 MIN + 2 nit |

R2 findings all closed. The 1 MAJ is the regression fix-round-2 introduced: `FAIL=0` at the start of the verify section unconditionally clobbers `FAIL=1` from the apply-phase. Both correctness lens (CORR3-001) and safety lens (SAF-R3-001) caught it independently.

## Findings addressed in this fix round

### From safety (R3) + correctness (R3)

- **SAF-R3-001 (MAJ) ≈ CORR3-001 (MIN)** (`FAIL=0` clobbers apply-phase failure): **closed** — replaced `FAIL=0` with `FAIL="${FAIL:-0}"`. The default-to-0 pattern preserves any prior FAIL=1 from the apply-phase trap.
- **SAF-R3-002 (MIN)** (`REQUIRED_CONTEXT` no validation, can corrupt log markdown via backtick/newline): **closed** — added case-statement check rejecting backtick + CR + LF chars; added 200-char length cap. Real GitHub Actions check-run names don't contain those chars.
- **SAF-R3-003 (MIN)** (`configure-020d2` POST has no diagnostic on failure): **closed** — wrapped POST in `if !` with explicit error message naming the partial state.
- **CORR3-002** (nit — `AFTER_JSON` GET unprotected under `set -e`): **acknowledged-deferred** — non-blocking. The GET-failure path is rare (would need API outage between PUT-success and GET); the existing `set -e` abort on GET failure produces a clear gh error message. Adding a trap here adds complexity without changing the user-visible failure mode.

### From completeness (R3)

- **COMP-R3-001** (020D2 dispatch-note silent on CORR2-004 post-merge fix): **closed** — added "Post-merge correction (added 2026-04-30 evening)" section to `docs/reviews/WP-SCP-022/dispatches/020d2/DISPATCH-NOTE.md` with timeline + scope.
- **COMP-R3-002** (STATUS.md 2026-07-21 row scoped to 020K only): **closed** — row text expanded to also reference TF-020G-001.
- **COMP-R3-003** (D-035 doesn't cite D-033): **closed** — added cross-reference to D-035 rationale: "The required-check context name `policy-check / scp/policy-check` traces to D-033 ...".
- **COMP-R3-004** (020G DISPATCH-NOTE lacks post-merge STATUS commitment): **closed** — added "Post-merge STATUS.md update commitment" section to DISPATCH-NOTE.md naming the two STATUS edits (Live operational state + Post-Threshold-A backlog) bundled with next slice's PR.

## Files modified in this round

- `scripts/enable-required-check.sh` — `FAIL` initialiser preserves prior value; `REQUIRED_CONTEXT` validation (backtick/CR/LF/length).
- `scripts/configure-020d2-required-check.sh` — POST step wrapped in failure-diagnostic.
- `docs/DECISIONS.md` — D-035 row cites D-033.
- `STATUS.md` — 2026-07-21 follow-up row references TF-020G-001.
- `docs/reviews/WP-SCP-022/dispatches/020d2/DISPATCH-NOTE.md` — post-merge correction note for the latent `required_signatures` bug.
- `docs/reviews/WP-SCP-022/dispatches/020g/DISPATCH-NOTE.md` — post-merge STATUS commitment section.
- `docs/reviews/WP-SCP-022/dispatches/020g/FIX-ROUND-3.md` — this file.

## R4 dispatch

Per `feedback_recursive_adversarial_review.md`, recurse to fixpoint. R3 had 1 MAJ on safety/correctness lens (now closed) + admin findings on completeness. R4 should declare fixpoint or surface only minor admin cleanup.
