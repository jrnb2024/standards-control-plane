# WP-SCP-022 slice 020L — FIX-ROUND-2 (R2 fixpoint)

**Date:** 2026-05-02
**Branch:** `feature/wp-scp-022-020l-rule-rfc-dogfood`
**HEAD pre-fix-round-2:** `52bf32a` (fix-round-1)
**R2 verdict:** **APPROVED on all three lenses — fixpoint reached.**

## R2 outcome

3-lens R2 (correctness / safety / completeness) verifies fix-round-1 closures and looks for new defects. Results:

| Lens | Verdict | New CRIT | New MAJ | New MIN | New nit |
|---|---|---|---|---|---|
| Correctness R2 | **APPROVED** | 0 | 0 | 0 | 1 |
| Safety/bypass R2 | **APPROVED** | 0 | 0 | 0 | 1 |
| Completeness R2 | **APPROVED** | 0 | 0 | 2 | 1 |
| **Total** | **APPROVED** | **0** | **0** | **2** | **3** |

**Fixpoint criterion** per `feedback_recursive_adversarial_review.md`: zero new CRIT/MAJ on a complete cycle. **MET.**

R1 closure verification:
- All 3 R1 MAJ correctness findings (helper name, regex, deny-rule comment) verified closed.
- All 2 R1 MAJ safety findings (cross-rule dependency, residual-bypass enumeration) verified closed.
- All 4 R1 MAJ completeness findings (VERSIONING.md citation, criterion-xiv alignment, RULE/RFC naming, label provisioning) verified closed.
- Fix-round-1 introduced no new CRIT/MAJ defects.

## New MIN findings → TF-020L entries

Both new MIN findings are in process-doc territory (RULE-TEMPLATE.md, README.md). Filing as TF-020L entries with closure paths rather than inline-closing in this slice — the changes affect the FRAMEWORK (how future RFCs are authored), not THIS proposal (which already handles them correctly).

### TF-020L-002 — RULE-TEMPLATE.md §5 lacks residual-bypass guidance

**Severity:** MIN. **Lens:** completeness (R2 COMP-R2-MIN-001).

**Gap.** RULE-001 §5 case 5 introduces a "Residual known bypass" category — explicitly naming the case where syntactically-compliant inputs satisfy the rule but not its semantic intent (URL exists but does not necessarily point to a decision artifact). RULE-TEMPLATE.md §5 does not direct future authors toward enumerating this category, so a next-RFC author who reads only RULE-TEMPLATE.md will document explicit new bypass mechanisms + structural no-op cases but will miss the residual-bypass framing unless they read RULE-001 as a worked example.

**Closure path.** Amend RULE-TEMPLATE.md §5 implicit-exclusion-set guidance with a note: "If the rule enforces a syntactic pattern (URL, regex, format constraint) rather than semantic validity of the matched value, add a 'Residual known bypass' case naming the gap between syntactic compliance and semantic intent — and the closure path (e.g. a future SCP-R-NNN with stricter domain checks, or explicit acknowledgement that honest-actor posture accepts the residual). See RULE-001 §5 case 5 as a worked example." Lightweight; can be folded into the next RFC slice OR a dedicated process-doc maintenance slice. No deadline (forward-compat).

### TF-020L-003 — README.md §3 "new domain" undefined

**Severity:** MIN. **Lens:** completeness (R2 COMP-R2-MIN-002).

**Gap.** README.md §3 Merge states "An entry in docs/DECISIONS.md if the rule introduces a new domain or escalates an existing rule's threshold" — but "new domain" is undefined. RULE-001 §9 commits explicitly to "same-domain as SCP-R-002 (waivers domain)" so RULE-001 is unambiguous, but every subsequent RFC will face the same operator-judgment ambiguity.

**Closure path.** Amend README.md §3 Merge to define: "A rule introduces a new domain if it evaluates a distinctly different input type (a new top-level input schema not addressed by any existing SCP-R-NNN rule) or a policy area with no existing SCP-R-NNN counterpart. Adding a new constraint on the same input schema as an existing rule (e.g. an additional field-level check on the waivers payload already governed by SCP-R-002) is same-domain and does not require a merge-time D-NNN." This makes RULE-001 §9's position canonical and eliminates future judgment-call ambiguity. Lightweight; can be folded into the next RFC slice OR a dedicated process-doc slice. No deadline (forward-compat).

## nit findings (non-actionable, recorded for audit)

- **R2-COR-NIT-001** — `rule_config` warn rule record shape lacks a `file` field (the `waiver` warn rule has it). Inherited asymmetry from SCP-R-002 / SCP-R-003 — intentional pattern, non-blocking. No closure needed.
- **R2-SAFE-NIT-001** — `scp_r_004_is_waiver_payload`'s dual-rule definition (count > 0 form + count == 0 form) collapses to `is_array(input)`. Mirrors SCP-R-002's intentional pattern verbatim — kept for parity. No bypass risk; no closure needed.
- **R2-COMP-NIT-001** — README.md "Labels" section ordering between Process and Auto-defer mechanics. The "Authorship guidance" section sits between Process and Labels; if reviewers prefer the structural ordering Process → Labels → Authorship guidance → Auto-defer mechanics, the section can be moved. Cosmetic; no process gap.

## Files touched in fix-round-2

- `docs/reviews/WP-SCP-022/dispatches/020l/FIX-ROUND-2.md` (this file).
- `docs/reviews/WP-SCP-022/dispatches/020l/review-{correctness,safety,completeness}-r2{-package,}.json` (R2 evidence).

No proposal-text or README-text changes in fix-round-2 — the new MIN findings are filed as TF-020L-002 + TF-020L-003 with closure paths rather than amended inline (they affect the FRAMEWORK for future RFCs, not THIS proposal which already handles both points correctly).

## Posture for proceed-to-PR-open

The proposal is at recursive-adversarial-review fixpoint. Per `feedback_recursive_adversarial_review.md`, fixpoint = "no new CRIT/MAJ findings on a complete cycle". MET on R2.

Cumulative: **R1 → R2 = 0 CRIT + 7 MAJ + 6 MIN + 4 nit closed (R1) + 0 CRIT + 0 MAJ + 2 MIN + 3 nit at R2** (the 2 R2 MINs filed as TF-020L-002 / TF-020L-003 with closure paths; the 3 nits non-actionable). 17 review findings total across two rounds with 0 BLOCKING outstanding.

Next: open the PR (DISPATCH-NOTE acceptance criterion (xiv) — opens 48h wall-clock window). The PR description includes a one-sentence Bypass-surface statement per criterion (xiv) updated wording. Operator-as-CODEOWNER (D-031 single-operator mode) approval recorded by explicit merge action after the 48h window per `README.md` §Process step 2 "Single-operator self-approval shape".
