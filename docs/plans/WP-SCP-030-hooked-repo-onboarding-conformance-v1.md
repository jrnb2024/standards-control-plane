# WP-SCP-030 — Hooked-repo onboarding conformance (D-058 second domain; proving ground)

**Version:** v1.0 (ACTIVE; promoted from named-but-not-built 2026-05-30)
**Strategic anchor:** `docs/decisions/D-058-scp-canonical-conformance-strategy-2026-05-29.md` §7 (Phase C roadmap) — promoted to active because it is **unblocked, docs-only, low-blast-radius, and immediately relieves a recurring pain**, making it the ideal proving ground for the D-058 Phase A → Phase B canonical-conformance machinery while the auth domain (WP-SCP-028) waits on CT prereqs.
**Domain authority:** ACC (owns the acc-hook). **SCP gates conformance; ACC authors the canonical.**
**Successor decision reservation:** D-060 — 4-week observation-window outcome (deny-promote / hold-at-warn / re-scope). (D-059 is reserved for WP-SCP-028 auth; do NOT reuse.)

---

## §1 Why this exists (the recurring pain)

Every Claude Code session that opens in a hooked repo (ACC, CT, RI, SCP) rediscovers the acc-hook by **tripping it**: it reads CLAUDE.md (which frames four-tier dispatch as a soft "preferred default"), sees a small task, starts writing source directly, gets denied mid-work, and pauses with a confused menu — one option of which (disable the hook) D-057 forbade estate-wide. Verified 2026-05-30 in CT: `.claude/settings.json` has the hook live, but CT's CLAUDE.md never warns the hook HARD-BLOCKS writes nor gives a session-start ceremony.

This is the textbook D-058 problem: a cross-cutting canonical ("how to operate in a hooked repo") exists, but **estate-wide conformance is not enforced**, so it doesn't reach the sessions that need it. The fix is canonical-conformance enforcement: ACC authors the onboarding-preamble contract; SCP gates that every hooked repo's CLAUDE.md carries it.

## §2 Scope + invariants

### 2.1 Goal

Two layers, in D-058 publish-before-gate order:

- **Layer 1 (Phase A — canonical content):** ACC authors a canonical "hooked-repo onboarding preamble" contract (what every hooked CLAUDE.md must contain); each hooked repo (ACC, CT, RI, SCP) instantiates it in its CLAUDE.md with its own ceremony. Docs-only ⇒ always-allowed by the hook ⇒ zero build friction. Immediate pain relief.
- **Layer 2 (Phase B — enforcement):** SCP-R-030 gates that a hooked repo's CLAUDE.md carries the canonical preamble marker. Warn-baseline first; 4-week observation; deny-promote at D-060. This is what makes Layer 1 durable (a new hooked repo, or a CLAUDE.md edit that drops the preamble, is caught).

### 2.2 Hard invariants

1. **LINKAGE not VALUES.** SCP-R-030 checks for the *presence of the canonical preamble marker* in CLAUDE.md, plus that the always-allowed list + never-disable rule + a ceremony pointer are present. It does NOT prescribe the repo's ceremony (that's repo-specific: CT four-tier Codex; SCP Pattern-3 dispatch). Inherited from D-049 + D-058.
2. **ACC is the authority.** The preamble *contract* (required structure) is ACC's to ratify. SCP proposes a draft, ACC ratifies + propagates. SCP never becomes the hook authority.
3. **Warn-baseline first.** SCP-R-030 ships at `warn`; deny-promotion requires D-060.
4. **Always-allowed build path.** Every Layer 1 artefact is `docs/**` or `CLAUDE.md` — always-allowed — so the fix routes around the very problem it solves (no ceremony needed to write the preamble).
5. **Reversibility.** SCP-R-030 flips to `disabled` via rule-config in <24h Renovate cycle.

### 2.3 Anti-scope

- Does NOT modify the acc-hook itself (ACC kernel; out of SCP scope).
- Does NOT prescribe each repo's self-build ceremony — only that CLAUDE.md documents *a* ceremony + the always-allowed list + the never-disable rule.
- Does NOT auto-install the hook or the preamble anywhere — SCP gates; it does not push state (enforcement-plane-not-control-plane, D-058 §1).
- Does NOT depend on 026F (gate-path domain, like WP-SCP-028).

## §3 The canonical preamble contract (Layer 1 — ACC ratifies)

SCP's proposed contract — what every hooked-repo CLAUDE.md MUST contain (ACC ratifies the final shape):

