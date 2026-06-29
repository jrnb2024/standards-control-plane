# REACH-1 adoption-cascade tracker

Per-repo status of the SCP `policy-check` adoption cascade (REACH plan v2,
`docs/reviews/SCP-REACH-PLAN-2026-06-29.md`). Cascade is **sequential, operator-attended,
warn-first** (add wrapper in warn mode → prove green → flip the required check). Never
touch kg-studio (other fork's workspace).

## Status

| Repo | Org | Status | Notes |
|---|---|---|---|
| standards-control-plane | jrnb2024 | **GATED** (self) | original |
| control-tower | jrnb2024 | **GATED** | original |
| mapp-pim | jrnb2024 | **GATED** | original |
| mapp-doc-agent | jrnb2024 | **GATED** | original (gated, not acc-hooked) |
| **mapp-size-allocation** | jrnb2024 | **WARN-merged ([#233](https://github.com/jrnb2024/mapp-size-allocation/pull/233)); flip pending** | pilot-1; `policy-check` proven green; `scorecard-emit:false` |
| acc | jrnb2024 | Tier-A, not started | same-org, acc-hooked; needs App+secrets+flip |
| mapp-returns-intelligence | **Mapp-Labs** | **deferred → cross-org pilot-2** | cross-org + admin-gated; needs cross-org App story |
| brand-dna-spectrogram | jrnb2024 | Tier-B | only working Kafka consumer |
| fashion-labelling-agent | jrnb2024 | Tier-B | |
| living-canvas | jrnb2024 | Tier-B | |
| agentic_commerce_pac | jrnb2024 | Tier-B | |
| mapp-visual-shopping | jrnb2024 | Tier-B (low) | STL-superseded |
| market-feed | jrnb2024 | **skip** | deprecated (D-038) |
| demos/scratch (adaptive-labelling-demo, ms-stl-demo, kg-demo-framework, fashion-catalogue, labs-trends, fractal-inquiry-os, mapp-estate-regression, fashion-ontology-service) | — | **skip** | not load-bearing |
| kg-studio | jrnb2024 | **NEVER** | other fork's active workspace |

## Per-repo onboarding recipe (proven on SA)

1. **Operator prereqs** (org-admin; can't be automated):
   - Install/confirm the `scp-federation-primitive` App (App ID `3795720`) on the repo with read access to `standards-control-plane`.
   - Set repo secrets: `SCP_FEDERATION_APP_ID` (= `3795720`, non-secret) + `SCP_FEDERATION_APP_PRIVATE_KEY` (a key generated on the App settings page; `gh secret set ... < key.pem`).
2. **Scaffold the wrapper:** `scripts/scaffold-downstream.sh --adopter-repo <owner/name> --default-branch main --scp-sha <v-release-sha> --scorecard-emit false --output-dir <dir>`. **`scorecard-emit: false` is REQUIRED for user-owned private repos** (actions/attest build-provenance is unavailable for them → fails closed; gating is unaffected).
3. **PR** (warn-first): add `.github/workflows/policy-check-wrapper.yml` + a CODEOWNERS line on it. The `policy-check` run on the PR proves the App auth. Merge once green (non-blocking until step 4).
4. **Flip the required check** (operator): `scripts/enable-required-check.sh --owner <owner> --repo <name> --branch main --preserve-existing-contexts` (add `--skip-required-signatures` if the repo isn't ready for signature enforcement). Preserves existing required checks; without `--preserve-existing-contexts` they are silently dropped.

## Findings banked

- Federation secrets are **per-repo** (App ID non-secret; private key operator-set). Not org-wide on jrnb2024.
- **Private user-owned adopters → `scorecard-emit: false`** (GitHub platform limit on attestations).
- Cross-org adopters (Mapp-Labs, e.g. RI) need a deliberate cross-org App-install + secrets story — deferred to pilot-2.
- `gating ≠ acc-hook` (mapp-doc-agent is gated but not acc-hooked) — adopters don't need the acc-hook to be gated.
