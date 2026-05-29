# D-057 — plan-stage review dispositions (2-round 3-lens)

**ADR:** `docs/decisions/D-057-scp-self-orchestrate-pattern-2026-05-29.md`
**Filed:** 2026-05-29
**Lenses:** correctness / safety_bypass / completeness_governance (estate-standard triplet per `feedback_orchestrator_auth_surface_plan_review_default.md`).

This trail captures **two rounds** of 3-lens review. Round 1 reviewed v1 of the ADR (hook-removal); round 2 reviewed the v2 ADR after the pivot. The pivot was forced by the safety_bypass REJECT on v1, not by an operator preference change — both rounds are recorded for the governance trail.

---

## Round 1 — v1 ADR (hook-removal proposal) — 2026-05-29

**v1 Decision:** ratify Pattern 3 as canonical for SCP self-work; **remove acc-hook from default `.claude/settings.json`** ("Pattern 3 + forward door"); retain binary + backup; named future trigger to revisit (Pattern-1 adoption).

**Verdicts:**
- correctness: ACCEPT-WITH-FIXES (2 MINOR + 2 NIT)
- safety_bypass: **REJECT** (2 CRITICAL + 2 HIGH + 2 MAJOR + 1 MINOR + 1 NIT)
- completeness_governance: ACCEPT-WITH-FIXES (2 HIGH + 4 MAJOR + 3 MINOR + 1 NIT)

**Why REJECT:** the safety_bypass lens established — and the orchestrator verified directly at `acc/hook/cmd/acc-hook/main.go:277-290` — that v1's central premise ("the hook is pure friction in Pattern 3; denies everything when no dispatch is active") was **factually wrong**. `alwaysAllowed()` permits `docs/**`, `.acc/work-packages/**`, the probe dirs, `CLAUDE.md`, `AGENTS.md`, and memory files unconditionally with no dispatch. The hook is a working **source-write guard that already lets documentation through**, not a blanket-deny. The 2026-05-26 run was blocked only because it tried to Write `src/.../scp_cli.py` (a source path) with no dispatch — the hook performing its function.

The lens also surfaced a **strictly-better option** (which the FUP `FUP-AUTONOMOUS-RUN-PROMPT-ACC-HOOK-ANTICIPATION-001` had already proposed as option (a) but v1 ignored): **keep the hook live, and have Pattern-3 autonomous sessions declare scope at session start by writing `.acc/active-dispatch.json` via an operator-run bootstrap.** This preserves the source-write guard + the HMAC forensic audit log, needs no ACC kernel change, and sets no precedent for ripping governance controls.

**Pivot:** the operator was presented with the REJECT findings, the verified `alwaysAllowed()` source, and a three-option re-decision (keep-hook-plus-dispatch / audit-only-hook-carve-out / still-remove-with-fixes). The operator ratified **keep-hook-plus-dispatch** (the recommended option). The ADR was re-authored as v2 against that direction.

The v1 ADR is not retained on disk — the file on the branch is v2. The v1 framing + the REJECT findings live here in the governance trail.

---

## Round 2 — v2 ADR (Pattern-3 + session-start dispatch) — 2026-05-29

**v2 Decision:** ratify Pattern 3 as canonical; **retain acc-hook live** (EST-003 disposition = RETAIN); govern Pattern-3 autonomous sessions via a session-start `.acc/active-dispatch.json` written by an operator-run bootstrap script; reframe EST-001; close FUP-AUTONOMOUS-RUN-PROMPT-ACC-HOOK-ANTICIPATION-001.

**Verdicts:**
- correctness: ACCEPT-WITH-FIXES
- safety_bypass: ACCEPT-WITH-FIXES (2 CRITICAL + 2 HIGH + 3 MAJOR + 1 MINOR + 1 NIT — all foldable, no REJECT)
- completeness_governance: ACCEPT-WITH-FIXES (1 HIGH + 2 MAJOR + 3 MINOR + 2 NIT — all foldable)

**No REJECT** — the direction holds. All load-bearing findings were folded into v2 of the ADR before the dependent doc set was authored.

### Round-2 findings + dispositions

