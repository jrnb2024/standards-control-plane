# WP-SCP-030 SCP-R-030 — R1 3-lens adversarial review dispositions

**Reviewed artefacts:** `policies/SCP-R-030.rego` + `schemas/rule-config.schema.json` (`acc-hook-installed` opt-in).
**Review mode:** 3 parallel lenses (correctness / safety_bypass / completeness_governance) per the cardinal 3-lens discipline. Static review (no `opa` binary in-session; acc-hook bash allowlist excludes `opa`/`regal` — validation is CI-side via `policy-check.yml`'s per-rule `opa test --threshold 90` step).
**Date:** 2026-05-31 (autonomous Pattern-3 run, dispatch `pattern3-20260531T202644Z-70945`).

---

## Lens verdicts

| Lens | Verdict | Blocking findings |
|---|---|---|
| correctness | ACCEPT-WITH-FIXES | CORR-MAJ-001, CORR-MAJ-002 |
| safety_bypass | REJECT (curable) | SB-MAJ-001, SB-MAJ-002 |
| completeness_governance | ACCEPT | none (CT-variant PASS + SCP-self dogfood PASS both verified) |

**R-FIXPOINT outcome:** the sharp, contract-aligned core of the safety_bypass REJECT is **CURED in-code** (marker top-of-file anchor); the residual is an explicitly-chosen warn-baseline heuristic trade-off (plan §4) accepted with documentation + a D-060 hardening item. No NEW failure surface introduced by the fix-round (cure-worse check below). Per prompt §3.3 the safety_bypass REJECT is surfaced to the operator in the §6 handoff for ratification — it is NOT silently overridden.

---

## Dispositions

### CORR-MAJ-001 — `scp_r_030_claude_md_content` undefined on non-string input — **FIXED**
The original `:= content if { is_string(content) }` left the value *undefined* when `input.claude_md` was present-but-non-string (null/number/object), making downstream helpers fragile. Added a second clause `:= "" if { not is_string(...) }` so the function is **total** (string when present, `""` otherwise). Mirrors the `default`/multi-clause idiom in `scp_common.rego` + `scp_r_008_unquote`. `policies/SCP-R-030.rego` content helper.

### CORR-MAJ-002 — fixture matrix lacks waiver + disable suppression-observability cases — **ACCEPTED → Phase 3**
The warn-observability blocks (waiver-suppression + rule-config-disable-suppression) need dedicated test cases to reach the ≥90% per-rule coverage gate. Folded into the Phase 3 fixture set: in addition to the §4 matrix, the test file adds (a) opted-in + marker-absent + active waiver → 0 deny + ≥1 warn observability record; (b) opted-in + marker-absent + `rules.SCP-R-030.disable: true` (+justification +expires_at) → 0 deny + ≥1 rule_config warn record. These exercise the suppression branches the 9-fixture matrix alone would leave uncovered.

### CORR-MAJ-003 — finding shape omits `severity`/`line` vs prompt §3.1 — **NOT A DEFECT (codebase-precedent followed)**
Prompt §3.1 lists an illustrative `{rule_id, severity, message, file, line}` shape. The realised shape `{rule_id, file, code, message, remediation_url, msg}` follows the **actual SCP-R-008 emission idiom** (which also omits `severity`; `line` is only emitted when a concrete line number exists — SCP-R-030 findings are whole-file CLAUDE.md-scoped). The `code` field carries the finding subtype (`marker_absent` / `claude_md_absent` / `element_missing:<name>`), which the prompt's §4 matrix asserts on. Followed codebase precedent over the prompt's illustrative shape.

### CORR-nit-001 — schema description "ellipsis" — **FALSE POSITIVE (stale read)**
The `acc-hook-installed` description already carries the full filename `D-058-scp-canonical-conformance-strategy-2026-05-29.md` (no ellipsis). No action.

### SB-MAJ-001 — buried / code-fenced marker spoofs whole-file `contains` — **PARTIALLY FIXED (sharp part cured)**
**Valid core:** the original `scp_r_030_has_marker` used `contains(content, marker)` anywhere in the file, so a marker buried at line 50 / inside a code-fence would pass without a genuine top-of-file preamble.
**Fix:** `scp_r_030_has_marker` now anchors the marker to the **first 3 lines** of CLAUDE.md, matching ACC contract element 1 ("marker on line 1"; all 6 hooked repos place it there per plan §5.1). A buried marker now correctly yields `marker_absent`. This closes the spoof that mattered.
**Declined (cure-worse):** anchoring the *element* checks (always-allowed / ceremony / never-disable) to a tight line-window around the marker. SCP's own preamble runs ~40 lines and the 6 repos' preambles vary in length/ordering; a tight element window would false-warn legitimate variants — the opposite failure for a rule whose whole point is to *reduce* friction. Element heuristics remain whole-file substring checks per plan §4's explicit "heuristic substring checks" design.

### SB-MAJ-002 — never-disable regex false-PASS on unrelated "not … disable" text — **ACCEPTED AS WARN-BASELINE TRADE-OFF (documented; D-060 hardening item)**
Valid observation: `(?i)(never|not|forbidden|don.t)[^\n]{0,60}disabl` can match unrelated CI/deploy prose, so element 5 can false-PASS.
**Why accepted, not fixed now:**
- **Warn-baseline + threat model.** SCP-R-030 ships at warn (never blocks merge in B.1). Its threat model is *accidental preamble drift*, not a malicious actor — a repo gaming its own onboarding preamble would only sabotage its own sessions (the preamble exists to stop *that repo's* sessions tripping the hook). There is no adversarial incentive.
- **False-PASS is the safe direction for a 4-week observation rule.** A false-PASS on element 5 = one missed warn; a false-WARN = noise that erodes trust during the very window D-060 will judge. Tightening the regex trades the safe error for the noisy one.
- **Plan §4 explicitly chose cheap heuristic substring checks.** This is in-intent, not drift.
**Forward:** logged as the D-060 hardening candidate `FUP-WP-SCP-030-ELEMENT-HEURISTIC-HARDENING-001` — if the 4-week observation shows real element-5 drift slipping through, D-060 can require a section-anchored never-disable check (e.g. under an `## If you trip the hook` heading) as part of any deny-promotion.

**FUP amendment (external-ratification fold, 2026-06-01) — MEASUREMENT BLIND-SPOT, must inform D-060.** Because the element checks (always-allowed / ceremony / never-disable) are **whole-file greps**, a CLAUDE.md with the *entire preamble deleted but the line-1 marker surviving* still PASSes via incidental substrings elsewhere in the file. Concretely on SCP-self: `"NEVER disable"` (~L47), `"scripts/"` (~L48), and a `docs/**` reference all appear outside the preamble block, so a stripped-preamble-but-marker-present SCP-self would score zero `element_missing` findings. **Consequence for D-060:** the 4-week observation **under-counts real preamble drift** — a low `element_missing` count must NOT be read as "preambles healthy." Section-anchored element checks (elements must appear within the preamble block, not anywhere in the file) should therefore be the **near-default at deny-promote**, not merely an option. This blind-spot is the warn-baseline trade-off accepted for B.1 (the marker top-of-file anchor is the only locality guard shipped); it is acceptable for the observation window precisely because the window's purpose is to inform D-060, where this note pre-commits the hardening direction.

> External 3-lens ratification (2026-06-01): RATIFY. Correctness clean; cure-worse empirically confirmed — SCP-self's preamble diverges ~11 lines from a tight element window, so shipping section-anchored element checks now would false-warn the dogfood itself. Deferral to D-060 (with this blind-spot recorded) is the correct call. No code changes.

### SB-nit-001 — finding_id-only waiver gap — **PRE-EXISTING, OUT OF SCOPE**
`scp_common.rego` already fails-closed on finding_id-only waivers (documented WP-SCP-022 020C.1 decision). SCP-R-030 reuses the shared `scp_active_waiver_for` helper (no bespoke waiver matching), so it inherits the safe behaviour. No SCP-R-030-specific action.

---

## Cure-worse R2 check

The two in-code fixes are evaluated for introduced failure surface:
- **Total-function `claude_md_content`:** strictly additive (a previously-undefined value becomes `""`). Cannot worsen any existing path; removes a fragility. No new surface.
- **Marker top-of-file anchor:** strictly tightens (rejects buried markers). Could only "worsen" by false-warning a repo whose marker is NOT in the first 3 lines — but all 6 hooked repos place it on line 1 (plan §5.1) and the PASS fixture mirrors SCP-self (line 1). No legitimate variant regresses.

No cure-worse R2 trigger. R-FIXPOINT MET for B.1.

---

## Verified-clean (completeness lens, full plan context)

- **Opt-in default-safety:** absent `acc-hook-installed` ⇒ rule never fires (vacuous-pass).
- **CT-style ceremony variant PASSES** (`dispatch` substring) — proves LINKAGE-not-VALUES (§8 criterion).
- **SCP-self dogfood PASSES** its own rule (marker line 1 + `## Always-allowed`+`docs/**` + `scripts/operator/scp-pattern3-dispatch.sh` + "forbidden … disable").
- **Edge cases:** `v2` marker ⇒ `marker_absent` (exact-substring, intended migration-window behaviour); duplicate marker ⇒ no double-fire (boolean `contains`); CLAUDE.md absent ⇒ `claude_md_absent`.
- **Governance:** warn-baseline shape (deny + WARN_BASELINE demotion deferred to companion workflow PR); D-060 reserved, not consumed; no VALUES prescribed.
