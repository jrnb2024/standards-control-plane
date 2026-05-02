# WP-SCP-022 continuation prompt — 2026-05-02 (PM, post-backlog-clear session)

This is the resume document for the next session. Read it cold.

## Read first (in this order)

1. `STATUS.md` — at-a-glance state, "Today's chain (2026-05-02)" full-backlog-clear table, scheduled follow-ups, all `TF-*` items.
2. `~/.claude/projects/-Users-amplience-Projects-standards-control-plane/memory/MEMORY.md` and the linked memory entries — user profile, four-tier dispatch, recursive-adversarial-review, dispatcher-compute-is-subscription, etc.
3. `policies/VERSIONING.md` — semver contract + deprecation ramp + Tag-cut + Bad-tag recovery.
4. `docs/adoption/ADOPT-001-project-onboarding.md` §12.7 — adopter integration appendix; **§12.7.13 REGENERATION INVARIANT** now covers BOTH `requirements/policy-check.txt` and `requirements/conflict-gate.txt` lockfiles + 6 total assertion sites.
5. `docs/DECISIONS.md` — full decision log; **D-022 through D-039** are the federation-primitive doctrine.
6. This file.

## Where the chain is

**WP-SCP-019** (Service Auth Contract) — closed 2026-04-20.
**WP-SCP-020** (Policy Federation Primitive) — closed at v1.0.0 / Threshold A on 2026-04-30.
**WP-SCP-021** (MCP Server) — closed 2026-04-29.
**WP-SCP-022** (Implementation Programme) — closed at Threshold A on 2026-04-30; **post-Threshold-A backlog largely cleared as of 2026-05-02**.

`main` HEAD is at `44673aa` (slice 020N close-out). Today's chain (2026-05-02 — full backlog clear):

| # | PR | Slice / Item | Outcome |
|---|---|---|---|
| 1 | #84 | 020M | hash-pinning policy-check + release-gate; v1.0.1 cut at `0e24cc6` |
| 2 | tag | — | v1.0.1 GitHub release published |
| 3 | #85 | 020M close-out | STATUS backfill (`9b23d3f`) |
| 4 | #72 | dependabot | setup-python 5.6.0 → 6.2.0 (`5750d89`) |
| 5 | #44 | dependabot | upload-artifact 4.6.2 → 7.0.1 (`cff11b6`) |
| 6 | #42 | dependabot | download-artifact 4.3.0 → 8.0.1 (`7e242b5`) |
| 7 | #43 | dependabot | checkout 4.2.2 → 6.0.2 (`5c19a1d`); 7 sites bumped |
| 8 | #86 | 020N | conflict-gate hash-pinning (`3046344`); R1 1-MAJ closed in fix-round-1 |
| 9 | #87 | 020N close-out | STATUS backfill + Dependabot triage record (`44673aa`) |

**TFs closed today:** TF-020H3rg-002, TF-020H3-003 (opportunistic), TF-020M-001, TF-020M-002 (pruned).
**D-NNN filed today:** D-038 (020M), D-039 (020N).
**TF-NNN filed today:** TF-020N-001 (id-token: write narrowing on conflict-gate.yml; pre-existing, forward-compat).

## Live operational state on main

- 3 hash-anchored Python supply-chain layers across all SCP-self pip-installing workflows: `policy-check.yml` + `release-gate.yml` (slice 020M lockfile `requirements/policy-check.txt`) + `conflict-gate.yml` (slice 020N lockfile `requirements/conflict-gate.txt`).
- 7 GitHub Action SHA pins refreshed to current MAJOR versions (setup-python v6.2.0, upload-artifact v7.0.1, download-artifact v8.0.1, checkout v6.0.2).
- `enforce_admins: true` on `main`; required-status-check `policy-check / scp/policy-check` (strict); `required_signatures: true`; `required_pull_request_reviews: count=0, codeowner=false` (single-operator per D-033).
- Tag-protection rulesets on `v*` (D-030) and `renovate/v*` (D-034).
- `v1.0.0` released (2026-04-30); `v1.0.1` released (2026-05-02) — Python deps hash-pinned, no public-surface change.
- Renovate shared preset live at `renovate/v1.0.0`; SCP self consumes via `renovate.json` pinned to `#renovate/v1.0.0`.

## What's left (next-session candidate pool)

### Substantive (large; one-slice each)

