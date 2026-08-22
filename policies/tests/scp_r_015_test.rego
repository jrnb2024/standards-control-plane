package main_test

import data.main
import rego.v1

# SCP-R-015 (integrity-green-required-to-leave-red; standards-domain rule GOV-007).
# Gates that a board cell may not be marked non-RED unless all four integrity
# clauses hold. Reads the materialiser-injected input.cell_transition envelope.
# Dormant (vacuous-pass) until the companion materialiser injects it
# (FUP-D067-CONFORMANCE-TCB-MATERIALISER-001). Ported from conformance-tcb
# policy/scp_r_triad_001.rego (LIVE gate there).
#
# TDD (GOV-004): authored RED first — the positive assertions (integrity-fail
# DENYs, fail-closed on missing field) fail until SCP-R-015.rego exists; the
# all-green / RED-cell / vacuous / suppression cases confirm no over-firing.

scp_r_015_deny(input_value) := [f |
	some f in main.deny with input as input_value
	f.rule_id == "SCP-R-015"
]

scp_r_015_warn(input_value) := [r |
	some r in main.warn with input as input_value
	r.rule_id == "SCP-R-015"
]

scp_r_015_deny_full(input_value, waivers, rule_config) := [f |
	some f in main.deny with input as input_value
		with data.waivers as waivers
		with data.rule_config as rule_config
	f.rule_id == "SCP-R-015"
]

scp_r_015_warn_full(input_value, waivers, rule_config) := [r |
	some r in main.warn with input as input_value
		with data.waivers as waivers
		with data.rule_config as rule_config
	r.rule_id == "SCP-R-015"
]

# A fully-integrity-green flip: all four clauses satisfied.
scp_r_015_green_cell := {
	"id": "boho-romance @ facet",
	"status": "GREEN-integrity",
	"computed_status": "GREEN-integrity",
	"fake_mutant_failed": true,
	"red_first": true,
	"classifier_ok": true,
}

# (vacuous) absent input → no findings (dormant until materialiser wires it).
test_scp_r_015_vacuous_absent_input if {
	count(scp_r_015_deny({})) == 0
	count(scp_r_015_warn({})) == 0
}

# (vacuous) an unrelated PR with no cell_transition → dormant.
test_scp_r_015_vacuous_unrelated_input if {
	count(scp_r_015_deny({"repo_id": "mapp-pim"})) == 0
}

# (pass) a cell whose claimed status is RED is never gated.
test_scp_r_015_pass_red_cell if {
	count(scp_r_015_deny({"cell_transition": {"id": "x @ edit", "status": "RED"}})) == 0
}

# (pass) a fully-integrity-green flip → no findings.
test_scp_r_015_pass_all_integrity_green if {
	count(scp_r_015_deny({"cell_transition": scp_r_015_green_cell})) == 0
}

# (deny) claims non-RED but computed_status disagrees (typed override).
test_scp_r_015_deny_computed_disagrees if {
	count(scp_r_015_deny({"cell_transition": object.union(scp_r_015_green_cell, {"computed_status": "RED"})})) >= 1
}

# (deny) claims non-RED but the standing fake-mutant did NOT fail (test blind).
test_scp_r_015_deny_fake_mutant_passed if {
	count(scp_r_015_deny({"cell_transition": object.union(scp_r_015_green_cell, {"fake_mutant_failed": false})})) >= 1
}

# (deny) claims non-RED with no red-first history.
test_scp_r_015_deny_no_red_first if {
	count(scp_r_015_deny({"cell_transition": object.union(scp_r_015_green_cell, {"red_first": false})})) >= 1
}

# (deny) claims non-RED but the transition classifier is not ok (TCB touched).
test_scp_r_015_deny_classifier_not_ok if {
	count(scp_r_015_deny({"cell_transition": object.union(scp_r_015_green_cell, {"classifier_ok": false})})) >= 1
}

# (deny, FAIL-CLOSED) claims non-RED with a required field absent → malformed DENY.
test_scp_r_015_fail_closed_missing_field if {
	count(scp_r_015_deny({"cell_transition": {
		"id": "x @ facet",
		"status": "GREEN-integrity",
		"computed_status": "GREEN-integrity",
		"fake_mutant_failed": true,
		"red_first": true,
	}})) >= 1
}

# (opt-out) bespoke rule-config key suppresses + emits observability warn.
test_scp_r_015_opt_out_suppresses if {
	input_value := {
		"cell_transition": object.union(scp_r_015_green_cell, {"fake_mutant_failed": false}),
		"rule_config": {"integrity-green-triad-disabled": true},
	}
	count(scp_r_015_deny(input_value)) == 0
	count(scp_r_015_warn(input_value)) >= 1
}

# (disable) rules.SCP-R-015.disable: true suppresses + emits observability warn.
test_scp_r_015_disable_suppresses if {
	input_value := {"cell_transition": object.union(scp_r_015_green_cell, {"fake_mutant_failed": false})}
	rule_config := {"rules": {"SCP-R-015": {
		"disable": true,
		"justification": "operator override",
		"expires_at": "2099-12-31T00:00:00Z",
	}}}
	count(scp_r_015_deny_full(input_value, [], rule_config)) == 0
	count(scp_r_015_warn_full(input_value, [], rule_config)) >= 1
}

# (waiver) active waiver suppresses + emits observability warn.
test_scp_r_015_waiver_suppresses if {
	input_value := {"cell_transition": object.union(scp_r_015_green_cell, {"fake_mutant_failed": false})}
	waivers := [{
		"waiver_id": "scp-r-015-grace",
		"rule_id": "SCP-R-015",
		"expires_at": "2099-12-31T00:00:00Z",
	}]
	count(scp_r_015_deny_full(input_value, waivers, {})) == 0
	count(scp_r_015_warn_full(input_value, waivers, {})) >= 1
}
