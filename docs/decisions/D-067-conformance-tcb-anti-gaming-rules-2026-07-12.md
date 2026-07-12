# D-067 — Register the three conformance-tcb anti-gaming rules as official SCP standards (warn-baseline, dormant)

**Date:** 2026-07-12 · **Status:** ACCEPTED · **Extends:** D-058 (canonical-conformance strategy) · **Reserves nothing; consumes nothing.**

> **Numbering note.** The prompt scoping this work named "D-062", but D-062 is
> already CONSUMED (accept PROP-004 as ARCH-006 ontology-canonical-consumption,
> 2026-07-02), and D-062/D-063/D-064/D-065 are all reserved by the WP-SCP-037
> canonical-source standards family, with D-066 consumed (cross-repo `audit_changed`,
> 2026-07-05) and D-059 (WP-SCP-028 deny-promote) / D-060 (WP-SCP-030 observation)
> still reserved. This decision is therefore filed as **D-067** — the next free
> number. Renumber on merge only if a reservation changed meanwhile.

## Context

Three anti-gaming conformance rules were designed, adversarially reviewed, and
**already enforce LIVE** in the separate `conformance-tcb` repo
(`jrnb2024/conformance-tcb`), where they are branch-protected required checks fed
by that repo's own CI. They were surfaced to SCP via `scp-standards.propose`
(PROP-010 / PROP-011 / PROP-012) for adjudication into official estate standards:

- **SCP-R-JOIN-001** (`policy/scp_r_join_001.rego`) — no-shortcuts serving-source allowlist.
- **SCP-R-TRIAD-001** (`policy/scp_r_triad_001.rego`) — integrity-green required to leave RED.
- **SCP-R-TCB-001** (`policy/scp_r_tcb_001.rego`) — TCB integrity + no self-certification.

They are the anti-gaming spine of the conformance harness (charter v2 §5): they stop
a demo "going green" by reading a hand-curated fixture, editing the board/test
harness instead of making the real join pass, or letting the harness certify
itself. They belong in SCP as **official estate governance standards** so they are
consult-discoverable, gate-registered, and available to cascade to the cohort — not
only enforced in one downstream repo.

## Decision

**Register the three rules as official SCP standards in the `governance` domain,
warn-baseline and DORMANT, following the SCP-R-013 ↔ ARCH-006 precedent exactly.**

1. **Split identity.** Each rule gets a standards-domain ID (prose + governance
   index) and a distinct SCP-R-NNN enforcement policy:
   - **GOV-006** ↔ `policies/SCP-R-014.rego` — no-shortcuts serving-source allowlist.
   - **GOV-007** ↔ `policies/SCP-R-015.rego` — integrity-green required to leave RED.
   - **GOV-008** ↔ `policies/SCP-R-016.rego` — TCB integrity + no self-certification.
   The CI workflow loads only `SCP-R-*.rego`; the scorecard filters `SCP-R-[0-9]+`;
   the finding `rule_id` is the SCP-R-NNN; the prose it links to is the GOV-NNN.

2. **Warn-baseline.** All three are added to BOTH `WARN_BASELINE_RULES` sites in
   `policy-check.yml` (the render-deny set and the scorecard set — the coupling
   guard). Their findings render as `::warning::` and are excluded from the
   merge-gate threshold.

3. **Dormant / vacuous-pass.** Each rule reads a materialiser-injected input
   envelope (`input.serving_allowlist_scan` / `input.cell_transition` /
   `input.tcb_integrity`) whose PRESENCE is the activation signal. Until the
   companion materialiser injects it, the key is absent → the rule VACUOUSLY
   PASSES on unrelated PRs (the SCP-R-009 / SCP-R-013 safe-failure precedent).
   The conformance-tcb **fail-closed** semantics (a malformed/partial input DENIES)
   are preserved but **scoped to activation**, so they cannot false-fire
   estate-wide before the materialiser exists.

## Honesty (this is load-bearing, per GOV-008's own no-self-cert principle)

- **(a) Live enforcement today = the conformance-tcb gate.** These rules FIRE and
  block in `jrnb2024/conformance-tcb`. On the SCP plane they are registered but
  DORMANT. This decision does NOT claim live SCP-plane enforcement.
