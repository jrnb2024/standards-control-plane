# TF-PIM-001 impl WP — R2 synthesis (v0.3)

**Reviewed:** 2026-05-21 PM-2 (impl WP plan-doc v0.3 at `d704c82`)
**Lenses dispatched:** sec / arch-skeptic / pragmatist (same shape as R1; Plan agents read-only; DO-NOT-EDIT mandate cited at sample-size-3 incidents)

---

## R2 convergence — 2/3 R-FIXPOINT-MET; 1/3 DIMINISHING-RETURNS

| Lens | Verdict | Convergence signal | R1 closures | New findings |
|---|---|---|---|---|
| sec | ACCEPT | R-FIXPOINT-MET | 3/3 CLOSED | 0 |
| arch-skeptic | ACCEPT-WITH-AMENDMENT | DIMINISHING-RETURNS | 6/6 CLOSED | 1 MIN (ARCH-MIN-001-R2) |
| pragmatist | ACCEPT | R-FIXPOINT-MET | 3/3 CLOSED | 0 |

**Total: 12/12 R1 findings CLOSED + 1 new MIN finding in v0.3 (`ARCH-MIN-001-R2`).**

## ARCH-MIN-001-R2 — the one new finding

The ARCH-MAJ-001 closure in v0.3 §7.5a step 3 correctly replaces `enable-required-check.sh --restore` with a `gh api -X PATCH` block. However, the illustrative PATCH hard-codes only ONE of FOUR SCP-self required contexts:

- Names: `check-invocation-log-entry`
- Drops (if executed verbatim): `policy-check-readback`, `validate PR body`, and `policy-check / scp/policy-check` (intentional removal by design)

Wave F step 2 names all 4 required contexts. The pre-state capture (`/tmp/scp-main-pre-rollback.json`) is provided but the operator is not instructed to use it for restoration. Under rollback time-pressure, an operator executing the illustrative PATCH verbatim would silently weaken SCP main's branch protection by dropping `policy-check-readback` and `validate PR body`.

**Severity:** MIN. Fires only in the rollback hot-path (Wave D regression + Wave F failure compound), not on the happy path. arch-skeptic flagged this as DIMINISHING-RETURNS (not REVISE) because the v0.3 document is materially correct + operationally ready on all load-bearing decisions; the remaining gap is documentation precision in a rare-path procedure.

**Amendment options:**
- **(a)** `jq`-based extraction of contexts from the captured pre-state JSON, fed into the restoration PATCH — strictly stronger; restoration becomes state-restore not memory-reconstruction
- **(b)** Explicit warning annotation: "verbatim execution would drop X and Y; always reconstruct from pre-state capture"

Option (a) chosen for v0.4 — strictly stronger.

## Option A R4 mechanical override (v0.4 declared R-fixpoint MET)

Per operator authorisation 2026-05-21 ("Cure-worse trigger + Option A R4 mechanical override at R3 if diminishing-returns") and `feedback_asymptotic_trajectory_split.md`:

- 2/3 lenses already at R-FIXPOINT-MET
- 1/3 lens at DIMINISHING-RETURNS (NOT REVISE; explicit signal that document is materially correct)
- The one outstanding finding (ARCH-MIN-001-R2) is documentation precision; closure is a single edit
- Continuing to full R3 dispatch (3 lenses re-reading the entire 600-line plan-doc) for one MIN finding closure is exactly the diminishing-returns trajectory the override is designed to short-circuit

**v0.4 mechanical-override fold:**
1. Apply ARCH-MIN-001-R2 closure (Option (a) — `jq`-based extraction)
2. Update R-cycle changelog with v0.4 row + Option A R4 mechanical override declaration
3. R-fixpoint MET at v0.4 (no R3 dispatch required)

The override is conservative — it does NOT skip any earlier review (R1 fired; R2 fired); it short-circuits the redundant R3 that would burn sub-agent compute on a document the lenses already converged was materially correct.

## Cross-cutting strengthening since R1

- v0.3 amendments were surgical and targeted (12 closures in <100 lines of edits)
- No cure-worse-than-disease pattern at the load-bearing-decisions level — only the one MIN finding in rollback hot-path
- All 3 lenses' R1 specs landed in v0.3 with citable text + inline "(v0.3 ... closure)" annotations for audit trail
- v0.3 stands ready for ready-flip + operator-attended merge per Wave B precedent (ADR-class merge ceremony for the impl plan-doc that gates Tier 2 Codex dispatch)

## v0.4 fold scope

Single edit: §7.5a step 3 PATCH block → jq-extraction from pre-state JSON.

R-fixpoint MET declared post-v0.4 push via Option A R4 mechanical override; no R3 sub-agent dispatch.

## Next steps post v0.4

1. Push v0.4 (CI verify)
2. Update PR #134 body to reflect R-fixpoint MET via R2 + Option A R4 override
3. Flip PR #134 DRAFT → ready
4. STANDDOWN for operator-attended merge ceremony per Wave B precedent
   - Operator reviews v0.4 rendered PR
   - Operator merges via explicit gh pr merge OR explicit paste-back authorisation
   - Mechanical auto-merge NOT authorised (impl plan-doc gates Tier 2 dispatch; equivalent to ADR-class artefact)
5. Post-merge: Wave A operator-attended ceremony begins
