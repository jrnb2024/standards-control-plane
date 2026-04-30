# ProgrammePlan — WP-SCP-020 Policy Federation Primitive

**Work Package:** `WP-SCP-020`
**Version:** 0.6 (FIXPOINT at round 5; §14 unknowns resolved 2026-04-21 — see `plan-fixpoint-log.md`)
**Status:** Draft — ready to merge. U-sec-2 and U-k both resolved.
**Date:** 2026-04-21
**Branch:** `feature/wp-scp-020-policy-federation-primitive-plan`
**Programme Ref:** SCP-073 (federation primitive backlog row, added in slice 020A — Phase 9)
**Decisions introduced:** D-022 (federation-primitive adoption), D-023 (chat-forum rejected / proposal queue adopted)
**§14 plan-PR blockers:** resolved 2026-04-21 — U-sec-2 = GitHub Pro personal account (path (a), all four features supported); U-k = personal user account (020K personal-account path).

## 1. Purpose

Convert SCP from an advisory, post-merge auditor into a deterministic,
pre-merge enforcement surface that every downstream repo in the estate is
bound to — without building a custom control-plane service. The primitive:

1. A **reusable GitHub Actions workflow** published by SCP, callable from
   every downstream repo via a SHA-pinned reference.
2. An **OPA/Conftest policy engine** executed inside that workflow against
   each caller PR's changed files, with waiver-aware evaluation and a
   structured annotation payload.
3. A **Renovate shared preset** that bumps every downstream repo's pin on
   SCP release.
4. A **branch-protection required-status-check** wired per downstream repo
   with `enforce_admins=true` and a named-approver break-glass procedure.

This is move #1 of the five-move MVCP captured in the 2026-04-21 strategy
session (see `project_scp_control_plane_architecture.md` in auto-memory).
Moves #2–#5 (MCP server; proposal queue; scorecards; estate rollout) follow
as separate WPs.

## 2. Why now, and what explicitly this is NOT

**Why now.** With `WP-SCP-019` closed and the estate heading into FLA /
Go-SDK / CT stabilisation, the highest-leverage foundation move is installing
the primitive that will eventually *cascade* the stabilised template across
the estate. Doing this before rollout means rollout itself runs on the
primitive rather than a bespoke per-repo migration programme.

**What this is NOT.**
- Not a migration programme. Only SCP self-pilot is forced onto the
  primitive in this WP; FLA pilot is deferred (§4.1).
- Not a rule-library deepening. **Exactly 3 rules** in v1.0.0 (§4 slice 020C);
  rules 4+ via RFC process in `v1.1+`.
