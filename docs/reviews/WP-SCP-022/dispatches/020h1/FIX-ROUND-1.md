# 020h1 fix-round-1 (post-r1)

**Date:** 2026-05-01

## Triggers

R1 dispatch returned (commit 4e186e3 reviewed):

- **R1 correctness** (`review-correctness.json`, ~8.4 min, APPROVED_WITH_FINDINGS): 4 MIN + 3 nit. **No CRIT/MAJ.**
- **R1 safety** (`review-safety.json`, ~6.3 min, APPROVED_WITH_FINDINGS): **3 MAJ** + 3 MIN + 2 nit.
- **R1 completeness** (`review-completeness.json`, ~10 min, APPROVED_WITH_NOTES): **3 MAJ** + 5 MIN + 1 nit.

**Cumulative: 6 MAJ + 12 MIN + 6 nit.** Per `feedback_protocol_over_shortcuts.md` no descoping; all closed inline or tracked as TF-020H1-NNN.

## Closures applied

### MAJ closures

| Finding | Severity | Closure |
|---|---|---|
| SAFE-MAJ-001 | MAJ | `docs/reviews/rule-proposals/README.md` §Process step 2: bypass-introducing-proposal exception added. When the proposal's §5 "Bypass surface" is non-empty, the 48h window is **non-waivable** and the PR description MUST include a "Bypass surface enumeration" paragraph naming every adopter-side control governing the surface. |
| SAFE-MAJ-002 | MAJ | `RULE-TEMPLATE.md` §5 extended with a fourth prompt — "Implicit exclusion set: under what manifest shapes does this rule return `allow` (pass)? Enumerate the key conditions that make a manifest exempt." Reviewers MUST verify the exemption set is intentional. |
| SAFE-MAJ-003 | MAJ | `SECURITY.md` shipped at repo root (~50 lines): GitHub Security Advisory + `jimbrooke@me.com` channels; 3-business-day initial-response SLA; 30-day coordinated-disclosure target; explicit in-scope / out-of-scope. ADOPT-001 §12.7.8 updated to drop "when published" and reference the new SECURITY.md directly. `.github/ISSUE_TEMPLATE/rule-regression.md` comment block updated likewise. Closes WP-SCP-020 §4.1 follow-up SCP-073.sec. |
| COMP-MAJ-001 | MAJ | TF-020H1-001 (enforce_release_gate) added to STATUS.md "Tracked-forward items from 020H.1". DISPATCH-NOTE "Out of scope" section reworded to point at TF-020H1-NNN entries. |
| COMP-MAJ-002 | MAJ | TF-020H1-002 (paging rotation) added to STATUS.md. DISPATCH-NOTE wording corrected (was: "tracked as VERSIONING.md-referenced future work"; now: "filed as TF-020H1-002"). |
| COMP-MAJ-003 | MAJ | **D-036 filed** in `docs/DECISIONS.md` ratifying VERSIONING.md semver contract + rule-RFC process as estate doctrine. Symmetric posture with D-035. Names the bypass-introducing-proposal exception (SAFE-MAJ-001 closure) explicitly so the doctrine reflects the post-fix-round-1 state. |

### MIN closures

