# TF-PIM-001 — pragmatist lens R1 review (A/C/D shortlist)

**Dispatched:** 2026-05-20 PM after PR #128 merge at `f137403`
**Agent type:** Plan (read-only; DO-NOT-EDIT mandate)
**Model:** Sonnet
**Worktree isolation:** yes
**Lens domain:** cascade-onboarding-cost + v1.3.0 sequencing + cohort-of-5 feasibility

---

## Lens: pragmatist

### Recommended path
**A**

### Why this path under the pragmatist lens

Path A is the correct choice for a cohort-of-5 executing against a tight v1.3.0 release window with one adopter already waiting on required-check restoration. The entire argument for A pivots on two facts: zero adopter-side integration cost, and a minimal SCP-side ceremony (one `gh repo edit` invocation + one D-NNN ADR merge). The plan-doc §5 Path A entry is unambiguous: "Per-adopter integration cost. Zero. Existing wrappers + SHA pins continue working unchanged." The `renovate/default.json` custom manager regex (`matchPackageNames: ["jrnb2024/standards-control-plane-"]`) already resolves correctly against a public repo; it requires no modification. The wrapper template at ADOPT-001 §12.7.1 requires no modification. The branch-protection setup (§12.7.3) requires no modification. The scaffolder output (`scripts/scaffold-downstream.sh`) requires no modification. For all five cohort adopters — PIM, CT, MDA, Recommender, shopify-app — every SCP artefact they currently hold (or would receive at onboarding) works unchanged the moment the repo flips public. That is a property no other path on the shortlist delivers.

The v1.3.0 release sequencing argument closes the case. D-049 §Sequencing item 1 commits: "v1.3.0 ships with SCP-R-005 at warn, self-dogfood only." TF-PIM-001 is the artefact-gate on adopter-side SCP-R-005 consumption — not a v1.3.0 ship blocker. But PIM's degraded `main` required-check state IS a load-bearing operational drag: every PIM PR is running without `policy-check / scp/policy-check` as a required gate, weakening the cascade-status: onboarded invariant established at PR #118. The faster TF-PIM-001 closes, the sooner the v1.3.0 release can go out carrying both the new rule AND a demonstrably working external-adopter path. Under Path A, the implementation sequence (plan-doc §8, path A order-of-operations) is: ADR merge → repo visibility flip → external-adopter cross-repo verification → PIM required-check restoration → STATUS closure. That sequence is 2–3 operator-attended steps, none of which require code change, none of which require per-adopter ceremony. Under Path C or D, the equivalent sequence requires code change to `policy-check.yml` + ADOPT-001 §12.7 rewrite + per-adopter App-install ceremony (C) or release-pipeline build work + Renovate preset adaptation (D). Path A's gap to a closed TF-PIM-001 is measured in hours; Path C or D is measured in days to weeks.

The one genuine cost of Path A — effective irreversibility after repo publication — is load-bearing but is not a pragmatist-domain concern at this stage. The plan-doc §5 Path A risk surface identifies four items: policy logic exposure, supply-chain attestation visibility, issue tracker surfacing, and inability to stage future internal-only artefacts in this repo. All four are real. But they are not cascade-onboarding-cost concerns; they are security and architecture concerns correctly owned by the sec and arch-skeptic lenses. From the pragmatist lane: SCP's public artefacts (D-001..D-049, ADOPT-001, WP-SCP-020..024 plan-docs, WP-SCP-020 invariants) already describe the policy logic surface to any motivated reader. The marginal exposure from making the repo public is lower than its description suggests, and the plan-doc §5 itself offers a compensating consideration: a future `standards-control-plane-private` repo can stage any genuinely internal-only artefacts. That compensating move is available; it does not need to happen before the TF-PIM-001 fix lands.

### Per-adopter integration cost across cohort-of-5

Under Path A, all integration cost is SCP-side and one-time. The per-adopter cost is zero in every case.

