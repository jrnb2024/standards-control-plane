package main_test

import data.main
import rego.v1

scp_r_001_results(input_value) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
		finding.rule_id == "SCP-R-001"
	]
}

scp_r_001_results_at(input_value, now_ns) := results if {
	results := [finding |
		some finding in main.deny with input as input_value with main.scp_r_001_now_ns as now_ns
		finding.rule_id == "SCP-R-001"
	]
}

test_scp_r_001_allows_canonical_svc_003_shape if {
	input_value := {"services": {"scp": {"local": {"runtime_contract": {"auth_contract": {"accepted_modes": [
		{"mode": "mode.user_oidc"},
		{
			"mode": "mode.bearer_legacy",
			"deprecation_close_date": "2026-06-30",
		},
	]}}}}}}

	count(scp_r_001_results_at(input_value, time.parse_rfc3339_ns("2026-01-01T00:00:00Z"))) == 0
}

test_scp_r_001_allows_simplified_auth_shape if {
	input_value := {"services": {"api": {"auth": {"mode": "mode.api_key"}}}}

	count(scp_r_001_results(input_value)) == 0
}

test_scp_r_001_denies_unknown_mode if {
	input_value := {"services": {"scp": {"local": {"runtime_contract": {"auth_contract": {"accepted_modes": [{"mode": "mode.custom"}]}}}}}}

	results := scp_r_001_results(input_value)
	count(results) == 1
	contains(results[0].message, "must use an approved SVC-003 mode")
}

test_scp_r_001_denies_invalid_bearer_legacy_close_date if {
	input_value := {"services": {"scp": {"local": {"runtime_contract": {"auth_contract": {"accepted_modes": [{
		"mode": "mode.bearer_legacy",
		"deprecation_close_date": "2026-12-31",
	}]}}}}}}

	results := scp_r_001_results(input_value)
	count(results) == 1
	contains(results[0].message, "deprecation_close_date")
}

test_scp_r_001_denies_flat_auth_unknown_mode if {
	input_value := {"services": {"svc": {"auth": {"mode": "mode.proprietary"}}}}

	results := scp_r_001_results(input_value)
	count(results) == 1
	contains(results[0].message, "approved SVC-003 mode")
}

test_scp_r_001_denies_flat_auth_bearer_legacy_invalid_date if {
	input_value := {"services": {"svc": {"auth": {
		"mode": "mode.bearer_legacy",
		"deprecation_close_date": "2026-03-01",
	}}}}

	results := scp_r_001_results(input_value)
	count(results) == 1
	contains(results[0].message, "deprecation_close_date")
}

test_scp_r_001_denies_non_object_mode_entry if {
	input_value := {"services": {"svc": {"prod": {"runtime_contract": {"auth_contract": {"accepted_modes": ["plain-string"]}}}}}}

	results := scp_r_001_results(input_value)
	count(results) == 1
	contains(results[0].message, "must be an object with a mode field")
}

test_scp_r_001_denies_past_bearer_legacy_close_date if {
	input_value := {"services": {"scp": {"local": {"runtime_contract": {"auth_contract": {"accepted_modes": [{
		"mode": "mode.bearer_legacy",
		"deprecation_close_date": "2026-06-30",
	}]}}}}}}

	results := scp_r_001_results_at(input_value, time.parse_rfc3339_ns("2026-07-01T00:00:00Z"))
	count(results) == 1
	contains(results[0].message, "must not be in the past")
}

# WP-SCP-022 slice 020C.1: waiver-aware + rule-config-aware test helpers.
scp_r_001_results_full(input_value, waivers, rule_config, now_ns) := results if {
	results := [finding |
		some finding in main.deny
			with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
			with main.scp_now_ns as now_ns
		finding.rule_id == "SCP-R-001"
	]
}

scp_r_001_warns_full(input_value, waivers, rule_config, now_ns) := records if {
	records := [record |
		some record in main.warn
			with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
			with main.scp_now_ns as now_ns
		record.rule_id == "SCP-R-001"
	]
}

scp_r_001_unknown_mode_input := {"services": {"scp": {"local": {"runtime_contract": {"auth_contract": {"accepted_modes": [{"mode": "mode.custom"}]}}}}}}

scp_r_001_test_now_ns := time.parse_rfc3339_ns("2026-04-29T00:00:00Z")

