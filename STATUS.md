# Standards Control Plane — STATUS

**Last updated:** 2026-05-01 (post-020H.2 + 020H.1 in flight)

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

- **TF-005**: structural enforcement of expired rule-config at release-tag time → add to 020D2.
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
- **TF-020H3-003**: Plan §4 020H part 3 canonical YAML wrapper text uses `standards-control-plane` (no trailing dash) in two places (was R1 completeness COMP-MIN-003 + 020F COMP-004). ADOPT-001 §12.7 has the correct version. Closure path: governance-only PR amending the plan doc on the next plan-touch slice (likely 020H.1 planning pass).
- **TF-020H3-004**: §12.7.4 path examples (`services.yml`, `output/findings/waivers.json`, `policies/**`) are SCP-internal naming (was R1 completeness COMP-NIT-001). Estate-cascade adopters (FLA, PIM, recommender, shopify-app, mapp-doc-agent, control-tower per WP-SCP-024) may have different file-shape conventions; v1.1 §12.7 wording could generalise. No deadline (cosmetic).
- **TF-020H3-005**: §12.7.2 doesn't include a one-sentence rationale for why `renovate/v*` is independent of the federation-primitive `v*` tag series (was R1 completeness COMP-NIT-002). Closure: v1.1 ADOPT-001 maintenance pass. No deadline (cosmetic).

## Recent decisions

- **D-029 (2026-04-29)** — `policy-check.yml` permissions block adds `statuses: write` for the read-back commit-status.
- **D-030 (2026-04-30)** — apply 020J protections (tag-protection v* + required-signed-commits on main); idempotent applier at `scripts/configure-020j-protections.sh`.
- **D-031 (2026-04-30)** — adopt 020K personal-account / single-operator CODEOWNERS path.
- **D-032 (2026-04-30)** — apply 020D2 required-status-check + enforce_admins=true branch protection.
- **D-033 (2026-04-30)** — 020D2.1 reconciliation: required-check context renamed to `policy-check / scp/policy-check` (the rendered Actions check-run name); single-operator review shape corrected to `count=0` + `codeowner=false` (GitHub forbids PR self-review, locking out the operator under count=1).
- **D-034 (2026-04-30)** — 020F renovate-tag-protection: parallel ruleset on `refs/tags/renovate/v*` (deletion / non_fast_forward / update blocked, `enforcement: active`, `bypass_actors: []`). Closes 020F R1 safety review CRIT-SAFE-001.
- **D-035 (2026-04-30)** — 020G adopter-helper invocation procedure as estate doctrine: `scripts/enable-required-check.sh` two-call PUT + POST shape, refuses CI, preserves `required_pull_request_reviews`, mandatory invocation-log commit at `docs/reviews/WP-SCP-020/branch-protection-log.md`.

## Post-Threshold-A backlog

- ~~**020E.b**: post-protection canary evidence~~ ✅ landed 2026-04-30 (PR #66, commit `8248732`).
- ~~**020E.c**: waiver-suppression canary + `scripts/replay-canary.sh`~~ ✅ landed 2026-04-30 (PR #70, commit `4962bc9`); needed 2-PR fixpoint dance for warn-msg conftest bug.
- ~~**020F**: Renovate shared preset~~ ✅ landed 2026-04-30 (PR #71, commit `2743d4a`); 4-round R1 fixpoint surfaced CRIT-SAFE-001 (renovate/v* unprotected) → D-034 + new ruleset live; preset published at `renovate/v1.0.0`.
- ~~**020G**: branch-protection automation script for adopter onboarding~~ ✅ landed 2026-04-30 (PR #74, commit `373bcd2`); fix-round-1 closed 11 R1 findings + R2 + R3 + R4 fixpoint.
- ~~**020H part 3**: ADOPT-001 §12 federation-integration appendix (closes TF-D1-001..003)~~ ✅ landed 2026-04-30 (PR #75, commit `347fde2`); 6-round recursive review reaching fixpoint at R3 (0 CRIT + 0 MAJ on all 3 lenses), 11 MAJ + 31 MIN + 11 nit closed. Opened TF-020H3-001..005.
- **020H.1**: VERSIONING.md + rule-RFC process + rollback detection (weekly canary-replay cron) + version-manifest.json + freshness-warning emit. **IN FLIGHT** (this PR's branch). Closes ADOPT-001 §12.7.5 forward-looking flag for `rule-regression` issue template + §12.7.11 forward-looking flag for freshness-warning. New: `policies/VERSIONING.md`, `docs/reviews/rule-proposals/{README,RULE-TEMPLATE}.md`, `.github/ISSUE_TEMPLATE/rule-regression.md`, `.github/workflows/canary-replay.yml`, `version-manifest.json`.
- ~~**020H.2**: Regal binary SHA256 verification — closes TF-020H3-001~~ ✅ landed 2026-05-01 (PR #77, commit `bac1427`); 3-round recursive review reaching fixpoint at R2 (0 CRIT + 0 MAJ), 3 MAJ + 5 MIN + 13 nit closed; closed 13 days ahead of the 2026-05-14 deadline.
- **SCP-073.sec**: `SECURITY.md` publication (security disclosure path for policy-bypass reports) — referenced from ADOPT-001 §12.7.8. WP-SCP-020 §4.1 follow-up; track parallel to 020H.1.
- **WP-SCP-022 proposal-queue**: structured proposal queue for new rules.
- **WP-SCP-023**: cross-repo scorecards.
- **WP-SCP-024**: estate cascade (FLA pilot → PIM/recommender/etc.).
