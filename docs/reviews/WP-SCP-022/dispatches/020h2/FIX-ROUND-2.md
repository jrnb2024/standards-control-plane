# 020h2 fix-round-2 (post-r2 — fixpoint reached)

**Date:** 2026-05-01

## Triggers — fixpoint reached at R2

R2 lens cycle returned **0 CRIT + 0 MAJ across all three lenses**:

| Lens | Verdict | CRIT | MAJ | MIN | nit |
|---|---|---|---|---|---|
| R2 correctness | PASS_WITH_FINDINGS | 0 | 0 | 0 | 2 |
| R2 safety | PASS_WITH_FINDINGS | 0 | 0 | 0 | 4 |
| R2 completeness | CONDITIONAL_PASS | 0 | 0 | 1 | 0 |
| **TOTAL** | — | **0** | **0** | **1** | **6** |

Per `feedback_recursive_adversarial_review.md`: **fixpoint criterion is "no new CRIT/MAJ"** — R2 confirms fixpoint.

Per `feedback_protocol_over_shortcuts.md` (no descoping): all 1 MIN + 6 nit findings closed inline this round.

## Closures applied

| Finding | Severity | Closure |
|---|---|---|
| COMP-R2-MIN-001 | MIN | DISPATCH-NOTE Files section + Slice acceptance checklist updated. New checklist items (vi) and (vii) added: (vi) ADOPT-001 §12.7 supply-chain disclosure update; (vii) CODEOWNERS extension. Files list now enumerates ADOPT-001 + CODEOWNERS + scripts/scp-policy-check + FIX-ROUND-1.md + FIX-ROUND-2.md + review JSONs. |
| R2-SAFE-001 | nit | (Same closure as COMP-R2-MIN-001 — DISPATCH-NOTE Files now includes ADOPT-001.) |
| R2-SAFE-002 | nit | §12.7.13 RUNNER_TEMP TOCTOU paragraph reworded — removed the unsupported `mode 0700` claim; replaced with ownership-based explanation: "the runner user being the exclusive writer (RUNNER_TEMP is owned by the runner user; the ephemeral single-user VM has no other local accounts that could exploit the window between operations)." Self-hosted-runner caveat strengthened. |
| R2-SAFE-003 + COR-R2-nit-002 | nit + nit | `assert_bare_binary_shape()` rewritten to use Python (`python3 -c 'open(...).read(2).hex()'`) instead of `xxd`. Closes the silent-degradation surface where `xxd` absence on a self-hosted runner would cause `magic=""` to silently pass the gzip-shape check. Python 3 is already a runner dependency for the rule-config wrapping helpers, so no new dependency is introduced. The `\|\| true` fallback is replaced with `\|\| emit_infra_failure ...` so any read failure is fail-closed. ADOPT-001 §12.7.13 "Asset-shape pin" paragraph also updated to reflect the Python implementation + remove the `xxd` reference. |
| R2-SAFE-004 | nit | §12.7.13 "Lockfile + version-pin governance" paragraph rewritten: fork-operator CODEOWNERS instructions are now self-contained inline (`scripts/** @<owner>` and `vendor/** @<owner>` before any self-protection line, with the ORDERING INVARIANT cross-reference). The misleading cross-ref to §12.7.4 / §12.7.1 (which cover the adopter-side caller-wrapper, not the fork's lockfile) is replaced with an explicit distinction. |
| COR-R2-nit-001 | nit | `scripts/scp-policy-check` `json_lock_field` Python helper now catches `(KeyError, TypeError)` symmetric with the workflow's `read_lockfile_field` post-fix-round-1 update. A malformed lockfile structure (e.g. `{"regal": "oops"}`) now emits a clear `malformed lockfile structure (...): ...` message instead of an uncaught Python traceback. |

## Closures NOT applied

None. All R2 findings closed.

## Cumulative across 2 rounds

| Round | Verdict by lens | CRIT | MAJ | MIN | nit |
|---|---|---|---|---|---|
| R1 corr | PASS_WITH_FINDINGS | 0 | 0 | 1 | 3 |
| R1 safety | BLOCKED | 0 | 2 | 1 | 2 |
| R1 comp | BLOCKED | 0 | 1 (≡ SAFE-001) | 2 | 1 |
| R2 corr | PASS_WITH_FINDINGS | 0 | 0 | 0 | 2 |
| R2 safety | PASS_WITH_FINDINGS | 0 | 0 | 0 | 4 |
| R2 comp | CONDITIONAL_PASS | 0 | 0 | 1 | 0 |
| **TOTAL** | — | **0** | **3** (2 distinct after collapsing SAFE-001 ≡ COMP-MAJ-001) | **5** | **12** |

3 MAJ closed (2 distinct issues — ADOPT-001 stale references + CODEOWNERS gap). 5 MIN closed. 12 nit closed.

**Slice 020H.2 ready for merge.**
