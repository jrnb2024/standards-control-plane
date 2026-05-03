# 023A — fix-round-3 audit (R3 → fix → R4 candidate)

**Date:** 2026-05-03 (PM-1)
**Branch:** `feature/wp-scp-023-cross-repo-scorecards-plan`
**Pre-fix-round-3 HEAD:** `ac48843` (fix-round-2)

## R3 finding tally

3× parallel Sonnet R3: 1 CHANGES_REQUESTED + 1 APPROVED_WITH_FINDINGS + 1 APPROVED.

| Lens | Verdict | new CRIT | new MAJ | new MIN | new nit |
|---|---|---|---|---|---|
| correctness | CHANGES_REQUESTED | 0 | 1 | 1 | 1 |
| safety_bypass | APPROVED_WITH_FINDINGS | 0 | 0 | 2 | 0 |
| completeness_governance | APPROVED | 0 | 0 | 1 | 0 |
| **total raw** | — | **0** | **1** | **4** | **1** |

After dedup: 0 CRIT, **1 unique MAJ** (incorrect CLI flag name `--source-path-prefix` cited in fix-round-2's MAJ-SAFE-R2-001 closure — the real `gh attestation verify` flag is `--signer-workflow`).

## Per-finding disposition

### MAJ (1 unique)

| ID | Lens(es) | Disposition | Action |
|---|---|---|---|
| **COR-R3-MAJ-001 / MIN-SAFE-R3-001** | correctness, safety | **INLINE-FIX** | Fix-round-2's "Non-negotiable verification constraint" block in §5 step 3 cited `--source-path-prefix` (a non-existent `gh attestation verify` flag). The correct flag is `--signer-workflow`. Without the fix, a 023C executor following the directive literally would encounter an unknown-flag error; if they then proceeded with only `--predicate-type`, the invocation would verify SLSA provenance type but NOT bind to the SCP reusable workflow path — reopening the rogue-workflow forgery path that MAJ-SAFE-R2-001 was meant to close. Replaced with `--signer-workflow` + concrete invocation example: `gh attestation verify <artifact> --signer-workflow jrnb2024/standards-control-plane-/.github/workflows/policy-check.yml@<sha>`. |

### MIN (4)

| ID | Lens | Disposition | Action |
|---|---|---|---|
| **COR-R3-MIN-001** | correctness | **INLINE-FIX** | §1 footnote "Move #2 is unassigned" — imprecise; move #2 is conflicted (WP-SCP-020 §1 implies MCP server while §3 + WP-SCP-021 §1 say move #3). Reworded to "conflicted in the corpus" + cited the specific WP-SCP-020 §1-vs-§3 inconsistency. |
| **MIN-SAFE-R3-002** | safety | **INLINE-FIX** | DECISIONS.md D-042 reservation note + §9 D-042 table row didn't explicitly name the `job_workflow_ref` verification constraint — a 023C Codex executor scanning DECISIONS.md alone would not see the mandatory trust constraint. Appended explicit mandatory-constraint language to DECISIONS.md blockquote + amended §9 table row. |
| **COMP-R3-MIN-001** | completeness | **INLINE-FIX** | STATUS.md "Today's chain (2026-05-03)" 023A row still said "Move #4". Updated to "Move #5". |

### nit (1)

| ID | Disposition |
|---|---|
| **COR-R3-nit-001** | **INLINE-FIX** | FIX-ROUND-2.md "Inline-fix summary" header said "6 edits across 3 files" but only 2 distinct files. Corrected to "2 files". |

## Inline-fix summary (6 edits across 4 files)

1. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` §5 step 3: `--source-path-prefix` → `--signer-workflow` + concrete invocation example (COR-R3-MAJ-001 / MIN-SAFE-R3-001).
2. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` §1 footnote: "unassigned" → "conflicted" with WP-SCP-020 §1-vs-§3 specifics (COR-R3-MIN-001).
3. `docs/plans/WP-SCP-023-cross-repo-scorecards.md` §9 D-042 table row: appended `job_workflow_ref` mandatory constraint (MIN-SAFE-R3-002).
4. `docs/DECISIONS.md` D-041/042/043 reservation blockquote: appended D-042 mandatory `job_workflow_ref` trust constraint with concrete `gh attestation verify --signer-workflow` invocation (MIN-SAFE-R3-002).
5. `STATUS.md` "Today's chain (2026-05-03)" 023A row: "Move #4" → "Move #5" + reference to D-042 mandatory constraint (COMP-R3-MIN-001).
6. `docs/reviews/WP-SCP-023/dispatches/023A-plan-doc/FIX-ROUND-2.md`: "6 edits across 3 files" → "2 files" (COR-R3-nit-001).

## Forward-filed TFs

R3 surfaced no new TF candidates. TF-023A-001 + TF-023A-002 carry from R1.

## Smoke-test post-fix

- `pytest tests/conflict_gate/`: 12/12 pass.
- `scripts/scp-pre-push-verify.sh`: ✓ all 3 SCP-R gates pass.

## R4 candidacy

R3 surfaced 0 new CRIT, 1 unique MAJ (closed inline). R3 also surfaced 4 MIN + 1 nit, all inline-fixed. The slice is ready for **R4 dispatch** to verify no NEW CRIT/MAJ findings emerge against the fix-round-3 surface. Per `feedback_recursive_adversarial_review.md` fixpoint criterion: R4 must surface 0 CRIT + 0 MAJ on a complete cycle.