1. **WP-SCP-022 proposal-queue / slice 020L — first rule-RFC dogfood** ★ recommended next-substantive.
   - The rule-RFC process landed in 020H.1 (`docs/reviews/rule-proposals/README.md` + `RULE-TEMPLATE.md`) but **has never been exercised**. Letter `L` reserved for this.
   - WP-SCP-024 (estate cascade) presumes the RFC works. Discovering process gaps with one operator is cheaper than discovering them when an FLA / PIM / etc adopter is also blocked.
   - Authoring `RFC-001-<topic>.md` is the substantive deliverable. Candidate first-rule topics covered in the prior continuation prompt: SCP-R-004 = waivers must reference an issue/PR URL in `reason` (additive, hygiene); SCP-R-004 = waiver-expiry stale-detection at PR time; SCP-R-002 deprecation-ramp closing TF-008 (exercises the deprecation contract — higher-risk first dogfood).
   - **Plan**: Phase 1 (this session) — author RFC-001 + open PR + walk through the 48h quorum=1 window. Phase 2 — implement the rule (slice 020H.5 or 020P), bump v1.0.0 → v1.1.0, cut tag.

2. **WP-SCP-023** — cross-repo scorecards. Large new WP. Gated on TF-006 (conflict-gate suppression-path fixture corpus, which itself depends on the Python evaluator gaining waiver awareness).

