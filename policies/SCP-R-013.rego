# RULE: SCP-R-013 — ontology-canonical-consumption (WP-SCP-037; standards-domain
# rule ARCH-006; D-058 first ontology-domain rule). Warn-baseline; deny-promote
# candidate at a future D-NNN once observed.
#
# INTENT (WP-SCP-037 §1a): the estate has ONE canonical fashion ontology
# authority — fashion-ontology-service (FOS). FLA AUTHORS the data; FOS SERVES
# it; every other app is a CONSUMER that must LINK to FOS (declare an
# `ontology_contract` in services.yml, pin a canonical_version, keep no divergent
# local copy). This rule gates that LINKAGE (D-058 LINKAGE-not-VALUES): it never
# reads ontology VALUES, only whether the consumer references + pins the
# canonical and does not embed a divergent copy. Modeled on SCP-R-009's
# structure (rule-local predicates, vacuous-pass dormancy, warn-baseline).
#
# NOTE the split identity: the STANDARDS-domain rule is ARCH-006 (architecture
# index + prose); the ENFORCEMENT policy is THIS file, SCP-R-013 (the CI workflow
# loads only policies/SCP-R-*.rego and the scorecard filters SCP-R-[0-9]+). The
# finding `rule_id` below is "SCP-R-013" so it flows through the workflow; the
# prose it links to is ARCH-006.
#
# INPUT CONTRACT (materialised by the companion workflow PR, NOT this WP —
# FUP-WP-SCP-037-ARCH-006-MATERIALISER-001; same dormancy pattern as SCP-R-009):
#   input.ontology_contract            — the consumer's services.yml
#                                        runtime_contract.ontology_contract block
#                                        (object; {} when absent)
#   input.ontology_consumer            — bool; true iff the workflow determined
#                                        this repo consumes ontology (calls FOS /
#                                        imports ontology usage) — gates the
#                                        missing-contract signal so unrelated
#                                        repos never false-fire
#   input.ontology_source_markers      — array of {kind, file[, symbol]} the
#                                        workflow greps: kind "embedded_file"
#                                        (ontology_complete.yaml/value_mappings.json)
#                                        or "local_class" (Ontology/OntologyLoader/
#                                        Canonicalizer)
#   input.repo_id                      — the adopter repo identifier
#   input.ontology_authoring_allowlist — array of repo ids the SCP materialiser
#                                        INJECTS (FOS + FLA). The authoring-source
#                                        carve-out reads ONLY this — NEVER a
#                                        self-asserted field in the adopter's own
#                                        services.yml (the bypass guard).
#   input.rule_config                  — adopter .scp/rule-config.yaml (opt-out)
# Until the workflow materialises these, input lacks the keys → every guard
# short-circuits → the rule VACUOUSLY PASSES (the SCP-R-006/009 safe-failure
# precedent). DORMANT until activation; do not claim live enforcement until the
# materialiser FUP lands.
#
# Defines its OWN scp_r_013_* predicates per the SCP-R-004/006/009 precedent
# (rule-local helpers preserve per-rule coverage; adding uncovered lines to
# scp_common.rego drops every rule below the 90% gate). Reuses ONLY the
# estate-wide suppression helpers scp_active_waiver_for + scp_rule_config_disabled
# + scp_waivers + scp_waiver_expired from scp_common.rego.

package main

import rego.v1

scp_r_013_rule_id := "SCP-R-013"

scp_r_013_canonical_service := "fashion-ontology-service"

scp_r_013_remediation_url := concat("", [
	"https://github.com/jrnb2024/standards-control-plane/blob/main/",
	"standards/architecture/rules/ARCH-006-ontology-canonical-consumption.md",
])

# Adopter opt-out (mirrors SCP-R-009's idiom). Reads input.rule_config (the
# materialised adopter config). Default false = active.
default scp_r_013_opted_out := false

scp_r_013_opted_out if {
	rc := object.get(input, "rule_config", {})
	is_object(rc)
	object.get(rc, "ontology-canonical-consumption-disabled", false) == true
}

# The consumer's declared ontology_contract (or {} when absent — dormant).
scp_r_013_contract := contract if {
	contract := object.get(input, "ontology_contract", {})
	is_object(contract)
}

# The workflow-grepped source markers (or [] when absent — vacuous-pass).
scp_r_013_markers := markers if {
	markers := object.get(input, "ontology_source_markers", [])
	is_array(markers)
}

# The SCP-injected authoring allowlist (or [] when absent). SCP-owned — the
# carve-out reads THIS, never adopter-supplied content.
scp_r_013_allowlist := allowlist if {
	allowlist := object.get(input, "ontology_authoring_allowlist", [])
	is_array(allowlist)
}

# True iff the workflow flagged this repo as an ontology consumer.
scp_r_013_is_consumer if {
	object.get(input, "ontology_consumer", false) == true
}

# CARVE-OUT (bypass guard): a repo is an authoring source ONLY if its repo_id is
# on the SCP-injected allowlist. FLA (author) + FOS (server) are exempt from the
# embedded-copy / local-class signals BECAUSE they legitimately hold the source.
# A repo self-asserting role:authoring-source in its OWN services.yml gets NO
# exemption — this predicate never reads adopter content.
scp_r_013_is_authoring_source if {
	repo_id := object.get(input, "repo_id", "")
	repo_id != ""
	repo_id in scp_r_013_allowlist
}

# Conservative local-copy fallback detection: a fallback that describes a local
# ontology copy defeats the canonical. Substring check (tightening — path-shaped
# fallbacks, "embedded", etc. — tracked in the materialiser FUP).
scp_r_013_fallback_is_local(fb) if {
	is_string(fb)
	contains(lower(fb), "local")
}

