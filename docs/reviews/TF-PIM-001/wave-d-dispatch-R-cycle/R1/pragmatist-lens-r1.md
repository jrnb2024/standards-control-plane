# TF-PIM-001 Wave D dispatch JSON — pragmatist lens R1

**Dispatched:** 2026-05-21 PM (Wave D dispatch authoring autonomous-scope per operator authorisation 2026-05-21 Reading A)
**Agent type:** Plan (read-only by design — DO-NOT-EDIT mandate enforced at tool-availability layer)
**Model:** Sonnet
**Worktree isolation:** yes (per estate auth-surface-plan-review default)
**Lens domain:** execution feasibility + Codex actionability + verify_commands runnability + scope-boundary realism + Tier 2 fire-readiness
**Artefact under review:** `docs/governance/work-packages/tf-pim-001-wave-d-policy-check-yaml-token-exchange.json` (v0.1)

---

**Verdict:** ACCEPT-WITH-AMENDMENT
**Convergence signal:** ITERATE-EXPECTED
**Findings count:** 3 total (0 BLOCKING + 1 MAJ + 1 MIN + 1 NIT)

---

## Findings

### PRAG-MAJ-001

**Type:** MAJ
**Title:** CMD 18 and CMD 19 use `git diff origin/main HEAD` (committed diff) — always produces empty result since Codex leaves changes unstaged; both commands will return non-zero exit on every correct Codex run
**Where:** `verify_commands` indices 17 and 18 (CMD 18 and CMD 19)

**Finding:** CMD 18 is:
```
git fetch origin main --depth=1 >/dev/null 2>&1; CHANGED=$(git diff --name-only origin/main HEAD -- 2>/dev/null); test "$CHANGED" = '.github/workflows/policy-check.yml' && echo "SCOPE OK: only policy-check.yml changed"
```
CMD 19 is:
```
git fetch origin main --depth=1 >/dev/null 2>&1; ADDED=$(git diff origin/main HEAD -- .github/workflows/policy-check.yml | grep -c '^+[^+]' || true); test "$ADDED" -ge 8 && test "$ADDED" -le 30 && echo "DIFF SIZE OK: $ADDED added lines (budget 8..30)"
```
Both use `origin/main HEAD` as the diff reference pair. This computes the diff between two committed states: the `origin/main` tip and the local `HEAD` commit. Evidence from the dispatch infrastructure (`acc/scripts/codex_dispatch.py` line 550, `git_sha_after = _git(cwd, "rev-parse", "HEAD")`) combined with dispatch logs confirms that Codex CLI in `workspace-write` sandbox mode consistently leaves changes UNSTAGED in the working tree without committing (`git_sha_before == git_sha_after` in all sampled dispatch logs). At the time Wave D fires, `HEAD` is `a25860d` = `origin/main` tip, so `git diff origin/main HEAD` produces zero output regardless of what Codex modified in the working tree. Consequently: CMD 18 produces `CHANGED=""`, and `test "" = '.github/workflows/policy-check.yml'` returns exit code 1 (false). CMD 19 produces `ADDED=0`, and `test 0 -ge 8` returns exit code 1. Both cause `verify_all_green = False` in the dispatcher, which overrides `effective_status = "blocked"` with `gate_failure = "verify_failed"` per `codex_dispatch.py` line 602. The dispatch is marked BLOCKED on every correct Codex execution. CMD 18 (scope gate) and CMD 19 (diff-budget gate) are the two highest-value structural safety verifications; their simultaneous failure is not a soft warning — it prevents the dispatch from completing.

**Why it matters:** Without functioning CMD 18 and CMD 19, every Codex run that correctly modifies only `policy-check.yml` will be marked BLOCKED. The operator will see a gate_failure="verify_failed" result and must diagnose whether the failure is real (Codex over-reached) or a false alarm (the commands themselves are wrong). On a kernel-dangerous Tier 2 dispatch, this false-alarm failure pattern invites the operator to dismiss gate failures as instrumentation noise, eroding the scope-gate discipline that Tier 2 dispatch protocol exists to enforce. Additionally, CMD 18 specifically is the ONLY verify_command that checks single-file scope at the git level — if it never runs correctly, there is no automated scope check beyond the dispatcher's own `scope_violations` computation.

**Suggested closure:** Replace both commands to diff against the working tree rather than committed history:

CMD 18 replacement:
```
CHANGED=$(git diff --name-only HEAD -- 2>/dev/null); test "$CHANGED" = '.github/workflows/policy-check.yml' && echo "SCOPE OK: only policy-check.yml changed"
```
(Drop the `git fetch` prefix — not needed for a working-tree-vs-HEAD comparison. `git diff HEAD --` shows all files modified in the working tree relative to the last commit, regardless of whether changes are staged.)

CMD 19 replacement:
```
ADDED=$(git diff HEAD -- .github/workflows/policy-check.yml | grep -c '^+[^+]' || true); test "$ADDED" -ge 11 && test "$ADDED" -le 30 && echo "DIFF SIZE OK: $ADDED added lines (budget 11..30)"
```
(Same: drop `git fetch`, replace `origin/main HEAD` with `HEAD` to capture unstaged working-tree diff. Lower bound tightened to 11 per PRAG-MIN-001.)

---

### PRAG-MIN-001

**Type:** MIN
**Title:** Instruction prose states "one new step (8 YAML lines)" but the EDIT 1 YAML block contains 9 lines; the diff-budget lower bound (8) is unreachable in any correct execution
**Where:** `instruction` field, Invariant 5 ("The diff is bounded to (a) one new step (8 YAML lines)"); `verify_commands` index 18 lower bound `test "$ADDED" -ge 8`

**Finding:** The YAML block in EDIT 1 has exactly 9 lines:
```
- name: Obtain SCP federation App installation token
  id: scp-app-token
  if: github.action_ref != ''
  uses: actions/create-github-app-token@...
  with:
    app-id: ...
    private-key: ...
    owner: jrnb2024
    repositories: standards-control-plane-
```
The minimum added-line count for any correct execution is 11 (9 step lines + 2 `token:` lines for EDIT 2 and EDIT 3), rising to 12 or more if a blank-line separator is inserted before the new step (standard YAML formatting convention in this file). The diff-budget lower bound of 8 is unreachable: no correct edit produces fewer than 11 added lines. The descriptive claim "8 YAML lines" is also off by one from the actual step body.

This finding is NOT about functional correctness of the YAML block itself. Codex reads the YAML block directly and will produce the correct 9-line step. The off-by-one only affects (a) the invariant description (human-facing) and (b) the diff-budget lower bound (which is too loose at the bottom but does not cause false rejections since 11 >= 8). The `test "$ADDED" -ge 8` guard will pass for any correct Codex output. However, the overly-loose lower bound (8 instead of 11) reduces the signal fidelity of CMD 19: a partial edit that adds only 8–10 lines (e.g., Codex inserts only EDIT 1 but forgets one `token:` line) would pass the lower bound gate.

**Why it matters:** The diff-budget gate is one of two structural guards against under-editing (the other being CMD 9 which checks for exactly 2 `token:` lines). The lower bound 8 admits under-edit scenarios that CMD 9 would catch independently. However, relying on CMD 9 as the sole under-edit guard means CMD 19's lower bound provides no incremental value. Tightening the lower bound to 11 would make CMD 19 non-redundant with CMD 9.

**Suggested closure:** (a) Amend the invariant-5 description from "8 YAML lines" to "9 YAML lines." (b) Update the CMD 19 lower bound from `test "$ADDED" -ge 8` to `test "$ADDED" -ge 11`.

---

### PRAG-NIT-001

**Type:** NIT
**Title:** CMD 16 proximity check verifies `repository: ${{ github.action_repository }}` is within ±8/+4 lines of the first `token:` line, but does NOT verify that `token:` precedes `path:` within the `with:` block
**Where:** `verify_commands` index 15 (CMD 16)

**Finding:** CMD 16 checks that `repository: ${{ github.action_repository }}` is within the awk window `[TOKEN_LINE - 8, TOKEN_LINE + 4]` of the first `token:` occurrence. This confirms EDIT 2's `token:` line is in the same `with:` block as the `.scp-runtime` checkout. However, it does not verify the EDIT 2 canonical ordering instruction: "Place the `token:` line BEFORE `path: .scp-runtime`." If Codex places `token:` AFTER `path: .scp-runtime` (i.e., `repository`, `ref`, `path`, `token`, `fetch-depth`, `persist-credentials`), CMD 16 still passes because `repository:` remains within the awk window. The `actions/checkout` action accepts inputs in any order (YAML keys are order-independent for the action runtime), so this is not a functional defect — it is a code-style violation against the canonical ordering stated in EDIT 2.

