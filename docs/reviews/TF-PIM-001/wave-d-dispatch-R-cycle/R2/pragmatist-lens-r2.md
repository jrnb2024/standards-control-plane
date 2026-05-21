# TF-PIM-001 Wave D dispatch JSON — pragmatist lens R2

**Dispatched:** 2026-05-21 PM (post v0.2 fold)
**Agent type:** Plan (read-only; DO-NOT-EDIT mandate per `feedback_subagent_review_only_scope_must_be_enforced`)
**Model:** Sonnet
**Worktree isolation:** yes
**Lens domain:** execution feasibility + Codex actionability + verify_commands runnability
**Artefact under review:** dispatch JSON v0.2

---

**Verdict:** ACCEPT
**Convergence signal:** R-FIXPOINT-MET
**Findings count:** 0 total (0 BLOCKING + 0 MAJ + 0 MIN + 0 NIT)
**R1 closures verified:** PRAG-MAJ-001 verified; PRAG-MIN-001 verified; PRAG-NIT-001 verified (subsumed)
**New findings:** none

---

## R1 closure verification

### PRAG-MAJ-001 verification — VERIFIED

CMD 20 + CMD 21 now use `git diff HEAD --` (working-tree-vs-last-commit), no `git fetch origin main` prefix. Probes correctly capture Codex's unstaged edits in `workspace-write` sandbox (per `codex_dispatch.py` line 138 "Leave changes unstaged in the working tree" + line 550 `git_sha_before == git_sha_after` invariant). Closure is fully correct.

### PRAG-MIN-001 verification — VERIFIED

Invariant 5 prose updated to "one new step (9 YAML lines)" with minimum-added-line count documented as 11. CMD 21 lower bound bumped from `-ge 8` to `-ge 11`. Math correct: 9 EDIT 1 lines + 1 EDIT 2 token + 1 EDIT 3 token = 11 minimum. Upper bound 30 provides ~17 lines of slack against realistic max of ~13. Appropriately calibrated.

### PRAG-NIT-001 verification — VERIFIED, SUBSUMED

The original NIT concern (token-before-path ordering not verified) is fully subsumed by ARCH-MIN-001 closure. CMD 18 in v0.2 performs three-point semantic ordering check `REPO < TOKEN < PATH` using `grep -nF | head -1` line-number extraction. Strictly stronger than the proximity-window approach in v0.1.

---

## New focus areas — assessment summary (no findings)

**Working-tree diff probe correctness** — confirmed. `codex_dispatch.py` line 138 explicit "Leave changes unstaged"; line 550 `git_sha_after` post-execution; no commit. `git diff HEAD --` correctly captures unstaged + staged changes. Network-independent.

**CMD 20 single-file equality test** — semantically correct. Shell command substitution strips trailing newlines; single-file change produces exact path string match; two-file change inserts middle newline that breaks equality. More stringent than `wc -l = 1` + separate path check.

**CMD 21 diff-size budget calibration** — sound. Lower 11 tight-correct; upper 30 generous-safe with ~17 lines slack against expected-max 13.

**Semantic ordering verify_commands aliasing risk** — none. All four anchor strings globally unique in policy-check.yml (line 109 / line 111 / line 1151 / line 1153 confirmed). `grep -nF | head -1` returns deterministic first-match. EDIT 2 + EDIT 3 token patterns are non-overlapping strings; each appears exactly once post-edit.

**Codex first-attempt success likelihood** — high. Instruction provides exact 9-line YAML for EDIT 1 with indentation context; exact `token:` line text for EDITS 2 + 3; explicit placement instructions; EDIT 2 vs EDIT 3 fallback asymmetry explained at length. 21 verify_commands give Codex a complete correctness oracle. gpt-5.4 xhigh + 2700s timeout appropriate.

**Notes field verbosity** — not a pragmatist concern. Confirmed from `codex_work_package.schema.json` line 58: notes field "appear in dispatch log, not in Codex prompt." `_construct_prompt` in `codex_dispatch.py` lines 75-139 builds prompt from `instruction`, `spec_paths`, `scope_boundary`, `verify_commands` only — notes never reach Codex's attention budget.

---

## Codex execution feasibility disposition (post-v0.2)

The v0.2 dispatch JSON is ready for Codex execution. All three R1 PRAG findings closed. Instruction substantively complete: verbatim 9-line EDIT 1 step body with correct SHA pin, correct `if:` guard, correct `with:` inputs. EDIT 2 and EDIT 3 precisely differentiated by the intentional fallback asymmetry with co-gated reasoning explained at sufficient depth for gpt-5.4 xhigh to reproduce. Three insertion sites uniquely resolvable at HEAD `a25860d`. Scope_boundary single-file. 2700s timeout adequate. Wave E derogation clearly out-of-scope. No remaining ambiguity that would cause scope breach, fallback inversion, or YAML syntax error on first dispatch.

## Verify_commands runnability disposition (post-v0.2)

All 21 verify_commands syntactically valid and semantically correct in Codex's CWD post-edit. CMD 16 (awk-window if-guard) is runnable with appropriate ±3 window for standard step-header. CMD 17 (step-ordering) runnable on unique anchors. CMDs 18-19 (EDIT 2 + EDIT 3 ordering) runnable and aliasing-safe. CMD 20 (working-tree scope gate) correctly probes unstaged changes. CMD 21 (diff-budget) tight-correct lower bound, generous-safe upper bound. YAML parse check succeeds. All grep -F / grep -cF treat `${{ ... }}` as literal strings. Negative-assertion commands (`! grep -qE`, `! grep -F`) correctly formed. Full 21-command suite produces clean verify-pass on any correct Codex execution.

## Convergence signal rationale

R-FIXPOINT-MET. All three R1 PRAG findings verified closed. Zero new pragmatist issues. v0.2 amendments internally consistent. Notes verbosity confirmed Codex-invisible. No instruction ambiguity, no verify_command runnability gaps, no scope_boundary / timeout concerns. R-fixpoint criterion met: no significant findings on substantive content remain open in the pragmatist domain.
