# Original User Specification — 2026-04-11

Captured from the planning session on 2026-04-11.

The content below is preserved as the source specification for the project.

# Standards Consultant and Audit Service

## Full specification and implementation plan

### Purpose

Build an internal **Standards Consultant and Audit Service** for agent-assisted software delivery.

The system must provide two distinct but related capabilities:

1. **Consult**

   * give implementation agents fast, structured guidance on governance, architecture, UX/IA, design system, and product conventions
   * surface relevant standards, existing drift, open findings, and approved patterns before coding begins

2. **Audit**

   * periodically or on demand scan the codebase and related project artefacts
   * evaluate conformance against defined standards
   * detect drift, regressions, and unresolved issues
   * publish findings in both human-readable and machine-readable form

This system is intended to become a shared internal advisory and compliance layer across projects, not just a one-off repo tool.

---

## 1. Goals

### Primary goals

* Create a central, versioned standards registry covering:

  * governance
  * architecture
  * UX / IA
  * design system
  * product coherence

* Allow build agents to query the service for:

  * applicable standards
  * approved patterns
  * area-specific known issues
  * open findings
  * constraints and warnings before implementation

* Provide structured audits that:

  * score conformance by domain
  * identify violations and drift
  * suggest remediation actions
  * persist findings in reusable files

* Make standards portable across projects so improvements in one codebase can be adopted elsewhere

* Keep the service structurally independent from implementation agents

### Secondary goals

* Improve front-end consistency and UX quality
* Reduce architecture drift
* Reduce governance bypass and prompt sprawl
* Create an evolving quality memory for teams and agents
* Support gradual tightening from advisory guidance to stronger enforcement

---

## 2. Non-goals

* Do not build a fully autonomous code-fixing agent in phase 1
* Do not attempt to replace human design judgement
* Do not create a universal design system engine for all possible stacks
* Do not make this dependent on a single model provider
* Do not hardcode Mapp-specific architectural decisions that belong to individual teams unless already standardised
* Do not try to infer undocumented standards from code alone without clearly marking inference as low confidence

---

## 3. Core principles

1. **Advisory first, blocking later**

   * phase 1 should guide and expose problems
   * enforcement should come only after confidence and trust improve

2. **Structured outputs over prose**

   * all evaluator outputs must be machine-readable
   * human reports should be summaries of structured findings

3. **Narrow evaluators, not one giant reviewer**

   * governance, architecture, UX/IA, design system, and product coherence should be separate domains

4. **Retrieval before reasoning**

   * consult mode should retrieve applicable standards and findings before generating advice

5. **Independent review**

   * the service must not rely on the same generation pipeline that writes the code being reviewed

6. **Versioned standards**

   * standards change over time; version and timestamp them

7. **Explicit confidence**

   * every inferred finding should carry a confidence score

8. **Human override**

   * humans must be able to mark findings as accepted, waived, false positive, or resolved

---

## 4. High-level system model

### Operating modes

#### Consult mode

Used by implementation agents at planning or coding time.

Input examples:

* affected subsystem
* task or enhancement spec
* impacted files
* question domain
* optional feature description

Output examples:

* applicable standards
* approved patterns
* known open findings in the target area
* risks to avoid
* implementation guidance
* suggested files or templates to consult

#### Audit mode

Used by CI, local CLI, or scheduled tasks.

Input examples:

* target repo or directory
* scope
* domains to evaluate
* baseline findings
* standards version

Output examples:

* domain scores
* violations
* drift summary
* regressions
* suggested remediation
* updated findings files

---

## 5. Domain model

The system will evaluate five core domains.

### 5.1 Governance

Checks whether agent-assisted work follows agreed process and controls.

Examples:

* correct enhancement spec present
* scope boundaries defined and respected
* prompt templates used correctly
* required artefacts present
* expected test or verification steps included
* no unauthorised file sprawl
* evidence of review loop where required

### 5.2 Architecture

Checks whether implementation follows agreed structural patterns.

Examples:

* service boundaries respected
* dependency direction valid
* no business orchestration buried in UI layer
* data access patterns followed
* API integration points consistent
* no direct coupling where abstractions are required
* eventing / async patterns conform to standard

