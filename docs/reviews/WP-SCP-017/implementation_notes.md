# WP-SCP-017 Implementation Notes

## Implementation summary

- extended `load_registry` to merge overlay registries deterministically
- threaded merged registry snapshots into consult, audit, changed-audit, and evaluator rule lookup
- added `service.py` with:
  - `GET /health`
  - `GET /registry`
  - `POST /consult`
  - `POST /audit`
- extended CLI commands with `--overlay` support
- added `serve` CLI command for local shared-service mode
- updated README command surface

## Review outcome

The main review fix was to push overlay-aware registry snapshots all the way
through evaluator rule loading, so service mode and CLI audit mode behave the
same way when an overlay replaces base rule metadata.
