# 020M fix-round-1 — closing R1 findings

**Date:** 2026-05-02
**Slice:** WP-SCP-022 020M (supply-chain hash-pinning + v1.0.1 cut)
**R1 review verdict (composite):** APPROVED_WITH_FINDINGS — 0 CRIT + 4 MAJ + 4 MIN + 6 nit across 3 lenses.
**Inputs:**
- `review-correctness.json` — 0 CRIT + 0 MAJ + 1 MIN + 2 nit.
- `review-safety.json` — 0 CRIT + 2 MAJ + 2 MIN + 2 nit.
- `review-completeness.json` — 0 CRIT + 2 MAJ + 1 MIN + 2 nit.

## R1 findings closed

### Safety lens

- **SAFE-MAJ-001 — CODEOWNERS gap on `requirements/`** ✅ closed inline. Added `requirements/** @jrnb2024` + `docs/releases/** @jrnb2024` to `CODEOWNERS` before the self-protection line, with header comment citing 020M R1 SAFE-MAJ-001 / SAFE-MIN-001. ORDERING INVARIANT preserved (specific governance rules before broad wildcards before self-protection).

- **SAFE-MAJ-002 — Runner-preinstalled-version bypass** ✅ closed inline. ubuntu-24.04 runners ship `pyyaml 6.0.1` from apt (`python3-yaml`); the prior conditional guard `if ! python3 -c 'import yaml'` would skip the hash-pinned install when this preinstalled version satisfied the import, running the workflow against the unhardened apt-shipped version. **Restructured all 4 install sites in `policy-check.yml` and the 1 site in `release-gate.yml` to:**

  (i) **Unconditional `pip install --user --require-hashes -r ...`** — runs every workflow execution regardless of runner-preinstalled state. `pip --require-hashes` is idempotent if the exact pinned version is already in user-site; otherwise pip downloads + hash-verifies + installs to user-site (which takes precedence over system-site per PEP 370).

  (ii) **Post-install version-pin assertion** — `python3 -c 'import yaml, jsonschema; assert yaml.__version__ == "6.0.2"; assert jsonschema.__version__ == "4.23.0"'`. Defends against future-PR drift where someone re-introduces a presence-only conditional skip without updating the lockfile pins. Failure mode emits a SCP-E001 / SCP-E004 annotation with the actual versions detected.

- **SAFE-MIN-001 — `docs/releases/**` CODEOWNERS gap** ✅ closed inline (same edit as SAFE-MAJ-001).

- **SAFE-MIN-002 — workflow-selftest trigger missing `requirements/**`** ✅ closed inline. Added `requirements/**` to `.github/workflows/workflow-selftest.yml` `pull_request.paths`. Renovate auto-bump PRs that touch only the lockfile now correctly trigger the selftest harness verification.

- **SAFE-MIN-003 — `conflict-gate.yml` retains unhardened `pip install pyyaml>=6.0`** ✅ filed as TF-020M-001 in STATUS.md "Tracked-forward items from 020M". Out of slice scope (TF-020H3rg-002 named `policy-check.yml` + `release-gate.yml` only); conflict-gate is a sibling workflow that exercises the Python evaluator against shared fixtures. Closure path: extend the 020M pattern to a sibling `requirements/conflict-gate.txt` (or share `requirements/policy-check.txt` if dep sets converge). Forward-compat v1.1.0 candidate.

- **SAFE-NIT-001 / SAFE-NIT-002** — covered by the MAJ closures above (CODEOWNERS coverage; runner-preinstall version drift defended).

### Correctness lens

- **COR-MIN-001 — `docs/releases/v1.0.1.md` line 28 mislabels plan change as "§4 020M row"** ✅ closed inline. Updated the line to read "three trailing-dash typo fixes in §4 020F + §4 020H part 3 (closes TF-020H3-003)" — accurately reflecting the actual diff.

- **COR-NIT-001 — `STATUS.md` missing from release notes file list** ✅ closed inline. Added `STATUS.md — slice 020M chain row + TF-020H3rg-002 + TF-020H3-003 + TF-020M-001 entries` to the release notes "Files in this release" section.

