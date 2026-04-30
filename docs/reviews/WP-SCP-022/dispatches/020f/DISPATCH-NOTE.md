# WP-SCP-022 slice 020F — dispatch note

**Date:** 2026-04-30
**Tier:** orchestrator-applied (Tier 1 only)

## Justification for not invoking Codex executor

Per `feedback_four_tier_dispatch.md` in-line escalation guidance.
Slice 020F's substantive surface is **three small config files**:

- `renovate/default.json` (~50 lines, schema-validated JSON)
- `renovate.json` (~10 lines, self-consumer)
- `.github/dependabot.yml` extension (~40 lines)

No code paths, no Rego, no schema-shape changes, no workflow YAML
authoring. Renovate's preset/customManager schema is a constrained
configuration surface; the orchestrator-applied Tier-1 path is
appropriate.

Codex Tier 4 (`gpt-5.3-codex-spark`) "boilerplate / fixtures /
CI YAML" would be the right tier IF dispatching. Dispatch overhead
(work-package authoring + dispatcher round-trip) exceeds authoring
cost for ~100 lines of constrained-syntax config.

## Slice acceptance per WP-SCP-020 §4 020F

- [x] **(i)** Preset exported via
  `github>jrnb2024/standards-control-plane-//renovate/default#<tag>`
  (config user calls in their own `renovate.json` `extends`).
  Verified by SCP-self consuming the preset (vi).
- [x] **(ii)** Regex-manager bumps wrapper's `@SHA` + `# tag:` comment
  together (`customManagers[0]` matches the canonical adopter
  marker pattern `# renovate: ... uses: ...@<SHA> # tag: <semver>`;
  `currentDigest` capture group + `currentValue` capture group both
  named so Renovate updates both fields atomically).
- [ ] **(iii)** Preset versioned with own tag series — POST-MERGE
  step. `renovate/v1.0.0` is cut from THIS slice's merge commit
  (TF-020F-003). The slice ships the preset; tagging is the
  trivial post-merge step. Corrected from pre-fix-round-1 (where
  this was wrongly ticked).
- [x] **(iv)** CODEOWNERS on `renovate/**` already covers via 020K
  rule `renovate/** @jrnb2024`. Verified at this slice land.
- [x] **(v)** `.github/dependabot.yml` monitors `.github/workflows/`
  for third-party action SHAs (actions/checkout etc.). Renovate
  customManager covers the SCP federation primitive's own SHA pins
  + tool-version pins via `scripts/.tool-versions` (covered in
  020B.2). Two tools complementary, not redundant — documented
  explicitly in dependabot.yml header.
- [x] **(vi)** SCP self consumes its own preset via `renovate.json`
  at repo root extending
  `github>jrnb2024/standards-control-plane-//renovate/default`.
  This validates the cascade in-WP — when SCP cuts a future
  release tag, Renovate runs against SCP's own wrapper and bumps
  the pin via the same path adopters use.
- [x] **(vii)** Org-config verification — Renovate Bot already
  active on `jrnb2024` per WP-SCP-020 §6 (Mend hosted app).
  `extends: ["config:recommended", ...]` at the top of
  `renovate/default.json` inherits the org defaults.
  **Verification artefact** (closure of fix-round-1 COMP-006 +
  fix-round-2 COR-R2-002): Renovate dashboard for the SCP repo
  is reachable at
  `https://developer.mend.io/github/jrnb2024/standards-control-plane-`
  (the primary, unambiguous evidence of Mend Renovate
  installation; Dependabot PRs are NOT corroborating evidence
  because Dependabot is GitHub-native, not Mend-hosted).

## Post-merge action

After this PR squash-merges to main, run:

**Prerequisites:** the operator's local clone of the SCP repo at
HEAD = current main, with `gh` authenticated and admin scope on
the SCP repo. The block uses portable path discovery (no operator-
local hard-coded path) so a future second-maintainer can run it
unchanged. Closes 020F R3 safety NEW-R3-SAFE-005.

