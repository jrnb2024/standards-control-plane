# TF-PIM-001 Wave D dispatch JSON — arch-skeptic lens R2

**Dispatched:** 2026-05-21 PM (post v0.2 fold)
**Agent type:** Plan (read-only; DO-NOT-EDIT mandate per `feedback_subagent_review_only_scope_must_be_enforced`)
**Model:** Sonnet
**Worktree isolation:** yes
**Lens domain:** architectural fit + reversibility + failure-surface + plan-doc fidelity
**Artefact under review:** dispatch JSON v0.2

---

**Verdict:** ACCEPT
**Convergence signal:** R-FIXPOINT-MET
**Findings count:** 1 total (0 BLOCKING + 0 MAJ + 0 MIN + 1 NIT)
**R1 closures verified:** ARCH-MAJ-001 verified; ARCH-MAJ-002 verified; ARCH-MIN-001+PRAG-NIT-001 verified; ARCH-MIN-002 verified; ARCH-MIN-003 verified (subsumed); ARCH-NIT-001 verified; ARCH-NIT-002 verified (false positive confirmed via schema)
**New findings:** 1 NIT (NEW-ARCH-NIT-R2-001 — CMD 16 awk-window coding inconsistency; non-blocking)

---

## R1 closure verification

### ARCH-MAJ-001 verification — VERIFIED, SOUND

The v0.2 instruction encodes the intentional asymmetry correctly at both expression and rationale levels. EDIT 2: `token: ${{ steps.scp-app-token.outputs.token }}` (plan-doc verbatim; no fallback). EDIT 3: `token: ${{ steps.scp-app-token.outputs.token || github.token }}` (fallback present). The EDIT 2 rationale is now explicit and architecturally complete: co-variant guards mean App token is guaranteed non-empty when EDIT 2 runs; fallback would be unreachable dead code teaching a misleading pattern. The EDIT 3 rationale identifies this site as the ONLY location where fallback is critical, driven by `if: always()` decoupling. Self-documenting in the instruction prose with explicit cross-reference.

Step-failure cascade semantics correctly encoded: under token-exchange failure, EDIT 2 step is skipped (default `success()` on its `if:`); EDIT 3 runs but fails fail-closed via permission-denied checkout. Both paths fail-closed.

### ARCH-MAJ-002 verification — VERIFIED, AUTHORITATIVE AND SUFFICIENT

The `notes` field embeds raw API resolution evidence inline. PRIMARY: `"sha":"bcd2ba49218906704ab6c1aa796996da409d3eb1"` + `"type":"commit"` — direct commit-type, no dereference. FALLBACK: two-step annotated-tag dereference chain documented (tag-SHA → commit-SHA `3beb63f4bd073e61482598c45c71c1019b59b73a`). Tag annotation metadata included. Provenance is independent of network access at verify time.

### ARCH-MIN-001 / PRAG-NIT-001 verification — VERIFIED, SEMANTICALLY SOUND

Awk-window probes replaced with semantic two-phase grep ordering checks (CMD 18 + CMD 19). CMD 18 (EDIT 2) anchors on three globally-unique strings (`repository: ${{ github.action_repository }}` / `token: ${{ steps.scp-app-token.outputs.token }}` / `path: .scp-runtime`). CMD 19 (EDIT 3) analogous. Resilient to comment-block preservation, blank-line insertion, line-count drift. `head -1` ensures first occurrence used; each anchor is unique so no aliasing risk.

### ARCH-MIN-002 verification — VERIFIED, OPERATIONALLY UNAMBIGUOUS

Wave E coupling derogation note in `notes` is specific and actionable. Names the constraint, explains sequential sequencing rationale, provides explicit operator coordination instruction. Operator firing the dispatch has sufficient information without consulting the plan-doc §4 directly.

### ARCH-MIN-003 verification — VERIFIED, SUBSUMED

No `git fetch origin main` dependency remains anywhere in v0.2 verify_commands. CMD 20 + CMD 21 both use `git diff HEAD` (working-tree-vs-last-commit). The `>/dev/null 2>&1` fetch error suppression is gone. Fully subsumed by PRAG-MAJ-001 fix as projected.

