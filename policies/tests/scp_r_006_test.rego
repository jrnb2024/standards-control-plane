package main_test

import data.main
import rego.v1

# Helpers — collect SCP-R-006 deny + warn records, optionally with
# waivers / rule-config / mocked time. Mirrors scp_r_004_test.rego shape.
# SCP-R-006 evaluates against a MULTI-FILE input shape (input.services_yml
# + input.rule_config + input.changed_files + ...) materialised by the
# workflow per RULE-003 §3.4 "Implementation note — workflow-glob
# narrowing". Until the sibling Codex Tier 2 PR materialises these
# inputs, R-006 vacuously passes under the existing per-file evaluation
# envelope.

scp_r_006_deny(input_value) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
		finding.rule_id == "SCP-R-006"
	]
}

scp_r_006_warn(input_value) := records if {
	records := [record |
		some record in main.warn with input as input_value
		record.rule_id == "SCP-R-006"
	]
}

scp_r_006_deny_full(input_value, waivers, rule_config) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
		finding.rule_id == "SCP-R-006"
	]
}

scp_r_006_warn_full(input_value, waivers, rule_config) := records if {
	records := [record |
		some record in main.warn with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
		record.rule_id == "SCP-R-006"
	]
}

# Standard estate-repos registry for tests. One service entry per the
# v1.4.0 ship contract (single ACC SA UUID across the estate).
scp_r_006_test_registry := {"services": [
	{
		"service_id": "control-tower",
		"acc_sa_uuid": "11111111-2222-3333-4444-555555555555",
	},
	{
		"service_id": "mapp-pim",
		"acc_sa_uuid": "11111111-2222-3333-4444-555555555555",
	},
]}

# Standard signed manifest for tests.
scp_r_006_test_manifest := {"entries": [{
	"target_repo_app_id": "ct-001",
	"mcp_server_sha256": "abc123def456abc123def456abc123def456abc123def456abc123def456",
}]}

# Standard rule_config for tests (acc-cross-repo-caller-scoped: true).
scp_r_006_test_rule_config_opted_in := {"acc-cross-repo-caller-scoped": true}

# ============================================================================
# Vacuous-pass tests (Inv-A through Inv-D require opt-in + trigger).
# ============================================================================

# (1) No rule_config opt-in → vacuous pass.
test_scp_r_006_no_opt_in_vacuous_pass if {
	input_value := {
		"changed_files": ["services.yml"],
		"services_yml": {"services": {"app": {"runtime_contract": {}}}},
	}
	count(scp_r_006_deny(input_value)) == 0
	count(scp_r_006_warn(input_value)) == 0
}

# (2) Opt-in but no trigger path in diff → vacuous pass.
test_scp_r_006_opted_in_no_trigger_vacuous_pass if {
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": ["docs/README.md"],
		"services_yml": {"services": {"app": {"runtime_contract": {}}}},
	}
	count(scp_r_006_deny(input_value)) == 0
	count(scp_r_006_warn(input_value)) == 0
}

# (3) Empty input (per-file envelope; current production state) → vacuous pass.
test_scp_r_006_empty_input_vacuous_pass if {
	count(scp_r_006_deny({})) == 0
	count(scp_r_006_warn({})) == 0
}

# ============================================================================
# Inv-A — allowed_callers declared
# ============================================================================

# (4) Opt-in + services.yml in diff + no allowed_callers → 1 Inv-A warn.
test_scp_r_006_inv_a_missing_allowed_callers if {
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": ["services.yml"],
		"services_yml": {"services": {"app": {"runtime_contract": {}}}},
		"estate_repos_yaml": scp_r_006_test_registry,
	}

	# At warn baseline; not promoted to deny.
	warns := scp_r_006_warn(input_value)
	count([w | some w in warns; w.invariant == "Inv-A"]) == 1

	# No deny (no threshold-override-deny set).
	denies := scp_r_006_deny(input_value)
	count([d | some d in denies; d.invariant == "Inv-A"]) == 0
}

# (5) Opt-in + services.yml in diff + allowed_callers present but empty → 1 Inv-A warn.
test_scp_r_006_inv_a_empty_allowed_callers if {
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": ["services.yml"],
		"services_yml": {"services": {"app": {"runtime_contract": {"allowed_callers": []}}}},
		"estate_repos_yaml": scp_r_006_test_registry,
	}
	warns := scp_r_006_warn(input_value)
	count([w | some w in warns; w.invariant == "Inv-A"]) == 1
}