- Not an MCP server (move #3 / WP-SCP-021).
- Not a proposal queue (move #4 / `WP-SCP-022-proposal-queue`, separately tracked per `docs/plans/WP-SCP-022-implementation-programme-plan.md` §12).
- Not a scorecards dashboard (move #5 / WP-SCP-023).
- Not a Python evaluator replacement. Python evaluators remain the
  deep-audit path; Rego handles fast shape-checks only. **Python and Rego
  are both authoritative in their own domain — disagreement blocks merge
  pending human adjudication** (020C.1 iii; D-022 rationale updated below).

## 3. Programme protocol position

Follows `PROG-SCP-001-autonomous-execution-plan.md`: one branch, one PR per
WP. Slices are review checkpoints on the WP-SCP-020 branch; the PR opens
when all in-WP slices are complete. Slice 020I (FLA pilot) is explicitly
deferred to a follow-up WP (§4.1).

### Slice ordering (canonical, v0.3 corrected)

```
020A  plan + review pack + D-022 + D-023 + BACKLOG row + policies/README.md stub
  ↓
020B  reusable workflow (all acceptance criteria below)  ✅ landed (PR #36)
  ↓
020B.1  workflow-selftest harness (pull_request trigger on workflow + policies/** + tests/workflow/** + schemas/policy-check-summary.schema.json)  ✅ landed (PR #38)
  ↓
020B.2  scripts/scp-policy-check local repro (tool-versions + SHA256 lockfile)  ✅ landed (PR #41)
  ↓
020C  starter Rego rule library (exactly 3 rules) + policies/README.md complete  ✅ landed (PR #49)
  ↓
020C.1  waiver-aware Rego + conflict-gate (adapter + fixture tree)  ✅ landed (PR #52, 2026-04-29)
  ↓
020J  SCP tag-protection rule for v* + required-signed-commits on main [PRECONDITION for 020D1]  🔄 in flight (this slice)
  ↓
020K  scp-break-glass team + CODEOWNERS wiring [PRECONDITION for 020D2]
  ↓
020D1  wrapper merged on SCP self (signed commit; required check NOT yet enabled)
  ↓
020H part 1  cut v1.0.0-rc.1 from 020D1 merge commit
  ↓
020E.a  pre-protection canary (unprotected branch demonstrates deny)
  ↓
020H part 2  promote v1.0.0-rc.1 → v1.0.0 (release-signoff.md records governance ok)
  ↓
020D2  required check enabled on SCP main with enforce_admins=true + review-flags per 020K
  ↓
020E.b  post-protection canary (required check blocks merge)
  ↓
020E.c  waiver-suppression canary (waiver entry suppresses deny)
  ↓
020F  Renovate shared preset + SCP self-consuming preset validation
  ↓
020G  scripts/enable-required-check.sh with branch-protection-log.md
  ↓
020H part 3  ADOPT-001 §12 appendix published
  ↓
020H.1  policies/VERSIONING.md + rule-RFC process + rollback detection
```

## 4. Scope

| Slice | Deliverable |
|-------|-------------|
| 020A | Plan doc (this), round-1/2 adversarial review evidence pack, fixpoint log, BACKLOG row SCP-073 in new Phase 9, D-022, D-023, STATUS.md stub, `policies/README.md` stub. |
| 020B | **Reusable workflow** `.github/workflows/policy-check.yml` (`workflow_call` only; caller wrapper `on: pull_request` only, refuses fork PRs). **Acceptance:** <br/>(i) `inputs:` enumerated with `type:` — `rule-set: string (default: "starter")`, `threshold: string (default: "deny")`, `annotate: boolean (default: true)`, `scp_bypass: boolean (default: false)`, `waivers-path: string (default: "output/findings/waivers.json")`, `rule-config-path: string (default: ".scp/rule-config.yaml")`, `fixture-path: string (default: ".") — restricts changed-file discovery to a path prefix; defaults to whole-repo evaluation for normal callers; used by the selftest harness for fixture-tree isolation`. <br/>(ii) No `${{ inputs.* }}` or `${{ github.event.* }}` inside any `run:` block; pass via `env:` with quoted expansion only. <br/>(iii) `permissions:` = `contents: read, statuses: write` (per D-029, 2026-04-29). `statuses: write` is required to post the 020C.1(vi) read-back commit-status on the sibling context `scp/policy-check-readback`; the privilege is bounded to `repos/<caller>/statuses/${{ pull_request.head.sha }}`. Conftest `-o github` emits workflow-command annotations `::error file=…::` which require no further perms; closure of U-sec-4. No `id-token`, no `checks: write`, no `pull-requests: write`. <br/>(iv) No `secrets:` declared on reusable workflow; adopter guidance (020H) forbids `secrets: inherit`. Caller's `GITHUB_TOKEN` is inherited with caller-declared `permissions:` as ceiling (closure of U-arch-2). <br/>(v) All `uses:` pinned by commit SHA. OPA binary version-pinned AND SHA256-verified before execution. Conftest same. Sigstore `gh attestation verify` used where upstream publishes (OPA v0.62+ — U-sec-1 closes before slice opens). <br/>(vi) No `actions/cache` in v1.0.0 (cache-poisoning surface closed). <br/>(vii) Changed-files mode (git diff against base ref) is v1.0.0 behaviour. Whole-tree adoption-sweep mode = `v1.1` input. <br/>(viii-a) OPA/Conftest binaries cached in the reusable workflow image with vendored fallback path. <br/>(viii-b) Named error codes: `SCP-E001` (infra fetch fail), `SCP-E002` (bundle load fail), `SCP-E003` (policy deny), `SCP-E004` (break-glass bypass emitted), `SCP-E005` (conflict-gate disagreement), `SCP-E006` (disabled-rule record emitted for observability). Fail-closed on infra errors. <br/>(viii-c) Break-glass (`scp_bypass: true`) fails closed UNLESS the caller's PR satisfies **all three** gates: (1) an approving review from a member of SCP-CODEOWNERS or the `scp-break-glass` GitHub team (see 020K); the caller's `main` branch protection must have `required_approving_review_count >= 1` + `dismiss_stale_reviews: true` + `require_review_from_non_author: true` — in single-operator mode (`scp-break-glass` team has only James), `require_review_from_non_author` is set `false` and bus-factor-1 is accepted per §8; (2) a sibling commit in the same PR containing both a `docs/DECISIONS.md` D-NNN record AND a matching `waivers.json` entry with `expires_at` > now — **verified by `scripts/verify-bypass-pairing.sh` run in workflow step `bypass-gate`**: script executes `git diff --name-only base..HEAD`, requires both `docs/DECISIONS.md` and `waivers.json` in the diff, greps `docs/DECISIONS.md` for a new D-NNN **table row** (regex `^\|\s*D-0[0-9]{3}\s*\|\s*20[0-9]{2}-[0-9]{2}-[0-9]{2}\s*\|` — verified against current `docs/DECISIONS.md` shape at D-001..D-020), greps the `waivers.json` diff for an added entry whose `rule_id` matches the bypass-triggering rule, refuses on any miss with `SCP-E004`; (3) the caller's `waivers.json` entry is readable by the workflow and passes schema. If any gate fails, `SCP-E004` is merge-blocking. <br/>(ix) Each deny emits structured `{rule_id, file, path, message, remediation_url}`; workflow renders to `::error file=…,title=RULE-ID::human message — see URL`. <br/>(x) JSON summary artefact with `schema_version: "1.0.0"`, `schemas/policy-check-summary.schema.json` committed. Payload includes: schema_version, PR SHA, base ref, rule-set tag, workflow-run-id, `findings: [{rule_id, file, verdict, message}]`, `disabled_rules: [{rule_id, reason, expires_at}]`, `waivers_applied: [...]`, `bypass_emitted: bool`, `conflict_gate: {run: bool, disagreements: []}`. <br/>(xi) Commit status context = `scp/policy-check` (stable; WP-SCP-023 aggregator consumer). |
| 020B.1 | **Workflow integration test harness.** `tests/workflow/fixture-pass/` and `tests/workflow/fixture-fail/`, each with minimal `services.yml` + expected annotations JSON. SCP-local job `workflow-selftest` trigger = `pull_request` on paths `.github/workflows/policy-check.yml`, `policies/**`, `tests/workflow/**`, `schemas/policy-check-summary.schema.json` (expected-annotations.json is schema-bound; schema changes must re-validate all fixture expectations; blocks merge of any PR touching those paths). |
| 020B.2 | **Local reproduction.** `scripts/scp-policy-check` shell script + `python -m standards_control_plane.policy_check`. Acceptance: (i) `scripts/.tool-versions` committed — OPA + Conftest versions; (ii) `scripts/scp-policy-check.lock` committed with SHA256 of both binaries for **linux-x64, linux-arm64 (GitHub `ubuntu-24.04-arm` runners), darwin-arm64, darwin-x64**; script prints a clear error and exits non-zero on unlisted platforms; (iii) script downloads binaries at first run, verifies SHA256, refuses to run on mismatch; (iv) offline support if binaries are already present at expected paths; (v) uses identical Rego bundle (checkout SCP at same pin), identical inputs, identical invocation to CI — single source of truth for invocation is `lib/policy_check_invocation.sh` sourced by both CI workflow and local script; (vi) `.github/dependabot.yml` (or a Renovate rule) watches `scripts/.tool-versions` so OPA/Conftest upstream releases open automation PRs against SCP self with lockfile bumps. |
| 020C | **Starter Rego rule library** at `policies/*.rego`. **Exactly 3 rules** in v1.0.0 (BS-9 + A-N9 closure): <br/>  **SCP-R-001** `services.yml` root-shape conformance to **pre-D-021 SVC-003 mode set** (`mode.user_oidc`, `mode.service_rs256`, `mode.api_key`, `mode.bearer_legacy`); `deprecation_close_date` ∈ {`"2026-06-30"`, `"2026-09-30"`}. <br/>  **SCP-R-002** `waivers.json` entry schema — required keys `approved_by`, `created_at`, `expires_at`, `rule_id` ∨ `finding_id`. <br/>  **SCP-R-003** ADOPT-001 §11 vendoring-manifest marker presence. **Semantics:** for every manifest file present in the PR's changed-file set (`package.json`, `pyproject.toml`, `go.mod`), the marker must be present; repos with zero manifests in the changed set return `allow` and emit an `SCP-E006` observability record `{rule_id: SCP-R-003, reason: "no-manifest-applicable"}` into the JSON summary so the enforcement gap is visible to WP-SCP-023 aggregation. <br/>**Each rule:** (i) deny emits structured `{rule_id, message, remediation_url}`; (ii) fixtures under `policies/testdata/<rule_id>/{allow,deny}.{yml,json}`; (iii) `opa test` coverage ≥ 90%. <br/>**`policies/README.md` complete** (started in 020A) — **template-first format**: (1) copy-pasteable skeleton `policies/<rule-id>.rego` template; (2) copy-pasteable skeleton fixture pair; (3) numbered 7-step checklist for contributing a rule; (4) explicit `opa fmt --fail` + `regal lint` + `opa test` invocation; (5) deny-payload schema reference; (6) CODEOWNERS + RFC link. Rule-ID scheme = `SCP-R-NNN`. <br/>CODEOWNERS rule on `policies/**` requiring review from named reviewer(s). `regal lint` + `opa fmt --fail` added to workflow. |
| 020C.1 | **Waiver-aware Rego + conflict-gate.** <br/>(i) Reusable workflow reads caller's `waivers.json` at `waivers-path`; passes to conftest as `--data`. Rules consume `data.waivers`; `deny` only when no matching unexpired waiver (`expires_at` > now by `rule_id` or `finding_id`). <br/>(ii) Canary includes: hard-block, waived→pass, and rule-config-disabled paths. <br/>(iii) **Conflict-gate.** Disagreement between Python evaluator and Rego rule on shared fixture = **merge-blocked** with error code `SCP-E005`. Adjudication is an amending decision record authored by any member of `SCP-CODEOWNERS` (solo today = James only; §8 accepts bus-factor-1 operational risk). "Python authoritative on conflict" is a CI-time contract only for the eventual resolution direction; it is NOT a runtime auto-pass. **Unblock path on SCP-E005:** the amending D-NNN lands in a *separate* PR that updates `tests/conflict_gate/fixtures/<SCP-R-NNN>/<scenario>/expected-verdict.json` to match the now-ratified verdict; the CI job `rego-vs-python-conflict` then green-lights fixtures against adapter outputs. The original blocked PR rebases onto main and re-runs. Chicken-and-egg avoided — the conflict-gate-failing PR is never the place where adjudication lands. <br/>(iv) **Conflict-gate mechanics (closure of A-N1):** <br/>    — **Adapter** at `tests/conflict_gate/adapter.py` normalises both engines' outputs to `{rule_id, file, verdict: allow|deny, reason: str}`. <br/>    — **Shared fixture tree** at `tests/conflict_gate/fixtures/<SCP-R-NNN>/<scenario>/{input.yml, expected-verdict.json}`. <br/>    — **CI job** `rego-vs-python-conflict` loads every fixture, runs both engines through adapter, asserts `rego.verdict == python.verdict == expected.verdict`. Any divergence fails the job. <br/>    — Fixture authoring is a **per-rule tax**, enumerated in `policies/README.md` step 5. <br/>(v) **Caller-side `.scp/rule-config.yaml` override** with rule-level `disable: <SCP-R-NNN>` + `justification: string` + `expires_at: date`. Deprecated rules emit one-release warning before removal. <br/>(vi) **Read-back (BS-4 closure).** Every disabled rule is emitted to JSON summary `disabled_rules` list AND enumerated in the `scp/policy-check` commit-status text ("3 rules enabled, 1 disabled: SCP-R-002 until 2026-06-15"). WP-SCP-023 aggregates across estate. |
| 020J | **SCP tag-protection rule + required-signed-commits.** `v*` tag-protection rule on SCP (prevents force-push of release tags). Required-signed-commits on `main` before `v1.0.0` is cut. **Precondition:** U-sec-2 resolved at plan merge (§14). If §14 resolution is (c) signed-release-manifest substitute: add `docs/releases/v1.0.0.sig` — detached Sigstore signature of the tag's tree hash, committed alongside the tag; Renovate preset pin-check verifies the signature at bump time. |
| 020K | **`CODEOWNERS` wiring (personal-account / single-operator mode).** U-k resolved 2026-04-21: `jrnb2024` is a GitHub personal user account; GitHub teams are not available on user namespaces. Personal-account path: (a) no `scp-break-glass` team created; (b) `CODEOWNERS` names `@jrnb2024` on `policies/**`, `renovate/**`, `.github/workflows/**`, `docs/DECISIONS.md`, `output/findings/waivers.json`; (c) branch-protection `require_review_from_non_author=false` at 020D2 (solo operator; self-approval is the only option); (d) §8 bus-factor-1 risk live; quarterly escalation review 2026-07-21 named in STATUS.md and memory. When a second maintainer onboards: add them to `CODEOWNERS`, flip `require_review_from_non_author=true`, amend §8 risk row to CLOSED. Slice completes before 020D2 opens. |
| 020D1 | **SCP self-dogfood wrapper merged (check NOT yet required).** SCP's own repo adds `.github/workflows/policy-check-wrapper.yml` calling the reusable workflow at `@<commit-SHA-of-v1.0.0-rc.1>`. Branch protection on `main` does *not* yet include the check. Merge commit must be signed (Sigstore/GPG). **Precondition:** 020J complete. |
| 020H part 1 | **Cut `v1.0.0-rc.1` tag** from the 020D1 merge commit. Release notes enumerate: exact 3 rules; error codes SCP-E001–E006; known limitations. |
| 020E.a | **Pre-protection canary.** Committed fixture branch `canary/deliberate-violation-pre` with deliberate Rego violation; `gh pr view --json` dump stored; failing workflow-run-id recorded; cold-start + warm-start wall-clock times recorded (closure of m-devex-12). Evidence in `canary-evidence.md`. |
| 020H part 2 | **Promote `v1.0.0-rc.1` → `v1.0.0`** after 020E.a green. Governance sign-off logged in `docs/reviews/WP-SCP-020/release-signoff.md` (named signer + timestamp + canary run-id reference). |
| 020D2 | **Enable required status check on SCP `main`.** `scp/policy-check` required on `main` with `enforce_admins=true` (closure of governance B-2). Branch-protection also sets: `required_approving_review_count=1`, `dismiss_stale_reviews: true`, and `require_review_from_non_author` per 020K outcome (`true` if team has ≥ 2 members; `false` + bus-factor-1 acceptance in §8 if solo). Break-glass procedure published in ADOPT-001 §12 — three-gate model per 020B(viii-c). |
| 020E.b | **Post-protection canary.** Second branch `canary/deliberate-violation-post` confirms required check blocks merge after 020D2. Evidence appended to `canary-evidence.md`. |
| 020E.c | **Waiver-suppression canary.** Branch `canary/waived-violation` demonstrates a `waivers.json` entry with `expires_at` in future suppresses the matching Rego deny (green PR). `scripts/replay-canary.sh` replays all three (a/b/c). |
| 020F | **Renovate shared preset.** `renovate/default.json` at repo subpath. Acceptance: (i) exported via `github>jrnb2024/standards-control-plane//renovate/default#<tag>`; (ii) regex-managers bump the wrapper's `@SHA` + comment-tag (not tag alone) — adopter pin remains a commit SHA; (iii) preset versioned with own tag series `renovate/v1.0.0` independent of workflow tag series; (iv) CODEOWNERS on `renovate/**` requires named reviewer(s); (v) `.github/dependabot.yml` in SCP self monitors `.github/workflows/*.yml` and `policies/**` (closure of m-sec-4); (vi) **SCP self consumes its own preset in this WP** (validates the cascade in-WP, not deferred); (vii) org-config verification (U-sec-3 + U-gov-1) closes before slice opens. |
| 020G | **Branch-protection automation.** `scripts/enable-required-check.sh`. Acceptance: (i) header asserts `gh --version >= 2.40`, `jq` on PATH, required fine-grained PAT scopes (`administration:write` on single target repo only); (ii) refuses without `--repo` and `--branch`; `--plan` flag prints PUT payload without applying; `--enforce-admins` flag defaults true; (iii) logs invocation (SHA of script, operator, timestamp, target, before/after API response JSON) to `docs/reviews/WP-SCP-020/branch-protection-log.md` — the log commit is part of the invocation procedure; (iv) bootstrap-only header declares script is not run unattended. |
| 020H part 3 | **ADOPT-001 §12 appendix "Federation primitive — adopter integration."** Contains exact minimal caller wrapper text below — no line-count claim, just the literal minimal YAML with Renovate marker (closure of BS-3 + N-4/F3): <br/>``` <br/># .github/workflows/policy-check.yml <br/>name: policy-check <br/>on: <br/>  pull_request: <br/>    branches: [main] <br/>permissions: <br/>  contents: read <br/>  statuses: write  # required for scp/policy-check-readback per D-029 / 020C.1(vi) <br/>jobs: <br/>  policy-check: <br/>    # renovate: datasource=github-tags depName=jrnb2024/standards-control-plane <br/>    uses: jrnb2024/standards-control-plane/.github/workflows/policy-check.yml@<commit-SHA>  # tag: v1.0.0 <br/>``` <br/>Additional sections: (i) Renovate `extends:` snippet pin-by-ref; (ii) branch-protection setup via 020G script; (iii) break-glass procedure with the three-gate model; (iv) rollback procedure (revert wrapper `@SHA` + re-run Renovate); (v) Python-evaluator / Rego scope ("Rego = PR gate; Python = nightly/manual/release-gate"); (vi) error codes SCP-E001–E006; (vii) `SECURITY.md` pointer for policy-bypass disclosure; (viii) pre-commit hook snippet invoking `scripts/scp-policy-check`; (ix) "no `secrets: inherit`" adopter requirement; (x) freshness-warning — workflow annotates when caller's pin is > 2 minor versions behind latest (via `version-manifest.json` fetched at checkout); (xi) Actions-billing note. |
| 020H.1 | **`policies/VERSIONING.md` + rule-RFC process + rollback detection.** <br/>(i) Semver contract on (a) `workflow_call` inputs, (b) `schemas/policy-check-summary.schema.json`, (c) rule IDs. Breaking changes require an amending decision row. <br/>(ii) Rule deprecation: one-release warning-annotation window before removal. <br/>(iii) Rule addition: RFC-lite process — `docs/reviews/rule-proposals/RULE-NNN.md` drafts; **quorum = 1 SCP-CODEOWNER approval**; review window = 48h wall-clock (weekends count); 0 approvals = auto-defer to next cycle (closure of BS-5). <br/>(iv) Rollback detection: **best-effort, no paging rotation in v1.0.0.** Detection mechanisms (closure of BS-6 + F6): (a) adopter-reported via SCP issue template `.github/ISSUE_TEMPLATE/rule-regression.md`; (b) SCP-side canary re-run on each release (CI matrix across all three canaries); (c) Dependabot/Renovate monitoring of SCP self's own pin (if workflow-selftest breaks on SCP own PR, that IS the signal); (d) **weekly scheduled workflow** (`cron: "0 9 * * MON"`) in SCP self replays `canary/deliberate-violation-pre`, `canary/deliberate-violation-post`, `canary/waived-violation` against the currently-released `@main` + `@v1.*` tags — divergence from rc-cut canary baseline opens a `rule-regression` issue automatically; (e) target 4h from report to tag-pin revert; escalation path = SCP issue tracker. |

### 4.1 Deferred to follow-up WP (explicit reason)

| Slice / WP | Deliverable | Blocker |
|---|---|---|
| 020I → `WP-SCP-020.1` | FLA pilot wiring at v1.0.0 pin. | (a) FLA economical; (b) Go SDK for CT auth landed; (c) CT lessons absorbed. Not in 020 acceptance. |
| → `WP-SCP-021` | SCP as MCP server (MVCP move #3). Carries ACC integration, cross-repo D-NNN visibility, FLA `.claude/review_gate` composition (SCP-073-compose). | Depends on 020. |
| → `WP-SCP-022-proposal-queue` | Structured proposal queue (MVCP move #4). D-023 rationale body expands here. (Note: `WP-SCP-022` itself is the implementation programme plan for this WP and 021; the proposal-queue WP is a separate later candidate.) | Depends on 021. |
| → `WP-SCP-023` | Estate scorecards + aggregate observability. Carries SCP-073.audit. | Depends on JSON summary flowing. |
| → `WP-SCP-024` | Estate rollout of required check across `{pim, recommender, shopify-app, mapp-doc-agent, control-tower, …}`. Gated on §7 + 020.1 + SCP-073-scaffolder. |
| Follow-up `SCP-073-scaffolder` | `scripts/scaffold-downstream.sh` emits all adopter artefacts from template. | Opens now; ready before WP-SCP-024. |
| Follow-up `SCP-073-compose` | FLA local gate ↔ federation primitive composition. | Opens now; delivered in WP-SCP-021. |
| Follow-up `SCP-073.audit` | Append-only audit mirror of JSON summary artefact on a schedule. | Opens now; WP-SCP-023 or sooner. |
| Follow-up `SCP-073.sec` | `SECURITY.md` embargo path. | Opens now; landed in 020H pointer + separate PR. |
| Follow-up `SCP-074` | Deny-by-default JSON-schema conformance (hardens against agents restructuring files to evade shape checks). | Opens now; scheduled post-estate-rollout. |

## 5. Out of scope

- Enabling required check on any repo beyond SCP self.
- SCP as MCP server; proposal queue; scorecards; cross-repo D-NNN indexing.
- Expanding the Rego rule library beyond the starter 3.
- Estate-wide branch-protection rollout.
- Python evaluator replacement (explicitly permanent out-of-scope).
- Whole-tree adoption-sweep mode (v1.1).
- On-call paging rotation for rollbacks (v1.x).

## 6. External dependencies

| Dependency | Owner | Notes |
|------------|-------|-------|
| `setup-opa` GitHub Action | OPA project | SHA-pinned action + binary version-pin + SHA256 + Sigstore verify. |
| Conftest | OPA project | Same. |
| Renovate Bot hosted app | Mend | Already active on `jrnb2024`; org-config extends semantics verified before 020F. |
| GitHub branch-protection API + tag-protection + required-signed-commits + `enforce_admins` | GitHub | **U-sec-2 confirms org plan tier supports all four.** See §14. |
| `actions/checkout`, `actions/upload-artifact` | GitHub | SHA-pinned. |
| `regal` Rego linter | StyraInc | Version-pinned. |

## 7. Rollout prerequisites for estate-wide adoption (not required for this WP)

Same as v0.2. Sequence: FLA economical → Go SDK landed → CT lessons
absorbed → WP-SCP-020.1 (FLA pilot) → WP-SCP-024 (estate rollout).

## 8. Risks (specification, not reassurance)

Every risk has a testable acceptance anchor in the named slice.

- **Supply chain.** 020B pins actions by SHA, binaries by version + SHA256 + Sigstore. 020F `.github/dependabot.yml` monitors workflows + `policies/**`.
- **Privilege escalation / secret exfiltration.** 020B: no `secrets:` on reusable workflow; adopter forbids `secrets: inherit`; `contents: read` plus `statuses: write` (per D-029, scoped to `repos/<caller>/statuses/<head_sha>` for the 020C.1(vi) read-back); no `id-token`, `checks: write`, or `pull-requests: write`. Caller `GITHUB_TOKEN` inherited with caller `permissions:` as ceiling.
- **Input validation / injection.** 020B: enumerated typed inputs; no `${{ inputs.* }}` / `${{ github.event.* }}` in `run:`; `env:` quoted only; no `pull_request_target`; no `actions/cache`.
- **Rego bundle integrity.** 020C: CODEOWNERS on `policies/**`. 020J: required-signed-commits on SCP `main` before `v1.0.0`.
- **Tag mutation.** 020J tag-protection rule for `v*` (precondition for 020D1). Adopters pin by commit SHA; Renovate preset bumps SHA+comment-tag.
- **Rego false-positive cascade.** Starter set = 3 rules. Staged release: `v1.0.0-rc.1` cut before `v1.0.0` promotion. SCP self double-canary (020E.a + 020E.b). Rollback: best-effort 4h via multi-mechanism detection (020H.1 iv).
- **SCP-outage blast radius.** 020B: OPA/Conftest cached with vendored fallback; named error codes SCP-E001–E006 distinguish infra-fail from policy-deny.
- **Break-glass abuse.** 020B(viii-c): `scp_bypass: true` fails closed unless three gates satisfied (CODEOWNER approval + sibling D-NNN + matching waivers.json). Daily scan workflow (in 020H.1) opens tracking issue on unpaired SCP-E004 emissions.
- **Rule/waiver/config cascade weakening.** 020C.1(vi): disabled rules emit into JSON summary AND commit-status text; WP-SCP-023 aggregates.
- **Rego/Python drift.** 020C.1(iii-iv): `rego-vs-python-conflict` CI job with adapter + shared fixtures; disagreement = merge-blocked SCP-E005.
- **SVC-003 evolution coupling.** 020C rules locked to pre-D-021 shape; D-021 (2026-05-31) re-cuts `v1.1.0` via RFC with rc track.
- **Bootstrap trust.** 020J (tag-protection + signed-commits) PRECEDES 020D1 (signed merge commit). rc.1 cut → canary pre → promote to v1.0.0 → required check on → canary post.
- **Caller-wrapper drift.** 020H ships the exact minimal wrapper (14 lines, zero required inputs). Renovate preset bumps the SHA.
- **Observability.** Per-repo Actions UI + `scp/policy-check` commit-status context tolerated for pilot. Aggregate dashboard deferred to WP-SCP-023.
- **Audit-trail retention.** GH workflow logs = 90-day retention. Extended mirror = follow-up `SCP-073.audit`.
- **Actions billing.** ADOPT-001 §12 notes caller-minute consumption.
- **Bus factor on adjudication + break-glass approval (accepted operational risk).** Today SCP has a single operator (James). The `scp-break-glass` team (020K) and `SCP-CODEOWNERS` set both initially name James only; `require_review_from_non_author` is `false` at 020D2 to avoid blocking all PRs; SCP-E005 conflict-gate adjudication names `SCP-CODEOWNERS` (= James). Accepted as operational exposure for v1.0.0; escalation path: when a second maintainer joins the estate, (a) add them to `scp-break-glass` team, (b) add them to `SCP-CODEOWNERS`, (c) flip `require_review_from_non_author` to `true`, (d) amend this risk row to CLOSED. Review quarterly; re-evaluate at 2026-07-21.

## 9. Acceptance criteria

The WP-SCP-020 PR merges when all of:

1. Slices 020A, 020B, 020B.1, 020B.2, 020C, 020C.1, 020J, 020K, 020D1, 020H(part 1), 020E.a, 020H(part 2), 020D2, 020E.b, 020E.c, 020F, 020G, 020H(part 3), 020H.1 complete on-branch.
2. SCP's own `main` has `scp/policy-check` required with `enforce_admins=true`; last 3 PRs show check passing.
3. All three canaries (020E.a, 020E.b, 020E.c) demonstrate expected blocking + suppression behaviour; evidence = committed fixture branches + `gh pr view --json` dumps + workflow-run-ids + cold/warm wall-clock times; `scripts/replay-canary.sh` replays all.
4. `rego-vs-python-conflict` CI job passes on shared fixture corpus (≥ 6 fixtures, 2 per rule).
5. `opa test` ≥ 90% coverage; `opa fmt --fail` + `regal lint` green.
6. `workflow-selftest` green on pass + fail fixtures.
7. `scripts/scp-policy-check` reproduces CI verdict on staged files; pre-commit hook integration tested; binary SHA256 verification exercised.
8. `policies/README.md` + `policies/VERSIONING.md` published.
9. ADOPT-001 §12 published with all adopter content per 020H part 3.
10. `v1.0.0` released cleanly with release notes, `release-signoff.md`, and SCP tag-protection active.
11. Adversarial review rounds 1, 2, 3 (or more) on-file; fixpoint log documents all deltas; round-N declares fixpoint.
12. `docs/BACKLOG.md` Phase 9 row SCP-073 marks 020 as `done (in-repo)`; follow-up tickets open.
13. `STATUS.md` refreshed.
14. **All plan-merge unknowns closed** per §14.
15. **Slice-by-slice review checkpoints** — each slice posts a review comment on the PR summarising its deliverables, and reviewer signs off before the next slice opens (closure of A-N6; keeps review cost per-slice not per-17-slice big bang).

## 10. Decisions introduced by this WP

- **D-022** (2026-04-21): Adopt reusable-workflow + OPA/Conftest + Renovate shared preset + required-status-check + `enforce_admins=true` as the estate's policy enforcement surface. *Rationale:* industry-standard shape, no custom control-plane service, cheapest path to pre-merge gate, supports waiver-aware evaluation + structured annotations. **Alternatives rejected:** (a) `palantir/policy-bot` — GitHub App per org, HCL-not-Rego (no OPA reuse), no Renovate cascade, no native waiver-overlay. (b) Custom control-plane service — build cost; duplicates GH Actions + branch protection.
- **D-023** (2026-04-21): Reject multi-agent free-form chat-forum pattern; adopt structured proposal queue (`docs/reviews/proposals/PROP-NNN.md` + MCP `propose()` tool — initial stub in WP-SCP-021 slice 021E; full adjudication workflow in `WP-SCP-022-proposal-queue`, separately tracked). *Rationale:* Du et al. (ICML 2024) wrong-direction convergence; Anthropic ~15× token cost; human-on-the-loop moderator-as-bottleneck. Full rationale body in this section + `docs/plans/WP-SCP-021-scp-as-mcp-server.md` §10.

## 11. Review evidence

- `docs/reviews/WP-SCP-020/adversarial-review-round-1.md` — 4 parallel reviewers v0.1 → v0.2.
- `docs/reviews/WP-SCP-020/adversarial-review-round-2.md` — 2 fixpoint-confirm reviewers v0.2 → v0.3.
- `docs/reviews/WP-SCP-020/adversarial-review-round-3.md` — 2 fixpoint-confirm reviewers v0.3 → fixpoint-or-continue (pending).
- `docs/reviews/WP-SCP-020/plan-fixpoint-log.md` — delta log v0.1 → v0.2 → v0.3.
- `docs/reviews/WP-SCP-020/research-citations.md` — primary sources backing D-022 and D-023.
- `docs/reviews/WP-SCP-020/canary-evidence.md` — populated in slices 020E.a/b/c.
- `docs/reviews/WP-SCP-020/branch-protection-log.md` — populated in 020G.
- `docs/reviews/WP-SCP-020/release-signoff.md` — populated in 020H part 2.

## 12. Next WP candidates (not opened here)

Same as v0.2. See §4.1 table.

## 13. Unknowns resolved in v0.3

- **U-sec-4** → **CLOSED**. Conftest `-o github` emits GitHub Actions workflow-command annotations (`::error file=…::`). These require no extra permissions beyond the runner itself. `contents: read` is sufficient. No `checks: write` or `pull-requests: write` needed.
- **U-arch-2** → **CLOSED**. Reusable workflow inherits caller's `GITHUB_TOKEN` and can only operate within the caller's declared `permissions:` block as ceiling. If the reusable workflow declares no `secrets:` block, it has no named secrets and `secrets: inherit` on the caller is meaningless (closure-safe).
- **U-devex-1** → **CLOSED**. Changed-files mode for v1.0.0.
- **U-arch-1** → **CLOSED**. Rule-ID scheme = `SCP-R-NNN`.
- **U-arch-3** → **CLOSED**. `scripts/enable-required-check.sh` `--branch` required arg.
- **U-arch-4** → **CLOSED**. rc.1 → v1.0.0 promotion governance = `release-signoff.md` named signer + canary-run-id reference.
- **U-arch-5** → **CLOSED**. "No applicable rules" returns green + artefact with empty findings.

## 14. Unknowns resolved 2026-04-21 (plan-PR-unblocked)

| ID | Question | Resolution |
|----|----------|------------|
| **U-sec-2** | `jrnb2024` GitHub plan tier supports `enforce_admins` + tag-protection + required-signed-commits + required status checks? | **RESOLVED — path (a).** Personal GitHub Pro account ($4/mo). All four features supported on private repos. Slice 020J cuts tag-protection on `v*` + required-signed-commits on `main` directly; no signed-release-manifest substitute needed. |
| **U-k** | `jrnb2024` organization or personal user account? | **RESOLVED — personal user account.** 020K takes the personal-account / single-operator path: no `scp-break-glass` team (not available on user namespaces), `CODEOWNERS` names @jrnb2024 only, `require_review_from_non_author=false` at 020D2, §8 bus-factor-1 risk live with 2026-07-21 escalation review. |

## 15. Unknowns closing before specific slice (not plan-PR-blocking)

| ID | Closes before | Question |
|----|---------------|----------|
| U-sec-1 | 020B | OPA / Conftest current Sigstore attestation availability via `gh attestation verify`. |
| U-sec-3 | 020F | Renovate hosted-app `extends` ref vs HEAD resolution semantics (empirical test). |
| U-devex-2 | 020C | Rego bundle (single) vs per-rule loading. |
| U-gov-1 | 020F | Renovate org-level config allows preset extends. |