### ARCH-NIT-001 verification — VERIFIED, CORRECTLY ENCODED

Invariant 6 added: "No permissions block amendment required... `actions/create-github-app-token` resolves credentials from GitHub Actions' built-in secret context; does NOT require `id-token: write` (which is OIDC). The existing WP-SCP-023 023B `id-token: write` exclusion is fully preserved." Coherent with the existing `permissions` block at lines 56-62 of policy-check.yml.

### ARCH-NIT-002 verification — VERIFIED, FALSE POSITIVE CONFIRMED VIA SCHEMA

`/Users/amplience/Projects/acc/schemas/codex_work_package.schema.json` line 49 explicitly enumerates `gpt-5.4` as a valid Codex CLI model: "Available: gpt-5.4, gpt-5.4-mini, gpt-5.3-codex, gpt-5.3-codex-spark, gpt-5.2." The schema's `reasoning_effort` description (line 54) explicitly pairs `gpt-5.4` with `xhigh` for kernel-dangerous work — exactly the v0.2 configuration. False positive confirmed.

---

## New findings

### NEW-ARCH-NIT-R2-001

**Type:** NIT
**Title:** CMD 16 retains an awk-window probe inconsistent with the ARCH-MIN-001 closure pattern
**Where:** `verify_commands` CMD 16
**Finding:** CMD 16 (the SEC-MIN-001 closure addition) is `IDLINE=$(grep -nF 'id: scp-app-token' ...); awk -v s=$((IDLINE-3)) -v e=$((IDLINE+3)) 'NR>=s && NR<=e' ... | grep -F "if: github.action_ref != ''"`. This is an awk-window probe — the same coding pattern that ARCH-MIN-001 closure replaced for CMD 18 and CMD 19. The window ±3 is tighter than the original ±8/+4 and is appropriate for the standard step-header shape (where `if:` sits 2 lines after `id:`), so functionally it will hold. But it is stylistically inconsistent with the new semantic ordering pattern.

**Why it matters:** NIT-level. Non-blocking. The ±3 window matches the expected `name:` → `id:` → `if:` step-header shape and will not false-fail on a standard Codex insertion.

**Suggested closure (operator-paced):** No action required before dispatch. Note for future hygiene: align CMD 16 with the CMD 18 / CMD 19 semantic-ordering pattern via a three-anchor check: `name: Obtain SCP federation App installation token` line < `if: github.action_ref != ''` line < `uses: actions/create-github-app-token@...` line.

---

## Plan-doc fidelity disposition (post-v0.2)

v0.2 is faithful to plan-doc §4 Wave D with one well-justified divergence captured in the instruction: EDIT 3's `|| github.token` fallback is a refinement on the plan-doc verbatim wording, justified by the if-always semantics; the plan-doc §4 Action step 4 should receive a post-R-fixpoint hygiene amendment (operator-paced; out-of-scope for this dispatch). EDIT 2 is now exact plan-doc verbatim. EDIT 1 reproduces the YAML block at plan-doc lines 188-198 verbatim with the SHA filled in. Scope_boundary remains correctly single-file. No new phantom citations.

## Convergence signal rationale

R-FIXPOINT-MET. All two MAJ + three MIN + two NIT R1 findings verified closed. The sole new R2 finding is NIT-class and non-blocking. Per the R-fixpoint criterion ("no new significant findings on a fresh round; one NIT does not constitute a significant finding"), R-FIXPOINT MET at v0.2. The arch-skeptic lens recommends NOT burning a third round to close the CMD 16 NIT — that would be cure-worse: the delta is a single verify_command substitution that can be folded mechanically without a full R3 lens dispatch. Option A R4 mechanical override threshold is R3, not R2, and is not engaged here because the R-fixpoint criterion is naturally satisfied.

Dispatch JSON v0.2 is ready for operator-paced PR opening + standdown at PR-opened state per continuation prompt step 7.
