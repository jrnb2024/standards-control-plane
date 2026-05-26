# Estate Convergence — Standards Control Plane (SCP)

**Repo role:** Policy authority (the second pillar)
**Canonical reference:** `/Users/amplience/Projects/control-tower/docs/architecture/ESTATE-CONVERGENCE-CHECKPOINTS.md`
**Source doc:** `~/Desktop/estate-drift-prevention-and-orchestration-2026-05-20.docx` (Rev 2)
**Last updated:** 2026-05-20

SCP is one of the four pillars. This file documents SCP's role in the convergence target and the active cascade.

## Where SCP fits

SCP is the **policy authority**: owns the Rego rule set, the `policy-check.yml` reusable workflow, the stdio MCP server (`scp-mcp-server`; zero adopter consumers as of 2026-05-26 — see WP-SCP-026), and the hook surfaces that consult those rules at every gate from pre-dispatch to post-merge. SCP's HTTP service is deployed at `https://scp.brokapps.ai` for FastAPI endpoints (`/consult` + `/audit` + `/registry` + frontend); MCP transport is stdio-only — HTTP MCP transport + `acc.brokapps.ai` MCP hosting claims retracted per D-054 + D-055 and deferred to WP-SCP-027.

SCP's contribution to drift prevention is the dimension that neither CT nor ACC can cover: deterministic, rule-based authorisation of what code is allowed to merge, federated to every adopter repo.

## SCP's place in the lifecycle

Five hook integration points (see Diagram 4 in the Rev 2 doc):

| Stage | Hook | What SCP enforces |
|---|---|---|
| Plan-stage | None (R-cycle handles it) | n/a |
| Pre-dispatch | ACC `acc-hook` (PreToolUse) | Scope boundary derived from rule consult |
| Per-tool-call | Same `acc-hook` re-fires | Per-tool scope violation |
| Pre-commit | Adopter `.claude/PreCommit` hook (WP-SCP-027 future-scope per D-054 + D-055) | MCP receipt signature/expiry/file-hash — deferred; not enforced today |
| Pre-merge / CI | `policy-check.yml` reusable workflow | Rego rule pack evaluation |
| Post-merge | scorecard-aggregator + telemetry | Observational |
| Break-glass | `enable-required-check.sh` | Operator-attended relaxation |

## SCP rules in production

| ID | Rule | Status |
|---|---|---|
| SCP-R-001 | `services.yml` auth modes + deprecation dates | DENY (v1.0.0) |
| SCP-R-002 | `waivers.json` schema validity | DENY (v1.0.0) |
| SCP-R-003 | Vendoring attestation marker | DENY (v1.0.0) |
| SCP-R-004 | Waiver reason cites URL | WARN (v1.1.0) |
| SCP-R-005 | DPBM design-system artefacts | DRAFT (v1.3.0) — promotes WARN→DENY post-Recommender bake |

All rules governed by **D-036 rule-RFC process**: every rule lands at WARN baseline, promotes to DENY via separate RFC with 48h quorum window.

## Active cascade — WP-SCP-024

Phase 1: PIM canary onboarded; bake observation in flight.
Phase 2: Cohort rollout — pending TF-PIM-001 resolution.

**P0 blocker — TF-PIM-001:** default `GITHUB_TOKEN` in `policy-check.yml` cannot clone private SCP repo from adopter context. Canonical fix paths: PAT/GitHub-App token via `secrets: inherit`, or make SCP public. Must clear in parallel with manifest work.

## DO NOT

- **DO NOT** add a new SCP rule outside the D-036 rule-RFC process.
- **DO NOT** promote a rule from WARN to DENY without the separate RFC + 48h quorum window.
- **DO NOT** modify `policy-check.yml` reusable workflow in ways that change its public contract without bumping the major version.
- **DO NOT** add new rule logic that depends on cross-repo state (rules are LOCAL to the adopter repo by design — CT's manifest is the global counterpart).
- **DO NOT** ship a new rule that requires the SCP repo to be public if TF-PIM-001 is still open (the cause-and-effect would be tangled).
- **DO NOT** promote SCP-R-005 to DENY until Recommender (first cohort adopter) has declared intent + completed bake.

## Cross-estate aggregator

SCP's stdio MCP server is one of the high-signal sources for the CT-hosted estate aggregator. The aggregator can call `scp.consult_rules` for any adopter (currently via `scp-cli consult --domain X` per WP-SCP-026 026B; eventually via direct MCP if a downstream consumer wires it) to surface rule-compliance state estate-wide. Receipt-signing on consult responses was retracted per D-054 + D-055; deferred to WP-SCP-027 future-scope on operator-attended demand signal.

## When in doubt

1. Check DO NOT list above
2. Check `/Users/amplience/Projects/control-tower/docs/architecture/ESTATE-CONVERGENCE-CHECKPOINTS.md`
3. Defer to D-036 rule-RFC process

## Status snapshot

- Threshold A reached 2026-04-30 (federation primitive shipped, dogfooded on self)
- 4 production rules enforcing (R-001/002/003 DENY, R-004 WARN); 1 draft (R-005)
- WP-SCP-024 Phase 1 canary (PIM) in flight; Phase 2 cohort blocked on TF-PIM-001
- D-049 adopted 2026-05-19/20 — DPBM design-system enforcement formally in SCP scope
