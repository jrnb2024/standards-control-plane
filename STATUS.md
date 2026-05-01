# Standards Control Plane — STATUS

**Last updated:** 2026-05-01 (post-020H.3.1 + 020H.4 rule-config canary in flight)

## At-a-glance

| Programme | State | Track |
|---|---|---|
| WP-SCP-019 (Service Auth Contract) | ✅ closed 2026-04-20 | — |
| WP-SCP-020 (Policy Federation Primitive) | ✅ **closed 2026-04-30** at v1.0.0 (Threshold A) | Track 1 |
| WP-SCP-021 (MCP Server) | ✅ landed 2026-04-29 (USER-GATE-C signed) | Track 2 |
| WP-SCP-022 (Implementation Programme) | ✅ **closed 2026-04-30** (USER-GATE-A signed) | Meta |

## Threshold A — REACHED 2026-04-30

> **Threshold A definition:** SCP gates itself on its own `main` via the federation primitive's reusable workflow with a required-status-check, all three v1.0.0 Rego rules enforcing, conflict-gate green on every PR, and a v1.0.0 release tag cut.

```
020A    plan + D-022 + D-023                                     ✅ landed
020B    reusable workflow                                        ✅ landed (PR #36)
020B.1  workflow-selftest harness                                ✅ landed (PR #38)
020B.2  scripts/scp-policy-check local repro                     ✅ landed (PR #41)
020C    starter Rego rule library (3 rules)                      ✅ landed (PR #49, 2026-04-28)
020C.1  waiver-aware Rego + conflict-gate + read-back            ✅ landed (PR #52, 2026-04-29)
020J    tag-protection v* + required-signed-commits              ✅ landed (PR #53, 2026-04-30) + applied
020K    CODEOWNERS wiring (personal-account / single-operator)   ✅ landed (PR #56, 2026-04-30)
020D1   self-dogfood wrapper merged (advisory mode)              ✅ landed (PR #57, 2026-04-30)
020H part 1  v1.0.0-rc.1 release notes + tag cut                 ✅ landed (PR #58, 2026-04-30)
020E.a  pre-protection canary                                    ✅ landed (PR #60, 2026-04-30)
🛑 USER-GATE-A0  human signoff before promoting to required       ✅ signed (PR #61, 2026-04-30)
020H part 2  promote v1.0.0-rc.1 → v1.0.0                        ✅ landed (PR #62, 2026-04-30) + tag cut
020D2   flip gate to required (enforce_admins=true)              ✅ landed (PR #63, 2026-04-30) + applied
020D2.1 reconciliation (D-033)                                   ✅ landed (this PR, 2026-04-30)
🛑 USER-GATE-A  Threshold A signoff (FINISH LINE)                 ✅ **signed** (PR #64, 2026-04-30)
```

## Live operational state

- `enforce_admins: true` on `main` — admin override OFF.
- `required_status_checks: ["policy-check / scp/policy-check"]` (strict).
- `required_signatures: true` on every commit reaching `main`.
- `required_pull_request_reviews: count=0, codeowner=false` (single-operator mode per D-033).
- Tag-protection ruleset on `v*` (deletion / non_fast_forward / update blocked).
- Tag-protection ruleset on `renovate/v*` (deletion / non_fast_forward / update blocked) — added 2026-04-30 with 020F (D-034).
- Renovate shared preset live at `renovate/default.json`, tagged `renovate/v1.0.0`; SCP self consumes the preset via `renovate.json` pinned to `#renovate/v1.0.0`.
- `v1.0.0` released at `https://github.com/jrnb2024/standards-control-plane-/releases/tag/v1.0.0`.

## Today's chain (2026-04-30 — single session)

13 PRs merged + 2 release tags + 1 GitHub release published. WP-SCP-022 reaches Threshold A. WP-SCP-020 closed.

