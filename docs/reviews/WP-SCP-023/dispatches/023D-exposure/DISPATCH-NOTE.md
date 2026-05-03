# WP-SCP-023 slice 023D — exposure surface (markdown report + MCP method) (dispatch note)

**Date:** 2026-05-03
**Tier:** orchestrator-applied (Tier 1) per `feedback_four_tier_dispatch.md`. Markdown report generator + MCP method + onboarding doc are mechanical translations of plan-doc §5; no design rework.
**Files D-043:** ratifies the MCP method `scp.consult_scorecard` shape + read-only contract per WP-SCP-023 plan-doc §9 reservation.
**Cuts:** no version bump for the markdown report (internal-only render of an already-public-via-git index). The MCP method addition IS public surface but it adds a new method (additive) — would normally be MINOR per VERSIONING.md, **EXCEPT** the MCP server is a separate transport that is NOT enumerated in the federation primitive's VERSIONING.md scope (see VERSIONING.md §"Scope" — only `policy-check.yml` workflow_call inputs + JSON Schemas + SCP-R-NNN rule IDs are in scope). The MCP server (per WP-SCP-021) has its own deployment cadence + its own schema-versioned responses (`schema_version: "1.0.0"` on each response). Adding a new method does not break the MCP server's response contract. **No federation primitive version bump.**

## Rationale

WP-SCP-023 023A plan-doc + 023B emitter (v1.2.0 LIVE) + 023C aggregator are all merged. 023D is the consumer-facing exposure surface: an auto-generated markdown report (operator/auditor consumption) + an MCP method (agent/tooling consumption).

## Scope decision — IN / OUT

### IN

| Item | Rationale |
|---|---|
| `scripts/generate-scorecard-report.py` (NEW) | Reads `output/scorecards/index.json` + emits `docs/scorecards/<YYYY-MM-DD>.md` markdown report. Standalone Python script (no new deps; uses jsonschema + stdlib). Aggregator workflow extended to invoke this in the commit job before opening the PR. |
| `.github/workflows/scorecard-aggregator.yml` — extend `commit` job to run the markdown generator + `add-paths` to include the new markdown file in the PR. | Markdown report ships in the same operator-review PR as the index, so review surface is unified. |
| `src/standards_control_plane/mcp_server/tools.py` — new `consult_scorecard` MCP method | Per plan-doc D-043. Read-only contract: returns aggregated metrics from `output/scorecards/index.json` + verification status. NEVER returns waiver content. Pattern follows `consult_rules` (request/response Pydantic models + `_log_tool_invocation` + registered via `server.tool(name="consult_scorecard", ...)`). |
| `tests/scorecard-mcp/test_consult_scorecard.py` — pytest validating the new MCP method against fixtures | 4 fixtures: empty index, single-verified, single-failure, repo-filter. Reuses the index-fixture corpus from 023C. |
| `tests/scorecard-report/test_scorecard_report.py` — pytest validating markdown generator | 3 fixtures (golden-file comparison): empty index → "no adopters opted in" placeholder; single-verified; mixed (verified + verification_failure + unreachable). |
| `docs/adoption/ADOPT-001-project-onboarding.md` §13 (NEW) | Adopter onboarding for cross-repo scorecards. Names: how to opt in (PR to `opt-in-registry.yaml`); what's in the emit (counts only, NEVER waiver content); how to read the central index + markdown report; how to query via MCP method. |
| `docs/DECISIONS.md` D-043 row | Ratifies the MCP method shape + read-only contract. |
| `STATUS.md` — 023D chain row | Convention. |

### OUT

| Item | Rationale |
|---|---|
| Tag cut + GitHub release | No federation primitive version bump (per Cuts above). The MCP server's deployment is governed by WP-SCP-021's deployment cadence. |
| Threshold A onboarding (≥3 adopters opted in) | Slice 023E scope. |
| `scp.audit_scorecard_changed` method | Plan-doc §1 names this as forward-looking; 023D ships the read-only `consult_scorecard` method only. `audit_scorecard_changed` would be a write surface (against MCP receipt records) and is out of scope per invariant 5 (read-only). Filed forward as TF-023D-001 if needed. |
| Cross-repo notification to ACC / CT / mapp-estate-regression (TF-023A-002) | Defer to 023E when adopters can actually participate. The exposure surface ships now; estate-wide announcement pairs with first-adopter onboarding. |
| Self-dogfood opt-in (TF-023C-001) | Slice 023E; we want to onboard SCP-self at the same time we onboard the first real adopter (FLA) so the first markdown report has 2+ rows. |
| markdown report retention policy | Plan-doc §10 Q4 names "keep last 90 days + compact older" as the likely answer. Implementation deferred until ~13 weekly reports accumulate (~Q3 2026). Filed forward as TF-023D-002. |
| MCP method authentication | Plan-doc invariant 5 says "MCP exposure is read-only". The MCP server's existing auth posture (per WP-SCP-021) handles this — `consult_scorecard` rides on the same Ed25519-signed receipt mechanism as other consult methods. No new auth primitive in this slice. |

## Tier-justification

Orchestrator-applied + 3-lens R1+R2 (per `feedback_four_tier_dispatch.md`). Markdown generator is ~80 lines of Python + Jinja-style format-string templating; MCP method is ~60 lines of Pydantic model + impl + registration; ADOPT-001 §13 is ~60 lines of prose. All are mechanical translations of plan-doc §5 + 023A/B/C precedents. If R1 surfaces a CRIT/MAJ requiring spec rework, escalate.

