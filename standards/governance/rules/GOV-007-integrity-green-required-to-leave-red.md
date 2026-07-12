# GOV-007 — Integrity-Green Is Required to Leave RED

**Domain:** governance
**Version:** 1.0.0
**Status:** active
**Severity default:** high
**Enforcement policy:** `policies/SCP-R-015.rego` (the standards-domain ID is GOV-007; the CI enforcement ID is SCP-R-015 — the workflow loads only `SCP-R-*.rego`).

> **Enforcement status: DORMANT on the SCP plane.** The `SCP-R-015` checks ship
> warn-baseline but VACUOUSLY PASS until the companion workflow materialiser
> injects their input (`FUP-D067-CONFORMANCE-TCB-MATERIALISER-001`). **LIVE
> enforcement today is the separate `conformance-tcb` repo gate**
> (`jrnb2024/conformance-tcb`, `policy/scp_r_triad_001.rego`), branch-protected and
> a required check there. Do not treat SCP-plane enforcement as live until the
> materialiser lands.

## Intent

A conformance board **cell** may not be marked **non-RED** (green / passing)
unless every integrity clause holds. This is the anti-"fake-done" gate: a cell
must go green by making the real join pass, not by editing the board or the test
harness.

## The four integrity clauses

1. **L2 computed-agrees** — the claimed status equals the computed-from-proof
   status (`render_board`). No typed override.
2. **L3 fake-mutant-failed** — the standing FAKE fixture FAILED its test (proving
   the test discriminates; a test that passes its own fake mutant is blind).
3. **L5 red-first** — a CI-observed, ledger-signed RED preceded the flip.
4. **Transition classifier** — the cumulative diff since the last signed RED is
   SUT-only, with TCB byte-identity.

The **correctness tier** (external / attested) is a **separate** required tag,
NOT gated by this rule. A cell claiming status `RED` is never gated here.

This is the **D-058 LINKAGE-not-VALUES** discipline: the rule gates the INTEGRITY
of the green claim, never the domain values under test.

## Input contract (materialiser-injected; dormant until then)

`SCP-R-015` reads `input.cell_transition`, an envelope the materialiser injects
per cell being flipped:

```
cell_transition:
  id:                 "boho-romance @ facet"
  status:             "GREEN-integrity"   # the CLAIMED status (!= RED is a flip)
  computed_status:    "GREEN-integrity"   # L2 derived-from-proof
  fake_mutant_failed: true                # L3
  red_first:          true                # L5
  classifier_ok:      true                # transition classifier
```

The **presence** of the envelope is the activation signal. Until then the key is
absent → vacuous pass. Once activated AND the cell claims non-RED, a missing
required field **fails closed** (denies).

## Suppression

Per-adopter opt-out via `.scp/rule-config.yaml` (`integrity-green-triad-disabled: true`
or `rules.SCP-R-015.disable: true`) or an active waiver against `SCP-R-015`. A
suppressed finding still emits an observability `warn` record.

## Cross-references

- Decision **D-067** (this rule's registration).
- LIVE gate: `jrnb2024/conformance-tcb` `policy/scp_r_triad_001.rego` (charter v2 §5).
- Precedent: ARCH-006 / SCP-R-013 (split identity + dormancy); D-058 (LINKAGE-not-VALUES).
