# TF-PIM-001 Wave D dispatch JSON — sec lens R1

**Dispatched:** 2026-05-21 PM (Wave D dispatch authoring autonomous-scope per operator authorisation 2026-05-21 Reading A)
**Agent type:** Plan (read-only by design — DO-NOT-EDIT mandate enforced at tool-availability layer per `feedback_subagent_review_only_scope_must_be_enforced`)
**Model:** Sonnet
**Worktree isolation:** yes (per estate auth-surface-plan-review default)
**Lens domain:** threat-model + auth-surface + trust-rooting + supply-chain
**Artefact under review:** `docs/governance/work-packages/tf-pim-001-wave-d-policy-check-yaml-token-exchange.json` (v0.1)

---

**Verdict:** ACCEPT-WITH-AMENDMENT
**Convergence signal:** ITERATE-EXPECTED
**Findings count:** 4 total (0 BLOCKING + 1 MAJ + 1 MIN + 2 NIT)

---

## Findings

### SEC-MAJ-001

**Type:** MAJ
**Title:** Wave E env-var coupling constraint overridden without inline derogation documentation
**Where:** dispatch JSON `instruction` field — final invariants block; "DO NOT add tests, scaffolding, env-var injection for selftest harness (that is Wave E, a separate dispatch)"
**Finding:** The impl WP plan-doc §4 Wave E contains an explicit binding constraint: "the `SCP_TEST_SIMULATE_APP_TOKEN_FAILURE` env-var check injected into `policy-check.yml`'s token-exchange step (Wave E Actions step 2) **MUST land in the same PR as Wave D** — both Wave D and Wave E modify `policy-check.yml`; separate PRs would conflict on that file." The dispatch JSON's instruction overrides this with "DO NOT add tests, scaffolding, env-var injection for selftest harness (that is Wave E, a separate dispatch)." The continuation prompt at `docs/continuation-prompts/2026-05-21-tf-pim-001-wave-d-dispatch-resume.md` similarly characterises Wave E as a separate dispatch, which appears to be an operator decision to sequence Wave E post-Wave D merge rather than in parallel — resolving the file-conflict risk that motivated the original "MUST land in same PR" language. However, this derogation is not documented inline in the dispatch JSON itself: the `instruction` says DO NOT but gives no rationale, the `notes` field does not reference the plan-doc constraint or explain why sequential sequencing makes the coupling unnecessary, and no `spec_paths` entry covers Wave E. A reviewer arriving at the dispatch JSON cold cannot determine whether the derogation is intentional (operator-authorized sequential sequencing) or an oversight.

The security dimension: without the `SCP_TEST_SIMULATE_APP_TOKEN_FAILURE` env-var injection in the Wave D PR, there is no CI-verified evidence that the workflow emits `SCP-E001` correctly when the App token-exchange step fails. The `|| github.token` fallback is fail-closed in the cross-repo failure case (caller `GITHUB_TOKEN` cannot read the private SCP repo, checkout fails with permission-denied rather than silently succeeding) so there is no live auth bypass. But the plan-doc §7.2 risk mitigation explicitly cites "Wave E selftest harness coverage exercises the token-exchange failure mode **before Wave D's PR merges**" as a Wave D blast-radius control. Removing that control without documentation leaves a gap in the pre-merge evidence record.

**Why it matters:** A plan-doc constraint marked MUST is being overridden without an inline acknowledgement. The sec-lens concern is not a live vulnerability but a gap in the verified-pre-merge evidence chain. If Wave E is delayed post-Wave D merge (e.g., context-window pressure, new wave prioritisation), the window of un-tested error-path behavior is open during Wave F dogfood and Wave G PIM canary runs. The failure mode in that window is loud (checkout fails, CI fails) not silent — but the SCP-E001 annotation verification is the evidence that the error surface is wired as designed.

**Suggested closure:** Add a note to the dispatch JSON `notes` field (or a comment in the `instruction`) explicitly acknowledging the plan-doc §4 Wave E "MUST land in same PR" constraint and documenting the operator-authorised resolution: "Wave E env-var injection is EXCLUDED from this dispatch by operator decision; Wave E fires as a sequential follow-on dispatch AFTER Wave D merges (not in parallel) — sequential sequencing eliminates the file-conflict risk that motivated the plan-doc's same-PR coupling requirement; Wave E's test coverage is therefore a post-merge gap for the period between Wave D merge and Wave E merge." This is a documentation-only amendment to the dispatch JSON that closes the derogation-undocumented gap without altering the scope of the Codex dispatch.

---

### SEC-MIN-001

**Type:** MIN
**Title:** No verify_command confirms the `if: github.action_ref != ''` guard on the new token-exchange step
**Where:** dispatch JSON `verify_commands` array — none of the 19 entries
**Finding:** The D-050 ADR §2 "Token acquisition flow" states: "The token-exchange step is gated by `if: github.action_ref != ''` — when the workflow is invoked LOCALLY (SCP-self dogfood; `github.action_ref` is empty), the token-exchange step skips." The dispatch JSON's `instruction` specifies this guard explicitly in the EDIT 1 YAML body: `if: github.action_ref != ''`. The instruction also documents the invariant: under SCP-self dogfood, both the token-exchange step AND the `.scp-runtime` checkout step skip together via the shared if-guard. This guard is architecturally critical: if Codex omits it from the step, the token-exchange action runs unconditionally on every policy-check invocation including SCP-self runs, making an unnecessary live call to the GitHub App API at every SCP-self CI run.

