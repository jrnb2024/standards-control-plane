# RULE: SCP-R-010 — auth-canonical-import-fence (WP-SCP-028; D-058 auth
# domain). Warn-baseline; deny-promote candidate at D-059.
#
# INTENT (plan §3.2 + autonomous-prompt §0.0(1)): an adopter source file that
# imports the ct-auth SDK must NOT shadow or re-implement the canonical's
# protected primitives. The contract declares TWO severity tiers:
#   protected_primitives.tier_deny[<lang>]  — shadow/re-implement = security
#                                             hole → DENY-class finding
#   protected_primitives.tier_warn[<lang>]  — shadow/re-implement = correctness
#                                             drift → WARN-class finding
# LINKAGE-not-VALUES: the forbidden-symbol sets are READ from CT's signed
# auth-contract-v1.yaml at evaluation time, never copied here.
#
# DEFERRED (R1 CG-MAJ-001): plan §3.2 warn-condition-1 (a same-file function
# with a `_legacy`/`_internal`/`_v1` suffix as a parallel-implementation
# heuristic) is NOT implemented here. The live CT contract expresses severity
# via the tier_deny/tier_warn symbol sets, not suffix patterns, and a suffix
# heuristic needs the companion workflow's file-content extraction. Tracked
# forward as FUP-WP-SCP-028-LEGACY-SUFFIX-WARN-001; this rule's warn class is
# the canonical tier_warn set, which is the LINKAGE-faithful signal.
#
# INPUT CONTRACT (materialised by the sibling companion workflow PR, NOT this
# WP — SCP-R-006 dormancy pattern):
#   input.auth_contract           — parsed CT contract (object); shape per
#                                   schemas/auth-contract-v1.schema.json
#   input.auth_contract_verified  — bool; true iff the workflow cosign-verified
#                                   the contract against auth-contract-v1.yaml.sig.bundle
#                                   (keyless Sigstore OIDC; identity
#                                   .../control-tower/.github/workflows/contract-manifest-publish.yml@refs/heads/main)
#   input.adopter_source_files    — array of {path, language, imports_ct_auth,
#                                   declared_symbols[], reexported_symbols[]}
#                                   extracted by the workflow (Rego cannot AST-parse)
#   input.rule_config             — adopter .scp/rule-config.yaml (opt-out)
# Absent inputs → vacuous-pass (DORMANT until activation).
#
# FAIL-CLOSED: contract present but unverified → signature finding (deny-class,
# rendered ::warning:: while warn-baseline; never blocks on a CT-side hiccup).
#
# Rule-local scp_r_010_* helpers (per-rule-coverage discipline). Reuses only
# scp_active_waiver_for + scp_rule_config_disabled from scp_common.rego.

package main

import rego.v1

scp_r_010_rule_id := "SCP-R-010"

scp_r_010_remediation_url := concat("", [
	"https://github.com/jrnb2024/standards-control-plane/blob/main/",
	"docs/plans/WP-SCP-028-auth-canonical-conformance-v1.md",
])

default scp_r_010_opted_out := false

scp_r_010_opted_out if {
	rc := object.get(input, "rule_config", {})
	is_object(rc)
	object.get(rc, "auth-canonical-import-fence-disabled", false) == true
}

scp_r_010_contract_verified if {
	object.get(input, "auth_contract_verified", false) == true
}

scp_r_010_contract := contract if {
	contract := object.get(input, "auth_contract", {})
	is_object(contract)
}

scp_r_010_source_files := files if {
	files := object.get(input, "adopter_source_files", [])
	is_array(files)
}

# Files that import the ct-auth SDK (the fence only applies to these).
scp_r_010_importing_files := [file |
	some file in scp_r_010_source_files
	is_object(file)
	object.get(file, "imports_ct_auth", false) == true
]

# Forbidden-symbol list for a tier + language (or [] when absent).
scp_r_010_tier_symbols(tier, lang) := symbols if {
	pp := object.get(scp_r_010_contract, "protected_primitives", {})
	tier_map := object.get(pp, tier, {})
	symbols := object.get(tier_map, lang, [])
	is_array(symbols)
}

# All symbols an adopter file declares OR re-exports (the shadow surface).
scp_r_010_file_symbols(file) := symbols if {
	declared := object.get(file, "declared_symbols", [])
	reexported := object.get(file, "reexported_symbols", [])
	symbols := array.concat(scp_r_010_as_array(declared), scp_r_010_as_array(reexported))
}

scp_r_010_as_array(x) := x if {
	is_array(x)
}

