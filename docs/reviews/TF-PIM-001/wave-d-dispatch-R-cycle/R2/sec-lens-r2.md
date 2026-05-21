# TF-PIM-001 Wave D dispatch JSON — sec lens R2

**Dispatched:** 2026-05-21 PM (post v0.2 fold)
**Agent type:** Plan (read-only; DO-NOT-EDIT mandate per `feedback_subagent_review_only_scope_must_be_enforced`)
**Model:** Sonnet
**Worktree isolation:** yes
**Lens domain:** threat-model + auth-surface + trust-rooting + supply-chain
**Artefact under review:** dispatch JSON v0.2

---

**Verdict:** ACCEPT
**Convergence signal:** R-FIXPOINT-MET
**Findings count:** 0 total (0 BLOCKING + 0 MAJ + 0 MIN + 0 NIT)
**R1 closures verified:** SEC-MAJ-001 verified; SEC-MIN-001 verified; SEC-NIT-001 verified; SEC-NIT-002 verified
**New findings:** none

---

## R1 closure verification

### SEC-MAJ-001 verification — VERIFIED, closure is substantive and semantically complete

The v0.2 `notes` field contains the "Wave E coupling derogation" section. It explicitly quotes the plan-doc §4 Wave E MUST constraint, names the operator decision that resolves it (continuation prompt 2026-05-21 step 1 + Reading A), explains the resolution mechanism (sequential sequencing — Wave E fires after Wave D's PR branch exists; Wave E's edits land on the same branch before merge; no file-conflict possible), acknowledges the residual gap (no CI-verified SCP-E001 emission proof), and names the compensating controls (Wave F dogfood + Wave G PIM canary as live-system firewalls). Operator coordination instruction included: "Do NOT merge the PR containing the Wave D change alone — Wave E must be folded in first."

### SEC-MIN-001 verification — VERIFIED, proximity-check semantics are sound

The new verify_command CMD 16 (`IDLINE=$(grep -nF 'id: scp-app-token' ...); awk -v s=$((IDLINE-3)) -v e=$((IDLINE+3)) 'NR>=s && NR<=e' ... | grep -F "if: github.action_ref != ''"`) correctly probes the proximity of the if-guard to the token-exchange step's id. The ±3-line window is correct for the canonical step-header shape: `name:` → `id:` → `if:` → `uses:`. Failure modes (empty IDLINE; awk-window missing the guard) correctly exit non-zero.

### SEC-NIT-001 verification — VERIFIED, §12.7.13 obligation discharged

The v0.2 `notes` field contains the "Sigstore attestation status" section explicitly labelled as closing R1 SEC-NIT-001. The note records: GitHub first-party action; attestations not yet published; TF-007 parallel posture; SHA-pin remains primary supply-chain anchor; CODEOWNERS `.github/** @jrnb2024` gates updates. This satisfies §12.7.13's Wave-D-dispatch-time obligation.

### SEC-NIT-002 verification — VERIFIED, CMD 21 lower bound reads `-ge 11`

The final `verify_commands` entry in v0.2 has lower bound `-ge 11` (up from `-ge 8`), matching the corrected math: 9 EDIT 1 lines + 2 EDIT 2/3 token lines = 11 minimum. Invariant 5 prose updated from "8 YAML lines" to "9 YAML lines" — consistent with the boundary change.

## New focus areas — assessment summary (no findings)

**EDIT 2 fallback removal under token-exchange step failure** — confirmed fail-closed. Per GitHub Actions semantics, when a step's `if:` lacks `success()`/`always()`/`failure()`, the implicit `success()` applies. So when EDIT 1 (token-exchange) fails, EDIT 2 (`.scp-runtime` checkout) is SKIPPED regardless of `github.action_ref != ''` evaluation. No empty-token checkout request fires. EDIT 3 (`if: always()`) runs but the `|| github.token` fallback engages and the checkout fails permission-denied against private SCP (cross-repo case) — fail-closed. Both paths are correct.

**Embedded SHA provenance in `notes`** — no sec risk. The embedded raw API responses contain only public-data fields (commit SHAs, public repo URLs, public tag metadata). App ID is a non-secret identifier. No credential material anywhere.

**§12.7.10 invariant under v0.2 wording** — preserved. Invariant 2 unchanged in substance from v0.1. VC[11] enforces `! grep -qE 'secrets:[[:space:]]*inherit'`.

**CMD 9 + CMD 10 grep-F substring-match semantics** — correctly distinguished. The EDIT 2 line ends `outputs.token }}` (close-braces); the EDIT 3 line ends `outputs.token || github.token }}` (pipe-pipe-token-close-braces). The grep -F substring `token: ${{ steps.scp-app-token.outputs.token }}` does NOT contiguously match the EDIT 3 line.

**Semantic ordering verify_commands (CMD 18 + 19)** — sufficient as sec-relevant probes. Each anchor is unique in the file; composite of CMD 9 (count=1), CMD 10 (count=1), CMD 16 (if-guard), CMD 17 (token-step before runtime), CMD 18 (EDIT 2 ordering), CMD 19 (EDIT 3 ordering) provides adequate coverage of token-placement correctness.

## Convergence signal rationale

R-FIXPOINT-MET. All four R1 SEC findings verified closed. Zero new sec findings at R2. The v0.2 amendments are well-scoped; none introduce new threat surface, new trust boundary, or new ambiguity. Federation-primitive invariants 1-5 fully preserved. The dispatch JSON v0.2 is ready for Codex fire pending operator-attended authorisation per the continuation prompt standdown.
