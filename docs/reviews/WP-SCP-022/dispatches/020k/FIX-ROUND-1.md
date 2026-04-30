# WP-SCP-022 slice 020K — fix round 1

**Date:** 2026-04-30 (afternoon)
**Triggered by:** R1 review × 3 (correctness / safety_bypass / completeness_governance) all returned with findings.

## R1 verdicts

| Lens | Verdict | Findings |
|---|---|---|
| correctness | NEEDS_FIXES | 1 MAJ + 1 nit |
| safety_bypass | REJECTED | 6 MAJ + 2 MIN + 3 nit |
| completeness_governance | CHANGES_REQUESTED | 1 MAJ + 2 nit |

## Findings addressed in this fix round

### From safety_bypass review (CODEOWNERS path-coverage gaps)

- **SAFE-001 (MAJ)** — `docs/security/mcp-signing-keys.pub` not covered. **Closed:** added `docs/security/** @jrnb2024`.
- **SAFE-002 (MAJ)** — `output/findings/open-findings.json` not covered. **Closed:** added `output/findings/** @jrnb2024`.
- **SAFE-003 (MAJ)** — `output/findings/false-positive-summary.json` not covered. **Closed:** subsumed by `output/findings/**`.
- **SAFE-004 (MAJ)** — `output/findings/findings-history.json` not covered. **Closed:** subsumed by `output/findings/**`.
- **SAFE-005 (MAJ)** — `docs/adoption/ADOPT-001-project-onboarding.md` not covered. **Closed:** added `docs/adoption/** @jrnb2024`.
- **SAFE-006 (MAJ)** — `docs/plans/**` not covered (retroactive spec tampering surface). **Closed:** added `docs/plans/** @jrnb2024`.
- **SAFE-007 (MIN)** — `docs/security/branch-protection.md` not covered. **Closed:** subsumed by `docs/security/**`.
- **SAFE-008 (MIN)** — `output/control-tower/**` and `output/ci/**` not covered (cross-repo compliance reporting). **Closed:** added both wildcards.
- **SAFE-009 (nit)** — last-match-wins ordering invariant. **Closed:** added an inline ORDERING INVARIANT comment block to CODEOWNERS noting that future broad-wildcard rules MUST be added BEFORE the specific governance rules.
- **SAFE-010 (nit)** — case-sensitivity note. **No-op:** documented as maintenance invariant, no code change required.
- **SAFE-011 (nit)** — 2026-07-21 diary entry could be automated. **Deferred:** scheduled-workflow automation tracked for a follow-up slice; the diary entry stands.
- **SAFE-012 (nit)** — `renovate/**` confirmed harmless. **No-op:** confirmed in D-031 rationale.

### From correctness review

- **COR-001 (MAJ)** — bypass-gate regex `D-0[0-9]{3}` in WP-SCP-020 §4 020B(viii-c) requires a four-digit suffix and would never match the actual three-digit IDs (D-001..D-031), permanently blocking any future break-glass bypass attempt under the spec. **Closed:** corrected to `D-[0-9]{3}` in plan §4 020B(viii-c) text + dispatch note. Verified `scripts/verify-bypass-pairing.sh` already implements the corrected pattern; this is a spec-text fix only.
- **COR-002 (nit)** — STATUS.md 020K progress line used shortened phrasing. **Closed:** updated to `personal-account / single-operator` to match canonical phrasing.

### From completeness_governance review

- **CG-MAJ-001 (MAJ)** — WP-SCP-020 §8 line 188 bus-factor-1 risk row carried two stale `scp-break-glass team` references that contradicted 020K AC(a) and D-031(a). An operator following §8 directly would attempt to add a second maintainer to a team that was never created. **Closed:** rewrote §8 line 188 to reflect the U-k personal-account resolution — single-operator phrasing, no team reference, escalation step `(a) add them to CODEOWNERS` (was `(a) scp-break-glass team, (b) SCP-CODEOWNERS, (c) flip flag, (d) amend risk row`).
- **CG-nit-002 (nit)** — §8 risk row lacked `[LIVE]` status badge. **Closed:** added `**[LIVE]**` prefix, plus `**[CLOSED]**` reference in the escalation path so future state changes are explicit.
- **CG-nit-003 (nit)** — MEMORY.md index entry for `project_scheduled_followups.md` did not reflect the two new entries (2026-07-21 and 2026-07-30). **Closed:** updated the one-line hook to include all current dates: D-021 (2026-05-31), Phase 2 notice (2026-07-02), 020K bus-factor-1 review (2026-07-21), 020J branch-protection review (2026-07-30), bearer-legacy close (2026-09-30).

## Files modified in this fix round

- `CODEOWNERS` — 6 new wildcard rules + ORDERING INVARIANT comment block.
- `docs/plans/WP-SCP-020-policy-federation-primitive.md` — §4 020B(viii-c) regex fix; §8 line 188 rewrite + `[LIVE]` badge.
- `STATUS.md` — 020K progress-line phrasing.
- `~/.claude/projects/.../memory/MEMORY.md` — scheduled-followups index entry.
- `docs/reviews/WP-SCP-022/dispatches/020k/FIX-ROUND-1.md` — this file.

## What was NOT addressed (and why)

- **SAFE-011** (automated cron for 2026-07-21 diary entry) — deferred. Adding a scheduled GitHub Actions workflow that opens an issue on 2026-07-21 is a separate slice (it adds a new workflow file + permissions discussion). The diary entry in STATUS.md + auto-memory is the v1.0.0 mechanism. Track for follow-up if the manual cadence proves unreliable.

## Next step

Recurse R1 review per `feedback_recursive_adversarial_review.md` — fixpoint requires the next round to surface no NEW blocking issues. If the next round is clean (or only repeats acknowledged-deferred items), 020K merges.
