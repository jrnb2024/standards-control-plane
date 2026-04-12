# TechnicalArchitecture — WP-SCP-017 Service API and Project Overlays

**Work Package:** `WP-SCP-017`  
**Version:** 0.1  
**Status:** Draft  
**Date:** 2026-04-12

## 1. Objective

Expose a lightweight shared-service mode and overlay mechanism without forking
the core consult and audit logic.

## 2. Proposed components

### Registry overlay merge

- extend `load_registry` to accept overlay registries
- merge overlay rules and patterns by identifier
- keep overlay application order explicit and deterministic

### `service.py`

- provide a minimal HTTP server using stdlib facilities
- expose `GET /health`, `GET /registry`, `POST /consult`, and `POST /audit`
- reuse existing consult and audit builders

### CLI

- add `--overlay` support to registry-dependent commands
- add a `serve` command for local shared-service mode
