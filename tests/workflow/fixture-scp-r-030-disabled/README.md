<!-- not the adopter CLAUDE.md; .md is skipped by the conftest per-file pass -->
# fixture-scp-r-030-disabled

WP-SCP-030 companion-activation selftest fixture — **row 5** of the SPEC §6 matrix
(opted-in, marker absent, but `rules.SCP-R-030.disable: true` → **vacuous-pass**).

Proves the `.scp/rule-config.yaml` disable path still suppresses through the NEW
repo-level `opa eval` pass: suppression is enforced INSIDE `data.main.deny`
(`not scp_rule_config_disabled`), which reads `data.rule_config` — so even though
the CLAUDE.md would otherwise fire `marker_absent`, no deny is produced and the
summary carries no SCP-R-030 finding. This is a safety_bypass-relevant assertion:
the auditable + expiring reversible path is intact under Option A.

- `rule-config.yaml` — `acc-hook-installed: true` AND `rules.SCP-R-030.disable: true`
  (with the schema-required `justification` + `expires_at`).
- `repo/CLAUDE.md` — present, marker absent (would fire `marker_absent` if not disabled).
- `expected-annotations.json` — `findings: []` (deny suppressed); gate green.
