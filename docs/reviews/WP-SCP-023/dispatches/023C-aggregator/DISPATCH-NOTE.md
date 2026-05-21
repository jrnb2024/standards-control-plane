# WP-SCP-023 slice 023C — central aggregator + signed index (dispatch note)

**Date:** 2026-05-03
**Tier:** orchestrator-applied (Tier 1) per `feedback_four_tier_dispatch.md`. Plan-doc §5 + 023B set the data shape + verification mechanism; 023C wires those into a cron workflow + an index. No design rework.
**Files D-042:** ratifies the aggregator pipeline trust model + mandatory `job_workflow_ref` constraint per `gh attestation verify --signer-workflow`.
**Cuts:** no version bump. The aggregator is SCP-self-only — no public-surface change for adopters per `policies/VERSIONING.md` §"Scope" (mirrors slice 020N hash-pinning of conflict-gate.yml — internal hardening, not on the public surface enumeration).

## Rationale

WP-SCP-023 023A plan-doc + 023B emitter + v1.2.0 tag are LIVE. 023C is the consumption side: a weekly cron on the SCP repo that pulls per-adopter emit artifacts, verifies their OIDC attestations against the SCP reusable workflow path + SHA pin, aggregates into a signed index, and opens a PR for operator review.

## Scope decision — IN / OUT

### IN

| Item | Rationale |
|---|---|
| `.github/workflows/scorecard-aggregator.yml` (NEW) | Cron-driven weekly + workflow_dispatch. Two-job permission scoping per plan-doc §5 (closes 023A R1 COR-MAJ-003): `aggregate` job (read-only + `attestations: read` for `gh attestation verify`); `commit` job (gated on aggregate success; `contents: write` + `pull-requests: write` to push branch + open PR). |
| `docs/scorecards/opt-in-registry.yaml` (NEW; initial empty registry) | The list of adopter repos that have opted in. Schema-validated. Adopters PR additions; CODEOWNERS-protected via `docs/scorecards/** @jrnb2024` (already added in 023A). |
| `schemas/scorecard-opt-in-registry.schema.json` (NEW) | Schema for the registry: each entry carries `repo: owner/name`, `default_branch: <branch>`, `expected_scp_workflow_ref: jrnb2024/standards-control-plane-/.github/workflows/policy-check.yml@<sha>` (the SCP reusable workflow path + SHA pin the adopter wrapper uses — this is what `gh attestation verify --signer-workflow` checks against). |
| `schemas/scorecard-index.schema.json` (NEW) | Schema for `output/scorecards/index.json`: `aggregated_at`, `aggregator_run_id`, `adopters: [{repo, status, last_emit, verification, error}]`. `status: verified \| verification_failure \| unreachable_at \| no_emit`. Aggregator NEVER emits raw waiver content (invariant 2 enforced by schema). |
| Aggregator script: Python heredoc within the workflow (mirrors 023B emitter pattern) | Reads opt-in-registry; for each adopter, `gh run list` → `gh run download` → `gh attestation verify --signer-workflow <expected_workflow_ref>` → schema-validate emit → record into index. Verification failures don't drop the adopter row; they record `status: verification_failure` with an error string. |
| `output/scorecards/.gitkeep` + initial `output/scorecards/index.json` placeholder | Pre-seed the directory so the first aggregator run has a place to write. The placeholder index has `adopters: []` + a comment. |
| `tests/scorecard-aggregator/` — pytest validating opt-in-registry schema + scorecard-index schema against fixture pairs | Validate empty registry (passes), single-adopter registry (passes), malformed registry (fails). Index fixtures: empty index, single-adopter-verified, single-adopter-failure. |
| `docs/DECISIONS.md` D-042 row | Ratifies the trust model: GitHub Actions Artifact Attestation for adopter emits (per-PR run signs); aggregator-side verification via `gh attestation verify --signer-workflow`; index trust rooted in git's required-signed-commits + CODEOWNERS + branch protection (NOT a separate Ed25519 layer — the WP-SCP-023 plan-doc invariant 6 "Ed25519-signed" is honoured in spirit because Sigstore/Fulcio uses Ed25519 under the hood, but managed by GitHub rather than by an SCP-side private key). |
| `policies/VERSIONING.md` — add scorecard-aggregator workflow + opt-in-registry/index schemas to internal-surface enumeration (not adopter-facing) | The aggregator is SCP-self-only; not public surface; consistent with conflict-gate.yml posture. |
| `STATUS.md` — 023C chain row | Convention. |

