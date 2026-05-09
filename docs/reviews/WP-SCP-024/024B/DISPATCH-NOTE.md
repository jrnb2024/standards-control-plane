# DISPATCH-NOTE — WP-SCP-024 slice 024B (scaffolder + `--restore` + invocation-log CI enforcement)

**Date:** 2026-05-09
**Branch:** `feature/wp-scp-024-024b-scaffolder` (off main `04135f0`)
**Predecessor:** WP-SCP-024 024A plan-doc v0.1 (PR #102, `4dc3faa`, 2026-05-04). Per plan-doc §6, 024B is the hard predecessor for 024C–F cohort onboarding.
**Successor target:** WP-SCP-024 024C PIM canary cascade.
**Decision filed:** D-044 (scaffolder operational contract + adopter-template versioning + invocation-log convention extension + `enable-required-check.sh --restore` mode).

`cascade-status:` not applicable — this slice does not onboard a cohort adopter; it ships the scaffolder + helpers that 024C–F will consume. CI gate `check-invocation-log-entry.sh` (which this slice introduces) does not apply to this slice's own PR.

## Backstory (recent governance moves)

- **2026-05-09:** the 6 D-035-aligned rules previously framed as gating CT Wave 1 entry on 2026-05-15 were RETIRED under that deadline (PR #105, `04135f0`). Re-scoped under WP-SCP-025 (parked plan-doc; kicks off post-WP-SCP-024 Threshold A; 5-candidate shortlist with success/anti-criterion against measurable adopter consumption signal).
- This frees the next ~3-5 days for slice 024B without dilution against a deadline that wasn't load-bearing.

## Why

Slice 024B delivers the three components that 024C–F cascade slices treat as scaffolding hard predecessors per plan-doc §6 + invariants 2 + 7:

1. **Scaffolder** generates adopter-side artefacts mechanically — every cascade slice's adopter PR has a consistent shape derived from one versioned template.
2. **`--restore` mode** proves the rollback SLO (<30 min single-operator-doable) is real, not aspirational. Plan-doc invariant 7 + slice-024B acceptance criterion: real-repo round-trip on a throw-away test repo, NOT a dry-run mock.
3. **`check-invocation-log-entry.sh`** is the CI enforcement of plan-doc invariant 2 (the cascade-status spec hardened over 9 review rounds). 4 behaviours: fail-closed default + 3 named cascade-status check-paths.

Without all three, cascade slices cannot be authored without the same 9-round adversarial review burden that 024A absorbed; the scaffolder + CI script collapse that surface into per-slice mechanical use.

## Scope (in)

| Deliverable | Path | Notes |
|---|---|---|
| Scaffolder helper | `scripts/scaffold-downstream.sh` | Per plan-doc §5.3 invocation contract: `--adopter-repo <owner/name> --default-branch <main\|master\|develop> --scp-sha <40-char-sha> --scorecard-emit <true\|false> --output-dir <local-clone-path>`. Bootstrap-only (refuses `CI=true` / `GITHUB_ACTIONS=true` per D-035 symmetry). Validates `--scp-sha` against SCP main HEAD at invocation time (warns if not main HEAD; refuses to emit on non-existent SHA). Emits `MANIFEST.json` listing every emitted file + SHA256 for audit. |
| Adopter wrapper template | `templates/adopter-wrapper.yml.tmpl` | Single source of truth for canonical adopter wrapper shape per ADOPT-001 §12. Substitutions: `{{default-branch}}`, `{{scp-sha}}`, `{{scorecard-emit}}`. Future wrapper-shape changes land in template + propagate via Renovate SHA bumps. |
| Scaffolder emissions (in `--output-dir`) | `<output>/.github/workflows/policy-check-wrapper.yml` + `<output>/.github/CODEOWNERS-snippet.txt` + `<output>/CASCADE-PR-BODY.md` | Per plan-doc §5.3. PR-body template covers cost estimate (T-024-09) + bus-factor-1 disclosure (invariant 9) + version-skew reference (T-024-04 + D-036) + scorecard-emit opt-in note (deferred per TF-023E-002). |
| `--restore` mode | extension to `scripts/enable-required-check.sh` | New flag `--restore <pre-state.json>` consumes captured before-state from a prior invocation log entry + reverses branch-protection mutation. Existing forward-mode behaviour unchanged. Plus safety check: refuses to invoke against a target whose `policy-check / scp/policy-check` has not run successfully at least once on a recent PR (closes the "enable before wrapper green-CI'd" foot-gun). |
| Invocation-log CI enforcer | `scripts/check-invocation-log-entry.sh` | Implements plan-doc invariant 2's 4 CI behaviours: (a) **fail-closed default** for absent/unrecognised `cascade-status:`; (b) `onboarded` → log entry present + target match; (c) `onboarded-operator-bump` → log entry present + target match + STATUS.md `TF-024X-renovate-<adopter-slug>` row matching regex format spec literally; (d) `blocked-on-adopter-conflict` → DISPATCH-NOTE `TF-024X-conflict-<adopter>` reference matching regex spec literally + log file NOT modified in PR diff. Regex literal: `TF-024X-(renovate\|conflict)-[a-z0-9]+(?:-[a-z0-9]+)+(?:\*\*)? \((open\|pending\|in-progress\|closed)\): \S.{19,}` |
| Scaffolder unit tests | `tests/scaffolder/test_scaffold_downstream.py` (or shell-level under `tests/`) | Schema-validates emitted wrapper against canonical shape; verifies template substitutions; verifies `MANIFEST.json` SHA256 round-trip. |
| `--restore` real-repo round-trip demo | `docs/reviews/WP-SCP-024/024B/restore-roundtrip-evidence.md` | NOT a dry-run mock per plan-doc invariant 7 SLO honesty + 024A R1 MAJ-SAFE-003. Throw-away test repo (e.g. `jrnb2024/scp-024b-restore-test`); capture before-state via existing log entry shape; mutate branch protection; restore via `--restore`; verify byte-for-byte match. Evidence captured for D-044 ratification. |
| `check-invocation-log-entry.sh` tests | `tests/check_invocation_log/test_check_invocation_log_entry.sh` (shell harness) or pytest equivalent | Each of the 4 CI behaviours has at least one positive + one negative case; regex anchors tested with worked examples (per 024A R7 CRIT lesson — "always test worked examples against the new regex"). |
| Setup `~/Projects/acc/docs/notifications/` if absent | NEW dir + README | Plan-doc §5.5 row 2 says "path established at 024B if not present". Empty-init the dir with a README so 024C kickoff can drop a notification there without scaffolding overhead. |
| ADOPT-001 §12 break-glass procedure | `docs/adoption/ADOPT-001-project-onboarding.md` §12 (new subsection) | 3-gate playbook: (1) disable required-check on target via `enable-required-check.sh --restore` capturing pre-break SHA; (2) SHA-pin SCP wrapper to known-good (last green release tag); (3) re-enable + re-run Renovate cycle. Lands alongside `--restore` because the two are co-dependent (break-glass procedure references `--restore` directly). |
| D-044 filing | `docs/DECISIONS.md` row | Scaffolder operational contract + adopter-template versioning + invocation-log convention extension + `enable-required-check.sh --restore` mode semantics. |
| STATUS.md update | "Today's chain (2026-05-09 — slice 024B)" entry | Documents this slice's outcome + closes the 024B-prep tasks. |

## Scope (out)

- 024C PIM cascade kickoff. That follows once 024B merges. Cross-repo notification at 024C kickoff (CT log + ACC log per §5.5).
- TF-023E-002 closure (workflow restructure). Carry-forward; not blocking 024B. **Note:** an untracked stub at `docs/reviews/WP-SCP-023/TF-023E-002/DISPATCH-NOTE.md` survives on this branch from the prior closure attempt; disposition is "ignore — TF-023E-002 carry-forward, separate work stream." A future TF-023E-002 closure session picks up the stub as the starting point. Do NOT include it in this slice's PR scope.
- D-021 May-31 atomic-workday filing. Independent track; pre-staged at `docs/reviews/WP-SCP-019/d019-may31-checkpoint.md`.
- Estate-auth coordination checklist + MCP adopter contract docs (§5/§4 of revised continuation prompt). Hold for now per operator direction.
- TF-024-AUTH-001 (services.yml self-conformance reconciliation). Lands inside D-021 PR on 2026-05-31.
- TF-024-R1-Evidence-Gate (port CT cardinal-rule-2 CI gate). Should-do post-024B.

## Cascade-status spec recap (the spec `check-invocation-log-entry.sh` enforces)

Per plan-doc §2 invariant 2 + §5.2 + 024A R6 R6-NEW-MAJ-003 fail-closed default:

```
TF-024X-(renovate|conflict)-[a-z0-9]+(?:-[a-z0-9]+)+(?:\*\*)? \((open|pending|in-progress|closed)\): \S.{19,}
```

Worked-example matrix (each MUST be tested in `check-invocation-log-entry.sh` test harness per 024A R7 CRIT lesson):

| Example | Match? | Why |
|---|---|---|
| `- **TF-024X-renovate-jrnb2024-pim** (open): Renovate disabled on PIM; operator-bumped @abc123 at 024C; track until adopter enables Renovate cohort.` | ✅ | STATUS.md bullet wrapping passes; regex doesn't care about wrapper |
| `See TF-024X-conflict-jrnb2024-pim (pending): adopter has prior policy-check workflow; awaiting rename PR.` | ✅ | DISPATCH-NOTE prose embedding passes |
| `- **TF-024X-renovate-jrnb2024-pim**` | ❌ | no status field |
| `- **TF-024X-renovate-jrnb2024-pim** (open):` | ❌ | empty description (0 chars after `: `) |
| `- **TF-024X-renovate-jrnb2024-pim** (open):                    ` | ❌ | all-whitespace description fails `\S` anchor |
| `- **TF-024X-renovate-jrnb2024-pim** (open): short` | ❌ | only 5 chars after `: `, fails `.{19,}` |

## Acceptance criteria

Per plan-doc §6 row 024B (literal):

- [ ] Scaffolder emits a known-fixture wrapper that schema-validates against the canonical wrapper shape from ADOPT-001 §12.
- [ ] `--restore` round-trip via captured before-state restores branch-protection state byte-for-byte **on a real throw-away test repo** (not a dry-run mock — closes 024A R1 MAJ-SAFE-003).
- [ ] `check-invocation-log-entry.sh` parses DISPATCH-NOTE `cascade-status:` field and implements all four CI behaviours per invariant 2:
  - [ ] **fail-closed default** (absent or unrecognised value → exit non-zero)
  - [ ] `onboarded`: requires log entry + target match
  - [ ] `onboarded-operator-bump`: requires log entry + target match + STATUS.md `TF-024X-renovate-<adopter-slug>` row matching regex literally
  - [ ] `blocked-on-adopter-conflict`: requires DISPATCH-NOTE `TF-024X-conflict-<adopter>` reference matching regex literally AND log file NOT modified in PR diff
- [ ] D-044 filed.
- [ ] All three components (scaffolder + `--restore` + `check-invocation-log-entry.sh` covering all four CI behaviours) are hard predecessors for 024C — verified by 024C DISPATCH-NOTE referencing each.

Plus:
- [ ] ADOPT-001 §12 break-glass 3-gate playbook written + cross-references `--restore`.
- [ ] `~/Projects/acc/docs/notifications/` dir established (per §5.5 row 2).
- [ ] 3-lens R1 + R2 fixpoint reached (0 new CRIT + 0 new MAJ on a complete cycle).
- [ ] CI green (own self-dogfood policy-check + scp/policy-check-readback + conflict-gate).
- [ ] Self-merge per D-040 single-operator-mode after fixpoint.

## Cross-repo coordination

None for slice 024B. The cascade-start announcement to CT + ACC + mapp-estate-regression files at 024C kickoff per plan-doc §5.5. This DISPATCH-NOTE's "Cross-repo coordination" subsection is intentionally minimal-but-present per plan-doc §5.5 closing paragraph (a slice DISPATCH-NOTE that skips this subsection fails the completeness lens).

## FLA pilot safety findings reviewed

[none new since 2026-05-04 (024A close)] — slice 024B is internal scaffolding; no FLA implications. Per plan-doc invariant 4, the cascade is FLA-independent and 024B does not consume FLA-derived templates.

## Dispatch plan

Standard four-tier dispatch per `feedback_four_tier_dispatch.md`:

1. **Codex Tier 3 executor** (`gpt-5.4-mini medium`) — implementation: scaffolder + template + `--restore` extension + `check-invocation-log-entry.sh` + tests. Bash + minimal Python; non-kernel-dangerous.
2. **3× parallel Sonnet R1** (500ms stagger): correctness / safety_bypass / completeness_governance lenses.
3. **R2 fixpoint** required (0 new CRIT + 0 new MAJ).
4. **Operator real-repo `--restore` round-trip demo** (sudo not required; standard `gh` PAT). Captures evidence into `docs/reviews/WP-SCP-024/024B/restore-roundtrip-evidence.md`.
5. **Self-merge** per D-040 single-operator-mode after fixpoint + CI green.

**Kernel-hook posture for this slice:** operator (you) is running `sudo bash /Users/amplience/Projects/acc/scripts/install_acc_hook.sh --orchestrator-user amplience` in parallel with this DISPATCH-NOTE drafting. Installer integrity verified at session resume — Mop-2 + Mop-3 hardening commits 2026-05-07 (caches, freshness binding, symlink-deny, error-mode tests, atomic config, verdict validation; .claude/ chmod + pre-switch deny decoration); same invocation shape; SHA256 `e5583fa756719a952d591535f3735e59311ebd33acf3e2dea8e9700a4d2c5b8a`. Once kernel hook is installed, codex_dispatch.py + claude_dispatch.py work durably for this slice and every cascade slice that follows. Until then, prep work proceeds (DISPATCH-NOTE, scope analysis, work-package authoring); first dispatch awaits hook-install confirmation.

## Sequencing

| Phase | Work | Tier | Estimated wall-clock |
|---|---|---|---|
| 0 (now) | DISPATCH-NOTE + work-package JSON authoring | Opus orchestrator (this session) | ~30 min |
| 1 | Codex executor: scaffolder + template + `--restore` + CI script + unit tests + ADOPT-001 §12 + D-044 row | Codex T3 | ~45–60 min |
| 2 | 3× parallel Sonnet R1 review (correctness / safety_bypass / completeness_governance) | Sonnet | ~10 min |
| 3 | Fix-rounds (Codex + targeted re-review) until R(N) fixpoint | Codex T3 + Sonnet | variable; expect 1–3 rounds |
| 4 | `--restore` real-repo round-trip demo on throw-away test repo | Operator (interactive `gh` calls; not dispatcher-mediated) | ~15 min |
| 5 | Final R-fixpoint check + self-merge | Opus | ~10 min |

Target: slice 024B merged within ~3–5 calendar days from kickoff.

## Reservation guard

Per `docs/DECISIONS.md` header, D-044 is reserved for this slice. Codex executor MUST NOT assign D-044 to any other decision filed during this slice. The reservation pattern mirrors D-021 (WP-SCP-022) + D-041–043 (WP-SCP-023) + D-044/045/046 (WP-SCP-024 reservation block already in place).

---

**Status:** DRAFT v0.1 — awaiting kernel-hook install confirmation, then Codex T3 executor dispatch.
