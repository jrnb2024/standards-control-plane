# WP-SCP-022 slice 020H.1 — dispatch note

**Date:** 2026-05-01
**Tier:** orchestrator-applied (Tier 1 only)
**Closes:**
- WP-SCP-020 §4 020H.1 sub-criteria (i) + (ii) + (iii) + (iv) all four — semver/deprecation, rule-RFC, rollback-detection.
- ADOPT-001 §12.7.5 forward-looking flag for `rule-regression` issue template.
- ADOPT-001 §12.7.11 forward-looking flag for freshness-warning + `version-manifest.json`.
- 020H.2 carrier-slice STATUS.md backfill commitment (COMP-MIN-002 from the 020h2 fix-round-1).

## Justification for not invoking Codex executor

Per `feedback_four_tier_dispatch.md` in-line escalation guidance.
The slice's surface is **5 new docs/configs + 1 workflow step
addition + 1 ADOPT-001 sub-section rewrite**:

- `policies/VERSIONING.md` — semver + deprecation policy doc.
- `docs/reviews/rule-proposals/README.md` + `RULE-TEMPLATE.md` — RFC process + copy-paste skeleton.
- `.github/ISSUE_TEMPLATE/rule-regression.md` — adopter-reported regression channel.
- `.github/workflows/canary-replay.yml` — weekly cron + `gh issue create` on divergence.
- `version-manifest.json` — published manifest at repo root.
- `policy-check.yml` — new "Freshness warning" step (best-effort, never fails the gate).
- `docs/adoption/ADOPT-001-project-onboarding.md` §12.7.11 rewrite (freshness-warning is now LIVE) + §12.7.7 SCP-FRESH-001 row added.

All seven surfaces are policy-text or YAML/JSON/Markdown authorship.
Codex Tier 3 dispatch overhead would exceed the marginal benefit;
orchestrator-applied + R1 × 3 is the right posture (symmetric with
020G / 020h3 / 020h2 dispatch notes).

## Slice acceptance per WP-SCP-020 §4 020H.1

- [x] **(i) Semver contract on `workflow_call` inputs, `policy-check-summary.schema.json`, rule IDs.**
  `policies/VERSIONING.md` defines the MAJOR/MINOR/PATCH split,
  enumerates breaking changes (input rename/remove, schema field
  removal, rule-ID re-numbering, deny-default promotion, etc.) and
  non-breaking additions. The doc names `v1.0.0` (cut 2026-04-30) as
  the first stable release and lists the v1.x stability surface
  explicitly. Migration / amending-decision pattern documented.

- [x] **(ii) Rule deprecation: one-release warning-annotation window before removal.**
  `policies/VERSIONING.md` "Deprecation ramp" section: minimum gap
  between deprecation announcement and removal is one MINOR release.
  Rule deprecation specifically: warning annotation
  `SCP-R-NNN deprecated; will be removed in v<X+1>.0.0` fires on
  every PR run during the deprecation window. Migration pointer in
  the warning text.

- [x] **(iii) Rule addition: RFC-lite process — `docs/reviews/rule-proposals/RULE-NNN.md` drafts; quorum = 1 SCP-CODEOWNER approval; review window = 48h wall-clock; 0 approvals = auto-defer (closure of BS-5).**
  `docs/reviews/rule-proposals/README.md` documents the process
  end-to-end: when to file, draft + PR mechanics, 48h window with
  weekend-counts, quorum=1 (single-operator mode per D-031;
  forward-compat to 2-of-N when second maintainer onboards),
  auto-defer on zero approvals with `defer` label. `RULE-TEMPLATE.md`
  is the copy-paste skeleton for any new proposal.

- [x] **(iv) Rollback detection — best-effort, no paging rotation in v1.0.0.**
  - **(iv-a)** `.github/ISSUE_TEMPLATE/rule-regression.md` added —
    structured fields for affected version, rule, regression class,
    symptom, expected behaviour, reproduction, adopter impact,
    triage checklist. Auto-assigns `@jrnb2024`. 4h target named.
  - **(iv-b)** SCP-side canary re-run on each release: existing
    `scripts/replay-canary.sh` (landed in 020E.c) covers this; the
    new cron (iv-d) automates it on a schedule.
  - **(iv-c)** Dependabot/Renovate monitoring: pre-existing — covered
    by SCP self's own `.github/dependabot.yml` + the Renovate preset
    self-consumption at `renovate.json`.
  - **(iv-d)** Weekly scheduled workflow: `.github/workflows/canary-replay.yml`
    runs `cron: "0 9 * * MON"` + manual `workflow_dispatch`. Replays
    via `scripts/replay-canary.sh`; on divergence (`exit_code != 0`),
    de-dups by week-tag and either creates a new `rule-regression`
    issue or comments on the existing one. `permissions: { issues: write, contents: read, actions: read }`.
  - **(iv-e)** Target 4h from report to tag-pin revert — documented
    in the issue-template body and in ADOPT-001 §12.7.5.