### 5.3 UX / IA

Checks whether product structure and user flow remain coherent.

Examples:

* navigation hierarchy is clear
* primary actions are explicit
* key flows are complete
* state transitions are consistent
* error and empty states are accounted for
* page structures align with IA templates
* cognitive overload is limited

### 5.4 Design system

Checks whether the front end uses agreed primitives and patterns.

Examples:

* approved components used where available
* token usage respected
* spacing / typography consistent
* layout primitives used correctly
* interactive states present
* accessibility basics not obviously broken
* no unnecessary bespoke component duplication

### 5.5 Product coherence

Checks whether the implementation makes sense as a product decision.

Examples:

* clear job-to-be-done
* feature behaviour aligned to product intent
* flow optimises for intended user outcome
* screen design supports the task rather than exposing raw system structure
* terminology consistent with product language
* no obvious local optimisation against the wrong objective

---

## 6. System architecture

### 6.1 Components

#### A. Standards Registry

A versioned set of source documents and structured metadata defining current standards.

#### B. Repo Extractor

Scans the target repo and gathers relevant artefacts.

#### C. Normaliser

Converts extracted material into a common intermediate representation.

#### D. Retrieval Layer

Maps consult requests and audit targets to relevant standards, examples, and prior findings.

#### E. Evaluators

One evaluator per domain.

#### F. Findings Store

Persists structured findings, waivers, resolutions, and trend history.

#### G. Report Generator

Creates human-readable summaries from structured outputs.

#### H. CLI / Service Interface

Exposes consult and audit operations.

---

## 7. Suggested repository structure

This can live either inside a target repo or in a separate shared repo. The structure below assumes a dedicated service repo.

```text
standards-consultant/
  README.md

  /standards
    /governance
      rules/
        GOV-001-scope-boundaries.md
        GOV-002-enhancement-spec.md
        GOV-003-review-evidence.md
      index.json

    /architecture
      rules/
        ARCH-001-service-boundaries.md
        ARCH-002-ui-domain-separation.md
        ARCH-003-api-access-pattern.md
        ARCH-004-async-orchestration.md
      patterns/
        dashboard-pattern.md
        task-workflow-pattern.md
      index.json

    /ux
      rules/
        UX-001-primary-actions.md
        UX-002-empty-error-loading-states.md
        UX-003-navigation-clarity.md
      patterns/
        workspace-page-template.md
        review-flow-template.md
      index.json

    /design
      rules/
        DS-001-approved-components.md
        DS-002-token-usage.md
        DS-003-layout-consistency.md
      tokens/
        tokens.json
      patterns/
        table-screen-pattern.md
        form-screen-pattern.md
      index.json

    /product
      rules/
        PROD-001-job-to-be-done.md
        PROD-002-user-outcome-alignment.md
        PROD-003-language-consistency.md
      index.json

    standards-index.json

  /schemas
    consult-request.schema.json
    consult-response.schema.json
    audit-request.schema.json
    audit-result.schema.json
    finding.schema.json
    findings-store.schema.json
    area-summary.schema.json
    standards-rule.schema.json

  /src
    /extractors
    /normalisers
    /retrieval
    /evaluators
      governance/
      architecture/
      ux/
      design/
      product/
    /reports
    /storage
    /cli
    /shared

  /prompts
    /consult
      governance.md
      architecture.md
      ux.md
      design.md
      product.md
    /audit
      governance.md
      architecture.md
      ux.md
      design.md
      product.md

  /fixtures
  /tests
  /examples

  /output
    /reports
    /findings
    /history
```

---

## 8. Source inputs to support

The system should be able to consume some combination of:

* markdown standards and docs
* enhancement specs
* prompt templates
* orchestration rules
* code files
* component definitions
* design tokens
* Storybook metadata if available
* UI screenshots if available later
* findings history
* waivers / accepted exceptions

Phase 1 should prioritise textual and code artefacts. Image or Figma-level analysis can come later.

---

## 9. Intermediate representation