# (6) Opt-in + valid allowed_callers → no Inv-A finding.
test_scp_r_006_inv_a_satisfied if {
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": ["services.yml"],
		"services_yml": {"services": {"app": {"runtime_contract": {"allowed_callers": ["control-tower"]}}}},
		"estate_repos_yaml": scp_r_006_test_registry,
	}
	warns := scp_r_006_warn(input_value)
	count([w | some w in warns; w.invariant == "Inv-A"]) == 0
}

# ============================================================================
# Inv-B — allowed_callers entries are in the estate registry
# ============================================================================

# (7) Opt-in + allowed_callers entry NOT in registry → 1 Inv-B warn.
test_scp_r_006_inv_b_unknown_caller if {
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": ["services.yml"],
		"services_yml": {"services": {"app": {"runtime_contract": {"allowed_callers": ["unknown-caller"]}}}},
		"estate_repos_yaml": scp_r_006_test_registry,
	}
	warns := scp_r_006_warn(input_value)
	count([w | some w in warns; w.invariant == "Inv-B"]) == 1
	some w in warns
	w.invariant == "Inv-B"
	w.caller == "unknown-caller"
}

# (8) Multiple unknown callers → multiple Inv-B findings.
test_scp_r_006_inv_b_multiple_unknown if {
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": ["services.yml"],
		"services_yml": {"services": {"app": {"runtime_contract": {"allowed_callers": ["unknown-1", "unknown-2"]}}}},
		"estate_repos_yaml": scp_r_006_test_registry,
	}
	warns := scp_r_006_warn(input_value)
	count([w | some w in warns; w.invariant == "Inv-B"]) == 2
}

# (9) All callers in registry → no Inv-B findings.
test_scp_r_006_inv_b_all_known if {
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": ["services.yml"],
		"services_yml": {"services": {"app": {"runtime_contract": {"allowed_callers": ["control-tower", "mapp-pim"]}}}},
		"estate_repos_yaml": scp_r_006_test_registry,
	}
	warns := scp_r_006_warn(input_value)
	count([w | some w in warns; w.invariant == "Inv-B"]) == 0
}

# ============================================================================
# Inv-C — MCP server SHA-pinned (UNCONDITIONAL DENY)
# ============================================================================

# (10) Opt-in + MCP server present + SHA mismatches manifest → 1 Inv-C deny.
test_scp_r_006_inv_c_sha_mismatch_unconditional_deny if {
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": [".acc/mcp_server.py"],
		"mcp_server_path": ".acc/mcp_server.py",
		"mcp_server_sha256": "WRONG_SHA",
		"target_repo_app_id": "ct-001",
		"signed_manifest": scp_r_006_test_manifest,
		"services_yml": {"services": {"app": {"runtime_contract": {"allowed_callers": ["control-tower"]}}}},
		"estate_repos_yaml": scp_r_006_test_registry,
	}
	denies := scp_r_006_deny(input_value)
	count([d | some d in denies; d.invariant == "Inv-C"]) == 1
	some d in denies
	d.invariant == "Inv-C"
	contains(d.message, "WRONG_SHA")
}

# (11) Opt-in + MCP server present + SHA matches manifest → no Inv-C finding.
test_scp_r_006_inv_c_sha_match_pass if {
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": [".acc/mcp_server.py"],
		"mcp_server_path": ".acc/mcp_server.py",
		"mcp_server_sha256": "abc123def456abc123def456abc123def456abc123def456abc123def456",
		"target_repo_app_id": "ct-001",
		"signed_manifest": scp_r_006_test_manifest,
		"services_yml": {"services": {"app": {"runtime_contract": {"allowed_callers": ["control-tower"]}}}},
		"estate_repos_yaml": scp_r_006_test_registry,
	}
	denies := scp_r_006_deny(input_value)
	count([d | some d in denies; d.invariant == "Inv-C"]) == 0
}

# (12) Opt-in + MCP server present + NO manifest entry → 1 Inv-C-missing-entry deny.
# (CORR-MAJ-002 R1 fail-CLOSED fix.)
test_scp_r_006_inv_c_missing_entry_unconditional_deny if {
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": [".acc/mcp_server.py"],
		"mcp_server_path": ".acc/mcp_server.py",
		"mcp_server_sha256": "any-sha",
		"target_repo_app_id": "unknown-app-id",
		"signed_manifest": scp_r_006_test_manifest,
		"services_yml": {"services": {"app": {"runtime_contract": {"allowed_callers": ["control-tower"]}}}},
		"estate_repos_yaml": scp_r_006_test_registry,
	}
	denies := scp_r_006_deny(input_value)
	count([d | some d in denies; d.invariant == "Inv-C-missing-entry"]) == 1
}