- [x] **(x — folded in from 020H part 3) Freshness warning + `version-manifest.json`.**
  `version-manifest.json` published at repo root (`{"version": "1.0.0", "minor": "1.0", ...}`). `policy-check.yml` gains a "Freshness warning" step that reads `${SCP_RUNTIME_ROOT}/version-manifest.json` (the wrapper-pinned manifest) and `https://raw.githubusercontent.com/jrnb2024/standards-control-plane-/main/version-manifest.json` (main HEAD) and emits `::warning::title=SCP-FRESH-001` when the wrapper minor is more than `freshness_warning_threshold_minor` (default 2) behind. Best-effort — every failure path skips silently and never fails the gate. ADOPT-001 §12.7.11 retitled "Freshness warning (post-020H.1)" with the IS-shipped contract; §12.7.7 error-code table extended with `SCP-FRESH-001` (Non-blocking, informational).

## Carrier-slice STATUS.md backfill (from 020H.2 COMP-MIN-002)

The 020h2 DISPATCH-NOTE deferred the "mark 020H.2 landed (PR # +
commit SHA)" STATUS.md edit to "the next opened slice on main
(020H.1 or SCP-073.sec, whichever opens first)". 020H.1 opens
first; the backfill lands in this PR's diff:

> ~~**020H.2**: Regal binary SHA256 verification — closes TF-020H3-001~~ ✅ landed 2026-05-01 (PR #77, commit `bac1427`); 3-round recursive review reaching fixpoint at R2 (0 CRIT + 0 MAJ), 3 MAJ + 5 MIN + 13 nit closed; closed 13 days ahead of the 2026-05-14 deadline.

The 020h2 carrier-slice obligation is therefore closed by this
slice. The STATUS.md "Last updated" line is also bumped.

## Out of scope / forward-looking — TF-020H1-NNN tracked-forward items

Per fix-round-1 closure of R1 completeness COMP-MAJ-001 + COMP-MAJ-002 + COMP-MIN-004 + R1 safety SAFE-MIN-005 + SAFE-nit-008, every "future work" item is now a named TF-020H1-NNN entry in `STATUS.md` "Tracked-forward items from 020H.1":

- **TF-020H1-001** — `enforce_release_gate` workflow (operator manually enforces the deprecation ramp at v1.0.0).
- **TF-020H1-002** — `canary-replay.yml` paging rotation (assignee-only signal at v1.0.0; revisit at WP-SCP-024 cascade).
- **TF-020H1-003** — `auto-defer` GitHub Action for stale rule-proposals (manual close + `defer` label step at v1.0.0).
- **TF-020H1-004** — rule-config disable canary missing (only deny + waiver paths covered).
- **TF-020H1-005** — RULE-TEMPLATE.md §10 BLOCKING-vs-deferrable guidance closed in fix-round-1; this TF tracks any subsequent §10 enhancement.

## R1 review

3× parallel Sonnet R1 review (correctness / safety_bypass /
completeness_governance). Recurse to fixpoint per
`feedback_recursive_adversarial_review.md`.

## Files

- `policies/VERSIONING.md` — semver + deprecation policy.
- `docs/reviews/rule-proposals/README.md` — RFC-lite process.
- `docs/reviews/rule-proposals/RULE-TEMPLATE.md` — copy-paste skeleton.
- `.github/ISSUE_TEMPLATE/rule-regression.md` — adopter-reported regressions.
- `.github/workflows/canary-replay.yml` — weekly cron + auto-issue.
- `version-manifest.json` — published manifest.
- `.github/workflows/policy-check.yml` — freshness-warning step added.
- `docs/adoption/ADOPT-001-project-onboarding.md` — §12.7.11 retitled (post-020H.1) + §12.7.7 SCP-FRESH-001 row.
- `STATUS.md` — 020H.1 IN FLIGHT row + 020H.2 backfill closure (carrier obligation).
- `docs/reviews/WP-SCP-022/dispatches/020h1/DISPATCH-NOTE.md` — this file.
