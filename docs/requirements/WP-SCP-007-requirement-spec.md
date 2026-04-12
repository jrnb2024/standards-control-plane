# RequirementSpec — WP-SCP-007 Waivers and Score Model

**Work Package:** `WP-SCP-007`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Implementation Branch:** `feature/wp-scp-007-waivers-and-scoring`

## 1. Purpose

Make waivers real in the live audit path and stop treating score calculation as
implicit evaluator-local logic.

This slice should honour active waivers without hiding the underlying findings,
keep waived issues out of active open-findings and score penalties, and record
the scoring model explicitly in both code and repo documentation.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-701 | The system shall load waivers from `output/findings/waivers.json` as a repo-local machine-readable input for audit assembly. |
| FR-SCP-702 | A waiver shall apply only when its `finding_id` matches a currently detected finding and its `expires_at` timestamp is later than or equal to the current audit timestamp. |
| FR-SCP-703 | Audit assembly shall preserve waived findings in the audit result with `status: "waived"` instead of silently dropping them. |
| FR-SCP-704 | Audit assembly shall expose applied waivers separately from unresolved unwaived findings so consumers can distinguish active exceptions from active debt. |
| FR-SCP-705 | Findings persistence shall preserve waived findings in history and exclude them from the open-findings store. |
| FR-SCP-706 | If more than one active waiver targets the same `finding_id` for the same audit timestamp, audit assembly shall fail explicitly rather than choosing arbitrarily. |
| FR-SCP-707 | The score calculation used by evaluators and audit assembly shall be implemented in one shared module rather than duplicated per evaluator. |
| FR-SCP-708 | Score calculation in this phase shall deduct only for active unwaived findings and shall not reduce the score for `waived`, `resolved`, `accepted`, `false_positive`, or `superseded` findings. |
| FR-SCP-709 | The scoring model shall remain deterministic, severity-based, and bounded to the 0 to 100 range. |
| FR-SCP-710 | The repo shall include explicit score-model documentation that explains the current severity deductions, status handling, and known future extension points. |
| FR-SCP-711 | Example audit outputs and tracked repo outputs shall stay schema-valid after the waiver-aware contract changes in this slice. |
| FR-SCP-712 | Waiver-aware outputs in this slice shall be ordered deterministically, including the applied-waivers list and any waiver-aware findings persistence results. |

## 3. Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-701 | Re-running the same audit request against unchanged findings and waiver inputs must produce byte-identical audit and findings-store outputs. |
| NFR-702 | Missing `waivers.json` shall be treated as an empty waiver set so the audit path remains usable before teams adopt waivers. |
| NFR-703 | Invalid waiver payloads shall fail explicitly and early rather than being partially ignored. |
| NFR-704 | The waiver overlay must stay outside evaluator heuristics so the same evaluator output can be reused with and without waivers. |

## 4. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-007-001 | An audit with no active waivers still returns the same effective open findings and scores as before this slice. | pytest |
| AC-WP-SCP-007-002 | An audit with an active waiver marks the targeted finding as `waived`, lists the waiver under a separate applied-waivers output field, and removes that finding from active score penalties. | pytest |
| AC-WP-SCP-007-003 | Persisting a waiver-aware audit keeps waived findings in history with `status: "waived"` and leaves them out of `open-findings.json`. | pytest |
| AC-WP-SCP-007-004 | Expired waivers are ignored, and duplicate overlapping active waivers for the same finding fail explicitly. | pytest |
| AC-WP-SCP-007-005 | Governance and architecture evaluators both derive scores through the shared score module without duplicating deduction constants locally. | pytest + code review |
| AC-WP-SCP-007-006 | The repo contains an explicit score-model reference document and README guidance for waiver and score behaviour. | manual review |
| AC-WP-SCP-007-007 | A finding that was previously waived but is still emitted after the waiver expires or is removed re-enters the active open-findings set and score penalties on the next audit. | pytest |
| AC-WP-SCP-007-008 | The work package leaves a complete evidence pack under `docs/reviews/WP-SCP-007/`. | manual review |

## 5. Scope Boundary

### In scope

- waiver loading and validation
- waiver application during audit assembly
- waiver-aware findings persistence
- shared deterministic scoring module
- explicit score-model documentation
- tests, examples, and evidence pack

### Out of scope

- CLI commands to create or edit waivers
- waiver-aware markdown report sections
- accepted-debt or false-positive authoring workflows
- regression-weighted scoring
- CI warning thresholds

## 5.1 Backlog mapping

### Consumed in this work package

- `SCP-031` — waiver model with expiry handling
- `SCP-033` — deterministic score calculation and documentation

### Explicitly not consumed in this work package

- `SCP-039` — bundled crash-safe artifact commit
- `SCP-050` — changed-file scoped audit
- `SCP-052` — CI warning thresholds

## 6. Risks

| ID | Risk | Mitigation |
|----|------|------------|
| R-701 | Waivers hide live issues instead of tracking them explicitly | Keep waived findings visible in audit/history with explicit status and separate waiver metadata |
| R-702 | Score logic diverges again across evaluators and audit assembly | Centralise deduction and status handling in one shared module |
| R-703 | Human-edited waiver files become ambiguous | Fail on overlapping active waivers for the same finding and validate all waiver payloads |
| R-704 | This slice accidentally widens into full lifecycle management UI or CLI work | Limit scope to read/apply behaviour plus documentation |

## 7. Rollout / Rollback

This is repo-local work. Rollout is merge to `main`. Rollback is revert of the
work package commit set if waiver or score semantics prove misleading.

## 8. Review Protocol

Plan review and code review for this work package must each use three reviewer
roles:

1. architecture / structure
2. security / quality / governance
3. completeness / acceptance coverage

Evidence is stored under `docs/reviews/WP-SCP-007/`.

Required evidence files:

- `review_findings.md`
- `implementation_notes.md`
- `acceptance_verification.md`
- `test_results.txt`

Minimum evidence content:

- `review_findings.md` records reviewer role, severity, disposition, and follow-up path for every plan/code review finding
- `implementation_notes.md` records the chosen waiver-overlay semantics, score-model choices, and any backlog carry-forward
- `acceptance_verification.md` maps each acceptance criterion to a concrete verification result
- `test_results.txt` captures the exact local test command output used for closure
