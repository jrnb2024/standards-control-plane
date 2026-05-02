# WP-SCP-022 slice TF-020P-005 — pre-push verify wrapper (dispatch note)

**Date:** 2026-05-02 (PM-4)
**Tier:** orchestrator-applied (Tier 1) per `feedback_four_tier_dispatch.md` — see "Tier-justification" below.
**Closes:** **TF-020P-005** (primary), **TF-020P-003** (Regal local-dev guidance — absorbed: the wrapper IS the guidance), **TF-020P-004** (`opa test --coverage --threshold 90` local-dev guidance — absorbed: same).
**Cuts:** no version bump. Internal-only tooling per `policies/VERSIONING.md` "Scope" — same posture as `.github/workflows/conflict-gate.yml` hash-pinning in slice 020N.

**Slice naming.** `TF-020P-005` is a tracked-forward closure slice on the post-Threshold-A backlog, not a new lettered slice. Lettered slices are reserved for substantive new surface; closing TF-class items uses the TF-id directly. Branch name `feature/wp-scp-022-tf-020p-005-pre-push-verify`.

## Rationale — why this slice now

Per `docs/reviews/WP-SCP-022/CONTINUATION-PROMPT-2026-05-02-pm-3.md` "Small TF-class slices (housekeeping)" recommendation, this is the highest-load-bearing housekeeping item remaining on the post-Threshold-A backlog:

