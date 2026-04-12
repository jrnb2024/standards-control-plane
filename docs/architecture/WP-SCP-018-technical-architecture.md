# TechnicalArchitecture — WP-SCP-018 Auth, Multi-Repo Reporting, and Richer Evidence Adapters

**Work Package:** `WP-SCP-018`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Objective

Finish the scheduled programme with minimal shared-service governance, estate
reporting, and broader evidence intake.

## 2. Proposed components

### Service auth

- extend `service.py` with optional bearer-token enforcement
- keep `/health` unprotected
- wire `serve --auth-token`

### `estate_reporting.py`

- read Control Tower dashboard artifacts from multiple repo outputs
- build a portfolio dashboard
- persist a trend view over prior portfolio snapshots

### Extractor / normaliser contracts

- extend extracted scope classification support for:
  - Storybook metadata
  - screenshot artifacts
  - graph artifacts
- add matching project-area artefact buckets
