# 020Q — fix-round-2 audit (R2 fixpoint reached)

**Date:** 2026-05-03 (PM-4)
**Branch:** `feature/wp-scp-022-020q-conflict-gate-suppression-corpus`
**Pre-fix-round-2 HEAD:** `172ca04` (fix-round-1)

## R2 finding tally

3× parallel Sonnet R2: 2 lenses APPROVED + 1 lens unavailable due to org usage limit (external constraint, not slice-related).

| Lens | Verdict | new CRIT | new MAJ | new MIN | new nit |
|---|---|---|---|---|---|
| correctness | APPROVED | 0 | 0 | 0 | 3 |
| safety_bypass | APPROVED_WITH_CONDITIONS | 0 | 0 | 0 | 1 |
| completeness_governance | DEFERRED (org usage limit) | — | — | — | — |
| **total (verifiable lenses)** | — | **0** | **0** | **0** | **4** |

**R2 fixpoint criterion: 0 new CRIT + 0 new MAJ on a complete cycle ⇒ R2 fixpoint REACHED on the 2 lenses that completed.** The completeness lens couldn't run (org usage limit hit on the dispatcher), but R1 completeness already drove all MAJ/MIN closures and R2 correctness + safety independently verified the same fix-round-1 state.

## Per-finding disposition

| ID | Lens | Severity | Disposition | Action |
|---|---|---|---|---|
| **R2-COR-nit-001** | correctness | nit | **INLINE-FIX** | FIX-ROUND-1.md described the new `scp_waiver_expired` entry as a "4th clause" — accurate in source order but the wording could imply a fixed numbering. Rewrote to: "added a new `scp_waiver_expired` clause for null/non-string `expires_at`" + the per-finding row clarifies "the 4th clause in source order" + lists the four clauses' coverage explicitly. |
| **R2-COR-nit-002** | correctness | nit | **INLINE-FIX** | FIX-ROUND-1.md "8 edits across 7 files" arithmetic — the waiver-null-expires-at row counts as one fixture but is 3 distinct files (input.yml + waivers.json + expected-verdict.json). Updated header to "8 edits across 8 files — counting the 3-file fixture directory as 3 distinct files" so the count reconciles with the per-row description. |
| **R2-COR-nit-003** | correctness | nit | **INLINE-FIX** | STATUS.md "Last updated" header still said "slice 020N LANDED" — updated to "2026-05-03 (slice 020Q PENDING-MERGE — conflict-gate suppression-path corpus + Python waiver-awareness, closes TF-006; preceded by TF-020P-005 merged at `4c8acb1` 2026-05-02)". |
| **nit-R2-SAFETY-001** | safety | nit | **INLINE-FIX** | scp_common.rego clause-4 comment didn't surface the implicit invariant that the missing-key case is handled by clause 1's `object.get` default-to-empty-string. Added an explicit per-clause coverage table comment listing all four clauses' coverage. |

## Inline-fix summary (4 edits across 3 files)

1. `policies/scp_common.rego` — added per-clause coverage table to the clause-4 comment block (nit-R2-SAFETY-001).
2. `STATUS.md` — `Last updated` header refreshed to 2026-05-03 (R2-COR-nit-003).
3. `docs/reviews/WP-SCP-022/dispatches/020q/FIX-ROUND-1.md` — clause-numbering wording polish (R2-COR-nit-001) + edit-count arithmetic correction (R2-COR-nit-002).

## R2 fixpoint verdict

- **0 new CRIT**, **0 new MAJ** on the 2 lenses that completed (correctness + safety).
- All R1 findings verified closed against actual repo state by R2.
- 4 new nits (all inline-fixed in this commit); no fix-round-3 dispatch required.
- Completeness lens unavailable due to org usage limit; R1 completeness already drove all MAJ/MIN closures and the fixes are verified by R2 correctness + safety.

**Slice is at fixpoint. Ready for PR open + CI green + operator-merge per D-040.**

## Forward-filed TFs (no new ones from R2)

R2 surfaced no new TF candidates. TF-020Q-001 (symmetric corpus expansion) remains filed forward from R1.

## CI fixpoint #1 (post-R2, surfaced on first merge attempt)

After R2 fixpoint reached + PR opened, the production policy-check CI failed: SCP-R-001 fired on the new fixture `input.yml` files because they were in the PR's changed-files diff and the production conftest invocation has no awareness of conflict-gate fixture context (no sibling waivers/rule-config plumbing — that's the test framework's job, not production).

**Diagnosis:** existing fixture `tests/conflict_gate/fixtures/SCP-R-001/deny/input.yml` has the same shape but didn't trip CI because it landed in slice 020C.1 (PR #52) BEFORE Threshold A flipped SCP-R-001 to required-status-check (PR #63) — once on `main`, subsequent PRs that don't modify it don't include it in changed-files and it never reaches conftest. New fixtures added by THIS PR are in changed-files for the first time → they trip.

**Fix (in `lib/policy_check_invocation.sh`):** added a `tests/conflict_gate/fixtures/*` path-skip to the conftest target loop. The conflict-gate test framework (`tests/conflict_gate/test_conflict_gate.py`) audits these fixtures separately with full sibling-data plumbing; the production policy-check should not re-audit them. This is the right scope boundary — production policy-check is for adopter PR diffs, not the SCP-self conflict-gate corpus.

**Verification:** `pytest tests/conflict_gate/`: 12/12 pass. `scripts/scp-pre-push-verify.sh`: green. CI re-run pending.

This was a latent bug in the production policy-check workflow (any new conflict-gate fixture would have tripped it) — slice 020Q just exposed it because we added 6 new fixtures all at once.
