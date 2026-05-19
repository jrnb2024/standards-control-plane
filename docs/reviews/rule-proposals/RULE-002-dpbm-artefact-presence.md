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

Add **SCP-R-005** at `threshold: warn` baseline in v1.3.0. The rule fires on PRs that modify files matching the adopter's declared frontend path globs (default: `frontend/**` and `src/components/**`, override via `.scp/rule-config.yaml`) on an adopter that has declared `dpbm-scoped: true` in `.scp/rule-config.yaml`. When fired, the rule asserts that at least one of `docs/design/DESIGN_SPEC.md`, `docs/design/FLOW_SPEC.md`, or `docs/design/TOKENS.md` is present in the adopter's repo tree (NOT necessarily in the changed-files set — the Phase-0 oracle artefacts are expected to be persistent, not co-touched on every frontend PR).

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

### 3.1 Match conditions

The rule fires when ALL of the following hold for a PR:

1. The adopter's `.scp/rule-config.yaml` declares `dpbm-scoped: true`. (Default is `dpbm-scoped: false` or unset, in which case the rule does not fire — vacuous pass.)
2. The PR's changed-files set contains at least one file path matching any of the adopter's declared frontend path globs. Default globs: `frontend/**`, `src/components/**`. Adopters override via `.scp/rule-config.yaml` `dpbm-frontend-paths: [<glob>, <glob>, ...]`.
3. The adopter's repo tree at PR HEAD does NOT contain at least one of: `docs/design/DESIGN_SPEC.md`, `docs/design/FLOW_SPEC.md`, `docs/design/TOKENS.md`. (Presence of at least ONE of the three is sufficient — the rule is the lowest-friction presence check that proves Phase 0 has begun. Adopters who carry all three immediately are doing DPBM Phase 0 fully; adopters who carry only one are doing the bare minimum but are not yet failing the rule.)

When all three hold, emit one finding per missing artefact, with the finding's `path` field pointing to the expected artefact location (e.g., `docs/design/DESIGN_SPEC.md`) so the GitHub Actions annotation surfaces in the Files-Changed tab at the right location.

Example: a PR on a `dpbm-scoped: true` adopter that touches `frontend/src/components/Button.tsx` but has no `docs/design/` directory at all triggers three findings — one for each of the three named artefacts — all `warn` threshold.

### 3.2 Severity & threshold

- Initial threshold: **`warn`** per `policies/VERSIONING.md`. New rules land at warn baseline; promotion to deny requires a separate rule-promote-warn-to-deny RFC (D-036).
- Adopter override: `.scp/rule-config.yaml` `disable: true` with `justification: <string>` and `expires_at: <date>` continues to suppress (all three fields required by `schemas/rule-config.schema.json` — same shape as SCP-R-004).
- Per-adopter promotion to deny: not via global RFC, but via the adopter setting `dpbm-scoped: true` AND `threshold-overrides: { SCP-R-005: deny }` in their `.scp/rule-config.yaml`. This is the per-adopter ramp the pragmatist agent perspective argued for — global warn baseline; deny activates only on adopters that have declared themselves ready. Schema change to `rule-config.schema.json` to add `threshold-overrides` is in scope for this rule's implementation slice.

The two-tier model (`dpbm-scoped` boolean + `threshold-overrides` map) is necessary because the cohort adopters' frontend maturity varies. Recommender (Next.js + Storybook) and shopify-app (Shopify-embedded UI) reach DPBM readiness on different timelines; PIM and mapp-doc-agent may never have a frontend deep enough to warrant the rule firing at all. A single global warn-to-deny ramp would either fire on under-ready adopters too soon or wait for the slowest. Per-adopter `threshold-overrides` is the natural shape.

### 3.3 Annotation contract

- **Infrastructure error code** (annotation `title=`): `SCP-E003` for a deny finding, `SCP-E006` for a disabled-rule observability record. Same closed infrastructure-code set documented at ADOPT-001 §12.7.7. This rule does not introduce a new SCP-EXXX code.
- **Rule-specific annotation** (when `annotate=true`): emitted as `::warning file=docs/design/DESIGN_SPEC.md,title=SCP-R-005::DPBM Phase 0 artefact 'docs/design/DESIGN_SPEC.md' missing — required for dpbm-scoped: true adopter on frontend-touching PR. See https://acc.brokapps.ai/decisions/ADR-016 for Phase 0 contents.` (Annotation level escalates to `error` if the adopter has set `threshold-overrides.SCP-R-005: deny` per §3.2.)
- The annotation deliberately carries the canonical ADR URL inline. This is the failure-output remediation surface flagged by the adopter-experience agent — a developer hitting this rule should see, in the PR Files-Changed tab, a direct pointer to the doctrine they need to satisfy. *(This URL is provisional; resolves to whatever the operator names as the canonical published location of ADR-016. Tracked by TF-D049-001.)*
- Sibling `scp/policy-check-readback` commit-status text: "DPBM Phase 0 oracle missing (3 artefacts)" — fits the ~80 char budget.

### 3.4 Implementation sketch

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
scp_r_005_default_frontend_globs := ["frontend/**", "src/components/**"]

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

The `input.repo_tree` shape needs to be extended at the workflow level to include the full file tree (not just changed files). This is a one-line change to `.github/workflows/policy-check.yml`'s input-construction step, and is the only non-trivial workflow change required for this rule.

