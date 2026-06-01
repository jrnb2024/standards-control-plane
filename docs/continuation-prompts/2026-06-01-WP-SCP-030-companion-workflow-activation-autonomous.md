# Autonomous-run prompt — WP-SCP-030 companion-workflow activation (SCP-R-030 dormant → FIRING)

**Drafted:** 2026-06-01 (after #196 shipped SCP-R-030 dormant + #198 scoped this build).
**SPEC anchor (read FIRST, it is authoritative):** `docs/plans/WP-SCP-030-companion-workflow-activation-scope.md`.
**Strategic anchor:** `docs/decisions/D-058-scp-canonical-conformance-strategy-2026-05-29.md`.
**Session character:** Single autonomous run via **Pattern 3** (D-057). **⚠️ KERNEL-DANGEROUS** — this modifies `policy-check.yml`, the estate merge-gate workflow. **NO HOLD-FOR-OPERATOR gates within the run.** Operator-attended controls are pre-flight (dispatch bootstrap) + post-run (v1.4.0 cut + B.2 cascade).

## Operator-ratified decisions (2026-06-01 — do NOT re-litigate)

1. **Architecture = Option A** — a dedicated, **additive** `opa eval` repo-level pass. **Do NOT use conftest `--combine`** (it changes `input` shape for every rule; rejected for blast radius). Do NOT modify the existing conftest per-file pass.
2. **Scope = SCP-R-030 ONLY.** Materialize ONLY SCP-R-030's three inputs. **Leave SCP-R-006 dormant** — do NOT materialize its extra inputs (`changed_files`/`services_yml`/`estate_repos_yaml`/…). SCP-R-006 is the deliberate "next consumer," not part of this PR.
3. **Ship as an ACTIVE rule.** No version bump in this PR (v1.4.0 is already in `version-manifest.json` from #196). The §6 handoff cuts **v1.4.0 AFTER this PR merges**, so the release tag ships an active rule.
4. **Vehicle = full D-057 canonical dispatcher process** (this prompt). No shortcuts.

---

## §0 Operator-attended pre-launch (THE ONLY MANUAL STEP)

### 0.1 Verify prereqs (normal terminal)
```bash
cd ~/Projects/standards-control-plane
git fetch origin main && git log --oneline origin/main -3
git show origin/main:policies/SCP-R-030.rego >/dev/null 2>&1 && echo "✅ SCP-R-030 on main (dormant)" || echo "HALT: SCP-R-030 not on main"
grep -c 'SCP-R-030' .github/workflows/policy-check.yml   # expect 0 → confirms still dormant (companion not yet done)
python3 -c "import json,pathlib; d=json.loads(pathlib.Path('.claude/settings.json').read_text()); print('hook:', list(d.get('hooks',{}).keys()))"  # expect PreToolUse
```
If SCP-R-030 already appears in `policy-check.yml`, this build already ran — STOP.

### 0.2 Bootstrap the session dispatch (D-057)
```bash
cd ~/Projects/standards-control-plane
scripts/operator/scp-pattern3-dispatch.sh \
    ".github/workflows/policy-check.yml" \
    ".github/workflows/workflow-selftest.yml" \
    "lib/policy_check_invocation.sh" \
    "tests/workflow/**" \
    "policies/SCP-R-030.rego" \
    "STATUS.md" \
    "docs/reviews/WP-SCP-030/**"
```
(If the hook denies a path NOT in this list mid-run, HALT and ask the operator to re-bootstrap with it added — **never** disable the hook, D-057.)

### 0.3 Launch
Open a fresh Claude Code session rooted at `~/Projects/standards-control-plane`. Paste:
```
Read and execute docs/continuation-prompts/2026-06-01-WP-SCP-030-companion-workflow-activation-autonomous.md
```

### 0.4 Teardown (end-of-run)
```bash
cd ~/Projects/standards-control-plane && scripts/operator/scp-pattern3-dispatch.sh --teardown
```

---

## §1 Phase 0 — in-session pre-flight (deterministic; HALT cleanly on failure)

### 1.1 Hook + dispatch
```bash
test -f .acc/active-dispatch.json && python3 -c "import json;d=json.load(open('.acc/active-dispatch.json'));assert '**' not in d['scope_boundary'];assert '.acc/active-dispatch.json' not in d['scope_boundary'];print('dispatch:',d['dispatch_id'],len(d['scope_boundary']),'paths')"
test -f .claude/settings.json && python3 -c "import json;assert 'PreToolUse' in json.load(open('.claude/settings.json')).get('hooks',{});print('hook live')"
```

### 1.2 Re-read the load-bearing context (confirm; do NOT re-author)
- **`docs/plans/WP-SCP-030-companion-workflow-activation-scope.md`** — your binding spec (architecture, exact edit sites, coupling guard, fixture matrix).
- `policies/SCP-R-030.rego` (lines ~55–82) — the exact `input.*` contract you must materialize: `input.rule_config` (opt-in `acc-hook-installed`), `input.claude_md_present` (bool), `input.claude_md` (string). NOTE: SCP-R-030 also reads `data.rule_config.rules["SCP-R-030"].disable` via `scp_common.rego` — that path is ALREADY materialized (`--data`); do not break it.
- `.github/workflows/policy-check.yml` — conftest per-file eval; the two `WARN_BASELINE_RULES` sites (L1139 render-deny, L1493 scorecard — the only two); the findings stream those steps consume; the ~L876 insertion point.
- `lib/policy_check_invocation.sh:246` (conftest invocation) + `:280–313` (the YAML→JSON `data.rule_config` wrap precedent — you mirror its parse, but place output at `input.rule_config`).
- `.github/workflows/workflow-selftest.yml` + `tests/workflow/fixture-pass` / `fixture-fail` — the fixture pattern you mirror.

---

## §2 Phase 1 — Build (Option A) per SPEC §3 + §4

### 2.1 Repo-level materialization + `opa eval` step (additive)
Add a new step to `policy-check.yml` (around the SPEC's L876 insertion point) that:
- reads adopter root `CLAUDE.md` → `claude_md_present` (bool), `claude_md` (string; `""` if absent or non-string);
- parses `.scp/rule-config.yaml` → `rule_config` (object; `{}` if absent) — mirror the `lib/...:280–313` parse;
- writes ONE envelope JSON `{"rule_config": …, "claude_md_present": …, "claude_md": …}`;
- runs `opa eval` against `policies/` for the repo-level rule's findings (deny + warn), emitting the canonical `SCPFinding` shape (`rule_id`/`severity`/`message`/`file`/`line`);
- **merges** those findings into the same findings JSON the render-deny (L1139) + scorecard (L1493) steps consume.
- **Additive only** — the conftest per-file pass (SCP-R-001…008) is untouched. Verify zero regression.

### 2.2 `WARN_BASELINE_RULES` — both sites
Add `"SCP-R-030"` at **L1139** AND **L1493** (`{"SCP-R-004","SCP-R-008"}` → `{…,"SCP-R-030"}`). These are the only two; confirm by grep after editing.

### 2.3 ⚠️ Coupling guard (SPEC §4.1 — non-negotiable)
2.1 + 2.2 land in THIS PR together. Prove it with the fixture in §3: an opted-in adopter with a **missing marker** must produce a `::warning::` with the **gate GREEN**, never a blocking deny. If you can only land one half, HALT — do not ship materialization without the baseline membership.

### 2.4 SCP-R-030 only
Do NOT materialize SCP-R-006's inputs. SCP-R-006 stays vacuous. (Decision 2.)

---

## §3 Phase 2 — Workflow selftest fixtures
New `tests/workflow/fixture-scp-r-030-*` dirs (mirror `fixture-pass`/`fixture-fail`), wired into `workflow-selftest.yml`. Matrix (SPEC §6):

| Fixture | `.scp/rule-config.yaml` | root `CLAUDE.md` | Expected |
|---|---|---|---|
| opted-in, full preamble | `acc-hook-installed: true` | marker in top-3 lines | **PASS** (no finding) |
| **opted-in, marker absent** | `acc-hook-installed: true` | no marker | **`::warning::`, gate GREEN** ← load-bearing |
| opted-in, CLAUDE.md absent | `acc-hook-installed: true` | (none) | `::warning::`, gate green |
| not opted-in | (key absent) | anything | vacuous-pass |
| opted-in but disabled | `acc-hook-installed: true` + `rules.SCP-R-030.disable: true` (+justification +expires_at) | no marker | vacuous-pass |
| regression | n/a | n/a | SCP-R-001…008 per-file outcomes unchanged |

---

## §4 R1 — 3-lens review (MANDATORY; kernel-dangerous merge-gate)
Dispatch 3 parallel lenses:
- **correctness**: does the `opa eval` envelope match SCP-R-030's `input.*` contract? Does findings-merge feed L1139/L1493 correctly? Per-file pass untouched?
- **safety_bypass**: can the new step be evaded, or can it alter the gate verdict for OTHER rules? Is the coupling guard airtight (no path where an opted-in missing-marker blocks a merge)? Does `data.rule_config` (disable) still work?
- **completeness_governance**: fixture coverage incl. the load-bearing warn-not-block case + regression; SCP-R-006 confirmed still dormant; no silent scope creep beyond decisions 1–4.

**A safety_bypass REJECT on this merge-gate change is a HARD STOP.** Cure-worse R2 in effect. Dispositions → `docs/reviews/WP-SCP-030/companion-r1-dispositions.md`. Fold to R-FIXPOINT before Phase 3.

---

## §5 Phase 3 — Bookkeeping
- **STATUS.md** chain row (triggers `check-invocation-log-entry`): companion SHIPPED, SCP-R-030 now FIRING (warn-baseline), B.2 ready, v1.4.0 ready-to-cut-as-active.
- **`docs/BACKLOG.md`**: WP-SCP-030 companion → SHIPPED; B.2 cohort opt-in {CT, PIM} ready; D-060 still reserved.
- **NO version bump** (v1.4.0 already in `version-manifest.json`).
- Carry the **measurement-blind-spot caveat** (from the B.1 r1-dispositions: whole-file element greps under-count drift) forward into the companion dispositions so D-060 reads it.

---

## §6 Phase 4 — Operator handoff (halt with this exact message)
```
WP-SCP-030 companion-workflow activation complete — SCP-R-030 is now FIRING (warn-baseline).

Operator-attended next steps:
1. CUT v1.4.0 (rule is now ACTIVE — decision 3):
   scripts/operator/cut-release.sh --version v1.4.0 --sha <MERGE_SHA>
2. B.2 COHORT OPT-IN ({CT, PIM} only; both already carry the marker on main):
   - add `acc-hook-installed: true` to CT  .scp/rule-config.yaml
   - add `acc-hook-installed: true` to PIM .scp/rule-config.yaml
   - SCP-self: dogfood is the PASS fixture (.scp/ gitignored); mapp-doc-agent: NOT hooked, do not opt in.
   - then: scripts/operator/scp-wrapper-bump-sweep.sh --emit-commands
3. OBSERVE 4 weeks after CT+PIM opt-in. ⚠️ D-060 caveat: whole-file element greps under-count drift —
   do NOT read a low element_missing count as "preambles healthy" (see companion r1-dispositions).
4. RATIFY D-060: deny-promote / hold-at-warn / re-scope.
5. TEARDOWN: scripts/operator/scp-pattern3-dispatch.sh --teardown

Files shipped: .github/workflows/policy-check.yml (Option-A repo-level eval step + both WARN_BASELINE_RULES sites)
  · .github/workflows/workflow-selftest.yml + tests/workflow/fixture-scp-r-030-* · STATUS.md · docs/BACKLOG.md
  · docs/reviews/WP-SCP-030/companion-r1-dispositions.md

3-lens R1: ACCEPT (R-FIXPOINT; no safety REJECT). Halts encountered: <list / none>.
```

---

## §7 Halting conditions
1. Pre-flight miss (SCP-R-030 not on main / already wired / hook or dispatch bad).
2. **safety_bypass REJECT** on the merge-gate change (hard stop).
3. **Cure-worse R2** trigger.
4. **Coupling cannot be satisfied** — if you cannot land materialization + both baseline edits together, HALT (never ship the deny-blocking half alone).
5. **Option A infeasible as specified** — if repo-level `input.*` cannot be materialized additively without touching the conftest per-file pass, HALT + surface to operator. Do NOT fall back to `--combine` (decision 1).
6. Selftest fixtures fail and fix-round-1 doesn't close it (signals the eval-path is wrong).
7. Context-budget split (>6h) — carry-forward continuation prompt.

## §8 Success criteria
- `policy-check.yml`: additive Option-A repo-level eval step; SCP-R-030 in BOTH `WARN_BASELINE_RULES` sites; conftest per-file pass unchanged.
- `workflow-selftest.yml` + `tests/workflow/fixture-scp-r-030-*`: all green, incl. **opted-in-missing-marker → WARN, gate GREEN**.
- 3-lens R1 ACCEPT (R-FIXPOINT; no safety REJECT; no cure-worse).
- STATUS chain row + BACKLOG flip; no version bump.
- CI green (policy-check / scp/policy-check + check-invocation-log-entry + workflow-selftest orchestrator).
- §6 handoff issued + teardown reminder.

## §9 Notes
- **Option A rationale:** additive repo-level pass = zero regression to the per-file rules; `--combine` rejected (decision 1).
- **SCP-R-006 stays dormant** (decision 2) — it is the next consumer of this same substrate.
- **WP-SCP-028 convergence:** the repo-level eval path you build here is the reusable substrate the auth domain's activation will extend. Build it clean.
- If hook denials occur: verify path in `scope_boundary`; verify TTL <4h; NEVER disable (D-057) — HALT + ask operator to re-bootstrap.

---

**Fires when:** operator runs §0 (dispatch bootstrap) + launches a session in `~/Projects/standards-control-plane`.
**Closes when:** §6 handoff issued + operator runs §0.4 teardown. Domain fully closes at D-060 post-observation.
