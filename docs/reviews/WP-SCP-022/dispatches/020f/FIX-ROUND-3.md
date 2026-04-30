# WP-SCP-022 slice 020F — fix round 3

**Date:** 2026-04-30 (evening)
**Triggered by:** R3 review × 3 surfaced 1 MAJ + 6 MIN + 3 nit on the corrected fix-round-2 artefact set.

## R3 verdicts

| Lens | Verdict | NEW findings vs R2 |
|---|---|---|
| correctness | **PASS** | 1 MIN |
| safety_bypass | **LGTM_WITH_CONDITIONS** | 4 MIN + 1 nit |
| completeness_governance | NOT_ACCEPTED | 1 MAJ + 2 MIN + 2 nit |

R2 findings all closed. The R3 NOT_ACCEPTED on completeness is real: the completeness lens caught documentation-runbook drift in `docs/security/branch-protection.md` (apply/verify sections were not updated to include the new 020F applier) — same root issue surfaced from the correctness lens (COR-R3-001) and partially from completeness (COMP-R3-001/003/005).

## Findings addressed in this fix round

### From completeness (R3)

- **COMP-R3-001** + **COR-R3-001** ("Two idempotent appliers" → "Three"): **closed** — `docs/security/branch-protection.md` "How to apply" section header and bullet list updated. Added the 020F invocation block + env-var override docs.
- **COMP-R3-003** (env-var docs missing for 020F script): **closed** — added `SCP_PROTECTION_REPO`, `SCP_RENOVATE_RULESET_NAME`, `SCP_RENOVATE_TAG_PATTERN` (+ defaults) to the 020F bullet.
- **COMP-R3-005** (verify block missing renovate ruleset): **closed** — added a parallel `gh api ... select(.name == "scp-tag-protection-renovate-v") | {id, enforcement, target}` command to the verify block.
- **COMP-R3-002** (D-034 cross-reference list lacked FIX-ROUND-2 entry): **closed** — FIX-ROUND-2.md COMP-R2-001 closure note expanded to enumerate every cross-reference site for D-034 (DECISIONS.md, branch-protection.md, configure-020f script, DISPATCH-NOTE.md).
- **COMP-R3-004** (STATUS.md row text mentions 2026-07-30 review but doesn't enumerate which rulesets it covers): **closed** — STATUS.md row text expanded to "covers `v*` ruleset, `main` protection, AND `renovate/v*` ruleset".

### From safety (R3)

- **NEW-R3-SAFE-001** (bypass_actors not asserted): **closed** — verification block extended with `bypass_count="$(jq '.bypass_actors | length')"` + `!= "0"` check.
- **NEW-R3-SAFE-002** (`conditions.ref_name.exclude` not asserted): **closed** — verification block extended with `exclude_count="$(jq '.conditions.ref_name.exclude | length')"` + `!= "0"` check.
- **NEW-R3-SAFE-003** (`head -1` non-deterministic on duplicate names): **closed** — switched to capturing `final_id` from the POST response via `gh api -X POST ... | jq -r '.id'`, eliminating the listing-and-selecting path entirely. Existing-ruleset path still uses listing (correct: looking up id of existing ruleset by name).
- **NEW-R3-SAFE-004** (`target` field not asserted): **closed** — verification block extended with `target_val="$(jq -r '.target')"` + `!= "tag"` check.
- **NEW-R3-SAFE-005** (runbook hardcodes operator-local path): **closed** — DISPATCH-NOTE.md post-merge sequence rewritten to use `cd "$(git rev-parse --show-toplevel)"` + explicit prerequisites note.

### Lower severity

- All R3 nits absorbed into the broader fixes above.

## Files modified in this round

- `scripts/configure-020f-renovate-tag-protection.sh` — POST-response ID capture; 6-property verification block (target / enforcement / rule-set / include-pattern / exclude-empty / bypass-empty).
- `docs/security/branch-protection.md` — "Three idempotent appliers" header + 020F apply block + env-var docs + verify command.
- `STATUS.md` — quarterly-review row text updated.
- `docs/reviews/WP-SCP-022/dispatches/020f/DISPATCH-NOTE.md` — portable-path runbook + prerequisites stanza.
- `docs/reviews/WP-SCP-022/dispatches/020f/FIX-ROUND-2.md` — D-034 cross-reference list expanded (COMP-R3-002).
- `docs/reviews/WP-SCP-022/dispatches/020f/FIX-ROUND-3.md` — this file.

## Next step

R4 dispatch. Per `feedback_recursive_adversarial_review.md`, recurse to fixpoint. R3 already returned PASS on correctness and LGTM_WITH_CONDITIONS on safety; only completeness was NOT_ACCEPTED, with all blockers closed in this round. R4 should declare fixpoint across all three lenses.