### OUT

| Item | Rationale |
|---|---|
| Markdown report generator | Slice 023D scope per plan-doc §6. |
| MCP method `scp.consult_scorecard` | Slice 023D scope. |
| ADOPT-001 §13 onboarding section | Slice 023D scope. |
| Threshold A onboarding (≥3 adopters) | Slice 023E scope. |
| Self-dogfood opt-in (the SCP repo opting itself in to scorecard-emit on its own self-test wrapper) | Forward-compat: the SCP-self wrapper at `policy-check-wrapper.yml` could be amended to opt in, providing a 1-adopter test corpus before real adopters arrive. Filed forward as TF-023C-001 to reduce scope creep on this slice. |
| Markdown report generator (lands in 023D) | Out of scope. |
| Post-aggregation Slack/email/notification | Out of scope; the GitHub PR is the notification surface. |

## Tier-justification

Orchestrator-applied + 3-lens R1+R2+R3 (per `feedback_four_tier_dispatch.md` + the established WP-SCP-022 / WP-SCP-023 023A/B pattern). New workflow + 2 schemas + Python heredoc + 2 fixture suites. The design is fully specified by plan-doc §5 + 023A/B precedent. If R1 surfaces a CRIT/MAJ requiring spec rework (e.g. trust model needs refinement beyond `gh attestation verify --signer-workflow`), escalate to Codex executor for fix-round-2.

## Slice acceptance

- [ ] **(i) `.github/workflows/scorecard-aggregator.yml`** with weekly cron (`schedule: '0 6 * * 1'` UTC Monday 06:00) + `workflow_dispatch` trigger; two-job structure per plan-doc §5; SHA-pinned action references.
- [ ] **(ii) `docs/scorecards/opt-in-registry.yaml`** initial state: `adopters: []` + a comment block explaining the opt-in PR workflow.
- [ ] **(iii) `schemas/scorecard-opt-in-registry.schema.json`** with `additionalProperties: false`, required fields `repo + default_branch + expected_scp_workflow_ref`.
- [ ] **(iv) `schemas/scorecard-index.schema.json`** with `additionalProperties: false`; per-adopter row carries `status` (enum: verified / verification_failure / unreachable / no_emit), `last_emit_run_id`, `last_emit_commit`, `last_emit_emitted_at`, optional `error` string. NEVER references waiver content fields.
- [ ] **(v) Aggregate job** runs read-only: `gh run list --workflow policy-check.yml --branch <default_branch> --status success --limit 1` to find the latest green run; `gh run download <id> --name scorecard-emit`; `gh attestation verify <emit> --signer-workflow <expected_workflow_ref>`; `jsonschema.validate` against the (cached) v0.1 emit schema; record into in-memory index.
- [ ] **(vi) Commit job** runs only on aggregate success: writes `output/scorecards/index.json`; commits on a `scorecards/<YYYY-MM-DD>` branch; pushes branch; opens a PR titled `chore(scorecards): weekly aggregator run <YYYY-MM-DD>` for operator review.
- [ ] **(vii) Verification failure handling** — emit signature invalid OR unreachable adopter OR no green run within last 7 days OR schema-invalid emit → adopter row records the failure-mode + error string; aggregator does NOT silently drop. Aggregator FAILS the run (loud) only on infrastructure errors (e.g. `gh` itself failing, jsonschema not installed).
- [ ] **(viii) NEVER waiver content** — schema enforces `additionalProperties: false`; pytest scans for `reason`/`approved_by`/`waiver_id` substrings (mirrors 023B test).
- [ ] **(ix) D-042 row in `docs/DECISIONS.md`** ratifies the trust model.
- [ ] **(x) `policies/VERSIONING.md`** internal-surface enumeration extended.
- [ ] **(xi) `STATUS.md`** 023C chain row + D-042 in Recent decisions.
- [ ] **(xii) Pytest passes** for `tests/scorecard-aggregator/` schema validation + waiver-content-exclusion scan.
- [ ] **(xiii) Pre-push wrapper passes** — `scripts/scp-pre-push-verify.sh` green.
- [ ] **(xiv) Adversarial review reaches fixpoint** — 3-lens R1 → recurse to fixpoint.
- [ ] **(xv) PR + CI green + operator-merge per D-040.** No tag cut (internal-only; matches 020N posture).

