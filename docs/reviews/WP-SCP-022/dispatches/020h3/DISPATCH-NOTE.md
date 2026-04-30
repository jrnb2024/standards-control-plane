# WP-SCP-022 slice 020H part 3 — dispatch note

**Date:** 2026-04-30 (evening, post-Threshold-A)
**Tier:** orchestrator-applied (Tier 1 only)

## Justification for not invoking Codex executor

Per `feedback_four_tier_dispatch.md` in-line escalation guidance.
This slice's substantive surface is **one Markdown sub-section
appended to an existing canonical adopter doc** —
`docs/adoption/ADOPT-001-project-onboarding.md` §12.7 (~166 lines).
No code paths, no schema additions, no rule-engine surface,
no shell scripts. The plan §4 020H part 3 row defines all 11
sub-sections and the literal text shape for the canonical wrapper
snippet, so the orchestrator's authoring task collapses to
"transcribe the plan's sub-criteria into adopter-facing prose
with verified cross-references."

Codex Tier 3 would amount to round-tripping a transcription with
all the dispatch overhead and result-parsing cost. Orchestrator-
applied + R1 × 3 is the correct posture for documentation slices
of this shape (symmetric with 020G's note, where the substantive
surface was a derived shell script).

## Slice acceptance per WP-SCP-020 §4 020H part 3

The plan §4 row enumerates 11 sub-sections plus a minimal caller
wrapper. The diff's §12.7 sub-sections map 1-to-1:

- [x] **(minimal wrapper)** §12.7.1 — verbatim canonical YAML; uses
  `jrnb2024/standards-control-plane-` (with trailing dash, closing
  TF-D1-001); declares `permissions: contents: read, statuses: write`
  per D-029 / 020C.1(vi); the fork-PR refusal `if:` is documented
  as **mandatory** (closing TF-D1-002).
- [x] **(i)** §12.7.2 — Renovate preset `extends:` snippet pinned by
  ref (`#renovate/v1.0.0`) plus the customManager-marker convention
  documented inline.
- [x] **(ii)** §12.7.3 — branch-protection setup via the 020G
  helper (`scripts/enable-required-check.sh`) + `--plan` first-run
  guidance + multi-maintainer review-shape preservation note.
- [x] **(iii)** §12.7.4 — break-glass three-gate model (CODEOWNERS
  approval + sibling D-NNN row + matching waivers.json entry); names
  `scripts/verify-bypass-pairing.sh` as the enforcement script and
  `SCP-E004` as the failure mode.
- [x] **(iv)** §12.7.5 — rollback procedure (revert wrapper `@SHA`
  + tag-comment + Renovate re-run); 4-hour target per plan §4
  020H.1 iv-e; flags `rule-regression` issue template as
  forward-looking (lands in 020H.1).
- [x] **(v)** §12.7.6 — Python evaluator vs Rego scope; conflict-gate
  failure-mode `SCP-E005` named.
- [x] **(vi)** §12.7.7 — error codes `SCP-E001`..`SCP-E006` table
  with failure-mode column; codes verified emitted by
  `.github/workflows/policy-check.yml` and `conflict-gate.yml`.
- [x] **(vii)** §12.7.8 — `SECURITY.md` pointer; flagged as
  forward-looking (publishes via WP-SCP-020 §4.1 follow-up
  `SCP-073.sec`); interim guidance: contact `@jrnb2024` directly.
- [x] **(viii)** §12.7.9 — pre-commit hook snippet invoking
  `scripts/scp-policy-check`; references the SHA-locked binary
  cache + offline support.
- [x] **(ix)** §12.7.10 — adopter MUST NOT use `secrets: inherit`;
  rationale (privilege ceiling = caller's GITHUB_TOKEN).
- [x] **(x)** §12.7.11 — freshness-warning contract; flagged as
  **lands in 020H.1**, not yet emitted at v1.0.0; Renovate preset
  is the primary freshness signal until 020H.1 ships.
- [x] **(xi)** §12.7.12 — Actions-billing note; ~30s warm-start
  per PR run; cold-start adds 10–15s for binary download + SHA
  verification; ~2,400 PR runs/month headroom on GitHub Free
  with 2,000-minute monthly budget.

## Tracked-forward closures

This slice closes the three TF-D1-NNN items from the 020D1 R1 review:

- **TF-D1-001** (was COMP-MAJ-001) — repo name with trailing dash
  (`standards-control-plane-`) used consistently in §12.7.1 and
  §12.7.2. Closed.
- **TF-D1-002** (was COMP-MIN-001) — fork-PR refusal documented as
  **mandatory** in §12.7.1 with security rationale (fork PRs run
  with read-only GITHUB_TOKEN and cannot post the readback +
  workflow-context-injection risk surface). Closed.
- **TF-D1-003** (was COMP-MIN-002) — ADOPT-001 §12 federation
  appendix now exists; the 020D1 wrapper header reference is no
  longer a forward reference. Closed.

## Forward-looking flags (NOT closed by this slice)

The appendix references three artefacts that ship in subsequent slices:

- **`rule-regression` issue template** — §12.7.5; lands in 020H.1.
- **`SECURITY.md`** — §12.7.8; lands in WP-SCP-020 §4.1 follow-up
  `SCP-073.sec`.
- **Freshness-warning emit + `version-manifest.json`** — §12.7.11;
  lands in 020H.1.

Each flag is named explicitly in-line so adopters reading the
appendix at v1.0.0 do not assume the capability is live yet.

## Post-merge STATUS.md update commitment

After this PR squash-merges to main, STATUS.md updates in TWO places:

1. The "Post-Threshold-A backlog" table: mark **020H part 3** landed
   with PR # and commit SHA reference.
2. The "Tracked-forward items" section: mark TF-D1-001..003 closed
   (or add a "Closed in 020H part 3" annotation row).

Bundle both edits with the next slice's PR (likely 020H.1) to
keep the chain auditable.

## What this PR does NOT do

- Does NOT ship the freshness-warning emit (deferred to 020H.1).
- Does NOT publish `SECURITY.md` (deferred to WP-SCP-020 §4.1
  `SCP-073.sec`).
- Does NOT publish the `rule-regression` issue template
  (deferred to 020H.1).
- Does NOT introduce SCP-E007+ codes — error-code table is the
  v1.0.0-shipped set only.
- Does NOT modify any code path. Documentation-only diff.

## R1 review

3× parallel Sonnet R1 review (correctness / safety_bypass /
completeness_governance). Recurse to fixpoint per
`feedback_recursive_adversarial_review.md`.

## Files

- `docs/adoption/ADOPT-001-project-onboarding.md` — appended §12.7
  (federation primitive — adopter integration).
- `docs/reviews/WP-SCP-022/dispatches/020h3/DISPATCH-NOTE.md` —
  this file.
