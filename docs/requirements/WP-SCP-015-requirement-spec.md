# RequirementSpec — WP-SCP-015 CI Outputs and Warning Thresholds

**Work Package:** `WP-SCP-015`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Implementation Branch:** `feature/wp-scp-015-ci-outputs`

## 1. Purpose

Add CI-facing outputs that project the existing audit result into compact
machine-readable and human-readable artifacts, plus deterministic warning
thresholds that stay advisory in this phase.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-1501 | The system shall derive CI outputs from an existing audit result instead of introducing a second evaluator path. |
| FR-SCP-1502 | `audit --write-output` and `audit-changed --write-output` shall emit a schema-valid CI JSON artifact and a compact CI markdown summary. |
| FR-SCP-1503 | The CI warning evaluator shall emit warning entries for open high-severity findings that meet or exceed a configured confidence threshold. |
| FR-SCP-1504 | The CI warning evaluator shall emit warning entries for unresolved regressions present in the audit result. |
| FR-SCP-1505 | The warning threshold model shall remain advisory in this phase and must not change CLI success semantics. |
| FR-SCP-1506 | The CLI shall expose a read path for the latest CI output so CI consumers and local users can inspect the current projection without reparsing full audit output. |

## 3. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-015-001 | CI output generation returns a schema-valid JSON projection with deterministic warning entries. | pytest |
| AC-WP-SCP-015-002 | CI warnings include high-confidence high-severity open findings and unresolved regressions, but do not force a non-zero CLI exit code. | pytest |
| AC-WP-SCP-015-003 | The CLI can print the latest CI artifact and fails clearly when the artifact is missing. | pytest |
| AC-WP-SCP-015-004 | The work package leaves a complete evidence pack under `docs/reviews/WP-SCP-015/`. | manual review |