The system needs a normalised view of the codebase and standards so evaluators are not operating on raw repo sprawl.

### Example project area model

```json
{
  "area_id": "returns-dashboard",
  "paths": [
    "apps/returns/src/pages/dashboard.tsx",
    "apps/returns/src/components/ReturnSummaryCard.tsx",
    "docs/enhancements/ENH-042-returns-dashboard.md"
  ],
  "subsystem": "returns",
  "artefacts": {
    "enhancement_specs": [],
    "prompts": [],
    "ui_components": [],
    "services": [],
    "tests": [],
    "standards_references": []
  },
  "metadata": {
    "languages": ["typescript"],
    "frameworks": ["react"],
    "tags": ["dashboard", "frontend", "returns"]
  }
}
```

### Example standards rule model

```json
{
  "rule_id": "ARCH-002",
  "domain": "architecture",
  "title": "UI layer must not contain domain orchestration",
  "summary": "Presentation components must delegate business workflows to domain service or action layers.",
  "severity_default": "high",
  "scope": ["frontend"],
  "signals": [
    "multiple API calls in page component",
    "business branching in view layer",
    "direct repository access from UI"
  ],
  "exceptions": [
    "small demo-only prototypes explicitly marked as exempt"
  ],
  "related_patterns": [
    "dashboard-pattern",
    "action-service-pattern"
  ],
  "version": "1.0.0",
  "status": "active"
}
```

---

## 10. Core interfaces

### 10.1 Consult request

```json
{
  "mode": "consult",
  "question": "How should I implement a new review screen for returns exceptions?",
  "domains": ["architecture", "ux", "design"],
  "area_id": "returns-exceptions",
  "paths": [
    "apps/returns/src/pages/exceptions.tsx"
  ],
  "task_context": {
    "feature_summary": "Add a triage screen for returns exceptions with filtering, detail panel and resolution actions.",
    "subsystem": "returns"
  }
}
```

### 10.2 Consult response

```json
{
  "request_id": "consult-001",
  "domains": ["architecture", "ux", "design"],
  "applicable_rules": [
    {
      "rule_id": "ARCH-002",
      "reason": "The requested screen involves action handling and must avoid embedding workflow orchestration in the page component."
    }
  ],
  "approved_patterns": [
    {
      "pattern_id": "table-screen-pattern",
      "reason": "Screen requires list, filters, detail and action workflow."
    }
  ],
  "open_findings": [
    {
      "finding_id": "F-104",
      "severity": "medium",
      "summary": "Existing returns screens duplicate filter state logic across pages."
    }
  ],
  "guidance": [
    "Keep filtering and selection state in a dedicated controller or hook, not scattered across cards and panels.",
    "Use approved data table and panel components where available.",
    "Explicitly define empty, loading and error states."
  ],
  "risks": [
    "UI-layer orchestration drift",
    "component duplication",
    "unclear primary action"
  ],
  "confidence": 0.84
}
```

### 10.3 Audit request

```json
{
  "mode": "audit",
  "domains": ["governance", "architecture", "ux", "design", "product"],
  "scope": {
    "paths": ["apps/returns", "docs/enhancements"],
    "subsystem": "returns"
  },
  "baseline_findings_file": "output/findings/open-findings.json",
  "standards_version": "2026-04-11"
}
```

### 10.4 Audit result

```json
{
  "audit_id": "audit-returns-2026-04-11",
  "scope": {
    "subsystem": "returns"
  },
  "scores": {
    "governance": 78,
    "architecture": 64,
    "ux": 58,
    "design": 71,
    "product": 74
  },
  "summary": {
    "high_severity_count": 3,
    "medium_severity_count": 8,
    "low_severity_count": 12
  },
  "findings": [],
  "drift": [],
  "regressions": [],
  "recommended_actions": [],
  "generated_at": "2026-04-11T16:10:00Z"
}
```

---

## 11. Findings model

Each finding should be explicit, scoped, and traceable.

### Finding schema shape

