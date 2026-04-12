# TechnicalArchitecture — WP-SCP-014 Changed-File Scoped Audit

**Work Package:** `WP-SCP-014`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Objective

Expose a changed-file audit mode without changing the evaluator contracts.

## 2. Proposed components

### `changed_audit.py`

- resolve changed files from git refs
- build a changed-audit request wrapper
- call the existing audit builder

### CLI

- add `audit-changed`
- keep `--write-output` optional and reuse the existing persistence path
