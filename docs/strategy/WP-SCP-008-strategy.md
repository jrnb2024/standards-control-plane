# Strategy — WP-SCP-008 Review Evidence Hardening and Pilot Tuning

**Work Package:** `WP-SCP-008`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Strategy

Use one small structured metadata block inside review markdown as the shared
source for both:

- governance traceability checks
- consult-time historical review retrieval

That lets the system reduce one of its weaker trust points without inventing a
separate storage layer or adding a dependency-heavy parser.

## 2. Why this slice now

The current governance evaluator still treats review evidence as a
path-plus-text heuristic:

- area markers anywhere in the file
- finding-id-like strings anywhere in the file
- status-like strings anywhere in the file

That is good enough for the first slice, but it is too permissive to sustain
trust.

At the same time, historical review retrieval is still missing even though the
repo already carries review packs that could seed it.

## 3. Delivery shape

### 3.1 Embedded structured metadata

Each eligible `review_findings.md` file should be able to carry one fenced JSON
block under a dedicated info string such as `scp-review-evidence`.

The block should stay small and explicit:

- `review_id`
- `area_id`
- `reviewed_at`
- `summary`
- `reviewed_paths`
- `findings`

### 3.2 One parser, two consumers

The same parser should power:

- governance review-evidence validation
- consult-time historical review selection

That avoids drifting heuristics.

### 3.3 Bounded migration

Migrate the review files that matter for current trust and retrieval:

- the seeded Returns pilot review file
- the repo-local review packs that should act as historical sources for this
  project, starting at `WP-SCP-003`

Legacy files without the structured block should be skipped by historical
retrieval rather than breaking unrelated flows.

### 3.4 Explicit consult contract change

The consult-response contract should grow explicitly in this slice with a
bounded `historical_reviews` field rather than hiding historical review
references inside generic guidance text.

## 4. Pilot tuning goal

The tuning goal for this slice is narrow:

- reduce false confidence from loose review-evidence matching
- document the change and the remaining residual risk

This is not yet the full false-positive loop.

## 5. Expected follow-on

If this lands cleanly, the next slice can define confidence classes before the
broader inference-heavy domains arrive.
