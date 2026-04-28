package main_test

import data.main
import rego.v1

scp_r_002_results(input_value) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
		finding.rule_id == "SCP-R-002"
	]
}

test_scp_r_002_allows_rule_scoped_waiver if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-28T00:00:00Z",
		"expires_at": "2026-06-30T23:59:59Z",
		"rule_id": "SCP-R-001",
	}]

	count(scp_r_002_results(input_value)) == 0
}

test_scp_r_002_allows_finding_scoped_waiver if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-28",
		"expires_at": "2026-09-30",
		"finding_id": "F-SVC-003-area-service-signal",
	}]

	count(scp_r_002_results(input_value)) == 0
}

test_scp_r_002_denies_missing_required_keys_and_identity if {
	input_value := [{"created_at": "2026-04-28T00:00:00Z"}]

	results := scp_r_002_results(input_value)
	count(results) == 3
	summaries := {result.msg | some result in results}
	summaries["waiver entry 0 must include approved_by"]
	summaries["waiver entry 0 must include expires_at"]
	summaries["waiver entry 0 must include either rule_id or finding_id"]
}

test_scp_r_002_ignores_non_waiver_arrays if {
	input_value := ["not-a-waiver"]

	count(scp_r_002_results(input_value)) == 0
}
