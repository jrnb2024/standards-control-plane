# 020h3-release-gate fix-round-1 (post-r1)

**Date:** 2026-05-01

## Triggers

R1 dispatch returned (commit 16dfc02 reviewed):

- **R1 correctness** (`review-correctness.json`, ~8 min, APPROVED_WITH_FINDINGS): 2 MAJ + 3 MIN + 1 nit.
- **R1 safety** (`review-safety.json`, ~6.3 min, CHANGES_REQUESTED): **1 CRIT** + 3 MAJ + 2 MIN + 2 nit.
- **R1 completeness** (`review-completeness.json`, ~9 min, NEEDS_FIX): 2 MAJ + 2 MIN.

**Cumulative: 1 CRIT + 7 MAJ + 7 MIN + 3 nit.** Per `feedback_protocol_over_shortcuts.md` no descoping; all closed inline OR tracked as TF-020H3rg-NNN.

## CRIT closure

| Finding | Closure |
|---|---|
| **CRIT-SAFE-001** (workflow is post-tag observer, not pre-emptive gate) | Acknowledged honestly across the board. Workflow header reframed to "two operating modes": (1) dry-run pre-flight via `workflow_dispatch` (the pre-emptive enforcement path; operator-mandatory per VERSIONING.md "Tag-cut procedure"); (2) post-tag observer on `push:tags:['v*']` (last-line-of-defense annotator). VERSIONING.md "Machine enforcement" section rewritten to make this explicit; new "Tag-cut procedure" section with the mandatory dry-run pre-flight step; new "Bad-tag recovery procedure" section. ADOPT-001 §12.7.7 SCP-EREL-001 row updated. DISPATCH-NOTE "Architectural framing" section added. **TF-020H3rg-003** filed for the missing auto-open-issue step on the post-tag observer path. |

## MAJ closures

| Finding | Closure |
|---|---|
| **MAJ-SAFE-002** (D-030 blocks tag deletion → no recovery for bad tag) | New "Bad-tag recovery procedure" subsection in `policies/VERSIONING.md`: cut a corrected v<X>.<Y+1>.0; bad tag remains immutable; release note on bad tag's GitHub release page; emergency ruleset-disable path documented with amending-decision-row requirement. |
| **MAJ-SAFE-003** (.scp/** absent from CODEOWNERS) | CODEOWNERS extended with `.scp/** @jrnb2024` inserted before `/CODEOWNERS` self-protection per ORDERING INVARIANT. Pre-emptive coverage — `.scp/rule-config.yaml` is currently absent on SCP-self but will be load-bearing for the release-gate expired-config check whenever it's added. |
| **MAJ-SAFE-004** (deprecations.yaml backdating tampering) | Workflow's deprecation-ramp check now emits `SCP-EREL-001-warn` (warning, non-blocking) annotations for entries where `announced_release` is more than one major behind candidate — flags suspicious backdating patterns for operator triage without blocking on legitimate edge cases. The structurally-inconsistent (>1 major behind on the SAME entry) case remains a hard refusal. |
| **COR-MAJ-001** (wrong pyyaml/jsonschema versions) | Versions corrected from `pyyaml==6.0.3` / `jsonschema==4.25.1` to `pyyaml==6.0.2` / `jsonschema==4.23.0` matching `policy-check.yml` lines 627-633 exactly. Comment notes the parity intent. |
| **COR-MAJ-002** (schema enum missing tag_protection_pattern) | `surface_kind` enum extended with `tag_protection_pattern` (covers v* / renovate/v* Repository Ruleset shape deprecations per VERSIONING.md "Tag protection" breaking-change category). Schema description updated. |
| **COMP-MAJ-001** (workflow doesn't enforce target_release is MAJOR) | Workflow's deprecation-ramp check now refuses any entry whose `target_release` is not vX.0.0 (per VERSIONING.md "the MAJOR bump is the breaking-change vehicle"). Refusal emits `SCP-EREL-001` with explicit reason. |
| **COMP-MAJ-002** (per-PR deprecation ::warning:: emission has no implementation) | VERSIONING.md "Rule deprecation specifically" subsection clarified: emission responsibility belongs to the surface itself (the rule's own Rego implementation), NOT a centralized emitter. Added `SCP-DEP-001` annotation class to ADOPT-001 §12.7.7 to register the warning shape. Non-rule surfaces follow the same pattern with surface-specific emission paths. |

## MIN closures

| Finding | Closure |
|---|---|
| **MIN-SAFE-005 + COR-nit-001** (date.today() vs UTC) | Workflow's expired-config check now uses `datetime.datetime.now(datetime.timezone.utc).date()` for timezone-deterministic comparison (matches policy-check.yml's pattern). |
| **MIN-SAFE-006** (pip install without --require-hashes) | Filed as **TF-020H3rg-002** to tighten BOTH `policy-check.yml` + `release-gate.yml` together. Matching the existing `policy-check.yml` pattern at v1.0.0 keeps the supply-chain story consistent across the SCP-source's two YAML/JSON-validating workflows; tightening one without the other would diverge. |
| **nit-SAFE-007 + COR-MIN-003** (concurrency expression) | Concurrency group expression rewritten as `release-gate-${{ github.event_name == 'workflow_dispatch' && inputs.dry_run_tag || github.ref }}` so dry-runs against different tags don't queue behind each other; push:tags is still serialised against any in-flight dry-run for the same tag. |
| **nit-SAFE-008** (DISPATCH-NOTE doesn't disclose post-tag observer limitation) | DISPATCH-NOTE "Architectural framing" section added (post-CRIT-SAFE-001 closure). |
| **COR-MIN-001** (FormatChecker missing) | Schema validator now constructed with `format_checker=FormatChecker()` so `format: date` constraint on `announced_at` is actually enforced. |
| **COR-MIN-002** (020H.1 still IN FLIGHT in STATUS) | STATUS.md 020H.1 row marked ✅ landed at PR #78 commit 06c2b61; cumulative review summary added. |
| **COMP-MIN-001** (no §12.7.7 row for deprecation ::warning::) | ADOPT-001 §12.7.7 extended with `SCP-DEP-001` row covering the per-PR deprecation announcement (informational, non-blocking). |
| **COMP-MIN-002** (TF-020H3rg-001 conditional / not filed) | TF-020H3rg-001 explicitly filed in STATUS.md (PR-time deprecation-announcement linter). DISPATCH-NOTE "Out of scope" section restructured to enumerate ALL TF-020H3rg-NNN items + "Out-of-scope without TF (resolved-as-not-needed)" sub-list for the items that don't warrant tracking. |

## Closures NOT applied

None. Every finding either inline-closed or tracked as TF-020H3rg-NNN.

## Re-review

R2 lens dispatch follows on the post-fix-round-1 state. Per `feedback_recursive_adversarial_review.md`, recurse until no new BLOCKING findings.

The fix-round-1 changes are substantial:
- 1 architectural reframing (CRIT-SAFE-001 closure spans workflow + VERSIONING.md + DISPATCH-NOTE + ADOPT-001 + STATUS).
- 1 new VERSIONING.md section (Tag-cut procedure + Bad-tag recovery procedure).
- 5 workflow-step modifications (deprecation-ramp check tightened, FormatChecker added, UTC-aware date, concurrency expression, pip versions).
- 3 schema/CODEOWNERS additions.
- 4 STATUS.md edits (020H.1 landed mark, TF-020H3rg-001/002/003 entries, DISPATCH-NOTE alignment).

R2 reviewers should expect to verify each closure is genuine and not just textual rewording, particularly the architectural reframing.
