package main

import rego.v1

scp_r_002_rule_id := "SCP-R-002"

scp_r_002_remediation_url := "https://github.com/jrnb2024/standards-control-plane-/blob/main/schemas/waiver.schema.json"

scp_r_002_required_keys := {
	"approved_by",
	"created_at",
	"expires_at",
	"reason",
}

scp_r_002_now_ns := time.now_ns()

deny contains {
	"message": message,
	"rule_id": scp_r_002_rule_id,
	"file": "output/findings/waivers.json",
	"remediation_url": scp_r_002_remediation_url,
} if {
	is_array(input)
	some index, entry in input
	not is_object(entry)
	message := sprintf("waiver entry %d must be an object", [index])
}

deny contains {
	"message": message,
	"rule_id": scp_r_002_rule_id,
	"file": "output/findings/waivers.json",
	"remediation_url": scp_r_002_remediation_url,
} if {
	scp_r_002_is_waiver_payload
	some index, entry in input
	is_object(entry)
	some key in scp_r_002_required_keys
	not scp_r_002_has_nonempty_string(entry, key)
	message := sprintf("waiver entry %d must include %s", [index, key])
}

deny contains {
	"message": message,
	"rule_id": scp_r_002_rule_id,
	"file": "output/findings/waivers.json",
	"remediation_url": scp_r_002_remediation_url,
} if {
	scp_r_002_is_waiver_payload
	some index, entry in input
	is_object(entry)
	not scp_r_002_has_nonempty_string(entry, "rule_id")
	not scp_r_002_has_nonempty_string(entry, "finding_id")
	message := sprintf("waiver entry %d must include either rule_id or finding_id", [index])
}

deny contains {
	"message": message,
	"rule_id": scp_r_002_rule_id,
	"file": "output/findings/waivers.json",
	"remediation_url": scp_r_002_remediation_url,
} if {
	scp_r_002_is_waiver_payload
	some index, entry in input
	is_object(entry)
	some key in {"created_at", "expires_at"}
	scp_r_002_has_nonempty_string(entry, key)
	not scp_r_002_has_valid_date_or_datetime(entry, key)
	message := sprintf("waiver entry %d %s must be a valid RFC 3339 date or date-time", [index, key])
}

deny contains {
	"message": message,
	"rule_id": scp_r_002_rule_id,
	"file": "output/findings/waivers.json",
	"remediation_url": scp_r_002_remediation_url,
} if {
	scp_r_002_is_waiver_payload
	some index, entry in input
	is_object(entry)
	scp_r_002_has_nonempty_string(entry, "expires_at")
	expires_at := object.get(entry, "expires_at", "")
	expiry_ns := scp_r_002_dateish_ns(expires_at)
	expiry_ns <= scp_r_002_now_ns
	message := sprintf("waiver entry %d expires_at must be in the future", [index])
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

scp_r_002_has_valid_date_or_datetime(entry, key) if {
	value := object.get(entry, key, null)
	scp_r_002_dateish_ns(value)
}

scp_r_002_dateish_ns(value) := ns if {
	is_string(value)
	regex.match(`^[0-9]{4}-[0-9]{2}-[0-9]{2}$`, value)
	ns := time.parse_rfc3339_ns(sprintf("%sT00:00:00Z", [value]))
}

scp_r_002_dateish_ns(value) := ns if {
	is_string(value)
	regex.match(`^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})$`, value)
	ns := time.parse_rfc3339_ns(value)
}
