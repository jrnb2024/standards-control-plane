# TF-PIM-001 — Implementation WP — Path C (GitHub App credential)

**Status:** DRAFT v0.1 (post-ratification; pre-R1)
**Path ratified:** C — GitHub App with `repository_permissions: { contents: read }` scoped to `jrnb2024/standards-control-plane-` only (operator-attended convergence 2026-05-21)
**Origin:** `docs/plans/TF-PIM-001-cross-repo-checkout-auth.md` §5.0 Path C; closed 2026-05-21 at `dceab0c`
**Owner:** @jrnb2024 (D-031 single-operator-mode)
**Dispatch tier:** **Tier 2** (kernel-dangerous federation primitive change; operator-attended fire mandatory)
**Auth-surface:** YES — this WP IS the auth-surface change; 3-lens R-cycle to R-fixpoint mandatory pre-merge; orchestrator-attended

---

## R-cycle changelog

| R | Date | Round | Findings | Closure |
|---|---|---|---|---|
| v0.1 | 2026-05-21 | author | — | initial draft |

R-fixpoint criterion: no new significant findings on a fresh 3-lens round, OR R4 mechanical override at R3 if diminishing-returns trajectory matches `feedback_asymptotic_trajectory_split.md`.

## §1 Plan

### 1.1 Why this WP exists

Path C was ratified 2026-05-21 as the canonical fix for **TF-PIM-001** (P0) — the cross-repo `actions/checkout` authentication failure that blocks every external WP-SCP-024 cascade adopter. PIM PR #236 surfaced the failure 2026-05-19; PIM `main`'s `policy-check / scp/policy-check` required-check has been relaxed operator-attended since then pending this WP closing.

The 3-agent review at `docs/reviews/TF-PIM-001/shortlist-A-C-D/` (sec=Strong C, arch-skeptic=Strong C, pragmatist=Strong A; operator-attended convergence resolved 2C+1A in favour of C on irreversibility-asymmetry grounds) committed the estate to: GitHub App authoring + SCP-controlled workflow code obtaining the App installation token + cross-repo `actions/checkout` using that token + ADOPT-001 §12.7 updated + D-NNN ADR ratifying the App-credential surface.

### 1.2 What this WP delivers

- A GitHub App (`scp-federation-primitive`) registered in @jrnb2024 with `repository_permissions: { contents: read }` scoped to `jrnb2024/standards-control-plane-` only.
- App private key stored as SCP-repo secret (`SCP_FEDERATION_APP_PRIVATE_KEY`) under D-031 single-operator custody.
- Reusable workflow `.github/workflows/policy-check.yml` amended: token-exchange step added; cross-repo `actions/checkout` steps (lines 107, 1149-1154) use the App installation token via `token:` parameter.
- ADOPT-001 §12.7 updated: new sub-section documenting App-install ceremony; §12.7.5 amended for de-adoption-side App-installation revocation; §12.7.10 reaffirmed (no inversion under Path C); §12.7.13 supply-chain section adds `generate-app-token` action SHA-pin tracking.
- New D-NNN ADR (provisional **D-050**) ratifying Path C App-credential surface + §12.7.10 invariant preservation + key custody under D-031 + reversal mechanism.
- Workflow-selftest harness coverage for the token-exchange failure mode (TF-PIM-001-ARCH-002).
- External-adopter cross-repo verification (PIM canary green) + PIM `main` required-check restoration (TF-PIM-001-PLAN-004).

### 1.3 What this WP does NOT deliver

- v1.3.0 release cut — independent track per D-049 §Sequencing item 1 (self-dogfood-only at v1.3.0; TF-PIM-001 is the artefact-gate on adopter-side consumption, not on the v1.3.0 ship).
- Renovate cascade changes — Path C is Renovate-neutral on the preset; existing `renovate/v*` tag tracking continues unchanged.
- Cohort-wide adopter wrapper updates — Path C does not require any adopter wrapper change (TF-PIM-001-PLAN-005 closes as N/A-UNDER-RATIFIED-PATH).
- Multi-org adopter App-install coordination tooling — out-of-scope at the 5-cohort all-`@jrnb2024` namespace; captured as TF-PIM-001-ARCH-004 for future surface.
- Second-maintainer onboarding for App-key co-custody — operator-paced; sequenced after the 2026-07-21 quarterly D-031 bus-factor-1 review.

## §2 Acceptance criteria

