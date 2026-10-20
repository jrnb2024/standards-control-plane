# WP-SCP-022 continuation prompt — 2026-05-02 (PM-2, post-020L dogfood session)

This is the resume document for the next session. Read it cold.

## Read first (in this order)

1. `STATUS.md` — at-a-glance state, "Today's chain (2026-05-02 — full backlog clear + first rule-RFC dogfood)" section now has 13 rows; tracked-forward section grew with `## Tracked-forward items from 020L (first rule-RFC dogfood)` containing TF-020L-001/002/003.
2. `~/.claude/projects/-Users-amplience-Projects-standards-control-plane/memory/MEMORY.md` and the linked memory entries.
3. `policies/VERSIONING.md` — semver contract.
4. `docs/adoption/ADOPT-001-project-onboarding.md` §12.7 — federation-primitive integration appendix.
5. `docs/DECISIONS.md` — full decision log; **D-022 through D-040** are the federation-primitive doctrine. **D-040 (2026-05-02)** is the 48h-CEILING-not-FLOOR-in-single-operator-mode amendment surfaced by the 020L dogfood.
6. `docs/reviews/rule-proposals/README.md` — RFC-lite process; substantially amended in slice 020L (RULE/RFC naming, single-operator self-approval shape, 48h CEILING-vs-FLOOR posture, Labels section).
7. `docs/reviews/rule-proposals/RULE-001-waiver-reason-must-cite-issue-or-pr.md` — first RFC, merged 2026-05-02 as canonical specification for SCP-R-004.
8. This file.

## Where the chain is

**WP-SCP-019** (Service Auth Contract) — closed 2026-04-20.
**WP-SCP-020** (Policy Federation Primitive) — closed at v1.0.0 / Threshold A on 2026-04-30.
**WP-SCP-021** (MCP Server) — closed 2026-04-29.
**WP-SCP-022** (Implementation Programme) — closed at Threshold A on 2026-04-30; **post-Threshold-A backlog cleared 2026-05-02 (020M / 020N / Dependabot triage / 020L dogfood) — only Phase-2-of-020L remains as the named-substantive next-slice candidate.**

`main` HEAD is at `25db685` (020L merge). Today's chain (2026-05-02) — 13 PRs landed (slices 020M / 020N / 4 Dependabot bumps / 020L + closeouts):

| # | PR | Slice | Outcome |
|---|---|---|---|
| 1–9 | (per `STATUS.md`) | 020M / v1.0.1 / 020N / 4 Dependabot triages + closeouts | Backlog clear pre-020L |
| 10 | #87 | 020N close-out | STATUS backfill + Dependabot triage record |
| 11 | #88 | — | 2026-05-02 PM continuation prompt for previous next-session |
| 12 | **#89** | **020L** | **First rule-RFC dogfood — RULE-001 / SCP-R-004; merged at `25db685` via D-040 operator-discretion early-merge** |
| 13 | this | 020L close-out | STATUS backfill + this continuation prompt |

The 020L dogfood was substantive enough to warrant its own R1+R2 fixpoint cycle PLUS a fix-round-3 framework amendment (D-040). Cumulative for 020L: 7 MAJ + 6 MIN + 4 nit closed (R1) + 2 MIN (TF-020L-002/003) + 3 nit (R2) + 1 framework amendment + 4 inline-closed process gaps + 2 GitHub labels provisioned.

---

## What's next — the candidate pool

### 1. ★ Phase 2 of 020L — implement SCP-R-004 + cut v1.1.0 (RECOMMENDED next-substantive)

The RFC-001 proposal is merged as canonical specification. Phase-2 deliverables (separate slice — name candidate `020P` or `020H.5`):

