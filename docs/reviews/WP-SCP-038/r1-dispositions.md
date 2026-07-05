# WP-SCP-038 — 3-lens R1 review dispositions

**Work Package:** WP-SCP-038 (audit-changed adopter-repo scoping)
**Review round:** R1 (build-stage), 3 parallel lenses per the four-tier dispatch protocol
(`feedback_four_tier_dispatch.md`): correctness / safety_bypass / completeness_governance.
**Date:** 2026-07-05
**Dispatch:** `pattern3-20260705T212353Z-58064` (superseded by later re-seeds; source under D-057).

R1 verdicts: correctness **SHIP**; safety_bypass **BLOCK** (2 MAJOR); completeness_governance
**BLOCK** (1 BLOCKER + 1 MAJOR). All blocking + major findings were resolved in-round (R1→R2),
no descoping (`feedback_split_not_descope.md`). R2 re-review recorded in
[`r2-dispositions.md`](r2-dispositions.md).

---

## Findings + dispositions

### [BLOCKER] (completeness) Missing STATUS.md chain entry + missing R1 evidence file cited by D-066
D-066 (`docs/DECISIONS.md`) and the plan-doc §8 cite `docs/reviews/WP-SCP-038/r1-dispositions.md`
and a STATUS chain entry that did not yet exist at review time.
**Disposition: FIXED.** This file is that evidence. The STATUS chain entry is added in the
same PR (it is authored at PR/merge time per the house convention, after R-fixpoint).

### [MAJOR] (safety) MCP `audit_changed` defaulted `repo_root` to `project_root()` → false-clean at the MCP boundary
`audit_changed_impl` defaulted the audit target to the SCP checkout when `repo_root` was omitted;
an adopter agent (the primary MCP caller) could silently audit SCP and get a normal-looking
`AuditChangedResponse` — the exact false-clean-about-the-wrong-repo the WP exists to kill, moved
to the MCP boundary.
**Disposition: FIXED.** MCP `repo_root` now defaults to `Path.cwd()` (mirrors the CLI's uniform
cwd-default): a server running inside the adopter workspace audits the adopter; a server
elsewhere fails loudly (non-git / missing ref) via the subprocess CLI's `resolve_audit_repo_root`
guard rather than silently self-auditing SCP. Field description updated to match
(`mcp_server/tools.py`, `AuditChangedRequest.repo_root`).

### [MAJOR] (safety) `GIT_DIR` / `GIT_WORK_TREE` inheritance defeats the cwd/root guard
Every git subprocess inherited the ambient env, so `GIT_DIR`/`GIT_WORK_TREE` set by a CI runner
or wrapper could redirect `git rev-parse --show-toplevel` (and `git diff`) for BOTH sides of the
cwd/root comparison identically — the guard would agree while both point at a third repo (e.g. SCP).
**Disposition: FIXED.** New `changed_audit.git_subprocess_env()` strips
`GIT_DIR`/`GIT_WORK_TREE`/`GIT_COMMON_DIR`/`GIT_INDEX_FILE`; `env=git_subprocess_env()` is passed
to every git subprocess in `changed_audit.py` (`_git_toplevel`, `_ref_is_commit`,
`list_changed_files`) and `mcp_server/tools.py` (`_run_git_command`, and the CLI subprocess in
`_run_audit_changed_cli`), so the passed `cwd` stays authoritative.

### [MAJOR] (completeness) E021 miss-test could false-pass on a subprocess/import break
`test_audit_changed_area_inference_miss_is_e021` asserted only `error_code == "SCP-MCP-E021"`;
because every subprocess failure (incl. a broken PYTHONPATH fixture) collapses to E021, the test
did not prove the failure was genuinely area inference.
**Disposition: FIXED.** The test now also asserts `response.message` contains `AreaIdInferenceError`
/ `area_id`. The companion positive test (`..._recovers_e021_with_area_hint`) asserts on
`changed_paths` + `area_id` content, independently proving the subprocess harness executes.

