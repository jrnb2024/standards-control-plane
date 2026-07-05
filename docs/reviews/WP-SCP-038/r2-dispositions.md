# WP-SCP-038 — 3-lens R2 re-review dispositions (fixpoint)

**Work Package:** WP-SCP-038 (audit-changed adopter-repo scoping)
**Review round:** R2 (build-stage) — re-review of the R1 fix deltas, 3 parallel lenses.
**Date:** 2026-07-05
**Precedent:** [`r1-dispositions.md`](r1-dispositions.md).

R2 verdicts: correctness **SHIP** (zero findings); safety_bypass **SHIP** (both R1 MAJORs
verified resolved by direct code inspection, no new BLOCKER/MAJOR); completeness_governance
**SHIP** (all R1 BLOCKER + MAJOR confirmed closed). **R-fixpoint reached** — no new blockers,
no descoping (`feedback_recursive_adversarial_review.md`).

---

## R1→R2 delta verification (all confirmed resolved)

- **MCP `repo_root` default → `Path.cwd()`** (was `project_root()`): verified — an omitted
  `repo_root` audits the server's cwd, never silently SCP; a bad root fails loudly via the
  subprocess CLI's `resolve_audit_repo_root`. Exercised by `tests/test_mcp_audit_changed.py`
  against a real temp repo.
- **`git_subprocess_env()` strip** on every git subprocess in the audit path
  (`_git_toplevel`, `_ref_is_commit`, `list_changed_files`, `_run_git_command`,
  `_run_audit_changed_cli`): verified complete; the 4 stripped vars
  (`GIT_DIR`/`GIT_WORK_TREE`/`GIT_COMMON_DIR`/`GIT_INDEX_FILE`) are the only ones that can make
  both guard sides silently agree on the wrong repo (others — CEILING/DISCOVERY/OBJECT_DIRECTORY/
  NAMESPACE — only cause loud failure or don't affect toplevel/diff identity). `env=` replaces
  the child env wholesale, so no unstripped window in the CLI child.
- **E021 miss-test** now asserts on `response.message` (area inference), no longer false-passes on
  a subprocess/import break.
- **Explicit-`changed_paths`+`repo_root`** branch made explicit + tested (extraction reads the
  passed root, proven discriminating).
- **`--opt=value` argv form**: confirmed safe (single tokens, no `shell=True`, no re-parse).
- **No import cycle** (`mcp_server.tools → changed_audit`, one-directional); argparse accepts the
  `=`-form for all seven options; cache-key strings match byte-for-byte.

## R2 residual MINORs + dispositions

### [MINOR] (safety) MCP field/docs overclaimed the "cwd-vs-repo_root mismatch fails loudly" guard
Because `_run_audit_changed_cli` forces the child `cwd = repo_root`, the cwd-mismatch branch of
`resolve_audit_repo_root` cannot fire on the MCP path (only non-git / missing-ref can). Not a
bypass (an explicit `repo_root` is always honestly audited, never substituted with SCP), but the
wording was inaccurate.
**Disposition: FIXED.** The `AuditChangedRequest.repo_root` field description, the
`mcp-error-codes.md` E021 section, and `mcp-adopter-contract.md` now state that the MCP tool
audits the `repo_root` you pass (subprocess `cwd = repo_root`) and that the cwd-mismatch guard is
a CLI/library check.

### [MINOR] (safety/correctness) `_proposal_branch_exists` (tools.py) omits `env=git_subprocess_env()`
The lone git call outside the audit-changed surface (in the `propose()` codepath) does not strip
GIT_* location vars.
**Disposition: ACCEPTED — tracked, not fixed here.** `propose_impl`'s `repo_root` is fixed to
`project_root()` and is NOT caller-overridable (`ProposeRequest` has no `repo_root`), so there is
no cwd/repo_root divergence for an env var to exploit — no bypass of any safety property. Touching
the `propose` path is out of scope for WP-SCP-038; filed as
`FUP-WP-SCP-038-PROPOSE-GIT-ENV-001` (defense-in-depth consistency).

### [MINOR] (safety) `Path.cwd()` default trades a deterministic wrong-repo mode for a deployment-dependent one
When `repo_root` is omitted and the server's cwd is an unrelated third repo, the tool audits that
repo. Inherent to the "audit the caller's cwd" contract (matches the CLI); still fails loudly on a
non-git cwd / missing ref, and never fabricates a result about SCP specifically.
**Disposition: ACCEPTED (by design, documented).** This is strictly better than the prior
always-SCP default and is documented in the field description + E021 doc. Awareness note only.

### [MINOR] (completeness) `docs/adoption/mcp-adopter-contract.md` had broader pre-existing drift
Stale line-number citations and a receipts section retracted per D-055; the `audit_changed`
request-shape example showed a `domain`/`changed_paths` schema the tool never accepted, and line
80 described the pre-fix SCP-working-tree read.
**Disposition: PARTIALLY FIXED + tracked.** The two `audit_changed`-specific statements WP-SCP-038
directly touched (the request-shape example → real `base_ref`/`head_ref`/`repo_root`/`subsystem`/
`area_hint` schema; the diff-scope line → the new `repo_root`/cwd contract) are corrected in this
PR. The remaining pre-existing drift (stale line numbers elsewhere) is filed as
`FUP-WP-SCP-038-MCP-ADOPTER-CONTRACT-REFRESH-001` — not introduced by this WP and out of its
declared file scope.

## Follow-ups filed

- `FUP-WP-SCP-038-REPO-LOCAL-OUTPUT-001` — `--write-output` still targets `output_dir()` under the
  SCP tree; adopter audits should write repo-local artifacts.
- `FUP-WP-SCP-038-PROPOSE-GIT-ENV-001` — strip GIT_* location vars in `_proposal_branch_exists`
  for consistency.
- `FUP-WP-SCP-038-MCP-ADOPTER-CONTRACT-REFRESH-001` — full staleness refresh of
  `docs/adoption/mcp-adopter-contract.md`.

**Fixpoint:** R2 clean across all three lenses; the R2 MINORs are FIXED (docs) or ACCEPTED-with-
rationale (tracked FUPs). No further review round required.
