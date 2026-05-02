package main_test

import data.main
import rego.v1

# Helpers — collect SCP-R-004 deny + warn records, optionally with
# waivers / rule-config / mocked time. Mirrors scp_r_002_test.rego shape.

scp_r_004_results(input_value) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
		finding.rule_id == "SCP-R-004"
	]
}

scp_r_004_results_full(input_value, waivers, rule_config, now_ns) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
			with main.scp_now_ns as now_ns
		finding.rule_id == "SCP-R-004"
	]
}

scp_r_004_warns_full(input_value, waivers, rule_config, now_ns) := records if {
	records := [record |
		some record in main.warn with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
			with main.scp_now_ns as now_ns
		record.rule_id == "SCP-R-004"
	]
}

scp_r_004_test_now_ns := time.parse_rfc3339_ns("2026-04-29T00:00:00Z")

# (1) Empty waivers payload — no findings.
test_scp_r_004_allows_empty_array if {
	count(scp_r_004_results([])) == 0
}

# (2) Single waiver with GitHub issue URL — no findings.
test_scp_r_004_allows_single_waiver_with_github_issue_url if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-28T00:00:00Z",
		"expires_at": "2099-06-30T23:59:59Z",
		"reason": "Approved per https://github.com/jrnb2024/standards-control-plane-/issues/42 — investigation pending",
		"rule_id": "SCP-R-001",
	}]
	count(scp_r_004_results(input_value)) == 0
}

# (3) Single waiver with non-GitHub URL — no findings (estate-flexibility).
test_scp_r_004_allows_single_waiver_with_non_github_url if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-28T00:00:00Z",
		"expires_at": "2099-06-30T23:59:59Z",
		"reason": "See https://linear.app/team/issue/ABC-123 for tracker",
		"rule_id": "SCP-R-001",
	}]
	count(scp_r_004_results(input_value)) == 0
}

# (4) Multi-waiver, all with URLs — no findings.
test_scp_r_004_allows_multi_waiver_all_with_urls if {
	input_value := [
		{
			"approved_by": "@jrnb2024",
			"created_at": "2026-04-28T00:00:00Z",
			"expires_at": "2099-06-30T23:59:59Z",
			"reason": "https://github.com/jrnb2024/standards-control-plane-/issues/42",
			"rule_id": "SCP-R-001",
		},
		{
			"approved_by": "@jrnb2024",
			"created_at": "2026-04-28T00:00:00Z",
			"expires_at": "2099-06-30T23:59:59Z",
			"reason": "Per design discussion in https://github.com/jrnb2024/standards-control-plane-/pull/78",
			"rule_id": "SCP-R-002",
		},
		{
			"approved_by": "@jrnb2024",
			"created_at": "2026-04-28T00:00:00Z",
			"expires_at": "2099-06-30T23:59:59Z",
			"reason": "Ratified per D-022 — see https://github.com/jrnb2024/standards-control-plane-/blob/main/docs/DECISIONS.md",
			"finding_id": "F-XYZ",
		},
	]
	count(scp_r_004_results(input_value)) == 0
}

# (5) Single waiver without URL — fires.
test_scp_r_004_denies_single_waiver_no_url if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-28T00:00:00Z",
		"expires_at": "2099-06-30T23:59:59Z",
		"reason": "approved by Jim",
		"rule_id": "SCP-R-001",
	}]
	results := scp_r_004_results(input_value)
	count(results) == 1
	# Annotation message contract per RULE-001 §3.3 — verify shape.
	contains(results[0].message, "SCP-R-004 waiver entry 0")
	contains(results[0].message, "rule_id=SCP-R-001")
	contains(results[0].message, "approved by Jim")
}

# (5b) Bare domain without scheme — should fire (regex requires https?://).
test_scp_r_004_denies_single_waiver_with_bare_domain if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-28T00:00:00Z",
		"expires_at": "2099-06-30T23:59:59Z",
		"reason": "see github.com for context",
		"rule_id": "SCP-R-001",
	}]
	count(scp_r_004_results(input_value)) == 1
}

