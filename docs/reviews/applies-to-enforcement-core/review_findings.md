# applies_to Enforcement-Core Coverage — R1 Review Findings

```scp-review-evidence
{
  "review_id": "APPLIES-TO-ENFORCEMENT-CORE",
  "area_id": "scp-applies-to-fix-src",
  "reviewed_at": "2026-07-19T00:00:00Z",
  "summary": "Three-lens R1 of the applies_to enforcement-core coverage fix (FUP-APPLIES-TO-ENFORCEMENT-CORE-COVERAGE-001): two SCP-self exact paths added to the governance domain fallback so resolve_domain governs SCP's own policy-check gate. correctness + safety_bypass CONFIRMED; completeness raised one blocking finding (BACKLOG RESOLVED-flip) resolved same-PR.",
  "reviewed_paths": [
    "src/standards_control_plane/applies_to.py",
    "tests/scp_mcp/test_tools/test_resolve_domain.py",
    "docs/BACKLOG.md",
    "STATUS.md"
  ],
  "findings": [
    {
      "finding_id": "RV-ATEC-001",
      "status": "resolved",
      "summary": "Completeness: the implementing PR left its own FUP row (docs/BACKLOG.md) marked OPEN, violating the RESOLVED-flip convention (precedent FUP-WP-SCP-037-ARCH-006-MATERIALISER-001). Resolved same-PR by flipping the row to RESOLVED/BUILT 2026-07-19 with branch + what-landed.",
      "domain": "governance"
    },
    {
      "finding_id": "RV-ATEC-002",
      "status": "resolved",
      "summary": "Coverage asymmetry: no resource-plane inheritance assertion (tool plane tested, resource plane not). Resolved by a test mirroring test_architecture_fallback_surfaces_go_files that asserts _applies_to_for_rule(GOV-002) inherits the enforcement-core paths, plus a .lock sibling non-match assertion.",
      "domain": "architecture"
    },
    {
      "finding_id": "RV-ATEC-003",
      "status": "accepted",
      "summary": "Deferred by design: the adopter-visible .github/workflows/policy-check.yml wrapper is NOT mapped — it exists in adopter repos so it needs a separate over-broadening assessment before governance globs attach. Recorded in the BACKLOG row + STATUS note. STATUS.md dated entry + no version-manifest bump (MCP tool plane internal per VERSIONING.md) + no DECISIONS.md D-row (tool-code fallback-table change, not a governed schema) all confirmed correct.",
      "domain": "governance"
    }
  ]
}
```

**Slice:** applies_to enforcement-core coverage (branch `fix/applies-to-enforcement-core-coverage`)
**Date:** 2026-07-19
**Gate:** build — 3-lens R1 (correctness / safety_bypass / completeness_governance)
**Status:** correctness + safety_bypass CONFIRMED; completeness blocking finding resolved same-PR

## Dispositions

| Lens | Verdict | Blocking findings | Disposition |
|------|---------|-------------------|-------------|
| correctness | CONFIRMED complete+correct | none | Traced the data flow: no governance rule (GOV-001..008) carries a `FALLBACK_APPLIES_TO_BY_RULE_ID` entry, so all inherit the domain fallback → the new globs enter `_registry_glob_domain_map` as `{path}→{governance}`. Exact-path patterns (no metachars) match only the literal path; `.lock` sibling and `scripts/scp-policy-check/foo` do not match; backslash input normalised. Glob hit `continue`s past the fuzzy tier → `governance@0.75`. Over-broadening guard holds (SVC-004 maps `scripts/deploy-*.sh`→service-lifecycle, unaffected). |
| safety_bypass | CONFIRMED no weakening | none | Two literal strings, zero wildcards → cannot match adopter files; adopters consume the reusable workflow remotely (ADOPT-001 §12; runtime `.scp-runtime/`) and do not vendor these filenames. `resolve_domain` sets no deny — it affects relevance/consult + audit scope only; the surfaced GOV-006/007/008 are warn-baseline/dormant, so no false DENY. Purely additive (diff = 2 files, appends only). No version-manifest bump owed (VERSIONING.md excludes the MCP tool plane). |
| completeness_governance | FINDINGS (resolved) | RV-ATEC-001 BACKLOG row left OPEN | Flipped OPEN→RESOLVED per the BACKLOG.md convention (RV-ATEC-001). Added resource-plane inheritance + `.lock` non-match assertions (RV-ATEC-002). Correctly ruled out: STATUS.md per-PR log claim (a dated entry is nonetheless added per this repo's stated process), DECISIONS.md D-row, and version-manifest bump — none owed. |

## Provenance

Surfaced during PR [#252](https://github.com/jrnb2024/standards-control-plane/pull/252) (portable-mktemp fix): `resolve_domain` on the changed enforcement-core files returned confidence 0, forcing an `area_hint` on that R1. Filed as `FUP-APPLIES-TO-ENFORCEMENT-CORE-COVERAGE-001` ([#253](https://github.com/jrnb2024/standards-control-plane/pull/253)); this PR implements it. Post-fix `audit_changed` of this diff: architecture 100, zero findings.
