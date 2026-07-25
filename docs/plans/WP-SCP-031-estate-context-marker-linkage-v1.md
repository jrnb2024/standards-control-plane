# WP-SCP-031 (WP-ESC-012b) — Estate-context bootstrap marker linkage (D-058 canonical-conformance)

**Version:** v1.0 (ACTIVE)
**Strategic anchor:** `docs/decisions/D-058-scp-canonical-conformance-strategy-2026-05-29.md` — SCP gates LINKAGE to a domain authority's canonical; it never becomes the authority. This WP applies the identical Phase A (publish canonical) → Phase B (gate conformance) machinery proven by WP-SCP-030 to a NEW domain: the estate-context bootstrap.
**Domain authority:** control-tower (owns `contracts/estate-context-marker.md`). **SCP gates conformance; control-tower authors the canonical.**
**Successor decision reservation:** a future D-NNN — the observation-window outcome (deny-promote / hold-at-warn / re-scope). Mirrors SCP-R-030's D-060 note; NOT consumed by this WP.

---

## §1 Why this exists (the recurring pain)

Every agent session that opens in an estate repo is supposed to consult the estate spine (the two authoritative planes — `estate-knowledge.consult_estate` for "what exists / in-flight / where things live" and `scp-standards` for "how we build this / am I about to break a standard") BEFORE acting on any non-trivial task. That instruction lives in the repo's agent-instruction file. But there are TWO such surfaces — `CLAUDE.md` (read by Claude Code) and `AGENTS.md` (read by Codex and other agent runtimes) — and nothing enforces that BOTH carry the bootstrap. A repo that adds the marker to `CLAUDE.md` but forgets `AGENTS.md` silently strands every Codex session: it never learns the estate operating context and re-derives, duplicates, or breaks a standard the spine would have caught.

This is the textbook D-058 problem: a cross-cutting canonical ("consult the estate spine before acting") exists, but estate-wide conformance across BOTH instruction surfaces is not enforced. The fix is canonical-conformance enforcement: control-tower authors the estate-context-marker contract; SCP gates that every opted-in repo's CLAUDE.md AND AGENTS.md carry it.

## §2 Scope + invariants

### 2.1 Goal

- **Layer 1 (canonical content):** control-tower authors a canonical estate-context bootstrap marker contract (`contracts/estate-context-marker.md`, `estate-context-bootstrap v1`); each opted-in repo instantiates the marker at the top of BOTH `CLAUDE.md` and `AGENTS.md`.
- **Layer 2 (enforcement):** SCP-R-031 gates that an opted-in repo's `CLAUDE.md` AND `AGENTS.md` each carry the canonical marker in their top-of-file block, and that neither leaks dynamic Estate state. Warn-baseline first; deny-promotion reserved to a future operator decision.

### 2.2 Hard invariants

1. **LINKAGE not VALUES.** SCP-R-031 checks for the *presence of the canonical marker* in the top-of-file block of each instruction file. It does NOT prescribe the estate content, the spine's contents, or any repo-specific context. Inherited from D-049 + D-058.
2. **control-tower is the authority.** The marker *contract* (the exact string, the STATIC-MARKER rule) is control-tower's to ratify at `contracts/estate-context-marker.md`. SCP never becomes the estate-context authority (D-058 anti-pattern).
3. **TWO files, one marker.** BOTH `CLAUDE.md` and `AGENTS.md` must carry the marker. This is the whole point vs SCP-R-030 (which gates `CLAUDE.md` only). The rule has independent teeth on each file — a present-and-marked `CLAUDE.md` does not excuse an un-marked `AGENTS.md`.
4. **STATIC-MARKER.** An instruction file carries ONLY the static marker, never dynamic Estate state. Live state (identity: `workspace_id`/`org_id`/`principal`; content-integrity: `sha256:`/`digest`; freshness: `freshness`/`expires_at`/`observed_at`/`watermark`) belongs to the runtime Estate-context plane, not a committed file. A leaked dynamic token in the top-of-file block fires `dynamic_state` — the file is being mis-used as a state channel (drift + stale-context hazard).
5. **Warn-baseline first.** SCP-R-031 ships at `warn`; deny-promotion requires a future operator decision.
6. **Reversibility.** SCP-R-031 flips to `disabled` via the generic `rules.SCP-R-031.disable` (+justification +expires_at) rule-config path, NOT a bespoke key.
7. **Vacuous-safe.** Absent `input.rule_config` (the production per-file envelope, until the companion PR materialises inputs) → the rule vacuously passes. Absent opt-in (`estate-context-marker` not true) → vacuously passes.

