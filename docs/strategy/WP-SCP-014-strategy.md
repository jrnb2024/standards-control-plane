# Strategy — WP-SCP-014 Changed-File Scoped Audit

**Work Package:** `WP-SCP-014`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Strategy

Keep changed-file audit as a thin layer over the existing audit builder:

- resolve changed files from git
- build an ordinary audit request from those paths
- return the wrapped result with the changed-path context attached

This avoids splitting the evaluator model or adding special per-domain logic.
