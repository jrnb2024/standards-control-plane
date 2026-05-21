# TF-PIM-001 Wave D dispatch JSON — arch-skeptic lens R1

**Dispatched:** 2026-05-21 PM (Wave D dispatch authoring autonomous-scope per operator authorisation 2026-05-21 Reading A)
**Agent type:** Plan (read-only by design — DO-NOT-EDIT mandate enforced at tool-availability layer)
**Model:** Sonnet
**Worktree isolation:** yes (per estate auth-surface-plan-review default)
**Lens domain:** architectural fit + reversibility + failure-surface + plan-doc fidelity
**Artefact under review:** `docs/governance/work-packages/tf-pim-001-wave-d-policy-check-yaml-token-exchange.json` (v0.1)

---

**Verdict:** ACCEPT-WITH-AMENDMENT
**Convergence signal:** ITERATE-EXPECTED
**Findings count:** 7 total (0 BLOCKING + 2 MAJ + 3 MIN + 2 NIT)

---

## Findings

### ARCH-MAJ-001

**Type:** MAJ
**Title:** `|| github.token` fallback on EDIT 2 is architecturally unsound — the if-guarded step should not have a fallback path that makes it appear safe to receive an empty token
**Where:** Dispatch JSON `instruction`, EDIT 2 section — `token: ${{ steps.scp-app-token.outputs.token || github.token }}`; also the rationale paragraph for EDIT 2
**Finding:** The dispatch JSON's rationale for using `|| github.token` on EDIT 2 (the `.scp-runtime` checkout) states that "for EDIT 2 the if-guard means the step itself also skips under SCP-self — so the fallback is harmless / unused." This reasoning is architecturally incomplete. The dispatch JSON's own instruction for EDIT 3 explains clearly why the fallback is critical there (the `if: always()` guard means the step runs under SCP-self). But for EDIT 2, the instruction presents the fallback as "harmless / unused" and simultaneously justifies it as keeping the two sites "symmetric and pattern-matchable." The architectural problem is this: the symmetry argument introduces the fallback on EDIT 2 without a bounded proof that it is truly unreachable. GitHub Actions expression evaluation for step outputs from skipped steps evaluates to an empty string — which means in any future condition where `if: github.action_ref != ''` evaluates differently (e.g., a GitHub Actions engine change, a self-hosted runner with a non-empty synthetic `action_ref`, or a future workflow restructure that removes the if-guard), EDIT 2's fallback would silently use `github.token` (the default credential) rather than surfacing an explicit failure. The plan-doc verbatim (lines 188-198) specifies `token: ${{ steps.scp-app-token.outputs.token }}` — no fallback — which is architecturally correct for EDIT 2: if the step runs (cross-repo path only), the App token MUST be present; if it is absent, that is a genuine misconfiguration, and the correct failure mode is an authentication error on `actions/checkout` that maps to SCP-E001, not a silent fallback to `github.token` that would produce a misleading success (the `github.token` from the adopter cannot read the private SCP repo, so the checkout would fail anyway, but after a potentially confusing "wrong token" authentication attempt rather than a clear "no App token obtained" failure). More specifically: EDIT 2's `if: github.action_ref != ''` guard and the token-exchange step's identical guard are co-variant — they are both skipped or both run together. The symmetry argument for adding the fallback to EDIT 2 is that Codex will be confused by the asymmetry. But the correct encoding is to have NO fallback on EDIT 2 (since if it runs, the App token MUST be present) and a critical fallback on EDIT 3 (since it always runs). The dispatch JSON as authored breaks this logical separation and makes the two sites look identical when they have meaningfully different semantics.

**Why it matters:** If a future operator or review agent looks at the two `token:` lines and sees identical expressions, they may assume both have the same semantics. Only EDIT 3 has a critical fallback. Encoding EDIT 2 differently (`token: ${{ steps.scp-app-token.outputs.token }}` — verbatim plan-doc) makes the semantics legible: EDIT 2 asserts "the App token must exist here"; EDIT 3 states "use App token if available, else GITHUB_TOKEN." The dispatch JSON's current encoding trades legibility for surface symmetry. The MAJ severity is warranted because this affects what Codex will produce, and the produced code's semantics are subtly wrong (the fallback path on EDIT 2 is unreachable but teaches an incorrect pattern that could propagate to future adopters reading the workflow).

