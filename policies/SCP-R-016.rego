# RULE: SCP-R-016 — tcb-integrity-no-self-certification (standards-domain rule
# GOV-008; conformance-tcb anti-gaming family; D-067). Warn-baseline; deny-promote
# candidate at a future D-NNN once observed.
#
# INTENT (conformance harness charter v2 §5, SCP-R-TCB-001): protect the Trusted
# Computing Base of the conformance harness and forbid self-certification. Four
# signals: (a) a diff touching a trust-root-covered path without a fresh
# hardware-token operator counter-signature; (b) a cell minted GREEN under an OIDC
# subject that is NOT the sanctioned pinned-container subject, or with no matching
# append-only ledger entry (no SUT-triggered job may assume the mint subject);
# (c) a diff editing a CI gate / branch-protection path without an operator
# signature; (d) a typed board status that DISAGREES with the computed proof
# (fake-done). Together these stop the harness certifying itself. (D-058
# LINKAGE-not-VALUES: it gates the integrity of the TCB + the mint provenance,
# never the domain values.)
#
# SPLIT IDENTITY (SCP-R-013 ↔ ARCH-006 precedent): the STANDARDS-domain rule is
# GOV-008 (governance index + prose); the ENFORCEMENT policy is THIS file,
# SCP-R-016. The finding `rule_id` is "SCP-R-016"; the prose it links to is GOV-008.
#
# LIVE ENFORCEMENT TODAY is the SEPARATE `conformance-tcb` repo gate
# (jrnb2024/conformance-tcb, policy/scp_r_tcb_001.rego), branch-protected +
# required-check there, fed from the PR diff + the green-mint context in its own CI.
# This SCP-plane registration makes it an OFFICIAL estate standard; SCP-plane FIRING
# needs the materialiser companion (FUP-D067-CONFORMANCE-TCB-MATERIALISER-001). Do
# NOT claim live SCP-plane enforcement until that FUP lands.
#
# HONESTY (mirrors the source rule): the harness ledger deliberately leaves
# operator_signature null; a real value is supplied ONLY by the operator's hardware
# token out-of-band — NEVER fabricated by the agent fleet. This rule reads that
# operator-owned field; it does not and cannot mint it.
#
# INPUT CONTRACT (materialised by the FUP above; same dormancy pattern as SCP-R-013):
#   input.tcb_integrity      — object envelope the materialiser injects from the PR
#                              diff + mint context. PRESENCE (an object) = activation;
#                              ABSENT → dormant vacuous pass.
#     .diff                  — array of {path, tcb_covered, ci_gate} changed paths.
#     .operator_signature    — fresh hardware-token counter-sig over the trust root
#                              (null/absent = no signature; operator-supplied only).
#     .greens                — array of {cell, oidc_subject, in_ledger} being minted.
#     .expected_oidc_subject — the sanctioned pinned-container mint subject.
#     .board_cells           — array of {id, typed, computed} typed-vs-computed board.
#   input.rule_config        — adopter .scp/rule-config.yaml (opt-out).
# Until the materialiser injects `tcb_integrity`, input lacks the key → the
# activation guard is false → the rule VACUOUSLY PASSES on unrelated PRs. Once the
# envelope IS present, the fail-closed guards make a missing `diff`/`board_cells`
# DENY (never silently allow) — the conformance-tcb fail-closed semantics, scoped to
# activation so they cannot false-fire estate-wide.
#
# Defines its OWN scp_r_016_* predicates (per-rule coverage; SCP-R-013 precedent).
# Reuses ONLY the estate-wide suppression helpers from scp_common.rego.

package main

import rego.v1

scp_r_016_rule_id := "SCP-R-016"

scp_r_016_remediation_url := concat("", [
	"https://github.com/jrnb2024/standards-control-plane/blob/main/",
	"standards/governance/rules/GOV-008-tcb-integrity-no-self-certification.md",
])

default scp_r_016_opted_out := false

scp_r_016_opted_out if {
	rc := object.get(input, "rule_config", {})
	is_object(rc)
	object.get(rc, "tcb-integrity-disabled", false) == true
}

# ACTIVATION (dormancy gate): the materialiser-injected TCB envelope. "__absent__"
# sentinel distinguishes key-absent (dormant) from present (activated).
scp_r_016_tcb := tcb if {
	tcb := object.get(input, "tcb_integrity", "__absent__")
	is_object(tcb)
}

scp_r_016_activated if {
	is_object(scp_r_016_tcb)
}

scp_r_016_finding(file, message) := {
	"rule_id": scp_r_016_rule_id,
	"file": file,
	"message": message,
	"remediation_url": scp_r_016_remediation_url,
}

# A fresh operator counter-signature is present iff operator_signature is a
# non-null, non-empty string. HONESTY: operator-supplied out-of-band; never
# fabricated by the fleet.
scp_r_016_has_operator_signature if {
	sig := object.get(scp_r_016_tcb, "operator_signature", null)
	is_string(sig)
	sig != ""
}

