# SVC-003 FREEZE DIRECTIVE — Standards Control Plane (SCP)
Posted 2026-04-18 · Ref: D-019 / WP-SCP-019

## Why
This is where SVC-003 LIVES. SCP drives the freeze, not subject to it. BUT:
two auth shapes currently coexist in this repo:
- bearer `--auth-token` path from WP-SCP-018 (merged)
- CT OIDC layer from post-closeout commit 66ba8a4 (ct_auth vendor wheel,
  JWKS via `CT_JWKS_URL`, audience via `CT_APP_ID`)

WP-SCP-019 reconciles them. Estate owner ratified the shape on 2026-04-18:
- SVC-003 is declare-a-contract with a closed set of approved modes
  (`mode.user_oidc`, `mode.service_rs256`, `mode.api_key`,
  `mode.bearer_legacy`).
- 66ba8a4's CT OIDC IS the reference shape for `mode.user_oidc` — no rework
  forced on that commit.
- `--auth-token` from WP-SCP-018 classifies as `mode.bearer_legacy` with
  deprecation close date decided during WP-SCP-019 authoring.

## CAN CONTINUE
- **WP-SCP-019 authoring** — SVC-003 rule, `evaluators/service_lifecycle.py`,
  auto-check, fixtures, tests. Unblocks the whole freeze.
- **`evaluators/service_lifecycle.py` stand-up** — SVC-001 and SVC-002 rules
  exist but have no evaluator; both silently uncovered today. Fix as part of
  WP-SCP-019.
- **Bug fixes** in consult/audit CLI.
- **Findings store hardening** (SCP-038/039 later backlog).
- **Calibration / false-positive tuning.**
- **ADOPT-001 §1-10** (install, overlays, wrappers, findings, governance,
  CI, local CLI) — orthogonal.
- **SCP-070 cloudflared tunnel hygiene** (uncommitted BACKLOG.md entry) —
  proceed as previously planned.
- **D-019 decision row authored in DECISIONS.md** as part of WP-SCP-019 PR.

## PAUSE / FREEZE
- **ADOPT-001 §11 (shared service mode bearer auth)** — rewrite blocked on
  SVC-003 mode decisions. Do not evangelise current `--auth-token` shape.
- **Post-closeout CT OIDC layer (commit 66ba8a4)** — LEAVE AS-IS during
  freeze. Do not modify; it's the reference.
- **New bearer-token extensions** — no, do not extend the `--auth-token`
  path.
- **SCP-070 ID for CT-integration tickets** — wrong. SCP-070 is taken by
  cloudflared. CT integration work uses **SCP-071**.
- **STATUS.md / BACKLOG.md updates for WP-SCP-019** — do in the same PR as
  019 authoring, not ad-hoc.

## IF IN DOUBT
Ask the user.

## UNFREEZE TRIGGER
WP-SCP-019 merged + SVC-003 published in `standards/service-lifecycle/rules/`
+ `evaluators/service_lifecycle.py` covering SVC-001/002/003 + reconciliation
of bearer and CT OIDC shapes documented in ADOPT-001 §11.
