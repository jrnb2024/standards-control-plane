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
		"expires_at": "2099-06-30T23:59:59Z",
		"reason": "Temporary compatibility waiver",
		"rule_id": "SCP-R-001",
	}]

	count(scp_r_002_results(input_value)) == 0
}

test_scp_r_002_allows_finding_scoped_waiver if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-28",
		"expires_at": "2099-09-30",
		"finding_id": "F-SVC-003-area-service-signal",
		"reason": "Reviewed exception for fixture coverage",
	}]

	count(scp_r_002_results(input_value)) == 0
}

test_scp_r_002_denies_missing_required_keys_and_identity if {
	input_value := [{"created_at": "2026-04-28T00:00:00Z"}]

	results := scp_r_002_results(input_value)
	count(results) == 4
	summaries := {result.message | some result in results}
	summaries["waiver entry 0 must include approved_by"]
	summaries["waiver entry 0 must include expires_at"]
	summaries["waiver entry 0 must include reason"]
	summaries["waiver entry 0 must include either rule_id or finding_id"]
}

test_scp_r_002_denies_scalar_only_arrays if {
	input_value := ["not-a-waiver"]

	results := scp_r_002_results(input_value)
	count(results) == 1
	results[0].message == "waiver entry 0 must be an object"
}

test_scp_r_002_denies_mixed_array_with_non_object if {
	input_value := [
		{
			"approved_by": "@jrnb2024",
			"created_at": "2026-04-28",
			"expires_at": "2099-09-30",
			"reason": "Reviewed exception for fixture coverage",
			"rule_id": "SCP-R-001",
		},
		"stray-string",
	]

	results := scp_r_002_results(input_value)
	count(results) == 1
	results[0].message == "waiver entry 1 must be an object"
}

test_scp_r_002_denies_invalid_temporal_fields if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026/04/28",
		"expires_at": "not-a-date",
		"reason": "Invalid temporal formats should be rejected",
		"rule_id": "SCP-R-001",
	}]

	results := scp_r_002_results(input_value)
	count(results) == 2
	summaries := {result.message | some result in results}
	summaries["waiver entry 0 created_at must be a valid RFC 3339 date or date-time"]
	summaries["waiver entry 0 expires_at must be a valid RFC 3339 date or date-time"]
}

test_scp_r_002_denies_expired_waivers if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-28",
		"expires_at": "2020-01-01",
		"reason": "Expired waivers must not pass",
		"rule_id": "SCP-R-001",
	}]

	results := scp_r_002_results(input_value)
	count(results) == 1
	results[0].message == "waiver entry 0 expires_at must be in the future"
}
