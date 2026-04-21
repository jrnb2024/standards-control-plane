# SCP Policy Bundle

**Status:** Stub — populated in WP-SCP-020 slice 020C.
**Plan:** `docs/plans/WP-SCP-020-policy-federation-primitive.md`.

This directory will hold the Rego policy bundle that SCP's federation
primitive evaluates at PR time. Rego rules handle fast shape-checks; the
existing Python evaluators (`evaluators/service_lifecycle.py` etc.) remain
the deep-audit path.

## Contents (when slice 020C lands)

- `SCP-R-001.rego` — `services.yml` root-shape SVC-003 mode-set conformance.
- `SCP-R-002.rego` — `waivers.json` entry schema.
- `SCP-R-003.rego` — ADOPT-001 §11 vendoring-manifest marker presence.
- `testdata/<rule-id>/{allow,deny}.{yml,json}` — fixture corpus per rule.
- `VERSIONING.md` — semver contract on inputs, JSON summary schema, rule
  IDs; rule-RFC process; rollback detection.

## Contributor checklist (placeholder — expanded in 020C)

When adding a new rule:

1. Draft `docs/reviews/rule-proposals/RULE-NNN.md` per VERSIONING.md §RFC.
2. Author `policies/SCP-R-NNN.rego`.
3. Emit `deny` payload shape `{rule_id, message, remediation_url}`.
4. Add allow + deny fixtures under `testdata/SCP-R-NNN/`.
5. Add conflict-gate fixture at `tests/conflict_gate/fixtures/SCP-R-NNN/`
   if the rule overlaps with a Python evaluator.
6. Run `opa fmt --fail`, `regal lint`, `opa test`.
7. Open PR; 1 SCP-CODEOWNER approval after 48h wall-clock review = eligible.

Rule-ID scheme: `SCP-R-NNN` (zero-padded, 3 digits).

CODEOWNERS review is required on any change inside `policies/**`.
