# 023B — fix-round-2 audit (R2 → fix → R3 candidate)

**Date:** 2026-05-03
**Branch:** `feature/wp-scp-023-023b-emitter`
**Pre-fix-round-2 HEAD:** `dd88b2e` (fix-round-1)

## R2 finding tally

3× parallel Sonnet R2: 1 CHANGES_REQUESTED + 1 APPROVED + 1 APPROVED_WITH_FINDINGS.

| Lens | Verdict | new CRIT | new MAJ | new MIN | new nit |
|---|---|---|---|---|---|
| correctness | CHANGES_REQUESTED | 0 | 1 | 0 | 5 |
| safety_bypass | APPROVED | 0 | 0 | 2 (carried) | 3 (carried) |
| completeness_governance | APPROVED_WITH_FINDINGS | 0 | 0 | 2 | 0 |
| **total NEW** | — | **0** | **1** | **2** | **5** |

R2 confirmed all R1 dispositions against actual repo state (5 R2-COR-CLOS-* nits are positive-confirmation entries). Safety carried R1 NO ACTION items — disposition unchanged.

## Per-finding disposition

### MAJ (1 new)

| ID | Lens | Disposition | Action |
|---|---|---|---|
| **R2-COR-MAJ-001** | correctness | **INLINE-FIX (real bug fix)** | Real correctness gap: warn-baseline rules (SCP-R-004 at v1.1.0+) emit raw findings with `verdict: deny` (the rule body is shape-parallel to deny rules; the workflow's render-deny step demotes them to `::warning::`). The scorecard emitter counted those as denies → produced verdict='deny' even when the gate passed (per render-deny exclusion). Closed by mirroring the workflow's `WARN_BASELINE_RULES = {"SCP-R-004"}` set in the emitter heredoc + excluding warn-baseline rule_ids from the denies counter + adding a separate verdict='warn' branch when only warn-baseline rules fired (post-suppression). New 4th fixture (`warn-baseline/`) locks in the parity. |

### MIN (2 new)

| ID | Lens | Disposition | Action |
|---|---|---|---|
| **CG-R2-MIN-001** | completeness | **NO ACTION** | DISPATCH-NOTE IN-scope table line still describes the schema's `signature` field; reviewer notes this R2 record itself serves as the clarification. The actual schema + plan-doc are correct. Audit-trail consistency only. |
| **CG-R2-MIN-002** | completeness | **INLINE-FIX** | Release notes "Workflow permissions delta" section had stale workflow-level wording. Rewrote to reflect the new job-scoped pattern: "The reusable workflow gains a new `attest-scorecard` job that declares `attestations: write` + `id-token: write` at JOB level..." |

### nit (5 new + 3 carried)

All R2 nit findings either confirm R1 closures (R2-COR-CLOS-001..005) or carry forward R1 NO ACTION items (nit-SAFE-001/002, MIN-SAFE-001/002 disposition reaffirmed). One new nit:
- **nit-SAFE-R2-001**: `attest-scorecard` job declares `contents: read` even though it doesn't read repo content. **NO ACTION**: defensive permission for future-compat (e.g. if a future debugging step needs to read a file from the checkout); cost is zero.

## Inline-fix summary (4 edits across 3 files)

1. `.github/workflows/policy-check.yml` Build heredoc: added `WARN_BASELINE_RULES = {"SCP-R-004"}` set + excluded warn-baseline rule_ids from denies counter (R2-COR-MAJ-001).
2. `.github/workflows/policy-check.yml` Build heredoc: rewrote verdict-derivation logic to prefer 'warn' over 'deny' when only warn-baseline rules fired post-suppression (R2-COR-MAJ-001).
3. `tests/scorecard-emit/fixtures/warn-baseline/{policy-check-summary.json, expected-scorecard-emit.json}` (NEW × 2 files): SCP-R-004 raw deny finding + no waiver → expected verdict='warn' with denies=0.
4. `docs/releases/v1.2.0.md` "Workflow permissions delta": rewrote to reflect job-scoped pattern (CG-R2-MIN-002).

## Forward-filed TFs

R2 surfaced no new TF candidates. TF-023B-001 + TF-023B-002 remain filed forward from R1.

## Smoke-test post-fix

- `pytest tests/scorecard-emit/ tests/conflict_gate/`: 24/24 pass (was 21; added 3 warn-baseline parametrized tests).
- `scripts/scp-pre-push-verify.sh`: ✓ all 3 SCP-R gates pass.

## R3 candidacy

R2 surfaced 0 new CRIT, 1 new MAJ (closed inline including a new fixture to lock in the parity), 2 MIN (1 inline-fixed + 1 NO ACTION), 5+3 nit (all NO ACTION). The slice is ready for **R3 dispatch** to verify no NEW CRIT/MAJ findings emerge against the fix-round-2 surface.
