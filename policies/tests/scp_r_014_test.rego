package main_test

import data.main
import rego.v1

# SCP-R-014 (no-shortcuts-serving-source-allowlist; standards-domain rule GOV-006).
# Gates that the serving path reads only sanctioned sources. Reads the materialiser-
# injected input.serving_allowlist_scan envelope. Dormant (vacuous-pass) until the
# companion materialiser injects it (FUP-D067-CONFORMANCE-TCB-MATERIALISER-001).
# Ported from conformance-tcb policy/scp_r_join_001.rego (LIVE gate there).
#
# TDD (GOV-004): authored RED first — the positive assertions (unsanctioned read
# DENYs, unclassified dir DENYs, dynamic filename DENYs, fail-closed on missing
# sub-keys) fail until SCP-R-014.rego exists; the compliant / vacuous / suppression
# cases then confirm no over-firing.

scp_r_014_deny(input_value) := [f |
	some f in main.deny with input as input_value
	f.rule_id == "SCP-R-014"
]

scp_r_014_warn(input_value) := [r |
	some r in main.warn with input as input_value
	r.rule_id == "SCP-R-014"
]

scp_r_014_deny_full(input_value, waivers, rule_config) := [f |
	some f in main.deny with input as input_value
		with data.waivers as waivers
		with data.rule_config as rule_config
	f.rule_id == "SCP-R-014"
]

scp_r_014_warn_full(input_value, waivers, rule_config) := [r |
	some r in main.warn with input as input_value
		with data.waivers as waivers
		with data.rule_config as rule_config
	r.rule_id == "SCP-R-014"
]

# A compliant scan: one sanctioned read, a classified dir, no dynamic filename.
scp_r_014_good_scan := {
	"sanctioned_sources": ["Recommender/services/search/index.go"],
	"serving_reads": [{
		"reader": "search/main.go",
		"source": "Recommender/services/search/index.go",
		"dynamic_filename": false,
	}],
	"serving_dirs": [{"dir": "Recommender/services/search", "classified": true}],
}

# (vacuous) absent input → no findings (dormant until materialiser wires it).
test_scp_r_014_vacuous_absent_input if {
	count(scp_r_014_deny({})) == 0
	count(scp_r_014_warn({})) == 0
}

# (vacuous) an unrelated PR with other keys but no serving_allowlist_scan → dormant.
test_scp_r_014_vacuous_unrelated_input if {
	count(scp_r_014_deny({"repo_id": "mapp-pim", "some_other_key": [1, 2, 3]})) == 0
}

# (pass) an activated compliant scan → no findings.
test_scp_r_014_pass_compliant_scan if {
	count(scp_r_014_deny({"serving_allowlist_scan": scp_r_014_good_scan})) == 0
}

# (deny) a serving read of a source NOT on the sanctioned allowlist.
test_scp_r_014_deny_unsanctioned_read if {
	count(scp_r_014_deny({"serving_allowlist_scan": {
		"sanctioned_sources": ["search/index.go"],
		"serving_reads": [{"reader": "search/main.go", "source": "fixtures/catalog_enriched_v3.json", "dynamic_filename": false}],
		"serving_dirs": [{"dir": "search", "classified": true}],
	}})) >= 1
}

# (deny) a new/unclassified serving directory.
test_scp_r_014_deny_unclassified_dir if {
	count(scp_r_014_deny({"serving_allowlist_scan": {
		"sanctioned_sources": ["search/index.go"],
		"serving_reads": [],
		"serving_dirs": [{"dir": "search/experimental", "classified": false}],
	}})) >= 1
}

# (deny) a dynamically-constructed serving filename.
test_scp_r_014_deny_dynamic_filename if {
	count(scp_r_014_deny({"serving_allowlist_scan": {
		"sanctioned_sources": ["search/index.go"],
		"serving_reads": [{"reader": "search/main.go", "source": "search/index.go", "dynamic_filename": true}],
		"serving_dirs": [{"dir": "search", "classified": true}],
	}})) >= 1
}

# (deny, FAIL-CLOSED) an activated envelope missing serving_reads → malformed DENY.
test_scp_r_014_fail_closed_missing_serving_reads if {
	count(scp_r_014_deny({"serving_allowlist_scan": {
		"sanctioned_sources": ["search/index.go"],
		"serving_dirs": [{"dir": "search", "classified": true}],
	}})) >= 1
}

# (deny, FAIL-CLOSED) an activated envelope missing serving_dirs → malformed DENY.
test_scp_r_014_fail_closed_missing_serving_dirs if {
	count(scp_r_014_deny({"serving_allowlist_scan": {
		"sanctioned_sources": ["search/index.go"],
		"serving_reads": [],
	}})) >= 1
}

# (deny, FAIL-CLOSED) an activated envelope missing sanctioned_sources → malformed DENY.
test_scp_r_014_fail_closed_missing_sanctioned_sources if {
	count(scp_r_014_deny({"serving_allowlist_scan": {
		"serving_reads": [],
		"serving_dirs": [],
	}})) >= 1
}

# (opt-out) bespoke rule-config key suppresses + emits observability warn.
test_scp_r_014_opt_out_suppresses if {
	input_value := {
		"serving_allowlist_scan": {
			"sanctioned_sources": ["search/index.go"],
			"serving_reads": [{"reader": "search/main.go", "source": "fixtures/x.json", "dynamic_filename": false}],
			"serving_dirs": [{"dir": "search", "classified": true}],
		},
		"rule_config": {"no-shortcuts-serving-allowlist-disabled": true},
	}
	count(scp_r_014_deny(input_value)) == 0
	count(scp_r_014_warn(input_value)) >= 1
}

# (disable) rules.SCP-R-014.disable: true suppresses + emits observability warn.
test_scp_r_014_disable_suppresses if {
	input_value := {"serving_allowlist_scan": {
		"sanctioned_sources": ["search/index.go"],
		"serving_reads": [{"reader": "search/main.go", "source": "fixtures/x.json", "dynamic_filename": false}],
		"serving_dirs": [{"dir": "search", "classified": true}],
	}}
	rule_config := {"rules": {"SCP-R-014": {
		"disable": true,
		"justification": "operator override",
		"expires_at": "2099-12-31T00:00:00Z",
	}}}
	count(scp_r_014_deny_full(input_value, [], rule_config)) == 0
	count(scp_r_014_warn_full(input_value, [], rule_config)) >= 1
}

# (waiver) active waiver suppresses + emits observability warn.
test_scp_r_014_waiver_suppresses if {
	input_value := {"serving_allowlist_scan": {
		"sanctioned_sources": ["search/index.go"],
		"serving_reads": [{"reader": "search/main.go", "source": "fixtures/x.json", "dynamic_filename": false}],
		"serving_dirs": [{"dir": "search", "classified": true}],
	}}
	waivers := [{
		"waiver_id": "scp-r-014-grace",
		"rule_id": "SCP-R-014",
		"expires_at": "2099-12-31T00:00:00Z",
	}]
	count(scp_r_014_deny_full(input_value, waivers, {})) == 0
	count(scp_r_014_warn_full(input_value, waivers, {})) >= 1
}
