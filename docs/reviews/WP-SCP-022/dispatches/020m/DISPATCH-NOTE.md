# WP-SCP-022 slice 020M — supply-chain hash-pinning + v1.0.1 cut (dispatch note)

**Date:** 2026-05-02
**Tier:** orchestrator-applied (Tier 1 only)
**Closes:** TF-020H3rg-002 (`pip install --require-hashes` for both YAML/JSON-validating workflows). Filed at 020H.3 R1 safety MIN-SAFE-006.

**Slice naming.** "020M" is the next free post-Threshold-A letter after 020K (CODEOWNERS, landed pre-Threshold-A) and 020L (reserved for the rule-RFC dogfood — a substantively different workstream which lives independently when authored). 020M is supply-chain hardening at PATCH bump only.

## Justification for not invoking Codex executor

Per `feedback_four_tier_dispatch.md` in-line escalation guidance.

The slice surface is small and mechanical:

- One generated artifact: `requirements/policy-check.txt` — produced by `pip-compile --generate-hashes` from `requirements/policy-check.in` (top-level pins `pyyaml==6.0.2` + `jsonschema==4.23.0`, matching the existing inline pins).
- One companion source: `requirements/policy-check.in` — the input to `pip-compile`, retained so future regenerations are reproducible.
- Five `pip install` site swaps across two workflow files (4× in `policy-check.yml`, 1× in `release-gate.yml`).
- One stale comment removal at `release-gate.yml` lines 110–114 (the comment that filed TF-020H3rg-002 as deferred — now closed).
- Version bump v1.0.0 → v1.0.1 + release-notes + D-038.

No Rego rule paths exercised; no schema changes; no breaking surface changes. Codex Tier 3 dispatch overhead would exceed marginal benefit; orchestrator-applied + R1 × 3 is the right posture (symmetric with 020H.3.1, 020H.4 dispatch notes).

## PATCH bump justification

Per `policies/VERSIONING.md` §"Semver guarantee":

> **PATCH** (`v1.0.x`) | Bug fixes, new informational annotations, performance improvements, observability records, **internal refactors of helpers/lib**.

Hash-pinning is an internal supply-chain hardening of the workflow's pip install steps. Same `pyyaml==6.0.2` + `jsonschema==4.23.0` versions retained — adopters see identical effective behaviour. No `workflow_call.inputs` change. No schema change. No rule change. No annotation surface change (error annotations preserved; message text refines to mention hash-pinning).

Therefore PATCH (v1.0.1) is correct. No `policies/deprecations.yaml` entry required (no surface deprecation).

## Slice acceptance

- [ ] **(i) Generated requirements file.** `requirements/policy-check.txt` produced by `pip-compile --generate-hashes` from `requirements/policy-check.in`. Includes `pyyaml==6.0.2` + `jsonschema==4.23.0` + transitive closure (`attrs`, `jsonschema-specifications`, `referencing`, `rpds-py`) with all-platform wheel SHA256 hashes. The file contains the `pip-compile` regeneration command in its header for adopter reproducibility.
- [ ] **(ii) `requirements/policy-check.in`.** Top-level pins; the regeneration source. Symmetric with `scripts/.tool-versions` + `scripts/scp-policy-check.lock` pattern (input + lockfile).
- [ ] **(iii) `policy-check.yml` install sites.** Four sites (lines 627, 633, 721, 1072) swap `pip install --user pkg==ver` for `pip install --user --require-hashes -r "${SCP_RUNTIME_ROOT}/requirements/policy-check.txt"`. Conditional `if ! python3 -c 'import <pkg>'` guards preserved. Error annotation messages refined to mention hash-pinning.
- [ ] **(iv) `release-gate.yml` install site.** Line 115 swaps to `pip install --quiet --user --require-hashes -r requirements/policy-check.txt`. Stale comment lines 110–114 (which filed TF-020H3rg-002 as deferred) removed/rewritten — TF-020H3rg-002 is now closed in this slice.
- [ ] **(v) `version-manifest.json` bump.** `v1.0.0` → `v1.0.1`.
- [ ] **(vi) D-038 amending decision.** `docs/DECISIONS.md` row ratifying supply-chain hash-pinning as PATCH (parallels D-029 statuses:write decision shape).
- [ ] **(vii) STATUS.md update.** "Today's chain (2026-05-02 — slice 020M)" section. TF-020H3rg-002 marked ✅ closed in 020M.
- [ ] **(viii) Plan §4 typo fix — TF-020H3-003 opportunistic close.** `docs/plans/WP-SCP-020-policy-federation-primitive.md` §4 020F (`extends:` shorthand) + 020H part 3 (canonical YAML wrapper) trailing-dash typos corrected from `standards-control-plane` to `standards-control-plane-`. Three occurrences total. The plan §4 acceptance table is frozen at Threshold A, so no 020M plan row is added; 020M lives in STATUS.md "Post-Threshold-A backlog" alongside 020H.1 / .2 / .3 / .3.1 / .4 (consistent with established post-Threshold-A pattern). This slice qualifies as a plan-touch slice per TF-020H3-003 closure path because it amends the plan file (typo fix), satisfying the closure condition.
- [ ] **(ix) Release notes.** `docs/releases/v1.0.1.md` (or release notes section conforming to existing convention). Per VERSIONING.md tag-cut procedure step 1.
- [ ] **(x) Post-merge: dry-run release-gate.** `gh workflow run release-gate.yml -f dry_run_tag=v1.0.1` and `gh run watch --exit-status` per VERSIONING.md mandatory pre-flight.
- [ ] **(xi) Post-merge: push v1.0.1 tag** + publish GitHub release.

