package main_test

import data.main
import rego.v1

scp_r_001_results(input_value) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
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

	count(scp_r_001_results(input_value)) == 0
}

test_scp_r_001_allows_simplified_auth_shape if {
	input_value := {"services": {"api": {"auth": {"mode": "mode.api_key"}}}}

	count(scp_r_001_results(input_value)) == 0
}

test_scp_r_001_denies_unknown_mode if {
	input_value := {"services": {"scp": {"local": {"runtime_contract": {"auth_contract": {"accepted_modes": [{"mode": "mode.custom"}]}}}}}}

	results := scp_r_001_results(input_value)
	count(results) == 1
	contains(results[0].msg, "must use an approved SVC-003 mode")
}

test_scp_r_001_denies_invalid_bearer_legacy_close_date if {
	input_value := {"services": {"scp": {"local": {"runtime_contract": {"auth_contract": {"accepted_modes": [{
		"mode": "mode.bearer_legacy",
		"deprecation_close_date": "2026-12-31",
	}]}}}}}}

	results := scp_r_001_results(input_value)
	count(results) == 1
	contains(results[0].msg, "deprecation_close_date")
}
