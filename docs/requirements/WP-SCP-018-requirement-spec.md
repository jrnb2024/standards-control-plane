# RequirementSpec — WP-SCP-018 Auth, Multi-Repo Reporting, and Richer Evidence Adapters

**Work Package:** `WP-SCP-018`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Implementation Branch:** `feature/wp-scp-018-auth-reporting-evidence`

## 1. Purpose

Add a minimal access model for shared service use, expose portfolio-style
reporting across repo outputs, and broaden the extracted evidence model with
explicit richer-adapter buckets.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-1801 | The local HTTP service shall support an optional bearer-token access model that protects consult, audit, and registry endpoints while leaving `GET /health` public. |
| FR-SCP-1802 | The CLI shall expose the service auth configuration without changing the unauthenticated default from the previous phase. |
| FR-SCP-1803 | The system shall build a schema-valid multi-repo dashboard from one or more repo output roots containing Control Tower dashboard artifacts. |
| FR-SCP-1804 | The system shall persist a simple trend view that compares the latest multi-repo dashboard to prior persisted portfolio snapshots. |
| FR-SCP-1805 | Extraction and normalisation shall recognise Storybook metadata, screenshot artifacts, and graph artifacts as explicit evidence buckets. |
| FR-SCP-1806 | Richer evidence adapters shall extend the existing extracted-scope and project-area contracts without changing the meaning of existing buckets. |

## 3. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-018-001 | Service requests fail without the configured bearer token and succeed with it, while `GET /health` remains open. | pytest |
| AC-WP-SCP-018-002 | Multi-repo dashboard and trend outputs validate against their schemas and aggregate repo-level estate summaries deterministically. | pytest |
| AC-WP-SCP-018-003 | Extraction and normalisation place Storybook, screenshot, and graph artifacts into explicit buckets without disturbing existing bucket behaviour. | pytest |
| AC-WP-SCP-018-004 | The work package leaves a complete evidence pack under `docs/reviews/WP-SCP-018/`. | manual review |