# (6) Multi-waiver, mixed — fires twice (one per missing-URL entry).
test_scp_r_004_denies_multi_waiver_mixed if {
	input_value := [
		{
			"approved_by": "@jrnb2024",
			"created_at": "2026-04-28T00:00:00Z",
			"expires_at": "2099-06-30T23:59:59Z",
			"reason": "approved by Jim",
			"rule_id": "SCP-R-001",
		},
		{
			"approved_by": "@jrnb2024",
			"created_at": "2026-04-28T00:00:00Z",
			"expires_at": "2099-06-30T23:59:59Z",
			"reason": "https://github.com/jrnb2024/standards-control-plane-/issues/99",
			"rule_id": "SCP-R-002",
		},
		{
			"approved_by": "@jrnb2024",
			"created_at": "2026-04-28T00:00:00Z",
			"expires_at": "2099-06-30T23:59:59Z",
			"reason": "discussed in slack — url tomorrow",
			"finding_id": "F-XYZ",
		},
	]
	results := scp_r_004_results(input_value)
	count(results) == 2
}

# (7-9) No-op on object/string/null inputs (path-scope guard).
test_scp_r_004_no_op_on_object_rooted_input if {
	count(scp_r_004_results({"not": "a waivers payload"})) == 0
}

test_scp_r_004_no_op_on_string_rooted_input if {
	count(scp_r_004_results("some text")) == 0
}

test_scp_r_004_no_op_on_null_input if {
	count(scp_r_004_results(null)) == 0
}

# (10) No-op on waiver missing `reason` field — SCP-R-002 covers; SCP-R-004 must not double-fire.
test_scp_r_004_no_op_on_waiver_with_reason_absent if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-28T00:00:00Z",
		"expires_at": "2099-06-30T23:59:59Z",
		"rule_id": "SCP-R-001",
	}]
	count(scp_r_004_results(input_value)) == 0
}

# (11) No-op on waiver with empty `reason` — SCP-R-002 covers; SCP-R-004 must not double-fire.
test_scp_r_004_no_op_on_waiver_with_empty_reason if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-28T00:00:00Z",
		"expires_at": "2099-06-30T23:59:59Z",
		"reason": "",
		"rule_id": "SCP-R-001",
	}]
	count(scp_r_004_results(input_value)) == 0
}

# (12) URL-bearing meta-waiver against SCP-R-004 itself suppresses the deny.
# Closes RULE-001 §5 third-bullet operational note (SAFE-MIN-001 closure).
test_scp_r_004_waiver_suppresses_deny if {
	# Input under evaluation: a no-URL waiver entry that would otherwise fire.
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-28T00:00:00Z",
		"expires_at": "2099-06-30T23:59:59Z",
		"reason": "approved by Jim",
		"rule_id": "SCP-R-001",
	}]
	# Active waiver against SCP-R-004 itself — its OWN reason MUST contain a URL
	# otherwise the meta-waiver is also a raw finding for SCP-R-004 (per RULE-001 §5).
	waivers := [{
		"waiver_id": "W-SCP-R-004-META",
		"rule_id": "SCP-R-004",
		"expires_at": "2099-12-31T23:59:59Z",
		"reason": "Waiving SCP-R-004 for legacy waivers per https://github.com/jrnb2024/standards-control-plane-/issues/100 transition window",
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29",
	}]
	count(scp_r_004_results_full(input_value, waivers, {}, scp_r_004_test_now_ns)) == 0
	warns := scp_r_004_warns_full(input_value, waivers, {}, scp_r_004_test_now_ns)
	count(warns) == 1
	warns[0].kind == "waiver"
	warns[0].waiver_id == "W-SCP-R-004-META"
}

