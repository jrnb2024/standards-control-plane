# RULE: SCP-R-006 — see docs/reviews/rule-proposals/RULE-003-acc-cross-repo-caller.md
#
# ACC-as-cross-repo-caller invariants (per D-036 + RULE-003). Fires when
# the adopter opts in via `.scp/rule-config.yaml` `acc-cross-repo-caller-scoped: true`
# AND at least one of the rule's trigger paths is in the PR diff
# (`services.yml`, `.acc/mcp_server.{py,ts}`, `.acc/cross-repo-received-events.jsonl`).
# Four invariants (Inv-A through Inv-D); see RULE-003 §3.1 for full semantics.
#
# **Inv-C is unconditional-deny** per RULE-003 §3.2 SB-MAJ-003 fix —
# tamper detection is binary, not ramp-able. Inv-A/B/D are warn baseline;
# adopters can promote to deny via `.scp/rule-config.yaml`
# `threshold-overrides: { SCP-R-006: deny }`.
#
# **v1.4.0 ship scope:** this Rego ships at content-addition non-kernel-
# dangerous footprint (rule body + tests + schemas). The companion
# workflow extension to materialise `input.services_yml`,
# `input.changed_files`, `input.rule_config`, `input.mcp_server_path`,
# `input.mcp_server_sha256`, `input.audit_log_path`, `input.audit_log_contents`,
# `input.estate_repos_yaml`, `input.signed_manifest`, `input.target_repo_app_id`
# lands in a sibling Codex Tier 2 PR (kernel-dangerous). Until that sibling
# PR lands, the rule is loaded but the invariant guards do not match
# (`input.rule_config` will be absent under the per-file evaluation
# envelope existing rules use); the rule vacuously passes. This is the
# safe failure mode.
#
# Defines its OWN `scp_r_006_*` predicates per the SCP-R-004 SAFE-MAJ-001
# precedent — TF-008 refactor of SCP-R-002 cannot silently break SCP-R-006.
# Reuses TWO shared helpers from scp_common.rego (used estate-wide):
# `scp_active_waiver_for` + `scp_rule_config_disabled`.
# All other helpers (threshold-overrides / glob_match / jsonl_records /
# manifest_lookup / manifest_has_entry) are RULE-003-local in the
# `scp_r_006_*` namespace per the per-rule coverage discipline below.

package main

import rego.v1

scp_r_006_rule_id := "SCP-R-006"

scp_r_006_remediation_url := concat("", [
	"https://github.com/jrnb2024/standards-control-plane/blob/main/",
	"docs/reviews/rule-proposals/RULE-003-acc-cross-repo-caller.md",
])

# Inv-D annotation cap per RULE-003 §3.3 — at most 10 orphan-UUID findings
# per PR to bound annotation noise on populated audit logs.
scp_r_006_inv_d_cap := 10

# ============================================================================
# Rule-local helpers per RULE-003 §3.4 (originally specified as additions
# to scp_common.rego shared across all rules; landed here in
# `scp_r_006_*` namespace per the per-rule coverage discipline — adding
# uncovered lines to scp_common.rego drops every existing rule's coverage
# below the 90% threshold the per-rule-coverage CI gate enforces).
# When RULE-002 (D-049 design-system; SCP-R-005) ships its Rego, it will
# need a parallel set of helpers OR a refactor extracting a shared
# helpers module with proper per-rule coverage strategy. Filed forward as
# TF-SCP-R-006-HELPERS-SHARED-001 (P3).
# ============================================================================

# True iff `.scp/rule-config.yaml` `threshold-overrides[rule_id] == "deny"`.
# Reads `data.rule_config.threshold-overrides` directly (NOT via object.get
# wrappers — OPA's recursion checker treats wrapper access as depending on
# every `data.*` rule, including `deny`, producing rego_recursion_error).
default scp_r_006_threshold_override_deny(_) := false

