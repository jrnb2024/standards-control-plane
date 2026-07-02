package main_test

import data.main
import rego.v1

# SCP-R-013 (ontology-canonical-consumption; standards-domain rule ARCH-006).
# Gates LINKAGE to the canonical fashion-ontology-service (FOS). Reads
# input.ontology_contract / input.ontology_consumer / input.ontology_source_markers
# / input.repo_id / input.ontology_authoring_allowlist. Dormant (vacuous-pass)
# until the companion workflow materialiser injects these
# (FUP-WP-SCP-037-ARCH-006-MATERIALISER-001). See policies/SCP-R-013.rego header.
#
# TDD (GOV-004): this test is authored RED first — the positive assertions
# (embedded copy DENYs, wrong canonical name DENYs, self-assert-still-DENYs)
# fail until SCP-R-013.rego exists; the compliant / carve-out / vacuous cases
# then confirm no over-firing.

scp_r_013_deny(input_value) := [f |
	some f in main.deny with input as input_value
	f.rule_id == "SCP-R-013"
]

scp_r_013_warn(input_value) := [r |
	some r in main.warn with input as input_value
	r.rule_id == "SCP-R-013"
]

scp_r_013_deny_full(input_value, waivers, rule_config) := [f |
	some f in main.deny with input as input_value
		with data.waivers as waivers
		with data.rule_config as rule_config
	f.rule_id == "SCP-R-013"
]

scp_r_013_warn_full(input_value, waivers, rule_config) := [r |
	some r in main.warn with input as input_value
		with data.waivers as waivers
		with data.rule_config as rule_config
	r.rule_id == "SCP-R-013"
]

# SCP-owned authoring allowlist (materialiser-injected in production). FOS
# serves the canonical; FLA authors the source data → both may legitimately
# hold the ontology files.
scp_r_013_allowlist := ["fashion-ontology-service", "fashion-labelling-agent"]

# A compliant consumer contract: links to FOS, pins a version, non-local fallback.
scp_r_013_good_contract := {
	"canonical_service": "fashion-ontology-service",
	"canonical_version": "1.2.0",
	"endpoints": ["/api/v1/value-mappings"],
	"fallback": "fail-request",
	"cache_ttl": "24h",
}

# (vacuous) absent input → no findings (dormant until materialiser wires it).
test_scp_r_013_vacuous_absent_input if {
	count(scp_r_013_deny({})) == 0
	count(scp_r_013_warn({})) == 0
}

# (deny) a repo the workflow flags as an ontology consumer, with NO
# ontology_contract declared → missing-linkage finding.
test_scp_r_013_deny_missing_contract_when_consumer if {
	count(scp_r_013_deny({
		"repo_id": "mapp-pim",
		"ontology_consumer": true,
	})) >= 1
}

# (pass) consumer that declares a compliant ontology_contract and embeds nothing.
test_scp_r_013_pass_compliant_consumer if {
	count(scp_r_013_deny({
		"repo_id": "mapp-pim",
		"ontology_consumer": true,
		"ontology_contract": scp_r_013_good_contract,
	})) == 0
}

# (deny) contract present but canonical_service is a bespoke name.
test_scp_r_013_deny_wrong_canonical_service if {
	count(scp_r_013_deny({
		"repo_id": "mapp-pim",
		"ontology_consumer": true,
		"ontology_contract": object.union(scp_r_013_good_contract, {"canonical_service": "pim-local-ontology"}),
	})) >= 1
}

# (deny) a declared contract that OMITS canonical_service — an empty/absent
# authority is still "not the canonical"; must not escape both signals.
test_scp_r_013_deny_missing_canonical_service if {
	count(scp_r_013_deny({
		"repo_id": "mapp-pim",
		"ontology_consumer": true,
		"ontology_contract": {"canonical_version": "1.0.0", "endpoints": ["/api/v1/value-mappings"]},
	})) >= 1
}

# (deny, FAIL-CLOSED) the authoring repo's markers STILL deny when the
# SCP-injected allowlist is absent (materialiser incomplete) — the carve-out
# must not fail-open on a missing allowlist.
test_scp_r_013_deny_authoring_repo_if_allowlist_absent if {
	count(scp_r_013_deny({
		"repo_id": "fashion-labelling-agent",
		"ontology_source_markers": [{"kind": "embedded_file", "file": "labelling_agent/ontology_complete.yaml"}],
	})) >= 1
}

