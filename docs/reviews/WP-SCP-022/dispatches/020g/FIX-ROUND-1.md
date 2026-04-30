# WP-SCP-022 slice 020G — fix round 1

**Date:** 2026-04-30 (evening)
**Triggered by:** R1 review × 3 surfaced 8 MAJ + 9 MIN + 4 nit findings.

## R1 verdicts

| Lens | Verdict | Findings |
|---|---|---|
| correctness | NEEDS_REVISION | 3 MAJ + 2 MIN + 2 nit |
| safety_bypass | CONDITIONAL | 3 MAJ + 5 MIN + 2 nit |
| completeness_governance | CONDITIONAL | 2 MAJ + 3 MIN + 1 nit |

The most critical finding (CORR-003) was a real script-breaking bug: `required_signatures` is NOT a documented field of the unified branch-protection PUT body — it's a dedicated sub-resource. The script as shipped at fix-round-0 would have failed verification on every fresh adopter repo, making the slice non-functional.

## Findings addressed in this fix round

### From correctness (R1)

- **CORR-001** (broken nested fences in log block): **closed** — switched outer fence to `~~~markdown` so inner triple-backtick `json` fences nest correctly per CommonMark.
- **CORR-002** (SCRIPT_SHA silently empty when run from non-SCP CWD): **closed** — replaced with SHA256 of the actually-executing file content (via `shasum -a 256 "$0"`) as the primary identifier; git-SHA reported as a secondary identifier with explicit `not-in-git-clone` fallback.
- **CORR-003** (`required_signatures: true` in unified PUT body would fail): **closed** — split into a dedicated `gh api -X POST .../protection/required_signatures` call after the unified PUT. The unified PUT body no longer carries `required_signatures`. Verification still confirms the sub-resource is enabled.
- **CORR-004** (no null guard on `.required_status_checks.contexts` in jq join): **closed** — added `// []` default before `join`.
- **CORR-005** (before-state capture masks all gh failures as "no protection"): **closed** — capture stderr + stdout, only treat the "Branch not protected" pattern as the no-protection-yet case; everything else aborts with the actual error.
- **CORR-006** (shift 2 fails ungracefully on missing flag value): **closed** — added explicit `[ $# -lt 2 ]` check before each `shift 2`.
- **CORR-007** (python3 not via require_cmd): **closed** — added `require_cmd python3` and `require_cmd shasum`.

### From safety (R1)

- **SAF-001** (SCRIPT_SHA can lie if uncommitted changes): **closed** — same fix as CORR-002. SHA256 of file content always reflects what actually ran.
- **SAF-002** (`required_pull_request_reviews: null` silently destroys adopter review enforcement): **closed** — script now reads existing reviews from before-state and splices them into the PUT payload. Adopters with multi-maintainer review-shape preserve it; adopters with no reviews stay at null (no change).
- **SAF-003** (`--no-enforce-admins` insufficient gate): **closed** — added `--i-understand-this-bypasses-the-gate` confirmation flag. Without it, `--no-enforce-admins` is silently ignored. With both, a 5-second pause + visible warning gives operators a chance to abort before applying.
- **SAF-004** (`--plan` doesn't show before-state): **closed** — `--plan` now prints both current branch-protection JSON AND the proposed PUT payload. Operator sees the full diff.
- **SAF-005** (heredoc parameter expansion as code-injection surface): **closed via SAF-006** — REPO + BRANCH path-traversal validation (regex check) eliminates the hostile-input class. Other interpolated values (REQUIRED_CONTEXT, OPERATOR, JSON blobs) are either operator-supplied at the same trust level or come from `gh api` responses (which we trust as much as the operator's GitHub identity).
- **SAF-006** (path-traversal in --branch): **closed** — added regex validation: `--repo` must match `[A-Za-z0-9._-]+/[A-Za-z0-9._-]+`; `--branch` rejects empty / slash-containing / `..`-containing / leading-dot values.
- **SAF-007** (no confirmation on apply): **acknowledged-deferred** — `--plan` is the documented confirmation step. Adding interactive confirmation in addition to `--plan` would clash with the bootstrap-only attended-script posture (the operator has to type the apply command after reviewing plan output anyway).
- **SAF-008** (OPERATOR identity mismatch with service-account PATs): **acknowledged** — documented in the script's bootstrap-only header that the recommended PAT shape is fine-grained scoped to a single target repo. A service-account PAT would still get its identity recorded; the log entry's git SHA + script SHA256 close any ambiguity.
- **SAF-009** (nested fences): **closed via CORR-001**.
- **SAF-010** (log not emitted on failure): **closed** — verification failure now falls through to log emission with explanatory text, then exits non-zero. Audit trail records failures.

### From completeness (R1)

- **COMP-001** (no D-NNN row): **closed** — D-035 added to `docs/DECISIONS.md`. Symmetric posture with D-030/D-031/D-032/D-034.
- **COMP-002** (PAT scope log-warn not implemented): **closed** — explicit stderr WARNING block printed before any mutation, listing required scope + recommendation (fine-grained PAT) + suggestion to run `--plan` first.
- **COMP-003** (gh 2.40 floor reasoning incorrect — script doesn't use rulesets API): **closed** — error message updated to "the unified branch-protection PUT shape used here has been stable since gh 2.x; anything older risks API drift". Floor stays at 2.40 for safety margin.
- **COMP-004** (no CI guard): **closed** — added `CI=true / GITHUB_ACTIONS=true` env-var guard at top of script. Refuses to run.
- **COMP-005** (broken nested fences in log block): **closed via CORR-001**.
- **COMP-006** (python3 not declared): **closed via CORR-007**.

## Files modified in this round

- `scripts/enable-required-check.sh` — substantial rewrite: bootstrap-only CI guard; PAT-scope warning; argument validation; required_signatures via dedicated endpoint; required_pull_request_reviews preservation; --no-enforce-admins acknowledgement-flag gate; SHA256 self-hash; nested-fence fix; null-safe jq.
- `docs/DECISIONS.md` — D-035 row.
- `docs/reviews/WP-SCP-022/dispatches/020g/FIX-ROUND-1.md` — this file.

## Next step

R2 dispatch on the corrected artefact set. Per `feedback_recursive_adversarial_review.md`, recurse to fixpoint.