# (i) waiver-suppression: a matching active waiver suppresses the deny
# and emits a kind=waiver warn record.
test_scp_r_001_waiver_suppresses_deny if {
	# Uses date-time expires_at to exercise scp_dateish_ns date-time branch.
	waivers := [{
		"waiver_id": "W-2026-001",
		"rule_id": "SCP-R-001",
		"expires_at": "2099-12-31T23:59:59Z",
		"reason": "test",
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29",
	}]
	count(scp_r_001_results_full(scp_r_001_unknown_mode_input, waivers, {}, scp_r_001_test_now_ns)) == 0
	warns := scp_r_001_warns_full(scp_r_001_unknown_mode_input, waivers, {}, scp_r_001_test_now_ns)
	count(warns) == 1
	warns[0].kind == "waiver"
	warns[0].waiver_id == "W-2026-001"
	warns[0].expires_at == "2099-12-31T23:59:59Z"
}

# (i) expired waiver does NOT suppress: deny still fires, no waiver warn.
test_scp_r_001_expired_waiver_does_not_suppress if {
	waivers := [{
		"waiver_id": "W-EXPIRED",
		"rule_id": "SCP-R-001",
		"expires_at": "2020-01-01",
		"reason": "test",
		"approved_by": "@jrnb2024",
		"created_at": "2019-01-01",
	}]
	results := scp_r_001_results_full(scp_r_001_unknown_mode_input, waivers, {}, scp_r_001_test_now_ns)
	count(results) == 1
	warns := scp_r_001_warns_full(scp_r_001_unknown_mode_input, waivers, {}, scp_r_001_test_now_ns)
	count(warns) == 0
}

# (v) rule-config disable suppresses the deny and emits a kind=rule_config warn.
test_scp_r_001_rule_config_disable_suppresses_deny if {
	rule_config := {"rules": {"SCP-R-001": {
		"disable": true,
		"justification": "test override",
		"expires_at": "2099-12-31",
	}}}
	count(scp_r_001_results_full(scp_r_001_unknown_mode_input, [], rule_config, scp_r_001_test_now_ns)) == 0
	warns := scp_r_001_warns_full(scp_r_001_unknown_mode_input, [], rule_config, scp_r_001_test_now_ns)
	count(warns) == 1
	warns[0].kind == "rule_config"
	warns[0].reason == "rule-config override"
	warns[0].expires_at == "2099-12-31"
}

# (v) expired rule-config disable still suppresses for one release; the
# expiry-warning annotation is emitted at the workflow layer (not here).
test_scp_r_001_expired_rule_config_still_suppresses if {
	rule_config := {"rules": {"SCP-R-001": {
		"disable": true,
		"justification": "stale override",
		"expires_at": "2020-01-01",
	}}}
	count(scp_r_001_results_full(scp_r_001_unknown_mode_input, [], rule_config, scp_r_001_test_now_ns)) == 0
	warns := scp_r_001_warns_full(scp_r_001_unknown_mode_input, [], rule_config, scp_r_001_test_now_ns)
	count(warns) == 1
	warns[0].kind == "rule_config"
}

# Coverage: scp_waiver_expired body 1 — missing/empty expires_at.
test_scp_r_001_waiver_with_missing_expires_at_does_not_suppress if {
	waivers := [{
		"waiver_id": "W-NO-EXPIRY",
		"rule_id": "SCP-R-001",
		"reason": "missing expires_at — must fail closed",
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29",
	}]
	results := scp_r_001_results_full(scp_r_001_unknown_mode_input, waivers, {}, scp_r_001_test_now_ns)
	count(results) == 1
	warns := scp_r_001_warns_full(scp_r_001_unknown_mode_input, waivers, {}, scp_r_001_test_now_ns)
	count(warns) == 0
}

# Coverage: scp_waiver_expired body 2 — malformed (unparseable) expires_at.
test_scp_r_001_waiver_with_malformed_expires_at_does_not_suppress if {
	waivers := [{
		"waiver_id": "W-BAD-DATE",
		"rule_id": "SCP-R-001",
		"expires_at": "not-a-date",
		"reason": "malformed expires_at — must fail closed",
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29",
	}]
	results := scp_r_001_results_full(scp_r_001_unknown_mode_input, waivers, {}, scp_r_001_test_now_ns)
	count(results) == 1
	warns := scp_r_001_warns_full(scp_r_001_unknown_mode_input, waivers, {}, scp_r_001_test_now_ns)
	count(warns) == 0
}
