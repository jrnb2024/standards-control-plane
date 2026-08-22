# GOV-005 — Estate Operating Stance Is Dev/Staging Only

**Domain:** governance  
**Version:** 1.0.0  
**Status:** active  
**Severity default:** medium

This is a single-operator dev/staging estate with no live customers. Every instance
is dev or staging; there is no production tier. Prod-grade gates, secret-rotation
alarms, multi-week soak windows, and cost-gating are overhead here and must not be
applied. Verify correctness directly and decide on "it works or it doesn't"; still
go through the PR workflow and never silently descope. Revisit this stance at the
first production launch (none planned).

## Signals

- a change or review that treats an estate instance as production, or applies a prod-only gate, with no live-customer basis (Hetzner is staging; AWS / `*.brokapps.ai` boxes labelled 'production' are staging/demo)
- a dev/demo secret or in-chat PAT flagged for rotation as a current blocker
- a multi-week observation/soak window or calendar gate imposed on a dev decision
- cost used as a reason to block, slow, descope, or deprioritise feature work before go-live

## Rationale

Re-litigating the same operating stance every session wastes the operator's time and
the agent's context. Codifying it once, in the SCP, lets every session apply it
consistently: ship pragmatically, gate on correctness rather than calendar or cost,
and reserve production-grade rigour for an actual production launch.
