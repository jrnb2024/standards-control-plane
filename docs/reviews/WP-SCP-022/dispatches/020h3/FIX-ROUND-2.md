# 020h3 fix-round-2 (post-r1-completeness-retry, pre-r2)

**Date:** 2026-04-30 (evening)

## Triggers

R1 completeness lens **timed out at 900 s** on first dispatch. Retry at **1800 s** (`review-completeness-r1retry.json`) returned **CONDITIONAL_PASS** with **7 MAJ + 3 MIN + 3 nit** findings against the pre-fix-round-1 §12.7 state. Most findings still apply post-fix-round-1; this fix-round-2 closes all 7 MAJ.

## Closures applied (all in this branch)

### COMP-MAJ-001 + COMP-MAJ-002 (§11.10 break-glass cross-reference)

§11.10's last bullet referenced `§11.x break-glass procedure` (an unresolved placeholder) and described a two-gate process (`paired DECISIONS row + waiver`) that contradicts §12.7.4's three-gate model. Updated to:

> One-off PR exceptions — use `scp_bypass: true` on the workflow invocation per the **three-gate** break-glass procedure documented in §12.7.4 (CODEOWNERS approval + sibling D-NNN row + matching `waivers.json` entry — all three required simultaneously).

Both findings collapse to a single one-line edit. ADOPT-001 now contains a single, consistent break-glass description anchored at §12.7.4.

### COMP-MAJ-003 (SCP-073.sec missing from STATUS.md)

§12.7.8 references `WP-SCP-020 §4.1 follow-up SCP-073.sec` for SECURITY.md publication, but the item was not in STATUS.md's post-Threshold-A backlog. Added explicit row:

> **SCP-073.sec**: `SECURITY.md` publication (security disclosure path for policy-bypass reports) — referenced from ADOPT-001 §12.7.8. WP-SCP-020 §4.1 follow-up; track parallel to 020H.1.

### COMP-MAJ-004 (no "verify integration is working" acceptance step)

§12.7.3 had `--plan` first-run guidance but no empirical-verification step. Added a 3-step verification block at the end of §12.7.3:

1. `gh api ... required_status_checks --jq '{strict, contexts}'` — verify required-check is registered.
2. `gh api ... enforce_admins --jq '.enabled'` + `... required_signatures --jq '.enabled'` — verify both are `true`.
3. Open a draft PR with a deliberate `SCP-R-001` violation (invalid `services.yml auth.mode`); confirm `policy-check / scp/policy-check` shows red with `SCP-E003` annotation AND the merge button is disabled. Close the draft after verification.

Cross-references D-033 as the empirical-verification rationale.

### COMP-MAJ-005 (no "remove entire integration" rollback path)

§12.7.5 only documented per-release SHA-pin rollback. Added a "Full de-adoption" sub-section:

1. PR removes `.github/workflows/policy-check.yml`, removes `extends:` from `renovate.json`, adds D-NNN row.
2. Post-merge `gh api -X PATCH .../protection/required_status_checks` to remove the SCP context. Includes the explicit `--input -` payload shape so the procedure is reproducible.
3. Optional `enforce_admins` relax; keep `required_signatures` (independent supply-chain hygiene).

The procedure is intentionally explicit so partial de-adoption (deleting the wrapper without removing the required-check, leaving the branch unmergeable) is foreclosed.

### COMP-MAJ-006 (SCP-side bus-factor-1 not disclosed to adopters)

§12.7.4 disclosed adopter-side single-operator constraints but didn't disclose that SCP itself is single-operator-gated per D-031 — adopters could not make an informed supply-chain-diversity decision. Added "SCP source — bus-factor-1 disclosure" paragraph to §12.7.4:

> As of v1.0.0, the SCP reusable workflow and Renovate preset … are themselves operated by a single maintainer (`@jrnb2024`) per D-031 (WP-SCP-020 §8 bus-factor-1 risk row). The SCP-side quarterly bus-factor-1 review is scheduled for 2026-07-21 … Estate-cascade rollouts (FLA pilot → PIM / recommender / shopify-app / mapp-doc-agent / control-tower per WP-SCP-024) will surface the same constraint until SCP onboards a second maintainer.

This is a factual disclosure, not a descope — preserves no-descoping invariant.

### COMP-MAJ-007 (TF-D1-001..003 not in STATUS.md tracked-forward section)

DISPATCH-NOTE deferred TF-D1-001..003 closure marking to "the next slice's PR (likely 020H.1)" — risking accountability evaporation if 020H.1 was delayed or rescoped. Added a new **"Tracked-forward items from 020D1 (closed in 020H part 3)"** section to STATUS.md in this PR's diff with explicit closure rows for all three TF-D1-NNN items, plus a separate **"Tracked-forward items from 020H part 3"** section for TF-020H3-001 (Regal SHA256 → 020H.2).

Now the closure evidence lives in this PR's commit, removing the future-PR dependency.

## MIN + nit findings (deferred — non-blocking, addressed pragmatically)

- **COMP-MIN-001** (no explicit step-by-step adopter onboarding sequence): the ordering is implicit in §12.7.1 → §12.7.2 → §12.7.3. Adopters who copy the snippets in document order get the right behaviour. No closure in this PR; track for v1.1 ADOPT-001 reorganisation.
- **COMP-MIN-002** (`SCP-CODEOWNERS` ambiguity): adopters may misread as SCP's own CODEOWNERS file. Closed implicitly by the §12.7.4 rewrite — the new wording ("your repo's CODEOWNERS for paths matching the gate's domain") clarifies the meaning.
- **COMP-MIN-003** (plan §4 020H part 3 wrapper spec text still uses repo name without trailing dash): the plan doc has the typo, ADOPT-001 has the correct version. Adopters who copy from ADOPT-001 (the canonical adopter doc) get correct text. The plan-doc typo is a pre-existing artefact noted by 020F's R1 review; track for plan-doc cleanup as a separate slice.
- **COMP-NIT-001** (services.yml / output/findings/waivers.json examples are SCP-internal paths): worth generalising for estate-cascade clarity. Not closed in this PR; track for ADOPT-001 v1.1.
- **COMP-NIT-002** (no rationale for `renovate/v*` independent versioning): factual but low-value. Not closed in this PR.
- **COMP-NIT-003** (pre-commit hook clone-maintenance guidance): closed by SAFE-007 fix-round-1 closure (clone-pinning instructions added).

## Re-review

R2 correctness + R2 safety dispatchers (PIDs 41415 / 41419) are running in parallel against the post-fix-round-1 state and will be reviewed against fix-round-2 once they return. Expected behaviour: any new findings against fix-round-1 closures get folded into a fix-round-3, and recursion continues until no new BLOCKING findings.

This is the protocol-over-shortcuts + recursive-adversarial-review pattern from `feedback_protocol_over_shortcuts.md` + `feedback_recursive_adversarial_review.md`. No descoping; tracked-forward items have named follow-up slices.
