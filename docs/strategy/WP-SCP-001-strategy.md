# StrategyDoc — WP-SCP-001 Registry and Consult Retrieval

**Work Package:** `WP-SCP-001`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-11

## 1. Why this slice first

The scaffold already has schemas, seed standards, and a CLI shape, but it still
returns placeholder consult output. The smallest useful next step is to make
consult real before expanding audit.

That is the right sequence because:

- consult is the entry point for pre-coding governance
- retrieval is simpler and easier to validate than evaluators
- the registry shape needs to settle before audit logic builds on it

## 2. Options considered

### Option A — implement evaluators next

Rejected for now.

This would leave the registry and consult path half-real while increasing
complexity. Evaluators need stable inputs; the retrieval and registry layer is
that input.

### Option B — make consult real first

Accepted.

This keeps the slice narrow and creates the first genuinely useful path for
implementation agents.

## 3. Chosen approach

- keep rule and pattern metadata structured in index JSON
- keep markdown files as human reference material
- load the registry through a dedicated loader module
- include a minimal read-only findings store path for consult
- add a consult service that:
  - loads requested domains
  - selects active rules and patterns
  - reads open findings
  - returns a schema-valid consult response

## 4. Why not parse markdown metadata first

Markdown metadata parsing is viable later, but it adds parsing choices and
failure modes before the registry contract has stabilised.

For this slice, structured JSON indexes are the more reliable source of truth.

## 4.1 Registry governance for this slice

The registry must remain governable.

For WP-SCP-001 that means:

- top-level registry and domain indexes carry explicit version/status metadata
- consult retrieval reads structured index data, not ad hoc markdown parsing
- any change to active rule metadata or pattern metadata is reviewable in git as
  structured data
- markdown files remain the human explanation layer, not the only machine
  contract

## 5. Success condition

The work package is successful when a real consult request produces a real,
deterministic, schema-valid answer from local standards and findings data,
without evaluator logic or model dependence.