- **PIM (`jrnb2024/mapp-pim`)** — cascade-status: onboarded at PR #118; `policy-check / scp/policy-check` currently NOT required on `main` (2026-05-19 relaxation). Under Path A: no wrapper change, no Renovate config change, no App install. Terminal action is operator-attended required-check restoration (TF-PIM-001-PLAN-004 ceremony, ~5 minutes via `gh api`). Integration cost: zero. PIM unblocks immediately on repo flip.
- **CT (`control-tower`)** — next cascade slice (024D), not yet onboarded. Matrix-UI work in flight per D-049. Under Path A: existing scaffolder output works unchanged on first run post-flip. `--preserve-existing-contexts` flag already documented in ADOPT-001 §12.7.3 brownfield section. Integration cost: zero. CT's in-flight UI work is not disrupted; the cascade slice opens and closes on the same ceremony as 024C.
- **MDA (`mapp-doc-agent`)** — minimal frontend; cascade paired with Recommender. Under Path A: same scaffolder output, same wrapper template, no App install. Integration cost: zero.
- **Recommender** — D-049 D3 first deny-gate target; DPBM-scoped adoption is post-TF-PIM-001 per D-049 §Sequencing. The TF-PIM-001 fix is what unlocks Recommender's adoption of SCP-R-005. Under Path A the unblock happens immediately; under C or D it is deferred by the implementation gap. Integration cost: zero.
- **shopify-app** — SA-011 visual migration closed 2026-05-20 (per STATUS.md 2026-05-20 PM chain, SA-011 context); future deny-gate #3 per D-049. Under Path A: same scaffolder output. Integration cost: zero.

### Renovate-cascade adaptation under this path

The `renovate/default.json` requires no changes under Path A. The `customManagers` regex at line 46 matches on `jrnb2024/standards-control-plane-` as a datasource; it resolves against GitHub's tags API which is public-scope-accessible regardless of repo visibility. The `matchPackageNames` entry matches the same repo name. The preset is published at `renovate/v1.0.0` (protected by the `scp-tag-protection-renovate-v` ruleset per D-034); tag-protection is visibility-independent.

Per adopter: the `renovate.json` extension snippet at ADOPT-001 §12.7.2 (`"github>jrnb2024/standards-control-plane-//renovate/default#renovate/v1.0.0"`) resolves correctly against a public repo without any adopter-side change. The wrapper marker comment (`# renovate: datasource=github-tags depName=jrnb2024/standards-control-plane-`) and the `# tag: v1.0.0` annotation are already present in scaffolded wrappers. Renovate will continue issuing SHA-pin-bump PRs on every SCP release exactly as before.

This is a clean no-change adaptation. Under Path D, the Renovate preset would need significant rewriting: the custom manager regex targets `uses: jrnb2024/standards-control-plane-/.github/workflows/policy-check.yml@<SHA>` lines, not a release-artefact download URL. The `datasourceTemplate: "github-tags"` maps to tag-based resolution, not release-asset resolution. Adapting the preset for D would require a new `customManagers` regex targeting the bundle-download URL pattern, a new `datasource` (`github-releases` or equivalent), and a per-adopter `renovate.json` update to pick up the new preset shape — material per-adopter friction for all five cohort members. Path C is Renovate-neutral on the preset itself but requires per-adopter App-install before the Renovate bump cycle can succeed.

### v1.3.0 sequencing under this path

Path A enables TF-PIM-001 to close WITHIN the v1.3.0 release window. The order of operations under Path A (plan-doc §8):

1. Plan-doc + 3-agent review (this work) — complete at review dispatch sign-off (today).
2. D-NNN ADR drafting + operator review — 1 session.
3. ADR merge + ratified.
4. Repo visibility flip — operator-attended, ~5 minutes (`gh repo edit jrnb2024/standards-control-plane- --visibility public`).
5. External-adopter cross-repo verification — PIM opens a PR, the SCP workflow runs green with existing SHA pin, all 12 policy-check steps complete. No code change on either side.
6. PIM `main` required-check restoration.
7. STATUS row + TF-PIM-001 closure.

Total elapsed from sign-off to closed: 1–2 sessions. v1.3.0 carries SCP-R-005 (per D-049 §Sequencing item 1) and TF-PIM-001 closes simultaneously or just after, allowing Recommender to begin its D-049-gated adoption sequence as D-049 §Sequencing item 3 specifies: "TF-PIM-001 closes — cross-repo checkout auth resolved; first external adopter runs the wrapper cross-repo green."

