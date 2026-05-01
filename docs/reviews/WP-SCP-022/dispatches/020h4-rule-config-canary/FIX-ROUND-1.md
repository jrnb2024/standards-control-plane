# 020h4-rule-config-canary fix-round-1 (post-r1)

**Date:** 2026-05-01

## Triggers

R1 dispatch returned (commit 07dfe3b reviewed):

- **R1 correctness** (`review-correctness.json`, ~6.9 min, APPROVED_WITH_FINDINGS): 0 MAJ + 1 MIN + 1 nit.
- **R1 safety** (`review-safety.json`, ~4.5 min, APPROVED_WITH_NOTES): **1 MAJ** + 3 MIN + 2 nit.
- **R1 completeness** (`review-completeness.json`, ~4.5 min, APPROVED): 0 MAJ + 1 MIN + 2 nit.

**Cumulative: 1 MAJ + 5 MIN + 5 nit.** Per `feedback_protocol_over_shortcuts.md` no descoping; all closed inline OR tracked as TF-020H4-NNN.

## MAJ closure

| Finding | Closure |
|---|---|
| **SAFE-MAJ-001** (DISPATCH-NOTE conflated PR #81's risk profile with PR #59's structurally-blocked CI=FAIL profile) | DISPATCH-NOTE acceptance item (i) corrected: "Risk profile matches canary 3's PR pattern (CI=PASS via suppression; label-only protection), NOT canary 1's PR #59 (CI=FAIL, structurally blocked)." canary-evidence.md Canary 4 section gained a new "Merge-protection note" subsection making the same point + naming TF-020H4-002 as the forward-compat closure path (Repository Ruleset matching `canary/*` blocking merge to main). |

## MIN closures

| Finding | Closure |
|---|---|
| SAFE-MIN-001 | Pre-existing `replay-canary.sh` ambiguity (`-1` sentinel for `gh run download` failure produces unclear REGRESSION rows). Filed as **TF-020H4-003** (replay-canary.sh hardening; pre-exists 020H.4 — landed in 020E.c — but surfaced by this slice's R1). |
| SAFE-MIN-002 | Same TF-020H4-003 covers the `--measure-cold-start` race window. |
| SAFE-MIN-003 + COR-nit-001 + COMP-MIN-001 | Three findings collapse to one TF: registry tuple doesn't catch suppress-still-works-but-observability-record-dropped regression class. Filed as **TF-020H4-001** (extend tuple with `expected_disabled_rules_count` field). The current tuple catches the primary regression class (suppress stops working → deny fires → conclusion=FAILURE + findings>=1); the missing case is narrow. Forward-compat. |
| COR-R1-MIN-001 | `replay-canary.sh` header prose fixed: "three federation-primitive canaries" → "four"; "The three canary branches" → "The four canary branches". Internally consistent with the numbered list (which already enumerates four). |

## nit closures

| Finding | Closure |
|---|---|
| SAFE-nit-001 | TF-E.c-001 (the `disabled_rules[*].expires_at` empty-string projection bug also affects rule-config entries) — already cross-referenced in canary-evidence.md Canary 4 §"Tracked-forward observations" + verdict-table column. No new closure needed. |
| SAFE-nit-002 | canary branch protection (canary/* has no ruleset blocking merge to main) — covered by **TF-020H4-002** (filed alongside SAFE-MAJ-001 closure). |
| COMP-nit-001 | Plan §4 020H.1(iv)(d) names three canaries; now four. The plan is frozen at Threshold A. Added a one-line note in canary-evidence.md Canary 4 §"Why this canary" acknowledging the plan-doc historical snapshot + cross-referencing TF-020H3-003 (broader plan-doc-staleness). |
| COMP-nit-002 | STATUS.md TF-020H1-005 strikethrough corrected: "~~**TF-020H1-005**~~ ✅ primary deliverable closed in 020H.1 fix-round-1 (SAFE-nit-008): ..." matches the strikethrough + ✅ pattern of TF-020H1-001 + TF-020H1-004. |

## Closures NOT applied

None. Every finding either inline-closed or filed as TF-020H4-NNN (3 new tracked-forward items: TF-020H4-001, TF-020H4-002, TF-020H4-003).

## Cumulative

1 MAJ closed (DISPATCH-NOTE risk-profile correction + canary-evidence Merge-protection subsection + TF-020H4-002 file). 5 MIN closed (some via TF-020H4 tracking). 5 nit closed.

## Re-review

R2 lens dispatch follows on the post-fix-round-1 state. Per `feedback_recursive_adversarial_review.md`, recurse until no new BLOCKING findings.
