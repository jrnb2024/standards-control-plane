# TF-PIM-001 — Cross-repo checkout authentication for SCP federation adopters

**Status:** CLOSED-WITH-RATIFIED-PATH (Path C ratified 2026-05-21 post orchestrator-attended 3-agent review; impl WP plan-doc at `docs/plans/TF-PIM-001-impl-path-c-app-credential.md`)
**Filed:** 2026-05-20 (after PR #125 D-049 + RULE-002 merge at `71a6e41`)
**Owner:** @jrnb2024
**Origin:** `docs/BACKLOG.md` Phase 12 row `TF-PIM-001` (filed 2026-05-19 from PIM PR #236 WP-300 Workbench Assembly unblock diagnostic)
**Severity:** P0 — fundamental blocker for every external WP-SCP-024 cascade adopter
**Auth-surface:** **YES** (every viable fix path touches the federation primitive's auth surface; mandatory plan-stage 3-agent review per `feedback_orchestrator_auth_surface_plan_review_default.md` before any implementation slice opens)

---

## 1. Context

WP-SCP-024 024C (PIM canary cascade) ceremonied closed 2026-05-17 at PR #118 merge with `cascade-status: onboarded`. PIM `main` had brownfield-merged with 5 required contexts including `policy-check / scp/policy-check`; `required_signatures.enabled=true`; D-045 filed.

On 2026-05-19, PIM PR #236 (WP-300 Workbench Assembly) opened against PIM `main` and was blocked by a `policy-check / scp/policy-check` failure. Diagnostic surfaced the failure mode: the SCP reusable workflow's cross-repo `actions/checkout` steps cannot clone the private SCP repository from an adopter context because the default `GITHUB_TOKEN` is scoped to the caller repository only.

Operator-attended unblock 2026-05-19: branch protection relaxation — `policy-check / scp/policy-check` removed from PIM `main` required-checks until this issue lands. PIM is currently operating with a relaxed required-check set, weakening the cascade's `cascade-status: onboarded` invariant. **This is a known load-bearing degradation; restoring PIM's full required-check set is part of this work's terminal-state criteria.**

The blocker affects **every external WP-SCP-024 cascade adopter**. SCP's own dogfood works because it is same-repo (`GITHUB_TOKEN` auto-has same-repo access). External adopters (PIM today; planned: control-tower, mapp-doc-agent, recommender, shopify-app) cannot exercise the federation primitive cross-repo while SCP remains private.

This plan-doc is **input to an orchestrator-attended plan-stage 3-agent review**. The plan-doc enumerates fix paths and surfaces the load-bearing decision-points; it does **not** pre-commit to a fix path. Path selection is the 3-agent review's output, ratified by the operator on dispatch sign-off.

## 2. Observed failure shape (precise)

Three `actions/checkout` invocations in `.github/workflows/policy-check.yml` (the federation primitive's reusable workflow at SHA `04523fac` for v1.0.0 / `41a5299` for the PR #236 caller pin):

| Step | Line | Repository checked out | Fails cross-repo on private SCP? |
|---|---|---|---|
| "Checkout caller repository" | 92 | (caller) — `${{ github.repository }}` | No — same repo, default `GITHUB_TOKEN` scope sufficient |
| "Checkout SCP runtime repository" | 107 | `${{ github.action_repository }}` at `${{ github.action_ref }}` → `.scp-runtime/` | **YES** — fails to clone private SCP |
| "Check out SCP repo at workflow ref for schema lookup" | 1149 | `jrnb2024/standards-control-plane` at `${{ github.workflow_sha }}` → `_scp-workflow/` | **YES** — fails to clone private SCP |

Both failing steps use the default token (no `token:` parameter set; falls back to `${{ github.token }}` which is the caller's `GITHUB_TOKEN`).

Downstream impact when these checkout steps fail:

- `.scp-runtime/` is empty → `scp-policy-check` lock-file, `.tool-versions`, `lib/policy_check_invocation.sh`, `policies/` all unreachable
- `_scp-workflow/` is empty → `schemas/policy-check-summary.schema.json` unreachable → schema validation fails
- All 12 policy-check steps SKIPPED in the GitHub Actions run
- Wrapper job exits non-zero → required-check fails → adopter PR blocked

Evidence: failed run `https://github.com/jrnb2024/mapp-pim/actions/runs/26131634673` — "Populate .scp-runtime (self-call fallback)" + "Check out SCP repo at workflow ref for schema lookup" both FAILED; all 12 policy-check steps SKIPPED.

## 3. Existing invariant under tension — ADOPT-001 §12.7.10

`docs/adoption/ADOPT-001-project-onboarding.md` §12.7.10 "NEVER use `secrets: inherit`":

> The SCP reusable workflow **does not declare any `secrets:`**. Adopter wrappers MUST NOT use `secrets: inherit` on the `uses:` invocation. The caller's `GITHUB_TOKEN` is the privilege ceiling; granting any other secret to the workflow expands the blast radius beyond what the federation primitive's threat model assumes.
>
> **Forward-compatibility caveat.** Do not add `secrets: inherit` even if it appears to be a safe no-op at the current SCP version (where the reusable workflow declares no secrets). A future SCP version that introduces any named `secrets:` declaration would retroactively pass every caller secret to the workflow on adopter repos that pre-emptively added `secrets: inherit`. Bypassing this declaration is therefore both unnecessary today AND a forward-compatibility risk.

This invariant is **load-bearing for the federation primitive's threat model**. It establishes a one-way auth-surface property: the workflow can NEVER see more than what its named inputs surface. Inverting §12.7.10 (allowing or requiring `secrets: inherit`) would re-open the federation primitive's auth surface in both directions:

- Adopter-side: caller secrets become visible to SCP-controlled workflow code.
- SCP-side: future named-secrets declarations would inherit silently from every `secrets: inherit` adopter.

The BACKLOG.md TF-PIM-001 row referenced "fix path (a): accept a PAT or GitHub-App token via `secrets: inherit` in the reusable workflow." That phrasing is the immediately-obvious GitHub-actions pattern, but it directly contradicts §12.7.10 as written. This contradiction is the canonical reason TF-PIM-001 work cannot proceed without orchestrator-attended plan-stage review — the routine implementation pattern violates an existing federation-primitive invariant.

The 3-agent review's job is to determine whether the invariant should be inverted, partially relaxed, or preserved (with a non-`secrets: inherit` fix path chosen). All three outcomes are tenable; the review's output is the ratification.

## 4. Threat model recap — what §12.7.10 is protecting

The federation primitive's invariant set (per WP-SCP-020 plan-doc §3 + WP-SCP-022 implementation programme §4.4 + ADOPT-001 §12.7 trust-rooting):

1. **Adopter token does not leave adopter context.** Caller `GITHUB_TOKEN` is workflow-scoped; never written to artefacts, never forwarded to network calls outside the GitHub Actions runner, never persisted in `actions/checkout`-cloned trees (the workflow sets `persist-credentials: false` on every checkout).
2. **SCP-controlled workflow code never sees adopter named secrets.** No `secrets:` declared on the reusable workflow → adopters' named secrets stay opaque to SCP code regardless of the wrapper invocation.
3. **Trust roots in tag-protected SHA pins.** Adopter wrappers pin to `policy-check.yml@<SHA>` at a tag-protected release (D-030 + D-034); branch-protection on SCP's `v*` and `renovate/v*` rulesets prevents tag mutation.
4. **Policy bundle integrity is verifiable.** OPA + Conftest + Regal binaries are SHA256-pinned and verified (per WP-SCP-022 020H.2 + 020M); `requirements/policy-check.txt` is hash-pinned (D-036 / 020M).
5. **Annotation surface is fixed.** SCP-EXXX error codes are a closed set (ADOPT-001 §12.7.7); the wrapper cannot inject arbitrary annotation content.

Inverting §12.7.10 (allowing `secrets: inherit`) breaks invariant 2 directly. Any fix path must either preserve invariant 2 OR explicitly ratify its relaxation with a compensating control.

## 5. Fix-path enumeration

Six fix paths surveyed. Each is described with its auth-surface implication, distribution-mechanism implication, and per-adopter integration cost.

### 5.0 Path closure — operator ratification 2026-05-21 (post 3-agent review)

The orchestrator-attended 3-agent review on the A/C/D shortlist ran 2026-05-20 PM. Evidence + synthesis: `docs/reviews/TF-PIM-001/shortlist-A-C-D/{sec,arch-skeptic,pragmatist}-lens-r1.md` + `synthesis.md`. Outcome was non-convergent (2-1 split: sec=Strong C, arch-skeptic=Strong C, pragmatist=Strong A); operator-attended convergence resolved 2026-05-21.

**Operator ratification — Path C (App-credential).** Final disposition:

- **Path C — RATIFIED (winning path).** GitHub App with `repository_permissions: { contents: read }` scoped to `jrnb2024/standards-control-plane` only. App token obtained inside SCP-controlled workflow code; never via `secrets: inherit`; §12.7.10 invariant fully preserved. Inherits TF-PIM-001-{SEC,ARCH}-* tracked-forward items from `sec-lens-r1.md` + `arch-skeptic-lens-r1.md` evidence (10 items total: App-credential rotation SOP, ADOPT-001 §12.7.5 de-adoption update, `generate-app-token` action SHA-pin + supply-chain registration, per-adopter App-install access verification, 2026-07-21 quarterly review extension, selftest harness coverage for App token-exchange failure path, ADOPT-001 §12.7 App-install ceremony documentation, multi-org adopter App-install coordination surface, D-NNN ADR for Path C App-credential surface). Rationale: sec + arch-skeptic concordance carries the decision on irreversibility asymmetry; Path A's "effectively irreversible" repo-public flip exposes all SCP historic content (DECISIONS.md / plan-docs / R1+R2 evidence / ADRs / governance content) permanently, and the compensating control (separate `standards-control-plane-private` repo) creates permanent two-repo split + bus-factor-1 + friction for future internal artefact authoring. Path C's risks are all recoverable: App-credential rotation, custody under D-031 quarterly review, install-ceremony as one-time per adopter. The 1-2 week implementation cost + PIM's extended degraded state are bounded + time-limited + operator-attended.

- **Path A — REJECTED-WITH-RATIONALE.** Rejected on irreversibility asymmetry. Repo-public flip permanently exposes historic governance content; compensating control via `standards-control-plane-private` creates permanent two-repo split + bus-factor-1. 1-2 session calendar saving did not outweigh permanent strategic exposure per operator ratification 2026-05-21.

- **Path D — REJECTED-WITH-RATIONALE.** Rejected by all three lenses (cross-cutting agreement) on attestation-parity gap + correlated bundle-pipeline failure + Renovate-preset rewrite cost.

- **Paths E + F — DROPPED-NOT-INVOKED (escalation-eligible per §10 STEP 1).** Not invoked because Path C ratification at 3-agent review stage closed the path-choice question. Both remain architecturally tenable per plan-doc §5; future TF-PIM-001-class auth-surface questions may surface them via §10 STEP 1 escalation. Per-path detail preserved verbatim below.

- **Path B — DROPPED-REQUIRES-OPERATOR-AUTHORISATION (status unchanged).** Path B status unchanged per pre-3-agent-review framing. §12.7.10 inversion not ratified; re-opening requires explicit subsequent operator authorisation per §10 STEP 2 (ASC-class).

Pragmatist's calendar-pressure case acknowledged but not overriding the irreversibility asymmetry: (i) v1.3.0 ships before TF-PIM-001 closes per D-049 §Sequencing item 1 (self-dogfood-only; TF-PIM-001 is artefact-gate on adopter-side consumption, not on v1.3.0 itself) — decoupling was intentional; (ii) PIM degraded state is documented + operator-attended + recoverable; PIM session continues Phase 4 labeller workflow productive work in parallel during the 1-2 weeks; (iii) Path D rejected by all three lenses (cross-cutting agreement); re-litigating via §10 STEP 1 (E/F) won't surface new information per arch-skeptic's unprompted E/F evaluation.

The original 6-path enumeration is preserved below verbatim so the Pareto-frontier reasoning that produced the A/C/D shortlist + the closure decisions stay auditable. Per-path headings carry the closure-state tag matching the disposition above.

### Path A — Make SCP repo public [REJECTED]

**Mechanism.** Change `jrnb2024/standards-control-plane` from private to public. Default `GITHUB_TOKEN` from any adopter context can then clone it (read-only) regardless of token scope.

**Auth-surface change.** None at the workflow layer. §12.7.10 invariant fully preserved.

**Distribution-mechanism change.** Repository visibility flip. No code change to `policy-check.yml`, no adopter wrapper change.

**Per-adopter integration cost.** Zero. Existing wrappers + SHA pins continue working unchanged.

**Risk surface.**

- Policy logic exposure — every Rego rule, every helper script, every test fixture becomes public-readable.
- Vendoring patterns + `scripts/scp-policy-check.lock` become public — attestation of SCP's supply-chain posture becomes visible to adversaries planning compromise pathways.
- Issue tracker + PR history become public — DISPATCH-NOTEs, R-cycle reviews, R1+R2 evidence trails, operator strategic decisions all surface.
- Future internal-only artefacts (e.g., proprietary domain rules that SCP authors) cannot be staged in this repo.

**Compensating considerations.**

- SCP's policy logic is already documented in public ADRs (D-001..D-049) + plan-docs + ADOPT-001 — much of the surface is *already* describable from public artefacts.
- Branch-protection + tag-protection posture defends against trust-chain attacks regardless of visibility.
- A separate `standards-control-plane-private` repo could host any future internal-only artefacts; the federation primitive lives in the public repo.

**Reversibility.** Once a private repo is made public, all historic content is permanently public (GitHub clones + caches). Effectively irreversible.

### Path B — Adopter-supplied PAT via `secrets: inherit` (inverts §12.7.10) [DROPPED — REQUIRES OPERATOR AUTHORISATION; status unchanged 2026-05-21]

**Mechanism.** Adopters configure a repo-scoped PAT with `repo:read` access on `jrnb2024/standards-control-plane`, store it as a repo secret (e.g., `SCP_FEDERATION_PAT`), and pass it to the workflow via `secrets: inherit` on the wrapper invocation. The reusable workflow declares the named secret and uses it as the `token:` parameter on the two cross-repo `actions/checkout` steps.

**Auth-surface change.** Major. Inverts §12.7.10 invariant — `secrets: inherit` adopter wrappers expose every adopter secret to SCP-controlled workflow code. Even if the reusable workflow declares only the one named secret today, future declarations would inherit silently.

**Distribution-mechanism change.** None. `policy-check.yml` continues to checkout the SCP repo cross-repo; only the token source changes.

**Per-adopter integration cost.** Material. Each adopter must (1) operator-mediated provision the PAT, (2) configure repo secret, (3) update wrapper to add `secrets: inherit`. PAT rotation becomes a cascade-wide coordination problem (every adopter must rotate when SCP's PAT-issuing identity rotates).

**Risk surface.**

- §12.7.10 forward-compat-caveat directly materialises: every future SCP version's added named secrets retroactively get every adopter's named secrets passed through.
- PAT custody — who holds the SCP-side PAT? Single-operator-mode (D-031) means @jrnb2024; this becomes a single point of failure for the entire estate's cascade.
- Per-PAT blast radius — if the PAT leaks, attacker can clone SCP regardless of repo visibility (which doesn't change under this path).

**Reversibility.** Workflow-level. Inverting the inversion is a workflow-config change + adopter wrapper update — same shape as the original change.

### Path C — GitHub App with SCP read scope, installed per-adopter [RATIFIED 2026-05-21]

**Mechanism.** Author a GitHub App `scp-federation-primitive` with `repository_permissions: { contents: read }` scoped to `jrnb2024/standards-control-plane` only. Adopters install the App on their own repos. The reusable workflow obtains an installation token via OIDC + the App's private key (held in SCP's secrets), uses that as the `token:` parameter on the cross-repo `actions/checkout` steps.

**Auth-surface change.** Smaller than Path B but non-zero. The workflow gains access to an SCP-issued installation token; that token's scope is limited to `contents: read` on the SCP repo. §12.7.10 invariant is preserved (`secrets: inherit` still NEVER); adopter named secrets are never seen by SCP code.

**Distribution-mechanism change.** Moderate. `policy-check.yml` gains an "obtain App installation token" step at the top of the cross-repo-checkout steps. SCP-side: App authoring + private-key custody. Adopter-side: App-install ceremony (one-time, via GitHub UI or API).

**Per-adopter integration cost.** Moderate. App-install is a one-time per-adopter ceremony — the wrapper itself doesn't change after install. PAT-rotation concern absent (App credentials rotate via GitHub's mechanism).

**Risk surface.**

- App's private key — SCP-side custody is a single point of failure (similar to Path B PAT, but App credentials are App-scoped, not user-scoped).
- App-install requires adopter-side org-admin access — friction at onboarding.
- OIDC + App pattern is more complex than PAT pattern — more steps to verify, more documentation to maintain in ADOPT-001 §12.7.

**Reversibility.** Workflow-level. App can be deleted or its installation revoked per-adopter; wrappers continue working (gracefully degraded — same failure mode as today, but recoverable by re-install).

### Path D — Public policy bundle via GitHub Releases [REJECTED 2026-05-21]

**Mechanism.** Pivot the federation primitive's distribution: instead of `actions/checkout` of the SCP repo at the workflow's pinned SHA, the reusable workflow downloads a public Release artefact (e.g., `scp-policy-bundle-v1.X.Y.tar.gz`) from GitHub Releases. Release artefacts are public on private repos for download-only access (no token required for public-release-asset download). The SCP repo can stay private.

**Auth-surface change.** None at the workflow layer. §12.7.10 invariant fully preserved.

**Distribution-mechanism change.** Major. SCP must publish a versioned policy-bundle Release artefact on every `v*` tag cut; the reusable workflow rewrites the cross-repo-checkout steps to download + extract the bundle. New supply-chain attestation surface — the bundle becomes the SHA-pinned distribution unit, replacing `github.workflow_sha`-anchored checkout.

**Per-adopter integration cost.** Low. Adopter wrappers continue working unchanged once the reusable workflow is updated; SHA pins become bundle-version pins (Renovate cascade adapts naturally).

**Risk surface.**

- Release-artefact publishing must be hash-attestation-verified (cosign / Sigstore) to maintain trust-rooting parity with the current checkout-at-tag-pin pattern.
- Bundle vs git-tree divergence — anything not bundled (recent CI changes, untagged commits) becomes invisible to adopters. The freshness-warning mechanism (020H.1) re-targets to bundle version comparison.
- Bundle build pipeline becomes a new failure surface — bundle authoring + publishing slice required at every release.

**Reversibility.** Major. Reverting to checkout-based distribution requires un-publishing bundles + reverting workflow + adopter Renovate-config revert.

### Path E — Public mirror repo (read-only) [DROPPED-NOT-INVOKED — escalation-eligible per §10 STEP 1]

**Mechanism.** Maintain `jrnb2024/standards-control-plane` as private (current state); auto-publish a public mirror `jrnb2024/standards-control-plane-mirror` containing only the federation-primitive surface (`policy-check.yml`, `policies/`, `schemas/`, `lib/`, `scripts/scp-policy-check.lock`, `.tool-versions`, `requirements/policy-check.txt`, `version-manifest.json`). Reusable workflow's cross-repo checkouts target the mirror; adopter wrappers point to the mirror.

**Auth-surface change.** None at the workflow layer. §12.7.10 invariant fully preserved.

**Distribution-mechanism change.** Moderate. Mirror-build pipeline (likely scheduled GH Actions cron + sync-action on tag cut) becomes a new failure surface. Adopter wrappers' `uses:` reference moves from `jrnb2024/standards-control-plane` to `jrnb2024/standards-control-plane-mirror`.

**Per-adopter integration cost.** Material at flip; zero afterwards. Every existing wrapper needs a one-time SHA + repo-name update; Renovate cascade adapts.

**Risk surface.**

- Mirror lag — if the sync pipeline fails, adopters get stale federation-primitive code. Operator-attended re-sync ceremony needed.
- Selective sync — choosing what gets mirrored is a security-policy decision (mirror everything = repo-visibility-flip equivalent; mirror selectively = same private-policy-logic posture as today).
- Two-repo split — DECISIONS.md, plan-docs, ADRs, governance content stays private; cascade-relevant content goes public. Bus-factor-1 acknowledged.

**Reversibility.** Moderate. Stop the mirror sync; adopter wrappers continue pointing at the mirror until SHA pin staleness forces a Renovate bump; coordinated cascade-wide wrapper-repo-flip-back ceremony required.

### Path F — Hybrid: public release artefact + private repo [DROPPED-NOT-INVOKED — escalation-eligible per §10 STEP 1]

**Mechanism.** Combine Path A's posture (some publicity) with Path D's distribution shape but inverted: SCP repo stays private; release artefacts (built from private source) are published to a separate public location (GitHub Releases on a public empty-source companion repo, OR a public CDN, OR PyPI-equivalent registry). Source private; artefacts public.

This is conceptually Path D + Path E combined — bundle distribution from a private source via a public artefact-host.

**Auth-surface change.** None at the workflow layer.

**Distribution-mechanism change.** Major (same as Path D) + Moderate (companion-repo or external-host coordination).

**Per-adopter integration cost.** Low (same as Path D).

**Risk surface.** Combined surface of Path D + Path E.

**Reversibility.** Major (same as Path D).

## 6. Decision points open for the 3-agent review

The orchestrator-attended plan-stage 3-agent review (sec / arch-skeptic / pragmatist lenses per `feedback_orchestrator_auth_surface_plan_review_default.md`) should converge on:

1. ~~**§12.7.10 disposition.** Preserve (paths A / C / D / E / F); invert (path B); or partially relax (path C is "limited relaxation" — App-token but not `secrets: inherit`).~~ **PARTIALLY RESOLVED 2026-05-20 PM by §5.0 shortlist confirmation:** §12.7.10 preserved across the A/C/D primary shortlist (Path A preserves at workflow layer via repo-public; Path C partially relaxes via App-token without `secrets: inherit`; Path D preserves via release-artefact distribution that avoids cross-repo checkout entirely). Path B (the only invariant-inverting option) is dropped from the shortlist; re-opening requires explicit operator authorisation per §10 STEP 2. The 3-agent review need not re-litigate the §12.7.10 disposition; that's now scoped to "A/C/D-preserving as-spec" only.
2. **Distribution-mechanism choice.** Checkout-of-source (A, C) vs release-artefact-download (D). Remains open — A and C keep checkout-of-source; D pivots to release-artefact. The review's primary architectural call.
3. **Reversibility tolerance.** Path A (repo public) is effectively irreversible; C and D are reversible at workflow-level / architectural-pivot-level cost respectively. How much irreversibility does the estate tolerate for the auth-surface property?
4. **PAT/App custody disposition (Path C only on shortlist).** Single-operator-mode (D-031) means @jrnb2024 holds the App credential; what's the bus-factor mitigation? (Was originally "paths B / C only" pre-shortlist; B is dropped so the disposition narrows to C alone.)
5. **Adopter-onboarding cost vs SCP-side cost.** Path A pushes cost to SCP (visibility decision); Path C pushes cost to adopters at App-install flip; Path D pushes cost to SCP (release-build pipeline). How does the cohort-of-5 weigh adopter-side vs SCP-side cost?
6. **Sequencing relative to v1.3.0 release.** Can TF-PIM-001 fix land within v1.3.0 (so v1.3.0 ships SCP-R-005 AND a working external-adopter path simultaneously), or does TF-PIM-001 require its own dedicated release cut?
7. ~~**Compensating control for §12.7.10 inversion (path B only).** If path B is selected, what compensates for the broken invariant 2?~~ **N/A under A/C/D shortlist.** Restored from N/A only if §10 STEP 2 fires (Path B re-opened with explicit operator authorisation); compensating control becomes load-bearing then.

The 3-agent review's output is a recommended fix-path from `{A, C, D}` with the remaining decision points (2-6 above) resolved. Operator ratifies on dispatch sign-off; ratified output is folded into a D-NNN ADR if any of paths A / C / D is chosen (each touches federation-primitive architectural invariants — visibility for A, App credential surface for C, distribution mechanism for D).

## 7. Acceptance criteria — what "TF-PIM-001 closed" means

Five criteria, all required:

1. **At least one external adopter runs the federation-primitive wrapper cross-repo end-to-end green** (PIM is the natural candidate; any cohort adopter qualifies). Evidence: a successful GitHub Actions run URL with all 12 policy-check steps COMPLETED green on an adopter PR.
2. **PIM `main`'s `policy-check / scp/policy-check` required-check restored.** The 2026-05-19 operator-attended relaxation reverses. Evidence: `gh api repos/mapp-pim/mapp-pim/branches/main/protection --jq '.required_status_checks.contexts'` returns the set containing `"policy-check / scp/policy-check"`.
3. **`docs/adoption/ADOPT-001-project-onboarding.md` updated.** Under the A/C/D shortlist, §12.7.10 is reaffirmed (all three primary paths preserve the invariant); §12.7.1 wrapper template updated for the chosen path; integration-cost guidance updated. *(If §10 STEP 2 escalation fires and Path B re-opens, §12.7.10 amended instead of reaffirmed.)*
4. **Ratifying D-NNN ADR filed** if the chosen path is A, C, or D (each touches federation-primitive architectural invariants — visibility decision for A, App credential surface for C, distribution mechanism for D). Path A specifically requires an ADR for the visibility decision given its effective irreversibility.
5. **R1-evidence-on-fix-PR satisfies cardinal-rule-2 3-lens.** Per `feedback_r1_surface_must_cite_ci.md`, the fix PR carries a 3-lens R1 block + CI citation pair on merge.

## 8. Dependencies + sequencing

**Blocks (downstream of TF-PIM-001 closing):**

- Every external WP-SCP-024 cascade slice past 024C (024D–024G).
- D-049 §Sequencing step 2 onward — first non-SCP adopter exercising the federation primitive cross-repo green is the artefact-gate the §Sequencing block depends on. SCP-R-005 v1.3.0 ship is **independent** in the codebase (rule + dogfood land regardless), but D-049's adopter-cascade outcome depends on TF-PIM-001.
- `FUP-WP-SCP-024-SCAFFOLDER-V1.2-INCOMPAT-001` (P1) — currently blocked by TF-PIM-001 per BACKLOG row.

**Does NOT block:**

- v1.3.0 release authoring (SCP-R-005.rego + scp_common helpers + schema extension + workflow narrow-glob materialisation). v1.3.0 can ship before TF-PIM-001 closes; the rule's adopter consumption is what's gated, not the rule's existence in the codebase.
- DECISIONS.md D-049 status flip DRAFT → ACCEPTED (small bookkeeping commit; can ride along with any near-term commit).

**Order of operations (if path C or D chosen — i.e., any path that touches federation-primitive code):**

1. Plan-doc + 3-agent review (this work) → operator ratification on dispatch sign-off
2. D-NNN ADR drafting + operator-review surface
3. ADR merge → ratified
4. Implementation slice (workflow changes + ADOPT-001 §12.7 updates)
5. SCP-self dogfood verification (selftest workflow exercises the new path)
6. External-adopter cross-repo verification (PIM canary on a new PR)
7. PIM `main` required-check restoration
8. STATUS row + TF-PIM-001 closure

**Order of operations (if path A chosen — repo public):**

1. Plan-doc + 3-agent review → operator ratification
2. D-NNN ADR for the visibility decision (irreversibility makes ratification mandatory) — operator-review surface
3. ADR merge → ratified
4. Repo visibility flip (one-line operator-attended op via GitHub UI or `gh repo edit`)
5. External-adopter cross-repo verification (no SCP code change needed; existing wrapper SHA pin should resolve naturally on next adopter PR)
6. PIM `main` required-check restoration
7. STATUS row + TF-PIM-001 closure

## 9. Plan-stage 3-agent review invocation discipline

Per `feedback_orchestrator_auth_surface_plan_review_default.md`, this work warrants the **orchestrator-attended** review pattern, not the standard dispatch-package 3× parallel Sonnet R1+R2.

Suggested invocation shape (operator-paced; this plan-doc does **not** self-dispatch):

- **Lens 1 — sec.** Threat-model coverage: does the chosen path preserve invariants 1-5 (§4 above)? Where does it relax, and what compensates? `gh attestation verify` parity preserved? Tag-protection trust-rooting preserved? Branch-protection-log audit-trail preserved?
- **Lens 2 — arch-skeptic.** Federation primitive's distribution architecture: does the chosen path introduce a new failure surface that's worse than the failure it removes? Reversibility analysis — what's the cost of un-doing this in 6 months if the choice turns out wrong?
- **Lens 3 — pragmatist.** Cascade-onboarding cost analysis: does the chosen path's per-adopter integration cost outweigh its benefit for the 5-adopter cohort (PIM + CT + MDA + Recommender + shopify-app)? What does Renovate-cascade adaptation look like? What's the v1.3.0 sequencing implication?

Each lens reviews this plan-doc + the federation-primitive code surface (`.github/workflows/policy-check.yml` + ADOPT-001 §12.7 + WP-SCP-020 plan-doc §3) + the existing D-NNN context (D-030 + D-031 + D-034 + D-036 + D-049 + ADR-016).

Each lens produces a structured output: recommended path + ratified-decision-points + identified-risk-surface + tracked-forward items. Operator-attended convergence of the three outputs is the dispatch sign-off.

## 10. Escalation path if A/C/D shortlist exhausted

The 3-agent review's ratification target is ONE of `{A, C, D}`. If review convergence determines that none of A/C/D clears the acceptance bar (e.g., A irreversibility-cost too high AND C App-custody-cost too high AND D distribution-pivot-cost too high), the natural escalation is:

**STEP 1.** Re-open shortlist with E + F added (still invariant-preserving). Fresh 3-agent review of `{A, C, D, E, F}`. Operator authorisation NOT required for this step (still within the invariant-preserving family — §12.7.10 stays preserved across all five paths). The plan-doc amend at the end of this STEP rewrites §5.0 disposition + per-path tags to reflect the broader shortlist; the existing rationale text under §5 paths E and F (preserved verbatim) supplies the comparative analysis.

**STEP 2.** If STEP 1 also exhausts without convergence, re-open Path B for consideration. Requires **EXPLICIT operator authorisation** to ratify §12.7.10 inversion BEFORE Path B enters the review surface. Operator-attended architectural-scope decision (treat as ASC-class — the §12.7.10 inversion is a load-bearing federation-primitive invariant change, not a routine implementation pattern). The operator authorisation surface should capture: (a) which constraint forces the inversion (since A/C/D + E/F all failed); (b) what compensating control replaces invariant 2 (`secrets: inherit` prohibition); (c) PAT custody plan under D-031 single-operator-mode bus-factor; (d) forward-compat-caveat mitigation — what prevents the next SCP version's added named secrets from retroactively passing every adopter's secret through.

This staged escalation preserves the load-bearing invariant for as long as architecturally possible without forcing a re-derive from review output. Future-session orchestrators picking up post-review work read this section directly rather than reconstructing the escalation logic from review-evidence prose.

**Escalation guardrail.** The escalation is one-directional: A/C/D → {A,C,D,E,F} → {A,C,D,E,F,B}. Closing a path once-attempted does NOT re-open the previous shortlist; if a path is ratified at any STEP, the escalation stops. If the operator wants to revisit a closed-with-rationale path mid-escalation, that requires fresh authorisation outside the staged sequence.

## 11. Cross-references

- **3-agent review evidence** (orchestrator-attended; landed via PR #130 at `747e2ad`):
  - `docs/reviews/TF-PIM-001/shortlist-A-C-D/sec-lens-r1.md` — sec lens Strong C
  - `docs/reviews/TF-PIM-001/shortlist-A-C-D/arch-skeptic-lens-r1.md` — arch-skeptic lens Strong C
  - `docs/reviews/TF-PIM-001/shortlist-A-C-D/pragmatist-lens-r1.md` — pragmatist lens Strong A
  - `docs/reviews/TF-PIM-001/shortlist-A-C-D/synthesis.md` — non-convergent synthesis + three operator convergence options (operator chose option 1 = Ratify Path C)
- **Implementation WP plan-doc (Path C scope)** — `docs/plans/TF-PIM-001-impl-path-c-app-credential.md` (separate plan-doc; authored post-ratification with CT-style template + 3-lens R1 from R1 + R-cycle to R-fixpoint MET)
- `docs/BACKLOG.md` Phase 12 → **TF-PIM-001** (this plan-doc's origin row)
- `docs/decisions/D-049-design-system-policy-layer-adoption-2026-05-19.md` §Sequencing — adopter cascade consumption gating
- `docs/adoption/ADOPT-001-project-onboarding.md` §12.7 (federation primitive adopter integration) + §12.7.10 (NEVER use `secrets: inherit`) + §12.7.13 (supply-chain posture)
- `docs/plans/WP-SCP-020-policy-federation-primitive.md` §3 (federation-primitive invariants)
- `docs/plans/WP-SCP-022-implementation-programme-plan.md` §4.4 (workflow-integration invariants)
- `docs/plans/WP-SCP-024-estate-cascade.md` (cascade plan; this plan-doc's downstream consumers)
- `.github/workflows/policy-check.yml` lines 92 / 107 / 1149 (the three checkout sites)
- `docs/DECISIONS.md` rows D-030 (tag-protection), D-031 (single-operator-mode), D-034 (Renovate cascade tag-protection), D-036 (rule-RFC + versioning), D-045 (PIM cascade close)
- Cross-tree memory:
  - `~/.claude/projects/-Users-amplience-Projects/memory/feedback_orchestrator_auth_surface_plan_review_default.md` — the mandate for orchestrator-attended review on auth-surface deviation
  - `~/.claude/projects/-Users-amplience-Projects/memory/feedback_artefact_gates_not_time_bakes.md` — the artefact-gate discipline applied at §7 acceptance criteria item 1

## 12. Tracked-forward items (not blocking this plan-doc)

- ~~**TF-PIM-001-PLAN-001 — Choose fix path.**~~ **CLOSED 2026-05-21 — Path C ratified.** Output of the 3-agent review + operator-attended convergence on the non-convergent 2-1 split. Evidence files cited in §11.
- ~~**TF-PIM-001-PLAN-002 — File D-NNN ADR.**~~ **OPEN — inherits to impl WP plan-doc.** Required for Path C per plan-doc §7 acceptance criterion 4. Drafted alongside the implementation WP plan-doc (`docs/plans/TF-PIM-001-impl-path-c-app-credential.md` — separate plan-doc per CT-style template).
- ~~**TF-PIM-001-PLAN-003 — Implementation slice scope.**~~ **CLOSED 2026-05-21 — Path C single slice.** Single slice covering: GitHub App authoring + workflow change (token-source on cross-repo `actions/checkout` steps) + ADOPT-001 §12.7 update (App-install ceremony + de-adoption update + supply-chain section). Authored in the impl WP plan-doc.
- **TF-PIM-001-PLAN-004 — PIM required-check restoration ceremony.** OPEN. Operator-attended; runs after external-adopter verification green per Path C order-of-operations.
- ~~**TF-PIM-001-PLAN-005 — Cohort-wide adopter wrapper updates.**~~ **NOT APPLICABLE under Path C** — Path C does not require adopter-side wrapper changes; per-adopter App-install ceremony is a separate one-time onboarding step (TF-PIM-001-SEC-004 + TF-PIM-001-ARCH-003 from evidence files). Close as N/A-UNDER-RATIFIED-PATH.

---

**End of plan-doc.** Status flipped from DRAFT → CLOSED-WITH-RATIFIED-PATH on 2026-05-21 (operator-attended convergence: Path C ratified post 3-agent review). Implementation WP plan-doc (`docs/plans/TF-PIM-001-impl-path-c-app-credential.md`) carries forward the Path C scope + 10 TF-PIM-001-{SEC,ARCH}-* tracked-forward items + the D-NNN ADR drafting (TF-PIM-001-PLAN-002 inherited).