# (13) Inv-C is UNCONDITIONAL — waiver does NOT suppress.
test_scp_r_006_inv_c_waiver_does_not_suppress if {
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": [".acc/mcp_server.py"],
		"mcp_server_path": ".acc/mcp_server.py",
		"mcp_server_sha256": "WRONG_SHA",
		"target_repo_app_id": "ct-001",
		"signed_manifest": scp_r_006_test_manifest,
		"services_yml": {"services": {"app": {"runtime_contract": {"allowed_callers": ["control-tower"]}}}},
		"estate_repos_yaml": scp_r_006_test_registry,
	}
	waivers := [{
		"waiver_id": "scp-r-006-temp",
		"rule_id": "SCP-R-006",
		"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/100",
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29T00:00:00Z",
		"expires_at": "2099-12-31T00:00:00Z",
	}]
	denies := scp_r_006_deny_full(input_value, waivers, {})
	count([d | some d in denies; d.invariant == "Inv-C"]) == 1
}

# (14) Inv-C is UNCONDITIONAL — rule-config-disable does NOT suppress.
test_scp_r_006_inv_c_rule_config_disable_does_not_suppress if {
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": [".acc/mcp_server.py"],
		"mcp_server_path": ".acc/mcp_server.py",
		"mcp_server_sha256": "WRONG_SHA",
		"target_repo_app_id": "ct-001",
		"signed_manifest": scp_r_006_test_manifest,
		"services_yml": {"services": {"app": {"runtime_contract": {"allowed_callers": ["control-tower"]}}}},
		"estate_repos_yaml": scp_r_006_test_registry,
	}
	rule_config := {"rules": {"SCP-R-006": {"disable": true, "justification": "test", "expires_at": "2099-12-31"}}}

	# Override input.rule_config inside the union — Inv-C still fires.
	denies := scp_r_006_deny_full(input_value, [], rule_config)
	count([d | some d in denies; d.invariant == "Inv-C"]) == 1
}

# ============================================================================
# Inv-D — audit-log sender_acc_sa_uuid is in registry
# ============================================================================

# (15) Opt-in + audit log with orphan UUID → 1 Inv-D warn.
test_scp_r_006_inv_d_orphan_uuid if {
	audit_jsonl := concat("\n", [
		`{"event": "received", "sender_acc_sa_uuid": "11111111-2222-3333-4444-555555555555"}`,
		`{"event": "received", "sender_acc_sa_uuid": "deadbeef-0000-0000-0000-000000000000"}`,
	])
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": [".acc/cross-repo-received-events.jsonl"],
		"audit_log_path": ".acc/cross-repo-received-events.jsonl",
		"audit_log_contents": audit_jsonl,
		"estate_repos_yaml": scp_r_006_test_registry,
		"services_yml": {"services": {"app": {"runtime_contract": {"allowed_callers": ["control-tower"]}}}},
	}
	warns := scp_r_006_warn(input_value)
	count([w | some w in warns; w.invariant == "Inv-D"]) == 1
	some w in warns
	w.invariant == "Inv-D"
	w.sender == "deadbeef-0000-0000-0000-000000000000"
}

# (16) All audit-log UUIDs known → no Inv-D findings.
test_scp_r_006_inv_d_all_known if {
	audit_jsonl := `{"event": "received", "sender_acc_sa_uuid": "11111111-2222-3333-4444-555555555555"}`
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": [".acc/cross-repo-received-events.jsonl"],
		"audit_log_path": ".acc/cross-repo-received-events.jsonl",
		"audit_log_contents": audit_jsonl,
		"estate_repos_yaml": scp_r_006_test_registry,
		"services_yml": {"services": {"app": {"runtime_contract": {"allowed_callers": ["control-tower"]}}}},
	}
	warns := scp_r_006_warn(input_value)
	count([w | some w in warns; w.invariant == "Inv-D"]) == 0
}