- **(b) SCP-plane firing needs a materialiser companion** — a follow-up work
  package, **`FUP-D067-CONFORMANCE-TCB-MATERIALISER-001`**, that injects the three
  input envelopes at adopter CI time. Until it lands, the rules are consult-visible
  and gate-registered but do not fire on adopter PRs.
- **(c) Deny-promotion is a future decision.** A later D-NNN decides deny-promote /
  hold-at-warn / re-scope AFTER an observation window on real firing traffic (the
  D-053 "earn deny on observed precision, not on the release that unblinds it"
  discipline). No calendar gate under GOV-005; the gate is evidence.
- **(d) No self-certification.** These rules were **proposed by the agent fleet**
  (PROP-010/011/012) and **adjudicated by the operator** (James). The fleet does
  not self-certify its own standards — the same anti-self-cert principle GOV-008
  encodes for the harness applies to the registration of GOV-008 itself.

## Consequences

- **New files:** `policies/SCP-R-014.rego` / `-015` / `-016` + their
  `policies/tests/scp_r_01{4,5,6}_test.rego`; `standards/governance/rules/GOV-00{6,7,8}-*.md`.
- **Edited:** `standards/governance/index.json` (rules GOV-006/007/008; version
  1.1.0 → 1.2.0); `policy-check.yml` (both `WARN_BASELINE_RULES` sites); `STATUS.md`
  (dated chain entry); `docs/DECISIONS.md` (this row).
- **`rule-inputs.yaml`: no entry.** These are materialiser-injected structured-input
  rules (the SCP-R-013 shape), NOT `input.source_file` + `input.content` content-fed
  rules (the SCP-R-003 envelope that `rule-inputs.yaml` feeds). SCP-R-013 likewise
  has no `rule-inputs.yaml` entry. Adding one would be incorrect (the feed
  surrogates changed-file content into YAML; these rules never read changed-file
  content — the materialiser injects a computed scan/transition/mint context).
- **Verification (pre-PR):** `opa check policies/*.rego` clean; per-rule
  `opa test --coverage --threshold 90 --fail-on-empty` GREEN (SCP-R-014 12/12 @93.5%,
  SCP-R-015 12/12 @93.3%, SCP-R-016 14/14 @94.2%); `opa fmt --diff` empty; `regal lint`
  clean under the repo's CI disable set; the new rules vacuously pass on unrelated
  input (dormancy proven by the `vacuous_*` tests).
- **Reversibility bounded:** per-adopter `disable` / waiver in the ≤24h Renovate
  cycle; warn-baseline cannot block a merge; a future D-NNN is the only path to deny.

## Alternatives rejected

- **A new `conformance` domain** rather than `governance` — heavier (new domain
  index + domain-map wiring) for three rules that are squarely about the integrity
  of the verification process, which `governance` (GOV-001..005: scope, planning,
  review-evidence, build-method, operating-stance) already covers. Rejected in
  favour of extending `governance`.
- **Register at `deny` immediately** — the rules have zero SCP-plane firing history
  (they cannot even fire until the materialiser lands). Deny on zero SCP-plane
  evidence violates the D-053 discipline. Rejected.
- **Leave them only in conformance-tcb** — then they are not estate standards, not
  consult-discoverable, and cannot cascade to the cohort. Rejected: the whole point
  of adjudication is to make them official.

## Cross-references

- D-058 (canonical-conformance strategy; LINKAGE-not-VALUES) · D-053 (earn-deny-on-evidence) ·
  ARCH-006 / SCP-R-013 (split-identity + dormancy precedent) · GOV-005 (no calendar/soak gates).
- LIVE gate: `jrnb2024/conformance-tcb` `policy/scp_r_{join,triad,tcb}_001.rego` (charter v2 §5).
- Proposals: PROP-010 / PROP-011 / PROP-012 (retire on merge: `adjudication_status: accepted`).
- Follow-up: `FUP-D067-CONFORMANCE-TCB-MATERIALISER-001` (SCP-plane input materialiser).
