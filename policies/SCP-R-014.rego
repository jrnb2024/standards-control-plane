# RULE: SCP-R-014 — no-shortcuts-serving-source-allowlist (standards-domain rule
# GOV-006; conformance-tcb anti-gaming family; D-067). Warn-baseline; deny-promote
# candidate at a future D-NNN once observed.
#
# INTENT (conformance harness charter v2 §5, SCP-R-JOIN-001): the serving path of
# a governed app may read ONLY sources that are on the sanctioned allowlist. A
# serving-path read of an unsanctioned source, a NEW/unclassified serving dir, or
# a dynamically-constructed serving filename are the three ways a demo "goes
# green" by quietly reading a hand-curated fixture instead of the canonical index.
# This rule gates that anti-shortcut discipline (D-058 LINKAGE-not-VALUES: it never
# reads the VALUES a source serves, only WHETHER the reader/dir/filename is on the
# sanctioned allowlist). Ratchet is shrink-only (the allowlist may only lose
# entries), enforced by the harness diffing the sanctioned list — not expressible
# in a single-input policy.
#
# SPLIT IDENTITY (SCP-R-013 ↔ ARCH-006 precedent): the STANDARDS-domain rule is
# GOV-006 (governance index + prose); the ENFORCEMENT policy is THIS file,
# SCP-R-014 (the CI workflow loads only policies/SCP-R-*.rego and the scorecard
# filters SCP-R-[0-9]+). The finding `rule_id` below is "SCP-R-014" so it flows
# through the workflow; the prose it links to is GOV-006.
#
# LIVE ENFORCEMENT TODAY is the SEPARATE `conformance-tcb` repo gate
# (jrnb2024/conformance-tcb, policy/scp_r_join_001.rego), which is branch-protected
# and required-check there and produces the serving-dataflow scan from its own CI.
# This SCP-plane registration makes the rule an OFFICIAL estate standard; SCP-plane
# FIRING needs a materialiser companion (FUP-D067-CONFORMANCE-TCB-MATERIALISER-001)
# that injects the input contract below. Do NOT claim live SCP-plane enforcement
# until that FUP lands.
#
# INPUT CONTRACT (materialised by the companion workflow PR — the FUP above; same
# dormancy pattern as SCP-R-013):
#   input.serving_allowlist_scan — object envelope the materialiser injects from the
#                                  dataflow-into-index scan. Its PRESENCE (an object,
#                                  even {}) is the activation signal; ABSENT → dormant.
#     .sanctioned_sources        — array of allowlisted source paths (the allowlist).
#     .serving_reads             — array of {reader, source, dynamic_filename} for
#                                  every read on the serving path.
#     .serving_dirs              — array of {dir, classified} for every serving dir.
#   input.rule_config            — adopter .scp/rule-config.yaml (opt-out).
# Until the materialiser injects `serving_allowlist_scan`, input lacks the key → the
# activation guard is false → every clause short-circuits → the rule VACUOUSLY
# PASSES on unrelated PRs (the SCP-R-006/009/013 safe-failure precedent). Once the
# envelope IS present, the fail-closed sub-key guards make a malformed/partial scan
# DENY (never silently allow) — the conformance-tcb fail-closed semantics, scoped to
# activation so they cannot false-fire estate-wide.
#
# Defines its OWN scp_r_014_* predicates per the SCP-R-004/006/009/013 precedent
# (rule-local helpers preserve per-rule coverage under the 90% gate). Reuses ONLY the
# estate-wide suppression helpers scp_active_waiver_for + scp_rule_config_disabled +
# scp_waivers + scp_waiver_expired from scp_common.rego.

package main

import rego.v1

scp_r_014_rule_id := "SCP-R-014"

scp_r_014_remediation_url := concat("", [
	"https://github.com/jrnb2024/standards-control-plane/blob/main/",
	"standards/governance/rules/GOV-006-no-shortcuts-serving-source-allowlist.md",
])

# Adopter opt-out (mirrors SCP-R-013's idiom). Reads input.rule_config. Default
# false = active.
default scp_r_014_opted_out := false

scp_r_014_opted_out if {
	rc := object.get(input, "rule_config", {})
	is_object(rc)
	object.get(rc, "no-shortcuts-serving-allowlist-disabled", false) == true
}

# ACTIVATION (dormancy gate): the materialiser-injected scan envelope. A "__absent__"
# sentinel default distinguishes "key absent" (dormant → vacuous pass) from a
# present-but-empty object (activated → fail-closed on missing sub-keys).
scp_r_014_scan := scan if {
	scan := object.get(input, "serving_allowlist_scan", "__absent__")
	is_object(scan)
}

scp_r_014_activated if {
	is_object(scp_r_014_scan)
}

# Finding builder (keeps partial-rule bodies under Regal's length cap).
scp_r_014_finding(file, message) := {
	"rule_id": scp_r_014_rule_id,
	"file": file,
	"message": message,
	"remediation_url": scp_r_014_remediation_url,
}

# The sanctioned allowlist is exact-path membership.
scp_r_014_source_sanctioned(src) if {
	some s in object.get(scp_r_014_scan, "sanctioned_sources", [])
	s == src
}

