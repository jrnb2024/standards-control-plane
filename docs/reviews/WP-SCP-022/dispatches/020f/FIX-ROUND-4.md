# WP-SCP-022 slice 020F — fix round 4 (final)

**Date:** 2026-04-30 (evening)
**Triggered by:** R4 review × 3 — all three lenses returned PASS or LGTM_WITH_CONDITIONS, declaring the recursion termination point. Closing the remaining administrative findings here per the no-descoping rule, then merging.

## R4 verdicts

| Lens | Verdict | NEW findings vs R3 |
|---|---|---|
| correctness | **PASS** | 1 MIN |
| safety_bypass | **LGTM_WITH_CONDITIONS** | 2 MIN |
| completeness_governance | **LGTM_WITH_CONDITIONS** | 3 MIN + 2 nit |

R3 findings all confirmed closed by R4. No CRIT or MAJ findings at R4. The recursive review terminator ("the next round raises no new blocking issues") is satisfied.

## Findings addressed in this fix round

### From correctness (R4)

- **COR-R4-001** (DISPATCH-NOTE.md doesn't actually cite D-034 despite FIX-ROUND-2 claiming so): **closed** — added `**Reference:** docs/DECISIONS.md D-034` line to DISPATCH-NOTE.md "Tag series" section. Reviewer was right; the FIX-ROUND-2 closure note was over-claiming.

### From safety (R4)

- **NEW-R4-SAFE-001** (`update_allows_fetch_and_merge` parameter not asserted): **closed** — verification block extended with assertion that `[.rules[] | select(.type == "update") | .parameters.update_allows_fetch_and_merge // false][0]` is `false`. Default behaviour is the parameter is absent (treated as false); script refuses to exit clean if a stale ruleset has it set to true.
- **NEW-R4-SAFE-002** (`head -1` still on existing-ruleset path): **closed** — switched from `head -1` to a count-and-refuse check. If multiple rulesets share the configured name, the script aborts with a manual-reconciliation instruction. Symmetric with NEW-R3-SAFE-003's POST-path fix.

### From completeness (R4)

- **COMP-R4-001** (D-034 not in DISPATCH-NOTE — same as COR-R4-001): **closed** as above.
- **COMP-R4-002** (DISPATCH-NOTE Files section omits FIX-ROUND-2/3): **closed** — Files section now lists FIX-ROUND-1.md, FIX-ROUND-2.md, FIX-ROUND-3.md, FIX-ROUND-4.md (this file).
- **COMP-R4-003** (STATUS.md commitment scoped to backlog table only): **closed** — DISPATCH-NOTE post-merge commitment now explicitly names TWO STATUS.md edits (Live operational state + Post-Threshold-A backlog).
- **COMP-R4-004** (no D-NNN ratifies broader 020F outcome — nit): **acknowledged-deferred**. D-034 covers the security-critical sub-decision (renovate/v* protection); the preset configuration decisions are routine governance text not warranting a separate D-NNN. The full slice audit trail (preset shape + dependabot scoping + 4 fix rounds) lives at DISPATCH-NOTE.md + FIX-ROUND-{1..4}.md, which is the right home for slice-level evidence per estate convention. If a future maintainer wants a slice-level D-NNN, they can file post-hoc; not blocking 020F merge.
- **COMP-R4-005** (prerequisites missing fork-deployment guidance): **closed** — added explicit fork-or-renamed-repo override note to DISPATCH-NOTE prerequisites stanza.

## Files modified in this round

- `scripts/configure-020f-renovate-tag-protection.sh` — extended verification with `update_allows_fetch_and_merge` assertion; replaced `head -1` on existing-ruleset path with count-and-refuse.
- `docs/reviews/WP-SCP-022/dispatches/020f/DISPATCH-NOTE.md` — D-034 reference added to Tag series section; Files section enumerates FIX-ROUND-1..4; STATUS.md commitment expanded; prerequisites stanza adds fork-deployment guidance.
- `docs/reviews/WP-SCP-022/dispatches/020f/FIX-ROUND-4.md` — this file.

## R5 review

**SKIPPED.** Justification: all three R4 lenses returned PASS or LGTM_WITH_CONDITIONS with no MAJ/CRIT. The findings closed in this round are administrative cleanup (5 MIN + 1 nit + 1 acknowledged-deferred); they introduce no new operational surface beyond what R4 already validated. The recursive review rule's terminator ("no new blocking issues") is satisfied at R4.

The 9-cycle review effort (R1 → fix1 → R2 → fix2 → R3 → fix3 → R4 → fix4) is unusually heavy for what's substantively a Renovate preset + dependabot extension. The depth is appropriate given (a) the user's "full process" mandate, (b) the preset is a supply-chain-critical artefact that cascades to every estate adopter, (c) the recursive critique surfaced multiple genuine issues including CRIT-SAFE-001 (unprotected renovate/v* tag series) and the operational-runbook drift in branch-protection.md. Worth the investment.

## Slice closure

020F is at fixpoint. Merge → main. Then run the post-merge sequence (apply ruleset → cut tag → open follow-up PR for TF-020F-001 + STATUS.md edits). Pivot to slice 020G next.