scp_r_006_threshold_override_deny(rule_id) if {
	data.rule_config["threshold-overrides"][rule_id] == "deny"
}

# True iff `.scp/rule-config.yaml` `threshold-overrides[rule_id]` is
# `"disable"` or `"off"`. Mirrors RULE-002 §3.2 enum {warn, deny, disable, off}.
default scp_r_006_threshold_override_disable(_) := false

scp_r_006_threshold_override_disable(rule_id) if {
	data.rule_config["threshold-overrides"][rule_id] == "disable"
}

scp_r_006_threshold_override_disable(rule_id) if {
	data.rule_config["threshold-overrides"][rule_id] == "off"
}

# Simple glob matcher. Translates `*` → `.*` and `?` → `.` per POSIX
# shell-glob convention; escapes regex special chars in the rest.
# Anchored to the full path (matches `^pattern$`).
scp_r_006_glob_match(pattern, path) if {
	escaped := regex.replace(pattern, `[.+^$()|{}\[\]\\]`, "\\$0")
	with_star := replace(escaped, "*", ".*")
	with_q := replace(with_star, "?", ".")
	regex.match(sprintf("^%s$", [with_q]), path)
}

# Parse JSONL string into a list of objects. Empty + non-object lines
# skipped (defensive against partial writes + log rotation artefacts).
scp_r_006_jsonl_records(content) := records if {
	is_string(content)
	lines := split(content, "\n")
	records := [record |
		some line in lines
		line != ""
		record := json.unmarshal(line)
		is_object(record)
	]
}

scp_r_006_jsonl_records(content) := [] if {
	not is_string(content)
}

# Look up a manifest entry by `target_repo_app_id`. Use
# `scp_r_006_manifest_has_entry` to test existence before calling.
scp_r_006_manifest_lookup(manifest, target_repo_app_id) := entry if {
	is_object(manifest)
	some entry in manifest.entries
	entry.target_repo_app_id == target_repo_app_id
}

# True iff the manifest has at least one entry for the given
# `target_repo_app_id`. Closes SCP-R-006 Inv-C R1 fail-OPEN gap
# (CORR-MAJ-002 in RULE-003 R1 review).
scp_r_006_manifest_has_entry(manifest, target_repo_app_id) if {
	is_object(manifest)
	some entry in manifest.entries
	entry.target_repo_app_id == target_repo_app_id
}

# Trigger paths the rule fires on (any one in the PR diff). Per
# RULE-003 §3.1 condition 2.
scp_r_006_trigger_paths := [
	"services.yml",
	".acc/mcp_server.py",
	".acc/mcp_server.ts",
	".acc/cross-repo-received-events.jsonl",
]

# Adopter opt-in gate. Per RULE-003 §3.1 condition 1.
# Vacuous false when `input.rule_config` is absent (i.e., the per-file
# evaluation envelope the existing rules use). Safe failure mode.
scp_r_006_acc_scoped if {
	rc := object.get(input, "rule_config", {})
	is_object(rc)
	object.get(rc, "acc-cross-repo-caller-scoped", false) == true
}

# True when at least one trigger path is in the PR diff. Per RULE-003
# §3.1 condition 2.
scp_r_006_trigger_present if {
	changed := object.get(input, "changed_files", [])
	is_array(changed)
	some changed_file in changed
	some trigger in scp_r_006_trigger_paths
	scp_r_006_glob_match(trigger, changed_file)
}

# Canonical service-id registry — the set of valid `allowed_callers`
# entries. Loaded from `input.estate_repos_yaml.services[].service_id`
# by the workflow.
scp_r_006_known_service_ids contains service_id if {
	registry := object.get(input, "estate_repos_yaml", {})
	is_object(registry)
	services := object.get(registry, "services", [])
	is_array(services)
	some service in services
	is_object(service)
	service_id := object.get(service, "service_id", "")
	service_id != ""
}

