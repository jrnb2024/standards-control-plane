# RULE-002 — DPBM Phase-0 artefact presence on frontend-touching PRs

**Status:** DRAFT (operator-review surface; not yet UNDER REVIEW)
**Author:** @jrnb2024
**Filed:** 2026-05-19
**Target release:** v1.3.0 (SCP federation primitive).
**Type:** rule-add
**Quorum required:** 1 (single-operator mode per D-031)
**Review window:** 48h wall-clock from PR open.
**Bypass-surface non-empty:** `true` *(this rule introduces a new `.scp/rule-config.yaml` key `dpbm-scoped: <bool>` that adopters declare to opt into design-system enforcement. The `dpbm-scoped` key is a bypass surface — an adopter that sets it to `false` (the default) suppresses every design-system rule the federation primitive ships. Because the bypass-surface is non-empty, the 48h review window is **non-waivable** per `README.md` — author cannot extend or shorten; zero approvals at 48h auto-defers. Closes WP-SCP-022 020H.1 R2 SAFE-MIN-001 — the field is machine-readable so future tooling can act on it without re-parsing the proposal text.)*

---

## 1. Summary

Add **SCP-R-005** at `threshold: warn` baseline in v1.3.0. The rule fires on PRs that modify files matching the adopter's declared frontend path globs (default: `["frontend/**"]` — adopters override via `.scp/rule-config.yaml`) on an adopter that has declared `dpbm-scoped: true` in `.scp/rule-config.yaml`. When fired, the rule asserts that at least one of `docs/design/DESIGN_SPEC.md`, `docs/design/FLOW_SPEC.md`, or `docs/design/TOKENS.md` is present in the adopter's repo tree (NOT necessarily in the changed-files set — the Phase-0 oracle artefacts are expected to be persistent, not co-touched on every frontend PR).

Adopters opt out via `.scp/rule-config.yaml` `disable: true` with a justification + `expires_at`, identical to every other SCP-R-NNN rule. Adopters that do not declare `dpbm-scoped: true` vacuously pass the rule — the rule guards itself against firing on adopters that have not opted in.

This is the first design-system policy-layer rule, ratifying D-049 Element 1 (Phase-0 artefact-presence gating). It is deliberately the smallest viable rule: presence-only, persistent-artefacts-only, opt-in-per-adopter, warn-baseline. It does not check token values, does not check view coverage, does not check visual-test co-touch, does not load a browser. Those checks are separate rule proposals (deferred to subsequent RULE-NNN filings) following the rule-RFC process individually.

## 2. Motivation

### Real-world finding

The estate has adopted DPBM (Design Parity Build Method) as the canonical method for producing designed visual output — per `/Users/amplience/Projects/acc/docs/decisions/ADR-016-design-parity-build-method.md` (ACC, 2026-04-27) and `/Users/amplience/Projects/control-tower/docs/decisions/D-048-design-parity-build-method-adoption.md` (CT, 2026-04-27). DPBM Phase 0 is the design-lock prerequisite: an adopter producing designed visual output must have, before any build proceeds, structured artefacts at `docs/design/DESIGN_SPEC.md` (per-view structured spec), `docs/design/FLOW_SPEC.md` (machine-readable user flows), `docs/design/TOKENS.md` (canonical token set), and `docs/design/screenshots/` (pinned visual baselines).

Returns Intelligence (`/Users/amplience/Projects/mapp-returns-intelligence/docs/design/`) carries all four artefact classes and is the gold-standard implementation. The five WP-SCP-024 cohort adopters (PIM, control-tower, mapp-doc-agent, recommender, shopify-app) do not — none of them today have a Phase-0 design-lock corpus. As cohort adopters begin DPBM-scoped frontend work (estimated 2026-Q3 for recommender, post-WP-SCP-024 Threshold A), the policy-layer gap becomes load-bearing: an adopter could ship frontend code, claim it followed DPBM, and have no Phase-0 artefact in the tree to corroborate the claim. The merge gate would not notice.