- **COR-NIT-002 — Hash-pinned install path skipped in primary CI run 25231306951** ✅ closed by the SAFE-MAJ-002 fix. The primary CI run will now always execute the install path on the next CI run (PR push triggers a new run).

### Completeness lens

- **COMP-MAJ-001 — TF-020H3-003 STATUS.md closure says "Both occurrences" but 3 lines were corrected** ✅ closed inline. Rephrased the closure description to: "**All three lines corrected** across **two logical locations**" with explicit enumeration of (1) §4 020F `extends:` shorthand line; (2) §4 020H part 3 renovate marker line; (3) §4 020H part 3 reusable-workflow ref line.

- **COMP-MAJ-002 — ADOPT-001 §12.7.13 not updated to disclose v1.0.1 Python dep hash-pinning** ✅ closed inline. Extended §12.7.13 with two new sub-paragraphs: (1) **Python dependency hash-pinning (post-020M)** — describes the `requirements/policy-check.txt` lockfile, the unconditional install pattern, the version-pin assertion, the CODEOWNERS coverage, and the adopter fork CODEOWNERS mirroring requirement; (2) **Lockfile regeneration procedure** — concrete `pip-compile --generate-hashes` command for adopters who maintain forks. Closes the SAFE-MAJ-001 + SAFE-MAJ-002 narrative on the adopter-facing side.

- **COMP-MIN-001 — ADOPT-001 §12.7.4 stale "TF-005 (deferred)" reference** ✅ closed inline. Updated to reflect TF-005 closure in slice 020H.3: "release-tag-time refusal of SCP-self expired rule-config entries is shipped at v1.0.0 via `.github/workflows/release-gate.yml` (TF-005 closed in slice 020H.3 — the release-gate workflow refuses a tag-cut when SCP-self `.scp/rule-config.yaml` has any `disable: true` entry with `expires_at < <UTC tag-cut date>`). Adopter-side rule-config expiry is enforced separately at PR time via SCP-E007."

- **COMP-NIT-001 — Duplicate TF-020H3rg-002 entry in STATUS.md** ✅ closed inline. Removed the redundant "Post-Threshold-A backlog" duplicate; the canonical closure marker remains in "Tracked-forward items from 020H.3 (release-gate)".

- **COMP-NIT-002 — Close-out plan does not name memory files** ✅ to be addressed in the close-out task (#10). Memory files to update: `project_post_threshold_a_state.md` (add 020M to landed slices); `project_wp_scp_022_plan.md` (reflect 020M closure).

- **COMP-NIT-003 — `requirements/**` CODEOWNERS gap** — covered by SAFE-MAJ-001.

## Files touched in fix-round-1

- `.github/workflows/policy-check.yml` — 4 install sites restructured (unconditional install + version-pin assertion).
- `.github/workflows/release-gate.yml` — install site smoke-test extended with version-pin assertion.
- `.github/workflows/workflow-selftest.yml` — `requirements/**` added to trigger paths.
- `CODEOWNERS` — `requirements/**` + `docs/releases/**` rules added before self-protection line.
- `docs/adoption/ADOPT-001-project-onboarding.md` — §12.7.13 extended; §12.7.4 stale TF-005 reference updated.
- `docs/releases/v1.0.1.md` — file list corrected (typo-fix wording, STATUS.md added, 3 new files added).
- `STATUS.md` — TF-020H3-003 closure phrasing corrected; TF-020M-001 added; duplicate TF-020H3rg-002 entry removed.
- `docs/reviews/WP-SCP-022/dispatches/020m/FIX-ROUND-1.md` — this file.

## R2 dispatch

3× parallel Sonnet R2 review on the post-fix branch HEAD. Lens-package files reuse R1 packages with HEAD ref bumped. Recurse to fixpoint per `feedback_recursive_adversarial_review.md` (no-new-CRIT/MAJ on a complete cycle).
