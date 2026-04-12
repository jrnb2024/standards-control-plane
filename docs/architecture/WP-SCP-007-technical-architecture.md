# TechnicalArchitecture — WP-SCP-007 Waivers and Score Model

**Work Package:** `WP-SCP-007`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Objective

Make the live audit path waiver-aware and replace duplicated evaluator-local
score math with one shared deterministic score module.

## 2. Proposed components

### `waivers.py`

Responsibilities:

- load `output/findings/waivers.json`
- validate each waiver entry
- filter active waivers for a given audit timestamp
- reject overlapping active waivers for the same `finding_id`

### `scoring.py`

Responsibilities:

- define the shared severity deductions
- define which finding statuses affect score
- calculate deterministic scores from a set of findings
- expose optional score breakdown metadata for tests and documentation

### `audit.py`

Responsibilities:

- run evaluators to get raw findings
- apply active waivers to current findings
- compute waiver-aware summary counts and per-domain scores
- include applied-waiver metadata in the structured audit result
- reopen previously waived findings automatically when the same finding is
  emitted without an active waiver in a later audit

### `findings.py`

Responsibilities:

- preserve `waived` status in history
- keep open store limited to active unwaived findings
- resolve prior `waived` findings when they are no longer emitted in the same
  audited scope

## 3. Data flow in this slice

1. CLI builds the live audit request
2. evaluators emit deterministic raw findings
3. waiver loader reads and validates `waivers.json`
4. audit assembly overlays active waivers onto matching findings
5. audit assembly computes:
   - waiver-aware findings list
   - applied waivers list
   - open severity counts plus waived count
   - per-domain scores through `scoring.py`
6. findings persistence writes:
   - history with `waived` or `resolved` statuses as applicable
   - open store with only active unwaived findings

## 4. Output rules

- missing `waivers.json` is equivalent to an empty waiver set
- invalid waiver payloads fail explicitly
- overlapping active waivers for the same finding fail explicitly
- audit results remain deterministic for the same request, findings, and waiver
  inputs
- shared scoring logic is used by evaluators and audit assembly
- the audit-result contract grows in this slice to include explicit
  `waivers_applied` output plus a waiver-aware summary count

## 5. Extension points

- authoring or approving waivers through CLI or service APIs
- accepted-debt and false-positive authoring flows
- regression-weighted score modifiers
- waiver-aware markdown report sections
