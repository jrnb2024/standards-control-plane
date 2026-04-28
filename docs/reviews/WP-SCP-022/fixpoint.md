# WP-SCP-022 — Adversarial-review fixpoint record

**Plan version at fixpoint:** v0.5
**Date:** 2026-04-28
**Round count:** 5 (R1 → v0.2 → R2 → v0.3 → R3 → v0.4 → R4 → v0.5 → R5 → fixpoint)
**Fix-round budget:** 5 used of 5 (full budget consumed)
**Total wall-clock:** ~50 min review compute (5 rounds × 3 reviewers × ~8 min average)
**Cumulative review spend:** ~$10 (well under the $30/slice budget cap defined in §8 R-022-07)

## Fixpoint criteria

Per WP-SCP-022 §4.3:

> All three either APPROVED or APPROVED_WITH_FINDINGS where every finding is MIN or nit (no CRIT, no MAJ) → Fixpoint reached → slice merges; MIN/nit findings recorded in `fixpoint.md` as known-acceptable issues.

R5 verdicts:

| Lens | Verdict | Findings |
|------|---------|----------|
| correctness | APPROVED_WITH_FINDINGS | 0 CRIT, 0 MAJ, 0 MIN, 1 nit |
| safety_bypass | APPROVED_WITH_FINDINGS | 0 CRIT, 0 MAJ, 1 MIN, 2 nit |
| completeness_governance | APPROVED_WITH_FINDINGS | 0 CRIT, 0 MAJ, 1 MIN, 2 nit |

All three: APPROVED_WITH_FINDINGS, MIN/nit only. **Fixpoint reached.**

## Round-by-round trajectory

| Round | Verdict combination | Aggregate findings | Outcome |
|-------|---------------------|--------------------|---------|
| R1 | 3× CHANGES_REQUESTED | 10 CRIT + 16 MAJ + 9 MIN + 2 nit | v0.2 |
| R2 | 3× CHANGES_REQUESTED | 0 CRIT + 9 MAJ + 6 MIN + 5 nit | v0.3 |
| R3 | 2× CHANGES_REQUESTED + 1× APPROVED_WITH_FINDINGS | 0 CRIT + 3 MAJ + 4 MIN + 4 nit | v0.4 |
| R4 | 1× CHANGES_REQUESTED + 2× APPROVED_WITH_FINDINGS | 0 CRIT + 1 MAJ + 5 MIN + 4 nit | v0.5 |
| R5 | 3× APPROVED_WITH_FINDINGS | 0 CRIT + 0 MAJ + 2 MIN + 5 nit | **Fixpoint** |

Every round caught real bugs:
- R1: slice-ordering errors against WP-SCP-020 §3 (3 CRIT); /tmp staging race + scope-boundary post-hoc + signer prompt-injection (4 CRIT in safety lens).
- R2: helper scripts specified in plan but only stub-implemented (3 of 9 MAJ); D-027/D-028 in DECISIONS.md not updated when plan body was rewritten.
- R3: helper-script path bug (no-fix-rounds branch); signer-pattern over-permissive substring; missing self_reported_concerns sanitization.
- R4: GitHub REST API verb wrong (PATCH→POST for required_signatures — would have blocked slice 020J on every dispatch).
- R5: only MIN/nit residuals.

## Hash chain (machine-verifiable signature)

Per §4.5 / §4.7 — each leaf is `sha256(<file>)` of the terminal-round
reviewer-result JSON; root is `sha256(correctness || safety || completeness)`.

## sha256_chain
correctness: b76dfc2ce2ca2df5892e13948079cd5dd2b709ec36f057259f656d21a72d2ba3
safety: 5d509970665e5cb2f1440bbf091a2d48d5437a1aadd1f64fc84c3a92d3c9bec1
completeness: 79ddba1af05a5421f07bb90ba116735fdfb60883262125c747ba3c777407aa16
chain: ba82c55ddc0388177dd327dafd4e6c403fe7f866ab71d8f3207ba90a24858f27

Source files:
- `r5-correctness/dispatcher-result.json`
- `r5-safety/dispatcher-result.json`
- `r5-completeness/dispatcher-result.json`

