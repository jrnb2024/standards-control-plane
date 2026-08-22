# ARCH-006 — Consumers Link to the Canonical Ontology, Never Embed a Divergent Copy

**Domain:** architecture
**Version:** 1.0.0
**Status:** active
**Severity default:** high
**Enforcement policy:** `policies/SCP-R-013.rego` (the standards-domain ID is ARCH-006; the CI enforcement ID is SCP-R-013 — the workflow loads only `SCP-R-*.rego`).

> **Enforcement status: DORMANT.** The `SCP-R-013` structural checks ship
> warn-baseline but VACUOUSLY PASS until the companion workflow materialiser
> injects their input (`FUP-WP-SCP-037-ARCH-006-MATERIALISER-001`) — the same
> dormancy pattern SCP-R-009 shipped under. This rule is consult-discoverable and
> gate-registered now; it does not FIRE on adopter PRs until the materialiser
> lands. Do not treat it as live enforcement until then.

The Mapp Fashion estate has **one canonical fashion ontology authority**:
**fashion-ontology-service (FOS)** (FastAPI, `:8020`; `fashion-ontology.brokapps.ai`
/ `ontology-dev.brokapps.ai`; canonical description in
`fashion-ontology-service/docs/ONTOLOGY.md`; ratified as the canonical by
Control Tower `SEX-001`). Every app that uses the ontology is a **CONSUMER** that
LINKS to FOS. No consumer embeds a divergent copy of the ontology or
re-implements canonicalization.

This is the **D-058 LINKAGE-not-VALUES** discipline: the domain authority (FOS)
owns the canonical VALUES; SCP gates the LINKAGE (does the consumer reference +
pin the canonical, and keep no divergent local copy?), never the values
themselves. It is the ontology counterpart of ARCH-005 (canonical event stream)
and the auth-canonical family (SCP-R-009/010/011).

## Authoring vs consuming

- **FLA authors** the ontology data. `fashion-labelling-agent` legitimately holds
  the source (`labelling_agent/ontology_complete.yaml`, `labelling_agent/ontology.py`).
- **FOS serves** it — the single runtime authority every consumer calls.
- **Everyone else consumes** — PIM, Recommender, the Outfit engine, Brand-DNA,
  Visual-Shopping, demo storefronts. A consumer CALLS FOS; it does not vendor the
  ontology file or re-derive canonicalization locally.

The authoring source is exempt from the no-embedded-copy signals — but ONLY
because it is on the **SCP-owned authoring allowlist** (`fashion-ontology-service`,
`fashion-labelling-agent`). A repo does NOT exempt itself by writing
`role: authoring-source` into its own `services.yml` — the exemption is
SCP-controlled, not self-asserted (the bypass guard).

## Required declaration

A consumer declares an `ontology_contract` block under its `services.yml`
`runtime_contract`:

```yaml
ontology_contract:
  canonical_service: fashion-ontology-service   # exact; the one authority
  canonical_version: "1.2.0"                     # a pinned version
  endpoints:                                     # the FOS endpoints it calls
    - /api/v1/value-mappings
    - /api/v1/canonicalize
  fallback: fail-request                         # MUST NOT be a local ontology copy
  cache_ttl: 24h                                 # <= 7d
```

A repo that does not consume the ontology omits the block (no declaration ≡ "this
service does not participate in the estate ontology"). Same enforcement pattern as
ARCH-005's `event_contract` and SVC-003's `auth_contract`: enforced by the
evaluator, not by the runtime-contract schema's `required` list.

## Signals (non-conformant)

The enforcement policy (`SCP-R-013`) emits a finding for each of:

1. **Missing linkage** — a repo the workflow identifies as an ontology consumer
   declares no `ontology_contract`.
2. **Wrong authority** — `ontology_contract.canonical_service` is anything other
   than `fashion-ontology-service`.
3. **Embedded canonical copy** — a vendored `ontology_complete.yaml` /
   `value_mappings.json` in a non-authoring (non-allowlisted) repo.
4. **Local re-implementation** — a local `Ontology` / `OntologyLoader` /
   `Canonicalizer` class in a non-authoring repo.
5. **Local-copy fallback** — `ontology_contract.fallback` resolves to a local
   ontology copy (a stale local YAML defeats the canonical).

Signals 1–5 are structural and enforceable without FOS publishing anything (they
gate LINKAGE, not values). They ship warn-baseline: findings render `::warning::`
and never block a merge, pending a future deny-promotion decision after
observation.

**Advisory until FOS publishes a version manifest:** version-pin conformance
(is the pinned `canonical_version` current / not deprecated?), endpoint existence,
and per-call performance guidance. These need FOS to publish a signed version
manifest (the D-058 4-artefact canonical); until then they are prose guidance in
`fashion-ontology-service/docs/ONTOLOGY.md`, not enforced.

## Adoption triggers

A service MUST adopt this rule when any of:

- **T1** — it starts calling FOS (first ontology consumption).
- **T2** — it introduces new ontology-dependent behaviour (labelling, faceting,
  canonicalization, value-mapping).
- **T3** — it currently embeds an ontology copy or a local ontology class
  (immediate remediation trigger — replace with a FOS call + `ontology_contract`).

## Waivers

Pre-existing consumers with an embedded copy may request a time-bound migration
waiver in `services.yml` under `runtime_contract.ontology_contract.waivers[]`
(surface + reason + `close_date`), mirroring ARCH-005's consolidation waivers.
Waivers make the rule shippable; they are not an indefinite escape hatch.
`fashion-labelling-agent` needs NO waiver — it is the allowlisted authoring source.

## Cross-references

- **D-058** — SCP canonical-conformance strategy (LINKAGE-not-VALUES). This is the
  first ontology-domain rule under it.
- **ARCH-005** — canonical event stream; the structural template this rule mirrors.
- **SCP-R-009/010/011** — auth-canonical family; the enforced-Rego +
  input-materialisation template `SCP-R-013` mirrors (including warn-baseline
  dormancy).
- **`reference_estate_canonical_sources.md`** — the estate canonical map
  (ontology → FOS).
- **`FUP-WP-SCP-037-ARCH-006-MATERIALISER-001`** — the companion workflow
  materialiser that activates the (currently dormant) structural checks + injects
  the SCP-owned authoring allowlist.
