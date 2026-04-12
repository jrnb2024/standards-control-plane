# Strategy — WP-SCP-007 Waivers and Score Model

**Work Package:** `WP-SCP-007`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Strategy

Treat waivers as an audit-time overlay on top of evaluator findings, not as a
special case buried inside each evaluator.

This slice should preserve one clean flow:

1. evaluators emit deterministic findings
2. audit assembly overlays active waivers onto those findings
3. persistence and reporting consume the waiver-aware result
4. scoring uses one explicit shared model

## 2. Why this slice now

The project now has:

- live governance and architecture evaluators
- durable open and history findings stores
- live markdown reports and area summaries

What it lacks is the ability to distinguish an active temporary exception from
an unresolved active issue, and the current score behaviour still lives as
duplicated evaluator-local constants.

## 3. Delivery shape

### 3.1 Waivers overlay findings, they do not erase them

An active waiver should change the effective status of a currently detected
finding from `open` to `waived`.

That means:

- the audit result still shows the finding
- the audit result also lists the applied waiver separately
- history preserves the waived status
- the open-findings store excludes it
- score penalties apply only to unwaived active findings

### 3.2 Keep waiver storage simple in phase 1

Use the existing repo-local file:

- `output/findings/waivers.json`

This slice only needs read/apply behaviour. Human editing is acceptable in
phase 1 as long as the file is validated and ambiguous overlap fails loudly.

### 3.3 Scoring becomes shared and documented

The score model should move into one shared module so both:

- evaluator-local raw scores
- audit-level waiver-aware effective scores

use the same rules.

The documentation should describe the current phase-1 model honestly:

- severity deductions are fixed
- only active unwaived findings reduce score
- repeated findings reduce score cumulatively
- regression weighting and richer debt handling are future work

## 4. Output strategy

### Audit result

The audit result should expose:

- `findings`: current findings with status, including `waived` where applicable
- `waivers_applied`: the active waivers actually used for this run
- `summary`: open severity counts plus waived count
- `scores`: waiver-aware domain scores

Applied waivers should be listed in deterministic `finding_id` then `waiver_id`
order so unchanged waiver state does not create output churn.

### Findings stores

- history keeps waived findings
- open store contains only `status == "open"`
- reruns with the same waiver state remain deterministic

### Reports in this slice

The existing markdown report generator should remain downstream of the persisted
open/history findings state. This slice should not add new waiver-specific
markdown sections.

## 5. Expected follow-on

If this slice lands cleanly, the next work package can harden review-evidence
signals and pilot tuning on top of a clearer distinction between active debt,
temporary exceptions, and score impact.
