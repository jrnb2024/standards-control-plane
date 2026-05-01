# WP-SCP-022 continuation prompt — 2026-05-01 (PM, post-six-slice session)

This is the resume document for the next session. Read it cold.

## Read first (in this order)

1. `STATUS.md` — at-a-glance state, "Today's chain (2026-05-01)" section, open PRs, scheduled follow-ups, all `TF-*` items.
2. `~/.claude/projects/-Users-amplience-Projects-standards-control-plane/memory/MEMORY.md` and the linked memory entries — user profile, four-tier dispatch, recursive-adversarial-review, dispatcher-compute-is-subscription, etc.
3. `policies/VERSIONING.md` — the semver contract + deprecation ramp + Tag-cut procedure + Bad-tag recovery procedure (post-020H.3 + 020H.3.1).
4. `docs/adoption/ADOPT-001-project-onboarding.md` §12.7 — adopter integration appendix (canonical post-Threshold-A surface; §12.7.1 through §12.7.13).
5. `docs/DECISIONS.md` — full decision log; **D-022 through D-037** are the federation-primitive doctrine.
6. This file.

## Where the chain is

**WP-SCP-020** (Policy Federation Primitive) — closed at v1.0.0 / Threshold A on 2026-04-30.
**WP-SCP-021** (MCP Server) — closed 2026-04-29.
**WP-SCP-022** (Implementation Programme) — closed at Threshold A on 2026-04-30; **post-Threshold-A backlog** is the active work surface as of this session.
**WP-SCP-019** (Service Auth Contract) — closed 2026-04-20.

`main` HEAD is at the close-out commit of this session. Six post-Threshold-A backlog slices landed in sequence on 2026-05-01:

| Order | PR | Slice | Closes |
|---|---|---|---|
| 1 | #75 | 020H part 3 | TF-D1-001..003 (ADOPT-001 §12.7 federation appendix) |
| 2 | #77 | 020H.2 | TF-020H3-001 (Regal SHA256 verification, 13 days early) |
| 3 | #78 | 020H.1 | SCP-073.sec (SECURITY.md); 020H.1 plan (i)+(ii)+(iii)+(iv) |
| 4 | #79 | 020H.3 | TF-005 + TF-020H1-001 (release-gate workflow) |
| 5 | #80 | 020H.3.1 | TF-020H3rg-003 (release-gate auto-issue + privilege split) |
| 6 | #82 | 020H.4 | TF-020H1-004 (rule-config disable canary) |
| 7 | this | session close-out | STATUS backfill + continuation prompt |

Each slice reached recursive-review fixpoint with **0 CRIT + 0 MAJ** on all three lenses (correctness / safety_bypass / completeness_governance) before merge. Cumulative: **~23 MAJ + ~89 MIN + ~59 nit closed across 17 review rounds.**

**D-036** (VERSIONING.md + rule-RFC process) and **D-037** (release-gate `issues: write` job-level scope) filed.

---

## Slice naming conventions (read carefully)

The 020H sub-series has a dual-notation convention that's already tripped reviewers:

- **`020H part N`** (no dot, with the word "part") = pre-Threshold-A v1.0.0-cut sequence. Closed at part 3 (PR #75); WILL NEVER GROW.
  - 020H part 1 = v1.0.0-rc.1 release notes (PR #58, merged 2026-04-30).
  - 020H part 2 = v1.0.0 promotion (PR #62, merged 2026-04-30).
  - 020H part 3 = ADOPT-001 §12 federation appendix (PR #75, merged 2026-04-30).
- **`020H.N`** (dot-N) = post-Threshold-A follow-ups in the H series. Indefinite extension.
  - 020H.1 = VERSIONING.md + rule-RFC + rollback-detection (PR #78).
  - 020H.2 = Regal SHA256 (PR #77).
  - 020H.3 = release-gate workflow (PR #79).
  - 020H.3.1 = release-gate auto-issue (PR #80) — `<slice>.<patch>` reconciliation pattern from 020D2.1.
  - 020H.4 = rule-config disable canary (PR #82).

`STATUS.md` "Post-Threshold-A backlog" section has an inline naming-note covering this. Future slices in the H series go to 020H.5 etc.; reconciliations to 020H.N.M.

---

## Tracked-forward inventory (the next-session candidate pool)

### `STATUS.md` "Tracked-forward items from 020C.1" — 4 items

- **TF-005** ✅ closed in 020H.3 (release-gate expired-config refusal).
- **TF-006** — conflict-gate suppression-path fixture corpus → WP-SCP-023 (gated on Python evaluator gaining waiver awareness). Forward-compat.
- **TF-007** — re-tighten `gh attestation verify` to hard-fail when OPA upstream begins publishing Sigstore attestations. **Extended in 020H.1** to also wire a Regal Sigstore soft-warn at re-tightening time. Gated on upstream.
- **TF-008** — path-scope SCP-R-002 to waivers.json files only. v1.1 candidate.

### `STATUS.md` "Tracked-forward items from 020D1 (closed in 020H part 3)" — 3 items, all closed

- TF-D1-001..003 ✅ closed in 020H part 3.

### `STATUS.md` "Tracked-forward items from 020H part 3" — 5 items

- **TF-020H3-001** ✅ closed in 020H.2.
- **TF-020H3-002** — ADOPT-001 §12.7 setup-sequence preamble (cosmetic, v1.1).
- **TF-020H3-003** — plan §4 020H part 3 trailing-dash typo (cosmetic, next plan-touch slice).
- **TF-020H3-004** — estate-cascade path-name generalisation (cosmetic, v1.1).
- **TF-020H3-005** — rationale for renovate/v* independence (cosmetic, v1.1).

### `STATUS.md` "Tracked-forward items from 020H.1" — 5 items

- **TF-020H1-001** ✅ closed in 020H.3.
- **TF-020H1-002** — canary-replay paging rotation (forward-compat, post-WP-SCP-024 cascade or 2026-07-21 escalation).
- **TF-020H1-003** — auto-defer GitHub Action for stale rule-proposals (forward-compat, post-WP-SCP-024).
- **TF-020H1-004** ✅ closed in 020H.4.
- **TF-020H1-005** — RULE-TEMPLATE §10 enhancement (primary deliverable closed in 020H.1 fix-round-1; nominally open for any subsequent §10 enhancement).

### `STATUS.md` "Tracked-forward items from 020H.3 (release-gate)" — 4 items

- **TF-020H3rg-001** — PR-time deprecation-announcement linter (forward-compat).
- **TF-020H3rg-002** — `pip install --require-hashes` for both YAML/JSON-validating workflows (forward-compat; touches `policy-check.yml` + `release-gate.yml` together).
- **TF-020H3rg-003** ✅ closed in 020H.3.1.
- **TF-020H3rg-004** — issue auto-close on corrective tag-cut (forward-compat).

### `STATUS.md` "Tracked-forward items from 020H.4 (rule-config canary)" — 3 items

- **TF-020H4-001** — extend `replay-canary.sh` registry tuple with `expected_disabled_rules_count` field (forward-compat).
- **TF-020H4-002** — Repository Ruleset matching `canary/*` blocking merge to main (forward-compat; closes label-only protection bus-factor-1 risk for suppression canaries).
- **TF-020H4-003** — `replay-canary.sh` error-handling hardening (-1 sentinel ambiguity + cold-start race; pre-exists 020H.4).

### Other open items in `STATUS.md` Post-Threshold-A backlog

- **WP-SCP-022 proposal-queue** — structured proposal queue for new rules (medium-sized; would dogfood the rule-RFC process landed in 020H.1).
- **WP-SCP-023** — cross-repo scorecards (large new WP).
- **WP-SCP-024** — estate cascade FLA pilot → PIM/recommender/etc. (large; gated on FLA pilot completion).

### `STATUS.md` "Open scheduled follow-ups" — 6 items, dated

| Date | Item |
|---|---|
| 2026-05-31 | D-021 atomic workday filing (per WP-SCP-019 hygiene response §3) |
| 2026-07-02 | Phase 2 X-CT-Timestamp activation notice (60-day advance notice before 2026-09-01) |
| 2026-07-21 | 2026-07-21 quarterly review (TWO independent items: 020K bus-factor-1 + TF-020G-001) |
| 2026-07-30 | branch-protection quarterly review (covers v* + main + renovate/v*) |
| 2026-09-30 | WP-SCP-019 D-019 mode.bearer_legacy operational close |

(TF-020H3-001's 2026-05-14 deadline was closed early at 2026-05-01 in slice 020H.2.)

---

## Picking the next slice

Recommendation candidates, ordered by load-bearing-ness + small-blast-radius:

### 1. WP-SCP-022 proposal-queue (substantive, medium-size, dogfoods the rule-RFC process)

The rule-RFC process landed at 020H.1 (`docs/reviews/rule-proposals/README.md` + `RULE-TEMPLATE.md`) but has never been exercised. The "proposal-queue" backlog item is essentially: **author the first rule proposal** using the new RULE-TEMPLATE.md. Picking a real candidate rule would:

- Dogfood the RFC process (catches process gaps before estate adopters use it).
- Validate the bypass-introducing-proposal exception path (SAFE-MAJ-001 closure from 020H.1).
- Give SCP a fourth rule (currently SCP-R-001/002/003 only) — tighter coverage of the federation primitive's expected scope.

Candidate first-rule topics:
- A rule that closes TF-008 (path-scope SCP-R-002 to waivers.json files only) — but TF-008 is "v1.1 candidate", not strictly a NEW rule. Could re-spec as a v1.1 rule deprecation + replacement.
- A new rule covering deprecation-ramp PR linting (would also close TF-020H3rg-001).
- A new rule covering required `policies/deprecations.yaml` entry on PRs that emit a `deprecated` warning annotation (cross-pollinates with TF-020H3rg-001).

### 2. TF-020H3rg-002 — pip install --require-hashes for both workflows (small, supply-chain hardening)

Touches `policy-check.yml` + `release-gate.yml`. Requires generating `requirements-pinned.txt` with `pip-compile --generate-hashes` and switching both workflows. Self-contained; one PR can close both workflow's hash-pinning together.

### 3. TF-020H4-001 — extend replay-canary.sh registry tuple (small, observability)

One bash function rewrite + canary-evidence.md baseline updates for all 4 canaries. Closes a narrow regression class (suppress works but observability dropped). Straightforward.

### 4. TF-020H3rg-004 — issue auto-close on corrective tag-cut (small, completes the release-gate story)

A workflow step that detects the corrective `v<X>.<Y+1>.0` and closes any open `release-gate-violation` issue for the bad tag-series. Symmetric pattern to the canary-replay.yml issue-creation step.

### 5. TF-020H4-002 — Repository Ruleset matching `canary/*` blocking merge to main

Currently the suppression-canary PRs (#67 + #81) are CI-green and merge-blocked only by labels. Adding a ruleset closes the bus-factor-1 hole. Small; mirrors D-030 + D-034 pattern.

### Lighter alternatives

- **Dependabot triage** — 4 stale MAJOR-version Action bumps (`#42`, `#43`, `#44`, `#72`) need explicit review (changelog read + dry-run). Each is its own small triage slice.
- **TF-020H3-002..005** — purely cosmetic ADOPT-001 v1.1 maintenance pass; bundle into a single docs-only PR.

### My pick (if asked again with no extra context)

**TF-020H4-001** (registry tuple extension) is the smallest concrete value-add that closes a real coverage gap. Dependabot triage is also reasonable but riskier.

If the user wants substantive: **WP-SCP-022 proposal-queue** — author the first rule proposal as the dogfooding milestone for the RFC process.

---

## First action on resume — verify state

Run these in parallel to confirm the slice chain is intact:

```bash
cd /Users/amplience/Projects/scp-track1
git fetch --prune origin
git checkout main
git pull --ff-only
git log --oneline origin/main -8
gh pr list --state open
gh api repos/jrnb2024/standards-control-plane-/branches/main/protection/required_status_checks --jq '{strict, contexts}'
```

Expected:
- `main` HEAD includes `c67a91a` (020H.4 merge) + the close-out commit (this session).
- Open PRs are: 4 Dependabot bumps (`#42, #43, #44, #72`) + 3 canary DO-NOT-MERGE (`#59, #67, #81`).
- Required check is `["policy-check / scp/policy-check"]` strict.

If branch-protection shows anything different from the live operational state in `STATUS.md`, investigate D-033's reconciliation chain before proceeding.

---

## Process invariants (do not violate)

The estate's review protocol at v1.0.0:

- **Four-tier dispatch is mandatory** for non-trivial slices — `feedback_four_tier_dispatch.md`. Orchestrator-applied is acceptable for pure-governance / pure-CI-YAML / docs work and is explicitly justified in each DISPATCH-NOTE.
- **Recursive adversarial review to fixpoint** — `feedback_recursive_adversarial_review.md`. Recurse on R1 / R2 / ... until **no new CRIT/MAJ findings** on a complete cycle. Fixpoint criterion is "no new BLOCKING", not "no new findings".
- **No descoping** — `feedback_protocol_over_shortcuts.md`. Every finding either inline-closed or named as a TF-NNN with a closure path.
- **Dispatcher compute is subscription-paid** — `feedback_dispatcher_compute_is_subscription_not_api.md`. Don't quote API token prices; cap is the OAuth session limit + monthly subscription budget.
- **3× parallel Sonnet R1** with R1 lens-package files committed to `docs/reviews/WP-SCP-022/dispatches/<slice>/review-{correctness,safety,completeness}-package.json` + result files alongside. Each fix-round documented as `FIX-ROUND-N.md`.
- **R2 safety clean APPROVED** (0 findings) is the strongest fixpoint signal observed in this session (020H.3.1 R2 safety hit it).
- **Cross-repo D-NNN prefixing** — `project_d_nnn_prefixing.md`. Estate uses `SCP D-NNN` / `CT D-NNN` prefixes in cross-repo references.

---

## Open Dependabot PRs requiring triage

The repo has 4 stale Dependabot PRs (each open since well before this session) that bump GitHub Actions to MAJOR new versions. Each touches the SHA pin in one or more workflow files; per `policies/VERSIONING.md`, MAJOR Actions bumps require deliberate review (changelog read; dry-run on a feature branch; verify the existing pinned actions/checkout signature still matches the gate's Resolve-tag step's expectations).

| PR | Bump | Affected files (likely) |
|---|---|---|
| #42 | actions/download-artifact 4.3.0 → 8.0.1 | `.github/workflows/*.yml` |
| #43 | actions/checkout 4.2.2 → 6.0.2 | `policy-check.yml`, `canary-replay.yml`, `release-gate.yml`, `workflow-selftest.yml` |
| #44 | actions/upload-artifact 4.6.2 → 7.0.1 | `policy-check.yml` |
| #72 | actions/setup-python 5.6.0 → 6.2.0 | (whichever workflows pin it) |

Triage approach: open each PR, read the upstream release-notes for breaking changes, dry-run on a temp branch, then merge or close. NOT auto-mergeable. Track as a "dependabot triage" slice if batched.

---

## Live operational state on `main` (snapshot)

- `enforce_admins: true` on main — admin override OFF.
- `required_status_checks: ["policy-check / scp/policy-check"]` (strict).
- `required_signatures: true` on every commit reaching main.
- `required_pull_request_reviews: count=0, codeowner=false` (single-operator personal-account mode per D-033).
- Tag-protection ruleset on `v*` (D-030).
- Tag-protection ruleset on `renovate/v*` (D-034).
- `v1.0.0` released at `https://github.com/jrnb2024/standards-control-plane-/releases/tag/v1.0.0`.
- Renovate shared preset published at `renovate/v1.0.0`.

---

## Key file paths (cheatsheet)

Workflows:
- `.github/workflows/policy-check.yml` — the reusable workflow adopters call.
- `.github/workflows/policy-check-wrapper.yml` — SCP self-dogfood caller.
- `.github/workflows/canary-replay.yml` — weekly cron + post-release rollback detection (020H.1).
- `.github/workflows/release-gate.yml` — tag-cut gate (020H.3 + 020H.3.1).
- `.github/workflows/conflict-gate.yml` — Rego-vs-Python conflict gate.
- `.github/workflows/workflow-selftest.yml` — synthetic harness for the gate.
- `.github/ISSUE_TEMPLATE/rule-regression.md` — adopter regression channel (020H.1).

Canaries:
- `canary/deliberate-violation-pre` (PR #59 DO-NOT-MERGE) — deny path; canaries 1+2.
- `canary/waived-violation` (PR #67 DO-NOT-MERGE) — waiver-suppressed deny.
- `canary/rule-config-disabled` (PR #81 DO-NOT-MERGE) — rule-config-suppressed deny (020H.4).

Policy + schema + version:
- `policies/SCP-R-001.rego` (+ tests) — bearer-legacy lifecycle.
- `policies/SCP-R-002.rego` (+ tests) — waivers shape.
- `policies/SCP-R-003.rego` (+ tests) — observability for no-manifest-applicable.
- `policies/scp_common.rego` — shared helpers.
- `policies/VERSIONING.md` — semver contract + Tag-cut + Bad-tag recovery.
- `policies/deprecations.yaml` — empty register at v1.0.0.
- `schemas/policy-check-summary.schema.json` — structured-summary contract.
- `schemas/rule-config.schema.json` — adopter rule-config contract.
- `schemas/deprecations.schema.json` — register schema (target_release locked to vX.0.0).
- `version-manifest.json` — published manifest read by freshness-warning.

Adopter / process:
- `docs/adoption/ADOPT-001-project-onboarding.md` §12.7 — federation-primitive integration appendix.
- `docs/reviews/rule-proposals/README.md` — RFC-lite process.
- `docs/reviews/rule-proposals/RULE-TEMPLATE.md` — copy-paste skeleton.
- `SECURITY.md` — disclosure path (SCP-073.sec landed in 020H.1 fix-round-1).

Dispatch evidence (for audit):
- `docs/reviews/WP-SCP-022/dispatches/<slice>/DISPATCH-NOTE.md` — per-slice dispatch.
- `docs/reviews/WP-SCP-022/dispatches/<slice>/FIX-ROUND-N.md` — per-fix-round audit.
- `docs/reviews/WP-SCP-022/dispatches/<slice>/review-{correctness,safety,completeness}{,-r2,-r3}.json` — review JSONs.

Decisions:
- `docs/DECISIONS.md` — D-022 through D-037 cover the federation primitive doctrine.

---

## Memory entries to verify on resume

When resuming, check these memories are still accurate:

- `project_wp_scp_022_plan.md` — should reflect 020H part 3 + 020H.1 + 020H.2 + 020H.3 + 020H.3.1 + 020H.4 all landed.
- `project_scheduled_followups.md` — TF-020H3-001's 2026-05-14 deadline is closed early; the 5 other dated items remain.
- `feedback_four_tier_dispatch.md` — invariant; should be unchanged.
- `feedback_recursive_adversarial_review.md` — invariant.
- `feedback_protocol_over_shortcuts.md` — invariant.
- `project_scp_control_plane_architecture.md` — invariant for the foreseeable future.

If any memory says a closed slice is "in flight" or names an open TF that's now closed, update it on resume.

---

## Tag-cut readiness

`v1.0.0` was cut on 2026-04-30. The next tag will be either `v1.0.1` (PATCH — bug fix) or `v1.1.0` (MINOR — new feature). Per `policies/VERSIONING.md` "Tag-cut procedure":

```bash
# 1. Author the release-prep PR (bump version-manifest.json + deprecations.yaml entries + release notes; merge).
# 2. Dry-run the gate.
gh workflow run release-gate.yml -f dry_run_tag=v1.0.1
sleep 5
RUN_ID="$(gh run list --workflow=release-gate.yml --limit 1 --json databaseId --jq '.[0].databaseId')"
gh run watch "${RUN_ID}" --exit-status
# 3. Push the tag (only after dry-run is clean).
# 4. Publish GitHub release; Renovate cascade follows.
```

The gate fires on tag push (post-tag observer) AND opens a `release-gate-violation` issue + `SCP-EREL-001` annotation on any violation (per 020H.3.1's job split). Dry-run is the operator-mandatory pre-flight.

**Bad-tag recovery procedure** is documented in `policies/VERSIONING.md` (cut a corrected `v<X>.<Y+1>.0`; bad tag is immutable per D-030).

---

## What "next session" looks like

- Run the "First action on resume" commands above.
- Decide: new substantive slice (proposal-queue, dependabot triage, or one of the small TFs), OR pause-state.
- For non-trivial slices: branch off main, follow the established slice protocol (DISPATCH-NOTE → R1 dispatch → fix-round-N → R2 → fixpoint → merge).
- For docs-only / housekeeping (e.g. dependabot triage, this close-out): single PR, optional R1, merge after CI.
- Update STATUS.md "Today's chain (next-date)" section with the slice list.
- Update auto-memory at slice close.
- Update this continuation prompt or write a fresh one for the following session.

---

## Final state of this session

- `main` HEAD: close-out commit landed (this PR).
- `origin/main` matches local main.
- Working tree clean (post-merge).
- All 6 substantive slices + 1 close-out PR documented.
- No CRIT or MAJ findings outstanding on any review round.
- 12 named TF entries open (covered above).
- 4 Dependabot PRs awaiting triage.
- Memory updated with slice closure summaries.

Ready to resume.