**Suggested closure:** Change EDIT 2's `token:` to `token: ${{ steps.scp-app-token.outputs.token }}` (verbatim plan-doc). Update the EDIT 2 rationale to explain the INTENTIONAL asymmetry: EDIT 2 asserts App-token presence (if this step runs, the exchange step also ran); EDIT 3 uses the fallback because `if: always()` decouples it from the exchange step's guard. Add an inline comment in the EDIT 2 instruction noting why the two sites differ. The SCP-self breakage risk is zero (EDIT 2 is itself if-guarded by the same `github.action_ref != ''` condition — if that condition is false, the step does not run at all). Simultaneously, update the EDIT 3 rationale to state explicitly: "EDIT 3 is the ONLY site where the `|| github.token` fallback is critical."

---

### ARCH-MAJ-002

**Type:** MAJ
**Title:** SHA pin `bcd2ba49218906704ab6c1aa796996da409d3eb1` cited as `v3.2.0` (2026-05-12) — not verifiable from repo state; no provenance evidence embedded in dispatch JSON
**Where:** Dispatch JSON `instruction` EDIT 1 YAML block; also in `verify_commands` item 4; also in `notes` field
**Finding:** The dispatch JSON asserts `bcd2ba49218906704ab6c1aa796996da409d3eb1` is `actions/create-github-app-token` v3.2.0 released 2026-05-12, verified via `gh api repos/actions/create-github-app-token/git/refs/tags/v3.2.0`. This is a point-in-time claim made at dispatch-JSON authoring time. The dispatch JSON contains NO embedded evidence of this resolution — no annotated-tag dereference output, no `git ls-remote` result, no inline citation of the SHA verification step that was performed. When Codex (or an R-cycle reviewer) receives the dispatch JSON, there is no way to independently confirm the SHA-to-version mapping from the JSON alone. Arch-skeptically: the plan-doc's Wave D Action step 1 specifies that the SHA-pin is the action's 40-char commit SHA from a verified tag dereference. The `notes` field cites `gh api repos/actions/create-github-app-token/git/refs/tags/v3.2.0` as the verification method but does not show the result. If the SHA is wrong (e.g., it is the tag object SHA not the commit SHA, or a typo), the workflow step will fail at runtime with a cryptic `uses:` resolution error. Furthermore, the `notes` field documents the FALLBACK `tibdex/github-app-token@3beb63f4bd073e61482598c45c71c1019b59b73a # v2.1.0` but does not clarify whether this was verified at dispatch-authoring time or is a pre-existing stub from the plan-doc (plan-doc §4 Action step 1 says the fallback SHA comes from "annotated-tag dereference" but the plan-doc does not embed the result either). The dispatch JSON's current state trusts the SHA claims without baking in any verifiability artefact.

**Why it matters:** This is a Tier 2 kernel-dangerous dispatch. If Codex inserts a wrong SHA, the workflow breaks for every adopter on the next PR. The verify_commands check that the exact SHA string is present in the file (`grep -F 'uses: actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1 # v3.2.0'`) — but this only verifies that Codex inserted the exact string from the dispatch JSON, not that the string is correct. The correctness of the SHA must be established before the dispatch JSON fires, and the evidence must be in the JSON so R-cycle reviewers can validate it.

**Suggested closure:** Embed the resolution evidence inline in the `notes` field as a pre-verified assertion: include the raw `gh api repos/actions/create-github-app-token/git/refs/tags/v3.2.0 --jq '.'` output (object type=commit + commit SHA) plus the raw `gh api repos/tibdex/github-app-token/git/refs/tags/v2.1.0 --jq '.'` output (annotated-tag-object + dereferenced commit SHA from `gh api repos/tibdex/github-app-token/git/tags/<tag-SHA>`). This creates an auditable trail in the dispatch JSON itself, independent of network access at verify time.

---

### ARCH-MIN-001

