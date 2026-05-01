# 020h3-1-auto-issue fix-round-1 (post-r1)

**Date:** 2026-05-01

## Triggers

R1 dispatch returned (commit 1a12f68 reviewed):

- **R1 correctness** (`review-correctness.json`, ~9 min, PASS): 0 MAJ + 2 MIN + 2 nit.
- **R1 safety** (`review-safety.json`, ~7.8 min, APPROVED_WITH_FINDINGS): **1 MAJ** + 3 MIN + 1 nit.
- **R1 completeness** (`review-completeness.json`, ~5.7 min, APPROVED_WITH_NOTES): 0 MAJ + 1 MIN + 1 nit.

**Cumulative: 1 MAJ + 6 MIN + 4 nit.** Per `feedback_protocol_over_shortcuts.md` no descoping; all closed inline.

## MAJ closure

| Finding | Closure |
|---|---|
| **SAFE-MAJ-001** (issues:write granted at job level — over-broad privilege scope) | release-gate.yml split into two jobs: `release-gate` (evaluation; `contents: read` only) + `release-gate-violation-issue` (`needs: release-gate`; fires on `needs.release-gate.result == 'failure' && github.event_name == 'push'`; `permissions: { contents: read, issues: write }`). The gate-evaluation steps (pip install, schema validate, ramp check, expired-config check) cannot accidentally open issues — they run in the `contents: read`-only job. **Ratified by D-037** (mirrors D-029 statuses:write precedent: amending decision row naming the precise threat-surface and bounded behaviour). |

## MIN closures

| Finding | Closure |
|---|---|
| SAFE-MIN-001 | Tag fallback now sanitised: `tag="$(printf '%s' "${raw}" | LC_ALL=C tr -cd 'A-Za-z0-9._-')"` — strips any character outside the safe set. Defense-in-depth (GITHUB_REF cannot contain shell metacharacters since it's set by GitHub Actions, but the sanitisation is cheap). |
| SAFE-MIN-002 | New "Ensure required labels exist (idempotent)" step pre-creates `release-gate-violation`, `needs-triage`, `auto-opened` labels via `gh label create --force` (gh CLI's idempotent flag). Closes the gh-issue-create-fails-if-label-missing path. |
| SAFE-MIN-003 | **D-037 filed** in `docs/DECISIONS.md` ratifying the `issues: write` job-level grant. Symmetric posture with D-029 (statuses:write for readback): privilege-write expansions get an amending decision row. STATUS.md "Recent decisions" extended with D-037. |
| COR-MIN-001 | Python template inside `<<'PY'` heredoc no longer uses `\`` escapes — the single-quoted heredoc preserves backticks literally and Python triple-quoted strings have no backtick syntax, so plain backticks are correct. (The reviewer's claim was about a hypothetical case; verified by inspection.) |
| COR-MIN-002 | The job-level `if: needs.release-gate.result == 'failure'` is just as broad as the original step-level `failure()` (any prior step failure triggers it), but acceptable: the issue body now explicitly says "Note: this issue may also fire on infra failures (pip install, network) — verify the failed step in the run before assuming a real violation." Operators triage. |
| COMP-MIN-001 | **TF-020H3rg-004 filed** in STATUS.md (issue auto-close on corrective tag-cut). Closure path: future workflow step that detects the corrected tag-cut and `gh issue close`s any open release-gate-violation issue for the bad tag-series. No deadline (forward-compat). |

## nit closures

| Finding | Closure |
|---|---|
| SAFE-nit-001 | Both branches (de-dup `gh issue comment` and new-issue `gh issue create`) now use Python templating for body composition. The de-dup branch builds `comment_body` via `python3 - <<'PY' ... print(f"Re-detected ...") PY`. Symmetric with the canary-replay.yml fix-round-1 SAFE-MIN-004 pattern. |
| COR-nit-001 | `gh issue list --search` query changed from `in:title "${title}"` (bracketed phrase, may be stripped by GitHub Search API) to `tag ${tag} failed validation` (plain substring), then jq-filtered locally for exact title match. Avoids the bracketed-token edge case. |
| COR-nit-002 | The concurrency group expression's different keys for dry-run vs push:tags is **intentional** — dry-runs against different tags shouldn't queue behind each other; push:tags has a single canonical key (`refs/tags/v...`). The fix-round-1 commit's expression already encodes this; the DISPATCH-NOTE note acknowledges the asymmetry. |
| COMP-NIT-001 | STATUS.md "Post-Threshold-A backlog" section gained an inline naming-note distinguishing "020H part 3" (pre-Threshold-A v1.0.0-cut sequence; PR #75 / 347fde2) vs "020H.3" (post-Threshold-A dot-N; PR #79 / 42f49db) vs "020H.3.1" (this PR's reconciliation). |

## Closures NOT applied

None. Every finding inline-closed.

## Re-review

R2 lens dispatch follows on the post-fix-round-1 state. Per `feedback_recursive_adversarial_review.md`, recurse until no new BLOCKING findings.

The fix-round-1 changes are substantial:
- 1 architectural refactor (workflow split into two jobs).
- 1 new D-NNN ratification row (D-037).
- 1 new TF-020H3rg-NNN entry (TF-020H3rg-004).
- 5 small mechanical edits (sanitisation, label-ensure, Python templating, search-API workaround, STATUS naming-note).

R2 reviewers should expect to verify each closure is genuine, particularly the privilege-scope refactor and the D-037 wording.