```json
{
  "finding_id": "F-2026-00031",
  "domain": "architecture",
  "rule_id": "ARCH-002",
  "severity": "high",
  "status": "open",
  "title": "UI layer contains workflow orchestration",
  "summary": "The page component directly coordinates API calls and branching business logic.",
  "evidence": [
    {
      "path": "apps/returns/src/pages/exceptions.tsx",
      "locator": "function ReturnsExceptionsPage",
      "snippet_ref": "local"
    }
  ],
  "area_id": "returns-exceptions",
  "suggested_remediation": [
    "Move branching workflow into service/action layer",
    "Keep view component focused on state binding and event dispatch"
  ],
  "confidence": 0.89,
  "detected_by": "architecture-evaluator",
  "standards_version": "2026-04-11",
  "created_at": "2026-04-11T16:10:00Z",
  "updated_at": "2026-04-11T16:10:00Z"
}
```

### Finding statuses

* `open`
* `accepted`
* `waived`
* `resolved`
* `false_positive`
* `superseded`

### Required metadata

Each finding must include:

* domain
* rule ID where possible
* severity
* evidence
* confidence
* timestamp
* subsystem / area
* remediation guidance

---

## 12. Domain evaluator responsibilities

### 12.1 Governance evaluator

Inputs:

* enhancement specs
* prompt templates
* operating rules
* file diffs or repo paths
* prior findings

Checks:

* expected artefacts exist
* enhancement boundaries declared
* modified files align with declared scope where possible
* governance template use is evident where applicable
* review trace or test intent exists where required

Outputs:

* findings
* governance score
* missing artefacts list
* exceptions requiring human review

### 12.2 Architecture evaluator

Inputs:

* source code
* architecture standards
* patterns
* area metadata

Checks:

* layering violations
* boundary leaks
* duplicate local abstractions
* data access shortcuts
* UI-domain mixing
* direct coupling bypassing agreed seams
* inconsistent async or eventing patterns

Outputs:

* violations
* architectural drift summary
* remediation themes

### 12.3 UX / IA evaluator

Inputs:

* route structure
* UI component names
* screen descriptions
* optional enhancement specs
* optional screenshots later

Checks:

* primary task visibility
* page / screen role clarity
* navigation consistency
* flow completeness
* empty / loading / error state coverage
* avoidable complexity
* obvious ambiguity in action model

Outputs:

* UX findings
* flow risks
* IA warnings
* suggested pattern references

### 12.4 Design system evaluator

Inputs:

* component usage
* tokens
* approved components
* styling conventions

Checks:

* token usage
* duplication of near-identical components
* layout inconsistency
* missing interactive states
* off-pattern component composition

Outputs:

* design conformity score
* duplication warnings
* missing-state flags
* suggested substitutions

### 12.5 Product coherence evaluator

Inputs:

* enhancement specs
* feature descriptions
* route / screen naming
* actions exposed
* standards

Checks:

* does the feature express a clear job to be done
* are the actions aligned to user outcome
* is terminology coherent
* is the experience solving the user task or exposing internal mechanics
* is the objective function obvious and sensible

Outputs:

* product coherence score
* ambiguous or confused features flagged
* naming / language issues
* warnings on local optimisation

---

## 13. Retrieval strategy

Consult mode should not dump all standards into context. It should retrieve only what is relevant.

### Retrieval inputs

* area / subsystem
* domains requested
* changed files
* feature summary
* known tags
* current open findings

### Retrieval outputs

For each consult request, retrieve:

* active rules relevant to the domain and subsystem
* approved patterns relevant to the feature type
* unresolved findings for the impacted area
* nearby historical regressions if useful
* waivers in force so advice stays current

### Retrieval rules

* prefer exact area matches first
* then subsystem matches
* then domain-wide active standards
* prioritise active over deprecated rules
* include no more than the minimum effective set of rules in consult response
* always include open high severity findings in the impacted area

---

## 14. Output files

### Machine-readable outputs

```text
/output/findings/open-findings.json
/output/findings/findings-history.json
/output/findings/waivers.json
/output/findings/area-summaries/returns.json
/output/findings/area-summaries/labeller.json
/output/findings/drift-summary.json
```

### Human-readable outputs

