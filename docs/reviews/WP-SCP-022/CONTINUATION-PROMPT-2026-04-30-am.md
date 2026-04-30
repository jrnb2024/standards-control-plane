# WP-SCP-022 continuation prompt — 2026-04-30 (AM, post-020C.1-merge, 020J PR open)

This is the resume document for the next session. Read it cold.

## Read first (in this order)

1. `STATUS.md` — at-a-glance Threshold A progress, active PRs, scheduled follow-ups, tracked-forward items.
2. `~/.claude/projects/-Users-amplience-Projects-standards-control-plane/memory/MEMORY.md` and the linked memory entries — user profile, four-tier dispatch, recursive adversarial review, dispatcher-compute-is-subscription, etc.
3. `docs/plans/WP-SCP-022-implementation-programme-plan.md` (v0.5 FIXPOINT) — meta-plan.
4. `docs/plans/WP-SCP-020-policy-federation-primitive.md` §3 sequence + §4 slice-acceptance table — canonical slice ordering and acceptance criteria.
5. `docs/security/branch-protection.md` — 020J configured-state documentation.
6. `docs/reviews/WP-SCP-022/dispatches/020c1/REVIEW-DEVIATION-2026-04-29.md` — R1 review deviation log (2 of 3 lenses budget-blocked).
7. `docs/reviews/WP-SCP-022/dispatches/020c1/review-correctness-and-safety-OPUS-SELF-REVIEW.md` — Opus self-review on the fixed code.
8. This file.

## Where the chain paused

### Active slice: 020J — tag-protection v* + required-signed-commits on main

- **PR #53** open at https://github.com/jrnb2024/standards-control-plane-/pull/53.
- Branch: `feature/wp-scp-020j-tag-protection-signed-commits` on the `scp-track1` worktree at `/Users/amplience/Projects/scp-track1/`.
- Substantively complete:
  - `scripts/configure-020j-protections.sh` — idempotent applier (Repository Ruleset for tag-`v*`, `required_signatures` on main).
  - `docs/security/branch-protection.md` — configured-state docs + verify + revert + bus-factor-1 review cadence.
  - `docs/DECISIONS.md` D-030 — decision row.
  - `docs/plans/WP-SCP-020-policy-federation-primitive.md` §3 sequence — completion checkmarks for landed slices.

**First action on resume:**

1. Check PR #53 CI state: `gh pr checks 53`.
2. Merge PR #53 once green. The substance is docs + a shell script — no rule-engine paths exercised, so CI should be quiet (only Dependabot + repo-default checks).
3. Run the script post-merge:
   ```bash
   cd /Users/amplience/Projects/scp-track1
   ./scripts/configure-020j-protections.sh
   ```
   Verify with the commands in `docs/security/branch-protection.md`:
   ```bash
   gh api repos/jrnb2024/standards-control-plane-/branches/main/protection/required_signatures --jq '.enabled'
   gh api repos/jrnb2024/standards-control-plane-/rulesets --jq '.[] | select(.name == "scp-tag-protection-v") | {id, enforcement, target}'
   ```

## What got done in the previous session

### Slice 020C.1 landed (PR #52, eb66c36, 2026-04-29 23:50 BST)

- Waiver-aware Rego rules (all three SCP-R-NNN consume `data.waivers` via shared `scp_active_waiver_for` helper in `policies/scp_common.rego`).
- Caller-side `.scp/rule-config.yaml` override with new `schemas/rule-config.schema.json` (Draft 2020-12, `additionalProperties: false`).
- Conflict-gate (rego-vs-python) workflow with adapter, fixtures (SCP-R-001/002 only — SCP-R-003 has documented gap), and CI job.
- Read-back commit-status `scp/policy-check-readback` posting human-readable text like "2/3 rules enabled, 0 disabled, 1 not applicable".
- Three new Rego helpers: `scp_active_waiver_for`, `scp_rule_config_disabled`, `scp_rule_config_entry`. Loaded into the per-rule `opa test` invocation by the workflow's coverage step.
- `policy-check-summary.schema.json` extended to allow date-or-date-time `expires_at` for `waivers_applied[*]` and `disabled_rules[*]`.
- D-029 row ratifying `statuses: write` permission for the read-back.

### Process notes from 020C.1

