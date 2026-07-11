# SCP Federation Primitive — Versioning Contract

**Status:** active as of slice 020H.1 (2026-05-01).
**Closes:** WP-SCP-020 §4 020H.1 sub-criteria (i) + (ii).

---

## Scope

This document defines the semver contract that the SCP federation
primitive guarantees to adopters who pin a `# tag: v<X>.<Y>.<Z>`
wrapper at `.github/workflows/policy-check.yml`. It covers three
public surfaces:

1. **Reusable workflow inputs** — `workflow_call.inputs` declared on
   `.github/workflows/policy-check.yml`.
2. **Schema contracts** — JSON Schema at
   `schemas/policy-check-summary.schema.json` (the structured
   summary artefact every adopter consumes for nightly + release-gate
   reconciliation), `schemas/rule-config.schema.json`, and
   `schemas/scorecard-emit.schema.json` (the opt-in cross-repo
   scorecard emit per WP-SCP-023 023B / D-041 — added at v1.2.0;
   MAJOR-pinned per WP-SCP-023 plan-doc §10 Q1).
3. **Rule IDs** — the `SCP-R-NNN` identifiers under `policies/`.
4. **Opt-in workflow inputs** — `scorecard-emit: bool` (added at
   v1.2.0 per WP-SCP-023 023B; default false). Opt-in inputs follow
   the same MINOR/MAJOR semver category as core inputs.

It does NOT cover internal-only surfaces: `lib/policy_check_invocation.sh`,
`scripts/scp-policy-check.lock`, helper scripts in `scripts/`, the
Renovate preset internal shape, the OPA Rego `scp_common.rego`
helpers, or the SCP-self cross-repo aggregator pipeline
(`.github/workflows/scorecard-aggregator.yml`,
`schemas/scorecard-opt-in-registry.schema.json`,
`schemas/scorecard-index.schema.json`,
`docs/scorecards/opt-in-registry.yaml`,
`output/scorecards/index.json` — added in slice 023C / D-042; mirrors
`.github/workflows/conflict-gate.yml` posture per slice 020N).
These are refactored without notice.

---

## Semver guarantee

**`MAJOR.MINOR.PATCH`** with strict semantic-versioning meaning:

| Bump | When | Adopter action required |
|---|---|---|
| **PATCH** (`v1.0.x`) | Bug fixes, new informational annotations, performance improvements, observability records, internal refactors of helpers/lib. | None — drop in the SHA bump and merge. |
| **MINOR** (`v1.x.0`) | New `workflow_call` inputs (with safe defaults), new `SCP-R-NNN` rules added with `threshold: warn` baseline, new optional schema fields, new commit-status contexts (informational), new `disabled_rules:` reasons. | Recommended: review the release notes for new rules. None mandatory unless the adopter wants to opt into a new rule's `threshold: deny`. |
| **MAJOR** (`vX.0.0`) | Breaking changes — see "What is breaking" below. | **Mandatory** — read the migration guide in the release notes; an amending decision row in adopter's `DECISIONS.md` (or equivalent) before bumping the SHA pin. |

---

## What counts as a breaking change

Any of the following requires a MAJOR bump and an amending decision row:

### Workflow inputs

- Removing a `workflow_call.inputs.<name>`.
- Renaming a `workflow_call.inputs.<name>`.
- Changing the `default:` value of an input in a way that flips an existing adopter's effective behaviour (e.g. `threshold: warn` → `threshold: deny`).
- Changing the `type:` of an input.
- Making a previously-optional input required.

### Schema contracts

- Removing a previously-required field from `policy-check-summary.schema.json` or `rule-config.schema.json`.
- Renaming any field (use add-new-then-deprecate instead).
- Tightening a string `pattern:` such that previously-valid values are rejected.
- Tightening a `format:` constraint (e.g. `date` → `date-time`).
- Adding a new required field (covered by the deprecation ramp — see below).
- Removing an `enum:` value that was previously emitted.

### Rule IDs