Five criteria, all required for WP closure:

1. **External-adopter cross-repo green.** At least one external adopter (PIM is the canary candidate) runs the federation-primitive wrapper cross-repo end-to-end with all 12 policy-check steps green. Evidence: successful GitHub Actions run URL on a PIM PR exercising the wrapper at the new policy-check.yml SHA. The "Populate .scp-runtime (self-call fallback)" + "Check out SCP repo at workflow ref for schema lookup" steps both succeed.

2. **PIM `main` required-check restored.** The 2026-05-19 operator-attended relaxation reverses; `policy-check / scp/policy-check` re-enters PIM `main`'s required contexts. Evidence: `gh api repos/jrnb2024/mapp-pim/branches/main/protection --jq '.required_status_checks.contexts'` returns a set containing `"policy-check / scp/policy-check"`. Invocation log entry written to `docs/reviews/WP-SCP-020/branch-protection-log.md`.

3. **ADOPT-001 §12.7 fully updated.** New sub-section (provisionally §12.7.16) documents the App-install ceremony; §12.7.5 amended for de-adoption-side App-installation revocation; §12.7.10 explicitly reaffirmed (no `secrets: inherit` anywhere — Path C is App-credential not PAT); §12.7.13 adds the `generate-app-token` action's SHA pin to supply-chain tracking.

4. **D-050 ADR ratified.** ADR landed in `docs/decisions/D-050-tf-pim-001-app-credential-surface-2026-MM-DD.md` + DECISIONS.md row appended. Captures: App-credential scope (`contents: read` on SCP repo only); §12.7.10 invariant preservation rationale; key-custody posture under D-031 + bus-factor-1 mitigation; reversal mechanism (delete App or revoke installations).

5. **R1-evidence-on-fix-PR satisfies cardinal-rule-2 3-lens.** Per `feedback_r1_surface_must_cite_ci.md`, the fix PR's `## R1 evidence` block carries all three lenses populated + CI citation pair (workflow run URL + `mergeStateStatus` post-merge) on merge.

## §3 Scope

### 3.1 In-scope (this WP delivers)

- GitHub App authoring (Wave A) — `scp-federation-primitive` App; `repository_permissions: { contents: read }`; private key generation + SCP-repo secret storage
- D-NNN ADR drafting + ratification (Wave B) — D-050 covering App-credential surface
- ADOPT-001 §12.7 updates (Wave C) — new §12.7.16 App-install ceremony; §12.7.5 de-adoption update; §12.7.10 reaffirmation; §12.7.13 supply-chain addition
- Reusable workflow change (Wave D) — `.github/workflows/policy-check.yml` token-exchange step + `token:` parameter on cross-repo `actions/checkout`
- Workflow-selftest harness coverage (Wave E) — token-exchange failure mode test fixture per TF-PIM-001-ARCH-002
- SCP-self dogfood verification (Wave F) — verify SCP-self CI runs green on a test PR with the new workflow
- External-adopter cross-repo verification (Wave G) — PIM canary; operator-attended App install on PIM; verify all 12 policy-check steps green
- PIM `main` required-check restoration (Wave H) — operator-attended `enable-required-check.sh --preserve-existing-contexts` invocation + invocation log entry + TF-PIM-001 closure

### 3.2 Out-of-scope (deferred or routed elsewhere)

- v1.3.0 release cut + SCP-R-005 ship — independent track per D-049 §Sequencing
- 4 cohort adopters beyond PIM (CT, MDA, Recommender, shopify-app) — App-install ceremony per adopter is a one-time onboarding step folded into future cascade slices (024D-024G); not part of this WP
- Multi-org adopter coordination surface — TF-PIM-001-ARCH-004; deferred to first non-`@jrnb2024`-namespace adopter
- Second-maintainer co-custody onboarding — deferred to 2026-07-21 quarterly D-031 review per TF-PIM-001-SEC-005
- 90-day App-key rotation execution — first rotation due 2026-08-21 (or earlier if account access changes); rotation SOP authored here, execution is operator-paced
- FUP-WP-SCP-024-SCAFFOLDER-V1.2-INCOMPAT-001 fix — unblocks once this WP closes (scaffolder can be verified against a real adopter run); separate impl slice opens after this WP

### 3.3 Inherited tracked-forward items

From `docs/reviews/TF-PIM-001/shortlist-A-C-D/sec-lens-r1.md` + `arch-skeptic-lens-r1.md`:

