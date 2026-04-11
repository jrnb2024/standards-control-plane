# STRAT-SCP-001 — Standards Control Plane Phased Adoption Strategy

**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-11

## 1. Executive Summary

Build a new standalone app, `standards-control-plane`, to become the shared
consult-and-audit layer for agent-assisted software delivery across the estate.

The specification is sound, but it should be implemented as a phased programme
rather than as a single full-stack build.

### Strategic recommendation

- keep the core system independent
- start with governance and architecture only
- make outputs structured and file-backed from day one
- delay richer UX, design, and product evaluators until the findings model,
  waiver model, and retrieval path are stable
- integrate with `mapp-doc-agent` and `control-tower` later rather than making
  either one the runtime home

## 2. Current Estate Position

The estate already has strong ingredients, but they are not yet connected as a
single reusable standards system.

### What already exists

- estate governance doctrine and mandatory review flow
- documentation taxonomy and ID discipline
- cross-project conformance briefs and review reports
- selective automation for platform conformance verification
- estate-wide documentation retrieval via `mapp-doc-agent`

### Initial seed sources

The first registry and example findings should be seeded from concrete estate
material rather than invented from scratch.

- `control-tower/governance/docs/DELIVERY_GOVERNANCE_PROTOCOL.md`
- `control-tower/governance/docs/DOCUMENTATION_STANDARDS.md`
- `control-tower/docs/conformance/brief-*.md`
- `control-tower/docs/conformance/review-*.md`
- `control-tower/scripts/verify-conformance.sh`
- `mapp-doc-agent/README.md`
- `mapp-doc-agent/src/indexer.js`
- `mapp-doc-agent/src/server.js`

### What is missing

- consult-before-coding as a standard agent workflow
- a versioned standards registry
- structured findings and waivers as the system of record
- deterministic scoring that survives across reviews
- cross-project portability of lessons and open issues

## 3. Strategic Positioning

The new app should occupy the gap between documentation retrieval and control
plane governance.

### Proposed boundary

`standards-control-plane` owns:

- standards registry
- schema contracts
- consult assembly
- audit orchestration
- evaluator framework
- findings lifecycle
- report generation

`mapp-doc-agent` contributes later:

- retrieval of broader estate documentation
- retrieval of historical review documents
- evidence augmentation for consult responses

`control-tower` contributes later:

- governance source material
- conformance source material
- service registry integration
- future surfacing of reports, waivers, and subsystem status

## 4. Product Position

This is not a chatbot and not a generic reviewer prompt.

It is a structured tool with two operating modes:

- **Consult**
  - narrow, targeted, pre-implementation guidance
- **Audit**
  - post-change or periodic conformance assessment with structured findings

The system should be treated as a quality memory and advisory control layer for
agent work, not as a hard gate on day one.

## 5. Delivery Principles

1. **Structured first**
   - JSON outputs are the system of record
   - markdown reports are generated summaries
2. **Advisory first**
   - no hard CI blocking in the first phases
3. **Deterministic where possible**
   - simple signal-based checks before model-heavy inference
4. **Independent core**
   - do not make the evaluator runtime depend on the same pipeline that writes
     the code under review
5. **Explicit confidence**
   - inferred findings must carry visible confidence
6. **Project overlays**
   - global standards plus project-specific overlays, not one giant universal
     rule set

## 6. Initial Scope Choice

### Recommended pilot subsystem

Use **Returns Intelligence** as the first pilot target.

Reasons:

- it is meaningful but bounded
- it spans backend, frontend, and workflow concerns
- it already has recent conformance review material that can seed examples
- it is rich enough to test governance and architecture checks without forcing
  UX/design/product automation immediately

### Recommended initial domains

- governance
- architecture

Do not make UX, design, or product coherence blocking or score-driving in the
first cut.

## 7. Target Operating Model

## 7.1 Consult flow

1. agent identifies impacted area and files
2. agent calls `consult`
3. system retrieves:
   - active rules
   - approved patterns
   - open findings
   - relevant warnings
4. system returns structured guidance
5. agent summarizes implementation plan against that guidance
6. code is written

## 7.2 Audit flow

1. developer, CI job, or schedule invokes `audit`
2. target files / subsystem are extracted and normalized
3. domain evaluators run
4. findings are written
5. scores and summaries are generated
6. humans resolve, waive, or accept exceptions

## 7.3 Human review flow

1. findings inspected in JSON first
2. markdown summary reviewed second
3. each finding moves through explicit lifecycle states
4. waivers are visible and time-bound
5. regressions are highlighted separately from old debt

## 8. Architecture Direction

The first implementation should be CLI-first and file-backed.

### Core components

- standards registry
- schema validation
- repo extractor
- area normaliser
- retrieval module
- governance evaluator
- architecture evaluator
- findings store
- report generator
- CLI commands

### Source of truth order

1. local standards registry
2. local findings / waivers / history
3. local project artefacts
4. later: docs-agent retrieval for historical and broader estate context

### Why CLI first

- keeps runtime simple
- makes local testing straightforward
- makes CI adoption easy
- avoids premature service coupling

## 9. Phased Programme

## Phase 0 — Framing and Seed Corpus

### Objective

Make the project real and bounded before writing evaluator logic.

