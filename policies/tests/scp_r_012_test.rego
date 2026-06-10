package main_test

import data.main
import rego.v1

scp_r_012_results(input_value) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
		finding.rule_id == "SCP-R-012"
	]
}

# --- allow paths -----------------------------------------------------------

# Destructive op + marker present → no finding.
test_scp_r_012_allows_attested_drop_table if {
	input_value := {
		"source_file": "alembic/versions/0042_drop_legacy.py",
		"content": "# scp:protected-table-attested\ndef upgrade():\n    op.drop_table(\"legacy_users\")\n",
	}

	count(scp_r_012_results(input_value)) == 0
}

# Additive-only migration (no destructive op) → no finding even without marker.
test_scp_r_012_allows_additive_only_migration if {
	input_value := {
		"source_file": "migrations/versions/0043_add_col.py",
		"content": "def upgrade():\n    op.create_table(\"orders\")\n    op.add_column(\"orders\", sa.Column(\"note\", sa.String()))\n",
	}

	count(scp_r_012_results(input_value)) == 0
}

# A `.py` that is NOT under a versions/ directory → not a migration → no finding.
test_scp_r_012_ignores_non_migration_python if {
	input_value := {
		"source_file": "app/models/user.py",
		"content": "def upgrade():\n    op.drop_table(\"users\")\n",
	}

	count(scp_r_012_results(input_value)) == 0
}

# Non-`.py` file with destructive-looking text → not a migration → no finding.
test_scp_r_012_ignores_non_python_input if {
	input_value := {
		"source_file": "versions/notes.md",
		"content": "op.drop_table(\"users\")\n",
	}

	count(scp_r_012_results(input_value)) == 0
}

# Raw-SQL destructive op + marker present → no finding.
test_scp_r_012_allows_attested_raw_sql_drop if {
	input_value := {
		"source_file": "db/versions/0044_raw.py",
		"content": "# scp:protected-table-attested\ndef upgrade():\n    op.execute(\"DROP TABLE oauth_clients\")\n",
	}

	count(scp_r_012_results(input_value)) == 0
}

# --- deny paths ------------------------------------------------------------

# drop_table without marker → 1 finding.
test_scp_r_012_denies_drop_table_without_marker if {
	input_value := {
		"source_file": "alembic/versions/0045_drop.py",
		"content": "def upgrade():\n    op.drop_table(\"permission_schemas\")\n",
	}

	results := scp_r_012_results(input_value)
	count(results) == 1
	results[0].file == "alembic/versions/0045_drop.py"
	contains(results[0].message, "scp:protected-table-attested")
}

# drop_column without marker → 1 finding.
test_scp_r_012_denies_drop_column_without_marker if {
	input_value := {
		"source_file": "migrations/versions/0046_dropcol.py",
		"content": "def upgrade():\n    op.drop_column(\"users\", \"email\")\n",
	}

	count(scp_r_012_results(input_value)) == 1
}

# alter_column without marker → 1 finding.
test_scp_r_012_denies_alter_column_without_marker if {
	input_value := {
		"source_file": "migrations/versions/0047_alter.py",
		"content": "def upgrade():\n    op.alter_column(\"tenants\", \"slug\", type_=sa.Text())\n",
	}

	count(scp_r_012_results(input_value)) == 1
}

# Raw-SQL ALTER without marker → 1 finding (case-insensitive).
test_scp_r_012_denies_raw_sql_alter_without_marker if {
	input_value := {
		"source_file": "db/versions/0048_rawalter.py",
		"content": "def upgrade():\n    op.execute(\"alter table users drop column ssn\")\n",
	}

	count(scp_r_012_results(input_value)) == 1
}

# drop_constraint without marker → 1 finding.
test_scp_r_012_denies_drop_constraint_without_marker if {
	input_value := {
		"source_file": "migrations/versions/0049_dropfk.py",
		"content": "def upgrade():\n    op.drop_constraint(\"fk_orders_user\", \"orders\", type_=\"foreignkey\")\n",
	}

	count(scp_r_012_results(input_value)) == 1
}

# rename_table without marker → 1 finding.
test_scp_r_012_denies_rename_table_without_marker if {
	input_value := {
		"source_file": "migrations/versions/0050_rename.py",
		"content": "def upgrade():\n    op.rename_table(\"users\", \"accounts\")\n",
	}

	count(scp_r_012_results(input_value)) == 1
}

