# TF-PIM-001 Wave D' Spec Draft — Verbatim Execution Artefacts

**Companion to:** `docs/plans/TF-PIM-001-impl-path-c-app-credential.md` v0.6 §11
**Authored:** 2026-05-23 (v0.6 R1 fold — Lens C CRIT-001 closure)
**Status:** DRAFT — pending v0.6 plan-doc R2 R-FIXPOINT MET + Wave D' WP-spec authoring

## §1 Purpose

The v0.6 plan-doc §11 captures DESIGN INTENT for Path C v2. Per `feedback_orchestrator_auth_surface_plan_review_default.md` + L26+L27+L28 discipline, the VERBATIM EXECUTION-CLASS TEXT (YAML diffs, ADR amendment text, ADOPT-001 amendment text, scaffolder template diff, workflow-selftest fixture spec) lives in WP-spec authoring artefacts — NOT in the plan-doc itself.

This companion is the staging ground for that WP-spec content. When the Wave D' WP-spec is authored (per the Wave-D' dispatch artefact authoring flow), it consumes these verbatim sections as its authoritative source.

Reading this doc in isolation: this is what a Wave D' Codex dispatch would actually do to the SCP repo. Plan-doc readers should read v0.6 §11 first for design rationale; this doc second for verbatim execution.

## §2 Verbatim YAML — policy-check.yml input declaration (axis I closure)

In `.github/workflows/policy-check.yml`, the `on.workflow_call.inputs:` block currently declares 9 inputs (rule-set / threshold / annotate / scp_bypass / waivers-path / rule-config-path / fixture-path / scorecard-emit / simulate-app-token-failure). v2 adds a 10th: `scp-sha`.

**Anchored extraction location:** add at the end of the `on.workflow_call.inputs:` block, AFTER `simulate-app-token-failure:` declaration and BEFORE the `permissions:` block (line ~72 in main HEAD `2917522`; verify with `awk '/^\s*simulate-app-token-failure:/,/^\s*default: false\s*$/' .github/workflows/policy-check.yml` → next non-blank line is the insertion point).

**Verbatim YAML to insert:**

```yaml
      scp-sha:
        description: |
          SCP federation-primitive SHA this reusable workflow was loaded
          from. REQUIRED — adopter wrapper MUST pass the same 40-char SHA
          used in the `uses: jrnb2024/standards-control-plane-/.github/workflows/policy-check.yml@<SHA>`
          pin. Used by the `.scp-runtime` + `_scp-workflow` checkout steps
          to fetch SCP runtime files at the version the caller pinned to.
          Closes L31 axis I (cross-repo reusable-workflow self-SHA awareness
          gap surfaced by Wave G fix-forward 2026-05-23) — GHA exposes NO
          clean callee-context variable for "the SHA I was loaded from" in
          cross-repo workflow_call context; `github.workflow_sha` resolves
          to the CALLER's wrapper SHA (PIM PR merge ref), not this
          reusable-workflow's loaded-from SHA.
          Validation: pre-flight in the policy-check job's first step
          asserts `inputs.scp-sha` is non-empty + matches `^[a-f0-9]{40}$`
          regex; mismatch emits SCP-E001 annotation + exits 1 BEFORE any
          App-token-exchange happens (closes L31 axis I HIGH-002 stale-SHA
          validation gap from v0.5 R1 Lens B finding).
        required: true
        type: string
```

**Lens B HIGH-002 (stale-SHA validation) closure:** add NEW step right after the existing "Checkout caller repository" step + BEFORE "Simulate App token-exchange failure":

