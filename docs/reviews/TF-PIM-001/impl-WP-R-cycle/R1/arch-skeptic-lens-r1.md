# TF-PIM-001 impl WP — arch-skeptic lens R1 review (v0.2)

**Dispatched:** 2026-05-21 PM against impl WP plan-doc v0.2 at `ef5312e`
**Agent type:** Plan (read-only; DO-NOT-EDIT mandate)
**Model:** Sonnet
**Worktree isolation:** yes
**Lens precedent:** reuse pattern from `docs/reviews/TF-PIM-001/shortlist-A-C-D/arch-skeptic-lens-r1.md`

---

## Lens: arch-skeptic — TF-PIM-001 impl WP v0.2 R1 review

### Verdict
ACCEPT-WITH-AMENDMENT

### Summary

The v0.2 wave structure is architecturally coherent and the sequencing is largely sound. The A→B→C→D→E→F→G→H chain reflects the correct dependency ordering: App authoring before any code change (App credential must exist before Wave D can acquire it); ADR before implementation (Wave B documents the architectural commitment before Wave D executes it); ADOPT-001 docs before the PR that tests against them (Wave C before Wave D merge); selftest before external exposure (Wave E before Wave G); SCP-self dogfood as the firewall before external-adopter exposure (Wave F before Wave G). v0.2 is measurably stronger than v0.1: the `.pem` discipline ceremony, sharpened Wave D parallelism boundary, §7.5a rollback tree, and §7.6 Wave G decision tree are all load-bearing additions. All 10 TF-PIM-001-{SEC,ARCH}-* items from this reviewer's prior evidence file are mapped to waves or explicitly TF-carried with rationale. The five ACs are verifiable and close-tight.

Two findings require pre-merge amendment. First, §7.5a Wave D rollback step 3's invocation shape is wrong: it references a `policy-check / scp/policy-check` context toggle on SCP main, but `enable-required-check.sh --restore` per D-047/D-048 requires a captured pre-state JSON from a prior invocation log entry; no such log entry exists for SCP-self's own branch protection (the dogfood gate was set up via WP-SCP-020 020D2, not via `enable-required-check.sh`). The rollback step names the script and the capability but the invocation parameters are not executable as written. Second, the §7.6 Wave G Branch 4 wording "all 12 policy-check steps green = workflow executed successfully, NOT no findings" creates an ambiguity that could allow a real RULE denial to be misrouted as "federation primitive working as designed" when the test PR was not intentionally constructed to be denial-free. AC #1 says "all 12 policy-check steps green" but the Wave G verification test PR (a "noop README touch") should be denial-free by design — the plan does not explicitly require that the canary test PR be designed to avoid triggering rule denials.

### Findings

**ARCH-MAJ-001 — §7.5a Wave D rollback step 3: `enable-required-check.sh --restore` requires a pre-state JSON that does not exist for SCP-self**

§7.5a step 3 states: "operator-attended temporary branch-protection toggle. `policy-check / scp/policy-check` removed from SCP main's required contexts ONLY IF Wave D regression also breaks SCP-self dogfood (matches PIM's current state)." The parenthetical implies invoking `enable-required-check.sh --restore` against the SCP repo. But D-047 specifies that `--restore` consumes a pre-state JSON captured in `docs/reviews/WP-SCP-020/branch-protection-log.md` from a prior `enable-required-check.sh` forward-mode invocation. SCP-self's branch protection was installed via WP-SCP-020 020D2, not via the `enable-required-check.sh` forward-mode path; there is no invocation-log entry for SCP-self with a captured before-state JSON. The rollback step is therefore not executable as written using the documented tool: the operator would need to issue a direct `gh api PATCH` or use the `--restore` flag with a manually constructed before-state JSON, neither of which is documented. The phrase "matches PIM's current state" is architecturally inapt — PIM's relaxation was an operator-attended manual API change (not a `--restore` operation).

**Amendment required:** Replace step 3 with an explicit invocation path acknowledging that `enable-required-check.sh --restore` is NOT available for SCP-self's branch protection. Provide the `gh api PATCH` shape required for the manual toggle.

**ARCH-MAJ-002 — §7.6 Wave G Branch 4 + AC #1 ambiguity: "all 12 steps green" conflates infrastructure health with denial-free policy evaluation**

AC #1 states "all 12 policy-check steps green" with the Wave G test PR being "a noop README touch." Branch 4 of §7.6 then asserts that `SCP-E003` denials on the test PR are "federation primitive WORKING AS DESIGNED" and that "Wave G acceptance criterion 1 still SATISFIED." This creates a scope ambiguity: if the Wave G canary test PR is not explicitly designed to be denial-free, Branch 4 allows AC #1 to be satisfied even when the policy-check run ends in `SCP-E003` denial. The plan does not explicitly constrain the test PR to be constructed such that no SCP-R-NNN rule fires.

