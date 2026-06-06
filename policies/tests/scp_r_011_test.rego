package main_test

import data.main
import rego.v1

# SCP-R-011 (auth-contract-claim-shape). Reads input.auth_contract (+_verified)
# + input.adopter_auth_handlers. old-shape/invalid-issuer→deny; MAJOR-lag→warn.
# Dormant until the companion workflow materialises.

scp_r_011_deny(input_value) := [f |
	some f in main.deny with input as input_value
	f.rule_id == "SCP-R-011"
]

scp_r_011_warn(input_value) := [r |
	some r in main.warn with input as input_value
	r.rule_id == "SCP-R-011"
]

scp_r_011_deny_full(input_value, waivers, rule_config) := [f |
	some f in main.deny with input as input_value
		with data.waivers as waivers
		with data.rule_config as rule_config
	f.rule_id == "SCP-R-011"
]

scp_r_011_warn_full(input_value, waivers, rule_config) := [r |
	some r in main.warn with input as input_value
		with data.waivers as waivers
		with data.rule_config as rule_config
	r.rule_id == "SCP-R-011"
]

scp_r_011_contract := {
	"claim_shape_version": "2.0.0",
	"issuers": [{"iss": "https://ct.brokapps.ai"}, {"iss": "control-tower"}],
}

# (vacuous) no handler touches Authorization → no findings.
test_scp_r_011_vacuous_no_handler if {
	input_value := {
		"auth_contract": scp_r_011_contract,
		"auth_contract_verified": true,
		"adopter_auth_handlers": [{"path": "a.py", "language": "python", "handles_authorization": false, "claims_uses_old_shape": true}],
	}
	count(scp_r_011_deny(input_value)) == 0
}

# (fail-closed) handler + contract present but unverified → 1 deny.
test_scp_r_011_fail_closed_unverified if {
	input_value := {
		"auth_contract": scp_r_011_contract,
		"auth_contract_verified": false,
		"adopter_auth_handlers": [{"path": "a.py", "language": "python", "handles_authorization": true}],
	}
	count(scp_r_011_deny(input_value)) == 1
}

# (deny) Claims type matches the old shape → deny.
test_scp_r_011_deny_old_shape if {
	input_value := {
		"auth_contract": scp_r_011_contract,
		"auth_contract_verified": true,
		"adopter_auth_handlers": [{"path": "claims.py", "language": "python", "handles_authorization": true, "claims_uses_old_shape": true}],
	}
	count(scp_r_011_deny(input_value)) == 1
}

# (deny) hardcoded issuer outside the canonical set → deny.
test_scp_r_011_deny_bad_issuer if {
	input_value := {
		"auth_contract": scp_r_011_contract,
		"auth_contract_verified": true,
		"adopter_auth_handlers": [{"path": "verify.py", "language": "python", "handles_authorization": true, "hardcoded_issuers": ["https://evil.example.com"]}],
	}
	count(scp_r_011_deny(input_value)) == 1
}

# (pass) hardcoded issuer that IS canonical → no finding.
test_scp_r_011_pass_canonical_issuer if {
	input_value := {
		"auth_contract": scp_r_011_contract,
		"auth_contract_verified": true,
		"adopter_auth_handlers": [{"path": "verify.py", "language": "python", "handles_authorization": true, "hardcoded_issuers": ["https://ct.brokapps.ai"]}],
	}
	count(scp_r_011_deny(input_value)) == 0
	count(scp_r_011_warn(input_value)) == 0
}

# (warn) declared claim_shape_version lags current by >=1 MAJOR → warn.
test_scp_r_011_warn_major_lag if {
	input_value := {
		"auth_contract": scp_r_011_contract,
		"auth_contract_verified": true,
		"adopter_auth_handlers": [{"path": "claims.py", "language": "python", "handles_authorization": true, "declared_claim_shape_version": "1.1.0"}],
	}
	count(scp_r_011_deny(input_value)) == 0
	count(scp_r_011_warn(input_value)) >= 1
}

# (pass) declared claim_shape_version current → no finding.
test_scp_r_011_pass_current_shape if {
	input_value := {
		"auth_contract": scp_r_011_contract,
		"auth_contract_verified": true,
		"adopter_auth_handlers": [{"path": "claims.py", "language": "python", "handles_authorization": true, "declared_claim_shape_version": "2.0.0"}],
	}
	count(scp_r_011_deny(input_value)) == 0
	count(scp_r_011_warn(input_value)) == 0
}

# (opt-out) bespoke key suppresses + observability warn.
test_scp_r_011_opt_out_suppresses if {
	input_value := {
		"rule_config": {"auth-contract-claim-shape-disabled": true},
		"auth_contract": scp_r_011_contract,
		"auth_contract_verified": true,
		"adopter_auth_handlers": [{"path": "claims.py", "language": "python", "handles_authorization": true, "claims_uses_old_shape": true}],
	}
	count(scp_r_011_deny(input_value)) == 0
	count(scp_r_011_warn(input_value)) >= 1
}

# (warn-only suppression) MAJOR-lag (warn-class, no deny) + opt-out → deny==0
# + observability warn — exercises the warn branch of scp_r_011_any_findings.
test_scp_r_011_warn_only_opt_out_observable if {
	input_value := {
		"rule_config": {"auth-contract-claim-shape-disabled": true},
		"auth_contract": scp_r_011_contract,
		"auth_contract_verified": true,
		"adopter_auth_handlers": [{"path": "claims.py", "language": "python", "handles_authorization": true, "declared_claim_shape_version": "1.1.0"}],
	}
	count(scp_r_011_deny(input_value)) == 0
	count(scp_r_011_warn(input_value)) >= 1
}

# (disable) rules.SCP-R-011.disable suppresses + observability warn.
test_scp_r_011_disable_suppresses if {
	input_value := {
		"auth_contract": scp_r_011_contract,
		"auth_contract_verified": true,
		"adopter_auth_handlers": [{"path": "claims.py", "language": "python", "handles_authorization": true, "claims_uses_old_shape": true}],
	}
	rule_config := {"rules": {"SCP-R-011": {
		"disable": true,
		"justification": "operator override",
		"expires_at": "2099-12-31T00:00:00Z",
	}}}
	count(scp_r_011_deny_full(input_value, [], rule_config)) == 0
	count(scp_r_011_warn_full(input_value, [], rule_config)) >= 1
}

# (waiver) active waiver suppresses + observability warn.
test_scp_r_011_waiver_suppresses if {
	input_value := {
		"auth_contract": scp_r_011_contract,
		"auth_contract_verified": true,
		"adopter_auth_handlers": [{"path": "claims.py", "language": "python", "handles_authorization": true, "claims_uses_old_shape": true}],
	}
	waivers := [{"waiver_id": "scp-r-011-grace", "rule_id": "SCP-R-011", "expires_at": "2099-12-31T00:00:00Z"}]
	count(scp_r_011_deny_full(input_value, waivers, {})) == 0
	count(scp_r_011_warn_full(input_value, waivers, {})) >= 1
}
