package main_test

import data.main
import rego.v1

# SCP-R-031 evaluates an aggregate envelope: input.rule_config carries the
# `estate-context-marker` opt-in (mirrors SCP-R-030's acc-hook-installed);
# input.claude_md_present + input.claude_md AND input.agents_md_present +
# input.agents_md carry BOTH instruction-file states (materialised by the
# companion workflow PR). data.rule_config carries the generic disable path;
# data.waivers the waiver path. Until the companion PR materialises
# input.rule_config, the rule vacuously passes in production (SCP-R-006/030
# safe-failure precedent).

scp_r_031_deny(input_value) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
		finding.rule_id == "SCP-R-031"
	]
}

scp_r_031_warn(input_value) := records if {
	records := [record |
		some record in main.warn with input as input_value
		record.rule_id == "SCP-R-031"
	]
}

scp_r_031_deny_full(input_value, waivers, rule_config) := results if {
	results := [finding |
		some finding in main.deny with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
		finding.rule_id == "SCP-R-031"
	]
}

scp_r_031_warn_full(input_value, waivers, rule_config) := records if {
	records := [record |
		some record in main.warn with input as input_value
			with data.waivers as waivers
			with data.rule_config as rule_config
		record.rule_id == "SCP-R-031"
	]
}

scp_r_031_codes(findings) := {f.code | some f in findings}

scp_r_031_files(findings) := {f.file | some f in findings}

# The ratified marker on line 1 (top-of-file block). A conformant instruction
# file carries it in its first 5 lines.
scp_r_031_marker := "<!-- canonical:estate-context-bootstrap v1 -->"

scp_r_031_conformant := concat("\n", [
	scp_r_031_marker,
	"# Estate operating context — consult before acting",
	"This repo works on the Mapp Fashion estate.",
])

# Marker present but pushed below the 5-line window (buried spoof) — must NOT
# count as present (anchored top-of-file check).
scp_r_031_buried := concat("\n", [
	"# Some repo",
	"line 2",
	"line 3",
	"line 4",
	"line 5",
	scp_r_031_marker,
	"buried below the window.",
])

scp_r_031_opted_in_rc := {"estate-context-marker": true}

# (1) Opted-in, BOTH files carry the marker → PASS (no findings). Dogfood.
test_scp_r_031_both_markers_present_passes if {
	input_value := {
		"rule_config": scp_r_031_opted_in_rc,
		"claude_md_present": true,
		"claude_md": scp_r_031_conformant,
		"agents_md_present": true,
		"agents_md": scp_r_031_conformant,
	}
	count(scp_r_031_deny(input_value)) == 0
	count(scp_r_031_warn(input_value)) == 0
}

# (2) NOT opted-in → vacuous-pass even with both files un-marked.
test_scp_r_031_not_opted_in_vacuous_pass if {
	input_value := {
		"claude_md_present": true,
		"claude_md": "# no marker",
		"agents_md_present": true,
		"agents_md": "# no marker",
	}
	count(scp_r_031_deny(input_value)) == 0
	count(scp_r_031_warn(input_value)) == 0
}

# (2b) rule_config present but estate-context-marker false → vacuous-pass.
test_scp_r_031_opt_in_false_vacuous_pass if {
	input_value := {
		"rule_config": {"estate-context-marker": false},
		"claude_md_present": true,
		"claude_md": "# no marker",
		"agents_md_present": true,
		"agents_md": "# no marker",
	}
	count(scp_r_031_deny(input_value)) == 0
}

# (3) Opted-in, CLAUDE.md lacks the marker but AGENTS.md has it → ONE finding
# naming CLAUDE.md.
test_scp_r_031_marker_absent_claude if {
	input_value := {
		"rule_config": scp_r_031_opted_in_rc,
		"claude_md_present": true,
		"claude_md": "# CLAUDE without the marker",
		"agents_md_present": true,
		"agents_md": scp_r_031_conformant,
	}
	results := scp_r_031_deny(input_value)
	count(results) == 1
	scp_r_031_codes(results) == {"marker_absent"}
	scp_r_031_files(results) == {"CLAUDE.md"}
}