This rule closes that gap as a presence check, not a content check. The argument for presence-only:

- An adopter who declares `dpbm-scoped: true` and then opens a frontend PR with no `DESIGN_SPEC.md` in their tree is, by construction, not building under DPBM. The rule catches the absence — the simplest possible signal.
- An adopter who declares `dpbm-scoped: true` and has `DESIGN_SPEC.md` present but stale or incomplete is a separate concern handled by ACC's `design_parity` micro-check (DPBM Phase 2 per ADR-016) at build time, and by later rule proposals (token-reference linkage, view coverage) at PR time.

### Threat model / governance concern

Three failure modes the absence of SCP-R-005 enables:

1. **DPBM-by-aspiration.** An adopter declares intent to follow DPBM (in their planning artefacts, in their `STRATEGY_*.md`, in the cascade DISPATCH-NOTE) but never produces the Phase-0 artefacts. Frontend PRs ship. There is no machine signal that the foundational discipline was skipped. Six months later when the adopter's UI has drifted from any consistent design intent, the post-mortem reveals the Phase-0 artefacts were never produced — but the cascade DISPATCH-NOTE shows the adopter as `dpbm-scoped: true`.

2. **DPBM-as-checkbox.** The adopter creates `docs/design/DESIGN_SPEC.md` once (as an empty stub to satisfy the rule, before SCP-R-005 was promoted to deny on their repo) and never updates it. The presence-rule still passes. This is the *false-positive* of presence-only checks; it is the cost of staying inside the static-Rego invariant the federation primitive depends on. The countermeasure is a separate later rule (proposed under future RULE-NNN) that checks `DESIGN_SPEC.md` non-trivially populates beyond a stub.

3. **DPBM-without-declaration.** An adopter does DPBM-quality work but never declares `dpbm-scoped: true`. The rule silently doesn't fire. The cascade DISPATCH-NOTE shows the adopter as un-scoped. This is acceptable — the rule explicitly does not require adopters to adopt DPBM; it requires adopters who *have declared* DPBM scope to keep the Phase-0 oracle present. Adopters who do DPBM-quality work without declaring scope are out-of-scope for the policy layer; declaration is the opt-in handle.

### Prior conversation

- `STATUS.md` 2026-05-09 chain — "D-048 DPBM — file SCP-side adoption decision" filed as the long-pending follow-up. This rule-RFC + D-049 jointly close that follow-up.
- `docs/decisions/D-049-design-system-policy-layer-adoption-2026-05-19.md` — the standalone ADR ratifying SCP's three-element role in estate design-system compliance. RULE-002 is the implementation companion: Element 1 (artefact-presence gating) realised as a concrete rule proposal.
- `docs/home/HOME.md` §8.2 "Policy expansion" — names DPBM as one of seven real candidates for the federation primitive to carry. RULE-002 is the first such candidate filed via the rule-RFC process.
- `/Users/amplience/Projects/acc/docs/decisions/ADR-016-design-parity-build-method.md` §Phase 0 — defines the four Phase-0 artefact classes (`DESIGN_SPEC.md`, `FLOW_SPEC.md`, `TOKENS.md`, screenshots) and locks them as DPBM prerequisites. RULE-002 enforces a subset (presence of at least one of the first three artefacts) at the SCP merge gate.

## 3. Rule specification

### 3.0 Resolved-by-default shape (folded 2026-05-20)

Two structural choices were left open at §7 "Open questions" filing and resolved by operator pre-restart authorisation 2026-05-20. Both are captured inline at the relevant sub-sections below; this paragraph names the resolutions explicitly so a reader scanning §3 does not have to cross-reference §7:

- **ONE-of-three Phase-0 artefact** (not all-three). See §3.1 condition 3. Per `cardinal-rule-2`'s 3-lens default (correctness / safety_bypass / completeness_governance), the rule's *correctness* lens is satisfied by any single artefact's presence — the bare-minimum signal that the adopter began the Phase 0 lock. The *safety_bypass* and *completeness_governance* lenses are not load-bearing on the artefact count: an adopter who carries one stub artefact and three blank ones gets the same `warn` from this rule as an adopter who carries one. Stricter all-three or content-non-trivial checks are separate later RFCs, mirroring D-040's risk-scaled exception parallel — risk-scaled enforcement, not all-at-once.
- **`threshold-overrides` as per-adopter tightening lever** (not loosening). See §3.2 + §5. The `threshold-overrides` map is the per-adopter ramp mechanism that the pragmatist agent perspective argued for and that the per-adopter cascade pattern requires. It is **always tightening** at the rule level — an adopter can promote `warn` → `deny` on themselves before the global ramp does. Loosening (e.g., `warn` → `disable`) is also schema-permitted, but loosening still requires the existing `justification` + `expires_at` waiver fields and is audited; loosening is not a free choice, it is a documented self-suppression with audit trail. The key shape is "per-adopter clock for promotion" + "per-adopter audit trail for suppression," not a generic threshold reassignment knob.

### 3.1 Match conditions

The rule fires when ALL of the following hold for a PR:

