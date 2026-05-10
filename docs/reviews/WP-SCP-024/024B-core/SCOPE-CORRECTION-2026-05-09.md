# Scope correction — WP-SCP-024 024B split into 024B-core + 024B-extras

**Date:** 2026-05-09
**Operator decision:** split slice 024B into two slices.

## Empirical justification (R6 → R7 → R8 trajectory)

WP-SCP-024 slice 024B as originally scoped accumulated 7 fix-rounds + 7 adversarial-review rounds against a single branch. Trajectory:

| R round | CRIT | MAJ unique | Notable |
|---|---|---|---|
| R1 | 2 | 9 | Worked-example matrix gap; --restore PUT shape |
| R2 | 1 | 7 | Renovate marker missing; --restore safety guards |
| R3 | 1 (×2 lenses) | 3 | Workflow-name collision; placeholder name drift |
| R4 | 0 | 6 | Test gaps + path-traversal hardening + ADOPT-001 alignment |
| R5 | 0 | 5 | Branch filter regression; required_signatures sub-resource |
| R6 | 0 | 6 | **Missed primary deliverable: CI workflow wiring** |
| R7 | 0 | 6 | **Bootstrap defect introduced by R6's fix** + 3 unique |
| R8 (correctness only; killed mid-flight) | 0 | 3 | **2 new defects in R7's just-added bootstrap fix** + 1 carry-forward |

**Empirical signal:** each fix-round closes 5–6 MAJ but introduces 2–3 new defects in the just-added code. Net rate of MAJ-closure is positive (+3–4 per round) but slow. Three structural problems:

1. **Surface area too large.** 16 files modified, ~3,500 lines of additions across 7 fix-rounds. A single review pass cannot reliably find all failure modes; each fix-round's new code introduces new edge cases that the next R-round catches.
2. **Bootstrap class.** R6 missed the CI workflow wiring (a primary deliverable). R7's fix for that wiring introduced a self-blocking defect on the slice's own PR (the workflow path-filtered into 024B's own DISPATCH-NOTE.md). Class of defect: code that introduces a primitive cannot easily test the primitive applied to the introducing slice itself without exclusion logic.
3. **Coupled lens.** --restore mode and CI workflow wiring share dependencies on `scripts/enable-required-check.sh` invocation log shape; reviewers in safety_bypass + correctness lenses both flag related findings, which inflates apparent finding count vs. unique surface.

## Decision

**Split 024B into:**

- **024B-core** (this slice): scaffolder + adopter wrapper template + cascade-status CI enforcement script + tests for both. ~2,000 lines; 5 files. Smaller scope = faster convergence; expect 1–2 R-cycles.
- **024B-extras** (next slice, branched from merged 024B-core): `enable-required-check.sh --restore` mode + ADOPT-001 §12.8 break-glass procedure + `.github/workflows/check-invocation-log-entry.yml` CI wiring + step 7 operator-interactive `--restore` real-repo round-trip demo. Informed by R8 carry-forward findings.

## Why this is NOT descope

Both halves still ship. The user explicitly rejected the "good-enough fixpoint with TF-tracked residuals" framing — that pattern is transparent-descope. Splitting is **incremental delivery**, which:

- Preserves all original 024B scope. Both halves ship before WP-SCP-024 cohort onboarding (024C+) opens.
- Gets faster feedback on the lower-risk half (scaffolder + template + CI script + tests) which has no operator-interactive demo dependency.
- Gives 024B-extras a clean review window informed by 024B-core's lessons.
- Keeps the rollback SLO honest: invariant-7's <30 min single-operator rollback STILL requires a real-repo round-trip demo at 024B-extras step 7. No invariant relaxed.

## Carry-forward from extras-parking

The original 024B branch is preserved at `feature/wp-scp-024-024b-extras-parking` (pushed 2026-05-09). Audit trail intact:

- 7 codex-fix-round-N-audit.log files
- 7 R-round archive directories (r1-archive through r7-archive; r8-archive contains partial R8 correctness output)
- All fix-round commits with detailed commit messages
- 024B-extras work-package authoring picks up here, informed by R8-CORR-001/002/003 carry-forward findings

## Sequencing

1. **024B-core** (this branch): R1 → fix-round-N → fixpoint → merge. Expected 1–2 R-cycles.
2. **024B-extras** (branched from merged core): R1 → fix-round-N → fixpoint → step 7 operator-interactive `--restore` real-repo round-trip demo → merge. Expected 1–2 R-cycles given lessons learned.
3. **024C** (PIM canary cascade): unblocked when 024B-extras merges (because cascade slices need both the scaffolder AND the --restore + CI workflow).

## Reference

- Original 024B DISPATCH-NOTE: parking branch `docs/reviews/WP-SCP-024/024B/DISPATCH-NOTE.md`
- 024B-core DISPATCH-NOTE: this slice's `docs/reviews/WP-SCP-024/024B-core/DISPATCH-NOTE.md`
- 024B-extras DISPATCH-NOTE: TBD when extras branch opens
- Plan-doc §6 amendment for split: lands in this PR
- D-044 reservation: stays with 024B-core (scaffolder + template + CI enforcement script). 024B-extras may reserve a sibling D-NNN for --restore + break-glass + workflow wiring at extras-slice authoring time.
