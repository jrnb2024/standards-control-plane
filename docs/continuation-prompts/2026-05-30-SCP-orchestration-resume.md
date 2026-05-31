# SCP orchestration session — clean restart prompt

**Drafted:** 2026-05-30 (end of the D-057 / D-058 / WP-SCP-028 / WP-SCP-030 session)
**Session character:** SCP coordination / orchestration session. Tracks the estate-wide canonical-conformance rollout; resumes per-domain build work when each domain's authority finishes its handoff.
**How to use:** paste the "DROP-IN" block below into a fresh Claude Code session, OR just point a session at this file. Everything it needs to reconstruct state cold is on-disk (this prompt tells it where).

---

## DROP-IN (paste this)

```
SCP orchestration session — resume. Read this file in full first:
standards-control-plane/docs/continuation-prompts/2026-05-30-SCP-orchestration-resume.md
Then run the PRE-FLIGHT, evaluate the TWO RESUME SIGNALS, and act per the DECISION TREE.
```

---

## Root context + hook discipline

This orchestration work runs cleanly from a session rooted at **`~/Projects`** (the parent dir) — SCP docs are then writable without tripping the acc-hook (the hook loads only when the SCP repo is the project root). If you end up **SCP-rooted** and need to write SCP **source** (`policies/**`, `scripts/**`, `schemas/**`, `tests/**`, `pyproject.toml`, root `STATUS.md`, `.claude/**`), use the **D-057 dispatch ceremony** (`scripts/operator/scp-pattern3-dispatch.sh "<paths>"` before the session; `--teardown` after). **Never disable the hook.** Docs (`docs/**`, `CLAUDE.md`, memory) are always-allowed either way.

## Pre-flight (verify LIVE state — do NOT trust any prior chat summary)

```bash
git -C ~/Projects/standards-control-plane fetch origin
git -C ~/Projects/standards-control-plane log --oneline origin/main -8
```

Then read, in order:
1. `standards-control-plane/STATUS.md` — top chain (most recent first)
2. `standards-control-plane/docs/decisions/D-058-scp-canonical-conformance-strategy-2026-05-29.md` — the strategic direction
3. `standards-control-plane/docs/plans/WP-SCP-028-auth-canonical-conformance-v1.md` — auth domain (first)
4. `standards-control-plane/docs/plans/WP-SCP-030-hooked-repo-onboarding-conformance-v1.md` — hooked-repo domain (proving ground)
5. SCP section of `~/.claude/projects/-Users-amplience-Projects/memory/MEMORY.md`

## Context (one paragraph)

D-058 (2026-05-29) ratified SCP's evolution from structural-hygiene linter to **canonical-architecture conformance oracle**, one domain at a time: SCP gates LINKAGE (does adopter code reference the canonical correctly?), never VALUES; **domain authorities author canonicals, SCP gates conformance** (enforcement-plane-not-control-plane); each domain needs a 4-artefact publish contract before SCP gates it. TWO domains are open, each **blocked on its authority finishing a handoff** — this is the publish-before-gate discipline working as designed, not stalling.

## The two resume signals + decision tree

### Domain 1 — AUTH (WP-SCP-028) — blocked on CT

**Signal:**
```bash
gh api repos/jrnb2024/control-tower/contents/contracts/auth-contract-v1.yaml \
  --jq '.content' | base64 -d | grep -q '^protected_primitives:' \
  && echo "CT AUTH READY" || echo "CT auth pending"
```

- **If READY** (and `auth-contract-v1.yaml.sig.bundle` cosign-verifies): the autonomous-run prompt is already written at `docs/continuation-prompts/2026-05-30-WP-SCP-028-auth-canonical-autonomous.md`. Run its **§0 ceremony** (operator bootstraps the session dispatch with the 16-path scope, then launches an SCP-rooted Claude Code session against it). It ships SCP-R-009/010/011 + tests + v1.4.0-cut handoff.
- **If pending:** CT hasn't executed its handoff (`docs/coordination/2026-05-30-WP-SCP-028-CT-prereqs-handoff-prompt.md`). Nothing buildable on the SCP side. Report + stand by.
- **Anchor note:** SCP verifies CT's canonical via the `.sig.bundle` (cosign), NOT the `manifest_sha256` field (a freshness hint that may drift). Do not gate on manifest_sha256 currency.