# (4) Opted-in, AGENTS.md lacks the marker but CLAUDE.md has it → ONE finding
# naming AGENTS.md. This is the teeth on the SECOND file (the whole point).
test_scp_r_031_marker_absent_agents if {
	input_value := {
		"rule_config": scp_r_031_opted_in_rc,
		"claude_md_present": true,
		"claude_md": scp_r_031_conformant,
		"agents_md_present": true,
		"agents_md": "# AGENTS without the marker",
	}
	results := scp_r_031_deny(input_value)
	count(results) == 1
	scp_r_031_codes(results) == {"marker_absent"}
	scp_r_031_files(results) == {"AGENTS.md"}
}

# (5) Opted-in, BOTH files lack the marker → TWO marker_absent findings, one
# per file.
test_scp_r_031_marker_absent_both if {
	input_value := {
		"rule_config": scp_r_031_opted_in_rc,
		"claude_md_present": true,
		"claude_md": "# no marker here",
		"agents_md_present": true,
		"agents_md": "# nor here",
	}
	results := scp_r_031_deny(input_value)
	count(results) == 2
	scp_r_031_codes(results) == {"marker_absent"}
	scp_r_031_files(results) == {"CLAUDE.md", "AGENTS.md"}
}

# (6) Opted-in, marker buried below the 5-line window → marker_absent (anchor
# rejects a marker pushed below the top-of-file window; an in-window code-fenced
# marker would still match by substring — a harmless present-spoof, not enforced).
test_scp_r_031_marker_buried_below_window if {
	input_value := {
		"rule_config": scp_r_031_opted_in_rc,
		"claude_md_present": true,
		"claude_md": scp_r_031_buried,
		"agents_md_present": true,
		"agents_md": scp_r_031_conformant,
	}
	results := scp_r_031_deny(input_value)
	count(results) == 1
	scp_r_031_files(results) == {"CLAUDE.md"}
}

# (7) Opted-in, wrong marker version v2 → marker_absent (exact-substring
# migration gate).
test_scp_r_031_marker_absent_wrong_version if {
	v2 := concat("\n", [
		"<!-- canonical:estate-context-bootstrap v2 -->",
		"# Estate operating context",
	])
	input_value := {
		"rule_config": scp_r_031_opted_in_rc,
		"claude_md_present": true,
		"claude_md": v2,
		"agents_md_present": true,
		"agents_md": scp_r_031_conformant,
	}
	scp_r_031_codes(scp_r_031_deny(input_value)) == {"marker_absent"}
	scp_r_031_files(scp_r_031_deny(input_value)) == {"CLAUDE.md"}
}

# (8) Opted-in, both files carry the marker BUT AGENTS.md leaks a dynamic
# Estate token in its top block → ONE dynamic_state finding naming AGENTS.md.
test_scp_r_031_dynamic_state_agents if {
	agents_with_state := concat("\n", [
		scp_r_031_marker,
		"# Estate operating context",
		"workspace_id: ws-42 org_id: mapp-fashion",
	])
	input_value := {
		"rule_config": scp_r_031_opted_in_rc,
		"claude_md_present": true,
		"claude_md": scp_r_031_conformant,
		"agents_md_present": true,
		"agents_md": agents_with_state,
	}
	results := scp_r_031_deny(input_value)
	count(results) == 1
	scp_r_031_codes(results) == {"dynamic_state"}
	scp_r_031_files(results) == {"AGENTS.md"}
}

# (8b) Dynamic token in CLAUDE.md top block (marker present) → dynamic_state
# naming CLAUDE.md. Exercises the CLAUDE.md dynamic-state clause + a different
# forbidden token (content digest).
test_scp_r_031_dynamic_state_claude if {
	claude_with_state := concat("\n", [
		scp_r_031_marker,
		"# Estate operating context",
		"pinned digest sha256:deadbeef expires_at 2026-12-31",
	])
	input_value := {
		"rule_config": scp_r_031_opted_in_rc,
		"claude_md_present": true,
		"claude_md": claude_with_state,
		"agents_md_present": true,
		"agents_md": scp_r_031_conformant,
	}
	results := scp_r_031_deny(input_value)
	count(results) == 1
	scp_r_031_codes(results) == {"dynamic_state"}
	scp_r_031_files(results) == {"CLAUDE.md"}
}

