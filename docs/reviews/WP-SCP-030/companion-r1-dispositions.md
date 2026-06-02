# WP-SCP-030 companion-workflow activation — 3-lens R1 dispositions

**Date:** 2026-06-01. **Branch:** `wp-scp-030-companion-activation`. **Session:** autonomous Pattern-3 run (D-057; dispatch `pattern3-20260601T213159Z-70241`).
**Change under review:** the companion-workflow activation PR — makes the dormant rule **SCP-R-030 FIRE** as a warn-baseline rule by (1) an additive Option-A `opa eval` repo-level pass in `policy-check.yml` that materialises `input.rule_config` / `input.claude_md_present` / `input.claude_md` and merges SCP-R-030 deny findings into `policy-findings.json`, and (2) adding `SCP-R-030` to **both** `WARN_BASELINE_RULES` sites (render-deny + scorecard). Plus four `tests/workflow/fixture-scp-r-030-*` selftest fixtures.
**Kernel-dangerous:** yes — modifies `policy-check.yml`, the estate merge-gate. Mandatory 3-lens R1; a safety_bypass REJECT on the merge-gate is a hard stop.
**Scope decisions (operator-ratified 2026-06-01, NOT re-litigated):** (1) Option A additive, no `--combine`; (2) SCP-R-030 only, SCP-R-006 stays dormant; (3) ship active, no version bump (v1.4.0 already on main); (4) full D-057 process.

---

## Verdicts

| Lens | Verdict | Notes |
|---|---|---|
| correctness | **ACCEPT** | Message strings verified char-for-char against the rego; envelope matches `input.*`; merge shape matches `policy-findings.json`; additive-only confirmed. NITs only. |
| safety_bypass | **ACCEPT** (no REJECT) | Coupling guard airtight (both `WARN_BASELINE_RULES` sites, same PR); SCP-R-030 can never reach `effective_denies`; data doc subprocess-isolated from the conftest pass; SCP-R-006 doubly-guarded dormant. One MIN (D-060 fail-closed gate). |
| completeness_governance | REJECT → **CURED → ACCEPT** | 3 MAJ, all *pending Phase-3 deliverables* (this dispositions doc; rows-4/6 coverage rationale; STATUS/BACKLOG bookkeeping). All additive, zero cure-worse risk. Folded in fix-round-1. |

**R-FIXPOINT: MET.** No safety_bypass REJECT (no §7 hard stop). The completeness REJECT was on deliverables that are authored in Phase 3 (this very document + the rows-4/6 in-code rationale + bookkeeping); folding them is purely additive (comments + docs), so cure-worse is impossible. No new blockers introduced.

---

## Findings + dispositions

### correctness (ACCEPT)
- **[CORR — message-string fidelity] VERIFIED.** The `marker_absent` and `claude_md_absent` oracle messages, the `remediation_url` (concat of the two rule strings), and `file`/`path` = `"CLAUDE.md"` match the rego (`policies/SCP-R-030.rego:139,151,40-43,127`) char-for-char. A mismatch would have failed the selftest summary comparison; none exists.
- **[CORR-NIT-001]** `out.get("message", out.get("msg", ""))` fallback is correct (the deny output always carries both `message` and `msg` = the same string). No change.
- **[CORR-NIT-002]** Per-file conftest pass untouched; the new step runs after `scp_policy_check_run` and only **appends** to `policy-findings.json`. Confirmed additive.
- **[CORR-NIT-003 → CG-MIN-001] Disabled-rule observability asymmetry.** A repo-level rule disabled via `.scp/rule-config.yaml` is suppressed inside `data.main.deny` (no deny emitted), so — unlike the conftest path — the step writes **no** `disabled-rules.json` record for it. The suppression is correct (no false finding; the `fixture-scp-r-030-disabled` oracle is accurate); only the scorecard's disabled-rules audit trail under-reports repo-level disables. **Disposition:** documented inline in the step comment; tracked-forward as `FUP-WP-SCP-030-REPO-LEVEL-DISABLE-OBSERVABILITY-001` (write an analogous record from `data.main.warn`), deferred to keep the warn-merge surface minimal for v1.