## 4. False-positive surface

Every rule has one. SCP-R-005 fires on legitimate manifests in the following cases:

1. **Adopter just declared `dpbm-scoped: true` and is opening the first PR.** They have not yet committed `docs/design/` artefacts. The rule fires `warn` on every frontend file in the PR. This is technically a false-positive in the sense that the adopter is *intending* to comply but has not yet had time to author the artefacts. Mitigation: the rule is `warn` baseline, not `deny`, so the PR is not blocked. Adopter can self-suppress for one release via `.scp/rule-config.yaml disable: true` with `justification: "first PR after dpbm-scoped opt-in; artefacts authored in follow-up PR"` and `expires_at: <one release>`.

2. **Adopter has Phase-0 artefacts at non-standard paths.** Some adopter places `DESIGN_SPEC.md` at `docs/architecture/design.md` rather than `docs/design/DESIGN_SPEC.md`. Mitigation: the rule's required-artefacts list is currently hardcoded. A future rule-promotion RFC may add an override (`.scp/rule-config.yaml dpbm-artefact-paths: { design_spec: <path>, flow_spec: <path>, tokens: <path> }`). For now, adopters with non-standard paths self-suppress via the standard `disable: true` waiver.

3. **Adopter touches a file under `frontend/` that is genuinely unrelated to design** (e.g., a Dockerfile, a `.env.example`, a CI helper script that happens to live in the frontend directory). Mitigation: the adopter narrows their `dpbm-frontend-paths` glob in `.scp/rule-config.yaml` to exclude non-design paths. The default globs (`frontend/**`, `src/components/**`) are intentionally wide; adopters tune them.

4. **PR touches a frontend file as part of a refactor that removes the entire frontend.** The adopter is mid-decommission. The rule fires on each file removal because the changed-files set still contains frontend paths but the artefacts are also being removed. Mitigation: the standard `disable: true` waiver applies; this scenario is rare enough that a dedicated `dpbm-scoped: false` flip mid-decommission is acceptable.

5. **Adopter declares `dpbm-scoped: true` aspirationally for a future quarter** and opens many PRs in the meantime that touch frontend files. The rule fires `warn` on every such PR. Mitigation: `dpbm-scoped: true` is meant to be set *when DPBM enforcement is desired*, not before. The rule's documentation (this proposal + the in-annotation URL) will make this clear; adopters who set the flag early get the visible signal.

## 5. New bypass-surface elements

Per the proposal header, this rule introduces bypass-surface elements that make the 48h review window non-waivable. Enumerating them explicitly:

1. **`.scp/rule-config.yaml` `dpbm-scoped: <bool>`** — new key. Default `false` (unset). When `false` or unset, SCP-R-005 (and any future design-system rules following the same pattern) does not fire. Adopters opt into design-system enforcement by setting this key to `true`. The schema extension lives in `schemas/rule-config.schema.json`.

2. **`.scp/rule-config.yaml` `dpbm-frontend-paths: [<glob>, …]`** — new key. Default `["frontend/**", "src/components/**"]`. Adopters override the path globs that determine when the rule fires.

3. **`.scp/rule-config.yaml` `threshold-overrides: { SCP-R-NNN: <warn|deny> }`** — new key (general-purpose, not SCP-R-005-specific, though SCP-R-005 is the first rule that uses it). Adopters override the rule's global threshold per their `.scp/rule-config.yaml`. This is the per-adopter warn-to-deny ramp mechanism per §3.2. Schema validation must restrict the keys to rule IDs that the SCP federation primitive ships and values to the documented threshold strings.

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

## 7. Open questions for operator review

This proposal is filed in DRAFT status. The following points are open for operator amendment before flipping the proposal to UNDER REVIEW:

1. **Does the rule fire on presence of ONE Phase-0 artefact or require ALL THREE (`DESIGN_SPEC.md` + `FLOW_SPEC.md` + `TOKENS.md`)?** This proposal commits to "at least one of three" as the lowest-friction first ramp. Stricter alternatives (require all three; require all three plus screenshots/) are deferred to later rule-promote RFCs. Operator may amend the §3.1 specification before review.

2. **Is the default frontend path glob set (`frontend/**`, `src/components/**`) right, or should it be narrower / wider?** Recommender uses `frontend/src/app/`; PIM uses `src/`; shopify-app's structure is unknown to this proposal. Operator may amend defaults before review; per-adopter override via `dpbm-frontend-paths` is committed in §5.

3. **Should the rule consume `input.repo_tree` (full tree) or restrict to a `docs/design/**` glob that the policy-check workflow specifically materialises?** Full tree is simplest but increases the workflow input payload. A narrow glob is more efficient but adds workflow surface area. Implementation-slice decision; not blocking the proposal.

4. **Should the rule-config schema for `threshold-overrides` allow `disable` as a value (functionally equivalent to existing `disable: true`)?** Currently the proposal restricts `threshold-overrides` values to `warn` / `deny`. Operator may amend.

5. **Should this rule ship at v1.3.0 or wait for WP-SCP-024 Threshold A (024G) to sign?** D-049 commits to shipping the rule at v1.3.0 at warn baseline (zero-cost release; no current adopter has `dpbm-scoped: true`). The pragmatist alternative is to hold all design-system work in authoring mode until 024G signs. Operator confirms timing on D-049 signature.
