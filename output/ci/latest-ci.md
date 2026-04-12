# Standards Control Plane — CI Summary

**Status:** advisory only
**Generated at:** 2026-04-11T00:00:00Z
**Audit ID:** audit-returns-2026-04-11
**Source:** audit
**Outcome:** pass_with_warnings
**Warnings:** 1

## Domain Scores
- governance: 100
- architecture: 25

## Warning Thresholds
- advisory_only: true
- finding_severities: critical, high
- minimum_confidence_class: high
- warn_on_regressions: true

## Warnings
- `WARN-FINDING-F-ARCH-001-returns-exceptions` [finding_threshold] Open finding F-ARCH-001-returns-exceptions meets the CI warning threshold: Code crosses bounded service roots

## Recommended Actions
- Route cross-boundary work through the approved integration seam instead of importing bounded implementation modules directly.
- Move workflow orchestration into an action or service layer and keep UI modules focused on state binding.
- Move remote-access setup behind the approved service abstraction for the subsystem.
