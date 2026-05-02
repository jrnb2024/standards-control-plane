# TF-020P-005 — fix-round-1 audit (R1 → fix → R2 candidate)

**Date:** 2026-05-02 (PM-4)
**Branch:** `feature/wp-scp-022-tf-020p-005-pre-push-verify`
**Pre-fix-round-1 HEAD:** `7b29dbc` (initial impl + DISPATCH-NOTE)

## R1 finding tally

3× parallel Sonnet R1 (correctness / safety_bypass / completeness_governance) reached APPROVED + APPROVED + CHANGES_REQUESTED.

| Lens | Verdict | CRIT | MAJ | MIN | nit |
|---|---|---|---|---|---|
| correctness | APPROVED | 0 | 0 | 0 | 2 |
| safety_bypass | CHANGES_REQUESTED | 0 | 0 | 2 | 2 |
| completeness_governance | APPROVED | 0 | 1 | 2 | 3 |
| **total** | **CHANGES_REQUESTED** | **0** | **1** | **4** | **7** |

## Per-finding disposition

### MAJ (1)

| ID | Lens | Disposition | Notes |
|---|---|---|---|
| **COMP-MAJ-001** | completeness | **NO ACTION — VERIFIED** | Reviewer flagged because executable bit cannot be confirmed via file-read alone. `git ls-files --stage scripts/scp-pre-push-verify.sh` returned `100755 ... scripts/scp-pre-push-verify.sh` — executable bit is set in the index. The MAJ is operationally a process-pending verification step, not a design gap. Closes immediately. |

### MIN (4)

| ID | Lens | Disposition | Inline-fix |
|---|---|---|---|
| **MIN-SAFE-001** | safety | **INLINE-FIX** | Tightened version-drift warning text from "may diverge" to "wrapper results may not match CI; install the pinned version or treat wrapper output as advisory only". One-line edit at `scripts/scp-pre-push-verify.sh` line 109. |
| **MIN-SAFE-002** | safety | **INLINE-FIX** | Added "Audience: SCP-repo rule authors only" paragraph at the head of `ADOPT-001` §12.7.9.1 explicitly excluding adopter repos and disclaiming the parent §12.7.9 SHA-pinning warning. One-paragraph addition. |
| **COMP-MIN-001** | completeness | **TF-FORWARD** | §12.7.9.1 audience placement under §12.7.9. Reviewer said "acceptable for v1.1.0". MIN-SAFE-002 inline-fix (audience clarifier) addresses the immediate confusion risk; full structural reorg deferred to next ADOPT-001 pass. Filed forward as **TF-020P-005b**. |
| **COMP-MIN-002** | completeness | **INLINE-FIX** | Wrapper line 31 amended `§12.7.9` → `§12.7.9.1`. One-line edit. |

### nit (7)

| ID | Lens | Disposition | Notes |
|---|---|---|---|
| **COR-nit-001** | correctness | **INLINE-FIX** | Made OPA + regal version parsers symmetric. Both now `awk -F':'` + `gsub(/[[:space:]]/, "", $2)`. Robust to any future whitespace padding change. Two-line edit + one-comment addition. |
| **COR-nit-002** | correctness | **INLINE-FIX** | Removed `printf ''` no-op in `read_pinned_version`; bare `return` is clearer. One-line edit. |
| **nit-SAFE-003** | safety | **NO ACTION** | PATH-resolution of opa/regal/git/find/awk is the documented design. SHA-verified bootstrapping is `scripts/scp-policy-check`'s scope per DISPATCH-NOTE. Reviewer agreed; no fix required. |
| **nit-SAFE-004** | safety | **NO ACTION** | The `[ -e "${rule_file}" ] || continue` glob-empty guard is a well-known bash idiom; no nullglob change needed. Reviewer agreed; no fix required. |
| **COMP-NIT-001** | completeness | **NO ACTION** | AC items (xii)–(xiv) are correctly process-pending. |
| **COMP-NIT-002** | completeness | **NO ACTION** | "Run Conftest tests" mislabeling exists only in the pre-PR STATUS.md description; the closing record correctly names `opa test`. Implementation is correct. |
| **COMP-NIT-003** | completeness | **TF-FORWARD** | `SCP_PRE_PUSH_VERSION_STRICT=1` env var to make parity-check fatal — opportunistic feature flag. Filed forward as **TF-020P-005c**. |

## Inline-fix summary (5 edits across 2 files)

1. `scripts/scp-pre-push-verify.sh` line 31: `§12.7.9` → `§12.7.9.1` (COMP-MIN-002).
2. `scripts/scp-pre-push-verify.sh` `read_pinned_version`: removed `printf ''` no-op (COR-nit-002).
3. `scripts/scp-pre-push-verify.sh` `read_installed_opa_version`: now uses `awk -F':'` + `gsub` (COR-nit-001).
4. `scripts/scp-pre-push-verify.sh` `check_version_parity`: tightened warning text (MIN-SAFE-001).
5. `docs/adoption/ADOPT-001-project-onboarding.md` §12.7.9.1: added explicit-audience paragraph (MIN-SAFE-002).

## Forward-filed TFs

- **TF-020P-005b** (low priority): ADOPT-001 §12.7.9.1 audience-placement reorg; opportunistic next ADOPT-001 structural pass.
- **TF-020P-005c** (very low priority): `SCP_PRE_PUSH_VERSION_STRICT=1` env var; opportunistic; second-requestor signal.

## Smoke-test post-fix

`scripts/scp-pre-push-verify.sh` re-run against `policies/` tree at fix-round-1 HEAD:
```
✓ scp-pre-push-verify: all 3 SCP-R gates pass
```
All three gates clean; OPA test coverage at 99.04% (well above 90% threshold) for the loaded rule × test pair under verification. No regression.

## R2 candidacy

R1 surfaced 0 CRIT findings and 1 MAJ that resolved as no-action-needed (executable bit verification). All MIN findings are closed (3 inline-fixed + 1 TF-forwarded with inline-fix supplementing). All nits are closed (2 inline-fixed + 4 no-action + 1 TF-forwarded — COMP-NIT-003 → TF-020P-005c). The slice is ready for **R2 dispatch** to verify no NEW CRIT/MAJ findings emerge against the fix-round-1 surface. Per `feedback_recursive_adversarial_review.md` fixpoint criterion: R2 must surface 0 CRIT + 0 MAJ on a complete cycle.
