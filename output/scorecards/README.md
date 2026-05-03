# SCP Scorecard Index

This directory holds `index.json` — the cross-repo scorecard aggregator's central index, produced by the weekly `.github/workflows/scorecard-aggregator.yml` cron run per WP-SCP-023 023C / D-042.

## Files

- `index.json` — the live aggregated index. Schema: `schemas/scorecard-index.schema.json`. Initial state on 023C merge is the placeholder (epoch `aggregated_at`, empty `adopters[]`); the first aggregator run after merge overwrites it.

## Trust model

- Index trust is rooted in git's required-signed-commits (per slice 020J) + `output/scorecards/** @jrnb2024` CODEOWNERS coverage (per slice 023A) + branch-protection on main (per slice 020D2). The aggregator commits via the workflow's job-scoped `contents: write` permission; every aggregator-produced PR is reviewed via CODEOWNERS before landing on main.
- Per-emit trust: the aggregator verifies each adopter's `scorecard-emit.json` artifact via `gh attestation verify --signer-workflow <expected_workflow_ref>`. Verification failures record `status: verification_failure` with an error string in the per-adopter row — never silently dropped.
- Privacy: the index NEVER carries waiver content (per WP-SCP-023 plan-doc invariant 2; schema enforces `additionalProperties: false` at every level).

See `docs/scorecards/opt-in-registry.yaml` for the list of opted-in adopters and the opt-in PR workflow.