```bash
# Navigate to the SCP repo root from anywhere inside a checkout.
cd "$(git rev-parse --show-toplevel)"
git checkout main && git pull --ff-only

# 1. Apply the renovate/v* tag-protection ruleset FIRST
#    (CRIT-SAFE-001 closure). The ruleset is idempotent against
#    an empty namespace, so applying before any tag is published
#    eliminates the TOCTOU window 020F R2 NEW-R2-SAFE-001
#    flagged (cut-tag-then-protect would leave the just-pushed
#    tag unprotected for the seconds between the two commands).
./scripts/configure-020f-renovate-tag-protection.sh

# 2. Cut the renovate/v1.0.0 tag (TF-020F-003 closure).
git tag -a renovate/v1.0.0 -m "renovate/v1.0.0 — initial preset"
git push origin renovate/v1.0.0

# 3. Open the follow-up PR pinning renovate.json to the new tag
#    (TF-020F-001 closure) — small ~5-line PR.
```

## Tracked-forward items (TF-020F-NNN)

- **TF-020F-001**: Pin `renovate.json` extends to `#renovate/v1.0.0`. Closes within hours of 020F merge.
- **TF-020F-002**: 020H part 3 ships the canonical adopter wrapper marker convention. Until then, marker documented inline in `renovate/default.json` description.
- **TF-020F-003**: Cut `renovate/v1.0.0` tag (post-merge step above).
- **TF-020F-004**: Plan §4 020F (i) text uses `standards-control-plane` without trailing dash; opportunistic plan-text fix.

## Tag series

The preset is versioned with its own `renovate/v*` tag series,
independent of the workflow tag series `v*`. Initial publication
of `renovate/v1.0.0` is the post-merge step listed above
(TF-020F-003).

The `renovate/v*` series IS protected by a parallel
tag-protection ruleset `scp-tag-protection-renovate-v` applied
post-merge via `scripts/configure-020f-renovate-tag-protection.sh`.
This closes 020F R1 safety review CRIT-SAFE-001 (preset poisoning
via tag re-pointing). Same protections as the 020J `v*` ruleset:
deletion / non_fast_forward / update blocked.

## What this PR does NOT do

- Does NOT cut the `renovate/v1.0.0` tag (post-merge step,
  TF-020F-003).
- Does NOT pin `renovate.json` extends to `#renovate/v1.0.0`
  (post-merge step, TF-020F-001 — depends on the tag existing).
- Does NOT automate preset-version bumps in adopter `extends:`
  fields. The customManager regex targets workflow YAML
  (`uses: ...@<SHA> # tag: <semver>`) only; preset-version
  bumps in `renovate.json` `extends:` are manual. Acceptable
  for v1.0.0 — preset shape evolves slowly and operator-attended
  bumps are appropriate. Documented per fix-round-1 nit-COMP-008.
- Does NOT enable Renovate on additional repos (estate cascade =
  WP-SCP-024).

## R1 review

3× parallel Sonnet R1 review will dispatch in parallel with CI per
"full process" mandate. Lenses: correctness, safety_bypass,
completeness_governance.

## Files

- `renovate/default.json` — the shared preset (new). Includes
  trust-boundary description, root automerge=false safety
  override, root ignoreUnstable=true with explicit per-package
  opt-in for the federation primitive, hardened prBodyNotes
  (release notes mutable; SHA authoritative), and the
  customManager regex matching the canonical adopter marker.
- `renovate.json` — SCP-self consumer (new). Pinning to
  `#renovate/v1.0.0` is post-merge follow-up (TF-020F-001).
- `.github/dependabot.yml` — extended (existing was bare-minimum
  GitHub Actions weekly). Wildcard group excludes privileged
  actions (`actions/checkout`, etc.) per fix-round-1 MAJ-SAFE-006.
- `scripts/configure-020f-renovate-tag-protection.sh` — new,
  idempotent applier for the `scp-tag-protection-renovate-v`
  ruleset (closes CRIT-SAFE-001).
- `.github/workflows/policy-check-wrapper.yml` — fix-round-1
  comment-tag correction (`v1.0.0` not `post-v1.0.0 + ...`)
  so the customManager regex actually matches.
- `docs/reviews/WP-SCP-022/dispatches/020f/DISPATCH-NOTE.md` —
  this file.
- `docs/reviews/WP-SCP-022/dispatches/020f/FIX-ROUND-1.md` —
  R1 fix evidence + tracked-forward items.

## Post-merge STATUS.md update commitment

After this PR merges, STATUS.md's "Post-Threshold-A backlog"
table updates to mark 020F landed. A follow-up PR (which also
closes TF-020F-001 — `renovate.json` tag pin) carries the
STATUS.md edit. Bundle to keep the chain auditable.
