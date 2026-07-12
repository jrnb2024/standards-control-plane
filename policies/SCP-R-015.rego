# RULE: SCP-R-015 — integrity-green-required-to-leave-red (standards-domain rule
# GOV-007; conformance-tcb anti-gaming family; D-067). Warn-baseline; deny-promote
# candidate at a future D-NNN once observed.
#
# INTENT (conformance harness charter v2 §5, SCP-R-TRIAD-001): a conformance board
# cell may not be marked NON-RED (green/passing) unless every integrity clause
# holds — the computed-from-proof status agrees with the claimed status (no typed
# override), the standing fake-mutant FAILED its test (the test discriminates),
# a CI-observed ledger-signed RED preceded the flip (red-first), and the transition
# classifier confirms an SUT-only cumulative diff with TCB byte-identity. This is
# the anti-"fake-done" gate: it stops a cell going green by editing the board or the
# test harness rather than by making the real join pass. (D-058 LINKAGE-not-VALUES:
# it gates the INTEGRITY of the green claim, never the domain values under test.)
# The correctness tier (external/attested) is a SEPARATE required tag, NOT gated here.
#
# SPLIT IDENTITY (SCP-R-013 ↔ ARCH-006 precedent): the STANDARDS-domain rule is
# GOV-007 (governance index + prose); the ENFORCEMENT policy is THIS file,
# SCP-R-015. The finding `rule_id` is "SCP-R-015"; the prose it links to is GOV-007.
#
# LIVE ENFORCEMENT TODAY is the SEPARATE `conformance-tcb` repo gate
# (jrnb2024/conformance-tcb, policy/scp_r_triad_001.rego), branch-protected +
# required-check there, fed by its own CI per cell it proposes to flip out of RED.
# This SCP-plane registration makes it an OFFICIAL estate standard; SCP-plane FIRING
# needs the materialiser companion (FUP-D067-CONFORMANCE-TCB-MATERIALISER-001). Do
# NOT claim live SCP-plane enforcement until that FUP lands.
#
# INPUT CONTRACT (materialised by the FUP above; same dormancy pattern as SCP-R-013):
#   input.cell_transition — object envelope the materialiser injects per cell being
#                           flipped. Its PRESENCE (an object) is the activation
#                           signal; ABSENT → dormant vacuous pass.
#     .id                 — cell identifier.
#     .status             — the status being CLAIMED (anything != "RED" is a flip).
#     .computed_status    — L2 derived-from-proof status (render_board).
#     .fake_mutant_failed — bool; L3 standing FAKE fixture failed its test (good).
#     .red_first          — bool; L5 a CI-observed ledger-signed RED preceded this.
#     .classifier_ok      — bool; transition classifier: SUT-only diff, TCB identical.
#   input.rule_config     — adopter .scp/rule-config.yaml (opt-out).
# Until the materialiser injects `cell_transition`, input lacks the key → the
# activation guard is false → the rule VACUOUSLY PASSES on unrelated PRs. Once the
# envelope IS present AND the cell claims non-RED, the fail-closed guard makes a
# missing required field DENY (never silently allow) — the conformance-tcb
# fail-closed semantics, scoped to activation so they cannot false-fire estate-wide.
# A cell whose claimed status is "RED" is never gated by this rule.
#
# Defines its OWN scp_r_015_* predicates (per-rule coverage; SCP-R-013 precedent).
# Reuses ONLY the estate-wide suppression helpers from scp_common.rego.

package main

import rego.v1

scp_r_015_rule_id := "SCP-R-015"

scp_r_015_remediation_url := concat("", [
	"https://github.com/jrnb2024/standards-control-plane/blob/main/",
	"standards/governance/rules/GOV-007-integrity-green-required-to-leave-red.md",
])

default scp_r_015_opted_out := false

scp_r_015_opted_out if {
	rc := object.get(input, "rule_config", {})
	is_object(rc)
	object.get(rc, "integrity-green-triad-disabled", false) == true
}

# ACTIVATION (dormancy gate): the materialiser-injected cell envelope. "__absent__"
# sentinel distinguishes key-absent (dormant) from present (activated).
scp_r_015_cell := cell if {
	cell := object.get(input, "cell_transition", "__absent__")
	is_object(cell)
}

scp_r_015_activated if {
	is_object(scp_r_015_cell)
}

scp_r_015_finding(file, message) := {
	"rule_id": scp_r_015_rule_id,
	"file": file,
	"message": message,
	"remediation_url": scp_r_015_remediation_url,
}

