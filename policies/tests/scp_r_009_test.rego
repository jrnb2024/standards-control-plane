package main_test

import data.main
import rego.v1

# SCP-R-009 (auth-canonical-version-pin). Reads input.canonical_sdk_versions
# (+_verified) + input.adopter_ct_auth_deps. Dormant (vacuous-pass) until the
# companion workflow materialises these. See policies/SCP-R-009.rego header.

scp_r_009_deny(input_value) := [f |
	some f in main.deny with input as input_value
	f.rule_id == "SCP-R-009"
]

scp_r_009_warn(input_value) := [r |
	some r in main.warn with input as input_value
	r.rule_id == "SCP-R-009"
]

scp_r_009_deny_full(input_value, waivers, rule_config) := [f |
	some f in main.deny with input as input_value
		with data.waivers as waivers
		with data.rule_config as rule_config
	f.rule_id == "SCP-R-009"
]

scp_r_009_warn_full(input_value, waivers, rule_config) := [r |
	some r in main.warn with input as input_value
		with data.waivers as waivers
		with data.rule_config as rule_config
	r.rule_id == "SCP-R-009"
]

# Minimal verified CT manifest: ct-auth-python floor 1.0.0 / canonical 1.1.0.
scp_r_009_manifest := {"packages": {
	"ct-auth-python": {"minimum_secure_version": "1.0.0", "canonical_version": "1.1.0"},
	"ct-auth-go": {"minimum_secure_version": "1.0.0", "canonical_version": "1.0.2"},
}}

# (vacuous) no ct-auth deps → no findings, even with a verified manifest.
test_scp_r_009_vacuous_no_deps if {
	count(scp_r_009_deny({
		"canonical_sdk_versions": scp_r_009_manifest,
		"canonical_sdk_versions_verified": true,
		"adopter_ct_auth_deps": [],
	})) == 0
}

# (dormant) deps present but no manifest materialised → vacuous-pass.
test_scp_r_009_dormant_no_manifest if {
	count(scp_r_009_deny({"adopter_ct_auth_deps": [{"package": "ct-auth-python", "version": "0.9.0", "file": "pyproject.toml"}]})) == 0
}

# (fail-closed) manifest present but NOT verified → 1 signature finding.
test_scp_r_009_fail_closed_unverified if {
	results := scp_r_009_deny({
		"canonical_sdk_versions": scp_r_009_manifest,
		"canonical_sdk_versions_verified": false,
		"adopter_ct_auth_deps": [{"package": "ct-auth-python", "version": "1.1.0", "file": "pyproject.toml"}],
	})
	count(results) == 1
}

# (deny, MAJOR below floor) dep 0.9.0 < floor 1.0.0 → deny.
test_scp_r_009_deny_below_floor_major if {
	results := scp_r_009_deny({
		"canonical_sdk_versions": scp_r_009_manifest,
		"canonical_sdk_versions_verified": true,
		"adopter_ct_auth_deps": [{"package": "ct-auth-python", "version": "0.9.0", "file": "pyproject.toml"}],
	})
	count(results) == 1
}

# (warn, MINOR stale) dep 1.0.0 >= floor 1.0.0 but < canonical 1.1.0 → warn
# (NOT deny — stale is warn-class, downgrade is deny-class; R1 CORR-MAJ-001).
test_scp_r_009_warn_stale_minor if {
	input_value := {
		"canonical_sdk_versions": scp_r_009_manifest,
		"canonical_sdk_versions_verified": true,
		"adopter_ct_auth_deps": [{"package": "ct-auth-python", "version": "1.0.0", "file": "pyproject.toml"}],
	}
	count(scp_r_009_deny(input_value)) == 0
	count(scp_r_009_warn(input_value)) == 1
}

# (warn, PATCH stale) ct-auth-go dep 1.0.1 < canonical 1.0.2 → warn (exercises
# the patch-level less-than clause).
test_scp_r_009_warn_stale_patch if {
	input_value := {
		"canonical_sdk_versions": scp_r_009_manifest,
		"canonical_sdk_versions_verified": true,
		"adopter_ct_auth_deps": [{"package": "ct-auth-go", "version": "1.0.1", "file": "go.mod"}],
	}
	count(scp_r_009_deny(input_value)) == 0
	count(scp_r_009_warn(input_value)) == 1
}

# (pass) dep at canonical version → no finding.
test_scp_r_009_pass_at_canonical if {
	input_value := {
		"canonical_sdk_versions": scp_r_009_manifest,
		"canonical_sdk_versions_verified": true,
		"adopter_ct_auth_deps": [{"package": "ct-auth-python", "version": "1.1.0", "file": "pyproject.toml"}],
	}
	count(scp_r_009_deny(input_value)) == 0
	count(scp_r_009_warn(input_value)) == 0
}

# (opt-out) bespoke key suppresses + emits observability warn.
test_scp_r_009_opt_out_suppresses if {
	input_value := {
		"rule_config": {"auth-canonical-version-pin-disabled": true},
		"canonical_sdk_versions": scp_r_009_manifest,
		"canonical_sdk_versions_verified": true,
		"adopter_ct_auth_deps": [{"package": "ct-auth-python", "version": "0.9.0", "file": "pyproject.toml"}],
	}
	count(scp_r_009_deny(input_value)) == 0
	count(scp_r_009_warn(input_value)) >= 1
}

# (warn-only suppression) stale dep (warn-class, no deny) + opt-out → deny==0
# + observability warn — exercises the warn branch of scp_r_009_any_findings.
test_scp_r_009_warn_only_opt_out_observable if {
	input_value := {
		"rule_config": {"auth-canonical-version-pin-disabled": true},
		"canonical_sdk_versions": scp_r_009_manifest,
		"canonical_sdk_versions_verified": true,
		"adopter_ct_auth_deps": [{"package": "ct-auth-python", "version": "1.0.0", "file": "pyproject.toml"}],
	}
	count(scp_r_009_deny(input_value)) == 0
	count(scp_r_009_warn(input_value)) >= 1
}

# (disable) rules.SCP-R-009.disable: true suppresses + emits observability warn.
test_scp_r_009_disable_suppresses if {
	input_value := {
		"canonical_sdk_versions": scp_r_009_manifest,
		"canonical_sdk_versions_verified": true,
		"adopter_ct_auth_deps": [{"package": "ct-auth-python", "version": "0.9.0", "file": "pyproject.toml"}],
	}
	rule_config := {"rules": {"SCP-R-009": {
		"disable": true,
		"justification": "operator override",
		"expires_at": "2099-12-31T00:00:00Z",
	}}}
	count(scp_r_009_deny_full(input_value, [], rule_config)) == 0
	count(scp_r_009_warn_full(input_value, [], rule_config)) >= 1
}

# (waiver) active waiver suppresses + emits observability warn.
test_scp_r_009_waiver_suppresses if {
	input_value := {
		"canonical_sdk_versions": scp_r_009_manifest,
		"canonical_sdk_versions_verified": true,
		"adopter_ct_auth_deps": [{"package": "ct-auth-python", "version": "0.9.0", "file": "pyproject.toml"}],
	}
	waivers := [{
		"waiver_id": "scp-r-009-grace",
		"rule_id": "SCP-R-009",
		"expires_at": "2099-12-31T00:00:00Z",
	}]
	count(scp_r_009_deny_full(input_value, waivers, {})) == 0
	count(scp_r_009_warn_full(input_value, waivers, {})) >= 1
}
