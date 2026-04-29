# SCP Policy Bundle

`policies/**` is the starter Rego bundle shipped by WP-SCP-020 slice `020C`.
`v1.0.0` is intentionally capped at exactly three top-level rules:
`SCP-R-001`, `SCP-R-002`, and `SCP-R-003`. Shared waiver-aware /
rule-config-aware helpers live in `policies/scp_common.rego` and are
loaded into every per-rule `opa test` invocation.

## Rule Template

Per WP-SCP-022 020C.1, every rule must factor potential denies through a
`scp_r_NNN_raw_findings` set, then guard the public `deny` rule with
`not scp_active_waiver_for(...)` and `not scp_rule_config_disabled(...)`,
plus emit `warn` records for waiver- and rule-config-suppressed
findings so observability flows into `policy-check-summary.json`.

Copy this into `policies/<rule-id>.rego`:

```rego
package main

import rego.v1

scp_r_nnn_rule_id := "SCP-R-NNN"
scp_r_nnn_remediation_url := "https://github.com/jrnb2024/standards-control-plane-/blob/main/<path-to-spec>"

# Compute every potential finding into a per-rule raw set.
scp_r_nnn_raw_findings contains finding if {
  violating_condition
  finding := {
    "message": "describe the failing shape in one sentence",
    "rule_id": scp_r_nnn_rule_id,
    "file": "<repo-relative-file>",
    "remediation_url": scp_r_nnn_remediation_url,
  }
}

# Public deny: emits raw findings only when no active waiver and no
# rule-config disable applies. Both helpers are defined in
# policies/scp_common.rego.
deny contains finding if {
  some finding in scp_r_nnn_raw_findings
  not scp_active_waiver_for(scp_r_nnn_rule_id)
  not scp_rule_config_disabled(scp_r_nnn_rule_id)
}

# Observability: emit a kind=waiver record for each matching active
# waiver when there is at least one would-be finding to suppress.
warn contains record if {
  count(scp_r_nnn_raw_findings) > 0
  some w in scp_waivers
  object.get(w, "rule_id", "") == scp_r_nnn_rule_id
  not scp_waiver_expired(w)
  record := {
    "kind": "waiver",
    "rule_id": scp_r_nnn_rule_id,
    "waiver_id": object.get(w, "waiver_id", ""),
    "finding_id": object.get(w, "finding_id", ""),
    "expires_at": object.get(w, "expires_at", ""),
    "file": "<repo-relative-file>",
  }
}

# Observability: emit a kind=rule_config record when the rule-config
# disable applies (regardless of expiry — expired rule-config still
# suppresses for one release; the workflow emits a separate
# ::warning:: annotation in that case).
warn contains record if {
  count(scp_r_nnn_raw_findings) > 0
  scp_rule_config_disabled(scp_r_nnn_rule_id)
  cfg := scp_rule_config_entry(scp_r_nnn_rule_id)
  record := {
    "kind": "rule_config",
    "rule_id": scp_r_nnn_rule_id,
    "reason": "rule-config override",
    "expires_at": object.get(cfg, "expires_at", ""),
  }
}
```

## Fixture Template

Copy this fixture pair and then replace the payload with your rule-specific
allow/deny samples:

```text
policies/testdata/SCP-R-NNN/
├── allow/
│   └── input.yml
└── deny/
    └── input.yml
```

```yaml
# policies/testdata/SCP-R-NNN/allow/input.yml
example: allow
```

```yaml
# policies/testdata/SCP-R-NNN/deny/input.yml
example: deny
```

## Checklist

1. Confirm the rule is in scope for the current release and does not violate the `exactly 3 rules in v1.0.0` invariant unless a later RFC explicitly expands the set.
2. Add `policies/SCP-R-NNN.rego` using `package main`, `import rego.v1`, and prefixed constants such as `scp_r_nnn_rule_id` / `scp_r_nnn_remediation_url`. `package main` is shared across every rule file, so unprefixed names collide.
3. Factor the rule's deny logic through `scp_r_nnn_raw_findings` and guard the public `deny` rule with `not scp_active_waiver_for(...)` and `not scp_rule_config_disabled(...)` per the 020C.1 pattern. Emit `warn` records with `kind=waiver` / `kind=rule_config` for observability. Helpers (`scp_active_waiver_for`, `scp_rule_config_disabled`, `scp_rule_config_entry`, `scp_waivers`, `scp_waiver_expired`) are defined in `policies/scp_common.rego`.
4. Add a deny payload `{message, rule_id, file, remediation_url}` and keep the field names aligned with `schemas/policy-check-summary.schema.json#/properties/findings/items`.
5. Add allow and deny fixtures under `policies/testdata/SCP-R-NNN/`, including both directions for each rule-specific variant you introduce. For waiver/rule-config code paths, add at least one suppressed-by-waiver and one suppressed-by-rule-config fixture per rule.
6. Add `opa test` coverage for the new rule (test file at `policies/tests/scp_r_NNN_test.rego`), include waiver-suppress, expired-waiver, rule-config-disable, and expired-rule-config tests, and keep coverage `>= 90%`. If the rule overlaps with a Python evaluator, also add the shared conflict-gate fixture required by WP-SCP-020 `020C.1`.
7. Run `find policies -type f -name '*.rego' -print0 | xargs -0 opa fmt --fail`, `regal lint --disable directory-package-mismatch --disable no-defined-entrypoint --disable with-outside-test-context --disable unconditional-assignment --disable line-length policies/`, and `opa test policies/ -v --coverage` before opening review.
8. Open the RFC-lite review artifact at `docs/reviews/rule-proposals/RULE-NNN.md` and get the required `CODEOWNERS` review on `policies/**`.

## References

- Deny payload schema: `schemas/policy-check-summary.schema.json#/properties/findings/items`
- Shared helpers: `policies/scp_common.rego` (`scp_active_waiver_for`, `scp_rule_config_disabled`, `scp_rule_config_entry`, `scp_waivers`, `scp_waiver_expired`, `scp_dateish_ns`, `scp_now_ns`)
- CODEOWNERS gate: `CODEOWNERS` (`policies/** @jrnb2024`, `schemas/** @jrnb2024`, `lib/** @jrnb2024`, `.github/workflows/** @jrnb2024`, `tests/conflict_gate/** @jrnb2024`)
- Rule RFC path: `docs/reviews/rule-proposals/RULE-NNN.md`
