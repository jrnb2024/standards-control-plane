---
adjudication_status: queued_no_adjudicator
expected_review_date: null
queued_at: 2026-09-04T23:51:25Z
---
> NOTE: WP-SCP-022-proposal-queue adjudication workflow is not yet live;
> proposals queue until adjudication ships. Status updates via
> GitHub issue on this branch (proposals/PROP-029). See
> docs/plans/WP-SCP-022-implementation-programme-plan.md §12.

<!-- proposal_metadata: {"affected_repos":["jrnb2024/adaptive-label","jrnb2024/fashion-ontology-service","jrnb2024/control-tower"],"caller_id":"stdio:85639:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server","mcp_origin":true,"proposal_hash":"3316d02ee9975263ca404946b4d3bd85967bf329aed4b8b6d8aa9c2c3e72e682","rule_id":"ARCH-006","signing_key_id":"428dfee16bc954ad"} -->

# PROP-029: ARCH-006 deviation: adaptive-label consumes the FTL taxonomy directly (content-hash pinned) until fashion-ontology-service becomes the FTL router

## Proposal Envelope
- mcp_origin: true
- caller_id: stdio:85639:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server
- signing_key_id: 428dfee16bc954ad

## Affected Repositories
- jrnb2024/adaptive-label
- jrnb2024/fashion-ontology-service
- jrnb2024/control-tower

## Rule Context
ARCH-006

## Proposal Body
## Context
The Adaptive Label (new repo `jrnb2024/adaptive-label`, clean rebuild of the FLA labelling pipeline, programme go 2026-09-04) labels products against the FTL taxonomy (`ftl.labs.mapp.com`, the Mapp Labs system of record for categories / attribute instances / values). The operator's direction is to use FTL as-is, keyed by FTL ids, pinned by content hash, with a diff-gate governing taxonomy updates.

## Deviation
ARCH-006 names `fashion-ontology-service` as the one canonical ontology authority and requires consumers to declare an `ontology_contract` pointing at it. `adaptive-label` instead declares `ontology_contract: {authority: ftl, canonical_version: pinned-by-content-hash, fallback: none}` in its `services.yml` and reads FTL directly through its own adapter (`adaptive_label.ontology`). It does NOT embed `ontology_complete.yaml` / `value_mappings.json` and does NOT re-implement a local Ontology/Canonicalizer — the rule's stated mischief. The pin is a cache of FTL, never authored locally; the diff-gate is the only writer.

## Proposal
1. Recognise FTL as an admissible upstream authority for `ontology_contract.authority` (values: `fashion-ontology-service` | `ftl`), with `canonical_version` allowed to be a content hash when the authority is FTL.
2. Plan: fashion-ontology-service becomes the FTL router (pull → pin → publish) in a later session; when it does, `adaptive-label` re-points its contract to it with no code change (the adapter reads a pinned snapshot either way).
3. Until then, a scoped waiver for `jrnb2024/adaptive-label` (rule ARCH-006, warn-baseline / DORMANT today).

## Evidence
- Design: `~/Projects/ADAPTIVE-LABEL-DESIGN-2026-09-04/The-Adaptive-Label.docx` §2 (adapter), §13 Decision 14.
- Decisions record: `adaptive-label/docs/decisions/2026-09-05-programme-decisions.md`.
- FTL structure measured 2026-09-04: 425 categories (346 live concrete), 2,102 attribute instances, 29,111 values, 6,195 mappings.

Filed by the orchestrator during the overnight rebuild; operator ruling requested in the morning.