# The cell is attempting to flip out of RED (missing status defaults to RED = not
# leaving, so an incomplete envelope never spuriously trips leaving_red).
scp_r_015_leaving_red if {
	scp_r_015_activated
	object.get(scp_r_015_cell, "status", "RED") != "RED"
}

# All four integrity conditions hold. Each helper is UNDEFINED (not false) when its
# clause fails — so the deny message below references RAW input fields, never these
# helpers (referencing an undefined value would make the deny body undefined and
# silently swallow the violation — the SCP-R-TRIAD-001 note).
scp_r_015_integrity_ok if {
	scp_r_015_computed_agrees
	scp_r_015_fake_ok
	scp_r_015_red_first_ok
	scp_r_015_classifier_ok
}

# L2: claimed status must equal the computed-from-proof status (no typed override).
scp_r_015_computed_agrees if {
	object.get(scp_r_015_cell, "computed_status", "__missing__") == object.get(scp_r_015_cell, "status", "__claimed__")
}

# L3: the standing fake-mutant must have FAILED its test (proves discrimination).
scp_r_015_fake_ok if {
	object.get(scp_r_015_cell, "fake_mutant_failed", false) == true
}

# L5: a CI-observed, ledger-signed RED must precede the flip (red-first).
scp_r_015_red_first_ok if {
	object.get(scp_r_015_cell, "red_first", false) == true
}

# Transition classifier: cumulative diff since the last signed RED is SUT-only,
# TCB byte-identical.
scp_r_015_classifier_ok if {
	object.get(scp_r_015_cell, "classifier_ok", false) == true
}

# --- fail-closed guard (ONLY when activated + claiming non-RED; a missing required
# field is malformed → DENY, never silently allow) -----------------------------
scp_r_015_deny_findings contains finding if {
	scp_r_015_leaving_red
	some k in {"id", "status", "computed_status", "fake_mutant_failed", "red_first", "classifier_ok"}
	object.get(scp_r_015_cell, k, "__missing__") == "__missing__"
	finding := scp_r_015_finding(
		"cell_transition",
		sprintf("SCP-R-015 (GOV-007): malformed — cell.%v absent while claiming non-RED (fail-closed).", [k]),
	)
}

# --- deny-class (a cell claiming non-RED that fails any integrity clause; demoted
# to ::warning:: by WARN_BASELINE membership; a future D-NNN flips it) -----------
scp_r_015_deny_findings contains finding if {
	scp_r_015_leaving_red
	not scp_r_015_integrity_ok
	finding := scp_r_015_finding(
		"cell_transition",
		sprintf(
			"SCP-R-015 (GOV-007): cell %q may not leave RED (claimed=%q): computed_status=%q, fake_mutant_failed=%v, red_first=%v, classifier_ok=%v. All four integrity clauses must hold to mark a cell non-RED.",
			[
				object.get(scp_r_015_cell, "id", ""),
				object.get(scp_r_015_cell, "status", ""),
				object.get(scp_r_015_cell, "computed_status", ""),
				object.get(scp_r_015_cell, "fake_mutant_failed", false),
				object.get(scp_r_015_cell, "red_first", false),
				object.get(scp_r_015_cell, "classifier_ok", false),
			],
		),
	)
}

scp_r_015_any_findings if {
	count(scp_r_015_deny_findings) > 0
}

deny contains output if {
	some finding in scp_r_015_deny_findings
	not scp_r_015_opted_out
	not scp_active_waiver_for(scp_r_015_rule_id)
	not scp_rule_config_disabled(scp_r_015_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

warn contains record if {
	scp_r_015_any_findings
	some w in scp_waivers
	object.get(w, "rule_id", "") == scp_r_015_rule_id
	not scp_waiver_expired(w)
	record := {
		"kind": "waiver",
		"rule_id": scp_r_015_rule_id,
		"waiver_id": object.get(w, "waiver_id", ""),
		"msg": sprintf("SCP-R-015 findings suppressed by active waiver %s", [object.get(w, "waiver_id", "")]),
	}
}

warn contains record if {
	scp_r_015_any_findings
	scp_r_015_opted_out
	record := {
		"kind": "rule-config-disable",
		"rule_id": scp_r_015_rule_id,
		"msg": "SCP-R-015 findings suppressed by integrity-green-triad-disabled opt-out",
	}
}

warn contains record if {
	scp_r_015_any_findings
	scp_rule_config_disabled(scp_r_015_rule_id)
	record := {
		"kind": "rule-config-disable",
		"rule_id": scp_r_015_rule_id,
		"msg": "SCP-R-015 findings suppressed by rule-config disable",
	}
}