| # | PR | Slice | Outcome |
|---|---|---|---|
| 1 | #53 | 020J | tag-protection + required_signatures applied |
| 2 | #54 | governance | STATUS.md + AM continuation prompt |
| 3 | #55 | docs | SCP overview demo deck |
| 4 | #56 | 020K | CODEOWNERS wiring + D-031 (3-round R1 fixpoint, 21 findings closed) |
| 5 | #57 | 020D1 | self-dogfood wrapper (advisory) |
| 6 | #58 | 020H.1 | rc.1 release notes + lib bash fix |
| 7 | tag | — | **`v1.0.0-rc.1` cut** |
| 8 | #59 | 020E.a | DO-NOT-MERGE canary demonstrating SCP-R-001 deny |
| 9 | #60 | 020E.a | canary evidence merged |
| 10 | #61 | gate | USER-GATE-A0 signed |
| 11 | #62 | 020H part 2 | release-signoff merged |
| 12 | tag | — | **`v1.0.0` cut + GitHub release published** |
| 13 | #63 | 020D2 | required-check + branch protection applied |
| 14 | #64 | gate | **USER-GATE-A signed → Threshold A reached** |
| 15 | this | 020D2.1 | reconciliation (D-033) — context-name + review-shape corrections |

## Open PRs

- **PR #59** 🔄 OPEN (DO-NOT-MERGE) — pre-protection canary preserved as permanent fixture; under enforced mode now `mergeStateStatus: BEHIND` (cannot merge by design).
- **Dependabot PRs (3)** still open — defer (post-Threshold-A backlog).

## Open scheduled follow-ups

| Item | Date | Source |
|---|---|---|
| D-021 atomic workday filing (D-021 reservation) | 2026-05-31 | docs/DECISIONS.md header |
| Phase 2 X-CT-Timestamp activation notice (60-day advance) | 2026-07-02 | project_scheduled_followups.md item 3 |
| WP-SCP-019 D-019 mode.bearer_legacy operational close | 2026-09-30 | project_d019_option_b_slide |
| 2026-07-21 quarterly review covers TWO independent items: (1) WP-SCP-020 020K bus-factor-1 escalation (CODEOWNERS / break-glass); (2) TF-020G-001 (interactive-confirm review on adopter helper). Both items reach the same date by separate paths but are evaluated independently. | 2026-07-21 | docs/plans/WP-SCP-020-policy-federation-primitive.md §8 + docs/reviews/WP-SCP-022/dispatches/020g/DISPATCH-NOTE.md |
| Branch-protection quarterly review (bus-factor-1; covers `v*` ruleset, `main` protection, AND `renovate/v*` ruleset) | 2026-07-30 | docs/security/branch-protection.md |

## Tracked-forward items from 020C.1

