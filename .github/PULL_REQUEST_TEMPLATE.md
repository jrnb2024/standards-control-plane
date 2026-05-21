<!--
SCP pull-request template. Closes GAP-P0-001 (cardinal-rule-2 R1 evidence linkage gap surfaced in 2026-05-13 orchestrator audit).

Cardinal-rule-2 binding: every non-trivial code/policy/governance change goes through a 3-lens R1 review (correctness / safety_bypass / completeness_governance) per `feedback_recursive_adversarial_review.md` + `feedback_protocol_over_shortcuts.md`. The R1 Evidence section below is the STRUCTURAL surfacing of that contract — adversarial-review evidence must be cited explicitly so reviewers (human + agent) and the merge-gate workflow (`.github/workflows/r1-evidence-check.yml`) can verify the linkage.

For docs/chore-class PRs where R1 is not applicable, state the rationale explicitly in the R1 Evidence section using the pattern shown.

Delete this comment block when authoring the PR. The template's section headings must remain.
-->

## Summary

<!--
1–3 sentence summary. State the change + the why. Cite the work-package
slice ID + commit SHA if amending an existing slice (e.g. WP-SCP-024
024B-extras-2 fix-round-N).
-->

## Test plan

<!--
Bulleted checklist of how the change was verified. Include at minimum:
- Local: shellcheck / pytest / bash test suite paths + rc=0
- CI: which checks must pass (policy-check, check-invocation-log-entry,
  validate PR body, etc.)
- Manual: any operator-attended steps (e.g. real-API smoke, gh CLI dry-run)
-->

- [ ]
- [ ]

## R1 Evidence

<!--
Cardinal-rule-2 binding. Three options below — pick ONE and fill in.

OPTION A — Standard 3-lens R1 evidence (most code/policy/governance PRs):
Cite the explicit lens JSON paths for the slice. Each lens MUST be a
non-empty path under docs/reviews/<WP>/<slice>/. The r1-evidence-check.yml
workflow validates that all three lens names appear with non-empty values.

- correctness: `docs/reviews/WP-SCP-NNN/<slice>/r1-correctness.json`
- safety_bypass: `docs/reviews/WP-SCP-NNN/<slice>/r1-safety_bypass.json`
- completeness_governance: `docs/reviews/WP-SCP-NNN/<slice>/r1-completeness_governance.json`

OPTION B — R1-not-applicable for docs/chore-class PRs:
State the rationale + a tracked-forward reference. Format mirrors CT
PRs #320/#326/#327 which established the pattern. Example:

> R1-not-applicable rationale: docs-only chore PR adding governance scaffolding (no code, schema, or policy mutation). Cardinal-rule-2 applies to slices that mutate production-touching surface; this PR introduces a structural surfacing of the rule itself. Tracked at GAP-P0-001 (this PR is the closure).

OPTION C — Protocol-deviation per `feedback_four_tier_dispatch.md` "note and justify" rule (in-flight / time-bounded exception):
Use the `## Protocol deviation` heading. The r1-evidence-check.yml
workflow accepts either OPTION A OR a documented Protocol deviation
block citing: "note and justify" + scope rationale (e.g. narrow scope,
documented deviation, time-bounded) + a FUP-/TF-/D-NNN reference.

Default to OPTION A unless the change is genuinely docs-only or
genuinely in-flight.
-->

- correctness:
- safety_bypass:
- completeness_governance:

## AC references

<!--
Which work-package acceptance criteria does this PR close or progress?

For implementation slices, cite the relevant DISPATCH-NOTE.md + plan-doc
section (e.g. `docs/plans/WP-SCP-024-estate-cascade.md` §6 row 024B).
For governance/process PRs, cite the relevant ADR / D-NNN row /
governance gap ID.

Example:
- Closes plan-doc §6 row 024B (024B-extras-2 depth-defense surface)
- Ratifies D-048 (depth-defense surface contract)
- Closes TF-024B-EXTRAS-2-TRANSFORM-INCLUSION-LIST-001 + 6 sibling TFs
-->

-

<!--
Carry-forward TFs / open follow-ups:
List anything this PR surfaces but does NOT close. Each entry should
have a status (open / deferred / out-of-scope) + owner. Per
`feedback_no_silent_descoping.md`: every TF gets a disposition.
-->

## Carry-forward

-
