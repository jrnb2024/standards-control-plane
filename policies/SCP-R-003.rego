package main

import rego.v1

scp_r_003_rule_id := "SCP-R-003"

scp_r_003_remediation_url := concat("", [
	"https://github.com/jrnb2024/standards-control-plane-/blob/main/",
	"docs/adoption/ADOPT-001-project-onboarding.md",
])

scp_r_003_manifest_names := {
	"package.json",
	"pyproject.toml",
	"go.mod",
}

deny contains {
	"message": message,
	"rule_id": scp_r_003_rule_id,
	"file": source_file,
	"remediation_url": scp_r_003_remediation_url,
} if {
	scp_r_003_manifest_input
	source_file := object.get(input, "source_file", "")
	content := object.get(input, "content", "")
	not scp_r_003_has_attestation_marker(content)
	message := sprintf("%s must declare the vendoring attestation marker `scp:vendoring-attested`", [source_file])
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
