# Standards Control Plane — Decision Log

**Last Updated:** 2026-04-11

| ID | Date | Decision | Status | Rationale |
|----|------|----------|--------|-----------|
| D-001 | 2026-04-11 | Use Python for the phase 1 CLI-first implementation | ACCEPTED | Fast path to explicit schemas, local tooling, JSON validation, and deterministic file-based execution |
| D-002 | 2026-04-11 | Keep the project as a standalone app rather than extending docs-agent or Control Tower directly | ACCEPTED | Keeps evaluator runtime independent while still allowing later integration with both systems |
| D-003 | 2026-04-11 | Limit the first governed implementation slice to standards registry loading, minimal findings loading, and consult retrieval | ACCEPTED | Keeps the first end-to-end work package narrow enough to review rigorously while still allowing real consult output |
| D-004 | 2026-04-11 | Introduce an explicit project-area intermediate representation before evaluator implementation | ACCEPTED | Keeps evaluator inputs deterministic, testable, and independent from raw repo sprawl |
| D-005 | 2026-04-11 | Wire governance evaluation through the audit CLI before attempting architecture evaluation | ACCEPTED | Establishes one real evaluator path end to end before widening the audit surface |
| D-006 | 2026-04-11 | Extend audit and project-area contracts before WP-SCP-003 implementation | ACCEPTED | Governance review evidence and unsupported-domain coverage must be first-class structured data, not implied by prose or raw path scanning |
| D-007 | 2026-04-11 | Use an explicit unattended-delivery protocol for the remaining programme | ACCEPTED | The remaining work should continue without waiting for user answers, using documented default decisions, bounded review loops, and backlog carry-forward for non-blocking residuals |