### 2.3 Anti-scope

- Does NOT author or modify the estate-context-marker contract itself (control-tower owns it; out of SCP scope).
- Does NOT prescribe the estate content each repo documents — only that the marker is present + no dynamic state leaks.
- Does NOT auto-install the marker anywhere — SCP gates; it does not push state (enforcement-plane-not-control-plane, D-058).
- Does NOT gate file ABSENCE. If `CLAUDE.md` or `AGENTS.md` is absent entirely, no finding fires for that surface (a distinct concern, out of scope for this LINKAGE rule).

## §3 The canonical marker (Layer 1 — control-tower ratifies)

- **Marker string (verbatim):** `<!-- canonical:estate-context-bootstrap v1 -->` (HTML comment; greppable; non-rendering). This is SCP-R-031's LINKAGE target.
- **Placement:** in the top-of-file block (first 5 lines) of BOTH `CLAUDE.md` and `AGENTS.md`. The 5-line window (vs SCP-R-030's 3) allows a short title / front-matter line above the marker on either surface, while still anchoring top-of-file to defeat a buried / code-fenced spoof.
- **Contract owner:** control-tower, at `contracts/estate-context-marker.md`.

## §4 SCP-R-031 design (Layer 2)

- **Opt-in trigger:** committed `.scp/rule-config.yaml` `estate-context-marker: true`, read from `input.rule_config` (mirrors SCP-R-030's `acc-hook-installed` and the SCP-R-006 `acc-cross-repo-caller-scoped` precedent). A repo that isn't in the estate-context cohort simply doesn't opt in → harmless vacuous-pass.
- **When `estate-context-marker: true`:**
  - **warn** if `CLAUDE.md` is present but lacks the marker in its top 5 lines → `marker_absent` naming CLAUDE.md.
  - **warn** if `AGENTS.md` is present but lacks the marker in its top 5 lines → `marker_absent` naming AGENTS.md.
  - **warn** if either file carries a forbidden dynamic-Estate token in its top 5-line block → `dynamic_state` naming the file, with the message "…carries dynamic Estate state; instruction files must carry only the static marker…".
- **Suppression:** reuses `scp_common.rego`'s `scp_active_waiver_for` + `scp_rule_config_disabled` exactly as SCP-R-030 does; emits the standard waiver / rule-config observability `warn` records.
- **Predicate isolation:** defines its OWN `scp_r_031_*` predicates (SCP-R-004 SAFE-MAJ-001 precedent); total-function content helpers keep every downstream predicate defined on malformed (non-string) input.

## §5 Phasing + registration state

| Phase | Owner | Deliverable | State |
|---|---|---|---|
| **A** — canonical marker contract | control-tower | `contracts/estate-context-marker.md` (`estate-context-bootstrap v1`) | control-tower authority (Layer 1) |
| **B.1** — SCP-R-031 rule + tests + fixtures | SCP (this WP / WP-ESC-012b) | `policies/SCP-R-031.rego` + `policies/tests/scp_r_031_test.rego` + 5 `tests/workflow/fixture-scp-r-031-*` + WARN_BASELINE membership + version-manifest bump | **THIS PR** |
| **B.2** — companion workflow activation | SCP | materialise `input.rule_config` + `input.claude_md*` + `input.agents_md*`; add SCP-R-031 to `REPO_LEVEL_RULES`; add `estate-context-marker` to `schemas/rule-config.schema.json`; wire the 5 fixtures into `workflow-selftest.yml` | **COMPANION PR (out of this PR's scope)** |
| **B.3** — observation-window outcome | operator | deny-promote / hold / re-scope | GATED on B.2 |

### §5.1 What ships in THIS PR (B.1)

- `policies/SCP-R-031.rego` — the rule (warn-baseline, vacuous-safe).
- `policies/tests/scp_r_031_test.rego` — the mandatory per-rule OPA coverage suite (the repo's `--fail-on-empty --threshold 90` gate at `.github/workflows/policy-check.yml` "Enforce per-rule OPA coverage" + `scripts/scp-pre-push-verify.sh` gate 3 requires it; 14 tests, ~98% coverage).
- `tests/workflow/fixture-scp-r-031-{marker-present-both,marker-absent-claude,marker-absent-agents,dynamic-state-present,disabled}` — the 5 end-to-end fixtures (staged; activated by B.2's `workflow-selftest.yml` wiring, exactly as WP-SCP-030's fixtures were staged before its companion PR).
- `.github/workflows/policy-check.yml` — SCP-R-031 added to BOTH `WARN_BASELINE_RULES` sites (the render-deny threshold set + the scorecard set), kept in lockstep.
- `version-manifest.json` — bumped `2.1.0 → 2.2.0` (additive-rule MINOR per `policies/VERSIONING.md`).

### §5.2 Deferred to the companion PR (B.2) — explicitly, not silently

These belong to the companion workflow-activation PR (mirroring how WP-SCP-030 split the rule PR from its companion materialisation PR). They are named here so nothing is silently descoped:

1. **Input materialisation.** `policy-check.yml`'s repo-level `opa eval` step (the `REPO_LEVEL_RULES` block) must materialise `input.rule_config` + `input.claude_md{,_present}` + `input.agents_md{,_present}` from the adopter root and add `SCP-R-031` to `REPO_LEVEL_RULES`. Until then the rule is loaded but DORMANT/vacuous in production (the SAFE coupling direction: warn-baselined-but-not-materialised never blocks).
2. **Schema opt-in key.** `schemas/rule-config.schema.json` (top-level `additionalProperties: false`) must gain an `estate-context-marker` boolean property, mirroring the `acc-hook-installed` entry SCP-R-030 added, so a real adopter's `.scp/rule-config.yaml` opt-in is schema-valid.
3. **Selftest wiring.** `workflow-selftest.yml` must add the 5 `fixture-scp-r-031-*` reusable-workflow invocations (+ their stash jobs + oracle assertions), mirroring the 4 `fixture-scp-r-030-*` invocations.

## §6 Success criteria (this PR = B.1)

- [x] `policies/SCP-R-031.rego` — models SCP-R-030 verbatim, extended to BOTH files; `opa fmt` clean, `regal lint` clean.
- [x] `policies/tests/scp_r_031_test.rego` — 14 tests, ≥90% coverage (`--fail-on-empty --threshold 90` GREEN).
- [x] 5 `tests/workflow/fixture-scp-r-031-*` fixtures, each producing its `expected-annotations.json` (verified via the Option-A `opa eval` mirror).
- [x] SCP-R-031 in BOTH `WARN_BASELINE_RULES` sites; NOT in any deny/blocking set.
- [x] `version-manifest.json` bumped to `2.2.0` (additive-rule MINOR).
- [x] Deny-promotion decision RESERVED (not consumed).

## §7 Relationship to SCP-R-030

SCP-R-030 (hooked-repo onboarding conformance) is the proving-ground precedent: same D-058 LINKAGE-not-VALUES machinery, same opt-in-via-`input.rule_config` trigger, same warn-baseline-then-observe cadence, same rule/companion-PR split. SCP-R-031 reuses that machinery on a NEW domain (estate-context) and extends it in exactly one dimension: it gates TWO instruction surfaces (CLAUDE.md + AGENTS.md) instead of one, and adds a STATIC-MARKER negative check. It does NOT touch SCP-R-030 or its fixtures.

---

**Filed:** 2026-07-25 (WP-ESC-012b).

**Closes when:** B.1 (this PR) + B.2 (companion activation) complete + the reserved operator decision ratifies the observation-window outcome.
