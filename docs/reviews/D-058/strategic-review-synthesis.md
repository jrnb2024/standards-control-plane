# D-058 — strategic-review synthesis (3-lens; 2026-05-29)

**ADR:** `docs/decisions/D-058-scp-canonical-conformance-strategy-2026-05-29.md`
**Lenses run:** architecture-coherence / sequencing-pragmatism / safety-devils-advocate
**Trigger:** operator strategic question 2026-05-29 — "what should we add to the rules to make it useful?" — with explicit ask for multi-agent analysis.

This document captures the convergence + divergence from the three lens dispatches + how the synthesis resolved them into D-058's decision shape. Per `feedback_orchestrator_auth_surface_plan_review_default.md`, strategic ADRs at the auth-adjacent altitude require plan-stage 3-lens review; this is that artefact.

---

## Lens verdicts

| Lens | Verdict | Single-most-important finding |
|---|---|---|
| **Architecture coherence** | COHERENT WITH AMENDMENTS | SCP is an enforcement plane + read-through index, **NOT** a control plane. Domain authorities own canonicals; SCP indexes + gates. Operator's "every agent consults SCP" framing slides toward control-plane shape; that conflation must be kept explicit. |
| **Sequencing + pragmatism** | NEEDS PREREQS — proceed to auth Phase 1 AFTER CT closes manifest_sha256 drift + FUP-CT-MANIFEST-CRON-REFRESH-001. Decoupled from 026F. | **Auth is the closest-to-shippable first domain.** CT canonical artefacts already mostly exist (canonical-sdk-versions.yaml signed + sha-pinned; auth-contract-v1.yaml at claim_shape_version 1.1.0; ct-auth-{py,ts,go} live; cosign infra PR #447). All 7 estate repos consume ct-auth. Only the manifest_sha256 drift blocks. |
| **Safety + devil's advocate** | PREMATURE — proposal is a category error (federated canonical-publication registry dressed up as more rules), filed 96h after D-054 ratified the opposite discipline. | **026F paradox: 7 domains designed for before the first canary (RULE-003) registers a single invocation.** Cheaper alternative: `docs/ESTATE-CANONICALS.md` + PR-template declaration + r1-evidence validator captures 80% of value at 10% of cost. |

## Where the lenses converged

All three lenses agreed on:

1. **Direction is right.** SCP's destination is canonical-conformance enforcement; D-036/RULE-003/SCP-R-006 is already the prototype shape; the operator's strategic instinct is sound.
2. **Scope is wrong.** Seven-domains-at-once is the WP-SCP-021 trap at 7× scale, filed days after D-054 explicitly chose the opposite bet. One domain end-to-end first; expand on evidence.
3. **SCP indexes + gates; does NOT author canonicals.** Authority transfer is the load-bearing failure mode to prevent.
4. **LINKAGE not VALUES.** D-049's hill-to-die-on must be inherited; rules check references to signed external artefacts, not canonical content.
5. **The merge-gate path is the trust root TODAY.** The MCP consult surface (`scp.consult_rules`) is the cost-reduction lane (move feedback from merge-time to write-time), but unproven at 2026-05-29; can't be the load-bearing assumption.

## Where the lenses diverged

The substantive disagreement was between **Lens 2** ("proceed to auth Phase 1 now") and **Lens 3** ("premature; do the cheap text shape first; wait for 026F + harm evidence").

### Lens 2's case (proceed)

- Auth is uniquely shippable: CT publication infrastructure ~80% ready
- All 7 estate repos consume ct-auth — blast radius is maximal
- The gate path is decoupled from 026F — no MCP dependency
- The actively-evolving CT canonical creates the most value-per-day if conformance gating exists
- "Build everything properly" + "ship one canary fast" reconcile at "one domain, fully built, then decide"

### Lens 3's case (wait)

- 026F paradox: ZERO invocations of the consult surface and we're designing for SEVEN domains
- `docs/ESTATE-CANONICALS.md` + PR-template + r1-evidence-check ships in ~2 days and covers 80% of the value
- The 7-domain framing smuggles new substrate (publication, lookup, cache-invalidation, agent integration) as "more rules"
- N=7 repos + 1 operator is a coordination problem solvable by team discipline at this scale; tooling cost exceeds friction cost
- Rule maintenance cost is super-linear (R-cycles + 3-lens reviews + FUPs + baseline-hash refresh)
- Survivorship bias: today's session shipped 6 PRs; another governance ADR feels cheap from inside the flow

## How the synthesis resolved divergence

The disagreement is **not** either-or. Both lenses are correct at different altitudes:

- **Lens 3 is right** that the cheap text shape (`ESTATE-CANONICALS.md` + PR template) is genuinely 80% of the value at 10% of the cost. Skipping it would be a category error — building infrastructure before evidence of need.
- **Lens 2 is right** that the auth domain specifically is shippable end-to-end now via the gate path, *independent* of any consult-surface evolution, given CT's near-ready publication.

D-058 stages BOTH as **Phase A (cheap, days) → Phase B (mechanical, weeks)**:

- **Phase A** (Lens 3's shape): `docs/coordination/2026-05-29-estate-canonicals-cheap-shape.md` (SCP-side coordination memo specifying what CT publishes). Authoritative artefact lands in CT operator-attended. PR templates + r1-evidence-check pattern propagate estate-wide. Captures the canonical-awareness baseline.
- **Phase B** (Lens 2's shape): `docs/plans/WP-SCP-028-auth-canonical-conformance-v1.md`. Three warn-baseline Rego rules over CT's already-published canonical-sdk-versions.yaml. 4-week observation window. Gated on CT closing the manifest_sha256 drift.

This sequencing addresses Lens 3's "category error" finding (the cheap shape is a real prelude, not skipped) AND Lens 2's "auth is shippable now" finding (Phase B fires once Phase A + CT drift-close are in place).

## Lens 3's smartest catch (institutional memory)

> "D-049 cooled exactly this ambition for design-system 6 weeks ago. The multi-agent process that drafted D-049 considered exactly the 'many rules for cross-cutting concerns' model and instead converged on: **one rule SCP-R-005 at warn baseline + rule-RFC paths for everything else**. The skeptic's hill: 'SCP does not load a browser and does not store design-token *values* in its rules.' Does the operator's current proposal violate that exact hill?"

D-058 inherits D-049's discipline VERBATIM. The 4-artefact publish contract (signed manifest + schema + estate registry + consult-domain key) is the structural enforcement of "LINKAGE not VALUES" at the cross-domain altitude. Without it, SCP drifts into authorship; with it, SCP stays at LINKAGE.

## Lens 1's smartest catch (architectural framing)

> "Is SCP being asked to become a control plane in the data-plane / control-plane sense (config distribution + state reconciliation), or just an enforcement plane (deny non-conformance)? The operator's framing reads like the former; the current implementation is the latter. What's the cost of conflating them, and is the conflation real or just terminological?"

D-058's Decision §1 makes the boundary explicit:
- **Renovate** is the distribution lane
- **ACC's dispatch** is the reconciliation lane
- **SCP** is the enforcement plane + read-through index — never pushes state to adopters

This is load-bearing because without it, future SCP work creeps toward "force-flip adopter state to canonical" — which is ACC's job, not SCP's.

## Lens 2's smartest catch (concrete first WP)

> "WP-SCP-028 — auth-canonical-conformance Phase 1: 3 warn-baseline Rego rules (SCP-R-009 version-pin, SCP-R-010 import-fence, SCP-R-011 claim-shape) tracking CT-published `policies/canonical-sdk-versions.yaml`, cascading to PIM + CT + mapp-doc-agent via existing required-check path; 4-week observation window before deny-promotion; gated on CT FUP-CT-MANIFEST-CRON-REFRESH-001 close + drift resolution; companion D-058 ADR establishing CT-as-sole-auth-canonical-authority."

D-058's Decision §6 + the plan-doc filed in the same PR adopt this verbatim. The named rules + baselines + cohort path + observation window + prereqs are all carried into the plan-doc as Phase B's commitments.

## What the operator missed in their enumeration

Lens 1 surveyed `~/Projects/` and surfaced four cross-cutting domains worth qualifying that the operator's seven didn't name:

- **Observability** (`/health` shape, OTel propagation — recurs in RI/SA/PIM/CT/SCP-self)
- **Vendored-SDK pinning** (`canonical-sdk-versions.yaml` exists in CT; extends current R-007/R-008)
- **Multi-language conformance pair** (ct-auth-py/ts/go — three implementations of one canonical; needs cross-language-parity gating)
- **Tenancy / cross-tenant leak prevention** (recurring in PIM CROSS-TENANT FTs)

D-058's Decision §7 incorporates all four into the named-but-not-built roadmap (WP-SCP-031, WP-SCP-032, WP-SCP-033, WP-SCP-034). These are higher-leverage than at least 2 of the operator's original 7 (FastAPI conventions are largely taste; Postgres patterns are mostly tool-choice).

## Bottom-line synthesis (mirrored in D-058 §"Decision")

The operator is **directionally right** about SCP's destination, **tactically wrong** about the 7-domain framing, and **practically right** that auth is the natural first domain — but only because CT has done most of the publication work in the last 96 hours and Lens 2 surfaced that. Without that timing accident, even auth would not yet be shippable.

D-058 ratifies:
- The strategic direction (canonical-conformance enforcement, indexed + gated by SCP, authored by domain authorities)
- The discipline (LINKAGE not VALUES; 4-artefact publish contract; enforcement-plane-not-control-plane; one-domain-at-a-time)
- The Phase A cheap shape (CT publishes ESTATE-CANONICALS.md; PR templates declare conformance; r1-evidence validates)
- The Phase B first slice (WP-SCP-028 auth-canonical-conformance; 3 warn-baseline rules; 4-week observation; D-059 reserved)
- The Phase C named-but-not-built roadmap (WP-SCP-029..N; each fires only when its authority publishes the 4-artefact tuple)
- The decoupling from 026F (Phase B uses gate path; consult surface stays observation-mode; cross-domain expansion that depends on consult gates on D-056)

The autonomous-run continuation prompt for WP-SCP-028 (`docs/continuation-prompts/2026-05-30-WP-SCP-028-auth-canonical-autonomous.md`) is filed in the same PR.

## Per-finding disposition table

| Lens | Finding | Severity | Disposition |
|---|---|---|---|
| L1 (architecture) | SCP/control-plane vs enforcement-plane conflation | HIGH | **FOLDED** into D-058 §1: explicit boundary statement; named in Anti-scope |
| L1 (architecture) | 4-artefact publish contract for domain qualification | HIGH | **FOLDED** into D-058 §3 (load-bearing) |
| L1 (architecture) | Consult-surface as bridge to gate (rule IDs threaded through) | MAJOR | **FOLDED** into D-058 §4 |
| L1 (architecture) | 4 additional domains worth qualifying (observability/SDK/multi-lang/tenancy) | MAJOR | **FOLDED** into D-058 §7 roadmap |
| L2 (sequencing) | Auth is the shippable first domain — concrete prereqs + 90-day roadmap | HIGH | **FOLDED** into D-058 §6 + WP-SCP-028 plan-doc filed in same PR |
| L2 (sequencing) | Decouple from 026F via gate-path use (Phase B doesn't depend on consult) | HIGH | **FOLDED** into D-058 §8 |
| L3 (safety) | 7-domain framing is the WP-SCP-021 trap at 7× scale, filed 96h after D-054 chose the opposite | CRITICAL | **FOLDED** — D-058 explicitly stages one-domain-at-a-time + Phase C is named-but-not-built; the strategic 3-lens review captured in this synthesis IS the discipline that catches this |
| L3 (safety) | The cheap shape (ESTATE-CANONICALS.md + PR template + r1-evidence) is 80% of value at 10% of cost | CRITICAL | **FOLDED** into D-058 §5 as Phase A; coordination memo filed in same PR |
| L3 (safety) | Authority transfer (SCP becoming canonical author) is the load-bearing failure mode | HIGH | **FOLDED** into D-058 §2 + Anti-scope; mirrors L1 finding |
| L3 (safety) | 026F paradox — designing for SEVEN domains before first canary observed | HIGH | **FOLDED** into D-058 §8 — Phase C entries that depend on consult are gated on D-056 |
| L3 (safety) | Bus-factor-1 amplification with rule maintenance cost super-linear | MAJOR | **FOLDED** into D-058 §10 + Accepted residual risk |
| L3 (safety) | Survivorship bias — today's session 6 PRs makes next ADR feel cheap | MAJOR | **NOTED**, not foldable — operator awareness is the mitigation. This very synthesis is the audit trail. |

---

**Outcome:** ACCEPT-WITH-AMENDMENTS folded into D-058. No REJECT. Per-WP plan-stage 3-lens review for WP-SCP-028 will be conducted during the autonomous-run cycle (the strategic review captured here ratifies the *direction*; per-WP reviews ratify the *implementation*).
