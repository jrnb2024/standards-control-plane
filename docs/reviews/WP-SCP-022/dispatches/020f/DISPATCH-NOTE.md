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
- [x] **(iii)** Preset versioned with own tag series — see "Tag
  series" section below.
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

## Tag series

The preset is versioned with its own `renovate/v*` tag series,
independent of the workflow tag series `v*`. Initial publication
of `renovate/v1.0.0` happens post-merge of this PR via:

```bash
cd /Users/amplience/Projects/scp-track1
git checkout main && git pull --ff-only
git tag -a renovate/v1.0.0 -m "renovate/v1.0.0 — initial preset"
git push origin renovate/v1.0.0
```

Note: the tag-protection ruleset on `v*` (020J) catches `v1.0.0`,
`v1.0.0-rc.1`, etc. — but does NOT catch `renovate/v1.0.0`
because the pattern is `refs/tags/v*` (literal `v` prefix at the
start of the tag name, no slash). The `renovate/v*` tag series
is intentionally outside this protection — it represents preset
shape, not federation-primitive shape, and the cost of
re-cutting a preset tag is bounded (Renovate re-evaluates on
each adopter's next scheduled run). If we wanted preset tag
protection, we'd add a second ruleset matching `refs/tags/renovate/v*`
in a follow-up slice. **Not in 020F scope.**

## What this PR does NOT do

- Does NOT cut the `renovate/v1.0.0` tag (post-merge step).
- Does NOT enable Renovate on additional repos (estate cascade =
  WP-SCP-024).
- Does NOT extend tag-protection to the `renovate/v*` series
  (deferred per "Tag series" section above).

## R1 review

3× parallel Sonnet R1 review will dispatch in parallel with CI per
"full process" mandate. Lenses: correctness, safety_bypass,
completeness_governance.

## Files

- `renovate/default.json` — the shared preset (new).
- `renovate.json` — SCP-self consumer (new).
- `.github/dependabot.yml` — extended (existing was bare-minimum
  GitHub Actions weekly).
- `docs/reviews/WP-SCP-022/dispatches/020f/DISPATCH-NOTE.md` —
  this file.
