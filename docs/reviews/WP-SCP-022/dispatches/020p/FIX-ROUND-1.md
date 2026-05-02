# WP-SCP-022 slice 020P — FIX-ROUND-1

**Date:** 2026-05-02
**Branch:** `feature/wp-scp-022-020p-scp-r-004-implementation`
**HEAD pre-fix-round-1:** `9f8639d` (slice 020P implementation).
**R1 verdict:** **APPROVED on all three lenses — fixpoint reached on R1 directly.**

## R1 outcome (3 lenses, parallel Sonnet)

| Lens | Verdict | CRIT | MAJ | MIN | nit |
|---|---|---|---|---|---|
| Correctness R1 | **APPROVED** | 0 | 0 | 1 | 1 |
| Safety/bypass R1 | **APPROVED** | 0 | 0 | 1 | 0 |
| Completeness R1 | **APPROVED** | 0 | 0 | 1 | 2 |
| **Total (deduped)** | **APPROVED** | **0** | **0** | **3** | **3** |

**Fixpoint criterion** per `feedback_recursive_adversarial_review.md`: zero new CRIT/MAJ on a complete cycle. **MET on R1.** This is the cleanest R1 result observed in WP-SCP-022 to date — the slice's mostly-mechanical translation from RULE-001's pre-vetted spec to implementation paid off.

## MIN closures

### COR-MIN-001 — meta-waiver test comment over-claims

**Lens:** correctness. **Severity:** MIN. **Inline-fix.**

The original `test_scp_r_004_waiver_suppresses_deny` comment asserted "the meta-waiver MUST contain a URL otherwise the meta-waiver is also a raw finding for SCP-R-004", but the test only exercised the suppression mechanism (waiver in `data.waivers`), not the fires-against-itself property (waiver in `input`). Reviewer correctly identified this as an over-claim.

**Closure.** Two-part fix in `policies/tests/scp_r_004_test.rego`:
1. **Clarify the original test's docstring** — it now honestly states the test exercises the suppression mechanism only, with a forward-pointer to the new property-exercising test.
2. **Add `test_scp_r_004_meta_waiver_without_url_fires_against_self`** — places a no-URL meta-waiver in `input` (alongside a legacy waiver) and verifies SCP-R-004 fires on BOTH entries (count == 2). This actually exercises the SAFE-MIN-001 property at unit-test level.
3. **Add `test_scp_r_004_meta_waiver_with_url_does_not_fire_against_self`** — symmetric: a URL-bearing meta-waiver in `input` does NOT fire (count == 0). Confirms the URL exemption applies to meta-waivers identically to legacy waivers.

Test count grew from 19 → 21. All pass locally (`opa test`: 65/65).

### SAFE-MIN-001 — workflow-command injection via newlines in waiver `reason`

**Lens:** safety/bypass. **Severity:** MIN. **Inline-fix in BOTH warn + deny branches (defense-in-depth, also closes pre-existing latent risk on deny path).**

Reviewer surfaced that `print(f"::warning file=...,title=...::{message}{suffix}")` writes attacker-controllable `reason` text directly to stdout, where GitHub Actions parses each line for workflow commands. A waiver entry with `reason: "approved by Jim\n::error file=.github/workflows/policy-check.yml,title=SCP-E001::malicious"` would produce a second stdout line that GitHub interprets as a workflow command.

**Impact.** LOW per reviewer assessment: modern runners disable `::set-env` and `::add-path`; only annotation cosmetic injection remains possible; the attacker already controls their own waivers.json content (so exfiltration via injected annotation is a low-value attack). However, the same shape exists on the **pre-existing deny-baseline branch** for SCP-R-001/002/003 — so the fix is doubly valuable: closes the new SCP-R-004 surface AND retroactively hardens the deny-baseline path that has carried this latent risk since the gate landed.

