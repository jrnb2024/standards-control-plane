---
adjudication_status: accepted
accepted_as: GOV-006
enforcement_policy: SCP-R-014
decision_ref: D-067
accepted_at: 2026-07-12
accepted_note: adjudicated into standards/governance/rules/GOV-006-no-shortcuts-serving-source-allowlist.md + index.json + policies/SCP-R-014.rego (warn-baseline, ships dormant/vacuous-pass). Live enforcement today = the conformance-tcb repo gate (policy/scp_r_join_001.rego); SCP-plane firing gated on FUP-D067-CONFORMANCE-TCB-MATERIALISER-001.
expected_review_date: null
queued_at: 2026-07-12T10:07:43Z
---
> NOTE: WP-SCP-022-proposal-queue adjudication workflow is not yet live;
> proposals queue until adjudication ships. Status updates via
> GitHub issue on this branch (proposals/PROP-010). See
> docs/plans/WP-SCP-022-implementation-programme-plan.md §12.

<!-- proposal_metadata: {"affected_repos":["Recommender","mapp-pim","kg-demo-storefront","fashion-ontology-service","kg-demo-framework"],"caller_id":"stdio:99776:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server","mcp_origin":true,"proposal_hash":"d9e6d35760c84b9b529d132b4916f9eb4e745650380c894b5d7ce7c2e6ab0db8","rule_id":"SCP-R-JOIN-001","signing_key_id":"428dfee16bc954ad"} -->

# PROP-010: SCP-R-JOIN-001 — No-shortcuts (allowlist) on the canonical serving path

## Proposal Envelope
- mcp_origin: true
- caller_id: stdio:99776:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server
- signing_key_id: 428dfee16bc954ad

## Affected Repositories
- Recommender
- mapp-pim
- kg-demo-storefront
- fashion-ontology-service
- kg-demo-framework

## Rule Context
SCP-R-JOIN-001

## Proposal Body
PROPOSED DENY-PLANE RULE (Rego SCP-R-*, a required policy-check gate — NOT the advisory SVC-* plane).

Provenance: Canonical Conformance Harness + Phase-0 charter v2 (~/Projects/PHASE-0-CHARTER-conformance-lite-v2-2026-07-12.md §5), hardened across two adversarial red-team rounds. Draft for operator review — do not self-approve.

INTENT: the canonical serving path may read ONLY sanctioned canonical sources; a baked-fixture/hardcode read is a lie (it makes a heuristic-seeded or fixture-served value byte-indistinguishable from a real one).

DENY when, on a serving-path file (roots DERIVED from the dataflow-into-the-served-index — includes services/, scripts/ e.g. rebuild_opensearch_index.py, ingest/, reindex entrypoints — NOT a hand-enumerated dir list):
 (a) it reads a data source NOT on `conformance/sanctioned-sources.yaml` (the allowlist of canonical stores: PIM projections, ontology service, the signed index); OR
 (b) a new top-level dir under a serving repo is unclassified (neither scanned-serving-path nor explicitly waived); OR
 (c) serving code constructs a data filename dynamically (defeats literal-pattern scanning).

WHY ALLOWLIST NOT DENYLIST: the harness's current 11-pattern denylist (banned.json) is blind to any new baked artifact under a new name and to un-rooted dirs (round-2 found rebuild_opensearch_index.py — the real index builder — invisible). 'What may I read' is a closed set; 'what I may not' is infinite.

RATCHET: `sanctioned-sources.yaml` and the scan roots are shrink-only, checked against append-only history; net growth needs a signed, expiring SCP waiver.

EVIDENCE ARTIFACTS (in the TCB): sanctioned-sources.yaml, the dataflow-derived roots manifest.
WAIVER: signed, expiring, per-source; a waiver may NEVER turn a capability cell green.
