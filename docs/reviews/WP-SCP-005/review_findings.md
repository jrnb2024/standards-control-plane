# WP-SCP-005 Review Findings

**Work Package:** `WP-SCP-005`  
**Date:** 2026-04-12  
**Gate:** A — planning  
**Status:** Findings incorporated; approved for implementation

## Findings

| Reviewer role | Severity | Finding | Disposition | Patch reference |
|---------------|----------|---------|-------------|-----------------|
| architecture / structure | High | `finding_id` reuse across different scope pairs could corrupt persisted lifecycle state. | Accepted and fixed by requiring collision checks against `(domain, area_id)` and explicit failure on mismatch. | RequirementSpec FR-SCP-502; TechnicalArchitecture section 3; Decision D-011 |
| security / quality / governance | High | Resolution scope was ambiguous and could spuriously resolve findings on partial audit coverage. | Accepted and fixed by constraining resolution to `scope.area_id` plus domains whose `domain_status` is `evaluated`. | RequirementSpec FR-SCP-503; Strategy section 3.1; TechnicalArchitecture section 3 |
| completeness / acceptance coverage | Medium | Deduplication was promised in the programme but not specified in the slice contract. | Accepted and fixed by adding explicit duplicate-handling requirements and acceptance coverage. | RequirementSpec FR-SCP-508; AC-WP-SCP-005-009 |
| completeness / acceptance coverage | Low | The CLI write contract was too vague. | Accepted and fixed by naming the explicit interface `audit --request <path> --write-output` and preserving read-only as default. | RequirementSpec FR-SCP-505; Strategy section 3.3; ProgrammePlan deliverable 3 |
| security / quality / governance | Medium | The read-only audit path was not acceptance-gated after introducing persistence. | Accepted and fixed by adding explicit no-write verification coverage. | RequirementSpec AC-WP-SCP-005-007 |
| security / quality / governance | Medium | Coupled output files lacked atomic-write requirements. | Accepted and fixed by requiring temp-file staging and atomic replacement. | RequirementSpec FR-SCP-509; Strategy section 4; TechnicalArchitecture section 4; Decision D-011 |
| security / quality / governance | Medium | `created_at` and `updated_at` semantics were required but not acceptance-gated. | Accepted and fixed by adding timestamp-preservation acceptance coverage. | RequirementSpec AC-WP-SCP-005-008; TechnicalArchitecture section 3 |
| architecture / structure | Low | Canonical ordering for persisted stores was not defined. | Accepted and fixed by documenting `(domain, area_id, finding_id)` ordering. | Strategy section 4; TechnicalArchitecture section 4 |
| security / quality / governance | Medium | Evidence files were named but not content-constrained enough for autonomous closure. | Accepted and fixed by adding minimum evidence content requirements. | RequirementSpec section 8; ProgrammePlan section 5 |

## Outcome

Gate A is complete. The planning pack is approved for implementation with
explicit scope-bound resolution, duplicate-handling rules, atomic-write
requirements, and a concrete CLI contract.

## Gate B — Code Review

**Date:** 2026-04-12  
**Status:** Findings addressed; one residual carried to backlog

| Reviewer role | Severity | Finding | Disposition | Patch reference |
|---------------|----------|---------|-------------|-----------------|
| completeness / acceptance coverage | High | The evidence pack was incomplete. | Fixed by adding implementation notes, acceptance verification, and raw test results. | `docs/reviews/WP-SCP-005/implementation_notes.md`, `docs/reviews/WP-SCP-005/acceptance_verification.md`, `docs/reviews/WP-SCP-005/test_results.txt` |
| architecture / structure | High | The write path was widened beyond the approved contract by exposing `--output-dir`. | Fixed by removing `--output-dir` from the CLI and keeping persistence confined to `output/findings/`. | `src/standards_control_plane/cli.py`; `tests/test_findings_persistence.py` |
| security / quality / governance | Medium | Coverage did not exercise the repo-backed write path or the read-only `findings` CLI. | Fixed by adding repo-backed `audit --write-output` coverage with restore logic and a `findings` command test. | `tests/test_findings_persistence.py` |
| architecture / structure | High | True crash-safe pair commits across both persisted findings files are not honestly provided by this slice. | Accepted as a bounded residual: the slice now documents per-file atomic replacement plus rollback on caught failures, and the stronger crash-safe pair commit is carried to backlog. | RequirementSpec FR-SCP-509; Strategy section 4; TechnicalArchitecture section 4; Backlog `SCP-038`; Decision `D-011` |
