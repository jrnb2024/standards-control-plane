# ProgrammePlan — WP-SCP-019 Service Auth Contract (SVC-003)

**Work Package:** `WP-SCP-019`
**Version:** 0.1
**Status:** Draft
**Date:** 2026-04-18
**Branch:** `feature/wp-scp-019-svc-003-auth-contract`
**Programme Ref:** SCP-071 (CT-integration contract thread)
**Freeze Ref:** D-019 / `FREEZE_DIRECTIVE_SVC003.md` (posted 2026-04-18)

## 1. Purpose

Publish SVC-003 as the canonical service-lifecycle rule for the estate's service
auth contract, stand up the service-lifecycle evaluator so SVC-001/002/003 are
all auto-checked, and reconcile the two in-repo auth stories (WP-SCP-018
`--auth-token` and commit `66ba8a4` Control Tower OIDC) against the ratified
closed mode set.

## 2. Programme protocol position

WP-SCP-019 is the new programme increment anticipated by `PROG-SCP-001` §7
("Any further work should be treated as a new programme increment rather than
an extension of this one"). It follows the per-WP protocol defined there: one
branch and one PR per work package. Slices 019A–F below are review checkpoints
on the WP-SCP-019 branch, not separate PRs; the PR opens when all slices are
complete.

## 3. Scope

| Slice | Deliverable | Status |
|-------|-------------|--------|
| 019A | SVC-003 rule text + approved-mode enum spec + planning quartet + D-019 + review-pack stub + BACKLOG row | complete (commit `ea9f7e0`) |
| 019B | `evaluators/service_lifecycle.py` covering SVC-001/002/003 with fixture corpus, including code-pattern scans for declared-mode/impl coherence | complete (commit `25b3594`) |
| 019B' | Cross-slice defect sweep: evaluator self-poisoning, `additionalProperties: false` unenforced, `waiver_ref` existence unchecked | complete (commit `d3a2606`) |
| 019C | Audit CLI integration + tests | complete (commit `c4ae4ba`) |
| 019D | Dogfood against `mapp-pim` (external, tracked under SCP-071) and Standards Control Plane itself (in-repo) | complete (commit `feb612c`) |
| 019E | ADOPT-001 §11 rewrite against ratified modes + `--auth-token` deprecation waiver record | complete (commit `41a28f3`) |
| 019F | Publish (update `docs/STATUS.md`, `README.md`, review pack, open PR) | complete (this commit) |

## 4. Out of Scope

Do not bundle the following into WP-SCP-019:

- SDK registry (PyPI/npm) — separate work, CT-side
- Kafka `ct-events` SDK extraction — separate work, CT-side
- Estate-repo CI integration of the service-lifecycle audit — WP-SCP-020 candidate
- Per-app migrations from `mode.bearer_legacy` to `mode.api_key` — separate
  work packages per app

## 5. External Dependencies

The following are dependencies outside this repo. They do not block 019A–E but
must be satisfied before the SVC-003 freeze lifts (see §6).

| Dependency | Owner | Notes |
|------------|-------|-------|
| Register SCP as a Control Tower agent-key issuer | Control Tower team | Required for `mode.api_key` to be the estate replacement for `mode.bearer_legacy` machine callers. Confirm during 019D/019E. |
| CT SDK 0.4.1 (TS) and 0.8.1 (Python `ct_auth`) available | Control Tower team | This repo currently vendors `ct_auth-0.8.0`; the 0.8.1 bump lands during 019C or as a follow-up. |
| At least one consuming app vendors the new CT SDK versions | Per-app owners | Evidence path: link to the consuming app's lockfile commit, captured in the 019F review pack. |

## 6. Risks

- **Estate-wide deprecation of `mode.bearer_legacy` by 2026-06-30** depends on
  the CT agent-key issuer registration above. If that dependency slips, the
  close date must be renegotiated; D-019 will need a follow-up decision row.
- **Dogfood scope** may uncover that commit `66ba8a4` deviates from the rule's
  declared shape in ways the adversarial review did not catch. 019D will
  produce the first hard evidence; any deviation requires an erratum to 019A
  or a small patch in 019B before the WP can publish.
- **Cross-repo SDK alignment** is not owned by this repo. If consuming apps
  cannot vendor the target CT SDK versions in time, the freeze stays in place
  and WP-SCP-019 ships without lifting it.

## 7. Unfreeze Trigger

The SVC-003 freeze directive (`FREEZE_DIRECTIVE_SVC003.md`) lifts when all
three are true:

1. WP-SCP-019 merged (SVC-003 + evaluator + ADOPT-001 rewrite)
2. CT SDK 0.4.1 (TS) and 0.8.1 (Python) vendored in at least one consuming
   app. Verification: link to the consuming app's lockfile commit, captured
   in `docs/reviews/WP-SCP-019/` in slice 019F.
3. Per-app migration plans drafted for apps not yet conformant. Verification:
   per-app `WP-<APP>-0NN` entries, referenced from `docs/reviews/WP-SCP-019/`
   in slice 019F.
