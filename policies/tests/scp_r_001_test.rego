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
