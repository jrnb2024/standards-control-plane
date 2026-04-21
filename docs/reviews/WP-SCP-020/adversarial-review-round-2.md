# WP-SCP-020 — Adversarial review round 2

**Date:** 2026-04-21
**Plan version reviewed:** v0.2
**Reviewers (parallel):** Reviewer A (architect + security), Reviewer B (governance-realist + devex/BS-hunting)
**Outcome:** RETURN TO v0.3. Round 2 confirmed that most v0.1 BLOCKINGs were resolved in v0.2, but surfaced ~6 new BLOCKING issues where v0.2 added governance *words* without naming the *mechanisms* that make those words bind.

---

## Reviewer A (architect + security)

### Round-1 BLOCKING verification

| # | Round-1 finding | Grade | Notes |
|---|---|---|---|
| 1 | Rego/Python source-of-truth conflict | PARTIAL | 020C.1 (iii) names `rego-vs-python-conflict` CI job with "shared fixture corpus" and "Python authoritative on disagreement." But the corpus is not specified, the "same input" adapter problem (Python takes `request.scope`/`services.yml` paths; Rego takes `data.*`) is unaddressed. Loose end — see N1. |
| 2 | Waiver integration end-to-end | FIXED | 020C.1 (i)+(ii) testable. |
| 3 | Bootstrap / circular dependency | PARTIAL | Split into 020D1/020D2 with rc.1 interim is correct. But §3 diagram shows `020H(promote v1.0.0) → 020J(tag-protection) → 020D2` — `v1.0.0` cut before tag-protection exists. Slice-row text contradicts diagram. See N2. |
| 4 | `-o github` annotation permissions | NOT FIXED | 020B (iv) defers resolution to U-sec-4, "closed before 020B merges." Deferring the blocker is not closing it. Per "no deferring," should close now. See N3. |
| 5 | `pull_request` vs `pull_request_target` | FIXED | Clean. |
| 6 | Input validation commitment | FIXED | 020B (ii)+(vi) testable. |
| 7 | SCP tag mutation + adopter SHA-pin | PARTIAL | Contingent-on-org-tier escape hatch hand-waves the substitute path. See N4. |
| 8 | Structured annotation payload | FIXED | 020B (ix)+020C structured-object + fixture; green. |
| 9 | Local reproduction script | FIXED | 020B.2 clean. |
| 10 | Break-glass posture | PARTIAL | `enforce_admins=true`, SCP-E004 marker. But `scp_bypass: true` is an input-bool anyone with PR-write can set. Audit marker alone is soft. See N5. |

### New findings introduced by v0.2

- **[BLOCKING] N1 — Conflict-gate under-specified to the point of not being runnable.** 020C.1 (iii) says "run both against a shared fixture corpus and assert same verdict." Python evaluators take parsed-object inputs threaded through `request.scope`/`services.yml` loaders; conftest-Rego takes file paths and produces `data.*` via its own loader. The plan names neither the adapter that normalises both to a common verdict tuple nor where shared fixtures live on disk. Fix: 020C.1 must add (v) adapter module `tests/conflict_gate/adapter.py` + (vi) fixture root `tests/conflict_gate/fixtures/SCP-R-NNN/{input,expected-verdict}.*`.

- **[BLOCKING] N2 — Slice-ordering diagram contradicts 020D1 / 020J preconditions.** §3 shows `020H(promote v1.0.0) → 020J(tag-protection) → 020D2`. But 020D1 scope row says tag-protection "must already exist" before 020D1 merges, and 020J says tag-protection "before `v1.0.0` is cut." So 020J must run *before* 020D1, not after 020H. As written, the cut of `v1.0.0` fires against an unprotected tag namespace. Fix: `020J → 020D1 → 020H(rc.1) → 020E.a → 020H(v1.0.0) → 020D2 → 020E.b → …`.

- **[BLOCKING] N3 — Unknowns scheduled to "close before slice opens" are plan-level decisions.** U-sec-2 (org-plan-tier for `enforce_admins`/tag-protection/signed-commits) **must** close before plan PR merges — if the org tier doesn't support `enforce_admins`, §9 acceptance #2 is unachievable. Same for U-sec-4 (Conftest annotation surface — it's a doc-read). Fix: gate plan-PR merge on U-sec-2 + U-sec-4 resolution, not slice-open. U-arch-2 (reusable-workflow caller vs SCP secrets) same pattern.

