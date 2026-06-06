# RULE: SCP-R-011 — auth-contract-claim-shape (WP-SCP-028; D-058 auth
# domain). Warn-baseline; deny-promote candidate at D-059.
#
# INTENT (plan §3.3 + autonomous-prompt §0.0(2)+(3)): adopter code that handles
# Authorization headers must conform to CT's current claim_shape_version (live
# 2.0.0; MAJOR per CT ASC-2026-05-30-002) and must only hardcode issuer strings
# that appear in CT's canonical issuers list. A Claims/JwtPayload type matching
# the old (1.x) shape is drift → DENY-class; a hardcoded issuer outside the
# canonical issuers set is drift → DENY-class; a declared claim_shape_version
# that lags CT's current by >=1 MAJOR is → WARN-class. LINKAGE-not-VALUES: the
# claim_shape_version + issuer set are READ from CT's signed contract, not copied.
# NOTE: the live contract exposes an `issuers:` array (enumerated iss values),
# NOT a `canonical_issuer_pattern` regex (that §3.3 field name does not exist).
#
# INPUT CONTRACT (materialised by the sibling companion workflow PR, NOT this WP):
#   input.auth_contract           — parsed CT contract (object)
#   input.auth_contract_verified  — bool; cosign-verified against the .sig.bundle
#   input.adopter_auth_handlers   — array of {path, language, handles_authorization,
#                                   declared_claim_shape_version, hardcoded_issuers[],
#                                   claims_uses_old_shape} extracted by the workflow
#   input.rule_config             — adopter .scp/rule-config.yaml (opt-out)
# Absent inputs → vacuous-pass (DORMANT until activation). Fail-closed on a
# present-but-unverified contract (signature finding; warn-baseline-rendered).
#
# Rule-local scp_r_011_* helpers. Reuses only scp_active_waiver_for +
# scp_rule_config_disabled from scp_common.rego.

package main

import rego.v1

scp_r_011_rule_id := "SCP-R-011"

scp_r_011_remediation_url := concat("", [
	"https://github.com/jrnb2024/standards-control-plane/blob/main/",
	"docs/plans/WP-SCP-028-auth-canonical-conformance-v1.md",
])

default scp_r_011_opted_out := false

scp_r_011_opted_out if {
	rc := object.get(input, "rule_config", {})
	is_object(rc)
	object.get(rc, "auth-contract-claim-shape-disabled", false) == true
}

scp_r_011_contract_verified if {
	object.get(input, "auth_contract_verified", false) == true
}

scp_r_011_contract := contract if {
	contract := object.get(input, "auth_contract", {})
	is_object(contract)
}

scp_r_011_handlers := handlers if {
	handlers := object.get(input, "adopter_auth_handlers", [])
	is_array(handlers)
}

# Handlers that actually touch Authorization (the rule only applies to these).
scp_r_011_auth_handlers := [h |
	some h in scp_r_011_handlers
	is_object(h)
	object.get(h, "handles_authorization", false) == true
]

# Canonical issuer iss-set (from the contract's issuers array).
scp_r_011_canonical_issuers contains iss if {
	issuers := object.get(scp_r_011_contract, "issuers", [])
	is_array(issuers)
	some entry in issuers
	is_object(entry)
	iss := object.get(entry, "iss", "")
	iss != ""
}

scp_r_011_major(v) := n if {
	is_string(v)
	raw := split(v, ".")
	count(raw) == 3
	n := to_number(raw[0])
}

scp_r_011_finding(file, message) := {
	"rule_id": scp_r_011_rule_id,
	"file": file,
	"message": message,
	"remediation_url": scp_r_011_remediation_url,
}

# --- fail-closed: contract present but unverified -------------------------
scp_r_011_deny_findings contains finding if {
	count(scp_r_011_auth_handlers) > 0
	scp_r_011_contract != {}
	not scp_r_011_contract_verified
	finding := scp_r_011_finding(
		"auth-contract-v1.yaml",
		"SCP-R-011: CT auth-contract present but its signature did NOT verify (cosign/.sig.bundle anchor). Claim-shape conformance cannot be trusted; fail-closed.",
	)
}

