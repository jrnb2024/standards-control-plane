# Continuation prompt — WP-SCP-024 cascade implementation kickoff

**Date:** 2026-05-04 AM (early hours)
**Session ended after:** WP-SCP-024 024A plan-doc merged at `4dc3faa` (PR #102) at fixpoint after 9 review rounds.

## What landed in this session (autonomous, 2026-05-03 → 2026-05-04)

User directive (2026-05-03): *"let's just do the remaining, please, but don't mind that it's a bunch of dispatches. Let's get this right. This is really critical stuff. Just keep going autonomously, using the full [process]."*

Tasks #1, #2, #3 from the prior continuation prompt all completed:

1. **TF-020P-005** (PR #94) — `scripts/scp-pre-push-verify.sh` wrapper.
2. **020Q / TF-006** (PR #96) — conflict-gate Python evaluator gains waiver-awareness; closes a real silent-bypass bug in `scp_common.rego` (null `expires_at`).
3. **WP-SCP-023 cross-repo scorecards** — full chain merged:
   - 023A plan-doc (#97); 023B emitter + v1.2.0 cut (#98); 023C aggregator (#99); 023D markdown report + MCP method (#100); 023E Threshold A scaffolding (#101).
4. **WP-SCP-024 estate cascade plan-doc** — 024A merged (#102) — FLA-independent.

**Cumulative session metrics:** 7 PRs merged. v1.2.0 SCP federation primitive cut. 2 GitHub-product constraints surfaced + filed (TF-023E-001 + TF-023E-002). 9-round adversarial review on 024A — unprecedented for a plan-doc slice.

**The 5-move MVCP is closed. WP-SCP-024 (estate cascade) is the natural successor.**

## Current state (HEAD)

- Main HEAD: `4dc3faa` (WP-SCP-024 024A plan-doc merged 2026-05-04T05:34:55Z).
- SCP federation primitive at **v1.2.0** (cut 2026-05-03 in slice 023B).
- USER-GATE-D scaffolded (`docs/gates/USER-GATE-D.md`, status `not-yet-signed`) — gated on first 3 real adopters opting into scorecard-emit + first weekly aggregator clean.
- Aggregator surface live (`.github/workflows/scorecard-aggregator.yml`); markdown report generator deterministic + golden-file tested; `scp.consult_scorecard` MCP method registered.

## What's NEXT

Per WP-SCP-024 plan-doc + memory `project_post_threshold_a_state.md`:

### Recommended order

**(a) FIRST — TF-023E-002 closure** (housekeeping; unblocks downstream cascade work):

Restructure `.github/workflows/policy-check.yml` so the `attest-scorecard` job is a **separate top-level workflow file** (not a job inside policy-check.yml). This closes the GitHub static-permission-validation gap that blocks SCP-self wrapper SHA bumps past v1.0.0. Once closed, the SCP-self wrapper can pin to v1.2.0+ and downstream cascade slices (024C+) can pin to v1.2.0+ without inheriting the same blocker.

This is **not** a hard predecessor for 024B (the scaffolder) but it is recommended before 024C onboards real adopters. Adopter wrappers will declare the same OIDC permissions; if TF-023E-002 isn't closed, every adopter that opts into scorecard-emit will hit the same startup_failure pattern.

**(b) THEN — WP-SCP-024 024B** (scaffolder + `--restore` + CI script):

Per plan-doc §6 + invariant 7 + invariant 2:

- `scripts/scaffold-downstream.sh` (= `SCP-073-scaffolder`) — emits adopter-side artefacts from versioned template.
- `templates/adopter-wrapper.yml.tmpl` — canonical adopter wrapper shape per ADOPT-001 §12.
- `enable-required-check.sh --restore <pre-state.json>` mode — rollback path per invariant 7. **MUST be demonstrated functional via real-repo round-trip on a throw-away test repo** (NOT a dry-run mock) before 024C opens.
- `scripts/check-invocation-log-entry.sh` — CI enforcement of invariant 2. Implements **4 CI behaviours**:
  - Fail-closed default for absent/unrecognised `cascade-status:` (exit non-zero).
  - `onboarded`: log entry present + target match.
  - `onboarded-operator-bump`: log entry present + target match + `TF-024X-renovate-<adopter-slug>` STATUS.md row matching invariant 2's regex format spec literally.
  - `blocked-on-adopter-conflict`: `TF-024X-conflict-<adopter>` reference matching regex spec literally + log file NOT modified in PR diff.
- D-044 filed.

**(c) THEN sequentially** (NON-parallelisable per plan-doc §6 ordering note):

- 024C PIM cascade (D-045)
- 024D control-tower cascade
- 024E mapp-doc-agent + recommender paired cascade
- 024F shopify-app cascade
- 024G Threshold A telemetry + USER-GATE-E (D-046)

Each cascade slice carries:
- Adopter PR (separate repo) — caller wrapper + optional CODEOWNERS line + PR body covering cost estimate + bus-factor-1 disclosure + version-skew tolerance + scorecard-emit opt-in note.
- SCP-side cascade slice PR — DISPATCH-NOTE with `cascade-status:` field + invocation log entry (conditional) + STATUS.md row + ADOPT-001 amendment if needed + 3-lens R1+R2 review JSONs.
- `enable-required-check.sh` invocation (operator-run from local).
- Post-bake observation entry — STATUS.md row appended once Renovate cycle merges + observed clean.
- Cross-repo coordination notification per plan-doc §5.5.

**Cascade is multi-week per slice by design** — invariant 8 requires ≥1 calendar week + ≥1 Renovate cycle observation per slice. Even autonomous execution cannot compress this without violating the invariant.

## Carry-forward state

**TFs that survived this session:**

- **TF-023E-001** (medium) — SCP-self scorecard-emit deferred until repo public OR org-owned. Operator action: make `standards-control-plane-` public OR transfer to an org. Until then, USER-GATE-D criterion (i) carve-out: SCP-self does NOT count toward "≥3 adopters".
- **TF-023E-002** (medium) — SCP-self wrapper SHA pin stuck at v1.0.0 (@41a5299). Closure: restructure `policy-check.yml` so `attest-scorecard` is separate top-level workflow file (recommended), OR close TF-023E-001 first then grant OIDC permissions universally at wrapper level. **Recommended next slice (housekeeping before 024B).**
- **TF-023A-001** (low) — k-anonymity framing for R-023-01 if leakage proves material.
- **TF-023B-001/002/003** — workflow-selftest fixture-pass-with-scorecard-emit (forward-compat); FLA-pilot canary scorecard fixture; WARN_BASELINE_RULES data-driven manifest.
- **TF-023C-001..007** — SCP self-dogfood (deferred via TF-023E-001); cron-health monitor; rate-limit; timeout; repo rename/transfer; minimum scp_version; adopter wrapper filename.
- **TF-023D-001/002/004/005** — `scp.audit_scorecard_changed` (write-side); markdown report retention; drift section; MCP server redeploy (pending next ACC deployment cycle).
- **WP-SCP-024 forward-files (will materialise as TF-024X-NNN at 024C+):**
  - `TF-024X-conflict-<adopter>` per `cascade-status: blocked-on-adopter-conflict` close-states (invariant 10).
  - `TF-024X-renovate-<adopter>` per `cascade-status: onboarded-operator-bump` paths (R-024-07).

## Decisions filed this session

- **D-041** (023B) — cross-repo scorecard data shape + opt-in adopter participation model.
- **D-042** (023C) — aggregator pipeline trust model + `gh attestation verify --signer-workflow` MANDATORY (per 023A R2 MAJ-SAFE-R2-001 closure).
- **D-043** (023D) — `scp.consult_scorecard` MCP method shape + read-only contract.

## Decisions reserved for WP-SCP-024 implementation

- **D-044** (024B) — scaffolder operational contract + `--restore` mode + `check-invocation-log-entry.sh` CI enforcement.
- **D-045** (024C) — estate cascade ordering + per-adopter onboarding contract + post-bake observation window + rollback procedure.
- **D-046** (024G) — Threshold A criteria + post-Threshold-A maintenance posture + `scp.consult_estate_status` decision.

## Critical reminders for next session

1. **WP-SCP-024 024A plan-doc is the canonical reference for the cascade-status spec.** Don't re-derive; consult it.
2. **Cascade is multi-week per slice by invariant 8.** Don't compress the bake window.
3. **--restore must be proven on a real throw-away test repo** before 024C opens (per invariant 7 SLO honesty).
4. **Each cascade slice's invocation-log-entry is CI-enforced** by `check-invocation-log-entry.sh`. The script must exist + green before 024C opens.
5. **D-040 reminder for any future RFC slice** in single-operator mode: 48h is CEILING (auto-defer trigger) not FLOOR.
6. **Local-dev pre-push** — `scripts/scp-pre-push-verify.sh` (TF-020P-005 closure) runs the CI rule-author triad (Regal + opa fmt + opa test --coverage); use it for any rule changes.
7. **The cascade-status spec was hardened over 9 review rounds.** If touching the spec, expect propagation gaps + plan to grep for the *concept* (not just literal phrases) when sweeping.

## Adversarial-review meta-lessons (for future plan-doc slices)

1. **Edit silent-drop pattern** — Edit tool occasionally reports success without actually modifying files. Workaround: Python script + verify-after-write with grep.
2. **Adversarial review must cover environmental constraints** — when reviewing OIDC + attestation + reusable-workflow permissions, consult GitHub's product matrix (private vs public, user-owned vs org-owned) + the static-permission validation behaviour. Not just code shape.
3. **`startup_failure` with no logs ≈ caller-vs-called permission ceiling violation.** Documented for future debugging.
4. **Defer self-dogfood rather than weaken trust model.** When environmental constraints prevent the canonical-adopter pattern from applying to SCP-self, defer; do not exempt.
5. **9-round adversarial review on cross-cutting clauses is normal.** Each round catches either a propagation gap, a substantive defect-class addition, or audit-trail bookkeeping. The recursive review process actually works.
6. **When restructuring a regex spec, always test worked examples against the new regex.** Surfaced as CRIT at R7 of 024A.
7. **Compound-notation closes-markers (`X (lens-A) + Y (lens-B)`) for multi-lens dedups.** Don't drop the partner ID. Surfaced at R8 of 024A.
8. **When sweeping for propagation gaps, grep for the CONCEPT** (every reference to the audit trail OR cascade-status OR TF-024X), not just the literal phrase.

## Resume checklist

1. `git checkout main && git pull --ff-only` — verify HEAD includes `4dc3faa` (024A).
2. Read `docs/plans/WP-SCP-024-estate-cascade.md` v0.1 in full.
3. Read this continuation prompt + memory `project_post_threshold_a_state.md` + `project_wp_scp_023_state.md` + `project_wp_scp_024_plan.md`.
4. Confirm with operator: TF-023E-002 closure first (housekeeping) OR direct to 024B (scaffolder)?
5. Begin selected slice with new branch + DISPATCH-NOTE + R1 dispatch + fix-round-N + R2 + ... → fixpoint → operator merge per D-040.
6. Update STATUS.md "Today's chain" + memory at slice close.
