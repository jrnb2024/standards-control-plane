# WP-SCP-022 slice 020L — FIX-ROUND-3 (post-R2 framework amendment)

**Date:** 2026-05-02
**Branch:** `feature/wp-scp-022-020l-rule-rfc-dogfood`
**HEAD pre-fix-round-3:** `a918234` (fix-round-2 / R2 fixpoint)
**Trigger:** operator-surfaced framework gap when reviewing merge-readiness of PR #89 post-R2 fixpoint.

## What surfaced

After R1+R2 fixpoint was reached on RULE-001 (the proposal text + RFC framework was at fixpoint with 0 BLOCKING outstanding), operator review of merge-readiness identified that the README's prescription of "operator merges after the 48h window has elapsed" was **vestigial** in single-operator mode:

- The 48h wall-clock window exists to give external reviewers wall-clock time to chime in.
- In single-operator mode (D-031 default at v1.0.0), the proposal author IS the only `SCP-CODEOWNERS` member.
- There are no external reviewers; the recursive 3-lens R1/R2 adversarial review IS the adversarial-review surface.
- The wall-clock pause is therefore theatre rather than safety in single-operator mode.

This is the kind of process gap the dogfood is **designed** to surface cheaply — the first RFC actually walking through the process exposed an operational reality that the framework hadn't anticipated.

## Closure

The clean fix is doctrinal — amend the framework to reflect operational reality, ratified by a D-NNN row.

### README.md amendment (`docs/reviews/rule-proposals/README.md`)

§Process step 2 amended:

- **Single-operator self-approval shape** bullet revised to drop the "after 48h has elapsed" phrasing — quorum-1 is satisfied by the operator's explicit merge action, recorded in PR description / trailing comment.
- **NEW bullet "48h window is a CEILING, not a FLOOR, in single-operator mode"** — operator may merge as soon as adversarial-review fixpoint is reached AND PR is open with the `scp-rule-proposal` label. The 48h CEILING remains for the auto-defer trigger.
- **Window (non-bypass proposals)** bullet revised to make the CEILING-vs-FLOOR distinction explicit.

### Bypass-introducing proposals — non-waivable 48h MINIMUM **preserved**

The non-waivable 48h window for bypass-introducing proposals (`Bypass-surface non-empty: true` per 020H.1 R1 SAFE-MAJ-001 closure) is **NOT changed** by D-040. The threat-surface justifies the wait even in single-operator mode: the operator may catch their own bypass-introducing PR's flaws on second look more reliably than for a non-bypass additive rule. The non-waivable minimum is unchanged.

### Post-2nd-maintainer-onboard posture

When a second maintainer onboards (D-031 escalation, 2026-07-21 review), the 48h becomes a mandatory **MINIMUM** to give the second maintainer time to review. The CEILING-not-FLOOR posture is single-operator-only. The README amendment names this explicitly.

### D-040 filing

`docs/DECISIONS.md` row D-040 ratifies the amended posture. Decision text + rationale captured in the canonical decision-record home rather than buried in this DISPATCH-NOTE. Symmetric with D-033's "operational reality must amend the spec when the spec encounters a constraint that wasn't anticipated" pattern.

### DISPATCH-NOTE.md criterion (xiv) update

Criterion (xiv) updated to reference D-040 and reframe the 48h as a CEILING in single-operator mode.

## Why fix-round-3 is not a third R-cycle

Per `feedback_recursive_adversarial_review.md`, fixpoint = "no new CRIT/MAJ findings on a complete cycle". R2 reached fixpoint (0 new CRIT/MAJ on the proposal-text + R1-closure surface). The framework amendment is operator-surfaced, not reviewer-surfaced — it falls outside the lens-package surfaces dispatched in R1+R2. Treating it as a third R-cycle would require dispatching new lens packages targeting the framework amendment itself, which would loop indefinitely (every framework amendment generates new framework-amendment surfaces). The pragmatic disposition is to record the amendment in this fix-round-3 + ratify by D-040 + merge.

If a future framework amendment of this magnitude surfaces post-R2, the operator may dispatch a targeted R3 against the amendment itself. For 020L, the amendment is small (3 README bullets + 1 D-NNN row + 1 DISPATCH-NOTE bullet update) and its substance has been reasoned about explicitly in the D-040 row's rationale column.

## Files touched in fix-round-3

- `docs/reviews/rule-proposals/README.md` — §Process step 2 amendment (3 bullets revised/added).
- `docs/DECISIONS.md` — D-040 row added.
- `docs/reviews/WP-SCP-022/dispatches/020l/DISPATCH-NOTE.md` — criterion (xiv) wording.
- `docs/reviews/WP-SCP-022/dispatches/020l/FIX-ROUND-3.md` (this file).

## Posture for merge

The proposal is at recursive-adversarial-review fixpoint AND the framework amendment surfaced post-R2 is closed via D-040. Per the amended README §Process step 2, the operator MAY merge PR #89 as soon as CI is green.

Cumulative across the slice:
- R1: 0 CRIT + 7 MAJ + 6 MIN + 4 nit closed.
- R2: 0 CRIT + 0 MAJ + 2 MIN (TF-020L-002, TF-020L-003) + 3 nit (non-actionable).
- Post-R2 framework amendment: D-040 ratifies single-operator 48h-CEILING-not-FLOOR posture.

Total: 17 review findings + 1 framework amendment + 3 forward-tracked TFs (TF-020L-001, 002, 003). 0 BLOCKING outstanding at merge time.