Under Path C: ADR + App authoring + `policy-check.yml` workflow changes + ADOPT-001 §12.7 rewrite + per-adopter App-install ceremony (requiring adopter org-admin access per plan-doc §5 Path C). Minimum 3–4 sessions; realistically 1–2 weeks given the review protocol (3-lens R1+R2 fixpoint required on the workflow change per WP-SCP-022 dispatch protocol). TF-PIM-001 does not close before v1.3.0 without compressing the protocol.

Under Path D: ADR + release-bundle pipeline authoring + workflow rewrite + Renovate preset rewrite + per-adopter Renovate config adaptation. The plan-doc §8 Path C/D order-of-operations lists 8 steps including "SCP-self dogfood verification" and "External-adopter cross-repo verification" after multiple rounds of code change. Multi-session, multi-week. TF-PIM-001 is definitely post-v1.3.0 under D.

**Conclusion:** Path A is the only shortlist member that allows TF-PIM-001 to close within the v1.3.0 release-cut window.

### PIM main required-check restoration timeline under this path

From "path ratified" to "PIM `main` has `policy-check / scp/policy-check` re-required":

1. Operator ratifies Path A at dispatch sign-off. (0 minutes)
2. ADR drafted, reviewed, merged. (1 session — estimate 2–4 hours of operator-attended work)
3. `gh repo edit jrnb2024/standards-control-plane- --visibility public` executed. (5 minutes operator-attended)
4. PIM: operator opens or re-runs an existing PR; SCP workflow runs cross-repo with existing `@41a5299` pin; all 12 policy-check steps complete green. Evidence: successful GitHub Actions run URL. (Time for CI run: ~45–60 seconds per §12.7.12)
5. Operator runs the TF-PIM-001-PLAN-004 ceremony: `gh api repos/jrnb2024/mapp-pim/branches/main/protection` PUT restoring `policy-check / scp/policy-check` to the required contexts list. Verification: `gh api repos/jrnb2024/mapp-pim/branches/main/protection --jq '.required_status_checks.contexts'` returns set containing `"policy-check / scp/policy-check"`. (10 minutes operator-attended)

**Estimated wall-clock: 1 operator session (2–4 hours total, dominated by ADR review, not the technical steps).** The degraded state — PIM `main` without a required policy-check gate — has been open since 2026-05-19. Under Path A it closes in one session post-ratification. Under Paths C or D it remains open for weeks.

### Risk surface accepted under this recommendation

1. **Effective irreversibility of repo visibility.** Once public, all historical content (commits, issues, PR discussions, DISPATCH-NOTEs, R-cycle evidence, operator strategic decisions, plan-docs including this one) is permanently accessible via GitHub caches and third-party clones. Rolling back the visibility flip does not unring the bell. This is the plan-doc's stated primary risk under Path A and is the strongest argument for C or D. Accepted here because the marginal exposure is evaluated as lower than its description: the public ADRs (D-001..D-049) already describe SCP's architecture, invariant set, and policy logic to any motivated reader; the Rego rules themselves are the low-value half of the exposure (the supply-chain posture, the attack surface analysis in WP-SCP-020 §3, is more sensitive and is already in public plan-docs).
2. **Issue tracker + PR history exposure.** DISPATCH-NOTEs, R-cycle review archives, cross-session context documentation, and operator strategic discussions become public. This is real operational surface exposure. Accepted because the alternative (Path C or D) carries an extended PIM degradation window that is itself a concrete operational risk.
3. **Future internal-only artefact staging forecloses.** If SCP later needs to author proprietary domain rules or non-public policy logic, this repo cannot host them. The compensating move (a separate `standards-control-plane-private` repo) is available but requires a future operator-attended org-setup step. Accepted as a forward-compat cost, not a current-state blocker.
4. **No PAT rotation problem (avoided).** Path A avoids the Path C App-credential bus-factor risk (D-031 single-operator-mode; @jrnb2024 holds the App private key) and the Path D release-pipeline new-failure-surface risk. These risks are not accepted — they are absent under Path A.

