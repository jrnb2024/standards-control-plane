# ProgrammePlan — WP-SCP-022 Implementation Programme (federation primitive + MCP server)

**Work Package:** `WP-SCP-022`
**Version:** 0.5 (R4 fix-round — closes 1 R4 MAJ + 5 MIN + 3 nit; safety + completeness already APPROVED_WITH_FINDINGS at R4; awaiting R5 review)
**Status:** Draft — ready for Gate C round-5 review (last in 5-round budget).
**Date:** 2026-04-28
**Branch:** `feature/wp-scp-022-implementation-programme-plan`
**Programme Refs:** SCP-073 (federation primitive backlog row, WP-SCP-020), SCP-075 (MCP server backlog row, WP-SCP-021)
**Decisions introduced:** D-026 (autonomous-dispatch protocol for SCP implementation slices), D-027 (parallel-track execution policy for WP-SCP-020 + WP-SCP-021), D-028 (SCP-side adoption of D-048 / ADR-016 Design Parity Build Method)
**Decisions reserved (do not assign):** D-021 — reserved for the 2026-05-31 atomic workday per WP-SCP-019 hygiene response (PR #30, 2026-04-21). Codex executors must NOT assign D-021 to any decision filed during this WP's autonomous run.
**Predecessors:**
- `WP-SCP-020` plan v0.6 (PR #31, commit `d502bc2`) — federation primitive design.
- `WP-SCP-021` plan v0.3 (PR #32, commit `3b198a1`) — MCP server design.
- `ARCH-005` (PR #34, commit `cccd042`) — canonical event-stream rule. Note: ARCH-005 is *not* a prerequisite for the 020C rule library (WP-SCP-020 §4 020C defines exactly three v1.0.0 rules — SCP-R-001/002/003 — none of which reference ARCH-005). ARCH-005 is listed as "predecessor" only because it is the latest rule on main and forms part of the post-WP-SCP-019 governance state the implementation programme runs against.

## 1. Purpose

WP-SCP-020 and WP-SCP-021 ratified the *what* — they describe the federation
primitive and the MCP server in design detail. Neither plan specifies the
*how* of implementation: the order in which slices run, the dispatch contract
each slice flows through, the review protocol applied to each slice, the
fix-round budget before escalation, or where the autonomous chain pauses for
human review.

`WP-SCP-022` ratifies the implementation programme. It:

1. Orders the WP-SCP-020 and WP-SCP-021 implementation slices into two
   parallel autonomous-dispatch tracks, with **Track 1 ordering matching
   WP-SCP-020 §3 verbatim** (no resequencing, no omissions).
2. Names the per-slice dispatch package contract — input, scope boundary,
   verify commands, evidence persistence — bound to the canonical
   `codex_work_package.schema.json` (ACC repo, blob SHA pinned in §6).
3. Names the per-slice review protocol — 3× Sonnet R1 in three lenses
   (correctness / safety_bypass / completeness_governance), parallel-dispatch
   with 500 ms stagger, fix rounds R(F), R(F+1), … recursing to fixpoint per
   `feedback_recursive_adversarial_review.md`, with explicit
   APPROVED_WITH_FINDINGS(MIN/nit-only) handling.
4. Names the user-gate checkpoints with **concrete artefact requirements**
   (signed `release-signoff.md`, `USER-GATE-A.md`, `USER-GATE-C.md`) so
   gate enforcement is non-discretionary.
5. Names the failure-mode handling — fix-round budget, OAuth-refresh path,
   escalation when fixpoint can't be reached, working-tree cleanup.
6. Names the stability prereqs for the *FLA pilot* gate (020I, deferred
   to follow-up WP per WP-SCP-020 §4.1) without blocking this WP on them.

This plan is a **process artefact** — it does not deepen the rule library,
ship code, or change estate adoption posture. It is the canonical reference
that subsequent slice dispatches cite for their dispatch shape.

## 2. Invariants and what this is NOT

### Invariants

1. **Every implementation slice flows through four-tier dispatch.** Opus
   orchestrator (this agent) prepares the dispatch package; Codex executor
   tier runs the slice; 3× parallel Sonnet R1 reviewers apply the three
   adversarial lenses; Opus consolidates verdicts and orchestrates fix
   rounds. No slice merges without 3× APPROVED — or APPROVED_WITH_FINDINGS
   where every finding is MIN or nit (§4.3).
2. **Adversarial review never descopes.** Per
   `feedback_recursive_adversarial_review.md`, recurse until no new
   blockers; reviewers never recommend descoping.
3. **Reusable workflow (020B) ships SHA-pinned, not version-pinned, by
   default.** `@v1` shorthand is documented but the canonical guidance in
   ADOPT-001 §12 is SHA pin + Renovate to bump (per WP-SCP-020 §4 020F).
4. **OPA Rego rules and existing Python evaluators are both authoritative
   in their own domain.** Disagreement blocks merge pending human
   adjudication (per WP-SCP-020 §4 020C.1.iii / D-022 rationale). This
   invariant is inherited verbatim, not redefined.
5. **MCP receipts are advisory, never gating.** Per WP-SCP-021 D-025
   invariant: federation gate (WP-SCP-020) is server-side authority;
   client-side hooks consuming MCP receipts catch agents that don't
   consult, but a receipt is never a gate bypass.
6. **Tracks are independent.** Track 1 (WP-SCP-020 implementation) and
   Track 2 (WP-SCP-021 implementation) progress in parallel; no slice in
   one track blocks a slice in the other.
7. **User-gate checkpoints pause the chain via committed artefacts.**
   USER-GATE-A0 (release sign-off), USER-GATE-A (post-self-enforcement),
   USER-GATE-C (post-021E MCP scaffold) each require a **named, dated,
   human-authored artefact** committed to the SCP repo before the chain
   advances. Opus orchestrator MUST verify the artefact's existence and
   signature before dispatching the next slice. Bypass is detected by the
   gate-enforcement helper at §4.7.
8. **Evidence persists in-repo.** Every dispatch's package, stdout,
   structured review JSON, consolidation note, and fixpoint record land
   under `docs/reviews/WP-SCP-022/dispatches/<slice-id>/` so the audit
   trail survives across sessions. **Dispatch packages are committed to
   the slice's feature branch BEFORE dispatch** (closes R1
   CRIT-BYPASS-002 — no /tmp staging).
9. **Reviewer findings entering Codex prompts are sanitized.** Free-text
   `claim`, `evidence`, `impact`, `mitigation` fields are passed through
   `scripts/sanitize_review_finding.py` before being inlined into a
   fix-round dispatch package. Sanitization: strip control characters
   (`\x00-\x1F\x7F`), escape backticks, length-cap each field at 2000
   chars with truncation marker, encode as a JSON-string literal. Closes
   R1 CRIT-BYPASS-004.
10. **ACC scripts and schemas are pinned by git SHA.** §6 pins ACC repo
    HEAD + blob SHAs of the five dispatcher artefacts at plan-merge time.
    Any drift is detected at slice-dispatch time by a SHA verify step;
    drift = pause for user review. Closes R1 MAJ-BYPASS-005.

### What this is NOT

- Not a redefinition of WP-SCP-020 or WP-SCP-021 scope. Slice content,
  decision records, and acceptance criteria are inherited from the parent
  plans. WP-SCP-022 only governs *how the slices run*.
- Not a new rule. No rules added, removed, or amended. ARCH-005 is on
  main but is not a prerequisite for any slice in this WP.
- Not an estate-rollout WP. Estate cascade is `WP-SCP-024`, deferred.
- Not a new dispatcher. Uses the canonical scripts at
  `~/Projects/acc/scripts/{codex_dispatch.py,claude_dispatch.py}`. If the
  dispatcher itself needs changes (e.g. session_id surfacing per §4.3
  finding C-MAJ-04), that's an ACC-repo PR and is out-of-scope here;
  see FUPs-022 below.
- Not a substitute for direct human review on user-gate checkpoints.
  Pause points exist precisely because the artefacts produced there
  (v1.0.0 release tag; required-check-on-main; MCP scaffold) have
  downstream contracts that outlive the autonomous run.
- Not a fix for dispatcher-level scope-boundary post-hoc enforcement
  (CRIT-BYPASS-001 partially mitigated; full closure requires ACC
  changes — see FUPs-022).

## 3. Programme protocol position

Follows `PROG-SCP-001-autonomous-execution-plan.md`, with the following
amendments specific to WP-SCP-022:

- **One PR per slice, not one PR per WP.** The parent plans (020 / 021)
  already specified per-slice PRs (020 §9.15). WP-SCP-022 makes that
  concrete: each slice is its own merged PR; the WP-SCP-022 plan PR itself
  closes when this document is merged.
- **Slices run on dedicated `feature/wp-scp-0NN<slice-id>-<short-name>`
  branches.** Branch names are deterministic so the dispatcher can recreate
  them; e.g. `feature/wp-scp-020b-reusable-workflow`.
- **Evidence directory is split** between parent-plan deliverable artefacts
  and dispatch artefacts:
  - **Parent-plan deliverables** (named in WP-SCP-020 §11 / WP-SCP-021 §11)
    land at the location named by the parent plan (e.g.
    `docs/reviews/WP-SCP-020/canary-evidence.md`,
    `docs/reviews/WP-SCP-020/release-signoff.md`,
    `docs/reviews/WP-SCP-020/branch-protection-log.md`).
  - **WP-SCP-022 dispatch artefacts** land at
    `docs/reviews/WP-SCP-022/dispatches/<slice-id>/` containing per-slice
    dispatch package + Codex transcript + 3× review JSONs + consolidation
    + fix-round artefacts + fixpoint record.
  - The slice's dispatch package's `instruction` field tells Codex which
    parent-plan path to write a given deliverable to, eliminating
    ambiguity at execution time.

### Slice ordering — Track 1 (WP-SCP-020 federation primitive)

**Verbatim from WP-SCP-020 §3 canonical ordering. No reordering, no
omissions.** Order is canonical; slices may not be reordered without
amending both this plan and WP-SCP-020.

In autonomous-run scope (Scope Y per user 2026-04-28 selection):

1. **020B** — Reusable GitHub workflow (`.github/workflows/policy-check.yml`).
2. **020B.1** — Workflow integration test harness (`tests/workflow/fixture-pass/` + `fixture-fail/`).
3. **020B.2** — Local reproduction (`scripts/scp-policy-check` + `python -m standards_control_plane.policy_check`).
4. **020C** — Starter Rego rule library (exactly 3 rules: SCP-R-001/002/003) + `policies/README.md` complete.
5. **020C.1** — Waiver-aware Rego + Python/Rego conflict-gate (adapter + fixture tree).
6. **020J** — SCP tag-protection rule for `v*` + required-signed-commits on `main`. **PRECONDITION for 020D1.**
7. **020K** — `CODEOWNERS` wiring (personal-account / single-operator mode per WP-SCP-020 §14 U-k). **PRECONDITION for 020D2.**
8. **020D1** — SCP self-dogfood wrapper merged on SCP self (signed commit; required check NOT yet enabled).
9. **020H part 1** — Cut `v1.0.0-rc.1` tag from the 020D1 merge commit. Release notes enumerate 3 rules + error codes SCP-E001–E006 + known limitations.
10. **020E.a** — **SCP-self pre-protection canary**. Committed fixture branch `canary/deliberate-violation-pre` with deliberate Rego violation; failing `gh pr view --json` dump stored; failing workflow-run-id recorded; cold-start + warm-start wall-clock times recorded. Evidence in `docs/reviews/WP-SCP-020/canary-evidence.md`. (NOT FLA pin work; that's deferred slice 020I per WP-SCP-020 §4.1.)

**[USER-GATE-A0]** — Release sign-off pause. Human signs
`docs/reviews/WP-SCP-020/release-signoff.md` (named signer + timestamp +
canary-run-id reference) per WP-SCP-020 §4 020H part 2 governance
requirement. Chain advances ONLY after the artefact lands committed on
main. Gate-enforcement helper (§4.7) verifies artefact presence and
named-signer line before dispatching slice 11.

11. **020H part 2** — Promote `v1.0.0-rc.1` → `v1.0.0`. Release governance recorded in the signed-off `release-signoff.md`.
12. **020D2** — Enable required status check on SCP `main`. `scp/policy-check` required with `enforce_admins=true`; `required_approving_review_count=1`; `dismiss_stale_reviews: true`; `require_review_from_non_author=false` per 020K solo-operator outcome (bus-factor-1 accepted in WP-SCP-020 §8). Break-glass procedure published in ADOPT-001 §12 — three-gate model per 020B(viii-c).

**[USER-GATE-A]** — Post-self-enforcement review pause. Human authors and
commits `docs/reviews/WP-SCP-022/gates/USER-GATE-A.md` recording (a) PR
URLs of all 12 Track 1 slices; (b) green status of the new required
check on a representative SCP-self PR after 020D2 lands; (c) any
operational concerns to address before continuing post-pause.

Track 1 deferred to post-pause continuation (FUP WP, not this WP):
- **020E.b** post-protection canary; **020E.c** waiver-suppression canary
- **020F** Renovate shared preset
- **020G** branch-protection automation
- **020H part 3** ADOPT-001 §12 adopter guide
- **020H.1** versioning + rule-RFC + rollback detection
- **020I** FLA pilot (gated on §7 stability prereqs)

### Slice ordering — Track 2 (WP-SCP-021 MCP server)

Independent of Track 1; runs in parallel.

In autonomous-run scope:

1. **021B** — MCP server scaffold via Python `mcp` SDK + Ed25519 keygen + PyPI publish as `standards-control-plane[mcp]` extra.
2. **021C** — Tools (`consult_rules`, `check_waiver`, `list_open_decisions`, `check_finding`, `audit_changed`, `resolve_domain`, `propose`) + error taxonomy (SCP-MCP-E0NN).
3. **021D** — Resources (`scp://rules/registry`, `scp://decisions`, `scp://findings/open`, `scp://waivers`, `scp://status`, `scp://security/signing-keys`, etc.) + domain-map.
4. **021E** — `propose()` stub with anti-spam + silent-rot banner.

**[USER-GATE-C]** — MCP scaffold review pause. Human authors and commits
`docs/reviews/WP-SCP-022/gates/USER-GATE-C.md` recording (a) PR URLs of
all 4 Track 2 slices; (b) `scp-mcp-server` installable from PyPI;
(c) Ed25519 public key published at `scp://security/signing-keys` and
mirrored at `docs/security/mcp-signing-keys.pub`.

Track 2 deferred to post-pause continuation:
- **021F** ADOPT-001 §13 adopter guide
- **021G** ACC integration stub
- **021H** HTTP transport
- **021I** auth + token rotation + OVERRIDE schema
- **021J** hash-chained observability
- **021K** self-consume evidence on post-020C PR

### Autonomous run scope (this WP)

Per the user's 2026-04-28 Scope Y selection:

- Track 1: 020B → 020B.1 → 020B.2 → 020C → 020C.1 → 020J → 020K → 020D1
  → 020H part 1 → 020E.a → **[USER-GATE-A0]** → 020H part 2 → 020D2 →
  **[USER-GATE-A]**. Total 12 implementation slices + 1 mid-chain
  human-input gate + 1 terminal gate.
- Track 2: 021B → 021C → 021D → 021E → **[USER-GATE-C]**. Total 4
  implementation slices + 1 terminal gate.

End state: SCP enforces its own Rego gate on its own `main`; MCP server
scaffold + tools + resources + propose-stub are installable from PyPI
with public verification key.

## 4. Scope

### 4.1 Per-slice dispatch package contract

Each slice produces exactly one dispatch package conforming to
`~/Projects/acc/schemas/codex_work_package.schema.json` (blob SHA pinned
in §6). Required fields and their slice-level conventions:

- **`package_id`** — `wp-scp-<NNN><slice-id>` (lower-snake), e.g.
  `wp-scp-020b-reusable-workflow`. Deterministic so logs land in
  predictable paths.
- **`instruction`** — narrative task definition. Cites the parent slice
  text by file path + section + line range (e.g. "Implement WP-SCP-020 §4
  slice 020B as defined in
  `docs/plans/WP-SCP-020-policy-federation-primitive.md` §4 line 113").
  Includes the explicit acceptance criteria from the parent plan inlined
  as a checklist, and the parent-plan path for any deliverable artefact
  the slice produces (so Codex knows the canonical write target).
- **`spec_paths`** — array of repo-relative paths Codex must read first.
  Always includes the parent WP plan, the relevant ADOPT-001 sections,
  and any rule files the slice references.
- **`scope_boundary`** — fnmatch globs listing every file Codex may
  create/modify/delete. Tight scoping is mandatory; over-broad scoping
  fails review (see §4.2 lens 2). **Symlink note:** `codex_dispatch.py`
  enforces scope_boundary post-hoc and does not currently resolve
  symlinks. Slices MUST NOT include `**` globs that span the repo root;
  symlinks within the working tree pointing outside scope are detected
  by the gate-enforcement helper at §4.7 (`scripts/wp_scp_022_gate_check.sh --slice <slice-id>`).
- **`verify_commands`** — non-empty array. Always includes `pytest` for
  the relevant test path; for workflow slices includes `actionlint` (or
  workflow-syntax linter); for Rego slices includes `conftest verify` +
  `opa test`.
- **`timeout_seconds`** — default 1800 (30 min); kernel-dangerous slices
  (020J tag-protection) use 3600.
- **`reasoning_effort`** — `medium` for scaffolding slices; `high` for
  slices touching Rego semantics (020C, 020C.1) or signing (021B Ed25519);
  `xhigh` reserved for any slice that touches branch-protection automation
  (020G — deferred post-pause; not in this autonomous run).
- **`model`** — null (Codex default `gpt-5.4`) for all slices in this WP.
- **`project_name`** — `"standards-control-plane"`.

**`pyproject.toml` partition (closes R1 MAJ-BYPASS-006):**
- Track 1 (020) owns `[tool.scp.federation]` (config keys for the
  federated workflow) and adds `scp-policy-check` to `[project.scripts]`.
- Track 2 (021) owns `[project.optional-dependencies.mcp]` and adds
  `scp-mcp-server` to `[project.scripts]`.
- `[project.scripts]` is shared by partition: each track only adds
  *new* entries with disjoint name prefixes; neither track edits the
  other's entry. Codex executors are explicitly told this in the
  instruction field.

**Other shared files:**
- `docs/STATUS.md` — touched only at slice-merge time by the orchestrator
  (Opus), never by Codex during execution. Slice scope_boundary MUST NOT
  include `docs/STATUS.md` (closes R1 nit-BYPASS-014).
- `CHANGELOG.md` — does not exist yet; created once during slice 020H
  part 1 (rc.1 cut), thereafter only the active track's slice may append.
- `requirements.txt` / `requirements-dev.txt` — partitioned by track
  (Track 1 entries live in `requirements.txt`; Track 2 entries live in a
  new `requirements-mcp.txt` keyed off the optional-dependencies group).

Dispatch packages live at
`docs/reviews/WP-SCP-022/dispatches/<slice-id>/dispatch-package.json`
and are **committed to the slice's feature branch BEFORE dispatch** so
the package is part of the audit trail. Closes R1 CRIT-BYPASS-002.

### 4.2 Per-slice review protocol

After Codex returns a successful dispatch, the orchestrator builds three
review packages:

- **Lens 1 — correctness.** Does the slice implement the parent plan's
  acceptance criteria? Are tests adequate? Are edge cases covered?
- **Lens 2 — safety_bypass.** Can an adopter (intentionally or not)
  bypass the gate? Are scope boundaries respected (including
  symlink/glob checks)? Are secrets/keys handled correctly? Can a
  malicious workflow input subvert the evaluator?
- **Lens 3 — completeness_governance.** Are decision records updated?
  Is documentation in sync with code? Is the slice consistent with the
  parent plan's invariants? Are downstream slices' assumptions still
  valid after this change?

Each review package is dispatched via `claude_dispatch.py` with a 500 ms
stagger between launches:

```
claude_dispatch.py --package docs/reviews/WP-SCP-022/dispatches/<slice-id>/review-correctness.json --cwd /Users/amplience/Projects/standards-control-plane &
sleep 0.5
claude_dispatch.py --package docs/reviews/WP-SCP-022/dispatches/<slice-id>/review-safety.json --cwd /Users/amplience/Projects/standards-control-plane &
sleep 0.5
claude_dispatch.py --package docs/reviews/WP-SCP-022/dispatches/<slice-id>/review-completeness.json --cwd /Users/amplience/Projects/standards-control-plane &
wait
```

Note: review packages are committed in-repo, NOT staged in `/tmp`
(closes R1 CRIT-BYPASS-002).

Each reviewer returns a `SonnetReviewResult` JSON conforming to
`~/Projects/acc/schemas/sonnet_review_result.schema.json` (blob SHA
pinned in §6).

### 4.3 Verdict consolidation and fix-round protocol

After all three reviews return, the orchestrator consolidates per the
following decision table:

| Verdict combination | Action |
|---------------------|--------|
| All three APPROVED | Fixpoint reached → slice merges. |
| All three either APPROVED or APPROVED_WITH_FINDINGS where every finding is MIN or nit (no CRIT, no MAJ) | Fixpoint reached → slice merges; MIN/nit findings recorded in `fixpoint.md` as known-acceptable issues. |
| Any reviewer returns CHANGES_REQUESTED **OR** any APPROVED_WITH_FINDINGS contains a CRIT or unmitigated MAJ | Fix round R(F) triggered. |

Fix-round dispatch:

- The orchestrator builds a new Codex dispatch package containing:
  (a) the original instruction; (b) the consolidated findings list with
  every CRIT + MAJ finding's `claim`, `evidence`, `impact`, `mitigation`
  fields **passed through `scripts/sanitize_review_finding.py`** (closes
  R1 CRIT-BYPASS-004 — strip control characters, escape backticks,
  length-cap each field at 2000 chars, JSON-string-encode); (c) the
  acceptance criterion that the fix round must close ("close all CRIT;
  mitigate every MAJ in-PR or escalate").
- **Session resumption (`resume_session_id`) is NOT used in v1 of this
  protocol.** The Codex dispatcher result schema does not surface the
  Codex CLI's session_id in a stable field (see FUP-022-01). Fix rounds
  re-dispatch fresh; Codex re-reads spec_paths; consolidated findings
  list is the substitute for session memory. Re-execution cost is
  bounded by the 5-round budget below.
- The same three reviewers re-run their lens against the fixed code.
  Reviewers do NOT see the consolidated findings list or the fix-round
  prompt — only the resulting code. Reviewer-independence note:
  reviewers may incidentally observe finding-IDs in code comments
  (R1 MIN-BYPASS-013); fix-round dispatch packages instruct Codex to
  NOT quote finding-IDs verbatim into code or commit messages.
- Recurse R(F+1), R(F+2), … until the verdict combination satisfies the
  fixpoint criteria above.

**Fix-round budget:** 5 rounds. After 5 rounds without fixpoint, the
slice is escalated to user review (paused, not merged). On budget
exhaustion, the orchestrator commits a `escalation.md` to
`docs/reviews/WP-SCP-022/dispatches/<slice-id>/` enumerating: the round
sequence, every finding raised at each round, the claimed fix at each
round, the working-tree state on the slice's feature branch (`git
status` + `git diff --stat` snapshot). The user can then either:
re-scope the slice, raise the budget for that slice with explicit
reasoning, or escalate to direct Opus implementation.

**Working-tree cleanup on escalation (closes R1 MIN-BYPASS-012):** if
the escalated slice has uncommitted Codex edits, the orchestrator runs
`git diff > docs/reviews/WP-SCP-022/dispatches/<slice-id>/escalation-uncommitted.diff`
then `git checkout -- .` to return the working tree to the last commit.
The diff is preserved in the audit trail.

### 4.4 Track parallelism

Tracks 1 and 2 run concurrently from the start. Concretely: 020B and 021B
are dispatched in the same wall-clock window; both proceed independently;
their reviews run in parallel against each other. Concurrent-dispatch
limit: 4 active Codex sessions across both tracks (1 active slice per
track + 3 review-side claude sessions per track is well within rate
limits per the field report 2026-04-22).

### 4.5 Evidence persistence + size limits

For each slice the following lands in
`docs/reviews/WP-SCP-022/dispatches/<slice-id>/`:

- `dispatch-package.json` — exact package handed to Codex.
- `codex-stdout.txt` — Codex full transcript. **Size cap 5 MB**;
  excess truncated with `... [TRUNCATED at 5MB; full log at <log_dir>]`
  marker, where `<log_dir>` is the dispatcher's
  `.acc/codex-dispatch-log/<package_id>/` path. Closes R1 MAJ-BYPASS-010.
- `verify-output.txt` — `verify_commands` output. Size cap 1 MB.
- `review-{correctness,safety,completeness}.json` — each reviewer's
  structured output. Size cap 2 MB each; oversized reviews fail the
  consolidation step and require user inspection.
- `consolidation-r0.md` — orchestrator's verdict consolidation for the
  initial review pass.
- `fix-round-N/dispatch-package.json` + `fix-round-N/codex-stdout.txt`
  + `fix-round-N/review-*.json` + `fix-round-N/consolidation.md` for
  each fix round.
- `fixpoint.md` — terminal record: round count, total wall time,
  cumulative review spend, links to all artefacts. Hash chain of
  reviewer JSONs included as machine-verifiable signature in a
  `## sha256_chain` block with leaves `correctness:`, `safety:`,
  `completeness:` (each `sha256(<file>)` of the **terminal-round**
  reviewer-result JSON) and root `chain:`
  (`sha256(correctness || safety || completeness)`). The terminal
  round is the highest-numbered `fix-round-N/` directory if any
  exist, else the initial round whose JSONs are at
  `<dispatch-dir>/review-{correctness,safety,completeness}.json`
  (per §4.2 — implementation slices use this flat layout). The
  `--check-hash-chain` mode of `scripts/wp_scp_022_gate_check.sh`
  operates on **implementation slices only** (the flat layout under
  `docs/reviews/WP-SCP-022/dispatches/<slice-id>/`). The WP-SCP-022
  plan-slice itself is the only review pack using the
  `r{N}-{lens}/dispatcher-result.json` layout per §11; that pack is
  not verified by the gate helper and is inspected manually
  (closes R4 C-MIN-01). Closes R1 CRIT-BYPASS-003 partially; full
  closure when 020G branch-protection automation lands post-pause.

**Content sanitization:** before commit, the orchestrator strips
NUL bytes from any reviewer JSON or Codex transcript and verifies the
file is valid UTF-8. Any decode failure escalates to user review.

### 4.6 D-048 / DPBM SCP-side adoption

The Design Parity Build Method estate doctrine (CT D-048, ACC ADR-016)
opens 2026-04-28. SCP files **D-028** as part of this WP, adopting DPBM
as a contract input for any slice that produces designed visual output.

Within WP-SCP-022 itself no slices produce visual output (they are
workflow, Rego, MCP-server, and CI work), so D-028 is a forward-looking
declaration rather than an immediate operational change.

**Enforcement injection mechanism (closes R1 MIN-BYPASS-011):** when a
future slice is identified as producing designed visual output (per the
DPBM applies-criteria), its dispatch package's `instruction` field MUST
include a "DPBM contract" subsection naming the prototype path, flow
diagram, and design-principles reference the build is bound to. The
orchestrator verifies the subsection is present before launching the
review pass; absence is treated as a CRIT finding and triggers fix
round.

D-028 lands operationally once CT PR #202 + ACC PR #106 have merged
and the canonical doctrine path is stable.

### 4.7 Gate-enforcement helper (`scripts/wp_scp_022_gate_check.sh`)

Closes R1 CRIT-BYPASS-003 (no hard-stop on 3× APPROVED) and
MAJ-BYPASS-009 (user-gate discretion).

A small bash helper at `scripts/wp_scp_022_gate_check.sh` (created in
slice 022A by Opus, NOT dispatched) is invoked by the orchestrator
before every slice dispatch and at every gate transition. It checks:

1. **Gate artefact existence + content.** For USER-GATE-A0, verify
   `docs/reviews/WP-SCP-020/release-signoff.md` contains all three of:
   a `Signed:` or `Signer:` line, an ISO-8601 timestamp line, and a
   canary-run-id line (per WP-SCP-020 §4 020H part 2 governance
   requirements). For USER-GATE-A / USER-GATE-C, verify the named
   artefact under `docs/reviews/WP-SCP-022/gates/` exists and contains
   a `Signed:` or `Signer:` line. **Defence-in-depth on signer
   identity** (see §8 R-022-12): the gate-artefact commit's author
   email is verified via `git log -1 --format=%ae <gate-artefact-path>`
   to match the configured operator address (default `jrnb2024@…`).
   Cryptographic signing is not in scope for v1.
2. **3× APPROVED hash chain.** For each merged slice, the helper's
   `--check-hash-chain <slice-id>` mode reads
   `docs/reviews/WP-SCP-022/dispatches/<slice-id>/fixpoint.md`,
   extracts the `sha256_chain:` block, and recomputes the chain over
   the three `dispatcher-result.json` files of the terminal review
   round. Mismatch = exit non-zero. The orchestrator runs this check
   immediately before opening the slice's PR and again before chaining
   the next slice.
3. **Symlink escape detection.** `--slice <slice-id>` mode enumerates
   symlinks in the working tree (excluding `.git`). For each link, the
   helper resolves the target portably via `python3 -c "import os; print(os.path.realpath(...))"`
   to handle macOS `readlink` lacking the `-f` flag (closes R2
   BYPASS-004). Targets outside the repo root = exit non-zero. Targets
   to non-existent paths emit a WARN line and exit non-zero (dangling
   symlinks are treated as escapes — the workflow has no business
   creating them).
4. **Decision-ID collision.** `--check-d021` mode greps DECISIONS.md
   for `^\| D-021 \|`. Absent = OK (reserved slot still empty). Present
   with date `2026-05-31` = OK (canonical atomic-workday filing).
   Present with any other date = exit non-zero.
5. **ACC pin drift.** `--check-acc-pin` reads
   `docs/reviews/WP-SCP-022/acc-pin-manifest.json` and verifies each
   blob SHA against `git -C $HOME/Projects/acc ls-tree HEAD <path>`.
   Drift on any blob = exit non-zero. Missing prerequisites (`jq`,
   ACC repo not a git directory) = exit non-zero (no silent skip;
   closes R2 C-R2-005).

The helper exits non-zero on any failure; orchestrator pauses the
chain and emits a notification. Exit codes: `0` pass, `1` artefact /
content missing, `2` symlink escape, `3` D-021 collision, `4` ACC
pin drift, `5` hash-chain mismatch, `6` missing prerequisite, `10`
invalid invocation. The bash `set -euo pipefail` preamble prevents
silent failures inside the helper itself; if `git rev-parse
--show-toplevel` fails, the helper exits with code 6 rather than
falling back to `$(pwd)` (closes R2 BYPASS-008).

## 5. Out of scope

- Estate-wide rollout beyond SCP self-dogfood (= `WP-SCP-024`).
- Second/third canary repos beyond SCP self (`WP-SCP-024`).
- FLA pilot (= 020I, deferred to `WP-SCP-020.1` per WP-SCP-020 §4.1;
  gated on §7 stability prereqs).
- MCP server post-self-dogfood completion (021F adopter guide, 021G ACC
  integration, 021H HTTP transport, 021I auth + token rotation, 021J
  observability, 021K self-consume — slated for post-pause continuation
  WP).
- Proposal-queue adjudication workflow (= future WP, separately tracked).
- Cross-repo decision-record aggregation (= `SCP-075-crossrepo`).
- Scorecards dashboard (= `WP-SCP-023`).
- Any change to the four-tier dispatch scripts in ACC. If a change is
  needed (e.g. session_id surfacing), file an ACC PR; this WP uses the
  dispatch scripts as-is.
- Operational filing of D-021 (2026-05-31 atomic workday — owned by
  WP-SCP-019 hygiene response, calendar-driven).
- Mid-May ADOPT-001 §11.5 callout removal (CT-flip-triggered, separate
  small follow-up PR per `project_scheduled_followups.md`).

## 6. External dependencies (pinned by git SHA)

ACC repo HEAD pinned at plan-merge time:
`b253363f38ccb7f0278ebde993c33117897e9aab`.

Blob SHAs:
- `scripts/codex_dispatch.py` blob `9d2083d88725d5feecb5982a645ecb00c0820816`.
- `scripts/claude_dispatch.py` blob `805e86c3b80c0a5e3ba2789e80dc578d0ed17a30`.
- `schemas/codex_work_package.schema.json` blob `2320352c3140f9dbbc6f1881c6b7ad6f4d3f1f01`.
- `schemas/codex_dispatch_result.schema.json` blob `17a083351f6eba37bd322cf609a7d930724aab4c`.
- `schemas/sonnet_review_result.schema.json` blob `9300aa6da4479dfc66cc10fad59ec7c5c71b45af`.

These SHAs are written into
`docs/reviews/WP-SCP-022/acc-pin-manifest.json` at plan-merge time.

**Manifest integrity (closes R3 BYPASS-005 carry-forward):** the pin
manifest path is added to `CODEOWNERS` (slice 020K). Note that
`CODEOWNERS` alone does not block PRs — branch-protection must also
set `require_code_owner_reviews: true` for the rule to be enforced
gate-side. WP-SCP-020 §4 020D2 sets this on SCP `main` (it is part of
the standard required-status-check configuration applied at 020D2),
so from 020D2 onward any change to the manifest requires CODEOWNERS
approval before merge. The window from 020K landing through 020D2
landing remains operator-vigilance-only. The chain only reaches 020D2
after 020E.a + 020H part 2 (release sign-off) so a tampered pin
discovered between 020K and 020D2 surfaces as obvious dispatcher
failures (drift detection in §4.7 helper); accepted residual.
(Closes R4 F-R4-001.)

**Drift detection:** `scripts/wp_scp_022_gate_check.sh` (per §4.7)
verifies each blob SHA against the live ACC working tree before each
dispatch. Drift → pause for user review (manual reconciliation: either
re-pin to new SHAs in this plan, file an amending decision, or revert
the ACC change).

**OAuth sessions** — `codex` and `claude` CLIs require live OAuth
sessions. If `codex` or `claude` returns 401/expired/invalid_grant
mid-run, the chain pauses and emits a notification to refresh sessions
per `reference_four_tier_dispatch.md` smoke-test commands. Closes R1
MAJ-BYPASS-008 partially: cached state from before refresh is
discarded by re-dispatching the slice fresh (resume_session_id NOT used
per §4.3).

**GitHub Actions** — for the reusable workflow slice (020B); requires
the SCP repo's existing GitHub App / PAT configuration.

**OPA/Conftest** — installable from `open-policy-agent/conftest`
releases; pin via Renovate digest (slice 020B/020B.2 work).

## 7. Rollout prerequisites for FLA pilot (post-pause, NOT this WP)

These prereqs gate `WP-SCP-020.1` (FLA pilot, slice 020I) and the
follow-up `WP-SCP-024` (estate cascade). They remain explicitly
captured here so that USER-GATE-A reviewer can verify them when
deciding whether to authorise the FLA-pilot follow-up WP.

1. **FLA economical** — close but not absolutely there as of 2026-04-28
   (active INFRA-058 through INFRA-063 work).
2. **`ct-auth` Go SDK landed** — `ct-events-go` SDK transplanted into
   Recommender 2026-04-28 (CT PR #201) is the second SDK iteration; the
   `ct-auth` Go SDK specifically is still pending.
3. **CT implementation lessons absorbed** — covered by the ongoing CT
   Phase 2/3 events programme post-mortem.

WP-SCP-022 builds the primitive and self-dogfoods regardless. Only the
post-pause FLA-pilot continuation waits on these prereqs.

## 8. Risks (specification, not reassurance)

- **R-022-01 — OAuth session expires mid-run.** Both Codex and Claude
  OAuth tokens have finite lifetimes. Mitigation: pause-on-401, emit
  notification, require user `codex login` / interactive `claude` to
  refresh. Run-state recovered by fresh re-dispatch (no
  resume_session_id per §4.3).
- **R-022-02 — Reviewer drift.** A reviewer may give a soft APPROVED on
  later rounds because it sees its own prior findings closed. Mitigation:
  reviewer prompts include "you have not reviewed this code before;
  apply the lens fresh"; review packages do not include prior findings
  text; reviewer JSONs are independent inputs to consolidation.
- **R-022-03 — Codex over-broad edits.** A scope-boundary glob set too
  loose could let Codex edit files outside intent. Mitigation: dispatch
  packages cite both file globs *and* the parent-plan slice text;
  `codex_dispatch.py` enforces scope_boundary post-hoc;
  `scripts/wp_scp_022_gate_check.sh` adds symlink-escape detection
  (§4.7). **Residual risk:** scope_boundary enforcement remains
  post-hoc (CRIT-BYPASS-001 partial mitigation only); full closure
  requires ACC dispatcher change tracked as `FUP-022-02`.
- **R-022-04 — Concurrent track race.** Tracks 1 and 2 may both modify
  shared files (e.g. `pyproject.toml`, `docs/STATUS.md`). Mitigation:
  partition rules in §4.1; `pyproject.toml` partitioned across
  `[tool.scp.federation]` (T1) and `[project.optional-dependencies.mcp]`
  (T2); `[project.scripts]` partitioned by name prefix; `STATUS.md`
  touched only at slice-merge time by orchestrator.
- **R-022-05 — Fix-round explosion.** A pathological slice runs the
  5-round fix budget with no convergence. Mitigation: budget cap pauses
  the chain; working-tree cleanup per §4.3; user re-scopes or escalates.
- **R-022-06 — Plan staleness.** WP-SCP-020 / 021 reference rules,
  decisions, or files that have moved between plan land (2026-04-21) and
  slice dispatch. Mitigation: each slice's dispatch package re-reads the
  parent plan's spec_paths first; if a referenced path is missing, the
  slice fails verify_commands and pauses.
- **R-022-07 — Review-cost runaway.** Three reviewers per slice ×
  potentially 5 fix rounds × 16 slices = up to 240 review dispatches.
  Mitigation: per-slice cap **$30** (all review rounds combined);
  aggregate cap **$300** for the full autonomous run. On overrun, the
  chain pauses and Opus emits a cost-cap notification. Review cost
  recorded in `fixpoint.md` per slice.
- **R-022-08 — Two open PRs collide on `docs/STATUS.md`.** PR #35
  (governance refresh) and the WP-SCP-022 plan PR both touch STATUS.md.
  Mitigation: WP-SCP-022 plan PR rebases on top of #35 once #35 lands;
  or vice versa. Either order is reconcilable as the diffs do not
  overlap line-by-line.
- **R-022-09 — 2026-05-31 D-021 atomic workday concurrent with
  Track 1.** D-021 amending decision lands on main while autonomous
  chain may be running Track 1 slices that touch DECISIONS.md (e.g.
  conflict-gate adjudication in 020C.1). Mitigation: §4.7 gate helper
  detects D-021 collision; D-021 reservation noted in §1 + DECISIONS.md;
  D-021 filing scheduled for the day-window 2026-05-31; Track 1
  scheduling coordinated to avoid in-flight DECISIONS.md edits on that
  date.
- **R-022-10 — Mid-May ADOPT-001 §11.5 callout removal concurrent with
  in-flight ADOPT-001 edits.** Track 1 020H part 3 (post-pause) edits
  ADOPT-001 §12; Track 2 021F (post-pause) edits ADOPT-001 §13. Both
  are post-pause and not in this WP's autonomous scope, so this WP is
  unaffected. Captured here for the post-pause continuation WP.
- **R-022-11 — Dispatcher result schema does not surface session_id.**
  Closes R1 C-MAJ-04. Mitigation: §4.3 specifies fix rounds
  re-dispatch fresh without resume_session_id; FUP-022-01 tracks the
  ACC change to surface session_id.
- **R-022-12 — User-gate bypass via context-compressed Opus session.**
  Closes R1 MAJ-BYPASS-009. Mitigation: §2 invariant 7 + §4.7 gate
  helper require committed artefact verification; Opus discretion is
  not the sole guard. **Residual:** the gate helper's `--gate` mode
  performs a regex match for `^(Signed|Signer):` lines but does NOT
  cryptographically verify signer identity — a Codex executor could
  in principle write a synthetic signed line. Defence-in-depth: the
  gate artefact lands as a separate commit (not part of an
  implementation-slice PR), and the orchestrator verifies the commit
  author is `jrnb2024` via `git log -1 --format=%ae <gate-artefact-path>`
  before advancing the chain. Captured as part of slice 022A delivery
  in §4.7 helper.
- **R-022-13 — 020J partial-apply on slice failure.** Slice 020J makes
  two GitHub API calls (tag-protection rule + required-signed-commits
  toggle). If the first succeeds and the second times out, the SCP
  repo is left half-protected: `v*` tags are guarded but `main` is not
  enforcing signed commits. Subsequent slices (020D1 onward) would
  proceed against an inconsistently-protected `main` and the
  required-signed-commits prerequisite for 020D1 (signed merge commit)
  would be advisory rather than enforced. **Mitigation:** slice 020J's
  dispatch package `instruction` field requires Codex to:
  (a) capture the `id` returned by `POST /repos/{owner}/{repo}/tags/protection`
  in `docs/reviews/WP-SCP-020/branch-protection-log.md` BEFORE invoking the
  required-signed-commits create call (`POST /repos/{owner}/{repo}/branches/main/protection/required_signatures` — the GitHub REST API endpoint "Create commit signature protection"; PATCH is not a valid verb on this endpoint and returns 405);
  (b) verify both API calls returned 200 OK before reporting
  `status=complete`; (c) on partial-apply (one OK, one error), invoke
  `gh api -X DELETE /repos/{owner}/{repo}/tags/protection/<numeric-id>`
  using the captured `id` to revert the tag-protection rule, then
  report `status=blocked` with
  `gate_failure=partial_apply_reverted`. **020J `verify_commands`** must
  include both: `gh api repos/{owner}/{repo}/tags/protection | jq '.[] | select(.pattern=="v*")'` returning a single match,
  and `gh api repos/{owner}/{repo}/branches/main/protection/required_signatures | jq '.enabled'` returning `true`.
  Either verify failing → exit non-zero → dispatcher status overridden
  to `blocked`. The orchestrator pauses the chain and emits a
  notification. No re-dispatch without user confirmation that the
  GitHub API state is reconciled.

## 9. Acceptance criteria

WP-SCP-022 is **plan-complete and ready to merge** when:

- [ ] Plan reaches fixpoint via at least 1 fix-round (R1 → R(F)) with
      all CRIT and unmitigated MAJ findings closed across all three
      lenses; OR all three R1 reviewers return APPROVED /
      APPROVED_WITH_FINDINGS(MIN/nit-only).
- [ ] Plan PR opened against `main`.
- [ ] `docs/DECISIONS.md` updated with D-026, D-027, D-028 + D-021
      reservation note.
- [ ] `docs/BACKLOG.md` Phase 11 row added: SCP-077 (this WP) +
      SCP-077-d048-followup + SCP-077-cost-cap.
- [ ] `docs/reviews/WP-SCP-022/` directory committed (review pack +
      dispatch evidence skeleton + R1 evidence + consolidation +
      fix-round evidence as applicable).
- [ ] `docs/reviews/WP-SCP-022/acc-pin-manifest.json` committed with
      ACC repo HEAD + blob SHAs of the five dispatcher artefacts.
- [ ] `scripts/wp_scp_022_gate_check.sh` and
      `scripts/sanitize_review_finding.py` committed (created in slice
      022A by Opus, NOT dispatched).

WP-SCP-022 is **autonomous-run-complete** (the chain reaches both
terminal gates cleanly) when:

- [ ] Track 1 has merged 020B → 020B.1 → 020B.2 → 020C → 020C.1 → 020J
      → 020K → 020D1 → 020H part 1 → 020E.a → 020H part 2 → 020D2 to
      `main` (12 PRs).
- [ ] `docs/reviews/WP-SCP-020/release-signoff.md` committed with named
      signer + timestamp + canary-run-id (USER-GATE-A0 closure).
- [ ] `docs/reviews/WP-SCP-022/gates/USER-GATE-A.md` committed.
- [ ] Track 2 has merged 021B → 021C → 021D → 021E to `main` (4 PRs).
- [ ] `docs/reviews/WP-SCP-022/gates/USER-GATE-C.md` committed.
- [ ] All evidence in
      `docs/reviews/WP-SCP-022/dispatches/<slice-id>/` for every
      merged slice.
- [ ] Required check `scp/policy-check` is live on SCP `main` with
      `enforce_admins=true` (verifiable via `gh api repos/<owner>/<repo>/branches/main/protection`).
- [ ] Slice 020J's both API-state verify_commands per §8 R-022-13
      passed at slice-merge time and recorded in slice 020J's
      `verify-output.txt` (one for tag-protection rule presence,
      one for required-signed-commits enabled). Closes R4 F-R4-002.
- [ ] `scp-mcp-server` is installable from PyPI as
      `standards-control-plane[mcp]` extra.

WP-SCP-022 is **programme-complete** when both autonomous-run-complete
**and**:

- [ ] WP-SCP-020 §9 acceptance criteria fully satisfied across this WP
      and the post-pause continuation WP (covers slices 020E.b/E.c,
      020F, 020G, 020H part 3, 020H.1, 020I).
- [ ] WP-SCP-021 §9 acceptance criteria fully satisfied across this WP
      and the post-pause continuation WP (covers slices 021F–021K).
- [ ] All FUP-022 follow-ups closed or explicitly tracked on backlog.

Programme-complete is the ratification handoff to `WP-SCP-024` (estate
cascade).

## 10. Decisions introduced by this WP

- **D-026 (2026-04-28):** Autonomous-dispatch protocol for SCP
  implementation slices. Each slice flows through four-tier dispatch
  (Opus orchestrator + Codex executor + 3× parallel Sonnet R1 review)
  with the lens set, fix-round protocol, evidence persistence, and
  fix-round budget defined in §4. Mandatory for all WP-SCP-020 and
  WP-SCP-021 implementation slices.
- **D-027 (2026-04-28):** Parallel-track execution for WP-SCP-020 and
  WP-SCP-021 implementation. The two tracks run concurrently from
  dispatch-zero to user-gate. Track 1 sequence (Scope Y per
  user 2026-04-28 selection): 020B → 020B.1 → 020B.2 → 020C → 020C.1
  → 020J → 020K → 020D1 → 020H part 1 → 020E.a → [USER-GATE-A0] →
  020H part 2 → 020D2 → [USER-GATE-A]. Track 2 sequence:
  021B → 021C → 021D → 021E → [USER-GATE-C].
- **D-028 (2026-04-28):** SCP adopts D-048 / ADR-016 Design Parity
  Build Method (DPBM) as a contract input for any future SCP slice
  that produces designed visual output. Forward-looking; lands
  operationally once CT PR #202 + ACC PR #106 have merged. Enforcement
  injection per §4.6.

**D-021 reservation:** D-021 is reserved for the 2026-05-31 atomic
workday filing per WP-SCP-019 hygiene response (PR #30, 2026-04-21).
Codex executors must NOT assign D-021 to any decision filed during
this WP's autonomous run. The §4.7 gate helper detects collisions.

## 11. Review evidence

`docs/reviews/WP-SCP-022/` is created in slice 022A (this plan slice)
and contains:

- `r1-correctness/` — first-round correctness lens output (filed
  2026-04-28).
- `r1-safety/` — first-round safety_bypass lens output.
- `r1-completeness/` — first-round completeness_governance lens output.
- `consolidation-r1.md` — orchestrator's consolidation of R1 verdicts
  (10 CRIT + 16 MAJ + 9 MIN + 2 nit unique findings; all-three
  CHANGES_REQUESTED).
- `fix-round-N/` (one per round) — fix-round Codex transcript + re-
  review outputs + consolidation note. (R1 fix authored by Opus;
  re-review = R2 lens triplet.)
- `fixpoint.md` — terminal record once R(F+N) achieves all-three
  APPROVED.

This same directory layout is replicated for each implementation slice
under `docs/reviews/WP-SCP-022/dispatches/<slice-id>/`.

## 12. Next WP candidates (not opened here)

- `WP-SCP-022.1` — post-pause continuation. Track 1 020E.b/E.c/F/G/H
  part 3/H.1; Track 2 021F/G/H/I/J/K. Opens after USER-GATE-A and
  USER-GATE-C close.
- `WP-SCP-020.1` — FLA pilot (slice 020I). Gated on §7 stability
  prereqs.
- `WP-SCP-024` — estate cascade beyond FLA. Gated on programme-complete.
- `WP-SCP-022-proposal-queue` — `propose()` adjudication workflow
  (move #4 in the MVCP).
- `WP-SCP-023` — scorecards dashboard (move #5).

## 13. Open unknowns (must close before specific slice)

- **U-022-01 (closed in v0.2):** review-cost cap. Per-slice $30,
  aggregate $300 default per §8 R-022-07. User may override at
  USER-GATE-A.
- **U-022-02 (closed in v0.2 — was redundant):** personal-Pro account
  signed-commit configuration. WP-SCP-020 §14 U-sec-2 already resolved:
  GitHub Pro personal account supports tag-protection + required-
  signed-commits. No separate verification needed.
- **U-022-03 (close before slice 021B):** PyPI publishing path. Personal
  user-namespace per WP-SCP-020 §14 U-k resolution; confirm
  `pyproject.toml` publish target is `standards-control-plane` (not
  `standards-control-plane-` matching the GitHub repo's trailing-dash
  slug).
- **U-022-04 (close before USER-GATE-C):** ACC integration target.
  Slice 021G hooks into `~/Projects/acc/src/acc/broker/dispatcher.py`;
  verify this file exists and the integration point (plan-decompose
  step) is stable as of slice dispatch time. (Note: 021G is post-pause,
  not in this autonomous run.)

## 14. Follow-ups (FUP-022-NN)

Tracked on backlog; not in this WP's autonomous scope.

- **FUP-022-01 — ACC dispatcher: surface session_id.** Modify
  `codex_dispatch.py` to surface the Codex CLI's session_id in the
  DispatcherResult so future fix rounds can use `resume_session_id`
  per WP-SCP-022 §4.3. Owner: ACC repo. P2.
- **FUP-022-02 — ACC dispatcher: scope-boundary symlink resolution.**
  Modify `codex_dispatch.py` to resolve symlinks before applying
  scope_boundary fnmatch checks (closes residual CRIT-BYPASS-001).
  Owner: ACC repo. P1.
- **FUP-022-03 — ACC dispatcher: pre-hoc scope-boundary enforcement.**
  Refactor `codex_dispatch.py` to refuse out-of-scope edits before they
  land on disk (closes residual CRIT-BYPASS-001 fully). Owner: ACC
  repo. P3.

---

**End of plan v0.5.** Awaiting Gate C round-5 review.