# Raw-SQL DROP wrapped in sa.text(...) without marker → 1 (regex wrapper branch).
test_scp_r_012_denies_raw_sql_text_wrapper_without_marker if {
	input_value := {
		"source_file": "db/versions/0051_text.py",
		"content": "def upgrade():\n    op.execute(sa.text(\"DROP TABLE oauth_clients\"))\n",
	}

	count(scp_r_012_results(input_value)) == 1
}

# Raw-SQL DROP in a multi-line triple-quoted string without marker → 1 (dotall).
test_scp_r_012_denies_raw_sql_multiline_without_marker if {
	input_value := {
		"source_file": "db/versions/0052_multiline.py",
		"content": "def upgrade():\n    op.execute(\"\"\"\n    DROP TABLE tenants\n    \"\"\")\n",
	}

	count(scp_r_012_results(input_value)) == 1
}

# --- suppression: waiver + rule-config -------------------------------------

scp_r_012_results_full(input_value, waivers, rule_config, now_ns) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
			with main.scp_now_ns as now_ns
		finding.rule_id == "SCP-R-012"
	]
}

scp_r_012_warns_full(input_value, waivers, rule_config, now_ns) := records if {
	records := [record |
		some record in main.warn with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
			with main.scp_now_ns as now_ns
		record.rule_id == "SCP-R-012"
	]
}

scp_r_012_unattested_migration := {
	"source_file": "alembic/versions/0099_drop.py",
	"content": "def upgrade():\n    op.drop_table(\"users\")\n",
}

scp_r_012_test_now_ns := time.parse_rfc3339_ns("2026-04-29T00:00:00Z")

# Active waiver suppresses the deny and emits a kind=waiver warn record.
test_scp_r_012_waiver_suppresses_deny if {
	waivers := [{
		"waiver_id": "W-MIGRATION",
		"rule_id": "SCP-R-012",
		"expires_at": "2099-12-31T23:59:59Z",
		"reason": "reviewed — table is not protected",
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29",
	}]
	count(scp_r_012_results_full(scp_r_012_unattested_migration, waivers, {}, scp_r_012_test_now_ns)) == 0
	warns := scp_r_012_warns_full(scp_r_012_unattested_migration, waivers, {}, scp_r_012_test_now_ns)
	count(warns) == 1
	warns[0].kind == "waiver"
	warns[0].waiver_id == "W-MIGRATION"
}

# Expired waiver does NOT suppress.
test_scp_r_012_expired_waiver_does_not_suppress if {
	waivers := [{
		"waiver_id": "W-EXPIRED",
		"rule_id": "SCP-R-012",
		"expires_at": "2020-01-01",
		"reason": "stale",
		"approved_by": "@jrnb2024",
		"created_at": "2019-01-01",
	}]
	count(scp_r_012_results_full(scp_r_012_unattested_migration, waivers, {}, scp_r_012_test_now_ns)) == 1
	count(scp_r_012_warns_full(scp_r_012_unattested_migration, waivers, {}, scp_r_012_test_now_ns)) == 0
}

# rule-config disable suppresses the deny and emits a kind=rule_config warn.
test_scp_r_012_rule_config_disable_suppresses_deny if {
	rule_config := {"rules": {"SCP-R-012": {
		"disable": true,
		"justification": "test override",
		"expires_at": "2099-12-31",
	}}}
	count(scp_r_012_results_full(scp_r_012_unattested_migration, [], rule_config, scp_r_012_test_now_ns)) == 0
	warns := scp_r_012_warns_full(scp_r_012_unattested_migration, [], rule_config, scp_r_012_test_now_ns)
	count(warns) == 1
	warns[0].kind == "rule_config"
	warns[0].reason == "rule-config override"
}

# Waiver with missing expires_at must fail closed (no suppression).
test_scp_r_012_waiver_missing_expires_at_does_not_suppress if {
	waivers := [{
		"waiver_id": "W-NO-EXPIRY",
		"rule_id": "SCP-R-012",
		"reason": "missing expires_at",
		"approved_by": "@jrnb2024",
		"created_at": "2026-04-29",
	}]
	count(scp_r_012_results_full(scp_r_012_unattested_migration, waivers, {}, scp_r_012_test_now_ns)) == 1
	count(scp_r_012_warns_full(scp_r_012_unattested_migration, waivers, {}, scp_r_012_test_now_ns)) == 0
}