### safety_bypass (ACCEPT — no REJECT)
- **[SB — coupling guard §4.1] VERIFIED airtight.** SCP-R-030 is in `WARN_BASELINE_RULES` at **both** the render-deny threshold-exclusion site and the scorecard site (same PR). An opted-in missing-marker adopter's finding flows to `warn_baseline_findings` → `::warning::`, is excluded from `effective_denies`, and the scorecard verdict maps to `warn` not `deny`. There is no path where it blocks the merge. (If it were in only one set: missing from render-deny → it would BLOCK = the §4.1 catastrophe; missing from scorecard → wrong verdict label only. Both present.)
- **[SB — other rules] VERIFIED.** The step merges only `rule_id in REPO_LEVEL_RULES={"SCP-R-030"}` and only appends; no per-file deny can be dropped/masked. The `--data` doc is scoped to the step's own `opa eval` subprocess and cannot leak into the conftest pass (which builds its own `data_dir` via the lib). An adopter cannot use it to suppress SCP-R-001..008.
- **[SB — SCP-R-006 dormancy] VERIFIED.** Doubly-guarded: its trigger needs `input.changed_files` (not materialised → vacuous) AND it's filtered out by `REPO_LEVEL_RULES`. No silent activation.
- **[SB-MIN-001 → CURED] D-060 fail-closed gate.** The step fails **open** on an opa error (annotate + merge nothing). This is safe **only** while SCP-R-030 is warn-baseline (excluded from threshold → cannot block regardless). A future D-060 deny-promotion that removes SCP-R-030 from `WARN_BASELINE_RULES` would turn this fail-open into a **silent merge-gate bypass** for a now-blocking rule. **Disposition:** added an explicit ⚠️ D-060 GATE note to the step requiring that promotion convert this block to fail-closed in the same PR. Tracked-forward as `FUP-WP-SCP-030-FAIL-CLOSED-AT-DENY-PROMOTE-001`.
- **[SB-NIT-001]** Message strings are not sanitised at JSON-write time but ARE sanitised at render time (`_sanitise_annotation_text`), consistent with the pre-existing conftest path; the messages are rule-hardcoded (no adopter interpolation). No new injection vector.

