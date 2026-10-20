# SCP reach work — clean-context continuation (2026-06-29)

This doc is the **self-contained continuation brief** for a fresh Claude Code session.
It carries the full output of the multi-agent SCP rule review so the next session needs
no prior context. Source of the review: 4 parallel Explore agents (enforcement-reality,
completeness, strategic-fit-vs-D-058, existing-rule soundness), all reconciled below.

---

## Verdict (why this work exists)

**The SCP's design is sound and D-058-faithful, but its *reach* is the bottleneck.**
It is a strong auth-conformance gate on 3 repos + an advisory library nobody is yet
forced to read. It is **not yet keeping the whole estate canonical**, and the unlock is
**reach (adoption + consult-consumption + Go coverage), not more rules**.

Hard numbers from the review:
| Dimension | Reality |
|---|---|
| Repo coverage | **3 of ~15** operational repos gated (mapp-pim, control-tower, mapp-doc-agent). |
| Blocking rules | **~4 of 12** actually block (R-001 auth-contract, R-002 waiver-schema, R-003 vendoring-manifest, R-012 migrations). 8 are warn-baseline. |
| Advisory tier | **22 of 23** standards have no enforcer; consult path has **zero documented consumers**. |
| Language | **Go is invisible** — ~387 Go files across CT+PIM match no rule globs. |

**Guardrails that bound this work (do not violate):**
- **D-058** — SCP gates **LINKAGE, never VALUES**; domain authorities author canonicals, SCP gates conformance. Author a rule only once a domain authority publishes the 4-artefact canonical (signed manifest + schema + registry + consult key).
- **D-049** anti-scope — no browser, no CSS parser, no token VALUES, no runtime, no semantic interpretation beyond signed-manifest verification.
- **GOV-004 / GOV-005 / SVC-004 stay ADVISORY consult standards.** They are orientation prose (process/stance), not mechanically auditable. **Do NOT promote them to enforced Rego** — that would violate D-049 (they describe control-plane behaviour, not LINKAGE) and be unfalsifiable.
- Most "missing rules" (tenancy, event-shape, secrets-beyond-`.env`) need a **domain authority to publish the canonical first**. Event-shape is the most-ready (the canonical already exists: `control-tower/.../SERVICES_YML_EVENT_CONTRACT.md` + validator + advisory ARCH-005) — but that's a later promotion, not part of this reach pass.

---

## Phase 0 — two verified quick fixes (do these FIRST, both gated paths)

Both defects were verified by direct inspection on 2026-06-29.

### Fix A — stale remediation-URL typo (BLOCKER: dead links)
`policies/SCP-R-001/002/003/004.rego` use `jrnb2024/standards-control-plane/blob/main/`
(**trailing dash** on the repo name) → 404s. Newer rules (SCP-R-006, R-012) use the
correct `jrnb2024/standards-control-plane/blob/main/`.

Exact edits (remove the trailing dash, `standards-control-plane-/` → `standards-control-plane/`):
- `policies/SCP-R-001.rego:8`
- `policies/SCP-R-002.rego:7`
- `policies/SCP-R-003.rego:8`
- `policies/SCP-R-004.rego:20`

### Fix B — ARCH-005 is a hidden rule (MAJOR)
`standards/architecture/rules/ARCH-005-event-stream-adoption.md` exists, `status: active`,
`severity high` — but is **NOT** in `standards/architecture/index.json` (which lists only
ARCH-001–004), so `consult_rules({domain:"architecture"})` never serves it.

Fix: add an ARCH-005 entry to the `rules` array in `standards/architecture/index.json`
(after ARCH-004), and bump the domain `version` 1.0.0 → 1.1.0. Pull `title`/`summary`/
`signals` from the `.md`. Entry must validate against `schemas/standards-rule.schema.json`
(`additionalProperties:false`; required: rule_id, domain, title, summary, path,
severity_default, scope, signals, version, status — **NO `applies_to` field**; applies_to
is derived in `resources.py`). Skeleton:
```json
{
  "rule_id": "ARCH-005",
  "domain": "architecture",
  "title": "Estate Services Must Use the Canonical Event Stream",
  "summary": "<from the .md>",
  "path": "rules/ARCH-005-event-stream-adoption.md",
  "severity_default": "high",
  "scope": ["backend"],
  "signals": ["<from the .md ## Signals>"],
  "exceptions": [],
  "related_patterns": ["action-service-pattern"],
  "version": "1.0.0",
  "status": "active"
}
```
Optional (only if trivial): add ARCH-005 event-stream globs to
`_FALLBACK_APPLIES_TO_BY_RULE_ID` in `resources.py` (e.g. `services.yml`, kafka/broker
config). Not required for Phase 0 — registration alone makes consult serve it.

**After Phase 0:** reconnect the scp-standards MCP server and verify
`consult_rules({domain:"architecture"})` now returns ARCH-005. (resources.py changes also
need an MCP restart to take effect — the server loads resources.py at startup.)

---

## The reach work — scope these three, plan + review, then build

The review's recommendation is **reach before rules**, in this priority order.