# Canonical ACC SA UUID registry — the set of valid `sender_acc_sa_uuid`
# values. Loaded from `input.estate_repos_yaml.services[].acc_sa_uuid` by
# the workflow. At v1.4.0 this is a one-element set per RULE-003 §3.1
# (single SA UUID across all 9 estate repos).
scp_r_006_known_acc_sa_uuids contains sa_uuid if {
	registry := object.get(input, "estate_repos_yaml", {})
	is_object(registry)
	services := object.get(registry, "services", [])
	is_array(services)
	some service in services
	is_object(service)
	sa_uuid := object.get(service, "acc_sa_uuid", "")
	sa_uuid != ""
}

# Helper: services.yml has at least one service with non-empty
# `allowed_callers`. Iterates the services dict (key, value) per
# RULE-003 CORR-MAJ-003 R1 fix.
scp_r_006_services_have_allowed_callers if {
	svcyml := object.get(input, "services_yml", {})
	is_object(svcyml)
	services := object.get(svcyml, "services", {})
	is_object(services)
	some service in services
	is_object(service)
	rc := object.get(service, "runtime_contract", {})
	is_object(rc)
	callers := object.get(rc, "allowed_callers", [])
	is_array(callers)
	count(callers) > 0
}

# Inv-A — `runtime_contract.allowed_callers` declared (non-empty list).
# Fires once per PR when the adopter is acc-cross-repo-caller-scoped + a
# trigger path is in the diff + no service in services.yml has a
# non-empty allowed_callers list.
scp_r_006_inv_a_findings contains finding if {
	scp_r_006_acc_scoped
	scp_r_006_trigger_present
	not scp_r_006_services_have_allowed_callers
	finding := {
		"rule_id": scp_r_006_rule_id,
		"file": "services.yml",
		"message": "SCP-R-006 Inv-A: 'runtime_contract.allowed_callers' missing or empty — required for acc-cross-repo-caller-scoped: true adopter. See D-036 Element 1.",
		"invariant": "Inv-A",
		"remediation_url": scp_r_006_remediation_url,
	}
}

# Helper: build Inv-B finding object (extracted to keep rule body under
# Regal's max-rule-length threshold).
scp_r_006_inv_b_finding(service_name, caller) := finding if {
	finding := {
		"rule_id": scp_r_006_rule_id,
		"file": "services.yml",
		"message": sprintf(
			"SCP-R-006 Inv-B: services.%s.runtime_contract.allowed_callers entry '%s' not in estate registry. See estate_repos.yaml.",
			[service_name, caller],
		),
		"invariant": "Inv-B",
		"service_name": service_name,
		"caller": caller,
		"remediation_url": scp_r_006_remediation_url,
	}
}

# Inv-B — every `allowed_callers` entry is in the estate registry.
# Fires per-entry. Per RULE-003 §3.1 Inv-B + CORR-MAJ-003 R1 fix
# (services.yml `services:` is a mapping, not a list).
scp_r_006_inv_b_findings contains finding if {
	scp_r_006_acc_scoped
	scp_r_006_trigger_present
	svcyml := object.get(input, "services_yml", {})
	is_object(svcyml)
	services := object.get(svcyml, "services", {})
	is_object(services)
	some service_name, service in services
	is_object(service)
	rc := object.get(service, "runtime_contract", {})
	is_object(rc)
	callers := object.get(rc, "allowed_callers", [])
	is_array(callers)
	some caller in callers
	is_string(caller)
	not caller in scp_r_006_known_service_ids
	finding := scp_r_006_inv_b_finding(service_name, caller)
}

# Helper: build Inv-C SHA-mismatch finding.
scp_r_006_inv_c_mismatch_finding(path, expected_sha, actual_sha) := finding if {
	finding := {
		"rule_id": scp_r_006_rule_id,
		"file": path,
		"message": sprintf(
			"SCP-R-006 Inv-C: MCP server source SHA mismatch. Expected %s; got %s. See D-036 Element 3.",
			[expected_sha, actual_sha],
		),
		"invariant": "Inv-C",
		"severity": "deny",
		"remediation_url": scp_r_006_remediation_url,
	}
}