### completeness_governance (REJECT → CURED → ACCEPT)
- **[CG-MAJ-001 → CURED]** `docs/reviews/WP-SCP-030/companion-r1-dispositions.md` absent. **Disposition:** this document. The measurement-blind-spot caveat is carried forward below (§5 requirement).
- **[CG-MAJ-002 → CURED]** Rows 4 (not-opted-in) + 6 (regression) coverage rationale undocumented. **Disposition:** added an explicit SPEC §6 coverage-map comment to the `workflow-selftest.yml` WP-SCP-030 block — row 4 is covered by the **existing** `fixture-pass` (no `rule-config-path` → `input.rule_config={}` → not opted in → vacuous; its `findings:[]` oracle unchanged), and row 6 by the **existing** `fixture-pass`/`fixture-fail` oracles staying byte-identical (the additive step touches only SCP-R-030). Rule-branch coverage for all rows also exists at the rego-unit layer (`policies/tests/scp_r_030_test.rego`, #196). This is a reasoned, surfaced coverage decision — **not** a silent descope: building four *new* reusable-workflow invocations covers the four gate-distinct behaviours the new path introduces (healthy-pass / warn-finding-shown / claude-absent-warn / disabled-suppressed); rows 4 & 6 are coverage the existing harness already provides every run, and duplicating them as new invocations would add artifact-collision plumbing without new assurance.
- **[CG-MAJ-003 → CURED]** STATUS.md chain row + BACKLOG.md flip absent. **Disposition:** authored in this PR (Phase 3 bookkeeping) — STATUS chain entry (companion SHIPPED, SCP-R-030 now FIRING warn-baseline, B.2 ready, v1.4.0 ready-to-cut-active) + BACKLOG WP-SCP-030 row flip (companion SHIPPED).
- **[CG-MIN-002 → CURED]** "Emit workflow summary" step updated to name the SCP-R-030 fixtures + the coupling-guard proof.
- **[CG-NIT-001]** `grep -c` of the uses-string returns 14 (includes 2 comment/message occurrences) while the anchored regex the assertion uses correctly counts 12 functional `uses:` lines. Assertion is correct; noted for future maintainers.
- **Decision compliance VERIFIED:** (1) Option A additive, no `--combine`, `lib/` not in diff; (2) `REPO_LEVEL_RULES={"SCP-R-030"}`, SCP-R-006 inputs not materialised; (3) `version-manifest.json` NOT in the diff (no bump); (4) full process.

---

## §5 carry-forward — MEASUREMENT BLIND-SPOT (must inform D-060)

Carried verbatim-in-substance from the B.1 dispositions (`docs/reviews/WP-SCP-030/r1-dispositions.md`, FUP amendment 2026-06-01):

> Because the element checks (always-allowed / ceremony / never-disable) are **whole-file greps**, a `CLAUDE.md` with the *entire preamble deleted but the line-1 marker surviving* still PASSes via incidental substrings elsewhere in the file (on SCP-self, `"NEVER disable"`, `"scripts/"`, and a `docs/**` reference all appear outside the preamble block). **Consequence for D-060:** the 4-week observation **under-counts real preamble drift** — a low `element_missing` count must **NOT** be read as "preambles healthy." Section-anchored element checks (elements must appear *within* the preamble block, not anywhere in the file) should be the **near-default at deny-promote**, not merely an option. The cure was deferred at B.1 because SCP-self's own preamble diverges ~11 lines from a tight element window, so shipping section-anchored checks now would false-warn the dogfood.

This companion PR does **not** change that heuristic (it only materialises the inputs + activates the warn). The blind-spot therefore persists into the observation window exactly as B.1 recorded it. **D-060 must read this before reading any `element_missing` telemetry.**

---

## Tracked-forward items (none blocking)
- `FUP-WP-SCP-030-FAIL-CLOSED-AT-DENY-PROMOTE-001` — D-060 deny-promotion must convert the step's fail-open to fail-closed in the same PR (SB-MIN-001).
- `FUP-WP-SCP-030-REPO-LEVEL-DISABLE-OBSERVABILITY-001` — emit a `disabled-rules.json` record for repo-level rule-config disables (from `data.main.warn`) so the scorecard audit trail matches the per-file path (CORR-NIT-003 / CG-MIN-001).
- `FUP-WP-SCP-030-ELEMENT-HEURISTIC-HARDENING-001` (from B.1) — section-anchored element checks at deny-promote; pre-committed direction for D-060.
- `FUP-WP-SCP-030-EXTEND-REACH-ACC-SA-RI-001` (from B.1) — hooked ∩ cohort reach extension.

## CI fix-round-1 (post-R1, §7.6 — selftest caught a real eval-path bug)
First CI run (PR #201, run 26785498712): all gate checks green AND all four `fixture-scp-r-030-*` policy-check jobs green, BUT the `workflow-selftest` orchestrator FAILED on the `fixture-scp-r-030-marker-absent` summary comparison — actual `findings: []` vs expected `[marker_absent]`. Root cause: the materialisation step's `opa eval` loaded the **whole `policies/` dir** (`--data <policy_root>`), which also pulls `policies/tests/*_test.rego` (`package main_test`) → `opa eval` **exit 2** (diagnostic on stdout, stderr empty) → the **fail-open** path swallowed it and merged zero findings (job stayed green because warn-baseline can't block — exactly the fail-open behaviour, and exactly why the selftest oracle is the catch). **Fix:** load only `scp_common.rego` + each `REPO_LEVEL_RULES` rule file (mirrors the proven conflict-gate adapter `_run_opa`), and surface stdout on error. This is the §7.6 single fix-round; it directly addresses the eval-path defect the selftest surfaced (not a fixture/oracle change — the oracle was correct; the eval was wrong). The fail-open design worked as intended (no adopter-merge block on the SCP-side error) and the selftest's materialisation-fires assertion did its job.

## CI evidence
To be appended once the re-run is green: `policy-check / scp/policy-check` + `check-invocation-log-entry` + the `workflow-selftest` orchestrator green, with the load-bearing `fixture-scp-r-030-marker-absent` job `success` AND its summary carrying the SCP-R-030 `marker_absent` finding.
