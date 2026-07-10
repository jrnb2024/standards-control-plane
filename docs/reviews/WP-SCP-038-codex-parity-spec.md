# WP-SCP-038 — Codex parity: canonical AGENTS.md + SCP-R-014 presence gate + Codex PreToolUse hook

**Status:** SPEC v2 (post plan-stage 3-lens R1 — folds
`docs/reviews/WP-SCP-038-codex-parity-r1-dispositions.md`). **Owners:** SCP (the gate) + ACC (the
canonical content + the Codex hook), per D-058. **Origin:** the 2026-07-10 investigation of whether
Codex is a bypass of the acc-hook.

> ⚠️ **HONEST FRAMING — carry this verbatim into every status/closure doc for this WP** (safety R1
> BLOCKER-1): *This WP does NOT gate Codex source-writes. The real enforcement stays the dispatcher's
> post-hoc scope+verify+audit + CI policy-check + gated-merge. This WP adds: advisory AGENTS.md context,
> presence-gating of that context, and (if feasible) a real Codex-side pre-exec hook. Do not summarise
> this as "Codex is now gated / Codex parity CLOSED."*

## Context — the gap, corrected

The acc-hook is a *Claude Code* `PreToolUse` hook; Codex does not run it. Codex's writes are governed
NOT inline but **post-hoc** by `acc/scripts/codex_dispatch.py` (scope-boundary + verify + audit;
symlink/nested/authorship hardened; 394 blocked dispatches on record). That path is **governed, not a
backdoor**. Two residuals: (1) Codex sees none of the rules Claude sees at write time; (2) nothing stops
a bare `codex exec` *around* the dispatcher.

