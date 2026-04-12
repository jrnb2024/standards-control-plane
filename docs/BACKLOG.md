# Standards Control Plane — Backlog

**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-11

This backlog is the initial execution list for the standalone standards
consult-and-audit app.

## Phase 0 — Framing

| ID | Title | Priority | Status | Notes |
|----|-------|----------|--------|-------|
| SCP-001 | Create standalone repo and docs structure | P0 | done | Initial planning scaffold and reference capture |
| SCP-002 | Capture original specification verbatim | P0 | done | Keep source intent intact for future review |
| SCP-003 | Record placement recommendation and rollout strategy | P0 | done | New app, docs-agent integration later, CT surfacing later |
| SCP-004 | Define project naming, scope, and initial doc map | P1 | done | `standards-control-plane` chosen as working repo name |
| SCP-005 | Select pilot subsystem and seed review corpus | P1 | ready | Recommend Returns Intelligence |
| SCP-006 | Define unattended autonomous delivery protocol and programme queue | P0 | done | Default decisions, blocker rules, and work-package sequencing now live in repo docs |

## Phase 1 — Advisory MVP

| ID | Title | Priority | Status | Dependencies | Notes |
|----|-------|----------|--------|--------------|-------|
| SCP-010 | Define consult, audit, finding, waiver, and summary schemas | P0 | done | SCP-005 | Contracts first |
| SCP-011 | Build standards registry loader and validator | P0 | done | SCP-010 | Live loader now backs `consult` and `show-registry` |
| SCP-012 | Create governance and architecture rule scaffolding | P0 | done | SCP-011 | Structured rule metadata now lives in domain indexes |
| SCP-013 | Build repo extractor for docs, code paths, tests, and configs | P0 | done | SCP-010 | Repo-bounded extractor landed with explicit extracted-scope contract and symlink-safe scope handling |
| SCP-014 | Build area normaliser / intermediate representation | P0 | done | SCP-013 | Explicit project-area contract landed with fixture-backed docs/code-path normalisation |
| SCP-015 | Implement consult retrieval and response assembly | P0 | done | SCP-011, SCP-014 | Live consult now assembles rules, patterns, findings, guidance, and risks |
| SCP-015A | Add minimal findings-store read path for consult | P0 | done | SCP-010 | Read-only findings selection with domain scope plus exact area/path escalation and deterministic ordering |
| SCP-016 | Implement governance evaluator | P0 | done | SCP-012, SCP-014 | Live governance audit path merged via WP-SCP-003 |
| SCP-017 | Implement architecture evaluator | P0 | done | SCP-012, SCP-014 | Architecture evaluator and live audit path merged in WP-SCP-004 |
| SCP-018 | Implement full findings store lifecycle and markdown report generator | P0 | done | SCP-016, SCP-017 | Findings lifecycle and report generation landed across WP-SCP-005 to WP-SCP-007 |
| SCP-019 | Build CLI commands for consult, audit, findings, report | P0 | done | SCP-015, SCP-018 | `consult`, `show-registry`, and `findings` now exercise live data paths |
| SCP-020 | Create fixtures, example requests, example outputs | P1 | done | SCP-019 | Example consult response now mirrors real consult output and seeded pilot fixtures are inspectable in repo |
| SCP-021 | Add tests for contracts, retrieval shape, evaluators, report output | P0 | done | SCP-019 | Retrieval, findings, and CLI tests added; current local run is green |
| SCP-022 | Promote review evidence from path bucket to structured metadata contract | P1 | done | SCP-016 | Structured review-evidence contract landed in WP-SCP-008 |

## Phase 2 — Findings Lifecycle and Retrieval Hardening