## Risk surface

1. **Hash-mismatch failure mode.** With `--require-hashes`, an `ubuntu-latest` runner that already has pyyaml/jsonschema preinstalled at any version DIFFERENT from the pinned version would fail when the conditional `if ! import` skip is taken — except the skip means no install runs at all, so no hash check. The risk is the OPPOSITE: if the runner does NOT have the package, pip downloads + verifies against the requirements file's hash list. If PyPI serves a wheel whose hash isn't in the list, pip refuses (correct behaviour — supply-chain attack caught). No new false-failure mode introduced for the green path.
2. **Cross-platform hash coverage.** `pip-compile --generate-hashes` includes hashes for wheels of all platforms PyPI publishes for the resolved version. CI runs on `ubuntu-latest` (Linux x86_64); the relevant wheel hash for pyyaml is in the file. Verified by inspection of the generated `requirements/policy-check.txt` (49 hash lines for pyyaml; covers all major platform/CPython tag combinations).
3. **Adopter checkout path.** Adopters consume the reusable workflow via `uses: jrnb2024/standards-control-plane-/.github/workflows/policy-check.yml@<sha>`. The adopter checkout step pulls the SCP runtime into `.scp-runtime/`, so `${SCP_RUNTIME_ROOT}/requirements/policy-check.txt` resolves correctly. Self-call fallback (line 107 sentinel-detect) symlinks `.scp-runtime` to caller working directory; the requirements file is then at the expected path either way.
4. **`release-gate.yml` path.** Release-gate runs only on the SCP repo itself (not adopters). Path is plain `requirements/policy-check.txt` (no `${SCP_RUNTIME_ROOT}` prefix). Confirmed by inspection (release-gate.yml does its own checkout, not via the .scp-runtime indirection).
5. **Future regeneration drift.** The pip-compile output captures the resolved transitive versions (`attrs`, `jsonschema-specifications`, `referencing`, `rpds-py`) at generation time. These versions DO drift over time as new releases land on PyPI. A regeneration on a future date may produce different transitive versions. Mitigation: header comment + `requirements/policy-check.in` (input) + the regeneration command let any maintainer reproduce the file deterministically by pinning to the same dates / using `--no-newer-than` if they want to freeze. For v1.0.1, the captured versions ARE the pinned versions; no drift until next regeneration.

## R1 review

3× parallel Sonnet R1 review (correctness / safety_bypass / completeness_governance). Recurse to fixpoint per `feedback_recursive_adversarial_review.md` (no-new-CRIT/MAJ on a complete cycle).

Lens-package files committed at:

- `docs/reviews/WP-SCP-022/dispatches/020m/review-correctness-package.json`
- `docs/reviews/WP-SCP-022/dispatches/020m/review-safety-package.json`
- `docs/reviews/WP-SCP-022/dispatches/020m/review-completeness-package.json`

Result + fix-round files alongside.

## Files

- `requirements/policy-check.in` (NEW) — top-level pin source.
- `requirements/policy-check.txt` (NEW) — generated, hash-pinned full closure.
- `.github/workflows/policy-check.yml` — 4 install-site swaps.
- `.github/workflows/release-gate.yml` — 1 install-site swap + comment cleanup.
- `version-manifest.json` — v1.0.0 → v1.0.1.
- `docs/DECISIONS.md` — D-038 row.
- `docs/releases/v1.0.1.md` (NEW) — release notes.
- `STATUS.md` — slice 020M chain row + TF-020H3rg-002 closure marker.
- `docs/plans/WP-SCP-020-policy-federation-primitive.md` — §4 020M row + TF-020H3-003 trailing-dash typo opportunistic close.
- `docs/reviews/WP-SCP-022/dispatches/020m/DISPATCH-NOTE.md` — this file.
