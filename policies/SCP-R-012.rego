# RULE: SCP-R-012 — see docs/reviews/rule-proposals/RULE-006-protected-table-migration-marker.md
#
# Destructive schema-migration operations (drop / rename / destructive-alter of a
# table or column) in an Alembic-style migration file (a `.py` under a
# `…/versions/…` directory) must carry the attestation marker
# `scp:protected-table-attested`. The marker is the AUTHOR'S assertion that the
# migration was checked against the domain's protected-tables policy (owned by
# CT — SCP does NOT enumerate protected tables; LINKAGE-not-VALUES per D-058).
# It catches the dangerous class — a destructive migration sailing through
# review and silently rewriting an auth/identity/tenancy table — without copying
# CT's protected-table list into an SCP rule body.
#
# Ships at DENY baseline (born-at-deny per WP-SCP-025 Phase 2 / D-053; NOT a
# member of the workflow's WARN_BASELINE_RULES set). Self-contained per-file:
# identical evaluation envelope to SCP-R-003 (`input.source_file` carries the
# path, `input.content` carries the text). Additive-only migrations
# (create_table / add_column / create_index) DO NOT trip the rule — only
# destructive / structural ops do (FP-surface control, RULE-006 §4).
#
# Defines its OWN scp_r_012_* predicates per the SCP-R-004 SAFE-MAJ-001 /
# SCP-R-003 precedent (rule-local helpers preserve per-rule coverage). Reuses
# ONLY the estate-wide suppression helpers scp_active_waiver_for +
# scp_rule_config_disabled + scp_rule_config_entry from scp_common.rego.
package main

import rego.v1

scp_r_012_rule_id := "SCP-R-012"

scp_r_012_remediation_url := concat("", [
	"https://github.com/jrnb2024/standards-control-plane/blob/main/",
	"docs/reviews/rule-proposals/RULE-006-protected-table-migration-marker.md",
])

# Destructive / structural DDL operations. Additive ops (create_table /
# add_column / create_index / create_*) are intentionally ABSENT — they are not
# the dangerous class and must not trip the rule (RULE-006 §4 FP surface).
scp_r_012_destructive_patterns := [
	`op\.drop_table\s*\(`,
	`op\.drop_column\s*\(`,
	`op\.drop_constraint\s*\(`,
	`op\.alter_column\s*\(`,
	`op\.rename_table\s*\(`,
	# Raw-SQL escape hatch: DROP / ALTER / TRUNCATE / RENAME inside an
	# op.execute() string (case-insensitive + dotall for multi-line SQL).
	# Allows an optional SQLAlchemy wrapper before the literal
	# (`text(...)` / `sa.text(...)`). Best-effort: still cannot see SQL
	# built from a variable / string concatenation (documented coverage
	# limit in RULE-006 §4 — the op.* helper path is the primary gate).
	`(?is)op\.execute\s*\(\s*(?:[a-z_.]+\s*\(\s*)?["'].*?\b(drop|alter|truncate|rename)\b`,
]

# True iff the file is an Alembic-style migration: a `.py` under a `versions/`
# directory (the Alembic revision-script convention). Self-contained — no
# external state, path-only.
scp_r_012_is_migration_file(path) if {
	endswith(path, ".py")
	regex.match(`(^|/)versions/`, path)
}

# True iff the content performs at least one destructive / structural DDL op.
scp_r_012_has_destructive_op(content) if {
	some pattern in scp_r_012_destructive_patterns
	regex.match(pattern, content)
}

# Marker form: a standalone `# scp:protected-table-attested` comment line
# (mirrors SCP-R-003's marker regex; `//` accepted for parity though migrations
# are Python).
scp_r_012_has_attestation_marker(content) if {
	regex.match(`(?m)^\s*(#|//)\s*scp:protected-table-attested\s*$`, content)
}

# Per-file applicability gate. Mirrors scp_r_003_manifest_input.
scp_r_012_migration_input if {
	source_file := object.get(input, "source_file", "")
	source_file != ""
	scp_r_012_is_migration_file(source_file)
	content := object.get(input, "content", "")
	is_string(content)
}

# Factor potential denies into raw_findings; public `deny` filters by
# waiver/rule-config suppression; `warn` rules emit observability for suppressed
# findings (SCP-R-003 / WP-SCP-022 precedent).
scp_r_012_raw_findings contains finding if {
	scp_r_012_migration_input
	source_file := object.get(input, "source_file", "")
	content := object.get(input, "content", "")
	scp_r_012_has_destructive_op(content)
	not scp_r_012_has_attestation_marker(content)
	finding := {
		"message": sprintf("%s performs a destructive schema-migration operation but does not declare the `scp:protected-table-attested` marker (confirm it does not destructively alter a protected table, then add the marker)", [source_file]),
		"rule_id": scp_r_012_rule_id,
		"file": source_file,
		"remediation_url": scp_r_012_remediation_url,
	}
}

# Public deny rule. Born at deny — NOT in WARN_BASELINE_RULES — so these block
# the merge gate (unless waived / rule-config-disabled).
deny contains output if {
	some finding in scp_r_012_raw_findings
	not scp_active_waiver_for(scp_r_012_rule_id)
	not scp_rule_config_disabled(scp_r_012_rule_id)
	output := object.union(finding, {"msg": finding.message})
}

# Suppression-observability warn: active waiver against SCP-R-012.
warn contains record if {
	count(scp_r_012_raw_findings) > 0
	some w in scp_waivers
	object.get(w, "rule_id", "") == scp_r_012_rule_id
	not scp_waiver_expired(w)
	record := {
		"kind": "waiver",
		"rule_id": scp_r_012_rule_id,
		"waiver_id": object.get(w, "waiver_id", ""),
		"finding_id": object.get(w, "finding_id", ""),
		"expires_at": object.get(w, "expires_at", ""),
		"file": object.get(input, "source_file", ""),
		"msg": sprintf(
			"%s suppressed by waiver (waiver_id=%s, expires_at=%s)",
			[scp_r_012_rule_id, object.get(w, "waiver_id", ""), object.get(w, "expires_at", "")],
		),
	}
}

# Suppression-observability warn: `.scp/rule-config.yaml disable: true`.
warn contains record if {
	count(scp_r_012_raw_findings) > 0
	scp_rule_config_disabled(scp_r_012_rule_id)
	cfg := scp_rule_config_entry(scp_r_012_rule_id)
	record := {
		"kind": "rule_config",
		"rule_id": scp_r_012_rule_id,
		"reason": "rule-config override",
		"expires_at": object.get(cfg, "expires_at", ""),
		"msg": sprintf(
			"%s suppressed by .scp/rule-config.yaml (expires_at=%s)",
			[scp_r_012_rule_id, object.get(cfg, "expires_at", "")],
		),
	}
}
