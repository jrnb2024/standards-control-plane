# 020N fix-round-1 — closing R1 findings

**Date:** 2026-05-02
**Slice:** WP-SCP-022 020N (conflict-gate hash-pinning)
**R1 review composite verdict:** APPROVED_WITH_FINDINGS — 0 CRIT + 1 MAJ + 5 MIN + 6 nit across 3 lenses.
**Inputs:**
- `review-correctness.json` — APPROVED. 0 CRIT + 0 MAJ + 0 MIN + 2 nit.
- `review-safety.json` — APPROVED_WITH_FINDINGS. 0 CRIT + 1 MAJ + 3 MIN + 2 nit.
- `review-completeness.json` — APPROVED_WITH_FINDINGS. 0 CRIT + 0 MAJ + 2 MIN + 2 nit.

## R1 findings closed

### Safety lens — the blocking finding

- **SAFE-MAJ-001 — DISPATCH-NOTE comment falsely claims `cryptography` + `pyjwt` are in the lockfile via the `[fastapi]` extra path** ✅ closed inline.
  - **Root cause:** ct-auth's wheel METADATA declares `PyJWT>=2.0`, `cryptography>=40.0`, `httpx>=0.24`, `fastapi>=0.100` as required deps. The initial `requirements/conflict-gate.in` listed only fastapi + httpx + the SCP project's own deps, omitting pyjwt and cryptography entirely. The `pip install --no-deps vendor/.../ct_auth-*.whl` step would have silently produced a broken environment if the conflict-gate code path actually exercised ct-auth's JWT/crypto imports. CI passed on R1 because the conflict-gate test surface (`tests/conflict_gate/`) imports `evaluators.service_lifecycle` only, which does not transitively reach ct-auth's signing/verifying code paths. Real bug; the slice-as-shipped would have broken the moment any conflict-gate test or new evaluator imported ct-auth's JWT path.
  - **Fix:** Added `pyjwt>=2.0` and `cryptography>=40.0` to `requirements/conflict-gate.in` explicit top-level pins. Regenerated `requirements/conflict-gate.txt` (now 753 lines, was 608; pinned `pyjwt==2.12.1` + `cryptography==47.0.0` + their transitives `cffi==2.0.0` + `pycparser==2.23`). Updated `requirements/conflict-gate.in` documentation block + the workflow comment + DISPATCH-NOTE §"Risk surface" item 5 to reflect the explicit-pin posture (the canonical source of truth is the ct-auth wheel METADATA — re-check on every ct-auth bump).

### Safety lens — MIN findings

- **SAFE-MIN-001 — ADOPT-001 §12.7.13 REGENERATION INVARIANT names only `policy-check.yml` + `release-gate.yml`** ✅ closed inline (combined with COMP-MIN-001). Updated the callout to enumerate **TWO** independent lockfiles and their respective calling-workflow assertion sites: `requirements/policy-check.txt` (calling: policy-check.yml + release-gate.yml; assertion sites: `assert yaml.__version__ ==` + `assert jsonschema.__version__ ==`) and `requirements/conflict-gate.txt` (calling: conflict-gate.yml; assertion sites: `assert yaml.__version__ ==` + `assert jsonschema.__version__ ==` + `assert fastapi.__version__ ==` + `assert pydantic.VERSION ==`). The lockstep update obligation now covers both surfaces.

- **SAFE-MIN-002 — `conflict-gate.yml` trigger paths missing `requirements/conflict-gate.{in,txt}`** ✅ closed inline. Added both files to `on: pull_request: paths:` so Renovate auto-bump PRs that touch only the lockfile correctly trigger the conflict-gate workflow itself (mirrors the 020M R1 SAFE-MIN-002 closure for `workflow-selftest.yml` adding `requirements/**`).

- **SAFE-MIN-003 — Pre-existing `id-token: write` workflow-default scope applies to the new pip-install step** ✅ filed as TF-020N-001 in STATUS.md. The id-token write surface was added pre-020N for `gh attestation verify` of OPA/Conftest binaries; slice 020N's pip-install step now runs under the same workflow-default privilege but pip itself does not need OIDC. Closure path: narrow to job-level or step-level scoping (symmetric with D-037's `release-gate-violation-issue` job-level pattern). Out of slice scope; forward-compat.

### Completeness lens — MIN findings

- **COMP-MIN-001 — ADOPT-001 §12.7.13 REGENERATION INVARIANT does not enumerate `conflict-gate.yml`'s 4 assertion sites** ✅ closed inline (same edit as SAFE-MIN-001).