**Why it matters:** Low. `actions/checkout` v6 does not care about `with:` key ordering. The canonical ordering is a readability/style preference. No correctness risk.

**Suggested closure:** Optional. Replaced wholesale by ARCH-MIN-001 closure (semantic two-phase grep ordering check that asserts `repository:` < `token:` < `path:` line-numbers). The arch-skeptic-suggested fix subsumes this NIT.

---

## Codex execution feasibility disposition

With the MAJ finding (PRAG-MAJ-001) closed, the dispatch JSON is clean for gpt-5.4 + xhigh. The instruction is precise and non-ambiguous: EDIT 1 provides an exact 9-line YAML block with correct indentation (6/8/10 space hierarchy matching the existing file); EDIT 2 and EDIT 3 provide exact `token:` line text with unambiguous "BEFORE path:" placement instructions; the `|| github.token` fallback is explained at length with the correctness rationale for both the guarded case (EDIT 2, `if: github.action_ref != ''`) and the always-running case (EDIT 3, `if: always()`). The three insertion sites are each uniquely identifiable at `a25860d` HEAD (the `.scp-runtime` checkout step is unique; the `scp-self-checkout` step is unique via `id:`). All 17 non-broken verify_commands are syntactically valid bash and semantically correct: `grep -F` treats `${{ ... || ... }}` as a literal string (no shell expansion inside single quotes); `grep -cF` on the `token:` expression works correctly; the awk window calculations for CMD 16 and CMD 17 place `repository: ${{ github.action_repository }}` and `path: _scp-workflow` correctly within their respective windows under any reasonable indentation of the inserted lines. With CMD 18 and CMD 19 corrected to use `git diff HEAD` instead of `git diff origin/main HEAD`, all 19 verify_commands are runnable and the dispatch is highly likely to produce a correct verify-pass result on first attempt given gpt-5.4 xhigh's YAML editing accuracy.

## Verify_commands runnability disposition

16 of 19 verify_commands are fully runnable in Codex's CWD as authored: all `python3`, `grep -F`, `grep -cF`, `grep -qE`, `grep -nF`, `test`, `awk`, `cut`, `head`, `tail` invocations are standard POSIX; the `python3 -c "import yaml..."` YAML parse check will succeed (Python 3 is used in `policy-check.yml` itself confirming availability); shell arithmetic `$((TOKEN_LINE - 8))` is bash-safe and gracefully fails to a negative awk start-line if the line is not found; the `! grep -qE 'secrets:[[:space:]]*inherit'` and `! grep -F '${{ secrets.GITHUB_TOKEN }}'` negative checks are correctly formed. CMD 18 and CMD 19 are the two broken commands (identified as MAJ finding PRAG-MAJ-001): both use `git diff origin/main HEAD` which produces an empty diff because Codex operates on the working tree without committing, confirmed by inspection of `acc/scripts/codex_dispatch.py` dispatch infrastructure and sampled dispatch logs showing `git_sha_before == git_sha_after` universally. The `git fetch origin main --depth=1` prefix in CMD 18 and CMD 19 is also unnecessary overhead once the commands are corrected to `git diff HEAD`. After the two-command amendment, all 19 verify_commands will run correctly in Codex's dispatch environment.

## Convergence signal rationale

ITERATE-EXPECTED. There is one MAJ finding (PRAG-MAJ-001) that must be closed before dispatch fires: CMD 18 and CMD 19 in their current form guarantee a blocked dispatch on every correct Codex execution. The fix is mechanical — a single string replacement in each command (`origin/main HEAD` → `HEAD` and removal of the `git fetch` prefix). The MIN finding (PRAG-MIN-001) is a two-character change that tightens the diff-budget lower bound from 8 to 11 and corrects a prose off-by-one. The NIT (PRAG-NIT-001) is optional polish (subsumed by ARCH-MIN-001). None of the three findings require architectural changes to the instruction logic, the scope_boundary, the step YAML block, the `|| github.token` fallback, or any of the 17 working verify_commands. At v0.2 (after folding PRAG-MAJ-001 + PRAG-MIN-001), the dispatch JSON should reach R-FIXPOINT-MET: the instruction is substantively correct, the step YAML is accurate, the line-number anchors are verified against `a25860d` HEAD, and the remaining 17 verify_commands are all syntactically and semantically sound.