| ID | Title | Wave |
|----|-------|------|
| TF-PIM-001-SEC-001 | App-credential rotation SOP | Wave A + Wave C (docs) |
| TF-PIM-001-SEC-002 | ADOPT-001 §12.7.5 de-adoption update | Wave C |
| TF-PIM-001-SEC-003 | `generate-app-token` action SHA-pin + supply-chain registration | Wave D + Wave C (§12.7.13) |
| TF-PIM-001-SEC-004 | Per-adopter App-install access verification | Wave G (PIM scope; future cascade slices for others) |
| TF-PIM-001-SEC-005 | 2026-07-21 quarterly review extension | TF carried to operator agenda (out-of-scope this WP) |
| TF-PIM-001-ARCH-001 | App private-key rotation schedule (90-day) | Wave A (SOP) + 2026-08-21 first execution (out-of-scope) |
| TF-PIM-001-ARCH-002 | Selftest harness coverage for App token-exchange failure | Wave E |
| TF-PIM-001-ARCH-003 | ADOPT-001 §12.7 App-install ceremony documentation | Wave C |
| TF-PIM-001-ARCH-004 | Multi-org adopter App-install coordination | TF carried (out-of-scope this WP; first non-@jrnb2024 adopter) |
| TF-PIM-001-ARCH-005 | D-NNN ADR for Path C App-credential surface | Wave B |

10 TF items; 8 in-scope across Waves A-G; 2 TF-carried (TF-PIM-001-SEC-005 + ARCH-004) as documented future surfaces.

## §4 Waves

Waves sequenced for delivery order. Each wave's outcome gates the next; waves D + E may parallelise once App credential is in SCP secrets (Wave A complete).

### Wave A — GitHub App authoring (operator-attended; no code change)

**Outcome.** `scp-federation-primitive` GitHub App exists in @jrnb2024 with scope `repository_permissions: { contents: read }` on `jrnb2024/standards-control-plane-` only. Private key stored as SCP-repo secret `SCP_FEDERATION_APP_PRIVATE_KEY`. App ID stored as `SCP_FEDERATION_APP_ID` (not strictly secret but stored alongside).

**Actions.**
1. Operator: GitHub UI → @jrnb2024 settings → Developer settings → GitHub Apps → New GitHub App
2. Configure: name `scp-federation-primitive`; homepage URL = SCP repo URL; webhook disabled; permissions = `Repository permissions: Contents: Read-only`; installation scope = "Only on this account"
3. Generate private key; download `.pem` file
4. SCP repo → Settings → Secrets → Actions → New repository secret `SCP_FEDERATION_APP_PRIVATE_KEY` with the .pem contents
5. Add second secret `SCP_FEDERATION_APP_ID` with the App's numeric ID (for ergonomic env var)
6. Verify App appears at https://github.com/settings/apps/scp-federation-primitive

**Verification.** Operator confirms App + secrets stored. `.pem` file deleted from local filesystem after upload (key only exists in SCP repo secret).

**Risk surface.** Wave A is the highest single-event risk in the WP — leaking the `.pem` during transit or post-upload-not-deleted gives an attacker the App credential. Mitigation: operator-attended; private key never committed; clipboard/file cleared post-upload.

**Wave A Tier:** operator-attended (no Codex dispatch; GitHub-UI ceremony)

### Wave B — D-050 ADR drafting + ratification

**Outcome.** `docs/decisions/D-050-tf-pim-001-app-credential-surface-YYYY-MM-DD.md` authored + DECISIONS.md row appended; status DRAFT in file until merge ceremony.

**Actions.**
1. Author D-050 ADR per the existing D-NNN structure (Context / Decision / Rationale / Justification / Cross-references / Tracked-forward items / Sequencing if applicable)
2. ADR captures: App-credential scope decision; §12.7.10 invariant preservation rationale; key-custody posture under D-031; reversal mechanism; relation to TF-PIM-001 plan-doc + ratification evidence files
3. DECISIONS.md row appended (single-table record)
4. Operator review at PR opening; merge ratifies (DRAFT → ACCEPTED at next status-bookkeeping commit per ADR ceremony)

**Verification.** D-050 ADR file present + DECISIONS.md row present; cross-refs to TF-PIM-001 plan-doc + evidence files + sec/arch-skeptic lens TF items.

**Wave B Tier:** operator-paced authoring; operator-attended merge

