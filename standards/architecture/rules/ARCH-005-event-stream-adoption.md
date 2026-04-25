# ARCH-005 — Estate Services Must Use the Canonical Event Stream

**Domain:** architecture
**Version:** 1.0.0
**Status:** active
**Severity default:** high
**Supersedes (in part):** ARCH-004 case-by-case "be consistent" guidance is replaced by the specific canonical pattern below for cross-app eventing. ARCH-004 still governs intra-service async patterns (background workers, retries, backoff) outside the event-stream surface.

The Mapp Fashion estate runs **one event stream**. Every service that publishes
or consumes events between estate apps does so through the canonical broker,
canonical topic-naming, canonical envelope, and canonical SDK described below.

The approved set is **closed**. Custom brokers, custom topic naming, custom
envelope shapes, and custom SDKs are not permitted; new variants require a
standards change.

## Why this rule exists

The 2026-04-25 estate event-streaming audit
(`control-tower/docs/strategy/STRAT-INFRA-EVENTS-001-estate-event-bus-consolidation.md`)
recorded **two parallel event installations** with no shared topology:

- **Ecosystem A** — `mapp-pim`'s self-hosted Redpanda, unprefixed topic names
  (`product-event`, `transform-event`, …), bespoke dual Go + Python event-bus
  libraries (`pkg/events`, `pylib/mf_platform/events.py`).
- **Ecosystem B** — Control Tower's Apache Kafka, namespaced topic names
  (`mapp.{domain}.{entity}.{event_type}`), `ct-events` Python SDK 0.1.0
  vendored across multiple repos but unused at every site.

Of the planned cross-app integrations (PIM → Recommender embeddings ingest,
PIM → FLA ontology drift, RI → BDS returns scoring, etc.), **one was working**
at audit time: BDS consuming from CT's Kafka. Every other link was stubbed,
deferred (D-037), or abandoned (Market Feed deprecation, D-038).

The fragmentation has measurable cost: schema drift between the duplicated
PIM Go/Python event-bus implementations is a known risk
(`mapp-pim/pylib/tests/test_events.py` exists specifically to keep them in
lockstep); cross-app integrations sit indefinitely deferred because there's
no shared spine to publish to. ARCH-005 names the spine.

## Canonical surface

### Broker

The estate runs **one broker** at any time:

| Mode | Broker | Use |
|------|--------|-----|
| **Pre-launch (current)** | Self-hosted Apache Kafka (the `control-tower-ct-kafka-1` container, or whatever the host instance moves to during environment migration) | Single broker for dev + the estate's "shared dev / staging" tier |
| **Post-launch (trigger: first real customer with an SLA)** | Managed Kafka (Confluent Cloud / AWS MSK Serverless / Aiven, procurement-driven choice) | Production tier |

Mode transition is a config change (broker URL + ACLs), not a re-architecture.
Both modes implement the same Kafka API; the SDK is broker-agnostic.

The pre-launch broker MUST run a single-tenant instance per environment.
Cross-environment event flow is not part of this rule — D-017 (Kafka env
isolation) governs that.

### Topic naming

Topic names follow the canonical four-part pattern:

```
mapp.{domain}.{entity}.{event_type}
```

- `domain` — bounded context (e.g. `catalog`, `returns`, `feed`, `iam`,
  `ontology`, `enrichment`, `agents`).
- `entity` — primary entity emitting the event (e.g. `product`, `return`,
  `user`, `ontology`, `embeddings`).
- `event_type` — past-tense verb describing what happened (e.g. `created`,
  `updated`, `deleted`, `imported`, `scored`, `published`).

Examples (canonical):

- `mapp.catalog.product.created`
- `mapp.catalog.product.updated`
- `mapp.catalog.product.embeddings.computed`
- `mapp.returns.return.scored`
- `mapp.feed.sync.completed`
- `mapp.ontology.version.updated`
- `mapp.iam.user.created`

Dead-letter topics use suffix `.dlq`, retention 7 days:

- `mapp.catalog.product.created.dlq`

Unprefixed topic names (PIM Ecosystem A: `product-event`, `transform-event`,
…) are non-conformant and must be renamed during the consolidation.

### Envelope

All events use the CloudEvents-flavoured envelope:

