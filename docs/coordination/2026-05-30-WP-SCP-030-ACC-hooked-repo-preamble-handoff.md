# ACC handoff — canonical hooked-repo onboarding preamble (WP-SCP-030 Layer 1)

**From:** Standards Control Plane (SCP), per D-058 + WP-SCP-030
**To:** ACC (Agent Control Centre) team / an ACC Claude Code session — **ACC owns the acc-hook, so ACC is the authority for this canonical**
**Filed:** 2026-05-30
**Nature:** Self-contained work brief. Drop the **"PROMPT"** section into a fresh Claude Code session rooted at `~/Projects/acc`, OR hand it to the ACC operator. Surrounding text is the requester's (SCP) record.

---

## Why SCP is asking (context — not part of the droppable prompt)

**The recurring pain:** every Claude Code session that opens in a hooked repo (ACC, CT, RI, SCP) rediscovers the acc-hook by *tripping it* mid-work, then pauses confused — sometimes offering to disable the hook (forbidden by D-057). Verified 2026-05-30: CT's `.claude/settings.json` has the hook live, but CT's CLAUDE.md frames four-tier dispatch as a soft "preferred default" and never warns the hook HARD-BLOCKS writes or gives a session-start ceremony. The knowledge exists but doesn't reach the session in a form that stops it.

**The fix (D-058 canonical-conformance shape):** the "how to operate in a hooked repo" canonical should be **authored by ACC** (you own the hook) and **gated by SCP** (SCP-R-030 checks every hooked repo's CLAUDE.md carries it). This handoff is **Layer 1** — author the canonical + propagate it. SCP's **Layer 2** (the gate) follows once you've ratified the contract.

**Why ACC and not SCP:** if SCP authored the hook-ceremony canonical, SCP would drift into being the hook authority — the exact D-058 anti-pattern. ACC owns the hook (ADR-019; Phase X). SCP proposes a draft below; **you ratify the canonical shape.**

**This is additive + not urgent.** It must not disrupt any in-flight ACC work (EST-P, cosignal, v1.1 cleanup). It's docs-only on the receiving repos (CLAUDE.md is always-allowed by the hook), so there's no hook friction in doing it.

## SCP's reference instantiation (already shipped)

SCP added the canonical preamble to its own `CLAUDE.md` (the dogfood reference) in the WP-SCP-030 Phase A PR. See `~/Projects/standards-control-plane/CLAUDE.md` — the block above the `<!-- canonical:acc-hook-onboarding v1 -->` marker is the proposed shape. Reuse / adapt it.

---

## ═══════════════ PROMPT (drop into an ACC Claude Code session) ═══════════════

You are working in the ACC repo at `~/Projects/acc`. ACC owns the acc-hook (Phase X kernel hook; ADR-019). The Standards Control Plane (SCP) project needs ACC to **author a canonical "hooked-repo onboarding preamble" contract** so every hooked repo's CLAUDE.md warns sessions about the hook at startup + gives the ceremony — instead of sessions rediscovering the hook by tripping it. SCP will then gate conformance (SCP-R-030). **ACC is the authority here** — you ratify the canonical; SCP only gates it. This work is **additive, docs-only, and not urgent** — do not disrupt in-flight EST-P / cosignal / v1.1 work.

### Deliverable 1 — author the canonical preamble contract

Author a short canonical doc (suggested path: `~/Projects/acc/docs/guides/hooked-repo-onboarding-preamble.md`) that defines **what every hooked repo's CLAUDE.md MUST contain**. SCP proposes this structure (ratify / adjust per ACC's authority over the hook):

1. **A canonical marker** on/near line 1 of CLAUDE.md: `<!-- canonical:acc-hook-onboarding v1 -->` (HTML comment; greppable; non-rendering). This is the LINKAGE target SCP-R-030 will grep for. **Confirm the marker string** (SCP will gate on exactly this; if ACC prefers a different marker, name it + tell SCP).
2. **A hard-gate warning** — the hook BLOCKS source writes; this is enforcement, not preference.
3. **The always-allowed path list** — `docs/**`, `CLAUDE.md`, `AGENTS.md`, `.acc/work-packages/**`, `.acc/codex-probes/**`, `.acc/claude-probes/**`, `~/.claude/projects/**/memory/*.md`. (Verify against the hook's actual `alwaysAllowed()` in `hook/cmd/acc-hook/main.go` — you own the source of truth; reconcile if it's drifted.)
4. **The gated path list + a per-repo ceremony pointer** — each repo names ITS self-build pattern (CT/ACC = four-tier Codex dispatch via `scripts/codex_dispatch.py`; SCP = Pattern-3 session-start dispatch via `scripts/operator/scp-pattern3-dispatch.sh` per D-057; RI = per its convention).
5. **The never-disable rule** — a tripped session declares scope or asks the operator; it does NOT disable enforcement (D-057, estate-wide).

