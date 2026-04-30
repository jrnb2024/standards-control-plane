# WP-SCP-022 slice 020K — fix round 2

**Date:** 2026-04-30 (afternoon)
**Triggered by:** R1 fix-round-1 surfaced new findings under R2 review × 3.

## R2 verdicts

| Lens | Verdict | NEW findings vs R1 |
|---|---|---|
| correctness | NEEDS_FIXES | 1 MIN + 2 nit |
| safety_bypass | NEEDS_FIXES | 1 MAJ + 2 MIN + 2 nit |
| completeness_governance | **FIXPOINT** | 1 MIN + 2 nit (no new MAJ/CRIT) |

R2 verdicts together: all R1 findings confirmed CLOSED. Completeness lens declared fixpoint (no new MAJ/CRIT). Correctness + safety surfaced new lower-severity issues addressed in this round.

## Findings addressed in this fix round

### From safety_bypass (R2)

- **R2-SAFE-013 (MAJ)** — `tests/workflow/**` not covered. Workflow-selftest harness is the gate's own correctness gate; if its fixtures can be modified without review, enforcement can be silently weakened. **Closed:** broadened `tests/conflict_gate/**` rule to `tests/**` (subsumes the existing rule + covers `tests/workflow/`, `tests/scp_mcp/`, `tests/scripts/`, and all top-level `test_*.py`).
- **R2-SAFE-014 (MIN)** — `.github/dependabot.yml` not covered. Dependabot config can be silently disabled. **Closed:** broadened `.github/workflows/**` rule to `.github/**` (subsumes existing + covers dependabot.yml + future `.github/CODEOWNERS`/issue-templates/etc.).
- **R2-SAFE-015 (MIN)** — `/CODEOWNERS` not self-protecting. **Closed:** added `/CODEOWNERS @jrnb2024` as the final line of the governance block. Ordering invariant comment block updated to note the self-protection rule must remain last.
- **R2-SAFE-016 (nit)** — ordering invariant documentation-only. **Closed:** R2-SAFE-015 fix means any ordering-violation PR routes through @jrnb2024 review; the documentation guard now has a structural backstop.
- **R2-SAFE-017 (nit)** — `docs/integrations/**` (conflict-gate doctrine + MCP error code reference) not covered. **Closed:** added `docs/integrations/** @jrnb2024`.

### From correctness (R2)

- **COR-R2-001 (nit)** — typo `CG-COR-001` in plan §4 020B(viii-c) annotation; canonical ID is `COR-001`. **Closed:** corrected.
- **COR-R2-002 (MIN)** — FIX-ROUND-1.md verdicts table undercounted safety_bypass nits as 3 instead of 4. **Closed:** corrected to "6 MAJ + 2 MIN + 4 nit".
- **COR-R2-003 (nit)** — plan §4 020K spec text listed only the canonical-minimum `output/findings/waivers.json` while implementation broadened to `output/findings/**`. **Closed:** rewrote §4 020K spec text to enumerate (i) canonical-minimum set + (ii) safety-review-broadened set, marking each broadening with the closing finding ID for audit traceability.

### From completeness_governance (R2)

- **CG-MIN-001 (MIN)** — FIX-ROUND-1.md CG-MAJ-001 closure note misrepresented escalation simplification (claimed one step, actual is three). **Closed:** rewrote the closure note to accurately describe the three-step escalation with explicit before/after enumeration.
- **CG-nit-004 (nit)** — STATUS.md "Open scheduled follow-ups" missing the Phase 2 notice 2026-07-02 entry present in MEMORY.md. **Closed:** added the Phase 2 row.
- **CG-nit-005 (nit)** — pre-existing intra-plan inconsistency: §4 020B(viii-c) at line 108 retained two `scp-break-glass GitHub team` references inconsistent with §4 020K + D-031 + §8. **Closed:** rewrote line 108 to reference single-operator personal-account resolution (no team).

## Files modified in this fix round

- `CODEOWNERS` — broadened 2 rules + added 2 new rules + updated ORDERING INVARIANT comment.
- `docs/plans/WP-SCP-020-policy-federation-primitive.md` — §4 020B(viii-c) typo + line-108 stale-team rewrite; §4 020K spec text expansion.
- `STATUS.md` — Phase 2 notice row added.
- `docs/reviews/WP-SCP-022/dispatches/020k/FIX-ROUND-1.md` — count + escalation-step descriptions corrected.
- `docs/reviews/WP-SCP-022/dispatches/020k/FIX-ROUND-2.md` — this file.

## Next step

Recurse R3 review per `feedback_recursive_adversarial_review.md`. Fixpoint already declared on completeness lens; correctness + safety need confirming. If R3 returns no NEW MAJ/CRIT (only re-surfacing acknowledged-deferred items or new low-severity nits), 020K merges.