```yaml
      - name: Validate inputs.scp-sha (L31 axis I + R1 Lens B HIGH-002)
        shell: bash
        env:
          SCP_SHA: ${{ inputs.scp-sha }}
        run: |
          set -euo pipefail
          if [ -z "${SCP_SHA}" ]; then
            echo "::error file=.github/workflows/policy-check.yml,title=SCP-E001::inputs.scp-sha is required for v2 cross-repo workflow_call (closes L31 axis I). Adopter wrapper MUST pass scp-sha matching the @<SHA> pin."
            exit 1
          fi
          if [[ ! "${SCP_SHA}" =~ ^[a-f0-9]{40}$ ]]; then
            echo "::error file=.github/workflows/policy-check.yml,title=SCP-E001::inputs.scp-sha must be 40-char lowercase hex (got '${SCP_SHA}'). Closes L31 axis I + v0.5 R1 Lens B HIGH-002 stale-SHA validation."
            exit 1
          fi
          # Note: we don't verify SHA EXISTS in SCP repo here — that would
          # require an authenticated API call before the App-token-exchange
          # step runs. The downstream `.scp-runtime` checkout step will
          # surface a clear `actions/checkout` error if the SHA is unreachable
          # (better signal than a synthetic pre-flight network check).
          echo "✓ inputs.scp-sha validated: ${SCP_SHA}"
```

## §3 Verbatim YAML — `.scp-runtime` checkout step (axis H + I final fix)

