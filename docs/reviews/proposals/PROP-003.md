---
adjudication_status: accepted
accepted_as: GOV-005
accepted_at: 2026-06-28
accepted_note: adjudicated into standards/<domain>/rules/GOV-005-*.md + index.json; live via consult_rules
expected_review_date: null
queued_at: 2026-06-27T22:32:05Z
---
> NOTE: WP-SCP-022-proposal-queue adjudication workflow is not yet live;
> proposals queue until adjudication ships. Status updates via
> GitHub issue on this branch (proposals/PROP-003). See
> docs/plans/WP-SCP-022-implementation-programme-plan.md §12.

<!-- proposal_metadata: {"affected_repos":["jrnb2024/kg-studio","jrnb2024/mapp-pim","jrnb2024/control-tower","jrnb2024/acc","jrnb2024/mapp-returns-intelligence","jrnb2024/mapp-size-allocation","jrnb2024/mapp-estate-dashboard","jrnb2024/standards-control-plane"],"caller_id":"stdio:30251:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server","mcp_origin":true,"proposal_hash":"90cd6222d44e6d0ba9aba07ceea866a995d5430c7e8de557df10a3416597639f","rule_id":null,"signing_key_id":"428dfee16bc954ad"} -->

# PROP-003: GOV-005 (candidate): Operating stance — dev/staging-only estate, no production tier, no governance theatre, cost is never a gate

## Proposal Envelope
- mcp_origin: true
- caller_id: stdio:30251:/Users/amplience/Projects/standards-control-plane/.venv-mcp/bin/scp-mcp-server
- signing_key_id: 428dfee16bc954ad

## Affected Repositories
- jrnb2024/kg-studio
- jrnb2024/mapp-pim
- jrnb2024/control-tower
- jrnb2024/acc
- jrnb2024/mapp-returns-intelligence
- jrnb2024/mapp-size-allocation
- jrnb2024/mapp-estate-dashboard
- jrnb2024/standards-control-plane

## Rule Context
null

## Proposal Body
## GOV-005 (candidate) — Estate operating stance (dev/staging only)

**Status:** proposed (new rule, `governance` domain). Migrates the operator's standing operating-mode preference (solo operator, James) out of per-project memory into the SCP as the canonical estate stance, so every session applies it without re-stating it.

**Stance.**
1. **No production tier — ever.** Every instance is dev or staging. Hetzner (`mapp-staging-1`, 178.104.238.60) = STAGING. AWS / `*.brokapps.ai` boxes labelled 'production' (e.g. `adaptivelabeller.brokapps.ai`, 'mapp-demos') are STAGING/demo. Do NOT treat any instance as prod or apply prod-grade gates.
2. **Dev/demo secrets are not rotation blockers.** Rotation is a go-live concern only. Do not flag dev/demo secrets or in-chat PATs for rotation as a current blocker.
3. **No governance theatre.** No multi-week observation/soak windows or calendar gates in dev. Decisions are made on "it works or it doesn't": verify correctness directly, then decide (keep / drop / promote). Bias to pragmatic shipping. (Still: verify correctness, never silently descope, always go through the PR workflow — see GOV-003 / the build-method standard.)
4. **Cost is never a decision gate (until live).** No cost framing — programme, opportunity, engineering-capacity, calendar-irreversibility — may block, slow, descope, or deprioritise feature work. State calendars factually. Cost savings are welcome as a benefit (caching, model choice), never as a gate. Mention spend only if >10× normal. Do not convert LOC to $/FTE via pre-AI benchmarks.

**Why.** This is a single-operator dev/staging estate with no live customers. Prod-grade gates, rotation alarms, soak windows, and cost-gating are pure overhead here and repeatedly waste sessions re-litigating settled stance. Re-evaluate stance at go-live (none planned).

**Signals (audit / session behaviour).**
- a change or review that treats an estate instance as production, or applies a prod-only gate, with no live-customer basis
- a dev/demo secret flagged for rotation as a current blocker
- a multi-week observation/soak window or calendar gate imposed on a dev decision
- cost used as a reason to block, slow, descope, or deprioritise feature work before go-live

**applies_to:** `docs/**/*.md`, `docs/DECISIONS.md`, `docs/STATUS.md`, `**/services.yml`   **severity_default:** medium   **scope:** all   **exceptions:** none while the estate is pre-go-live (revisit on first production launch).
