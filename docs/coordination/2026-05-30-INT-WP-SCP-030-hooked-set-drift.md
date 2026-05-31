# INT — WP-SCP-030 hooked-set spec drift (4 → 6) + enforcement-reach nuance

**Type:** Interpretation / spec-drift paper-trail (Reading-B auto-resolution).
**Filed:** 2026-05-30, during the SCP orchestration session that wrote the SCP-R-030 Phase-B autonomous-run prompt (triggered by ACC executing the WP-SCP-030 Phase-A.3 handoff).
**Governing convention:** `feedback_autonomous_spec_drift_resolution.md` (Reading-B) — overnight/autonomous runs auto-resolve **in-intent feature-shape WP-substrate drift** (take the recommended option + file an INT paper-trail + proceed); STILL park on auth / security / high-blast / data-contract / cure-worse / scope-beyond-intent.

## Why Reading-B applies (not park)

| Park trigger | Present? |
|---|---|
| auth / security surface | No — hooked-repo onboarding conformance; warn-baseline; LINKAGE-not-VALUES |
| high blast radius | No — docs-only this turn; the rule is warn-baseline + opt-in + reversible |
| data-contract change | No — additive top-level rule-config opt-in; `additionalProperties:false` preserved |
| cure-worse | No |
| scope beyond intent | No — the WP's intent is "every hooked repo's CLAUDE.md carries the canonical"; more hooked repos = more of the same intent |

⇒ Auto-resolve. The resolution is also **already what the authority (ACC) did**, so SCP is conforming to published reality, not inventing scope.

## The drift

- **Plan said:** hooked set = **4** — ACC / CT / RI / SCP (`WP-SCP-030` §1, §2.1, §2.2.1, §3, §5 A.3), from the audit it referenced.
- **Live reality (verified 2026-05-30):** `grep acc-hook ~/Projects/<repo>/.claude/settings.json` across local checkouts →

  | Repo | acc-hook in settings.json |
  |---|---|
  | acc | HOOKED |
  | control-tower | HOOKED |
  | mapp-pim | HOOKED |
  | mapp-size-allocation | HOOKED |
  | mapp-returns-intelligence | HOOKED |
  | standards-control-plane | HOOKED |
  | mapp-visual-shopping | no-acc-hook (governance hooks only — correctly excluded) |

  ⇒ **6 hooked repos.** PIM + SA were hooked in the 2026-05-27 WS-D estate iteration, after the plan's audit.

## Resolution

1. **Adopt the 6-repo set** wherever the plan said 4 (recorded in plan §9 amendment).
2. **No new propagation work for SCP** — ACC already propagated the canonical preamble to all 6 (ACC #342 / CT #468 / PIM #372 / SA #169 / RI Mapp-Labs#216) in its Phase-A.3 handoff; SCP notify PR #194 already records "6-repo propagation."
3. **B.2 cohort cascade opt-in is bounded by enforcement reach** (below).

## Enforcement-reach nuance (the substantive consequence — no silent caps)

SCP-R-030 only *fires* in a repo that runs SCP's `policy-check` workflow. Therefore:

- **Hooked set (Layer-1 marker):** {ACC, CT, PIM, SA, RI, SCP} = 6.
- **SCP cohort (runs `policy-check.yml`):** {CT, PIM, mapp-doc-agent} + SCP-self.
- **SCP-R-030 enforcement reach = hooked ∩ cohort = {CT, PIM, SCP-self}** = 3.

Consequences:
- **ACC / SA / RI** carry the canonical marker but **Layer-2 cannot gate them** until they onboard as SCP cohort adopters → forward item **`FUP-WP-SCP-030-EXTEND-REACH-ACC-SA-RI-001`** (not a blocker).
- **mapp-doc-agent** is in the cohort but **not hooked** → never opts in (`acc-hook-installed` absent ⇒ vacuous-pass; harmless).
- The **B.2 cascade opt-in** therefore touches only **{CT, PIM}** (+ SCP-self, done in B.1) — each only *after* its propagation PR merges (so the marker is live on main; the rule never warns falsely).

This is the expected shape of **enforcement-plane-not-control-plane** (D-058): the canonical reaches everywhere; SCP's *gate* reaches its cohort. Stating it prevents a false "we gate all hooked repos" impression.

## Forward items opened

- `FUP-WP-SCP-030-EXTEND-REACH-ACC-SA-RI-001` — when/if ACC, SA, RI onboard as SCP cohort adopters, flip their `acc-hook-installed: true` so SCP-R-030 gates them too. Until then they rely on Layer-1 (the canonical in their CLAUDE.md) + their own acc-hook, not on SCP's gate.

## Cross-refs

- Plan §9 amendment: `docs/plans/WP-SCP-030-hooked-repo-onboarding-conformance-v1.md`.
- Autonomous-run prompt §5.5 + §6: `docs/continuation-prompts/2026-05-30-WP-SCP-030-SCP-R-030-phase-b-autonomous.md`.
- ACC authority + propagation: ACC #342 (canonical guide + ADR-019) + SCP notify #194.
