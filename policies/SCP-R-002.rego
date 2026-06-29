package main

import rego.v1

scp_r_002_rule_id := "SCP-R-002"

scp_r_002_remediation_url := "https://github.com/jrnb2024/standards-control-plane/blob/main/schemas/waiver.schema.json"

scp_r_002_required_keys := {
	"approved_by",
	"created_at",
	"expires_at",
	"reason",
}

scp_r_002_now_ns := time.now_ns()

# WP-SCP-022 slice 020C.1 (i)+(v): every potential deny is computed into
# scp_r_002_raw_findings first; the public `deny` rule emits only those
# not suppressed by a waiver against SCP-R-002 or by .scp/rule-config.yaml.
#
# Closes WP-SCP-022 R2 F-R2-COR-002: a malformed waivers.json (null,
# string) silently passed all per-entry rules. Top-level shape check
# fires before per-entry rules.
#
# Scope note (TF-008): this rule is NOT path-scoped — conftest invokes
# every rego rule against every changed file, so SCP-R-002 sees
# services.yml, expected-annotations.json, and any other dict-shaped
# payload. A naive `not is_array(input)` deny would fire on every
# non-waiver file and break adopters' regular PR runs. The rule is
# therefore narrowed to fire on null and string roots only — the
# realistic malformed-waivers shapes for this gap window. Dict-shaped
# non-arrays (e.g. `{"approved_by": ...}` as a top-level waiver-with-no-array)
# are covered by per-entry SCP-R-002 tests when wrapped as `[{...}]`,
# and by per-rule unit tests via `with input as ...`. Path-scoped
# routing (e.g. only run SCP-R-002 when the file basename is
# waivers.json) is tracked for v1.1 as TF-008.
scp_r_002_raw_findings contains finding if {
	not is_array(input)
	scp_r_002_is_malformed_root
	finding := {
		"message": "waivers.json root must be a JSON array of waiver entry objects",
		"rule_id": scp_r_002_rule_id,
		"file": "output/findings/waivers.json",
		"remediation_url": scp_r_002_remediation_url,
	}
}

# A malformed waivers.json root, in scope for SCP-R-002 v1.0.0:
# - null (file empty / undefined input)
# - string (text instead of JSON array)
# Excluded for v1.0.0 (dict-shaped): conftest-shared-evaluation
# means SCP-R-002 sees every file's parsed content; dict-rooted
# inputs are typically OTHER file types (services.yml etc.), not
# malformed waivers. TF-008 will path-scope SCP-R-002 to waivers.json
# only and re-include dict-rooted detection.
scp_r_002_is_malformed_root if {
	is_null(input)
}

scp_r_002_is_malformed_root if {
	is_string(input)
}

scp_r_002_raw_findings contains finding if {
	is_array(input)
	some index, entry in input
	not is_object(entry)
	finding := {
		"message": sprintf("waiver entry %d must be an object", [index]),
		"rule_id": scp_r_002_rule_id,
		"file": "output/findings/waivers.json",
		"remediation_url": scp_r_002_remediation_url,
	}
}

scp_r_002_raw_findings contains finding if {
	scp_r_002_is_waiver_payload
	some index, entry in input
	is_object(entry)
	some key in scp_r_002_required_keys
	not scp_r_002_has_nonempty_string(entry, key)
	finding := {
		"message": sprintf("waiver entry %d must include %s", [index, key]),
		"rule_id": scp_r_002_rule_id,
		"file": "output/findings/waivers.json",
		"remediation_url": scp_r_002_remediation_url,
	}
}

scp_r_002_raw_findings contains finding if {
	scp_r_002_is_waiver_payload
	some index, entry in input
	is_object(entry)
	not scp_r_002_has_nonempty_string(entry, "rule_id")
	not scp_r_002_has_nonempty_string(entry, "finding_id")
	finding := {
		"message": sprintf("waiver entry %d must include either rule_id or finding_id", [index]),
		"rule_id": scp_r_002_rule_id,
		"file": "output/findings/waivers.json",
		"remediation_url": scp_r_002_remediation_url,
	}
}

scp_r_002_raw_findings contains finding if {
	scp_r_002_is_waiver_payload
	some index, entry in input
	is_object(entry)
	some key in {"created_at", "expires_at"}
	scp_r_002_has_nonempty_string(entry, key)
	not scp_r_002_has_valid_date_or_datetime(entry, key)
	finding := {
		"message": sprintf("waiver entry %d %s must be a valid RFC 3339 date or date-time", [index, key]),
		"rule_id": scp_r_002_rule_id,
		"file": "output/findings/waivers.json",
		"remediation_url": scp_r_002_remediation_url,
	}
}

scp_r_002_raw_findings contains finding if {
	scp_r_002_is_waiver_payload
	some index, entry in input
	is_object(entry)
	scp_r_002_has_nonempty_string(entry, "expires_at")
	expires_at := object.get(entry, "expires_at", "")
	expiry_ns := scp_r_002_dateish_ns(expires_at)
	expiry_ns <= scp_r_002_now_ns
	finding := {
		"message": sprintf("waiver entry %d expires_at must be in the future", [index]),
		"rule_id": scp_r_002_rule_id,
		"file": "output/findings/waivers.json",
		"remediation_url": scp_r_002_remediation_url,
	}
}

# Conftest 0.x requires deny outputs to carry `msg`; we union it from
# `message` so downstream consumers reading `.message` keep working.
deny contains output if {
	some finding in scp_r_002_raw_findings
	not scp_active_waiver_for(scp_r_002_rule_id)
	not scp_rule_config_disabled(scp_r_002_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

warn contains record if {
	count(scp_r_002_raw_findings) > 0
	some w in scp_waivers
	object.get(w, "rule_id", "") == scp_r_002_rule_id
	not scp_waiver_expired(w)
	record := {
		"kind": "waiver",
		"rule_id": scp_r_002_rule_id,
		"waiver_id": object.get(w, "waiver_id", ""),
		"finding_id": object.get(w, "finding_id", ""),
		"expires_at": object.get(w, "expires_at", ""),
		"file": "output/findings/waivers.json",
		"msg": sprintf(
			"%s suppressed by waiver (waiver_id=%s, expires_at=%s)",
			[scp_r_002_rule_id, object.get(w, "waiver_id", ""), object.get(w, "expires_at", "")],
		),
	}
}

warn contains record if {
	count(scp_r_002_raw_findings) > 0
	scp_rule_config_disabled(scp_r_002_rule_id)
	cfg := scp_rule_config_entry(scp_r_002_rule_id)
	record := {
		"kind": "rule_config",
		"rule_id": scp_r_002_rule_id,
		"reason": "rule-config override",
		"expires_at": object.get(cfg, "expires_at", ""),
		"msg": sprintf(
			"%s suppressed by .scp/rule-config.yaml (expires_at=%s)",
			[scp_r_002_rule_id, object.get(cfg, "expires_at", "")],
		),
	}
}

# Closes WP-SCP-022 R2 F-R2-COR-003 / R2-SAF-MAJ-01: prior detector
# evaluated false on `[{}]` or `[{"custom":"x"}]` (objects with no
# recognised keys), so per-entry deny rules were skipped — silent
# bypass. Tightened: any non-empty array is a waiver payload; the
# per-entry rules below catch missing required fields. Empty array
# remains a no-op (nothing to validate).
scp_r_002_is_waiver_payload if {
	is_array(input)
	count(input) > 0
}

scp_r_002_is_waiver_payload if {
	is_array(input)
	count(input) == 0
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
