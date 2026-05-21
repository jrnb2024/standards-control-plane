# 023C — fix-round-2 audit (R2 fixpoint reached)

**Date:** 2026-05-03
**Branch:** `feature/wp-scp-023-023c-aggregator`
**Pre-fix-round-2 HEAD:** `8458e1c`

## R2 finding tally

3× parallel Sonnet R2: all 3 lenses APPROVED.

| Lens | Verdict | new CRIT | new MAJ | new MIN | new nit |
|---|---|---|---|---|---|
| correctness | APPROVED | 0 | 0 | 1 | 5 (closure-confirmation) |
| safety_bypass | APPROVED | 0 | 0 | 0 | 1 |
| completeness | APPROVED | 0 | 0 | 1 | 0 |
| **total NEW** | — | **0** | **0** | **2** | **6** |

**R2 fixpoint criterion: 0 new CRIT + 0 new MAJ on a complete cycle ⇒ R2 FIXPOINT REACHED.**

R2 confirmed all R1 dispositions against actual repo state (5 closure-confirmation entries from correctness lens).

## Per-finding disposition

### MIN (2 new)

| ID | Disposition | Action |
|---|---|---|
| **C-COR-R2-MIN-001** | **INLINE-FIX** | `last_emit_run_id` + `last_emit_commit` field-level descriptions still said "Present iff status in (verified, verification_failure)" — but the no_emit download-failure path AND the prior-row-retention-on-unreachable path also populate them. Rewrote both descriptions to accurately reflect the multi-status presence semantics. |
| **R2-CG-MIN-001** | **INLINE-FIX** | TF-023C-006 + TF-023C-007 were named in FIX-ROUND-1.md but missing from STATUS.md canonical TF register. Added both entries to STATUS.md tracked-forward section. |

### nit (6 new)

| ID | Disposition |
|---|---|
| C-COR-R2-CLOSURE-* (5 entries) | **NO ACTION** — closure-confirmation nits |
| **R2-SAFE-NIT-001** | **NO ACTION** — `int(latest.get('databaseId', 0))` is unguarded against non-int. The default 0 + the run-id presence semantics make this safe in practice (a databaseId=0 would produce a `gh run download 0` failure recorded as no_emit). Cosmetic robustness improvement; no security surface. |

## Inline-fix summary (2 edits)

1. `schemas/scorecard-index.schema.json` — `last_emit_run_id` + `last_emit_commit` description rewrites (C-COR-R2-MIN-001).
2. `STATUS.md` — TF-023C-006 + TF-023C-007 entries added (R2-CG-MIN-001).

## Forward-filed TFs

R2 surfaced no new TF candidates. TF-023C-001..007 remain filed forward.

## Smoke-test post-fix

- `pytest tests/scorecard-aggregator/ tests/scorecard-emit/ tests/conflict_gate/`: 35/35 pass.
- `scripts/scp-pre-push-verify.sh`: ✓ all 3 SCP-R gates pass.

## R2 fixpoint verdict

- **0 new CRIT + 0 new MAJ** on a complete adversarial cycle ⇒ **R2 FIXPOINT REACHED** per `feedback_recursive_adversarial_review.md`.
- All R1 dispositions verified against actual repo state.
- 2 R2 MINs both inline-fixed; 6 nits NO ACTION.

**Slice is at fixpoint. Ready for PR + CI green + operator-merge per D-040.**

## 2-round adversarial-review cycle summary

- **R1**: 4 unique MAJ closed inline (signer-workflow regex anchor + runtime check; conditional schema branches; status enum description rewrite; 7-day staleness check) + 4 MIN inline-fixed + 4 TF-forwarded.
- **R2**: 0 new CRIT/MAJ + 2 MIN inline-fixed (description polish + STATUS register completeness) ⇒ FIXPOINT.

Adversarial review caught 4 unique MAJs total — including a real defence-in-depth gap (signer-workflow regex permitted any owner/repo namespace) and a real missing-AC bug (7-day staleness check named in DISPATCH-NOTE but absent from implementation).
