# WP-SCP-022 continuation prompt — 2026-05-02 (PM-3, post-020P / v1.1.0-cut session)

This is the resume document for the next session. Read it cold.

## Read first (in this order)

1. `STATUS.md` — at-a-glance state. "Today's chain (2026-05-02)" now has **15 rows**; `## Tracked-forward items from 020P (RULE-001 Phase 2)` section added (TF-020P-001..005).
2. `~/.claude/projects/-Users-amplience-Projects-standards-control-plane/memory/MEMORY.md` and the linked memory entries.
3. `policies/VERSIONING.md` — semver contract.
4. `docs/adoption/ADOPT-001-project-onboarding.md` §12.7 — federation-primitive integration appendix; **§12.7.14 NEW** in v1.1.0 covers adopter response to SCP-R-004 warn annotations.
5. `docs/DECISIONS.md` — full decision log; **D-022 through D-040** are the federation-primitive doctrine. D-040 (slice 020L) ratifies the 48h-CEILING-not-FLOOR posture in single-operator mode.
6. `docs/releases/v1.1.0.md` — release notes for the new ship.
7. `policies/SCP-R-004.rego` + `docs/reviews/rule-proposals/RULE-001-waiver-reason-must-cite-issue-or-pr.md` — the rule + its canonical specification.
8. This file.

## Where the chain is

**WP-SCP-019** (Service Auth Contract) — closed 2026-04-20.
**WP-SCP-020** (Policy Federation Primitive) — closed at v1.0.0 / Threshold A on 2026-04-30.
**WP-SCP-021** (MCP Server) — closed 2026-04-29.
**WP-SCP-022** (Implementation Programme) — closed at Threshold A on 2026-04-30. **Post-Threshold-A backlog cleared 2026-05-02 (020M / 020N / Dependabot triage / 020L / 020P / v1.1.0 cut).** No named-substantive backlog item remains; work goes to large-WP candidates (WP-SCP-023, WP-SCP-024) or small-TF housekeeping.

`main` HEAD is at `d83ce52` (020P merge). Today's chain (2026-05-02) — 15 PRs landed:

| # | PR | Slice | Outcome |
|---|---|---|---|
| 1–11 | (per `STATUS.md`) | 020M / v1.0.1 / 020N / Dependabot triages / closeouts / 2026-05-02 PM continuation | Backlog clear pre-020L |
| 12 | #89 | **020L** | First rule-RFC dogfood — RULE-001 / SCP-R-004 proposal merged + D-040 filed |
| 13 | #90 | 020L close-out | STATUS backfill + 2026-05-02 PM-2 continuation |
| 14 | **#91** | **020P** | **RULE-001 Phase 2 — SCP-R-004 LIVE + v1.1.0 cut** |
| 15 | this | 020P close-out | STATUS backfill + this continuation prompt |

**v1.1.0 release artifacts:**
- Tag: `v1.1.0` at commit `d83ce52`.
- GitHub release: `https://github.com/jrnb2024/standards-control-plane/releases/tag/v1.1.0`.
- Release notes: `docs/releases/v1.1.0.md`.
- Release-gate dry-run + post-tag observer: both clean (no `SCP-EREL-001` fire; no auto-issue opened).
- Renovate cascade follows on the next scheduled run.

---

## What's next — the candidate pool

### No named-substantive items remaining on the post-Threshold-A backlog

Both WP-SCP-022 proposal-queue Phase 1 (020L) and Phase 2 (020P) are now closed. Strategic-priority next-substantive candidates are large WPs gated on upstream conditions:

### 1. WP-SCP-023 — cross-repo scorecards

Large new WP. Gated on TF-006 (conflict-gate suppression-path fixture corpus, which itself depends on the Python evaluator gaining waiver awareness). Significant design + implementation work; would benefit from its own plan-doc slice first.

### 2. WP-SCP-024 — estate cascade FLA pilot → PIM/recommender/etc.