scp_r_010_as_array(x) := [] if {
	not is_array(x)
}

scp_r_010_finding(file, message) := {
	"rule_id": scp_r_010_rule_id,
	"file": file,
	"message": message,
	"remediation_url": scp_r_010_remediation_url,
}

# --- fail-closed: contract present but unverified -------------------------
scp_r_010_deny_findings contains finding if {
	count(scp_r_010_importing_files) > 0
	scp_r_010_contract != {}
	not scp_r_010_contract_verified
	finding := scp_r_010_finding(
		"auth-contract-v1.yaml",
		"SCP-R-010: CT auth-contract present but its signature did NOT verify (cosign/.sig.bundle anchor). Import-fence cannot be trusted; fail-closed.",
	)
}

# --- deny-class: a tier_deny canonical primitive is shadowed/re-implemented
scp_r_010_deny_findings contains finding if {
	scp_r_010_contract_verified
	some file in scp_r_010_importing_files
	lang := object.get(file, "language", "")
	some sym in scp_r_010_file_symbols(file)
	sym in scp_r_010_tier_symbols("tier_deny", lang)
	finding := scp_r_010_finding(
		object.get(file, "path", ""),
		sprintf(
			"SCP-R-010: file imports ct-auth yet declares/re-exports '%s', a tier_deny canonical primitive (security-class). Use the SDK's primitive; do not shadow it. See CT auth-contract-v1.yaml protected_primitives.tier_deny.%s.",
			[sym, lang],
		),
	)
}

# --- warn-class: a tier_warn canonical primitive is shadowed --------------
scp_r_010_warn_findings contains finding if {
	scp_r_010_contract_verified
	some file in scp_r_010_importing_files
	lang := object.get(file, "language", "")
	some sym in scp_r_010_file_symbols(file)
	sym in scp_r_010_tier_symbols("tier_warn", lang)
	finding := scp_r_010_finding(
		object.get(file, "path", ""),
		sprintf(
			"SCP-R-010: file imports ct-auth yet declares/re-exports '%s', a tier_warn canonical primitive (correctness drift). Prefer the SDK's primitive. See CT auth-contract-v1.yaml protected_primitives.tier_warn.%s.",
			[sym, lang],
		),
	)
}

# True iff the rule produced ANY finding (deny or warn) — guards the
# suppression-observability records so a suppressed warn-only finding is still
# observable (R1 CORR-MIN-001 / CG-MIN-006).
scp_r_010_any_findings if {
	count(scp_r_010_deny_findings) > 0
}

scp_r_010_any_findings if {
	count(scp_r_010_warn_findings) > 0
}

# Public deny rule (tier_deny shadows + fail-closed). Warn-baseline membership
# demotes to ::warning:: until D-059 deny-promotion.
deny contains output if {
	some finding in scp_r_010_deny_findings
	not scp_r_010_opted_out
	not scp_active_waiver_for(scp_r_010_rule_id)
	not scp_rule_config_disabled(scp_r_010_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

# Public warn rule (tier_warn shadows — inherently warn, not deny even post-D-059).
warn contains output if {
	some finding in scp_r_010_warn_findings
	not scp_r_010_opted_out
	not scp_active_waiver_for(scp_r_010_rule_id)
	not scp_rule_config_disabled(scp_r_010_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

# Suppression-observability warn: active waiver against SCP-R-010.
warn contains record if {
	scp_r_010_any_findings
	some w in scp_waivers
	object.get(w, "rule_id", "") == scp_r_010_rule_id
	not scp_waiver_expired(w)
	record := {
		"kind": "waiver",
		"rule_id": scp_r_010_rule_id,
		"waiver_id": object.get(w, "waiver_id", ""),
		"msg": sprintf("SCP-R-010 findings suppressed by active waiver %s", [object.get(w, "waiver_id", "")]),
	}
}

# Suppression-observability warn: disable / opt-out.
warn contains record if {
	scp_r_010_any_findings
	scp_rule_config_disabled(scp_r_010_rule_id)
	record := {
		"kind": "rule-config-disable",
		"rule_id": scp_r_010_rule_id,
		"msg": "SCP-R-010 findings suppressed by .scp/rule-config.yaml disable: true",
	}
}

warn contains record if {
	scp_r_010_any_findings
	scp_r_010_opted_out
	record := {
		"kind": "rule-config-disable",
		"rule_id": scp_r_010_rule_id,
		"msg": "SCP-R-010 findings suppressed by .scp/rule-config.yaml auth-canonical-import-fence-disabled: true",
	}
}
