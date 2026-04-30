# Standards Control Plane — STATUS

**Last updated:** 2026-04-30 (early AM, post-020J PR open)

## At-a-glance

| Programme | State | Track |
|---|---|---|
| WP-SCP-019 (Service Auth Contract) | ✅ closed 2026-04-20 | — |
| WP-SCP-020 (Policy Federation Primitive) | 🔄 in flight (~50% slices done) | Track 1 |
| WP-SCP-021 (MCP Server) | ✅ landed 2026-04-29 (USER-GATE-C signed) | Track 2 |
| WP-SCP-022 (Implementation Programme) | 🔄 in flight (orchestrator for 020 + 021) | Meta |

## Threshold A progress (the operational finish line)

> **Threshold A definition:** SCP gates itself on its own `main` via the federation primitive's reusable workflow with a required-status-check, all three v1.0.0 Rego rules enforcing, conflict-gate green on every PR, and a v1.0.0 release tag cut.

```
020A    plan + D-022 + D-023                                     ✅ landed
020B    reusable workflow                                        ✅ landed (PR #36)
020B.1  workflow-selftest harness                                ✅ landed (PR #38)
020B.2  scripts/scp-policy-check local repro                     ✅ landed (PR #41)
020C    starter Rego rule library (3 rules)                      ✅ landed (PR #49, 2026-04-28)
020C.1  waiver-aware Rego + conflict-gate + read-back            ✅ landed (PR #52, 2026-04-29)
020J    tag-protection v* + required-signed-commits              🔄 PR #53 open (this slice)
020K    adopter onboarding + ADOPT-005 self-cert                 ⏳ next
020D1   self-dogfood wrapper merged (advisory mode)              ⏳
020H pt 1  cut v1.0.0-rc.1 + observability metrics emit          ⏳
020E.a  pre-protection canary                                    ⏳
🛑 USER-GATE-A0  human signoff before promoting to required       ⏳
020H pt 2  observability dashboards                              ⏳
020D2   flip gate to required + cut v1.0.0                       ⏳
🛑 USER-GATE-A  Threshold A signoff (FINISH LINE)                 ⏳
```

## Recent landings (last 48h)

- **PR #52 (eb66c36)** — slice 020C.1: waiver-aware Rego + conflict-gate (rego-vs-python) + caller-side `.scp/rule-config.yaml` override + `scp/policy-check-readback` commit-status. 18-commit CI fixpoint dance to get end-to-end green.
- **PR #50** — gate-helper: `SCP_OPERATOR_EMAILS_DEFAULT` extension covering all observed operator emails.
- **PR #49** — slice 020C: 3 starter Rego rules (SCP-R-001 / 002 / 003) + `policies/README.md` + `CODEOWNERS` + workflow `opa-fmt` / regal / test-coverage gate.
- **USER-GATE-C signed** (commit bcfc706, 2026-04-29) — Track 2 (MCP server) close-out.

## Active PRs

- **PR #52** ✅ MERGED — slice 020C.1.
- **PR #53** 🔄 OPEN — slice 020J. Awaiting CI + maintainer post-merge action (run `scripts/configure-020j-protections.sh`).
- **Dependabot PRs (3)** opened automatically post-#52 merge:
  - `actions/checkout` v4.2.2 → v6.0.2
  - `actions/upload-artifact` v4.6.2 → v7.0.1
  - `actions/download-artifact` v4.3.0 → v8.0.1
  Defer until after Threshold A; major-version bumps may surface CI breakage.

## Open scheduled follow-ups

| Item | Date | Source |
|---|---|---|
| D-021 atomic workday filing (D-021 reservation) | 2026-05-31 | docs/DECISIONS.md header |
| WP-SCP-019 D-019 mode.bearer_legacy operational close | 2026-09-30 | project_d019_option_b_slide |
| Branch-protection quarterly review (bus-factor-1) | 2026-07-30 | docs/security/branch-protection.md |

## Tracked-forward items from 020C.1

- **TF-005**: structural enforcement of expired rule-config at release-tag time → add to 020D2.
- **TF-006**: conflict-gate suppression-path fixture corpus → WP-SCP-023 (when Python evaluator gains waiver awareness).
- **TF-007**: re-tighten `gh attestation verify` to hard-fail when OPA upstream begins publishing Sigstore attestations.
- **TF-008**: path-scope SCP-R-002 to waivers.json files only (currently narrowed to null/string-rooted detection only) → v1.1.

## Recent decisions

- **D-029 (2026-04-29)** — `policy-check.yml` permissions block adds `statuses: write` for the read-back commit-status.
- **D-030 (2026-04-30)** — apply 020J protections (tag-protection v* + required-signed-commits on main); idempotent applier at `scripts/configure-020j-protections.sh`.