1. **Slice 020P needed 4 CI roundtrips** — fix-rounds 2/3/4 each surfaced a verification step missing locally:
   - Round 2: Regal `pointless-reassignment` lint not run locally (CI's "Lint policies" step).
   - Round 3: `opa test --coverage --threshold 90` not run locally — the slice was at 89.7% (just under) and CI caught it.
   - Round 4: `opa fmt --fail` not run locally — local edits didn't preserve canonical formatting.
2. **Each future SCP-R-NNN rule slice will hit the same gaps.** WP-SCP-023 (cross-repo scorecards) likely adds new Rego predicates; without the wrapper it will re-litigate the same three CI gaps slice-by-slice.
3. **The fix is small and well-scoped.** A ~30-50 line bash wrapper that mirrors CI's three steps exactly (same Regal disable flags, same per-rule `opa test`, same `opa fmt --fail`) absorbs all three TF entries with no architectural change.
4. **Pre-WP-SCP-023 sequencing matters.** Landing TF-020P-005 before TF-006 + WP-SCP-023 implementation slices means the next WP picks up clean local-dev verification from the first commit.

## Scope decision — what's IN, what's OUT

| Item | Disposition | Rationale |
|---|---|---|
| `scripts/scp-pre-push-verify.sh` (new bash wrapper) | **IN** | Primary deliverable. Mirrors CI's three SCP-R rule gates: Regal lint + `opa fmt --fail` + per-rule `opa test --coverage --threshold 90 --fail-on-empty -v`. |
| Same Regal `--disable` flag list as CI | **IN** | CI/local parity is the slice's whole point. Source-of-truth is `.github/workflows/policy-check.yml` "Lint policies with Regal" step. |
| Per-rule `opa test` invocation (one per `SCP-R-*.rego`) | **IN** | Mirrors CI exactly. Aggregate `opa test policies/...` would obscure which rule's coverage tripped. |
| Aggregate failure-collection (run all 3 steps before exiting) | **IN** | Operator UX: surfacing all three failures in one run is faster than fail-fast across multiple invocations. |
| Tool-presence preflight (`command -v opa regal`) with clear install hint | **IN** | Without preflight the script's failure mode is opaque shell errors. |
| `.tool-versions` version-mismatch warning (non-fatal) | **IN** | If local opa/regal versions diverge from `scripts/.tool-versions`, surface a warning but keep running — non-fatal because local-dev parity ≠ supply-chain pin enforcement. |
| README.md / ADOPT-001 reference to the new script | **IN** | One-line pointer in README §Local development OR ADOPT-001 §12.7.9 (pre-commit hook contract). Decision: ADOPT-001 §12.7.9 is the right home — it already documents pre-commit hook posture. |
| `lib/test-pre-push-verify.bats` or smoke-test for the script | **OUT (filed forward as TF-020P-005a if R1 surfaces this as required)** | Smoke-testing a 50-line bash wrapper that calls already-CI-tested binaries adds review surface without commensurate value-add. Justify in DISPATCH-NOTE (this section). If R1's safety lens flags it, escalate. |
| CODEOWNERS entry for the new script | **OUT (already covered)** | Existing `scripts/** @jrnb2024` rule (CODEOWNERS:55) covers `scripts/scp-pre-push-verify.sh` with no edit. |
| Wiring as a git pre-push hook (`.git/hooks/pre-push`) | **OUT** | `.git/hooks/` is per-clone state, not committable. Documenting the manual install pattern in ADOPT-001 §12.7.9 is sufficient. Adopters can wire it via Husky / pre-commit framework if they prefer. |
| Bootstrapping opa/regal binaries with SHA verification | **OUT** | Out of scope. `scripts/scp-policy-check` is the canonical SHA-verifying bootstrap script. The pre-push wrapper assumes the operator has `opa`/`regal` already installed (matching how WP-SCP-022 has been operating to date). |
| Running Conftest tests (`policies/tests/*_test.rego` via Conftest, not OPA) | **OUT** | CI's coverage-enforcement step uses `opa test`, not Conftest. The wrapper mirrors that. Conftest is for `tests/conflict_gate/fixtures/**` which is conflict-gate's domain, not pre-push. |
| Replicating the workflow-selftest harness | **OUT** | Different concern (workflow integrity, not rule-author pre-push). |
| `version-manifest.json` bump | **OUT** | Internal tooling, no public-surface change. Per VERSIONING.md "Scope". |
| `RELEASE_NOTES.md` entry | **OUT** | Internal tooling, no adopter-visible behaviour change. |

## Tier-justification (why orchestrator-applied + 3-lens R1, NOT Codex executor)

Per `feedback_four_tier_dispatch.md` in-line escalation guidance:

**Arguments for Codex executor:** new bash file, ~50-100 lines, multiple interacting tool invocations.

**Arguments for orchestrator-applied:**
- Implementation is **mechanical translation** from `.github/workflows/policy-check.yml` (three CI steps) to a single bash script. The CI block is 80 lines; the wrapper is a near-1:1 condensation.
- No design decisions remain — every flag is fixed by parity with CI.
- The slice surface is bounded (one new file + one ADOPT-001 paragraph) and the failure modes are well-understood (binary missing, version mismatch, gate trips).
- Recursive 3-lens Sonnet R1 review is the right adversarial layer: correctness (does it actually mirror CI?), safety (does it introduce any new bypass surface?), completeness (does it close all three TF entries cleanly?).
- 020M, 020N, 020L, 020P all used orchestrator-applied + 3-lens R1 successfully; this slice has strictly less surface than any of those.

**Decision: orchestrator-applied + 3-lens R1.** If R1 surfaces a CRIT/MAJ that requires non-trivial design rework, escalate to Codex executor for fix-round-2.

## Slice acceptance

- [ ] **(i) Wrapper script exists.** `scripts/scp-pre-push-verify.sh` with `set -uo pipefail`, `#!/usr/bin/env bash` shebang, `chmod +x`.
- [ ] **(ii) Regal lint mirrors CI exactly.** Same 12 `--disable` flags as `.github/workflows/policy-check.yml` "Lint policies with Regal" step (lines 545-566). Targets `policies/` directory.
- [ ] **(iii) `opa fmt --fail` mirrors CI exactly.** Iterates every `*.rego` under `policies/` (including `policies/tests/`). Same find-loop pattern as CI lines 569-577.
- [ ] **(iv) Per-rule `opa test` mirrors CI exactly.** For each `policies/SCP-R-*.rego`: invoke `opa test <rule_file> policies/scp_common.rego policies/tests/<lowered_rule_base>_test.rego --coverage --threshold 90 --fail-on-empty -v`. Same per-rule iteration as CI lines 579-620.
- [ ] **(v) Aggregate failure collection.** All three steps run; failures collected and reported at end; non-zero exit only after all run. Operator sees full failure surface in one invocation.
- [ ] **(vi) Tool preflight.** `command -v opa` + `command -v regal` + (optionally) `command -v jq` checked at start; missing-tool error names the tool + suggests install path (`brew install opa regal` on darwin, distro-equivalent on linux).
- [ ] **(vii) `.tool-versions` parity warning (non-fatal).** Read `scripts/.tool-versions`; if local `opa version` / `regal version` differs, emit a warning but keep running.
- [ ] **(viii) Repo-root anchoring.** Script auto-resolves repo root via `git rev-parse --show-toplevel`; runnable from any subdirectory. `set -uo pipefail` (not `-e`) so failures don't short-circuit before all gates run.
- [ ] **(ix) Clear pass/fail banner at end.** Green "✓ all 3 SCP-R gates pass" or red "✗ N of 3 SCP-R gates failed" with bulleted list of which gates.
- [ ] **(x) ADOPT-001 §12.7.9 reference.** One-paragraph note in `docs/adoption/ADOPT-001-project-onboarding.md` §12.7.9 (or wherever pre-commit-hook contract lives) pointing at `scripts/scp-pre-push-verify.sh` as the recommended pre-push gate.
- [ ] **(xi) STATUS.md tracked-forward updates.** Mark TF-020P-003 / 004 / 005 closed; reference this slice as closure path.
- [ ] **(xii) Adversarial review reaches fixpoint.** 3-lens R1 → recurse R2 / R3 until no new CRIT/MAJ on a complete cycle. Lens packages + result JSONs + FIX-ROUND-N.md alongside this DISPATCH-NOTE.
- [ ] **(xiii) PR opens + operator-merge per D-040.** No `scp-rule-proposal` label (this is a code/tooling PR, not a rule-RFC). CI green prerequisite.
- [ ] **(xiv) STATUS.md backfill + memory + close-out PR.** Update `project_post_threshold_a_state.md` to reflect TF-020P-003/004/005 closure.

## Risk surface

1. **Local-dev binary version drift from CI.** Mitigation: emit `.tool-versions` parity warning. Drift does not break the wrapper (CI uses SHA-pinned binaries; local can lag without affecting supply-chain trust). Stronger enforcement (fatal on version drift) is rejected — would force operators to upgrade local opa/regal in lockstep with CI bumps, creating friction with no commensurate safety gain at v1.x.
2. **Wrapper might lull operator into thinking it covers more than CI.** Mitigation: the wrapper covers ONLY the three rule-author-facing gates. It does NOT cover: workflow-selftest, conflict-gate Python evaluator, supply-chain SHA verification, freshness-warning, release-gate dry-run. Document this scope inline at the top of the script.
3. **Bash portability — `find -print0` / `xargs -0` / `read -d ''` are not POSIX.** Mitigation: shebang is `#!/usr/bin/env bash` and the script targets bash specifically. macOS ships bash 3.2; the constructs used are bash 3.2-compatible (matched by `scripts/replay-canary.sh` which already runs on the same surface).
4. **Failure collection might mask which gate caused which failure.** Mitigation: per-step output is verbose (`-v` on opa test, regal's default output, opa fmt's per-file failures). The end summary names the gate; the verbose output above shows the specifics.
5. **ADOPT-001 §12.7.9 reference may bind adopters who haven't installed opa/regal locally.** Mitigation: §12.7.9 will explicitly mark the wrapper as RECOMMENDED, not REQUIRED. Adopters without local opa/regal can still rely on CI; the wrapper is a CI-roundtrip-saver, not a federation-conformance gate.
6. **Bypass-surface concern: could an attacker tamper with the wrapper to silently skip gates?** Mitigation: the wrapper is purely informational; CI is still the authoritative gate. A tampered wrapper would only fool the operator's local-dev experience, not CI's enforcement. CODEOWNERS `scripts/** @jrnb2024` already routes any wrapper change through review.

## R1 review

3× parallel Sonnet R1 review (correctness / safety / completeness). Recurse to fixpoint per `feedback_recursive_adversarial_review.md`. Lens packages + result JSONs + FIX-ROUND-N.md alongside this file.

Review surface focuses:
- **Correctness.** Does `scripts/scp-pre-push-verify.sh` produce identical pass/fail verdicts to CI's three steps when run against the same `policies/` tree? Are the Regal disable flags identical to CI's list? Is the per-rule `opa test` invocation identical (same flags, same loaded files)? Does failure-collection actually report all three gates' status without short-circuiting? Does `set -uo pipefail` (without `-e`) interact correctly with the failure-collection pattern?
- **Safety / bypass.** Does the wrapper introduce any new bypass surface? Could a tampered local opa/regal binary silently pass while CI fails (yes, but CI is authoritative — the wrapper is informational only)? Is there a path where `--threshold 90` is silently dropped (e.g. shell quoting bug)? Does the version-parity warning emit confidently enough to be noticed by an operator? Does the wrapper write to any state outside the repo (no — should be confirmed)?
- **Completeness.** Does the slice actually close TF-020P-003/004/005 cleanly (the three gaps named in their closure paths)? Does ADOPT-001 §12.7.9 (or wherever) reference the wrapper? Does STATUS.md mark all three TFs closed? Is there any gap between "wrapper exists" and "operator actually uses it" that should be addressed in this slice (vs deferred to a future slice)?

## Files

- `scripts/scp-pre-push-verify.sh` (NEW; ~80-100 lines bash).
- `docs/adoption/ADOPT-001-project-onboarding.md` — §12.7.9 (or appropriate section) one-paragraph reference.
- `STATUS.md` — TF-020P-003 / 004 / 005 marked closed.
- `docs/reviews/WP-SCP-022/dispatches/020p-005-pre-push-verify/DISPATCH-NOTE.md` (this file).
- `docs/reviews/WP-SCP-022/dispatches/020p-005-pre-push-verify/review-{correctness,safety,completeness}-package.json` — R1 lens packages.
- `docs/reviews/WP-SCP-022/dispatches/020p-005-pre-push-verify/review-{correctness,safety,completeness}.json` — R1 results.
- `docs/reviews/WP-SCP-022/dispatches/020p-005-pre-push-verify/FIX-ROUND-N.md` — per fix-round audit (if any rounds needed).

## Forward-looking

- **TF-020P-005a candidate** (file at slice close if R1 safety lens flags it): smoke-test the wrapper itself via a `tests/scripts/test_pre_push_verify.bats` or equivalent. Closure path: file when smoke-test value exceeds review-surface cost (probably never — the wrapper IS already covered by CI parity, the only meaningful failure mode is "wrapper diverges from CI" which a smoke-test wouldn't detect anyway).
- **TF-020P-001** (data-driven `WARN_BASELINE_RULES` manifest) — unchanged; file when 2nd warn-baseline rule lands. Not relevant to this slice.
- **Pre-push hook installer slice** — possible future TF if adopter feedback says "wrapper is recommended but I forgot to run it." Not filed yet.
