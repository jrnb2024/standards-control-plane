package main_test

import data.main
import rego.v1

# SCP-R-010 (auth-canonical-import-fence). Reads input.auth_contract
# (+_verified) + input.adopter_source_files. Two tiers: tier_deny shadow→deny,
# tier_warn shadow→warn. Dormant until the companion workflow materialises.

scp_r_010_deny(input_value) := [f |
	some f in main.deny with input as input_value
	f.rule_id == "SCP-R-010"
]

scp_r_010_warn(input_value) := [r |
	some r in main.warn with input as input_value
	r.rule_id == "SCP-R-010"
]

scp_r_010_deny_full(input_value, waivers, rule_config) := [f |
	some f in main.deny with input as input_value
		with data.waivers as waivers
		with data.rule_config as rule_config
	f.rule_id == "SCP-R-010"
]

scp_r_010_warn_full(input_value, waivers, rule_config) := [r |
	some r in main.warn with input as input_value
		with data.waivers as waivers
		with data.rule_config as rule_config
	r.rule_id == "SCP-R-010"
]

scp_r_010_contract := {"protected_primitives": {
	"tier_deny": {"python": ["validate_token", "JWKSClient"], "typescript": ["validateToken"]},
	"tier_warn": {"python": ["has_permission"]},
}}

# (vacuous) no file imports ct-auth → no findings.
test_scp_r_010_vacuous_no_import if {
	input_value := {
		"auth_contract": scp_r_010_contract,
		"auth_contract_verified": true,
		"adopter_source_files": [{"path": "a.py", "language": "python", "imports_ct_auth": false, "declared_symbols": ["validate_token"]}],
	}
	count(scp_r_010_deny(input_value)) == 0
	count(scp_r_010_warn(input_value)) == 0
}

# (fail-closed) importing file + contract present but unverified → 1 deny.
test_scp_r_010_fail_closed_unverified if {
	input_value := {
		"auth_contract": scp_r_010_contract,
		"auth_contract_verified": false,
		"adopter_source_files": [{"path": "a.py", "language": "python", "imports_ct_auth": true, "declared_symbols": []}],
	}
	count(scp_r_010_deny(input_value)) == 1
}

# (deny) tier_deny symbol shadowed in an importing file → deny.
test_scp_r_010_deny_tier_deny_shadow if {
	input_value := {
		"auth_contract": scp_r_010_contract,
		"auth_contract_verified": true,
		"adopter_source_files": [{"path": "auth.py", "language": "python", "imports_ct_auth": true, "declared_symbols": ["validate_token", "helper"]}],
	}
	count(scp_r_010_deny(input_value)) == 1
}

# (deny via re-export) tier_deny symbol re-exported → deny (exercises the
# reexported_symbols concat path).
test_scp_r_010_deny_reexport if {
	input_value := {
		"auth_contract": scp_r_010_contract,
		"auth_contract_verified": true,
		"adopter_source_files": [{"path": "index.ts", "language": "typescript", "imports_ct_auth": true, "declared_symbols": [], "reexported_symbols": ["validateToken"]}],
	}
	count(scp_r_010_deny(input_value)) == 1
}

# (warn) tier_warn symbol shadowed → warn (not deny).
test_scp_r_010_warn_tier_warn_shadow if {
	input_value := {
		"auth_contract": scp_r_010_contract,
		"auth_contract_verified": true,
		"adopter_source_files": [{"path": "perm.py", "language": "python", "imports_ct_auth": true, "declared_symbols": ["has_permission"]}],
	}
	count(scp_r_010_deny(input_value)) == 0
	count(scp_r_010_warn(input_value)) >= 1
}

# (pass) imports ct-auth but shadows nothing → no finding. Also exercises the
# non-array declared_symbols branch (null → treated as []).
test_scp_r_010_pass_clean_import if {
	input_value := {
		"auth_contract": scp_r_010_contract,
		"auth_contract_verified": true,
		"adopter_source_files": [{"path": "ok.py", "language": "python", "imports_ct_auth": true, "declared_symbols": null}],
	}
	count(scp_r_010_deny(input_value)) == 0
	count(scp_r_010_warn(input_value)) == 0
}

# (opt-out) bespoke key suppresses + observability warn.
test_scp_r_010_opt_out_suppresses if {
	input_value := {
		"rule_config": {"auth-canonical-import-fence-disabled": true},
		"auth_contract": scp_r_010_contract,
		"auth_contract_verified": true,
		"adopter_source_files": [{"path": "auth.py", "language": "python", "imports_ct_auth": true, "declared_symbols": ["validate_token"]}],
	}
	count(scp_r_010_deny(input_value)) == 0
	count(scp_r_010_warn(input_value)) >= 1
}

# (warn-only suppression) tier_warn shadow (no tier_deny) + opt-out → deny==0
# + observability warn — exercises the warn branch of scp_r_010_any_findings.
test_scp_r_010_warn_only_opt_out_observable if {
	input_value := {
		"rule_config": {"auth-canonical-import-fence-disabled": true},
		"auth_contract": scp_r_010_contract,
		"auth_contract_verified": true,
		"adopter_source_files": [{"path": "perm.py", "language": "python", "imports_ct_auth": true, "declared_symbols": ["has_permission"]}],
	}
	count(scp_r_010_deny(input_value)) == 0
	count(scp_r_010_warn(input_value)) >= 1
}

# (disable) rules.SCP-R-010.disable suppresses + observability warn.
test_scp_r_010_disable_suppresses if {
	input_value := {
		"auth_contract": scp_r_010_contract,
		"auth_contract_verified": true,
		"adopter_source_files": [{"path": "auth.py", "language": "python", "imports_ct_auth": true, "declared_symbols": ["validate_token"]}],
	}
	rule_config := {"rules": {"SCP-R-010": {
		"disable": true,
		"justification": "operator override",
		"expires_at": "2099-12-31T00:00:00Z",
	}}}
	count(scp_r_010_deny_full(input_value, [], rule_config)) == 0
	count(scp_r_010_warn_full(input_value, [], rule_config)) >= 1
}

# (waiver) active waiver suppresses + observability warn.
test_scp_r_010_waiver_suppresses if {
	input_value := {
		"auth_contract": scp_r_010_contract,
		"auth_contract_verified": true,
		"adopter_source_files": [{"path": "auth.py", "language": "python", "imports_ct_auth": true, "declared_symbols": ["validate_token"]}],
	}
	waivers := [{"waiver_id": "scp-r-010-grace", "rule_id": "SCP-R-010", "expires_at": "2099-12-31T00:00:00Z"}]
	count(scp_r_010_deny_full(input_value, waivers, {})) == 0
	count(scp_r_010_warn_full(input_value, waivers, {})) >= 1
}
