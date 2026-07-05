# RequirementSpec — WP-SCP-014 Changed-File Scoped Audit

**Work Package:** `WP-SCP-014`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12  
**Implementation Branch:** `feature/wp-scp-014-changed-audit`

## 1. Purpose

Add a git-aware changed-file audit mode suitable for PR workflows while keeping
the scope repo-bounded and deterministic.

> **Superseded in part by D-066 (2026-07-05).** FR-SCP-1401's "SCP-repo-bounded"
> constraint is lifted: `audit_changed` now accepts an explicit `repo_root`
> naming another estate git worktree, and the `git diff` + evaluator reads are
> bounded to *that* root instead of the SCP repo. Determinism and the
> path-escape boundary (now enforced relative to the supplied root) are
> retained.

## 2. Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-SCP-1401 | The system shall resolve changed files from git refs using a repo-bounded `git diff` path. **(D-066: "repo" = the supplied `repo_root` worktree, defaulting to the SCP repo.)** |
| FR-SCP-1402 | The system shall ignore deleted or non-existent paths when building a changed-file scoped audit request. |
| FR-SCP-1403 | The CLI shall expose an `audit-changed` command that accepts base ref, head ref, domains, subsystem, standards version, and optional area id. |
| FR-SCP-1404 | The changed-file audit result shall expose the resolved changed paths alongside the underlying audit result. |

## 3. Acceptance Criteria

| ID | Acceptance Criterion | Verification |
|----|----------------------|-------------|
| AC-WP-SCP-014-001 | The changed-file resolver returns deterministic, repo-relative changed paths in a temp git repo. | pytest |
| AC-WP-SCP-014-002 | The changed-file audit builder accepts explicit changed paths and returns a schema-valid changed-audit result. | pytest |
| AC-WP-SCP-014-003 | The work package leaves a complete evidence pack under `docs/reviews/WP-SCP-014/`. | manual review |
