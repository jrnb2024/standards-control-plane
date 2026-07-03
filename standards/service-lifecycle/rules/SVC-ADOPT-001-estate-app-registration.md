# SVC-ADOPT-001 — Estate App Registration Is Nine Touchpoints, Consulted as One

**Domain:** service-lifecycle
**Version:** 1.0.0
**Status:** active
**Severity default:** medium

> **Enforcement posture: ADVISORY-CONSULT.** This rule is the consultable INDEX
> of the estate's registration touchpoints. It authors no new Rego. The
> touchpoints that ARE lintable already fire as their own rules (SVC-001/002/003,
> SCP-R-030); the rest live in other repos' registries and are consult-only.

Registering a new app into the Mapp Fashion estate is a fixed set of **nine
touchpoints**. Without an authored standard, an operator rediscovers them per
app ("go look at how the other apps did it") and misses one. SVC-ADOPT-001 names
them as ONE consultable checklist so a new app inherits the set instead of
reinventing it. It is the registration member of the canonical-source standards
family (WP-SCP-037) — the counterpart of the ontology canonical (ARCH-006) and
the networking canonical (SVC-005).

## The nine touchpoints

| # | Touchpoint | Where | Lintable? |
|---|------------|-------|-----------|
| 1 | **CT estate-manifest** | `control-tower/contracts/estate-manifest.json` entry | no (CT-repo registry) |
| 2 | **CT services.yml** | a service entry with `runtime_contract` + health path + `auth_contract` | **yes — SVC-001 / SVC-002 / SVC-003** |
| 3 | **CT OAuth client** | a Control Tower OAuth client (if the app has an HTTP surface behind CT SSO) | no (CT-side config) |
| 4 | **SCP adoption** | `.github/workflows/policy-check-wrapper.yml` (App `scp-federation-primitive` + 2 secrets) + the acc-hook onboarding block in `CLAUDE.md` (if hooked) + branch protection with the **check-run** `policy-check / scp/policy-check` required (NOT the commit-status `scp/policy-check-readback` — see §12.7.3) | **partly — SCP-R-030 (hook block) + the required check itself**; ceremony in ADOPT-001 §12.7.0 |
| 5 | **ACC estate_repos** | `acc/config/estate_repos.yaml` entry | no (ACC-repo registry) |
| 6 | **Estate-dashboard health discovery** | reachable by `mapp-estate-dashboard` health discovery (health endpoint conforms to SVC-002) | indirect (SVC-002 gates the endpoint shape) |
| 7 | **doc-manifest** | `mapp-doc-agent/doc-manifest.json` entry (so `consult_estate` / doc-agent index the repo) | no (doc-agent registry) |
| 8 | **MCP registry** | if the app exposes an MCP server, it is registered in the estate MCP registry | no (registry) |
| 9 | **Governance docs** | the app appears in the estate governance surface (STATUS / OVERVIEW / estate map) as a registered citizen | no (prose) |

## Adoption triggers

A new app MUST work through the nine touchpoints when:

- **T1** — the app is first stood up on a `*.brokapps.ai` hostname (it becomes an
  estate surface; pair with SVC-004 deploy + SVC-005 networking).
- **T2** — the app gains an HTTP surface that other estate apps or agents call
  (triggers touchpoints 2/3/6/8).
- **T3** — the app's repo starts being gated / hooked (triggers touchpoint 4).

A local-only script or a one-off with no estate surface is not bound until it
crosses a trigger.

## Signals

The consult signals are enumerated in this rule's `index.json` entry (the nine
touchpoints above are the signal set — a missing touchpoint on a new estate app
is the finding). Because this is an advisory-consult rule, the signals are served
via `consult_rules` for authoring guidance; they are not compiled into an
enforcing Rego (the lintable subset already fires as SVC-001/002/003 + SCP-R-030).

## Rationale

An operator kept rediscovering the registration touchpoints per app ("go look at
how the other apps did it") and missing one — so a new app would ship
half-registered (in CT services.yml but absent from ACC estate_repos, or reachable
but not in the estate-dashboard health discovery). Naming the nine touchpoints as
one consultable checklist means a new app inherits the complete set instead of
reconstructing it. It is deliberately advisory, not a new gate: six of the nine
touchpoints are entries in other repos' registries, and per D-058 (LINKAGE-not-
VALUES) SCP gates the tree it evaluates, not another repo's registry — enforcement
stays with the in-tree subset (SVC-001/002/003, SCP-R-030). GOV-005: a consult
index, not governance theatre.

## Why advisory, not enforced

Six of the nine touchpoints are entries in OTHER repos' registries (CT
estate-manifest, CT OAuth, ACC estate_repos, doc-manifest, MCP registry,
governance docs). SCP gates the ADOPTER's own tree at merge time, so it cannot
lint a CT-manifest entry from the adopter's PR (LINKAGE-not-VALUES: SCP gates
what's in the tree it evaluates). The consultable checklist closes the
"which touchpoints did I miss?" gap; enforcement stays with the parts that ARE
in-tree — SVC-001/002/003 (the services.yml contract) and SCP-R-030 (the
hooked-repo onboarding block).

## The sequential ceremony (touchpoint 4 detail)

The SCP-adoption touchpoint has a fixed order — App install → 2 secrets → warm
wrapper PR → clean flip → invocation-log — documented as the canonical
onboarding ceremony in `docs/adoption/ADOPT-001-project-onboarding.md` §12.7.0
(the WP-SCP-037 §1d enhancement). Consult it before gating a new adopter.

## Cross-references

- **D-058** — canonical-conformance strategy (LINKAGE-not-VALUES).
- **SVC-001 / SVC-002 / SVC-003** — the lintable services.yml contract (touchpoint 2).
- **SVC-004** — deploy recipe; **SVC-005** — networking recipe. Registration
  (this rule) + deploy + networking are the full estate bring-up trio.
- **SCP-R-030** — hooked-repo onboarding block (touchpoint 4).
- **ADOPT-001 §12.7.0** — the SCP-adoption sequential ceremony.
- **`reference_estate_canonical_sources.md`** — the estate canonical map
  (registration → the 9 touchpoints).
