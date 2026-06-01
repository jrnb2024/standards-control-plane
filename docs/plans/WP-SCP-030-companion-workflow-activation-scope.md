# WP-SCP-030 — companion-workflow activation scope (SCP-R-030 dormant → firing)

**Status:** SCOPE (not yet built). Authored 2026-06-01 by the orchestration session after #196 (SCP-R-030 dormant on main) merged.
**Purpose:** specify the "companion workflow PR" that activates SCP-R-030 — the step every prior note deferred ("materialize inputs + add to `WARN_BASELINE_RULES`, same PR").
**Headline finding:** this is **kernel-dangerous workflow engineering, not a 2-line edit.** Read §2 before estimating.

---

## §1 Goal

Make SCP-R-030 actually fire at adopter merge gates as a **warn-baseline** rule: when an opted-in hooked adopter's `CLAUDE.md` lacks the canonical onboarding-preamble marker, emit a `::warning::` (never block) for the 4-week observation window → D-060.

Concretely the rule must stop vacuous-passing in production. It reads three **repo-level** inputs that do not exist in the current evaluation envelope:
- `input.rule_config` — the adopter's parsed `.scp/rule-config.yaml` (for the `acc-hook-installed` opt-in gate)
- `input.claude_md_present` — boolean (root `CLAUDE.md` exists)
- `input.claude_md` — string (root `CLAUDE.md` content)

(Verified against `policies/SCP-R-030.rego:55–82`.)

## §2 Why this is hard (the load-bearing finding — verified 2026-06-01)

The production gate evaluates via **conftest, per file** (`lib/policy_check_invocation.sh:246` → `conftest test --no-fail --output json --policy <dir>`; no `opa eval`, no `--combine`). Conftest merges **each file's own content** into `input`, and the caller's `.scp/rule-config.yaml` + waivers are injected as **`data.*`** via `--data` — **not** `input.*`.

So `input.rule_config` / `input.claude_md*` are **repo-level** fields that the per-file conftest model simply does not provide. This is the exact reason **SCP-R-006 has never fired either** — its own header (`policies/SCP-R-006.rego:17–24`) says input materialization "lands in a sibling Codex Tier 2 PR (kernel-dangerous). Until that sibling [lands]… `input.rule_config` will be absent under the per-file evaluation envelope… the rule vacuously passes." **That sibling PR was never built.** This companion PR is that same kernel-dangerous infrastructure, now driven by SCP-R-030.

**Implication:** the companion PR must introduce a way to evaluate repo-level (`input.*`) rules — a genuinely new evaluation path in the gate workflow, plus integration of its findings into the existing deny/scorecard aggregation. Treat as **Tier-2 / kernel-dangerous**, operator-attended, with a mandatory 3-lens R1.

## §3 Architecture decision (REQUIRED before build)

How to materialize repo-level `input.*` under a per-file conftest model. Three candidates:

| Option | Mechanism | Pro | Con |
|---|---|---|---|
| **(A) dedicated `opa eval` repo-level pass** *(recommended)* | A new workflow step builds ONE input JSON `{rule_config, claude_md_present, claude_md}` and runs `opa eval -i <envelope.json> -d policies/ 'data.<...>.deny'` for the repo-level rules only; merge its findings into the same findings stream the render/scorecard steps consume. | Clean isolation; does not touch the per-file conftest pass (zero regression surface for SCP-R-001…008); exactly the shape repo-level rules want | New eval path + findings-merge plumbing to author + test |
| **(B) conftest `--combine`** | Combine all files into one `input` array. | Reuses conftest | **Changes `input` shape for EVERY rule** — would break the per-file rules (input becomes an array of `{path,contents}`). High blast radius. Reject. |
| **(C) synthetic envelope "file"** | Write `.scp-eval-envelope.json` and pass it as one more conftest target so its contents land in `input`. | No new eval path | Conftest still evaluates it per-file (one input among many); the repo-level rule would fire once per file or need awkward filename guards; brittle. |

**Recommendation: (A).** Keep the conftest per-file pass exactly as-is; add a *separate, additive* `opa eval` step for repo-level rules. This bounds the blast radius to the new step + the findings-merge, and is reusable when SCP-R-006 (and future repo-level rules) are activated.

## §4 Exact edits (once Option A is ratified)

1. **NEW repo-level materialization + eval step** in `.github/workflows/policy-check.yml`, inserted after rule-config schema validation (~after line 876) and before/around the deny-render step. It must:
   - read the adopter root `CLAUDE.md` → `claude_md_present` (bool) + `claude_md` (string; `""` if absent/non-string);
   - parse `.scp/rule-config.yaml` → `rule_config` (object; `{}` if absent) — mirror the existing YAML→JSON wrap at `lib/policy_check_invocation.sh:280–313`, but place it at `input.rule_config` (not `data.rule_config`);
   - `opa eval` the repo-level rule set against this envelope, emit findings in the canonical `SCPFinding` shape (`rule_id`/`severity`/`message`/`file`/`line`);
   - **merge** those findings into the findings JSON consumed by the deny-render step (1139) + scorecard step (1493).
   - Keep `data.rule_config` (the disable path) intact — SCP-R-030 ALSO reads `data.rule_config.rules["SCP-R-030"].disable` via `scp_common.rego`; that path already works.
