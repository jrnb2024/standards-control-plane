# Autonomous-run prompt — WP-SCP-030 SCP-R-030 (hooked-repo onboarding conformance) Phase B

**Drafted:** 2026-05-30 (the day ACC executed the WP-SCP-030 Phase-A.3 handoff — canonical preamble ratified + 6-repo propagation; ACC #342 / CT #468 / PIM #372 / SA #169 / RI Mapp-Labs#216 / SCP notify #194).
**Plan-doc anchor:** `docs/plans/WP-SCP-030-hooked-repo-onboarding-conformance-v1.md` (§4 rule design + §5 phasing + §6 success + **§9 amendment** — the 4→6 hooked-set drift-fold).
**Strategic anchor:** `docs/decisions/D-058-scp-canonical-conformance-strategy-2026-05-29.md`.
**Session character:** Single autonomous run via Pattern 3 (Claude Code autonomous session per D-057). **NO HOLD-FOR-OPERATOR gates within the run.** Operator-attended controls are pre-flight (dispatch bootstrap + publish-before-gate verification) and post-run (release cut + the **B.2 cohort cascade**, which is operator-attended by design).

> This is the **proving-ground domain** for the D-058 Phase A → Phase B canonical-conformance machinery (auth/WP-SCP-028 is the flagship, blocked on CT). It ships ONE warn-baseline rule. Scope is deliberately small.

---

## §0 Operator-attended pre-launch (THIS IS THE ONLY MANUAL STEP)

### 0.1 Verify the publish-before-gate prereq (ACC has published the canonical)

The D-058 discipline: **SCP gates conformance only after the authority publishes the canonical.** The authority is ACC; the canonical is its ratified onboarding-preamble contract + the marker string. Run from a normal terminal:

```bash
cd ~/Projects/standards-control-plane
git fetch origin main && git log --oneline origin/main -3

# HARD PREREQ: ACC's canonical preamble guide is published on ACC main,
# and carries the ratified marker verbatim. (ACC #342 must be MERGED.)
gh api repos/jrnb2024/ACC/contents/docs/guides/hooked-repo-onboarding-preamble.md \
  --jq '.content' | base64 -d | grep -q 'canonical:acc-hook-onboarding v1' \
  && echo "ACC CANONICAL PUBLISHED" \
  || { echo "HALT: ACC #342 not merged / marker absent — publish-before-gate not satisfied"; }

# SCP-self already carries the marker (PR #192, on main) — the dogfood reference.
grep -q 'canonical:acc-hook-onboarding v1' CLAUDE.md \
  && echo "SCP-self marker present" || echo "HALT: SCP-self CLAUDE.md lost the marker"

# acc-hook live (D-057 cardinal pre-flight)
python3 -c "import json,pathlib; d=json.loads(pathlib.Path('.claude/settings.json').read_text()); print('hooks:', list(d.get('hooks',{}).keys()))"
# Expect: hooks: ['PreToolUse']
```

If the ACC-canonical check HALTs: stop. Do not launch. ACC #342 must merge first (it is the authority source the propagation PRs reference). **The marker string is ratified verbatim: `<!-- canonical:acc-hook-onboarding v1 -->` — SCP-R-030 greps for exactly this.**

> The propagation PRs into CT/PIM/SA/RI (#468/#372/#169/#216) gate **B.2** (each adopter's opt-in), NOT this run (B.1 = rule + SCP-self opt-in). They do not need to be merged to launch — but see §6 for the post-run cascade ordering (an adopter opts in only after its CLAUDE.md carries the marker on main, so the rule never warns falsely).

### 0.2 Bootstrap the session-start dispatch (D-057)

From the same terminal:

```bash
cd ~/Projects/standards-control-plane
scripts/operator/scp-pattern3-dispatch.sh \
    "policies/SCP-R-030.rego" \
    "policies/scp_common.rego" \
    "schemas/rule-config.schema.json" \
    "tests/policies/test_SCP-R-030*" \
    "tests/policies/fixtures/SCP-R-030/**" \
    "tests/conflict_gate/fixtures/SCP-R-030/**" \
    "policies/VERSIONING.md" \
    "policies/rule-config.yaml" \
    ".scp/rule-config.yaml" \
    "version-manifest.json" \
    "STATUS.md" \
    "docs/reviews/WP-SCP-030/**"
```

**Critical (D-057 §4 self-escalation guard):** none of these paths covers `.acc/active-dispatch.json`. The script refuses blanket globs.

### 0.3 Launch the autonomous Claude Code session

Open a fresh Claude Code session in `~/Projects/standards-control-plane` (project root = SCP repo; hook live + gating to declared scope). Paste:

```
Read and execute docs/continuation-prompts/2026-05-30-WP-SCP-030-SCP-R-030-phase-b-autonomous.md
```

### 0.4 Teardown (end-of-run)

```bash
cd ~/Projects/standards-control-plane
scripts/operator/scp-pattern3-dispatch.sh --teardown
```

Mandatory final D-057 step. The autonomous session reminds the operator in its close-out.

---

## §1 Autonomous session — Phase 0 pre-flight (deterministic)

Run at start. **HALT cleanly** (operator-action message) if any fail.

### 1.1 Verify hook + dispatch state

```bash
test -f .claude/settings.json && python3 -c "
import json
d=json.load(open('.claude/settings.json'))
assert 'PreToolUse' in d.get('hooks',{}), 'acc-hook NOT live'
print('hook: live')
"
test -f .acc/active-dispatch.json && python3 -c "
import json
d=json.load(open('.acc/active-dispatch.json'))
assert 'scope_boundary' in d and '**' not in d['scope_boundary']
assert '.acc/active-dispatch.json' not in d['scope_boundary']
print('dispatch:', d['dispatch_id'], 'scope entries:', len(d['scope_boundary']))
"
```

HALT if either fails.

### 1.2 Re-verify the ACC canonical is published (defense-in-depth vs §0.1)

```bash
curl -sL "https://raw.githubusercontent.com/jrnb2024/ACC/main/docs/guides/hooked-repo-onboarding-preamble.md" -o /tmp/acc-preamble.md
grep -q 'canonical:acc-hook-onboarding v1' /tmp/acc-preamble.md \
  || { echo "HALT: ACC canonical not on main (publish-before-gate)"; exit 1; }
grep -q 'canonical:acc-hook-onboarding v1' CLAUDE.md \
  || { echo "HALT: SCP-self lost the marker"; exit 1; }
```

> LINKAGE-not-VALUES: you are confirming the canonical *exists + is published*, NOT re-authoring it. ACC owns the contract; SCP gates conformance to it.

### 1.3 Re-read load-bearing context (confirm understanding; do NOT re-author)

- `docs/plans/WP-SCP-030-hooked-repo-onboarding-conformance-v1.md` — binding plan; **§4 (rule design + the gitignored-trigger wrinkle)** + **§9 (the 4→6 hooked-set drift amendment + reach nuance)**.
- `docs/decisions/D-058-scp-canonical-conformance-strategy-2026-05-29.md` — LINKAGE-not-VALUES; enforcement-plane-not-control-plane; publish-before-gate.
- `docs/decisions/D-057-scp-self-orchestrate-pattern-2026-05-29.md` — never-disable; this run's ceremony.
- `/tmp/acc-preamble.md` (fetched §1.2) — ACC's canonical contract: the 5 required preamble elements you gate LINKAGE on.
- `CLAUDE.md` (SCP-self) — the reference instantiation + dogfood; your PASS fixture mirrors it.
- `policies/SCP-R-006.rego` + `policies/SCP-R-008.rego` — shape precedent (vacuous-pass guard, warn emission, `SCPFinding` shape).
- `policies/scp_common.rego` — shared helpers.
- `schemas/rule-config.schema.json` — extension target (the opt-in trigger); note `acc-cross-repo-caller-scoped` is the existing top-level-boolean opt-in precedent.
- `policies/VERSIONING.md` — `WARN_BASELINE_RULES` extension target.

---

## §2 Phase 1 — Schema extension (the opt-in trigger)

Per plan §4, the trigger is **option (a): committed rule-config opt-in** (`.scp/rule-config.yaml acc-hook-installed: true`). `.claude/settings.json` is gitignored estate-wide, so the rule cannot read the tree to know a repo is hooked → it needs a committed signal.

### 2.1 Extend `schemas/rule-config.schema.json`

Add ONE top-level boolean property, mirroring the existing `acc-cross-repo-caller-scoped` opt-in pattern exactly:

```jsonc
"acc-hook-installed": {
  "type": "boolean",
  "description": "Adopter opt-in to SCP-R-030 (hooked-repo onboarding conformance). Set true ONLY in a repo that runs the acc-hook AND whose CLAUDE.md carries the canonical onboarding preamble. Default false; rule vacuous-passes when absent or false. See docs/decisions/D-058-... + docs/plans/WP-SCP-030-...md."
}
```

- Do NOT add a bespoke disable key — reversibility uses the **existing generic** `rules.SCP-R-030.disable` (+ justification + expires_at) path already in the schema. (Plan §2.2.5: "flips to disabled via rule-config in <24h Renovate cycle.")
- `additionalProperties: false` is set at top level — adding the property is required for any opt-in config to validate.

### 2.2 R1 plan-stage review on the schema (3 lenses)

Dispatch 3 parallel review agents (Explore / general-purpose):
- **correctness**: does the property mirror the `acc-cross-repo-caller-scoped` precedent? Does `additionalProperties:false` still hold? Does an opted-in `.scp/rule-config.yaml` validate?
- **safety_bypass**: can a repo set `acc-hook-installed: true` AND `rules.SCP-R-030.disable: true` to silently dodge the gate? (Document the interaction — disable is auditable + expiring; that is the intended reversible path, not a bypass. Confirm the disable carries justification + expires_at.)
- **completeness_governance**: is the opt-in default-safe (absent ⇒ no fire)? Does it match plan §4's option-(a) recommendation?

Fold findings before Phase 2.

---

## §3 Phase 2 — Rule: `policies/SCP-R-030.rego`

Author per plan §4. **LINKAGE not VALUES** — the rule checks the *presence + shape of the canonical preamble*, never prescribes the repo's ceremony.

### 3.1 Rule logic

- **Vacuous-pass** (zero findings) when `.scp/rule-config.yaml` lacks `acc-hook-installed: true`. (A non-hooked repo, or one not opted in — harmless; it has no hook to onboard for. Same safe-failure pattern as SCP-R-006's opt-in.)
- **Vacuous-pass** when `rules.SCP-R-030.disable: true` (auditable reversible path).
- **When `acc-hook-installed: true` and not disabled:**
  - **warn** (deny post-D-060-promote) if `CLAUDE.md` is absent OR lacks the marker `<!-- canonical:acc-hook-onboarding v1 -->` (the LINKAGE target — exact substring).
  - **warn** if the marker is present but a required preamble element is missing — heuristic substring checks for the 3 cheap-to-detect elements (plan §3 + ACC's published contract):
    1. the always-allowed path list (substring `docs/**` near an "always-allowed" heading),
    2. a ceremony pointer (substring `dispatch` or `scripts/` ceremony reference),
    3. the never-disable rule (substring matching D-057 "do NOT disable" / "never disable").
- Emit the canonical `SCPFinding` shape (`rule_id`, `severity`, `message`, `file`, `line`) — copy the emission idiom from `SCP-R-008.rego`.
- Keep all element checks as **warn** at this stage (warn-baseline); only marker-absence is the deny-class condition reserved for post-D-060.

### 3.2 `policies/scp_common.rego` — extend only if needed

If a CLAUDE.md-load/grep helper is reused, add it here; keep it vacuous-safe (empty/null on missing file, never panic).

### 3.3 R1 plan-stage review on the rule (3 lenses; MANDATORY per cardinal rule)

Dispatch 3 parallel review agents:
- **correctness**: does the logic match plan §4? Are the vacuous-pass paths (not-opted-in, disabled) correct? Does marker-detection use the exact ratified string? Are element checks warn (not deny)?
- **safety_bypass**: can a repo carry a fake/renamed marker, a marker in a code-fence/comment that doesn't count, or strip the preamble while keeping the marker line? Can opt-in + element-omission slip through silently? Is the disable path auditable (justification + expires_at enforced by schema)?
- **completeness_governance**: edge cases — CLAUDE.md absent; marker present twice; marker with wrong version suffix (`v2`); multi-line preamble variants across the 6 hooked repos' different ceremonies (CT four-tier Codex vs SCP Pattern-3 — the rule must accept BOTH, since it gates LINKAGE not the specific ceremony).

**Cure-worse R2 trigger** in effect. A **REJECT on the safety_bypass lens HALTS** for operator (this is a conformance gate, not auth — but the cardinal 3-lens discipline still makes a REJECT a hard stop).

Fold findings + fix-rounds to R-FIXPOINT before Phase 3. File dispositions at `docs/reviews/WP-SCP-030/r1-dispositions.md`.

---

## §4 Phase 3 — Tests + fixtures

Fixture matrix for SCP-R-030 (mirror the `tests/conflict_gate/fixtures/SCP-R-001/rule-config-disabled/` layout for the disable case):

| Fixture | rule-config | CLAUDE.md | Expected |
|---|---|---|---|
| opted-in, full preamble (mirrors SCP-self) | `acc-hook-installed: true` | marker + all 3 elements | PASS (no findings) |
| opted-in, marker absent | `acc-hook-installed: true` | no marker | warn (`marker_absent`) |
| opted-in, CLAUDE.md absent | `acc-hook-installed: true` | (file missing) | warn (`claude_md_absent`) |
| opted-in, marker but no always-allowed list | `acc-hook-installed: true` | marker only | warn (`element_missing:always-allowed`) |
| opted-in, marker but no ceremony pointer | `acc-hook-installed: true` | marker, no ceremony | warn (`element_missing:ceremony`) |
| opted-in, marker but no never-disable rule | `acc-hook-installed: true` | marker, no never-disable | warn (`element_missing:never-disable`) |
| NOT opted-in | (no `acc-hook-installed`) | anything | vacuous-pass |
| opted-in but disabled | `acc-hook-installed: true` + `rules.SCP-R-030.disable: true` (+justification +expires_at) | no marker | vacuous-pass (auditable reversible) |
| CT-style ceremony variant | `acc-hook-installed: true` | marker + four-tier-Codex ceremony pointer | PASS (rule accepts non-SCP ceremony — LINKAGE not VALUES) |

### 4.1 Coverage + lint

```bash
opa test policies/ tests/policies/ --coverage --format=json | jq '.coverage.files'   # ≥90% on SCP-R-030.rego
regal lint policies/
opa fmt --diff policies/
```

Halt on any failure (coverage <90% AND fix-round-1 doesn't close it ⇒ rule-shape problem; halt).

---

## §5 Phase 4 — Bookkeeping

### 5.1 `policies/VERSIONING.md`
Add `SCP-R-030` to `WARN_BASELINE_RULES`. Add a doc block: SCP-R-030 = hooked-repo onboarding conformance; D-060 deny-promotion path; **enforcement reach = hooked ∩ SCP-cohort** (see §5.5 note).

### 5.2 `version-manifest.json`
Bump to **the next MINOR from whatever the file currently reads — do NOT hardcode.** (Additive-rule ⇒ MINOR per VERSIONING.md. WP-SCP-028 may have shipped v1.4.0 first; if so this is v1.5.0. Read the current value and increment the MINOR.)

### 5.3 `.scp/rule-config.yaml` (SCP-self opt-in — the dogfood)
Set `acc-hook-installed: true` for SCP-self. SCP-self's CLAUDE.md already carries the marker + all elements (PR #192), so SCP-self PASSES its own new rule — the dogfood. (If `.scp/rule-config.yaml` doesn't exist yet, create it with the `rules` block + this key, schema-valid.)

### 5.4 `docs/BACKLOG.md`
Flip WP-SCP-030 row: Phase B.1 SHIPPED; **B.2 cohort cascade = operator-attended, pending** (see §6). D-060 reserved (not consumed).

### 5.5 `STATUS.md` chain row (triggers `check-invocation-log-entry`)
Document: SCP-R-030 SHIPPED warn-baseline; next-MINOR ready-to-cut; B.2 cohort cascade pending; D-060 reserved. **Record the enforcement-reach nuance explicitly (no silent caps):** the hooked set is 6 repos (ACC/CT/PIM/SA/RI/SCP) but SCP-R-030 only *gates* repos that also run SCP's `policy-check` workflow — i.e. the cohort ∩ hooked = **{CT, PIM, SCP-self}**. ACC/SA/RI carry the Layer-1 marker but are not SCP cohort adopters, so Layer-2 does not reach them until they onboard (tracked as a forward item, not a blocker).

---

## §6 Phase 5 — Operator handoff

Halt with this exact operator-action message:

```
WP-SCP-030 SCP-R-030 (Phase B.1) autonomous run complete.

Operator-attended next steps:

1. CUT the release (next MINOR — confirm the number from version-manifest.json):
   scripts/operator/cut-release.sh --version vX.Y.0 --sha <MERGE_SHA>

2. B.2 COHORT CASCADE (operator-attended; ordering matters):
   For each SCP-cohort adopter that is ALSO hooked — currently {CT, PIM} —
   opt in ONLY AFTER that repo's WP-SCP-030 propagation PR has MERGED
   (so its CLAUDE.md carries the marker on main; otherwise the rule warns falsely):
     - CT  (#468 merged?)  -> add `acc-hook-installed: true` to CT  .scp/rule-config.yaml
     - PIM (#372 merged?)  -> add `acc-hook-installed: true` to PIM .scp/rule-config.yaml
   SCP-self already opted in this run (it carries the marker).
   mapp-doc-agent is an SCP cohort adopter but is NOT hooked -> do NOT opt it in.
   ACC / SA / RI are hooked + carry the marker but are NOT SCP cohort adopters ->
   Layer-2 cannot gate them yet (forward item; not a blocker).
   Then run the wrapper bump-sweep so adopters chase the new version tag, not HEAD:
     scripts/operator/scp-wrapper-bump-sweep.sh --emit-commands

3. OBSERVE 4 weeks after CT + PIM opt-in merges:
   - rule firing rate per adopter; false-positive count; real marker-drop catches.

4. RATIFY D-060 at observation close: deny-promote / hold-at-warn / re-scope.

5. TEARDOWN session dispatch (D-057):
   scripts/operator/scp-pattern3-dispatch.sh --teardown

Files shipped this run:
  - policies/SCP-R-030.rego
  - policies/scp_common.rego (extended, if needed)
  - schemas/rule-config.schema.json (acc-hook-installed opt-in added)
  - .scp/rule-config.yaml (SCP-self acc-hook-installed: true — dogfood)
  - tests/policies/test_SCP-R-030*.json + fixtures
  - policies/VERSIONING.md (WARN_BASELINE_RULES + reach note)
  - version-manifest.json (next MINOR)
  - docs/BACKLOG.md (Phase B.1 SHIPPED; B.2 pending)
  - docs/reviews/WP-SCP-030/r1-dispositions.md
  - STATUS.md (chain row + reach nuance)

3-lens R1 outcome: ACCEPT (R-FIXPOINT MET; no REJECTs, no cure-worse).
Halt conditions encountered: <list, or "none">.
```

---

## §7 Halting conditions (escalate cleanly to operator)

1. **Publish-before-gate miss** — ACC canonical not on ACC main / marker absent (§0.1 / §1.2), OR SCP-self lost its marker, OR hook not live, OR dispatch malformed/missing.
2. **safety_bypass REJECT** on the rule (cardinal 3-lens hard stop).
3. **Cure-worse R2 trigger** (a fix-round introducing a worse-than-original failure mode).
4. **Coverage <90%** on SCP-R-030 AND fix-round-1 doesn't close it (rule-shape problem).
5. **Context-budget split** (>6h elapsed; split after Phase 2 or Phase 3; carry-forward continuation prompt).

---

## §8 Success criteria

- `policies/SCP-R-030.rego` — warn-baseline; ≥90% opa coverage; regal lint + opa fmt clean.
- `schemas/rule-config.schema.json` extended with `acc-hook-installed` opt-in (mirrors `acc-cross-repo-caller-scoped`); `additionalProperties:false` preserved.
- `.scp/rule-config.yaml` opts SCP-self in → SCP-self PASSES its own rule (dogfood).
- Fixture matrix (§4) all green, incl. the CT-style-ceremony PASS (proves LINKAGE-not-VALUES) + the disabled-vacuous-pass case.
- `VERSIONING.md` WARN_BASELINE_RULES extended + reach note; `version-manifest.json` next-MINOR.
- `docs/BACKLOG.md` Phase B.1 → SHIPPED, B.2 pending; D-060 reserved (not consumed).
- `STATUS.md` chain row (triggers `check-invocation-log-entry`) carrying the enforcement-reach nuance.
- 3-lens R1 evidence at `docs/reviews/WP-SCP-030/r1-dispositions.md`.
- CI green on all required checks (policy-check / scp/policy-check + check-invocation-log-entry + r1-evidence-check).
- Operator-handoff message at close; teardown reminder issued.

---

## §9 Inheritance + relationship to WP-SCP-028

This is the **proving ground** (plan §7): it exercises the identical Phase A (authority publishes canonical) → Phase B (SCP gates conformance) machinery as the auth flagship, on a low-risk docs-domain. The two lessons it banks for WP-SCP-028 + every later Phase-C domain:
1. **the gitignored-trigger resolution** — option-(a) committed opt-in (`acc-hook-installed`) is the reusable pattern for "the signal SCP needs to know whether to fire lives in a gitignored file."
2. **enforcement-reach ≠ canonical-reach** — a canonical can be propagated estate-wide (6 repos) while SCP's *gate* only reaches the cohort subset (3). State the gap; never imply full coverage.

If the autonomous session hits hook denials: verify the path is in `scope_boundary`; verify TTL fresh (<4h); NEVER disable the hook (D-057) — HALT + ask operator to re-bootstrap with extended scope.

---

**Identified at:** 2026-05-30 — ACC executed the Phase-A.3 handoff (canonical ratified + 6-repo propagation); WP-SCP-030 Layer-2 (B.1) unblocked.

**Filed:** 2026-05-30 (this prompt; concurrent with the plan §9 drift-fold).

**Fires when:** operator runs §0 pre-launch (ACC #342 merged) AND launches a Claude Code session in `~/Projects/standards-control-plane`.

**Closes when:** §6 operator-handoff message issued AND operator runs §0.4 teardown. Domain fully closes at D-060 (post-4-week observation).