### REACH-1 — Adoption cascade (3/15 → estate)  [highest leverage]
**Problem:** every existing rule only applies to the 3 gated repos. Wiring `policy-check`
into the ungated ~12 makes *all* current rules apply everywhere — far higher ROI than any
new rule.
**Ungated repos** (confirm live list at session start): Recommender, acc, kg-studio, RI,
SA, estate-dashboard, market-feed/feedonomics, FLA, linkedin-content-os, amplience-kg-mvp,
ms-stl-demo/primark-stl-demo, visual-shopping.
**Procedure:** `docs/adoption/ADOPT-001-project-onboarding.md`. Each adopter also needs its
own acc-kernel install to be hook-governed (per GOV-004; hook-integrity is per-`--cwd`).
**Constraints:** per-repo PRs are **cross-repo + branch-protection = operator-attended**
(autonomous-directive boundary). Do these **sequentially, not batched** (multirepo-cleanup
rule). Deliverable: an onboarding helper script + a tracking checklist; do NOT bulk-open
15 PRs unattended.
**⚠ Fork isolation:** kg-studio is the *other fork's* active workspace. Do **not** touch
kg-studio, its worktrees, or its Codex dispatches. If kg-studio is in the adopt list,
flag it for the operator and skip — do not onboard it from this session.

### REACH-2 — Consult-consumption (zero consumers)
**Problem:** the 22 advisory standards (incl. GOV-004/005, SVC-004, ARCH-*) are dead
letters — nothing forces a session to read them.
**Step 1 (done):** the global `~/.claude/CLAUDE.md` consult-first block routes every
session to `resolve_domain → consult_rules → audit_changed`.
**To build:** (a) a per-repo CLAUDE.md consult line in each adopter; (b) a **SessionStart
hook** that surfaces `resolve_domain`/`consult_rules` automatically. Hooks are **owned by
ACC** (D-058 / WP-SCP-030 onboarding-block pattern) — coordinate with ACC; do not fork a
parallel hook mechanism. Deliverable: a SessionStart hook template + rollout plan.

### REACH-3 — Go coverage (~387 Go files invisible)
**Problem:** rule `applies_to` globs are `.py`/`.ts` only; CT + PIM are heavily Go, so
architecture/auth rules never fire on them.
**Caution:** many rules are *semantically* Python-specific — do NOT just bolt `.go` onto
their globs. Go needs its own signals. Likely shape: extend the **auth-contract** rules
(R-009/010/011) to recognise the Go auth-SDK linkage, + a new **Go-conventions advisory
standard**. Stay on D-058: gate **LINKAGE** (does Go code reference the canonical
auth/event SDK?), never values.

---

## Mechanics the fresh session needs

- **Pattern-3 dispatch (D-057):** before any source write (`policies/**`, `standards/**`,
  `scripts/**`, `src/**`, `tests/**`, `schemas/**`), the **operator** runs from a plain
  terminal: `scripts/operator/scp-pattern3-dispatch.sh "<path>" ["<path>" ...]`. The
  acc-hook blocks gated writes otherwise. **Never disable the hook.** Teardown at session
  end: `scripts/operator/scp-pattern3-dispatch.sh --teardown`.
- **Always-allowed (no dispatch):** `docs/**`, `CLAUDE.md`, `.acc/work-packages/**`, memory.
- **Merge:** PR workflow only, never direct to main. Non-WP governed change → 
  `scripts/operator/scp-gated-merge.sh <PR#>` (drops only `check-invocation-log-entry`,
  restores protection via trap, refuses unless `policy-check` is green). PR body MUST carry
  a `## R1 evidence` block (correctness / safety_bypass / completeness_governance).
- **🔑 Signing gotcha:** main enforces `required_signatures`. Commit with
  `-c user.email=james.brooke@mapp.com -S` or GitHub marks it Unverified and the merge
  blocks even after gated-merge.
- **MCP reflects committed state** for resources; consult_rules/resolve_domain read the
  working tree for data, but `resources.py` *code* loads at MCP-server startup → restart
  the MCP server after editing resources.py.
- **Build method (GOV-004):** four-tier dispatch — Opus orchestrates, Codex Tier-3 in an
  isolated worktree, 3× Sonnet parallel adversarial review, TDD operator-RED-test-first.
  **Plan-stage 3-agent review before exiting plan mode** (auth/governance surface default).

## Suggested first actions for the fresh session
1. Hard-sync: `git -C ~/Projects/standards-control-plane fetch && git reset --hard origin/main`; confirm branch/log.
2. Ask operator to run the Phase-0 dispatch (scope below), then land Phase 0 (one PR, gated-merge), verify ARCH-005 serves.
3. Produce a scoping plan for REACH-1/2/3, run the plan-stage 3-agent review, then ExitPlanMode for approval **before** building.

**Phase-0 dispatch scope (give to operator):**
```
scripts/operator/scp-pattern3-dispatch.sh \
  "policies/SCP-R-001.rego" "policies/SCP-R-002.rego" \
  "policies/SCP-R-003.rego" "policies/SCP-R-004.rego" \
  "standards/architecture/index.json"
```
