# WP-SCP-020 — Plan fixpoint log

Tracks how the plan evolves between adversarial-review rounds. Each row is
a finding from a round that changed the plan, with the exact slice/section
where the change landed.

## v0.1 → v0.2 (post round-1 review, 2026-04-21)

### BLOCKING findings folded in

| # | Finding (reviewer) | Resolution in v0.2 |
|---|---|---|
| 1 | Rego/Python source-of-truth conflict unspecified (architect B1) | New slice 020C.1 adds `rego-vs-python-conflict` CI job; Python authoritative on disagreement. §2 "Not a Python evaluator replacement" made explicit + permanent. |
| 2 | Waiver integration missing end-to-end (architect B2 ≡ governance B-1) | New slice 020C.1: reusable workflow reads `waivers.json`, passes to conftest as `--data`; rules consume `data.waivers` and deny only when no matching unexpired waiver present. Canary covers both hard-block and waived→pass. §9 acceptance #4 added. |
| 3 | Bootstrap circular dependency hand-waved (architect B3 + security M6) | Slice 020D split into 020D1 (wrapper merged, check NOT required, signed commit, tag-protection pre-existing) / 020D2 (required check on, `enforce_admins=true`). rc.1 tag cut before dogfood-required; rc.1 → v1.0.0 promotion gated on double-canary green. Slice ordering diagram added to §3. |
| 4 | `-o github` annotations need `pull-requests: write` (security B1) | Slice 020B acceptance (iv): `permissions:` verified against actual annotation surface (unknown U-sec-4 must resolve before slice opens). |
| 5 | `pull_request` vs `pull_request_target` unspecified (security B2) | Slice 020B acceptance (i): `on: workflow_call` only; caller wrapper uses `on: pull_request` only; refuses to run on fork PRs. §8 risks spec this too. |
| 6 | No input validation commitment (security B3) | Slice 020B acceptance (ii) + (vi): enumerated typed inputs; no `${{ inputs.* }}` or `${{ github.event.* }}` in `run:`; `env:` quoted expansion only. |
| 7 | Tag mutation on SCP not addressed (security B4) | New slice 020J adds SCP tag-protection rule for `v*` + required-signed-commits on `main` before `v1.0.0` is cut. ADOPT-001 §12 (slice 020H part 3) requires adopter pin by commit SHA with comment tag, not tag alone. |
| 8 | Annotation payload undefined (devex #1) | Slice 020B acceptance (ix) + slice 020C: every deny emits structured `{rule_id, file, path, message, remediation_url}`; workflow renders to GitHub annotation format with title and URL. Fixture asserts shape. |
| 9 | No local-reproduction path (devex #2) | New slice 020B.2 ships `scripts/scp-policy-check` + Python wrapper running conftest with identical invocation to CI. Pre-commit hook documented in ADOPT-001 §12. |
| 10 | Break-glass / admin-bypass posture missing (governance B-2) | Slice 020D2 sets `enforce_admins=true` on SCP self; slice 020H (part 3) publishes break-glass procedure (time-bound admin-PR with post-hoc waiver + D-NNN); slice 020B adds `scp_bypass: true` input emitting SCP-E004 audit marker. |

### MAJOR findings folded in

| # | Finding | Resolution |
|---|---|---|
| M-arch-1 | Slice ordering wrong (architect) | Linear dependency chain added to §3; canary immediately follows rc tag; dogfood pins rc tag. |
| M-arch-2 | Versioning strategy absent | New slice 020H.1 publishes `policies/VERSIONING.md` with semver contract on inputs / JSON schema / rule IDs; rule-RFC process (48h window, `v1.x-rc.N`, 4h rollback SLA). |
| M-arch-3 | JSON summary schema undefined (≡ devex #5) | Slice 020B acceptance (x): `schemas/policy-check-summary.schema.json` with `schema_version: "1.0.0"`; payload includes schema_version + PR SHA + base ref + rule-set tag + workflow-run-id. |
| M-arch-4 | No observability surface | Slice 020B acceptance (xii): commit status with stable context `scp/policy-check`. Aggregate visibility deferred to WP-SCP-023 (named in §4.1 + §8). |
| M-arch-5 | Downstream-coupling / SCP-outage blast radius | Slice 020B acceptance (xi): OPA/Conftest binaries cached with vendored fallback; fail-closed with named error codes SCP-E001–E004. Break-glass input (xi) added. |
| M-arch-6 | Rule deprecation / opt-out path | Slice 020C.1: caller-side `.scp/rule-config.yaml` override with rule-level `disable` + `justification` + `expires_at`; deprecated rules emit one-release warning before removal. |
| M-arch-7 | No reusable workflow test strategy (≡ devex #3) | New slice 020B.1 workflow integration test harness: fixture-pass / fixture-fail fixtures + `workflow-selftest` job. |
| M-arch-8 | SVC-003 evolution coupling | Slice 020C locks starter rules to pre-D-021 shape explicitly; §8 risk names D-021 re-cut path; 020H.1 RFC-lite mechanism handles the `v1.x` bump. |
| M-sec-1 | Renovate preset compromise | Slice 020F acceptance: preset pin-by-ref required, separate tag series `renovate/v1.0.0`, CODEOWNERS on `renovate/**` for two-person review, Dependabot monitors `.github/workflows/*.yml` and `policies/**`. SCP self-repo consumes its own preset (validation-in-WP, not deferred to 020I). |
| M-sec-2 | `setup-opa` community-maintained | Slice 020B acceptance (v): binary version-pin + checksum verification + Sigstore attestation where upstream publishes. U-sec-1 closes before slice opens. |
| M-sec-3 | Caller secret exfiltration via `secrets: inherit` | Slice 020B acceptance (iii): no `secrets:` on reusable workflow; ADOPT-001 §12 forbids `secrets: inherit`. |
| M-sec-4 | Rego bundle integrity | Slice 020C: CODEOWNERS on `policies/**`; slice 020J: required-signed-commits on SCP `main` before `v1.0.0`. |
| M-sec-5 | `enable-required-check.sh` token scope + audit | Slice 020G acceptance rewritten: fine-grained PAT `administration:write` on single repo, refuses without `--repo`, `--plan` flag, invocation logged to `branch-protection-log.md`, bootstrap-only header. |
| M-sec-6 | Bootstrap trust gap (≡ architect B3 resolution) | Slice 020D1: signed merge commit; slice 020J: tag-protection before 020D1; slice 020E: double canary (pre + post protection). |
| M-gov-3 | Rule-6 pressure governance | Slice 020H.1 RFC-lite process with 48h window, rc.N gating, 4h rollback SLA. |
| M-gov-4 | D-022 "cheapest path" undefended vs policy-bot | §10 D-022 rationale rewritten to explicitly reject policy-bot (HCL-not-Rego, no Renovate cascade, no waiver-overlay model) and custom control-plane (build cost, duplicates GitHub primitives). |
| M-devex-4 | No `policies/README.md` | Slice 020A stub + slice 020C completion; sections on naming / deny-payload / fixture-layout / linter-invocation / worked example. `regal lint` + `opa fmt --fail` added to workflow. |
| M-devex-6 | Caller wrapper minimalism unspecified | Slice 020H (part 3): ≤ 12-line wrapper, zero required inputs (all defaulted in reusable workflow). |

### MINOR findings folded in

| # | Finding | Resolution |
|---|---|---|
| m-arch-1 | 020G "audit-logged" undefined | Slice 020G (iv): log target `docs/reviews/WP-SCP-020/branch-protection-log.md` with SHA, operator, timestamp, before/after API response. |
| m-arch-2 | 020F Renovate-preset org-config verification unowned | 020F acceptance: org-config verification before slice opens (U-sec-3 + U-gov-1). |
| m-arch-3 | ACC not mentioned | Correctly orthogonal. Named as WP-SCP-021 dependency in §4.1 + §12. |
| m-arch-4 | BACKLOG row SCP-073 vs Phase 9 naming | §4 table explicitly names "new Phase 9"; slice 020A adds the Phase 9 row. |
| m-sec-1 | `id-token` not mentioned | §8 risks: "no `id-token` permission in v1.0.0"; slice 020B acceptance (viii). |
| m-sec-2 | Script-injection via PR title/branch name | Slice 020B acceptance (vi): explicit prohibition. |
| m-sec-3 | Cache-poisoning via `actions/cache` | Slice 020B acceptance (vii): no `actions/cache` in v1.0.0. |
| m-sec-4 | Dependabot parity | Slice 020F (v): `.github/dependabot.yml` monitors workflows + policies. |
| m-sec-5 | SECURITY.md / embargo path | Follow-up ticket `SCP-073.sec` opened; slice 020H ADOPT-001 §12 adds pointer. |
| m-devex-8 | `enable-required-check.sh` robustness | Slice 020G acceptance: gh version check, jq dep, fine-grained PAT, `--plan` flag. |
| m-devex-9 | Canary evidence format | Slice 020E: committed fixture branches + JSON dumps + `replay-canary.sh`. |
| m-devex-10 | Python/Rego scope silent skip | Slice 020H §12 (vii): explicit "Rego = PR gate; Python = nightly/manual/release-gate". |
| m-devex-11 | Renovate preset drift freshness warning | Slice 020B / 020H (xiii): workflow annotates when caller pin > 2 minor versions behind latest via `version-manifest.json`. |
| m-devex-12 | Cold-start cost unstated | Slice 020E (d): cold + warm wall-clock times recorded in canary evidence. |

### Follow-up tickets opened (explicit out-of-WP, not descope)

- `SCP-073-compose` — FLA `.claude/review_gate` ↔ federation-primitive composition (delivered in WP-SCP-021).
- `SCP-073-scaffolder` — `scripts/scaffold-downstream.sh` (ready before WP-SCP-024).
- `SCP-073.audit` — append-only audit mirroring (WP-SCP-023 or sooner).
- `SCP-073.sec` — `SECURITY.md` embargo path.
- `SCP-074` — deny-by-default JSON-schema conformance against agents restructuring files to evade shape checks.

### Unknowns carried forward (must close before named slice)

U-sec-1 (OPA Sigstore), U-sec-2 (org plan tier), U-sec-3 (Renovate extends
ref/HEAD), U-sec-4 (Conftest annotation surface), U-devex-2 (Rego bundle
vs per-rule), U-arch-2 (caller vs SCP secrets), U-gov-1 (Renovate org
config). See plan §13 for close-before-slice mapping.

**Deltas resolved in-plan without slice action:**
- U-devex-1 → changed-files for v1.0.0.
- U-arch-1 → rule-ID scheme `SCP-R-NNN`.
- U-arch-3 → 020G `--branch` required arg.
- U-arch-4 → rc.1 → v1.0.0 promotion via `release-signoff.md`.
- U-arch-5 → "no applicable rules" returns green + empty-findings artefact.

## v0.2 → v0.3 (post round-2 review, 2026-04-21)

### BLOCKING findings folded in (6 unique from round 2)

| # | Finding | Resolution in v0.3 |
|---|---|---|
| 1 | A-N1 Conflict-gate adapter + fixture path unspecified | 020C.1 (iv): adapter module `tests/conflict_gate/adapter.py` normalises both engines to `{rule_id, file, verdict, reason}`; shared fixture tree at `tests/conflict_gate/fixtures/<SCP-R-NNN>/<scenario>/{input.yml, expected-verdict.json}`; CI job `rego-vs-python-conflict` loads every fixture and asserts parity. Fixture authoring documented in `policies/README.md` step 5. |
| 2 | A-N2 Slice-ordering diagram self-contradictory | §3 redrawn. Canonical order: `020J → 020D1 → 020H(rc.1) → 020E.a → 020H(v1.0.0) → 020D2 → 020E.b → 020E.c → 020F → 020G → 020H(part 3) → 020H.1`. Tag protection now precedes rc cut. |
| 3 | A-N3 Unknowns leak past plan merge | §14 introduced — plan-PR-blocking unknowns (U-sec-2 only, needs James confirmation). §13 lists unknowns closed in v0.3 (U-sec-4 via Conftest docs, U-arch-2 via GH reusable-workflow semantics, U-devex-1, U-arch-1/3/4/5). §15 lists unknowns that close before specific slice (non-plan-blocking). |
| 4 | A-N4 + B-BS-2 `scp_bypass: true` access control | 020B (viii-c): bypass fails closed unless **all three** gates satisfied — (1) CODEOWNER or `scp-break-glass` team approving review; (2) sibling commit with D-NNN record + matching `waivers.json` entry in the same PR (not "within 5 days"); (3) waivers.json entry readable + schema-passing. SCP-E004 is merge-blocking unless matched. Daily scan in 020H.1 opens tracking issue on unpaired emissions. |
| 5 | B-BS-1 + A-N5 Python-authoritative non-operational / tyranny | 020C.1 (iii) rewritten: disagreement **fails closed** (blocks merge) + emits `SCP-E005 conflict-gate-disagreement`; adjudication is an amending decision record. "Python authoritative" is a CI-time resolution direction only, not a runtime auto-pass. §2 updated. |
| 6 | B-BS-3 ≤ 12-line wrapper arithmetic | Number dropped. 020H(part 3) publishes exact 14-line minimal wrapper in-plan (YAML block). Scaffolder follow-up `SCP-073-scaffolder` generates it for adopters. |

### MAJOR findings folded in

| # | Finding | Resolution |
|---|---|---|
| B-BS-4 | `.scp/rule-config.yaml` silent cascade-weakening | 020C.1 (vi): disabled rules emitted into JSON summary `disabled_rules` list AND enumerated in `scp/policy-check` commit-status text ("3 rules enabled, 1 disabled: SCP-R-002 until 2026-06-15"). SCP-E006 error code added. WP-SCP-023 aggregates across estate. |
| B-BS-5 | RFC 48h window theatre | 020H.1 (iii): quorum = 1 SCP-CODEOWNER approval = merge-eligible after 48h wall-clock (weekends count); 0 approvals = auto-defer. |
| B-BS-6 | Rollback-SLA 4h has no pager | 020H.1 (iv): honesty downgrade. "Best-effort, no paging rotation in v1.0.0." Detection mechanisms: (a) adopter issue template `.github/ISSUE_TEMPLATE/rule-regression.md`; (b) SCP-side canary re-run on each release; (c) Dependabot/Renovate monitoring of SCP self's pin. Target 4h from report to tag-pin revert; escalation via SCP issue tracker. |
| B-BS-7 | `workflow-selftest` trigger contradiction | 020B.1: trigger changed to `pull_request` on paths `.github/workflows/policy-check.yml`, `policies/**`, `tests/workflow/**`. No `workflow_dispatch` confusion. |
| B-BS-8 | `scripts/scp-policy-check` binary SHA parity unspecified | 020B.2 acceptance: `scripts/.tool-versions` + `scripts/scp-policy-check.lock` committed with SHA256 for linux-x64 + darwin-arm64 + darwin-x64; script verifies SHA256 before execution; offline support if binaries pre-present; `lib/policy_check_invocation.sh` shared between CI and local. |
| A-N6 | 15-slice review cost | §9(15): slice-by-slice review checkpoints — each slice posts PR review comment; reviewer signs off before next opens. |
| A-N7 | U-arch-2 leaks past plan merge | §13 U-arch-2 CLOSED in v0.3 (reusable workflow inherits caller token + permissions ceiling). |
| A-N8 | 020B (xi) triple-purpose numbering | Split into (viii-a) cache/fallback, (viii-b) error codes, (viii-c) break-glass gates. |
| A-N9 | ≤ 5 rules but only 3 listed | Commit to **exactly 3** rules in v1.0.0 (SCP-R-001/002/003). Rules 4+ via RFC in `v1.1.x`. |

### MINOR findings folded in

| # | Finding | Resolution |
|---|---|---|
| B-BS-9 | `policies/README.md` prose-wall risk | 020C: template-first format. Copy-pasteable skeleton `policies/<rule-id>.rego`; copy-pasteable fixture pair; numbered 7-step checklist; linter invocations; deny-payload schema reference. |

### STRUCTURAL (considered, rejected)

- **B-BS-10 WP split at rc→promote boundary.** Rejected. James directive: no descoping, no deferring. WP stays monolithic. A-N6 slice-by-slice review checkpoints address review-cost concern.

### Unknowns resolved in v0.3 (not slice-blocking, not plan-blocking)

- **U-sec-4 CLOSED.** Conftest `-o github` = workflow-command annotations, no extra perms.
- **U-arch-2 CLOSED.** Reusable workflow inherits caller token with caller `permissions:` ceiling.
- **U-devex-1 CLOSED.** Changed-files mode for v1.0.0.
- **U-arch-1/3/4/5 CLOSED.** Rule-ID scheme `SCP-R-NNN`; `--branch` required arg; rc→v1.0.0 via `release-signoff.md`; no-applicable-rules = green + empty-findings artefact.

### Plan-PR-merge-blocking unknown remaining

- **U-sec-2 OPEN.** `jrnb2024` GitHub org plan tier support for `enforce_admins` + tag-protection + required-signed-commits + required status checks. Needs James confirmation. Plan cannot merge until chosen between (a) Pro tier, (b) public repo, (c) signed-release-manifest substitute.

## v0.3 → v0.4 (post round-3 review, 2026-04-21)

### BLOCKING findings folded in (2 unique from round 3)

| # | Finding | Resolution in v0.4 |
|---|---|---|
| 1 | F1 + N-2: `scp_bypass` three-gate enforcement is words not mechanism | **New slice 020K** creates `scp-break-glass` GitHub team + CODEOWNERS wiring. 020D2 acceptance adds branch-protection flags `required_approving_review_count=1`, `dismiss_stale_reviews: true`, `require_review_from_non_author` per 020K outcome. 020B(viii-c) Gate (2) names `scripts/verify-bypass-pairing.sh` with concrete regex — executes `git diff --name-only base..HEAD`, requires both `docs/DECISIONS.md` and `waivers.json` in diff, greps `^### D-0[0-9]{3}\s+\(20[0-9]{2}-` for new D-NNN heading, cross-refs `waivers.json` entry `rule_id` against bypass-triggering rule, fails SCP-E004 on any miss. |
| 2 | F2 + N-3: SCP-E005 unblock path undefined + bus-factor | 020C.1(iii) prose added — amending D-NNN lands in a *separate* PR that updates `tests/conflict_gate/fixtures/<SCP-R-NNN>/<scenario>/expected-verdict.json`; original blocked PR rebases. Chicken-and-egg avoided. Named approver set = `SCP-CODEOWNERS`. Bus-factor-1 accepted in §8 operational-risk row with explicit escalation path and 2026-07-21 review date. |

### MAJOR findings folded in

| # | Finding | Resolution |
|---|---|---|
| N-4 / F3 | Renovate marker missing in wrapper | 020H(part 3) YAML now includes `# renovate: datasource=github-tags depName=jrnb2024/standards-control-plane` directly above the `uses:` line. |
| N-5 / F4 | `scp-policy-check.lock` linux-arm64 missing | 020B.2(ii) now covers `linux-x64 + linux-arm64 + darwin-arm64 + darwin-x64`; (vi) adds Dependabot/Renovate watch on `scripts/.tool-versions` for upstream OPA/Conftest bumps. |
| F5 | SCP-R-003 manifest-marker ambiguity | 020C SCP-R-003 semantics rewritten: "for every manifest file present in the PR's changed-file set, marker required; repos with zero manifests return allow + SCP-E006 `no-manifest-applicable`". |
| F6 | Post-release rollback no cron | 020H.1(iv)(d) adds weekly `cron: "0 9 * * MON"` scheduled workflow replaying all three canaries against `@main` + `@v1.*`; opens `rule-regression` issue on divergence. |

### MINOR findings folded in

| # | Finding | Resolution |
|---|---|---|
| N-6 | 020J precondition phrasing | Changed to "U-sec-2 resolved at plan merge (§14)." |

### Non-blocking observations (noted, not folded)

- **N-1** line-count observation — non-blocking; plan already removed line-count claim.
- **N-7** canary mandatoriness — answered by close-reading; all three required per §9(1).
- **F7** `scripts/scp-report-disabled-rules` — optional nice-to-have; not added to v0.4 to keep scope tight; captured informally for post-WP consideration.

### Structural

- New slice 020K added to scope table, §3 diagram, §9 acceptance list.
- §8 risks adds "Bus factor on adjudication + break-glass approval" as accepted operational risk with quarterly-review escalation path.

## v0.4 → v0.5 (post round-4, 2026-04-21)

### BLOCKING fixed

| # | Finding | Resolution |
|---|---|---|
| 1 | `verify-bypass-pairing.sh` regex `^### D-0[0-9]{3}\s+\(20[0-9]{2}-` does not match the actual table-row shape in `docs/DECISIONS.md` | Regex corrected to `^\|\s*D-0[0-9]{3}\s*\|\s*20[0-9]{2}-[0-9]{2}-[0-9]{2}\s*\|` — verified against current D-001..D-020 entries in `docs/DECISIONS.md`. |

### MAJOR fixed

| # | Finding | Resolution |
|---|---|---|
| 020K personal-account path | Teams don't exist on personal GitHub accounts; team-creation-first wording was unexecutable if `jrnb2024` is a user namespace | 020K rewritten to explicitly branch on namespace type. Org-path creates team + multi-member flow. Personal-account-path skips team creation entirely, keeps James-only CODEOWNERS, `require_review_from_non_author=false`, bus-factor-1 applies. James confirms namespace type at §14. |

### Non-blocking observations confirmed

- Renovate `datasource=github-tags` correct for SHA-plus-tag-comment pin pattern.
- `cron: "0 9 * * MON"` UTC is fine (GH Actions default).
- §8 bus-factor acceptance is an honest plan decision, not a blocker-hider.

## v0.5 → v0.6 (James confirmations received 2026-04-21)

James resolved both plan-PR-blocking unknowns:
- **U-sec-2** → personal GitHub Pro (path (a)). All four branch/tag protection features supported.
- **U-k** → personal user account. 020K collapses to the personal-account path; no team creation.

v0.6 = v0.5 with:
- §14 rewritten to reflect resolutions (no longer blocking).
- 020K simplified to single personal-account path; no more branching prose.
- Frontmatter status → "ready to merge."

## v0.5 → FIXPOINT REACHED (round 5, 2026-04-21)

Round-5 single-reviewer verification returned **FIXPOINT REACHED**:

1. Regex fix in 020B(viii-c) — **FIXED**. New regex `^\|\s*D-0[0-9]{3}\s*\|\s*20[0-9]{2}-[0-9]{2}-[0-9]{2}\s*\|` matches the literal D-020 row in `docs/DECISIONS.md` (`| D-020 | 2026-04-18 | ...`); covers D-001..D-020.
2. 020K namespace branching — **FIXED**. Two-branch structure (org vs personal account); §14 U-k added as plan-PR-blocking unknown alongside U-sec-2.
3. No new BLOCKER introduced by v0.5. Scan of §3 diagram, §4 slice table, §8 risks, §9 acceptance, §14/§15 unknowns shows edits are localised; downstream slice references stay consistent.

**v0.5 ships as the plan-PR version.** Plan-PR merge requires James's confirmation of U-sec-2 (org plan tier) and U-k (namespace type) per §14.

## Review-round summary

| Round | Reviewers | Outcome | Blockers found |
|-------|-----------|---------|----------------|
| 1 | 4 parallel (architect, security, governance, devex) | → v0.2 | 9 unique BLOCKING |
| 2 | 2 parallel (arch+sec, gov+devex) | → v0.3 | 6 unique BLOCKING |
| 3 | 2 parallel (arch+sec, gov+devex) | → v0.4 | 2 unique BLOCKING |
| 4 | 1 combined | → v0.5 | 1 BLOCKING + 1 MAJOR |
| 5 | 1 combined | **FIXPOINT** | 0 |

Total distinct BLOCKING findings surfaced + closed across the review programme: 18.




