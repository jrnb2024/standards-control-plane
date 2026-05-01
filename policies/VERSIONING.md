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
   reconciliation) plus `schemas/rule-config.schema.json`.
3. **Rule IDs** — the `SCP-R-NNN` identifiers under `policies/`.

It does NOT cover internal-only surfaces: `lib/policy_check_invocation.sh`,
`scripts/scp-policy-check.lock`, helper scripts in `scripts/`, the
Renovate preset internal shape, or the OPA Rego `scp_common.rego`
helpers. These are refactored without notice.

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

- Removing `--repo`, `--branch`, `--plan`, `--no-enforce-admins`, or `--i-understand-this-bypasses-the-gate` flags from `scripts/enable-required-check.sh`.
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
   gh run list --workflow=release-gate.yml --limit 1   # wait for completion + verify exit 0
   ```

   If the dry-run exits clean, the tag is safe to push. **The
   dry-run pre-flight is mandatory before every v* tag-cut.**

2. **Post-tag observer (`push: tags: ['v*']`).** GitHub Actions
   cannot block a `push: tags` event — by the time the workflow
   fires, the tag already exists on the remote. This trigger
   therefore acts as a last-line-of-defense observer: it annotates
   the bad tag with `SCP-EREL-001` and (per TF-020H3rg-003) opens
   a `release-gate-violation` issue for triage. The bad tag itself
   is immutable per D-030 (the `scp-tag-protection-v` Repository
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
  tag. Adopters who pinned to the bad tag's SHA see the
  `SCP-FRESH-001` warning on subsequent PRs (per ADOPT-001 §12.7.11)
  prompting them to bump.
- **In an emergency only** (e.g. the bad tag introduced a security
  vulnerability that publishing a corrected tag does not
  immediately mitigate), the temporary-ruleset-disable path is:
  `gh api -X DELETE repos/jrnb2024/standards-control-plane-/rulesets/<id>`
  (requires `administration:write` PAT); delete the bad tag; restore
  the ruleset. This bypasses the bus-factor-1 protection and MUST
  be paired with an amending decision row in `docs/DECISIONS.md`.

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

- The three rules `SCP-R-001`, `SCP-R-002`, `SCP-R-003` keep their IDs
  and (subject to the deprecation ramp) their behaviour shape.
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