# --- fail-closed guards (ONLY when activated; a missing required sub-key is
# malformed → DENY, never silently allow) --------------------------------------
scp_r_016_deny_findings contains finding if {
	scp_r_016_activated
	object.get(scp_r_016_tcb, "diff", "__missing__") == "__missing__"
	finding := scp_r_016_finding(
		"tcb_integrity",
		"SCP-R-016 (GOV-008): malformed input — activated tcb_integrity is missing `diff` (fail-closed).",
	)
}

scp_r_016_deny_findings contains finding if {
	scp_r_016_activated
	object.get(scp_r_016_tcb, "board_cells", "__missing__") == "__missing__"
	finding := scp_r_016_finding(
		"tcb_integrity",
		"SCP-R-016 (GOV-008): malformed input — activated tcb_integrity is missing `board_cells` (fail-closed).",
	)
}

# (a) a TCB-covered path modified WITHOUT a fresh hardware-token operator counter-sig.
scp_r_016_deny_findings contains finding if {
	scp_r_016_activated
	some change in object.get(scp_r_016_tcb, "diff", [])
	object.get(change, "tcb_covered", false) == true
	not scp_r_016_has_operator_signature
	finding := scp_r_016_finding(
		object.get(change, "path", "tcb_integrity"),
		sprintf(
			"SCP-R-016(a) (GOV-008): TCB-covered path %q modified without a fresh hardware-token operator counter-signature.",
			[object.get(change, "path", "")],
		),
	)
}

# (b) a green minted outside the sanctioned pinned-container OIDC subject.
scp_r_016_deny_findings contains finding if {
	scp_r_016_activated
	some g in object.get(scp_r_016_tcb, "greens", [])
	object.get(g, "oidc_subject", "") != object.get(scp_r_016_tcb, "expected_oidc_subject", "__expected__")
	finding := scp_r_016_finding(
		"tcb_integrity",
		sprintf(
			"SCP-R-016(b) (GOV-008): green for %q minted outside the container OIDC subject (got %q, expected %q).",
			[object.get(g, "cell", ""), object.get(g, "oidc_subject", ""), object.get(scp_r_016_tcb, "expected_oidc_subject", "")],
		),
	)
}

# (b) a green with no matching append-only ledger entry.
scp_r_016_deny_findings contains finding if {
	scp_r_016_activated
	some g in object.get(scp_r_016_tcb, "greens", [])
	object.get(g, "in_ledger", true) == false
	finding := scp_r_016_finding(
		"tcb_integrity",
		sprintf("SCP-R-016(b) (GOV-008): green for %q has no matching entry in the append-only ledger.", [object.get(g, "cell", "")]),
	)
}

# (c) a CI gate / branch-protection path edited WITHOUT an operator signature.
scp_r_016_deny_findings contains finding if {
	scp_r_016_activated
	some change in object.get(scp_r_016_tcb, "diff", [])
	object.get(change, "ci_gate", false) == true
	not scp_r_016_has_operator_signature
	finding := scp_r_016_finding(
		object.get(change, "path", "tcb_integrity"),
		sprintf(
			"SCP-R-016(c) (GOV-008): CI gate / branch-protection path %q edited without an operator signature.",
			[object.get(change, "path", "")],
		),
	)
}

# (d) a typed board status that DISAGREES with the computed proof (fake-done).
scp_r_016_deny_findings contains finding if {
	scp_r_016_activated
	some c in object.get(scp_r_016_tcb, "board_cells", [])
	object.get(c, "typed", "__typed__") != object.get(c, "computed", "__computed__")
	finding := scp_r_016_finding(
		"tcb_integrity",
		sprintf(
			"SCP-R-016(d) (GOV-008): typed board status for %q (%q) disagrees with computed (%q) — fake-done.",
			[object.get(c, "id", ""), object.get(c, "typed", ""), object.get(c, "computed", "")],
		),
	)
}

scp_r_016_any_findings if {
	count(scp_r_016_deny_findings) > 0
}

deny contains output if {
	some finding in scp_r_016_deny_findings
	not scp_r_016_opted_out
	not scp_active_waiver_for(scp_r_016_rule_id)
	not scp_rule_config_disabled(scp_r_016_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

warn contains record if {
	scp_r_016_any_findings
	some w in scp_waivers
	object.get(w, "rule_id", "") == scp_r_016_rule_id
	not scp_waiver_expired(w)
	record := {
		"kind": "waiver",
		"rule_id": scp_r_016_rule_id,
		"waiver_id": object.get(w, "waiver_id", ""),
		"msg": sprintf("SCP-R-016 findings suppressed by active waiver %s", [object.get(w, "waiver_id", "")]),
	}
}

warn contains record if {
	scp_r_016_any_findings
	scp_r_016_opted_out
	record := {
		"kind": "rule-config-disable",
		"rule_id": scp_r_016_rule_id,
		"msg": "SCP-R-016 findings suppressed by tcb-integrity-disabled opt-out",
	}
}

warn contains record if {
	scp_r_016_any_findings
	scp_rule_config_disabled(scp_r_016_rule_id)
	record := {
		"kind": "rule-config-disable",
		"rule_id": scp_r_016_rule_id,
		"msg": "SCP-R-016 findings suppressed by rule-config disable",
	}
}