```text
/output/reports/latest-review.md
/output/reports/subsystems/returns-review.md
/output/reports/subsystems/labeller-review.md
```

### Report expectations

#### latest-review.md should include:

* audit timestamp
* scope
* standards version
* domain scores
* key regressions
* top open high severity issues
* recommended next actions
* notable improvements since previous audit

---

## 15. CLI surface

Keep the external interface simple.

### Suggested commands

```bash
standards-consultant consult --area returns-exceptions --domains architecture,ux,design --question "How should I implement a triage screen?"
```

```bash
standards-consultant audit --scope apps/returns --domains governance,architecture,ux,design,product
```

```bash
standards-consultant audit --subsystem returns --write-output
```

```bash
standards-consultant report --latest
```

```bash
standards-consultant findings --area returns-exceptions
```

### Exit behaviour

Phase 1:

* always return success unless runtime failure occurs
* findings and score determine quality, not process exit code

Later phases:

* optional thresholds can fail CI for high severity unresolved regressions

---

## 16. Execution modes

### Local

Developer or agent can run consult or audit against a target area.

### CI

Run targeted audit on changed files or subsystems in pull requests.

### Scheduled

Run broader nightly or weekly audits to refresh open findings and drift trends.

### Optional future mode

Shared internal service endpoint for multi-repo consult queries.

---

## 17. Scoring

Scoring should be simple and explainable.

### Per-domain score

0 to 100.

### Suggested interpretation

* 90–100: strong compliance
* 75–89: acceptable but with notable issues
* 60–74: meaningful drift or quality risk
* below 60: poor compliance, requires remediation

### Scoring principles

* high severity issues should materially affect score
* repeated issues should weigh more than isolated ones
* waived issues should not keep dragging active score down
* unresolved regressions should count more heavily than longstanding accepted debt
* score calculations must be deterministic and documented

---

## 18. Human review workflow

Humans need a way to manage the findings lifecycle.

### Actions

* mark accepted debt
* mark waived exception with reason and expiry
* mark resolved
* mark false positive

### Waiver model example

```json
{
  "waiver_id": "W-0012",
  "finding_id": "F-2026-00031",
  "reason": "Temporary exception during migration from old returns architecture",
  "approved_by": "team-lead",
  "expires_at": "2026-06-30T00:00:00Z",
  "created_at": "2026-04-11T16:20:00Z"
}
```

### Requirement

Audits must honour active waivers and show them separately from unresolved unwaived issues.

---

## 19. Implementation phases

### Phase 1 — Skeleton and manual standards

Goal: make the system real, even if narrow.

Deliver:

* repo structure
* schemas
* standards registry
* extractors for docs and code paths
* consult and audit CLI skeleton
* governance and architecture evaluators first
* findings store and markdown report generation
* sample outputs

Success criteria:

* can consult against a real subsystem
* can audit a real subsystem
* writes open findings and latest review files

### Phase 2 — UX / design / product evaluators

Deliver:

* UX/IA evaluator
* design system evaluator
* product coherence evaluator
* improved retrieval by area and feature type
* area-level summaries
* trend history

Success criteria:

* meaningful multi-domain audits
* useful consult output for front-end and product work
* domain scores stable and explainable

### Phase 3 — CI integration and review lifecycle

Deliver:

* changed-file scoped audit
* waiver handling
* regression detection
* CI-friendly outputs
* thresholds as warnings only initially

Success criteria:

* PR workflow can run targeted audits
* team can manage accepted debt and waivers

### Phase 4 — Stronger evidence and richer UX checks

Deliver:

* optional screenshot ingestion
* optional Storybook metadata
* optional route graph / component graph analysis
* better design drift detection
* better front-end duplication detection

Success criteria:

* higher confidence UX/design findings
* fewer false positives

### Phase 5 — Shared multi-repo consultant

Deliver:

* package or service form
* shared standards versions
* per-project overlays
* central reporting across projects

Success criteria:

* one project’s improved standards can be consumed by others
* consult mode becomes standard pre-coding workflow

---

## 20. Acceptance criteria

### Functional

