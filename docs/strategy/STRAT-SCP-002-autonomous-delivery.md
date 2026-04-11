# Strategy — STRAT-SCP-002 Autonomous Delivery

**Strategy ID:** `STRAT-SCP-002`  
**Status:** Active  
**Date:** 2026-04-11

## 1. Purpose

Define how the remaining programme should run unattended, without pausing for
routine product or implementation decisions.

This document exists so the repo can move end to end through the backlog using
the same branch, review, PR, and merge discipline already established, while
avoiding avoidable waiting on the user.

## 2. Default operating position

The default is:

- continue
- make the next defensible decision from local context
- keep scope aligned to the active work package
- record residual issues in backlog or review evidence instead of stalling

The system should not pause for confirmation unless one of the explicit hard
blockers in section 6 is hit.

## 3. Decision hierarchy

When unattended execution needs a decision, use this order:

1. user-approved source specification and strategy docs
2. approved work-package requirement, strategy, architecture, and plan docs
3. explicit local contracts and existing code patterns
4. simplest implementation that preserves determinism and extension room
5. backlog carry-forward for non-blocking residual issues

If two options are both valid, choose the narrower one that keeps the current
work package reviewable.

## 4. Standard execution loop

For each work package:

1. start from clean `main`
2. create one feature branch
3. write or update Gate A documents
4. run one plan-review pass with three reviewer lenses
5. patch the real findings from that review
6. implement the approved slice
7. verify locally and write evidence files
8. run one code-review pass with three reviewer lenses
9. fix blocking findings
10. backlog non-blocking residuals that are not worth stalling the slice over
11. open draft PR
12. perform one quick PR pass
13. merge, clean up branch state, and continue from fresh `main`

## 5. Review-loop limits

To avoid getting stuck:

- run one plan-review cycle per work package
- run one code-review cycle per work package
- make one bounded remediation pass after each cycle
- do not repeat the same review gate indefinitely

If a remaining issue after the remediation pass is:

- invalidating the work package acceptance criteria, fix it before merge
- not invalidating the work package acceptance criteria, log it to backlog and
  proceed

## 6. Hard blockers that justify stopping

Stop only for issues like:

- missing GitHub or git access needed to branch, push, or merge
- missing credentials or external access required for the active work package
- destructive migration or data-loss risk that cannot be bounded safely
- a contradiction between approved documents that would make acceptance criteria
  undefined
- protected-branch or repository rules that require human intervention

Everything else should be handled by local decision, bounded remediation, or
backlog carry-forward.

## 7. Backlog carry-forward rule

Create or update a backlog item instead of stalling when all of the following
are true:

- the issue is real
- it does not invalidate the current work package acceptance criteria
- it has a clear follow-on shape
- fixing it now would materially delay the current slice without changing the
  slice outcome

The backlog entry must state:

- what remains
- why it was deferred
- which work package exposed it
- what future dependency or trigger should pull it forward

## 8. Guardrails

Unattended delivery must still avoid:

- speculative redesigns outside the active slice
- hidden contract changes without schema or docs updates
- free-text-only outputs where a structured contract is expected
- merge-with-known-red-tests
- widening a work package because a follow-on idea appeared during review

## 9. Immediate next slice

The next default work package after this strategy lands is:

- `WP-SCP-004` — architecture evaluator and audit extension

The canonical queue after that lives in
`docs/plans/PROG-SCP-001-autonomous-execution-plan.md`.
