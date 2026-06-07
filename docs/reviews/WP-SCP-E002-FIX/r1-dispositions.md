# R1 dispositions — v1.5.1 SCP-E002 over-broad on deleted manifests

**Change:** `fix/scp-e002-deleted-manifest` (standalone PATCH bugfix, SEPARATE from WP-SCP-028).
**Baseline:** `main` @ `9533891` (v1.5.0).
**Review mode:** mandatory 3-lens adversarial R1 (correctness / safety_bypass / completeness_governance), dispatched as three parallel reviewers per estate standard. safety_bypass is a hard-stop lens.

## The bug

`.github/workflows/policy-check.yml` "Prepare manifest evaluation targets" step iterated `changed-files.txt`. In adopter mode that file is `git diff --name-only BASE..HEAD`, which **includes deletions**. For any path whose basename ∈ {package.json, pyproject.toml, go.mod} the old inline Python did `manifest_count += 1; if not Path(path).is_file(): print ::error SCP-E002; sys.exit(1)`. So any adopter PR that **deleted** a manifest (e.g. retiring a vendored Go module's `go.mod`) hard-failed the required `policy-check / scp/policy-check` gate. Live repro: mapp-pim #403 deleting `pkg/platform/vendor/github.com/mapp-fashion/ctauth/go.mod`.

## The fix

1. Skip a manifest that is not a regular file at HEAD (a deletion) instead of failing — a removal has no content to evaluate and no vendoring-attestation surface to hide.
2. Move `manifest_count += 1` **after** the skip so a pure deletion cannot flip `SCP_R003_MANIFEST_APPLICABLE` true for a no-op.
3. Extract the (now-fixed) target-prep logic out of the inline workflow heredoc into `lib/policy_check_invocation.sh::scp_policy_check_prepare_manifest_targets` so it is directly unit-testable. `lib/` is an internal surface per `policies/VERSIONING.md` §Scope ("refactored without notice") → PATCH-class internal refactor. The workflow step now `source`s the lib and calls the function.
4. Test: `tests/workflow/test_prepare_manifest_targets.py` (stdlib-only; runnable via plain `python`, also pytest-collectable) — deletion-skipped / modified-evaluated (anti-over-skip) / mixed. Wired into CI via the standalone `prepare-manifest-targets-unit` job in `.github/workflows/workflow-selftest.yml` (the only place that runs it; conftest-gate.yml runs pytest only over `tests/conflict_gate/`).
5. `version-manifest.json` 1.5.0→1.5.1; `STATUS.md` chain entry.

## Lens verdicts

- **safety_bypass: APPROVE.**
- **correctness: REJECT** — dispositive reason is the changeset contamination (see CRIT-CONTAM); core logic would APPROVE in isolation.
- **completeness_governance: REJECT** — dispositive reason is the same contamination; governance (PATCH legitimacy, count-12 invariant, surface-stability) all check out.

## safety_bypass reasoning (the operator's explicit question)

**Can skipping a deleted manifest hide a vendoring-attestation evasion? No.** Traced end-to-end: `policies/SCP-R-003.rego` fires `deny` only when `input.content` exists and lacks the `scp:vendoring-attested` marker; its entire input is the YAML surrogate, which is now built **only for manifests present on disk at HEAD**. A deleted manifest has no content at HEAD — the deletion removes the entire declaration, so there is nothing to attest and no surface to bypass. The old `sys.exit(1)` was never a detection control; it was an over-broad hard-fail. Counterexample search (delete `go.mod` + smuggle malicious vendored `.go`): SCP-R-003 never evaluated vendored source content, and `.go` files are skipped at the conftest extension filter regardless — so the fix removes a false-positive block, not a detection. No SCP rule keys on the *absence/deletion* of a manifest path, so dropping the deleted entry from `changed-files.txt` suppresses nothing. `manifest_count`-after-skip makes `SCP_R003_MANIFEST_APPLICABLE` strictly track evaluable manifests → no false-negative on a fireable rule. The lib is sourced from the SCP-pinned `${SCP_RUNTIME_ROOT}` runtime (not adopter-controlled); adopter values are handled only as Python strings (`Path`/`read_text`/`json.dumps`), heredoc is single-quoted — no injection vector.

## Findings and dispositions

| ID | Lens | Sev | Finding | Disposition |
|---|---|---|---|---|
| CRIT-CONTAM | corr + compl | CRIT | Working tree commingles unrelated WP-SCP-028 Phase-2 R-028 fixtures + count 12→15 in `workflow-selftest.yml` + untracked `fixture-scp-r-028-*` dirs (committed nowhere). Caused by a **concurrent WP-SCP-028 Phase-2 session writing the same shared working tree** (proven by file mtimes: `workflow-selftest.yml` rewritten at 06:11 after my edits; fixture dirs created 06:05–06:07 interleaved). The R-028 trust-boundary fixture passes `simulate-canonical-verify-failure` (an input not declared on `policy-check.yml` here — it is in `stash@{0}`), so left as-is the `workflow-selftest` required check would go RED. | **RESOLVE via operator coordination** (operator chose "coordinate, then I finish"). Other session checkpoints/commits its R-028 WIP to its own branch; I then restore `workflow-selftest.yml` to main + only my job and stage my files explicitly (never `git add -A`). I will NOT strip/stash the R-028 work (committed nowhere → would destroy live WIP). |
| WIRE-AGG | corr + compl | MAJ | `prepare-manifest-targets-unit` is terminal — absent from the `workflow-selftest` aggregator's `needs:` list, so a failing unit test would not block the required check. | **FIX at finish** — add `prepare-manifest-targets-unit` to the `workflow-selftest` job `needs:`. |
| WIRE-PATH | corr + compl | MAJ | `workflow-selftest.yml` `on.pull_request.paths` omits `lib/**`; a future lib-only edit to the extracted function would not trigger the selftest. | **FIX at finish** — add `lib/**` to the path-trigger set. |
| TWIN-CONFTEST | compl + corr | MAJ→FUP | Identical-class bug in `scp_policy_check_run`: a DELETED non-manifest conftest-parseable file (removed `services.yml`/`.yaml`/`.json`/`.toml`) passes the extension filter (no `is_file` check), reaches `conftest "${targets[@]}"` as a non-existent path → conftest errors → SCP-E002 + `return 1`. Same root cause (adopter `git diff` includes deletions), same required gate. completeness lens argues fold-now (one-line `[ -f "$target" ] || continue` + test) vs split. | **SURFACED** as `FUP-SCP-E002-CONFTEST-DELETED-TARGET-001` (STATUS.md). **Decision deferred to operator at finish**: fold into v1.5.1 (in dispatch scope: `lib/` + `tests/workflow/`; same bug framing) OR keep as a ratified split (split-not-descope). Not silently dropped. |
| R1-BOOKKEEP | compl | MAJ | STATUS.md cited this dispositions doc as "ACCEPT at R-FIXPOINT" before it existed / before R1 completed. | **FIX** — this doc now exists and records the real findings; at finish, STATUS wording is reconciled to the true post-fold state (ACCEPT contingent on WIRE-AGG + WIRE-PATH folded and the tree de-contaminated). |
| ISFILE-COMMENT | safety | MIN | `not source.is_file()` is broader than "deletion" (also dir / broken symlink / FIFO). Old code fail-closed there; new code fail-open. Provably non-exploitable (no readable regular-file content = nothing to attest; a symlink to a real regular file resolves True and IS evaluated). | **FIX at finish** — broaden the comment to state the condition is "any non-regular-file path = no evaluable content = skip (intentional, safe)". No behavioural change. |
| ENV-COMMENT | corr + compl | MIN | Function docstring says GITHUB_ENV is "skipped if unset, e.g. under the unit test," but the unit test SETS GITHUB_ENV; the unset branch is actually uncovered. | **FIX at finish** — correct the docstring example. |
| TEST-CORPUS | compl | MIN | Tests exercise deletion/modification only via `go.mod`; `package.json`/`pyproject.toml` deletion paths and multi-deletion not directly asserted (logic is basename-set symmetric → low risk). | **ADD at finish** — one `package.json` deletion case for breadth. |

## Governance checks that PASS (no action)

- **v1.5.1 PATCH is correct.** `SCP-E002` is NOT removed as a surface — it still fires in multiple other conditions in the lib (init-outputs path checks, changed-files-missing, waiver/rule-config wrapper failures, conftest failure). Only one over-broad *trigger condition* (deleted manifest) is dropped — a loosening (fewer denies), never classified as breaking by `policies/VERSIONING.md`. The §Scope clause names `lib/policy_check_invocation.sh` internal-only → extraction is PATCH-legit. No workflow-input / schema / rule-ID / error-code surface changed.
- **Count-12 invariant intact for the clean PR.** `prepare-manifest-targets-unit` adds NO `uses: ./.github/workflows/policy-check.yml` line; the 12→15 bump is purely the R-028 contamination.
- **Behavioural equivalence of the extraction** verified line-by-line against the former inline Python: surrogate indexing `{index:04d}`, YAML payload shape, trailing-newline handling, changed-files rewrite, and the flag write are preserved; only the three intentional deltas (env-driven changed-files path, GITHUB_ENV `.get` guard, manifest_count-after-skip) differ.

## Final disposition

**ACCEPT at R-FIXPOINT, contingent on the finish step:** (a) tree de-contaminated via operator coordination; (b) WIRE-AGG + WIRE-PATH folded; (c) ISFILE-COMMENT + ENV-COMMENT + TEST-CORPUS folded; (d) TWIN-CONFTEST fold-vs-split decided with the operator. The core fix is correct and safe (unanimous on the logic; safety_bypass clean with no REJECT). The REJECTs were environmental (shared-tree contamination), not defects in the fix.
