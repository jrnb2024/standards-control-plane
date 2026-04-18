# Strategy — WP-SCP-019 Service Auth Contract (SVC-003)

**Work Package:** `WP-SCP-019`
**Version:** 0.1
**Status:** Draft
**Date:** 2026-04-18

## 1. Strategy

Treat SVC-003 the same way SVC-001 treats the runtime contract: the rule
requires the service to *declare* which auth modes it accepts, and the
auto-check validates that the declaration matches implementation against a
closed set of estate-approved modes.

This keeps three competing pressures aligned:

- **Estate reality has three live token types** (CT JWT RS256, service JWT
  HS256, API key). A single fixed mechanism breaks machine callers.
- **Free-form declaration produces drift.** A closed enum of four modes
  prevents apps from inventing new shapes without a standards change.
- **Existing implementations stay valid.** Commit `66ba8a4` becomes the
  reference for `mode.user_oidc`; WP-SCP-018's `--auth-token` path is
  classified as `mode.bearer_legacy` with an explicit deprecation close date
  rather than deleted.

Delivery is phased so the rule and evaluator land together; the estate-wide
`--auth-token` migration runs as separate per-app work packages after the
freeze lifts.

## 2. Sequencing

- 019A publishes the rule and mode spec so downstream slices have a stable
  reference.
- 019B/C stand up the evaluator and audit wiring so the rule is enforceable.
- 019D dogfoods against a known-conformant pilot (`mapp-pim`) before the rule
  is generalised to adopters.
- 019E rewrites ADOPT-001 §11 only after the rule and evaluator are proven
  against a real service.
- 019F publishes, updates STATUS.md, and records D-019.