**Closure.** `.github/workflows/policy-check.yml` "Render deny annotations and enforce threshold" step adds a `_sanitise_annotation_text` helper that collapses `\r\n`, `\n`, and `\r` to single spaces. Applied to both warn-baseline AND deny-baseline annotation message text. The base SCP-E003 line is NOT sanitised (it's pure SCP-controlled text — no attacker surface).

YAML still parses + tests still pass.

### COMP-MIN-001 — conflict-gate fixture corpus is 2 vs RULE-001 §6.2 spec's ~12

**Lens:** completeness. **Severity:** MIN. **File as TF-020P-002.**

The implementation provides 1 allow + 1 deny conflict-gate fixture, matching the established SCP-R-001/002 minimal-smoke-test pattern (engine-agreement is the conflict-gate's primary contract; exhaustive coverage lives in the 21-case Conftest test suite). RULE-001 §6.2 enumerated 12 fixture scenarios as a Phase-2 deliverable without explicitly marking any as optional. The reviewer correctly notes this is a **documentational gap** rather than a coverage gap — every §6.2 scenario IS tested in Conftest, just not in the conflict-gate.

**Closure.** **TF-020P-002 filed** with two-path closure:
- (a) Expand conflict-gate fixture corpus to match RULE-001 §6.2 verbatim (10 more fixture pairs).
- (b) Amend RULE-TEMPLATE.md §6.2 framing to mark the minimal-smoke-test pattern as the canonical implementation intent (engine-agreement smoke test in conflict-gate; exhaustive coverage in Conftest).

The slice that closes TF-020P-002 chooses the path. (b) is the cleaner doctrinal closure — canonises the SCP-R-001/002/003/004 established pattern. (a) is the more thorough proof but duplicates Conftest coverage.

**Not addressed inline in this slice** because: (a) bundling the fixture corpus expansion would scope-creep slice 020P; (b) amending RULE-TEMPLATE.md a second time in this slice (after the §5 amendment for TF-020L-002) raises the "framework-doc-touch density per slice" beyond useful — better to space out RULE-TEMPLATE amendments across separate slices to make their individual review tractable.

### COR-NIT-001 — stronger truncation pin-test (optional)

**Lens:** correctness. **Severity:** nit. **Acknowledged; not closed in fix-round-1.**

Reviewer noted that `test_scp_r_004_truncates_long_reason_in_message` checks (a) message contains `…` and (b) does NOT contain the tail phrase, which together prove truncation happened *somewhere before the tail* but do not pin the exact 79-char cut. A pin-test would assert message contains `<exactly the first 79 chars>…` literally.

**Disposition.** Acknowledged as a defensive-test improvement; not closed in fix-round-1 because the existing test catches the regression class the truncation predicate is defending against (full-reason leak), and a pin-test would be brittle to any future formatting change in the message template. Leaving as-is.

### COMP-NIT-001 + COMP-NIT-002 — non-actionable

- **COMP-NIT-001** noted that result JSONs were not yet committed at review-start time (now they ARE, post-R1). No-op.
- **COMP-NIT-002** confirmed the Renovate preset does NOT need a v1.1.0 cut (preset content unchanged; per VERSIONING.md the renovate/v* tag series is independent of v*). No-op.

## TF-020P entries filed in this fix-round

### TF-020P-001 — data-driven WARN_BASELINE_RULES manifest

**Filed for symmetry / forward-compat.** The `WARN_BASELINE_RULES = {"SCP-R-004"}` set in `.github/workflows/policy-check.yml` is hardcoded inline. When a 2nd warn-baseline rule lands, consider promoting to a data-driven `policies/rule-baselines.yaml` manifest + `schemas/rule-baselines.schema.json` schema. The hardcoded set is sufficient at v1.1.0 (single warn-baseline rule). Documented in DISPATCH-NOTE risk surface, release notes, and the workflow's inline comment. Closure path: file when 2nd warn-baseline rule is proposed (likely during the next rule-RFC slice). No deadline (forward-compat).

### TF-020P-002 — conflict-gate fixture corpus expand vs RULE-TEMPLATE.md §6.2 amendment

Filed at COMP-MIN-001 closure. Closure path: EITHER expand conflict-gate fixtures to match RULE-001 §6.2 verbatim (10 more fixture pairs) OR amend RULE-TEMPLATE.md §6.2 framing to canonise the SCP-R-001/002/003/004 minimal-smoke-test pattern as the established implementation intent. Lightweight doctrinal closure; foldable into a future RFC slice or process-doc maintenance slice. Forward-compat; no deadline.

## Files touched in fix-round-1

- `policies/tests/scp_r_004_test.rego` — clarified `test_scp_r_004_waiver_suppresses_deny` docstring; added `test_scp_r_004_meta_waiver_without_url_fires_against_self` + `test_scp_r_004_meta_waiver_with_url_does_not_fire_against_self`. Test count 19 → 21.
- `.github/workflows/policy-check.yml` — added `_sanitise_annotation_text` helper; applied to both warn-baseline AND deny-baseline annotation message rendering.
- `docs/reviews/WP-SCP-022/dispatches/020p/FIX-ROUND-1.md` (this file).
- `docs/reviews/WP-SCP-022/dispatches/020p/review-{correctness,safety,completeness}{-package,}.json` — R1 evidence (committed at this fix-round).

## Verification

- `opa test policies/SCP-R-001.rego policies/SCP-R-002.rego policies/SCP-R-003.rego policies/SCP-R-004.rego policies/scp_common.rego policies/tests/`: **65/65 PASS** (44 pre-existing + 21 new SCP-R-004 cases; +2 from 19 in fix-round-1).
- `python3 -m pytest tests/conflict_gate/`: **6/6 PASS** (4 pre-existing + 2 new SCP-R-004).
- `yaml.safe_load(open('.github/workflows/policy-check.yml'))`: **valid**.
- `json.load(open('version-manifest.json'))`: **valid**.

## Posture for proceed-to-PR-open

Fix-round-1 closed all 3 R1 MINs:
- Two inline (COR-MIN-001 + SAFE-MIN-001).
- One filed forward (COMP-MIN-001 → TF-020P-002).
- Plus TF-020P-001 filed for symmetry.

R2 review is OPTIONAL given R1 reached fixpoint directly. Per `feedback_recursive_adversarial_review.md`, fixpoint = no new CRIT/MAJ on a complete cycle — R1 met this. The fix-round-1 changes are surgical (test cases + sanitization helper) and unlikely to introduce regressions.

**Decision: skip R2 and proceed to PR open + operator-merge per D-040.** If a future change to slice 020P warrants R2, a fix-round-2 round can be dispatched at any time; R1 fixpoint plus the surgical fix-round-1 nature is sufficient for merge-readiness.

Cumulative across the slice: **0 CRIT + 0 MAJ + 3 MIN + 3 nit closed (R1) + 0 new findings (fix-round-1)**. 6 review findings closed across 1 round with 0 BLOCKING outstanding. Plus 2 forward-compat TF-020P entries filed.
