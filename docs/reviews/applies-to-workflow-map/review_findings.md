# applies_to Workflow Mapping — R1 Review Findings

```scp-review-evidence
{
  "review_id": "APPLIES-TO-WORKFLOW-MAP",
  "area_id": "scp-workflow-map-src",
  "reviewed_at": "2026-07-19T00:00:00Z",
  "summary": "Three-lens R1 of mapping the reusable CI workflow .github/workflows/policy-check.yml to the governance domain (discharges the deferred CI-side half of FUP-APPLIES-TO-ENFORCEMENT-CORE-COVERAGE-001). correctness + safety_bypass CONFIRMED; completeness owed-artefacts (BACKLOG clause + STATUS + this file) resolved same-PR.",
  "reviewed_paths": [
    "src/standards_control_plane/applies_to.py",
    "tests/scp_mcp/test_tools/test_resolve_domain.py",
    "docs/BACKLOG.md",
    "STATUS.md"
  ],
  "findings": [
    {
      "finding_id": "RV-ATWM-001",
      "status": "resolved",
      "summary": "Completeness: code+test shipped without the governance-tracking artefacts the sibling PRs carried. Resolved same-PR: amended the FUP BACKLOG deferred clause (reusable workflow now mapped; wrapper intentionally NOT), added the STATUS.md PM-4 dated entry, and this review-evidence file.",
      "domain": "governance"
    },
    {
      "finding_id": "RV-ATWM-002",
      "status": "resolved",
      "summary": "Completeness (minor): the sibling PR guarded the .lock non-match + a backslash variant; this PR initially lacked analogous guards for the workflow path. Resolved by adding a .yml.bak non-match assertion and a backslash-normalised positive-match assertion.",
      "domain": "architecture"
    },
    {
      "finding_id": "RV-ATWM-003",
      "status": "accepted",
      "summary": "Safety_bypass residual (accepted, explicit): the path .github/workflows/policy-check.yml also exists in LEGACY adopter repos that named their own caller wrapper policy-check.yml (canonical is policy-check-wrapper.yml, which is deliberately NOT mapped). Such a wrapper SHA-bump would resolve governance@0.75, but the effect is advisory-only: resolve_domain sets no deny; GOV-002/003 have no SCP-R-*.rego implementation; the MCP server has zero adopter consumers; adopter CI runs the conftest SCP-R-* gate, not the governance-evaluator. Bounded exact-path form is the correct trade vs mapping the wrapper (which would hit every canonical adopter's routine bump) or a blanket .github/workflows/**.",
      "domain": "governance"
    }
  ]
}
```

**Slice:** map the reusable policy-check workflow to governance (branch `fix/applies-to-map-policy-check-workflow`)
**Date:** 2026-07-19
**Gate:** build — 3-lens R1 (correctness / safety_bypass / completeness_governance)
**Status:** correctness + safety_bypass CONFIRMED; completeness owed-artefacts resolved same-PR

## Dispositions

| Lens | Verdict | Blocking findings | Disposition |
|------|---------|-------------------|-------------|
| correctness | CONFIRMED complete+correct | none | Exact-path pattern (no metachars) matches only `.github/workflows/policy-check.yml`; empirically rejects `policy-check-wrapper.yml`, `policy-check.yml.bak`, and nested variants. `fnmatchcase` has no dotfile special-casing so the leading-dot `.github` segment matches literally. GOV-001..008 carry no rule-specific override → inherit the domain fallback → glob map `{path}→{governance}`; glob hit skips fuzzy → `governance@0.75`. |
| safety_bypass | CONFIRMED no unacceptable weakening | none | Purely additive (one glob). Maps only the reusable workflow, NOT the wrapper, NOT blanket `.github/workflows/**`. Residual blast radius stated (RV-ATWM-003): legacy-named adopter wrapper resolves governance@0.75 but advisory-only — no deny, GOV-002/003 have no Rego plane, MCP server has zero adopter consumers, adopter CI unaffected. No version-manifest bump owed: the versioned `.github/workflows/policy-check.yml` adopter contract is `workflow_call` inputs + schemas + SCP-R-NNN IDs (none touched); this is orthogonal relevance metadata on the internal MCP tool plane. |
| completeness_governance | FINDINGS (resolved) | RV-ATWM-001 owed artefacts | BACKLOG deferred clause amended, STATUS PM-4 entry added, this review file added, two guard tests added (RV-ATWM-001/002). DECISIONS.md D-row + version-manifest bump correctly not owed. |

## Provenance

Discharges the CI-side half deferred by PR [#254](https://github.com/jrnb2024/standards-control-plane/pull/254) (FUP-APPLIES-TO-ENFORCEMENT-CORE-COVERAGE-001). Filename investigation before design: SCP's `.github/workflows/policy-check.yml` is the reusable `workflow_call` machinery; the canonical adopter wrapper is `.github/workflows/policy-check-wrapper.yml` (ADOPT-001 §12.7.1 scaffolder + Renovate). Post-fix `audit_changed` of this diff: architecture 100, zero findings.
