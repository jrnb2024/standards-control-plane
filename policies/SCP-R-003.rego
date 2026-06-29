package main

import rego.v1

scp_r_003_rule_id := "SCP-R-003"

scp_r_003_remediation_url := concat("", [
	"https://github.com/jrnb2024/standards-control-plane/blob/main/",
	"docs/adoption/ADOPT-001-project-onboarding.md",
])

scp_r_003_manifest_names := {
	"package.json",
	"pyproject.toml",
	"go.mod",
}

# WP-SCP-022 slice 020C.1 (i)+(v): factor potential denies into
# scp_r_003_raw_findings; public `deny` filters by waiver/rule-config
# suppression; `warn` rules emit observability for suppressed findings.
scp_r_003_raw_findings contains finding if {
	scp_r_003_manifest_input
	source_file := object.get(input, "source_file", "")
	content := object.get(input, "content", "")
	not scp_r_003_has_attestation_marker(content)
	finding := {
		"message": sprintf("%s must declare the vendoring attestation marker `scp:vendoring-attested`", [source_file]),
		"rule_id": scp_r_003_rule_id,
		"file": source_file,
		"remediation_url": scp_r_003_remediation_url,
	}
}

# Conftest 0.x requires deny outputs to carry `msg`; we union it from
# `message` so downstream consumers reading `.message` keep working.
deny contains output if {
	some finding in scp_r_003_raw_findings
	not scp_active_waiver_for(scp_r_003_rule_id)
	not scp_rule_config_disabled(scp_r_003_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

warn contains record if {
	count(scp_r_003_raw_findings) > 0
	some w in scp_waivers
	object.get(w, "rule_id", "") == scp_r_003_rule_id
	not scp_waiver_expired(w)
	record := {
		"kind": "waiver",
		"rule_id": scp_r_003_rule_id,
		"waiver_id": object.get(w, "waiver_id", ""),
		"finding_id": object.get(w, "finding_id", ""),
		"expires_at": object.get(w, "expires_at", ""),
		"file": object.get(input, "source_file", ""),
		"msg": sprintf(
			"%s suppressed by waiver (waiver_id=%s, expires_at=%s)",
			[scp_r_003_rule_id, object.get(w, "waiver_id", ""), object.get(w, "expires_at", "")],
		),
	}
}

warn contains record if {
	count(scp_r_003_raw_findings) > 0
	scp_rule_config_disabled(scp_r_003_rule_id)
	cfg := scp_rule_config_entry(scp_r_003_rule_id)
	record := {
		"kind": "rule_config",
		"rule_id": scp_r_003_rule_id,
		"reason": "rule-config override",
		"expires_at": object.get(cfg, "expires_at", ""),
		"msg": sprintf(
			"%s suppressed by .scp/rule-config.yaml (expires_at=%s)",
			[scp_r_003_rule_id, object.get(cfg, "expires_at", "")],
		),
	}
}

scp_r_003_manifest_input if {
	source_file := object.get(input, "source_file", "")
	source_file != ""
	scp_r_003_manifest_names[scp_r_003_basename(source_file)]
	content := object.get(input, "content", "")
	is_string(content)
}

scp_r_003_has_attestation_marker(content) if {
	regex.match(`(?m)^\s*(#|//)\s*scp:vendoring-attested\s*$`, content)
}

scp_r_003_has_attestation_marker(content) if {
	regex.match(`(?s).*"scp:vendoring-attested"\s*:\s*true.*`, content)
}

scp_r_003_basename(path) := name if {
	parts := split(path, "/")
	name := parts[count(parts) - 1]
}
