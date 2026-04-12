# Strategy — WP-SCP-010 UX / IA Scaffolding and Evaluator Shell

**Work Package:** `WP-SCP-010`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Strategy

Start with a deliberately narrow UX shell that only checks for screen signals an
implementation agent can act on directly from code:

- clear primary action
- explicit loading / empty / error coverage
- obvious screen-role or navigation cues

## 2. Why this slice now

The system now has explicit confidence classes. That makes it safe to add the
first inference-adjacent domain as long as the checks stay bounded and the
confidence remains visible.

## 3. Delivery shape

### 3.1 Registry first

Add UX rules and patterns to the live registry so consult can use them even
before the evaluator grows richer.

### 3.2 Shell, not grand reviewer

The evaluator should not attempt broad UX judgement. It should emit findings
only when obvious structural signals are missing from the screen files.

### 3.3 One failing pilot, one stable fixture

Use the seeded Returns pilot to exercise the missing-signal path and add one
stable fixture to prove the shell can also stay quiet.
