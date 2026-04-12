# Strategy — WP-SCP-009 Confidence Taxonomy and Evidence Classes

**Work Package:** `WP-SCP-009`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Strategy

Add one small shared confidence module and one small evidence-class vocabulary,
then thread both through the existing contracts instead of letting each future
evaluator invent its own meaning.

## 2. Why this slice now

The next phase brings three advisory-heavy domains:

- UX / IA
- design system
- product coherence

Those domains will rely more on bounded inference than the current governance
and architecture checks. If confidence classes are not explicit before they
land, later contracts will drift and findings will be harder to interpret.

## 3. Delivery shape

### 3.1 Confidence stays numeric first

The source value remains the numeric `confidence` score already used in
findings. The new `confidence_class` is derived deterministically from that
score rather than stored independently.

### 3.2 Small evidence vocabulary

The evidence model should classify where evidence came from, not restate the
whole detection method. This slice should keep the class list small:

- `direct_file`
- `declared_metadata`
- `structured_review`
- `historical_review`
- `derived_heuristic`

### 3.3 Existing evaluators first

Governance and architecture should adopt the new contract immediately so the
taxonomy is exercised before new domains arrive.

### 3.4 Visible in consult as well as audit

The change must not stop at audit output. Consult responses should also expose
the derived confidence class, including on surfaced open findings, so
implementation agents see the trust signal before coding.

## 4. Expected follow-on

If this lands cleanly, the next slices can add UX, design, and product
evaluators without inventing their own confidence semantics.