- **[BLOCKING] N4 — `scp_bypass: true` auditability insufficient.** Input is a workflow-call bool any caller-PR author can set. "Emits SCP-E004 in JSON summary" is passive. Fix in 020B + 020H §12: (a) named-approver gate — bypass honoured only if PR has approving review from SCP-CODEOWNER or `scp-break-glass` team; (b) bypass blocks merge unless a sibling commit in the same PR contains D-NNN record + paired `waivers.json` entry — not "within 5 business days"; (c) daily workflow scans SCP-E004 emissions and opens tracking issue if D-NNN pairing absent.

- **[MAJOR] N5 — "Python authoritative on conflict" locks in Python tyranny with no amendment path.** If conflict-gate failure surfaces genuine Python bug (Rego correctly denies, Python incorrectly allows), the gate *passes* (Python wins by default) and PR proceeds bug-shielded. Fix: on disagreement, gate **fails** (blocks merge), emits SCP-E005 `conflict-gate-disagreement`, adjudication is amending decision record.

- **[MAJOR] N6 — 15-slice review cost.** WP-SCP-019 had 6 slices; WP-SCP-020 v0.2 has 15-17 checkpoints depending on count. Recommend §9 sub-clause committing to slice-by-slice squash with tagged review checkpoints.

- **[MAJOR] N7 — §13 open unknowns leak past plan merge.** U-arch-2 is marked "closes before 020B" — should close before plan merge.

- **[MINOR] N8 — 020B (xi) triple-use numbering.** Cache + error codes + break-glass in one row; split into xi-a, xi-b, xi-c.

- **[MINOR] N9 — ≤ 5 rules names only 3 categories.** Commit to exactly 3 for v1.0.0, add 2 via v1.1+ RFC.

### Fixpoint declaration

**RETURN TO v0.3** on N1, N2, N3, N4 (BLOCKING); clean N5–N9 in same round.

---

## Reviewer B (governance-realist + devex, BS-hunting)

### Round-1 finding verification

- **Governance B-1 (waiver-aware Rego):** FIXED.
- **Governance B-2 (break-glass / enforce_admins):** PARTIAL. `enforce_admins=true` set; `scp_bypass: true` emits SCP-E004. But access control on `scp_bypass` undefined — see BS-2.
- **Devex #1 (annotation payload):** FIXED.
- **Devex #2 (local repro):** PARTIAL. Binary-SHA pinning unspecified — see BS-8.
- **Devex #3 (workflow test harness):** PARTIAL → NEW-BLOCKER. Enforcement gap — see BS-7.
- **Devex #4 (`policies/README.md`):** PARTIAL. Sections named, structure/usability not — see BS-9.
- **Devex #5 (JSON schema):** FIXED.
- **Devex #6 (caller wrapper ≤12 lines):** NOT FIXED. Arithmetic fails — see BS-3.
- **Devex #7 (observability):** PARTIAL. Aggregate visibility correctly deferred to WP-SCP-023.
- **Governance M-1 (fast-feedback):** FIXED.
- **Governance M-3 (rule-RFC):** PARTIAL. Window named but reviewer/quorum unspecified — see BS-5.
- **Governance M-4 (policy-bot rejection):** FIXED.
- **Governance M-5 (scaffolder):** FIXED as follow-up.

### New BS introduced by v0.2

- **[BLOCKING] BS-1 — "Python authoritative on conflict" is non-operational.** §2 + 020C.1(iii) declare precedence but name no runtime mechanism. At 11pm Friday with Python=allow/Rego=deny, the on-call engineer has no path: the Rego deny blocks merge, the "Python authoritative" statement is CI-time assertion on fixtures, not runtime override. Either require matching Python evaluator pass in-workflow, or admit precedence is dev-time contract only.

- **[BLOCKING] BS-2 — `scp_bypass: true` has no access control.** Nothing prevents AI coding agent setting on own PR, merging, 5-day window enforced by nobody. CODEOWNERS is on `policies/**`, not caller wrappers. Fix: require SHA-pinned waiver reference resolvable at workflow time; SCP-E004 is merge-blocking unless matching unexpired `waivers.json` entry exists.

- **[BLOCKING] BS-3 — ≤ 12 lines is not real.** Minimum wrapper: `name:` (1) + `on: pull_request` with `branches:` (3) + `permissions:` with 2-3 grants (4) + `jobs:` + job-key + `uses: …@SHA` (3) = ~11 before `with:` or concurrency. Add freshness-warning UX → 13-14. Either drop the number, ship exact minimal wrapper in plan text, or commit to generating via SCP-073-scaffolder.

