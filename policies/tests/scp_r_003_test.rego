package main_test

import data.main
import rego.v1

scp_r_003_results(input_value) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
		finding.rule_id == "SCP-R-003"
	]
}

test_scp_r_003_allows_package_json_boolean_marker if {
	input_value := {
		"source_file": "package.json",
		"content": "{\n  \"name\": \"scp\",\n  \"scp:vendoring-attested\": true\n}\n",
	}

	count(scp_r_003_results(input_value)) == 0
}

test_scp_r_003_allows_comment_marker_for_pyproject if {
	input_value := {
		"source_file": "pyproject.toml",
		"content": "# scp:vendoring-attested\n[project]\nname = \"scp\"\n",
	}

	count(scp_r_003_results(input_value)) == 0
}

test_scp_r_003_denies_missing_marker if {
	input_value := {
		"source_file": "go.mod",
		"content": "module example.com/scp\n\ngo 1.23.0\n",
	}

	results := scp_r_003_results(input_value)
	count(results) == 1
	results[0].file == "go.mod"
	contains(results[0].message, "vendoring attestation marker")
}

test_scp_r_003_allows_comment_marker_for_go_mod if {
	input_value := {
		"source_file": "go.mod",
		"content": "// scp:vendoring-attested\nmodule example.com/scp\n\ngo 1.23.0\n",
	}

	count(scp_r_003_results(input_value)) == 0
}

test_scp_r_003_denies_package_json_without_marker if {
	input_value := {
		"source_file": "package.json",
		"content": "{\n  \"name\": \"scp\"\n}\n",
	}

	results := scp_r_003_results(input_value)
	count(results) == 1
	results[0].file == "package.json"
	contains(results[0].message, "vendoring attestation marker")
}

test_scp_r_003_denies_pyproject_without_marker if {
	input_value := {
		"source_file": "pyproject.toml",
		"content": "[project]\nname = \"scp\"\n",
	}

	results := scp_r_003_results(input_value)
	count(results) == 1
	results[0].file == "pyproject.toml"
	contains(results[0].message, "vendoring attestation marker")
}

test_scp_r_003_ignores_non_manifest_inputs if {
	input_value := {
		"source_file": "README.md",
		"content": "# not a manifest\n",
	}

	count(scp_r_003_results(input_value)) == 0
}

# WP-SCP-022 slice 020C.1: waiver-aware + rule-config-aware test helpers.
scp_r_003_results_full(input_value, waivers, rule_config, now_ns) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
			with main.scp_now_ns as now_ns
		finding.rule_id == "SCP-R-003"
	]
}

scp_r_003_warns_full(input_value, waivers, rule_config, now_ns) := records if {
	records := [record |
		some record in main.warn with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
			with main.scp_now_ns as now_ns
		record.rule_id == "SCP-R-003"
	]
}

scp_r_003_unattested_manifest := {
	"source_file": "go.mod",
	"content": "module example.com/scp\n\ngo 1.23.0\n",
}

scp_r_003_test_now_ns := time.parse_rfc3339_ns("2026-04-29T00:00:00Z")

# (i) waiver-suppression: a matching active waiver suppresses the deny
# and emits a kind=waiver warn record.
test_scp_r_003_waiver_suppresses_deny if {
	# Uses date-time expires_at to exercise scp_dateish_ns date-time branch.
	waivers := [{
		"waiver_id": "W-MANIFEST",
		"rule_id": "SCP-R-003",
		"expires_at": "2099-12-31T23:59:59Z",
		"reason": "test",
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29",
	}]
	count(scp_r_003_results_full(scp_r_003_unattested_manifest, waivers, {}, scp_r_003_test_now_ns)) == 0
	warns := scp_r_003_warns_full(scp_r_003_unattested_manifest, waivers, {}, scp_r_003_test_now_ns)
	count(warns) == 1
	warns[0].kind == "waiver"
	warns[0].waiver_id == "W-MANIFEST"
}

# (i) expired waiver does NOT suppress.
test_scp_r_003_expired_waiver_does_not_suppress if {
	waivers := [{
		"waiver_id": "W-EXPIRED",
		"rule_id": "SCP-R-003",
		"expires_at": "2020-01-01",
		"reason": "test",
		"approved_by": "@jrnb2024",
		"created_at": "2019-01-01",
	}]
	results := scp_r_003_results_full(scp_r_003_unattested_manifest, waivers, {}, scp_r_003_test_now_ns)
	count(results) == 1
	warns := scp_r_003_warns_full(scp_r_003_unattested_manifest, waivers, {}, scp_r_003_test_now_ns)
	count(warns) == 0
}

# (v) rule-config disable suppresses the deny and emits a kind=rule_config warn.
test_scp_r_003_rule_config_disable_suppresses_deny if {
	rule_config := {"rules": {"SCP-R-003": {
		"disable": true,
		"justification": "test override",
		"expires_at": "2099-12-31",
	}}}
	count(scp_r_003_results_full(scp_r_003_unattested_manifest, [], rule_config, scp_r_003_test_now_ns)) == 0
	warns := scp_r_003_warns_full(scp_r_003_unattested_manifest, [], rule_config, scp_r_003_test_now_ns)
	count(warns) == 1
	warns[0].kind == "rule_config"
	warns[0].reason == "rule-config override"
}

# (v) expired rule-config disable still suppresses for one release.
test_scp_r_003_expired_rule_config_still_suppresses if {
	rule_config := {"rules": {"SCP-R-003": {
		"disable": true,
		"justification": "stale override",
		"expires_at": "2020-01-01",
	}}}
	count(scp_r_003_results_full(scp_r_003_unattested_manifest, [], rule_config, scp_r_003_test_now_ns)) == 0
	warns := scp_r_003_warns_full(scp_r_003_unattested_manifest, [], rule_config, scp_r_003_test_now_ns)
	count(warns) == 1
	warns[0].kind == "rule_config"
}

# Coverage: scp_waiver_expired body 1 — missing/empty expires_at.
test_scp_r_003_waiver_with_missing_expires_at_does_not_suppress if {
	waivers := [{
		"waiver_id": "W-NO-EXPIRY",
		"rule_id": "SCP-R-003",
		"reason": "missing expires_at — must fail closed",
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29",
	}]
	results := scp_r_003_results_full(scp_r_003_unattested_manifest, waivers, {}, scp_r_003_test_now_ns)
	count(results) == 1
	warns := scp_r_003_warns_full(scp_r_003_unattested_manifest, waivers, {}, scp_r_003_test_now_ns)
	count(warns) == 0
}

# Coverage: scp_waiver_expired body 2 — malformed (unparseable) expires_at.
test_scp_r_003_waiver_with_malformed_expires_at_does_not_suppress if {
	waivers := [{
		"waiver_id": "W-BAD-DATE",
		"rule_id": "SCP-R-003",
		"expires_at": "not-a-date",
		"reason": "malformed expires_at — must fail closed",
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29",
	}]
	results := scp_r_003_results_full(scp_r_003_unattested_manifest, waivers, {}, scp_r_003_test_now_ns)
	count(results) == 1
	warns := scp_r_003_warns_full(scp_r_003_unattested_manifest, waivers, {}, scp_r_003_test_now_ns)
	count(warns) == 0
}