**Type:** MIN
**Title:** EDIT 3 awk-based context probe is fragile to Codex edit ordering if Codex inserts EDIT 1 before running verify
**Where:** Dispatch JSON `verify_commands` items at positions 16 and 17 (the `awk -v start=$((TOKEN_LINE - 8))` probes)
**Finding:** The two awk-based verify_commands resolve `TOKEN_LINE` by finding the first and last occurrence of `token:` lines, then check `repository: ${{ github.action_repository }}` is within ±8/+4 lines of the first token line and `path: _scp-workflow` within ±8/+4 of the last. The window `start=$((TOKEN_LINE - 8))` and `end=$((TOKEN_LINE + 4))` is a tight 13-line window. The actual expected layout of the `.scp-runtime` checkout block (EDIT 2) is: `name:` → `if:` (with multi-line comment above) → `uses:` → `with:` → `repository:` → `ref:` → `token:` (NEW) → `path:` → `fetch-depth:` → `persist-credentials:`. Under reasonable insertion the `repository:` line is 2 lines above the new `token:` line (within window). However, if the awk window is calibrated marginally and Codex preserves the multi-line comment block above the step's `with:` section, edge cases could miss. The L28 anchored-awk discipline accepts this fragility, but the window selection is borderline for the actual step shape.

**Why it matters:** If the awk probe misfires due to line-count drift (comments preserved, extra blank lines), the verify_commands stage flags a false failure, causing Codex to re-attempt the edit in a way that may introduce regressions. Given the Tier 2 kernel-dangerous classification, a verify_command false-failure that drives Codex to reattempt is more dangerous than no probe.

**Suggested closure:** Replace the two awk-window probes with a two-phase grep ordering check: first locate the `.scp-runtime` checkout step start line and the `_scp-workflow` checkout step start line; then verify (a) the `token:` line for EDIT 2 falls between the `repository: ${{ github.action_repository }}` line and the `path: .scp-runtime` line, AND (b) the `token:` line for EDIT 3 falls between the `repository: jrnb2024/standards-control-plane-` line and the `path: _scp-workflow` line. This is more semantically anchored than a fixed-window awk and resilient to comment-block preservation.

---

### ARCH-MIN-002

**Type:** MIN
**Title:** Wave E coupling constraint not asserted in dispatch JSON scope_boundary or verify_commands
**Where:** Dispatch JSON `scope_boundary` field; `instruction` ("Touch no other file") section
**Finding:** The plan-doc §4 Wave E specifies (as closed-finding ARCH-MIN-001): "the `SCP_TEST_SIMULATE_APP_TOKEN_FAILURE` env-var check injected into `policy-check.yml`'s token-exchange step (Wave E Actions step 2) **MUST land in the same PR as Wave D**." The dispatch JSON's instruction explicitly states "DO NOT add tests, scaffolding, env-var injection for selftest harness (that is Wave E, a separate dispatch)." This is the correct scope-tightening, but the dispatch JSON does not document the coupling constraint for the operator who reads it: namely, that Wave D's Tier 2 fire must be coordinated with the Wave E dispatch (which also modifies `policy-check.yml`) and that both must land in the same PR. Without this note, an operator who fires the Wave D dispatch in isolation, gets a green PR, and merges it — will then face a `policy-check.yml` conflict when Wave E fires. The dispatch JSON currently defers Wave E entirely with no coordination note, which means the operator has to recall the coupling from the plan-doc §4 rather than having it surfaced inline. (Overlaps with sec lens SEC-MAJ-001 — single fix-point closes both.)

**Why it matters:** Wave E touching the same file is a hard constraint. A merged Wave D without Wave E's env-var addition is correct per the dispatch JSON's own scope, but the resulting file state is incomplete per the plan-doc's Wave D + Wave E coupling mandate. An operator who does not also hold Wave E's dispatch authoring state in working memory could merge Wave D, then encounter a merge conflict on Wave E, requiring a Wave D v0.2 re-edit.

