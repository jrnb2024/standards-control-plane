# RequirementSpec — WP-SCP-019 Service Auth Contract (SVC-003)

**Work Package:** `WP-SCP-019`
**Version:** 0.1
**Status:** Draft
**Date:** 2026-04-18
**Implementation Branch:** `feature/wp-scp-019-svc-003-auth-contract`

## 1. Purpose

Define the estate's service auth contract as a declare-a-contract rule with a
closed set of approved modes, stand up the service-lifecycle evaluator to
auto-check SVC-001/002/003, and reconcile existing in-repo auth implementations
against the ratified mode set.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-1901 | The system shall define a `service-lifecycle` rule `SVC-003` requiring every service to declare an `auth_contract` block under its `runtime_contract`, listing the auth modes it accepts. |
| FR-SCP-1902 | The approved auth mode set shall be a closed enum of exactly four values: `mode.user_oidc`, `mode.service_rs256`, `mode.api_key`, `mode.bearer_legacy`. No custom modes are permitted. |
| FR-SCP-1903 | Each declared mode entry shall carry the mode-specific metadata required by its spec (audience for JWT modes, issuer reference for API key, deprecation close date and waiver reference for legacy bearer). |
| FR-SCP-1904 | The `auth_contract` declaration shall be validated by a JSON schema that references the approved-mode enum. |
| FR-SCP-1905 | `evaluators/service_lifecycle.py` shall auto-check SVC-001, SVC-002, and SVC-003 against a service manifest and fixture corpus. |
| FR-SCP-1906 | The audit CLI shall run the service-lifecycle evaluator as part of the standard audit path. |
| FR-SCP-1907 | ADOPT-001 §11 shall be rewritten to offer `mode.api_key` for machine callers and `mode.user_oidc` for browser callers, citing commit `66ba8a4` as the reference implementation for `mode.user_oidc`. |
| FR-SCP-1908 | `mode.bearer_legacy` shall require a per-service migration waiver with an explicit close date; the close date for the SCP service's own `--auth-token` path shall be 2026-06-30. |

## 3. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-019-001 | SVC-003 rule is published under `standards/service-lifecycle/rules/` and registered in the domain index. | manual review |
| AC-WP-SCP-019-002 | The `auth-contract` schema validates a service declaration containing any combination of the four approved modes and rejects unknown modes. | pytest |
| AC-WP-SCP-019-003 | `evaluators/service_lifecycle.py` covers SVC-001, SVC-002, and SVC-003 signals with fixture-backed positive and negative cases. | pytest |
| AC-WP-SCP-019-004 | The audit CLI emits SVC-001/002/003 findings against a fixture corpus that includes at least one service per approved mode. | pytest |
| AC-WP-SCP-019-005 | `mapp-pim` dogfood run produces zero unexpected SVC-003 findings against the current PIM auth implementation. | manual review |
| AC-WP-SCP-019-006 | ADOPT-001 §11 no longer documents `--auth-token` as the default shared-service auth path and names the four approved modes. | manual review |
| AC-WP-SCP-019-007 | The work package leaves a complete evidence pack under `docs/reviews/WP-SCP-019/`. | manual review |