None of the 19 verify_commands check for the if-guard. A command such as `grep -F "if: github.action_ref != ''" .github/workflows/policy-check.yml` would directly verify the guard is present. Alternatively, a contextual check near the `id: scp-app-token` line would confirm both the step ID and the guard appear in close proximity.

The security dimension is secondary (unconditional token-exchange is unnecessary but not a bypass), but the behavioral regression is real: SCP-self runs would create superfluous App API calls and the D-050-documented SCP-self invariant (token-exchange skips under SCP-self) would be silently violated without any verify_command catching it.

**Why it matters:** The if-guard is a D-050-documented invariant (§2 "Token acquisition flow"), a plan-doc §4 Wave D Action step 6 invariant ("SCP-self dogfood case: token-exchange step skips per the `if:` guard"), and an explicit EDIT 1 requirement. Its absence from the verify_commands is a gap given the Tier 2 dispatch rigor standard.

**Suggested closure:** Add one verify_command — a proximity check that asserts the `if: github.action_ref != ''` guard appears within ±3 lines of the `id: scp-app-token` line: `IDLINE=$(grep -nF 'id: scp-app-token' .github/workflows/policy-check.yml | head -1 | cut -d: -f1); awk -v s=$((IDLINE-3)) -v e=$((IDLINE+3)) 'NR>=s && NR<=e' .github/workflows/policy-check.yml | grep -F "if: github.action_ref != ''"`.

---

### SEC-NIT-001

**Type:** NIT
**Title:** Sigstore attestation evaluation status for `actions/create-github-app-token` not documented in dispatch JSON
**Where:** dispatch JSON `notes` field
**Finding:** ADOPT-001 §12.7.13 states: "Sigstore attestation status. Evaluated at Wave D dispatch time (same TF-007 parallel posture as OPA / Conftest / Regal — if the chosen action publishes Sigstore attestations, `gh attestation verify` may ratchet up in a future SCP release)." The dispatch JSON `notes` field documents SHA verification (`commit-SHA verified via gh api repos/actions/create-github-app-token/git/refs/tags/v3.2.0`) but does not document the result of the Sigstore attestation evaluation. The PRIMARY action (`actions/create-github-app-token`) is a GitHub first-party action, so its Sigstore posture is relevant. Similarly, the FALLBACK action `tibdex/github-app-token@3beb63f4bd073e61482598c45c71c1019b59b73a # v2.1.0` has its commit-SHA noted but no supply-chain posture evaluation documented (though the FALLBACK is not engaged, so §12.7.13's "Fallback documentation requirement" items (a)-(d) technically apply only if the fallback is engaged).

**Why it matters:** §12.7.13 makes the Sigstore evaluation a Wave D dispatch time obligation. A reviewer auditing this dispatch JSON against §12.7.13 cannot determine whether the evaluation was performed and what it found. For TF-007 tracking purposes, the evaluation result (even if "attestations not published by this action") should be on-record.

**Suggested closure:** Append one sentence to the `notes` field: "Sigstore attestation status for `actions/create-github-app-token` v3.2.0 evaluated at dispatch authoring: GitHub first-party action — attestations checked via `gh attestation verify` / GitHub's native attestation API; [result: 'not published' / 'verified' — operator to confirm and fill]; TF-007 parallel posture unchanged."

---

### SEC-NIT-002

**Type:** NIT
**Title:** VC[18] diff budget lower bound (8) is below the actual minimum addline count (10)
**Where:** dispatch JSON `verify_commands[18]` — `test "$ADDED" -ge 8 && test "$ADDED" -le 30`
**Finding:** The dispatch instruction states the diff is bounded to "(a) one new step (8 YAML lines), (b) two new `token:` lines on existing steps" — a minimum of 10 added lines. VC[18]'s lower bound of 8 would pass even if Codex inserted only the new token-exchange step (8 lines) without adding the two `token:` lines (EDIT 2 + EDIT 3). In isolation this creates a gap where a partial implementation passes the budget check. The gap is compensated by VC[8] (`test "$(grep -cF 'token: ${{ steps.scp-app-token.outputs.token || github.token }}' ...)" = 2`), which would catch the missing `token:` lines. The combined coverage of VC[8] + VC[18] is adequate; VC[18] alone is weakly specified.

**Why it matters:** Weak budget-lower-bound is not exploitable given VC[8]'s compensating check, but it represents a documentation precision gap. The lower bound should match the minimum expected implementation. (Note: pragmatist lens PRAG-MIN-001 separately observes the EDIT 1 YAML block is actually 9 lines not 8 — so true minimum is 11, not 10. Adopt pragmatist's tighter bound.)

