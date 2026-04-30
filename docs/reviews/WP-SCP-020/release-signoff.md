# WP-SCP-020 v1.0.0 — release sign-off

**Tag:** `v1.0.0`
**Date:** 2026-04-30
**Promoted from:** `v1.0.0-rc.1` (cut 2026-04-30T14:52:04Z, target SHA `351b7b7e63fcbe20c629800c750f3a6ec9b1e36e`).
**v1.0.0 target SHA:** `a2f5ab30f261cb8100a8c6cd3b9f2faf1984599d` — the main HEAD post-USER-GATE-A0 merge.
**Slice:** WP-SCP-022 020H part 2 — promote rc.1 → v1.0.0 with governance signoff.

## Sign-off statement

> "I, @jrnb2024, confirm the federation primitive at SHA `a2f5ab3` meets the WP-SCP-020 v1.0.0 release criteria. The pre-protection canary (020E.a, PR #59) demonstrated SCP-R-001 deny on a real PR with a real violation; the deny finding payload is structurally correct; the workflow runs in 20 seconds warm-start; the rc.1 release notes accurately enumerate what ships. I authorise promotion of `v1.0.0-rc.1` to `v1.0.0`."

Recorded as a verified-signed commit by @jrnb2024 (SSH key id 925245) on the merge of this signoff PR.

## What changed since v1.0.0-rc.1

Between `v1.0.0-rc.1` (`351b7b7`) and `v1.0.0` (`a2f5ab3`) the only main-branch additions are:

| PR | What | Touches |
|---|---|---|
| #58 | rc.1 release notes + lib targets-array CI fix | `docs/releases/v1.0.0-rc.1.md`, `lib/policy_check_invocation.sh` |
| #60 | 020E.a canary evidence doc | `docs/reviews/WP-SCP-020/canary-evidence.md` |
| #61 | USER-GATE-A0 signoff package | `docs/reviews/WP-SCP-020/USER-GATE-A0-signoff-prep.md` |

No Rego rule changes. No schema changes. No reusable-workflow changes. No CODEOWNERS changes. Only documentation + one bash-grammar fix in `lib/policy_check_invocation.sh` (the `targets=()` initialiser, closing the SCP-R-003 manifest-not-applicable code path under `set -u`). v1.0.0 == rc.1 + audit trail + the lib bash fix that surfaced under real-PR CI.

## Acceptance criteria — verified at `v1.0.0` cut

| Criterion | State | Evidence |
|---|---|---|
| 3 starter Rego rules (SCP-R-001/002/003) | ✅ landed | `policies/SCP-R-{001,002,003}.rego` |
| Reusable workflow at `.github/workflows/policy-check.yml` | ✅ landed | PR #36 |
| Workflow-selftest harness | ✅ landed | PR #38 |
| Local-repro CLI `scripts/scp-policy-check` | ✅ landed | PR #41 |
| Waiver-aware Rego + caller `.scp/rule-config.yaml` override | ✅ landed | PR #52 |
| Conflict-gate (rego vs python) | ✅ landed | PR #52, `tests/conflict_gate/` |
| Read-back commit-status `scp/policy-check-readback` | ✅ landed | PR #52 (D-029) |
| Tag-protection ruleset on `v*` + `required_signatures` on main | ✅ landed | PR #53 (D-030) |
| CODEOWNERS wiring (personal-account / single-operator) | ✅ landed | PR #56 (D-031) |
| Self-dogfood wrapper `policy-check-wrapper.yml` | ✅ landed | PR #57 |
| `v1.0.0-rc.1` release notes published | ✅ landed | PR #58 + tag |
| Pre-protection canary 020E.a deny verified | ✅ landed | PRs #59 (canary), #60 (evidence), workflow-run-id 25172373569 |
| USER-GATE-A0 signed | ✅ landed | PR #61, commit `a2f5ab3` |

## Canary run-id reference (per spec)

The 020E.a canary's failing workflow-run-id is `25172373569` (job `73795068201`). Structured finding payload at `docs/reviews/WP-SCP-020/canary-evidence.md`.

## Known limitations carried into v1.0.0

Per `docs/releases/v1.0.0-rc.1.md` "Known limitations / tracked-forward items":

- **TF-005**: structural enforcement of expired rule-config at release-tag time → 020D2 acceptance criterion.
- **TF-006**: conflict-gate suppression-path fixture corpus → WP-SCP-023 prerequisite.
- **TF-007**: re-tighten `gh attestation verify` to hard-fail when OPA upstream publishes Sigstore attestations.
- **TF-008**: path-scope SCP-R-002 to waivers.json files only → v1.1.
- **TF-D1-001..003**: 020H part 3 obligations from 020D1 R1 review.

None block v1.0.0 release. Each has a named resolution path.

## What v1.0.0 unlocks

- **020D2**: required-status-check enable. `scp/policy-check` becomes a required check on `main` with `enforce_admins=true`. After this, every PR to main must pass the gate before merge.
- **020E.b**: post-protection canary (`canary/deliberate-violation-post`) — verifies that the required check actually blocks merge under enforcement mode.
- **020E.c**: waiver-suppression canary (`canary/waived-violation`) — verifies that a sibling waivers.json entry suppresses the matching deny.
- **USER-GATE-A**: Threshold A finish line — operator confirms SCP gates itself successfully on its own main.

## Provenance

- Tag-protection ruleset `scp-tag-protection-v` (id 15752458) prevents force-push, deletion, or update of `v1.0.0`.
- `required_signatures` enabled on `main` since 2026-04-30 morning.
- Tag commit `a2f5ab30f261cb8100a8c6cd3b9f2faf1984599d` is the squash-merge of PR #61 (USER-GATE-A0 signature).

## Sign-off

@jrnb2024 — 2026-04-30