The doc should make clear: the contract specifies the *required structure*; each repo fills in its *own ceremony*. (Auth-authority parallel: like CT owns `auth-contract-v1.yaml`, ACC owns this.)

### Deliverable 2 — instantiate the preamble in ACC's own CLAUDE.md

Add the canonical preamble block (with the marker) to `~/Projects/acc/CLAUDE.md`, naming ACC's ceremony (four-tier dispatch / `acc orchestrate`). ACC's CLAUDE.md already documents Phase X extensively — fold the onboarding preamble to the TOP so a session reads it first.

### Deliverable 3 — propagate to CT + RI (the other hooked repos)

Either directly (small docs PRs per repo — CLAUDE.md is always-allowed, no ceremony) or by handing each repo a one-line instruction to add the marker + its ceremony. The hooked repos as of 2026-05-30: **ACC, CT, RI (mapp-returns-intelligence), SCP** (SCP already done). Verify the current hooked-repo set against the estate hook-install audit (`docs/audits/estate-acc-hook-install-state-*.md`) — it may have grown since 2026-05-24.

### Pre-flight (do this first)

1. `git -C ~/Projects/acc fetch origin && git -C ~/Projects/acc status` — clean tree on main.
2. Read `hook/cmd/acc-hook/main.go` `alwaysAllowed()` — confirm the always-allowed list is accurate (you're the source of truth).
3. Read SCP's reference instantiation: `~/Projects/standards-control-plane/CLAUDE.md` (the block above the marker).
4. Check the estate hook-install audit for the current hooked-repo set.
5. Confirm no in-flight ACC work touches CLAUDE.md / the hook docs in a conflicting way.

### Acceptance criteria

- [ ] Canonical preamble contract doc authored + the marker string confirmed (`<!-- canonical:acc-hook-onboarding v1 -->` or ACC's chosen alternative, communicated to SCP).
- [ ] ACC's own CLAUDE.md carries the preamble (marker + always-allowed list + ceremony pointer + never-disable rule).
- [ ] CT + RI CLAUDE.md carry it (directly, or instructions handed off).
- [ ] PR opened with ACC's standard governance (3-lens review per ACC's discipline if it touches anything beyond docs; docs-only may be lighter).
- [ ] SCP notified of the confirmed marker string so SCP-R-030 (Layer 2) gates on the right target.

### What NOT to do

- Do NOT change the acc-hook binary / `main.go` behaviour — this is docs/canonical authoring only.
- Do NOT disrupt in-flight EST-P / cosignal / v1.1 work for this; it's additive + not urgent.
- Do NOT have SCP own this canonical — ACC ratifies; SCP gates. (If you disagree with the proposed structure, change it — you're the authority.)

### When done

Notify SCP (or update `~/Projects/standards-control-plane/docs/plans/WP-SCP-030-hooked-repo-onboarding-conformance-v1.md` §5 phasing table: Phase A.3 done) with the confirmed marker string. SCP then ships Layer 2 (SCP-R-030 conformance rule).

## ═══════════════ END PROMPT ═══════════════

---

## Notes for the SCP requester (not part of the droppable prompt)

- **Layer 2 (SCP-R-030) is GATED on this handoff's Deliverable 1** — SCP can't gate on a marker ACC hasn't ratified. Once ACC confirms the marker string, SCP's WP-SCP-030 Phase B (the rule) can be authored.
- **The gitignored-settings.json trigger wrinkle** (SCP-R-030 can't read `.claude/settings.json` from the checked-out tree) is SCP's to solve at Phase B — likely a committed `.scp/rule-config.yaml` `acc-hook-installed: true` opt-in. ACC option (b) — dropping a tracked `.acc/hook-installed` marker in the install ceremony — would be a cleaner cross-repo trigger; mention it to ACC if they're amenable, but it's not blocking.
- **SCP-self CLAUDE.md is already the reference** — ACC can copy its shape.
