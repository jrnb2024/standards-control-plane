package main_test

import data.main
import rego.v1

# Helpers — collect SCP-R-007 deny + warn records, optionally with
# waivers / rule-config / mocked time. Mirrors scp_r_004_test.rego shape.

scp_r_007_results(input_value) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
		finding.rule_id == "SCP-R-007"
	]
}

scp_r_007_results_full(input_value, waivers, rule_config, now_ns) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
			with main.scp_r_007_now_ns as now_ns
			with main.scp_now_ns as now_ns
		finding.rule_id == "SCP-R-007"
	]
}

scp_r_007_warns_full(input_value, waivers, rule_config, now_ns) := records if {
	records := [record |
		some record in main.warn with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
			with main.scp_r_007_now_ns as now_ns
			with main.scp_now_ns as now_ns
		record.rule_id == "SCP-R-007"
	]
}

# Fixed test time anchor — 2026-04-29T00:00:00Z matches scp_r_004_test.rego.
scp_r_007_test_now_ns := time.parse_rfc3339_ns("2026-04-29T00:00:00Z")

# Helpers for date arithmetic in fixtures.
scp_r_007_test_now_str := "2026-04-29T00:00:00Z"

# Mock now_ns for tests that don't need date math.
scp_r_007_with_now(input_value) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
			with main.scp_r_007_now_ns as scp_r_007_test_now_ns
			with main.scp_now_ns as scp_r_007_test_now_ns
		finding.rule_id == "SCP-R-007"
	]
}

# (1) Empty waivers array — no findings.
test_scp_r_007_allows_empty_array if {
	count(scp_r_007_with_now([])) == 0
}

# (2) Single waiver, expires_at = now+30d, window=30d — no findings.
test_scp_r_007_allows_30d_window_30d_future if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29T00:00:00Z",
		"expires_at": "2026-05-29T00:00:00Z",
		"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/42",
		"rule_id": "SCP-R-001",
	}]
	count(scp_r_007_with_now(input_value)) == 0
}

# (3) Single waiver, expires_at = now+89d, window=89d — no findings (boundary).
test_scp_r_007_allows_89d_window_boundary if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29T00:00:00Z",
		"expires_at": "2026-07-27T00:00:00Z",
		"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/42",
		"rule_id": "SCP-R-001",
	}]
	count(scp_r_007_with_now(input_value)) == 0
}

# (4) Single waiver, expires_at = now+91d, window=91d — 1 deny finding (branch b).
test_scp_r_007_denies_91d_window_violation if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29T00:00:00Z",
		"expires_at": "2026-07-29T00:00:00Z",
		"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/42",
		"rule_id": "SCP-R-001",
	}]
	results := scp_r_007_with_now(input_value)
	count(results) == 1
	contains(results[0].message, "window violation")
}

# (5) Single waiver, expires_at = now+200d, window=200d — 1 deny finding (branch b).
test_scp_r_007_denies_200d_window_violation if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29T00:00:00Z",
		"expires_at": "2026-11-15T00:00:00Z",
		"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/42",
		"rule_id": "SCP-R-001",
	}]
	results := scp_r_007_with_now(input_value)
	count(results) == 1
}

# (6) Single waiver, expires_at = now-1d (already expired) — 1 deny finding (branch a).
test_scp_r_007_denies_already_expired_1d if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-01T00:00:00Z",
		"expires_at": "2026-04-28T00:00:00Z",
		"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/42",
		"rule_id": "SCP-R-001",
	}]
	results := scp_r_007_with_now(input_value)
	count(results) == 1
	contains(results[0].message, "already expired")
}

# (7) Single waiver, expires_at = now-30d (long expired) — 1 deny finding (branch a).
test_scp_r_007_denies_already_expired_30d if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-03-01T00:00:00Z",
		"expires_at": "2026-03-30T00:00:00Z",
		"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/42",
		"rule_id": "SCP-R-001",
	}]
	results := scp_r_007_with_now(input_value)
	count(results) == 1
}