## Slice acceptance

- [ ] **(i) `scripts/generate-scorecard-report.py`** with deterministic output (sort_keys, no timestamps in body), Markdown shape: header + per-adopter table + drift section (versus prior report if available) + footer.
- [ ] **(ii) `.github/workflows/scorecard-aggregator.yml`** commit job extended: runs the markdown generator + adds the new file to the PR's add-paths.
- [ ] **(iii) `src/standards_control_plane/mcp_server/tools.py`** has `ConsultScorecardRequest`, `ConsultScorecardResponse`, `consult_scorecard_impl`, `consult_scorecard`, registered via `register_tools`.
- [ ] **(iv) `consult_scorecard` request shape**: `repo_filter: str | None` (single repo or omit for all), `since_emitted_at: str | None` (ISO-8601). Response: `aggregated_at`, `aggregator_run_id`, `adopters: list[ConsultScorecardAdopterRow]` with shape (repo, status, verdict, scp_version, last_emit_emitted_at, rule_count_summary, error). NO raw waiver content; NO unbounded fields.
- [ ] **(v) Pytest** `tests/scorecard-mcp/test_consult_scorecard.py` — 4 cases (empty / single-verified / single-failure / repo-filter); request/response shape validated.
- [ ] **(vi) Pytest** `tests/scorecard-report/test_scorecard_report.py` — 3 golden-file fixtures (empty / single / mixed).
- [ ] **(vii) ADOPT-001 §13** with: opt-in PR workflow, emit privacy contract, how to read the central index, how to query via MCP, troubleshooting common failures (verification_failure / unreachable / no_emit).
- [ ] **(viii) D-043 row in `docs/DECISIONS.md`** + Last Updated.
- [ ] **(ix) STATUS.md 023D chain row + D-043 in Recent decisions.**
- [ ] **(x) NEVER-waiver-content** invariant maintained: the MCP method response shape excludes `reason`/`approved_by`/`waiver_id`; pytest scan confirms.
- [ ] **(xi) Pre-push wrapper passes** + all prior tests pass (35 + 4 + 3 = 42 expected).
- [ ] **(xii) Adversarial review reaches fixpoint** — 3-lens R1 → recurse to fixpoint.
- [ ] **(xiii) PR + CI green + operator-merge per D-040.**

## Risk surface

1. **MCP method enumeration** — could a hostile agent enumerate all adopter waivers via repeated calls? Mitigation: response carries aggregated counts only (waiver content excluded by Pydantic model). Existing MCP rate-limit + receipt mechanism caps abuse.
2. **Markdown drift** — auto-generated markdown could be hand-edited by an operator before merging the aggregator PR. Mitigation: regenerator overwrites on next run; the markdown is informational.
3. **`consult_scorecard` reads stale index** — MCP server reads `output/scorecards/index.json` from the SCP repo's git working copy at MCP-call time. If the aggregator hasn't run for a week, the index is stale. Mitigation: response includes `aggregated_at` so consumers see the staleness; cron-health TF-023C-002 handles the structural gap.
4. **Empty-index responses** — when no adopters are opted in (Threshold A pre-state), the response is `adopters: []`. Verify this returns cleanly; consumers should not crash.
5. **`since_emitted_at` filter** — must accept ISO-8601 + reject malformed input via Pydantic validator. Mitigation: Pydantic `Field` constraint + try/except in impl.

## R1 review focus

- **Correctness**: markdown generator output shape matches plan-doc §5 spec; MCP method's request/response Pydantic models match the established pattern; new method registered correctly; ADOPT-001 §13 cross-references to 023B/023C accurate.
- **Safety**: MCP response NEVER carries waiver content (verify schema-level + runtime); no new authentication surface introduced; markdown report doesn't expose adopter-side error strings beyond what's already in the index; the MCP method file path resolution stays inside the SCP repo's `output/scorecards/index.json` (no path-traversal).
- **Completeness**: AC items (i)–(xiii) all addressable; D-043 row complete; ADOPT-001 §13 covers the four common failure modes; cross-repo notification (TF-023A-002) updated for 023D readiness.

## Files

### Modified
- `.github/workflows/scorecard-aggregator.yml` — commit job extension.
- `src/standards_control_plane/mcp_server/tools.py` — new method.
- `docs/adoption/ADOPT-001-project-onboarding.md` — §13.
- `docs/DECISIONS.md` — D-043 row.
- `STATUS.md` — 023D chain row + D-043.

### Added
- `scripts/generate-scorecard-report.py`
- `tests/scorecard-mcp/test_consult_scorecard.py`
- `tests/scorecard-mcp/fixtures/{empty,single-verified,single-failure,multi-with-filter}/{index.json, expected-response.json}`
- `tests/scorecard-report/test_scorecard_report.py`
- `tests/scorecard-report/fixtures/{empty,single,mixed}/{index.json, expected.md}`
- `docs/reviews/WP-SCP-023/dispatches/023D-exposure/{DISPATCH-NOTE.md, review-*-package.json, review-*.json, FIX-ROUND-N.md}`

## Forward-looking

- **TF-023D-001** (low priority): `scp.audit_scorecard_changed` MCP method (write-side; out of scope this slice).
- **TF-023D-002** (low priority): markdown report retention policy (keep last 90 days; compact older). Defer until ~Q3 2026.
- **D-043** filed in this slice.