```jsonc
{
  "event_id": "uuid",                  // unique per event
  "event_type": "mapp.catalog.product.created",  // matches the topic's leaf
  "schema_version": 1,                 // integer, additive-only evolution
  "source": "service-name",            // e.g. "pim-product-core"
  "org_id": "tenant_id",
  "brand_id": "brand_id | null",       // optional
  "actor_id": "user_id | agent_id | service",
  "actor_type": "user | agent | service | system",
  "entity_type": "product | return | …",
  "entity_id": "entity_uuid",
  "timestamp": "RFC3339",
  "correlation_id": "string | null",   // for cross-event tracing
  "payload": { /* event-type-specific */ }
}
```

Schemas evolve **additively only** — new versions may add optional fields but
must not remove or rename existing fields. Breaking changes require a new
`schema_version` AND a new event_type AND coordinated consumer migration.

Schemas live in `control-tower/packages/ct-events-schemas/` and are the single
source of truth. Per-service local schema files (e.g.
`mapp-pim/api/schemas/events/`) are non-conformant and must be deleted during
consolidation.

### SDK

Per-language canonical SDKs (the closed set):

| Language | Package | Source | Status |
|----------|---------|--------|--------|
| Python | `ct-events` | `control-tower/packages/ct-events-python/` | 0.1.0 vendored, ready to publish to internal registry; production-ready API |
| Go | `ct-events-go` | (planned per Recommender ADR-005, lands in Recommender first then transplanted to CT) | Not yet authored |
| TypeScript | `ct-events-ts` | (only required if a Node consumer needs it) | Not yet authored; defer until first concrete consumer |

The SDK is the **only** approved client library. Bespoke wrappers around
`confluent-kafka`, `aiokafka`, `kafka-python`, `segmentio/kafka-go`, `kafkajs`,
`node-rdkafka`, `rdkafka`, etc. are non-conformant. Existing bespoke
implementations must be retired during consolidation:

- `mapp-pim/pkg/events/` (Go) — retire.
- `mapp-pim/pylib/mf_platform/events.py` — retire.
- `mapp-pim/services/event-bus/main.go` (HTTP stub) — retire.
- `control-tower/src/control_tower/events/producer.py` (`ConfluentEventProducer`) —
  refactor to use the SDK rather than calling `confluent-kafka` directly.
- `brand-dna-spectrogram/backend/events/kafka_consumers.py` (the only working
  consumer in the estate) — keep its semantics; rebase on the published SDK.

### CT Event Gateway

For producers that cannot link the SDK directly (browser-side code, third-party
webhooks, lightweight scripts, languages without an SDK), Control Tower
exposes a thin HTTP-to-Kafka gateway at `POST /api/v1/events/publish`. The
endpoint validates the envelope + schema, authenticates the caller (per
SVC-003 auth modes), and produces to the canonical broker.

Service-to-service producers MUST use the SDK directly, not the Event Gateway.
The gateway is for callers that demonstrably cannot link the SDK.

### Schema Registry

Resolved schemas are served by Confluent Schema Registry (or a self-hosted
JSON Schema equivalent). The SDK fetches + caches schemas at runtime; CI
conformance checks (see "Conformance" below) hit the registry to validate the
calling service's pinned schema versions.

## Adoption triggers

A service that produces or consumes cross-app events MUST adopt this rule
when any of:

- **T1 — first cross-app integration.** The service starts publishing to or
  subscribing from a topic consumed by another estate service.
- **T2 — net-new event flow.** A new event_type is introduced.
- **T3 — breaking schema change.** Any modification that's not additive forces
  re-registration + consumer coordination.
- **T4 — deprecation of a legacy bespoke broker / library.** Existing PIM
  Ecosystem A code is the immediate trigger; bespoke producer code at any
  service is a long-tail trigger.

A service that is NOT yet a producer or consumer (e.g. mapp-size-allocation,
living-canvas, mapp-visual-shopping at audit time) is not bound by ARCH-005
until it crosses one of the triggers. The unused `KAFKA_BOOTSTRAP_SERVERS` env
in `mapp-returns-intelligence/docker-compose.yml` is non-binding until RI
actually wires a consumer.

## Required declaration

Each service registered in `services.yml` that produces or consumes events
MUST declare an `event_contract` block under its `runtime_contract`:

