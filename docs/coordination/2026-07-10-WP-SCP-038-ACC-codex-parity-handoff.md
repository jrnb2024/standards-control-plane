# WP-SCP-038 — ACC handoff: canonical AGENTS.md block + Codex PreToolUse hook

**From:** SCP (WP-SCP-038). **To:** ACC (owns the Codex orchestrator/dispatch canon; D-058). **Date:**
2026-07-10. Template: the WP-SCP-030 CLAUDE.md-preamble handoff (same SCP-proposes / ACC-authors shape).

## Why SCP is asking

The 2026-07-10 investigation confirmed Codex is **not** bound by the acc-hook (it's a Claude Code hook).
Codex is governed post-hoc by `acc/scripts/codex_dispatch.py` — real, but two residuals remain: (1) a
cooperative Codex sees none of the rules a Claude session sees at write time (AGENTS.md is absent/empty/
inconsistent across the estate); (2) nothing stops a bare `codex exec` around the dispatcher. SCP is
authoring the *gate* (SCP-R-014, presence of a canonical AGENTS.md block). **ACC owns the two things SCP
cannot author:** the canonical AGENTS.md content, and the Codex-side hook. This is D-058: SCP proposes +
gates; ACC authors the orchestrator canon.

> **HONEST FRAMING (do not drop):** none of this gates Codex source-writes. Enforcement stays the
> dispatcher + CI + gated-merge. This adds advisory context + presence-gating + (if feasible) a real
> Codex pre-exec hook. Never summarise as "Codex is now gated."

## ═══════════════════════ PROMPT (drop into a fresh ACC session) ═══════════════════════

You are authoring two ACC-owned canonicals for WP-SCP-038. SCP owns the gate; you own the content.

**Deliverable D1 — the canonical AGENTS.md onboarding block.**
Author a marker-delimited block (marker exactly `<!-- canonical:codex-dispatch-onboarding v1 -->` on
line 1) for adopter `AGENTS.md` files. It is the Codex counterpart of the acc-hook CLAUDE.md preamble ACC
already owns — but Codex-specific, NOT a copy of the acc-hook ceremony. It MUST state:
- Codex source changes MUST go through `acc/scripts/codex_dispatch.py` with a declared `scope_boundary`;
  the acc-hook does NOT protect the repo from Codex; the dispatcher's post-hoc scope+verify+audit is the
  gate; no bare `codex exec` for source; never add a `--sandbox` bypass flag.
- Consult SCP before non-trivial work: `scp-cli consult --changed <files>` (or resolve_domain →
  consult_rules → audit_changed); returned rules are normative.
- Scope discipline: out-of-scope work → STOP + return `status=blocked`; PR-workflow, never direct to
  main; no silent descope.
Roll it to the repos that ACTUALLY run Codex (survey: acc, mapp-pim, control-tower, agentic_commerce_pac,
mapp-size-allocation, Recommender). **Runtime-file sync (load-bearing):** SCP-R-014 gates the *committed
repo-tree* AGENTS.md, but Codex reads `~/.codex/AGENTS.md` (global, currently empty) + per-project/`-c`
overrides. Ensure the runtime file(s) carry the same block, or the gate is cosmetic.

**Deliverable D3 — the Codex PreToolUse hook (INVESTIGATE FIRST).**
`codex features list` shows `hooks stable true`; `.codex/hooks.json` supports a `PreToolUse` hook that
blocks on exit-2, currently **shell-command-matched**. **Investigate:** does Codex's file-write surface in
`workspace-write` mode route through the shell/`apply_patch` command the matcher sees?
- If YES: author a `.codex/hooks.json` PreToolUse hook that refuses source-writes not inside an active
  dispatch — a real Codex-side gate. Have the dispatcher expose a verifiable per-invocation signal (a
  PID-bound nonce written to `.acc/codex-dispatch-log/`, NOT a static env var — a static `1` is trivially
  spoofable by `export`). Tell SCP so it can gate `.codex/hooks.json` presence (SCP-R-015 or fold into
  SCP-R-014).
- If NO (writes bypass the matcher): report that, and a wrapper is only a speed-bump (accidental→
  deliberate) — do not claim it as a gate.

**Do NOT:**
- Do NOT author the SCP-R-014 rule (that's SCP's).
- Do NOT add a `--sandbox`/approval bypass to `codex_dispatch.py` (the dispatcher pins workspace-write
  unconditionally — invariant).
- Do NOT weaken the dispatcher's scope/verify/audit on the theory that AGENTS.md now "covers it."
- Do NOT summarise the WP as closing the Codex-gating gap.

## ═══════════════════════ end PROMPT ═══════════════════════

## Pre-flight (ACC)
- [ ] Confirm the AGENTS.md marker string matches SCP-R-014's `canonical_marker` exactly (coordinate with
      SCP — an off-by-one breaks the gate, same trap as SCP-R-030 v1/v2 markers).
- [ ] Confirm `codex features list` still shows `hooks stable`, and read the current
      `.codex/hooks.json` schema (the vendored `migrate-to-codex/references/differences.md` documents the
      PreToolUse shell-matcher semantics).
- [ ] Decide the runtime-AGENTS.md sync mechanism (global vs per-project) with the operator.

## Acceptance
- [ ] D1 canonical block authored + ratified (ACC owns) + rolled to the 6 Codex-user repos + runtime sync.
- [ ] D3 investigation reported (hook-feasible: yes/no) + the corresponding artefact (real hook, or an
      honest wrapper + downgraded claim).
- [ ] SCP notified of the marker + (if D3 real) the `.codex/hooks.json` presence signal, so SCP can gate.

## References
- `docs/reviews/WP-SCP-038-codex-parity-spec.md` (this WP's spec v2) + its R1 dispositions.
- `docs/coordination/2026-05-30-WP-SCP-030-ACC-hooked-repo-preamble-handoff.md` (the precedent this copies).
- `policies/SCP-R-030.rego` (the presence-gate SCP-R-014 mirrors).
