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

deny contains {
	"msg": msg,
	"rule_id": scp_r_001_rule_id,
	"file": "services.yml",
	"remediation_url": scp_r_001_remediation_url,
} if {
	some record in scp_r_001_mode_records
	not is_object(record.entry)
	msg := sprintf("%s must be an object with a mode field", [record.path])
}

deny contains {
	"msg": msg,
	"rule_id": scp_r_001_rule_id,
	"file": "services.yml",
	"remediation_url": scp_r_001_remediation_url,
} if {
	some record in scp_r_001_mode_records
	is_object(record.entry)
	mode := object.get(record.entry, "mode", "")
	not scp_r_001_allowed_modes[mode]
	msg := sprintf(
		"%s.mode must use an approved SVC-003 mode: %v",
		[record.path, sort([mode_name | mode_name := scp_r_001_allowed_modes[_]])],
	)
}

deny contains {
	"msg": msg,
	"rule_id": scp_r_001_rule_id,
	"file": "services.yml",
	"remediation_url": scp_r_001_remediation_url,
} if {
	some record in scp_r_001_mode_records
	is_object(record.entry)
	record.entry.mode == "mode.bearer_legacy"
	close_date := object.get(record.entry, "deprecation_close_date", "")
	not scp_r_001_allowed_close_dates[close_date]
	msg := sprintf(
		"%s.deprecation_close_date must be one of %v when mode=mode.bearer_legacy",
		[record.path, sort([date | date := scp_r_001_allowed_close_dates[_]])],
	)
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
