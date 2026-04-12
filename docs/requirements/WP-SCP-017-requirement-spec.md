# RequirementSpec — WP-SCP-017 Service API and Project Overlays

**Work Package:** `WP-SCP-017`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Implementation Branch:** `feature/wp-scp-017-service-and-overlays`

## 1. Purpose

Expose consult and audit operations through a lightweight service interface and
allow projects to layer local standards overlays on top of the shared registry.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-1701 | The system shall support loading one or more overlay registries on top of the shared standards registry in deterministic order. |
| FR-SCP-1702 | Overlay registries shall be able to add new rules and patterns or replace base rules and patterns by identifier. |
| FR-SCP-1703 | CLI consult, audit, audit-changed, show-registry, and service modes shall accept the same overlay configuration. |
| FR-SCP-1704 | The service API shall expose at least `GET /health`, `GET /registry`, `POST /consult`, and `POST /audit`. |
| FR-SCP-1705 | The service API shall reuse the existing consult and audit builders rather than introducing parallel request handling logic. |
| FR-SCP-1706 | The service slice shall remain local and unauthenticated in this phase; access control lands later. |

## 3. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-017-001 | Overlay registry loading merges overlay rules and patterns deterministically and supports identifier-based replacement. | pytest |
| AC-WP-SCP-017-002 | Consult and audit paths honour overlay registries, including changed severity or guidance where overlay rules replace base rules. | pytest |
| AC-WP-SCP-017-003 | The service API serves health, registry, consult, and audit responses over HTTP using the same underlying contracts as the CLI. | pytest |
| AC-WP-SCP-017-004 | The work package leaves a complete evidence pack under `docs/reviews/WP-SCP-017/`. | manual review |