# --- fail-closed guards (ONLY when activated; a missing required sub-key of a
# present envelope is malformed → DENY, never silently allow) -------------------

scp_r_014_deny_findings contains finding if {
	scp_r_014_activated
	object.get(scp_r_014_scan, "serving_reads", "__missing__") == "__missing__"
	finding := scp_r_014_finding(
		"serving_allowlist_scan",
		"SCP-R-014 (GOV-006): malformed input — activated scan is missing `serving_reads` (fail-closed).",
	)
}

scp_r_014_deny_findings contains finding if {
	scp_r_014_activated
	object.get(scp_r_014_scan, "serving_dirs", "__missing__") == "__missing__"
	finding := scp_r_014_finding(
		"serving_allowlist_scan",
		"SCP-R-014 (GOV-006): malformed input — activated scan is missing `serving_dirs` (fail-closed).",
	)
}

scp_r_014_deny_findings contains finding if {
	scp_r_014_activated
	object.get(scp_r_014_scan, "sanctioned_sources", "__missing__") == "__missing__"
	finding := scp_r_014_finding(
		"serving_allowlist_scan",
		"SCP-R-014 (GOV-006): malformed input — activated scan is missing `sanctioned_sources` (fail-closed).",
	)
}

# --- deny-class (structural anti-shortcut violations; demoted to ::warning:: by
# WARN_BASELINE membership in the workflow; a future D-NNN deny-promote flips it) --

# (1) a serving-path read of a source NOT on the sanctioned allowlist.
scp_r_014_deny_findings contains finding if {
	scp_r_014_activated
	some read in object.get(scp_r_014_scan, "serving_reads", [])
	not scp_r_014_source_sanctioned(object.get(read, "source", ""))
	finding := scp_r_014_finding(
		object.get(read, "reader", "serving_allowlist_scan"),
		sprintf(
			"SCP-R-014 (GOV-006): unsanctioned serving read — %q reads %q which is not on the sanctioned-sources allowlist. A serving-path read must reference a sanctioned canonical source, not a hand-curated fixture.",
			[object.get(read, "reader", ""), object.get(read, "source", "")],
		),
	)
}

# (2) a new/unclassified serving directory (the blind-dir check).
scp_r_014_deny_findings contains finding if {
	scp_r_014_activated
	some d in object.get(scp_r_014_scan, "serving_dirs", [])
	object.get(d, "classified", true) == false
	finding := scp_r_014_finding(
		object.get(d, "dir", "serving_allowlist_scan"),
		sprintf(
			"SCP-R-014 (GOV-006): unclassified serving dir %q. A new serving dir must be classified into the sanctioned-sources allowlist before it may read.",
			[object.get(d, "dir", "")],
		),
	)
}

# (3) a dynamically-constructed serving filename (defeats the allowlist statically).
scp_r_014_deny_findings contains finding if {
	scp_r_014_activated
	some read in object.get(scp_r_014_scan, "serving_reads", [])
	object.get(read, "dynamic_filename", false) == true
	finding := scp_r_014_finding(
		object.get(read, "reader", "serving_allowlist_scan"),
		sprintf(
			"SCP-R-014 (GOV-006): dynamic serving filename in %q (source %q built at runtime; the allowlist cannot verify it statically).",
			[object.get(read, "reader", ""), object.get(read, "source", "")],
		),
	)
}

# True iff the rule produced ANY finding — guards the suppression-observability
# records so a suppressed finding is still observable (SCP-R-013 precedent).
scp_r_014_any_findings if {
	count(scp_r_014_deny_findings) > 0
}

# Public deny rule. Warn-baseline membership in the workflow demotes these to
# ::warning:: + excludes from the merge-gate threshold; a future D-NNN flips it.
deny contains output if {
	some finding in scp_r_014_deny_findings
	not scp_r_014_opted_out
	not scp_active_waiver_for(scp_r_014_rule_id)
	not scp_rule_config_disabled(scp_r_014_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

# Suppression-observability warn: active waiver against SCP-R-014.
warn contains record if {
	scp_r_014_any_findings
	some w in scp_waivers
	object.get(w, "rule_id", "") == scp_r_014_rule_id
	not scp_waiver_expired(w)
	record := {
		"kind": "waiver",
		"rule_id": scp_r_014_rule_id,
		"waiver_id": object.get(w, "waiver_id", ""),
		"msg": sprintf("SCP-R-014 findings suppressed by active waiver %s", [object.get(w, "waiver_id", "")]),
	}
}

# Suppression-observability warn: bespoke opt-out key.
warn contains record if {
	scp_r_014_any_findings
	scp_r_014_opted_out
	record := {
		"kind": "rule-config-disable",
		"rule_id": scp_r_014_rule_id,
		"msg": "SCP-R-014 findings suppressed by no-shortcuts-serving-allowlist-disabled opt-out",
	}
}

# Suppression-observability warn: `.scp/rule-config.yaml` disable.
warn contains record if {
	scp_r_014_any_findings
	scp_rule_config_disabled(scp_r_014_rule_id)
	record := {
		"kind": "rule-config-disable",
		"rule_id": scp_r_014_rule_id,
		"msg": "SCP-R-014 findings suppressed by rule-config disable",
	}
}