# Helper: build Inv-C missing-entry finding (CORR-MAJ-002 R1 fix —
# fail-CLOSED when manifest has no entry for an on-disk MCP server).
scp_r_006_inv_c_missing_entry_finding(path, target_repo_app_id) := finding if {
	finding := {
		"rule_id": scp_r_006_rule_id,
		"file": path,
		"message": sprintf(
			"SCP-R-006 Inv-C: MCP server source present on disk but no entry in signed manifest for target_repo_app_id '%s'. See D-036 Element 3.",
			[target_repo_app_id],
		),
		"invariant": "Inv-C-missing-entry",
		"severity": "deny",
		"remediation_url": scp_r_006_remediation_url,
	}
}

# Inv-C — MCP server source SHA matches signed manifest entry.
# UNCONDITIONAL DENY per RULE-003 §3.2 SB-MAJ-003 (tamper detection
# is binary, not ramp-able). Two failure modes:
#   (a) SHA mismatch — on-disk SHA differs from manifest entry SHA;
#   (b) Missing entry — on-disk MCP server exists but no manifest entry
#       for target_repo_app_id (CORR-MAJ-002 R1 fail-CLOSED fix).
scp_r_006_inv_c_findings contains finding if {
	scp_r_006_acc_scoped
	scp_r_006_trigger_present
	mcp_path := object.get(input, "mcp_server_path", "")
	mcp_path != ""
	manifest := object.get(input, "signed_manifest", {})
	target := object.get(input, "target_repo_app_id", "")
	target != ""
	scp_r_006_manifest_has_entry(manifest, target)
	entry := scp_r_006_manifest_lookup(manifest, target)
	expected_sha := object.get(entry, "mcp_server_sha256", "")
	expected_sha != ""
	actual_sha := object.get(input, "mcp_server_sha256", "")
	actual_sha != ""
	expected_sha != actual_sha
	finding := scp_r_006_inv_c_mismatch_finding(mcp_path, expected_sha, actual_sha)
}

scp_r_006_inv_c_findings contains finding if {
	scp_r_006_acc_scoped
	scp_r_006_trigger_present
	mcp_path := object.get(input, "mcp_server_path", "")
	mcp_path != ""
	manifest := object.get(input, "signed_manifest", {})
	target := object.get(input, "target_repo_app_id", "")
	target != ""
	not scp_r_006_manifest_has_entry(manifest, target)
	finding := scp_r_006_inv_c_missing_entry_finding(mcp_path, target)
}

# Helper: build Inv-D orphan-UUID finding.
scp_r_006_inv_d_finding(audit_path, sender) := finding if {
	finding := {
		"rule_id": scp_r_006_rule_id,
		"file": audit_path,
		"message": sprintf(
			"SCP-R-006 Inv-D: orphan sender_acc_sa_uuid '%s' — not in ACC SA UUID registry. See estate_repos.yaml.",
			[sender],
		),
		"invariant": "Inv-D",
		"sender": sender,
		"remediation_url": scp_r_006_remediation_url,
	}
}

# Inv-D — audit-log `sender_acc_sa_uuid` is in the registry.
# Fires per orphan entry (10-cap rendering is workflow-side per
# RULE-003 §3.3; this rule body produces all findings). Warn baseline
# (Inv-A/B/D are ramp-able; Inv-C is unconditional-deny).
scp_r_006_inv_d_findings contains finding if {
	scp_r_006_acc_scoped
	scp_r_006_trigger_present
	audit_path := object.get(input, "audit_log_path", "")
	audit_path != ""
	contents := object.get(input, "audit_log_contents", "")
	some record in scp_r_006_jsonl_records(contents)
	is_object(record)
	sender := object.get(record, "sender_acc_sa_uuid", "")
	sender != ""
	not sender in scp_r_006_known_acc_sa_uuids
	finding := scp_r_006_inv_d_finding(audit_path, sender)
}