### [MAJOR→resolved] (correctness / safety) Explicit-`changed_paths` branch could extract from `project_root()` silently
`build_changed_file_audit_result(changed_paths=[...])` without `repo_root` left the extraction root
`None` → `extract_scope` fell back to `project_root()` (SCP). Adopter-unreachable (CLI + MCP never
supply `changed_paths`; only direct library callers auditing SCP's own fixtures do), but an open
door inconsistent with the WP intent.
**Disposition: FIXED (documented + explicit + tested).** The branch now resolves
`(repo_root or project_root())` **explicitly** with a comment stating it is SCP-internal and that a
library caller auditing a non-SCP repo via `changed_paths` MUST pass `repo_root`. `project_root()`
is the *correct* default for the only real callers (SCP fixture path-sets), so forcing `repo_root`
was rejected as it would break them. New test
`test_build_changed_file_audit_result_explicit_changed_paths_honours_repo_root` proves an explicit
`repo_root` is honoured (extraction reads that tree, not SCP).

### [MINOR] (safety/correctness) `--subsystem` / `--area-id` argv could mis-parse on a leading `-`
`subsystem` (derived from `repo_root.name`) and `area_hint` were passed as two argv tokens; a value
starting with `-` could be mis-parsed by argparse.
**Disposition: FIXED.** `_run_audit_changed_cli` now uses the `--opt=value` single-token form for
all args. (Not exploitable — argv list, no `shell=True` — hardened for robustness.)

### [MINOR] (completeness) plan-doc §3.3 "both call sites" imprecise
`extract_scope` is called once; the "both call sites" referred to `_normalise_scope`'s two
`normalise_project_area` calls reusing the single extracted scope.
**Disposition: FIXED.** Plan-doc §3.3 wording clarified.

### [MINOR] (correctness) MCP `repo_root` field description overstated "MUST"
**Disposition: FIXED** as part of the cwd-default change — the description now describes the
cwd-default and the loud-failure contract, not an unenforced "MUST".

### [MINOR] (safety) `subsystem` not shape-validated (unlike `consult_rules`)
**Disposition: ACCEPTED (consistent with the CLI).** The CLI `audit-changed --subsystem` and
`audit-request.schema.json` do not constrain subsystem beyond non-empty; `subsystem` is an
area-normalisation tag, not a repo-identity input, and is passed as a discrete argv element (no
injection). Tightening it estate-wide is out of scope for WP-SCP-038; left consistent with the
existing CLI contract.

### [MINOR] (safety) TOCTOU between the in-process pre-diff and the subprocess re-diff
**Disposition: ACCEPTED (out of scope).** Both diffs target the same repo path; only ref-content
freshness can race (concurrent push), which does not affect the wrong-repo property this WP fixes.

---

## Non-findings confirmed by reviewers (defensive evidence)

- No files under `policies/` or `.github/workflows/policy-check.yml` touched — the CI OPA/Conftest
  plane is genuinely untouched (anti-scope honoured).
- HTTP `/audit` (`service.py`) calls `build_audit_result` with `repo_root=None` (default) — there
  is no `/audit-changed` HTTP route, so the HTTP plane is unaffected, not silently broken.
- Every caller of `build_audit_result` / `extract_scope` / `list_changed_files` / `_audit_cache_key`
  either correctly defaults `repo_root=None` (plain `audit`, self-dogfood, HTTP — behaviour
  preserved) or threads `repo_root` (CLI, MCP).
- `output_dir()` still resolves under `project_root()`; the `--write-output` repo-locality gap is
  accurately named as a pre-existing follow-up (`FUP-WP-SCP-038-REPO-LOCAL-OUTPUT-001`), not
  silently shipped as fixed.
- Defect-1 regression test is genuinely discriminating: verified against the pre-fix code that the
  old `project_root()` default would have produced a different (wrong) `changed_paths`.
- Full suite: 370 passed; 5 pre-existing failures unrelated to this diff (scorecard golden-file
  path drift, a secrets-pattern false positive on committed rule fixtures, a governance rule-count
  drift from GOV-004/005) — reproduced identically on the clean baseline (pre-change) via
  `git stash`, confirming they are branch/env state, not regressions.