- **Track A** (orchestrator-applied conflict-gate adapter + fixtures + CI job) landed first at `cd0fd91`.
- **Track B** (codex slim dispatch for waiver-aware Rego + rule-config + read-back) timed out at the 5400 s ceiling. Per WP-SCP-022 §4.3 + State 3, reverted to orchestrator-applied. Result file committed as audit evidence at `docs/reviews/WP-SCP-022/dispatches/020c1/dispatcher-result-slim.json`.
- **R1 review.** 3× Sonnet lens dispatch attempted; 1 of 3 (`completeness_governance`) returned structured findings (1 CRIT, 6 MAJ, 2 MIN, 1 nit, 1 spec-drift item — all addressed in commit `6cc02b2`); the other two hit a hard 429 monthly-usage cap on the dispatcher account at ~10 min each. Deviation logged at `docs/reviews/WP-SCP-022/dispatches/020c1/REVIEW-DEVIATION-2026-04-29.md` and substituted with an Opus self-review on the fixed code at `review-correctness-and-safety-OPUS-SELF-REVIEW.md` (no new BLOCKING findings).
- **CI fixpoint.** A long sequence of CI failures surfaced once selftest could actually run end-to-end (workflow-selftest had been broken at workflow-load on every commit on `main` since the file was authored). Each layer was diagnosed and fixed in turn — see commit history `eb66c36..2ff3b3a` on main. The full set of issues encountered and fixed:

| # | Symptom | Root cause | Fix |
|---|---|---|---|
| 1 | workflow-selftest fails at workflow-load (zero check-runs) | `uses: ./.github/workflows/policy-check.yml@<sha>` invalid — GitHub Actions does NOT support `@<ref>` on local reusable-workflow refs | Use bare `uses: ./...`; replaced pin-staleness check with bare-form invocation count |
| 2 | `gh attestation verify` hard-fails (HTTP 404) | OPA v1.x has not published Sigstore attestations to GitHub's attestation database | Soft-warn with `::warning::`; SHA256 + lockfile-pin remains the primary security floor (TF-007) |
| 3 | Multiple regal lint violations | Rego patterns are stylistic mismatches with regal's idiomatic preferences (waiver helpers, `external-reference`, `unresolved-reference`, `defer-assignment`, `opa-fmt`, `messy-rule`, `superfluous-object-get`, `non-loop-expression`) | Disabled in workflow + README. Authoritative formatting is enforced by the dedicated `opa fmt --fail` step |
| 4 | `rego_recursion_error` from `object.get(data, ...)` | OPA's recursion checker treats `object.get(data, ...)` as a dependency on the entire `data.main` namespace, including `deny` | Use direct path references (`data.waivers`) + `default` rule values for fallbacks |
| 5 | Conftest 0.x rejects deny output: `"msg" field must be present` | Our deny payloads used `message`, not `msg` | `output := object.union(finding, {"msg": finding.message})` in deny rule |
| 6 | SCP-R-002 deny fires on every dict-rooted file | Pre-existing rule-design gap: no path-scoping; `not is_array(input)` triggered on services.yml, expected-annotations.json, etc. | Narrowed scope to null/string-rooted detection only for v1.0.0 (TF-008) |
| 7 | Conftest crashes: `unknown parser: md` | `tests/workflow/fixture-fail/WILL-FAIL-AFTER-020C.md` was passed to conftest in target list | Lib filters target list to evaluable extensions (yml, yaml, json, toml, hcl, ini, properties, cue, edn, xml) |
| 8 | Selftest only evaluates the diff, not the fixture tree | When the PR touched `tests/workflow/<harness>/expected-annotations.json`, the diff returned only that file — services.yml was never evaluated | `SCP_FIXTURE_PATH != "."` always enumerates the fixture tree (selftest mode); adopter mode (`.`) continues to scope to PR diff |
| 9 | `policy-check.yml` self-call path: empty `.scp-runtime` | Cross-repo checkout step partially runs even in local-uses mode (creates empty `.scp-runtime/.git`); existence check short-circuits the symlink-fallback | Sentinel-file detection: if `.scp-runtime/scripts/.tool-versions` is missing, `rm -rf .scp-runtime && ln -s "$(pwd)" .scp-runtime` |
| 10 | `continue-on-error: true` on `uses:` job → workflow-load failure | GitHub Actions does NOT support `continue-on-error` on reusable-workflow `uses:` jobs | Reverted; `fixture-fail-policy-check` shows red-by-design on PR checks; 020D1 will configure required-status-checks to require only the orchestrator job |
| 11 | Oracles out of date | `tests/workflow/<harness>/expected-annotations.json` was authored before 020C ('no Rego rules ship yet') and before SCP-R-003 no-manifest-applicable observability | Refreshed oracles; absolute fixture-path `file:` field |
| 12 | Subscription Actions budget exhausted (HTTP "Actions budget is preventing further use") | Personal GitHub plan's Actions budget capped during the 20+ CI runs | User reset budget; CI resumed |