# Aggregator: ramp-able findings (Inv-A + Inv-B + Inv-D). Subject to
# warn/deny baseline + threshold-overrides + waiver suppression +
# rule-config-disable. Per RULE-003 §3.4 CORR-MIN-003 R1 fix (explicit
# partial-rule aggregator instead of set-union syntax).
scp_r_006_ramp_findings contains finding if {
	some finding in scp_r_006_inv_a_findings
}

scp_r_006_ramp_findings contains finding if {
	some finding in scp_r_006_inv_b_findings
}

scp_r_006_ramp_findings contains finding if {
	some finding in scp_r_006_inv_d_findings
}

# Public deny rule. Two pathways:
#   (a) Ramp-able findings (Inv-A/B/D) when adopter has set
#       `threshold-overrides: { SCP-R-006: deny }`. Subject to waiver
#       + rule-config-disable + threshold-override-disable suppression.
#   (b) Inv-C findings — UNCONDITIONAL deny per RULE-003 §3.2 SB-MAJ-003.
#       Inv-C exempt from waiver + rule-config-disable + threshold-overrides
#       per RULE-003 §3.2 ("Inv-C is NOT subject to the `disable: true`
#       waiver"). Tamper detection is binary.
deny contains output if {
	some finding in scp_r_006_ramp_findings
	not scp_active_waiver_for(scp_r_006_rule_id)
	not scp_rule_config_disabled(scp_r_006_rule_id)
	not scp_r_006_threshold_override_disable(scp_r_006_rule_id)
	scp_r_006_threshold_override_deny(scp_r_006_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

deny contains output if {
	some finding in scp_r_006_inv_c_findings
	output := object.union(finding, {"msg": finding.message})
}

# Public warn rule. Ramp-able findings (Inv-A/B/D) at warn baseline
# when adopter has NOT set `threshold-overrides: { SCP-R-006: deny }`.
# Subject to waiver + rule-config-disable + threshold-override-disable
# suppression.
warn contains output if {
	some finding in scp_r_006_ramp_findings
	not scp_active_waiver_for(scp_r_006_rule_id)
	not scp_rule_config_disabled(scp_r_006_rule_id)
	not scp_r_006_threshold_override_disable(scp_r_006_rule_id)
	not scp_r_006_threshold_override_deny(scp_r_006_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

# Suppression-observability warn: active waiver against SCP-R-006.
# Mirrors SCP-R-002/003/004/007/008 warn-rule shape. Note: Inv-C
# findings are NOT included here because Inv-C is exempt from waiver
# suppression per RULE-003 §3.2.
warn contains record if {
	count(scp_r_006_ramp_findings) > 0
	some w in scp_waivers
	object.get(w, "rule_id", "") == scp_r_006_rule_id
	not scp_waiver_expired(w)
	record := {
		"kind": "waiver",
		"rule_id": scp_r_006_rule_id,
		"waiver_id": object.get(w, "waiver_id", ""),
		"msg": sprintf(
			"SCP-R-006 ramp-able findings suppressed by active waiver %s (Inv-C exempt; not suppressed)",
			[object.get(w, "waiver_id", "")],
		),
	}
}

# Suppression-observability warn: `.scp/rule-config.yaml disable: true`.
warn contains record if {
	count(scp_r_006_ramp_findings) > 0
	scp_rule_config_disabled(scp_r_006_rule_id)
	record := {
		"kind": "rule-config-disable",
		"rule_id": scp_r_006_rule_id,
		"msg": "SCP-R-006 ramp-able findings suppressed by .scp/rule-config.yaml disable: true (Inv-C exempt; not suppressed)",
	}
}