**Suggested closure:** Add a `notes` paragraph: "OPERATOR COORDINATION REQUIRED: Wave E (selftest harness fixture) MUST be authored and committed into THIS SAME PR before merge. Wave E adds the `SCP_TEST_SIMULATE_APP_TOKEN_FAILURE` env-var check to the token-exchange step in `policy-check.yml` (plan-doc §4 Wave E Actions step 2 + ARCH-MIN-001 R1 closure mandate). Wave E's Tier 2 dispatch fires after Wave D is authored; both changesets land in the same PR branch. Do NOT merge the Wave D change alone — this would create a merge conflict for Wave E."

---

### ARCH-MIN-003

**Type:** MIN
**Title:** Diff-bound check uses `git fetch origin main --depth=1` which is fragile in Codex execution environments without guaranteed remote access
**Where:** Dispatch JSON `verify_commands`, items 18 and 19 (the `git fetch origin main --depth=1` commands)
**Finding:** Two verify_commands require fetching `origin/main` from GitHub to compare the changed file set and added line count. In a Codex execution environment, `git fetch` requires (a) network access to the GitHub remote, (b) `origin` to be configured to the correct remote URL, and (c) sufficient GitHub API / git authentication for the operation. These conditions may not hold in all Codex execution contexts. The verify_command uses `>/dev/null 2>&1` to suppress errors, meaning a fetch failure silently passes the subsequent `git diff origin/main HEAD` command — which then either compares against a stale local `origin/main` (if the ref is cached) or fails entirely. (Subsumed by pragmatist PRAG-MAJ-001 closure: replace `git diff origin/main HEAD` with `git diff HEAD` (working-tree-vs-last-commit, no remote required).)

**Why it matters:** The scope-check verify_commands are the primary defence against Codex scope-breach. If they silently pass due to fetch failure, a scope-breach would go undetected at verify time.

**Suggested closure:** Closed by PRAG-MAJ-001 fix.

---

### ARCH-NIT-001

**Type:** NIT
**Title:** Permissions block analysis missing from dispatch JSON — `actions/create-github-app-token` does NOT require additional workflow-level permissions; should be explicitly asserted
**Where:** Dispatch JSON `instruction` invariants section; `notes` field
**Finding:** The dispatch JSON's invariants do not explicitly assert that the workflow's existing `permissions` block (`contents: read`, `statuses: write`, lines 56-58 of `policy-check.yml`) is SUFFICIENT for the App-token-exchange step and requires NO amendment. This is correct — `actions/create-github-app-token` reads SCP-repo secrets via GitHub Actions' built-in secret resolution mechanism (no additional permission scope needed) — but the absence of an explicit assertion creates a gap in the dispatch JSON's self-documentation. The existing WP-SCP-023 023B comment in the workflow's `permissions` block explicitly calls out that `id-token: write` is NOT granted workflow-wide for OIDC safety reasons. Adding a token-exchange step without confirming permissions compatibility could look to a future reviewer like the permissions block was not checked.

**Why it matters:** NIT-level — the invariant holds without the assertion. But for a Tier 2 kernel-dangerous dispatch, the permissions block compatibility should be stated, especially given the 023B comment explicitly guards against `id-token: write` workflow-level grants.

**Suggested closure:** Add to the invariants section: "**No permissions block amendment required.** The workflow-level permissions (`contents: read`, `statuses: write`) are sufficient for the token-exchange step. `actions/create-github-app-token` resolves `SCP_FEDERATION_APP_ID` + `SCP_FEDERATION_APP_PRIVATE_KEY` from GitHub Actions' built-in secret context; it does NOT require `id-token: write` (which is OIDC, not App-credential). The existing WP-SCP-023 023B `id-token: write` exclusion is fully preserved."

---

### ARCH-NIT-002

**Type:** NIT
**Title:** `model: "gpt-5.4"` field — non-estate-standard model name may be ignored or mis-routed by the Codex dispatch harness
**Where:** Dispatch JSON top-level `model` field: `"model": "gpt-5.4"`
**Finding:** The lens flagged `"gpt-5.4"` as not an Anthropic model ID. **FALSE POSITIVE — closed at synthesis.** The canonical schema `/Users/amplience/Projects/acc/schemas/codex_work_package.schema.json` line 49 enumerates valid Codex CLI model overrides: `"Available: gpt-5.4, gpt-5.4-mini, gpt-5.3-codex, gpt-5.3-codex-spark, gpt-5.2."` `gpt-5.4` IS the canonical Codex CLI model name for Tier 2 kernel-dangerous work; it is routed through the Codex CLI, not the Anthropic API. The lens confused the Codex CLI model namespace with the Anthropic namespace.

