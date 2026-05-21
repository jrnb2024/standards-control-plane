# TF-PIM-001 Wave D dispatch JSON — R1 synthesis

**Date:** 2026-05-21 PM
**Artefact under review:** `docs/governance/work-packages/tf-pim-001-wave-d-policy-check-yaml-token-exchange.json` (v0.1)
**Lenses dispatched:** sec / arch-skeptic / pragmatist (3-lens auth-surface default per estate convention)
**Dispatch mode:** parallel Plan agents (read-only by design — DO-NOT-EDIT mandate enforced at tool-availability layer); sample-size-3 incident citation (CT c565fd0 / Recommender V14 INT #2 / `docs/ESTATE-CONVERGENCE.md` PR #131 history) — ZERO scope-breach observed across R1

## Verdict matrix

| Lens | Verdict | Convergence | BLOCK | MAJ | MIN | NIT |
|------|---------|-------------|-------|-----|-----|-----|
| sec | ACCEPT-WITH-AMENDMENT | ITERATE-EXPECTED | 0 | 1 | 1 | 2 |
| arch-skeptic | ACCEPT-WITH-AMENDMENT | ITERATE-EXPECTED | 0 | 2 | 3 | 2 |
| pragmatist | ACCEPT-WITH-AMENDMENT | ITERATE-EXPECTED | 0 | 1 | 1 | 1 |
| **TOTAL** | | | **0** | **4** | **5** | **5** |

**Three-lens consensus:** ITERATE-EXPECTED. Zero BLOCKING. All findings are remediable inline in a single v0.2 fold without scope-split or plan-doc rework.

## Closure plan (v0.2 fold)

### MAJ closures (mandatory — close before R2)

1. **PRAG-MAJ-001** — Fix CMD 18 + CMD 19 to use `git diff HEAD` (working-tree-vs-last-commit) instead of `git diff origin/main HEAD` (committed diff); drop the `git fetch` prefix. Rationale: Codex CLI in workspace-write sandbox leaves changes unstaged (`git_sha_before == git_sha_after`), so committed-diff probes produce empty output and false-BLOCKED every correct run. Working-tree diff is remote-independent and correctly captures Codex's edits.

2. **ARCH-MAJ-001** — Remove `|| github.token` fallback from EDIT 2's `token:` expression; keep on EDIT 3. EDIT 2 becomes `token: ${{ steps.scp-app-token.outputs.token }}` (plan-doc verbatim). Update rationale to document the INTENTIONAL asymmetry: EDIT 2 asserts App-token presence (co-gated step — `if: github.action_ref != ''` co-variant with token-exchange step); EDIT 3 keeps fallback because `if: always()` decouples it from the exchange step's guard. EDIT 3 is the ONLY site where the fallback is critical.

3. **ARCH-MAJ-002** — Embed pre-verified SHA resolution evidence in the `notes` field. Include the raw `gh api repos/actions/create-github-app-token/git/refs/tags/v3.2.0 --jq '.object'` output (showing commit-type + SHA `bcd2ba49218906704ab6c1aa796996da409d3eb1`) AND the FALLBACK's tag-dereference chain (annotated-tag SHA → `gh api repos/tibdex/github-app-token/git/tags/<tag-SHA>` → commit-SHA `3beb63f4bd073e61482598c45c71c1019b59b73a`). Creates an auditable trail independent of network access at verify time.

4. **SEC-MAJ-001 / ARCH-MIN-002 (same fix-point)** — Add Wave E coupling derogation note to dispatch JSON `notes` field. Document operator-decided sequential sequencing: Wave E env-var injection EXCLUDED from this dispatch; Wave E fires post-Wave D merge (not in parallel); same-PR coupling constraint resolved by sequential sequencing not by inclusion.

### MIN closures (should fold — cheap)

5. **SEC-MIN-001** — Add verify_command: `IDLINE=$(grep -nF 'id: scp-app-token' .github/workflows/policy-check.yml | head -1 | cut -d: -f1); awk -v s=$((IDLINE-3)) -v e=$((IDLINE+3)) 'NR>=s && NR<=e' .github/workflows/policy-check.yml | grep -F "if: github.action_ref != ''"` — verifies the if-guard appears within ±3 lines of the token-exchange step's id.

6. **ARCH-MIN-001 / PRAG-NIT-001 (combined fix-point)** — Replace the two awk-window probes (CMD 16 + CMD 17) with semantic two-phase grep ordering checks:
   - EDIT 2 ordering: `repository: ${{ github.action_repository }}` line < `token: ${{ steps.scp-app-token.outputs.token }}` line < `path: .scp-runtime` line
   - EDIT 3 ordering: `repository: jrnb2024/standards-control-plane-` line < `token: ${{ steps.scp-app-token.outputs.token || github.token }}` line < `path: _scp-workflow` line
   This is more semantically anchored than fixed-window awk and resilient to comment-block preservation. Subsumes PRAG-NIT-001 (token-before-path ordering).

7. **PRAG-MIN-001 / SEC-NIT-002 (combined fix-point)** — Amend invariant-5 description from "8 YAML lines" to "9 YAML lines"; bump CMD 19 diff-budget lower bound from `-ge 8` to `-ge 11` (true minimum: 9 step lines + 2 token lines).

8. **ARCH-MIN-003** — Subsumed by PRAG-MAJ-001 fix (replacing `git diff origin/main HEAD` with `git diff HEAD` removes the `git fetch` dependency entirely).

### NIT closures (optional polish)

9. **SEC-NIT-001** — Add Sigstore attestation status sentence to `notes`: "Sigstore attestation status for `actions/create-github-app-token` v3.2.0 evaluated at dispatch authoring: GitHub first-party action; attestations not yet published to GitHub's attestation database (TF-007 parallel posture); SHA-pin remains the primary supply-chain anchor."

10. **ARCH-NIT-001** — Add invariant 6: "**No permissions block amendment required.** The workflow-level permissions (`contents: read`, `statuses: write`) are sufficient for the token-exchange step. `actions/create-github-app-token` resolves App credentials from GitHub Actions' built-in secret context; does NOT require `id-token: write` (which is OIDC, not App-credential). The existing WP-SCP-023 023B `id-token: write` exclusion is fully preserved."

11. **ARCH-NIT-002** — No action. FALSE POSITIVE — `gpt-5.4` IS the canonical Codex CLI model name per `/Users/amplience/Projects/acc/schemas/codex_work_package.schema.json` line 49 (enumerated: `gpt-5.4, gpt-5.4-mini, gpt-5.3-codex, gpt-5.3-codex-spark, gpt-5.2`). Lens confused Codex CLI namespace with Anthropic namespace. Closure note in v0.2 R-cycle changelog.

## Federation-primitive invariants disposition (sec lens consensus)

All five invariants preserved under the v0.2-amended dispatch JSON:

1. **Adopter token does not leave adopter context** — preserved (App-token-only checkout; `persist-credentials: false` on all 3 sites; no SCP-controlled script reads the App token)
2. **SCP-controlled workflow code never sees adopter named secrets** — preserved (no `secrets:` block on workflow_call; App key in SCP-repo secrets; VC[11] enforces no `secrets: inherit`)
3. **Trust roots in tag-protected SHA pins** — preserved (40-char commit SHA pin; CODEOWNERS `.github/** @jrnb2024` gates updates; FALLBACK SHA documented but not engaged)
4. **Policy bundle integrity is verifiable** — preserved (scope_boundary single-file; no lockfile changes)
5. **Annotation surface is fixed** — preserved (no new SCP-EXXX codes; new step is internal, not annotation-emitting)

## Plan-doc fidelity (arch-skeptic disposition)

The v0.1 dispatch JSON was substantially faithful to plan-doc §4 Wave D except for the EDIT 2 `|| github.token` fallback — closed in v0.2 by reverting to plan-doc verbatim. The EDIT 3 fallback divergence is justified (the plan-doc Action step 6 rationale on SCP-self correctness implicitly requires the fallback for the `if: always()` schema-lookup step; the plan-doc verbatim wording is incomplete for this site). Post-R-fixpoint hygiene: the impl WP plan-doc §4 Action step 4 may be amended to include the EDIT 3 fallback explicitly — operator-paced; out-of-scope for the Wave D dispatch JSON itself.

## Reversibility (arch-skeptic disposition)

The v0.2 dispatch JSON preserves the D-050 / plan-doc §7.5a reversibility profile fully:
- Scope_boundary single-file → single-PR revert
- SCP-self continues post-revert (co-gated steps both skip under self-dogfood)
- App + secrets stored in Wave A remain intact (no Wave A re-do needed on revert)
- ADOPT-001 §12.7 + D-050 ADR remain published (architectural commitment unchanged; only workflow change reverted)

## Convergence to R-FIXPOINT MET (R2 expectation)

After v0.2 fold (all 4 MAJ closures + the 4 cheap MIN closures), R2 is expected to:
- Surface zero new BLOCKING/MAJ findings on the substantive dispatch content (instruction, scope_boundary, verify_commands core probes)
- Possibly surface 1-2 new MIN/NIT findings on the new content added in v0.2 (Wave E coordination note phrasing; SHA-provenance evidence formatting; semantic-grep ordering check wording) — these are expected residuals not blockers
- Reach R-FIXPOINT MET if the new-finding count is 0-2 NIT-class with no MAJ
- Trigger Option A R4 mechanical override at R3 if cure-worse signal surfaces (per `feedback_asymptotic_trajectory_split.md` + precedent from impl WP plan-doc v0.4 invocation)

## Standdown posture (per continuation prompt step 7)

After R-FIXPOINT MET: open PR with 3-lens R1 evidence block (correctness / safety_bypass / completeness_governance — lens-name-mapped from sec → safety_bypass; arch-skeptic → correctness; pragmatist → completeness_governance per estate validate-PR-body convention); standdown at PR-opened state. Codex Tier 2 fire remains operator-attended per the four-tier dispatch pattern + the continuation prompt's explicit Reading A exclusion ("First Codex fire in a new WP class is operator-paced").
