# RULE: SCP-R-007 — see docs/reviews/rule-proposals/RULE-004-waiver-expiry-within-window.md
#
# Waiver `expires_at` must be within a bounded window (≤ 90 days from
# `created_at`) AND must not already be in the past. Ships at deny
# baseline (LOW false-positive risk; date arithmetic on schema-validated
# fields). Filed via WP-SCP-025 Phase 1 (operator-authorised early
# kickoff 2026-05-25).
#
# Defines its OWN `scp_r_007_*` predicates rather than calling
# `scp_r_002_*` / `scp_common` equivalents that share semantics, per
# the SCP-R-004 SAFE-MAJ-001 precedent — a TF-008 refactor of SCP-R-002
# cannot silently break SCP-R-007.
package main

import rego.v1

scp_r_007_rule_id := "SCP-R-007"

scp_r_007_remediation_url := concat("", [
	"https://github.com/jrnb2024/standards-control-plane/blob/main/",
	"docs/reviews/rule-proposals/RULE-004-waiver-expiry-within-window.md",
])

# 90 days in nanoseconds. RULE-004 §3.1 (b) window boundary.
# 90 * 24 * 60 * 60 * 1_000_000_000 = 7_776_000_000_000_000.
scp_r_007_window_ns := 7776000000000000

# Test-mockable time symbol. Tests override via
# `with main.scp_r_007_now_ns as <ns>`. Mirrors scp_r_004_test.rego
# `scp_now_ns` pattern.
scp_r_007_now_ns := time.now_ns()

# Waivers payload guard. Mirrors SCP-R-002 / SCP-R-004 intentional
# both-empty-and-non-empty acceptance: an empty array yields no
# `some index, entry in input` bindings; a non-empty array enters
# per-entry checks. Defined in the SCP-R-007 namespace.
scp_r_007_is_waiver_payload if {
	is_array(input)
	count(input) > 0
}

scp_r_007_is_waiver_payload if {
	is_array(input)
	count(input) == 0
}

# Branch (a): waiver entry whose expires_at parses as RFC3339 AND is in
# the past (already expired). Per RULE-004 §3.1 (a). Fires per-entry.
scp_r_007_raw_findings contains finding if {
	scp_r_007_is_waiver_payload
	some index, entry in input
	is_object(entry)
	expires_at_str := object.get(entry, "expires_at", "")
	expires_at_str != ""
	is_string(expires_at_str)
	expires_at_ns := time.parse_rfc3339_ns(expires_at_str)
	expires_at_ns < scp_r_007_now_ns
	finding := {
		"message": sprintf(
			"SCP-R-007 waiver entry %d (rule_id=%s) is already expired: expires_at=%s, now (ns)=%d. Stale waivers should be removed from waivers.json. See RULE-004.",
			[
				index,
				object.get(entry, "rule_id", ""),
				expires_at_str,
				scp_r_007_now_ns,
			],
		),
		"rule_id": scp_r_007_rule_id,
		"file": "output/findings/waivers.json",
		"remediation_url": scp_r_007_remediation_url,
	}
}

# Helper: build window-violation finding object. Extracted to keep the
# raw_findings rule body under Regal's max-rule-length style threshold.
scp_r_007_window_violation_finding(index, entry, created_at_str, expires_at_str, delta_days) := finding if {
	finding := {
		"message": sprintf(
			"SCP-R-007 waiver entry %d (rule_id=%s) window violation: expires_at=%s, created_at=%s, delta=%dd > 90d. Tighten expires_at or file a per-adopter override.",
			[
				index,
				object.get(entry, "rule_id", ""),
				expires_at_str,
				created_at_str,
				delta_days,
			],
		),
		"rule_id": scp_r_007_rule_id,
		"file": "output/findings/waivers.json",
		"remediation_url": scp_r_007_remediation_url,
	}
}

# Branch (b): waiver entry whose (expires_at - created_at) exceeds the
# 90-day window. Per RULE-004 §3.1 (b). Fires per-entry. Requires BOTH
# created_at AND expires_at parse cleanly as RFC3339 — shape-incomplete
# waivers are SCP-R-002's concern.
scp_r_007_raw_findings contains finding if {
	scp_r_007_is_waiver_payload
	some index, entry in input
	is_object(entry)
	created_at_str := object.get(entry, "created_at", "")
	expires_at_str := object.get(entry, "expires_at", "")
	created_at_str != ""
	expires_at_str != ""
	is_string(created_at_str)
	is_string(expires_at_str)
	created_at_ns := time.parse_rfc3339_ns(created_at_str)
	expires_at_ns := time.parse_rfc3339_ns(expires_at_str)

	# Only fire branch (b) when NOT already expired (covered by branch (a)).
	expires_at_ns >= scp_r_007_now_ns
	delta_ns := expires_at_ns - created_at_ns
	delta_ns > scp_r_007_window_ns
	delta_days := delta_ns / 86400000000000
	finding := scp_r_007_window_violation_finding(index, entry, created_at_str, expires_at_str, delta_days)
}

# Public deny rule. Fires on raw findings not suppressed by an active
# waiver against SCP-R-007 OR by `.scp/rule-config.yaml` `disable: true`
# for SCP-R-007. SCP-R-007 ships at deny baseline (NOT in
# WARN_BASELINE_RULES per RULE-004 §3.2 LOW FP risk classification).
deny contains output if {
	some finding in scp_r_007_raw_findings
	not scp_active_waiver_for(scp_r_007_rule_id)
	not scp_rule_config_disabled(scp_r_007_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

# Suppression-observability warn: an active (unexpired) waiver against
# SCP-R-007 silenced the deny. Emits one record per waiver-suppression
# event. Mirrors SCP-R-002 / SCP-R-004 warn-rule shape.
warn contains record if {
	count(scp_r_007_raw_findings) > 0
	some w in scp_waivers
	object.get(w, "rule_id", "") == scp_r_007_rule_id
	not scp_waiver_expired(w)
	record := {
		"kind": "waiver",
		"rule_id": scp_r_007_rule_id,
		"waiver_id": object.get(w, "waiver_id", ""),
		"msg": sprintf(
			"SCP-R-007 suppressed by active waiver %s (rule_id=%s)",
			[object.get(w, "waiver_id", ""), scp_r_007_rule_id],
		),
	}
}

# Suppression-observability warn: a `.scp/rule-config.yaml disable: true`
# entry silenced the deny. Mirrors SCP-R-002 / SCP-R-004 warn-rule shape.
warn contains record if {
	count(scp_r_007_raw_findings) > 0
	scp_rule_config_disabled(scp_r_007_rule_id)
	record := {
		"kind": "rule-config-disable",
		"rule_id": scp_r_007_rule_id,
		"msg": sprintf(
			"SCP-R-007 suppressed by .scp/rule-config.yaml disable: true",
			[],
		),
	}
}
