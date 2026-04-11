# Standards Control Plane — Initial Assessment

**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-11

## 1. Summary

The specification is directionally strong and addresses a real gap in the
current estate.

Today the estate has:

- clear governance doctrine
- documentation taxonomy and review expectations
- narrative conformance reviews
- narrow automation for selected conformance checks
- estate-wide documentation retrieval via `mapp-doc-agent`

What it does **not** yet have is a structured, reusable standards system that:

- advises agents before coding
- records findings in machine-readable form
- supports waivers and history cleanly
- runs targeted audits against code and artefacts
- carries lessons from one repo into another without redoing manual review

## 2. Placement Recommendation

The full system should live as a **new standalone app**.

### Why not make `mapp-doc-agent` the home

`mapp-doc-agent` is already well-shaped for retrieval:

- estate-wide documentation indexing
- hybrid search
- RAG-oriented consult support
- MCP-friendly search endpoints

That makes it a strong future integration point for consult mode, but not a
good home for:

- evaluator orchestration
- findings lifecycle
- score calculation
- waivers
- audit scheduling
- CI-facing machine-readable outputs

It should be treated as a retrieval dependency, not the core runtime.

### Why not make `control-tower` the home

`control-tower` already owns:

- governance language
- conformance framing
- service registry
- review corpus
- cross-project operational authority

That makes it the natural long-term place to **surface** standards results.
It does not make it the best place to **host** a new cross-repo scanning and
evaluation engine.

Putting the entire service inside Control Tower would:

- widen the blast radius of a critical control-plane service
- mix estate operations with repo analysis concerns
- make independent evolution of the standards system harder

The better model is:

- standalone evaluator core
- Control Tower integration for visibility and policy management later

## 3. Assessment of the Specification

### What the spec gets right

- separate `consult` and `audit` modes
- advisory-first rollout
- retrieval before reasoning
- versioned standards
- distinct evaluators by domain
- structured findings, not prose-first review output
- explicit waiver / accepted / resolved lifecycle
- confidence on inferred findings

### What needs tightening

The spec is strongest when treated as a **phased roadmap**, not as a day-one
build target.

### Strong fit for phase 1

- standards registry
- schemas
- consult contract
- audit contract
- governance evaluator
- architecture evaluator
- findings store
- markdown report generation
- CLI surface

### Needs slower treatment

- UX / IA evaluator
- design system evaluator
- product coherence evaluator

Those domains are valuable, but they are more inference-heavy and will produce
more false positives unless introduced carefully with explicit confidence and a
strong human override model.

## 4. Will it improve current governance?

Yes, materially, if implemented with scope discipline.

Current governance is strong on doctrine and review process, but much of its
state still lives in:

- markdown governance docs
- review packs
- conformance briefs
- one-off reviewer judgement

This proposal improves that by adding:

- a versioned standards registry
- reusable consult responses before coding starts
- structured findings files
- deterministic scoring rules
- explicit waiver handling
- accumulated quality memory across repos

## 5. Recommended Guardrails

1. Do not attempt all five domains in phase 1.
2. Keep the first delivery advisory-only.
3. Distinguish deterministic checks from inferred checks.
4. Make the standards registry the source of truth, not retrieved markdown.
5. Add `project overlays` early so the global rules do not become too vague.
6. Treat product coherence as advisory for a long time.

## 6. Bottom Line

The specification is sensible and worth pursuing.

The important adjustment is not to weaken it, but to sequence it properly:

- **phase 1:** governance + architecture, file-backed findings, consult +
  audit contracts, CLI
- **phase 2:** waivers, regressions, scoring hardening, retrieval integration
- **phase 3+:** UX, design, product, CI surfacing, and shared service mode

That would be a meaningful upgrade over the current governance model without
creating a false sense of precision too early.