# --- deny-class: adopter Claims type matches the old (pre-current) shape ---
scp_r_011_deny_findings contains finding if {
	scp_r_011_contract_verified
	some h in scp_r_011_auth_handlers
	object.get(h, "claims_uses_old_shape", false) == true
	csv := object.get(scp_r_011_contract, "claim_shape_version", "")
	finding := scp_r_011_finding(
		object.get(h, "path", ""),
		sprintf(
			"SCP-R-011: Authorization-handling code declares a Claims/JwtPayload type matching an OLD claim shape; CT's current claim_shape_version is %s. Update the type to the current shape. See CT auth-contract-v1.yaml.",
			[csv],
		),
	)
}

# --- deny-class: hardcoded issuer not in the canonical issuers set ---------
scp_r_011_deny_findings contains finding if {
	scp_r_011_contract_verified
	some h in scp_r_011_auth_handlers
	issuers := object.get(h, "hardcoded_issuers", [])
	is_array(issuers)
	some iss in issuers
	is_string(iss)
	iss != ""
	not iss in scp_r_011_canonical_issuers
	finding := scp_r_011_finding(
		object.get(h, "path", ""),
		sprintf(
			"SCP-R-011: hardcoded JWT issuer '%s' is not in CT's canonical issuers set. Use a canonical issuer or read it from config. See CT auth-contract-v1.yaml issuers.",
			[iss],
		),
	)
}

# --- warn-class: declared claim_shape_version lags current by >=1 MAJOR ----
scp_r_011_warn_findings contains finding if {
	scp_r_011_contract_verified
	some h in scp_r_011_auth_handlers
	declared := object.get(h, "declared_claim_shape_version", "")
	declared != ""
	canonical := object.get(scp_r_011_contract, "claim_shape_version", "")
	scp_r_011_major(declared) < scp_r_011_major(canonical)
	finding := scp_r_011_finding(
		object.get(h, "path", ""),
		sprintf(
			"SCP-R-011: declared claim_shape_version %s lags CT's current %s by >=1 MAJOR. Align to the current claim shape. See CT auth-contract-v1.yaml.",
			[declared, canonical],
		),
	)
}

# True iff the rule produced ANY finding (deny or warn) — guards the
# suppression-observability records so a suppressed warn-only finding is still
# observable (R1 CORR-MIN-001 / CG-MIN-006).
scp_r_011_any_findings if {
	count(scp_r_011_deny_findings) > 0
}

scp_r_011_any_findings if {
	count(scp_r_011_warn_findings) > 0
}

# Public deny rule (old-shape + invalid-issuer + fail-closed). Warn-baseline
# membership demotes to ::warning:: until D-059.
deny contains output if {
	some finding in scp_r_011_deny_findings
	not scp_r_011_opted_out
	not scp_active_waiver_for(scp_r_011_rule_id)
	not scp_rule_config_disabled(scp_r_011_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

# Public warn rule (MAJOR-lag — inherently warn).
warn contains output if {
	some finding in scp_r_011_warn_findings
	not scp_r_011_opted_out
	not scp_active_waiver_for(scp_r_011_rule_id)
	not scp_rule_config_disabled(scp_r_011_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

# Suppression-observability warn: active waiver against SCP-R-011.
warn contains record if {
	scp_r_011_any_findings
	some w in scp_waivers
	object.get(w, "rule_id", "") == scp_r_011_rule_id
	not scp_waiver_expired(w)
	record := {
		"kind": "waiver",
		"rule_id": scp_r_011_rule_id,
		"waiver_id": object.get(w, "waiver_id", ""),
		"msg": sprintf("SCP-R-011 findings suppressed by active waiver %s", [object.get(w, "waiver_id", "")]),
	}
}

# Suppression-observability warn: disable / opt-out.
warn contains record if {
	scp_r_011_any_findings
	scp_rule_config_disabled(scp_r_011_rule_id)
	record := {
		"kind": "rule-config-disable",
		"rule_id": scp_r_011_rule_id,
		"msg": "SCP-R-011 findings suppressed by .scp/rule-config.yaml disable: true",
	}
}

warn contains record if {
	scp_r_011_any_findings
	scp_r_011_opted_out
	record := {
		"kind": "rule-config-disable",
		"rule_id": scp_r_011_rule_id,
		"msg": "SCP-R-011 findings suppressed by .scp/rule-config.yaml auth-contract-claim-shape-disabled: true",
	}
}
