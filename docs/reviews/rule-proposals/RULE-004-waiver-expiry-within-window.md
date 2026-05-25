# RULE-004 — waiver `expires_at` must be within a bounded window AND not already expired

**Status:** DRAFT
**Author:** @jrnb2024
**Filed:** 2026-05-25
**Target release:** v1.3.0 (SCP federation primitive).
**Type:** rule-add
**Quorum required:** 1 (single-operator mode per D-031)
**Review window:** 48h wall-clock CEILING per D-040 (early-merge permitted in single-operator mode when CI green + 3-lens R1 fixpoint).
**Bypass-surface non-empty:** `false` *(no new `.scp/rule-config.yaml` key, no new `scp_bypass:` variant, no new waiver shape; reuses existing waiver-suppression via `data.waivers` for rule SCP-R-007 and existing `.scp/rule-config.yaml disable: true` for SCP-R-007.)*

---

## 1. Summary

Waivers carry an `expires_at` field (required by SCP-R-002 schema). This rule (SCP-R-007) adds the **semantic** check that the field's value is (a) **not in the past** AND (b) **within 90 days of `created_at`** (configurable per-adopter via `.scp/rule-config.yaml` future enhancement). Closes the silent-bypass-by-stale-waiver pattern that SCP-R-002 (schema completeness) + SCP-R-004 (URL citation) leave open.

## 2. Motivation

- **Concrete finding:** SCP-R-002 + SCP-R-004 currently accept a waiver with `expires_at: "2099-12-31T23:59:59Z"` as schema-complete (it has the field; field is non-empty string). The waiver suppresses the deny it was filed against indefinitely. Across the cohort, a long-running waiver becomes a silent bypass because no review cadence forces re-evaluation.
- **Threat model:** an operator (or future automation) authoring a waiver with mistakenly-distant `expires_at` (e.g. typo, copy-paste from another waiver) creates an indefinite bypass that no schema-level rule catches. Companion concern: a STALE waiver (`expires_at < now`) should be a no-op per `scp_common.rego` `scp_waiver_expired` semantics, but operators may not realise the waiver is stale + remove it; the live `waivers.json` accumulates dead entries.
- **Prior conversation:** WP-SCP-025 §3 candidate list 2026-05-09; selected at Phase 1 kickoff 2026-05-25 per WP-SCP-025 v1.0 §3.2.

## 3. Rule specification

### 3.1 Match conditions

Fires per-waiver-entry against `output/findings/waivers.json` (subject to TF-008 path-scoping note in SCP-R-002 — same conftest evaluation envelope) when ALL of:

1. The current evaluation input matches the SCP-R-002 `is_waiver_payload` shape (array of objects).
2. The entry has `created_at` AND `expires_at` as non-empty RFC3339 / date-shaped strings.
3. EITHER:
   - **(a) Already expired:** `expires_at < scp_now_ns`, OR
   - **(b) Window violation:** `(expires_at - created_at) > 90 days` (90 days = 7,776,000,000,000,000 ns).

Note: shape-validation errors (missing `created_at`, malformed RFC3339, etc.) are NOT this rule's concern — SCP-R-002 owns schema completeness. SCP-R-007 only fires on shape-valid waivers whose semantic timing is wrong.

### 3.2 Severity & threshold

- **Initial threshold:** `deny` — LOW false-positive risk (date arithmetic on schema-validated fields; the only legitimate failure mode is an operator-authored waiver with > 90d gap, which is exactly what this rule wants to surface).
- **Adopter override:** existing `.scp/rule-config.yaml disable: true with justification + expires_at` continues to suppress per `schemas/rule-config.schema.json`. Future per-adopter window override (e.g. CT 30-day cap; FLA 180-day cap) is a v1.4.0+ ramp via separate RFC; out of scope for v1.3.0.

### 3.3 Annotation contract

- **Infrastructure error code:** reuses `SCP-E003` (deny) per ADOPT-001 §12.7.7 — no new SCP-EXXX code claimed.
- **Rule-specific annotation:** `::error file=output/findings/waivers.json,title=SCP-R-007::waiver entry %d (rule_id=%s) expires_at %s violates window: <reason>` where `<reason>` is one of:
  - `"already expired (expires_at=%s, now=%s)"`
  - `"window exceeds 90 days (expires_at=%s, created_at=%s, delta=%dd)"`
- **Sibling commit-status text:** waiver-window-violation reported via the `scp/policy-check-readback` summary as `1 SCP-R-007 finding(s)` (~30 chars budget).

### 3.4 Implementation sketch

