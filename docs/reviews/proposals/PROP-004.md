---
adjudication_status: accepted
accepted_as: ARCH-006
enforcement_policy: SCP-R-013
decision_ref: D-062
accepted_at: 2026-07-02
accepted_note: adjudicated into standards/architecture/rules/ARCH-006-ontology-canonical-consumption.md + index.json + policies/SCP-R-013.rego (warn-baseline, ships dormant/vacuous-pass); live via consult_rules. WP-SCP-037 §1a.
expected_review_date: null
queued_at: 2026-07-02T22:10:14Z
---
> NOTE: WP-SCP-022-proposal-queue adjudication workflow is not yet live;
> proposals queue until adjudication ships. Status updates via
> GitHub issue on this branch (proposals/PROP-004). See
> docs/plans/WP-SCP-022-implementation-programme-plan.md §12.

<!-- proposal_metadata: {"affected_repos":["fashion-ontology-service","mapp-pim","fashion-labelling-agent","mf-intent-os","mapp-visual-shopping","amplience-kg-mvp","kg-studio"],"caller_id":"stdio:11666:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server","mcp_origin":true,"proposal_hash":"07ee4c4d22915f241c3db0112e230c277cf669ca2b2b0ead8e8d5f43be0579a3","rule_id":"ARCH-006","signing_key_id":"428dfee16bc954ad"} -->

# PROP-004: ARCH-006 ontology-canonical-consumption — consumers link to fashion-ontology-service, never embed a divergent ontology copy

## Proposal Envelope
- mcp_origin: true
- caller_id: stdio:11666:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server
- signing_key_id: 428dfee16bc954ad

## Affected Repositories
- fashion-ontology-service
- mapp-pim
- fashion-labelling-agent
- mf-intent-os
- mapp-visual-shopping
- amplience-kg-mvp
- kg-studio

## Rule Context
ARCH-006

## Proposal Body
## Principle (D-058 LINKAGE-not-VALUES)

There is ONE canonical fashion ontology authority: **fashion-ontology-service (FOS)** (FastAPI :8020; `fashion-ontology-service/docs/ONTOLOGY.md`; ratified canonical by CT `SEX-001`). FLA *authors* the ontology data; FOS *serves* it; every other app (PIM, Recommender, Outfit engine, Brand-DNA, Visual-Shopping, demo storefronts) is a **CONSUMER** that must CALL FOS, not embed a divergent copy or re-implement canonicalization. Modeled on ARCH-005 (canonical event stream) + the auth-canonical family (SCP-R-009/010/011): the domain authority owns the canonical; SCP gates the LINKAGE (does the consumer reference + pin the canonical?), never the VALUES.

## The contract

A consumer declares an `ontology_contract` block under its `services.yml` `runtime_contract`:
- `canonical_service: fashion-ontology-service` (exact)
- `canonical_version:` a pinned version
- `endpoints:` the FOS endpoints it calls
- `fallback:` MUST NOT be a local ontology copy (a stale local YAML defeats the point)
- `cache_ttl:` ≤ 7d

## Enforcement (structural, warn-baseline; ships DORMANT/vacuous-pass until the companion materialiser wires input — same dormancy pattern as SCP-R-009)

Signals (deny-class findings, rendered ::warning:: via WARN_BASELINE):
1. `ontology_contract` block absent from a consumer's services.yml.
2. `canonical_service` != `fashion-ontology-service`.
3. Embedded canonical ontology file present (`ontology_complete.yaml` / `value_mappings.json`).
4. Local ontology re-implementation (`Ontology` / `OntologyLoader` / `Canonicalizer` class).
5. `fallback` resolves to a local ontology copy.

ADVISORY until FOS publishes a version manifest: version-pin conformance, endpoint/deprecation/perf.

## The authoring-source carve-out (bypass guard)

FLA legitimately embeds `ontology_complete.yaml` (it AUTHORS the data). Signals 3/4 must NOT DENY the authoring source — BUT the exemption is **SCP-controlled**: the materialiser injects `input.ontology_authoring_allowlist` (FOS + FLA identifiers, SCP-owned). A repo is exempt ONLY if it is on that allowlist. An adopter self-asserting `role: authoring-source` in its own services.yml gets NO exemption. Confirm at adjudication.

## Enforcement policy ID

Standards-domain rule ID = **ARCH-006** (architecture domain, index + prose). Enforcement policy = **policies/SCP-R-013.rego** (the CI workflow loads only SCP-R-*.rego; scorecard filters SCP-R-[0-9]+). SCP-R-013's internal rule_id string = "ARCH-006" so findings render under the standard. Add SCP-R-013 to BOTH WARN_BASELINE_RULES sites in policy-check.yml in the same PR.