**CORRECTION (R1 correctness BLOCKER-1 — I was wrong in v1):** Codex is NOT hook-less. `codex features
list` → `hooks   stable   true`; `.codex/hooks.json` supports a `PreToolUse` hook that **blocks** on
`permissionDecision:"deny"` / exit code 2. Its current coverage is **shell-command-matched** (per the
vendored codex migration doc), NOT a universal Write/Edit matcher. So a real Codex-side pre-exec gate
may be possible — this reshapes D3 (below). (Note: `plugin_hooks` is a *removed* feature; the *general*
`hooks` config-layer feature is the live one — don't conflate.)

## Repo scope — SURVEYED, not guessed (R1 completeness MAJOR-4)

Live `codex_dispatch.py` usage (dispatch-log counts, 2026-07-10):

| Actual Codex users | dispatches | | Zero Codex usage |
|---|---|---|---|
| acc | 1032 | | standards-control-plane (0) — SCP self-work is Pattern-3/Claude, never Codex |
| mapp-pim | 369 | | mapp-doc-agent (0) |
| control-tower | 239 | | fashion-ontology-service (0) |
| agentic_commerce_pac | 139 | | graph-twin (0) |
| mapp-size-allocation | 135 | | kg-studio (0 dispatches; 95 probes — probed, not dispatched: edge case) |
| Recommender | 4 | | |

**WP-038 target set = repos that ACTUALLY run Codex.** For the SCP-*gated* subset (D2), that's the live
SCP cohort ∩ Codex-users. ⚠️ SCP's own `CLAUDE.md` cohort line is STALE ("mapp-pim · control-tower ·
mapp-doc-agent") — reality after the 2026-07-04 cascade is 13 gated adopters; **reconcile that line
first** (a docs fix, sibling to this WP). Post-reconcile, the gated ∩ Codex-user pilot set is
**{mapp-pim, control-tower}**; acc governs itself. **SCP-self is NOT on the D1 list** (it doesn't run
Codex — v1's inclusion was the self-contradiction R1 caught); it may carry the block for symmetry but
it is not load-bearing there.

## The three deliverables + ownership

### D1 — Canonical AGENTS.md onboarding block  (ACC AUTHORS · SCP GATES presence via D2)
ACC authors a marker-delimited AGENTS.md block, marker `<!-- canonical:codex-dispatch-onboarding v1 -->`
(verbatim pattern like SCP-R-030's). Required content (Codex-specific — NOT the Claude acc-hook ceremony):
- **The dispatcher is mandatory for source work** — "Codex source changes MUST go through
  `codex_dispatch.py` with a declared `scope_boundary`; the acc-hook does NOT protect this repo from
  Codex; no bare `codex exec` for source; no `--sandbox` bypass."
- **Consult SCP** (`scp-cli consult` / resolve→consult→audit) — the REACH content CI/Codex agents can't
  get from `~/.claude/CLAUDE.md`.
- **Scope discipline** (out-of-scope → `status=blocked`) + estate cardinals (PR-workflow, no direct-to-main,
  no silent descope).
- **ROLL-OUT RESIDUAL (hard acceptance criterion, R1 safety MAJOR-4):** SCP-R-014 verifies the *committed
  repo-tree* `AGENTS.md`. That is NOT necessarily the file Codex reads at runtime (`~/.codex/AGENTS.md`
  global is empty; `-c`/per-project overrides exist). D1's block must state that the runtime AGENTS.md
  must match, and the ACC handoff must have the operator sync the global/per-project file. Presence-in-repo
  ≠ presence-at-runtime.

### D2 — SCP-R-014 agents-md-onboarding presence gate  (SCP AUTHORS · TWO PHASES)
R1 completeness BLOCKER-2: split like every precedent (SCP-R-009→v1.5.0 dormant / v1.6.0 fire;
SCP-R-030 B.1 dormant / companion-activation; SCP-R-013 dormant / materialiser FUP). **Do NOT collapse.**

**Phase 1 — ship the rule DORMANT** (its own PR): `propose()` → adjudicate → **the four
adjudicate-proposal.md artefacts by name** (R1 completeness MAJOR-3): (a) rule prose
`standards/governance/rules/SCP-R-014-<slug>.md`, (b) `standards/governance/index.json` entry
schema-valid **+ bump the domain `version`**, (c) `docs/DECISIONS.md` D-0NN row, (d) retire `PROP-0NN`
(`adjudication_status: accepted`). Plus `policies/SCP-R-014.rego` (rule-local `scp_r_014_*`;
`canonical_marker := "<!-- canonical:codex-dispatch-onboarding v1 -->"`; exact-substring on
`input.agents_md`; opt-in `.scp/rule-config.yaml` key **`codex-dispatch-onboarding`** — DISTINCT from
`acc-hook-installed`, R1 correctness MINOR-4: a repo can be a Codex target without the acc-hook;
vacuous-pass on absent input) + `policies/tests/scp_r_014_test.rego`. **Finding/remediation text MUST
carry the presence≠compliance disclaimer** (hard criterion, R1 safety MAJOR-3): "marker present ≠ Codex
verified compliant; the dispatcher is the enforcement." Ships warn-baseline-registered but vacuous.

**Phase 2 — companion materialiser (fire live)** (separate PR): extend the SCP-R-030 repo-level opa-eval
step in `policy-check.yml` (~line 902) to ALSO read `AGENTS.md` → `input.agents_md*` and add `"SCP-R-014"`
to `REPO_LEVEL_RULES` (mechanically identical to the existing SCP-R-030 wiring — R1 correctness CONFIRMED
feasible in the SAME step). Add `SCP-R-014` to BOTH `WARN_BASELINE_RULES` sites. **Update
`schemas/rule-config.schema.json`** to accept the `codex-dispatch-onboarding` key (R1 correctness MAJOR-3:
the schema is `additionalProperties:false` — a new key fails validation without this). Selftest fixtures
(marker-present PASS / marker-absent finding), wired with the full workflow-selftest footprint (job-chain
+ aggregator needs + keystone assertion + cases + count-guard). **Author from scratch:**
`policies/VERSIONING.md` SCP-R-014 subsection + Live-members line; `version-manifest.json` MINOR bump;
`STATUS.md` chain entry (R1 completeness BLOCKER-1 — these were dropped in v1, the SAME omission the
ARCH-006 v1 plan made). Cut release + cohort pin-bump. Observation window → future D-NNN deny-promotion.

**Dispatch scope (Phase 2):** `.github/workflows/policy-check.yml`, `.github/workflows/workflow-selftest.yml`,
`policies/**`, `tests/**`, `schemas/rule-config.schema.json`, `STATUS.md`, `version-manifest.json`.

**DESIGN ALTERNATIVE (R1 open):** extend SCP-R-030 (one rule, two markers) vs new SCP-R-014. Recommend
NEW — keeps SCP-R-030's live D-060 observation undisturbed; cost is a duplicated marker-grep shape.

### D3 — a REAL Codex PreToolUse hook (REDESIGNED · ACC AUTHORS · investigation-gated)
R1 correctness BLOCKER-1+2 killed v1's design (the "Codex has no hook" premise was false; the
`ACC_CODEX_DISPATCH_ACTIVE` state-var the wrapper keyed off **does not exist** — `codex_dispatch.py:568`
*removes* a token, exports nothing). Redesign:

**Primary (if feasible): a `.codex/hooks.json` `PreToolUse` hook.** Codex's PreToolUse is shell-matched
and blocks on exit-2. **REQUIRED pre-build investigation:** does Codex's file-write surface in
`workspace-write` mode route through the shell/`apply_patch` command the PreToolUse matcher can see? If
YES → a genuine Codex-side pre-exec gate that refuses source-writes not inside a dispatch — strictly
stronger than a $PATH shim, and **SCP-gateable on `.codex/hooks.json` presence** (mirror D2's marker
pattern → a sibling `SCP-R-015` or fold into SCP-R-014). If NO (Codex writes bypass the shell matcher)
→ fall back to the wrapper, and CORRECT the spec's rationale to "Codex has a hook but it doesn't cover
the write surface," never "impossible."

**Fallback wrapper — with the honesty corrected (R1 safety MAJOR-2):** if a wrapper is used, the real
trivial bypass is `export ACC_CODEX_DISPATCH_ACTIVE=1` (NOT "unset the var" — absence is the blocking
state). To make the guard's block/allow *and its audit log* meaningful, the dispatcher must write a
**per-invocation nonce** (PID-bound, verifiable against `.acc/codex-dispatch-log/`), NOT a static `1` a
caller can spoof — otherwise downgrade the logging claim to "cannot distinguish a spoofed var from a real
dispatch." Either way: a wrapper is a speed-bump (converts accidental→deliberate), not a hard gate.

## The ACC handoff — a real droppable artefact (R1 completeness MAJOR-6)
Authored alongside this spec at `docs/coordination/2026-07-10-WP-SCP-038-ACC-codex-parity-handoff.md`
(WP-SCP-030's handoff as the literal template: why-SCP-asks preamble + a delimited PROMPT block scoped to
a fresh ACC session + pre-flight + per-deliverable acceptance checkboxes + a "what NOT to do" section).

## Governance bookkeeping (R1 completeness MINOR-7/8)
- **File BOTH deferrals as `docs/BACKLOG.md` rows** (not just prose names): `FUP-WP-SCP-038-CODEX-SANDBOX-
  TIGHTENING` (network_access=false default, de-blanket the `trusted` project list — the one genuinely
  HARD lever, deferred because coarse + workflow-breaking) and `FUP-WP-SCP-038-CLAUDE-AGENTS-DEDUP`.
- **WP-level decision:** file a `D-NNN` for WP-SCP-038's *approach* (distinct from SCP-R-014's rule-
  acceptance D-NNN) OR explicitly note none is needed (precedent is mixed) — decide, don't drift.
- **Pilot-success criteria (before fan-out):** SCP-R-014 fires correctly on {mapp-pim, control-tower}
  (marker-present→pass, marker-removed→warn), survives ≥1 Renovate pin-bump cycle, zero false denies.

## Non-goals (honest deferrals, both now BACKLOG-tracked)
- Codex sandbox tightening → `FUP-WP-SCP-038-CODEX-SANDBOX-TIGHTENING`.
- CLAUDE.md/AGENTS.md dedup into a shared include → `FUP-WP-SCP-038-CLAUDE-AGENTS-DEDUP`.

## Open questions for adjudication
1. SCP-R-014 vs extend-SCP-030 (recommend new).
2. Rule domain: **governance recommended** — and note (R1 completeness MAJOR-5) a NEW `agent-lifecycle`
   domain is NOT symmetric: the `standards-rule.schema.json` `domain` enum is CLOSED
   (`governance/architecture/ux/design/product/service-lifecycle`) + needs a new dir + domain-map wiring.
   So "governance" is cheaper AND a fine topical fit.
3. D3 primary-vs-fallback — resolved by the required PreToolUse-reaches-write-surface investigation.
4. Whether the `.codex/hooks.json` presence gate is a new SCP-R-015 or folded into SCP-R-014.