# Finding builder (keeps partial-rule bodies under Regal's length cap).
scp_r_013_finding(file, message) := {
	"rule_id": scp_r_013_rule_id,
	"file": file,
	"message": message,
	"remediation_url": scp_r_013_remediation_url,
}

# --- deny-class (structural LINKAGE violations; demoted to ::warning:: by
# WARN_BASELINE membership in the workflow; a future D-NNN deny-promote flips
# that) ------------------------------------------------------------------------

# (1) an ontology consumer with NO ontology_contract declared.
scp_r_013_deny_findings contains finding if {
	scp_r_013_is_consumer
	scp_r_013_contract == {}
	finding := scp_r_013_finding(
		"services.yml",
		"SCP-R-013 (ARCH-006): repo consumes the fashion ontology but declares no ontology_contract in services.yml runtime_contract. Link to the canonical fashion-ontology-service (canonical_service + pinned canonical_version + endpoints + non-local fallback).",
	)
}

# (2) ontology_contract present but canonical_service is a bespoke name — OR
# absent/empty in a declared contract (an empty authority is still "not the
# canonical"; do not let a partially-populated contract escape both signals).
scp_r_013_deny_findings contains finding if {
	scp_r_013_contract != {}
	cs := object.get(scp_r_013_contract, "canonical_service", "")
	cs != scp_r_013_canonical_service
	finding := scp_r_013_finding(
		"services.yml",
		sprintf(
			"SCP-R-013 (ARCH-006): ontology_contract.canonical_service is %q but the one canonical ontology authority is %q. A declared ontology_contract must name fashion-ontology-service (not a bespoke/local ontology, and not empty).",
			[cs, scp_r_013_canonical_service],
		),
	)
}

# (3) an embedded canonical ontology file in a non-authoring repo.
scp_r_013_deny_findings contains finding if {
	not scp_r_013_is_authoring_source
	some m in scp_r_013_markers
	object.get(m, "kind", "") == "embedded_file"
	file := object.get(m, "file", "ontology_complete.yaml")
	finding := scp_r_013_finding(
		file,
		sprintf(
			"SCP-R-013 (ARCH-006): embedded canonical ontology file %q. Consumers must NOT vendor a divergent copy (ontology_complete.yaml / value_mappings.json) — call fashion-ontology-service. Only the authoring source (allowlisted) may hold it.",
			[file],
		),
	)
}

# (4) a local ontology re-implementation class in a non-authoring repo.
scp_r_013_deny_findings contains finding if {
	not scp_r_013_is_authoring_source
	some m in scp_r_013_markers
	object.get(m, "kind", "") == "local_class"
	file := object.get(m, "file", "")
	symbol := object.get(m, "symbol", "Ontology")
	finding := scp_r_013_finding(
		file,
		sprintf(
			"SCP-R-013 (ARCH-006): local ontology re-implementation %q in %q. Do not re-implement canonicalization — consume fashion-ontology-service. Only the authoring source (allowlisted) may.",
			[symbol, file],
		),
	)
}

# (5) fallback resolves to a local ontology copy.
scp_r_013_deny_findings contains finding if {
	scp_r_013_contract != {}
	fb := object.get(scp_r_013_contract, "fallback", "")
	fb != ""
	scp_r_013_fallback_is_local(fb)
	finding := scp_r_013_finding(
		"services.yml",
		sprintf(
			"SCP-R-013 (ARCH-006): ontology_contract.fallback %q resolves to a local ontology copy. A stale local fallback defeats the canonical; fail the request or degrade, do not read a vendored copy.",
			[fb],
		),
	)
}

# True iff the rule produced ANY finding — guards the suppression-observability
# records so a suppressed finding is still observable (SCP-R-009 precedent).
scp_r_013_any_findings if {
	count(scp_r_013_deny_findings) > 0
}

# Public deny rule. Warn-baseline membership in the workflow demotes these to
# ::warning:: + excludes from the merge-gate threshold; a future D-NNN flips it.
deny contains output if {
	some finding in scp_r_013_deny_findings
	not scp_r_013_opted_out
	not scp_active_waiver_for(scp_r_013_rule_id)
	not scp_rule_config_disabled(scp_r_013_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

# Suppression-observability warn: active waiver against SCP-R-013.
warn contains record if {
	scp_r_013_any_findings
	some w in scp_waivers
	object.get(w, "rule_id", "") == scp_r_013_rule_id
	not scp_waiver_expired(w)
	record := {
		"kind": "waiver",
		"rule_id": scp_r_013_rule_id,
		"waiver_id": object.get(w, "waiver_id", ""),
		"msg": sprintf("SCP-R-013 findings suppressed by active waiver %s", [object.get(w, "waiver_id", "")]),
	}
}

# Suppression-observability warn: `.scp/rule-config.yaml` disable or opt-out.
warn contains record if {
	scp_r_013_any_findings
	scp_r_013_opted_out
	record := {
		"kind": "rule-config-disable",
		"rule_id": scp_r_013_rule_id,
		"msg": "SCP-R-013 findings suppressed by ontology-canonical-consumption-disabled opt-out",
	}
}

warn contains record if {
	scp_r_013_any_findings
	scp_rule_config_disabled(scp_r_013_rule_id)
	record := {
		"kind": "rule-config-disable",
		"rule_id": scp_r_013_rule_id,
		"msg": "SCP-R-013 findings suppressed by rule-config disable",
	}
}
