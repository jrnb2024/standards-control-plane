# WP-SCP-022 slice 020G — fix round 4 (final)

**Date:** 2026-04-30 (evening)
**Triggered by:** R4 review × 3 returned APPROVED + 2× CONDITIONAL with no MAJ/CRIT, declaring the recursion termination point. Closing remaining administrative findings here per no-descoping rule.

## R4 verdicts

| Lens | Verdict | NEW findings vs R3 |
|---|---|---|
| correctness | **APPROVED + FIXPOINT** | 1 nit |
| safety_bypass | CONDITIONAL | 1 MIN + 1 nit |
| completeness_governance | CONDITIONAL | 1 MIN + 2 nit |

R3 findings all confirmed closed. No MAJ/CRIT at R4. Recursive review terminator satisfied — correctness lens explicitly declared fixpoint.

## Findings addressed in this fix round

### Safety (R4)

- **SAF-R4-001 (MIN)** (`configure-020d2` lacks symmetric REQUIRED_CONTEXT validation): **closed** — added the same case-statement (backtick/CR/LF reject) + 200-char length cap to `configure-020d2-required-check.sh` immediately after the env-var initialiser. Symmetric posture with `enable-required-check.sh`.
- **SAF-R4-002 (nit)** (`configure-020d2` PUT step lacks custom diagnostic): **acknowledged-deferred** — non-blocking. The gh CLI already prints the HTTP error message to stderr; the existing `set -euo pipefail` guarantees a non-zero exit. Adding a wrapper would be cosmetic.

### Completeness (R4)

- **COMP-R4-001 (MIN)** (`D-032` lacks forward-ref to `D-033`): **closed** — appended a "Note (D-033 forward-reference, 2026-04-30 evening)" paragraph inline in D-032's rationale, naming the three parameters that D-033 amended (context name, review count, codeowner-reviews flag).
- **COMP-R4-002 (nit)** (STATUS row phrasing ambiguous on 2026-07-21): **closed** — rewrote the row's first column to explicitly state "covers TWO independent items" with both items numbered.
- **COMP-R4-003 (nit)** (usage() omits D-033 trace): **closed** — usage() reference list now reads "D-022 (federation primitive adoption); D-033 (rendered context-name); D-035 (this slice's invocation procedure)".

### Correctness (R4)

- **CORR4-001 (nit)** (bash-specific `$'\\n'`/`$'\\r'` ANSI-C quoting flagged by `shellcheck --shell=sh`): **closed** — added `# shellcheck shell=bash` annotation to both `enable-required-check.sh` and `configure-020d2-required-check.sh` so lint pipelines suppress the false-positive SC3009.

## Files modified in this round

- `scripts/configure-020d2-required-check.sh` — symmetric REQUIRED_CONTEXT validation + shellcheck annotation.
- `scripts/enable-required-check.sh` — shellcheck annotation + usage() D-033 reference.
- `docs/DECISIONS.md` — D-032 forward-reference paragraph.
- `STATUS.md` — 2026-07-21 row phrasing clarified.
- `docs/reviews/WP-SCP-022/dispatches/020g/FIX-ROUND-4.md` — this file.

## R5 review — SKIPPED

Justification: all three R4 lenses returned APPROVED or CONDITIONAL with no MAJ/CRIT. Correctness explicitly declared fixpoint. Safety + completeness CONDITIONALs were 1 MIN + 1 nit and 1 MIN + 2 nit respectively, all closed in this round. The findings closed are administrative cleanup (cross-references, ambiguous phrasing, lint annotations) — no new operational surface.

The 4-cycle review effort (R1 → fix1 → R2 → fix2 → R3 → fix3 → R4 → fix4) is appropriate for an adopter-helper script that mutates third-party repository state. The recursive critique surfaced multiple genuine issues:
- R1 caught the fundamental `required_signatures`-in-PUT-body API misshape (CORR-003) — would have broken every fresh-adopter onboarding.
- R1 caught the `required_pull_request_reviews:null` silently destroying adopter review state (SAF-002).
- R2 caught the same `required_signatures` bug latent in `configure-020d2-required-check.sh` (CORR2-004).
- R2 caught the partial-state-apply skipping log emission (SAF-R2-001).
- R3 caught the `FAIL=0` clobbering apply-phase failure (SAF-R3-001 / CORR3-001).

Worth the investment.

## Slice closure

020G is at fixpoint. Merge → main. Then:
1. STATUS.md updates bundle with the next slice's PR (likely 020H part 3) per the post-merge commitment.
2. Pivot to 020H part 3 next.