# (9) Opted-in, CLAUDE.md present-but-non-string (null) → content totals to ""
# (second clause) → marker_absent naming CLAUDE.md.
test_scp_r_031_non_string_content_totals_empty if {
	input_value := {
		"rule_config": scp_r_031_opted_in_rc,
		"claude_md_present": true,
		"claude_md": null,
		"agents_md_present": true,
		"agents_md": scp_r_031_conformant,
	}
	scp_r_031_codes(scp_r_031_deny(input_value)) == {"marker_absent"}
	scp_r_031_files(scp_r_031_deny(input_value)) == {"CLAUDE.md"}
}

# (9b) Opted-in, AGENTS.md present-but-non-string (null) → content totals to ""
# via the SECOND-FILE total-function clause (scp_r_031_agents_md_content := ""
# if not is_string(...)) → marker_absent naming AGENTS.md. The symmetric partner
# to (9): CLAUDE.md is conformant here so the ONLY finding comes from the
# AGENTS.md "" branch, making that total-function line load-bearing under
# regression (test 9 exercises only the CLAUDE.md twin).
test_scp_r_031_agents_non_string_content_totals_empty if {
	input_value := {
		"rule_config": scp_r_031_opted_in_rc,
		"claude_md_present": true,
		"claude_md": scp_r_031_conformant,
		"agents_md_present": true,
		"agents_md": null,
	}
	results := scp_r_031_deny(input_value)
	count(results) == 1
	scp_r_031_codes(results) == {"marker_absent"}
	scp_r_031_files(results) == {"AGENTS.md"}
}

# (10) Opted-in + a file absent (present flag false) → that file is NOT gated
# (no finding for it). Only the present-and-un-marked AGENTS.md fires.
test_scp_r_031_absent_file_not_gated if {
	input_value := {
		"rule_config": scp_r_031_opted_in_rc,
		"claude_md_present": false,
		"agents_md_present": true,
		"agents_md": "# AGENTS without the marker",
	}
	results := scp_r_031_deny(input_value)
	count(results) == 1
	scp_r_031_files(results) == {"AGENTS.md"}
}

# (11) Opted-in + both markers absent + rules.SCP-R-031.disable: true → 0 deny
# + warn observability (rule-config suppression path through data.main.deny).
test_scp_r_031_rule_config_disable_suppresses if {
	input_value := {
		"rule_config": scp_r_031_opted_in_rc,
		"claude_md_present": true,
		"claude_md": "# no marker",
		"agents_md_present": true,
		"agents_md": "# no marker",
	}
	rule_config := {"rules": {"SCP-R-031": {
		"disable": true,
		"justification": "Operator override during onboarding window",
		"expires_at": "2099-12-31T00:00:00Z",
	}}}
	count(scp_r_031_deny_full(input_value, [], rule_config)) == 0
	warns := scp_r_031_warn_full(input_value, [], rule_config)
	count(warns) >= 1
}

# (12) Opted-in + markers absent + active waiver → 0 deny + warn observability.
test_scp_r_031_active_waiver_suppresses if {
	input_value := {
		"rule_config": scp_r_031_opted_in_rc,
		"claude_md_present": true,
		"claude_md": "# no marker",
		"agents_md_present": true,
		"agents_md": "# no marker",
	}
	waivers := [{
		"waiver_id": "scp-r-031-onboarding-grace",
		"rule_id": "SCP-R-031",
		"reason": "Approved per https://github.com/jrnb2024/standards-control-plane/issues/231",
		"approved_by": "@jrnb2024",
		"created_at": "2026-07-25T00:00:00Z",
		"expires_at": "2099-12-31T00:00:00Z",
	}]
	count(scp_r_031_deny_full(input_value, waivers, {})) == 0
	count(scp_r_031_warn_full(input_value, waivers, {})) >= 1
}