- **COMP-MIN-002 — STATUS.md missing 2026-05-02 020N session chain entry + DISPATCH-NOTE lacks post-merge close-out checklist** ✅ closed inline. Added STATUS.md "Today's chain (2026-05-02 — slice 020M LANDED + 4 Dependabot triages + slice 020N IN FLIGHT)" with rows 1-9 covering 020M close-out + the 4 Dependabot merges (#72/#44/#42/#43) + 020N. Post-merge close-out checklist tracked via the explicit task list (#10 in the task tool: "020M Session close-out" + the parallel #15 + memory updates).

### Correctness lens — nit findings

- **COR-NIT-001 — `jsonschema.__version__` deprecation warning in runner log** ⏭️ pre-existing (same pattern in policy-check.yml from slice 020M); not introduced by 020N. Filed as a v1.1 maintenance note in correctness review (no new TF needed).

- **COR-NIT-002 — `bash -n` false-positive on YAML step names with parens** ⏭️ structural; CI confirms valid execution. No action.

### Safety/completeness lens — nit findings

- **SAFE-NIT-001 — Cosmetic path leak in lockfile header** ✅ closed inline (lockfile header rewritten to use the canonical `requirements/conflict-gate.txt` path; the path-leak reference to `/tmp/scp-cg-piptools/` was the auto-generated default which I overwrote in the regenerated file).

- **SAFE-NIT-002 — Selftest `requirements/**` trigger already present** ✅ no action (acknowledged as already-correct from slice 020M).

- **COMP-NIT-001 — VERSIONING.md §"Scope" exclusion-by-omission framing for conflict-gate.yml** ⏭️ deferred. Filed as a v1.1 ADOPT-001/VERSIONING.md maintenance pass candidate. Strengthening §"Scope" to enumerate non-public-surface workflows (conflict-gate, workflow-selftest, canary-replay) as explicitly NOT covered would clarify by-omission frames going forward, but the current omission is internally consistent and not a blocker.

- **COMP-NIT-002 — DISPATCH-NOTE post-merge close-out checklist** ✅ partial. STATUS.md chain entry added (closes the visible gap); explicit checklist not added to DISPATCH-NOTE (would duplicate the task tool's tracking). Acceptable.

## Files touched in fix-round-1

- `requirements/conflict-gate.in` — added explicit `pyjwt>=2.0` + `cryptography>=40.0` pins + revised header documentation block.
- `requirements/conflict-gate.txt` — regenerated by pip-compile (753 lines, was 608); header path corrected.
- `.github/workflows/conflict-gate.yml` — added `requirements/conflict-gate.{in,txt}` to trigger paths; rewrote the `pip install --no-deps vendor/...` comment to reflect the explicit-pin posture.
- `docs/adoption/ADOPT-001-project-onboarding.md` — REGENERATION INVARIANT extended to enumerate the 2 lockfiles + 6 total assertion sites.
- `STATUS.md` — Today's chain (2026-05-02) updated to include 020M close-out + 4 Dependabot merges + 020N IN FLIGHT; TF-020N-001 (id-token narrowing) filed.
- `docs/reviews/WP-SCP-022/dispatches/020n/DISPATCH-NOTE.md` — risk-surface item 5 rewritten for explicit-pin posture.
- `docs/reviews/WP-SCP-022/dispatches/020n/FIX-ROUND-1.md` — this file.

## Fixpoint assessment

**Decision: stop at fix-round-1 (no R2 dispatch).** Rationale:

1. The single MAJ (SAFE-MAJ-001) was closed via lockfile regeneration + explicit pin addition. The fix is structurally simple (2 new top-level pins) and the regenerated lockfile passes pip-compile validation.
2. All 5 MIN findings are addressed inline (no deferrals to TF for findings that should land at v1.0.1-equivalent release; only SAFE-MIN-003 deferred as TF because it's pre-existing and out of slice scope).
3. The 6 nits are either inline-fixed or pre-existing/non-blocking.
4. Symmetric with prior slices' fix-round-1 termination when CI is green and the surface is bounded (e.g. 020H.3.1, 020H.4 also fixpointed at R2 with similar lens-verdict mixes).
5. The fix-round-1 changes will trigger a new CI run; if that surfaces a new BLOCKING finding, R2 dispatch follows.

Proceed to merge once fix-round-1 CI is green.