* can answer consult requests with relevant standards, patterns, and open findings
* can perform audit across a subsystem and generate structured findings
* can write findings and report files
* can handle at least governance and architecture in phase 1
* can support adding new standards without code changes to core evaluator framework
* can map findings to affected areas and files

### Quality

* outputs are deterministic enough to be trusted
* structure is easy for other agents to consume
* false positives are manageable, not overwhelming
* reports are concise and useful
* evaluators are separable and testable

### Operability

* easy to run locally
* easy to run in CI
* outputs easy to inspect in git
* no dependency on a single proprietary internal environment

---

## 21. Risks and mitigations

### Risk: turns into markdown sludge

Mitigation:

* enforce JSON schemas
* keep report generation downstream of structured outputs
* do not let evaluators emit free-form essays as primary output

### Risk: low trust due to false positives

Mitigation:

* include confidence
* support waiver / false positive workflow
* begin with advisory mode
* make rules explicit and evidence-based

### Risk: standards become stale

Mitigation:

* version rules
* add timestamps
* maintain standards index
* archive deprecated rules

### Risk: over-centralised bureaucracy

Mitigation:

* focus on a small number of high-value standards first
* do not over-specify local implementation details
* separate global standards from project overlays

### Risk: agent overreliance on bad advice

Mitigation:

* retrieve source rule references in consult output
* expose evidence and rationale
* keep humans able to challenge standards

### Risk: architecture inference is too weak

Mitigation:

* begin with obvious anti-patterns and high-signal checks
* add project-specific rules gradually
* do not pretend to know what is not documented

---

## 22. Recommended initial scope

Do not start with everything.

Start with one real project area and two high-value domains.

### Recommended initial subsystem

Choose a meaningful but bounded area such as:

* returns
* labeller
* market feed
* visual commerce front-end

### Recommended initial domains

* governance
* architecture

Then add:

* UX / IA
* design system
* product coherence

This sequence will reduce complexity and get the service useful quickly.

---

## 23. Suggested build approach for the local team

### Language

Use the language and ecosystem most natural for the team and repo. TypeScript or Python are both fine.

### Minimum architectural constraints

* schemas must be explicit
* evaluators must be modular
* retrieval layer must be separable from evaluation
* findings store must be durable and inspectable
* CLI must be simple and scriptable

### Avoid

* giant monolithic prompt
* one evaluator doing all domains
* hidden scoring logic
* free-text-only outputs
* hardcoded repo assumptions where possible

---

## 24. Example consult workflow for implementation agents

Implementation agents should follow this sequence before coding:

1. Identify impacted area and files
2. Call consult mode for relevant domains
3. Read:

   * active rules
   * approved patterns
   * open findings in the area
4. Summarise planned implementation against those constraints
5. Only then implement
6. Run targeted audit after implementation
7. Remediate or explicitly record accepted exceptions

That should become part of your standard operating loop.

---

## 25. Example advisory logic

For a new front-end screen, consult should likely return:

* architecture:

  * keep business orchestration out of page component
  * use approved service/action seam

* UX:

  * define primary task and primary action
  * specify loading / empty / error states
  * use a known page template

* design:

  * use approved filters, table, drawer/panel, and button components
  * follow token usage and layout primitives
  * do not create bespoke variants unless justified

* product:

  * state job to be done in one sentence
  * ensure screen language matches product language
  * avoid surfacing internal workflow terms to users without intent

---

## 26. Definition of done for phase 1

Phase 1 is done when:

* the team can point the system at a real subsystem
* consult returns relevant governance and architecture guidance
* audit produces a valid score and findings file
* findings can be reviewed and updated by humans
* the report is useful enough that people actually read it
* no one has to guess where to find the latest open issues

If those are not true, it is not done, however polished the code looks.

---

## 27. Open decisions for the local team

These should be left to the local team rather than hardcoded in this spec:

* final language choice
* packaging as library, CLI, or service first
* exact storage backend beyond file-based output in phase 1
* exact model provider selection
* exact scoring weights
* exact integration with CI platform
* project-specific overlay mechanism
* optional screenshot / Figma integration timing

