# WP-SCP-022 slice 020N — conflict-gate hash-pinning (dispatch note)

**Date:** 2026-05-02
**Tier:** orchestrator-applied (Tier 1 only)
**Closes:** TF-020M-001 (`conflict-gate.yml` retains unhardened `pip install pyyaml>=6.0`). Filed at 020M R1 safety SAFE-MIN-003 closure.

**Slice naming.** "020N" is the next free post-Threshold-A letter after 020M (the supply-chain hash-pinning slice for the policy-check + release-gate workflows; v1.0.1, 2026-05-02). 020N extends the same supply-chain hardening posture to the conflict-gate workflow.

## Justification for not invoking Codex executor

Per `feedback_four_tier_dispatch.md` in-line escalation guidance.

The slice surface mirrors 020M's pattern:

- One generated artifact: `requirements/conflict-gate.txt` — produced by `pip-compile --generate-hashes` from `requirements/conflict-gate.in` (top-level pins matching `pyproject.toml` `[project.dependencies]` + `[project.optional-dependencies.dev]`).
- One companion source: `requirements/conflict-gate.in` — the input to `pip-compile`.
- One workflow file edit: `.github/workflows/conflict-gate.yml` "Install Python dependencies" step restructured to: (i) hash-pinned `pip install --require-hashes -r requirements/conflict-gate.txt`; (ii) local vendored `ct-auth` wheel installed `--no-deps`; (iii) editable local SCP package installed `--no-deps`; (iv) post-install version-pin assertion.
- D-039 + STATUS.md updates + TF-020M-002 prune.

No Rego rule paths exercised; no schema changes; no breaking surface changes. Orchestrator-applied + R1 × 3 is the right posture (symmetric with 020M dispatch note).

## Internal-surface justification (no semver bump)

Per `policies/VERSIONING.md` "Scope" section:

> It does NOT cover internal-only surfaces: `lib/policy_check_invocation.sh`, `scripts/scp-policy-check.lock`, helper scripts in `scripts/`, the Renovate preset internal shape, or the OPA Rego `scp_common.rego` helpers. These are refactored without notice.

`.github/workflows/conflict-gate.yml` is not in the public surface enumerated by VERSIONING.md §"Scope". It is a SCP-self-only workflow that runs on PRs to the SCP repo to enforce Rego/Python evaluator agreement; adopters do not consume it. The `requirements/conflict-gate.{in,txt}` files are likewise SCP-internal. Therefore **no version bump** is required and **no `policies/deprecations.yaml` entry** is needed.

This contrasts with 020M which bumped v1.0.0 → v1.0.1 because `policy-check.yml` IS a public surface (every adopter wrapper invokes it).

## Slice acceptance