### Wave C — ADOPT-001 §12.7 updates

**Outcome.** ADOPT-001 §12.7 updated as follows:

- **New §12.7.16 App-install ceremony.** Documents: (a) GitHub App name + install URL; (b) required installation scope (`contents: read` on `standards-control-plane-` only); (c) org-admin access requirement per adopter (D-031 single-operator-mode means @jrnb2024 self-installs on all 5 cohort adopters under @jrnb2024 namespace); (d) what happens if installation is revoked (SCP-E001 emission, not silent); (e) how to verify installation is active before invoking `enable-required-check.sh`.
- **§12.7.5 amended (de-adoption).** New step: after wrapper deletion + branch-protection removal, adopter org-admin must revoke the `scp-federation-primitive` App installation from Settings → Integrations → GitHub Apps. Residual installation = persistent unnecessary access vector.
- **§12.7.10 reaffirmed.** Explicit note: Path C ratified 2026-05-21 with `secrets: inherit` STILL prohibited. App credential obtained inside SCP-controlled workflow code; never passed via caller secrets. §12.7.10 invariant fully preserved.
- **§12.7.13 amended (supply-chain).** Adds the `generate-app-token` action (e.g., `actions/create-github-app-token` or equivalent — specified in Wave D) as a SHA-pinned dependency tracked in `scripts/scp-policy-check.lock` (or equivalent supply-chain tracking shape).

**Actions.**
1. Read existing ADOPT-001 §12.7 verbatim to anchor edits
2. Author §12.7.16 covering the 5 substantive items above
3. Amend §12.7.5 with revocation step
4. Add reaffirmation footnote to §12.7.10
5. Amend §12.7.13 with action SHA-pin

**Verification.** §12.7 reads coherently end-to-end; cross-refs to D-050 + this WP plan-doc.

**Wave C Tier:** operator-paced authoring; can dispatch Codex for §12.7.16 drafting (mechanical-doc-add) at operator discretion

### Wave D — Reusable workflow change (Codex Tier 2 dispatch)

**Outcome.** `.github/workflows/policy-check.yml` amended: token-exchange step added; cross-repo `actions/checkout` steps (lines 107, 1149-1154 in current SHA) use the App installation token via `token:` parameter.