# (12b) Expired waiver against SCP-R-004 does NOT suppress (fail-closed).
test_scp_r_004_expired_waiver_does_not_suppress if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-28T00:00:00Z",
		"expires_at": "2099-06-30T23:59:59Z",
		"reason": "approved by Jim",
		"rule_id": "SCP-R-001",
	}]
	waivers := [{
		"waiver_id": "W-EXPIRED",
		"rule_id": "SCP-R-004",
		"expires_at": "2020-01-01",
		"reason": "expired waiver — see https://github.com/jrnb2024/standards-control-plane-/issues/1",
		"approved_by": "@jrnb2024",
		"created_at": "2019-01-01",
	}]
	results := scp_r_004_results_full(input_value, waivers, {}, scp_r_004_test_now_ns)
	count(results) == 1
}

# (13) `.scp/rule-config.yaml` disable suppresses the deny + emits rule_config warn.
test_scp_r_004_rule_config_disable_suppresses_deny if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-28T00:00:00Z",
		"expires_at": "2099-06-30T23:59:59Z",
		"reason": "approved by Jim",
		"rule_id": "SCP-R-001",
	}]
	rule_config := {"rules": {"SCP-R-004": {
		"disable": true,
		"justification": "transition window — amending legacy waivers to include URLs",
		"expires_at": "2099-12-31",
	}}}
	count(scp_r_004_results_full(input_value, [], rule_config, scp_r_004_test_now_ns)) == 0
	warns := scp_r_004_warns_full(input_value, [], rule_config, scp_r_004_test_now_ns)
	count(warns) == 1
	warns[0].kind == "rule_config"
	warns[0].reason == "rule-config override"
}

# (13b) Expired rule-config disable still suppresses for one release (matches SCP-R-002 behaviour).
test_scp_r_004_expired_rule_config_still_suppresses if {
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-28T00:00:00Z",
		"expires_at": "2099-06-30T23:59:59Z",
		"reason": "approved by Jim",
		"rule_id": "SCP-R-001",
	}]
	rule_config := {"rules": {"SCP-R-004": {
		"disable": true,
		"justification": "stale override — should warn but still suppress for one release",
		"expires_at": "2020-01-01",
	}}}
	count(scp_r_004_results_full(input_value, [], rule_config, scp_r_004_test_now_ns)) == 0
	warns := scp_r_004_warns_full(input_value, [], rule_config, scp_r_004_test_now_ns)
	count(warns) == 1
	warns[0].kind == "rule_config"
}

# (14) Truncation of long `reason` text — verify 80-char + ellipsis per RULE-001 §3.3.
test_scp_r_004_truncates_long_reason_in_message if {
	long_reason := "this is a very long reason text that exceeds the 80-character truncation budget by quite a bit and should be truncated"
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-28T00:00:00Z",
		"expires_at": "2099-06-30T23:59:59Z",
		"reason": long_reason,
		"rule_id": "SCP-R-001",
	}]
	results := scp_r_004_results(input_value)
	count(results) == 1
	# Message should contain the truncated reason (79 chars + ellipsis), not the full reason.
	contains(results[0].message, "…")
	# Should NOT contain the tail of the long reason.
	not contains(results[0].message, "by quite a bit and should be truncated")
}

# (14b) Short `reason` is NOT truncated.
test_scp_r_004_does_not_truncate_short_reason if {
	short_reason := "approved by Jim"
	input_value := [{
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-28T00:00:00Z",
		"expires_at": "2099-06-30T23:59:59Z",
		"reason": short_reason,
		"rule_id": "SCP-R-001",
	}]
	results := scp_r_004_results(input_value)
	count(results) == 1
	contains(results[0].message, "approved by Jim")
	not contains(results[0].message, "…")
}

# (15) Mixed-array with non-object entry — SCP-R-004 skips the non-object (SCP-R-002 covers it).
test_scp_r_004_skips_non_object_entries if {
	input_value := [
		{
			"approved_by": "@jrnb2024",
			"created_at": "2026-04-28T00:00:00Z",
			"expires_at": "2099-06-30T23:59:59Z",
			"reason": "approved by Jim",
			"rule_id": "SCP-R-001",
		},
		"stray-string",
	]
	# SCP-R-004 fires once on entry 0 and skips entry 1.
	count(scp_r_004_results(input_value)) == 1
}
