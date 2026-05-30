# D-058 — SCP strategic direction: canonical-conformance enforcement for cross-cutting domains; one-domain-at-a-time; auth first

**Status:** DRAFT (operator-review surface; flips to ACCEPTED on PR merge per the post-merge ADR ceremony established by D-047 / D-048 / D-049 / D-050 / D-054 / D-055 / D-057).
**Date filed:** 2026-05-29
**Decision date:** TBD (operator signature on merge)
**Operator:** @jrnb2024
**Origin:** operator strategic question 2026-05-29 (post-D-057): "what should we add to the rules to make it useful?" 3-lens strategic review (architecture coherence / sequencing-pragmatism / devil's advocate) conducted in the same session; synthesis converges on this ADR.
**Builds on:** D-049 (SCP-R-005 design-system; same architectural shape — LINKAGE not VALUES) + D-054 (Shape C discipline: ship one canary fast, defer broader scope to named successor) + D-036/RULE-003 + D-057 (Pattern 3 self-orchestrate ceremony — autonomous SCP development happens via dispatch).
**Successors named (do NOT consume):**
- **WP-SCP-028** — auth-canonical-conformance Phase 1 (first domain end-to-end; ratified by this ADR + plan-doc filed in same PR).
- **WP-SCP-029..N** — named-but-not-built roadmap for additional domains; each fires only when its owning authority publishes a signed canonical artefact.
- **D-059** reserved for the auth-canonical observation-window outcome (deny-promote / hold-at-warn / re-scope at the 4-week mark).
**Review provenance:** 3-lens strategic review 2026-05-29 (correctness / sequencing+pragmatism / safety+devil's-advocate); synthesis in `docs/reviews/D-058/strategic-review-synthesis.md`. All three lenses returned variants of "directionally right; scope wrong; auth is the shippable first domain"; the synthesis resolved divergence between Lens-2's "proceed now" and Lens-3's "premature" via a two-phase A-then-B sequence (cheap text index first, Rego enforcement second).

---

## Context

### What SCP is today (verified, 2026-05-29)

- 8 Rego rules at `policies/SCP-R-001..R-008.rego`; 6 actually fire on adopter PRs. The library is **structural hygiene** (`.env*` files, vendoring attestation, waiver TTL, secret patterns in env files). It does its job, but the library is thin and the rules don't gate the *substantive* architectural decisions that drive estate convergence.
- 3 LIVE adopters on the merge-gate cohort cascade (PIM, CT, mapp-doc-agent). Cohort cascade machinery proven: ship one Rego rule → 3 adopters get a required-status-check within hours.
- MCP `consult_rules` consult surface: built (`scp-cli` shipped PR #176; RI canary wired at `~/Projects/ri-est-p-ws-2/.acc/mcp_server.py:298-340`); **zero real invocations to date**. 026F observation window OPEN until 2026-06-23; D-056 reserved to decide advance/hold/re-scope.
- D-049 established the architectural discipline that's load-bearing here: SCP rules encode **LINKAGE** ("does this thing reference the canonical correctly?"), NOT **VALUES** ("here's what the canonical IS"). SCP does not load a browser; does not store token values; does not run a runtime. OPA Rego over a checked-out tree only.
- D-054 chose Shape C explicitly: ship one consumer fast (RULE-003/SCP-R-006 prototype), defer broader scope to a named successor (WP-SCP-027). That discipline applies to this ADR's strategic move too — at the cross-cutting-domain altitude.

### The strategic question

The operator asked 2026-05-29: should SCP evolve from "structural hygiene linter" into a **canonical-architecture conformance oracle** for cross-cutting domains (auth, orchestrator/dispatcher, governance docs, Kafka, FastAPI, frontend, Postgres, observability, SDK pinning, multi-language conformance, tenancy)? Each domain's canonical is owned by an authority (CT for auth, ACC for orchestrator, etc.); agents consult SCP for the current canonical before authoring; SCP gates PRs at merge time against the canonical.

### What the 3-lens strategic review concluded

- **Direction: yes.** All three lenses agreed canonical-conformance enforcement is SCP's highest-leverage purpose; D-036/RULE-003/SCP-R-006 is already the prototype shape.
- **SCP's role: indexer + enforcer, NOT canonical author.** Domain authorities own the canonical; SCP indexes signed artefacts + gates conformance. Cross-validates D-049's anti-scope discipline.
- **Scope: one domain end-to-end, observed, then expand.** Seven-domain framing is the WP-SCP-021 trap at 7× scale, filed days after D-054 explicitly chose the opposite bet (Lens 3's most pointed finding; not refuted by 1 or 2).
- **What gates work: LINKAGE not VALUES.** Rules check "does your code reference the canonical at the correct version + correct linkage shape," not "does your code match a copy of the canonical content."
- **What trust root works today: the merge-gate required-check.** The consult surface (MCP) is the cost-reduction lane — moves feedback from merge-time to write-time — but is still unproven at 2026-05-29; can't be the load-bearing assumption.
- **First domain: auth.** CT has done most of the publication work already (canonical-sdk-versions.yaml signed + sha-pinned; auth-contract-v1.yaml at `claim_shape_version 1.1.0`; ct-auth-{py,ts,go} live; cosign infra shipped PR #447); only the `manifest_sha256` drift needs closing. All 7 estate repos consume ct-auth. Actively-evolving canonical (48h push 2026-05-29 in flight).

## Decision

Ratify **canonical-architecture conformance enforcement as SCP's strategic direction**, with the following discipline locked in:

### Architectural shape (load-bearing)

1. **SCP is an enforcement plane + read-through index, NOT a control plane.** Renovate is the distribution lane; ACC's dispatch is the reconciliation lane; SCP never pushes state to adopters. It indexes signed canonicals and gates at merge time.

2. **LINKAGE not VALUES.** SCP rules verify that adopter code references the canonical (path, version, signed manifest, schema) correctly. SCP does NOT carry the canonical content. Domain authorities own authorship; SCP owns gating.

3. **Domain-publish contract (4 artefacts).** A domain qualifies for SCP gating ONLY when its authority has published:
   - **(a) A signed manifest** (Ed25519 signed; published at a stable path; CT-cosign-style)
   - **(b) A schema** declaring the manifest's required keys
   - **(c) An estate registry entry** (e.g. `control-tower/config/estate_repos.yaml` row)
   - **(d) A consult-domain key** (registered in SCP's MCP consult registry)
   Absent any of these, SCP does not author a Rego rule for that domain. This prevents SCP from drifting into canonical authorship by filling in missing publication infrastructure.

4. **The consult surface bridges write-time and merge-time, doesn't replace either.** When `scp.consult_rules(domain=X)` is invoked, the response returns rule IDs that the gate will assert. Adopter agents are required to surface those rule IDs in their work artefacts (PR body, commit message, or dispatch declaration). This closes the consult-zero-invocations gap (D-054 026F anti-criterion) by making the gate enforce that consult happened — without making consult itself a deny-gate.

### Sequencing (one domain at a time)

5. **Phase A — Estate-canonicals index (cheap text shape; CT-owned, SCP-coordinated).** Publish `control-tower/docs/ESTATE-CANONICALS.md` listing each estate domain → owning authority → canonical doc path → current version. Estate-wide PR-template addition: "this PR touches domain(s) [...]; conforms to ESTATE-CANONICALS.md §X.Y at version Z." Existing r1-evidence-check pattern validates the declaration string is present (not its content — that's still LINKAGE). Ships in days. Captures ~80% of canonical-awareness value with zero Rego, zero MCP, zero new substrate. The SCP-side coordination memo is filed inline in this PR at `docs/coordination/2026-05-29-estate-canonicals-cheap-shape.md`; the authoritative artefact lands in CT operator-attended.

6. **Phase B — Auth-canonical Rego enforcement (WP-SCP-028; 6-10 weeks; SCP-owned).** Plan-doc filed at `docs/plans/WP-SCP-028-auth-canonical-conformance-v1.md` in this PR. Three warn-baseline rules:
   - **SCP-R-009 — auth-canonical-version-pin**: adopter manifests must reference ct-auth-{py,ts,go} package versions ≥ those declared in CT's `policies/canonical-sdk-versions.yaml`. Deny on downgrade; warn on stale.
   - **SCP-R-010 — auth-canonical-import-fence**: adopter source files importing from `ct_auth` / `@control-tower/auth` / `ctauth-go` must NOT shadow or re-implement the verify/sign primitives. Detection via canonical-doc-declared forbidden symbol set.
   - **SCP-R-011 — auth-contract-claim-shape**: any `Authorization`-handling code path must accept the current `claim_shape_version` (1.1.0 today); detect old issuers-of-1 schema patterns as deny.
   Prereq: CT closes `manifest_sha256` drift (`386b4097` recorded vs `eddcd053` actual) + ratifies `FUP-CT-MANIFEST-CRON-REFRESH-001`. 4-week observation window after rules land in cohort cascade; D-059 ratifies deny-promote / hold-at-warn / re-scope.

7. **Phase C — Named-but-not-built roadmap (WP-SCP-029..N).** Each subsequent domain becomes a named WP that fires *only* when its owning authority publishes the 4-artefact tuple. Priority order (by canonical-maturity + adopter coverage):
   - **WP-SCP-029** — Kafka event-shape conformance (RI/SA pair; BaseEvent baseline-hash gate already exists; needs producer/consumer registry from CT)
   - **WP-SCP-030** — ACC orchestrator-canonical conformance (gated on PLAN-EST-P-v3 shipping past WS-EST-P-2; currently Gate-A draft)
   - **WP-SCP-031** — Vendored-SDK pinning (extends current R-007/R-008; uses CT's canonical-sdk-versions.yaml)
   - **WP-SCP-032** — Multi-language conformance pair (ct-auth-py/ts/go parity; gates that all 3 implementations advance together)
   - **WP-SCP-033** — Observability canonical (`/health` shape, OTel propagation; needs an owning authority to publish)
   - **WP-SCP-034** — Tenancy / cross-tenant leak prevention (recurring in PIM CROSS-TENANT FTs)
   - **WP-SCP-035** — Governance documentation taxonomy (extends existing SCP-self discipline)
   - **WP-SCP-036+** — FastAPI conventions, frontend framework, Postgres patterns (lowest-priority; most canonical-immature; tool-choice or taste-dominated)

8. **Decoupling from 026F.** WP-SCP-028 (auth Phase B) uses the proven merge-gate required-check path, NOT the MCP consult surface. It does not depend on 026F outcome. Cross-domain expansion (WP-SCP-029+) that depends on `consult_rules` invocation is gated on D-056 ratifying advance-to-WP-SCP-027.

### Operator-attended controls

9. **Each new domain WP requires its own plan-stage 3-lens review** (per `feedback_orchestrator_auth_surface_plan_review_default.md` — auth and auth-adjacent surfaces are mandatory). The strategic 3-lens review captured in this ADR ratifies the *direction*; per-WP reviews ratify the *implementation*.

10. **Bus-factor-1 acknowledged (D-031 + D-040).** This direction expands SCP's maintenance surface across multiple domains; operator capacity is the binding constraint. Phase C entries are *deferred* until evidence of harm from current divergence + capacity to maintain. They are roadmap, not commitment.

## What this IS and is NOT

**IS:**
- A strategic ratification that SCP's destination is canonical-conformance enforcement, scoped one-domain-at-a-time, anchored at LINKAGE not VALUES.
- A concrete first-domain implementation handoff (WP-SCP-028 plan-doc + autonomous-run continuation prompt filed in same PR).
- A named-but-not-built roadmap (WP-SCP-029..N) that's reserved, not committed.
- Architectural discipline (the 4-artefact publish contract; enforcement-plane-not-control-plane) explicit in writing so future ADRs inherit it.

**IS NOT:**
- A commitment to ship all 7+ domains. Each fires only on evidence.
- A commitment to build the MCP consult surface beyond what 026F observation justifies. The gate path is the load-bearing trust root; consult is cost-reduction layered on top.
- Authority transfer. SCP does NOT become the auth authority (CT is). It does NOT become the orchestrator authority (ACC is). It indexes + gates.
- A replacement for code review or governance ADRs. SCP rules complement those at the merge boundary; they don't replace human judgement on novel patterns.
- An MCP-first strategy. The first deliverable (WP-SCP-028) uses the merge-gate path, not the consult path.

## Anti-scope (preserves D-049 hill-to-die-on)

- No browser. No CSS parser. No runtime preview.
- No token VALUES. No JWT verification at SCP. No cryptographic primitive re-implementation.
- No state reconciliation (push-canonical-to-adopters). Renovate distributes; ACC reconciles; SCP gates.
- No semantic interpretation of canonical content beyond signed-manifest verification. Rules read structure (presence, version, path, schema), not meaning.

## Accepted residual risk

- **False positives on novel-but-correct patterns.** Especially in auth, where the canonical evolves monthly. Mitigation: warn-baseline first; 4-week observation before deny-promote; per-rule TTL escape hatch; PR review remains the human backstop. Trade-off acknowledged: rules WILL occasionally deny correct PRs in their first 30 days post-ship.
- **Canonical drift between owner repo and SCP reference.** CT updates `canonical-sdk-versions.yaml`; SCP's rule still references the prior version's expected shape. Mitigation: SCP rules read the manifest at evaluation time (no SHA-pinned-copy in SCP); CT's signed-manifest infrastructure is the source of truth.
- **Estate-wide deny storms on rule-misfire.** A faulty new SCP rule could block merges across 3+ adopters simultaneously. Mitigation: warn-baseline-first discipline (a faulty warn-rule is noise, not block); cohort cascade can be reverted in <1h via rule-config disable.
- **Operator burnout from rule maintenance.** Multiplied if Phase C entries fire prematurely. Mitigation: roadmap status (not commitment); each entry's prereq is "domain authority publishes the 4-artefact tuple" — operator capacity is the gating function.

## Reversal mechanism

If Phase B's auth slice fails (false-positive storm, adopter friction tickets, canonical-drift cascade failure), the reversal cost is bounded:
- Flip SCP-R-009/010/011 baselines from `warn`/`deny` to `disabled` via rule-config — propagates in next Renovate cycle (~24h)
- Cohort adopters can locally disable via their `.scp/rule-config.yaml` until SCP cuts a fix
- Rule code can be deleted in a single PR; cohort adopters' wrapper pins remain valid
- Total reversal cost: <1 day, no adopter migration required

The strategic direction itself (this ADR) is reversible by a successor ADR. If the auth Phase observation surfaces that "the gate adds friction without preventing real harm" or "the canonical-authority publication overhead is unsustainable," D-NNN could amend or rescind D-058. The estate would revert to its current state (structural-hygiene-only rule library + WP-SCP-021-prototype RULE-003).

## Status flip ceremony

Per the established estate pattern (D-047 / D-048 / D-049 / D-050 / D-054 / D-055 / D-057), this ADR's status flips DRAFT → ACCEPTED on the merge of the PR that opens it. Operator merge constitutes the ratification signature.

**PR body discipline (pre-merge gate).** The PR MUST include a `## R1 evidence` block with three lens lines citing the 2026-05-29 3-lens strategic review (correctness / safety_bypass / completeness_governance — or matching synonyms; the SCP r1-evidence-check regex accepts the canonical triplet). The review evidence lives at `docs/reviews/D-058/strategic-review-synthesis.md` in this PR.

## Successor decisions reserved

- **D-059** — WP-SCP-028 auth-canonical observation-window outcome (deny-promote / hold-at-warn / re-scope at 4-week close). Filed inline at WP-SCP-028 close-out.
- **D-NNN per WP-SCP-029..N** — each subsequent domain's plan-doc ratification gets its own ADR at fire time.

## Diff-verification

Per `feedback_verbatim_claim_diff_verification.md`, the load-bearing claims in this ADR are grounded in repo state at filing:

```bash
# SCP rule library size (8 rules; 6 actually fire — verify):
ls /Users/amplience/Projects/standards-control-plane/policies/SCP-R-*.rego | wc -l
# Cohort cascade adopters LIVE (3):
grep -E "cohort.*LIVE|adopters.*LIVE" /Users/amplience/Projects/standards-control-plane/STATUS.md | head -3
# CT canonical artefacts present (verify):
ls /Users/amplience/Projects/control-tower/policies/canonical-sdk-versions.yaml /Users/amplience/Projects/control-tower/contracts/auth-contract-v1.yaml 2>&1
# 026F window open (still unobserved as of D-058 filing):
ls /Users/amplience/Projects/ri-est-p-ws-2/.acc/dispatches/ 2>&1   # expected: No such file or directory
```

---

**Identified at:** 2026-05-29 operator strategic question (post-D-057 merge).

**Filed:** 2026-05-29 (this ADR PR).

**Closes when:** operator merges this PR + `docs/DECISIONS.md` row appended + WP-SCP-028 plan-doc landed + ESTATE-CANONICALS coordination memo filed + autonomous-run continuation prompt for WP-SCP-028 landed + STATUS chain row.