1. **A canonical marker** on/near line 1: `<!-- canonical:acc-hook-onboarding v1 -->` (HTML comment; greppable; non-rendering). This is SCP-R-030's LINKAGE target.
2. **A hard-gate warning** stating the hook BLOCKS source writes (not soft guidance).
3. **The always-allowed path list** (`docs/**`, `CLAUDE.md`, `AGENTS.md`, `.acc/work-packages/**`, probe dirs, memory).
4. **The gated path list** + the repo's **ceremony pointer** (CT: four-tier Codex dispatch via `scripts/codex_dispatch.py`; SCP: Pattern-3 session-start dispatch via `scripts/operator/scp-pattern3-dispatch.sh`; ACC: four-tier / `acc orchestrate`; RI: per its convention).
5. **The never-disable rule** (D-057): a tripped session declares scope or asks the operator; it does NOT disable enforcement.

The SCP-self CLAUDE.md (shipped in this WP's PR) is the reference instantiation + the dogfood.

## §4 SCP-R-030 design (Layer 2 — the trigger wrinkle)

**Known design problem (flagged honestly at plan stage):** `.claude/settings.json` is **gitignored** estate-wide. A Rego rule evaluating the checked-out tree cannot read it → cannot naively detect "the hook is installed." So SCP-R-030's *trigger* needs a committed signal. Three candidate triggers (decide at code-stage 3-lens review):

| Option | Trigger mechanism | Pro | Con |
|---|---|---|---|
| **(a) rule-config opt-in** | Repo declares `acc-hook-installed: true` in committed `.scp/rule-config.yaml` | Explicit; committed; adopter-controlled | Relies on the repo opting in (a non-hooked repo could forget — but then it has no hook to onboard for, so harmless) |
| **(b) committed install marker** | ACC install ceremony drops a tracked `.acc/hook-installed` marker (committed, unlike settings.json) | Auto-set by install; can't forget | Requires an ACC-side install-script change (cross-repo) |
| **(c) ACC-published estate registry** | SCP reads CT/ACC-published `estate_repos.yaml` listing hooked repos | Single source of truth; matches D-058 4-artefact contract | Needs the registry published first (gating dependency) |

**Recommendation:** ship (a) for v1 (zero cross-repo dependency; adopter-controlled; harmless false-negative), and name (b)+(c) as hardening successors. The rule:

- **Vacuous-pass** when `.scp/rule-config.yaml` lacks `acc-hook-installed: true` (repo isn't a hooked repo, or hasn't opted in).
- **When `acc-hook-installed: true`:**
  - **deny** if `CLAUDE.md` is absent OR lacks the `<!-- canonical:acc-hook-onboarding v1 -->` marker (post-deny-promote; warn pre-promote)
  - **warn** if the marker is present but a required element is missing (always-allowed list / ceremony pointer / never-disable rule) — heuristic substring checks
- Emits the canonical `SCPFinding` shape.

## §5 Phasing

| Phase | Owner | Deliverable | State |
|---|---|---|---|
| **A.1** — canonical contract draft | SCP (this PR) | `docs/coordination/2026-05-30-WP-SCP-030-ACC-hooked-repo-preamble-handoff.md` — proposes the contract + droppable ACC prompt | THIS PR |
| **A.2** — SCP-self reference instantiation | SCP (this PR) | `CLAUDE.md` with the canonical preamble (dogfood) | THIS PR |
| **A.3** — ACC ratifies contract + propagates | ACC | ACC authors the contract canonically + adds preamble to ACC / CT / RI / **PIM / SA** CLAUDE.md | **DONE 2026-05-30** — see §5.1 |
| **B.1** — SCP-R-030 rule + schema + tests | SCP (autonomous run, post-A.3) | `policies/SCP-R-030.rego` + rule-config schema extension + fixtures; warn-baseline | GATED on A.3 + trigger decision |
| **B.2** — cohort cascade + 4-week observe | SCP + operator | v1.x cut; propagate; observe | GATED on B.1 |
| **B.3** — D-060 outcome | operator | deny-promote / hold / re-scope | GATED on B.2 |

### §5.1 Phase A.3 — ACC ratification + propagation (DONE 2026-05-30)

ACC (the acc-hook authority) executed the A.3 handoff. **Confirmation for SCP's Layer 2 (B.1):**

- **Marker string CONFIRMED — unchanged from the proposal:** `<!-- canonical:acc-hook-onboarding v1 -->`. ACC ratified it verbatim; **SCP-R-030 should grep for exactly this.** No alternative marker was chosen.
- **Canonical contract authored by ACC:** `~/Projects/acc/docs/guides/hooked-repo-onboarding-preamble.md` (ACC owns it; SCP gates it). It ratifies the 5 required preamble elements (marker / hard-gate warning / always-allowed list / gated-set + per-repo ceremony pointer / D-057 never-disable rule). The always-allowed set is sourced from `hook/cmd/acc-hook/main.go` `alwaysAllowed()` and matches SCP's reference instantiation exactly (no drift).
- **⚠️ Hooked-repo set is larger than this plan assumed — B.1/B.2 must update the cohort.** This plan + the handoff name the hooked set as **ACC / CT / RI / SCP** (4). ACC live-verified (grep of each repo's `.claude/settings.json`, not the older audit alone) that the acc-hook is registered in **6 repos**: **ACC, control-tower, mapp-pim, mapp-size-allocation, mapp-returns-intelligence, standards-control-plane**. PIM + SA were hooked in the 2026-05-27 WS-D estate iteration (post the 2026-05-24 audit this plan referenced). `mapp-visual-shopping` carries governance hooks only (no acc-hook) → **excluded** until the acc-hook is wired there. **SCP-R-030's cohort cascade (B.2) and any `acc-hook-installed: true` opt-in propagation must cover all 6 — PIM + SA included** — or PIM/SA sessions keep tripping the hook unaware (the exact pain this WP closes).
- **Propagation PRs (each adds the marker on line 1 + the preamble naming that repo's ceremony):**
  | Repo | PR | Ceremony named |
  |---|---|---|
  | ACC (contract + self) | jrnb2024/ACC#342 | four-tier Codex dispatch |
  | control-tower | jrnb2024/control-tower#468 | four-tier Codex dispatch |
  | mapp-pim | jrnb2024/mapp-pim#372 | Codex dispatch (four-tier governance) |
  | mapp-size-allocation | jrnb2024/mapp-size-allocation#169 | four-tier Codex dispatch |
  | mapp-returns-intelligence | Mapp-Labs/mapp-returns-intelligence#216 | four-tier dispatch (DEC-054; ACC's `codex_dispatch.py --cwd`) |
  | standards-control-plane | already live (#192, Phase A.2) | Pattern-3 session-start dispatch (D-057) |
- **B.1 element-presence heuristics (per §4):** all 5 instantiations use the SCP-reference shape, so the warn-level substring checks (always-allowed list / ceremony pointer / never-disable rule) will pass on the canonical headings (`## Always-allowed`, `## Source writes are GATED`, `## If you trip the hook`).

**A.3 is no longer GATED — Phase B.1 (SCP-R-030 rule) is now unblocked.**

## §6 Success criteria (this PR = Phase A.1 + A.2)

- [ ] SCP-self `CLAUDE.md` created carrying the canonical preamble + marker (dogfood reference)
- [ ] ACC coordination memo + droppable ACC prompt filed
- [ ] This plan-doc filed; BACKLOG WP-SCP-030 row promoted named-but-not-built → Phase-A-active
- [ ] STATUS chain row (triggers check-invocation-log-entry)
- [ ] D-060 reserved (not consumed)

~~Phases A.3 + B are GATED on ACC ratifying the contract (Layer 1 cross-repo authority step).~~ **A.3 DONE 2026-05-30** (§5.1); Phase B.1 is now unblocked.

## §7 Relationship to WP-SCP-028 (auth)

Auth remains the strategic flagship first domain. WP-SCP-030 is the **proving ground**: it exercises the identical Phase A (publish canonical) → Phase B (gate conformance) machinery on a low-risk, unblocked, docs-only domain *while* CT does the auth prereqs. Lessons from WP-SCP-030's Phase B (especially the gitignored-trigger resolution) feed directly into WP-SCP-028 + every subsequent Phase C domain. Running it first is parallelism between a blocked-priority domain and an unblocked-rehearsal domain — not a reordering of "auth first" as the flagship.

## §8 D-060 reservation

D-060 is RESERVED for the WP-SCP-030 Layer-2 observation-window outcome. Do NOT assign D-060 to any other decision. (D-059 = WP-SCP-028 auth.) Reservation pattern mirrors D-021 / D-041-043 / D-055-056 / D-059.

---

**Identified at:** 2026-05-30 operator question ("why do we hit the hook every time — can SCP tell every session?").

**Filed:** 2026-05-30 (this PR; promoted from D-058 §7 roadmap).

**Closes when:** Phase A.3 + B complete + D-060 ratifies outcome.