Those are implementation decisions, not product-spec decisions.

---

## 28. Build prompt for Claude Code

You can drop the following into Claude Code.

```text
Build a Standards Consultant and Audit Service according to the following specification.

Purpose:
Create an internal advisory and compliance system for agent-assisted software delivery. The system must support two modes:
1. consult: provide implementation agents with structured guidance based on standards, approved patterns, and open findings
2. audit: scan a repo or subsystem and produce structured findings, scores, drift summaries, and human-readable reports

Important constraints:
- advisory first, not blocking by default
- structured outputs first, prose second
- separate evaluators by domain
- retrieval before reasoning
- keep the review system structurally independent from implementation agents
- do not over-prescribe local implementation choices that belong to the team
- where architecture or product intent is inferred rather than explicitly documented, mark lower confidence

Core domains:
- governance
- architecture
- ux / ia
- design system
- product coherence

Phase 1 scope:
Implement the core framework with initial support for:
- standards registry
- schemas
- extractors
- normaliser
- retrieval layer
- governance evaluator
- architecture evaluator
- findings store
- markdown report generation
- CLI surface for consult and audit

Recommended structure:
- /standards for versioned rules and patterns
- /schemas for all structured contracts
- /src for extractors, normalisers, retrieval, evaluators, storage, reports, cli
- /output for findings and reports
- /prompts if prompt-backed evaluators are used
- modular evaluators by domain

Functional requirements:
1. Consult mode
   - accept area, domains, question, paths, and optional task context
   - retrieve only the relevant active standards, patterns, and open findings
   - return a structured consult response containing:
     - applicable_rules
     - approved_patterns
     - open_findings
     - guidance
     - risks
     - confidence

2. Audit mode
   - accept domains and repo or subsystem scope
   - run domain evaluators
   - return scores, findings, drift summaries, recommended actions, and metadata
   - write machine-readable output files and a human-readable markdown report

3. Findings lifecycle
   - define structured finding schema
   - support statuses:
     - open
     - accepted
     - waived
     - resolved
     - false_positive
     - superseded
   - support waivers with reason and expiry

4. Scoring
   - produce per-domain scores from 0 to 100
   - scoring must be deterministic and documented
   - high severity unresolved issues should materially reduce score

5. CLI
   - expose at least:
     - consult
     - audit
     - report
     - findings

6. Output files
   - open findings
   - findings history
   - area summaries
   - latest review report

Non-goals for phase 1:
- no autonomous code-fixing
- no hard CI blocking by default
- no dependence on screenshots or Figma yet
- no one giant evaluator covering all domains

Technical expectations:
- favour clarity and maintainability over cleverness
- make schemas explicit
- keep evaluators modular and testable
- use structured JSON outputs as the system of record
- keep markdown reports as generated summaries, not primary data
- include confidence on inferred findings
- add sample standards and at least one working end-to-end example
- include tests for schemas, retrieval, and evaluator output shape

Design expectations:
- keep the framework generic enough for multiple repos or subsystems
- do not hardcode Mapp-specific architecture assumptions unless expressed as standards
- make it straightforward to add UX, design system, and product evaluators in phase 2

Deliverables:
- working project structure
- schema definitions
- standards registry scaffolding with example rules
- extractors and normaliser
- retrieval module
- governance evaluator
- architecture evaluator
- findings store
- report generator
- CLI commands
- sample outputs under /output
- tests
- README with local usage instructions and extension model

Also produce:
1. a short architecture overview
2. a list of assumptions
3. a list of open extension points for phase 2 and phase 3

Do not collapse everything into a single file unless there is a compelling reason.
Do not create a vague chatbot.
Build a proper structured tool.
```

---

## 29. Practical note

I would not ask Claude Code to build all five domains in one go. That’s how you get sludge and half-baked abstraction.

I’d use the prompt above but explicitly tell it to complete **phase 1 only** first:

* registry
* schemas
* consult
* audit
* governance evaluator
* architecture evaluator
* findings store
* reports
* CLI

Then do a second pass for:

* UX / IA
* design system
* product coherence