**Amendment required:** Add a constraint to Wave G Action step 3 specifying that the canary test PR MUST be designed to avoid triggering rule denials (e.g., a noop change to a file path outside all SCP-R-* evaluation surface). AC #1's "all 12 policy-check steps green" should be clarified to mean "all 12 steps complete with PASS verdict" not "all 12 steps ran to completion regardless of verdict." Reword Branch 4 accordingly.

**ARCH-MIN-001 — §4 Wave E authoring parallelism: env-var injection must be same-PR-coupled with Wave D (mandatory, not optional)**

Wave E action step 2: "Add the `SCP_TEST_SIMULATE_APP_TOKEN_FAILURE` env-var flag check at the top of the token-exchange step in `policy-check.yml`". This means Wave E implementation touches `policy-check.yml` — same file as Wave D. Separate PRs would conflict. Plan's "same-PR coupling with Wave D acceptable" implies optional — should be MANDATORY for env-var injection (fixture design can still parallel; the actual env-var landing must be in Wave D's PR).

**ARCH-MIN-002 — §3.2 scaffolder FUP out-of-scope correct; dependency description understates Wave G evidence reuse**

Plan correctly places `FUP-WP-SCP-024-SCAFFOLDER-V1.2-INCOMPAT-001` out-of-scope, but should explicitly state Wave G's evidence URL IS the validation for the scaffolder fix (scaffolder generated PIM's wrapper; PIM's CI run validates the scaffolder output). Otherwise the scaffolder FUP slice might unnecessarily require its own verification run.

**ARCH-MIN-003 — §9 follow-ups: TF-PIM-001-ARCH-002 real-API follow-up coverage not listed as distinct §9 item**

§3.3 maps TF-PIM-001-ARCH-002 to Wave E; Wave E body documents the mock-vs-real-API decision. But §9 does not carry a follow-up entry for the real-API coverage track. The 2026-08-21 rotation execution date appears in §9 (correct); the real-API selftest follow-up should receive parity treatment.

**ARCH-NIT-001 — §6.4 grep scope is adopter-wrappers-only; SCP-self wrapper not covered**

`§6.4 §12.7.10 invariant preservation` grep scope says "Expect: zero matches in adopter policy-check-wrapper.yml files." SCP-self's own wrapper (`standards-control-plane-/.github/workflows/policy-check-wrapper.yml`) should also be in scope. If SCP-self's wrapper gained a `secrets: inherit` clause at any point, the invariant would be violated for the dogfood case too.

### Wave-by-wave reversibility ranking

1. Wave A — Cheapest. Delete App + secrets; <15 minutes; no code change
2. Wave B — Near-free. Revert D-050 ADR PR + DECISIONS.md row
3. Wave C — Low. Revert ADOPT-001 §12.7 updates; one PR
4. Wave E — Low-medium. Revert selftest fixture; bundled with Wave D if same-PR-coupled
5. Wave D — Medium. Revert policy-check.yml change; one PR + Tier 2 review + operator-attended fire
6. Wave F — Zero. No state change
7. Wave G — Medium-high. Revoke App install on PIM + re-open branch protection degradation
8. Wave H — Highest (but not high in absolute terms). Re-relax PIM main required-check; TF-PIM-001 re-opens

**Non-reversible in practice:** None. The `.pem` exposure risk during Wave A is the only item where a failure is partially non-reversible (leaked key cannot be un-leaked), but the credential can be rotated.

### Pareto-frontier check

**Argument for collapse (A+B+C+D → single slice):** Wave A is GitHub-UI ceremony (cannot be PR); B (ADR) + C (docs) + D (workflow) could land in one commit; lower merge-ceremony overhead.

**Argument against:** ADR-first discipline (B before D) is architecturally intentional (D-049 followed the same shape); coupling ADR to Codex Tier 2 dispatch would force ADR through code-change R-cycle protocol.

**Possible simplification:** Wave C (ADOPT-001 updates) could be same-PR-coupled with Wave D — docs about what workflow change introduces naturally belong in the same PR. §5.2 already notes "same-PR coupling with Wave D acceptable" for Wave E; Wave C merits same treatment. **Surfaced as observation, not finding.**

**Verdict:** 8-wave structure is acceptable as-is; Wave C/D same-PR coupling should be explicitly recommended rather than optional.

### Carry-forward to R2

R2 must verify closure of ARCH-MAJ-001 and ARCH-MAJ-002 amendments before accepting:
- ARCH-MAJ-001 closure: §7.5a step 3 must name direct `gh api PATCH` invocation; `enable-required-check.sh --restore` reference removed or qualified
- ARCH-MAJ-002 closure: Wave G Action step 3 specifies denial-free canary PR design; AC #1 commentary clarifies "PASS verdict"

ARCH-MIN-001/002/003 + ARCH-NIT-001 fold inline as v0.3 amends before R2 dispatch.

### Convergence signal
ITERATE-EXPECTED
