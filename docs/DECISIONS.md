# Standards Control Plane — Decision Log

**Last Updated:** 2026-04-11

| ID | Date | Decision | Status | Rationale |
|----|------|----------|--------|-----------|
| D-001 | 2026-04-11 | Use Python for the phase 1 CLI-first implementation | ACCEPTED | Fast path to explicit schemas, local tooling, JSON validation, and deterministic file-based execution |
| D-002 | 2026-04-11 | Keep the project as a standalone app rather than extending docs-agent or Control Tower directly | ACCEPTED | Keeps evaluator runtime independent while still allowing later integration with both systems |
| D-003 | 2026-04-11 | Limit the first governed implementation slice to standards registry loading, minimal findings loading, and consult retrieval | ACCEPTED | Keeps the first end-to-end work package narrow enough to review rigorously while still allowing real consult output |
