# ARCH-003 Client-Wrapper Exemption — R1 Review Findings

```scp-review-evidence
{
  "review_id": "ARCH-003-CLIENT-WRAPPER",
  "area_id": "standards-control-plane-standards",
  "reviewed_at": "2026-07-19T00:00:00Z",
  "summary": "Three-lens R1 adversarial review of the ARCH-003 client-wrapper exemption (evaluator + standards prose + tests); both blocking completeness findings resolved same-PR.",
  "reviewed_paths": [
    "src/standards_control_plane/evaluators/architecture.py",
    "standards/architecture/index.json",
    "standards/architecture/rules/ARCH-003-api-access-pattern.md",
    "tests/test_architecture_audit.py",
    "STATUS.md"
  ],
  "findings": [
    {
      "finding_id": "RV-ARCH003CW-001",
      "status": "resolved",
      "summary": "Completeness F1: standards prose and index.json exceptions slot did not record the client-wrapper convention; resolved by ARCH-003 rule md Exceptions section + index entry (rule 1.0.0->1.1.0, index 1.2.0->1.3.0).",
      "domain": "governance"
    },
    {
      "finding_id": "RV-ARCH003CW-002",
      "status": "resolved",
      "summary": "Completeness F2: no STATUS.md governance trail; resolved by dated STATUS.md entry (2026-07-19). DECISIONS.md row left to operator (D-number assignment operator-gated, D-066 precedent).",
      "domain": "governance"
    },
    {
      "finding_id": "RV-ARCH003CW-003",
      "status": "resolved",
      "summary": "Completeness F3 / correctness note: -client cross-language variant, backslash and uppercase paths, and negative stems untested; resolved by predicate unit test + search-client.ts case in the repo-backed test.",
      "domain": "architecture"
    },
    {
      "finding_id": "RV-ARCH003CW-004",
      "status": "accepted",
      "summary": "Safety-bypass: filename-stem exemption is content-blind and gameable by rename; accepted for a medium/warn-tier heuristic (same character as the pre-existing /backend/services/ and test-path exemptions). Tightening the proxy with a structural corroborant noted as follow-up candidate.",
      "domain": "architecture"
    },
    {
      "finding_id": "RV-ARCH003CW-005",
      "status": "accepted",
      "summary": "Self-audit residuals: ARCH-003 fires on the evaluator's own source because REMOTE_ACCESS_MARKERS contains the marker string literals (self-referential false positive, string literals not remote access); GOV-002 enhancement-spec absence carried as a note-and-justify protocol deviation (small bugfix slice, PR #239/#247 precedent, non-kernel-dangerous, narrow scope).",
      "domain": "governance"
    }
  ]
}
```

**Slice:** ARCH-003 client-wrapper exemption (branch `fix/arch-003-client-wrapper-exemption`)  
**Date:** 2026-07-19  
**Gate:** build — 3-lens R1 (correctness / safety_bypass / completeness_governance)  
**Status:** Blocking findings resolved same-PR; accepted residuals documented

## Dispositions

| Lens | Verdict | Blocking findings | Disposition |
|------|---------|-------------------|-------------|
| correctness | CONFIRMED-correct | none | Predicate verified on posix/backslash/bare/uppercase shapes and negative stems (`client.py`, `my_client_utils.py` not exempt); single call site (ARCH-003 only); seeded fixtures unaffected; new test proven non-vacuous. Non-blocking: multi-suffix stems (`*.d.ts`, `*.gen.ts`) not exempted — conservative, still flags. |
| safety_bypass | acceptable, no unacceptable weakening | none | Exemption scoped solely to `_ad_hoc_api_access_finding`; no leakage to ARCH-001/002/004 or the Rego plane. Rename-evasion acknowledged as lowest-friction bypass; tolerable for warn-tier (RV-ARCH003CW-004). |
| completeness_governance | FINDINGS | F1 prose/exceptions drift; F2 missing STATUS trail | Both resolved same-PR (RV-ARCH003CW-001/002). F3 coverage gap resolved (RV-ARCH003CW-003). F4 version-manifest bump and F5 applies_to twin checked-and-dismissed: VERSIONING.md scope excludes the Python evaluator (no Rego rule maps to ARCH-003); applies_to governs rule relevance, not finding emission, and must keep surfacing ARCH rules for client wrappers on consult. |

## Provenance

mapp-pim [PR #732](https://github.com/jrnb2024/mapp-pim/pull/732) re-audit false-flagged
`services/enrichment/services/product_core_client.py` — the exemplar of the very
abstraction ARCH-003 mandates. Post-fix re-audit of that diff: architecture 100, zero findings.