```rego
package main

import rego.v1

scp_r_007_rule_id := "SCP-R-007"
scp_r_007_remediation_url := concat("", [...])
scp_r_007_window_ns := 7776000000000000  # 90 days in ns
scp_r_007_now_ns := time.now_ns()  # test-mockable

scp_r_007_raw_findings contains finding if {
  is_array(input)
  some index, entry in input
  is_object(entry)
  created_at_str := object.get(entry, "created_at", "")
  expires_at_str := object.get(entry, "expires_at", "")
  created_at_str != ""
  expires_at_str != ""
  created_at_ns := time.parse_rfc3339_ns(created_at_str)
  expires_at_ns := time.parse_rfc3339_ns(expires_at_str)

  # Branch (a): already expired
  expires_at_ns < scp_r_007_now_ns
  finding := { ... }
}

scp_r_007_raw_findings contains finding if {
  ...
  # Branch (b): window violation
  (expires_at_ns - created_at_ns) > scp_r_007_window_ns
  finding := { ... }
}

deny contains output if {
  some finding in scp_r_007_raw_findings
  not scp_active_waiver_for(scp_r_007_rule_id)
  not scp_rule_config_disabled(scp_r_007_rule_id)
  output := object.union(finding, {"msg": finding.message})
}

# warn rules for waiver-suppression observability (SCP-R-002/004 pattern)
warn contains record if { ... }
```

Reuses `scp_common.rego` helpers: `scp_active_waiver_for(rule_id)` + `scp_rule_config_disabled(rule_id)` + `scp_waiver_expired(w)` (the latter as inspiration for the "already expired" branch but reimplemented in SCP-R-007 namespace per the SCP-R-004 SAFE-MAJ-001 closure pattern — i.e., a SCP-R-002 refactor cannot silently break SCP-R-007).

## 4. False-positive surface

- **Legitimate long-running waivers** (>90 days): rare in practice; expected ≤0.5 per 100 PRs. Recommended adopter response: shorten the waiver to ≤90 days at next operator review, OR file an adopter override via `.scp/rule-config.yaml` if the long window is operationally necessary.
- **Cross-tz `expires_at` vs `created_at`:** `time.parse_rfc3339_ns` normalises to UTC; no false positive expected from tz handling.
- **Waiver carried across an SCP version bump:** the rule re-evaluates against `scp_now_ns` at every gate run, so the "already expired" branch may fire on a previously-active waiver that has since aged past `expires_at`. This is the intended catch behavior, not a false positive.

Aggregate expected FP rate: ≤0.5%. Threshold for promotion-blocking: ≤2% (set high so we have headroom; if exceeded, indicates a misconception about the 90-day window).

## 5. Bypass surface

No new bypass surface. Existing suppression mechanisms (active waiver + rule-config disable) apply. The rule's introduction itself is governed by the standard rule-add type (48h CEILING per D-040).

## 6. Test fixtures

### 6.1 Conftest test matrix

Per `tests/policies/SCP-R-007/`:

| # | Fixture | Expected verdict | Tests |
|---|---|---|---|
| 1 | empty waivers array | no findings | allow path |
| 2 | single waiver, expires_at = now+30d, window=30d ✓ | no findings | allow path |
| 3 | single waiver, expires_at = now+89d, window=89d ✓ | no findings | window-boundary |
| 4 | single waiver, expires_at = now+91d, window=91d ✗ | 1 deny finding | window-violation branch (b) |
| 5 | single waiver, expires_at = now+200d, window=200d ✗ | 1 deny finding | window-violation branch (b) |
| 6 | single waiver, expires_at = now-1d (already expired) | 1 deny finding | already-expired branch (a) |
| 7 | single waiver, expires_at = now-30d (long expired) | 1 deny finding | already-expired branch (a) |
| 8 | single waiver, expires_at = now+30d, created_at missing | no findings (SCP-R-002 owns shape) | shape-ignore |
| 9 | single waiver, expires_at malformed RFC3339 | no findings (SCP-R-002 owns shape) | shape-ignore |
| 10 | 2 waivers — 1 valid + 1 expired | 1 deny finding (the expired one) | per-entry independence |
| 11 | waiver with rule-config disable for SCP-R-007 | no findings (rule disabled) | rule-config suppression |
| 12 | waiver-with-window-violation + active waiver for SCP-R-007 | no findings + warn record | waiver suppression |

### 6.2 Per-rule OPA coverage

Target ≥90% per `scripts/scp-pre-push-verify.sh` parity with CI.

## 7. Bake observation + promotion path

- v1.3.0 cut → PIM Renovate auto-PR → ≥1 calendar week observation per WP-SCP-024 invariant 8.
- No promotion needed (already at deny baseline).
- Phase 2 candidate: per-adopter window override via `.scp/rule-config.yaml` extension (v1.4.0+).

## 8. Open questions

None at filing time — operator-attended ratification 2026-05-25 locked all decision points.
