# SCP Policy Bundle

`policies/**` is the starter Rego bundle shipped by WP-SCP-020 slice `020C`.
`v1.0.0` is intentionally capped at exactly three top-level rules:
`SCP-R-001`, `SCP-R-002`, and `SCP-R-003`.

## Rule Template

Copy this into `policies/<rule-id>.rego`:

```rego
package main

import rego.v1

scp_r_nnn_rule_id := "SCP-R-NNN"
scp_r_nnn_remediation_url := "https://github.com/jrnb2024/standards-control-plane-/blob/main/<path-to-spec>"

deny contains {
  "message": message,
  "rule_id": scp_r_nnn_rule_id,
  "file": "<repo-relative-file>",
  "remediation_url": scp_r_nnn_remediation_url,
} if {
  violating_condition
  message := "describe the failing shape in one sentence"
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
3. Add a `deny contains {message, rule_id, file, remediation_url}` payload and keep the field names aligned with `schemas/policy-check-summary.schema.json#/properties/findings/items`.
4. Add allow and deny fixtures under `policies/testdata/SCP-R-NNN/`, including both directions for each rule-specific variant you introduce.
5. Add `opa test` coverage for the new rule and keep that rule at `>= 90%` coverage. If the rule overlaps with a Python evaluator, also add the shared conflict-gate fixture required by WP-SCP-020 `020C.1`.
6. Run `find policies -type f -name '*.rego' -print0 | xargs -0 opa fmt --fail`, `regal lint --disable directory-package-mismatch --disable no-defined-entrypoint --disable with-outside-test-context --disable unconditional-assignment --disable line-length policies/`, and `opa test policies/ -v --coverage` before opening review.
7. Open the RFC-lite review artifact at `docs/reviews/rule-proposals/RULE-NNN.md` and get the required `CODEOWNERS` review on `policies/**`.

## References

- Deny payload schema: `schemas/policy-check-summary.schema.json#/properties/findings/items`
- CODEOWNERS gate: `CODEOWNERS` (`policies/** @jrnb2024`)
- Rule RFC path: `docs/reviews/rule-proposals/RULE-NNN.md`
