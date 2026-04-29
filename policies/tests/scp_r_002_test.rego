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

# Closes WP-SCP-022 R2 F-R2-COR-002: non-array waivers.json must deny.
test_scp_r_002_denies_non_array_object if {
	input_value := {"approved_by": "@jrnb2024"}

	results := scp_r_002_results(input_value)
	count(results) == 1
	results[0].message == "waivers.json root must be a JSON array of waiver entry objects"
}

test_scp_r_002_denies_non_array_null if {
	results := scp_r_002_results(null)
	count(results) == 1
	results[0].message == "waivers.json root must be a JSON array of waiver entry objects"
}

test_scp_r_002_denies_non_array_string if {
	results := scp_r_002_results("not-an-array")
	count(results) == 1
	results[0].message == "waivers.json root must be a JSON array of waiver entry objects"
}

# Closes WP-SCP-022 R2 F-R2-COR-003 / R2-SAF-MAJ-01: array-of-empty-objects
# previously bypassed all per-entry deny rules because the payload
# detector required at least one recognised key. Now any non-empty array
# is a waiver payload; per-entry rules fire and catch missing fields.
test_scp_r_002_denies_array_of_empty_objects if {
	input_value := [{}, {"custom_key": "x"}]

	results := scp_r_002_results(input_value)

	# Each entry should fire required-keys + identity-key rules
	# (4 required keys × 2 entries = 8) + (1 identity rule × 2 entries = 2)
	# = 10 deny findings. Check we get strictly more than 0 (the bypass
	# was 0 findings) and that both entries are individually flagged.
	count(results) > 0
	flagged_entry_0 := [r | some r in results; contains(r.message, "entry 0")]
	flagged_entry_1 := [r | some r in results; contains(r.message, "entry 1")]
	count(flagged_entry_0) > 0
	count(flagged_entry_1) > 0
}

# WP-SCP-022 slice 020C.1: waiver-aware + rule-config-aware test helpers.
scp_r_002_results_full(input_value, waivers, rule_config, now_ns) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
			with main.scp_now_ns as now_ns
			with main.scp_r_002_now_ns as now_ns
		finding.rule_id == "SCP-R-002"
	]
}

scp_r_002_warns_full(input_value, waivers, rule_config, now_ns) := records if {
	records := [record |
		some record in main.warn with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
			with main.scp_now_ns as now_ns
			with main.scp_r_002_now_ns as now_ns
		record.rule_id == "SCP-R-002"
	]
}

scp_r_002_invalid_input := "not-an-array"

scp_r_002_test_now_ns := time.parse_rfc3339_ns("2026-04-29T00:00:00Z")

# (i) waiver-suppression: a matching active waiver suppresses the deny
# and emits a kind=waiver warn record.
test_scp_r_002_waiver_suppresses_deny if {
	# Uses date-time expires_at to exercise scp_dateish_ns date-time branch.
	waivers := [{
		"waiver_id": "W-WAIVERS-FILE",
		"rule_id": "SCP-R-002",
		"expires_at": "2099-12-31T23:59:59Z",
		"reason": "test",
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29",
	}]
	count(scp_r_002_results_full(scp_r_002_invalid_input, waivers, {}, scp_r_002_test_now_ns)) == 0
	warns := scp_r_002_warns_full(scp_r_002_invalid_input, waivers, {}, scp_r_002_test_now_ns)
	count(warns) == 1
	warns[0].kind == "waiver"
	warns[0].waiver_id == "W-WAIVERS-FILE"
}

# (i) expired waiver does NOT suppress.
test_scp_r_002_expired_waiver_does_not_suppress if {
	waivers := [{
		"waiver_id": "W-EXPIRED",
		"rule_id": "SCP-R-002",
		"expires_at": "2020-01-01",
		"reason": "test",
		"approved_by": "@jrnb2024",
		"created_at": "2019-01-01",
	}]
	results := scp_r_002_results_full(scp_r_002_invalid_input, waivers, {}, scp_r_002_test_now_ns)
	count(results) == 1
	warns := scp_r_002_warns_full(scp_r_002_invalid_input, waivers, {}, scp_r_002_test_now_ns)
	count(warns) == 0
}

# (v) rule-config disable suppresses the deny and emits a kind=rule_config warn.
test_scp_r_002_rule_config_disable_suppresses_deny if {
	rule_config := {"rules": {"SCP-R-002": {
		"disable": true,
		"justification": "test override",
		"expires_at": "2099-12-31",
	}}}
	count(scp_r_002_results_full(scp_r_002_invalid_input, [], rule_config, scp_r_002_test_now_ns)) == 0
	warns := scp_r_002_warns_full(scp_r_002_invalid_input, [], rule_config, scp_r_002_test_now_ns)
	count(warns) == 1
	warns[0].kind == "rule_config"
	warns[0].reason == "rule-config override"
}

# (v) expired rule-config disable still suppresses for one release.
test_scp_r_002_expired_rule_config_still_suppresses if {
	rule_config := {"rules": {"SCP-R-002": {
		"disable": true,
		"justification": "stale override",
		"expires_at": "2020-01-01",
	}}}
	count(scp_r_002_results_full(scp_r_002_invalid_input, [], rule_config, scp_r_002_test_now_ns)) == 0
	warns := scp_r_002_warns_full(scp_r_002_invalid_input, [], rule_config, scp_r_002_test_now_ns)
	count(warns) == 1
	warns[0].kind == "rule_config"
}

# Coverage: scp_waiver_expired body 1 — missing/empty expires_at.
test_scp_r_002_waiver_with_missing_expires_at_does_not_suppress if {
	waivers := [{
		"waiver_id": "W-NO-EXPIRY",
		"rule_id": "SCP-R-002",
		"reason": "missing expires_at — must fail closed",
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29",
	}]
	results := scp_r_002_results_full(scp_r_002_invalid_input, waivers, {}, scp_r_002_test_now_ns)
	count(results) == 1
	warns := scp_r_002_warns_full(scp_r_002_invalid_input, waivers, {}, scp_r_002_test_now_ns)
	count(warns) == 0
}

# Coverage: scp_waiver_expired body 2 — malformed (unparseable) expires_at.
test_scp_r_002_waiver_with_malformed_expires_at_does_not_suppress if {
	waivers := [{
		"waiver_id": "W-BAD-DATE",
		"rule_id": "SCP-R-002",
		"expires_at": "not-a-date",
		"reason": "malformed expires_at — must fail closed",
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29",
	}]
	results := scp_r_002_results_full(scp_r_002_invalid_input, waivers, {}, scp_r_002_test_now_ns)
	count(results) == 1
	warns := scp_r_002_warns_full(scp_r_002_invalid_input, waivers, {}, scp_r_002_test_now_ns)
	count(warns) == 0
}
