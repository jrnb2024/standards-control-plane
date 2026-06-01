# WP-SCP-030 Phase B.1 — autonomous-run resume note (scope-extension halt)

**Run:** autonomous Pattern-3 session, dispatch `pattern3-20260531T202644Z-70945`, 2026-05-31.
**Why halted:** the Rego test file must live at `policies/tests/scp_r_030_test.rego` (the CI per-rule coverage gate in `.github/workflows/policy-check.yml` derives this exact path mechanically from the rule basename). That path is **NOT** in the active dispatch's `scope_boundary` — the bootstrap (prompt §0.2) used `tests/policies/test_SCP-R-030*`, a directory that does not exist in this repo (the convention is `policies/tests/`). The acc-hook will deny the write. Per D-057 / prompt §9 the session does **not** work around the hook — it halts for a scope re-bootstrap.

Also note: `opa` / `regal` are **not** in the acc-hook bash allowlist, so rule/test validation is **CI-side only** (the `policy-check` workflow's `opa test --threshold 90` + `regal lint` + `opa fmt --fail` steps). Local `opa test` is not runnable in-session.

---

## Operator action — re-bootstrap with the corrected test path

From a normal terminal (outside the session):

```bash
cd ~/Projects/standards-control-plane
scripts/operator/scp-pattern3-dispatch.sh \
    "policies/SCP-R-030.rego" \
    "policies/scp_common.rego" \
    "schemas/rule-config.schema.json" \
    "policies/tests/scp_r_030_test.rego" \
    "policies/VERSIONING.md" \
    "version-manifest.json" \
    "STATUS.md" \
    "docs/reviews/WP-SCP-030/**"
```

(Drops the non-existent `tests/policies/...` + `tests/conflict_gate/fixtures/SCP-R-030/**` + `policies/rule-config.yaml` + `.scp/rule-config.yaml` entries; adds the real `policies/tests/scp_r_030_test.rego`. No conflict_gate fixture is needed — SCP-R-007/008 ship without one. `.scp/rule-config.yaml` is gitignored estate-wide in the SCP repo, so it is not committable and not needed — see the spec-drift note below.) The script stamps a fresh 4h TTL; the in-session hook reads the new dispatch on the next tool call, so the session can continue in place.

---

## Done this run (in working tree, hook-passed, in scope)

- `schemas/rule-config.schema.json` — `acc-hook-installed` boolean opt-in added (mirrors `acc-cross-repo-caller-scoped`; `additionalProperties:false` preserved).
- `policies/SCP-R-030.rego` — warn-baseline rule, R1-fixpoint (see `r1-dispositions.md`).
- `policies/VERSIONING.md` — `SCP-R-030` added to the warn-baseline register + `WARN_BASELINE_RULES` doc block + enforcement-reach note + D-060 path.
- `version-manifest.json` — v1.3.0 → **v1.4.0** (additive-rule MINOR).
- `docs/BACKLOG.md` — WP-SCP-030 row → Phase B.1 SHIPPED; B.2 pending; D-060 reserved.
- `STATUS.md` — header v1.4.0 line + bottom invocation-log chain entry (with the reach nuance + spec-drift note).
- `docs/reviews/WP-SCP-030/r1-dispositions.md` — 3-lens R1 dispositions (ACCEPT at R-FIXPOINT).

## Remaining after re-bootstrap

1. Write `policies/tests/scp_r_030_test.rego` (full content below).
2. `git checkout -b wp-scp-030-scp-r-030-phase-b` (never commit to main).
3. Stage explicitly + commit + push + `gh pr create`.
4. Verify CI green (`policy-check / scp/policy-check` incl. per-rule `opa test --threshold 90` on SCP-R-030, `regal lint`, `opa fmt`, `check-invocation-log-entry` [passes not-applicable], `r1-evidence-check`). If `opa fmt --fail` flags formatting, apply the diff it reports (in-session can't run `opa fmt`, so first CI run is the formatting oracle).
5. Emit the §6 operator-handoff message + teardown reminder.

---

## SPEC-DRIFT auto-resolutions (Reading-B; low-blast warn-baseline docs domain)

1. **Test path** `tests/policies/` → `policies/tests/scp_r_030_test.rego` (repo convention; CI coverage gate path). Drove this halt.
2. **SCP-self `.scp/rule-config.yaml` opt-in** (prompt §5.3): `.scp/` is gitignored estate-wide in the SCP repo (`.gitignore:6`; only `tests/conflict_gate/fixtures/**/.scp/` negated). A root `.scp/rule-config.yaml` is therefore **not committable** for SCP-self and is moot anyway (the rule reads `input.rule_config`, which the production per-file envelope does not materialise → vacuous-pass until the companion workflow PR — the SCP-R-006 precedent). **SCP-self dogfood = the PASS unit-test fixture** mirroring SCP-self's CLAUDE.md. Adopters (CT/PIM in B.2) commit `.scp/rule-config.yaml acc-hook-installed: true` in THEIR repos (not gitignored there).
3. **Finding shape** follows the SCP-R-008 emission idiom (`{rule_id, file, code, message, remediation_url, msg}`; no `severity`/`line`) over prompt §3.1's illustrative `{rule_id, severity, message, file, line}`. The `code` field carries the finding subtype the §4 matrix asserts on.
4. **`WARN_BASELINE_RULES` membership + input materialisation** deferred to a companion workflow PR (`.github/workflows/policy-check.yml` is gated + out of this dispatch's scope), exactly as SCP-R-006 deferred its workflow wiring. Documented in `VERSIONING.md` + `STATUS.md`.

---

## `policies/tests/scp_r_030_test.rego` — ready-to-drop content

```rego
package main_test

import data.main
import rego.v1

# SCP-R-030 evaluates an aggregate envelope: input.rule_config carries the
# `acc-hook-installed` opt-in (mirrors SCP-R-006); input.claude_md_present +
# input.claude_md carry the CLAUDE.md state (materialised by the companion
# workflow PR). data.rule_config carries the generic disable path; data.waivers
# the waiver path. Until the companion PR materialises input.rule_config, the
# rule vacuously passes in production (SCP-R-006 safe-failure precedent).

scp_r_030_deny(input_value) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
		finding.rule_id == "SCP-R-030"
	]
}

scp_r_030_warn(input_value) := records if {
	records := [record |
		some record in main.warn with input as input_value
		record.rule_id == "SCP-R-030"
	]
}

scp_r_030_deny_full(input_value, waivers, rule_config) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
		finding.rule_id == "SCP-R-030"
	]
}

scp_r_030_warn_full(input_value, waivers, rule_config) := records if {
	records := [record |
		some record in main.warn with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
		record.rule_id == "SCP-R-030"
	]
}

scp_r_030_codes(findings) := {c | some f in findings; c := f.code}

# A fully-conformant preamble (mirrors SCP-self): marker line 1 + the
# always-allowed list + a Pattern-3 ceremony pointer (scripts/) + the
# never-disable rule (reverse "disabl … forbidden" form).
scp_r_030_full_preamble := concat("\n", [
	"<!-- canonical:acc-hook-onboarding v1 -->",
	"# This repo runs the acc-hook (PreToolUse enforcement)",
	"## Always-allowed — write these freely, no ceremony",
	"docs/** · CLAUDE.md · AGENTS.md · .acc/work-packages/**",
	"## Source writes are GATED",
	"Operator runs scripts/operator/scp-pattern3-dispatch.sh before a source session.",
	"## If you trip the hook",
	"Disabling enforcement to get unblocked is forbidden estate-wide (D-057); never disable the hook.",
])

# CT-style variant (LINKAGE-not-VALUES): four-tier Codex "dispatch" ceremony
# with NO scripts/ reference, and the forward "never … disable" form. Proves
# the rule accepts a non-SCP ceremony.
scp_r_030_ct_preamble := concat("\n", [
	"<!-- canonical:acc-hook-onboarding v1 -->",
	"# control-tower runs the acc-hook",
	"## Always-allowed",
	"docs/** and CLAUDE.md are always-allowed.",
	"## Source writes are GATED",
	"Use four-tier Codex dispatch (governed by DEC-054).",
	"## If you trip the hook",
	"You declare scope or ask the operator; you NEVER disable enforcement.",
])

scp_r_030_opted_in_rc := {"acc-hook-installed": true}

# (1) Opted-in, full preamble (mirrors SCP-self) → PASS (no findings). Dogfood.
test_scp_r_030_full_preamble_passes if {
	input_value := {
		"rule_config": scp_r_030_opted_in_rc,
		"claude_md_present": true,
		"claude_md": scp_r_030_full_preamble,
	}
	count(scp_r_030_deny(input_value)) == 0
	count(scp_r_030_warn(input_value)) == 0
}

# (9) CT-style ceremony variant → PASS (accepts non-SCP "dispatch" ceremony +
# forward never-disable). Proves LINKAGE-not-VALUES.
test_scp_r_030_ct_ceremony_variant_passes if {
	input_value := {
		"rule_config": scp_r_030_opted_in_rc,
		"claude_md_present": true,
		"claude_md": scp_r_030_ct_preamble,
	}
	count(scp_r_030_deny(input_value)) == 0
}

# (7) NOT opted-in → vacuous-pass.
test_scp_r_030_not_opted_in_vacuous_pass if {
	input_value := {
		"claude_md_present": true,
		"claude_md": "# no preamble at all",
	}
	count(scp_r_030_deny(input_value)) == 0
	count(scp_r_030_warn(input_value)) == 0
}

# (7b) rule_config present but acc-hook-installed false → vacuous-pass.
test_scp_r_030_opt_in_false_vacuous_pass if {
	input_value := {
		"rule_config": {"acc-hook-installed": false},
		"claude_md_present": true,
		"claude_md": "# no preamble",
	}
	count(scp_r_030_deny(input_value)) == 0
}

# (3) Opted-in, CLAUDE.md absent → warn claude_md_absent.
test_scp_r_030_claude_md_absent if {
	input_value := {
		"rule_config": scp_r_030_opted_in_rc,
		"claude_md_present": false,
	}
	results := scp_r_030_deny(input_value)
	count(results) == 1
	scp_r_030_codes(results) == {"claude_md_absent"}
}

# (2) Opted-in, marker buried below line 3 (top-of-file anchor) → marker_absent.
test_scp_r_030_marker_absent_when_buried if {
	buried := concat("\n", [
		"# Some repo",
		"No marker on the first lines.",
		"Body text.",
		"<!-- canonical:acc-hook-onboarding v1 -->",
		"## Always-allowed",
		"docs/** ; run scripts/dispatch.sh ; never disable the hook.",
	])
	input_value := {
		"rule_config": scp_r_030_opted_in_rc,
		"claude_md_present": true,
		"claude_md": buried,
	}
	results := scp_r_030_deny(input_value)
	count(results) == 1
	scp_r_030_codes(results) == {"marker_absent"}
}

# (2b) Wrong marker version v2 → marker_absent (exact-substring migration gate).
test_scp_r_030_marker_absent_wrong_version if {
	v2 := concat("\n", [
		"<!-- canonical:acc-hook-onboarding v2 -->",
		"## Always-allowed",
		"docs/** ; scripts/dispatch.sh ; never disable.",
	])
	input_value := {
		"rule_config": scp_r_030_opted_in_rc,
		"claude_md_present": true,
		"claude_md": v2,
	}
	scp_r_030_codes(scp_r_030_deny(input_value)) == {"marker_absent"}
}

# (4) Marker present, no always-allowed list → element_missing:always-allowed.
test_scp_r_030_element_missing_always_allowed if {
	content := concat("\n", [
		"<!-- canonical:acc-hook-onboarding v1 -->",
		"# Repo",
		"Run scripts/codex_dispatch.py. Never disable the hook.",
	])
	input_value := {
		"rule_config": scp_r_030_opted_in_rc,
		"claude_md_present": true,
		"claude_md": content,
	}
	results := scp_r_030_deny(input_value)
	count(results) == 1
	scp_r_030_codes(results) == {"element_missing:always-allowed"}
}

# (5) Marker present, no ceremony pointer → element_missing:ceremony.
test_scp_r_030_element_missing_ceremony if {
	content := concat("\n", [
		"<!-- canonical:acc-hook-onboarding v1 -->",
		"## Always-allowed",
		"docs/** write freely.",
		"## Notes",
		"No ceremony reference here. Never disable the hook.",
	])
	input_value := {
		"rule_config": scp_r_030_opted_in_rc,
		"claude_md_present": true,
		"claude_md": content,
	}
	results := scp_r_030_deny(input_value)
	count(results) == 1
	scp_r_030_codes(results) == {"element_missing:ceremony"}
}

# (6) Marker present, no never-disable rule → element_missing:never-disable.
test_scp_r_030_element_missing_never_disable if {
	content := concat("\n", [
		"<!-- canonical:acc-hook-onboarding v1 -->",
		"## Always-allowed",
		"docs/** free; run scripts/dispatch.sh.",
	])
	input_value := {
		"rule_config": scp_r_030_opted_in_rc,
		"claude_md_present": true,
		"claude_md": content,
	}
	results := scp_r_030_deny(input_value)
	count(results) == 1
	scp_r_030_codes(results) == {"element_missing:never-disable"}
}

# (13) Opted-in, claude_md present-but-non-string (null) → content totals to ""
# (CORR-MAJ-001 second clause) → marker_absent.
test_scp_r_030_non_string_content_totals_empty if {
	input_value := {
		"rule_config": scp_r_030_opted_in_rc,
		"claude_md_present": true,
		"claude_md": null,
	}
	scp_r_030_codes(scp_r_030_deny(input_value)) == {"marker_absent"}
}

# (8) Opted-in + marker absent + rules.SCP-R-030.disable: true → 0 deny + warn.
test_scp_r_030_rule_config_disable_suppresses if {
	input_value := {
		"rule_config": scp_r_030_opted_in_rc,
		"claude_md_present": true,
		"claude_md": "# no marker",
	}
	rule_config := {"rules": {"SCP-R-030": {
		"disable": true,
		"justification": "Operator override during onboarding window",
		"expires_at": "2099-12-31T00:00:00Z",
	}}}
	count(scp_r_030_deny_full(input_value, [], rule_config)) == 0
	warns := scp_r_030_warn_full(input_value, [], rule_config)
	count(warns) >= 1
}

# (10) Opted-in + marker absent + active waiver → 0 deny + warn observability.
test_scp_r_030_active_waiver_suppresses if {
	input_value := {
		"rule_config": scp_r_030_opted_in_rc,
		"claude_md_present": true,
		"claude_md": "# no marker",
	}
	waivers := [{
		"waiver_id": "scp-r-030-onboarding-grace",
		"rule_id": "SCP-R-030",
		"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/200",
		"approved_by": "@jrnb2024",
		"created_at": "2026-05-31T00:00:00Z",
		"expires_at": "2099-12-31T00:00:00Z",
	}]
	count(scp_r_030_deny_full(input_value, waivers, {})) == 0
	count(scp_r_030_warn_full(input_value, waivers, {})) >= 1
}
```