- **[MAJOR] BS-4 — `.scp/rule-config.yaml` cascade-weakening.** Callers silently disable rules; no read-back to SCP. 10 repos × 2 disabled "temporarily" = primitive becomes advisory. Fix: 020B emits `disabled_rules` list in JSON summary; WP-SCP-023 aggregates; acceptance adds disabled-rule enumeration in commit-status text.

- **[MAJOR] BS-5 — RFC 48h window is theatre.** No quorum, no named reviewer role, no failure mode. Is 48h wall-clock or business-hours? Fix: state quorum (1 SCP-CODEOWNER approval = merge-eligible after 48h wall-clock; 0 approvals = auto-defer).

- **[MAJOR] BS-6 — "Rollback SLA 4h" has no pager.** James solo on SCP; "4h" aspirational. Fix: name detection (adopter-reported via issue template + SCP-side canary re-run on each release); SLA: "best-effort, target 4h; no paging rotation in v1.0.0; escalation via SCP issue tracker."

- **[MAJOR] BS-7 — `workflow-selftest` enforcement gap.** 020B.1 says "runs on every SCP PR; blocks merge if output diverges" but triggers via `workflow_dispatch` (manual). Self-contradictory. Fix: trigger `pull_request` on paths `.github/workflows/policy-check.yml` + `policies/**`.

- **[MAJOR] BS-8 — `scripts/scp-policy-check` binary-SHA parity.** "Same binary SHAs, same bundle" but plan doesn't say how. Fix: pin OPA/Conftest version + SHA256 in `scripts/.tool-versions` or `scripts/scp-policy-check.lock`; script verifies on run.

- **[MINOR] BS-9 — `policies/README.md` prose-wall risk.** Six sections, no structure commitment. For agent adding rule #6 at 2am needs numbered checklist + copy-pasteable template.

- **[MAJOR STRUCTURAL] BS-10 — 15 slices for one WP.** WP-SCP-019 delivered in 6. Stall-mid-WP risk compounds with U-sec-2 going wrong. Recommend split: WP-SCP-020 = A, B, B.1, B.2, C, C.1, D1, E(a), H(rc.1). WP-SCP-020-gate = J, D2, E(b/c), F, G, H(part2/3), H.1. rc→promote is natural seam.

### Fixpoint declaration

**RETURN TO v0.3** on BS-1, BS-2, BS-3 (BLOCKING); fold BS-4, BS-5, BS-6, BS-7, BS-8 (MAJOR); decide BS-10 split.

---

## Round-2 consolidation

**6 unique BLOCKINGs** (dedup: A-N4 ≡ B-BS-2):

| # | Finding | v0.3 resolution plan |
|---|---|---|
| 1 | Conflict-gate adapter + fixture path unspecified (A-N1) | 020C.1 adds (v) adapter module, (vi) fixture tree path |
| 2 | Slice-ordering diagram self-contradictory (A-N2) | §3 redrawn: `020J → 020D1 → 020H(rc.1) → 020E.a → 020H(v1.0.0) → 020D2 → 020E.b → 020F → 020G → 020H(part3) → 020H.1` |
| 3 | U-sec-2, U-sec-4, U-arch-2 leak past plan merge (A-N3 + A-N7) | Resolve all three now in v0.3 §13 + new §14 |
| 4 | `scp_bypass: true` access control (A-N4 ≡ B-BS-2) | 020B bypass requires (a) SCP-CODEOWNER approval, (b) sibling commit with D-NNN + waivers.json entry, (c) SCP-E004 merge-blocking unless matching unexpired waiver; daily scan workflow in 020H |
| 5 | Python-authoritative non-operational (B-BS-1 + A-N5) | 020C.1 (iii) rewritten: on disagreement, gate **fails** (blocks merge) + SCP-E005; dev-time parity remains a CI contract but is not a runtime override |
| 6 | ≤ 12-line wrapper arithmetic (B-BS-3) | Drop the number; 020H publishes exact minimal wrapper text; SCP-073-scaffolder generates it |

**7 MAJORs** (A-N6, A-N8, A-N9, B-BS-4, B-BS-5, B-BS-6, B-BS-7, B-BS-8): all folded into v0.3 slice acceptance criteria.

**1 MINOR** (B-BS-9): `policies/README.md` template-first format in 020C acceptance.

**1 STRUCTURAL** (B-BS-10, recommended split): **Rejected** — operator directive is "no descoping, no deferring." WP stays monolithic; §9 adds slice-by-slice review-checkpoint commitment to address review cost (A-N6 fold).

Round 3 plan: two reviewers re-verify the 6 BLOCKING closures + spot-check MAJORs. If no new BLOCKER surfaces, fixpoint reached.
