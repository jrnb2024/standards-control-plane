package main

import rego.v1

scp_r_001_rule_id := "SCP-R-001"

scp_r_001_remediation_url := concat("", [
	"https://github.com/jrnb2024/standards-control-plane-/blob/main/",
	"standards/service-lifecycle/SVC-003.md",
])

scp_r_001_allowed_modes := {
	"mode.user_oidc",
	"mode.service_rs256",
	"mode.api_key",
	"mode.bearer_legacy",
}

scp_r_001_allowed_close_dates := {
	"2026-06-30",
	"2026-09-30",
}

scp_r_001_now_ns := time.now_ns()

# WP-SCP-022 slice 020C.1 (i)+(v): every potential deny is computed into
# scp_r_001_raw_findings first; the public `deny` rule emits only those
# not suppressed by a waiver or by .scp/rule-config.yaml. `warn` rules
# below emit observability records for suppressed findings.
scp_r_001_raw_findings contains finding if {
	some record in scp_r_001_mode_records
	not is_object(record.entry)
	finding := {
		"message": sprintf("%s must be an object with a mode field", [record.path]),
		"rule_id": scp_r_001_rule_id,
		"file": "services.yml",
		"remediation_url": scp_r_001_remediation_url,
	}
}

scp_r_001_raw_findings contains finding if {
	some record in scp_r_001_mode_records
	is_object(record.entry)
	mode := object.get(record.entry, "mode", "")
	not scp_r_001_allowed_modes[mode]
	finding := {
		"message": sprintf(
			"%s.mode must use an approved SVC-003 mode: %v",
			[record.path, sort([mode_name | mode_name := scp_r_001_allowed_modes[_]])],
		),
		"rule_id": scp_r_001_rule_id,
		"file": "services.yml",
		"remediation_url": scp_r_001_remediation_url,
	}
}

scp_r_001_raw_findings contains finding if {
	some record in scp_r_001_mode_records
	is_object(record.entry)
	record.entry.mode == "mode.bearer_legacy"
	close_date := object.get(record.entry, "deprecation_close_date", "")
	not scp_r_001_allowed_close_dates[close_date]
	finding := {
		"message": sprintf(
			"%s.deprecation_close_date must be one of %v when mode=mode.bearer_legacy",
			[record.path, sort([date | date := scp_r_001_allowed_close_dates[_]])],
		),
		"rule_id": scp_r_001_rule_id,
		"file": "services.yml",
		"remediation_url": scp_r_001_remediation_url,
	}
}

scp_r_001_raw_findings contains finding if {
	some record in scp_r_001_mode_records
	is_object(record.entry)
	record.entry.mode == "mode.bearer_legacy"
	close_date := object.get(record.entry, "deprecation_close_date", "")
	scp_r_001_allowed_close_dates[close_date]
	scp_r_001_close_date_ns(close_date) < scp_r_001_now_ns
	finding := {
		"message": sprintf(
			"%s.deprecation_close_date must not be in the past when mode=mode.bearer_legacy",
			[record.path],
		),
		"rule_id": scp_r_001_rule_id,
		"file": "services.yml",
		"remediation_url": scp_r_001_remediation_url,
	}
}

# Public deny: emits a raw finding only when no active waiver and no
# rule-config disable applies for SCP-R-001. Conftest 0.x requires every
# deny output object to carry a `msg` field; we union it from the
# finding's `message` so existing downstream consumers (lib post-processor,
# summary schema, tests) that read `.message` keep working.
deny contains output if {
	some finding in scp_r_001_raw_findings
	not scp_active_waiver_for(scp_r_001_rule_id)
	not scp_rule_config_disabled(scp_r_001_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

# Observability: emit one warn per matching active waiver, but only when
# there's at least one would-be finding to suppress (avoids warn noise
# when the rule passes outright).
warn contains record if {
	count(scp_r_001_raw_findings) > 0
	some w in scp_waivers
	object.get(w, "rule_id", "") == scp_r_001_rule_id
	not scp_waiver_expired(w)
	record := {
		"kind": "waiver",
		"rule_id": scp_r_001_rule_id,
		"waiver_id": object.get(w, "waiver_id", ""),
		"finding_id": object.get(w, "finding_id", ""),
		"expires_at": object.get(w, "expires_at", ""),
		"file": "services.yml",
	}
}

# Observability: emit a warn when rule-config disable applies for this
# rule, regardless of whether expiry has passed (per spec, expired
# rule-config still suppresses for one release; the workflow emits a
# separate ::warning:: annotation in that case).
warn contains record if {
	count(scp_r_001_raw_findings) > 0
	scp_rule_config_disabled(scp_r_001_rule_id)
	cfg := scp_rule_config_entry(scp_r_001_rule_id)
	record := {
		"kind": "rule_config",
		"rule_id": scp_r_001_rule_id,
		"reason": "rule-config override",
		"expires_at": object.get(cfg, "expires_at", ""),
	}
}

scp_r_001_close_date_ns(close_date) := ns if {
	ns := time.parse_rfc3339_ns(sprintf("%sT00:00:00Z", [close_date]))
}

scp_r_001_mode_records contains {
	"path": sprintf(
		"services.%s.%s.runtime_contract.auth_contract.accepted_modes[%d]",
		[service_name, environment_name, index],
	),
	"entry": entry,
} if {
	services := object.get(input, "services", {})
	some service_name in object.keys(services)
	service := services[service_name]
	is_object(service)
	some environment_name in object.keys(service)
	environment := service[environment_name]
	is_object(environment)
	runtime_contract := object.get(environment, "runtime_contract", null)
	is_object(runtime_contract)
	auth_contract := object.get(runtime_contract, "auth_contract", null)
	is_object(auth_contract)
	accepted_modes := object.get(auth_contract, "accepted_modes", null)
	is_array(accepted_modes)
	some index, entry in accepted_modes
}

scp_r_001_mode_records contains {
	"path": sprintf("services.%s.auth", [service_name]),
	"entry": auth,
} if {
	services := object.get(input, "services", {})
	some service_name in object.keys(services)
	service := services[service_name]
	is_object(service)
	auth := object.get(service, "auth", null)
	is_object(auth)
}