```yaml
event_contract:
  produces:
    - topic: mapp.catalog.product.created
      schema_version: 1
      source: pim-product-core
    - topic: mapp.catalog.product.updated
      schema_version: 1
  consumes:
    - topic: mapp.catalog.product.embeddings.computed
      schema_version: 1
      consumer_group: recommender-embeddings-ingest
  sdk:
    language: python
    package: ct-events
    version: ">=0.2.0"
  broker_target: ct-kafka  # canonical broker alias; resolved at deploy time
```

Services that don't produce or consume cross-app events omit the block (no
declaration ≡ "this service does not participate in the estate event stream").

The `event_contract` block is enforced by the service-lifecycle evaluator,
not by the runtime-contract schema's `required` list. Same pattern as SVC-003
auth_contract enforcement.

## Conformance

CI checks (run by SCP evaluator):

1. **Topic-naming conformance** — declared topics match `mapp.{domain}.{entity}.{event_type}`.
2. **Envelope conformance** — sample envelopes (committed in fixtures) validate against the canonical Pydantic model exposed by `ct-events-schemas`.
3. **SDK pin conformance** — service's `requirements.txt` / `go.mod` / `package.json` declares the canonical SDK at the required minimum version.
4. **No bespoke client** — service's source tree contains no direct imports of `confluent-kafka`, `aiokafka`, `kafka-python`, `segmentio/kafka-go`, `kafkajs`, `node-rdkafka`, or `rdkafka`. Only the SDK is permitted as the Kafka client.
5. **No bespoke envelope** — service does not define its own event envelope schema; consumes only from `ct-events-schemas`.

Failure of any check at PR time blocks merge. Pre-existing non-conformance is
recorded as a per-service migration waiver with an explicit close date (see
"Waivers" below) — same pattern as SVC-003's `mode.bearer_legacy` deprecation.

## Waivers

Pre-existing services with bespoke implementations may request a time-bound
waiver during consolidation:

- **Waiver shape:** declared in `services.yml` under
  `runtime_contract.event_contract.waivers[]`. Each waiver names the
  non-conforming surface (e.g. `bespoke_client: pkg/events/`), the reason
  (e.g. `"PIM consolidation in flight per
  STRAT-INFRA-EVENTS-001 Phase 2"`), and an explicit `close_date`.
- **Default close date:** 90 days from this rule's `Status: active` date.
- **Renewal:** allowed once with explicit governance review; second renewal
  requires elevated SCP review.
- **Expiry without close:** SCP evaluator escalates to severity `critical` on
  the next CI run after `close_date` passes.

Waivers exist to make the rule shippable; they're not an indefinite escape
hatch.

## Cross-references

- **STRAT-INFRA-EVENTS-001** —
  `control-tower/docs/strategy/STRAT-INFRA-EVENTS-001-estate-event-bus-consolidation.md`.
  This rule is the SCP-side counterpart of that strategy doc.
- **D-037** — supersedes the "DEFERRED pending SCP rule" status. With this
  rule active, D-037 transitions from DEFERRED to ENACTED via the canonical
  SDK adoption pathway.
- **D-038** — Market Feed event-stream successor. Market Feed is deprecated
  (2026-04-24); D-038 closes as `obsolete`. No successor needed; the
  canonical estate stream is the successor.
- **ARCH-004** — Generic async-pattern consistency. ARCH-005 supersedes
  ARCH-004 specifically for cross-app eventing; ARCH-004 still governs
  intra-service async patterns.
- **SVC-003** — Auth-contract rule. Producers calling the CT Event Gateway
  MUST authenticate via an SVC-003-approved mode. Service-to-service Kafka
  producers authenticate via broker ACLs (per-tenant credentials from CT
  Vault).
- **D-017** — Kafka env isolation. ARCH-005's "one broker" applies
  per-environment; D-017 governs cross-env flow (which is currently null).
- **Recommender ADR-005** — `ct-events-go` SDK design. Will be the Go SDK
  authority once authored.
- **Phase-3 ct-events planning prompt** —
  `control-tower/docs/handoffs/phase-3-ct-events-planning-prompt.md`. The
  envelope shape, topic-naming convention, and Event Gateway endpoint were
  drafted there; this rule promotes them from "planning prompt" to
  "canonical".
- **Market Feed FREEZE_DIRECTIVE_SVC003.md** — historical only (Market Feed
  deprecated). The unfreeze trigger language ("ct-events SDK published +
  migration plan drafted") is the most explicit prior statement of the
  consolidation gate condition; this rule's `Status: active` is the
  fulfilment of that condition.
