package main_test

import data.main
import rego.v1

# SCP-R-016 (tcb-integrity-no-self-certification; standards-domain rule GOV-008).
# Gates the TCB of the conformance harness + forbids self-certification. Reads the
# materialiser-injected input.tcb_integrity envelope. Dormant (vacuous-pass) until
# the companion materialiser injects it (FUP-D067-CONFORMANCE-TCB-MATERIALISER-001).
# Ported from conformance-tcb policy/scp_r_tcb_001.rego (LIVE gate there).
#
# TDD (GOV-004): authored RED first — the positive assertions (unsigned TCB edit
# DENYs, wrong OIDC subject DENYs, no-ledger DENYs, unsigned CI-gate edit DENYs,
# typed!=computed DENYs, fail-closed on missing sub-keys) fail until SCP-R-016.rego
# exists; the fully-signed / vacuous / suppression cases confirm no over-firing.

scp_r_016_deny(input_value) := [f |
	some f in main.deny with input as input_value
	f.rule_id == "SCP-R-016"
]

scp_r_016_warn(input_value) := [r |
	some r in main.warn with input as input_value
	r.rule_id == "SCP-R-016"
]

scp_r_016_deny_full(input_value, waivers, rule_config) := [f |
	some f in main.deny with input as input_value
		with data.waivers as waivers
		with data.rule_config as rule_config
	f.rule_id == "SCP-R-016"
]

scp_r_016_warn_full(input_value, waivers, rule_config) := [r |
	some r in main.warn with input as input_value
		with data.waivers as waivers
		with data.rule_config as rule_config
	r.rule_id == "SCP-R-016"
]

scp_r_016_subject := "repo:jrnb2024/conformance-tcb:ref:refs/heads/main:job:mint"

# A fully-clean, fully-signed TCB envelope: no TCB/CI edits, greens minted under the
# sanctioned subject + in ledger, board reconciled.
scp_r_016_clean := {
	"diff": [{"path": "src/harness/render_board.py", "tcb_covered": false, "ci_gate": false}],
	"operator_signature": null,
	"greens": [{"cell": "boho-romance @ facet", "oidc_subject": scp_r_016_subject, "in_ledger": true}],
	"expected_oidc_subject": scp_r_016_subject,
	"board_cells": [{"id": "boho-romance @ facet", "typed": "GREEN", "computed": "GREEN"}],
}

# (vacuous) absent input → no findings (dormant until materialiser wires it).
test_scp_r_016_vacuous_absent_input if {
	count(scp_r_016_deny({})) == 0
	count(scp_r_016_warn({})) == 0
}

# (vacuous) an unrelated PR with no tcb_integrity → dormant.
test_scp_r_016_vacuous_unrelated_input if {
	count(scp_r_016_deny({"repo_id": "mapp-pim"})) == 0
}

# (pass) a fully-clean, fully-signed TCB envelope → no findings.
test_scp_r_016_pass_clean if {
	count(scp_r_016_deny({"tcb_integrity": scp_r_016_clean})) == 0
}

# (deny, a) a TCB-covered path modified without an operator counter-signature.
test_scp_r_016_deny_tcb_edit_unsigned if {
	count(scp_r_016_deny({"tcb_integrity": object.union(scp_r_016_clean, {"diff": [{"path": "trust-root.yaml", "tcb_covered": true, "ci_gate": false}]})})) >= 1
}

# (pass, a) the same TCB edit WITH a fresh operator signature → allowed.
test_scp_r_016_pass_tcb_edit_signed if {
	count(scp_r_016_deny({"tcb_integrity": object.union(scp_r_016_clean, {
		"diff": [{"path": "trust-root.yaml", "tcb_covered": true, "ci_gate": false}],
		"operator_signature": "ed25519:abc123...",
	})})) == 0
}

# (deny, b) a green minted outside the sanctioned container OIDC subject.
test_scp_r_016_deny_wrong_oidc_subject if {
	count(scp_r_016_deny({"tcb_integrity": object.union(scp_r_016_clean, {"greens": [{"cell": "x", "oidc_subject": "repo:attacker/evil:job:mint", "in_ledger": true}]})})) >= 1
}

# (deny, b) a green with no matching append-only ledger entry.
test_scp_r_016_deny_not_in_ledger if {
	count(scp_r_016_deny({"tcb_integrity": object.union(scp_r_016_clean, {"greens": [{"cell": "x", "oidc_subject": scp_r_016_subject, "in_ledger": false}]})})) >= 1
}

# (deny, c) a CI gate / branch-protection path edited without an operator signature.
test_scp_r_016_deny_ci_gate_unsigned if {
	count(scp_r_016_deny({"tcb_integrity": object.union(scp_r_016_clean, {"diff": [{"path": ".github/workflows/oracle-integrity.yml", "tcb_covered": false, "ci_gate": true}]})})) >= 1
}

# (deny, d) a typed board status that disagrees with the computed proof.
test_scp_r_016_deny_typed_disagrees if {
	count(scp_r_016_deny({"tcb_integrity": object.union(scp_r_016_clean, {"board_cells": [{"id": "x @ edit", "typed": "GREEN", "computed": "RED"}]})})) >= 1
}

# (deny, FAIL-CLOSED) an activated envelope missing diff → malformed DENY.
test_scp_r_016_fail_closed_missing_diff if {
	count(scp_r_016_deny({"tcb_integrity": {
		"greens": [],
		"expected_oidc_subject": scp_r_016_subject,
		"board_cells": [],
	}})) >= 1
}

# (deny, FAIL-CLOSED) an activated envelope missing board_cells → malformed DENY.
test_scp_r_016_fail_closed_missing_board_cells if {
	count(scp_r_016_deny({"tcb_integrity": {
		"diff": [],
		"greens": [],
		"expected_oidc_subject": scp_r_016_subject,
	}})) >= 1
}

# (opt-out) bespoke rule-config key suppresses + emits observability warn.
test_scp_r_016_opt_out_suppresses if {
	input_value := {
		"tcb_integrity": object.union(scp_r_016_clean, {"board_cells": [{"id": "x", "typed": "GREEN", "computed": "RED"}]}),
		"rule_config": {"tcb-integrity-disabled": true},
	}
	count(scp_r_016_deny(input_value)) == 0
	count(scp_r_016_warn(input_value)) >= 1
}

# (disable) rules.SCP-R-016.disable: true suppresses + emits observability warn.
test_scp_r_016_disable_suppresses if {
	input_value := {"tcb_integrity": object.union(scp_r_016_clean, {"board_cells": [{"id": "x", "typed": "GREEN", "computed": "RED"}]})}
	rule_config := {"rules": {"SCP-R-016": {
		"disable": true,
		"justification": "operator override",
		"expires_at": "2099-12-31T00:00:00Z",
	}}}
	count(scp_r_016_deny_full(input_value, [], rule_config)) == 0
	count(scp_r_016_warn_full(input_value, [], rule_config)) >= 1
}

# (waiver) active waiver suppresses + emits observability warn.
test_scp_r_016_waiver_suppresses if {
	input_value := {"tcb_integrity": object.union(scp_r_016_clean, {"board_cells": [{"id": "x", "typed": "GREEN", "computed": "RED"}]})}
	waivers := [{
		"waiver_id": "scp-r-016-grace",
		"rule_id": "SCP-R-016",
		"expires_at": "2099-12-31T00:00:00Z",
	}]
	count(scp_r_016_deny_full(input_value, waivers, {})) == 0
	count(scp_r_016_warn_full(input_value, waivers, {})) >= 1
}