**Suggested closure:** Change VC[18]'s lower bound from `8` to `11` per pragmatist PRAG-MIN-001 closure (accounting for EDIT 1's actual 9-line step body + 2 EDIT 2/3 token lines = 11 minimum).

---

## Federation-primitive invariants 1-5 disposition

**Invariant 1 — Adopter token does not leave adopter context.** Preserved. The dispatch instructs Codex to touch only the two SCP-repo cross-repo checkout steps (EDITS 2 + 3) with a `token:` parameter; the first checkout (line 92, "Checkout caller repository") is explicitly held unchanged. The `persist-credentials: false` count invariant (3 occurrences, verified by VC[9]) closes the persisted-credential path. The `|| github.token` fallback on EDIT 3 supplies the caller's `GITHUB_TOKEN` only as a fallback for the SCP-self case (where the caller IS SCP) or as a fail-closed fallback under cross-repo token-exchange failure (caller `GITHUB_TOKEN` cannot read the private SCP repo). The App token is passed to a SHA-pinned action (`actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd`) only — no SCP-controlled scripts receive it directly.

**Invariant 2 — SCP-controlled workflow code never sees adopter named secrets.** Preserved. The `workflow_call:` trigger has no `secrets:` block (current pre-state verified; dispatch invariant 2 explicitly prohibits adding one; VC[11] enforces `! grep -qE 'secrets:[[:space:]]*inherit'`). The App private key (`${{ secrets.SCP_FEDERATION_APP_PRIVATE_KEY }}`) resolves against the SCP repo's own secrets in the reusable-workflow context — not from the caller. D-050 §2 and §3 confirm this is the architecture-ratified mechanism. The dispatch JSON instruction paragraph on invariant 2 correctly documents the resolution context. This is the primary §12.7.10 critical property and the dispatch preserves it accurately.

**Invariant 3 — Trust roots in tag-protected SHA pins.** Preserved with the same nuance noted in the path-ratification sec lens. The new action `actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1` is a 40-character commit SHA (verified 40 chars; no tag ref or branch ref; `# v3.2.0` comment for human readability only). The SHA-pin is verified via `gh api repos/actions/create-github-app-token/git/refs/tags/v3.2.0` per the notes field. CODEOWNERS `.github/** @jrnb2024` (confirmed in the CODEOWNERS file) gates future SHA-pin updates under single-operator mode. The FALLBACK SHA `3beb63f4bd073e61482598c45c71c1019b59b73a` (40 chars; annotated-tag dereference per notes) is documented but not engaged. The existing three checkout pins remain at `de0fac2e4500dabe0009e67214ff5f5447ce83dd` (verified by VC[10]).

**Invariant 4 — Policy bundle integrity is verifiable.** Preserved and unaffected. The dispatch scope boundary is precisely `[".github/workflows/policy-check.yml"]` only; `scripts/scp-policy-check.lock`, `scripts/.tool-versions`, and all policy bundle files are untouched. The diff-scope verify_command (VC[17]) confirms only `policy-check.yml` changes. No new lockfile entries or SHA256 verification steps are added or removed.

**Invariant 5 — Annotation surface is fixed.** Preserved. The dispatch instruction's invariant 5 explicitly states "No new env vars, no new jobs, no other step renames." The new token-exchange step is an internal implementation step, not an annotation-emitting step. No new `SCP-EXXX` error codes are introduced by the dispatch. The `SCP-E001` annotation for token-exchange failure would be emitted by the Wave E fixture injection (not present in this dispatch), so the annotation surface contract is unchanged by this dispatch alone.

---

## Convergence signal rationale

The dispatch JSON correctly encodes the Wave D scope. The three critical sec properties — §12.7.10 invariant preservation (no `secrets: inherit`, App key in SCP-repo secrets), `persist-credentials: false` on all three checkout sites, and App token scoped to `jrnb2024/standards-control-plane-` via `owner` + `repositories` inputs — are each accurately specified and each has a corresponding verify_command. The `|| github.token` fallback semantics are documented in detail with correct analysis for both the SCP-self and cross-repo-failure cases; the fallback is fail-closed in the security-relevant scenario (cross-repo with token-exchange failure: caller `GITHUB_TOKEN` cannot read the private SCP repo). The SHA pin is a 40-character commit SHA; the PRIMARY action is GitHub first-party; CODEOWNERS coverage on `.github/**` gates future updates.

The two non-NIT findings are remediable inline: SEC-MAJ-001 requires a documentation note in the `notes` field (or `instruction`) acknowledging the Wave E derogation and its rationale (sequential sequencing eliminates the file-conflict risk); SEC-MIN-001 requires one additional verify_command entry. Neither requires structural changes to the EDIT 1/2/3 instruction content or to the scope boundary. Upon closure of SEC-MAJ-001 + SEC-MIN-001 (and optionally the two NITs), the dispatch JSON should be fit for R-fixpoint at R2 with DIMINISHING-RETURNS signal likely achievable by a single focused amendment pass.