### Tracked-forward items (do not lose)

- **TF-005** — structural enforcement of expired rule-config at release-tag time. Per WP-SCP-022 020C.1(v) spec, expired rule-config disables suppress for one release as a deprecation ramp; the per-PR `::warning::` annotation is the visible signal between releases. The release-cut-time refusal that prevents indefinite "edit expires_at to past" abuse should land in **020D2** as an acceptance criterion: refuse to cut a `v1.x.y` tag if any `.scp/rule-config.yaml` entry has `disable: true` AND `expires_at < now`.
- **TF-006** — conflict-gate suppression-path fixture corpus. The conflict-gate currently only covers raw rule paths. Adding waiver- or rule-config-suppressed fixtures requires the Python evaluator side to gain waiver awareness (it doesn't have it today). Tracked as a **WP-SCP-023** prerequisite item.
- **TF-007** — re-tighten `gh attestation verify` to hard-fail. Currently soft-warn in both `policy-check.yml` and `conflict-gate.yml`. Watch the OPA release stream for Sigstore attestation publishing; restore hard-fail when the pinned version has an attestation available.
- **TF-008** — path-scope SCP-R-002 to waivers.json files only. v1.0.0 narrowed scope to null/string-rooted detection (the realistic malformed-waivers shapes); dict-rooted detection is excluded for v1.0.0 because conftest sees every changed file and would false-positive on services.yml etc. Track for **v1.1**: route rules to file patterns via either `--namespace` or per-package conftest config.

### Estate notes from 020C.1

- The pre-existing `workflow-selftest.yml` was broken on every commit on `main` since it was authored — the `@<sha>` syntax for local reusable-workflow refs is invalid and GitHub Actions failed to load the workflow before any job could run. It's now fixed and runs end-to-end, including SCP self-dogfood self-call path via a `.scp-runtime` symlink fallback.
- The `fixture-fail-policy-check / scp/policy-check` job shows red-by-design on PR checks (the harness intentionally invokes the reusable workflow against a services.yml that triggers SCP-R-001's deny). The substantive selftest gate is the orchestrator's `workflow-selftest` job (different from the workflow file's name); green there means both fixtures behaved as expected. **020D1** will configure required-status-checks to require only the orchestrator's job.

## Slice queue from this point

| Slice | Subject | Risk | Notes |
|---|---|---|---|
| **020J** (PR #53 open) | tag-protection v* + required-signed-commits | Low | Merge PR #53; run `scripts/configure-020j-protections.sh`; verify |
| **020K** | adopter onboarding doc + ADOPT-005 self-cert | Low | Per WP-SCP-020 §4 020K (canonical, NOT continuation prompt's mislabelled "Renovate"). Single-operator path: CODEOWNERS names @jrnb2024 only |
| **020D1** | self-dogfood wrapper merged (advisory mode) | **HIGH** | First time SCP gates real PRs (its own). Will surface CI quirks the synthetic selftest fixtures missed. Will need its own CI fixpoint dance |
| **020H pt 1** | cut v1.0.0-rc.1 + observability metrics emit | Medium | First interaction with the tag-protection from 020J |
| **020E.a** | pre-protection canary | Medium | Internal canary (not yet FLA / PIM / CT) |
| **🛑 USER-GATE-A0** | first paused human signoff | — | User confirms advisory → required promotion |
| **020H pt 2** | observability dashboards | Low | |
| **020D2** | required-status-check + cut v1.0.0 | Medium | Irreversible-ish; reachable via revert. Add TF-005 acceptance criterion for release-tag-time check |
| **🛑 USER-GATE-A** | Threshold A signoff | — | The finish line |

## Key process invariants (do not violate)

- **Four-tier dispatch is mandatory** for non-trivial slices (`feedback_four_tier_dispatch.md`). Codex Tier 3 default executor; 3× parallel Sonnet R1 review (correctness / safety_bypass / completeness_governance lenses); recurse to fixpoint per `feedback_recursive_adversarial_review.md`.
- **Dispatcher compute is subscription-paid** (`feedback_dispatcher_compute_is_subscription_not_api.md`) — don't quote API token prices.
- **Protocol over shortcuts** (`feedback_protocol_over_shortcuts.md`) — frustration = thinking-quality concern, never process-skip request.
- **Adversarial review to fixpoint** (`feedback_recursive_adversarial_review.md`) — non-trivial work gets multi-reviewer parallel critique, recurse until no new blockers, no descoping.
- **Cross-repo D-NNN prefixing** (`project_d_nnn_prefixing.md`) — CT and SCP both use D-019/D-020/D-021; prefix `SCP D-NNN` / `CT D-NNN` in cross-repo references.

## Risks for 020D1 (the next high-risk slice)

When SCP first runs its own gate on its own PRs, the synthetic selftest's coverage gap will surface. Expected categories of new findings:

1. **Real PR file types not in the selftest fixture set.** The lib's target filter accepts `yml|yaml|json|toml|hcl|ini|properties|cue|edn|xml`. PRs touching `.py`, `.rego`, `.md`, `.sh`, etc. will be silently skipped. Verify this is the intended behaviour (the rules should only apply to declarative manifests).
2. **services.yml shape variations.** SCP's own repo doesn't use SVC-003 services.yml in production patterns — its own services.yml may not match the rule's services-by-name shape.
3. **SCP-R-002's narrowed scope.** Real waivers.json files may show up; verify the rule fires correctly on them.
4. **Conflict-gate fixture coverage.** The 6 fixtures (2 per rule × 2 rules in the corpus, SCP-R-003 excluded) may not match SCP's own PR diff patterns.

Plan for 020D1: open the wrapper PR, watch the workflow run, expect 2-4 follow-up commits to fix coverage gaps, then merge. Same pattern as 020C.1's CI fixpoint dance but in real-PR setting.

## Useful commands

```bash
# Resume context
cd /Users/amplience/Projects/scp-track1
git fetch --prune origin
git status
gh pr list --state open --author @me

# 020J post-merge action
./scripts/configure-020j-protections.sh
gh api repos/jrnb2024/standards-control-plane-/branches/main/protection/required_signatures --jq '.enabled'
gh api repos/jrnb2024/standards-control-plane-/rulesets --jq '.[] | select(.name == "scp-tag-protection-v") | {id, enforcement, target}'

# Check Threshold A progress
cat STATUS.md

# Check tracked-forward items
grep -A2 "TF-00[5-8]" STATUS.md docs/reviews/WP-SCP-022/dispatches/020c1/REVIEW-DEVIATION-2026-04-29.md
```

## Estimated time to Threshold A

Risk-weighted ETA (per the user's "how far away" question 2026-04-30 00:55 BST):

- **Floor**: by end of next session, 020D1 (advisory dogfood working) is past.
- **Mid case**: by end of next session, USER-GATE-A0 is awaiting user signoff.
- **Stretch**: by end of next session, Threshold A reached.

Caveat: the big tail risk is **020D1** — first time SCP runs its own gate on its own PRs. Expect a 020C.1-class CI fixpoint dance. Most of 2026-04-29's session was diagnosing CI in a synthetic setting; 020D1 is the same in a real setting. If unlucky, more "SCP-R-002 doesn't path-scope" / "conftest doesn't parse this file type" / "fixture/rule shape mismatch" issues will surface.

## Memory entries to verify

When resuming, check these memories are still accurate:
- `project_wp_scp_022_plan.md` — should reflect 020C.1 landed.
- `project_scheduled_followups.md` — should include the 2026-07-30 branch-protection review.
- `feedback_four_tier_dispatch.md` — invariant; should be unchanged.
- `feedback_recursive_adversarial_review.md` — invariant.
- `project_scp_control_plane_architecture.md` — invariant for the foreseeable future.

If any memory says "no rules ship yet" or refers to 020C/C.1 as in-flight, update it: those slices are landed.

## Final sanity-check before starting work

Run this at the top of the next session:

```bash
cd /Users/amplience/Projects/scp-track1
git fetch --prune origin
git checkout main
git pull --ff-only
git log --oneline -5
gh pr list --state open
gh pr checks 53 2>&1 | head -10
```

Expected: `main` includes `eb66c36` (020C.1 merge). PR #53 (020J) should be either still open or merged. If merged, the next action is running the configure script.
