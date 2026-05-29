# D-057 — SCP self-orchestrate pattern: Pattern 3 (Claude Code autonomous sessions) canonical for self-work, governed by a session-start ACC dispatch; acc-hook RETAINED

**Status:** DRAFT (operator-review surface; flips to ACCEPTED on PR merge per the post-merge ADR ceremony established by D-047 / D-048 / D-049 / D-050 / D-054 / D-055).
**Date filed:** 2026-05-29
**Decision date:** TBD (operator signature on merge)
**Operator:** @jrnb2024
**Origin:** WP-SCP-EST-002-SELF-ORCHESTRATE-PATTERN (`docs/BACKLOG.md` Phase 12 L166, filed 2026-05-26 PM). Strategic ADR — not a WP-SCP-026 slice.
**Closes:** WP-SCP-EST-002 (the decision) + WP-SCP-EST-003-HOOK-REENABLEMENT (the disposition: hook RETAINED, governed by a session-start dispatch) + FUP-AUTONOMOUS-RUN-PROMPT-ACC-HOOK-ANTICIPATION-001 (resolved by the session-start dispatch prologue convention this ADR establishes).
**Reframes (does not close):** WP-SCP-EST-001-PER-REPO-MCP-PROXY — recast as the prerequisite for a *future* Pattern-1 adoption (ACC orchestrating SCP as a cross-repo target); still gated on WP-SCP-026 026F observation; not urgent; not required by this decision.
**Related upstream:** ACC `PLAN-EST-P-cross-repo-orchestration-v3` (Gate-A draft; `WP-ACC-PHASE-P-PLAN` NOT STARTED per CT PROG-EST-001); ACC ADR-019 (Phase X supervisor-rip — the Go PreToolUse hook is the estate's sole mechanical write-scope enforcement); CT `PROG-EST-001` Estate Rollout Programme (SCP = `n/a (Python; non-CT consumer) … NOT INSTALLED (optional)` for estate hook install).
**Successor reservation note:** D-056 remains reserved for WP-SCP-026 026F Threshold / USER-GATE-G observation contract (do NOT consume). This ADR takes D-057.
**Review provenance:** 3-lens plan-stage review conducted 2026-05-29 (correctness / safety_bypass / completeness_governance), per `feedback_orchestrator_auth_surface_plan_review_default.md`. **v1 of this ADR proposed removing the hook; the safety_bypass lens REJECTED it** for resting on a false "the hook is pure friction in Pattern 3" premise. This v2 pivots to the review's recommended option (retain the hook; govern Pattern-3 sessions with a session-start dispatch). The disposition trail is in `docs/reviews/D-057/` (this PR).

---

## Context

### Pattern taxonomy

Three estate self-/cross-orchestration patterns are in play:

- **Pattern 1** — ACC orchestrates TO an adopter repo (`acc orchestrate --cross-repo`; ACC dispatches WorkPackages against an external repo's working tree, writing `.acc/active-dispatch.json` in that repo before each tool call).
- **Pattern 2** — an adopter repo runs its OWN `acc orchestrate` for self-build (hierarchical WorkPackage orchestration inside that repo).
- **Pattern 3** — standalone Claude Code autonomous sessions (operator launches a Claude Code session against a continuation prompt; no ACC orchestrator process).

Today SCP, PIM, CT, FLA, and Recommender all self-develop via **Pattern 3**. Only ACC itself runs `acc orchestrate`, and only for its own self-build.

### What the acc-hook actually enforces (corrected from EST-002's filing framing)

The acc-hook (`<acc>/hook/cmd/acc-hook/main.go`, deployed to SCP at `.claude/hooks/dist/darwin-arm64/acc-hook`) is a Claude Code **PreToolUse** matcher on `Write|Edit|Bash|NotebookEdit`. On each gated tool call it:

1. **ALLOWS unconditionally** if the target path is in `alwaysAllowed()` — verified at `main.go:277-290`: `docs/**`, `.acc/work-packages/**`, `.acc/codex-probes/**`, `.acc/claude-probes/**`, `CLAUDE.md`, `AGENTS.md`, and `~/.claude/projects/**/memory/*.md`.
2. **ALLOWS** if the target path is within the `scope_boundary` of an active dispatch at `.acc/active-dispatch.json`.
3. **DENIES** otherwise. (Separately, it denies *all* Bash redirections unconditionally — `bash.Decide()` never consults the active-dispatch scope, so a dispatch does not unlock redirections; e.g. `cat x > docs/foo.md` is denied even though `docs/**` is always-allowed.)

It also appends an **HMAC-SHA256-signed forensic record of every gated call** (allow *and* deny) to `.acc/hook-audit-log/YYYY-MM-DD.jsonl`. Per ACC ADR-019, this hook is the estate's **sole mechanical write-scope enforcement** post-supervisor-rip.

**Net effect for SCP:** documentation writes (`docs/**`, plus `CLAUDE.md` / `AGENTS.md` / memory) are *always* permitted; **source** writes (`src/**`, `tests/**`, `policies/**`, `scripts/**`, `pyproject.toml`, root-level `STATUS.md`, `.claude/**`) are permitted **only within an active dispatch's `scope_boundary`**. There is no friction for doc work; there is a (correct, intentional) gate on unscoped source mutation.

### Correction to the framing that motivated EST-002

EST-002's filing text — and v1 of this ADR — characterised the hook as friction "incompatible with Pattern 3 without intervention." The 2026-05-29 review established that this is inaccurate. The hook is fully compatible with Pattern 3 the moment a session **declares its scope** via a dispatch. The 2026-05-26 autonomous run was blocked at Phase 0 precisely because it attempted to `Write` `src/standards_control_plane/scp_cli.py` — a source path — with **no active dispatch**. That is the hook performing its function, not malfunctioning. The incompatibility was the **absence of a dispatch**, not the hook.

### Upstream readiness

ACC `PLAN-EST-P-cross-repo-orchestration-v3` is at Gate-A draft, a 15-24 week programme; `WP-ACC-PHASE-P-PLAN` is NOT STARTED. Pattern 2 (adopter self-build via `acc orchestrate`) is not formally scoped in v3. Running `acc orchestrate` for self-build (Pattern 2) requires the acc-hook installed + SHA-pinned; cross-repo dispatch (Pattern 1) *additionally* requires the target repo to ship `.acc/mcp_server.py` (a per-repo MCP server) + CT SDK bearer-token auth wiring. CT `PROG-EST-001` lists SCP as optional / non-CT-consumer for estate hook install; SCP is not in the C.1–C.8 auth cohort cascade.

## Decision

Ratify **Pattern 3 (Claude Code autonomous sessions) as SCP's canonical self-orchestrate mode, governed by a session-start ACC dispatch.** The acc-hook is **RETAINED and remains live.** Concretely:

1. **The acc-hook stays installed and live.** `.claude/settings.json`'s PreToolUse matcher is unchanged. (`.claude/settings.json` is gitignored / untracked — it carries no committed repo state and is NOT modified by this PR.) **EST-003 disposition = RETAIN.** **Honesty note:** the hook was *manually removed* for the 2026-05-26 autonomous run (backup `.claude/settings.json.acc-hook-backup`) and *restored* as that run's final action (backup then deleted) — see `STATUS.md` 2026-05-26 chain. The current live state is therefore the restored state. **This ADR forbids that remove-then-restore pattern going forward:** an autonomous session MUST NOT disable its own enforcement hook; it declares scope via a dispatch instead (Decision 2-3). Removing the hook is no longer an approved expedient.

2. **Pattern-3 autonomous sessions declare scope at session start** by writing `.acc/active-dispatch.json` with a `scope_boundary` enumerating the source paths the session intends to touch, plus `dispatch_id` and `started_at`. Doc-only sessions (`docs/**`, memory, `CLAUDE.md`) need **no** dispatch — those paths are always-allowed.

3. **The dispatch is created by an operator-run bootstrap** — plain bash, run *outside* the Claude Code session — via `scripts/operator/scp-pattern3-dispatch.sh "<scope-glob>" ["<scope-glob>" ...]`. The mechanism is mundane, not a special carve-out: the acc-hook is a Claude Code **PreToolUse** hook, so it only fires on tool calls *mediated by a Claude Code session*. A script the operator runs in a normal terminal never routes through the hook, so it can write `.acc/active-dispatch.json` freely. This is the concrete realisation of FUP-AUTONOMOUS-RUN-PROMPT-ACC-HOOK-ANTICIPATION-001's proposed option (a).

4. **`scope_boundary` discipline: narrow + specific.** Enumerate the files/dirs the session will touch (e.g. `src/standards_control_plane/scp_cli.py`, `tests/test_scp_cli.py`, `STATUS.md`). The dispatch-writer script (`scripts/operator/scp-pattern3-dispatch.sh`) MUST enforce — as tested acceptance criteria in the runbook — that it:
   - **refuses blanket globs** (`**`, `/`, `.`, `./`);
   - **refuses any glob that would match `.acc/active-dispatch.json` itself** — i.e. `.acc`, `.acc/`, `.acc/**`, `.acc/*`, and the literal path. **This is the load-bearing self-escalation guard** (see Accepted residual risk): the dispatch file is NOT in the hook's `alwaysAllowed()` set, so if a session's own `scope_boundary` covered the dispatch file, the session could overwrite `.acc/active-dispatch.json` mid-run to widen its scope to `src/**`. Forbidding self-covering scopes at write time closes that path on the SCP side;
   - **refuses to run under `CI=true` / `GITHUB_ACTIONS=true`** (operator-attended only).
   These are acceptance criteria, not descriptions of shipped behaviour — the script ships in this PR with each criterion covered by a test in the runbook. A complementary hook-side deny of `.acc/active-dispatch.json` is filed forward as an ACC-side FUP (defence-in-depth; cross-repo, kernel-dangerous — out of this ADR's scope).

5. **The hook keeps logging.** The HMAC forensic trail in `.acc/hook-audit-log/` is preserved — the dispatch ceremony *satisfies* the hook, it does not disable it.

5a. **Dispatch freshness + teardown.** The hook already enforces a freshness gate on the dispatch: `started_at` older than `active_dispatch_ttl_seconds` (SCP `acc.kernel.config` = `14400`, i.e. 4h) is denied, as is a `dispatch_id` with a missing/future `started_at` (fail-closed; `hook/internal/policy/freshness.go`). To prevent a *later, unrelated* Pattern-3 session inheriting a prior session's still-within-TTL scope: (i) the writer script stamps `started_at` to *now* on every write; (ii) the runbook + continuation-prompt mandate a **teardown step** (`rm -f .acc/active-dispatch.json`) at session end; (iii) operators keep `scope_boundary` minimal so even a stale-but-fresh dispatch grants little.

6. **Continuation-prompt convention.** The canonical SCP autonomous-run prompt prologue (a) verifies the hook is live (cardinal pre-flight — UNCHANGED; the hook stays on), and (b) instructs the operator to run the dispatch bootstrap with the session's intended source scope before kickoff, OR notes "doc-only run — no dispatch needed." This closes FUP-AUTONOMOUS-RUN-PROMPT-ACC-HOOK-ANTICIPATION-001.

7. **EST-001 reframed.** WP-SCP-EST-001 (per-repo MCP server `.acc/mcp_server.py`) is the prerequisite for SCP becoming a Pattern-1 *target* (ACC orchestrating SCP). It remains valid, stays gated on the 026F observation window, and is NOT urgent or required by this decision.

## Accepted residual risk

This is an honest downgrade from ACC's Pattern-1/2 posture, accepted with eyes open:

- **`scope_boundary` is self-declared.** A Pattern-3 session's scope is declared by the operator at bootstrap, not set by a separate orchestrator uid (as in Pattern 1/2). An overbroad declaration weakens the guard. **Mitigations:** the dispatch-writer script refuses blanket globs (`**`, `/`, `.`); the runbook mandates narrow enumeration; PR review remains the human backstop; the HMAC audit log records every write for post-hoc detection.
- **Self-rewrite vector (the sharper risk).** `.acc/active-dispatch.json` is NOT in the hook's `alwaysAllowed()` set, so a session can only write it if its *own* `scope_boundary` covers it. If a careless scope did (e.g. `.acc/**` or `**`), the session could overwrite its own dispatch mid-run to escalate to `src/**`. **Mitigation:** Decision 4 makes the writer script refuse any scope glob matching the dispatch path — closing this on the SCP side. Residual: this is a write-time guard in an operator script, not a hook-side deny; the defence-in-depth hook-side deny is filed as an ACC-side FUP.
- **The bootstrap runs outside the hook.** The dispatch file is written by an operator-run plain-bash script. This is not a special carve-out — the hook is a Claude Code PreToolUse hook and simply never sees tool calls made outside a Claude Code session (a normal-terminal script). The trust anchor is the operator knowingly running the script with a reviewed scope.

These are accepted because SCP is **single-maintainer, doc-heavy, low-blast-radius source, and NOT an ACC orchestration target.** They would NOT be acceptable for a repo with a production auth/secrets surface or one that ACC orchestrates (see gating predicate below).

## What this IS and is NOT

**IS:** a self-work orchestration-mode choice for SCP that keeps the mechanical write-scope guard + the forensic audit trail, and adds a lightweight session-start scope-declaration step.

**IS NOT:**
- (a) Removal or weakening of the acc-hook. The hook stays live and keeps logging.
- (b) A claim that Pattern 3 + self-declared dispatch is right for every estate repo. Repos with auth/secrets surfaces or that ARE ACC orchestration targets (PIM, CT) keep the stricter orchestrator-sets-scope posture.
- (c) A change to SCP's role as a policy **source** for ACC's cross-repo work. D-036 / RULE-003 / SCP-R-006 are untouched — that is SCP enforcing policy *on* ACC's orchestration, a separate concern from how SCP develops itself.
- (d) Permission to skip the R-cycle / plan-stage review / adversarial-review discipline. Those remain the substantive governance; the dispatch is an additional mechanical scope-confinement, not a substitute for review.

## Gating predicate (prevents precedent misuse)

A repo MAY adopt SCP's "Pattern 3 + self-declared session dispatch" posture only if **ALL** of the following hold:

1. The repo is **not** an ACC `acc orchestrate` cross-repo target.
2. The self-edited source carries **no** production auth / secrets / credential surface.
3. The repo is single-maintainer or small-team **with PR review** on `main`.
4. The workload is **doc-heavy** (most autonomous writes land in always-allowed paths).

A repo failing **any** of these MUST keep the stricter posture (orchestrator-sets-scope, or hook with no self-declared-dispatch carve-out). **The stricter posture is the default; "if in doubt, keep the hook ungated-only."** Any repo adopting SCP's posture MUST record a one-line predicate self-assessment in its own ADR, citing all four conditions with evidence — citing D-057 alone is insufficient. This ADR is **not** a template for repos to relax governance; it is a scoped decision for SCP's specific profile. (Concretely: PIM and CT both run the acc-hook live today and both fail condition 2 — they carry auth surfaces — so neither may cite D-057 to relax.)

## Reversal / forward door

If SCP later becomes an ACC orchestration target (Pattern 1):

- Ship WP-SCP-EST-001 (`.acc/mcp_server.py` per-repo MCP server). The dispatch is then written by the ACC orchestrator (a separate uid) rather than the operator bootstrap — strictly stronger.
- The hook is already live, so there is **no re-install**. Cost ≈ the WP-SCP-EST-001 build + ≤1 day of wiring.

The decision is reversible at low cost because nothing is torn out — the guard remains in place throughout.

## Boundaries (anti-scope of THIS ADR)

This ADR does NOT: decide the WP-SCP-EST-001 build shape; modify the ACC hook source; change the posture for any other estate repo; modify D-036 / RULE-003 / SCP-R-006; or alter `.claude/settings.json` (gitignored; hook config unchanged).

## Downstream artefacts (this PR)

1. `docs/decisions/D-057-scp-self-orchestrate-pattern-2026-05-29.md` — this ADR (new).
2. `docs/DECISIONS.md` — append D-057 row + bump `**Last Updated:**` (string describing D-057).
3. `docs/BACKLOG.md` — main table (L164-167): EST-002 → CLOSED, EST-003 → CLOSED, EST-001 disposition reframed, FUP-AUTONOMOUS-RUN-PROMPT-ACC-HOOK-ANTICIPATION-001 → CLOSED; **and** the Phase-12 Deferred-with-disposition table (L190-193): same four rows updated. **Plus a NEW FUP** `FUP-ACC-HOOK-DENY-ACTIVE-DISPATCH-PATH-001` (P2, ACC-side, defence-in-depth) recommending the acc-hook add `.acc/active-dispatch.json` to a hook-side deny so the self-escalation guard does not rely on the SCP writer script alone.
4. `docs/operator-runbooks/scp-pattern3-dispatch.md` — the session-start dispatch ceremony runbook + `scope_boundary` discipline + the script's tested acceptance criteria + teardown step (new).
5. `scripts/operator/scp-pattern3-dispatch.sh` — operator-run dispatch-writer. Acceptance criteria (tested in the runbook): refuses blanket globs (`**`/`/`/`.`); refuses any glob matching `.acc/active-dispatch.json`; refuses `CI=true`/`GITHUB_ACTIONS=true`; stamps `started_at` to now. (New; source path — authored under a dispatch, see "Status flip ceremony".)
6. `docs/continuation-prompts/2026-05-27-WP-SCP-026-shipped.md` — prologue updated to add the dispatch-bootstrap step + the teardown step (hook-live cardinal pre-flight retained).
7. `STATUS.md` — chain row (triggers `check-invocation-log-entry` path-trigger; source/root path — authored under a dispatch). The row points forward to D-057 so the stale 2026-05-26 `cp …acc-hook-backup…` restore instruction is superseded.
8. `docs/ESTATE-CONVERGENCE.md` — clarify (existing hook rows) that the acc-hook is honoured in Pattern 3 via the session-start dispatch. `docs/OVERVIEW.md` — **add a net-new note** on how SCP develops itself (Pattern 3 + dispatch); there is no existing self-development prose to "clarify."
9. `~/.claude/projects/-Users-amplience-Projects/memory/MEMORY.md` — SCP index line gains a one-line D-057 note (out-of-repo; memory currency).
10. `docs/reviews/D-057/dispositions.md` — the 2-round 3-lens review trail (v1 hook-removal REJECT by safety_bypass → v2 retain-plus-dispatch ACCEPT-WITH-FIXES) + per-finding disposition. Durable evidence for the `## R1 evidence` PR-body claim (new).

`.claude/settings.json` is **gitignored + UNCHANGED** — no settings diff is part of this PR. The dogfood `.acc/active-dispatch.json` is also gitignored + ephemeral by design (it will not appear in the merged diff; that is correct, not a missing artefact).

## Status flip ceremony

Per the established estate pattern (D-047 / D-048 / D-049 / D-050 / D-054 / D-055), this ADR's status flips DRAFT → ACCEPTED on the merge of the PR that opens it. Operator merge constitutes the ratification signature.

**Authoring-session note (honest):** this PR was authored from a Claude Code session whose project root is the *parent* directory `/Users/amplience/Projects`, **not** the SCP repo. The acc-hook is registered in the SCP repo's `.claude/settings.json`, which Claude Code loads only when the SCP repo is the project root — so the hook was **not in effect** for this session's writes, and the source artefacts (`scripts/operator/scp-pattern3-dispatch.sh` + the root `STATUS.md` row) were written without hook gating. This is disclosed rather than dressed up as a dogfood: the ceremony's *first genuine exercise* is the next **SCP-repo-rooted** Pattern-3 autonomous session, which the updated continuation prompt instructs to bootstrap a dispatch via the shipped script (and tear it down at session end). The hook's gating behaviour on SCP-rooted sessions was confirmed empirically during the 2026-05-26 runs (source writes denied without a dispatch; see `.acc/hook-audit-log/2026-05-26.jsonl`), and the script's self-escalation guard (Decision 4) is verified by the runbook's acceptance-criteria tests, not by this PR's own authoring path.

**PR body discipline (pre-merge gate).** The PR MUST include a `## R1 evidence` block with three lens lines matching `.github/workflows/r1-evidence-check.yml` regex `^[ \t]*-[ \t]*(correctness|safety_bypass|completeness_governance):[ \t]*\S` — `- correctness: …`, `- safety_bypass: …`, `- completeness_governance: …` — citing the 2026-05-29 3-lens review (no bold labels; the validator rejects bold). CI fails on PR open without all three populated.

## Diff-verification

Per `feedback_verbatim_claim_diff_verification.md`, the load-bearing claims in this ADR are grounded in the actual repo state at filing:

```bash
# Hook allows docs/, gates source (the corrected premise) — anchored awk, not line-number sed:
awk '/^func alwaysAllowed/,/^}/' /Users/amplience/Projects/acc/hook/cmd/acc-hook/main.go
# Hook enforces a 4h dispatch TTL (freshness gate):
awk '/DefaultActiveDispatchTTLSeconds/{print}' /Users/amplience/Projects/acc/hook/internal/policy/freshness.go
# settings.json is gitignored (no committed state to change):
git -C /Users/amplience/Projects/standards-control-plane check-ignore .claude/settings.json   # rc=0
# Highest filed D-number is D-055; D-056 reserved; D-057 free:
grep -E '^\| D-05[4-7] ' /Users/amplience/Projects/standards-control-plane/docs/DECISIONS.md
# EST-001/002/003 + FUP backlog rows:
grep -nE 'WP-SCP-EST-00[1-3]|FUP-AUTONOMOUS-RUN-PROMPT-ACC-HOOK' /Users/amplience/Projects/standards-control-plane/docs/BACKLOG.md
```

---

**Identified at:** 2026-05-26 (WP-SCP-EST-002 filing) + 2026-05-29 (3-lens review pivot from hook-removal to hook-retain-plus-dispatch).

**Filed:** 2026-05-29 (this ADR PR).

**Closes when:** operator merges this PR + `docs/DECISIONS.md` row appended + BACKLOG EST-002/003 + FUP flipped CLOSED + STATUS chain row landed.
