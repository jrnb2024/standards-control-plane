# RULE: SCP-R-004 — see docs/reviews/rule-proposals/RULE-001-waiver-reason-must-cite-issue-or-pr.md
#
# Waiver `reason` field must contain at least one HTTP(S) URL pointing
# at a decision artifact (issue, PR, decision log entry). At v1.1.0 the
# rule fires at warn baseline — adopters see a `::warning::` annotation
# rather than a merge-blocking deny. Promotion to deny default is a
# separate RFC and the earliest plausible MAJOR (v2.0.0+).
#
# Defines its OWN `scp_r_004_is_waiver_payload` and
# `scp_r_004_has_nonempty_string` predicates rather than calling the
# `scp_r_002_*` equivalents. Closes 020L R1 SAFE-MAJ-001 — a TF-008
# refactor of SCP-R-002 cannot silently break SCP-R-004.
package main

import rego.v1

scp_r_004_rule_id := "SCP-R-004"

scp_r_004_remediation_url := concat("", [
	"https://github.com/jrnb2024/standards-control-plane/blob/main/",
	"docs/reviews/rule-proposals/RULE-001-waiver-reason-must-cite-issue-or-pr.md",
])

# Waivers payload guard. Mirrors SCP-R-002's intentional both-empty-and-non-empty
# acceptance: an empty array yields no `some index, entry in input` bindings
# and the rule body cannot succeed; a non-empty array enters per-entry checks.
# Defined in the SCP-R-004 namespace per 020L R1 SAFE-MAJ-001 closure.
scp_r_004_is_waiver_payload if {
	is_array(input)
	count(input) > 0
}

scp_r_004_is_waiver_payload if {
	is_array(input)
	count(input) == 0
}

scp_r_004_has_nonempty_string(entry, key) if {
	value := object.get(entry, key, null)
	is_string(value)
	value != ""
}

# URL-presence check. Matches any HTTP(S) URL substring. RE2 syntax
# (Rego's `regex.match` uses RE2). `[^\s]` is the ASCII whitespace
# complement set; for the §6.2 ASCII fixture corpus this matches the
# Python `re` `\S` semantics. See TF-020L-001 for the Unicode-whitespace
# divergence + Phase-2 monitor closure path.
scp_r_004_has_url(text) if {
	regex.match(`https?://[^\s]+`, text)
}

# Truncate `reason` to 80 characters with trailing ellipsis if the
# original exceeds the budget. Matches RULE-001 §3.3 annotation-message
# contract. Two-branch shape: short-or-equal returns the input as-is
# (no intermediate variable per Regal `pointless-reassignment` rule);
# over-budget returns first 79 chars + U+2026 ellipsis = 80 total.
scp_r_004_truncate_reason(reason) := reason if {
	count(reason) <= 80
}

scp_r_004_truncate_reason(reason) := concat("", [substring(reason, 0, 79), "…"]) if {
	count(reason) > 80
}

# Per-entry raw findings. Fires on each waiver entry whose `reason` is
# a non-empty string but does NOT contain at least one HTTP(S) URL.
# The annotation message includes the entry's own `rule_id` and
# `finding_id` (if present) plus the truncated reason text per §3.3.
scp_r_004_raw_findings contains finding if {
	scp_r_004_is_waiver_payload
	some index, entry in input
	is_object(entry)
	scp_r_004_has_nonempty_string(entry, "reason")
	reason := object.get(entry, "reason", "")
	not scp_r_004_has_url(reason)
	finding := {
		"message": sprintf(
			"SCP-R-004 waiver entry %d (rule_id=%s, finding_id=%s): reason field must contain a decision-artifact URL (issue, PR, or decision log entry). Found reason text: \"%s\"",
			[
				index,
				object.get(entry, "rule_id", ""),
				object.get(entry, "finding_id", ""),
				scp_r_004_truncate_reason(reason),
			],
		),
		"rule_id": scp_r_004_rule_id,
		"file": "output/findings/waivers.json",
		"remediation_url": scp_r_004_remediation_url,
	}
}

# Public deny rule. Fires on raw findings not suppressed by an active
# waiver against SCP-R-004 OR by `.scp/rule-config.yaml` `disable: true`
# for SCP-R-004. At warn baseline the workflow's "Render deny
# annotations and enforce threshold" step recognises SCP-R-004 in its
# WARN_BASELINE_RULES set and emits `::warning::` annotations rather
# than `::error::` AND excludes SCP-R-004 from the threshold check. The
# deny rule itself remains shape-parallel to SCP-R-001/002/003 so a
# future promotion to deny default (v2.0.0+ via separate RFC) flips
# only the workflow's warn-class set.
deny contains output if {
	some finding in scp_r_004_raw_findings
	not scp_active_waiver_for(scp_r_004_rule_id)
	not scp_rule_config_disabled(scp_r_004_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

# Suppression-observability: an active (unexpired) waiver against
# SCP-R-004 silenced the deny. Emits one record per waiver-suppression
# event. Mirrors SCP-R-002 / SCP-R-003 warn-rule shape.
warn contains record if {
	count(scp_r_004_raw_findings) > 0
	some w in scp_waivers
	object.get(w, "rule_id", "") == scp_r_004_rule_id
	not scp_waiver_expired(w)
	record := {
		"kind": "waiver",
		"rule_id": scp_r_004_rule_id,
		"waiver_id": object.get(w, "waiver_id", ""),
		"finding_id": object.get(w, "finding_id", ""),
		"expires_at": object.get(w, "expires_at", ""),
		"file": "output/findings/waivers.json",
		"msg": sprintf(
			"%s suppressed by waiver (waiver_id=%s, expires_at=%s)",
			[scp_r_004_rule_id, object.get(w, "waiver_id", ""), object.get(w, "expires_at", "")],
		),
	}
}

# Suppression-observability: `.scp/rule-config.yaml` `disable: true`
# silenced the deny. Emits one record per evaluation. Mirrors SCP-R-002
# / SCP-R-003 rule_config warn-rule shape.
warn contains record if {
	count(scp_r_004_raw_findings) > 0
	scp_rule_config_disabled(scp_r_004_rule_id)
	cfg := scp_rule_config_entry(scp_r_004_rule_id)
	record := {
		"kind": "rule_config",
		"rule_id": scp_r_004_rule_id,
		"reason": "rule-config override",
		"expires_at": object.get(cfg, "expires_at", ""),
		"msg": sprintf(
			"%s suppressed by .scp/rule-config.yaml (expires_at=%s)",
			[scp_r_004_rule_id, object.get(cfg, "expires_at", "")],
		),
	}
}