# (deny) an embedded canonical ontology file in a non-authoring repo.
test_scp_r_013_deny_embedded_ontology_file if {
	count(scp_r_013_deny({
		"repo_id": "mapp-pim",
		"ontology_authoring_allowlist": scp_r_013_allowlist,
		"ontology_source_markers": [{"kind": "embedded_file", "file": "value_mappings.json"}],
	})) >= 1
}

# (deny) a local ontology re-implementation class in a non-authoring repo.
test_scp_r_013_deny_local_ontology_class if {
	count(scp_r_013_deny({
		"repo_id": "mf-intent-os",
		"ontology_authoring_allowlist": scp_r_013_allowlist,
		"ontology_source_markers": [{"kind": "local_class", "file": "search/ontology.py", "symbol": "Canonicalizer"}],
	})) >= 1
}

# (pass, CARVE-OUT) the authoring source (FLA) embeds the ontology file — it
# AUTHORS the data. Exempt from the embedded/local-class signals BECAUSE it is
# on the SCP-injected allowlist.
test_scp_r_013_carveout_authoring_source_passes if {
	count(scp_r_013_deny({
		"repo_id": "fashion-labelling-agent",
		"ontology_authoring_allowlist": scp_r_013_allowlist,
		"ontology_source_markers": [
			{"kind": "embedded_file", "file": "labelling_agent/ontology_complete.yaml"},
			{"kind": "local_class", "file": "labelling_agent/ontology.py", "symbol": "Ontology"},
		],
	})) == 0
}

# (deny, BYPASS GUARD) a repo NOT on the allowlist self-asserts
# role: authoring-source in its OWN contract while embedding the ontology file.
# The self-assertion is IGNORED (the exemption is allowlist-only) → still DENY.
test_scp_r_013_no_self_assert_bypass if {
	count(scp_r_013_deny({
		"repo_id": "sneaky-app",
		"ontology_authoring_allowlist": scp_r_013_allowlist,
		"ontology_contract": {"canonical_service": "fashion-ontology-service", "role": "authoring-source"},
		"ontology_source_markers": [{"kind": "embedded_file", "file": "ontology_complete.yaml"}],
	})) >= 1
}

# (deny) fallback resolves to a local ontology copy (defeats the canonical).
test_scp_r_013_deny_fallback_local_copy if {
	count(scp_r_013_deny({
		"repo_id": "mapp-pim",
		"ontology_consumer": true,
		"ontology_contract": object.union(scp_r_013_good_contract, {"fallback": "use local copy"}),
	})) >= 1
}

# (opt-out) bespoke rule-config key suppresses + emits observability warn.
test_scp_r_013_opt_out_suppresses if {
	input_value := {
		"repo_id": "mapp-pim",
		"ontology_authoring_allowlist": scp_r_013_allowlist,
		"ontology_source_markers": [{"kind": "embedded_file", "file": "ontology_complete.yaml"}],
		"rule_config": {"ontology-canonical-consumption-disabled": true},
	}
	count(scp_r_013_deny(input_value)) == 0
	count(scp_r_013_warn(input_value)) >= 1
}

# (disable) rules.SCP-R-013.disable: true suppresses + emits observability warn.
test_scp_r_013_disable_suppresses if {
	input_value := {
		"repo_id": "mapp-pim",
		"ontology_authoring_allowlist": scp_r_013_allowlist,
		"ontology_source_markers": [{"kind": "embedded_file", "file": "ontology_complete.yaml"}],
	}
	rule_config := {"rules": {"SCP-R-013": {
		"disable": true,
		"justification": "operator override",
		"expires_at": "2099-12-31T00:00:00Z",
	}}}
	count(scp_r_013_deny_full(input_value, [], rule_config)) == 0
	count(scp_r_013_warn_full(input_value, [], rule_config)) >= 1
}

# (waiver) active waiver suppresses + emits observability warn.
test_scp_r_013_waiver_suppresses if {
	input_value := {
		"repo_id": "mapp-pim",
		"ontology_authoring_allowlist": scp_r_013_allowlist,
		"ontology_source_markers": [{"kind": "embedded_file", "file": "ontology_complete.yaml"}],
	}
	waivers := [{
		"waiver_id": "scp-r-013-grace",
		"rule_id": "SCP-R-013",
		"expires_at": "2099-12-31T00:00:00Z",
	}]
	count(scp_r_013_deny_full(input_value, waivers, {})) == 0
	count(scp_r_013_warn_full(input_value, waivers, {})) >= 1
}