**Anchored extraction location:** replace the entire "Checkout SCP runtime repository" step block. Current shape (post-PR-#142) at HEAD `2917522`:

```yaml
      - name: Checkout SCP runtime repository
        # [comments preserved]
        if: github.repository != 'jrnb2024/standards-control-plane-'
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          repository: jrnb2024/standards-control-plane-
          ref: ${{ github.workflow_sha }}            # WRONG for cross-repo — was the axis-H "fix" that introduced axis-I
          token: ${{ steps.scp-app-token.outputs.token }}
          path: .scp-runtime
```

**v2 replacement:**

```yaml
      - name: Checkout SCP runtime repository
        # When invoked cross-repo (the standard adopter path), this step
        # checks out the pinned SCP runtime into .scp-runtime so the
        # install + lib-source steps can read scripts/.tool-versions,
        # scripts/scp-policy-check.lock, lib/policy_check_invocation.sh,
        # and policies/. When invoked LOCALLY (`uses: ./...` from the
        # same repo, e.g. workflow-selftest), this step is skipped and
        # the populate step below symlinks the caller working directory
        # in place of the (now-absent) .scp-runtime.
        # WAVE-G AXIS-I FIX (v0.6 — 2026-05-23): uses inputs.scp-sha
        # instead of github.workflow_sha. github.workflow_sha resolves to
        # the CALLER's wrapper SHA in cross-repo workflow_call context
        # (PIM PR merge ref), NOT the SCP-side SHA the reusable workflow
        # was loaded from. inputs.scp-sha is REQUIRED + pre-validated by
        # the first job step (see "Validate inputs.scp-sha" above).
        if: github.repository != 'jrnb2024/standards-control-plane-'
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          repository: jrnb2024/standards-control-plane-
          ref: ${{ inputs.scp-sha }}
          token: ${{ steps.scp-app-token.outputs.token }}
          path: .scp-runtime
```

## §4 Verbatim YAML — `_scp-workflow` checkout step (axis I parallel fix)

**Anchored extraction location:** find the existing "Check out SCP repo at workflow ref for schema lookup" step. Anchor: `awk '/Check out SCP repo at workflow ref for schema lookup/,/persist-credentials: false/' .github/workflows/policy-check.yml`.

Current shape at HEAD `2917522`:

```yaml
      - name: Check out SCP repo at workflow ref for schema lookup
        id: scp-self-checkout
        if: always()
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          repository: jrnb2024/standards-control-plane-
          ref: ${{ github.workflow_sha }}            # WRONG for cross-repo — same axis-I bug as .scp-runtime
          token: ${{ steps.scp-app-token.outputs.token || github.token }}
          path: _scp-workflow
          persist-credentials: false
```

**v2 replacement:**

```yaml
      - name: Check out SCP repo at workflow ref for schema lookup
        id: scp-self-checkout
        # WAVE-G AXIS-I FIX (v0.6 — 2026-05-23): same axis-I bug as the
        # .scp-runtime checkout step above. ref: was github.workflow_sha
        # (CALLER's wrapper SHA in cross-repo); now uses inputs.scp-sha
        # (SCP-side SHA the reusable workflow was loaded from). Pattern
        # mirrors .scp-runtime checkout step (consolidated v2 architecture).
        # SCP-self invocation: inputs.scp-sha won't be set in selftest
        # context (selftest is a workflow_call from same-repo without the
        # adopter wrapper pattern), so fallback to github.workflow_sha (which
        # IS correct for SCP-self / same-repo workflow_call invocations —
        # only WRONG for cross-repo). The fallback preserves the schema-
        # lookup step for selftest harness while fixing the cross-repo case.
        if: always()
        uses: actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd # v6.0.2
        with:
          repository: jrnb2024/standards-control-plane-
          ref: ${{ inputs.scp-sha || github.workflow_sha }}
          token: ${{ steps.scp-app-token.outputs.token || github.token }}
          path: _scp-workflow
          persist-credentials: false
```

**Design note for selftest:** workflow-selftest.yml is SCP-self (same-repo) workflow_call. It doesn't pass `inputs.scp-sha` (no adopter wrapper pattern). The fallback `inputs.scp-sha || github.workflow_sha` keeps the schema-lookup step functional for selftest. Workflow-selftest fixture (§7 below) adds a "selftest doesn't pass scp-sha + schema-lookup still resolves" assertion.

## §5 Verbatim diff — `templates/adopter-wrapper.yml.tmpl` (axis I in scaffolder template)

**Anchored extraction location:** the `with:` block in the existing template (post-PR-#142). Add `scp-sha: {{SCP_SHA}}` after `scorecard-emit: {{SCORECARD_EMIT}}`.

**Diff:**

```diff
 jobs:
   policy-check:
     if: ${{ github.event.pull_request.head.repo.full_name == github.event.pull_request.base.repo.full_name }}
     permissions:
       contents: read
       statuses: write
       # [permissions comment block preserved]
       attestations: write
       id-token: write
     # Pin must be a 40-char SHA per WP-SCP-020 020B(v).
     # renovate: datasource=github-tags depName=jrnb2024/standards-control-plane-
     uses: jrnb2024/standards-control-plane-/.github/workflows/policy-check.yml@{{SCP_SHA}}
     with:
       scorecard-emit: {{SCORECARD_EMIT}}
+      # `scp-sha:` MUST mirror the @<SHA> pin above (axis I closure per
+      # ASC-2026-05-22-001 + plan-doc v0.6 §11.5). The Renovate auto-bump
+      # marker on the `uses:` line above triggers Renovate to update the
+      # @<SHA> pin; the {{SCP_SHA}} substitution in scaffolded wrappers
+      # populates BOTH the pin AND this input from the same source-of-truth
+      # value at scaffold time. Manual bumps (outside the scaffolder) MUST
+      # update both — see ADOPT-001 §12.7.16b for the bump procedure.
+      scp-sha: {{SCP_SHA}}
     # `secrets: inherit` per ASC-2026-05-22-001 Option α (ratified
     # [secrets comment block preserved]
     secrets: inherit
```

**Lens B HIGH-003 (transition discipline) closure:** see §10 below for the adopter-wrapper transition discipline section.

## §6 Verbatim — pre-authored PIM wrapper for Wave G v2

For Wave G v2 re-run on PIM, operator copies-pastes the wrapper text below into `frontend-repo/.github/workflows/policy-check-wrapper.yml` (the existing wrapper on PIM main is currently pinned to pre-axis-H SHA per the Wave G fix-forward history). `<NEW_SCP_SHA>` is replaced with the post-Wave-D' merge SHA on SCP main at Wave G v2 fire time.

```yaml
# Generated by scripts/scaffold-downstream.sh = SCP-073-scaffolder per WP-SCP-024 024B (D-044).
# Adopter wrapper canonical shape per ADOPT-001 §12 (v2; v0.6-amended for axis I + axes D/E/F/G).

name: policy-check

"on":
  pull_request:
    branches: [main]

permissions:
  contents: read
  statuses: write

jobs:
  policy-check:
    if: ${{ github.event.pull_request.head.repo.full_name == github.event.pull_request.base.repo.full_name }}
    permissions:
      contents: read
      statuses: write
      # See ADOPT-001 §12.7 for full architectural reasoning on caller-job
      # permissions (axis F closure — WP-SCP-023 023B attest-scorecard
      # caller-permissions-validation requirement).
      attestations: write
      id-token: write
    # Pin must be a 40-char SHA per WP-SCP-020 020B(v).
    # renovate: datasource=github-tags depName=jrnb2024/standards-control-plane-
    uses: jrnb2024/standards-control-plane-/.github/workflows/policy-check.yml@<NEW_SCP_SHA>
    with:
      scorecard-emit: false
      # scp-sha: MUST mirror the @<SHA> pin above (axis I closure)
      scp-sha: <NEW_SCP_SHA>
    # See ADOPT-001 §12.7.7 amendment for `secrets: inherit` architectural
    # choice rationale (axis G Option α per ASC-2026-05-22-001).
    secrets: inherit
```

**Operator-facing Wave G v2 ceremony:** see ADOPT-001 §12.7.16a amendment text in §8 below for App-install Repository access UI selection guidance.

## §7 Workflow-selftest fixture spec (axis I test coverage)

**File location:** new fixture at `tests/workflow/fixture-scp-sha-validation/` (parallel to existing fixture-pass / fixture-fail / fixture-simulate-token-exchange-failure).

**Test cases (closes Lens B MED-001 + Lens C MED-001 fixture-concreteness findings):**

| Test case | Setup | Expected outcome |
|---|---|---|
| Happy path (selftest invocation; no scp-sha) | Selftest calls policy-check.yml locally; doesn't pass `scp-sha` input | Pre-flight validation step short-circuits (selftest context); schema-lookup step uses `github.workflow_sha` fallback successfully; full pipeline green |
| Required input missing (cross-repo simulation) | Synthetic test caller passes `simulate-cross-repo: true` + `scp-sha: ""` (empty) | Pre-flight validation fires; SCP-E001 annotation emitted; exit code 1 on the validation step BEFORE App-token-exchange runs |
| Wrong SHA shape (malformed) | Synthetic test caller passes `scp-sha: "not-a-sha"` | Pre-flight validation fires; regex assertion fails; SCP-E001 annotation emitted with received value; exit code 1 |
| Mismatched-but-valid-shape SHA (unreachable in SCP) | Synthetic test caller passes `scp-sha: "0000000000000000000000000000000000000000"` (valid shape, doesn't exist) | Pre-flight validation passes (shape OK); `.scp-runtime` checkout step fails with `actions/checkout` error referencing the SHA; downstream steps skip; exit code 128 propagates |
| Happy path cross-repo (full integration) | Pre-authored fixture wrapper at `tests/workflow/fixture-scp-sha-validation/wrapper.yml` calls `uses: ./.github/workflows/policy-check.yml` with `scp-sha: ${{ github.sha }}` (same-repo SHA — wrapper-bump-simulation) | Pre-flight validation passes; full pipeline runs; selftest orchestrator asserts result == success |

**Cross-repo simulation note:** workflow-selftest runs in SCP-self context (same-repo). It cannot literally simulate cross-repo invocation (no external adopter repo available in selftest). The "cross-repo simulation" rows above use a `simulate-cross-repo: true` input (NEW input on policy-check.yml — small addition) that the pre-flight validation honors as if it were cross-repo. This is mock-coverage, parallel to the existing `simulate-app-token-failure` pattern. Real cross-repo coverage is operator-attended via Wave G v2 canary on PIM.

## §8 ADOPT-001 §12.7.16a verbatim text (axis E closure — App-install Repository access UI ceremony)

Insert as new sub-section after §12.7.16 (App-install ceremony from Wave C):

```markdown
#### §12.7.16a — App-install "Repository access" UI ceremony (axis E)

When operator installs `scp-federation-primitive` App on an adopter repo
via https://github.com/apps/scp-federation-primitive/installations/new,
the GitHub UI prompts for two distinct selections that are easy to conflate:

1. **Installation target** — the org and repo where the App is INSTALLED
   (i.e., which repo gets the App's webhook + which repo's secrets can
   mint App tokens from this install). For adopter onboarding, this is the
   adopter's repo (e.g., `jrnb2024/mapp-pim`, `jrnb2024/Recommender`, etc.).

2. **Repository access** — the repos the App's installation token can READ
   from this install (i.e., which repos the App-token-exchange step can
   subsequently call via cross-repo `actions/checkout`). For the SCP
   federation primitive pattern, this is ALWAYS `jrnb2024/standards-
   control-plane-` (the SCP repo, which the adopter's reusable-workflow
   call needs to checkout into `.scp-runtime`).

**Discipline:** operator MUST select **"Only select repositories"** in the
Repository access section and then select **`jrnb2024/standards-control-plane-`**
(NOT the adopter repo where the App is being installed).

If the operator accidentally selects the adopter repo in the Repository
access section (a common misinterpretation — "Repository access" sounds
like "which repo is this App associated with"), the App's installation
token will only be able to read the adopter repo, and the `.scp-runtime`
cross-repo checkout step will fail with `fatal: repository
'https://github.com/jrnb2024/standards-control-plane-/' not found` (despite
the URL being correct — the token lacks SCP read access).

**Verification:** after Save, the App's "Configure" page must show:
```
Permissions
  Read access to code and metadata

Repository access
  Only select repositories
  Selected 1 repository.
    jrnb2024/standards-control-plane-
```

If the listed repository is the adopter repo instead, operator MUST
re-configure to select SCP. The App can stay installed on the adopter
repo (that's correct); only the Repository access selection needs to
change.

**Background:** L31 axis E (App-install per-install repo-access scope
selection) surfaced during TF-PIM-001 Wave G canary 2026-05-22; operator's
initial App install selected the wrong "Repository access" target. Per
ASC-2026-05-22-001 + plan-doc v0.6 §11, the §12.7.16a ceremony codifies
the correct UI selection for all future adopter onboarding (cohort cascade
024D-024G + any subsequent adopter).
```

## §9 ADOPT-001 §12.7.16b verbatim text (axis D closure — wrapper SHA-pin bump procedure)

Insert as new sub-section after §12.7.16a:

```markdown
#### §12.7.16b — Adopter wrapper SHA-pin bump procedure (axes D + I)

When SCP cuts a new release OR ships a critical fix that adopters MUST pick
up, adopter wrappers' `@<SHA>` pin needs bumping. Per axis I closure (v0.6
§11.5), the bump now requires **two** synchronized field updates:

1. The `uses:` line `@<SHA>` pin
2. The `scp-sha:` input value (must match `@<SHA>` exactly)

If the two diverge, the workflow either runs at the wrong version (security
gap) or fails at `inputs.scp-sha` pre-flight validation (degraded discipline).

**Standard procedure (Renovate auto-bump):**

1. Renovate detects new SHA tag on `jrnb2024/standards-control-plane-`
   (per `renovate: datasource=github-tags` marker on the `uses:` line)
2. Renovate opens PR on adopter repo bumping the `@<SHA>` pin in the
   `uses:` line
3. **WARNING**: Renovate's default behavior does NOT update the `scp-sha:`
   input value in the same `with:` block. Adopter MUST add a Renovate
   regex-rule that updates `scp-sha:` to mirror the `@<SHA>` value, OR
   manually edit the `scp-sha:` value in Renovate's PR before merge.
4. CI runs against the Renovate PR; if `scp-sha:` mismatches `@<SHA>`,
   pre-flight validation fails with clear SCP-E001 annotation
5. After both fields match + CI green, merge

**Renovate regex-rule template** (adopters should add to `renovate.json`):

```json
{
  "packageRules": [
    {
      "matchPackageNames": ["jrnb2024/standards-control-plane-"],
      "postUpgradeTasks": {
        "commands": [
          "sed -i \"s/scp-sha: .*$/scp-sha: ${{ depName.newValue }}/\" .github/workflows/policy-check-wrapper.yml"
        ],
        "fileFilters": [".github/workflows/policy-check-wrapper.yml"],
        "executionMode": "update"
      }
    }
  ]
}
```

(Renovate's `postUpgradeTasks` requires admin-level Renovate self-host or
Mend Renovate's premium tier. For adopters on free Renovate, manual edit
of the `scp-sha:` value in the Renovate PR is the workaround.)

**Manual bump procedure (no Renovate):**

1. Identify new SCP SHA from SCP repo's recent main HEAD or release notes
2. Edit `.github/workflows/policy-check-wrapper.yml`:
   - Update `uses: ...@<OLD_SHA>` → `uses: ...@<NEW_SHA>`
   - Update `scp-sha: <OLD_SHA>` → `scp-sha: <NEW_SHA>`
3. Verify both values match: `grep -E "@[a-f0-9]{40}|scp-sha: [a-f0-9]{40}"
   .github/workflows/policy-check-wrapper.yml | awk '{print $NF}' | sort -u
   | wc -l` should equal `1` (one unique value across both lines)
4. Commit + push + open PR
5. CI verifies; merge

**Verification (post-bump CI green):** PR's `policy-check / scp/policy-check`
check returns SUCCESS. If FAILURE, inspect:
- `inputs.scp-sha` validation step output (mismatched values OR malformed SHA)
- `.scp-runtime` checkout step (unreachable SHA on SCP — typo or stale)
- Other policy-check steps (substantive policy violation OR SCP-side bug)

**Cadence:** SCP cuts new SHA on every main-branch merge. Adopters bump at
their discretion. Recommended cadence:
- Critical security fix: ASAP (operator-attended)
- Feature release (e.g., new rule set, new opt-in input): within 2 weeks
  of SCP release-notes
- Hygiene bump: monthly (Renovate-automated)

**Background:** L31 axis D (artefact-pin currency) + axis I (cross-repo
self-SHA awareness) surfaced during TF-PIM-001 Wave G 2026-05-22 to
2026-05-23. PIM's wrapper was pinned to a SHA from 2026-04 (pre-Wave-D —
the very TF-PIM-001 cross-repo auth bug PIM was supposed to validate the
fix for). Per ASC-2026-05-22-001 + plan-doc v0.6 §11, this §12.7.16b
ceremony codifies the bump discipline for all future adopters.
```

## §10 Adopter-wrapper transition discipline (Lens B HIGH-003 closure)

**Question raised by R1 Lens B HIGH-003:** post-v2 ships, what happens to existing adopter wrappers that don't have `scp-sha:` input in their `with:` block?

**Answer:** v2 introduces `inputs.scp-sha` as `required: true`. Pre-v2 adopter wrappers (without `scp-sha:`) will fail GHA startup validation with a clear error: `"Input required and not supplied: scp-sha"`. The workflow won't run at all.

**Transition approach (operator-confirmed during v0.6 R1 fold):** HARD CUT, not backward-compat fallback. Rationale:
- Backward-compat (`required: false` + fallback to `github.workflow_sha`) would preserve the axis I bug for adopters who don't bump — silent failure mode that the CI would still call "success"
- Hard cut (`required: true`) forces every adopter to bump synchronously with v2 ship
- Cohort cascade slices 024D-024G can pre-stage the bump in the same PR that introduces the adopter wrapper (zero transition pain — they never had a v1 wrapper)
- Existing adopters (only PIM currently) get their bump as part of Wave G v2 re-fire (operator-attended; coordinated)

**Future-adopter discipline:** future cohort cascade slices (024D-024G + beyond) generate adopter wrappers DIRECTLY from the post-v2 scaffolder template — they never have the pre-v2 shape.

**Existing-adopter discipline:** the PIM wrapper bump is the canonical instance. CT / MDA / Recommender / shopify-app — when their cohort slices fire — will use the v2 scaffolder template natively (no transition).

**Mitigation if a stale-pin adopter PR fires post-v2:** the GHA startup error (`Input required and not supplied: scp-sha`) is loud and actionable. Adopter reads the error → follows ADOPT-001 §12.7.16b bump procedure → CI green. No silent failure mode.

## §11 D-050 ADR v2 amendment text (Lens C CRIT-001 + MED-004 closure)

D-050 ADR (in `docs/DECISIONS.md`) currently has an `ACCEPTED` row for Path C ratification (2026-05-21 / PR #136). v2 amendment adds:
- An "Amendment 2026-05-23" sub-row capturing the 7-axis closure findings + Option α architectural choice + axis I `inputs.scp-sha` pattern
- Updated invariants list (App-credential broad-grant distinction; `secrets: inherit` allowed at caller-side; `inputs.scp-sha` required cross-repo pattern; adopter wrapper repo-access scope discipline)
- Closure path: this v0.6 plan-doc + companion specs

**No new D-NNN reservation needed.** Path C remains the ratified architecture; the amendment captures implementation-detail evolution.

**Verbatim D-050 amendment text** (insert into `docs/DECISIONS.md` D-050 row's status-detail column):

```markdown
**Amendment 2026-05-23 — Path C v2 (closes ASC-2026-05-22-001).**

Wave G fix-forward cycle (2026-05-22 → 2026-05-23) surfaced 7 cross-repo
auth-architecture gaps not anticipated in v1 design (L31 axes C/D/E/F/G/H/I
per `~/.claude/projects/-Users-amplience-Projects/memory/feedback_content_
semantic_verification_gap.md`). Operator-ratified hard-stand-down per
cure-worse cardinal rule 2 + the formalized R2-fix-cycle rule from
Recommender Option B pre-review (2026-05-22).

Path C v2 incorporates all 7 SCP-side axes into the design upfront:

1. **`secrets: inherit` at adopter caller-job** (axes C + G; Option α
   ratified): adopter wrapper grants `secrets: inherit` so the SCP-trusted
   reusable workflow can mint App tokens from adopter-stored secrets.
   §12.7.10 invariant preserved literally — no `secrets: inherit` IN
   policy-check.yml (the original PAT-broad-grant prohibition); App-
   credential broad-grant from adopter to SCP-trusted-workflow is
   materially different (read-only, scoped to SCP repo, operator-
   revokable per-install).

2. **`inputs.scp-sha` required for cross-repo callees** (axes H + I):
   GHA exposes no clean callee-context variable for "the SHA the
   cross-repo reusable workflow was loaded from." Adopter wrapper MUST
   pass `scp-sha:` matching the `@<SHA>` pin. Cross-repo checkout steps
   use `inputs.scp-sha` (not `github.workflow_sha` which resolves to
   caller's wrapper SHA).

3. **App-install Repository access scope explicit** (axis E): ADOPT-001
   §12.7.16a documents the UI ceremony — Repository access MUST be
   `jrnb2024/standards-control-plane-` (NOT the adopter repo).

4. **Adopter wrapper bump procedure** (axis D): ADOPT-001 §12.7.16b
   documents synchronized `@<SHA>` + `scp-sha:` bump procedure with
   Renovate auto-bump regex-rule template + manual fallback.

5. **Caller-job permissions for `attest-scorecard`** (axis F): scaffolder
   template includes `attestations: write + id-token: write` at caller-job
   level (job-scoped per 023B MAJ-SAFE-001, NOT workflow-level OIDC trust).
   Closed in SCP PR #142.

Implementation: SCP PR #142 (axes C/F/G/H), Wave D' amendment PR
(axis I + axes D/E ADOPT-001 documentation), Wave G v2 PIM canary
re-fire (post-Wave-D' merge), Wave H PIM main required-check restoration
(per existing plan-doc §4).

Status: Path C v2 design ratified 2026-05-23. Implementation in progress
(Wave D' amendment authored per plan-doc v0.6 §11 + this companion
`docs/plans/TF-PIM-001-wave-d-prime-spec-draft.md`).

Deferred follow-ups: TF-SCP-PATH-C-WORKFLOW-CALL-SECRETS-EXPLICIT-
DECLARATION-V2 (Option β explicit declaration + per-call pass-through;
estate-wide hardening once cohort cascade stable; P3); FUP-SCP-ADOPTER-
WRAPPER-PERMISSIONS-PROPAGATION (estate-wide adopter wrapper update
coordination for cohort cascade 024D-024G; P2 — adopter wrappers
generate from updated scaffolder template natively); Path A consideration
as long-term simplification (P3 — strategic).
```

## §12 Lens C MED follow-ups

- **MED-002 (§12.7.7 amendment scope):** §12.7.7 amendment is a new paragraph at the END of §12.7.7 (after the existing PAT-broad-grant prohibition discussion) that explicitly states: "Adopter-side `secrets: inherit` on the policy-check caller-job is the v2 architectural choice (axis G Option α per ASC-2026-05-22-001). This is MATERIALLY DIFFERENT from `secrets: inherit` IN policy-check.yml (which §12.7.10 explicitly prohibits): the adopter-side inherit grants the SCP-trusted reusable workflow read access to adopter secrets (App-credential pass-through for cross-repo auth); it does NOT clone a PAT into the callee context. See plan-doc v0.6 §11.5 + ASC-2026-05-22-001 for full architectural reasoning."

- **MED-005 (FUP-SCP-ADOPTER-WRAPPER-PERMISSIONS-PROPAGATION P-rating):** Re-rate from P1 to P2 per R1 Lens C feedback. Rationale: cohort cascade slices 024D-024G generate adopter wrappers DIRECTLY from the v2 scaffolder template — they never have the pre-v2 shape, so the propagation gap doesn't apply to future adopters. Existing PIM wrapper bump is handled via Wave G v2 re-fire (operator-attended). FUP captures the cohort-coordination ceremony for completeness but isn't blocking.

- **MED-006 (TF-SCP-PATH-C-WORKFLOW-CALL-SECRETS-EXPLICIT-DECLARATION-V2 naming):** Tracked-forward as `TF-PIM-001-WORKFLOW-CALL-SECRETS-EXPLICIT-DECLARATION-V2` (renamed to align with TF-PIM-001 naming convention; not a new WP). Captures Option β for v2 hardening. P3.

## §13 Cross-references

- `docs/plans/TF-PIM-001-impl-path-c-app-credential.md` v0.6 §11 (the plan-doc this companion supports)
- `~/.claude/projects/-Users-amplience-Projects/memory/ASC-2026-05-22-001.md` (operator ratification record)
- `~/.claude/projects/-Users-amplience-Projects/memory/feedback_content_semantic_verification_gap.md` (L31 9-axis estate memo — methodology framework)
- `docs/DECISIONS.md` D-050 (the ADR being amended per §11 above)
- `docs/adoption/ADOPT-001-project-onboarding.md` §12.7 (the ceremony documentation being amended per §8 + §9 above)
- `templates/adopter-wrapper.yml.tmpl` (scaffolder template being amended per §5 above; partially closed in PR #142)
- PR #142 (Wave G consolidated 5-axis closure — axes C/F/G/H)
- PR #259 (PIM canary — standing-down with 9-axis evidence chain preserved)
- `feedback_autonomous_directive_scope_interpretation.md` (Reading A — cure-worse cardinal rule 2 invocation authority)
