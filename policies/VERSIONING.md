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

**Machine enforcement:** `.github/workflows/release-gate.yml` runs
on every `push: tags: ['v*']` (plus `workflow_dispatch:` for
dry-run). It refuses the tag-cut (`SCP-EREL-001`) when:

- any `policies/deprecations.yaml` entry has `target_release` matching
  the candidate tag AND `announced_release` is not at least one MINOR
  behind the candidate, OR
- any `.scp/rule-config.yaml` entry on the SCP repo itself has
  `disable: true` AND `expires_at < <tag-cut date>` (the SCP-self
  half of TF-005 — adopter-side rule-config expiry is enforced at
  PR time via SCP-E007, not here).

To verify a tag without cutting it: `gh workflow run release-gate.yml -f dry_run_tag=v1.1.0`.

Rule deprecation specifically: when an `SCP-R-NNN` rule is
deprecated:

- The rule's deny continues to fire at its current `threshold:` value
  during the deprecation window.
- Each PR run emits `::warning::SCP-R-NNN deprecated; will be removed in v<X+1>.0.0; <migration-pointer>`.
- The release-cut at v<X+1>.0.0 removes the rule from `policies/`.
- A migration pointer (link to a rule-proposal-style amending document
  or a §M.N section of an ADR) MUST be in the warning annotation.

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
