# ProgrammePlan — WP-SCP-038 audit-changed adopter-repo scoping

**Work Package:** `WP-SCP-038`
**Version:** 0.1 (Draft — authored 2026-07-05)
**Status:** DRAFT — plan + source implemented under Pattern-3 dispatch `pattern3-20260705T210025Z-34664` (D-057).
**Date kicked off:** 2026-07-05 (field defect discovered while shipping the WS-4 consumer WP in mapp-pim, PR jrnb2024/mapp-pim#615; the kg-studio WS-4 session hit the same wall earlier as SCP-MCP-E021).
**Predecessors:**
- WP-SCP-021 (MCP Server) — landed; `audit_changed` MCP tool + `_run_audit_changed_cli` shell-out live.
- WP-SCP-026 (MCP consumer integration) — landed; ADOPT-001 §13 runbook is the adopter-facing MCP surface WP-SCP-038 unblocks.
- SCP-013/014 (extractor + normaliser) — landed; the `repo_root`-aware `extract_scope` this WP finally plumbs end-to-end.

---

## 1. Purpose

The `audit-changed` plane is the executable form of the estate's **"before you finish a
change → `audit_changed` on the diff"** rule (global `CLAUDE.md`). Two field-verified defects
mean it **structurally cannot audit an adopter repo's diff** — the exact job the rule asks of it:

1. **CLI silently audits the wrong repo (the dangerous one).** `changed_audit._repo_root()`
   defaults to `resources.project_root()` — `Path(__file__).resolve().parents[2]`, i.e. **always
   the standards-control-plane checkout**. `cmd_audit_changed` never passes `repo_root`, so
   `git diff base..head` runs in the SCP repo regardless of the caller's cwd. Reproduced from
   `~/Projects/mapp-pim-ws4c`: `audit-changed --base-ref origin/main --head-ref HEAD
   --domains service-lifecycle --subsystem pim --area-id pim-enrichment` returned **score 100 /
   zero findings**, but `changed_paths` was `docs/reviews/WP-SCP-020/branch-protection-log.md` —
   SCP's own diff. A **false-clean verdict about the wrong repository**. This directly violates
   ADOPT-001 §3 / §5.2 ("keep audit local to the repo that owns the code").

2. **MCP route has no way to supply the required area hint.** The `audit_changed` MCP tool dies
   with **SCP-MCP-E021** (`AreaIdInferenceError: Unable to infer area_id from extracted scope;
   explicit area_hint required`, `normaliser._infer_area_id`). The tool schema
   (`AuditChangedRequest`) only exposes `base_ref`/`head_ref` — no `area_hint`, no `subsystem`,
   no repo root — so the error is **unrecoverable by the caller**. Ruled "manual review is the
   accepted fallback" in the kg-studio session (SCP-MCP-E021); that fallback is what this WP retires.

The CI `policy-check.yml` reusable workflow (OPA/Conftest) is a **separate plane and is NOT in
scope** — it is not broken. WP-SCP-038 touches only the CLI + MCP audit-changed plane.

## 2. Goal + success criterion

**Goal (locked 2026-07-05):**

- `audit-changed` audits the **caller's** repository by default, never the SCP checkout.
- The false-clean mode is **killed outright** — a wrong-repo / missing-ref / cwd-mismatch
  condition **fails loudly** instead of silently defaulting to `project_root()`.
- The MCP `audit_changed` tool can supply `area_hint` / `subsystem` / `repo_root`, so
  **SCP-MCP-E021 becomes recoverable** by the caller.

**Success criterion:**

- A regression test runs `audit-changed` against a **second temp git repo** and asserts
  `changed_paths` come from **that** repo (not SCP).
- A test asserts the MCP path can pass an **area hint end-to-end** (a scope that would raise
  SCP-MCP-E021 without the hint succeeds with it).
- Full suite green under the four-tier dispatch protocol; adversarial review to fixpoint.

**Anti-criterion (treat as failed / re-scope):**

- Any code path still defaulting the audit repo root to `project_root()` silently.
- The plain `audit` command (`build_audit_result`) or SCP self-dogfood audit behaviour changes.

## 3. Defect analysis + fix design

### 3.1 The plumbing gap (deeper than "just pass `repo_root` from the CLI")

The original framing was "the `repo_root` parameter already exists in the library — it's just
never plumbed from the CLI." That undercounts by one layer. The full read of the call graph:

```
cmd_audit_changed (cli.py)
  └─ build_changed_file_audit_result (changed_audit.py)   ← NO repo_root param today
       ├─ list_changed_files(repo_root=None)              ← _repo_root() → project_root()  [git diff]
       └─ build_audit_result(request)                     ← NO repo_root param today
            └─ _normalise_scope(...)                       ← calls extract_scope WITHOUT repo_root
                 └─ extract_scope(scope_paths)             ← _repo_root(None) → project_root()  [file reads]
```

Two independent `project_root()` defaults must be defeated: the **git diff** root
(`list_changed_files`) **and** the **content-extraction** root (`extract_scope`). Fixing only
the diff would leave `extract_scope` resolving adopter-relative paths under the SCP checkout —
`FileNotFoundError` at best, or (as in the repro, where the diffed file was an SCP file that
exists) another false-clean. `extract_scope` **already accepts** `repo_root` (extractor.py:91);
it is simply never passed. So the fix is a thread-through, not new extractor logic.

### 3.2 Repo-root resolution + the loud guard (kills false-clean)

New `changed_audit.resolve_audit_repo_root(repo_root, *, base_ref, head_ref, cwd=None)` +
`RepoRootResolutionError(ValueError)`:

- **Default to the caller's cwd, never `project_root()`.** This is the single change that
  removes the silent SCP default.
- **Require a git work tree.** Resolve via `git -C <root> rev-parse --show-toplevel`; normalise
  to the toplevel. Not a git repo → `RepoRootResolutionError` (loud).
- **Require both refs present** in that work tree (`git rev-parse --verify <ref>^{commit}`);
  a missing ref → `RepoRootResolutionError` naming the ref + repo (loud).
- **Refuse a cwd / repo mismatch.** If the cwd's git toplevel differs from the resolved root,
  fail loudly — the caller is standing in a different repo than the one about to be diffed
  (the exact wrong-repo footgun). Escape hatch: `cd` into the target repo (or set cwd and
  `--repo-root` to the same repo). Content extraction correctness depends on this invariant too.

`resolve_audit_repo_root` runs **only when `changed_paths` is None** (i.e. we actually shell to
git). The explicit-`changed_paths` library path (used by the existing unit test and by callers
that supply paths directly) is untouched.

### 3.3 Thread-through (backward-compatible; default `None` preserves current behaviour)

| Function | Change |
|---|---|
| `changed_audit._repo_root` | default `project_root()` → `Path.cwd()` (belt-and-suspenders for direct callers) |
| `changed_audit.build_changed_file_audit_result` | **+`repo_root: Path \| None = None`**; resolve+validate when diffing; pass validated root to `list_changed_files` **and** `build_audit_result` |
| `audit.build_audit_result` | **+`repo_root: Path \| None = None`** → `_normalise_scope` |
| `audit._normalise_scope` | **+`repo_root`** → `extract_scope(scope_paths, repo_root=repo_root)` (single `extract_scope` call; the two `normalise_project_area` invocations reuse its result) |
| `extractor.extract_scope` | **no change** — already accepts `repo_root` |

`repo_root=None` everywhere ⇒ `extract_scope` keeps its `project_root()` default ⇒ the plain
`audit` command and SCP self-dogfood are byte-for-byte unchanged.

### 3.4 CLI surface

`cmd_audit_changed` gains `--repo-root` (default: caller cwd). Threaded into
`build_changed_file_audit_result(repo_root=...)`. ADOPT-001 §10.1's recommended invocation
(run from the adopter checkout, `--base-ref origin/main --head-ref HEAD`) now audits the
adopter repo with **no flag change required** — the default is cwd.

### 3.5 MCP surface (makes SCP-MCP-E021 recoverable)

`AuditChangedRequest` gains `repo_root` / `subsystem` / `area_hint` (all optional, described).
`audit_changed_impl`:

- `repo_root = (Path(request.repo_root) if request.repo_root else Path.cwd()).resolve()`
  — defaults to the MCP server's cwd (mirrors the CLI), **not** `project_root()`. A server
  running inside the adopter workspace audits the adopter; elsewhere it fails loudly (non-git /
  missing ref) rather than silently self-auditing SCP. (R1 safety fix — see
  `docs/reviews/WP-SCP-038/r1-dispositions.md`.)
- `subsystem = request.subsystem or repo_root.name`.
- threads `repo_root` into the in-process pre-diff (`_resolve_git_commit`,
  `_list_changed_files_with_timeout` — already `repo_root`-parameterised).
- `_run_audit_changed_cli` gains `repo_root` / `subsystem` / `area_hint`, emits
  `--repo-root` / `--subsystem` / `--area-id`, and sets subprocess **cwd = repo_root** so the
  CLI's cwd-vs-repo-root guard is satisfied and `extract_scope` reads from the right tree.
- cache key folds in `repo_root` / `subsystem` / `area_hint` (they change the result).

A non-inferable scope (e.g. a lone `services.yml`) that raised SCP-MCP-E021 now succeeds when
the caller passes `area_hint`. `docs/integrations/mcp-error-codes.md` E021 remediation updated
to name the recovering fields.

## 4. Anti-scope (what WP-SCP-038 is NOT)

- **NOT** the CI `policy-check.yml` OPA/Conftest plane — explicitly out of scope, not broken.
- **NOT** a change to `resources.project_root()` — it is correct for locating SCP's *own*
  standards/schemas; only the *audit-target* roots move to cwd.
- **NOT** the `--write-output` artifact location. `output_dir()` is still `project_root()/output`,
  so an adopter audit's `--write-output` writes into SCP's tree. That is a **pre-existing** wart
  and a tracked follow-up (FUP-WP-SCP-038-REPO-LOCAL-OUTPUT-001), not part of the two verified defects.
- **NOT** a new domain/rule; no Rego, no registry version bump.

## 5. Process protocol

WP-SCP-038 follows the four-tier dispatch protocol (`feedback_four_tier_dispatch.md`):

- **Plan-doc slice (this v0.1):** Opus orchestrator drafts (docs — no dispatch needed).
- **Implementation slice:** Opus authors source under an operator-seeded Pattern-3 dispatch
  (D-057); **3× parallel Sonnet R1** review (correctness / safety_bypass / completeness_governance),
  recurse to R-fixpoint (no new blockers), no descoping. R1 must cite the CI URL + `mergeStateStatus`.
- **Self-audit:** `scp-standards.audit_changed` on the final diff before PR (dogfood).

## 6. Slice plan

| Slice | Deliverable | Decision | PR # |
|---|---|---|---|
| 038A (this) | Plan-doc v0.1 (`docs/plans/`) | D-066 (reserved) | (bundled) |
| 038B | Source + tests + doc edits (STATUS chain entry, ADOPT-001 §10.1 note, E021 remediation) | (inherits D-066) | TBD |

Delivered as one PR unless review demands a split (per `feedback_split_not_descope.md`).

## 7. Decisions reserved

- **D-066** — the false-clean kill is a **behaviour change**: `audit-changed` previously
  silent-passed against `project_root()`; it now **hard-fails** on a non-git / missing-ref /
  cwd-mismatch root, and defaults its audit target to the caller's cwd. Recorded so the
  new loud-failure contract and the `--repo-root` / MCP `repo_root`+`area_hint`+`subsystem`
  surface are governance-traceable.

## 8. Files touched

**Source (gated — needs dispatch scope):**
`src/standards_control_plane/changed_audit.py` · `src/standards_control_plane/audit.py` ·
`src/standards_control_plane/cli.py` · `src/standards_control_plane/mcp_server/tools.py` ·
`tests/test_changed_audit.py` · `tests/test_mcp_audit_changed.py` (new) · `STATUS.md` (chain entry)

**Docs (always-allowed):**
`docs/plans/WP-SCP-038-*.md` (this) · `docs/integrations/mcp-error-codes.md` (E021 remediation) ·
`docs/adoption/ADOPT-001-project-onboarding.md` (§10.1 repo-root note) · `docs/reviews/WP-SCP-038/*` ·
`docs/DECISIONS.md` (D-066 row)

## 9. Risks

1. **`build_audit_result` is shared with the plain `audit` command + MCP consult paths.**
   Mitigation: new `repo_root` param defaults to `None` ⇒ zero behaviour change when unset;
   regression covered by the existing explicit-`changed_paths` test staying green.
2. **The cwd-mismatch guard is strict** (fails on `--repo-root` pointing away from cwd).
   Mitigation: this is the directed "fail loudly" behaviour; the MCP subprocess sets
   `cwd = repo_root` so the MCP path is unaffected; documented escape hatch (`cd` first).
3. **MCP subprocess heaviness in tests** (real git + `python -m ...cli`). Mitigation: mirrors
   the existing changed_audit test pattern; unique `tmp_path` per test + cache cleared per test.
4. **`--write-output` into SCP's tree for adopter audits** (pre-existing). Mitigation: flagged
   as FUP-WP-SCP-038-REPO-LOCAL-OUTPUT-001; out of scope here to keep the fix tight.

## 10. Acceptance criteria

1. WP-SCP-038 plan-doc merged; D-066 row filed.
2. `audit-changed` with no `--repo-root`, run from an adopter checkout, audits **that** repo.
3. Non-git root / missing ref / cwd-mismatch ⇒ `RepoRootResolutionError` (loud), never a
   silent SCP default.
4. MCP `audit_changed` accepts `area_hint` / `subsystem` / `repo_root`; a scope that raised
   SCP-MCP-E021 succeeds with `area_hint`.
5. Regression test: second temp git repo ⇒ `changed_paths` from that repo. MCP area-hint
   end-to-end test green.
6. Plain `audit` command + SCP self-dogfood unchanged; full suite green; 3-lens R1 to fixpoint;
   self `audit_changed` clean on the diff.

---

**Status:** DRAFT v0.1 — 038A plan + 038B source authored 2026-07-05 under dispatch
`pattern3-20260705T210025Z-34664` (D-057).
