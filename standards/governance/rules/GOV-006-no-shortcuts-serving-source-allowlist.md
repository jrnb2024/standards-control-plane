# GOV-006 — The Serving Path Reads Only Sanctioned Sources (No Shortcuts)

**Domain:** governance
**Version:** 1.0.0
**Status:** active
**Severity default:** high
**Enforcement policy:** `policies/SCP-R-014.rego` (the standards-domain ID is GOV-006; the CI enforcement ID is SCP-R-014 — the workflow loads only `SCP-R-*.rego`).

> **Enforcement status: DORMANT on the SCP plane.** The `SCP-R-014` structural
> checks ship warn-baseline but VACUOUSLY PASS until the companion workflow
> materialiser injects their input (`FUP-D067-CONFORMANCE-TCB-MATERIALISER-001`) —
> the same dormancy pattern SCP-R-009 / SCP-R-013 shipped under. **LIVE enforcement
> today is the separate `conformance-tcb` repo gate** (`jrnb2024/conformance-tcb`,
> `policy/scp_r_join_001.rego`), which is branch-protected and a required check
> there. This rule is consult-discoverable and gate-registered now; it does not
> FIRE on adopter PRs until the materialiser lands. Do not treat SCP-plane
> enforcement as live until then.

## Intent

A governed app's **serving path** — the code that answers a live request from the
canonical index — may read **only** sources that are on the sanctioned-sources
allowlist. This is the anti-shortcut discipline: the most common way a demo
"goes green" dishonestly is by quietly reading a hand-curated fixture
(`fixtures/catalog_enriched_v3.json`) on the serving path instead of the real
canonical index.

This is the **D-058 LINKAGE-not-VALUES** discipline: SCP never reads the VALUES a
source serves, only WHETHER the reader / directory / filename is sanctioned.

## The three signals

1. **Unsanctioned serving read** — a serving-path read of a source that is not on
   the `sanctioned-sources` allowlist.
2. **Unclassified serving dir** — a new serving directory must be classified into
   the allowlist before it may read (the blind-dir check).
3. **Dynamic serving filename** — a serving filename constructed at runtime defeats
   static allowlist verification.

The allowlist **ratchet is shrink-only**: it may lose entries but not gain them
without review. (The ratchet is enforced by the harness diffing the sanctioned
list across commits, not by this single-input policy.)

## Input contract (materialiser-injected; dormant until then)

`SCP-R-014` reads `input.serving_allowlist_scan`, an envelope the materialiser
injects from the dataflow-into-index scan:

```
serving_allowlist_scan:
  sanctioned_sources: [ "Recommender/services/search/index.go", ... ]
  serving_reads:      [ { reader, source, dynamic_filename }, ... ]
  serving_dirs:       [ { dir, classified }, ... ]
```

The **presence** of the envelope is the activation signal. Until the materialiser
injects it, the key is absent → the rule vacuously passes. Once activated, a
malformed/partial scan (a missing required sub-key) **fails closed** (denies) — the
conformance-tcb fail-closed semantics, scoped to activation so they never
false-fire estate-wide.

## Remediation

Add the source to the sanctioned-sources allowlist (with justification), classify
the new serving directory, or replace the dynamic filename with a static
allowlisted path. Do not read a hand-curated fixture on the serving path.

## Suppression

Per-adopter opt-out via `.scp/rule-config.yaml` (`no-shortcuts-serving-allowlist-disabled: true`
or `rules.SCP-R-014.disable: true`) or an active waiver against `SCP-R-014`. A
suppressed finding still emits an observability `warn` record.

## Cross-references

- Decision **D-067** (this rule's registration).
- LIVE gate: `jrnb2024/conformance-tcb` `policy/scp_r_join_001.rego` (charter v2 §5).
- Precedent: ARCH-006 / SCP-R-013 (split identity + dormancy); D-058 (LINKAGE-not-VALUES).
