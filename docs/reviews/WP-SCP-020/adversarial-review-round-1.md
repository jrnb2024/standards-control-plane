# WP-SCP-020 — Adversarial review round 1

**Date:** 2026-04-21
**Plan version reviewed:** v0.1
**Reviewers (parallel):** architect, security, governance-realist, devex/implementation-realist
**Outcome:** return to v0.2; 11 BLOCKING findings across reviewers (several overlap); ~30 MAJOR; ~15 MINOR; numerous unknowns carried forward.

Round-1 findings are reproduced verbatim below per reviewer. Consolidation,
de-duplication, and mapping to v0.2 slices is in `plan-fixpoint-log.md`.

---

## 1. Architect review

### Findings

- **[BLOCKING | in-scope]** Rego/Python source-of-truth conflict is unspecified. §5 permanently excludes Python evaluator replacement and declares "Rego handles fast shape checks, Python the deep-audit path," but the starter rule set in 020C (`services.yml` root-shape conformance to SVC-003, `waivers.json` schema) already overlaps directly with `evaluators/service_lifecycle.py`'s SVC-001/002/003 and 019B' `waiver_ref`/`additionalProperties` coverage. The plan names no precedence rule, no shared fixture corpus, and no regression gate that fails if Rego and Python disagree on the same input. When SVC-003 evolves (near-certain: D-021 on 2026-05-31 mutates `deprecation_close_date`, SCP-071 registers a waiver, Phase-2 `X-CT-Timestamp` lands by 2026-07-02), the two layers will drift silently. Fix: add a slice (020C.1) that binds every overlapping rule to a shared fixture set and a CI assertion `conftest verdict == evaluator verdict` on the same input; declare Python authoritative on conflict until a decision record says otherwise.

- **[BLOCKING | in-scope]** Waiver integration is missing end-to-end. 020C validates `waivers.json` *schema*, but the plan never says how a Rego rule consults `waivers.json` to suppress a finding at PR time. ADOPT-001 §11.7 and the 2026-04-21 hygiene response commit SCP to waiver-bearing exceptions (`scp-bearer-legacy-migration`, `expires_at: 2026-09-30`). If the federation primitive fires deny on a services.yml entry that carries a valid waiver, the gate will block SCP's own 2026-05-31 atomic workday PR. Fix: 020C must include a `data.waivers` input loaded from the caller repo, rule-level `waiver_ref` lookup with `expires_at` expiry check, and a fixture proving a live waiver suppresses the deny.

- **[BLOCKING | in-scope]** Bootstrap / circular-dependency mitigation is hand-waved. §8 says "slice 020D orders the merge before the branch-protection update" — but 020D's deliverable *is* the wrapper plus the required-status-check enable. Ordering inside a single slice isn't a mitigation, it's a restatement. The `v1.0.0` tag (020H) is also cut from the merge commit of a PR that was validated by... itself. Fix: split 020D into 020D1 (wrapper merged, no required check) → 020E (canary on unprotected branch) → 020H pre-release tag `v1.0.0-rc.1` → 020D2 (required check enabled against rc tag) → 020H promotes rc to `v1.0.0` post-canary green.

- **[MAJOR | in-scope]** Slice ordering is wrong. 020D (self-dogfood) is scheduled before 020E (canary) and before 020H (`v1.0.0`). Dogfooding a moving `@main` target on SCP itself means every subsequent slice PR runs against a different engine; canary evidence captured at 020E is invalidated the moment 020F/G/H mutate the workflow. Canary must immediately follow the frozen rc tag; dogfood must pin to that tag. Also: 020F Renovate preset has no consumer until 020I, making it effectively unexercised in-WP — move to a validation slice that at least has SCP dogfood consuming its own preset.

- **[MAJOR | in-scope]** Versioning strategy is absent. "First SCP release tag `v1.0.0`" and "staged release tags (`v1.0-rc.1`, `v1.0`, `v1.1`)" appear in §8 risks but nowhere in scope. No semver contract for the reusable workflow's `workflow_call` inputs, no breaking-change policy, no deprecation window for rule removals, no caller compatibility matrix. Renovate will happily bump every downstream to a breaking `v2.0.0`. Fix: add 020H.1 — `VERSIONING.md` in repo subpath `policies/` committing to semver on (a) inputs, (b) artefact JSON schema, (c) rule IDs; breaking changes require an amending decision row.