- [ ] **(i) Generated requirements file.** `requirements/conflict-gate.txt` produced by `pip-compile --generate-hashes` from `requirements/conflict-gate.in`. Includes pyyaml + jsonschema + fastapi + uvicorn + httpx + pydantic + pytest + ruff + mypy + transitive closure with all-platform wheel SHA256s. Generated under Python 3.12 to match the workflow's `setup-python` pin (`python-version: "3.12"`).
- [ ] **(ii) `requirements/conflict-gate.in`.** Top-level pins source. Documents the regeneration command + REGENERATION INVARIANT (assertion-string lockstep update). Symmetric with `requirements/policy-check.in` (slice 020M).
- [ ] **(iii) `conflict-gate.yml` install step.** Replaced `pip install -e '.[dev]'` + `pip install pyyaml>=6.0` with: hash-pinned install + `--no-deps` ct-auth wheel install + `--no-deps -e .` SCP install + version-pin assertion.
- [ ] **(iv) Version-pin assertion.** Strict-equality `assert yaml.__version__ == "6.0.3"` (etc.) for pyyaml + jsonschema + fastapi + pydantic. Defends against future-PR drift (mirrors 020M SAFE-MAJ-002 pattern).
- [ ] **(v) D-039 amending decision.** `docs/DECISIONS.md` row ratifying conflict-gate hash-pinning posture (parallels D-038's slice-acceptance shape).
- [ ] **(vi) STATUS.md update.** TF-020M-001 marked ✅ closed in 020N. TF-020M-002 marked ✅ already-inline-closed in fix-round-2 (the REGENERATION INVARIANT callout in ADOPT-001 §12.7.13 already addresses the lockstep concern).
- [ ] **(vii) `requirements/**` CODEOWNERS coverage.** Already covered by 020M's edit; no new CODEOWNERS line needed.

## PyYAML version drift across workflows (acceptable)

`requirements/conflict-gate.txt` pins **pyyaml==6.0.3**; `requirements/policy-check.txt` pins **pyyaml==6.0.2**. The drift is intentional:

- `requirements/policy-check.in` pins `pyyaml==6.0.2` exactly (matching the v1.0.0 inline pin).
- `requirements/conflict-gate.in` pins `pyyaml>=6.0` (matching `pyproject.toml`'s `pyyaml>=6.0` constraint), which pip-compile resolved to the latest stable.

These are independent workflows with independent supply-chain anchors. The next regeneration of either lockfile may align them or not — drift is acceptable as long as both are hash-anchored.

## Risk surface

1. **Lockfile resolution under different Python versions.** Generated under Python 3.12 (matching `setup-python: python-version: "3.12"` in conflict-gate.yml). Wheels listed are for all platforms PyPI publishes; ubuntu-24.04 + Python 3.12 is the CI runtime — should be in the hash list.
2. **`ct-auth` vendored wheel chain-of-trust.** The wheel is in `vendor/python/ct_auth-0.8.0-py3-none-any.whl` (CODEOWNERS-protected via `vendor/** @jrnb2024`). Its install does NOT go through `--require-hashes` (pip refuses for local wheels). The chain-of-trust is the CODEOWNERS coverage on `vendor/**` plus the wheel being vendored in-tree (not fetched from a network).
3. **`pip install --no-deps -e .` could miss new transitive deps if pyproject.toml is edited.** A future PR that adds a new dependency to `pyproject.toml` without updating `requirements/conflict-gate.in` would fail at runtime (the new module would not be importable). This is fail-closed but not loud at PR-time. Closure path: a future linter could grep for unsynced deps; out of scope for 020N.
4. **Version-pin assertion drift on regeneration.** Mirrors the 020M REGENERATION INVARIANT — addressed by the explicit callout in `requirements/conflict-gate.in` documentation block.
5. **`ct-auth[fastapi]` extra deps coverage.** ct-auth's `[fastapi]` extra pulls in fastapi-related deps. Those deps overlap with `requirements/conflict-gate.txt`'s top-level pins (fastapi, pydantic, etc.). If ct-auth requires a transitive dep that's NOT in the lockfile (e.g. `cryptography`), the `--no-deps` install would succeed but runtime `import` would fail. ct-auth is currently used by SCP only via the MCP server path (slice WP-SCP-021); the conflict-gate doesn't exercise ct-auth at runtime. So the install will succeed even if a transitive is missing — fail-closed at the dependent code path, not at install time.

## R1 review

3× parallel Sonnet R1 review (correctness / safety_bypass / completeness_governance). Recurse to fixpoint per `feedback_recursive_adversarial_review.md` (no-new-CRIT/MAJ on a complete cycle).

Lens-package files committed alongside; result + fix-round files alongside.

## Files

- `requirements/conflict-gate.in` (NEW) — top-level pin source.
- `requirements/conflict-gate.txt` (NEW) — generated, hash-pinned full closure.
- `.github/workflows/conflict-gate.yml` — install step restructured (hash-pinned + version-assert + `--no-deps` for vendored wheel + editable SCP install).
- `docs/DECISIONS.md` — D-039 row.
- `STATUS.md` — TF-020M-001 closed; TF-020M-002 prune (already inline-closed).
- `docs/reviews/WP-SCP-022/dispatches/020n/DISPATCH-NOTE.md` — this file.
