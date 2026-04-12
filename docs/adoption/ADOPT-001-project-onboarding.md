# ADOPT-001 — Standards Control Plane Project Onboarding

**Version:** 0.1
**Status:** Active
**Date:** 2026-04-12

## 1. Purpose

This is the single onboarding brief for any repo that wants to adopt the
Standards Control Plane.

If a team asks, "What do we need to change to use SCP in our repo, wire it into
CI, and update our governance docs?", point them here.

The goal is not to redesign the adopter repo. The goal is to plug SCP into the
repo's existing delivery process in a way that is:

- structured
- reviewable
- advisory first
- easy to run locally and in CI
- compatible with stronger existing repo governance

## 2. What Adopting Teams Get

After onboarding, a project should be able to:

1. ask for targeted standards guidance before coding
2. run changed-file audit in PR workflows
3. run full or subsystem audit on a schedule
4. keep findings, waivers, and reports in a consistent shape
5. layer repo-specific standards on top of the shared registry
6. publish CI-facing and Control Tower-facing outputs without a second audit path

## 3. Estate Best-Practice Position

Adopt SCP using the same broad discipline already proven across Control Tower,
Documentation Intelligence, and the estate conformance work:

- use a shared standard, not copy-pasted local folklore
- extract and reuse proven patterns rather than inventing a second mechanism
- keep the integration layer thin; do not refactor core business logic just to
  "make SCP fit"
- keep audit local to the repo that owns the code
- keep findings structured and durable; markdown is a projection, not the source
  of truth
- keep the rollout advisory first; do not introduce hard CI blocking at
  adoption time
- keep project overlays explicit instead of weakening the shared standard into
  vague prose
- keep the existing repo governance protocol if it is stronger; SCP supplements
  governance, it does not replace it

## 4. Governance Rules Teams Must Preserve

The minimum expected governance posture for adopters is:

1. do not silently descope
2. do not skip the repo's existing review process
3. every SCP finding is resolved, waived, accepted, marked false positive, or
   explicitly deferred by the repo's normal governance path
4. docs and control records are updated in the same session as code changes
5. git stays clean: branch, PR, merge, and artifact ownership remain explicit

If a repo already follows the stronger Control Tower delivery protocol with
parallel adversarial review, keep using it.

## 5. Recommended Deployment Model

Use this deployment model unless there is a strong repo-specific reason not to:

### 5.1 Package and CLI first

Install SCP as a Python tool dependency in the adopter repo and call it through
CLI commands in local workflows and CI.

This is the default and recommended mode.

### 5.2 Repo-local audit

Run `audit-changed` and `audit` inside the target repo, not in a central shared
service. The repo that owns the code should own extraction, normalisation, and
artifact generation.

### 5.3 Optional shared consult service

If teams want a shared consult endpoint, run `serve` with bearer auth and use it
for consult and registry access. Do not move the canonical audit runtime there
yet.

### 5.4 Control Tower consumes artifacts

Control Tower should read the emitted artifacts. It should not invoke evaluator
runtime directly.

### 5.5 Docs-agent remains optional

Docs-agent is a future enrichment layer for broader retrieval and historical
evidence. It is not required for base onboarding.

## 6. Pre-Onboarding Decisions

Before implementation begins, each adopting repo must decide the following:

| Decision | Why it matters |
|----------|----------------|
| **Repo owner** | Owns the adoption and follow-up fixes |
| **Governance owner** | Owns waivers, accepted debt, and process wording |
| **Overlay owner** | Owns repo-specific standards and overlay drift |
| **Pilot subsystem** | Gives consult and audit a bounded first target |
| **Primary domains** | Start with `governance,architecture` unless there is a specific reason not to |
| **CI owner** | Wires PR and scheduled audit jobs |
| **Agent instruction file** | Defines where consult-before-coding will be added (`CLAUDE.md`, `AGENTS.md`, or equivalent) |
| **Service mode decision** | Decide whether local CLI is enough or whether the repo wants the optional HTTP service |

## 7. Required Repo Changes

Every adopter should make the following changes.

### 7.1 Install SCP as a pinned tool dependency

Until SCP is published to an internal package index, the simplest path is to pin
the GitHub repo:

```bash
pip install "git+https://github.com/jrnb2024/standards-control-plane-.git@main"
```

Best practice:

- pin the Git reference or released version explicitly
- do not install from a floating local copy in CI
- keep SCP version changes visible in dependency review

### 7.2 Add a repo-local overlay

Create a repo-local overlay directory so project-specific rules and patterns can
sharpen the shared registry without editing SCP core.

Recommended location:

```text
governance/standards-control-plane/
  standards-index.json
  architecture/
    index.json
    rules/
    patterns/
  governance/
    index.json
    rules/
```

Use overlays for:

- repo-specific boundary rules
- stricter severity for already-shared rules
- approved local patterns
- project terminology or subsystem tags

Do not use overlays for:

- broad restatement of the shared registry
- undocumented local preferences with no owner
- hiding or weakening shared standards that should remain estate-wide

### 7.3 Add thin wrapper scripts

Do not scatter raw long CLI invocations across prompts, READMEs, and CI files.
Create repo-local wrapper scripts with the repo's fixed defaults.

Recommended wrappers:

```text
scripts/scp-consult
scripts/scp-audit-pr
scripts/scp-audit-full
```

Those wrappers should own:

- subsystem default
- overlay path
- standards version
- any repo-specific request-file path

### 7.4 Add findings and waiver ownership

The repo must own these artifacts:

- `output/findings/waivers.json`
- `output/findings/open-findings.json`
- `output/findings/findings-history.json`
- `output/findings/area-summaries/*.json`
- `output/reports/latest-review.md`

Best practice:

- commit waivers and long-lived findings/history artifacts through normal PR flow
- treat PR-scoped CI summaries as build artifacts, not as mandatory committed files
- keep waiver approvals explicit and time-bound

### 7.5 Update governance docs

Every adopter should update:

- `CLAUDE.md`, `AGENTS.md`, or equivalent agent instruction file
- repo governance protocol or delivery guide
- PR template or delivery checklist if one exists

## 8. Governance Doc Wording to Add

At minimum, the adopting repo should add a section equivalent to this:

```text
## Standards Control Plane Usage

Before implementation:
1. Identify impacted subsystem, area, and files.
2. Run SCP consult for the relevant domains.
3. Read applicable rules, approved patterns, and open findings.
4. Summarise the implementation plan against those constraints before coding.

Before PR or handoff:
1. Run SCP changed-file audit.
2. Review findings and fix them where required.
3. Record waivers or accepted debt explicitly; do not silently bypass findings.
4. Keep generated findings and report artifacts aligned with the code change.
```

If the repo already has stronger governance language, integrate SCP into that
language rather than replacing it.

## 9. Agent Workflow Teams Should Adopt

This is the expected operating loop for implementation agents:

1. identify impacted subsystem, area, and likely changed files
2. run `consult`
3. read:
   - applicable rules
   - approved patterns
   - open findings
   - relevant historical review references
4. summarise the plan against those constraints
5. implement
6. run `audit-changed`
7. fix findings or explicitly record exceptions through the repo's governance path
8. only then open or update the PR

SCP should become part of the normal pre-coding and pre-PR loop. It should not
be a late afterthought.

## 10. CI Integration

### 10.1 PR workflow

Each adopting repo should add a non-blocking PR job that runs changed-file audit.

Recommended command shape:

```bash
standards-control-plane audit-changed \
  --base-ref origin/main \
  --head-ref HEAD \
  --domains governance,architecture \
  --subsystem <subsystem> \
  --standards-version <registry-version> \
  --overlay governance/standards-control-plane \
  --write-output
```

Then publish:

- `output/ci/latest-ci.json`
- `output/ci/latest-ci.md`
- `output/reports/latest-review.md`

Do not fail the build on day one. Warnings should be visible first.

### 10.2 Scheduled workflow

Each adopting repo should also add a scheduled job for broader refresh:

```bash
standards-control-plane audit \
  --request governance/scp/audit-request.json \
  --overlay governance/standards-control-plane \
  --write-output
```

Recommended cadence:

- nightly for fast-moving repos
- weekly for slower repos

### 10.3 Control Tower projection

If the repo participates in estate-level reporting, publish or expose:

- `output/control-tower/surface.json`
- `output/control-tower/estate-dashboard.json`
- `output/control-tower/subsystems/*.json`

## 11. Optional Shared Service Mode

If a team wants a shared consult endpoint, use:

```bash
standards-control-plane serve \
  --host 127.0.0.1 \
  --port 8000 \
  --auth-token <token> \
  --overlay governance/standards-control-plane
```

Guidance:

- keep auth on if the service is shared across users or runners
- use service mode primarily for consult and registry access
- keep audit local to the repo even if consult is remote

## 12. Architecture Principles for Adopters

These are the key architectural principles teams should follow while adopting
SCP.

### 12.1 Extract, do not reinvent

Use the shared registry, shared contracts, and shared outputs. Do not create a
repo-specific second standards engine.

### 12.2 Thin integration only

Add wrapper scripts, CI jobs, overlays, and governance references. Do not
perform broad business-logic refactors just because the repo is onboarding SCP.

### 12.3 One audit model

CI outputs, Control Tower outputs, and reports should all be projections from
the same audit result. Do not invent a separate CI-specific evaluator path.

### 12.4 Structured artifacts first

Findings JSON, waivers JSON, audit results, and summaries are the durable
records. Markdown exists to help humans review those records.

### 12.5 Explicit overlays

If the repo needs local specificity, express it through an explicit overlay with
an owner. Do not bake local assumptions into global SCP core.

### 12.6 Deterministic checks before inference

Start by relying most heavily on governance and architecture signals that are
already deterministic or evidence-backed. Expand advisory use of UX, design, and
product only when the repo is comfortable with the confidence model.

## 13. Recommended Adoption Phases

### Phase 0 — Prep

- choose owners
- choose pilot subsystem
- add overlay directory
- add wrapper scripts
- update governance docs

### Phase 1 — Local advisory use

- run `consult` before implementation work
- run `audit-changed` locally before PRs
- keep domains to `governance,architecture`

### Phase 2 — CI advisory mode

- add PR CI job for changed-file audit
- publish CI artifacts
- do not block merges on warnings yet

### Phase 3 — Scheduled findings refresh

- add scheduled full or subsystem audit
- start maintaining waivers and accepted debt explicitly
- review trend and rollup artifacts regularly

### Phase 4 — Optional service and estate surfacing

- stand up the optional consult service if it helps multiple teams
- plug emitted artifacts into Control Tower or a local dashboard

## 14. Anti-Patterns to Avoid

Do not do these:

- do not make SCP the user's first hard merge gate
- do not onboard all five domains at once unless the repo already trusts the
  weaker advisory domains
- do not put repo-specific assumptions into SCP core when an overlay would do
- do not keep findings in chat, tickets, or screenshots only
- do not create floating TODOs instead of findings, waivers, or backlog items
- do not replace the repo's stronger existing review protocol with a weaker SCP
  process
- do not run a central service and assume that removes the need for repo-local
  CI integration

## 15. Adoption Acceptance Checklist

A repo is properly onboarded when all of the following are true:

- SCP is installed as a pinned dependency
- a repo-local overlay exists with a named owner
- wrapper scripts exist for consult and audit
- agent instructions explicitly require consult before coding
- CI runs changed-file audit on PRs
- scheduled audit exists for the repo or pilot subsystem
- waivers are stored in repo and time-bound
- findings and reports are inspectable through normal repo workflows
- the team knows who approves waivers and who owns overlay changes

If those are not true, the repo is not actually onboarded.

## 16. Source Practices This Guide Was Derived From

This onboarding guide is aligned to:

- `control-tower/governance/docs/DELIVERY_GOVERNANCE_PROTOCOL.md`
- `control-tower/governance/docs/DOCUMENTATION_STANDARDS.md`
- `control-tower/docs/strategy/platform-conformance-strategy.md`
- `control-tower/docs/handoffs/conformance-prompts.md`
- [STRAT-SCP-001-phased-adoption.md](../strategy/STRAT-SCP-001-phased-adoption.md)
- [README.md](../../README.md)

Those sources collectively define the estate's strongest current practice for:

- governance discipline
- thin conformance integration
- repo-local ownership with shared standards
- advisory-first rollout
- explicit project overlays