# (8) Single waiver, created_at missing — no findings (SCP-R-002 owns shape).
test_scp_r_007_ignores_missing_created_at if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"expires_at": "2026-12-29T00:00:00Z",
		"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/42",
		"rule_id": "SCP-R-001",
	}]

	# expires_at is in the future, no created_at — branch (b) cannot fire
	# (parse_rfc3339_ns of empty string would error), branch (a) doesn't fire
	# (future date). Result: no findings.
	count(scp_r_007_with_now(input_value)) == 0
}

# (9) Single waiver, expires_at malformed RFC3339 — no findings (SCP-R-002 owns shape).
# Note: in Rego, parse_rfc3339_ns on a malformed string fails the body silently;
# no finding emitted.
test_scp_r_007_ignores_malformed_expires_at if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29T00:00:00Z",
		"expires_at": "not-a-date",
		"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/42",
		"rule_id": "SCP-R-001",
	}]
	count(scp_r_007_with_now(input_value)) == 0
}

# (10) 2 waivers — 1 valid + 1 expired — 1 deny finding (the expired one).
test_scp_r_007_per_entry_independence if {
	input_value := [
		{
			"approved_by": "@jrnb2024",
			"created_at": "2026-04-29T00:00:00Z",
			"expires_at": "2026-05-29T00:00:00Z",
			"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/42",
			"rule_id": "SCP-R-001",
		},
		{
			"approved_by": "@jrnb2024",
			"created_at": "2026-03-01T00:00:00Z",
			"expires_at": "2026-03-30T00:00:00Z",
			"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/99",
			"rule_id": "SCP-R-002",
		},
	]
	results := scp_r_007_with_now(input_value)
	count(results) == 1
	contains(results[0].message, "entry 1")
}

# (11) Waiver-with-window-violation + rule-config disable for SCP-R-007 — no findings.
test_scp_r_007_rule_config_disable_suppresses if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29T00:00:00Z",
		"expires_at": "2026-11-15T00:00:00Z",
		"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/42",
		"rule_id": "SCP-R-001",
	}]
	rule_config := {"rules": {"SCP-R-007": {
		"disable": true,
		"justification": "Operator override for window cap",
		"expires_at": "2099-12-31T00:00:00Z",
	}}}
	results := scp_r_007_results_full(input_value, [], rule_config, scp_r_007_test_now_ns)
	count(results) == 0
}

# (12a) Production-default time symbol (no mock) — empty waiver array yields no findings.
# Covers line 31: `scp_r_007_now_ns := time.now_ns()` default path.
test_scp_r_007_production_default_time_empty if {
	# No `with` overrides — uses real time.now_ns() through both
	# scp_r_007_now_ns and scp_now_ns.
	results := [finding |
		some finding in main.deny with input as []
		finding.rule_id == "SCP-R-007"
	]
	count(results) == 0
}

# (12b) Rule-config disable observability warn — verify the warn rule emits a record.
# Covers lines 146-149: warn rule body for rule_config branch.
test_scp_r_007_rule_config_disable_emits_warn if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29T00:00:00Z",
		"expires_at": "2026-11-15T00:00:00Z",
		"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/42",
		"rule_id": "SCP-R-001",
	}]
	rule_config := {"rules": {"SCP-R-007": {
		"disable": true,
		"justification": "Operator override for window cap",
		"expires_at": "2099-12-31T00:00:00Z",
	}}}
	warns := scp_r_007_warns_full(input_value, [], rule_config, scp_r_007_test_now_ns)
	count(warns) >= 1

	# One of the warns should be a rule-config-disable kind.
	some w in warns
	w.kind == "rule-config-disable"
}

# (12) Waiver-with-window-violation + active waiver against SCP-R-007 — no deny + warn.
test_scp_r_007_active_waiver_suppresses if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29T00:00:00Z",
		"expires_at": "2026-11-15T00:00:00Z",
		"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/42",
		"rule_id": "SCP-R-001",
	}]
	waivers := [{
		"waiver_id": "scp-r-007-allow-200d",
		"rule_id": "SCP-R-007",
		"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/100",
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29T00:00:00Z",
		"expires_at": "2026-07-15T00:00:00Z",
	}]
	results := scp_r_007_results_full(input_value, waivers, {}, scp_r_007_test_now_ns)
	count(results) == 0
	warns := scp_r_007_warns_full(input_value, waivers, {}, scp_r_007_test_now_ns)
	count(warns) >= 1
}