That will go much better.

---

## 30. Additional implementation prompt: engineering build brief

Use this if you want a more execution-focused prompt for Claude Code after the high-level spec.

```text
Implement phase 1 only of the Standards Consultant and Audit Service.

Goal:
Stand up a working structured tool, not a concept demo.

Scope for this phase:
- standards registry
- explicit schemas
- repo extractors
- normaliser
- retrieval layer
- governance evaluator
- architecture evaluator
- findings storage
- report generator
- CLI commands
- tests
- sample outputs

Requirements:
- choose a clean modular structure
- use structured JSON outputs as the source of truth
- generate markdown reports from structured findings
- keep scoring deterministic and documented
- keep evaluators separate
- include confidence on inferred findings
- include a clear README

Consult mode must:
- accept area, domains, question, paths, and task context
- retrieve relevant active rules, patterns, and open findings
- return a structured consult response

Audit mode must:
- accept scope and requested domains
- run governance and architecture evaluators
- write output files for open findings, history, and latest report
- return per-domain scores and recommended actions

Do not implement UX, design system, or product evaluators yet except for scaffolding and extension points.
Do not implement auto-fixing.
Do not make this CI-blocking by default.

Provide:
1. code
2. sample standards
3. example consult request and response
4. example audit request and response
5. tests
6. README
7. explanation of extension points

Optimise for maintainability and future extension, not maximum cleverness.
```

---

## 31. Additional implementation prompt: consult and audit contracts

Use this if you want Claude Code to focus on contract quality first.

```text
Design and implement the contracts for a Standards Consultant and Audit Service.

Focus on:
- consult request and response schemas
- audit request and response schemas
- finding schema
- waiver schema
- findings store schema
- area summary schema
- standards rule schema

Then implement:
- validation logic
- sample fixtures
- tests for valid and invalid payloads
- clear documentation of each contract

Principles:
- explicit and strict where useful
- extensible without breaking changes
- clear support for confidence, evidence, severity, lifecycle status, and standards versioning
- suitable for both human inspection and agent consumption

Do not build the full service first.
Get the contracts right.
```

---

## 32. Additional implementation prompt: standards registry scaffolding

Use this if you want to force good structure in the standards layer before implementation logic expands.

```text
Create the standards registry scaffolding for a Standards Consultant and Audit Service.

Need:
- standards directory structure by domain
- example rule files for governance and architecture
- index files per domain
- top-level standards index
- rule metadata model with version, status, severity, scope, signals, exceptions, related patterns
- example architecture patterns and governance rules
- documentation for how to add, version, deprecate, and archive standards

Output should be concrete and usable by code.
Do not leave this as a vague markdown outline.
```

---

## 33. Additional implementation prompt: future phase scaffolding for UX, design and product

Use this after phase 1 exists.

```text
Extend the existing Standards Consultant and Audit Service by adding scaffolding and initial evaluator implementations for:
- UX / IA
- design system
- product coherence

Requirements:
- preserve the existing consult and audit contracts
- add rule and pattern structures for these domains
- implement evaluators as separate modules
- keep output structured
- add sample standards and fixtures
- make confidence explicit where inference is weak

Do not redesign phase 1.
Extend it cleanly.
```

---

## 34. Suggested rollout plan for the local team

### Step 1

Build phase 1 against one bounded subsystem.

### Step 2

Use it in advisory mode only for a couple of weeks.

### Step 3

Tune false positives, confidence scores, and standards wording.

### Step 4

Add UX / IA and design system domains.

### Step 5

Integrate targeted audit into PR workflows as warnings.

### Step 6

Only later consider stronger gating on high-confidence, high-severity regressions.

---

## 35. Blunt conclusion

This is worth doing.

If you are serious about multi-agent development, without something like this you will keep getting:

* governance drift
* architecture decay
* mediocre front ends
* repo-specific folklore instead of reusable standards
* agents starting cold every time

The right model is:

* central standards
* consult before implementation
* audit after implementation
* persistent findings as shared quality memory

That is how you turn scattered agent work into something more like an operating system for quality.