**Why it matters:** N/A — false positive.

**Suggested closure:** No action. Closure note in synthesis.

---

## Plan-doc fidelity disposition

The dispatch JSON is substantially faithful to impl WP plan-doc §4 Wave D. The verbatim YAML block at plan-doc lines 188-198 is reproduced exactly in EDIT 1 (step body, `id:`, `if:`, `uses:` with SHA comment, and all `with:` inputs). EDIT 2 and EDIT 3's `token:` parameter additions correspond to plan-doc Action steps 3 and 4. The `if: github.action_ref != ''` guard semantics described in plan-doc Action step 6 are correctly encoded in both EDIT 1 and EDIT 2, and the dispatch JSON's EDIT 3 rationale correctly explains why the `|| github.token` fallback is critical for the `if: always()` schema-lookup checkout but not for the if-guarded `.scp-runtime` checkout. However, the key divergence from plan-doc verbatim is the `|| github.token` fallback on EDIT 2: the plan-doc reads `token: ${{ steps.scp-app-token.outputs.token }}` for both sites (Action steps 3 and 4 are symmetric in the plan-doc), while the dispatch JSON adds the fallback to both. For EDIT 3 this is a well-justified refinement — the plan-doc Action step 6 rationale supports it and the dispatch JSON documents the SCP-self correctness argument clearly. For EDIT 2 the fallback is architecturally incorrect: the `.scp-runtime` checkout step is co-gated with the token-exchange step by the same `if:` guard, so when EDIT 2 runs, the App token must be present; the fallback serves no valid purpose and teaches an incorrect pattern. This is the basis for ARCH-MAJ-001. The divergence on EDIT 3 is justified and should be reflected in the plan-doc as a post-R-fixpoint hygiene amendment. The divergence on EDIT 2 should be resolved by bringing the dispatch JSON back to the plan-doc verbatim (`token: ${{ steps.scp-app-token.outputs.token }}` — no fallback).

## Reversibility disposition

The dispatch JSON's encoding preserves the reversibility profile established in D-050 §Reversal mechanism and plan-doc §7.5a. The change is confined to a single file; the rollback path is a single PR revert (`git revert <wave-d-merge-commit-SHA>`); SCP-self continues working post-revert because the token-exchange step and the `.scp-runtime` checkout share the same `if: github.action_ref != ''` guard (both skip under self-dogfood). No new cross-file dependencies are introduced that would impede rollback — the dispatch JSON's scope_boundary is correctly locked to `.github/workflows/policy-check.yml` only. The rollback cost estimated in D-050 as `<1 day operator-attended` is not impeded by the dispatch JSON's encoding. The ARCH-MAJ-001 finding (asymmetric fallback) does not affect reversibility because the problematic `|| github.token` on EDIT 2 would silently degrade (the fallback token cannot read the private SCP repo anyway, so the step would fail with an authentication error rather than silently succeeding on rollback), but a revert removes it cleanly.

## Convergence signal rationale

ITERATE-EXPECTED is the correct signal: two MAJ findings must close before Codex dispatch fires, and both are addressable in a single v0.2 pass of the dispatch JSON. ARCH-MAJ-001 (EDIT 2 token expression) requires a one-line change to the instruction + a rationale paragraph update. ARCH-MAJ-002 (SHA provenance) requires either an online verify_command or an embedded pre-verified assertion in `notes`. Neither requires plan-doc re-authoring or a new R-cycle on the plan-doc itself. The three MIN findings (ARCH-MIN-001 through ARCH-MIN-003) are all cheap inline amendments. After a v0.2 fold, a focused R2 on the two MAJ closure points + the updated EDIT 2 expression is expected to reach R-FIXPOINT-MET. There is no cure-worse signal and no scope-split candidate — the dispatch JSON's structure is sound; the findings are precision issues, not architectural rethink.
