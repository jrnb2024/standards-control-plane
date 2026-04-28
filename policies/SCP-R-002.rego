package main

import rego.v1

scp_r_002_rule_id := "SCP-R-002"

scp_r_002_remediation_url := "https://github.com/jrnb2024/standards-control-plane-/blob/main/schemas/waiver.schema.json"

scp_r_002_required_keys := {
	"approved_by",
	"created_at",
	"expires_at",
}

deny contains {
	"msg": msg,
	"rule_id": scp_r_002_rule_id,
	"file": "output/findings/waivers.json",
	"remediation_url": scp_r_002_remediation_url,
} if {
	scp_r_002_is_waiver_payload
	some index, entry in input
	not is_object(entry)
	msg := sprintf("waiver entry %d must be an object", [index])
}

deny contains {
	"msg": msg,
	"rule_id": scp_r_002_rule_id,
	"file": "output/findings/waivers.json",
	"remediation_url": scp_r_002_remediation_url,
} if {
	scp_r_002_is_waiver_payload
	some index, entry in input
	is_object(entry)
	some key in scp_r_002_required_keys
	not scp_r_002_has_nonempty_string(entry, key)
	msg := sprintf("waiver entry %d must include %s", [index, key])
}

deny contains {
	"msg": msg,
	"rule_id": scp_r_002_rule_id,
	"file": "output/findings/waivers.json",
	"remediation_url": scp_r_002_remediation_url,
} if {
	scp_r_002_is_waiver_payload
	some index, entry in input
	is_object(entry)
	not scp_r_002_has_nonempty_string(entry, "rule_id")
	not scp_r_002_has_nonempty_string(entry, "finding_id")
	msg := sprintf("waiver entry %d must include either rule_id or finding_id", [index])
}

scp_r_002_is_waiver_payload if {
	is_array(input)
	count(input) == 0
}

scp_r_002_is_waiver_payload if {
	is_array(input)
	some entry in input
	is_object(entry)
	some key in {"approved_by", "created_at", "expires_at", "rule_id", "finding_id", "waiver_id", "reason"}
	object.get(entry, key, null) != null
}

scp_r_002_has_nonempty_string(entry, key) if {
	value := object.get(entry, key, null)
	is_string(value)
	value != ""
}
