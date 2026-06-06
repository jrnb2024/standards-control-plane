# Autonomous-run prompt — WP-SCP-028 Phase 2: companion MATERIALISATION workflow (the FIRING step for SCP-R-009/010/011)

**Drafted:** 2026-06-06 (after PR #205 merged Phase 1 dormant rules at `97802c4`).
**Plan anchor:** `docs/plans/WP-SCP-028-auth-canonical-conformance-v1.md` (§4 input materialisation).
**Phase-1 dispositions (read — carries the deferred conditions + FUPs):** `docs/reviews/WP-SCP-028/per-rule-r1-dispositions.md`.
**PRECEDENT (mirror this, do NOT invent a new mechanism):** the SCP-R-030 companion-activation PR **#201** — an additive Option-A `opa eval` repo-level pass in `policy-check.yml` that materialises `input.*` + adds the rule to both `WARN_BASELINE_RULES` sites. The 2026-06-01 PM STATUS chain entry + `docs/reviews/WP-SCP-030/companion-r1-dispositions.md` describe it.
**Session character:** single autonomous run via Pattern 3 (D-057). KERNEL-DANGEROUS (modifies `policy-check.yml`, the estate merge-gate) AND the ENFORCEMENT step for the auth surface. NO hold-for-operator gates within the run; operator-attended controls are pre-flight (cosign verify + dispatch seed) + post-run (v1.6.0 cut + merge).

## State (Phase 1 DONE, on main)
SCP-R-009/010/011 are authored DORMANT (warn-baseline, vacuous-pass) — PR #205, merge `97802c4`, `version-manifest` 1.5.0. They read `input.canonical_sdk_versions` / `input.auth_contract` (+ `*_verified` flags) / `input.adopter_*` but those are never materialised, so they emit nothing. `scp_common.rego` was NOT touched (helpers are rule-local per the per-rule-coverage discipline). This session authors the companion that materialises the inputs and flips the rules to firing. **The rules themselves should NOT need editing** — read them and confirm the input contract; if a rule needs a change, that is a signal to re-examine, not a default.

## §0.0 ⚠️ BLOCKER RESOLVED — fetch the canonical from the PUBLIC surface, not private CT (D-061)
The first Phase-2 attempt HALTED correctly: `control-tower` is **private**, so the CI materialisation cannot fetch CT's canonical from `raw.githubusercontent.com/.../control-tower/...` (404 unauth) at unattended adopter-CI time. Resolution per **D-061** (`docs/decisions/D-061-conformance-canonicals-public-signed-surface-2026-06-06.md`) + CT's **WP-CT-PUBLISH-CANONICAL-PUBLIC-SURFACE**: CT publishes the signed canonical to a **public surface** (recommended `jrnb2024/estate-canonicals`); the materialisation fetches THAT (unauthenticated — works in any adopter's CI) and **cosign-verifies BOTH canonicals** (Decision A: `canonical-sdk-versions.yaml` is cosign-signed too, NOT Ed25519 — one trust mechanism).

**✅ SURFACE IS LIVE + VERIFIED (2026-06-07).** The CT publish WP merged (#501 + #502); `contract-manifest-publish.yml` ran on main and published 4 signed artefacts. Confirmed: `auth-contract-v1.yaml` AND `canonical-sdk-versions.yaml` both fetch **200** from `https://raw.githubusercontent.com/jrnb2024/estate-canonicals/main/<f>` and **cosign-verify** (`verify-public-canonical-surface.sh` → PASS; identity `…/contract-manifest-publish.yml@refs/heads/main`, issuer `token.actions.githubusercontent.com`). **So SCP-R-009 HAS a cosign anchor.** Do NOT conclude "no sig" from CT's private in-place `policies/canonical-sdk-versions.yaml` (signed into the surface, not in place) or from the pre-Decision-A plan §4 table — both are superseded. Fire all three; cosign-verify both canonicals from the public surface.
- **GATING:** this phase cannot run until the CT publish WP has landed and the public surface serves the artefacts. Confirm before launching: `curl -fsSL https://raw.githubusercontent.com/jrnb2024/estate-canonicals/main/auth-contract-v1.yaml` returns 200. If it 404s, the CT publish WP isn't live yet → HALT, ping CT.
- The cosign **identity is unchanged** (`…/contract-manifest-publish.yml@refs/heads/main`, issuer `token.actions.githubusercontent.com`) — CT signs the artefacts regardless of where they are mirrored; the signature, not the surface, is the trust anchor.
- Throughout §0/§1/§4 below, wherever a fetch references `control-tower`, read **the public surface** instead. (Confirm the exact public URL once the CT publish WP lands.)

## The task — three things this PR must do
1. **MATERIALISE the rule inputs** in the policy-check pipeline (mirror #201's additive opa-eval repo-level pass; do NOT touch the conftest per-file pass):
   - `input.canonical_sdk_versions` ← fetch `canonical-sdk-versions.yaml` (+ its sig) from the PUBLIC canonical surface (`estate-canonicals`, per D-061/§0.0) — NOT private `control-tower` (404s in CI).
   - `input.auth_contract` ← fetch `auth-contract-v1.yaml` (+ `.sig.bundle`) from the same public surface.
   - `input.adopter_*` ← the adopter-side inputs each rule compares against (read the exact keys + shapes from `policies/SCP-R-009/010/011.rego`: `adopter_ct_auth_deps`, `adopter_source_files`, `adopter_auth_handlers`). These are workflow-EXTRACTED from the adopter's checked-out tree.
   - Set `*_verified` flags ONLY from the workflow's OWN cosign run (see below).
2. **FIRE the rules**: add `SCP-R-009`, `SCP-R-010`, `SCP-R-011` to `policy-check.yml` `WARN_BASELINE_RULES` at BOTH sites (render-deny threshold-exclusion + scorecard), per the #201/#196 pattern. Coupling guard: materialisation + WARN_BASELINE membership land in the SAME PR (else a firing rule's deny would BLOCK instead of warn).
3. **CLOSE the safety-lens FUPs** (the crux — why a naive materialisation is unsafe):
   - **FUP-WP-SCP-028-VERIFIED-FLAG-TRUST-BOUNDARY-001:** `auth_contract_verified` (and the sdk-versions equivalent) MUST be derived from the workflow's own `cosign verify-blob` exit status — NEVER read from an adopter-supplied file/input. The materialisation step BUILDS the input envelope JSON in the SCP-runtime workflow context; adopter repo content must never flow into the `*_verified` flag. **Test it:** a selftest fixture where an adopter file claims `verified: true` must NOT satisfy the rule (the flag still comes from cosign).
   - **FUP-WP-SCP-028-IMPORT-FENCE-EVASION-DOC-001:** document the SCP-R-010 import-fence static-extractor evasion surface (dynamic getattr alias / case-variant rename / indirect re-export / conditional import) where the extractor + workflow set `adopter_source_files`; record what is NOT caught so D-059 doesn't assume exhaustiveness.

## The cosign materialisation (operator-confirmed working 2026-06-06 — the workflow runs it in CI)
Fail-closed anchor = CT's `auth-contract-v1.yaml.sig.bundle`. The materialisation step runs, in CI:
```bash
cosign verify-blob \
  --bundle contracts/auth-contract-v1.yaml.sig.bundle \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  --certificate-identity 'https://github.com/jrnb2024/control-tower/.github/workflows/contract-manifest-publish.yml@refs/heads/main' \
  contracts/auth-contract-v1.yaml
```
Only on success does `auth_contract_verified` become true and the contract bytes feed `input.auth_contract`. On failure → fail-closed (rules see `verified=false` → their signature finding fires, warn-rendered; never silently trust). Do the same for `canonical-sdk-versions.yaml` — it **IS cosign-signed** on the public surface (Decision A; verified 2026-06-07, same identity/issuer). cosign-verify it identically and set `canonical_sdk_versions_verified` from THAT run. This supersedes the plan §4 table's pre-Decision-A "fetch-only, no sig" line for sdk-versions, so SCP-R-009 fires honestly (verified=true from a real cosign run, never hardcoded). cosign must be installed in the workflow (pin it like opa/conftest/regal in `scripts/.tool-versions` + the lockfile, OR via the cosign-installer action — choose the estate-consistent path; check how CT/the lockfile handles it).

## §0 Operator-attended pre-launch (the ONLY manual steps — do these BEFORE the session writes source)
1. **Verify the cosign anchor against live CT main** (the §7.5 gate). ⚠️ The contract + `.sig.bundle` live in the **control-tower** repo, NOT in SCP — fetch them first (running cosign from the SCP dir 404s). Expect `Verified OK`; on real cert-chain mismatch → HALT, ping CT (do not author the firing step against an unverifiable canonical):
   ```bash
   gh api repos/jrnb2024/control-tower/contents/contracts/auth-contract-v1.yaml \
     --header "Accept: application/vnd.github.raw" > /tmp/auth-contract-v1.yaml
   gh api repos/jrnb2024/control-tower/contents/contracts/auth-contract-v1.yaml.sig.bundle \
     --header "Accept: application/vnd.github.raw" > /tmp/auth-contract-v1.yaml.sig.bundle
   cosign verify-blob \
     --bundle /tmp/auth-contract-v1.yaml.sig.bundle \
     --certificate-oidc-issuer https://token.actions.githubusercontent.com \
     --certificate-identity 'https://github.com/jrnb2024/control-tower/.github/workflows/contract-manifest-publish.yml@refs/heads/main' \
     /tmp/auth-contract-v1.yaml
   ```
   (In CI the materialisation step does the same fetch-then-verify against CT main — there is no contract file inside the SCP repo.)
2. **Seed the Pattern-3 dispatch** from a normal terminal (the acc-hook only fires on Claude-mediated calls, so the session cannot seed it). Proposed scope (7 gated paths; `docs/**` are always-allowed — omit):
   ```bash
   cd ~/Projects/standards-control-plane
   scripts/operator/scp-pattern3-dispatch.sh \
       ".github/workflows/policy-check.yml" \
       ".github/workflows/workflow-selftest.yml" \
       "lib/policy_check_invocation.sh" \
       "tests/workflow/**" \
       "policies/VERSIONING.md" \
       "version-manifest.json" \
       "STATUS.md"
   ```
   (The session will confirm/extend this; if a write is denied mid-run, HALT and ask to re-bootstrap — never disable the hook, D-057. NOTE: `policies/SCP-R-0NN.rego` are deliberately NOT in scope — the rules are frozen from Phase 1.)
3. Launch a fresh session and paste the short kick-off prompt.

## §1 In-session pre-flight (deterministic; HALT cleanly on failure)
- Confirm active dispatch covers the 7 paths + hook live (`jq` on `.acc/active-dispatch.json`; `jq .hooks` on `.claude/settings.json`).
- Re-read the LIVE CT shapes via `gh api repos/jrnb2024/control-tower/contents/<path> --header "Accept: application/vnd.github.raw"` (avoids the denied `base64`): `contracts/auth-contract-v1.yaml` (protected_primitives still present; claim_shape_version 2.0.0; issuers: array; tier_deny/tier_warn × python/typescript/go) + `policies/canonical-sdk-versions.yaml`. Author against LIVE, not stale plan assumptions.
- Read PR #201's policy-check.yml diff for the exact opa-eval-step shape to mirror.

## §2 Build (mirror #201)
- The opa eval pass must load ONLY `scp_common.rego` + the repo-level rule files (`SCP-R-009/010/011.rego`) — **NOT the whole `policies/` dir**: loading the dir pulls `policies/tests/*_test.rego` (`package main_test`) and `opa eval` exits 2 with the diagnostic on STDOUT (stderr empty). This cost a CI round on #201; the fix is `--data scp_common.rego --data SCP-R-009.rego ...`. Surface opa's stdout on error.
- Build the input envelope in the workflow step (the trust boundary): `*_verified` from the cosign exit code; `input.adopter_*` from the checked-out adopter tree; CT manifests fetched + (for auth_contract) cosign-verified. Merge the rules' deny/warn findings into the same `policy-findings.json` the render-deny + scorecard steps consume (additive; conftest per-file pass untouched).
- Add SCP-R-009/010/011 to both `WARN_BASELINE_RULES` sites.

## §3 Selftest fixtures (mirror #201's `tests/workflow/fixture-scp-r-030-*`)
Real reusable-workflow invocations proving the FIRING + the trust boundary. At minimum:
- opted-in adopter, conformant → no finding, gate green.
- **load-bearing:** an adopter with a non-conformant input (e.g. a tier_deny shadow, or a below-floor pin) → WARN, gate GREEN (warn-baseline never blocks) — proves the coupling guard.
- **trust-boundary (the crux):** an adopter file ASSERTING `verified: true` while cosign would NOT verify → the rule still sees `verified=false` / fail-closed (the adopter cannot spoof verification). This is the FUP-001 test.
- regression: existing fixtures (fixture-pass/fail) unchanged.
Wire into `workflow-selftest.yml` (update the exact-N `uses:` count assertion; orchestrator `needs` + result-assertions + summary-vs-oracle compares). The harness's by-design-red inner jobs (fixture-fail + scp-sha failure-path) stay red; the `workflow-selftest` orchestrator is the gate.

## §4 R1 — 3-lens, safety_bypass = HARD STOP (non-negotiable; this is the enforcement step)
- correctness: envelope matches each rule's `input.*` contract; findings merge into render-deny/scorecard correctly; conftest per-file pass untouched; opa eval loads only the needed rego files.
- safety_bypass: can an adopter spoof `*_verified` (the trust boundary)? evade the import-fence? alter the gate verdict for other rules? Is the coupling guard airtight (no path where a firing auth rule deny-BLOCKS)? **A REJECT here is a HARD STOP.**
- completeness_governance: fixture coverage incl. the trust-boundary + load-bearing-warn cases; FUP-001 + evasion-doc closed; no scope creep; bookkeeping complete.
Dispositions → `docs/reviews/WP-SCP-028/companion-r1-dispositions.md`. Drive to R-FIXPOINT (cure-worse R2 in effect).

## §5 Bookkeeping
- `policies/VERSIONING.md`: flip the auth-rules register from "Target members pending their companion workflow PR" → live members (move 009/010/011 into the live `WARN_BASELINE_RULES` line).
- `version-manifest.json`: 1.5.0 → **1.6.0** (read-then-increment; do not hardcode).
- `STATUS.md` chain row (triggers `check-invocation-log-entry`): companion SHIPPED, SCP-R-009/010/011 FIRING (warn-baseline), v1.6.0 ready-to-cut, FUP-001 closed + tested, 4-week observation window opens after merge → D-059.
- `docs/BACKLOG.md` + `docs/DECISIONS.md` (always-allowed): WP-SCP-028 Phase 2 SHIPPED; D-059 still reserved.

## §6 Operator handoff (halt with this)
```
WP-SCP-028 Phase 2 (companion materialisation) complete — SCP-R-009/010/011 now FIRING (warn-baseline).
PR #<n> — CI green (do not merge; operator-attended).
1. CUT v1.6.0: scripts/operator/cut-release.sh --version v1.6.0 --sha <MERGE_SHA>
2. COHORT CASCADE: scripts/operator/scp-wrapper-bump-sweep.sh --emit-commands
3. OBSERVE 4 weeks → RATIFY D-059 (deny-promote / hold-at-warn / re-scope).
4. TEARDOWN: scripts/operator/scp-pattern3-dispatch.sh --teardown
3-lens R1: ACCEPT (R-FIXPOINT; no safety REJECT). Halts: <list / none>.
```

## §7 Halting conditions
1. cosign verify-blob fails against live CT main (§0.1) — HALT, ping CT (do not author against an unverifiable canonical).
2. **safety_bypass REJECT** on the merge-gate / trust-boundary — HARD STOP.
3. Cure-worse R2 trigger.
4. Coupling cannot be satisfied (materialisation without WARN_BASELINE membership) — HALT.
5. opa-eval materialisation infeasible additively without touching the conftest per-file pass — HALT, surface (do NOT fall back to `--combine`).
6. Hook denial on an out-of-scope path — HALT, ask operator to re-bootstrap (never disable the hook).
7. Selftest fixtures fail + fix-round-1 doesn't close it.

## §8 In-session tooling reality (acc-hook allowlist — learned in Phase 1)
NO `cosign`/`opa`/`regal`/`conftest`/`python3` (any form)/`base64`/`yq`/`cd`/`echo`/redirections/`$(...)`/`/tmp` in-session — validation is CI-only. Hand-author carefully; lean on CI + the 3-lens R1. Read live CT shapes via `gh api ... --header "Accept: application/vnd.github.raw"`. PR body for the r1-evidence gate needs a level-2 `## R1 evidence` heading with bare `- correctness:` / `- safety_bypass:` / `- completeness_governance:` bullets, via `gh pr create --body-file`. Commit via `git commit -F <in-scope-file>`. Poll CI with `gh pr checks` + the Monitor tool; fetch failing job logs via `gh api repos/.../actions/jobs/<id>/logs | grep ...`.

**Done =** materialisation pass live + SCP-R-009/010/011 in `WARN_BASELINE_RULES` (firing as warn) + the `_verified` trust-boundary FUP closed AND tested + CI-green PR awaiting operator merge. After merge + v1.6.0 cut + cohort cascade, the 4-week observation window opens → D-059.