### Domain 2 — HOOKED-REPO ONBOARDING (WP-SCP-030) — blocked on ACC

**Signal:**
```bash
grep -q 'canonical:acc-hook-onboarding' ~/Projects/control-tower/CLAUDE.md \
  && echo "ACC PROPAGATED TO CT" || echo "ACC handoff pending"
ls ~/Projects/acc/docs/guides/hooked-repo-onboarding-preamble.md 2>/dev/null \
  && echo "ACC contract authored"
```

- **If ACC has ratified + propagated + confirmed the marker string:** write the **SCP-R-030 autonomous-run prompt** (Phase B per WP-SCP-030 plan-doc §4 + §6 — warn-baseline rule; trigger via committed `.scp/rule-config.yaml acc-hook-installed: true` opt-in since `.claude/settings.json` is gitignored; gate on the **ACC-confirmed marker string**; D-060 reserved), then launch it.
- **Do NOT author SCP-R-030 before ACC confirms the marker** — that's the premature work D-058's publish-before-gate order prevents.
- **If pending:** ACC hasn't executed its handoff (`docs/coordination/2026-05-30-WP-SCP-030-ACC-hooked-repo-preamble-handoff.md`). Report + stand by.

### If NEITHER signal is READY

Nothing buildable on the SCP side. Both handoff prompts are delivered (CT + ACC); the ball is in their courts. Report status + stand by, or pick up a standing item below.

## Standing / passive items (no action unless they move)

- **026F observation window** — open → 2026-06-23. Watch `~/Projects/ri-est-p-ws-2/.acc/dispatches/` (dir may not exist yet) for any `tool_scp_consult_rules` invocation. D-056 ratifies advance-to-WP-SCP-027 / hold / re-scope at close. Passive; no build.
- **shopify-app onboarding** — adopter #5 of 5; closes the WP-SCP-024 cohort cascade → FINAL-CLOSE. ~20-30 min operator-attended ceremony (App install + secrets + smoke + required-check flip). `FUP-WP-SCP-024-SHOPIFY-APP-ONBOARDING-001`.
- **Recommender 024E** — deferred on CT `ErrManifestStale` (CT-side workstream; not SCP-actionable).
- **SCP-wrapper bump-sweep** — `scripts/operator/scp-wrapper-bump-sweep.sh` (3 adopters drift from main HEAD after each SCP merge; operator-attended monthly; option-(c) per `FUP-WP-SCP-024-RENOVATE-MARKER-ESTATE-WIDE-001`). Note: the next SCP release tag should be cut before the next meaningful sweep so adopters chase a version, not HEAD.

## Discipline (estate-wide; non-negotiable)

- 3-lens adversarial review (correctness / safety_bypass / completeness_governance) on any rule, plan, or strategic decision. A REJECT on an auth-surface is a hard stop.
- NEVER commit directly to main — PR workflow, no exceptions.
- NEVER disable the acc-hook to get unblocked (D-057) — declare scope via dispatch.
- Stage explicitly (never `git add -A` / `commit -am` over a dirty tree — see the 2026-05-30 PIM bump near-miss); verify `git branch --show-current` + `git status --short` before commit.
- STATUS chain row on every PR (triggers `check-invocation-log-entry`); PR body carries a `## R1 evidence` block (3 plain `- lens:` lines, no bold).

## What shipped in the session that produced this prompt (2026-05-29 → 2026-05-30)

- **D-057** (PR #187) — Pattern 3 self-orchestrate + session-start dispatch ceremony; acc-hook RETAINED; v1 hook-removal REJECTED by safety lens.
- **Renovate option-c** (PR #188) + **sweep-script fixes** (PR #189) + 3 adopter wrapper bumps (PIM #363 / CT #456 / mapp-doc-agent #69) to `572f331`.
- **D-058** (PR #190) — canonical-conformance strategy; WP-SCP-028 + WP-SCP-029..036 roadmap.
- **WP-SCP-028 CT-handoff + .sig.bundle anchor correction** (PR #191).
- **WP-SCP-030 Phase A** (PR #192) — SCP-self CLAUDE.md (dogfood) + ACC handoff + plan-doc; the fix for "we hit the acc-hook every time."

---

**Closes when:** both domains advance through their authority handoffs and SCP ships SCP-R-009/010/011 (auth) + SCP-R-030 (hooked-repo), each through its 4-week observation to D-059 / D-060.