# (17) Multiple orphan UUIDs → multiple Inv-D findings.
test_scp_r_006_inv_d_multiple_orphans if {
	audit_jsonl := concat("\n", [
		`{"event": "received", "sender_acc_sa_uuid": "orphan-1"}`,
		`{"event": "received", "sender_acc_sa_uuid": "orphan-2"}`,
		`{"event": "received", "sender_acc_sa_uuid": "orphan-3"}`,
	])
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": [".acc/cross-repo-received-events.jsonl"],
		"audit_log_path": ".acc/cross-repo-received-events.jsonl",
		"audit_log_contents": audit_jsonl,
		"estate_repos_yaml": scp_r_006_test_registry,
		"services_yml": {"services": {"app": {"runtime_contract": {"allowed_callers": ["control-tower"]}}}},
	}
	warns := scp_r_006_warn(input_value)
	count([w | some w in warns; w.invariant == "Inv-D"]) == 3
}

# ============================================================================
# Suppression-path tests (Inv-A/B/D only — Inv-C is unconditional)
# ============================================================================

# (18) Inv-A + active waiver → no warn finding + suppression-observability record.
test_scp_r_006_inv_a_active_waiver_suppresses if {
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": ["services.yml"],
		"services_yml": {"services": {"app": {"runtime_contract": {}}}},
		"estate_repos_yaml": scp_r_006_test_registry,
	}
	waivers := [{
		"waiver_id": "scp-r-006-temp",
		"rule_id": "SCP-R-006",
		"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/100",
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29T00:00:00Z",
		"expires_at": "2099-12-31T00:00:00Z",
	}]
	warns := scp_r_006_warn_full(input_value, waivers, scp_r_006_test_rule_config_opted_in)

	# Original Inv-A warn suppressed; only the suppression-observability record remains.
	count([w | some w in warns; w.invariant == "Inv-A"]) == 0
	count([w | some w in warns; w.kind == "waiver"]) >= 1
}

# (19) Inv-A + threshold-overrides: deny → finding moves from warn to deny.
test_scp_r_006_threshold_override_deny_moves_to_deny if {
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": ["services.yml"],
		"services_yml": {"services": {"app": {"runtime_contract": {}}}},
		"estate_repos_yaml": scp_r_006_test_registry,
	}
	rule_config_with_override := {
		"acc-cross-repo-caller-scoped": true,
		"threshold-overrides": {"SCP-R-006": "deny"},
	}
	warns := scp_r_006_warn_full(input_value, [], rule_config_with_override)
	denies := scp_r_006_deny_full(input_value, [], rule_config_with_override)
	count([w | some w in warns; w.invariant == "Inv-A"]) == 0
	count([d | some d in denies; d.invariant == "Inv-A"]) == 1
}

# (20) Inv-A + threshold-overrides: disable → no finding.
test_scp_r_006_threshold_override_disable_suppresses if {
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": ["services.yml"],
		"services_yml": {"services": {"app": {"runtime_contract": {}}}},
		"estate_repos_yaml": scp_r_006_test_registry,
	}
	rule_config_with_disable := {
		"acc-cross-repo-caller-scoped": true,
		"threshold-overrides": {"SCP-R-006": "disable"},
	}
	warns := scp_r_006_warn_full(input_value, [], rule_config_with_disable)
	denies := scp_r_006_deny_full(input_value, [], rule_config_with_disable)
	count([w | some w in warns; w.invariant == "Inv-A"]) == 0
	count([d | some d in denies; d.invariant == "Inv-A"]) == 0
}

# (21) Inv-C + threshold-overrides: disable → STILL fires (unconditional per §3.2).
test_scp_r_006_inv_c_threshold_override_does_not_suppress if {
	input_value := {
		"rule_config": scp_r_006_test_rule_config_opted_in,
		"changed_files": [".acc/mcp_server.py"],
		"mcp_server_path": ".acc/mcp_server.py",
		"mcp_server_sha256": "WRONG_SHA",
		"target_repo_app_id": "ct-001",
		"signed_manifest": scp_r_006_test_manifest,
		"services_yml": {"services": {"app": {"runtime_contract": {"allowed_callers": ["control-tower"]}}}},
		"estate_repos_yaml": scp_r_006_test_registry,
	}
	rule_config_with_disable := {
		"acc-cross-repo-caller-scoped": true,
		"threshold-overrides": {"SCP-R-006": "disable"},
	}
	denies := scp_r_006_deny_full(input_value, [], rule_config_with_disable)
	count([d | some d in denies; d.invariant == "Inv-C"]) == 1
}