- Removing an `SCP-R-NNN` rule.
- Re-numbering an `SCP-R-NNN` rule (the ID is the durable contract; the underlying logic is internal).
- Promoting a rule from `threshold: warn` to `threshold: deny` as the **default** at the SCP source. (Adopters may always override per-rule via `.scp/rule-config.yaml`; the default flip is what's breaking.)
- Tightening a rule's match scope such that previously-passing manifests now deny.

### Read-back / annotation contracts

- Removing `scp/policy-check-readback` commit-status posting.
- Removing a `::warning::` or `::error::` annotation surface that adopters' downstream tooling parses (e.g. an annotation parser that grouped on `title=SCP-E001`).
- Renaming an `SCP-ENNN` error-code identifier.

### Branch-protection helper

- Removing `--repo`, `--branch`, `--plan`, `--no-enforce-admins`, `--i-understand-this-bypasses-the-gate`, `--restore`, `--expected-wrapper-sha`, `--i-understand-restore-removes-admin-enforcement`, `--i-understand-restore-removes-required-checks`, `--i-understand-restore-disables-strict-mode`, `--i-understand-restore-disables-required-signatures`, `--i-understand-restore-replaces-required-check-context`, `--i-understand-restore-re-enables-force-pushes`, `--i-understand-restore-re-enables-deletions`, `--i-understand-this-repo-has-no-prior-green-ci`, `--i-understand-no-gate-2-verification`, or `--i-understand-wrapper-inaccessible` flags from `scripts/enable-required-check.sh`.
- Changing the script's invocation-log markdown block schema.

### Tag protection

- Changing the `v*` or `renovate/v*` Repository Ruleset shape (deletion / non-fast-forward / update behaviour).

---

## What does NOT count as breaking

- Adding new `workflow_call.inputs.<name>` with a safe default.
- Adding new `SCP-R-NNN` rules at `threshold: warn` baseline.
- Adding new schema fields (`additionalProperties: false` is preserved — but new fields are added under existing properties, not as required new top-level fields).
- Adding new `enum:` values that were not previously emitted.
- Adding new `disabled_rules:` reasons.
- Adding new informational `::warning::` or `::error::` titles (if existing titles preserved).
- Internal helper-library refactors.
- New commit-status contexts (the existing two are stable).
- New OPA / Conftest / Regal binary version bumps in the lockfile (these are SHA-pinned; adopters get the new pins via Renovate auto-bump).

---

## Deprecation ramp (one-release warning window)

**Closes 020H.1 sub-criterion (ii); enforced by 020H.3 release-gate.**

When the SCP source needs to remove or breaking-change one of the
public surfaces above, the change MUST proceed via a **one-release
deprecation ramp**:

1. **Release N: add the new surface** (alongside the old surface), and
   in the same release add a `::warning::` annotation to the old
   surface stating: `<surface> deprecated; use <new-surface>; will be
   removed in v<X+1>.0.0`. Document in release notes. **Add an entry
   to `policies/deprecations.yaml`** with `announced_at`,
   `announced_release`, `target_release`, and `migration_pointer`
   (per `schemas/deprecations.schema.json`).
2. **Release N+1 (the next MINOR or MAJOR — whichever lands first):**
   keep both surfaces live; the warning continues to fire.
3. **Release N+M (the MAJOR after the next MINOR):** old surface is
   removed; the MAJOR bump is the breaking-change vehicle. An amending
   decision row in `docs/DECISIONS.md` records the removal. **Remove
   the entry from `policies/deprecations.yaml`** as part of the
   removal commit.

The minimum gap between deprecation announcement (step 1) and
removal (step 3) is **one MINOR release**. Adopters who track every
MINOR release see at least one full PR cycle's worth of warnings
before the surface vanishes.

**Machine enforcement** — two operating modes per `.github/workflows/release-gate.yml`:

1. **Dry-run pre-flight (workflow_dispatch).** The pre-emptive
   enforcement path. The operator runs the gate BEFORE pushing the
   tag:

   ```bash
   gh workflow run release-gate.yml -f dry_run_tag=v1.1.0
   # Wait for the run to start, then watch for completion + non-zero
   # exit on failure (gh run list always exits 0; gh run watch with
   # --exit-status surfaces the workflow's verdict). Closes 020H.3 R2
   # nit-SAFE-001.
   sleep 5  # allow the dispatch to register
   RUN_ID="$(gh run list --workflow=release-gate.yml --limit 1 --json databaseId --jq '.[0].databaseId')"
   gh run watch "${RUN_ID}" --exit-status
   ```

   If the dry-run exits clean, the tag is safe to push. **The
   dry-run pre-flight is mandatory before every v* tag-cut.**

2. **Post-tag observer (`push: tags: ['v*']`).** GitHub Actions
   cannot block a `push: tags` event — by the time the workflow
   fires, the tag already exists on the remote. This trigger
   therefore acts as a last-line-of-defense observer: it annotates
   the bad tag with `SCP-EREL-001` AND opens a
   `release-gate-violation` GitHub issue auto-assigned to `@jrnb2024`
   for triage (per slice 020H.3.1 closure of TF-020H3rg-003 —
   `permissions: { issues: write }` on the workflow + de-dup by tag,
   matching the canary-replay.yml pattern). The bad tag itself is
   immutable per D-030 (the `scp-tag-protection-v` Repository
   Ruleset blocks deletion + force-push + non-fast-forward, including
   for admins).

Both modes evaluate the same TWO invariants:

- any `policies/deprecations.yaml` entry has `target_release` matching
  the candidate tag AND `announced_release` is not at least one MINOR
  behind the candidate, OR
- any `.scp/rule-config.yaml` entry on the SCP repo itself has
  `disable: true` AND `expires_at < <UTC date>` (the SCP-self
  half of TF-005 — adopter-side rule-config expiry is enforced at
  PR time via SCP-E007, not here).

The release-gate also emits **warning** annotations
(`SCP-EREL-001-warn`) on suspicious deprecation patterns
(announced_release more than one major behind candidate) without
blocking — operators triage manually.

### Tag-cut procedure (operator)

Mandatory pre-flight + apply pattern. ALWAYS:

1. **Author the release-prep PR.** Bump `version-manifest.json`;
   add or remove entries in `policies/deprecations.yaml` per the
   ramp; write release notes; merge to `main`.
2. **Dry-run the gate.** `gh workflow run release-gate.yml -f dry_run_tag=<tag>` and wait for exit 0.
3. **Push the tag.** Only after dry-run is clean. The post-tag
   observer fires automatically as a final check.
4. **Publish the GitHub release** + Renovate bump cascade per the
   normal 020H part 2 procedure.

### Bad-tag recovery procedure

If a tag is pushed that fails the post-tag observer:

- **Do NOT attempt to delete or force-push the tag.** The D-030 +
  D-034 tag-protection rulesets block deletion and force-push,
  including for admins. The bad tag is immutable.
- **Cut a corrected `v<X>.<Y+1>.0`** (next MINOR) that satisfies
  the ramp. The bad tag remains in the tag list but is superseded
  by the corrected one.
- **Add a release note on the bad tag's GitHub release page**
  documenting the violation + pointing adopters to the corrected
  tag. Detection latency depends on the adopter's bump path:
  - **Renovate-using adopters** (the §12.7.2 recommended path) see
    the automated bump PR to `v<X>.<Y+1>.0` within hours of
    publication; the bump PR is the primary signal.
  - **Manually SHA-pinning adopters** see no immediate signal at
    all. The `SCP-FRESH-001` freshness warning (ADOPT-001 §12.7.11)
    fires only when the wrapper is more than `freshness_warning_threshold_minor` (default 2) MINOR releases behind main HEAD —
    so an adopter pinned to the bad v<X>.<Y>.<Z> sees the warning
    only after `v<X>.<Y+3>.0` has been cut. Manual quarterly review
    of the SCP releases page (per the §12.7.11 manual fallback) is
    the supplementary signal for this cohort.
- **In an emergency only** (e.g. the bad tag introduced a security
  vulnerability that publishing a corrected tag does not
  immediately mitigate), the temporary-ruleset-disable path is:

  ```bash
  # 1. Discover the ruleset id.
  gh api repos/jrnb2024/standards-control-plane-/rulesets \
    --jq '.[] | {id, name}'

  # 2. Delete the ruleset (requires administration:write PAT).
  gh api -X DELETE repos/jrnb2024/standards-control-plane-/rulesets/<id>

  # 3. Delete the bad tag.
  git push --delete origin v<X>.<Y>.<Z>

  # 4. Restore the ruleset (idempotent; reproduces the D-030 state).
  bash scripts/configure-020j-protections.sh
  ```

  This bypasses the bus-factor-1 protection and MUST be paired with
  an amending decision row in `docs/DECISIONS.md` (closes 020H.3
  R2 COR-nit-002).

Rule deprecation specifically: when an `SCP-R-NNN` rule is
deprecated:

- The rule's deny continues to fire at its current `threshold:` value
  during the deprecation window.
- **The rule's own Rego implementation** emits a per-PR
  `::warning::SCP-R-NNN deprecated; will be removed in v<X+1>.0.0; <migration-pointer>`
  annotation. There is no centralized emitter — each rule self-announces.
  This is the `SCP-DEP-001` annotation class (registered in ADOPT-001
  §12.7.7); the deprecation-PR adds the warning emission alongside
  the existing rule logic and adds the matching entry to
  `policies/deprecations.yaml`.
- The release-cut at v<X+1>.0.0 removes the rule from `policies/`
  AND removes the entry from `policies/deprecations.yaml`. The
  release-gate enforces this contract (refuses to cut the tag if
  the entry is still present and the ramp window hasn't elapsed).
- A migration pointer (link to a rule-proposal-style amending document
  or a §M.N section of an ADR) MUST be in the warning annotation.

Non-rule surfaces (workflow inputs, schema fields, annotation titles,
branch-protection helper flags, tag-protection patterns) follow the
same ramp pattern with surface-specific emission paths — the
`policies/deprecations.yaml` entry has `surface_kind` covering each
category. The emission responsibility belongs to the surface
maintainer (e.g. a workflow-input deprecation announces via a
deprecation log line in the workflow itself).

---

## What "stable" means for v1.x

`v1.0.0` (cut 2026-04-30) is the first stable release. Until v2.0.0 is
cut:

- The shipped rules `SCP-R-001`, `SCP-R-002`, `SCP-R-003`,
  `SCP-R-004` (warn baseline since v1.1.0), `SCP-R-007` (deny baseline
  since v1.3.0), `SCP-R-008` (warn baseline since v1.3.0),
  `SCP-R-030` (warn baseline since v1.4.0) — and any
  subsequently-shipped `SCP-R-NNN` — keep their IDs and (subject to
  the deprecation ramp) their behaviour shape. `SCP-R-005` + `SCP-R-006`
  are RESERVED for D-049 (RULE-002 design-system) + D-036 (RULE-003
  ACC-as-cross-repo-caller) per their respective in-flight slices and
  intentionally skipped from the WP-SCP-025 Phase 1 numbering.

### WARN_BASELINE_RULES — warn-baseline rule register

The live warn-baseline set is the `WARN_BASELINE_RULES` Python set in
`.github/workflows/policy-check.yml` ("Render deny annotations and
enforce threshold" step). Rules in it fire the Rego `deny` rule (raw
findings exist) but are rendered as `::warning::` annotations and
excluded from the merge-gate threshold check, so they never block
merge. Live members (in the `policy-check.yml` set today): `SCP-R-004`,
`SCP-R-008`, `SCP-R-009`, `SCP-R-010`, `SCP-R-011`, `SCP-R-013`, `SCP-R-030`.
The auth trio `SCP-R-009/010/011` (WP-SCP-028; D-058 first auth domain) moved
from target → live at **v1.6.0**: the companion workflow PR materialised their
`input.*` and added them to BOTH `WARN_BASELINE_RULES` sites in the SAME PR
(the SCP-R-030 B.1→companion coupling precedent). Their deny-promotion is
gated on **D-059** (post-4-week observation) and removes them from this set.
`SCP-R-013` (WP-SCP-037; D-058 first ontology domain) has been a warn-baseline
member since §1a (v2.0.x) but ran DORMANT until its companion materialiser
FIRES it at **v2.1.0**; deny-promotion is reserved to a future D-NNN.

**SCP-R-030 — hooked-repo onboarding conformance (WP-SCP-030 Layer 2;
D-058 second domain / proving ground; added v1.4.0).** Gates that a
repo running the acc-hook carries ACC's canonical onboarding preamble
(marker `<!-- canonical:acc-hook-onboarding v1 -->` + the always-allowed
list + a ceremony pointer + the never-disable rule) in its CLAUDE.md.
LINKAGE-not-VALUES: ACC authors the contract, SCP gates linkage; any
repo ceremony is accepted. Notes:

- **Deferred workflow wiring.** v1.4.0 ships the Rego + tests + schema
  opt-in only. The `WARN_BASELINE_RULES` set membership above + the
  materialisation of `input.rule_config` + `input.claude_md*` into the
  evaluation envelope land in a **companion workflow PR**. Until then
  the rule is loaded but **vacuously passes** in production (the
  SCP-R-006 safe-failure precedent).
- **D-060 deny-promotion path.** The `marker_absent` condition is the
  reserved deny-class condition; element-presence checks stay warn.
  Deny-promotion is gated on D-060 (post-4-week observation) and, like
  any warn→deny default flip, is a MAJOR change requiring the rule-RFC
  process — adopters may always opt in early via `.scp/rule-config.yaml`
  `threshold-overrides`.
- **Enforcement reach ≠ canonical reach (no silent caps).** ACC
  propagated the canonical preamble to all 6 hooked repos
  (ACC / CT / PIM / SA / RI / SCP). SCP-R-030 only *gates* repos that
  also run SCP's `policy-check` workflow, so its enforcement reach is
  **hooked ∩ SCP-cohort = {CT, PIM, SCP-self}**. ACC / SA / RI carry the
  Layer-1 marker but are not SCP cohort adopters, so Layer-2 does not
  reach them until they onboard (forward item
  `FUP-WP-SCP-030-EXTEND-REACH-ACC-SA-RI-001`, not a blocker).
  `mapp-doc-agent` is in the cohort but is not hooked → never opts in
  (vacuous-pass; harmless).

**SCP-R-009 / SCP-R-010 / SCP-R-011 — auth-canonical conformance
(WP-SCP-028 Phase 1; D-058 first auth domain; added v1.5.0).** Gate
adopter conformance to CT's published auth canonical: SCP-R-009
(version-pin) against `canonical-sdk-versions.yaml`; SCP-R-010
(import-fence; two tiers — `tier_deny` shadow → deny-class, `tier_warn`
shadow → warn-class) + SCP-R-011 (claim-shape) against
`auth-contract-v1.yaml`. LINKAGE-not-VALUES: CT is the sole auth
authority; SCP reads CT's signed manifests at evaluation time and never
copies their values. Notes:

- **Workflow wiring (SHIPPED at v1.6.0; was deferred at v1.5.0).** v1.5.0
  shipped the Rego + tests + 2 schemas + the 3 `auth-*-disabled` opt-out keys
  dormant. The **v1.6.0 companion workflow PR (WP-SCP-028 Phase 2)** added
  `SCP-R-009/010/011` to BOTH `WARN_BASELINE_RULES` sites in
  `policy-check.yml` AND materialised `input.canonical_sdk_versions` /
  `input.auth_contract` (+ their cosign-derived `_verified` flags) /
  `input.adopter_*` via an additive Option-A `opa eval` repo-level pass
  (mirroring the SCP-R-030 step; conftest per-file pass untouched). The rules
  now FIRE warn-baseline in production. End-to-end coverage:
  `tests/workflow/fixture-scp-r-028-{pass,import-fence,trust-boundary}`.
- **cosign verification anchor.** The companion workflow cosign-verifies
  CT's `auth-contract-v1.yaml.sig.bundle` (keyless Sigstore OIDC;
  identity `.../control-tower/.github/workflows/contract-manifest-publish.yml@refs/heads/main`)
  and passes `*_verified: true`; the rules **fail closed** (emit a
  signature finding) on a present-but-unverified manifest. The
  `manifest_sha256` field is a freshness hint, NOT the anchor.
- **D-059 deny-promotion path.** All three ship warn-baseline; the
  `tier_deny`/below-floor/old-shape/invalid-issuer conditions are the
  reserved deny-class conditions. Deny-promotion is gated on D-059
  (post-4-week observation) and is a MAJOR change requiring the rule-RFC
  process — adopters may opt in early via `threshold-overrides` or opt
  out via the `auth-*-disabled` keys.

**SCP-R-013 — ontology-canonical-consumption (WP-SCP-037; standards-domain
rule ARCH-006; D-058 first ontology domain; added v2.0.x, FIRES v2.1.0).**
Gates that a consumer LINKS to the one canonical fashion ontology authority
(`fashion-ontology-service`) via an `ontology_contract` in `services.yml` and
does not vendor a divergent copy / re-implement canonicalization.
LINKAGE-not-VALUES: FLA authors the data, FOS serves it, SCP gates only the
linkage. Notes:

- **Workflow wiring (SHIPPED at v2.1.0; was DORMANT since §1a / v2.0.x).**
  §1a shipped the Rego + tests + the `ontology-canonical-consumption-disabled`
  opt-out key and added `SCP-R-013` to BOTH `WARN_BASELINE_RULES` sites, but
  the rule vacuous-passed for want of materialised input. The **v2.1.0
  companion materialiser (FUP-WP-SCP-037-ARCH-006-MATERIALISER-001)** adds an
  additive Option-A `opa eval` repo-level pass ("Materialise ontology-canonical
  inputs and evaluate ARCH-006 (SCP-R-013)") that extracts
  `input.ontology_contract` from `services.yml`, greps
  `input.ontology_source_markers`, derives `input.ontology_consumer`, and
  injects the SCP-owned `input.ontology_authoring_allowlist` + full-identity
  `input.repo_id` — so the rule now FIRES warn-baseline in production. No
  cosign/fetch (structural checks read only the adopter tree). End-to-end
  coverage: `tests/workflow/fixture-scp-r-013-{embedded,compliant,carveout,no-self-assert}`.
- **Authoring-source carve-out (trust boundary).** The embedded-copy /
  local-class signals are waived ONLY for repo_ids on the SCP-injected
  `ONTOLOGY_AUTHORING_ALLOWLIST` (`fashion-ontology-service`,
  `fashion-labelling-agent`, `kg-studio`) — keyed on `$GITHUB_REPOSITORY`,
  NEVER a role field asserted in the adopter's own `services.yml`
  (proven by the `no-self-assert` fixture). The identity-gated `ontology-repo-id`
  selftest seam is unreachable by any adopter.
- **Advisory until FOS publishes a version manifest.** Version-pin / endpoint /
  deprecation / perf conformance stay advisory; only the five structural
  LINKAGE signals fire today. Deny-promotion is reserved to a future D-NNN
  (post-observation), a MAJOR change via the rule-RFC process; adopters may opt
  out early via `.scp/rule-config.yaml` `ontology-canonical-consumption-disabled`.

- The `workflow_call` inputs declared on `policy-check.yml` at v1.0.0
  remain stable.
- The `schemas/policy-check-summary.schema.json` shape at v1.0.0
  remains stable.
- The required-check context name `policy-check / scp/policy-check`
  (per D-033) remains stable.
- The Renovate preset `extends:` shorthand
  `github>jrnb2024/standards-control-plane-//renovate/default` remains
  stable.

When v2.0.0 is contemplated, the proposal lands as an ADR via the
rule-RFC process at `docs/reviews/rule-proposals/` (see that
directory's `README.md`).

---

## What adopters SHOULD do on each bump type

- **PATCH (auto-bumped by Renovate):** review the diff in the bump PR
  for unexpected behavioural changes, then merge. Most patches require
  no other action.
- **MINOR:** read release notes; if any new rule lands at
  `threshold: warn` baseline, decide whether to opt into `threshold: deny`
  via `.scp/rule-config.yaml` or wait for the rule to be promoted in a
  future release.
- **MAJOR:** read the migration guide in the release notes; file an
  amending decision row in your repo's `DECISIONS.md` (or equivalent)
  before bumping the SHA pin; if your repo is part of an estate
  cascade (WP-SCP-024), coordinate the bump with the estate owner.

---

## How to file an amending decision

When an adopter accepts a MAJOR bump or breaking change, the
amending decision row should follow the pattern in
`docs/DECISIONS.md`:

```
| D-NNN | <date> | Adopt SCP federation primitive v<X>.0.0 — breaking changes <enumerate>. <Migration steps taken>. | ACCEPTED | <rationale> |
```

This creates a durable audit trail of the version-bump decision
chain. Symmetric with how SCP self files D-022 (initial adoption)
and would file an amending row for any future SCP-self v2.0.0 jump.

---

## References

- WP-SCP-020 plan §4 020H.1 — slice acceptance for this document.
- ADOPT-001 §12.7 — adopter integration appendix.
- `docs/DECISIONS.md` D-022 — initial federation primitive adoption.
- `docs/DECISIONS.md` D-036 — VERSIONING.md + rule-RFC process ratification.
- `docs/reviews/rule-proposals/README.md` — rule-RFC process for rule additions and proposed breaking changes.
- `policies/deprecations.yaml` — live deprecation register (the data the release-gate workflow reads).
- `schemas/deprecations.schema.json` — schema for the register.
- `.github/workflows/release-gate.yml` — the machine-enforced ramp + expired-config refusal at tag-cut.