| ID | Title | Priority | Status | Dependencies | Notes |
|----|-------|----------|--------|--------------|-------|
| SCP-030 | Add finding lifecycle transitions and validation | P0 | done | SCP-018 | Lifecycle foundation landed in WP-SCP-005 |
| SCP-031 | Add waiver model with expiry handling | P0 | done | SCP-030 | Waiver expiry handling landed in WP-SCP-007 |
| SCP-032 | Implement finding identity, dedup, and history tracking | P0 | done | SCP-018 | Finding identity, dedup, and history tracking landed in WP-SCP-005 |
| SCP-033 | Implement deterministic score calculation and documentation | P1 | done | SCP-032 | Shared score model landed in WP-SCP-007 |
| SCP-034 | Generate area summaries and subsystem rollups | P1 | done | SCP-033 | Deterministic area summaries landed in WP-SCP-006 |
| SCP-035 | Build retrieval adapter for historical review docs | P1 | done | SCP-015 | Historical review retrieval landed in WP-SCP-008 |
| SCP-036 | Add optional docs-agent connector for consult enrichment | P2 | later | SCP-035 | Do not make phase 1 depend on it |
| SCP-037 | Run pilot on Returns Intelligence and tune false positives | P0 | done | SCP-021, SCP-032 | First pilot tuning pass landed in WP-SCP-008 |
| SCP-038 | Add crash-safe pair commit for persisted findings stores | P1 | later | SCP-032 | Current slice uses per-file atomic replacement plus rollback on caught failures; true crash-safe pair commit needs a stronger storage model |
| SCP-039 | Add crash-safe bundled commit for findings plus report artifacts | P1 | later | SCP-038 | Reporting will initially reuse the existing write-flow guarantees rather than invent a cross-artifact transaction |
| SCP-046 | Add score-model version tag to audit output | P2 | later | SCP-033 | Current phase documents score semantics in repo only; future score-model changes will need output-level traceability |
| SCP-047 | Cache parsed structured review evidence for repeated consult and audit calls | P2 | later | SCP-035 | Current phase reparses repo review markdown on demand; acceptable now, but not ideal for larger estates |

## Phase 3 — UX / Design / Product Expansion

| ID | Title | Priority | Status | Dependencies | Notes |
|----|-------|----------|--------|--------------|-------|
| SCP-040 | Add UX / IA standards scaffolding and evaluator shell | P1 | done | SCP-037 | UX evaluator shell landed in WP-SCP-010 |
| SCP-041 | Add design system standards scaffolding and evaluator shell | P1 | done | SCP-037 | Design evaluator shell landed in WP-SCP-011 |
| SCP-042 | Add product coherence standards scaffolding and evaluator shell | P2 | done | SCP-037 | Product evaluator shell landed in WP-SCP-012 |
| SCP-043 | Define confidence taxonomy and evidence classes | P0 | done | SCP-040 | Confidence taxonomy and evidence classes landed in WP-SCP-009 |
| SCP-044 | Add false-positive review loop and calibration pack | P0 | done | SCP-043 | Calibration and false-positive summary landed in WP-SCP-013 |
| SCP-045 | Tune consult output ordering for front-end implementation use | P1 | done | SCP-040, SCP-041 | Front-end consult ordering landed in WP-SCP-013 |

## Phase 4 — CI and Control Tower Surfacing

| ID | Title | Priority | Status | Dependencies | Notes |
|----|-------|----------|--------|--------------|-------|
| SCP-050 | Add changed-file scoped audit mode | P0 | done | SCP-032 | Changed-file audit landed in WP-SCP-014 |
| SCP-051 | Emit CI-friendly JSON and markdown outputs | P0 | done | SCP-050 | CI-facing JSON and markdown outputs landed in WP-SCP-015 |
| SCP-052 | Add warning thresholds for unresolved high-confidence regressions | P1 | done | SCP-051 | Advisory warning thresholds landed in WP-SCP-015 |
| SCP-053 | Design Control Tower integration surface | P1 | done | SCP-034 | Control Tower surface landed in WP-SCP-016 |
| SCP-054 | Publish subsystem summaries suitable for estate dashboards | P1 | done | SCP-053 | Estate dashboard outputs landed in WP-SCP-016 |

## Phase 5 — Shared Service Promotion

| ID | Title | Priority | Status | Dependencies | Notes |
|----|-------|----------|--------|--------------|-------|
| SCP-060 | Expose service API for consult and audit operations | P1 | done | SCP-051 | Service API landed in WP-SCP-017 |
| SCP-061 | Add project overlay mechanism | P0 | done | SCP-011 | Overlay-aware registry loading landed in WP-SCP-017 |
| SCP-062 | Add auth/access model for shared service use | P2 | done | SCP-060 | Optional bearer auth landed in WP-SCP-018 |
| SCP-063 | Build multi-repo reporting and trend views | P2 | done | SCP-054, SCP-060 | Multi-repo dashboard, history, and trend outputs landed in WP-SCP-018 |
| SCP-064 | Add richer evidence adapters (Storybook, screenshots, graphs) | P3 | done | SCP-044 | Richer evidence buckets landed in WP-SCP-018 |

## Not Before

Do **not** pull these forward into phase 1:

- screenshot or Figma analysis
- blocking CI thresholds
- product coherence scoring as an authoritative signal
- large model-dependent evaluator logic without deterministic baseline checks
- Control Tower runtime coupling
- docs-agent as a hard dependency for core rule selection