1. The adopter's `.scp/rule-config.yaml` declares `dpbm-scoped: true`. (Default is `dpbm-scoped: false` or unset, in which case the rule does not fire — vacuous pass.)
2. The PR's changed-files set contains at least one file path matching any of the adopter's declared frontend path globs. Default globs: `["frontend/**"]` (single-element list — see "Default glob rationale" below). Adopters override via `.scp/rule-config.yaml` `dpbm-frontend-paths: [<glob>, <glob>, ...]`.

   **Default glob rationale (folded 2026-05-20):** Operator grep-check across the 5 named cohort adopters returned `frontend/**` matches 5/5 (every adopter that has a frontend directory uses a top-level `frontend/`); `src/components/**` matches 0/5 (no adopter has frontend code under `src/components/`). The prior multi-glob default (`["frontend/**", "src/components/**"]`) was a defensive guess at structures none of the cohort actually use; the single-glob `["frontend/**"]` default matches the empirical adopter shape and reduces the false-positive surface to exactly the path-shape adopters do use. Adopters with non-`frontend/**` structures (e.g., Recommender's per-adopter override that adds `shopify-app/app/**` per D-049 §"Decision points" item 3 bullet 5) declare overrides via `dpbm-frontend-paths`; the default is conservative and tight.
3. The adopter's repo tree at PR HEAD does NOT contain at least one of: `docs/design/DESIGN_SPEC.md`, `docs/design/FLOW_SPEC.md`, `docs/design/TOKENS.md`. **Presence of at least ONE of the three is sufficient — RESOLVED 2026-05-20 per §3.0 (cardinal-rule-2 3-lens default + D-040 risk-scaled exception parallel).** Adopters who carry all three immediately are doing DPBM Phase 0 fully; adopters who carry only one are doing the bare minimum but are not yet failing the rule. The all-three (or "all-three plus screenshots") variant is deferred to a later rule-promote RFC; this rule is the lowest-friction first ramp.

When all three hold, emit one finding per missing artefact, with the finding's `path` field pointing to the expected artefact location (e.g., `docs/design/DESIGN_SPEC.md`) so the GitHub Actions annotation surfaces in the Files-Changed tab at the right location.

Example: a PR on a `dpbm-scoped: true` adopter that touches `frontend/src/components/Button.tsx` but has no `docs/design/` directory at all triggers three findings — one for each of the three named artefacts — all `warn` threshold.

### 3.2 Severity & threshold

- Initial threshold: **`warn`** per `policies/VERSIONING.md`. New rules land at warn baseline; promotion to deny requires a separate rule-promote-warn-to-deny RFC (D-036).
- Adopter override: `.scp/rule-config.yaml` `disable: true` with `justification: <string>` and `expires_at: <date>` continues to suppress (all three fields required by `schemas/rule-config.schema.json` — same shape as SCP-R-004).
- Per-adopter promotion to deny: not via global RFC, but via the adopter setting `dpbm-scoped: true` AND `threshold-overrides: { SCP-R-005: deny }` in their `.scp/rule-config.yaml`. This is the per-adopter ramp the pragmatist agent perspective argued for — global warn baseline; deny activates only on adopters that have declared themselves ready. Schema change to `rule-config.schema.json` to add `threshold-overrides` is in scope for this rule's implementation slice.
- **`threshold-overrides` value enum (resolved 2026-05-20):** the map accepts the value set `{warn, deny, disable, off}`. `warn` and `deny` are the two threshold levels in `policies/VERSIONING.md` today; `disable` is the existing self-suppression semantic (preserved for migration parity with existing `disable: true` waiver field); `off` is a synonym for `disable` accepted at config-load for readability — both lower to the same internal state. Schema validation restricts keys to rule IDs the SCP federation primitive ships at the resolved version, and values to this four-element enum. Any other value is a `rule-config.schema.json` validation failure at config-load (fails the policy-check workflow loudly, not silently).
- **Migration from existing `disable: true` waiver (resolved 2026-05-20):** the existing per-rule `disable: true` waiver shape (the SCP-R-001..R-004 pattern) is mapped silently at config-load to `threshold-overrides: { SCP-R-NNN: disable }`. Adopters do not need to rewrite their existing `.scp/rule-config.yaml` files; the loader normalises the old shape into the new shape. The justification + `expires_at` fields ride along with the override per the existing waiver-audit pattern. New adopters configure via `threshold-overrides` directly; old adopters' working config keeps working. The migration is a config-load transformation, not a one-time rewrite ceremony — no flag day required.

The two-tier model (`dpbm-scoped` boolean + `threshold-overrides` map) is necessary because the cohort adopters' frontend maturity varies. Recommender (Next.js + Storybook) and shopify-app (Shopify-embedded UI) reach DPBM readiness on different timelines; PIM and mapp-doc-agent may never have a frontend deep enough to warrant the rule firing at all. A single global warn-to-deny ramp would either fire on under-ready adopters too soon or wait for the slowest. Per-adopter `threshold-overrides` is the natural shape.

### 3.3 Annotation contract

- **Infrastructure error code** (annotation `title=`): `SCP-E003` for a deny finding, `SCP-E006` for a disabled-rule observability record. Same closed infrastructure-code set documented at ADOPT-001 §12.7.7. This rule does not introduce a new SCP-EXXX code.
- **Rule-specific annotation** (when `annotate=true`): emitted as `::warning file=docs/design/DESIGN_SPEC.md,title=SCP-R-005::DPBM Phase 0 artefact 'docs/design/DESIGN_SPEC.md' missing — required for dpbm-scoped: true adopter on frontend-touching PR. See https://acc.brokapps.ai/decisions/ADR-016 for Phase 0 contents.` (Annotation level escalates to `error` if the adopter has set `threshold-overrides.SCP-R-005: deny` per §3.2.)
- The annotation deliberately carries the canonical ADR URL inline. This is the failure-output remediation surface flagged by the adopter-experience agent — a developer hitting this rule should see, in the PR Files-Changed tab, a direct pointer to the doctrine they need to satisfy. *(This URL is provisional; resolves to whatever the operator names as the canonical published location of ADR-016. Tracked by TF-D049-001.)*
- Sibling `scp/policy-check-readback` commit-status text: "DPBM Phase 0 oracle missing (3 artefacts)" — fits the ~80 char budget.

### 3.4 Implementation sketch

**Scope of this rule's v1.3.0 implementation slice (resolved 2026-05-20):**

- **IN scope:** `policies/SCP-R-005.rego` + tests; `scp_common.rego` helper additions (`glob_match`, `file_in_tree`, `scp_threshold_override_deny`); `schemas/rule-config.schema.json` extension for `dpbm-scoped` + `dpbm-frontend-paths` + `threshold-overrides`; `.github/workflows/policy-check.yml` narrow-glob `repo_tree` materialisation (per §3.4 "Implementation note — workflow-glob narrowing"); the SCP self-dogfood wrapper exercises the rule against SCP's own `main`.
- **OUT of scope for v1.3.0 (deferred):** token-package release flow per D-049 Element 3 — **floor of v1.4.0**, design-team-paced (cadence follows RI's `docs/design/TOKENS.md` authoring tempo, decoupled from SCP federation-primitive release cadence). v1.3.0 carries SCP-R-005 + dogfood only — no token-package release at v1.3.0. The rule's annotation URL points to the canonical published location of ADR-016 (see §3.3); pointing to a token-package artefact URL is a v1.4.0+ enhancement, tracked under TF-D049-003.
- **OUT of scope (deferred to later rule-RFCs):** token-reference linkage checking; visual-test co-touch on frontend PRs; view-coverage in `DESIGN_SPEC.md`; `UAT_REPORT_*.md` presence at release tags. Each is a separate rule proposal per the rule-RFC process (D-036), not bundled into RULE-002.

Proof-of-concept Rego pattern (lands separately under `policies/SCP-R-005.rego`, with companion tests under `policies/tests/scp_r_005_test.rego`):

```rego
package main

import data.scp_common as scp

scp_r_005_rule_id := "SCP-R-005"

# Adopter declared DPBM-scoped via .scp/rule-config.yaml.
scp_r_005_dpbm_scoped if {
    object.get(input.rule_config, "dpbm-scoped", false) == true
}

# Default frontend path globs (adopters override via rule-config).
# Single-element list per §3.1 "Default glob rationale" — 5/5 cohort
# adopters use top-level `frontend/`; src/components/** matched 0/5.
scp_r_005_default_frontend_globs := ["frontend/**"]

scp_r_005_frontend_globs := object.get(
    input.rule_config,
    "dpbm-frontend-paths",
    scp_r_005_default_frontend_globs,
)

# PR's changed-files set contains at least one frontend-globbed path.
scp_r_005_frontend_change_present if {
    some changed_file in input.changed_files
    some glob in scp_r_005_frontend_globs
    glob_match(glob, changed_file)  # helper in scp_common
}

# Phase 0 artefacts the rule looks for. At least one of these must be
# present in the repo tree at HEAD.
scp_r_005_required_artefacts := {
    "docs/design/DESIGN_SPEC.md",
    "docs/design/FLOW_SPEC.md",
    "docs/design/TOKENS.md",
}

scp_r_005_present_artefacts := {a |
    some a in scp_r_005_required_artefacts
    file_in_tree(a)  # helper checks input.repo_tree
}

scp_r_005_phase0_satisfied if {
    count(scp_r_005_present_artefacts) >= 1
}

# Findings: one per missing artefact, when all match conditions hold.
scp_r_005_raw_findings contains finding if {
    scp_r_005_dpbm_scoped
    scp_r_005_frontend_change_present
    not scp_r_005_phase0_satisfied
    some artefact in scp_r_005_required_artefacts
    not artefact in scp_r_005_present_artefacts
    finding := {
        "rule_id": scp_r_005_rule_id,
        "severity": "warn",
        "path": artefact,
        "message": sprintf(
            "DPBM Phase 0 artefact '%s' missing — required for dpbm-scoped: true adopter on frontend-touching PR. See ADR-016 for Phase 0 contents.",
            [artefact],
        ),
    }
}

# Standard waiver + rule-config-disable + threshold-override gating.
# Identical shape to SCP-R-004 (see policies/SCP-R-004.rego).
warn contains output if {
    some finding in scp_r_005_raw_findings
    not scp_active_waiver_for(scp_r_005_rule_id)
    not scp_rule_config_disabled(scp_r_005_rule_id)
    not scp_threshold_override_deny(scp_r_005_rule_id)
    output := object.union(finding, {"msg": finding.message})
}

deny contains output if {
    some finding in scp_r_005_raw_findings
    not scp_active_waiver_for(scp_r_005_rule_id)
    not scp_rule_config_disabled(scp_r_005_rule_id)
    scp_threshold_override_deny(scp_r_005_rule_id)
    output := object.union(finding, {"msg": finding.message})
}
```

Reused helpers from `policies/scp_common.rego`: `scp_active_waiver_for`, `scp_rule_config_disabled`, `scp_waiver_expired`. New helpers needed: `glob_match(<glob>, <path>)`, `file_in_tree(<path>)`, `scp_threshold_override_deny(<rule_id>)`. All three are small, single-purpose, and add to scp_common per the rule-RFC implementation slice.

#### Implementation note — workflow-glob narrowing (resolved 2026-05-20)

The `input.repo_tree` field is **scoped to a narrow workflow-level glob, not the full repo tree.** The workflow constructs `input.repo_tree` by enumerating files matching the glob set `docs/design/**` (and any future design-system rule's required artefact glob) at PR HEAD, not by inventorying the entire checked-out tree. This is the **workflow filters → Rego evaluates** split that the existing federation primitive already follows for `input.changed_files` (workflow narrows to the PR's changed-file set; Rego evaluates against that input shape, never crawling the working tree).

Rationale (folded 2026-05-20):

- **Performance.** A full-tree enumeration on a large adopter repo (thousands to tens of thousands of files) inflates the policy-check input payload and the Rego evaluation surface for every PR. The narrow `docs/design/**` glob keeps the input bounded regardless of adopter size — same shape, same evaluation cost, on a 100-file repo or a 50k-file repo.
- **Pattern parity with existing federation surface.** Every existing rule (SCP-R-001..R-004) operates on a workflow-narrowed input shape: `input.changed_files` (a glob over the PR's diff), `input.rule_config` (a single file), `input.waivers` (a single file). No existing rule consumes a full-tree inventory. RULE-002 holding that invariant means the federation primitive's input-construction step continues to be the one-place authority for "what does the rule see"; the rule itself never reasons about absent inputs.
- **Per-adopter design-system rule co-evolution.** A future design-system rule (token-reference linkage; view-coverage; UAT-presence) will extend the `docs/design/**` glob to e.g. `docs/design/uat-screenshots/**` — a small, narrow addition. The narrow-glob discipline means each future rule names exactly the paths it needs; the workflow input grows predictably as the policy-layer expands, never as the adopter repo grows.

The one workflow change required: extend `.github/workflows/policy-check.yml`'s input-construction step to materialise a `repo_tree` field populated by `git ls-tree --name-only HEAD -- docs/design/` (or equivalent), narrowed to the design-system glob set. The `file_in_tree(<path>)` helper in scp_common consults this narrow list, not a full-tree inventory.

## 4. False-positive surface

Every rule has one. SCP-R-005 fires on legitimate manifests in the following cases:

1. **Adopter just declared `dpbm-scoped: true` and is opening the first PR.** They have not yet committed `docs/design/` artefacts. The rule fires `warn` on every frontend file in the PR. This is technically a false-positive in the sense that the adopter is *intending* to comply but has not yet had time to author the artefacts. Mitigation: the rule is `warn` baseline, not `deny`, so the PR is not blocked. Adopter can self-suppress for one release via `.scp/rule-config.yaml disable: true` with `justification: "first PR after dpbm-scoped opt-in; artefacts authored in follow-up PR"` and `expires_at: <one release>`.

2. **Adopter has Phase-0 artefacts at non-standard paths.** Some adopter places `DESIGN_SPEC.md` at `docs/architecture/design.md` rather than `docs/design/DESIGN_SPEC.md`. Mitigation: the rule's required-artefacts list is currently hardcoded. A future rule-promotion RFC may add an override (`.scp/rule-config.yaml dpbm-artefact-paths: { design_spec: <path>, flow_spec: <path>, tokens: <path> }`). For now, adopters with non-standard paths self-suppress via the standard `disable: true` waiver.

3. **Adopter touches a file under `frontend/` that is genuinely unrelated to design** (e.g., a Dockerfile, a `.env.example`, a CI helper script that happens to live in the frontend directory). Mitigation: the adopter narrows their `dpbm-frontend-paths` glob in `.scp/rule-config.yaml` to exclude non-design paths. The default glob (`["frontend/**"]`) is intentionally wide; adopters tune it.

4. **PR touches a frontend file as part of a refactor that removes the entire frontend.** The adopter is mid-decommission. The rule fires on each file removal because the changed-files set still contains frontend paths but the artefacts are also being removed. Mitigation: the standard `disable: true` waiver applies; this scenario is rare enough that a dedicated `dpbm-scoped: false` flip mid-decommission is acceptable.

5. **Adopter declares `dpbm-scoped: true` aspirationally for a future quarter** and opens many PRs in the meantime that touch frontend files. The rule fires `warn` on every such PR. Mitigation: `dpbm-scoped: true` is meant to be set *when DPBM enforcement is desired*, not before. The rule's documentation (this proposal + the in-annotation URL) will make this clear; adopters who set the flag early get the visible signal.

## 5. New bypass-surface elements

Per the proposal header, this rule introduces bypass-surface elements that make the 48h review window non-waivable. Enumerating them explicitly:

1. **`.scp/rule-config.yaml` `dpbm-scoped: <bool>`** — new key. Default `false` (unset). When `false` or unset, SCP-R-005 (and any future design-system rules following the same pattern) does not fire. Adopters opt into design-system enforcement by setting this key to `true`. The schema extension lives in `schemas/rule-config.schema.json`.

2. **`.scp/rule-config.yaml` `dpbm-frontend-paths: [<glob>, …]`** — new key. Default `["frontend/**"]` (single-element list per §3.1 "Default glob rationale" — 5/5 cohort grep). Adopters override the path globs that determine when the rule fires.

3. **`.scp/rule-config.yaml` `threshold-overrides: { SCP-R-NNN: <warn|deny|disable|off> }`** — new key (general-purpose, not SCP-R-005-specific, though SCP-R-005 is the first rule that uses it). Adopters override the rule's global threshold per their `.scp/rule-config.yaml`. This is the per-adopter warn-to-deny ramp mechanism per §3.2. Value enum is the four-element set `{warn, deny, disable, off}`; `off` is a synonym for `disable` accepted at config-load for readability. Schema validation restricts the keys to rule IDs that the SCP federation primitive ships at the resolved version and values to the four-element enum; any other value fails config-load loudly. Existing `disable: true` per-rule waiver shape migrates silently at config-load to `threshold-overrides: { SCP-R-NNN: disable }` — no rewrite ceremony required of existing adopters (see §3.2 migration note).

All three additions follow the existing `.scp/rule-config.yaml` shape, are schema-validated by `schemas/rule-config.schema.json`, and are subject to CODEOWNERS protection on the adopter side per ADOPT-001 §11.10. No new SCP-side bypass surface is introduced — every override remains adopter-declared, schema-validated, and committed to the adopter's repo where the audit trail lives.

The non-waivable 48h review window applies because **any** non-empty bypass-surface addition triggers the non-waivable rule per `docs/reviews/rule-proposals/README.md`. The author cannot extend the window; zero approvals at 48h auto-defers.

## 6. Cross-references

- `docs/decisions/D-049-design-system-policy-layer-adoption-2026-05-19.md` — companion standalone ADR; D-049 Element 1 is what this rule implements.
- `docs/DECISIONS.md` — appended row for D-049 (referenced from this proposal).
- `/Users/amplience/Projects/acc/docs/decisions/ADR-016-design-parity-build-method.md` — DPBM doctrine the rule enforces Phase 0 of.
- `/Users/amplience/Projects/control-tower/docs/decisions/D-048-design-parity-build-method-adoption.md` — CT-side DPBM adoption.
- `/Users/amplience/Projects/mapp-returns-intelligence/docs/design/` — gold-standard Phase 0 corpus.
- `policies/SCP-R-004.rego` + `policies/tests/scp_r_004_test.rego` — closest existing rule pattern (waiver-aware, rule-config-aware, warn-baseline). RULE-002 implementation slice models SCP-R-005.rego on this shape.
- `policies/scp_common.rego` — helper library; this rule adds `glob_match`, `file_in_tree`, `scp_threshold_override_deny` helpers.
- `schemas/rule-config.schema.json` — extends with `dpbm-scoped`, `dpbm-frontend-paths`, `threshold-overrides` keys.
- `docs/home/HOME.md` §8.2 — names DPBM as one of seven real candidates for federation primitive policy expansion. RULE-002 is the first such candidate filed.
- `docs/BACKLOG.md` Phase 12 → **TF-PIM-001** "Cross-repo checkout authentication for SCP federation adopters" — explicit adopter-consumption-timing dependency. SCP-R-005 ships at v1.3.0 self-dogfood-only per D-049 §Sequencing; external adopters cannot exercise this rule cross-repo until TF-PIM-001 closes (default `GITHUB_TOKEN` cannot clone the private SCP repo from an adopter context). RULE-002 ships into the codebase independent of TF-PIM-001; *adopter consumption* is gated on it.

## 7. Open questions for operator review

This proposal is filed in DRAFT status. The following points are open for operator amendment before flipping the proposal to UNDER REVIEW:

1. ~~**Does the rule fire on presence of ONE Phase-0 artefact or require ALL THREE?**~~ **RESOLVED 2026-05-20:** ONE-of-three. See §3.0 + §3.1 condition 3. Lowest-friction first ramp; stricter alternatives deferred to later rule-promote RFCs.

2. ~~**Is the default frontend path glob set (`frontend/**`, `src/components/**`) right, or should it be narrower / wider?**~~ **RESOLVED 2026-05-20:** default → `["frontend/**"]` (single-element). Operator grep-check across 5 named cohort adopters: `frontend/**` matches 5/5; `src/components/**` matches 0/5. Per-adopter override via `dpbm-frontend-paths` (committed in §5) handles non-default structures — first concrete example folded into RULE-002: Recommender adds `shopify-app/app/**` per D-049 §"Decision points" item 3.

3. ~~**Should the rule consume `input.repo_tree` (full tree) or restrict to a narrow glob?**~~ **RESOLVED 2026-05-20:** narrow workflow-glob (`docs/design/**`), not full tree. See §3.4 "Implementation note — workflow-glob narrowing." Workflow filters → Rego evaluates; matches the existing federation primitive's `input.changed_files` pattern; bounded input payload regardless of adopter size; small predictable growth as future design-system rules extend the design-system glob set.

4. ~~**Should the rule-config schema for `threshold-overrides` allow `disable` as a value?**~~ **RESOLVED 2026-05-20:** value enum = `{warn, deny, disable, off}` — `disable` and `off` both accepted (synonym pair) so adopters can use whichever reads more naturally in YAML, and existing `disable: true` per-rule waivers migrate silently at config-load. See §3.2 + §5 (key 3).

5. ~~**Should this rule ship at v1.3.0 or wait for WP-SCP-024 Threshold A (024G) to sign?**~~ **RESOLVED 2026-05-20:** ship at v1.3.0 at warn baseline **as self-dogfood-only**. Adopter-cascade consumption is held until TF-PIM-001 (cross-repo `actions/checkout` authentication) closes — see D-049 §Sequencing and §6 cross-reference to TF-PIM-001. WP-SCP-025 (design-system build work-package) remains in authoring mode until 024G Threshold A signs; the v1.3.0 rule ship does not violate that hold because the rule fires zero times against external adopters at v1.3.0.

---

**All §7 open questions resolved 2026-05-20** (operator pre-restart authorisation; this rule-RFC has no remaining decision points). Proposal moves from operator-review-DRAFT to UNDER-REVIEW on PR-merge ceremony per the established rule-RFC review lifecycle.