- ~~**TF-005**: structural enforcement of expired rule-config at release-tag time~~ ✅ **closed in slice 020H.3** (this PR's branch); `.github/workflows/release-gate.yml` refuses a tag-cut when `.scp/rule-config.yaml` (SCP-self) has any `disable: true` entry with `expires_at < <tag-cut date>`. Adopter-side rule-config expiry is enforced separately at PR time via SCP-E007.
- **TF-006**: conflict-gate suppression-path fixture corpus → WP-SCP-023 (when Python evaluator gains waiver awareness).
- **TF-007**: re-tighten `gh attestation verify` to hard-fail when OPA upstream begins publishing Sigstore attestations. **Extended in 020H.2** to also wire a Regal Sigstore soft-warn at re-tightening time — Regal is published via OPA's pipeline and almost certainly shares the same upstream attestation gap timeline; symmetric treatment when the gap closes. Conftest also covered (no published attestations either).
- **TF-008**: path-scope SCP-R-002 to waivers.json files only (currently narrowed to null/string-rooted detection only) → v1.1.

## Tracked-forward items from 020D1 (closed in 020H part 3)

- **TF-D1-001**: WP-SCP-020 §4 020H part 3 canonical adopter template repo name uses trailing dash (`standards-control-plane-`) — ✅ closed in **020H part 3** (this PR's branch); §12.7.1 + §12.7.2 use the correct repo name.
- **TF-D1-002**: Document fork-PR refusal as mandatory or optional for adopters — ✅ closed in **020H part 3**; §12.7.1 documents the `if:` as **mandatory** with security rationale.
- **TF-D1-003**: Wrapper header references 'ADOPT-001 §12' federation appendix — ✅ closed in **020H part 3**; §12.7 federation-primitive adopter integration appendix now exists.

## Tracked-forward items from 020H part 3

- **TF-020H3-001**: Regal binary SHA256 verification — ✅ **closed in slice 020H.2 (this PR's branch)** before the 2026-05-14 deadline. `scripts/.tool-versions` now pins `regal 0.40.0`; `scripts/scp-policy-check.lock` carries Regal SHA256 entries for all four platforms (linux-x64, linux-arm64, darwin-arm64, darwin-x64); `.github/workflows/policy-check.yml` reads `REGAL_VERSION` from tool-versions, `REGAL_SHA256` from the lockfile, and resolves Regal via the new `resolve_regal()` helper symmetric with `resolve_opa()` (vendor-fallback parity). Sigstore attestation soft-warn for Regal not added (folds into TF-007).
- **TF-020H3-002**: ADOPT-001 §12.7 lacks an explicit "do these in this order" adopter onboarding sequence (was R1 completeness COMP-MIN-001). Document order implicitly encodes §12.7.1 → §12.7.2 → §12.7.3 → §12.7.4 setup flow, but a v1.1 §12.7 preamble would make the sequence explicit. No deadline (cosmetic).
- **TF-020H3-003**: Plan §4 020H part 3 canonical YAML wrapper text uses `standards-control-plane` (no trailing dash) in two places (was R1 completeness COMP-MIN-003 + 020F COMP-004). ADOPT-001 §12.7 has the correct version. Closure path: governance-only PR amending the plan doc on the next plan-touch slice (NOT 020H.1 — 020H.1 added new policy/process docs but did not amend the plan; this TF stays open for a future plan-touch slice). No deadline (cosmetic).
- **TF-020H3-004**: §12.7.4 path examples (`services.yml`, `output/findings/waivers.json`, `policies/**`) are SCP-internal naming (was R1 completeness COMP-NIT-001). Estate-cascade adopters (FLA, PIM, recommender, shopify-app, mapp-doc-agent, control-tower per WP-SCP-024) may have different file-shape conventions; v1.1 §12.7 wording could generalise. No deadline (cosmetic).
- **TF-020H3-005**: §12.7.2 doesn't include a one-sentence rationale for why `renovate/v*` is independent of the federation-primitive `v*` tag series (was R1 completeness COMP-NIT-002). Closure: v1.1 ADOPT-001 maintenance pass. No deadline (cosmetic).

## Tracked-forward items from 020H.1

- ~~**TF-020H1-001**: `enforce_release_gate` workflow~~ ✅ **closed in slice 020H.3** (this PR's branch); `.github/workflows/release-gate.yml` reads `policies/deprecations.yaml` (validated against `schemas/deprecations.schema.json`) and refuses a tag-cut on `push: tags: ['v*']` when any entry's `target_release` matches the candidate AND `announced_release` is not at least one MINOR behind. `workflow_dispatch:` with `dry_run_tag` input lets the operator test before pushing. Annotation: `SCP-EREL-001`.
- **TF-020H1-002**: `canary-replay.yml` paging rotation — at v1.0.0 the auto-opened `rule-regression` issue assigns `@jrnb2024` only (single-operator per D-031). For estate cascade (WP-SCP-024) a paging rotation would replace the assignee-only signal. Closure path: revisit at WP-SCP-024 planning OR at the 2026-07-21 quarterly bus-factor review when a second maintainer onboards. No deadline (forward-compat). Filed at 020H.1 R1 completeness COMP-MAJ-002 closure.
- **TF-020H1-003**: `auto-defer` GitHub Action for stale rule-proposals — currently a manual close + `defer` label step (per `docs/reviews/rule-proposals/README.md` §Process step 2). For estate scale (post-WP-SCP-024 cascade) when proposal volume warrants automation, a scheduled GH Action would close PRs with no approvals after the 48h window. No deadline (forward-compat). Filed at 020H.1 R1 completeness COMP-MIN-004 closure.
- ~~**TF-020H1-004**: rule-config disable canary missing~~ ✅ **closed in slice 020H.4** (this PR's branch). New `canary/rule-config-disabled` branch (PR #81 DO-NOT-MERGE; SHA `841d350`) carries the deliberate SCP-R-001 violation + a `.scp/rule-config.yaml` disable entry; workflow run `25211284467` verified PASS (deny suppressed by rule-config code path; findings=0; waivers=0; disabled_rules=2). `scripts/replay-canary.sh` registry extended with `rule-config-disabled|canary/rule-config-disabled|SUCCESS|0|0`. `docs/reviews/WP-SCP-020/canary-evidence.md` extended with Canary 4 baseline section. Suppression-path coverage triad complete: deny / waiver-suppressed / rule-config-suppressed.
- ~~**TF-020H1-005**~~ ✅ primary deliverable closed in 020H.1 fix-round-1 (SAFE-nit-008): `RULE-TEMPLATE.md` §10 `[BLOCKING]` / `[deferrable]` question-marking guidance + no-quorum-with-unresolved-`[BLOCKING]` invariant landed. This TF remains nominally open only for any subsequent §10 enhancement (e.g. an auto-detect linter that flags unresolved `[BLOCKING]` markers in a proposal PR). No deadline (cosmetic).

## Tracked-forward items from 020H.3 (release-gate)

- **TF-020H3rg-001**: PR-time deprecation-announcement linter — currently a rule-deprecation PR adds an entry to `policies/deprecations.yaml` per the rule-RFC process; no automated check that the entry is added when a `deprecated` annotation is introduced. Closure path: a future linter step in `policy-check.yml` (or a separate workflow) that greps for new `deprecated` warning emissions in a PR diff and refuses the PR if no corresponding `policies/deprecations.yaml` entry was added in the same PR. No deadline (forward-compat). Filed at 020H.3 R1 completeness COMP-MIN-002 closure.
- **TF-020H3rg-002**: `pip install --require-hashes` for `policy-check.yml` + `release-gate.yml` pyyaml/jsonschema installs. Both workflows currently version-pin without hash-pinning (matching the existing pattern). A PyPI compromise of either pinned version could substitute a malicious package on the next install. Closure path: generate a `requirements-pinned.txt` with `pip-compile --generate-hashes`; switch both workflows to `pip install -r <file>`. No deadline (forward-compat; matches the deferred OPA Sigstore re-tightening tracked at TF-007). Filed at 020H.3 R1 safety MIN-SAFE-006 closure.
- ~~**TF-020H3rg-003**: Auto-open `release-gate-violation` issue on push:tags failure~~ ✅ **closed in slice 020H.3.1** (this PR's branch). `.github/workflows/release-gate.yml` split into two jobs: `release-gate` (evaluation; `contents: read`) + `release-gate-violation-issue` (`needs: release-gate`; `if: needs.release-gate.result == 'failure' && github.event_name == 'push'`; `permissions: { contents: read, issues: write }`; pre-creates labels via `gh label create --force`; de-dups by tag substring; uses Python templating in both new-issue and comment branches). Ratified by **D-037** (issues:write job-level scope). Forward-compat assignee env: `SCP_RELEASE_GATE_ASSIGNEES` (defaults to `jrnb2024`).
- **TF-020H3rg-004**: Issue auto-close on corrective tag-cut — when the operator cuts the corrected `v<X>.<Y+1>.0`, the open `release-gate-violation` issue isn't auto-closed. Operator closes manually after the triage checklist completes. Closure path: a future workflow step that detects the corrected tag-cut and `gh issue close`s any open release-gate-violation issue for the bad tag-series. No deadline (forward-compat). Filed at 020H.3.1 R1 completeness COMP-MIN-001 closure.

## Tracked-forward items from 020H.4 (rule-config canary)

- **TF-020H4-001**: Extend `scripts/replay-canary.sh` registry tuple to include `expected_disabled_rules_count` field. Current tuple (verdict, findings, waivers) catches the primary regression class (suppress stops working → deny fires → conclusion=FAILURE + findings>=1) but misses a "suppress-still-works-but-observability-record-dropped" regression class. Closure path: extend the registry tuple to a 6th field, add a parse + verify branch in the script, update existing entries with the baseline disabled_rules counts. No deadline (forward-compat). Filed at 020H.4 R1 safety SAFE-MIN-003 + completeness COMP-MIN-001 closure.
- **TF-020H4-002**: Repository Ruleset matching `canary/*` blocking merge to `main` from any `canary/` branch. Currently the suppression-canary PRs (Canary 3 PR + Canary 4 PR #81) are CI-green (the gate suppresses) and the only merge barrier is the DO-NOT-MERGE label + operator discipline. Bus-factor-1 risk: a single accidental click would merge a canary into main. Closure path: when a second maintainer onboards (D-031 escalation, 2026-07-21 review), add a `scp-canary-no-merge-to-main` ruleset. Forward-compat — single-operator mode at v1.0.0 mitigates this risk via the same operator running both halves. Filed at 020H.4 R1 safety SAFE-MAJ-001 closure (architectural framing) + SAFE-nit-002 (canary branch protection).
- **TF-020H4-003**: `scripts/replay-canary.sh` error-handling hardening — (a) the `-1` sentinel for failed `gh run download` produces ambiguous output (REGRESSION rows could be either real drift or download failure); explicit ERROR rows would disambiguate; (b) `--measure-cold-start` mode dispatches a workflow run + sleeps 5 + reads "latest" with no race-protection — under concurrent invocations the wrong run could be read. Both pre-exist 020H.4 (landed in 020E.c) but surfaced by this slice's R1 safety review. Closure path: a hardening pass on replay-canary.sh in a future canary-touch slice. No deadline. Filed at 020H.4 R1 safety SAFE-MIN-001 + SAFE-MIN-002.

## Recent decisions

- **D-029 (2026-04-29)** — `policy-check.yml` permissions block adds `statuses: write` for the read-back commit-status.
- **D-030 (2026-04-30)** — apply 020J protections (tag-protection v* + required-signed-commits on main); idempotent applier at `scripts/configure-020j-protections.sh`.
- **D-031 (2026-04-30)** — adopt 020K personal-account / single-operator CODEOWNERS path.
- **D-032 (2026-04-30)** — apply 020D2 required-status-check + enforce_admins=true branch protection.
- **D-033 (2026-04-30)** — 020D2.1 reconciliation: required-check context renamed to `policy-check / scp/policy-check` (the rendered Actions check-run name); single-operator review shape corrected to `count=0` + `codeowner=false` (GitHub forbids PR self-review, locking out the operator under count=1).
- **D-034 (2026-04-30)** — 020F renovate-tag-protection: parallel ruleset on `refs/tags/renovate/v*` (deletion / non_fast_forward / update blocked, `enforcement: active`, `bypass_actors: []`). Closes 020F R1 safety review CRIT-SAFE-001.
- **D-035 (2026-04-30)** — 020G adopter-helper invocation procedure as estate doctrine: `scripts/enable-required-check.sh` two-call PUT + POST shape, refuses CI, preserves `required_pull_request_reviews`, mandatory invocation-log commit at `docs/reviews/WP-SCP-020/branch-protection-log.md`.
- **D-036 (2026-05-01)** — `policies/VERSIONING.md` MAJOR/MINOR/PATCH semver contract with one-release deprecation ramp AND `docs/reviews/rule-proposals/` RFC-lite process (quorum=1, 48h wall-clock window, auto-defer on zero approvals, **non-waivable window for bypass-introducing proposals** per 020H.1 R1 SAFE-MAJ-001 closure) adopted as estate doctrine. Closes WP-SCP-020 §4 020H.1 (i)+(ii)+(iii) and BS-5.
- **D-037 (2026-05-01)** — Grant `issues: write` (job-level scope) to the `release-gate-violation-issue` job in `.github/workflows/release-gate.yml` per slice 020H.3.1. The release-gate evaluation job remains `contents: read` only; the new job fires solely on `needs.release-gate.result == 'failure' && github.event_name == 'push'`. Symmetric with D-029 (020C.1 `statuses: write` for readback). Closes WP-SCP-022 020H.3.1 R1 SAFE-MIN-003 + SAFE-MAJ-001.

## Post-Threshold-A backlog

> **Naming note (per 020H.3 + 020H.3.1 disambiguation):** "020H **part** 3" (no dot, with the word "part") is the pre-Threshold-A v1.0.0-cut sequence slice that landed at PR #75 / commit `347fde2` (ADOPT-001 §12 federation appendix). "020H**.**3" (with dot) is the post-Threshold-A dot-N follow-up that landed at PR #79 / commit `42f49db` (release-gate workflow). "020H**.**3.1" (with two dots) is the reconciliation follow-up at this PR (release-gate auto-issue). The dot-N convention extends infinitely (020H.4, 020H.5, ...); the `part N` series is closed at part 3 (Threshold A).

- ~~**020E.b**: post-protection canary evidence~~ ✅ landed 2026-04-30 (PR #66, commit `8248732`).
- ~~**020E.c**: waiver-suppression canary + `scripts/replay-canary.sh`~~ ✅ landed 2026-04-30 (PR #70, commit `4962bc9`); needed 2-PR fixpoint dance for warn-msg conftest bug.
- ~~**020F**: Renovate shared preset~~ ✅ landed 2026-04-30 (PR #71, commit `2743d4a`); 4-round R1 fixpoint surfaced CRIT-SAFE-001 (renovate/v* unprotected) → D-034 + new ruleset live; preset published at `renovate/v1.0.0`.
- ~~**020G**: branch-protection automation script for adopter onboarding~~ ✅ landed 2026-04-30 (PR #74, commit `373bcd2`); fix-round-1 closed 11 R1 findings + R2 + R3 + R4 fixpoint.
- ~~**020H part 3**: ADOPT-001 §12 federation-integration appendix (closes TF-D1-001..003)~~ ✅ landed 2026-04-30 (PR #75, commit `347fde2`); 6-round recursive review reaching fixpoint at R3 (0 CRIT + 0 MAJ on all 3 lenses), 11 MAJ + 31 MIN + 11 nit closed. Opened TF-020H3-001..005.
- ~~**020H.1**: VERSIONING.md + rule-RFC process + rollback detection + version-manifest.json + freshness-warning emit~~ ✅ landed 2026-05-01 (PR #78, commit `06c2b61`); 2-round recursive review reaching fixpoint at R2 (0 CRIT + 0 MAJ on all 3 lenses), 6 MAJ + 17 MIN + 11 nit closed. Filed D-036 + opened TF-020H1-001..005. Closed SCP-073.sec (SECURITY.md published).
- ~~**020H.2**: Regal binary SHA256 verification — closes TF-020H3-001~~ ✅ landed 2026-05-01 (PR #77, commit `bac1427`); 3-round recursive review reaching fixpoint at R2 (0 CRIT + 0 MAJ), 3 MAJ + 5 MIN + 13 nit closed; closed 13 days ahead of the 2026-05-14 deadline.
- ~~**020H.3**: release-gate workflow (closes TF-005 + TF-020H1-001)~~ ✅ landed 2026-05-01 (PR #79, commit `42f49db`); 2-round recursive review reaching fixpoint at R2 (0 CRIT + 0 MAJ on all 3 lenses), 1 CRIT + 7 MAJ + 10 MIN + 10 nit closed across 2 fix-rounds. Architectural framing: workflow is observer/annotator (post-tag), not pre-emptive gate; pre-emptive enforcement is the operator's mandatory dry-run pre-flight discipline. Opened TF-020H3rg-001..003.
- ~~**020H.3.1**: release-gate auto-issue (closes TF-020H3rg-003)~~ ✅ landed 2026-05-01 (PR #80, commit `d3e3c73`); 2-round recursive review reaching fixpoint at R2 with R2 safety clean APPROVED (0 findings), 1 MAJ + 8 MIN + 6 nit + 1 fix-round-1 self-correction closed. Two-job split: release-gate (contents:read) + release-gate-violation-issue (issues:write at job level per D-037). Filed TF-020H3rg-004.
- **020H.4**: rule-config disable canary (closes TF-020H1-004). **IN FLIGHT** (this PR's branch). New `canary/rule-config-disabled` branch (PR #81 DO-NOT-MERGE) verified PASS at workflow run `25211284467`; `scripts/replay-canary.sh` registry extended; `docs/reviews/WP-SCP-020/canary-evidence.md` Canary 4 baseline section added. Suppression-path coverage triad complete.
- ~~**SCP-073.sec**: `SECURITY.md` publication (security disclosure path for policy-bypass reports)~~ ✅ landed 2026-05-01 in 020H.1 fix-round-1 (commit `3817384`); `SECURITY.md` at repo root with GitHub Security Advisory + `jimbrooke@me.com` channels, 3-business-day SLA, 30-day coordinated-disclosure target; ADOPT-001 §12.7.8 + `.github/ISSUE_TEMPLATE/rule-regression.md` updated to reference it directly. Closes WP-SCP-020 §4.1 SCP-073.sec forward-looking flag.
- **WP-SCP-022 proposal-queue**: structured proposal queue for new rules.
- **WP-SCP-023**: cross-repo scorecards.
- **WP-SCP-024**: estate cascade (FLA pilot → PIM/recommender/etc.).
