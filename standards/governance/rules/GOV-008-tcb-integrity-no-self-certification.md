# GOV-008 — TCB Integrity and No Self-Certification

**Domain:** governance
**Version:** 1.0.0
**Status:** active
**Severity default:** high
**Enforcement policy:** `policies/SCP-R-016.rego` (the standards-domain ID is GOV-008; the CI enforcement ID is SCP-R-016 — the workflow loads only `SCP-R-*.rego`).

> **Enforcement status: DORMANT on the SCP plane.** The `SCP-R-016` checks ship
> warn-baseline but VACUOUSLY PASS until the companion workflow materialiser
> injects their input (`FUP-D067-CONFORMANCE-TCB-MATERIALISER-001`). **LIVE
> enforcement today is the separate `conformance-tcb` repo gate**
> (`jrnb2024/conformance-tcb`, `policy/scp_r_tcb_001.rego`), branch-protected and a
> required check there. Do not treat SCP-plane enforcement as live until the
> materialiser lands.

## Intent

Protect the **Trusted Computing Base (TCB)** of the conformance harness and forbid
**self-certification**. The harness may not certify itself: the paths that define
what "green" means, and the identity that mints greens, are protected by operator
signatures and container-minted provenance.

## The four signals

- **(a) TCB-covered edit without a counter-signature** — a diff touching a
  trust-root-covered path requires a fresh **hardware-token operator
  counter-signature**.
- **(b) Green minted outside the sanctioned identity** — a green must be minted
  under the sanctioned pinned-container **OIDC subject** and recorded in the
  **append-only ledger**. No SUT-triggered job may assume the mint subject.
- **(c) CI-gate edit without an operator signature** — a diff editing a CI gate or
  branch-protection path requires an operator signature.
- **(d) Typed disagrees with computed** — a typed board status may not disagree
  with the computed proof (fake-done).

## Honesty note

The harness **ledger deliberately leaves `operator_signature` null**. A real value
is supplied ONLY by the operator's hardware token **out-of-band** — it is **never
fabricated by the agent fleet**. This rule reads that operator-owned field; it
does not and cannot mint it. The same discipline applies to this rule's own
registration: these anti-gaming rules were **proposed by the agent fleet** (via
`scp-standards.propose`, PROP-010/011/012) and **adjudicated by the operator**
(James) — the fleet does not self-certify its own standards (see D-067).

This is the **D-058 LINKAGE-not-VALUES** discipline: the rule gates the integrity
of the TCB and the mint provenance, never the domain values.

## Input contract (materialiser-injected; dormant until then)

`SCP-R-016` reads `input.tcb_integrity`, an envelope the materialiser injects from
the PR diff + the green-mint context:

```
tcb_integrity:
  diff:                 [ { path, tcb_covered, ci_gate }, ... ]
  operator_signature:   null                 # operator-supplied out-of-band only
  greens:               [ { cell, oidc_subject, in_ledger }, ... ]
  expected_oidc_subject: "repo:jrnb2024/conformance-tcb:ref:refs/heads/main:job:mint"
  board_cells:          [ { id, typed, computed }, ... ]
```

The **presence** of the envelope is the activation signal. Until then the key is
absent → vacuous pass. Once activated, a missing `diff` / `board_cells` **fails
closed** (denies).

## Suppression

Per-adopter opt-out via `.scp/rule-config.yaml` (`tcb-integrity-disabled: true` or
`rules.SCP-R-016.disable: true`) or an active waiver against `SCP-R-016`. A
suppressed finding still emits an observability `warn` record.

## Cross-references

- Decision **D-067** (this rule's registration).
- LIVE gate: `jrnb2024/conformance-tcb` `policy/scp_r_tcb_001.rego` (charter v2 §5).
- Precedent: ARCH-006 / SCP-R-013 (split identity + dormancy); D-058 (LINKAGE-not-VALUES).
