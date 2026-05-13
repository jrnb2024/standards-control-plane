# D-SCP-024B-SCOPE-SPLIT-2026-05-09 — WP-SCP-024 024B operator-decided scope split

**Status:** ACCEPTED
**Date filed:** 2026-05-13
**Decision dates:** 2026-05-09 (first split: 024B → 024B-core + 024B-extras), 2026-05-11 (second split: 024B-extras → 024B-extras-1 + 024B-extras-2)
**Operator:** @jrnb2024
**Closes governance gap:** GAP-P1-001 (orchestrator audit, 2026-05-13) — operator-decided scope splits were recorded in operational `SCOPE-CORRECTION*.md` artefacts but had no canonical decision-record entry citing the authorisation date + justification.

## Context

WP-SCP-024 (estate cascade) plan-doc §6 originally enumerated slice 024B as a single monolithic deliverable spanning scaffolder + adopter wrapper template + cascade-status CI enforcement + `enable-required-check.sh --restore` mode + ADOPT-001 §12.8 break-glass procedure + `.github/workflows/check-invocation-log-entry.yml` CI wiring + step 7 operator-interactive `--restore` real-repo round-trip demo + extensive test surface. Roughly 16 files; ~3,500 lines of additions over the original 024B branch.

During implementation, the slice accumulated 7 fix-rounds + 7 adversarial-review rounds against a single branch without converging to fixpoint. R-trajectory (per `docs/reviews/WP-SCP-024/024B-core/SCOPE-CORRECTION-2026-05-09.md` empirical justification table): R1 9 MAJ → R5 5 MAJ → R6 6 MAJ (**missed primary deliverable: CI workflow wiring**) → R7 6 MAJ (**bootstrap defect introduced by R6's fix**) → R8 (correctness only, killed mid-flight) 3 MAJ. Net MAJ-closure was positive (+3–4 per round) but the rate was incompatible with the operator's calendar.

The original 024B branch is preserved at `feature/wp-scp-024-024b-extras-parking` as audit trail (7 codex-fix-round-N-audit.log files + 7 R-round archive directories).

## Decision

Operator decision on 2026-05-09 (first split) and 2026-05-11 (second split): split 024B into incremental sibling slices to bound the per-slice review load.

### First split — 2026-05-09

**024B-core** (this slice): scaffolder + adopter wrapper template + cascade-status CI enforcement script (`scripts/check-invocation-log-entry.sh`) + tests for both. ~2,000 lines; 5 files. Smaller scope = faster convergence; converged in 1–2 R-cycles. Filed D-044. Merged 2026-05-09 at `249aa9f`.

**024B-extras** (next slice, branched from merged 024B-core): `enable-required-check.sh --restore` mode + ADOPT-001 §12.8 break-glass + `.github/workflows/check-invocation-log-entry.yml` CI wiring + step 7 operator-interactive `--restore` real-repo round-trip demo. Informed by R8 carry-forward findings.

Operational artefact: `docs/reviews/WP-SCP-024/024B-core/SCOPE-CORRECTION-2026-05-09.md`.

### Second split — 2026-05-11

024B-extras attempted convergence over 16 R-cycles + 38 hours of session wall-time without reaching criterion (b) fixpoint. R-trajectory plateaued at ~5 MAJ per round (R12 4 / R13 4 / R14 3 / R15 8 / R16 6) with most findings being latent depth-defects in the depth-defense surface, not just-added-code regressions. Asymptotic-trajectory signal per `feedback_asymptotic_trajectory_split.md`.

**024B-extras-1** (carved): core `--restore` + ADOPT-001 §12.8 (manual Gate 3) + CI workflow + 6 of 6 posture-degradation flags. Filed D-047. Merged 2026-05-12 at `d7b16d0` (PR #113).

**024B-extras-2** (depth-defense surface, sibling): `--expected-wrapper-sha` + annotated-tag dereferencing + canonical-context guard + set-equality verify phase + transform inclusion lists + audited Gate 2 bypass + ADOPT-001 §12.8 automated Gate 3 rewrite. Filed D-048. Merged 2026-05-13 at `13572fe` (PR #114).

Operational artefact: `docs/reviews/WP-SCP-024/024B-extras/SCOPE-CORRECTION-2-2026-05-11.md`.

## Rationale

The split is **incremental delivery, NOT descope** (per `feedback_split_not_descope.md` + `feedback_asymptotic_trajectory_split.md`). Three load-bearing properties hold:

1. **All original 024B scope ships.** Three sibling slices (024B-core + 024B-extras-1 + 024B-extras-2) collectively deliver every deliverable in the original 024B Scope (in) table. Nothing is dropped.

2. **024C cohort onboarding is not advanced or weakened.** The two splits preserve the pre-existing precondition that 024B must close before 024C opens. 024C remains gated on 024B-extras-1 merge + FUP-ACC-INSTALL-TARGET-REPO-001 closure + TF-024B-REQCHECK-ENABLE-001 closure. 024B-extras-2 does NOT gate 024C (its depth-defense additions are real defensive value but invariant 7's <30-min rollback SLO is satisfied by the core `--restore` mode in 024B-extras-1).

3. **Each split is auditable.** The operational `SCOPE-CORRECTION*.md` artefacts contain the empirical R-trajectory data that motivated the split. This ADR cites those artefacts as primary evidence and records the operator authorisation as a separate, searchable decision-record entry.

## Justification

The "good-enough fixpoint with TF-tracked residuals" framing was explicitly rejected by the operator as transparent-descope (per `feedback_split_not_descope.md`). Splitting bounded the per-slice review surface to a tractable size where each R-cycle's fix-round produced a net reduction in MAJ-count without re-introducing equal defect-density in the just-added code. The diagnosis was confirmed empirically: 024B-core converged in 1–2 R-cycles after the first split; 024B-extras-1 converged after 30 R-cycles (more than expected, surfaced 4 mock-masking CRITs along the way); 024B-extras-2 converged at criterion (a) after 4 R-cycles.

## Cross-references

- `docs/reviews/WP-SCP-024/024B-core/SCOPE-CORRECTION-2026-05-09.md` — first split operational artefact (empirical R-trajectory + justification body).
- `docs/reviews/WP-SCP-024/024B-extras/SCOPE-CORRECTION-2-2026-05-11.md` — second split operational artefact.
- `docs/DECISIONS.md` D-044 (024B-core ratification) — accepted 2026-05-09.
- `docs/DECISIONS.md` D-047 (024B-extras-1 ratification) — accepted 2026-05-10.
- `docs/DECISIONS.md` D-048 (024B-extras-2 depth-defense surface ratification) — accepted 2026-05-13.
- `docs/plans/WP-SCP-024-estate-cascade.md` §6 (slice plan table; "024B split note" annotation).
- `feedback_split_not_descope.md` — auto-memory rule that motivates the framing.
- `feedback_asymptotic_trajectory_split.md` — auto-memory rule applied at the 024B-extras → 024B-extras-2 split.

## Status

ACCEPTED. All three sibling slices (024B-core + 024B-extras-1 + 024B-extras-2) merged; D-044 + D-047 + D-048 filed; 024B-extras-parking branch preserved as audit trail. 024C remains gated on FUP-ACC-INSTALL-TARGET-REPO-001 (ACC-side, not SCP-side).
