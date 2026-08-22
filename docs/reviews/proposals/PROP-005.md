---
adjudication_status: accepted
accepted_as: SVC-ADOPT-001
decision_ref: D-063
accepted_at: 2026-07-03
accepted_note: adjudicated into standards/service-lifecycle/rules/SVC-ADOPT-001-estate-app-registration.md + index.json (advisory-consult, no Rego); live via consult_rules. WP-SCP-037 §1b.
expected_review_date: null
queued_at: 2026-07-03T11:11:16Z
---
> NOTE: WP-SCP-022-proposal-queue adjudication workflow is not yet live;
> proposals queue until adjudication ships. Status updates via
> GitHub issue on this branch (proposals/PROP-005). See
> docs/plans/WP-SCP-022-implementation-programme-plan.md §12.

<!-- proposal_metadata: {"affected_repos":["standards-control-plane","control-tower","acc","mapp-estate-dashboard","mapp-doc-agent"],"caller_id":"stdio:35116:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server","mcp_origin":true,"proposal_hash":"327e8ad760058998aed1868a9d01b5c601dbb1b70a218084b13f4a3d631e61f9","rule_id":"SVC-ADOPT-001","signing_key_id":"428dfee16bc954ad"} -->

# PROP-005: SVC-ADOPT-001 estate app-registration — the 9 registration touchpoints as one consultable standard

## Proposal Envelope
- mcp_origin: true
- caller_id: stdio:35116:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server
- signing_key_id: 428dfee16bc954ad

## Affected Repositories
- standards-control-plane
- control-tower
- acc
- mapp-estate-dashboard
- mapp-doc-agent

## Rule Context
SVC-ADOPT-001

## Proposal Body
## Principle

Registering a new app into the Mapp Fashion estate is a fixed set of **9 touchpoints**. Today an operator rediscovers them per-app ("go look at how the other apps did it"). SVC-ADOPT-001 names them as ONE consultable standard so a new app inherits the checklist instead of reinventing it. Part of the canonical-source standards family (WP-SCP-037); the registration counterpart of the ontology (ARCH-006) and networking (SVC-005) canonicals.

## The 9 touchpoints

1. **CT estate-manifest** — `control-tower/contracts/estate-manifest.json` entry (the estate's authoritative app registry).
2. **CT services.yml** — a service entry with `runtime_contract` (SVC-001) + health path (SVC-002) + `auth_contract` (SVC-003).
3. **CT OAuth client** — a Control Tower OAuth client registration (if the app has an HTTP surface behind CT SSO).
4. **SCP adoption** — the `policy-check-wrapper.yml` (App `scp-federation-primitive` + 2 secrets), the SCP-R-030 acc-hook onboarding block in CLAUDE.md (if hooked), and branch protection with `policy-check / scp/policy-check` required. Canonical procedure: ADOPT-001.
5. **ACC estate_repos** — `acc/config/estate_repos.yaml` entry (so ACC orchestration + the estate dashboard see the repo).
6. **Estate-dashboard health discovery** — the app is reachable by the `mapp-estate-dashboard` health-discovery (its health endpoint conforms to SVC-002).
7. **doc-manifest** — `mapp-doc-agent/doc-manifest.json` entry (so consult_estate/doc-agent index the repo's docs).
8. **MCP registry** — if the app exposes an MCP server, it is registered in the estate MCP registry.
9. **Governance docs** — the app appears in the estate governance surface (STATUS/OVERVIEW/estate map) as a registered citizen.

## Enforcement posture

**Advisory-consult** (the checklist is prose). The ENFORCEABLE parts already exist and fire independently: SVC-001/002/003 (services.yml contract), SCP-R-030 (hooked-repo onboarding block), the policy-check required-status-check itself. SVC-ADOPT-001 is the consultable INDEX that ties them together + names the non-lintable touchpoints (CT manifest, OAuth client, ACC estate_repos, doc-manifest, MCP registry, governance docs). No new Rego. The sequential onboarding CEREMONY (App install → 2 secrets → warm wrapper PR → clean flip → invocation-log) is documented in ADOPT-001 §12.7 (WS1d enhancement).

## Why advisory not enforced

Most touchpoints live in OTHER repos (CT, ACC, doc-agent) and are registry entries, not adopter-repo source — SCP gates the adopter's own tree, so it can't lint a CT manifest entry from the adopter's PR. The consultable checklist closes the "which touchpoints did I miss?" gap; enforcement stays with the parts that ARE in-tree (SVC-001/002/003, SCP-R-030).