### Deliverables

- new repo and docs structure
- captured source specification
- placement and rollout strategy
- initial backlog
- project naming and boundaries
- seed list of source governance / conformance documents
- pilot subsystem choice

### What not to do

- no evaluator logic yet
- no model-provider lock-in
- no UI build

### Exit criteria

- repo exists with planning docs
- source material inventory is clear
- phase 1 scope is explicitly narrowed

## Phase 1 — Advisory MVP

### Objective

Stand up a real structured tool for governance and architecture consult + audit.

### Deliverables

- standards registry scaffolding
- explicit schemas
- extractor and normaliser
- consult CLI
- audit CLI
- governance evaluator
- architecture evaluator
- findings store
- markdown report generation
- sample outputs
- tests for contracts, retrieval shape, and evaluator outputs

### Constraints

- advisory only
- file-backed outputs only
- no UI dependency
- no CI gating thresholds

### Success criteria

- consult returns useful guidance for a real target area
- audit writes valid findings and report files
- findings can be tracked by area and rule
- reports are useful enough to review without extra narrative handholding

## Phase 2 — Findings Lifecycle and Retrieval Hardening

### Objective

Turn the MVP into a durable review system rather than a one-shot checker.

### Deliverables

- waivers model and expiry handling
- accepted / false-positive / resolved states
- regression detection
- finding deduplication rules
- documented deterministic scoring
- area summaries
- retrieval adapter for historical estate review material
- optional docs-agent integration for contextual consult enrichment

### Constraints

- keep standards registry as the source of truth
- do not let estate retrieval overwrite active rule selection

### Success criteria

- repeated audits produce stable findings identities
- waived debt stops distorting active scores
- regressions are highlighted separately from old debt

## Phase 3 — UX, Design, and Product Advisory Expansion

### Objective

Extend the system beyond governance and architecture while controlling trust.

### Deliverables

- UX / IA evaluator scaffolding
- design system evaluator scaffolding
- product coherence evaluator scaffolding
- confidence taxonomy for inferred checks
- evidence model for low / medium / high confidence findings
- guidance-only scoring treatment for inference-heavy domains

### Constraints

- these domains stay advisory
- confidence must be visible
- false-positive review loop must exist before expanding aggressively

### Success criteria

- useful consult guidance for front-end work
- manageable finding volumes
- confidence distribution is understandable

## Phase 4 — CI and Control Tower Integration

### Objective

Make targeted audit part of the delivery loop without turning it into
bureaucratic drag.

### Deliverables

- changed-file scoped audit mode
- CI-ready JSON and markdown outputs
- warnings on unresolved high-confidence regressions
- Control Tower surfacing plan or integration slice
- subsystem rollups suitable for broader estate visibility

### Constraints

- warnings first, not blocking
- human override remains explicit

### Success criteria

- PR workflows can run targeted audit
- teams can inspect findings without trawling repo history
- Control Tower can surface status without owning evaluator runtime

## Phase 5 — Shared Multi-Repo Service

### Objective

Promote the tool from a repo-local CLI into a shared internal capability.

### Deliverables

- service API
- project overlays
- auth/access model
- multi-repo reporting
- standards version distribution
- richer evidence adapters such as Storybook, screenshots, and component graph
  ingestion where justified

### Success criteria

- one project's improved standards can be reused by another
- consult mode becomes a standard pre-coding step
- cross-project drift is visible at the right level of abstraction

## 10. Backlog Structure

The working backlog is maintained in [`docs/BACKLOG.md`](../BACKLOG.md).

### Backlog themes

- foundation and contracts
- standards seeding
- evaluator implementation
- findings lifecycle
- retrieval integration
- CI integration
- shared service promotion

## 11. Risks and Mitigations

### Risk: markdown sludge

Mitigation:

- schemas first
- structured outputs as source of truth
- markdown only downstream of findings JSON

### Risk: over-ambitious phase 1

Mitigation:

- hard-limit initial domains to governance and architecture
- no UI build in phase 1
- no hard gating in phase 1

### Risk: false positives erode trust

Mitigation:

- deterministic checks first
- explicit confidence
- waiver / false-positive workflow in phase 2

### Risk: app becomes a dumping ground for every governance concern

Mitigation:

- keep project overlays explicit
- keep runtime boundary independent
- do not absorb Control Tower responsibilities that belong elsewhere

## 12. Measures of Success

### Early measures

- consult used before implementation in at least one real workflow
- audit generates stable findings on a pilot subsystem
- findings are specific enough to act on
- review volume is manageable

### Later measures

- reduced repeated review comments across repos
- fewer architecture and governance regressions reaching late review
- improved reuse of standards and patterns across projects

## 13. Open Decisions

These decisions should remain open until phase 1 framing is complete:

- TypeScript vs Python for the core implementation
- local-only CLI first vs packaged CLI
- precise scoring weights
- storage backend beyond files
- when docs-agent integration becomes worth the dependency
- when Control Tower surfacing becomes worth the coupling

## 14. Immediate Recommendation

Approve the project as a new standalone app and execute:

1. phase 0 framing
2. phase 1 advisory MVP
3. phase 2 findings lifecycle

Do not attempt the full five-domain vision in one build pass.