**Actions.**
1. Pin the `generate-app-token` action by 40-char commit SHA — candidate actions: `actions/create-github-app-token@<SHA>` (GitHub's first-party action; preferred for supply-chain provenance) OR `tibdex/github-app-token@<SHA>` (well-established third-party). Codex dispatch determines exact pin from upstream availability at dispatch time.
2. Add "Obtain App installation token" step BEFORE the cross-repo `actions/checkout` step at line 107:
   ```yaml
   - name: Obtain SCP federation App installation token
     id: scp-app-token
     if: github.action_ref != ''
     uses: actions/create-github-app-token@<SHA-PIN>
     with:
       app-id: ${{ secrets.SCP_FEDERATION_APP_ID }}
       private-key: ${{ secrets.SCP_FEDERATION_APP_PRIVATE_KEY }}
       owner: jrnb2024
       repositories: standards-control-plane-
   ```
3. Update the "Checkout SCP runtime repository" step (line 107) to use `token: ${{ steps.scp-app-token.outputs.token }}` — preserve `persist-credentials: false`
4. Update the "Check out SCP repo at workflow ref for schema lookup" step (line 1149) identically
5. Preserve all other workflow logic + invariants
6. SCP-self dogfood case (same-repo invocation; `github.action_ref` empty): token-exchange step skips per the `if:` guard; default `GITHUB_TOKEN` continues to suffice for the self-call fallback

**Verification.** Workflow YAML parses cleanly; no other workflow logic touched.

**Wave D Tier:** **Tier 2 Codex dispatch** (kernel-dangerous federation primitive change). Operator-attended fire. Standard four-tier protocol: Codex executor; 3-lens R1+R2 review (sec / arch-skeptic / pragmatist per `feedback_orchestrator_auth_surface_plan_review_default.md`); DO-NOT-EDIT sub-agent mandate per `feedback_subagent_review_only_scope_must_be_enforced`; R-cycle to R-fixpoint MET; preflight grep MANDATORY.

### Wave E — Workflow-selftest harness coverage (TF-PIM-001-ARCH-002)

**Outcome.** `tests/workflow-selftest/` (or equivalent path) gains coverage for the App token-exchange failure mode — when the App key is misconfigured / installation missing / GitHub App API unavailable, the workflow fails with `SCP-E001` rather than continuing silently.

**Actions.**
1. Identify the existing selftest harness structure (workflow fixture-pass / fixture-fail entries)
2. Add a test fixture or stub-mode env-var flag (`SCP_TEST_SIMULATE_APP_TOKEN_FAILURE=1`?) that exercises the token-exchange step failing
3. Verify the workflow emits `SCP-E001` annotation + commit-status fail
4. Document the new fixture in `tests/workflow-selftest/README.md` (or equivalent) + cross-ref to TF-PIM-001-ARCH-002

**Verification.** Selftest CI run shows the new fixture executing + producing the expected `SCP-E001` error code.

**Wave E Tier:** Tier 2 Codex dispatch (touches CI fixture + workflow indirectly)

### Wave F — SCP-self dogfood verification

**Outcome.** SCP-self CI runs green on a test PR with the new policy-check.yml workflow.

**Actions.**
1. Open a small test PR on SCP itself (after Waves A + B + C + D + E land) — could be a docs-only PR or this WP plan-doc's closure amend
2. Verify all 4 required checks pass: `policy-check / scp/policy-check`, `policy-check-readback`, `check-invocation-log-entry`, `validate PR body`
3. Verify the SCP-self dogfood path: `github.action_ref` empty → token-exchange step skips → self-call fallback engages → all 12 policy-check steps complete
4. Capture evidence URL

**Verification.** Test PR's CI rollup all SUCCESS; SCP-self dogfood unchanged.

**Wave F Tier:** operator-attended (verify-only)

### Wave G — External-adopter cross-repo verification (PIM canary)

**Outcome.** PIM exercises the new federation primitive cross-repo with all 12 policy-check steps green.

**Actions.**
1. Operator-attended App install on PIM (`mapp-pim/mapp-pim`): visit `https://github.com/apps/scp-federation-primitive/installations/new` → select PIM repo → confirm scope = `Read access to code on jrnb2024/standards-control-plane-` only
2. Verify installation via `gh api /app/installations` (requires authenticated as the App; alternative: PIM repo Settings → Integrations → GitHub Apps shows the install)
3. Open a small test PR on PIM (e.g., a noop README touch); GitHub Actions runs the wrapper which invokes the SCP reusable workflow cross-repo
4. Verify all 12 policy-check steps complete + green; capture run URL
5. Verify the App token was successfully obtained + used for both cross-repo checkout steps; `persist-credentials: false` preserved (no App token written to artefacts)

**Verification.** PIM CI run URL with all 12 policy-check steps green; App installation verified active.

**Wave G Tier:** operator-attended

### Wave H — PIM `main` required-check restoration + TF-PIM-001 closure

**Outcome.** PIM `main`'s `policy-check / scp/policy-check` re-enters required contexts; TF-PIM-001 closes; STATUS.md + BACKLOG.md updated.

**Actions.**
1. Operator runs `scripts/enable-required-check.sh --repo mapp-pim/mapp-pim --branch main --preserve-existing-contexts` (dry-run first via `--plan`)
2. Verify post-PUT: `gh api repos/mapp-pim/mapp-pim/branches/main/protection --jq '.required_status_checks.contexts'` returns set containing `"policy-check / scp/policy-check"`
3. Invocation log entry written to `docs/reviews/WP-SCP-020/branch-protection-log.md`
4. STATUS.md `Last updated:` header refresh + new "Today's chain" entry capturing TF-PIM-001 closure
5. BACKLOG.md Phase 12 → strikethrough TF-PIM-001 row with closure date + cross-ref to this WP's final commit
6. FUP-WP-SCP-024-SCAFFOLDER-V1.2-INCOMPAT-001 unblock signal — open separate impl slice once scaffolder can be verified against a real adopter run (out-of-scope this WP, captured as follow-up)

**Verification.** PIM `main` protection state restored; STATUS.md + BACKLOG.md reflect closure; invocation log entry committed.

**Wave H Tier:** operator-attended

## §5 Review shape

### 5.1 R-cycle protocol for this plan-doc

3-lens R1 from R1 (auth-adjacent — TF-PIM-001 IS the auth-surface):

- **Lens 1 — correctness.** Does the plan-doc accurately reflect Path C ratified scope? Are all 10 TF-PIM-001-{SEC,ARCH}-* items mapped to a wave or explicitly TF-carried? Are §3.2 out-of-scope items consistent with the ratification rationale (irreversibility-asymmetry preserved; multi-org coordination deferred)?
- **Lens 2 — safety_bypass.** Does any wave introduce a new bypass surface? Does Wave D's workflow change preserve §12.7.10 invariant + invariants 1-5 from the plan-doc's §4 threat-model recap? Are the App secret storage requirements (`SCP_FEDERATION_APP_PRIVATE_KEY` as repo-scoped, not org-scoped) explicit? Does Wave A's operator-attended ceremony adequately mitigate `.pem` exposure risk during transit?
- **Lens 3 — completeness_governance.** Are all 5 §2 acceptance criteria captured + verifiable? Is the D-050 ADR scope sufficient? Does §3 inherited-TF table close the loop with the evidence files? Is Tier 2 dispatch operator-attended fire explicit at Wave D?

R-cycle to R-fixpoint MET (no new significant findings on a fresh round) OR R4 mechanical override at R3 if diminishing-returns trajectory.

### 5.2 R-cycle protocol for individual waves

- Wave A (operator-attended ceremony) — no R-cycle; operator-verified at execution
- Wave B (ADR drafting) — 3-lens R1; operator-attended merge
- Wave C (ADOPT-001 doc updates) — 3-lens R1; mechanical-doc-add pattern
- Wave D (workflow change — Tier 2) — 3-lens R1+R2 to R-fixpoint MET; Codex dispatch; operator-attended fire; cure-worse trigger active; Option A R4 mechanical override at R3 if diminishing-returns
- Wave E (selftest fixture) — 3-lens R1; same-PR coupling with Wave D acceptable
- Wave F (SCP-self verify) — operator-attended; no R-cycle
- Wave G (PIM canary) — operator-attended; cross-cutting check against §2 acceptance criterion 1
- Wave H (PIM restoration + closure) — operator-attended; cross-cutting check against §2 criteria 2 + 5

### 5.3 DO-NOT-EDIT sub-agent mandate

Per `feedback_subagent_review_only_scope_must_be_enforced` (sample-size-2 across CT + Recommender 48h; load-bearing pending ACC harness-level fix per ACC PR #247):

All R-cycle sub-agents dispatched for this WP MUST be read-only (Plan agent type per the established estate pattern; no Edit/Write/NotebookEdit tools). Sub-agent outputs return as text to the orchestrator; orchestrator writes evidence files. Sub-agents writing to disk = scope-breach failure = R0 trigger.

### 5.4 Preflight grep — MANDATORY pre-R1

Per `feedback_dispatch_scope_omission_pre_flight_check` + `feedback_int_pre_grep_at_plan_ready`:

Before R1 dispatch, run:

```bash
grep -oE "(INT-|FUP-|TF-|ASC-|D-)[A-Z0-9_-]+" docs/plans/TF-PIM-001-impl-path-c-app-credential.md | sort -u
# Cross-check each citation against BACKLOG.md (INT/FUP/TF) OR docs/decisions/ (D-NNN) OR memory dir (feedback_*)
```

HARD-FAIL on phantom citation. If any citation has no backing artefact, fold filing into this plan-doc as a v0.2 amend before R1 dispatch.

### 5.5 Cure-worse trigger

If R-cycle fixpoint stalls past R3 with diminishing-returns (per `feedback_asymptotic_trajectory_split.md`):

- R3 closures introduce new latent defects in the just-fixed area → diminishing-returns signal
- Trigger: Option A R4 mechanical override (sub-agent dispatches a fresh perspective; if same finding-class re-emerges, surface as scope-split candidate)
- Scope-split candidate: carve sub-surface to sibling slice (Wave D's selftest harness coverage carve to Wave E was already this pattern at plan-doc authoring time)

## §6 Verify

### 6.1 SCP-self dogfood acceptance (Wave F)

```bash
# After Wave D ships:
gh pr create --repo jrnb2024/standards-control-plane- --base main --head <test-branch> --title "test: dogfood verify post-Path-C workflow change" --body "..."
gh pr view <#> --json statusCheckRollup --jq '[.statusCheckRollup[] | .conclusion // .state]'
# Expect: all SUCCESS for 4 required checks
```

### 6.2 External-adopter cross-repo green (Wave G)

```bash
# After Wave A + D ship + App installed on PIM:
gh pr create --repo mapp-pim/mapp-pim --base main --head <pim-test-branch> --title "test: cross-repo verify post-Path-C" --body "..."
# Wait for CI; capture run URL
gh run list --repo mapp-pim/mapp-pim --branch <pim-test-branch> --limit 1 --json status,conclusion,url
# Expect: status=COMPLETED, conclusion=SUCCESS; all 12 policy-check steps green
```

### 6.3 PIM `main` required-check restored (Wave H)

```bash
gh api repos/mapp-pim/mapp-pim/branches/main/protection --jq '.required_status_checks.contexts'
# Expect: array containing "policy-check / scp/policy-check"
```

### 6.4 §12.7.10 invariant preservation (cross-cutting)

```bash
# Verify no secrets: inherit in adopter wrappers post-Path-C ship:
gh search code --owner=jrnb2024 'secrets: inherit'
# Expect: zero matches in adopter policy-check-wrapper.yml files
```

### 6.5 R1-evidence-on-fix-PR (Wave D + cross-cutting)

PR body for the Wave D Codex dispatch slice MUST carry:

```
## R1 evidence

- correctness: <link to lens evidence file + CI URL>
- safety_bypass: <link to lens evidence file + CI URL>
- completeness_governance: <link to lens evidence file + CI URL>

CI citation pair:
- policy-check / scp/policy-check: SUCCESS @ <CI URL>
- mergeStateStatus: CLEAN
```

Per `feedback_r1_surface_must_cite_ci.md`.

## §7 Risks

### 7.1 Wave-A `.pem` exposure during App private-key upload

**Risk.** Operator downloads `.pem` from GitHub Apps settings; uploads to SCP repo secret; clipboard or filesystem retains the private key briefly.

**Mitigation.**
- Wave A operator-attended; clipboard cleared after paste; `.pem` file deleted from local FS immediately after upload
- SCP repo secret is scoped to Actions context only (not org-level; not visible in repo settings UI except as `********`)
- If exposure suspected: delete App + recreate; rotation procedure documented in TF-PIM-001-SEC-001 / ARCH-001

**Severity.** HIGH if exposure occurs (full App credential leaked); LOW probability if Wave A ceremony followed.

### 7.2 Tier 2 Codex dispatch on Wave D introduces unanticipated workflow regression

**Risk.** The workflow change is auth-surface-touching + executes on every adopter PR; a regression could block every external adopter simultaneously.

**Mitigation.**
- Tier 2 dispatch per WP-SCP-022 protocol: Codex executor; 3-lens R1+R2 to R-fixpoint MET; DO-NOT-EDIT sub-agent mandate
- Wave E selftest harness coverage exercises the token-exchange failure mode before Wave D's PR merges
- Wave F SCP-self dogfood verification fires before any external adopter is exposed
- Wave G PIM canary is the first external-adopter exposure; broader cohort exposure deferred to future cascade slices
- Rollback mechanism: revert the Wave D PR; SCP-self continues working (same-repo `GITHUB_TOKEN` self-call fallback); external adopters return to pre-WP failure mode (no NEW failure introduced by rollback)

**Severity.** MEDIUM (bounded blast radius — only external adopters affected; SCP-self continues green; rollback is single-PR revert)

### 7.3 D-031 single-operator bus-factor on App-credential custody

**Risk.** @jrnb2024 holds the App private key exclusively. Account compromise OR @jrnb2024 unavailable during key rotation = blocked external adopter cascade.

**Mitigation.**
- Rotation SOP authored in Wave A + Wave C; 90-day rotation cadence per TF-PIM-001-ARCH-001
- 2026-07-21 quarterly D-031 review (TF-PIM-001-SEC-005) extends to include App-key custody audit
- Second-maintainer onboarding (operator-paced) eliminates bus-factor-1 once it lands
- App installation tokens auto-rotate every 1 hour (GitHub-managed); compromise window is bounded by token TTL not key TTL

**Severity.** MEDIUM (same bus-factor-1 risk as every other SCP-side governance artefact; not novel to this WP)

### 7.4 `generate-app-token` action's upstream supply-chain (per TF-PIM-001-SEC-003)

**Risk.** The new third-party action (`actions/create-github-app-token` or equivalent) becomes a new supply-chain dependency. Upstream compromise → SCP federation primitive compromise.

**Mitigation.**
- 40-char commit SHA pin (no tag refs) per WP-SCP-022 supply-chain posture
- CODEOWNERS coverage on `.github/**` ensures unauthorised SHA-pin updates are blocked
- Sigstore attestation status evaluated at Wave D (same TF-007 parallel for OPA / Conftest / Regal — if action publishes Sigstore attestations, `gh attestation verify` ratchets up)
- Action selection: prefer `actions/create-github-app-token` (GitHub first-party) over third-party for provenance

**Severity.** LOW-MEDIUM (single SHA-pin dependency; mitigated by existing supply-chain posture)

### 7.5 Path C 1-2 week implementation timeline overruns + PIM degraded state persists longer

**Risk.** Wave D's R-cycle stalls past R3 (cure-worse trigger fires); plan-doc authoring + R-cycle + dispatch + verification takes longer than estimated.

**Mitigation.**
- D-049 §Sequencing decouples v1.3.0 ship from TF-PIM-001 close; PIM degraded state does not block v1.3.0 ship-readiness
- PIM team's productive work continues during the degraded window (Phase 4 labeller workflow per operator's calendar note)
- §10 STEP 1 escalation path (re-open with E + F) remains available if A/C/D timing becomes load-bearing — though arch-skeptic already evaluated E/F as not Pareto-better than C
- §5.5 cure-worse trigger + Option A R4 mechanical override actively monitors for diminishing-returns

**Severity.** LOW (timeline slip is bounded; no second-order failure)

## §8 Standdown semantics

Real triggers only (per estate-wide discipline):

1. CRIT arch-scope question (operator-attended ASC)
2. Cure-worse-than-disease (R3 ship-proposal trigger)
3. Real context window degradation
4. ASC needing operator authorisation
5. Genuine resource constraint (Sonnet quota)

If implementation WP authoring (this v0.1 → v0.X iteration) surfaces an architectural-scope question on App-token surface vs SCP-side workflow restructure → file ASC + stand down for operator authorisation.

Otherwise: chain through R-cycle to R-fixpoint MET; then surface for operator review before any Wave D Codex dispatch fires.

## §9 Follow-ups

- TF-PIM-001-PLAN-002 (D-NNN ADR) — INHERITED from the closed plan-doc; delivered in Wave B
- TF-PIM-001-PLAN-004 (PIM required-check restoration) — INHERITED; delivered in Wave H
- TF-PIM-001-SEC-001..005 — INHERITED from sec lens evidence file; mapped per §3.3 table
- TF-PIM-001-ARCH-001..005 — INHERITED from arch-skeptic lens evidence file; mapped per §3.3 table
- FUP-WP-SCP-024-SCAFFOLDER-V1.2-INCOMPAT-001 (P1) — unblocks at TF-PIM-001 closure; separate impl slice opens after Wave H
- 2026-08-21 first App-key rotation execution — operator-attended; per TF-PIM-001-ARCH-001 cadence
- 2026-07-21 quarterly D-031 review extension — operator-attended; per TF-PIM-001-SEC-005
- Future cascade slices (024D-024G) inherit App-install ceremony per adopter — captured in WP-SCP-024 §5.2 update at first 024D dispatch

## §10 Closure

WP-closure when all 5 §2 acceptance criteria are satisfied:

1. ✅ External-adopter (PIM) cross-repo run green
2. ✅ PIM `main` `policy-check / scp/policy-check` required-check restored
3. ✅ ADOPT-001 §12.7 updated (§12.7.16 added; §12.7.5 amended; §12.7.10 reaffirmed; §12.7.13 amended)
4. ✅ D-050 ADR ratified
5. ✅ R1-evidence-on-fix-PR satisfies cardinal-rule-2 3-lens + CI citation pair

Closure ceremony:
- STATUS.md final entry under "Today's chain (YYYY-MM-DD — TF-PIM-001 CLOSED)" capturing all 5 criteria + evidence URLs
- BACKLOG.md Phase 12 → TF-PIM-001 row strikethrough with closure date + closure-commit SHA
- This plan-doc Status flips DRAFT → CLOSED at the closure-ceremony commit
- D-049 §Sequencing item 2 ("TF-PIM-001 closes") artefact-gate satisfied → Recommender becomes the natural next deny-gate adopter per D-049 D3 ratification

---

**End of plan-doc v0.1.** R1 dispatch pending operator review of v0.1 OR fresh R-cycle directive.
