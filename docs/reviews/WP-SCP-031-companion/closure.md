# WP-SCP-031 B.2 — companion workflow-activation closure (SCP-R-031 dormant → firing)

**Programme:** PLAN-CT-ESTATE-CONTEXT-001 · Phase 0-D · **Repository:** standards-control-plane
**Branch:** `feat/scp-r-031-companion-materialization` (off `origin/main` `e96b4f3`)
**Companion to:** WP-ESC-012b rule PR (#258, `policies/SCP-R-031.rego` merged dormant/warn-only) — see `docs/reviews/WP-ESC-031/closure.md`.
**Plan:** `docs/plans/WP-SCP-031-estate-context-marker-linkage-v1.md` §5.2 (items 1–3 = this PR; item 4 reserved).
**Precedent mirrored:** WP-SCP-030 companion (`docs/plans/WP-SCP-030-companion-workflow-activation-scope.md`) — Option-A repo-level `opa eval` pass.

## What this delivers

Makes the already-merged advisory rule **SCP-R-031** actually **EVALUATE** at adopter merge gates as a **warn-baseline** rule, without promoting it to enforcing. When an opted-in adopter (`.scp/rule-config.yaml estate-context-marker: true`) is missing the canonical Estate-context bootstrap marker on EITHER `CLAUDE.md` or `AGENTS.md` (or leaks dynamic Estate state in the top-of-file block), the gate emits a `::warning::` and **stays green** — never a deny. The rule was loaded + in both `WARN_BASELINE_RULES` sites since v2.2.0 but ran DORMANT/vacuous in production because the per-file conftest envelope never carried its repo-level inputs; this companion materialises those inputs.

## Exact edits (scope-bounded to the 6 named files)

### 1. `.github/workflows/policy-check.yml` — materialisation + eval set (the firing step)
- **Materialised `input.agents_md{,_present}`** in the repo-level Option-A `opa eval` step, mirroring the existing `input.claude_md{,_present}` lines byte-for-byte in shape: reads the evaluated repo root `AGENTS.md` (`agents_md_present = agents_md_file.is_file()`; present-but-unreadable → content `""` keeps the rule total, presence stays true), and added `agents_md`/`agents_md_present` to the `envelope` dict. `input.rule_config` (the shared opt-in surface — SCP-R-031 reads `estate-context-marker` from it) was already materialised for SCP-R-030; no change needed there.
- **`REPO_LEVEL_RULES = {"SCP-R-030"}` → `{"SCP-R-030", "SCP-R-031"}`** — this is what makes SCP-R-031 evaluate at repo level. The `opa eval` command already loads each rule in `REPO_LEVEL_RULES` (`--data policies/<rid>.rego`), so SCP-R-031.rego is now loaded + evaluated + its findings merged into `output/findings/policy-findings.json`.
- Step name + two comments updated for accuracy (envelope shape, added rule). **No logic change to any `.rego` file.**

### 2. `schemas/rule-config.schema.json` — opt-in key
- Added `"estate-context-marker": {"type": "boolean", ...}` alongside `acc-hook-installed`, under the top-level `additionalProperties: false`. An adopter's `.scp/rule-config.yaml estate-context-marker: true` now validates instead of being rejected by SCP-E007. Additive optional field (MINOR-safe).

### 3. `.github/workflows/workflow-selftest.yml` — 5 fixtures wired
- Added the 5 `fixture-scp-r-031-*` reusable-workflow invocations (`marker-present-both`, `marker-absent-claude`, `marker-absent-agents`, `dynamic-state-present`, `disabled`) + their `stash-*-summary` jobs, spliced into the linear green fixture chain between the SCP-R-013 tail and `fixture-fail-policy-check` (re-pointed `fixture-fail`'s `needs` to the new tail `stash-fixture-scp-r-031-disabled-summary`, preserving the single-`policy-check-summary`-artifact invariant).
- Added to the `workflow-selftest` aggregator: 10 `needs:` entries, 5 artifact-download steps, 5 oracle comparison `cases`, and a **`WP-SCP-031 §5.1 coupling guard`** assert step (all 5 fixture jobs must result in `success`).
- `validate-selftest-config` local-uses invocation count bumped `19 → 24` (+ error-message enumeration updated).

### 4. `version-manifest.json` — `2.2.0 → 2.3.0`
- Additive MINOR (new optional schema field + firing a previously-dormant warn-baseline rule; no rule-ID surface change), per `policies/VERSIONING.md`. `version` + `minor` + `released_at` bumped together; `_comment` gained the v2.3.0 sentence.

### 5. `docs/plans/WP-SCP-031-...-v1.md`
- §5 phase-table row **B.2 → DONE**; §5.2 items 1–3 marked DONE; item 4 (consume CT `marker.json` `dynamic_state_detectors`) explicitly kept RESERVED as a pre-deny-promotion obligation, not part of this warn-only companion.

## Verification evidence (all GREEN)

| Gate | Result |
|---|---|
| `opa test policies/SCP-R-031.rego policies/scp_common.rego policies/tests/scp_r_031_test.rego -v` | **PASS 15/15** |
| `opa fmt --diff policies/SCP-R-031.rego` | clean (rule unchanged) |
| `scripts/scp-pre-push-verify.sh` | **all 3 SCP-R gates pass** (aggregate coverage 98.26% ≥ 90) |
| `policy-check.yml` + `workflow-selftest.yml` YAML parse | valid |
| `schemas/rule-config.schema.json` + `version-manifest.json` JSON parse | valid |
| selftest local-uses invocation count (validator regex) | 24 (matches the bumped guard) |
| **End-to-end materialisation simulation** (replicated the workflow's exact envelope build + `opa eval data.main.deny` + filter/merge, per fixture) | **ALL 5 MATCH** their `expected-annotations.json` findings |

Materialisation simulation detail (exercises the real materialisation + rule + suppression together, not vocabulary-matching):
- `marker-present-both` → 0 findings (both surfaces marked) ✓
- `marker-absent-claude` → 1 `marker_absent` naming **CLAUDE.md** ✓
- `marker-absent-agents` → 1 `marker_absent` naming **AGENTS.md** (the load-bearing second-file teeth over SCP-R-030) ✓
- `dynamic-state-present` → 1 `dynamic_state` naming **AGENTS.md** ✓
- `disabled` → 0 findings (rule-config disable suppresses inside `data.main.deny`) ✓

## Advisory-safety invariant (holds)

SCP-R-031 stays **ADVISORY**. It is in **both** `WARN_BASELINE_RULES` sites (unchanged by this PR) and is present in **no** deny/blocking/conflict-gate set — added ONLY to `REPO_LEVEL_RULES` (the eval set). Therefore an adopter that opted in (`estate-context-marker: true`) but is missing the marker gets a **WARN finding, gate green — never a CI-failing deny**. The `marker-absent-*` / `dynamic-state-present` fixtures carry deny-class findings that render `::warning::`; the coupling-guard assert (`result == success` for all 5, threshold: deny) is the executable proof. The 5 programme repos already carry the marker on both surfaces, so they PASS. **Deny-promotion is a separate later operator decision (WP-SCP-031 B.3 / §5.2 item 4), not this PR.**

## Scope cleanliness

`git diff --stat` touches only the 6 named files; **`policies/**` is untouched** — SCP-R-030, `scp_common.rego`, and every other rule are byte-identical. No stubs; the materialisation reads real adopter files and the rule fires on real content.

## Exit state

SCP-R-031 fires warn-baseline in production; advisory-contained; vacuous-safe when not opted in or inputs absent; single-source-of-truth for dynamic-state detection preserved (interim heuristic retained pending item 4 at deny-promotion). Ready for orchestrator 3-lens R1 review + commit.