2. **`.github/workflows/policy-check.yml:1139`** — `WARN_BASELINE_RULES = {"SCP-R-004", "SCP-R-008"}` → add `"SCP-R-030"`. (Render-deny step: demotes its denies to `::warning::` + excludes from the merge-gate threshold.)
3. **`.github/workflows/policy-check.yml:1493`** — same literal, same edit. (Scorecard step: excludes baseline rules from the effective-deny count.)
   - These two are the **only** places the baseline set is enumerated (verified).

### ⚠️ §4.1 The non-negotiable coupling guard
Edits (1)+(2)+(3) **MUST land in the same PR.** If input materialization (1) ships without the `WARN_BASELINE_RULES` membership (2)+(3), an opted-in adopter with a missing marker would emit a **deny that BLOCKS the merge gate** instead of a warning — violating warn-baseline-first (§2.2.3) and breaking adopter merges. Materialization and membership are a single atomic change.

## §5 Scope decision: SCP-R-030 only, or also un-dormant SCP-R-006?

Option (A)'s repo-level eval path is general — it *could* also feed SCP-R-006's inputs (`input.changed_files`, `input.services_yml`, `input.estate_repos_yaml`, …) and un-dormant it. **Recommendation: build the path generally but materialize ONLY SCP-R-030's three inputs in this PR.** Do **not** materialize SCP-R-006's extra inputs here — that would silently activate SCP-R-006 (a behavior change with its own review surface). Keep SCP-R-006 vacuous; note it as the next consumer of the same infra. (Decision for the operator: confirm SCP-R-030-only.)

## §6 Test plan (workflow-level, via the selftest harness)

Fixtures proving activation + the warn-baseline guarantee (not just unit rego tests — those passed in #196):
- opted-in (`acc-hook-installed: true`) + `CLAUDE.md` w/ marker top-3 → **PASS** (no finding)
- opted-in + marker absent → **`::warning::`, gate stays GREEN** ← the load-bearing assertion (proves §4.1 coupling: warn, NOT deny-block)
- opted-in + `CLAUDE.md` absent → `::warning::`, gate green
- NOT opted-in → vacuous-pass (no finding)
- opted-in + `rules.SCP-R-030.disable: true` (+justification +expires_at) → vacuous-pass
- regression: SCP-R-001…008 per-file behavior unchanged (the new step is additive)

## §7 Build mechanics + review

- **Kernel-dangerous** (gates merges across the estate) → operator-attended dispatch (Pattern-3 SCP-rooted session OR Codex Tier-2), scope = `.github/workflows/policy-check.yml` + `lib/**` + selftest fixtures + `STATUS.md` + `docs/reviews/WP-SCP-030/**`.
- **Mandatory 3-lens R1** (correctness / safety_bypass / completeness_governance); a safety_bypass REJECT on a merge-gate change is a hard stop.
- **No version bump needed**: v1.4.0 (already on main, the rule) becomes meaningful once this wiring lands; cut the v1.4.0 release **after** this PR so the tag ships an active rule. (Alternatively keep the SCP-R-006-style "version-on-author" and cut v1.4.0 now with the rule dormant — operator's call; §8.)

## §8 Open decisions for the operator

1. **Architecture:** ratify Option (A) (dedicated `opa eval` repo-level pass)? (recommended)
2. **Scope:** SCP-R-030-only materialization, leaving SCP-R-006 dormant? (recommended)
3. **Release timing:** cut v1.4.0 *after* this companion PR (ships active rule) vs *now* (dormant, SCP-R-006 precedent)?
4. **Build vehicle:** Pattern-3 SCP-rooted autonomous session vs Codex Tier-2 dispatch?

## §9 Relationship to WP-SCP-028 (auth)

The auth domain (SCP-R-009/010/011) reads its canonical via a **signed manifest**, not `input.rule_config` — but it shares the same "rule authored dormant, activated by a companion materialization step" pattern (SCP-R-006 → SCP-R-030 → auth). **The repo-level eval path built here is the reusable substrate the auth activation will extend.** Building it cleanly for SCP-R-030 directly de-risks WP-SCP-028's eventual activation. This is the proving-ground value, realized.

---

**Closes when:** the companion PR ships (Option-A path + 2 baseline-set edits + selftest fixtures, all one PR, 3-lens R1 MET), CI green, and an opted-in missing-marker adopter is observed to **warn (gate green), not deny**.