- **[MAJOR | in-scope]** Artefact schema for the JSON summary is undefined. 020B emits a JSON summary artefact; 020H references "known failure modes" but there is no documented schema, no version field, no stability commitment. Downstream consumers (scorecards in move #5, MCP server in move #3, Control Tower ingestion per ADOPT-001 §10.3) will grow against an ad-hoc shape. Fix: ship `schemas/policy-check-summary.schema.json` in 020B with a `schema_version` field and a CI contract test.

- **[MAJOR | in-scope]** No observability surface. The plan names no log retention, no run-count metric, no "did the check even fire" visibility, no failure-rate dashboard, no way to tell whether the gate is silently failing-open on a caller due to a misconfigured required check. 020G's "audit-logged" is a human note, not telemetry. Fix: 020B must write a structured run record to the JSON artefact *and* set a commit status with a stable context string so downstream aggregation (move #5) has something to read; add an SCP-side record of every tag cut + consumer list.

- **[MAJOR | in-scope]** Downstream-coupling / SCP-outage blast radius is unmitigated. Plan acknowledges coupling in risks but offers no circuit-breaker. If `open-policy-agent/setup-opa`'s pinned SHA 404s, or GHCR throttles the Conftest pull, every downstream caller's PR fails merge. Fix: 020B must cache OPA/Conftest binaries in the reusable workflow with a vendored fallback path, and the Rego bundle fetch must have a documented "workflow fails-closed with a named error code X" contract so operators can distinguish infra failure from policy deny. Add a kill-switch input (`scp_bypass: true` with audit-logged emission) for the pathological "SCP is broken, estate needs to ship" case.

- **[MAJOR | in-scope]** Rule deprecation / opt-out path not specified. There's no mechanism for a downstream repo to declare "rule R doesn't apply to us" short of a full waiver. `waivers.json` is finding-scoped, not rule-scoped. Fix: 020C must define a `.scp/rule-config.yaml` (or equivalent) in the caller, loaded as Rego input, with rule-level disable + justification + expiry; deprecated rules emit a one-release warning before removal.

- **[MAJOR | in-scope]** No test strategy for the reusable workflow itself. `opa test` covers Rego units; nothing covers the workflow end-to-end (input validation, SHA-pinned action resolution, annotation emission, artefact upload, exit-code contract, caller-input injection attempts). Fix: add 020B.1 — a harness repo or `act`-driven integration test that exercises the workflow against green/red fixtures before any tag is cut.

- **[MAJOR | in-scope]** SVC-003 evolution coupling not captured. D-021 (2026-05-31), Phase-2 `X-CT-Timestamp` notice (2026-07-02), and the CT_AGENT_KEY_OPS publish flip all mutate the SVC-003 surface that 020C's shape rules encode. Fix: either sequence 020C post-D-021 or commit the rule set explicitly to the pre-D-021 shape with an amending-release plan.

- **[MAJOR | follow-up = WP-SCP-022]** D-023 adopts proposal-queue over chat-forum with no observable tie-in to this WP. Keep the decision record but move the rationale body to the WP-SCP-022 plan so WP-SCP-020's scope stays on the primitive.

- **[MINOR | in-scope]** 020G's `enable-required-check.sh` is "human-invoked, audit-logged" with no definition of what "audit-logged" means. Fix: write the log target into the slice deliverable.

- **[MINOR | in-scope]** §6 says "Renovate preset consumption needs org-config verification" but no slice owns that verification. Add to 020F acceptance.

- **[MINOR | follow-up = WP-SCP-021]** ACC (`~/Projects/acc`) is not mentioned. Pre-merge gate is correctly orthogonal to orchestration, so this is not in-scope here — but WP-SCP-021 (MCP server) will need an ACC integration story. Flag on WP-SCP-021 plan opening.

- **[MINOR | in-scope]** Scope row 020A references "BACKLOG row SCP-073" but acceptance §9 says "Phase 9" — `docs/BACKLOG.md` currently shows the repo at SCP-071 / Phase 8. Confirm Phase 9 exists or fix numbering before merge.

### Unknowns

- Rule-ID naming scheme (`SVC-003-root-shape`? `SCP-R-001`?). Cross-references depend on this being stable from day one.
- Does the reusable workflow run in the caller's repo context or SCP's? Security posture differs materially.
- Caller's default branch not `main`? 020G's `--branch` arg exists but 020D hard-codes `main`.
- Local-parity pre-push path? ADOPT-001's `scripts/scp-audit-pr` pattern is evaluator-based.
- `v1.0.0-rc.N` → `v1.0.0` promotion governance: decision-record? release-notes? sign-off?
- "No applicable rules" semantics: green, neutral, or skipped?
- 020I prerequisite slip beyond `v1.0.0` support window — LTS `v1.0.0` or FLA onboards at `v1.2`?
- Renovate preset opinionated defaults acceptability across heterogeneous repos.

---

## 2. Security review

### BLOCKING

- **B1 [in-scope slice 020B]** `-o github` annotations require `pull-requests: write`, not read-only. §8 risk bullet 1 is factually wrong; conftest's `-o github` emits workflow-command annotations (no perm needed) but if Checks API annotations are intended, `checks: write` and/or `pull-requests: write` is needed. Spec must state exactly which annotation surface and the minimum permission block per surface.

- **B2 [in-scope slice 020B]** `pull_request` vs `pull_request_target` is unspecified. `pull_request_target` runs with base-repo secrets against head-repo code — classic RCE via malicious workflow edit in fork PR. Plan must mandate `pull_request` only, refuse to run on fork PRs.

- **B3 [in-scope slice 020B/020C]** No input validation commitment. §8 claims typed/validated inputs but 020B/020C list no inputs. Plan must enumerate expected inputs, declare `type:`, commit to no `${{ inputs.* }}` inside `run:` blocks, pass via `env:` with quoted expansion only.

- **B4 [in-scope slice 020H / new appendix]** Tag mutation on SCP not addressed. `v1.0.0` is mutable by default. Attacker with write on SCP can force-push `v1.0.0` to malicious commit and every Renovate-pinned downstream inherits on next run. Plan must add: (a) SCP tag-protection rule for `v*` (new slice 020J); (b) adopter guidance to pin by commit SHA, not tag; (c) Renovate preset bumps SHA+comment-tag.

### MAJOR

- **M1 [in-scope slice 020F / §8]** Renovate preset compromise has no distinct review discipline. `extends: "github>…//renovate/default"` resolves HEAD unless downstream pins. Plan must require: (a) downstream `extends` pin by ref; (b) CODEOWNERS on `renovate/` requiring two-person review; (c) preset versioned with own tag sequence.

- **M2 [in-scope slice 020B]** `open-policy-agent/setup-opa` is community-maintained, not verified. SHA-pin covers the action but not the OPA binary `setup-opa` downloads from releases. Plan must require version-pin OPA binary AND verify checksum; likewise Conftest. Add Sigstore attestation verify where upstream publishes.

- **M3 [in-scope slice 020B]** Caller secret exfiltration via `secrets: inherit`. Plan silent. Reusable workflow must declare no `secrets:` block; ADOPT-001 §12 must show callers not using `secrets: inherit`.

- **M4 [in-scope slice 020C / CODEOWNERS]** Rego bundle integrity asserted but not enforced. Plan must require CODEOWNERS on `policies/*.rego`, required-signed-commits on SCP `main` before `v1.0.0` cut.

- **M5 [in-scope slice 020G]** `enable-required-check.sh` token scope + audit undefined. Plan must specify: fine-grained PAT with `administration:write` on single target repo only; script refuses without `--repo`; logs invocation to `docs/reviews/WP-SCP-020/branch-protection-log.md`; bootstrap-only header.

- **M6 [in-scope slice 020D / 020E]** Bootstrap trust gap acknowledged but unmitigated. Strengthen: require 020D merge commit signed; protected-tag rule created *before* 020D merges; canary evidence (020E) must include a second deliberate break *after* protection.

- **M7 [follow-up=SCP-073.audit]** No audit trail spec for policy-check invocations. GitHub's workflow run logs are retention-limited and mutable. Minimum: JSON summary artefact mirrored to signed append-only log (commit to `docs/reviews/policy-audit/` on a schedule).

### MINOR

- **m1 [in-scope §8]** `id-token` permission not mentioned. Plan should state explicitly: "no `id-token` permission is granted in v1.0.0."
- **m2 [in-scope slice 020B]** Script-injection via PR title/branch name not addressed. Plan should prohibit `${{ github.event.* }}` inside `run:` scripts.
- **m3 [in-scope slice 020B]** Cache poisoning surface via `actions/cache`. Plan should state: "no `actions/cache` in v1.0.0" or specify key derivation.
- **m4 [in-scope slice 020F]** Renovate preset review needs Dependabot parity. Add SCP's own `.github/dependabot.yml` to monitor `.github/workflows/*.yml` and `policies/`.
- **m5 [follow-up=SCP-073.sec]** No security-contact / embargo path. Add `SECURITY.md` pointer in ADOPT-001 §12.

### Unknowns

- **U1.** OPA/Conftest current attestation publishing — whether v0.62+ ships Sigstore bundles that `gh attestation verify` will accept off-the-shelf.
- **U2.** Whether `jrnb2024` org plan tier supports GitHub tag-protection rules and required-signed-commits.
- **U3.** Renovate hosted-app behaviour when preset's `extends` URL resolves at ref vs HEAD.
- **U4.** Whether current Conftest `-o github` emits workflow-command annotations (no perm needed) or Checks API annotations (needs `checks: write`).

---

## 3. Governance-realist review

### BLOCKING

- **B-1 [in-scope]** Waiver-aware Rego evaluation is unspecified. *[Duplicates architect B2 — consolidated in v0.2 as slice 020C.1.]* First false-positive at 11pm Friday → PR blocked → waiver does nothing → someone bypasses via admin. Fix: slice must (a) read `waivers.json` inside reusable workflow, (b) pass entries as Rego `data.waivers`, (c) rules `deny` only when no matching unexpired waiver present, (d) canary covers both "hard block" and "waived → pass".

- **B-2 [in-scope]** Break-glass / admin-bypass posture missing. Required checks bypassable by admins by default. Plan must declare: who holds admin, whether `enforce_admins=true` is required, break-glass procedure for genuine prod incident, auditable bypass record. Fix: slice 020G sets `enforce_admins=true` on SCP self; documents break-glass (time-bound admin-PR with post-hoc waiver + D-NNN record); captures audit-log query adopters run weekly.

### MAJOR

- **M-1 [in-scope]** Fast-feedback path before required check absent. Until MCP WP-021, agents discover rules by push → fail → guess. Fix: slice 020H ships `scripts/scp-check-local` that runs conftest against staged files using pinned bundle; ADOPT-001 §12 documents pre-commit hook.

- **M-2 [follow-up=SCP-073-compose]** FLA `.claude/review_gate` vs primitive composition undefined. Local gate + federation check are both required; local gate must mention SCP check-name when triggered by conftest fail. Full integration is SCP-021 work.

- **M-3 [in-scope]** Rule-6 pressure and release-cadence governance unspecified. Fix: §10 commits each new Rego rule to (a) RFC-lite `docs/reviews/rule-proposals/RULE-NNN.md`, (b) 48h review window, (c) `v1.x-rc.N` published first, (d) rollback SLA = 4h.

- **M-4 [in-scope]** D-022 "cheapest path" claim undefended vs policy-bot. Fix: D-022 rationale adds one sentence explicitly rejecting policy-bot (GitHub App per org, HCL-not-Rego, no Renovate cascade).

- **M-5 [follow-up=SCP-073-scaffolder]** Bootstrap cost per repo is real; §7's deferral optimistic. Four files per repo × 8–12 repos with AI agents editing = drift. Fix as follow-up: `scripts/scaffold-downstream.sh`.

### MINOR

- **m-1 [follow-up=SCP-074]** Agents restructuring files to evade shape checks. Better primitive is deny-by-default JSON-schema conformance on known filenames. Not in 020 scope; capture as follow-up.
- **m-2 [follow-up=SCP-021-dep]** Cross-repo D-NNN invisibility. Correctly deferred to MCP WP.
- **m-3 [out-of-scope, correct]** Proposal-queue skeleton in 020. Ordering fine *if* M-3's rule-RFC process lands.

### Unknowns

- Does GitHub's required-status-check API support `enforce_admins` on private repo without Enterprise?
- Does `gh api` in 020G have sufficient scope on a PAT James already holds?
- Renovate preset consumption org-config verification before slice 020F starts.

---

## 4. DevEx / implementation-realist review

### BLOCKING

- **[in-scope] #1** Annotation payload undefined; default conftest `-o github` output opaque. First FLA failure costs ~15 min of Slack. Fix in 020B acceptance: every `deny` rule emits `{rule_id, file, path, message, remediation_url}`; workflow translates to GitHub annotation format `::error file=…,title=RULE-ID::human message — see URL`. Add Rego fixture asserting structured message shape.

- **[in-scope] #2** No local-reproduction path. Zero mention of `make policy-check` / `scp policy-check`. Feedback loop push → wait 30–60s → fix → push. Fix: add slice 020B.2 shipping `scripts/policy-check.sh` running `conftest test --policy policies/ <changed-files>` with same invocation as CI; document in ADOPT-001 §12.

### MAJOR

- **#3 [in-scope]** Reusable workflow no test harness. §9 acceptance never tests workflow YAML itself. Fix: in 020B add `tests/workflow/` with `fixture-pass/` and `fixture-fail/` each containing minimal `services.yml` + expected annotations JSON; run in SCP-local job `workflow-selftest`.

- **#4 [in-scope]** No `policies/README.md` for contributors. Rego is third language; without README drifts. Fix in 020C: sections on naming, required `deny` message shape, fixture layout, `opa fmt` + `opa test` pre-commit, worked example. Also add `opa fmt --fail` and `regal lint` to workflow.

- **#5 [in-scope]** JSON summary artefact has no schema, no declared consumer. *[Duplicates architect M3.]* Fix: `schemas/policy-check-summary.schema.json` in 020B with `schema_version: "1.0.0"`; note "consumer = WP-SCP-023 (Tech Insights)."

- **#6 [in-scope]** Caller wrapper minimalism unspecified. Adopters will copy-edit and drift. Fix in 020H: publish ≤ 12-line wrapper with zero required inputs (defaults in reusable workflow: `rule-set: starter`, `threshold: deny`, `annotate: true`).

- **#7 [follow-up=WP-SCP-023]** No observability for estate-wide red/green. 100 runs/week across estate is GH Actions UI per-repo only. Name as gap in §8 Risks.

### MINOR

- **#8 [in-scope]** `scripts/enable-required-check.sh` (020G) should declare required `gh` version, token scopes, `jq` dependency; `--plan` flag.
- **#9 [in-scope]** Canary evidence (020E) format unspecified. Fix: committed fixture branch `canary/deliberate-violation` + stored `gh pr view --json` dump + failing `workflow-run-id`; `scripts/replay-canary.sh`.
- **#10 [in-scope]** Python-evaluator / Rego split risks silent skip. ADOPT-001 §12 must say explicitly "Rego = PR gate; Python deep audit = nightly/manual."
- **#11 [in-scope]** Renovate preset drift without freshness warning. Reusable workflow emits warning annotation when tag > N minor versions behind latest.
- **#12 [in-scope]** Cold-start cost unstated. §8 asserts "< 30s" — request this is measured in canary evidence.

### Unknowns

- **U1.** Changed-files (git diff base) or whole-tree evaluation? Plan doesn't say.
- **U2.** `policies/*.rego` load as single bundle or per-rule? Affects failure scoping.
- **U3.** FLA pilot (020I) uses same `v1.0.0` tag as SCP self or `v1.0-rc` track? Same tag = lockstep, landmine at 10.
- **U4.** JSON summary artefact includes triggering PR's SHA and base ref? Required for Tech Insights correlation.

---

## Consolidation summary

**11 BLOCKING findings (after de-duplication, 9 unique):**

1. Waiver-aware Rego evaluation (architect B2 ≡ governance B-1) → new slice 020C.1
2. Rego/Python source-of-truth conflict (architect B1) → 020C.1 conflict-gate
3. Bootstrap / circular dependency (architect B3 + security M6) → split 020D into 020D1/020D2 + rc tag + signed commits
4. Permissions / `pull-requests: write` correctness (security B1) → 020B acceptance
5. `pull_request` vs `pull_request_target` (security B2) → 020B acceptance mandating `pull_request` only
6. Input validation commitment (security B3) → 020B acceptance enumerating inputs + env-only interpolation
7. SCP tag-mutation protection + adopter SHA-pin (security B4) → new slice 020J + 020H adopter guidance
8. Annotation payload structured object + remediation URL (devex #1) → 020B + 020C acceptance
9. Local reproduction script (devex #2) → new slice 020B.2
10. Break-glass posture (governance B-2) → 020G acceptance (`enforce_admins=true`, break-glass recipe)
11. *(governance B-1 duplicate of #1)*

All 9 unique BLOCKINGs fold into v0.2. No descoping, no deferring. See `plan-fixpoint-log.md`.

**~30 MAJOR findings** fold into v0.2 acceptance criteria across slices 020B, 020B.1, 020B.2, 020C, 020C.1, 020D1, 020D2, 020E, 020F, 020G, 020H, 020H.1, 020J.

**~15 MINOR findings** — most fold into v0.2; a few (SCP-073-compose, SCP-073-scaffolder, SCP-073.sec, SCP-073.audit, SCP-074) become named follow-ups listed in v0.2 §12.

**~20 unknowns** captured in v0.2 "Unknowns" appendix — some blocking resolution depends on infra verification (OPA Sigstore, `jrnb2024` org plan tier, Renovate preset HEAD vs ref resolution, Conftest annotation surface). Those must close before the slice that depends on them opens; they do not block this plan-only PR.