3. **WP-SCP-024** — estate cascade FLA pilot → PIM/recommender/etc. Large; gated on FLA pilot completion (per memory `reference_fla_gold_standard.md` — still maturing, don't freeze template yet).

### Small TF-class slices

- **TF-020H4-001** — extend `scripts/replay-canary.sh` registry tuple with `expected_disabled_rules_count`. One-bash-function rewrite + 4 canary baseline updates. Closes a "suppress-works-but-observability-dropped" regression class.
- **TF-020H3rg-004** — issue auto-close on corrective tag-cut. A workflow step detecting the corrected `v<X>.<Y+1>.0` and `gh issue close`-ing any open `release-gate-violation` issue. Symmetric with canary-replay.yml's auto-open pattern.
- **TF-020H4-002** — `canary/*` Repository Ruleset blocking merge to main. Bus-factor-1-mitigation; gated on 2nd-maintainer onboard (2026-07-21 review).
- **TF-020H4-003** — `replay-canary.sh` error-handling hardening (-1 sentinel disambiguation + cold-start race). Pre-existing 020E.c surface.
- **TF-020N-001** — narrow `conflict-gate.yml` `id-token: write` from workflow-default to job-level (symmetric with D-037's `release-gate-violation-issue` job-level scoping pattern).
- **TF-020H3rg-002** — `pip install --require-hashes` ✅ closed 2026-05-02 in slice 020M; remaining `pip install` site at `policies/VERSIONING.md` line ~136 docs example is illustrative only.

### Forward-compat (gated on upstream / cosmetic)

- **TF-006** — conflict-gate suppression-path fixture corpus → WP-SCP-023.
- **TF-007** — re-tighten `gh attestation verify` to hard-fail when OPA upstream begins publishing Sigstore attestations.
- **TF-008** — path-scope SCP-R-002 to waivers.json files only → v1.1 candidate (could fold into a 020L follow-up).
- **TF-020H3-002, 003, 004, 005** — cosmetic ADOPT-001 §12.7 v1.1 maintenance pass.
- **TF-020H1-002** (canary-replay paging rotation; post-WP-SCP-024 cascade or 2026-07-21 escalation).
- **TF-020H1-003** (auto-defer GitHub Action for stale rule-proposals; post-WP-SCP-024).
- **TF-020H1-005** (RULE-TEMPLATE §10 enhancement; cosmetic).
- **TF-020H3rg-001** (PR-time deprecation-announcement linter; forward-compat).

### Recommendation for next session

If the user wants substantive: **slice 020L — first rule-RFC dogfood**. The continuation prompt 2026-05-01-pm.md framed three candidate first-rule topics; selection is Phase 1's first decision. The RFC is a docs-only PR that opens a 48h wall-clock window — Phase 1 closes this session; Phase 2 (rule implementation + v1.1.0 cut) is a follow-up session.

If the user wants small concrete value: **TF-020H4-001 (replay-canary registry tuple)** — smallest concrete value-add, narrow blast radius.

If the user wants infrastructure clean-up: **TF-020N-001 (id-token narrowing)** — small, supply-chain hardening, symmetric with D-037 pattern.

## Open scheduled follow-ups

| Item | Date | Source |
|---|---|---|
| D-021 atomic workday filing (D-021 reservation) | 2026-05-31 | docs/DECISIONS.md header |
| Phase 2 X-CT-Timestamp activation notice (60-day advance) | 2026-07-02 | project_scheduled_followups.md item 3 |
| 2026-07-21 quarterly review (TWO items: 020K bus-factor-1 + TF-020G-001) | 2026-07-21 | docs/plans/WP-SCP-020 §8 + dispatches/020g/DISPATCH-NOTE.md |
| Branch-protection quarterly review (v* + main + renovate/v* rulesets) | 2026-07-30 | docs/security/branch-protection.md |
| WP-SCP-019 D-019 mode.bearer_legacy operational close | 2026-09-30 | project_d019_option_b_slide |

## First action on resume

```bash
cd /Users/amplience/Projects/scp-track1
git fetch --prune origin
git checkout main
git pull --ff-only
git log --oneline origin/main -10
gh pr list --state open
gh api repos/jrnb2024/standards-control-plane-/branches/main/protection/required_status_checks --jq '{strict, contexts}'
```

Expected:
- `main` HEAD includes `44673aa` (slice 020N close-out) or later.
- Open PRs are: 3 canary DO-NOT-MERGE (`#59, #67, #81`). No other PRs open.
- Required check is `["policy-check / scp/policy-check"]` strict.

If branch-protection shows anything different from the live operational state above, investigate D-033's reconciliation chain.

## Process invariants (do not violate)

- **Four-tier dispatch is mandatory** for non-trivial slices — `feedback_four_tier_dispatch.md`. Orchestrator-applied is acceptable for pure-governance / pure-CI-YAML / docs work and is explicitly justified in each DISPATCH-NOTE.
- **Recursive adversarial review to fixpoint** — `feedback_recursive_adversarial_review.md`. Recurse on R1 / R2 / ... until **no new CRIT/MAJ findings** on a complete cycle.
- **No descoping** — `feedback_protocol_over_shortcuts.md`. Every finding either inline-closed or named as a TF-NNN with a closure path.
- **Dispatcher compute is subscription-paid** — `feedback_dispatcher_compute_is_subscription_not_api.md`. Don't quote API token prices.
- **3× parallel Sonnet R1** — lens packages in `docs/reviews/WP-SCP-022/dispatches/<slice>/review-{correctness,safety,completeness}-package.json`; result files alongside; each fix-round documented as `FIX-ROUND-N.md`.
- **Cross-repo D-NNN prefixing** — `project_d_nnn_prefixing.md`. Estate uses `SCP D-NNN` / `CT D-NNN` prefixes in cross-repo references.

## Key file paths (cheatsheet)

Workflows:
- `.github/workflows/policy-check.yml` — reusable workflow adopters call. Hash-pinned via `requirements/policy-check.txt` (slice 020M).
- `.github/workflows/policy-check-wrapper.yml` — SCP self-dogfood caller.
- `.github/workflows/release-gate.yml` — tag-cut gate (020H.3 + 020H.3.1). Hash-pinned via `requirements/policy-check.txt`.
- `.github/workflows/conflict-gate.yml` — Rego-vs-Python conflict gate. Hash-pinned via `requirements/conflict-gate.txt` (slice 020N).
- `.github/workflows/canary-replay.yml` — weekly cron + post-release rollback detection.
- `.github/workflows/workflow-selftest.yml` — synthetic harness for the gate.

Lockfiles + version pins:
- `requirements/policy-check.{in,txt}` — slice 020M; pyyaml==6.0.2 + jsonschema==4.23.0 + transitives.
- `requirements/conflict-gate.{in,txt}` — slice 020N; fastapi + pydantic + pyyaml + jsonschema + pyjwt + cryptography + transitives.
- `scripts/.tool-versions` + `scripts/scp-policy-check.lock` — OPA + Conftest + Regal binary SHA256 pins.

Rule-RFC infra (for slice 020L):
- `docs/reviews/rule-proposals/README.md` — RFC-lite process (quorum=1, 48h wall-clock window).
- `docs/reviews/rule-proposals/RULE-TEMPLATE.md` — copy-paste skeleton.

## What "next session" looks like

- Run the "First action on resume" commands above.
- Pick a slice from the candidate pool (recommendation: 020L if substantive; TF-020H4-001 / TF-020N-001 if small).
- For non-trivial slices: branch off main, follow the established slice protocol (DISPATCH-NOTE → R1 dispatch → fix-round-N → R2 → fixpoint → merge).
- Update STATUS.md "Today's chain (next-date)" + auto-memory + this continuation prompt at slice close.

## Final state of this session

- `main` HEAD: `44673aa` (slice 020N close-out).
- `origin/main` matches local main.
- Working tree clean.
- All in-flight branches deleted.
- v1.0.1 released; release-gate dry-run + post-tag observer both clean.
- Memory updated: `project_post_threshold_a_state.md` reflects 020N + Dependabot triages + closed/open TF state + letter convention extended.
- 12+ named TF entries open (forward-compat); 5 dated scheduled follow-ups (next is 2026-05-31).

Ready to resume.