### Decision points (from plan-doc §6) resolved by this recommendation

- **Decision point 2 (Distribution-mechanism choice):** Resolved as checkout-of-source. Path A retains the existing checkout-based distribution; no pivot to release-artefact download (D) is required.
- **Decision point 3 (Reversibility tolerance):** Resolved as "accepts effective irreversibility" for Path A. The estate tolerates the irreversible repo-public flip given the zero per-adopter cost and the minimal SCP-side ceremony. The pragmatist lens holds that the reversibility cost is a future-session concern; the PIM degradation cost is a current-session operational burden.
- **Decision point 4 (PAT/App custody — Path C only):** Resolved as N/A. Path A does not introduce App credential custody risk; the D-031 single-operator-mode bus-factor concern on App credentials is avoided entirely.
- **Decision point 5 (Adopter-onboarding cost vs SCP-side cost):** Resolved definitively. Per-adopter cost under Path A = zero across all five cohort members. SCP-side cost = one ADR session + one `gh repo edit` invocation + one verification run. The cohort-of-5 asymmetry favours pushing cost to SCP-side when the SCP-side cost is this small. Path C's App-install ceremony (per-adopter, requires org-admin access per §5 Path C) multiplied across 5 adopters is larger than Path A's one-time visibility flip. Path D's Renovate-preset rewrite + release-pipeline build + per-adopter Renovate config adaptation is larger still.
- **Decision point 6 (Sequencing relative to v1.3.0):** Resolved as "TF-PIM-001 closes within v1.3.0 window." Path A is the only shortlist member that achieves this without compressing the review protocol. Under C or D, TF-PIM-001 is post-v1.3.0.

### Tracked-forward items this recommendation generates

- **TF-PIM-001-PRAG-001 — D-NNN ADR for repo-public visibility decision — mandatory pre-flip gate.** The plan-doc §7 acceptance criterion 4 requires a ratifying ADR for Path A. The ADR must capture: (a) the effective-irreversibility acknowledgement; (b) the compensating-control posture (branch-protection + tag-protection defends trust-chain regardless of visibility; future internal artefacts route via a separate `standards-control-plane-private` repo); (c) operator-authorised sign-off. This TF gates the `gh repo edit` invocation — no visibility flip without a merged ADR.
- **TF-PIM-001-PRAG-002 — PIM required-check restoration ceremony execution (TF-PIM-001-PLAN-004 operationalisation).** Operator runs `enable-required-check.sh --preserve-existing-contexts` against `jrnb2024/mapp-pim` `main` after cross-repo verification green. Re-adds `policy-check / scp/policy-check` to the required contexts. Invocation log entry written to `docs/reviews/WP-SCP-020/branch-protection-log.md`. Close condition: `gh api repos/jrnb2024/mapp-pim/branches/main/protection --jq '.required_status_checks.contexts'` returns set containing `"policy-check / scp/policy-check"`.
- **TF-PIM-001-PRAG-003 — FUP-WP-SCP-024-SCAFFOLDER-V1.2-INCOMPAT-001 unblock signal.** The scaffolder incompatibility (BACKLOG Phase 12, P1) is currently blocked by TF-PIM-001 ("without cross-repo auth, scaffolder output can't run anyway"). Under Path A, the unblock is automatic: once the repo is public, the scaffolder can be verified against a real adopter run. Operationalise the FUP unblock: after TF-PIM-001 closes, re-run the scaffolder against a test adopter to verify the `with: scorecard-emit: false` removal (path (a) from the BACKLOG row) is working. File a separate implementation slice for the scaffolder fix if not already resolved at TF-PIM-001 close.
- **TF-PIM-001-PRAG-004 — Issue tracker triage before flip.** Before executing the visibility flip, operator audits open issues + PR history for any content that must NOT be public (e.g., references to non-public external accounts, vendor-negotiation context, internal cost data). Close condition: operator-signed "nothing materially sensitive in issue/PR history" attestation, captured in the D-NNN ADR body or as a checklist item in the flip-ceremony runbook.

### Convergence signal
**Strong A**
