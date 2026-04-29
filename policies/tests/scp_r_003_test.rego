package main_test

import data.main
import rego.v1

scp_r_003_results(input_value) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
		finding.rule_id == "SCP-R-003"
	]
}

test_scp_r_003_allows_package_json_boolean_marker if {
	input_value := {
		"source_file": "package.json",
		"content": "{\n  \"name\": \"scp\",\n  \"scp:vendoring-attested\": true\n}\n",
	}

	count(scp_r_003_results(input_value)) == 0
}

test_scp_r_003_allows_comment_marker_for_pyproject if {
	input_value := {
		"source_file": "pyproject.toml",
		"content": "# scp:vendoring-attested\n[project]\nname = \"scp\"\n",
	}

	count(scp_r_003_results(input_value)) == 0
}

test_scp_r_003_denies_missing_marker if {
	input_value := {
		"source_file": "go.mod",
		"content": "module example.com/scp\n\ngo 1.23.0\n",
	}

	results := scp_r_003_results(input_value)
	count(results) == 1
	results[0].file == "go.mod"
	contains(results[0].message, "vendoring attestation marker")
}

test_scp_r_003_allows_comment_marker_for_go_mod if {
	input_value := {
		"source_file": "go.mod",
		"content": "// scp:vendoring-attested\nmodule example.com/scp\n\ngo 1.23.0\n",
	}

	count(scp_r_003_results(input_value)) == 0
}

test_scp_r_003_denies_package_json_without_marker if {
	input_value := {
		"source_file": "package.json",
		"content": "{\n  \"name\": \"scp\"\n}\n",
	}

	results := scp_r_003_results(input_value)
	count(results) == 1
	results[0].file == "package.json"
	contains(results[0].message, "vendoring attestation marker")
}

test_scp_r_003_denies_pyproject_without_marker if {
	input_value := {
		"source_file": "pyproject.toml",
		"content": "[project]\nname = \"scp\"\n",
	}

	results := scp_r_003_results(input_value)
	count(results) == 1
	results[0].file == "pyproject.toml"
	contains(results[0].message, "vendoring attestation marker")
}

test_scp_r_003_ignores_non_manifest_inputs if {
	input_value := {
		"source_file": "README.md",
		"content": "# not a manifest\n",
	}

	count(scp_r_003_results(input_value)) == 0
}