Large; gated on FLA pilot completion (per memory `reference_fla_gold_standard.md` — still maturing, don't freeze template yet). v1.1.0 is the first MINOR-bump shipped; observing how Renovate cascades v1.1.0 across the estate IS effectively early WP-SCP-024 evidence collection.

### Small TF-class slices (housekeeping)

The TF inventory grew significantly across 020L + 020P. Candidates ordered by load-bearing-ness:

- **TF-020P-005** (recommended) — `scripts/scp-pre-push-verify.sh` wrapper combining `opa fmt --fail`, Regal lint, and `opa test --coverage --threshold 90`. Three CI roundtrips on slice 020P each surfaced a verification step missing locally; this fix collapses them. ~30-line bash + CODEOWNERS entry.
- **TF-020L-002 (alt-path candidate) → TF-020P-002** — IF the slice that addresses TF-020P-002 picks the "amend RULE-TEMPLATE.md §6.2 framing" path, that slice could also adopt the canonical-pattern doctrine for §6.2 spec text in future RFCs.
- **TF-020P-001** — data-driven `policies/rule-baselines.yaml` manifest. File when 2nd warn-baseline rule lands (so deferred indefinitely; no action needed today).
- **TF-020P-003 + 004** — fold into TF-020P-005's pre-push wrapper.
- **TF-020N-001** — `conflict-gate.yml` `id-token: write` job-level narrowing (filed 2026-05-02; symmetric with D-037).
- **TF-020H4-001** — extend `replay-canary.sh` registry tuple with `expected_disabled_rules_count`.
- **TF-020H3rg-004** — auto-close `release-gate-violation` issue on corrective tag-cut.
- **TF-020H4-003** — `replay-canary.sh` error-handling hardening.
- **TF-020H4-002** — `canary/*` Repository Ruleset (deferred to 2026-07-21 2nd-maintainer onboarding).
- **TF-020L-001** — Unicode-whitespace regex divergence; ongoing Phase-2 monitor (no flap observed at v1.1.0 cut; continue ~30-90d across estate).

### Forward-compat / cosmetic (no urgency)

TF-006, TF-007, TF-008, TF-020H3-002/004/005, TF-020H1-002/003/005, TF-020H3rg-001.

### Scheduled follow-ups (dated, not now)

| Date | Item |
|---|---|
| 2026-05-31 | D-021 atomic workday filing (per WP-SCP-019 hygiene response §3) |
| 2026-07-02 | Phase 2 X-CT-Timestamp activation notice (60-day advance notice before 2026-09-01) |
| 2026-07-21 | quarterly review (TWO independent items: 020K bus-factor-1 + TF-020G-001) |
| 2026-07-30 | branch-protection quarterly review (covers v* + main + renovate/v*) |
| 2026-09-30 | WP-SCP-019 D-019 mode.bearer_legacy operational close |

---

## Key 020P learnings (carry forward)

### Local-dev verification is currently incomplete vs CI

Slice 020P needed **4 CI roundtrips** (fix-rounds 2/3/4 surfaced separate gaps):
1. **Regal lint** — `opa fmt` doesn't run Regal. Local `opa test` PASSED but CI's Regal lint caught `pointless-reassignment`.
2. **Coverage threshold** — `opa test` (no flags) doesn't enforce the `--threshold 90`. Local PASSED but CI's `--coverage --threshold 90` failed at 89.7% (just under).
3. **`opa fmt --fail`** — local edit didn't preserve canonical formatting. CI's format-check failed.

**TF-020P-005 captures the fix:** a `scripts/scp-pre-push-verify.sh` wrapper that runs all three (Regal + opa test --coverage --threshold 90 + opa fmt --fail) before push. Strongly recommended as the next-housekeeping slice.

### Warn-baseline rendering pattern is established

`.github/workflows/policy-check.yml` "Render deny annotations and enforce threshold" step now distinguishes warn-baseline from deny-baseline rules via `WARN_BASELINE_RULES` set. This pattern works for v1.1.0's single warn-baseline rule (SCP-R-004). When a 2nd warn-baseline rule lands, promote to data-driven manifest per TF-020P-001.

### Annotation sanitisation applied to BOTH branches

Defense-in-depth: `_sanitise_annotation_text` applies to warn AND deny branches in policy-check.yml. Closes a latent newline-injection risk that pre-existed on the deny path for SCP-R-001/002/003 — a free benefit from the slice 020P fix-round-1 review.

### Self-contained Rego predicates per rule

SCP-R-004 defines its own `scp_r_004_is_waiver_payload` + `scp_r_004_has_nonempty_string` predicates rather than calling `scp_r_002_*`. Closes 020L SAFE-MAJ-001. Pattern to repeat for every future SCP-R-NNN rule.

### Operator-discretion early-merge per D-040 applies to code PRs too

D-040 specifically named rule-RFC PRs, but the same principle (single-operator post-fixpoint can merge without minimum wall-clock wait) applies to code PRs that have reached recursive-adversarial-review fixpoint. Slice 020P merged within hours of opening once R1 fixpoint + CI green.

---

## First action on resume

```bash
cd /Users/amplience/Projects/scp-track1
git fetch --prune origin
git checkout main
git pull --ff-only
git log --oneline origin/main -10
gh pr list --state open
gh release list --limit 5
gh api repos/jrnb2024/standards-control-plane/branches/main/protection/required_status_checks --jq '{strict, contexts}'
```

Expected:
- `main` HEAD includes `d83ce52` (020P merge) + the close-out commit.
- Open PRs are: 3 canary DO-NOT-MERGE (`#59, #67, #81`).
- `gh release list` shows v1.1.0 (2026-05-02), v1.0.1 (2026-05-02), v1.0.0 (2026-04-30).
- Required check is `["policy-check / scp/policy-check"]` strict.

## Process invariants (do not violate)

- **Four-tier dispatch is mandatory** for non-trivial slices — `feedback_four_tier_dispatch.md`. Orchestrator-applied is acceptable for pure-governance / pure-CI-YAML / docs work and is explicitly justified in each DISPATCH-NOTE.
- **Recursive adversarial review to fixpoint** — `feedback_recursive_adversarial_review.md`. Recurse on R1 / R2 / ... until **no new CRIT/MAJ findings** on a complete cycle. Slice 020P reached fixpoint on R1 directly — possible when the spec is fully pre-vetted.
- **No descoping** — `feedback_protocol_over_shortcuts.md`.
- **Dispatcher compute is subscription-paid** — `feedback_dispatcher_compute_is_subscription_not_api.md`.
- **3× parallel Sonnet R1** — lens packages + result files in `docs/reviews/WP-SCP-022/dispatches/<slice>/`.
- **Cross-repo D-NNN prefixing** — `project_d_nnn_prefixing.md`.
- **D-040 single-operator-mode 48h posture**: 48h is CEILING-not-FLOOR; merge eligible at fixpoint + label + PR-open. Bypass-introducing proposals retain non-waivable 48h MINIMUM.
- **Local pre-push verification (post-020P recommendation)**: until TF-020P-005's wrapper script lands, manually run `opa fmt --fail`, Regal lint, and `opa test --coverage --threshold 90` before push to avoid CI roundtrips.

## Live operational state on `main` (snapshot)

- **4 SCP-R rules live**: SCP-R-001 (services.yml mode lifecycle), SCP-R-002 (waivers shape), SCP-R-003 (vendoring attestation), **SCP-R-004 (waiver reason URL — NEW at v1.1.0)**.
- 3 hash-anchored Python supply-chain layers: policy-check.yml + release-gate.yml + conflict-gate.yml (all hash-pinned via `requirements/`).
- 7 GitHub Action SHA pins refreshed to current MAJOR versions.
- `enforce_admins: true` on main; required-status-check `policy-check / scp/policy-check` (strict); `required_signatures: true`; `required_pull_request_reviews: count=0, codeowner=false` (single-operator per D-033).
- Tag-protection rulesets on `v*` (D-030) and `renovate/v*` (D-034).
- **`v1.0.0` released 2026-04-30; `v1.0.1` released 2026-05-02; `v1.1.0` released 2026-05-02** (SCP-R-004 at warn baseline; no public-surface breaking change).
- Renovate shared preset live at `renovate/v1.0.0`.
- 2 GitHub labels for proposal infra: `scp-rule-proposal` (color 0E8A16, green), `defer` (color D4C5F9, light purple).
- New `WARN_BASELINE_RULES = {"SCP-R-004"}` set in `.github/workflows/policy-check.yml`.

## Final state of this session

- `main` HEAD: 020P close-out commit (this PR).
- `origin/main` matches local main.
- Working tree clean (post-merge).
- All 020P dispatch evidence committed (DISPATCH-NOTE, FIX-ROUND-1, 6 review JSONs).
- D-040 (filed in 020L) is the most recent decision; no D-NNN added in 020P (SCP-R-004 is same-domain as SCP-R-002 per RULE-001 §9 + the README §3 "new domain" definition added in 020P closes TF-020L-003).
- TF-020L-002 + TF-020L-003 closed; TF-020P-001..005 filed; TF-020L-001 still open as ongoing Phase-2 monitor.
- Memory updated: `project_post_threshold_a_state.md` reflects 020P closure + v1.1.0 LIVE.
- **No named-substantive backlog item remains** — the next session picks from large-WP candidates (WP-SCP-023, WP-SCP-024) OR small-TF housekeeping (recommended: TF-020P-005 pre-push verify wrapper).

Ready to resume.