| Lens | ID | Severity | Finding | Disposition |
|---|---|---|---|---|
| safety_bypass | CRIT-1 | CRITICAL | ADR was framing hook as "unchanged" while BACKLOG/STATUS document the 2026-05-26 remove-then-restore. Must be honest + forbid the pattern going forward. | **FOLDED** into Decision 1 (honesty note + explicit prohibition: "an autonomous session MUST NOT disable its own enforcement hook"). |
| safety_bypass | CRIT-2 | CRITICAL | **Self-escalation vector.** `.acc/active-dispatch.json` is NOT in `alwaysAllowed()`. A session whose `scope_boundary` covers the dispatch file (via `.acc/**`, `**`, or the literal) could overwrite the dispatch mid-run to escalate to `src/**`. | **FOLDED** into Decision 4 as the load-bearing self-escalation guard: writer script MUST refuse any scope glob matching `.acc/active-dispatch.json`. Also recorded in Accepted residual risk. ACC-side hook-deny filed forward as `FUP-ACC-HOOK-DENY-ACTIVE-DISPATCH-PATH-001` for defence-in-depth. |
| safety_bypass | HIGH-1 | HIGH | "Script refuses X" is described as fact, but the script doesn't exist yet — reword to tested acceptance criteria; ship the script with criteria tested. | **FOLDED**: Decision 4 reworded as "MUST enforce (as tested acceptance criteria in the runbook)"; script ships in this PR with the criteria implemented; runbook documents the tests. |
| safety_bypass | HIGH-2 | HIGH | Bootstrap-ordering: the FIRST dispatch can't be written by a script that doesn't exist yet. | **FOLDED**: Status-flip ceremony "Authoring-session note" explicitly addresses this; on this PR specifically, the orchestrator session was parent-rooted (hook not in effect) so the bootstrap question was moot for the authoring path, with the first genuine ceremony exercise deferred to the next SCP-rooted autonomous session. |
| safety_bypass | MAJOR-1 | MAJOR | Gating predicate is enumerated but a "stricter is the default" backstop is missing — risks precedent misuse by repos that don't meet all four conditions. | **FOLDED**: gating predicate now states "stricter is the default" + requires any adopter to record a per-condition self-assessment in its own ADR (citing D-057 alone is insufficient); PIM/CT explicitly called out as failing condition 2. |
| safety_bypass | MAJOR-2 | MAJOR | "Bootstrap runs outside the hook" framing implied a special cosignal carve-out; it's not — it's a mundane consequence of PreToolUse hooks only firing on Claude-mediated calls. | **FOLDED**: Decision 3 + Accepted residual risk reworded to state the mechanism plainly ("the hook is a Claude Code PreToolUse hook and simply never sees tool calls made outside a Claude Code session"). |
| safety_bypass | MAJOR-3 | MAJOR | Hook already has a 4h dispatch TTL (`DefaultActiveDispatchTTLSeconds=14400`, `freshness.go`) — ADR should cite it + mandate teardown so a later session doesn't inherit a prior session's still-fresh dispatch. | **FOLDED**: new Decision 5a wires in the TTL + mandates `--teardown` step + `started_at` stamped to now. Script's `--teardown` implements this. Runbook + continuation-prompt include the teardown step. |
| safety_bypass | MINOR-1 | MINOR | Runbook should document that malformed dispatch JSON fails closed (the hook treats parse failures as no-dispatch). | **CARRIED to runbook**: documented in `docs/operator-runbooks/scp-pattern3-dispatch.md` "Fail-closed semantics" section. |
| safety_bypass | NIT-1 | NIT | Use awk anchored to function name, not line-number sed, for `alwaysAllowed()` cite (per `feedback_line_range_endpoints_anchored_awk_not_manual_counting.md`). | **FOLDED**: Diff-verification block now uses `awk '/^func alwaysAllowed/,/^}/'`. |
| completeness | HIGH-1 | HIGH | ADR references `docs/reviews/D-057/` but omits it from the Downstream artefacts checklist. | **FOLDED**: checklist item 10 added (this file). |
| completeness | MAJOR-1 | MAJOR | No durable 3-lens-review-evidence artefact named, despite the ADR claiming a review. | **FOLDED**: same as HIGH-1 — this dispositions doc is the durable evidence. |
| completeness | MAJOR-2 | MAJOR | Dogfood claim has bootstrap-ordering circularity. | **FOLDED**: Authoring-session note rewritten honestly (parent-rooted session, hook not in effect for authoring path; ceremony first-exercised by next SCP-rooted session). |
| completeness | MINOR-1 | MINOR | `OVERVIEW.md` has no existing Pattern-3 self-dev prose to "clarify" — it's a net-new addition. | **FOLDED**: checklist item 8 reworded "add a net-new note" for OVERVIEW; "clarify" retained only for ESTATE-CONVERGENCE which does have existing hook rows. |
| completeness | MINOR-2 | MINOR | STATUS.md L349 historical row carries a dead `cp …acc-hook-backup…` restore instruction. | **FOLDED**: the new STATUS chain row points forward to D-057 so the stale instruction is superseded. |
| completeness | MINOR-3 | MINOR | `.acc/active-dispatch.json` is gitignored/ephemeral — should be stated so reviewers don't flag its absence. | **FOLDED**: Authoring-session note states it explicitly; checklist tail repeats it. |
| completeness | NIT | NIT | BACKLOG line citations off by one (L165-167 → should be L164-167; L186-194 → L190-193). | **FOLDED**: Downstream artefacts citations corrected. |
| correctness | MIN-1 | MINOR | Hook bullet 3 imprecise — "denies Bash redirections without a dispatch" was wrong; redirections are denied **regardless** of dispatch (`bash.Decide()` never consults scope). | **FOLDED**: Context bullet 3 now states this precisely. |
| correctness | MIN-2 | MINOR | Escape-hatch mechanism conflated with cosignal. | **FOLDED**: same as safety MAJOR-2. |
| correctness | NIT-1 | NIT | Use awk not sed for alwaysAllowed cite. | **FOLDED**: same as safety NIT-1. |
| correctness | NIT-2 | NIT | Tighten "Last Updated" bump description in checklist item 2. | **FOLDED**: checklist item 2 now reads "append D-057 row + bump `**Last Updated:**` (string describing D-057)." |

### Verification of the v1 → v2 pivot resolutions

All v1 safety_bypass CRITICAL/HIGH/MAJOR findings either (a) became moot under v2 because the v2 decision keeps the hook live (e.g. "removing the hook ends HMAC audit logging"), or (b) are explicitly handled by v2's mechanisms (the self-escalation vector flagged in round 2 is the one genuinely-new issue v2 introduced + closes; everything else from v1 collapses cleanly).

The v1 completeness HIGH `.claude/settings.json` is gitignored ⟹ no committable hook-removal mechanism — also moot under v2 because v2 makes no change to settings.json.

---

## Outcome

- **v2 ADR:** ACCEPT-WITH-FIXES across all three lenses, all fixes folded **before** the dependent doc set was written.
- **PR body** carries the `## R1 evidence` block citing this dispositions doc.
- **Status flip ceremony** (D-057 → ACCEPTED) on PR merge per the established post-merge pattern.
