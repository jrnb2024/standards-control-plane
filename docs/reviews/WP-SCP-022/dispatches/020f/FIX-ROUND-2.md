# WP-SCP-022 slice 020F — fix round 2

**Date:** 2026-04-30 (evening)
**Triggered by:** R2 review × 3 surfaced 2 MAJ + 4 MIN + 1 nit on the corrected fix-round-1 artefact set.

## R2 verdicts

| Lens | Verdict | NEW findings vs R1 |
|---|---|---|
| correctness | **PASS** | 1 MIN + 1 nit |
| safety_bypass | **LGTM_WITH_CONDITIONS** | 2 MIN |
| completeness_governance | NOT_ACCEPTED | 2 MAJ + 2 MIN |

The 2 MAJ blockers are both consequences of fix-round-1 referencing artefacts that didn't yet exist (the configure-script header cited `D-034` and a `branch-protection.md` section that hadn't been written). All R1 findings remain closed.

## Findings addressed in this fix round

### From completeness (R2)

- **COMP-R2-001** (D-034 dangling reference): **closed** — D-034 row added to `docs/DECISIONS.md` ratifying the renovate/v* protection ruleset, citing CRIT-SAFE-001 + naming the ruleset + symmetric posture with D-030. D-034 is now referenced from `docs/DECISIONS.md` (the row itself), `docs/security/branch-protection.md` ("Tag protection — renovate/v* pattern" section header reference), `scripts/configure-020f-renovate-tag-protection.sh` (script header), and `docs/reviews/WP-SCP-022/dispatches/020f/DISPATCH-NOTE.md` (slice-acceptance + post-merge-action sections). Cross-document consistency verified via `grep -c D-034`.
- **COMP-R2-002** (branch-protection.md missing renovate/v* section): **closed** — added "Tag protection — `renovate/v*` pattern" subsection to `docs/security/branch-protection.md`. References D-034. Documents the script's hardening (jq construction + multi-property verification).
- **COMP-R2-003** (preset description doesn't name `config:recommended` as floating ref): **closed** — appended explicit sentence to `renovate/default.json` description naming `config:recommended` as Mend-administered floating reference and how the explicit root-level `automerge: false` defends against silent changes.
- **COMP-R2-004** (DISPATCH-NOTE doesn't document extends-automation asymmetry): **closed** — added bullet to "What this PR does NOT do" explaining customManager targets workflow YAML only; preset-version bumps in adopter `extends:` are manual.

### From safety (R2)

- **NEW-R2-SAFE-001** (TOCTOU window — cut tag before applying protection): **closed** — post-merge sequence reordered to apply the protection ruleset FIRST (idempotent against empty namespace), then cut the tag. The ruleset waits for matching tag refs; applying before any tag exists is safe.
- **NEW-R2-SAFE-002** (heredoc command injection on env vars + insufficient verification): **closed** — script rewritten to use `jq -n --arg ...` for JSON construction (structurally separates env-var values from JSON structure). Verification step now reads the full ruleset back via the per-ruleset endpoint and asserts: `enforcement: "active"`, all 3 rule types present (deletion / non_fast_forward / update), and the include-pattern matches the expected value.

### From correctness (R2)

- **COR-R2-001** (verifier should also check ref_name.include pattern): **closed** — same fix as NEW-R2-SAFE-002 covers it (multi-property verification block includes the include-pattern assertion).
- **COR-R2-002** (DISPATCH-NOTE evidence block cites Dependabot PRs as Mend-Renovate evidence): **closed** — Dependabot citation removed; explicit note added that Dependabot is GitHub-native, not Mend-hosted, and is NOT corroborating evidence. The Mend dashboard URL is sufficient on its own.

## Files modified in this round

- `scripts/configure-020f-renovate-tag-protection.sh` — rewrote `apply_renovate_tag_protection()` to use `jq -n --arg` for JSON construction; verification block now asserts full ruleset state (enforcement, rule-type set, include-pattern).
- `docs/DECISIONS.md` — D-034 row.
- `docs/security/branch-protection.md` — new "Tag protection — `renovate/v*` pattern" subsection.
- `renovate/default.json` — description sentence about `config:recommended`.
- `docs/reviews/WP-SCP-022/dispatches/020f/DISPATCH-NOTE.md` — post-merge sequence reordered, evidence block tightened, extends-automation-asymmetry bullet added.
- `docs/reviews/WP-SCP-022/dispatches/020f/FIX-ROUND-2.md` — this file.

## Next step

R3 dispatch. Per `feedback_recursive_adversarial_review.md`, recurse to fixpoint. Correctness already declared PASS at R2; safety LGTM_WITH_CONDITIONS; completeness needed two evidence artefacts that landed here. R3 should confirm fixpoint.