## Risk surface

1. **Mandatory `job_workflow_ref` verification gap** — already addressed by D-042; the `gh attestation verify --signer-workflow` flag is the binding mechanism. Verified at 023A R3 with the corrected flag name.
2. **Adopter SHA-pin drift** — adopters bump their wrapper SHA pin via Renovate; the opt-in-registry's `expected_scp_workflow_ref` must track. Mitigation: opt-in-registry value can be a regex/glob (e.g. allow any SHA on the SCP main branch via `--cert-identity-regexp`)? **No** — that would weaken the binding. Keep it strict: each adopter PRs an update to their `expected_scp_workflow_ref` when they bump. Cost: extra PR friction. Accept this; revisit at 023E if friction proves material.
3. **Two-job artefact handoff** — aggregate job runs in-memory; commit job needs to read aggregate's output. Use `actions/upload-artifact` for the index between jobs (ephemeral within the workflow run; SHA-pinned same as 023B).
4. **Single-operator self-merge of aggregator PRs** — every weekly run produces a PR. Operator must review + merge. If unattended, PRs stack up. Acceptable: the PRs are non-urgent (informational); operator triage is intentional per plan-doc invariant 1 (informational not authoritative).
5. **Cron failure modes** — if the cron is unhealthy (GitHub Actions outage, etc.), no aggregator run lands; the index goes stale. Mitigation: STATUS.md will flag a cron-health monitor TF as forward work.
6. **`gh attestation verify` rate-limit** — for an estate of N adopters, each weekly run does N verifications; rate limits could cap. Acceptable at v0.1 (small N); revisit at 023E.

## R1 review focus

- **Correctness**: schema shapes match plan-doc + 023B emit shape; aggregator script logic produces correct in-memory index from real fixture inputs; `gh attestation verify --signer-workflow` invocation form is correct (cite real flag); two-job artefact handoff is sound.
- **Safety**: mandatory `job_workflow_ref` constraint actually enforces `--signer-workflow` (no fallback path that drops it); no waiver content can leak via index even under adversarial emit; opt-in-registry tampering is bounded by CODEOWNERS; `commit` job permissions cannot be exploited if `aggregate` is compromised; failure-mode recording doesn't silently drop adopters.
- **Completeness**: AC items (i)–(xv) all addressable; D-042 row complete; cron schedule is documented; the opt-in PR workflow is described in opt-in-registry.yaml header comment; STATUS.md updated.

## Files

### Modified
- `STATUS.md`, `policies/VERSIONING.md`, `docs/DECISIONS.md`.

### Added
- `.github/workflows/scorecard-aggregator.yml`
- `docs/scorecards/opt-in-registry.yaml`
- `schemas/scorecard-opt-in-registry.schema.json`
- `schemas/scorecard-index.schema.json`
- `output/scorecards/index.json` (placeholder; aggregator writes this on first run)
- `tests/scorecard-aggregator/test_scorecard_aggregator_schemas.py`
- `tests/scorecard-aggregator/fixtures/{empty-registry,single-adopter-registry,malformed-registry}/{registry.yaml,expected-validation-result.txt}`
- `tests/scorecard-aggregator/fixtures/{empty-index,single-verified-index,single-failure-index}/index.json`
- `docs/reviews/WP-SCP-023/dispatches/023C-aggregator/{DISPATCH-NOTE.md, review-*-package.json, review-*.json, FIX-ROUND-N.md}`

## Forward-looking

- **TF-023C-001**: SCP self-dogfood — opt the SCP repo's own self-test wrapper into `scorecard-emit: true` so the aggregator has a 1-adopter test corpus before real adopters arrive (target: 023E or post-merge cleanup).
- **TF-023C-002**: cron-health monitor — alert when the aggregator hasn't produced a fresh index in >2 weeks.
- **D-042** filed in this slice.