| Finding | Severity | Closure |
|---|---|---|
| COR-REPLAY-001 | MIN | `canary-replay.yml` GITHUB_OUTPUT delimiter is now per-run unique: `delim="REPLAY_EOF_${RANDOM}_${RANDOM}_$(date +%N)"`. Cryptographically negligible chance of collision with replay-canary.sh's TSV output. |
| COR-TEMPLATE-001 | MIN | `RULE-TEMPLATE.md` §3.2 now lists all three required fields: `disable: true` + `justification: <string>` + `expires_at: <date>` per `schemas/rule-config.schema.json`. |
| COR-TEMPLATE-002 | MIN | `RULE-TEMPLATE.md` §3.3 clarified: error code (`SCP-EXXX`) goes in annotation `title=`, rule ID (`SCP-R-NNN`) goes in the human-readable message. The two are distinct fields. |
| COR-MANIFEST-001 | MIN | ADOPT-001 §12.7.11 wording rewritten to be unambiguous about the int-pair comparison (`(major, minor)` parsed as integer pair; emit when majors differ OR `(main.minor - pinned.minor) > threshold`). |
| COR-INPUTS-001 | MIN | `canary-replay.yml` `${{ inputs.measure_cold_start }}` now passed via `env: INPUT_MEASURE_COLD_START` and read in bash via `${INPUT_MEASURE_COLD_START}` (020B security pattern — no direct `${{ }}` expansion inside `run:`). Replay args pass via bash array `replay_args=("--measure-cold-start")`. |
| COR-MANIFEST-002 | MIN | `version-manifest.json` `$schema` URL removed (pointing to the JSON Schema meta-schema was incorrect). Replaced with a `_schema_note` field explaining the absence and naming the future closure path (`schemas/version-manifest.schema.json` if the surface grows). |
| COR-DEDUP-001 | MIN | `canary-replay.yml` adds `concurrency: { group: canary-replay, cancel-in-progress: false }` — overlapping runs queue rather than racing the gh-issue-list / gh-issue-create check. |
| SAFE-MIN-004 | MIN | `canary-replay.yml` issue-body composition now uses a Python heredoc (`python3 - <<'PY'`) with single-quoted delimiter, replacing the bash heredoc with shell-expanded `${REPLAY_OUTPUT}`. Placeholders are explicitly substituted via Python `.replace()`; shell metacharacters in REPLAY_OUTPUT cannot inject. |
| SAFE-MIN-005 | MIN | TF-020H1-004 (rule-config disable canary missing) added to STATUS.md. Closure path: add `canary/rule-config-disabled` branch + extend `scripts/replay-canary.sh` registry. Forward-compat. |
| SAFE-MIN-006 | MIN | `policy-check.yml` freshness-warning step now reads `freshness_warning_threshold_minor` from the **PINNED** manifest (`.scp-runtime/version-manifest.json`), NOT from main HEAD's manifest. Closes the attack surface where main-HEAD compromise could silence the warning by setting threshold=999. ADOPT-001 §12.7.11 updated to reflect the change. |
| COMP-MIN-001 | MIN | `canary-replay.yml` adds `release: { types: [published] }` trigger — closes plan §4 020H.1 (iv-b) "on each release" requirement (was cron + workflow_dispatch only). |
| COMP-MIN-002 | MIN | ADOPT-001 §12.7.5 step 4 updated: "(lands in 020H.1)" replaced with "shipped at 020H.1" + actual file path. |
| COMP-MIN-003 | MIN | `docs/reviews/rule-proposals/README.md` D-031 citation now includes canonical path `docs/DECISIONS.md`. |
| COMP-MIN-004 | MIN | TF-020H1-003 (auto-defer GH Action) added to STATUS.md. Closure path: scheduled GH Action when proposal volume warrants automation. Forward-compat. |
| COMP-MIN-005 | MIN | STATUS.md TF-020H3-003 closure-path estimate corrected: "(NOT 020H.1 — 020H.1 added new policy/process docs but did not amend the plan; this TF stays open for a future plan-touch slice)". |

### nit closures

| Finding | Severity | Closure |
|---|---|---|
| SAFE-nit-007 | nit | `canary-replay.yml` `--assignee jrnb2024` replaced with `--assignee "${assignees}"` where `assignees="${SCP_REGRESSION_ASSIGNEES:-jrnb2024}"`. Forward-compat for the 2026-07-21 second-maintainer onboarding (set the env var in the workflow at that time). |
| SAFE-nit-008 | nit | `RULE-TEMPLATE.md` §10 "Open questions" extended with `[BLOCKING]` vs `[deferrable]` markers + explicit note that proposals with unresolved `[BLOCKING]` questions do NOT meet quorum. |
| COMP-nit-001 | nit | `RULE-TEMPLATE.md` §6 "Conflict-gate strategy" extended to reference `tests/conflict_gate/<rule-id>/{allow,deny}/` fixture path + `adapter.py` adapter contract + `SCP-E005` merge-blocking consequence. |

## Summary

- **3 MAJ** in safety lens (rule-RFC bypass-quorum + template implicit-exclusion + missing SECURITY.md) closed inline.
- **3 MAJ** in completeness lens (TF-020H1-NNN tracking + D-036 ratification) closed inline.
- **12 MIN + 6 nit** closed via inline edits OR tracked-forward items (TF-020H1-001..005).

No descoping. Every finding either closed by an inline edit or named as a TF-020H1-NNN entry with a closure path.

R2 lens dispatch follows on the post-fix-round-1 state. Per `feedback_recursive_adversarial_review.md`, recurse until no new BLOCKING findings.
