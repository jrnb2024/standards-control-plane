# TF-PIM-001 impl WP — arch-skeptic lens R2 review (v0.3)

**Dispatched:** 2026-05-21 PM-2 against impl WP plan-doc v0.3 at `d704c82`
**Agent type:** Plan (read-only; DO-NOT-EDIT mandate)
**Model:** Sonnet
**Worktree isolation:** yes

---

## Lens: arch-skeptic — TF-PIM-001 impl WP v0.3 R2 review

### Verdict
ACCEPT-WITH-AMENDMENT

### R1 closure verification

#### ARCH-MAJ-001 closure
**CLOSED.** §7.5a step 3 explicitly names "Invocation shape: direct `gh api PATCH` (NOT `enable-required-check.sh --restore`)" with rationale citing WP-SCP-020 020D2 and the absence of a pre-state JSON in the branch-protection log; a concrete `gh api -X PATCH` shell block is provided; restoration is documented to consume the captured `/tmp/scp-main-pre-rollback.json` as input to a manual PATCH. The `enable-required-check.sh --restore` reference is removed and the non-applicability is explained. The finding's three closure criteria are all met.

#### ARCH-MAJ-002 closure
**CLOSED.** AC #1 now reads "all 12 policy-check steps complete with PASS verdict" and explicitly states the canary PR is "designed denial-free per Wave G Action step 3" and that "no `SCP-R-NNN` rule emits a deny finding"; "AC #1 is NOT satisfied until a denial-free run is captured" is unambiguous. Wave G Action step 3 contains an explicit "Canary PR MUST be designed denial-free" constraint with a concrete avoidance heuristic. §7.6 Branch 4 is reworded to make the canary-PR-design failure surface and the federation-primitive failure surface separable.

#### ARCH-MIN-001 closure
**CLOSED.** Wave E parallelism paragraph contains explicit mandatory language: "the `SCP_TEST_SIMULATE_APP_TOKEN_FAILURE` env-var check injected into `policy-check.yml`'s token-exchange step (Wave E Actions step 2) **MUST land in the same PR as Wave D**". Optionality language is gone.

#### ARCH-MIN-002 closure
**CLOSED.** §3.2 now contains: "Wave G's PIM canary CI run URL IS the validation evidence for the scaffolder fix — the scaffolder generated PIM's wrapper (PR #234 instance), so PIM's CI run validates the scaffolder output directly."

#### ARCH-MIN-003 closure
**CLOSED.** §9 carries an explicit "TF-PIM-001-ARCH-002 real-API selftest coverage follow-up (v0.3 ARCH-MIN-003 closure)" entry with concrete close condition + sequencing + fixture description.

#### ARCH-NIT-001 closure
**CLOSED.** §6.4 now contains "INCLUDING SCP-self (jrnb2024/standards-control-plane-/.github/workflows/policy-check-wrapper.yml)" with annotation "(v0.3 ARCH-NIT-001 closure)". The secondary local grep also covers `.github/workflows/` without restriction.

### New findings introduced by v0.3

**ARCH-MIN-001-R2 — §7.5a step 3 PATCH invocation hard-codes only one of four SCP-self required contexts**

The ARCH-MAJ-001 closure correctly replaces `enable-required-check.sh --restore` with a `gh api -X PATCH` block. However, the example PATCH is illustrative in a dangerous way: it reconstructs required contexts as `-F 'required_status_checks[contexts][]=check-invocation-log-entry'` and the comment says `# canonical context only; policy-check removed`. Wave F step 2 names four SCP-self required checks: `policy-check / scp/policy-check`, `policy-check-readback`, `check-invocation-log-entry`, and `validate PR body`. The rollback PATCH drops `policy-check-readback` and `validate PR body` from the array. A pre-state capture (`gh api ... > /tmp/scp-main-pre-rollback.json`) is provided, but the operator is not instructed to use that capture to reconstruct the full contexts array in the restoration PATCH. Under rollback time-pressure, an operator executing the PATCH verbatim would inadvertently weaken SCP main's branch protection.

**Amendment required (v0.4 closure):** Replace the illustrative PATCH with a `jq`-based extraction from the captured pre-state JSON, fed into the restoration PATCH. This makes restoration state-restore rather than memory-reconstruction.

**Severity-rationale:** MIN — fires only in rollback hot-path (Wave D regression + Wave F failure); not on the happy path; closure is a one-block edit.

### Carry-forward to R3
ARCH-MIN-001-R2 closure verification — either at R3 if operator-attended OR at Option A R4 mechanical override (per operator authorisation; appropriate given DIMINISHING-RETURNS convergence signal).

### Convergence signal
**DIMINISHING-RETURNS**

The six R1 findings are all cleanly closed; the remaining finding is a contained documentation-precision issue in a rollback hot-path (not the happy path), is low-complexity to fix (a `jq` extraction instruction), and does not affect any wave sequencing, acceptance criteria, or architectural surface. The v0.3 document is materially correct and operationally ready on all load-bearing decisions. **Option A R4 mechanical override is the recommended close path** — fold ARCH-MIN-001-R2 into v0.4 + declare R-fixpoint MET without burning a full R3 dispatch on one MIN finding.