(The plan-slice's hash-chain is recorded here as a self-test of the
sha256_chain block format. Implementation slices will have their own
fixpoint.md records under
`docs/reviews/WP-SCP-022/dispatches/<slice-id>/fixpoint.md` per §4.5.)

## Recorded MIN/nit residuals (do NOT block merge)

These were surfaced at R5 and accepted as known-acceptable issues per
§4.3. Each is small enough to address in a post-merge cleanup PR or to
defer with a follow-up backlog row.

### Correctness lens (R5)

- **R5-C-nit-01** — `check_acc_pin()` calls `require_cmd jq python3` but
  python3 is unused inside the function body. Same pattern as R4-C-nit-01
  (which was fixed in `check_hash_chain` only — `check_acc_pin` was not
  swept). Trivial 1-line fix.

### Safety lens (R5)

- **R5-BYPASS-001 (MIN)** — `_looks_like_review_result` heuristic in
  `sanitize_review_finding.py` accepts a finding dict with a valid
  verdict enum value AND `findings=[]` (empty list). In that edge
  case the finding's own `claim`/`evidence`/`impact`/`mitigation`
  fields skip per-finding sanitization. Real-world impact is low —
  empty findings array means no payload-bearing fields would reach
  Codex anyway — but a tighter heuristic could require non-empty
  findings list OR distinguish on presence of `id`+`severity` keys.
- **R5-BYPASS-002 (nit)** — `plan_version` not in
  `_REVIEW_RESULT_TOP_STRING_FIELDS`. The R4 mitigation explicitly
  recommended adding it; was overlooked.
- **R5-BYPASS-003 (nit)** — same as R5-C-nit-01 (`check_acc_pin`
  python3 over-broad require). Counted twice across lenses.

### Completeness lens (R5)

- **F-R5-001 (MIN)** — §6 manifest-integrity wording asserts
  WP-SCP-020 §4 020D2 sets `require_code_owner_reviews: true`, but
  WP-SCP-020 §4 020D2 does not explicitly include this flag in its
  list of branch-protection settings. Real-world impact: when slice
  020D2 is dispatched, Codex reading WP-SCP-020 §4 020D2 won't apply
  the flag and the manifest CODEOWNERS protection won't enforce.
  **Mitigation (open as separate cleanup PR):** amend WP-SCP-020 §4
  020D2 to add `require_code_owner_reviews: true` to the branch-
  protection list, OR reword §6 to say the flag is set in slice
  020D2's actual dispatch package instruction (not in the plan
  document itself).
- **F-R5-002 (nit)** — §4.1 verify_commands guidance doesn't cross-
  reference §8 R-022-13 for the 020J-specific API verify pattern.
- **F-R5-003 (nit)** — `scripts/wp_scp_022_gate_check.sh` line 51
  defines `SCP_OPERATOR_EMAIL` (singular) but the active mechanism
  uses `SCP_OPERATOR_EMAILS` (plural). The singular variable is
  unused dead code.

## Action items post-fixpoint (small follow-up PRs)

1. **WP-SCP-022 cleanup** — close the 5 MIN/nit residuals above via a
   single small follow-up PR (`chore/wp-scp-022-fixpoint-cleanup`)
   targeting the merged plan branch. Estimated diff: ~15 lines across
   plan + helper scripts.
2. **WP-SCP-020 §4 020D2 amendment** — add
   `require_code_owner_reviews: true` to the branch-protection list
   per F-R5-001 closure path. ~1 line.

These follow-ups are NOT blockers for opening the WP-SCP-022 plan PR
or for dispatching the first implementation slices. They are tracked
on backlog as part of the WP-SCP-022 close-out hygiene.

## Verdict

**WP-SCP-022 v0.5 plan reaches Gate-C fixpoint at R5.** PR is opened
against `main`. Implementation slices may begin dispatch per the plan
once the PR merges.

The 5-round adversarial review process detected and closed:
- 10 CRITs (slice-ordering, race conditions, prompt-injection,
  hard-stop absence)
- 26 MAJs (helper-script bugs, decision-record inconsistencies, REST
  API verb bug, signer-pattern issues, etc.)

Per `feedback_recursive_adversarial_review.md` (mandatory from
2026-04-22) the review process is complete with no descoping, no
silent fixes, and full evidence trail in
`docs/reviews/WP-SCP-022/r{1..5}-{correctness,safety,completeness}/`.