- `policies/scp_r_004.rego` — implementation following the §3.4 sketch in RULE-001 (own `scp_r_004_is_waiver_payload` + `scp_r_004_has_nonempty_string` predicates per SAFE-MAJ-001 closure; `scp_r_004_has_url(text) := regex.match(`https?://[^\s]+`, text)`; deny + warn rules).
- `policies/tests/scp_r_004_test.rego` — Conftest tests covering ~14 cases per RULE-001 §8.1.
- `tests/conflict_gate/scp-r-004/{allow,deny}/` — conflict-gate fixtures per RULE-001 §6.2.
- `version-manifest.json` — bump v1.0.1 → v1.1.0.
- Release notes for v1.1.0 (mention SCP-R-004 at warn baseline).
- No `policies/deprecations.yaml` entry (rule-add at warn).
- Tag-cut + GitHub release.
- ADOPT-001 §12.7.X subsection "Adopter response to SCP-R-004 warn annotations" per RULE-001 §9.
- Workflow's "Emit per-rule warning annotations" step (`.github/workflows/policy-check.yml`) — add SCP-R-004 to warn-class set OR use generic warn-class enumeration per RULE-001 §3.4 "Warn-baseline workflow integration".

Phase 2 is straightforward execution off the merged RFC. Standard slice protocol: DISPATCH-NOTE → R1 dispatch → fix-round-N → R2 → fixpoint → operator-merge per D-040 (48h CEILING-not-FLOOR in single-operator mode).

### 2. WP-SCP-023 — cross-repo scorecards

Large new WP. Gated on TF-006 (conflict-gate suppression-path fixture corpus, which itself depends on the Python evaluator gaining waiver awareness).

### 3. WP-SCP-024 — estate cascade FLA pilot → PIM/recommender/etc.

Large; gated on FLA pilot completion (per memory `reference_fla_gold_standard.md` — still maturing, don't freeze template yet).

### Small TF-class slices (housekeeping; narrow blast radius)

- **TF-020L-002** — RULE-TEMPLATE.md §5 lacks residual-bypass guidance for syntactic-pattern rules. One-paragraph addition pointing at RULE-001 §5 case 5 as a worked example. Can fold into Phase-2 of 020L (the implementation slice would naturally touch RULE-TEMPLATE.md if the PoC is included).
- **TF-020L-003** — README.md §3 "new domain" undefined. Lightweight; can fold into Phase-2 of 020L OR a dedicated process-doc slice.
- **TF-020L-001** — Unicode-whitespace regex divergence in conflict-gate. Phase-2 monitor; close as no-op if no `SCP-E005` flap surfaces during the warn-baseline observation window on the SCP self-dogfood gate.
- **TF-020H4-001** — extend `replay-canary.sh` registry tuple with `expected_disabled_rules_count`. Closes a "suppress-works-but-observability-dropped" regression class.
- **TF-020N-001** — narrow `conflict-gate.yml` `id-token: write` to job-level (filed 2026-05-02; symmetric with D-037).
- **TF-020H3rg-004** — auto-close `release-gate-violation` issue on corrective tag-cut.
- **TF-020H4-003** — `replay-canary.sh` error-handling hardening (`-1` sentinel + cold-start race).
- **TF-020H4-002** — `canary/*` Repository Ruleset (deferred to 2026-07-21 2nd-maintainer onboarding).

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

## Key 020L learnings (carry forward)

- **48h is a CEILING in single-operator mode**, not a FLOOR. Operator may merge a non-bypass RFC as soon as fixpoint reached + PR open + `scp-rule-proposal` label applied. D-040 ratifies. Bypass-introducing proposals retain non-waivable 48h MINIMUM.
- **Self-contained Rego predicates per rule** — define own `scp_r_NNN_*` predicates rather than calling `scp_r_NNN-other_*` directly. Prevents silent-bypass on a refactor of the other rule. Common-shared helpers belong in `scp_common.rego` (which IS the right cross-rule home, refactoring there breaks all rules simultaneously rather than one silently).
- **§5 must include a "Residual known bypass" case** for rules enforcing syntactic patterns (URL, regex, format constraint). Not in template yet (TF-020L-002).
- **Two GitHub labels provisioned**: `scp-rule-proposal` (color 0E8A16, green) + `defer` (color D4C5F9, light purple). RFC PRs should apply `scp-rule-proposal` at open.
- **Operator-merge rationale comment** is the explicit decision artifact in single-operator mode (per README §Process step 2 single-operator self-approval bullet). The PR timeline carries the decision text; GitHub forbids PR self-review so a review approval cannot serve as the artifact.

## First action on resume

```bash
cd /Users/amplience/Projects/scp-track1
git fetch --prune origin
git checkout main
git pull --ff-only
git log --oneline origin/main -10
gh pr list --state open
gh api repos/jrnb2024/standards-control-plane/branches/main/protection/required_status_checks --jq '{strict, contexts}'
gh label list --search "scp-rule-proposal\|defer"
```

Expected:
- `main` HEAD includes `25db685` (020L merge) + the close-out commit.
- Open PRs are: 3 canary DO-NOT-MERGE (`#59, #67, #81`).
- Required check is `["policy-check / scp/policy-check"]` strict.
- Both new labels (`scp-rule-proposal`, `defer`) present.

## Process invariants (do not violate)

- **Four-tier dispatch is mandatory** for non-trivial slices — `feedback_four_tier_dispatch.md`. Orchestrator-applied is acceptable for pure-governance / pure-CI-YAML / docs work and is explicitly justified in each DISPATCH-NOTE.
- **Recursive adversarial review to fixpoint** — `feedback_recursive_adversarial_review.md`. Recurse on R1 / R2 / ... until **no new CRIT/MAJ findings** on a complete cycle.
- **No descoping** — `feedback_protocol_over_shortcuts.md`. Every finding either inline-closed or named as a TF-NNN with a closure path.
- **Dispatcher compute is subscription-paid** — `feedback_dispatcher_compute_is_subscription_not_api.md`. Don't quote API token prices.
- **3× parallel Sonnet R1** — lens packages in `docs/reviews/WP-SCP-022/dispatches/<slice>/review-{correctness,safety,completeness}-package.json`; result files alongside; each fix-round documented as `FIX-ROUND-N.md`.
- **Cross-repo D-NNN prefixing** — `project_d_nnn_prefixing.md`. Estate uses `SCP D-NNN` / `CT D-NNN` prefixes in cross-repo references.
- **D-040 single-operator-mode 48h posture**: 48h is CEILING-not-FLOOR; merge eligible at fixpoint + label + PR-open. Bypass-introducing proposals retain non-waivable 48h MINIMUM.

## Live operational state on `main` (snapshot)

- 3 hash-anchored Python supply-chain layers: policy-check.yml + release-gate.yml + conflict-gate.yml (all hash-pinned via `requirements/`).
- 7 GitHub Action SHA pins refreshed to current MAJOR versions.
- `enforce_admins: true` on main; required-status-check `policy-check / scp/policy-check` (strict); `required_signatures: true`; `required_pull_request_reviews: count=0, codeowner=false` (single-operator per D-033).
- Tag-protection rulesets on `v*` (D-030) and `renovate/v*` (D-034).
- `v1.0.0` released 2026-04-30; `v1.0.1` released 2026-05-02 (Python deps hash-pinned, no public-surface change).
- Renovate shared preset live at `renovate/v1.0.0`.
- 4 SCP-R rules implemented + 1 SCP-R rule **specified-only** (SCP-R-004 awaiting Phase-2 implementation).
- 2 new labels provisioned (`scp-rule-proposal`, `defer`).

## Final state of this session

- `main` HEAD: 020L close-out commit (this PR).
- `origin/main` matches local main.
- Working tree clean (post-merge).
- All 020L dispatch evidence committed (DISPATCH-NOTE, FIX-ROUND-1/2/3, 12× review JSON files including R1/R2 packages and results).
- D-040 filed; TF-020L-001/002/003 filed.
- README.md substantially amended (§Process step 1 + step 2 + step 3 + new §Labels section).
- Memory updated: `project_post_threshold_a_state.md` reflects 020L closure + Phase-2 forward.
- Phase-2-of-020L is the named-substantive next-slice candidate.

Ready to resume.
